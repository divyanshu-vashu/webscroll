"""
engines/profiler_engine/bot_detector.py

Detection Pipeline:

  Layer 1: Size heuristic          (~0ms)
  Layer 2: Structural signal match (~1ms)  — HARD/SOFT two-tier scoring
  Layer 3: DOM heuristics          (~1ms)
  Layer 4: ML Ensemble             (~5-20ms, only called when rules are ambiguous)

ML ENSEMBLE CONSENSUS RULE (AND logic):
  - All 3 models run: TF-IDF, FastText, MiniLM Transformer
  - A page is marked BLOCKED only if ALL available models agree it's blocked
  - If ANY model returns is_blocked=False → treat as NORMAL content
  - This protects real market news/articles from being incorrectly blocked

FALSE POSITIVE PROTECTION:
  The word "cloudflare" alone scores 0.
  Only structural tokens (cf_chl_, challenge-platform, etc.) score hard points.
  SOFT signals (brand words) only add score when hard signals already fired.
"""
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signature Database — Two-Tier: HARD + SOFT
# ---------------------------------------------------------------------------

HARD_SIGNALS = [
    # Cloudflare (structural tokens only — cannot appear in normal article text)
    (r"cf_chl_",                        "CLOUDFLARE", 50, "CF challenge JS token"),
    (r"challenge-platform",             "CLOUDFLARE", 50, "CF challenge-platform script"),
    (r"window\._cf_chl",               "CLOUDFLARE", 50, "CF challenge JS variable"),
    (r"cf-browser-verification",        "CLOUDFLARE", 45, "CF browser verification element"),
    (r"<title[^>]*>Attention Required", "CLOUDFLARE", 45, "CF Attention Required page title"),
    (r"DDoS protection by Cloudflare",  "CLOUDFLARE", 50, "CF DDoS protection banner"),
    (r"Checking your browser before",   "CLOUDFLARE", 45, "CF browser check message"),
    (r'name="cf-turnstile-response"',   "CLOUDFLARE", 50, "CF Turnstile form field"),
    (r"jschl-answer",                   "CLOUDFLARE", 50, "CF JS challenge answer field"),
    (r"__cf_bm",                        "CLOUDFLARE", 30, "CF bot management cookie"),

    # CAPTCHA (widget-level attributes — not article brand mentions)
    (r"g-recaptcha",                    "CAPTCHA", 55, "Google reCAPTCHA widget"),
    (r'class="h-captcha"',              "CAPTCHA", 55, "hCaptcha widget class"),
    (r"data-sitekey=",                  "CAPTCHA", 40, "CAPTCHA sitekey attribute"),
    (r'data-callback="onSubmit"',       "CAPTCHA", 35, "CAPTCHA submit callback"),
    (r"verify you are human",           "CAPTCHA", 50, "Human verification prompt"),
    (r"FunCaptcha",                     "CAPTCHA", 50, "Arkose FunCaptcha widget"),
    (r"robot check",                    "CAPTCHA", 40, "Robot check message"),

    # Anti-bot vendor SDKs (JS identifiers — not article text)
    (r"_perimeterx",                    "BLOCKED", 55, "PerimeterX anti-bot SDK"),
    (r"akamai-abck",                    "BLOCKED", 50, "Akamai bot manager cookie/JS"),
    (r"px-captcha",                     "BLOCKED", 50, "PerimeterX captcha widget"),
    (r'"dd":\{"cid"',                   "BLOCKED", 55, "DataDome JS object"),
    (r"Pardon Our Interruption",        "BLOCKED", 50, "Imperva/Incapsula block page"),

    # Access denied (title-specific to avoid false match on news)
    (r"<title[^>]*>Access Denied",      "BLOCKED", 50, "Access Denied page title"),
    (r"<title[^>]*>403 Forbidden",      "BLOCKED", 45, "403 Forbidden page title"),
    (r"automated queries",              "BLOCKED", 45, "Automated query detection"),
    (r"bot detected",                   "BLOCKED", 55, "Bot detected message"),
    (r"temporarily blocked",            "BLOCKED", 40, "Temporarily blocked message"),
    (r"request blocked",                "BLOCKED", 40, "Request blocked message"),

    # Rate limit
    (r"<title[^>]*>429",               "RATE_LIMIT", 55, "HTTP 429 page title"),
    (r"too many requests",              "RATE_LIMIT", 40, "Too many requests message"),

    # Login wall
    (r"sign in to continue",            "LOGIN", 45, "Sign-in gate message"),
    (r"login required",                 "LOGIN", 40, "Login required message"),
    (r"authentication required",        "LOGIN", 40, "Authentication required"),

    # JS required
    (r"enable javascript to continue",  "JS_REQUIRED", 45, "JS required message"),
    (r'<div id="root"></div>',          "JS_REQUIRED", 35, "Empty React root div"),
    (r'<div id="app"></div>',           "JS_REQUIRED", 30, "Empty Vue app div"),

    # Browser Network / Connection / DNS Errors (Chrome, Firefox, Safari)
    (r"dns_probe_finished",             "ERROR", 60, "Chrome DNS probe error"),
    (r"err_connection_refused",         "ERROR", 60, "Chrome connection refused error"),
    (r"err_name_not_resolved",          "ERROR", 60, "Chrome host resolution error"),
    (r"err_proxy_connection_failed",    "ERROR", 60, "Chrome proxy connection failed"),
    (r"err_internet_disconnected",      "ERROR", 60, "Chrome internet disconnected"),
    (r"server IP address could not be found", "ERROR", 60, "Chrome server address not found error"),
    (r"site can't be reached",          "ERROR", 60, "Browser offline/unreachable error"),
    (r'class="neterror"',               "ERROR", 60, "Chrome network error page class"),
    (r'id="main-frame-error"',          "ERROR", 60, "Chrome main frame error div"),
    (r'class="icon-offline"',           "ERROR", 60, "Chrome offline icon class"),
]

# Soft signals: brand/generic words that mean nothing alone.
# Only applied when hard_score >= SOFT_APPLY_MIN_HARD_SCORE.
SOFT_SIGNALS = [
    (r"\bcloudflare\b",     "CLOUDFLARE", 5,  "Cloudflare brand mention"),
    (r"\bcaptcha\b",        "CAPTCHA",    5,  "captcha word mention"),
    (r"\bdatadome\b",       "BLOCKED",    8,  "DataDome brand mention"),
    (r"\baccess denied\b",  "BLOCKED",    8,  "Access denied phrase"),
    (r"\bsecurity check\b", "BLOCKED",    5,  "Security check phrase"),
    (r"\brecaptcha\b",      "CAPTCHA",    5,  "reCAPTCHA mention"),
    (r"\bhcaptcha\b",       "CAPTCHA",    5,  "hCaptcha mention"),
    (r"\bunusual traffic\b","BLOCKED",    8,  "Unusual traffic mention"),
    (r"\brate.?limit\b",    "RATE_LIMIT", 8,  "Rate limit mention"),
]

MIN_REAL_PAGE_BYTES     = 5_000
SUSPICIOUS_PAGE_BYTES   = 20_000
SCORE_BLOCKED_THRESHOLD = 45   # Must score >= 45 to auto-block (raised to cut false positives)
SCORE_SUSPICIOUS_THRESHOLD = 20  # 20-44 → ambiguous → call ML ensemble
SOFT_APPLY_MIN_HARD_SCORE = 25   # Soft signals only count when hard signals already fired


# ---------------------------------------------------------------------------
# ML Ensemble helper
# ---------------------------------------------------------------------------

def _run_ml_ensemble(
    html: str,
    url: str,
    tfidf_clf,
    fasttext_clf,
    transformer_clf
) -> Optional[Dict[str, Any]]:
    """
    Run all 3 ML classifiers and apply AND consensus logic:
      - BLOCKED only if ALL available models agree is_blocked=True
      - If ANY model says False (content) → return NORMAL immediately

    This makes the ensemble extremely conservative — it will never
    incorrectly block a page that any one model considers real content.
    """
    results = []
    model_labels = []

    # Collect predictions from each available model
    for clf, name in [
        (tfidf_clf,       "TF-IDF"),
        (fasttext_clf,    "FastText"),
        (transformer_clf, "MiniLM"),
    ]:
        if clf is None:
            continue
        try:
            pred = clf.predict(html)
            if pred is None:
                continue
            results.append(pred)
            model_labels.append(
                f"{name}: {pred['page_type']} ({pred['confidence']:.2f})"
            )
            logger.debug(f"[ML:{name}] {pred['page_type']} confidence={pred['confidence']:.2f}")
        except Exception as e:
            logger.warning(f"[ML:{name}] prediction error: {e}")

    if not results:
        logger.debug("[ML Ensemble] No models available, skipping.")
        return None

    # AND logic: if any model says NOT blocked → it's content, pass through
    any_says_normal = any(not r["is_blocked"] for r in results)
    if any_says_normal:
        logger.info(
            f"[ML Ensemble] ✅ At least one model says NORMAL — treating as content. "
            f"Votes: {model_labels}"
        )
        return {
            "is_blocked": False,
            "page_type": "NORMAL",
            "confidence": max(r["confidence"] for r in results if not r["is_blocked"]),
            "reasons": [f"ML ensemble (AND rule): content confirmed — {m}" for m in model_labels],
            "score": 0,
        }

    # All models agree it's blocked — consensus block
    # Use the most common page_type among them
    from collections import Counter
    type_counts = Counter(r["page_type"] for r in results)
    dominant_type = type_counts.most_common(1)[0][0]
    avg_confidence = sum(r["confidence"] for r in results) / len(results)

    logger.warning(
        f"[ML Ensemble] 🚫 ALL {len(results)} models agree BLOCKED — "
        f"type={dominant_type}, avg_confidence={avg_confidence:.2f}, "
        f"votes={model_labels}, url={url}"
    )
    return {
        "is_blocked": True,
        "page_type": dominant_type,
        "confidence": round(avg_confidence, 3),
        "reasons": [f"ML ensemble (AND rule): all models blocked — {m}" for m in model_labels],
        "score": int(avg_confidence * 100),
    }


# ---------------------------------------------------------------------------
# BotDetector
# ---------------------------------------------------------------------------

class BotDetector:
    """
    Context-aware, false-positive-safe bot-page detector.

    Scoring:
      HARD signals: structural tokens impossible in normal articles.
      SOFT signals: brand words, only add weight if hard signals fired.
      ML Ensemble:  AND logic — all 3 models must agree to block.

    Accepts optional pre-loaded ML classifiers for the ensemble layer.
    If no classifiers are passed, ambiguous pages are marked SUSPICIOUS
    but NOT blocked (safe default — better to let a bot page through
    than to block real content).
    """

    def __init__(
        self,
        tfidf_clf=None,
        fasttext_clf=None,
        transformer_clf=None,
    ):
        """
        Args:
            tfidf_clf:       Loaded TfIdfClassifier instance (or None)
            fasttext_clf:    Loaded FastTextClassifier instance (or None)
            transformer_clf: Loaded TransformerClassifier instance (or None)
        """
        self.tfidf_clf = tfidf_clf
        self.fasttext_clf = fasttext_clf
        self.transformer_clf = transformer_clf
        self._ml_available = any([tfidf_clf, fasttext_clf, transformer_clf])

    def detect(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Classify an HTML response. Returns:
        {
            "is_blocked": bool,
            "page_type":  str,    # NORMAL | CLOUDFLARE | CAPTCHA | BLOCKED | ...
            "confidence": float,
            "reasons":    list[str],
            "score":      int,
        }
        """
        html_len = len(html)

        # Fast path for truly empty pages
        if html_len < 100:
            return self._build("EMPTY", 100, 1.0, ["HTML < 100 bytes (empty)"])

        score = 0
        hard_score = 0
        reasons: List[str] = []
        type_scores: Dict[str, int] = {}

        # -------------------------------------------------------------------
        # LAYER 1: Size Heuristic
        # -------------------------------------------------------------------
        if html_len < MIN_REAL_PAGE_BYTES:
            delta = 25
            score += delta; hard_score += delta
            reasons.append(f"HTML very small ({html_len} bytes)")
            type_scores["BLOCKED"] = type_scores.get("BLOCKED", 0) + delta

        # -------------------------------------------------------------------
        # LAYER 2a: HARD Signal Matching
        # -------------------------------------------------------------------
        for pattern, ptype, weight, label in HARD_SIGNALS:
            if re.search(pattern, html, re.IGNORECASE):
                score += weight; hard_score += weight
                reasons.append(label)
                type_scores[ptype] = type_scores.get(ptype, 0) + weight

        # -------------------------------------------------------------------
        # LAYER 2b: SOFT Signals (only when hard signals confirmed something)
        # -------------------------------------------------------------------
        if hard_score >= SOFT_APPLY_MIN_HARD_SCORE:
            for pattern, ptype, weight, label in SOFT_SIGNALS:
                if re.search(pattern, html, re.IGNORECASE):
                    score += weight
                    reasons.append(label)
                    type_scores[ptype] = type_scores.get(ptype, 0) + weight

        # -------------------------------------------------------------------
        # LAYER 3: DOM Heuristics
        # -------------------------------------------------------------------
        tag_count = html.count("<")
        if tag_count < 20 and html_len < SUSPICIOUS_PAGE_BYTES:
            delta = 20
            score += delta; hard_score += delta
            reasons.append(f"Sparse DOM (~{tag_count} tags)")
            type_scores["BLOCKED"] = type_scores.get("BLOCKED", 0) + delta

        script_count = html.lower().count("<script")
        visible_chars = len(re.sub(r"<[^>]+>", "", html).strip())
        if script_count > 3 and visible_chars < 200:
            delta = 20
            score += delta; hard_score += delta
            reasons.append(f"High script/text ratio ({script_count} scripts, {visible_chars} chars)")
            type_scores["CLOUDFLARE"] = type_scores.get("CLOUDFLARE", 0) + delta

        # -------------------------------------------------------------------
        # LAYER 4: Decide
        # -------------------------------------------------------------------
        dominant_type = max(type_scores, key=type_scores.get) if type_scores else "NORMAL"
        confidence = min(score / 100.0, 1.0)

        # Clear block — no ML needed
        if score >= SCORE_BLOCKED_THRESHOLD:
            logger.warning(
                f"[BotDetector] RULE BLOCK — type={dominant_type}, score={score}, "
                f"url={url}, signals={reasons[:4]}"
            )
            return self._build(dominant_type, score, confidence, reasons)

        # Ambiguous zone — call ML ensemble
        if score >= SCORE_SUSPICIOUS_THRESHOLD:
            if self._ml_available:
                ml_result = _run_ml_ensemble(
                    html, url,
                    self.tfidf_clf, self.fasttext_clf, self.transformer_clf
                )
                if ml_result is not None:
                    return ml_result
            # No ML available → be conservative, let it through as SUSPICIOUS
            logger.info(f"[BotDetector] SUSPICIOUS (score={score}, no ML) — url={url}")
            return self._build("SUSPICIOUS", score, confidence, reasons)

        # Clean pass
        logger.debug(f"[BotDetector] NORMAL — score={score}, url={url}")
        return self._build("NORMAL", score, confidence, reasons)

    def _build(self, page_type: str, score: int, confidence: float, reasons: List[str]) -> Dict[str, Any]:
        return {
            "is_blocked": page_type not in ("NORMAL", "SUSPICIOUS"),
            "page_type":  page_type,
            "confidence": round(confidence, 3),
            "reasons":    reasons,
            "score":      score,
        }


# ---------------------------------------------------------------------------
# Factory — auto-loads cached models, trains if missing
# ---------------------------------------------------------------------------

def get_detector(
    tfidf_path:    str = "models/tfidf.joblib",
    fasttext_path: str = "models/fasttext.bin",
    miniml_path:   str = "models/miniml_head.joblib",
    use_ml:        bool = True
) -> BotDetector:
    """
    Returns a fully-armed BotDetector with all 3 ML models loaded.

    - If model files exist in models/ → loads them instantly (no retraining).
    - If model files are missing       → trains from train.json and saves to models/.

    Usage:
        from engines.profiler_engine.bot_detector import get_detector
        detector = get_detector()
        result = detector.detect(html, url="https://example.com")

    Args:
        tfidf_path:    Path to saved TF-IDF model (.joblib)
        fasttext_path: Path to saved FastText model (.bin)
        miniml_path:   Path to saved MiniLM head (.joblib)
        use_ml:        Set False to run rule-only mode (no ML, fastest)
    """
    if not use_ml:
        print("[get_detector] ML disabled — running rule-only mode.")
        return BotDetector()

    tfidf_clf    = None
    fasttext_clf = None
    transformer_clf = None

    try:
        from engines.profiler_engine.ml.tf_idf import TfIdfClassifier
        tfidf_clf = TfIdfClassifier.load_or_train(tfidf_path)
    except Exception as e:
        logger.warning(f"[get_detector] TF-IDF load/train failed: {e}")

    try:
        from engines.profiler_engine.ml.fasttext_classifier import FastTextClassifier
        fasttext_clf = FastTextClassifier.load_or_train(fasttext_path)
    except Exception as e:
        logger.warning(f"[get_detector] FastText load/train failed: {e}")

    try:
        from engines.profiler_engine.ml.sm_transformer import TransformerClassifier
        transformer_clf = TransformerClassifier.load_or_train(miniml_path)
    except Exception as e:
        logger.warning(f"[get_detector] MiniLM load/train failed: {e}")

    loaded = [n for n, c in [("TF-IDF", tfidf_clf), ("FastText", fasttext_clf), ("MiniLM", transformer_clf)] if c]
    print(f"[get_detector] Ready — ML models loaded: {loaded}")

    return BotDetector(
        tfidf_clf=tfidf_clf,
        fasttext_clf=fasttext_clf,
        transformer_clf=transformer_clf,
    )
