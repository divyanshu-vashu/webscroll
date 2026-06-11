"""
engines/search/search_engine.py

Search engine facade — wraps DuckDuckGo (and future providers).
Two modes:
  search_text(query, top_k)  → web search results
  search_news(query, top_k)  → news results
"""
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Allow running as a script directly (webscroll/ must be in sys.path)
_ROOT = str(Path(__file__).parents[2])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engines.search.duckduck import search_text, search_news

logger = logging.getLogger(__name__)


def run_search(
    query: str,
    mode: str,          # "text" | "news"
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """
    Unified search entry point.

    Args:
        query:  Search query string.
        mode:   "text" for web search, "news" for news search.
        top_k:  Max results (default: 20).

    Returns:
        List of result dicts. Each dict always contains a "url"/"href" key
        that can be passed to the orchestrator.
    """
    mode = mode.strip().lower()

    if mode == "text":
        results = search_text(query, top_k=top_k)
        # Normalise key: text() returns "href", rename to "url" for consistency
        for r in results:
            if "href" in r and "url" not in r:
                r["url"] = r["href"]
        return results

    elif mode == "news":
        return search_news(query, top_k=top_k)

    else:
        raise ValueError(f"Unknown search mode '{mode}'. Use 'text' or 'news'.")


def extract_urls(results: List[Dict[str, Any]]) -> List[str]:
    """
    Pull just the URLs out of a search result list.
    Works for both text (href/url key) and news (url key) results.
    """
    urls = []
    for r in results:
        url = r.get("url") or r.get("href", "")
        if url and url.startswith("http"):
            urls.append(url)
    return urls


if __name__ == "__main__":
    # ── TEXT search test ──────────────────────────────────────────
    print("\n=== TEXT SEARCH: 'open source LLM model' ===")
    text_results = run_search("open source LLM model", mode="text", top_k=5)
    text_urls    = extract_urls(text_results)
    for r in text_results:
        print(f"  {r.get('title','')[:60]}")
        print(f"  url : {r.get('url') or r.get('href','')}")
        print(f"  body: {r.get('body','')[:100]}")
        print()
    print(f"  → {len(text_urls)} URLs extracted: {text_urls}\n")

    # ── NEWS search test ──────────────────────────────────────────
    print("=== NEWS SEARCH: 'gaming software industry' ===")
    news_results = run_search("gaming software industry", mode="news", top_k=5)
    news_urls    = extract_urls(news_results)
    for r in news_results:
        print(f"  {r.get('title','')[:60]}")
        print(f"  url  : {r.get('url','')}")
        print(f"  date : {r.get('date','')[:19]}  src: {r.get('source','')}")
        print()
    print(f"  → {len(news_urls)} URLs extracted: {news_urls}\n")
