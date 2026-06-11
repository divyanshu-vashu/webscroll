from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    from lxml import html as lxml_html
    from lxml import etree
except Exception:  # pragma: no cover - optional dependency
    lxml_html = None
    etree = None

try:
    from markdownify import markdownify as html_to_markdown
except Exception:  # pragma: no cover - optional dependency
    html_to_markdown = None

try:
    from readability import Document
except Exception:  # pragma: no cover - optional dependency
    Document = None


NOISE_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "header", "footer", "nav", "aside"}
NOISE_HINTS = (
    "cookie",
    "consent",
    "newsletter",
    "modal",
    "popup",
    "social",
    "breadcrumb",
    "related",
    "recommend",
    "promo",
)
PRODUCT_HINTS = ("price", "sku", "spec", "product", "buy", "cart", "availability")
PRESERVE_ATTRS = (
    "data-ph-at-job-title-text",
    "data-ph-at-job-id-text",
    "data-ph-at-job-seqno-text",
    "data-ph-at-id",
    "itemprop",
)
PRESERVE_DATA_IDS = {
    "job-link",
    "jobdescription-text",
    "apply-link",
    "pagination-page-number-link",
}


@dataclass
class ExtractionResult:
    raw_html: str
    normalized_html: str
    clean_text: str
    markdown: str
    metrics: Dict[str, object] = field(default_factory=dict)


def _looks_like_product(text: str) -> bool:
    lowered = text.lower()
    return sum(1 for hint in PRODUCT_HINTS if hint in lowered) >= 2


def _is_preserved_tag(tag) -> bool:
    if tag.name == "a" and tag.get("href"):
        return True
    if tag.get("data-ph-at-id") in PRESERVE_DATA_IDS:
        return True
    return any(tag.get(attr) for attr in PRESERVE_ATTRS)


def _remove_noise_bs4(soup: BeautifulSoup) -> None:
    for tag in list(soup.find_all(True)):
        if tag.name in NOISE_TAGS:
            tag.decompose()
            continue
        if _is_preserved_tag(tag):
            continue
        if tag.attrs is None:
            continue
        class_attr = tag.get("class", [])
        if isinstance(class_attr, str):
            class_list = [class_attr]
        elif isinstance(class_attr, list):
            class_list = class_attr
        else:
            class_list = []
        attrs = " ".join(
            [
                " ".join(class_list),
                tag.get("id", "") or "",
                tag.get("role", "") or "",
                tag.get("aria-label", "") or "",
            ]
        ).lower()
        if any(hint in attrs for hint in NOISE_HINTS):
            tag.decompose()


def _normalize_links_and_images(soup: BeautifulSoup, base_url: str) -> None:
    for link in soup.find_all("a", href=True):
        link["href"] = urljoin(base_url, link["href"])
        title = (link.get("data-ph-at-job-title-text") or "").strip()
        if title and not link.get_text(strip=True):
            link.string = title
    for image in soup.find_all("img"):
        if image.get("srcset"):
            best_src = None
            best_score = -1.0
            for item in image.get("srcset", "").split(","):
                parts = item.strip().split()
                if not parts:
                    continue
                candidate = parts[0]
                descriptor = parts[1] if len(parts) > 1 else "1x"
                score = 1.0
                if descriptor.endswith("w"):
                    try:
                        score = float(descriptor[:-1])
                    except ValueError:
                        score = 1.0
                elif descriptor.endswith("x"):
                    try:
                        score = float(descriptor[:-1]) * 1000
                    except ValueError:
                        score = 1.0
                if score > best_score:
                    best_score = score
                    best_src = candidate
            if best_src:
                image["src"] = urljoin(base_url, best_src)
        if image.get("src"):
            image["src"] = urljoin(base_url, image["src"])


def _prune_repeated_low_text_blocks(soup: BeautifulSoup) -> None:
    signatures = Counter()
    tag_map = []
    for tag in soup.find_all(True):
        if tag.attrs is None:
            continue
        children = tuple(child.name for child in tag.find_all(recursive=False) if getattr(child, "name", None))
        class_attr = tag.get("class", [])
        if isinstance(class_attr, str):
            class_list = [class_attr]
        elif isinstance(class_attr, list):
            class_list = class_attr
        else:
            class_list = []
        class_names = tuple(sorted(class_list)[:3])
        signature = (tag.name, class_names, children[:4])
        text_len = len(tag.get_text(" ", strip=True))
        signatures[(signature, min(text_len // 20, 6))] += 1
        tag_map.append((tag, signature, text_len))

    for tag, signature, text_len in tag_map:
        if _is_preserved_tag(tag):
            continue
        bucket = (signature, min(text_len // 20, 6))
        if signatures[bucket] >= 4 and text_len < 120:
            tag.decompose()


def _apply_readability_if_useful(html_content: str, current_html: str, current_text: str) -> str:
    if Document is None:
        return current_html
    if _looks_like_product(current_text):
        return current_html
    try:
        summary_html = Document(html_content).summary(html_partial=True)
        if len(summary_html) > max(400, len(current_html) // 3):
            return summary_html
    except Exception:
        return current_html
    return current_html


def extract_content(html_content: str, base_url: str = "", mode: str = "balanced") -> ExtractionResult:
    if not html_content:
        return ExtractionResult(raw_html="", normalized_html="", clean_text="", markdown="", metrics={"mode": mode})

    soup = BeautifulSoup(html_content, "lxml" if lxml_html is not None else "html.parser")
    _remove_noise_bs4(soup)
    _normalize_links_and_images(soup, base_url)
    _prune_repeated_low_text_blocks(soup)

    normalized_html = str(soup)
    initial_text = soup.get_text("\n", strip=True)
    normalized_html = _apply_readability_if_useful(html_content, normalized_html, initial_text)

    clean_soup = BeautifulSoup(normalized_html, "html.parser")
    for link in clean_soup.find_all("a", href=True):
        link_text = link.get_text(strip=True)
        link_href = link["href"]
        if link_text and link_href and not link_href.startswith("javascript:"):
            link.replace_with(f" {link_text} ({link_href}) ")

    clean_text = re.sub(r"\n{3,}", "\n\n", clean_soup.get_text("\n", strip=True)).strip()

    markdown = clean_text
    if html_to_markdown is not None:
        try:
            markdown = html_to_markdown(
                normalized_html,
                heading_style="ATX",
                bullets="-",
                escape_asterisks=False,
                escape_underscores=False,
            ).strip()
        except Exception:
            markdown = clean_text

    return ExtractionResult(
        raw_html=html_content,
        normalized_html=normalized_html,
        clean_text=clean_text,
        markdown=markdown,
        metrics={
            "mode": mode,
            "text_length": len(clean_text),
            "markdown_length": len(markdown),
            "normalized_html_length": len(normalized_html),
        },
    )
