from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Optional

from engines.strategy_engine.models import DomainAccessProfile, EngineDecision, ScrapeRequest


MIN_HTTP_TEXT_LEN = 500
MIN_HTTP_TRUST_BROWSER_SUCCESSES = 2
MIN_SIMILARITY_FOR_HTTP_TRUST = 0.75


def text_similarity(left: str, right: str) -> Optional[float]:
    left = (left or "").strip()
    right = (right or "").strip()
    if not left or not right:
        return None
    return round(difflib.SequenceMatcher(a=left[:20_000], b=right[:20_000]).ratio(), 4)


@dataclass
class ProbeEvaluation:
    accepted: bool
    reason: str
    similarity: Optional[float] = None
    grant_http_trust: bool = False


class UnlockFirstEnginePicker:
    def decide(self, request: ScrapeRequest, profile: DomainAccessProfile) -> EngineDecision:
        if request.unlock_strategy != "unlock_first":
            return EngineDecision(path="browser", reason="unlock strategy override", domain_state_version=profile.version)

        if not request.allow_http_probe:
            return EngineDecision(path="browser", reason="HTTP probe disabled by request", domain_state_version=profile.version)

        if profile.http_trust:
            return EngineDecision(path="http_probe", reason="domain previously earned HTTP trust", domain_state_version=profile.version)

        if profile.browser_success_count >= MIN_HTTP_TRUST_BROWSER_SUCCESSES and profile.browser_reference_text:
            return EngineDecision(
                path="http_probe_trial",
                reason="domain has repeated browser successes and can be trialed via HTTP",
                domain_state_version=profile.version,
            )

        return EngineDecision(
            path="browser",
            reason="unknown or untrusted domain stays on browser waterfall",
            domain_state_version=profile.version,
        )

    def evaluate_http_probe(
        self,
        *,
        probe_text: str,
        reference_text: str,
        is_blocked: bool,
        is_js_required: bool,
    ) -> ProbeEvaluation:
        if is_blocked:
            return ProbeEvaluation(accepted=False, reason="HTTP probe was blocked", similarity=None)
        if is_js_required:
            return ProbeEvaluation(accepted=False, reason="HTTP probe indicates JavaScript is required", similarity=None)
        if len((probe_text or "").strip()) < MIN_HTTP_TEXT_LEN:
            return ProbeEvaluation(accepted=False, reason="HTTP probe text too small to trust", similarity=None)

        similarity = text_similarity(probe_text, reference_text)
        if similarity is None:
            return ProbeEvaluation(
                accepted=True,
                reason="HTTP probe usable but there is no browser reference text yet",
                similarity=None,
                grant_http_trust=False,
            )
        if similarity < MIN_SIMILARITY_FOR_HTTP_TRUST:
            return ProbeEvaluation(
                accepted=False,
                reason=f"HTTP probe diverged from browser reference ({similarity:.2f})",
                similarity=similarity,
                grant_http_trust=False,
            )
        return ProbeEvaluation(
            accepted=True,
            reason=f"HTTP probe matched browser reference ({similarity:.2f})",
            similarity=similarity,
            grant_http_trust=True,
        )
