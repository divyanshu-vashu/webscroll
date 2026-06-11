from engines.text_engine.extraction_pipeline import extract_content


def normalize_html(html_content: str, base_url: str = "", mode: str = "balanced") -> str:
    return extract_content(html_content, base_url=base_url, mode=mode).normalized_html
