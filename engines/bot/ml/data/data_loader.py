"""
engines/profiler_engine/ml/data/data_loader.py

Loads and normalises training data from train.json.

Label Mapping (raw JSON → classifier class):
  bot_detected  → BLOCKED
  blocked       → BLOCKED
  normal        → NORMAL
  neutral       → NEUTRAL   (ambiguous pages — loading spinners, 404s, etc.)

Usage:
    from engines.profiler_engine.ml.data.data_loader import load_train_data
    html_samples, labels = load_train_data()
"""
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Canonical path to the training JSON
_DEFAULT_PATH = Path(__file__).parent / "train" / "train.json"

# Normalise raw JSON labels → classifier class strings
LABEL_MAP = {
    "bot_detected": "BLOCKED",
    "blocked":      "BLOCKED",
    "normal":       "NORMAL",
    "neutral":      "NEUTRAL",
}


def load_train_data(
    path: Optional[Path] = None,
    include_neutral: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Load training samples from train.json.

    Args:
        path:            Custom path to train.json (defaults to data/train/train.json).
        include_neutral: Whether to include NEUTRAL-labelled samples.
                         Set False for strict BLOCKED vs NORMAL binary classification.

    Returns:
        (html_samples, labels) — parallel lists ready for any classifier's .train()
    """
    target = Path(path) if path else _DEFAULT_PATH

    if not target.exists():
        raise FileNotFoundError(
            f"[DataLoader] train.json not found at {target}. "
            "Please create it or pass the correct path."
        )

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("train_html", [])

    html_samples: List[str] = []
    labels: List[str] = []
    skipped = 0

    for entry in entries:
        raw_label = entry.get("label", "").strip().lower()
        html = entry.get("html", "").strip()

        if not html or not raw_label:
            skipped += 1
            continue

        mapped = LABEL_MAP.get(raw_label)
        if mapped is None:
            logger.warning(f"[DataLoader] Unknown label '{raw_label}' — skipping.")
            skipped += 1
            continue

        if mapped == "NEUTRAL" and not include_neutral:
            continue

        html_samples.append(html)
        labels.append(mapped)

    # Count per class for visibility
    class_counts = {}
    for lbl in labels:
        class_counts[lbl] = class_counts.get(lbl, 0) + 1

    logger.info(
        f"[DataLoader] Loaded {len(html_samples)} samples "
        f"(skipped={skipped}) — {class_counts}"
    )
    print(
        f"[DataLoader] {len(html_samples)} samples — {class_counts}"
    )

    return html_samples, labels
