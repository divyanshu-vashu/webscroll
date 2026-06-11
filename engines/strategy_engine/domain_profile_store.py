from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from engines.strategy_engine.models import DomainAccessProfile


class DomainProfileStore:
    def __init__(self, path: str = "storage/domain_access_profiles.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, DomainAccessProfile] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            self._cache = {
                domain: DomainAccessProfile.from_dict(payload)
                for domain, payload in raw.items()
            }
        self._loaded = True

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(
                {domain: profile.to_dict() for domain, profile in self._cache.items()},
                indent=2,
            ),
            encoding="utf-8",
        )

    def get(self, domain: str) -> DomainAccessProfile:
        self._load()
        if domain not in self._cache:
            self._cache[domain] = DomainAccessProfile(domain=domain)
        return self._cache[domain]

    def mark_success(
        self,
        *,
        domain: str,
        driver_name: str,
        session_key: Optional[str],
        preferred_path: str,
        vendor: Optional[str] = None,
        reference_text: str = "",
        similarity: Optional[float] = None,
        http_trust: Optional[bool] = None,
    ) -> DomainAccessProfile:
        profile = self.get(domain)
        profile.last_good_driver = driver_name
        profile.last_good_session = session_key
        profile.preferred_path = preferred_path
        profile.browser_success_count += 1 if driver_name != "http_probe" else 0
        profile.failure_count = max(profile.failure_count - 1, 0)
        profile.block_rate = self._compute_block_rate(profile)
        profile.add_vendor_hint(vendor)
        profile.add_similarity(similarity)
        if reference_text and driver_name != "http_probe":
            profile.browser_reference_text = reference_text[:12_000]
        if http_trust is not None:
            profile.http_trust = http_trust
        profile.touch()
        self._save()
        return profile

    def mark_failure(
        self,
        *,
        domain: str,
        vendor: Optional[str] = None,
        http_trust: Optional[bool] = None,
    ) -> DomainAccessProfile:
        profile = self.get(domain)
        profile.failure_count += 1
        profile.block_rate = self._compute_block_rate(profile)
        profile.add_vendor_hint(vendor)
        if http_trust is not None:
            profile.http_trust = http_trust
        profile.touch()
        self._save()
        return profile

    def _compute_block_rate(self, profile: DomainAccessProfile) -> float:
        total = profile.browser_success_count + profile.failure_count
        if total <= 0:
            return 0.0
        return round(profile.failure_count / total, 3)
