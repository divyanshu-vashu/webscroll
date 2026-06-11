import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from fastmcp import FastMCP

from engines.strategy_engine.orchestrator import StrategyOrchestrator, PageResult
from engines.strategy_engine.models import ScrapeRequest, PageAction
from engines.search.search_engine import run_search, extract_urls
from main import save_page, _make_crawl_session_folder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daemon")

DB_PATH = "jobs.db"

app = FastAPI(
    title="WebScroll Daemon",
    description="Stealth Web Extraction Pipeline Service with Async SQLite Job Queue & MCP Server",
    version="1.2.0",
)

# Global Orchestrator instance
orchestrator = StrategyOrchestrator()

# Memory Queue for instant wakeup
memory_queue = asyncio.Queue()

# Setup FastMCP server
mcp = FastMCP("WebScroll")


class PageActionModel(BaseModel):
    kind: str
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout_ms: int = 5000
    optional: bool = False
    notes: str = ""
    max_iterations: int = 10
    wait_ms: int = 1500
    scroll_step_px: int = 800


class PaginationConfigModel(BaseModel):
    type: str
    param: Optional[str] = None
    step: int = 1
    max_pages: int = 20
    next_url: Optional[str] = None
    page_urls: List[str] = Field(default_factory=list)
    pattern: Optional[str] = None
    offset_param: Optional[str] = None
    limit_param: Optional[str] = None
    limit_value: Optional[int] = None
    selector: Optional[str] = None
    mode: Optional[str] = None
    concurrent: bool = False
    max_workers: int = 3


class ScrapeRequestModel(BaseModel):
    url: str
    crawl: bool = False
    actions: List[PageActionModel] = Field(default_factory=list)
    session_key: Optional[str] = None
    allow_http_probe: bool = True
    proxy_policy: str = "sticky"
    extraction_mode: str = "balanced"
    unlock_strategy: str = "unlock_first"
    pagination_mode: bool = False
    pagination: Optional[PaginationConfigModel] = None
    stream_mode: bool = False
    max_pages: int = 100
    max_depth: int = 3
    delay: float = 1.5
    output_dir: str = "storage/extracted"


class SearchRequestModel(BaseModel):
    query: str
    mode: str = "text"  # "text" or "news"
    top_k: int = 20
    output_dir: str = "storage/extracted"
    scrape_results: bool = True
    delay: float = 1.5


def serialize_page_result(page: PageResult) -> Dict[str, Any]:
    return page.to_dict()


def _model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def init_db():
    """Create jobs table if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'pending',
                payload TEXT,
                result TEXT,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def worker():
    """Background worker processing jobs from the queue."""
    logger.info("Background job queue worker started.")
    while True:
        job_id = await memory_queue.get()
        logger.info("Processing job %s from queue", job_id)

        # 1. Update status to 'processing'
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE jobs SET status='processing', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (job_id,)
            )
            await db.commit()

            cursor = await db.execute("SELECT payload FROM jobs WHERE id=?", (job_id,))
            row = await cursor.fetchone()
            if not row:
                memory_queue.task_done()
                continue
            payload_str = row[0]

        # 2. Execute job
        try:
            payload = json.loads(payload_str)
            url = payload["url"]
            crawl = payload.get("crawl", False)
            output_dir = payload.get("output_dir", "storage/extracted")
            max_pages = payload.get("max_pages", 100)
            max_depth = payload.get("max_depth", 3)
            delay = payload.get("delay", 1.5)

            storage_path = Path(output_dir)
            storage_path.mkdir(parents=True, exist_ok=True)

            if crawl:
                session_storage = _make_crawl_session_folder(url, storage_path)
            else:
                session_storage = storage_path

            # Reconfigure orchestrator
            orchestrator.max_pages = max_pages
            orchestrator.max_depth = max_depth
            orchestrator.crawl_delay = delay

            actions_list = [
                PageAction(
                    kind=a.get("kind"),
                    selector=a.get("selector"),
                    value=a.get("value"),
                    timeout_ms=a.get("timeout_ms", 5000),
                optional=a.get("optional", False),
                notes=a.get("notes", ""),
                max_iterations=a.get("max_iterations", 10),
                wait_ms=a.get("wait_ms", 1500),
                scroll_step_px=a.get("scroll_step_px", 800),
            )
            for a in payload.get("actions", [])
        ]

            scrape_req = ScrapeRequest(
                url=url,
                crawl=crawl,
                actions=actions_list,
                session_key=payload.get("session_key"),
                allow_http_probe=payload.get("allow_http_probe", True),
                proxy_policy=payload.get("proxy_policy", "sticky"),
                extraction_mode=payload.get("extraction_mode", "balanced"),
                unlock_strategy=payload.get("unlock_strategy", "unlock_first"),
                pagination_mode=payload.get("pagination_mode", False),
                pagination=payload.get("pagination"),
                stream_mode=payload.get("stream_mode", False),
            )

            results_list = []

            def on_page_callback(page: PageResult):
                save_page(page, session_storage)
                results_list.append(page)

            # Run synchronously blocking scraping library safely in a worker thread
            await asyncio.to_thread(
                orchestrator.run,
                url=url,
                crawl=crawl,
                on_page=on_page_callback,
                request=scrape_req
            )

            serialized_results = [serialize_page_result(r) for r in results_list]

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE jobs SET status='done', result=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps(serialized_results), job_id)
                )
                await db.commit()
            logger.info("Job %s completed successfully", job_id)

        except Exception as e:
            logger.exception("Failed to process job %s", job_id)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE jobs SET status='failed', error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (str(e), job_id)
                )
                await db.commit()

        finally:
            memory_queue.task_done()


# =========================================================================
# MCP Tools Registration
# =========================================================================
@mcp.tool()
async def scrape_url(url: str, crawl: bool = False, max_pages: int = 10, max_depth: int = 2) -> str:
    """
    Stealthily scrape or crawl a website URL and return the extracted visible text/markdown.
    - url: The target URL to extract (e.g. 'https://techcrunch.com').
    - crawl: If True, crawls and extracts links recursively on the site.
    - max_pages: Maximum pages to fetch in crawl mode. Default 10.
    - max_depth: Maximum BFS recursion depth. Default 2.
    """
    logger.info("MCP scrape tool triggered for URL: %s", url)
    payload = {
        "url": url,
        "crawl": crawl,
        "actions": [],
        "session_key": None,
        "allow_http_probe": True,
        "proxy_policy": "sticky",
        "extraction_mode": "balanced",
        "unlock_strategy": "unlock_first",
        "max_pages": max_pages,
        "max_depth": max_depth,
        "delay": 1.5,
        "output_dir": "storage/extracted"
    }

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO jobs (payload, status) VALUES (?, 'pending')",
            (json.dumps(payload),)
        )
        await db.commit()
        job_id = cursor.lastrowid

    await memory_queue.put(job_id)

    # Poll database for completion (up to 5 minutes)
    for _ in range(300):
        await asyncio.sleep(1)
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT status, result, error FROM jobs WHERE id=?",
                (job_id,)
            )
            row = await cursor.fetchone()
            if row:
                status, result, error = row
                if status == 'done':
                    results = json.loads(result)
                    output = []
                    for r in results:
                        output.append(f"### URL: {r.get('url')}\n\n{r.get('markdown', '')}")
                    return "\n\n---\n\n".join(output)
                elif status == 'failed':
                    return f"Scraping failed: {error}"
    return "Scraping job timed out."


@mcp.tool()
async def search_web(query: str, mode: str = "text", top_k: int = 5) -> str:
    """
    Search the web or news and return matching result URLs.
    - query: The query text to search.
    - mode: Search type ('text' or 'news'). Default is 'text'.
    - top_k: Number of search results to retrieve. Default is 5.
    """
    logger.info("MCP search tool triggered query='%s' mode=%s", query, mode)
    try:
        search_results = await asyncio.to_thread(run_search, query, mode=mode, top_k=top_k)
        urls = extract_urls(search_results)
        return json.dumps({"query": query, "urls": urls}, indent=2)
    except Exception as e:
        return f"Search failed: {e}"


@app.on_event("startup")
async def startup_event():
    # Setup SQLite db
    await init_db()

    # Recovery: read pending or processing jobs on startup and enqueue them
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM jobs WHERE status IN ('pending', 'processing') ORDER BY id ASC"
        )
        rows = await cursor.fetchall()
        for row in rows:
            await memory_queue.put(row[0])
            logger.info("Recovered and queued unfinished job %s", row[0])

    # Start queue worker background task
    asyncio.create_task(worker())


# Mount MCP ASGI application onto FastAPI at /mcp
app.mount("/mcp", mcp.http_app())


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "WebScroll Daemon is running"}


@app.post("/job/scrape")
async def submit_scrape_job(payload: ScrapeRequestModel):
    """
    Submit a scrape job to be processed asynchronously by the worker.
    Returns the queued job ID.
    """
    logger.info("Queuing scrape job for url=%s", payload.url)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO jobs (payload, status) VALUES (?, 'pending')",
            (json.dumps(_model_to_dict(payload)),)
        )
        await db.commit()
        job_id = cursor.lastrowid

    await memory_queue.put(job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/job/{job_id}")
async def get_job_status(job_id: int):
    """
    Get the status and result of a submitted job.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT status, result, error, created_at, updated_at FROM jobs WHERE id=?",
            (job_id,)
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    status, result, error, created_at, updated_at = row
    response = {
        "job_id": job_id,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "error": error,
        "results": None
    }

    if result:
        response["results"] = json.loads(result)

    return response


@app.post("/scrape")
def scrape_instant(payload: ScrapeRequestModel):
    """
    Synchronous direct scraping endpoint (processes scrape instantly in caller thread).
    """
    logger.info("Direct instant scrape requested for url=%s", payload.url)
    storage_path = Path(payload.output_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    if payload.crawl:
        session_storage = _make_crawl_session_folder(payload.url, storage_path)
    else:
        session_storage = storage_path

    orchestrator.max_pages = payload.max_pages
    orchestrator.max_depth = payload.max_depth
    orchestrator.crawl_delay = payload.delay

    actions_list = [
        PageAction(
            kind=a.kind,
            selector=a.selector,
            value=a.value,
            timeout_ms=a.timeout_ms,
            optional=a.optional,
            notes=a.notes,
            max_iterations=a.max_iterations,
            wait_ms=a.wait_ms,
            scroll_step_px=a.scroll_step_px,
        )
        for a in payload.actions
    ]

    scrape_req = ScrapeRequest(
        url=payload.url,
        crawl=payload.crawl,
        actions=actions_list,
        session_key=payload.session_key,
        allow_http_probe=payload.allow_http_probe,
        proxy_policy=payload.proxy_policy,
        extraction_mode=payload.extraction_mode,
        unlock_strategy=payload.unlock_strategy,
        pagination_mode=payload.pagination_mode,
        pagination=_model_to_dict(payload.pagination) if payload.pagination else None,
        stream_mode=payload.stream_mode,
    )

    results_list = []

    def on_page_callback(page: PageResult):
        save_page(page, session_storage)
        results_list.append(page)

    try:
        orchestrator.run(
            url=payload.url,
            crawl=payload.crawl,
            on_page=on_page_callback,
            request=scrape_req,
        )
    except Exception as e:
        logger.exception("Error executing direct scrape")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "results": [serialize_page_result(r) for r in results_list],
    }


@app.post("/search")
def search(payload: SearchRequestModel):
    """
    Run a search query (web/news) and optionally scrape the resulting URLs.
    """
    logger.info("Search requested: query='%s' mode=%s", payload.query, payload.mode)
    if payload.mode not in ("text", "news"):
        raise HTTPException(
            status_code=400, detail="Search mode must be 'text' or 'news'"
        )

    try:
        search_results = run_search(
            payload.query, mode=payload.mode, top_k=payload.top_k
        )
        urls = extract_urls(search_results)
    except Exception as e:
        logger.exception("Error executing search query")
        raise HTTPException(status_code=500, detail=str(e))

    output_results = []
    if payload.scrape_results and urls:
        storage_path = Path(payload.output_dir)
        storage_path.mkdir(parents=True, exist_ok=True)
        orchestrator.crawl_delay = payload.delay

        def on_page_callback(page: PageResult):
            save_page(page, storage_path)
            output_results.append(page)

        for url in urls:
            try:
                orchestrator.run(url=url, crawl=False, on_page=on_page_callback)
            except Exception as e:
                logger.warning("Failed to scrape search result URL %s: %s", url, e)

    return {
        "query": payload.query,
        "mode": payload.mode,
        "urls_found": urls,
        "scraped_results_count": len(output_results),
        "results": [serialize_page_result(r) for r in output_results],
    }


if __name__ == "__main__":
    uvicorn.run("daemon:app", host="127.0.0.1", port=8000, reload=True)
