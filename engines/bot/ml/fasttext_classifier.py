"""
engines/profiler_engine/ml/fasttext_classifier.py

Layer 2 ML Fallback: FastText subword classifier.

Why FastText over standard embeddings for this task?
Anti-bot pages contain fragmented, rare tokens:
  - cf_chl_seq
  - recaptcha-token
  - jschl-answer
  - cf-ray
  - akamai-abck
  - datadome
  - _perimeterx

These are: rare, fragmented, non-dictionary tokens.
Normal word embeddings fail here. FastText handles them via
SUBWORD n-grams — it recognises "cf_chl" even if the full token
was never seen during training.

Classes: NORMAL | CLOUDFLARE | CAPTCHA | BLOCKED | RATE_LIMIT | LOGIN | JS_REQUIRED | EMPTY

Usage:
    from engines.profiler_engine.ml.fasttext_classifier import FastTextClassifier
    clf = FastTextClassifier()
    clf.train("data/train.txt")          # FastText format file
    clf.save("models/fasttext.bin")
    clf.load("models/fasttext.bin")
    result = clf.predict(html_string)

Training file format (one sample per line):
    __label__CLOUDFLARE  cf_chl_ challenge-platform Attention Required
    __label__NORMAL  Product available buy now add to cart
"""
import re
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# NumPy 2.x compatibility shim for fasttext
# fasttext internally calls np.array(probs, copy=False) which raises
# ValueError in NumPy 2.0+. We patch it before fasttext ever imports numpy.
# ---------------------------------------------------------------------------
try:
    import numpy as _np
    if int(_np.__version__.split(".")[0]) >= 2:
        _orig_np_array = _np.array
        def _compat_np_array(obj, *args, **kwargs):
            kwargs.pop("copy", None)  # strip the incompatible kwarg
            return _orig_np_array(obj, *args, **kwargs)
        _np.array = _compat_np_array
except Exception:
    pass

logger = logging.getLogger(__name__)


def _extract_features(html: str) -> str:
    """
    Extract a compact feature string suitable for FastText subword learning.
    We emphasise the anti-bot tokens that subword models handle best.
    """
    parts = []

    # Page title
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title:
        parts.append(title.group(1).strip()[:80])

    # Visible text (stripped of HTML tags)
    visible = re.sub(r"<[^>]+>", " ", html)
    visible = re.sub(r"\s+", " ", visible).strip()[:800]
    parts.append(visible)

    # Anti-bot structural tokens — include AS-IS so FastText learns subwords
    # E.g., "cf_chl_seq" → subwords: cf, _chl, _seq, cf_chl, etc.
    anti_bot_tokens = re.findall(
        r"(cf_chl_\w*|challenge-platform|cf-browser-verification|"
        r"g-recaptcha|hcaptcha|data-sitekey|jschl-answer|cf-ray|"
        r"akamai-abck|_perimeterx|datadome|px-captcha|__cf_bm|"
        r"cf-turnstile-response)",
        html, re.IGNORECASE
    )
    if anti_bot_tokens:
        parts.extend(anti_bot_tokens)

    # Page size bucket
    size = len(html)
    if size < 5000:
        parts.append("SIZE_TINY")
    elif size < 20000:
        parts.append("SIZE_SMALL")
    else:
        parts.append("SIZE_LARGE")

    return " ".join(parts).lower()


class FastTextClassifier:
    """
    FastText subword text classifier for HTML page classification.
    Handles fragmented anti-bot token patterns that standard embeddings miss.
    Model size: typically 5-30MB. Inference: <1ms.
    """
    BLOCKED_CLASSES = {"cloudflare", "captcha", "blocked", "rate_limit", "empty"}

    def __init__(self):
        self._model = None

    def train(self, html_samples: List[str], labels: List[str], model_path: str = "models/fasttext.bin"):
        """
        Train a FastText classifier from raw HTML samples and string labels.
        """
        try:
            import fasttext
        except ImportError:
            logger.error("[FastTextClassifier] fasttext not installed. Run: pip install fasttext-wheel")
            raise

        # Write FastText-format training file to a temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for html, label in zip(html_samples, labels):
                text = _extract_features(html)
                f.write(f"__label__{label.upper()}  {text}\n")
            tmp_path = f.name

        self._model = fasttext.train_supervised(
            input=tmp_path,
            epoch=25,
            lr=0.5,
            wordNgrams=2,           # Bigrams help with paired tokens like "cf-ray"
            dim=100,
            minCount=1,
            loss="softmax"
        )
        os.unlink(tmp_path)

        os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
        self._model.save_model(model_path)
        logger.info(f"[FastTextClassifier] Model trained and saved to {model_path}")

    def save(self, path: str):
        if self._model:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._model.save_model(path)

    def load(self, path: str):
        try:
            import fasttext
        except ImportError:
            raise ImportError("Run: pip install fasttext-wheel")
        self._model = fasttext.load_model(path)
        logger.info(f"[FastTextClassifier] Model loaded from {path}")

    @classmethod
    def load_or_train(cls, model_path: str = "models/fasttext.bin", data_path=None) -> "FastTextClassifier":
        """
        Load model from disk if it exists; otherwise train from train.json and save.
        FastText saves as a single .bin — very fast to reload (~10ms).
        """
        import os
        clf = cls()
        if os.path.exists(model_path):
            print(f"[FastTextClassifier] Loading cached model from {model_path}")
            clf.load(model_path)
        else:
            print(f"[FastTextClassifier] No cached model — training from data...")
            import sys
            from pathlib import Path
            root = str(Path(__file__).parents[3])
            if root not in sys.path:
                sys.path.insert(0, root)
            from engines.profiler_engine.ml.data.data_loader import load_train_data
            html_samples, labels = load_train_data(data_path)
            clf.train(html_samples, labels, model_path=model_path)
        return clf

    def predict(self, html: str) -> Optional[Dict[str, Any]]:
        """Classify a single HTML string. Returns BotDetector-compatible result."""
        if not self._model:
            logger.warning("[FastTextClassifier] Model not loaded.")
            return None

        text = _extract_features(html)

        # Use list() to safely convert probs — avoids NumPy 2.x copy=False bug
        # in fasttext's internal np.array(probs, copy=False) call
        labels, probs = self._model.predict(text, k=1)
        probs = list(probs)  # detach from fasttext's internal numpy view

        raw_label = labels[0].replace("__label__", "")
        page_type = raw_label.upper()
        confidence = float(probs[0])

        is_blocked = page_type.lower() in self.BLOCKED_CLASSES and confidence > 0.6

        return {
            "is_blocked": is_blocked,
            "page_type": page_type,
            "confidence": round(confidence, 3),
            "reasons": [f"FastText classifier: {page_type} @ {confidence:.2f}"],
            "score": int(confidence * 100),
        }


# Allow running this file directly as a script (adds webscroll/ to sys.path)
import sys as _sys
from pathlib import Path as _Path
_PROJECT_ROOT = str(_Path(__file__).parents[3])  # webscroll/
if _PROJECT_ROOT not in _sys.path:
    _sys.path.insert(0, _PROJECT_ROOT)
from engines.profiler_engine.ml.data.data_loader import load_train_data


def main():
    """Train on train.json and test two edge-case pages."""
    html_samples, labels = load_train_data()

    clf = FastTextClassifier()
    clf.train(html_samples, labels)

    print("\n--- Test 1: Real Cloudflare challenge page ---")
    result = clf.predict(
        "<title>Attention Required! | Cloudflare</title>"
        "<body>cf_chl_ challenge-platform window._cf_chl jschl-answer DDoS protection</body>"
    )
    print(result)

    print("\n--- Test 2: Normal market news mentioning Cloudflare brand ---")
    result = clf.predict(
        "<title>Cloudflare Q3 Earnings Beat | Reuters</title>"
        "<body>Cloudflare stock NET rose 12 percent after earnings beat. Revenue guidance raised."
        " Enterprise customer additions strong. CEO comments on AI opportunity.</body>"
    )
    print(result)

    print("\n--- Test 3: DataDome block ---")
    result = clf.predict(
        "<title>Verify you are human</title>"
        "<body><div id='datadome-wrapper'><iframe src='https://geo.captcha-delivery.com/captcha/'>datadome</iframe></div></body>"
    )
    print(result)

if __name__ == '__main__':
    main()