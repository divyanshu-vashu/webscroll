"""
engines/search/duckduck.py

DuckDuckGo search wrapper using the `ddgs` library.
Supports two search modes:
  - text : general web search (returns title, href, body)
  - news : news search (returns date, title, body, url, source)

Install: pip install ddgs
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def search_text(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
    """
    Web text search via DuckDuckGo.

    Args:
        query:  Search query string.
        top_k:  Max number of results to return (default: 20).

    Returns:
        List of dicts with keys: title, href, body
    """
    try:
        from ddgs import DDGS
    except ImportError:
        raise ImportError("Run: pip install ddgs")

    logger.info(f"[DuckDuckGo] text search: '{query}' top_k={top_k}")

    try:
        results = DDGS().text(
            query,
            region="us-en",
            safesearch="moderate",
            max_results=top_k,
            backend="auto",
        )
        logger.info(f"[DuckDuckGo] text search returned {len(results)} results")
        return results or []
    except Exception as e:
        logger.error(f"[DuckDuckGo] text search failed: {e}")
        return []


def search_news(query: str, top_k: int = 20) -> List[Dict[str, Any]]:
    """
    News search via DuckDuckGo.

    Args:
        query:  Search query string.
        top_k:  Max number of results to return (default: 20).

    Returns:
        List of dicts with keys: date, title, body, url, image, source
    """
    try:
        from ddgs import DDGS
    except ImportError:
        raise ImportError("Run: pip install ddgs")

    logger.info(f"[DuckDuckGo] news search: '{query}' top_k={top_k}")

    try:
        results = DDGS().news(
            query,
            region="us-en",
            safesearch="moderate",
            timelimit=None,     # No time filter — return all recency
            max_results=top_k,
            backend="auto",
        )
        logger.info(f"[DuckDuckGo] news search returned {len(results)} results")
        return results or []
    except Exception as e:
        logger.error(f"[DuckDuckGo] news search failed: {e}")
        return []



def main():
    import json

    print("\n=== TEXT SEARCH: 'open source latest llm model' ===")
    for r in search_text("open source latest llm model", top_k=5):
        print(f"  [{r.get('title','?')[:60]}]")
        print(f"   url : {r.get('href') or r.get('url','')}")
        print(f"   body: {r.get('body','')[:100]}")
        print()

    print("\n=== NEWS SEARCH: 'gaming software industry' ===")
    for r in search_news("gaming software industry", top_k=5):
        print(f"  [{r.get('title','?')[:60]}]")
        print(f"   url  : {r.get('url','')}")
        print(f"   date : {r.get('date','')}")
        print(f"   src  : {r.get('source','')}")
        print()

if __name__ == "__main__":
    main()