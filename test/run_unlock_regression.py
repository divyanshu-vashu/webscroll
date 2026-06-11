import json
from pathlib import Path

from engines.strategy_engine.orchestrator import StrategyOrchestrator


BASELINE_PATH = Path("test/fixtures/protected_sites_baseline.json")
OUTPUT_PATH = Path("storage/baselines/latest_unlock_regression.json")


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    orchestrator = StrategyOrchestrator()
    rows = []

    for item in baseline:
        url = item["url"]
        results = orchestrator.run(url=url, crawl=False)
        page = results[0]
        rows.append(
            {
                "url": url,
                "category": item.get("category"),
                "expected_unlock": item.get("expected_unlock"),
                "driver_used": page.driver_used,
                "html_size_bytes": len(page.html),
                "elapsed_seconds": page.elapsed,
                "detection_type": page.detection.get("page_type"),
                "detection_score": page.detection.get("score"),
                "success": page.is_success(),
                "usable_text_length": len(page.clean_text or ""),
                "protection_type": page.protection_type,
                "session_key": page.session_key,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote baseline report to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
