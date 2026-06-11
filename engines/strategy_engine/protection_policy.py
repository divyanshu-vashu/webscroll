from __future__ import annotations

from typing import Dict, Iterable, Optional

from engines.strategy_engine.models import ProtectionSignal


POLICY_TABLE = {
    "ALLOW": "allow",
    "SOFT_CHALLENGE_WAIT": "reuse_session_wait",
    "INTERACTIVE_CHALLENGE": "force_selenium_interaction",
    "HARD_BLOCK": "fallback_or_rotate",
    "RATE_LIMIT": "burn_proxy_retry_later",
    "LOGIN_WALL": "stop_requires_auth",
    "BROKEN_PROXY": "burn_proxy_keep_session",
    "JS_REQUIRED": "disable_http_temporarily",
    "EMPTY": "retry_or_fallback_browser",
}


def _find_vendor(*parts: Iterable[str]) -> Optional[str]:
    joined = " ".join(
        fragment.lower()
        for group in parts
        for fragment in (group if isinstance(group, (list, tuple)) else [group])
        if fragment
    )
    vendor_map = {
        "cloudflare": "Cloudflare",
        "datadome": "DataDome",
        "akamai": "Akamai",
        "perimeterx": "PerimeterX",
        "imperva": "Imperva",
        "incapsula": "Imperva",
        "turnstile": "Cloudflare",
        "captcha": "CAPTCHA",
    }
    for needle, vendor in vendor_map.items():
        if needle in joined:
            return vendor
    return None


def classify_protection(detection: Dict[str, object], html: str = "") -> ProtectionSignal:
    page_type = str(detection.get("page_type", "NORMAL") or "NORMAL").upper()
    reasons = [str(reason) for reason in detection.get("reasons", [])]
    confidence = float(detection.get("confidence", 0.0) or 0.0)
    vendor = _find_vendor(page_type, reasons, html[:500])
    lowered = " ".join(reasons).lower()

    if not html.strip():
        kind = "EMPTY"
    elif page_type in {"NORMAL", "SUSPICIOUS"} and not detection.get("is_blocked", False):
        kind = "ALLOW"
    elif page_type == "ERROR" and any(token in lowered for token in ("proxy", "dns", "connection", "offline")):
        kind = "BROKEN_PROXY"
    elif page_type == "RATE_LIMIT":
        kind = "RATE_LIMIT"
    elif page_type == "LOGIN":
        kind = "LOGIN_WALL"
    elif page_type == "JS_REQUIRED":
        kind = "JS_REQUIRED"
    elif page_type in {"CLOUDFLARE", "CAPTCHA"}:
        if any(token in lowered for token in ("turnstile", "captcha", "verification", "checking your browser")):
            kind = "INTERACTIVE_CHALLENGE"
        else:
            kind = "SOFT_CHALLENGE_WAIT"
    elif detection.get("is_blocked", False):
        kind = "HARD_BLOCK"
    else:
        kind = "ALLOW"

    return ProtectionSignal(
        kind=kind,
        vendor=vendor,
        confidence=confidence,
        reasons=reasons,
        recommended_next_step=POLICY_TABLE.get(kind, "allow"),
    )
