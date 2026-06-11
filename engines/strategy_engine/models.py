from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PageAction:
    kind: str
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout_ms: int = 5_000
    optional: bool = False
    notes: str = ""
    max_iterations: int = 10
    wait_ms: int = 1_500
    scroll_step_px: int = 800

    @classmethod
    def from_any(cls, raw: Any) -> "PageAction":
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, dict):
            return cls(
                kind=str(raw.get("kind", "")).strip(),
                selector=raw.get("selector"),
                value=raw.get("value"),
                timeout_ms=int(raw.get("timeout_ms", 5_000)),
                optional=bool(raw.get("optional", False)),
                notes=str(raw.get("notes", "")),
                max_iterations=int(raw.get("max_iterations", 10)),
                wait_ms=int(raw.get("wait_ms", raw.get("timeout_ms", 1_500))),
                scroll_step_px=int(raw.get("scroll_step_px", 800)),
            )
        raise TypeError(f"Unsupported page action payload: {type(raw)!r}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaginationConfig:
    type: str = ""
    param: Optional[str] = None
    step: int = 1
    max_pages: int = 20
    next_url: Optional[str] = None
    page_urls: List[str] = field(default_factory=list)
    pattern: Optional[str] = None
    offset_param: Optional[str] = None
    limit_param: Optional[str] = None
    limit_value: Optional[int] = None
    selector: Optional[str] = None
    mode: Optional[str] = None
    concurrent: bool = False
    max_workers: int = 3

    @classmethod
    def from_any(cls, raw: Any) -> Optional["PaginationConfig"]:
        if raw is None:
            return None
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, dict):
            return cls(
                type=str(raw.get("type", "")).strip(),
                param=raw.get("param"),
                step=int(raw.get("step", 1)),
                max_pages=int(raw.get("max_pages", 20)),
                next_url=raw.get("next_url"),
                page_urls=[str(url) for url in raw.get("page_urls", [])],
                pattern=raw.get("pattern"),
                offset_param=raw.get("offset_param"),
                limit_param=raw.get("limit_param"),
                limit_value=int(raw["limit_value"]) if raw.get("limit_value") is not None else None,
                selector=raw.get("selector"),
                mode=raw.get("mode"),
                concurrent=bool(raw.get("concurrent", False)),
                max_workers=int(raw.get("max_workers", 3)),
            )
        raise TypeError(f"Unsupported pagination payload: {type(raw)!r}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScrapeRequest:
    url: str
    crawl: bool = False
    actions: List[PageAction] = field(default_factory=list)
    session_key: Optional[str] = None
    allow_http_probe: bool = True
    proxy_policy: str = "sticky"
    extraction_mode: str = "balanced"
    unlock_strategy: str = "unlock_first"
    pagination_mode: bool = False
    pagination: Optional[PaginationConfig] = None
    stream_mode: bool = False

    @classmethod
    def from_any(
        cls,
        *,
        url: str,
        crawl: bool = False,
        request: Optional["ScrapeRequest"] = None,
        actions: Optional[List[Any]] = None,
        pagination_mode: Optional[bool] = None,
        pagination: Optional[Any] = None,
    ) -> "ScrapeRequest":
        if request is None:
            return cls(
                url=url,
                crawl=crawl,
                actions=[PageAction.from_any(a) for a in actions or []],
                pagination_mode=bool(pagination_mode) if pagination_mode is not None else False,
                pagination=PaginationConfig.from_any(pagination),
            )

        request.url = url
        request.crawl = crawl
        if actions is not None:
            request.actions = [PageAction.from_any(a) for a in actions]
        else:
            request.actions = [PageAction.from_any(a) for a in request.actions]
        if pagination_mode is not None:
            request.pagination_mode = bool(pagination_mode)
        if pagination is not None:
            request.pagination = PaginationConfig.from_any(pagination)
        return request

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["actions"] = [a.to_dict() for a in self.actions]
        payload["pagination"] = self.pagination.to_dict() if self.pagination else None
        return payload


@dataclass
class ProtectionSignal:
    kind: str
    vendor: Optional[str] = None
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    recommended_next_step: str = "allow"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EngineDecision:
    path: str
    reason: str
    domain_state_version: int = 0
    similarity_score: Optional[float] = None
    escalated_from: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AttemptResult:
    driver_name: str
    path: str
    elapsed: float
    html_size: int
    blocked: bool
    detection: Dict[str, Any] = field(default_factory=dict)
    protection_signal: Optional[ProtectionSignal] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    session_key: Optional[str] = None
    action_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        detection = dict(self.detection)
        if "html" in detection:
            detection["html_size"] = len(detection.get("html") or "")
            detection.pop("html", None)
        payload["detection"] = detection
        if self.protection_signal is not None:
            payload["protection_signal"] = self.protection_signal.to_dict()
        return payload


@dataclass
class AttemptTrace:
    started_at: str = field(default_factory=_utc_now)
    completed_at: Optional[str] = None
    attempts: List[AttemptResult] = field(default_factory=list)

    def add(self, attempt: AttemptResult) -> None:
        self.attempts.append(attempt)

    def finalize(self) -> None:
        self.completed_at = _utc_now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass
class DomainAccessProfile:
    domain: str
    preferred_path: str = "browser"
    last_good_driver: Optional[str] = None
    last_good_session: Optional[str] = None
    http_trust: bool = False
    block_rate: float = 0.0
    vendor_hints: List[str] = field(default_factory=list)
    notes: str = ""
    version: int = 0
    browser_success_count: int = 0
    failure_count: int = 0
    recent_similarity_scores: List[float] = field(default_factory=list)
    browser_reference_text: str = ""
    last_updated_at: str = field(default_factory=_utc_now)

    def add_vendor_hint(self, vendor: Optional[str]) -> None:
        if vendor and vendor not in self.vendor_hints:
            self.vendor_hints.append(vendor)

    def add_similarity(self, similarity: Optional[float]) -> None:
        if similarity is None:
            return
        self.recent_similarity_scores.append(round(float(similarity), 4))
        self.recent_similarity_scores = self.recent_similarity_scores[-10:]

    def touch(self) -> None:
        self.version += 1
        self.last_updated_at = _utc_now()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "DomainAccessProfile":
        return cls(**raw)


@dataclass
class PageResult:
    url: str
    html: str
    depth: int
    driver_used: str
    detection: Dict[str, Any]
    elapsed: float
    error: Optional[str] = None
    normalized_html: str = ""
    clean_text: str = ""
    markdown: str = ""
    attempt_trace: Optional[AttemptTrace] = None
    engine_decision: Optional[EngineDecision] = None
    session_key: Optional[str] = None
    protection_type: Optional[str] = None

    def is_success(self) -> bool:
        return bool(self.html) and not self.detection.get("is_blocked", True)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if self.attempt_trace is not None:
            payload["attempt_trace"] = self.attempt_trace.to_dict()
        if self.engine_decision is not None:
            payload["engine_decision"] = self.engine_decision.to_dict()
        return payload

    def __repr__(self) -> str:
        status = "OK" if self.is_success() else "FAIL"
        return (
            f"PageResult({status} depth={self.depth} driver={self.driver_used} "
            f"size={len(self.html)} url={self.url[:60]})"
        )
