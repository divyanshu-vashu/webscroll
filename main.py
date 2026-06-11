"""
main.py — WebScroll pipeline entry point.

Usage:
    # Single page
    python main.py --site https://techcrunch.com

    # Web text search → fetch all result URLs
    python main.py --search_text="cloudflare earnings Q3" --search_topk 10

    # News search → fetch all result URLs
    python main.py --search_news="RBI rate cut 2025" --search_topk 20

    # BFS site crawl
    python main.py --site https://techcrunch.com --crawl --max-pages 50 --max-depth 2
"""
import argparse
import sys
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from engines.text_engine.text_extractor import extract_html_bundle
from engines.strategy_engine.orchestrator import StrategyOrchestrator, PageResult
from engines.search.search_engine import run_search, extract_urls

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")
# ---------------------------------------------------------------------------


def _url_to_folder(url: str) -> str:
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    try:
        domain = url.split("//")[-1].split("/")[0].replace(".", "_")
    except Exception:
        domain = "unknown"
    return f"{domain}_{url_hash}"


def _make_crawl_session_folder(seed_url: str, base_storage: Path) -> Path:
    """Create a unique timestamped session folder for a BFS crawl run."""
    try:
        domain = seed_url.split("//")[-1].split("/")[0].replace(".", "_")
    except Exception:
        domain = "unknown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = base_storage / f"{domain}_crawl_{timestamp}"
    session_folder.mkdir(parents=True, exist_ok=True)
    return session_folder


def save_page(page: PageResult, base_storage: Path) -> Path:
    """Persist a single PageResult to disk with normalized HTML and Markdown outputs."""
    folder = base_storage / _url_to_folder(page.url)
    folder.mkdir(parents=True, exist_ok=True)

    # raw HTML
    (folder / "raw.html").write_text(page.html, encoding="utf-8")

    if page.normalized_html or page.clean_text or page.markdown:
        normalized_html = page.normalized_html
        text = page.clean_text
        markdown = page.markdown
        extraction_metrics = {}
    else:
        extracted = extract_html_bundle(page.html, base_url=page.url)
        normalized_html = extracted.normalized_html
        text = extracted.clean_text
        markdown = extracted.markdown
        extraction_metrics = extracted.metrics

    (folder / "clean.txt").write_text(text, encoding="utf-8")
    (folder / "markdown.md").write_text(markdown, encoding="utf-8")

    # metadata
    meta = {
        "target_url":          page.url,
        "extracted_at":        datetime.now(timezone.utc).isoformat(),
        "driver_used":         page.driver_used,
        "crawl_depth":         page.depth,
        "was_blocked":         page.detection.get("is_blocked", False),
        "detection_type":      page.detection.get("page_type", "UNKNOWN"),
        "detection_score":     page.detection.get("score", 0),
        "elapsed_seconds":     page.elapsed,
        "html_size_bytes":     len(page.html),
        "word_count":          len(text.split()),
        "markdown_length":     len(markdown),
        "error":               page.error,
        "session_key":         page.session_key,
        "protection_type":     page.protection_type,
        "engine_decision":     page.engine_decision.to_dict() if page.engine_decision else None,
        "attempt_trace":       page.attempt_trace.to_dict() if page.attempt_trace else None,
        "extraction_metrics":  extraction_metrics,
    }
    (folder / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return folder


def main():
    parser = argparse.ArgumentParser(
        description="WebScroll — Stealth Web Extraction Pipeline",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--site",        type=str,             help="Direct URL to fetch or BFS-crawl")
    parser.add_argument("--search_text",  type=str, default=None, help="Web text search query (fetches top results)")
    parser.add_argument("--search_news",  type=str, default=None, help="News search query (fetches top news URLs)")
    parser.add_argument("--search_topk",  type=int, default=20,   help="Max search results to fetch (default: 20)")
    parser.add_argument("--stealth",      action="store_true",  help="Use stealth browser orchestrator")
    parser.add_argument("--crawl",        action="store_true",  help="BFS crawl the site from --site")
    parser.add_argument("--max-pages",    type=int, default=100, help="Max pages to crawl (default: 100)")
    parser.add_argument("--max-depth",    type=int, default=3,   help="Max BFS depth (default: 3)")
    parser.add_argument("--delay",        type=float, default=1.5, help="Seconds between crawl requests")
    parser.add_argument("--output",       type=str, default="storage/extracted", help="Output directory")

    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Validate: must provide at least one input mode
    # -------------------------------------------------------------------------
    if not args.site and not args.search_text and not args.search_news:
        print("Error: provide --site, --search_text, or --search_news")
        parser.print_help()
        sys.exit(1)

    storage_path = Path(args.output)

    # Build orchestrator (shared across all modes)
    orchestrator = StrategyOrchestrator(
        max_pages   = args.max_pages,
        max_depth   = args.max_depth,
        crawl_delay = args.delay,
    )

    # Real-time save callback
    saved_count = [0]
    def on_page(page: PageResult):
        folder = save_page(page, storage_path)
        saved_count[0] += 1
        print(
            f"  [{saved_count[0]:>4}] depth={page.depth} | "
            f"{len(page.html):>8} bytes | {page.driver_used:<12} | {page.url[:70]}"
        )

    # =========================================================================
    # MODE 1: --search_text or --search_news
    # =========================================================================
    if args.search_text or args.search_news:
        mode  = "text" if args.search_text else "news"
        query = args.search_text or args.search_news
        top_k = args.search_topk

        print(f"\n🔍 Search mode: {mode.upper()}")
        print(f"   Query    : {query}")
        print(f"   Top-K    : {top_k}")
        print(f"   Output   : {storage_path}\n")

        # Step 1 — run search
        search_results = run_search(query, mode=mode, top_k=top_k)
        urls = extract_urls(search_results)

        if not urls:
            print("❌ No URLs returned from search.")
            sys.exit(1)

        print(f"✅ Search returned {len(urls)} URLs. Fetching...\n")
        all_results = []

        for url in urls:
            try:
                results = orchestrator.run(url=url, crawl=False, on_page=on_page)
                all_results.extend(results)
            except KeyboardInterrupt:
                print("\n⏹ Interrupted.")
                break
            except Exception as e:
                print(f"  ⚠️  {url[:60]} — {e}")

    # =========================================================================
    # MODE 2: --site (single page or BFS crawl)
    # =========================================================================
    else:
        url   = args.site
        crawl = args.crawl

        # For crawl mode: create a dedicated session folder so all pages
        # from this run are grouped together instead of dumped flat.
        if crawl:
            session_storage = _make_crawl_session_folder(url, storage_path)
        else:
            session_storage = storage_path

        print(f"\n🚀 WebScroll starting")
        print(f"   URL       : {url}")
        print(f"   Mode      : {'BFS Crawl' if crawl else 'Single Page'}")
        if crawl:
            print(f"   Max pages : {args.max_pages}")
            print(f"   Max depth : {args.max_depth}")
            print(f"   Session   : {session_storage}")
        print(f"   Output    : {storage_path}\n")

        # Update the on_page callback to write into session_storage
        saved_count[0] = 0
        def on_page(page: PageResult):  # noqa: F811
            folder = save_page(page, session_storage)
            saved_count[0] += 1
            print(
                f"  [{saved_count[0]:>4}] depth={page.depth} | "
                f"{len(page.html):>8} bytes | {page.driver_used:<12} | {page.url[:70]}"
            )

        try:
            all_results = orchestrator.run(url=url, crawl=crawl, on_page=on_page)
        except KeyboardInterrupt:
            print("\n⏹ Crawl interrupted.")
            sys.exit(0)
        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            sys.exit(1)

    # =========================================================================
    # Summary
    # =========================================================================
    success = [r for r in all_results if r.is_success()]
    print(f"\n{'='*60}")
    print(f"✅ Done — {len(success)}/{len(all_results)} pages successfully extracted")
    print(f"   Output: {storage_path.resolve()}")
    if success:
        avg_size = sum(len(r.html) for r in success) / len(success)
        print(f"   Avg page size: {avg_size:,.0f} bytes")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
