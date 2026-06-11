from engines.text_engine.extraction_pipeline import ExtractionResult, extract_content


def clean_html_to_text(html_content: str, base_url: str = "", mode: str = "balanced") -> str:
    """Backward-compatible text extraction wrapper."""
    return extract_content(html_content, base_url=base_url, mode=mode).clean_text


def extract_html_bundle(html_content: str, base_url: str = "", mode: str = "balanced") -> ExtractionResult:
    """Return normalized HTML, clean text, and Markdown in one pass."""
    return extract_content(html_content, base_url=base_url, mode=mode)
