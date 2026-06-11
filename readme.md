# WebScroll

WebScroll is a modular, stealthy web extraction platform. It uses layered defense mechanisms (Browser Fingerprinting, Stealth Clients, Persistent Contexts) to bypass anti-bot protections and cleanly extract `HTML` and `TXT` files for AI ingestion.

## Requirements

Ensure you have your environment set up and dependencies installed:

```bash
pip install -r requirements.txt
playwright install chromium
```

*(Note: Since we use Patchright/Playwright, you must install the browser binaries using the Playwright install command)*

## How to Run

WebScroll uses `main.py` as its core entry point. You can run it in a few different modes depending on your goal.

### 1. Single Page Fetch
To fetch a single URL and bypass protections:
```bash
python main.py --site https://techcrunch.com
```

### 2. BFS Crawl (Simple — uses defaults)
`--crawl` flag is **required** to enable crawl mode. Without it, only the single seed URL is fetched.
```bash
python main.py --site https://techcrunch.com --crawl
```
This uses the defaults: `max-pages=100`, `max-depth=3`, `delay=1.5s`.

### 3. BFS Crawl (Custom limits)
To limit how far the crawl goes:
```bash
python main.py --site https://techcrunch.com --crawl --max-pages 50 --max-depth 2
```
* `--max-pages`: Maximum number of pages to fetch (default: 100).
* `--max-depth`: How many clicks deep to crawl from the seed URL (default: 3).
* `--delay`: Politeness delay between requests in seconds (default: 1.5).

### 3. Search Mode (General Web)
To run a text search query and scrape the top results automatically:
```bash
python main.py --search_text="cloudflare earnings Q3" --search_topk 10
```

### 4. Search Mode (News)
To run a news-specific search query and scrape the top results:
```bash
python main.py --search_news="RBI rate cut 2025" --search_topk 20
```

## Daemon & MCP Server Mode

You can also run WebScroll as a long-running daemon API and Model Context Protocol (MCP) server. This avoids command-line browser startup overhead for subsequent scrapes and allows LLM agents to call WebScroll directly.

### Start the Daemon Server
```bash
python daemon.py
```
This runs the FastAPI application and mounts the MCP server under `/mcp` on `http://127.0.0.1:8000`.

### REST Endpoints
* **`GET /health`**: Health check.
* **`POST /job/scrape`**: Submit a scrape job payload to the persistent SQLite database queue. Returns a `job_id`.
* **`GET /job/{job_id}`**: Check job status (`pending`, `processing`, `done`, `failed`) and retrieve results.
* **`POST /scrape`**: Immediate synchronous stealth scrape.

### MCP Tools Exposing
* **`scrape_url`**: Direct extraction tool for LLM agents.
* **`search_web`**: Search query tool for LLM agents.

## Output


All scraped data is saved by default into the `storage/extracted/` directory. Each URL gets its own unique folder containing:
* `raw.html`: The raw, rendered HTML source.
* `clean.txt`: Cleaned visible text, stripped of scripts, styles, and nav elements.
* `metadata.json`: Technical metadata about the extraction (driver used, block status, etc.).

You can change the output directory by appending `--output custom_folder_path`.



`main.py` currently supports CLI mode for:
- single page fetch
- BFS crawl
- search text -> fetch result URLs
- search news -> fetch result URLs

`daemon.py` supports:
- REST API mode
- async job queue mode
- MCP server mount at `/mcp`

**CLI Mode (`main.py`)**

From the project root:

```powershell
python main.py --site "https://example.com"
```

Useful parameters:
- `--site` direct URL to scrape
- `--crawl` enable BFS crawl
- `--max-pages 50` max pages for crawl
- `--max-depth 2` max BFS depth
- `--delay 1.5` delay between crawl requests
- `--output "storage/extracted"` output folder
- `--search_text "query"` search web then scrape results
- `--search_news "query"` search news then scrape results
- `--search_topk 10` number of search results to fetch

Examples:

Single page:
```powershell
python main.py --site "https://careers.adobe.com/us/en/c/engineering-and-product-jobs"
```

Crawl mode:
```powershell
python main.py --site "https://example.com" --crawl --max-pages 20 --max-depth 2 --delay 2
```

Search text mode:
```powershell
python main.py --search_text "cloudflare earnings" --search_topk 10
```

Search news mode:
```powershell
python main.py --search_news "RBI rate cut" --search_topk 10
```

**Important note about pagination mode**
Right now `main.py` does not expose `pagination_mode` or `pagination` as CLI arguments yet. That feature was wired into the request/orchestrator layer, not into CLI flags.

So for pagination mode, use **daemon mode** for now.

**Daemon Mode (`daemon.py`)**

Start the daemon:

```powershell
python daemon.py
```

Default server:
- `http://127.0.0.1:8000`
- health check: `GET /health`

**Instant scrape API**
Endpoint:
```text
POST /scrape
```

Example body for normal scrape:
```json
{
  "url": "https://example.com/jobs",
  "crawl": false,
  "actions": [],
  "max_pages": 20,
  "max_depth": 2,
  "delay": 1.5,
  "output_dir": "storage/extracted"
}
```

Example body for **pagination mode**:
```json
{
  "url": "https://example.com/jobs?page=1",
  "crawl": false,
  "pagination_mode": true,
  "pagination": {
    "type": "url_param",
    "param": "page",
    "step": 1,
    "max_pages": 10
  },
  "stream_mode": true,
  "actions": [],
  "output_dir": "storage/extracted"
}
```

Example for offset/limit:
```json
{
  "url": "https://example.com/jobs?offset=0&limit=25",
  "pagination_mode": true,
  "pagination": {
    "type": "offset_limit",
    "offset_param": "offset",
    "limit_param": "limit",
    "limit_value": 25,
    "max_pages": 10
  }
}
```

Example for path pagination:
```json
{
  "url": "https://example.com/jobs/page/1",
  "pagination_mode": true,
  "pagination": {
    "type": "url_path",
    "pattern": "/page/{page}",
    "max_pages": 10
  }
}
```

Example for numbered links:
```json
{
  "url": "https://example.com/jobs",
  "pagination_mode": true,
  "pagination": {
    "type": "numbered_links",
    "selector": "nav[aria-label*='pagination'] a",
    "mode": "href",
    "max_pages": 10
  }
}
```

Example with JS actions like load more:
```json
{
  "url": "https://example.com/jobs",
  "pagination_mode": true,
  "pagination": {
    "type": "click_append",
    "max_pages": 10
  },
  "actions": [
    {
      "kind": "repeat_click_append",
      "selector": "button:contains('Load More'), [data-testid='load-more']",
      "max_iterations": 20,
      "wait_ms": 2000,
      "optional": true
    }
  ]
}
```

**Async job mode**
Queue a job:
```text
POST /job/scrape
```

Check result:
```text
GET /job/{job_id}
```

**cURL example**
```powershell
curl -X POST "http://127.0.0.1:8000/scrape" `
  -H "Content-Type: application/json" `
  -d "{\"url\":\"https://example.com/jobs?page=1\",\"pagination_mode\":true,\"pagination\":{\"type\":\"url_param\",\"param\":\"page\",\"step\":1,\"max_pages\":5}}"
```

**My recommendation**
- Use `main.py` for quick single-page or crawl runs.
- Use `daemon.py` for pagination mode, structured actions, and API-driven runs.

If you want, I can do one more step and add `--pagination-mode` and `--pagination-json` directly to [main.py](C:/Users/Divyanshu_Singh/OneDrive%20-%20Infiniti%20Research/Documents/onecode/pc1/tn/webscroll/main.py) so you can run pagination from CLI too.







