from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BrowserSessionState:
    session_key: str
    domain: str
    browser_profile_dir: str
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    viewport_family: str = "desktop"
    proxy_affinity: Optional[str] = None
    trust_score: float = 0.5
    last_challenge_at: Optional[str] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    local_storage: Dict[str, str] = field(default_factory=dict)
    burned: bool = False
    last_driver: Optional[str] = None
    attempt_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, object]) -> "BrowserSessionState":
        return cls(**raw)


class JsonSessionStore:
    def __init__(self, path: str = "storage/browser_sessions.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, BrowserSessionState] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            self._cache = {
                session_key: BrowserSessionState.from_dict(payload)
                for session_key, payload in raw.items()
            }
        self._loaded = True

    def _save(self) -> None:
        self.path.write_text(
            json.dumps({key: state.to_dict() for key, state in self._cache.items()}, indent=2),
            encoding="utf-8",
        )

    def get_or_create(
        self,
        *,
        domain: str,
        session_key: Optional[str],
        profile_dir: str,
        locale: str,
        timezone_id: str,
        viewport_family: str,
    ) -> BrowserSessionState:
        self._load()
        key = session_key or domain.replace(".", "_")
        state = self._cache.get(key)
        if state is None or state.burned:
            state = BrowserSessionState(
                session_key=key,
                domain=domain,
                browser_profile_dir=profile_dir,
                locale=locale,
                timezone_id=timezone_id,
                viewport_family=viewport_family,
            )
            self._cache[key] = state
            self._save()
        return state

    def mark_success(self, session_key: str, driver_name: str) -> Optional[BrowserSessionState]:
        self._load()
        state = self._cache.get(session_key)
        if state is None:
            return None
        state.attempt_count += 1
        state.success_count += 1
        state.last_driver = driver_name
        state.trust_score = min(1.0, round(state.trust_score + 0.1, 3))
        state.touch()
        self._save()
        return state

    def mark_blocked(self, session_key: str, driver_name: str, *, burn: bool = False) -> Optional[BrowserSessionState]:
        self._load()
        state = self._cache.get(session_key)
        if state is None:
            return None
        state.attempt_count += 1
        state.failure_count += 1
        state.last_driver = driver_name
        state.last_challenge_at = _utc_now()
        state.trust_score = max(0.0, round(state.trust_score - 0.15, 3))
        state.burned = burn
        state.touch()
        self._save()
        return state

    def set_proxy_affinity(self, session_key: str, proxy_id: Optional[str]) -> Optional[BrowserSessionState]:
        self._load()
        state = self._cache.get(session_key)
        if state is None:
            return None
        state.proxy_affinity = proxy_id
        state.touch()
        self._save()
        return state
