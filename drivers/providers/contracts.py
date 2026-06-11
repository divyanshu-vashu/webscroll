from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class ProxyLease:
    proxy_id: str
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    sticky_key: Optional[str] = None

    def to_driver_proxy(self) -> Dict[str, str]:
        payload = {"server": self.server}
        if self.username:
            payload["username"] = self.username
        if self.password:
            payload["password"] = self.password
        return payload

    def to_dict(self) -> Dict[str, Optional[str]]:
        return asdict(self)


class ProxyProvider(ABC):
    @abstractmethod
    def lease(self, *, domain: str, session_key: Optional[str], policy: str) -> Optional[ProxyLease]:
        raise NotImplementedError

    @abstractmethod
    def mark_good(self, lease: ProxyLease) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_bad(self, lease: ProxyLease, reason: str) -> None:
        raise NotImplementedError


class CaptchaProvider(ABC):
    @abstractmethod
    def solve(self, *, vendor: str, context: Dict[str, object]) -> Optional[str]:
        raise NotImplementedError


class NullProxyProvider(ProxyProvider):
    def lease(self, *, domain: str, session_key: Optional[str], policy: str) -> Optional[ProxyLease]:
        return None

    def mark_good(self, lease: ProxyLease) -> None:
        return None

    def mark_bad(self, lease: ProxyLease, reason: str) -> None:
        return None


class NullCaptchaProvider(CaptchaProvider):
    def solve(self, *, vendor: str, context: Dict[str, object]) -> Optional[str]:
        return None
