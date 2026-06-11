"""
engines/crawel/crawel_detection.py

Link extraction engine — given a fetched HTML page and its origin URL,
extracts all navigable internal links and returns them as a normalised
list of fully-qualified absolute URLs.

Design decisions:
  - selectolax (Lexbor backend) — 25x faster than BeautifulSoup for this task
  - Falls back to regex if selectolax is not installed
  - Normalises relative paths → absolute URLs (href="/about" → https://domain.com/about)
  - Deduplicates within the page (cross-page dedup is handled by the BFS visited set)
  - Stays on the same domain by default (configurable)
  - Strips anchors (#section), query strings are preserved
  - Skips mailto:, tel:, javascript:, data: hrefs
  - Skips binary file extensions (.pdf, .zip, .png, etc.)

Usage:
    from engines.crawel.crawel_detection import extract_links
    links = extract_links(html, base_url="https://example.com/news/article-1")
"""
import re
import logging
from typing import List, Optional
from urllib.parse import urlparse, urljoin, urlunparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# File extensions to skip — these are not crawlable HTML pages
SKIP_EXTENSIONS = {
    ".pdf", ".zip", ".gz", ".tar", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".mp4", ".mp3", ".avi", ".mov", ".webm",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".css", ".js", ".json", ".xml", ".rss", ".atom",
    ".woff", ".woff2", ".ttf", ".eot",
}

# URI schemes that are not HTTP(S) navigable
SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp", "sftp", "blob"}


def _is_valid_url(href: str) -> bool:
    """Return True if this href is worth adding to the crawl queue."""
    if not href or len(href) > 2048:
        return False
    scheme = href.split(":")[0].lower()
    if scheme in SKIP_SCHEMES:
        return False
    # Skip anchors only
    if href.startswith("#"):
        return False
    return True


def _normalize(href: str, base_url: str) -> Optional[str]:
    """
    Convert any href (relative or absolute) to a clean absolute URL.
    - Resolves relative paths relative to base_url
    - Strips fragments (#section)
    - Returns None if the result is not a valid http/https URL
    """
    try:
        absolute = urljoin(base_url, href.strip())
        parsed = urlparse(absolute)

        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            return None

        # Strip fragment
        clean = urlunparse(parsed._replace(fragment=""))

        # Skip binary extensions
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
            return None

        return clean
    except Exception:
        return None


def _same_domain(url: str, base_url: str) -> bool:
    """Check if url belongs to the same registered domain as base_url."""
    try:
        base_host = urlparse(base_url).netloc.lower().lstrip("www.")
        url_host  = urlparse(url).netloc.lower().lstrip("www.")
        return url_host == base_host or url_host.endswith("." + base_host)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Extraction — selectolax (fast) with regex fallback
# ---------------------------------------------------------------------------

def _extract_hrefs_selectolax(html: str) -> List[str]:
    """Use selectolax Lexbor parser — fastest HTML parser available."""
    from selectolax.lexbor import LexborHTMLParser
    parser = LexborHTMLParser(html)
    hrefs = []
    for node in parser.css("a[href]"):
        href = node.attributes.get("href", "")
        if href:
            hrefs.append(href)
    return hrefs


def _extract_hrefs_regex(html: str) -> List[str]:
    """Regex fallback — slower but zero dependencies."""
    return re.findall(r'href=["\']([^"\'#\s][^"\']*)["\']', html, re.IGNORECASE)


def extract_links(
    html: str,
    base_url: str,
    same_domain_only: bool = True,
    max_links: int = 500,
) -> List[str]:
    """
    Extract all navigable links from an HTML page.

    Args:
        html:             Raw HTML string of the fetched page.
        base_url:         The URL this HTML was fetched from (used to resolve relative hrefs).
        same_domain_only: If True, only return links to the same domain as base_url.
        max_links:        Hard cap on returned links (avoids link-bomb pages).

    Returns:
        Deduplicated list of absolute URLs, ready to enqueue in the BFS crawler.
    """
    if not html or not base_url:
        return []

    # --- Extract raw hrefs ---
    try:
        raw_hrefs = _extract_hrefs_selectolax(html)
        logger.debug(f"[LinkExtractor] selectolax extracted {len(raw_hrefs)} hrefs")
    except ImportError:
        logger.debug("[LinkExtractor] selectolax not available, falling back to regex")
        raw_hrefs = _extract_hrefs_regex(html)
    except Exception as e:
        logger.warning(f"[LinkExtractor] selectolax error: {e} — falling back to regex")
        raw_hrefs = _extract_hrefs_regex(html)

    # --- Filter, normalise, deduplicate ---
    seen = set()
    result = []

    for href in raw_hrefs:
        if not _is_valid_url(href):
            continue

        absolute = _normalize(href, base_url)
        if absolute is None:
            continue

        if same_domain_only and not _same_domain(absolute, base_url):
            continue

        if absolute in seen:
            continue

        seen.add(absolute)
        result.append(absolute)

        if len(result) >= max_links:
            logger.warning(
                f"[LinkExtractor] Hit max_links={max_links} cap for {base_url} — "
                f"truncating. Consider reducing crawl depth."
            )
            break

    logger.info(
        f"[LinkExtractor] {base_url} → {len(result)} unique links "
        f"(same_domain={same_domain_only})"
    )
    return result