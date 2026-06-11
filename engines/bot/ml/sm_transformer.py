"""
engines/profiler_engine/ml/sm_transformer.py

Layer 3 ML Fallback (Highest Accuracy): Sentence-Transformer classifier.
Model: all-MiniLM-L6-v2

Why MiniLM over larger LLMs?
  - MiniLM is 80MB vs GPT-4's ~800GB
  - Inference ~5-20ms on CPU (vs seconds for LLM API)
  - Produces 384-dim semantic embeddings — captures meaning, not just keywords
  - "Cloudflare" in earnings report ≠ "Cloudflare" in challenge page
    MiniLM understands this semantic difference. Regex does not.
  - Only used when TF-IDF + FastText are ambiguous

Classes: NORMAL | CLOUDFLARE | CAPTCHA | BLOCKED | RATE_LIMIT | LOGIN | JS_REQUIRED | EMPTY

Usage:
    from engines.profiler_engine.ml.sm_transformer import TransformerClassifier
    clf = TransformerClassifier()
    clf.train(html_samples, labels)    # builds embeddings + trains head
    clf.save("models/miniml_clf.joblib")
    clf.load("models/miniml_clf.joblib")
    result = clf.predict(html)
"""
import re
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"   # 80MB, 384-dim, CPU-friendly
MAX_TEXT_CHARS = 512                # MiniLM max sequence (in chars before tokenisation)


def _extract_text(html: str) -> str:
    """
    Extract the most semantically meaningful text from HTML.
    MiniLM works on text — we want the content that semantically
    distinguishes a real page from a bot challenge page.
    """
    # Page title first (most discriminative for our use case)
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title_text = title.group(1).strip() if title else ""

    # Visible body text
    visible = re.sub(r"<[^>]+>", " ", html)
    visible = re.sub(r"\s+", " ", visible).strip()

    # Combine: title gets repeated to give it extra semantic weight
    combined = f"{title_text} {title_text} {visible}"
    return combined[:MAX_TEXT_CHARS]


class TransformerClassifier:
    """
    Semantic embedding classifier using all-MiniLM-L6-v2.
    Best for ambiguous pages where TF-IDF / FastText are uncertain.
    
    Architecture:
        HTML → text extraction → MiniLM embed (384-dim) → Logistic Regression head
    """
    BLOCKED_CLASSES = {"CLOUDFLARE", "CAPTCHA", "BLOCKED", "RATE_LIMIT", "EMPTY"}

    def __init__(self):
        self._embedder = None
        self._head = None       # Logistic Regression head trained on top of embeddings
        self._classes = None

    def _load_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[TransformerClassifier] Loading {MODEL_NAME}...")
                self._embedder = SentenceTransformer(MODEL_NAME)
                logger.info(f"[TransformerClassifier] {MODEL_NAME} ready.")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._embedder

    def train(self, html_samples: List[str], labels: List[str]):
        """
        Train the classification head on top of MiniLM embeddings.
        MiniLM is used as a frozen feature extractor.
        Only the LR head is trained.
        """
        try:
            from sklearn.linear_model import LogisticRegression
            import numpy as np
        except ImportError:
            raise ImportError("Run: pip install scikit-learn")

        embedder = self._load_embedder()

        logger.info(f"[TransformerClassifier] Generating embeddings for {len(html_samples)} samples...")
        texts = [_extract_text(h) for h in html_samples]
        embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=32)

        self._head = LogisticRegression(max_iter=500, C=1.0, class_weight="balanced")
        self._head.fit(embeddings, labels)
        self._classes = self._head.classes_
        logger.info("[TransformerClassifier] Classification head trained.")

    def save(self, path: str):
        """Persist only the LR head (MiniLM is reloaded from HuggingFace/cache)."""
        try:
            import joblib
        except ImportError:
            raise ImportError("Run: pip install joblib")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump({"head": self._head, "classes": self._classes}, path)
        logger.info(f"[TransformerClassifier] Head saved to {path}")

    def load(self, path: str):
        """Load the LR head. MiniLM embedder is loaded lazily."""
        try:
            import joblib
        except ImportError:
            raise ImportError("Run: pip install joblib")
        data = joblib.load(path)
        self._head = data["head"]
        self._classes = data["classes"]
        logger.info(f"[TransformerClassifier] Head loaded from {path}")

    @classmethod
    def load_or_train(cls, model_path: str = "models/miniml_head.joblib", data_path=None) -> "TransformerClassifier":
        """
        Load the LR classification head from disk if it exists; otherwise train and save.
        The MiniLM embedder itself is always loaded from HuggingFace cache (cached locally after first download).
        """
        import os
        clf = cls()
        if os.path.exists(model_path):
            print(f"[TransformerClassifier] Loading cached head from {model_path}")
            clf.load(model_path)
        else:
            print(f"[TransformerClassifier] No cached head — training from data...")
            import sys
            from pathlib import Path
            root = str(Path(__file__).parents[3])
            if root not in sys.path:
                sys.path.insert(0, root)
            from engines.profiler_engine.ml.data.data_loader import load_train_data
            html_samples, labels = load_train_data(data_path)
            clf.train(html_samples, labels)
            clf.save(model_path)
        return clf

    def predict(self, html: str) -> Optional[Dict[str, Any]]:
        """Classify a single HTML string using semantic embeddings."""
        if not self._head:
            logger.warning("[TransformerClassifier] Head not loaded — skipping.")
            return None

        embedder = self._load_embedder()
        text = _extract_text(html)
        embedding = embedder.encode([text])

        proba = self._head.predict_proba(embedding)[0]
        best_idx = proba.argmax()
        page_type = str(self._classes[best_idx])  # cast from np.str_ → plain str
        confidence = float(proba[best_idx])

        # Lowered from 0.65 → 0.6 to avoid false negatives (e.g. 0.611 blocked confidence)
        is_blocked = page_type in self.BLOCKED_CLASSES and confidence > 0.6

        return {
            "is_blocked": is_blocked,
            "page_type": page_type,
            "confidence": round(confidence, 3),
            "reasons": [f"MiniLM transformer: {page_type} @ {confidence:.2f}"],
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

    clf = TransformerClassifier()
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