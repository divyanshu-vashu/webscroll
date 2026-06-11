"""
engines/strategy_engine/orchestrator.py

Unlock-first orchestration around the current working browser waterfall.

Important invariants preserved:
  - SeleniumDriver remains the first and primary unlock path.
  - BROWSER_CLASSES ordering is unchanged.
  - Unknown domains stay browser-first.
  - HTTP probing is only allowed after a domain has earned enough trust.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from drivers.browser_clients.camoufox_driver import CamoufoxDriver
from drivers.browser_clients.cloak_browser import CloakBrowserDriver
from drivers.browser_clients.nodriver_client import NodriverClient
from drivers.browser_clients.patchright_driver import PatchrightDriver
from drivers.browser_clients.playwright_driver import PlaywrightDriver
from drivers.browser_clients.selenium_driver import SeleniumDriver
from drivers.http_clients.http_probe_client import HttpProbeClient
from drivers.identity.browserforge_manager import BrowserForgeManager
from drivers.providers.contracts import NullCaptchaProvider, NullProxyProvider, ProxyLease
from drivers.sessions.session_store import BrowserSessionState, JsonSessionStore
from engines.bot.bot_detector import BotDetector
from engines.crawel.crawel_detection import extract_links
from engines.strategy_engine.domain_profile_store import DomainProfileStore
from engines.strategy_engine.engine_picker import ProbeEvaluation, UnlockFirstEnginePicker
from engines.strategy_engine.models import (
    AttemptResult,
    AttemptTrace,
    DomainAccessProfile,
    EngineDecision,
    PageAction,
    PageResult,
    PaginationConfig,
    ScrapeRequest,
)
from engines.strategy_engine.protection_policy import classify_protection
from engines.text_engine.text_extractor import extract_html_bundle

logger = logging.getLogger(__name__)

DEFAULT_CRAWL_DELAY = 1.5
DEFAULT_MAX_PAGES = 200
DEFAULT_MAX_DEPTH = 3

identity_manager = BrowserForgeManager()

# Active browser pool.
# Order matters for waterfall: fastest/stealthiest first.
# SeleniumDriver uses SeleniumBase UC Mode (auto-manages chromedriver versions).
BROWSER_CLASSES = [CloakBrowserDriver, SeleniumDriver, NodriverClient, CamoufoxDriver]

NEXT_PAGINATION_SELECTORS = [
    "a[rel='next']",
    "link[rel='next']",
    "[aria-label='Next']",
    "[aria-label='Next page']",
    "button[aria-label*='Next']",
    "a[aria-label*='Next']",
    ".mat-paginator-navigation-next",
    "button.mat-paginator-navigation-next",
    "[class*='pagination'][class*='next']",
    "[class*='pager'][class*='next']",
    "[data-testid*='next']",
    "[data-cy*='next']",
    ".pagination__next",
    ".pagination-next",
    ".next-page",
    "a.next",
    "li.next > a",
    ".paginate_button.next",
]

LOAD_MORE_SELECTORS = [
    "button:contains('Load More')",
    "button:contains('Show More')",
    "button:contains('See More')",
    "a:contains('Load More')",
    "a:contains('Show More')",
    "[data-testid*='load-more']",
    "[data-cy*='load-more']",
    "[class*='load-more']",
]


def _base_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _viewport_family(profile: Dict[str, Any]) -> str:
    return "mobile" if profile.get("is_mobile") else "desktop"


@dataclass
class FetchContext:
    domain: str
    domain_profile: DomainAccessProfile
    session: BrowserSessionState
    identity_profile: Dict[str, Any]
    proxy_lease: Optional[ProxyLease]


class StrategyOrchestrator:
    """
    Unlock-first orchestrator that preserves the current sequential browser
    waterfall while adding:
      - request and trace models
      - sticky session trust
      - conservative HTTP probing
      - protection-policy aware routing
      - normalized HTML/text/Markdown extraction
    """

    def __init__(
        self,
        max_workers: int = 3,
        crawl_delay: float = DEFAULT_CRAWL_DELAY,
        max_pages: int = DEFAULT_MAX_PAGES,
        max_depth: int = DEFAULT_MAX_DEPTH,
        domain_profile_store: Optional[DomainProfileStore] = None,
        session_store: Optional[JsonSessionStore] = None,
    ):
        self.detector = BotDetector()
        self.max_workers = max_workers
        self.crawl_delay = crawl_delay
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.domain_profiles = domain_profile_store or DomainProfileStore()
        self.session_store = session_store or JsonSessionStore()
        self.proxy_provider = NullProxyProvider()
        self.captcha_provider = NullCaptchaProvider()
        self.http_probe = HttpProbeClient()
        self.engine_picker = UnlockFirstEnginePicker()

    def run(
        self,
        url: str,
        crawl: bool = False,
        on_page: Optional[Callable[[PageResult], None]] = None,
        request: Optional[ScrapeRequest] = None,
    ) -> List[PageResult]:
        request = ScrapeRequest.from_any(url=url, crawl=crawl, request=request)
        if request.crawl and request.pagination_mode:
            return self._crawl_with_pagination(seed_url=url, request=request, on_page=on_page)
        if request.pagination_mode:
            return self._run_pagination(url=url, request=request, on_page=on_page)
        if request.crawl:
            return self._bfs_crawl(seed_url=url, request=request, on_page=on_page)

        result = self._fetch_single(url, depth=0, request=request)
        if on_page and result.is_success():
            on_page(result)
        return [result]

    def _run_pagination(
        self,
        *,
        url: str,
        request: ScrapeRequest,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        configured = request.pagination
        pagination = PaginationConfig(
            type="auto",
            max_pages=configured.max_pages if configured else min(self.max_pages, 20),
        )
        return self._run_auto_pagination(url=url, request=request, pagination=pagination, on_page=on_page)

    def _crawl_with_pagination(
        self,
        *,
        seed_url: str,
        request: ScrapeRequest,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        pagination_request = ScrapeRequest(
            url=seed_url,
            crawl=False,
            actions=request.actions,
            session_key=request.session_key,
            allow_http_probe=request.allow_http_probe,
            proxy_policy=request.proxy_policy,
            extraction_mode=request.extraction_mode,
            unlock_strategy=request.unlock_strategy,
            pagination_mode=True,
            pagination=request.pagination,
            stream_mode=request.stream_mode,
        )
        pagination_pages = self._run_pagination(url=seed_url, request=pagination_request, on_page=on_page)
        visited_urls = {page.url for page in pagination_pages}
        remaining_capacity = max(self.max_pages - len(visited_urls), 0)
        if remaining_capacity <= 0:
            return pagination_pages

        bfs_request = ScrapeRequest(
            url=seed_url,
            crawl=True,
            actions=request.actions,
            session_key=request.session_key,
            allow_http_probe=request.allow_http_probe,
            proxy_policy=request.proxy_policy,
            extraction_mode=request.extraction_mode,
            unlock_strategy=request.unlock_strategy,
            pagination_mode=False,
            pagination=None,
            stream_mode=request.stream_mode,
        )
        bfs_pages = self._bfs_crawl(
            seed_url=seed_url,
            request=bfs_request,
            on_page=on_page,
            initial_pages=pagination_pages,
            visited_urls=visited_urls,
            remaining_capacity=remaining_capacity,
        )
        return pagination_pages + bfs_pages

    def _run_auto_pagination(
        self,
        *,
        url: str,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        detected_from_url = self._detect_pagination_from_url(url)
        if detected_from_url and detected_from_url.type in {"url_param", "offset_limit", "url_path"}:
            detected_from_url.max_pages = pagination.max_pages
            return self._run_url_pagination(
                url=url,
                request=request,
                pagination=detected_from_url,
                on_page=on_page,
            )

        first_page = self._fetch_single(url=url, depth=0, request=request)
        if not first_page.is_success():
            return [first_page]

        detected = self._detect_pagination_from_page(first_page=first_page, url=url, max_pages=pagination.max_pages)
        if not detected:
            if on_page:
                on_page(first_page)
                self._release_page_payload(first_page, request)
            return [first_page]

        if detected.type == "numbered_links":
            return self._continue_numbered_link_pagination(
                first_page=first_page,
                request=request,
                pagination=detected,
                on_page=on_page,
            )

        if detected.type == "url_list":
            return self._continue_url_list_pagination(
                first_page=first_page,
                request=request,
                pagination=detected,
                on_page=on_page,
            )

        if detected.type in {"url_param", "offset_limit", "url_path"}:
            return self._continue_url_pagination(
                first_page=first_page,
                request=request,
                pagination=detected,
                on_page=on_page,
            )

        if detected.type in {"click_append", "click_next", "scroll"}:
            action_request = self._request_with_detected_action(request=request, detected=detected)
            paged_result = self._fetch_single(url=url, depth=0, request=action_request)
            if on_page and paged_result.is_success():
                on_page(paged_result)
                self._release_page_payload(paged_result, action_request)
            return [paged_result]

        if on_page:
            on_page(first_page)
            self._release_page_payload(first_page, request)
        return [first_page]

    def _fetch_single(self, url: str, depth: int, request: ScrapeRequest) -> PageResult:
        self.crashed_drivers = set()
        start = time.time()
        trace = AttemptTrace()
        ctx = self._build_context(url, request)
        decision = self.engine_picker.decide(request, ctx.domain_profile)

        logger.info(
            "[Orchestrator] Starting fetch domain=%s path=%s session=%s reason=%s",
            ctx.domain,
            decision.path,
            ctx.session.session_key,
            decision.reason,
        )

        if decision.path in {"http_probe", "http_probe_trial"}:
            probe_result, probe_eval = self._attempt_http_probe(
                url=url,
                depth=depth,
                request=request,
                ctx=ctx,
                trace=trace,
                decision=decision,
                start_time=start,
            )
            if probe_result is not None:
                trace.finalize()
                probe_result.attempt_trace = trace
                return probe_result

            decision = EngineDecision(
                path="browser",
                reason=f"{decision.reason}; escalated after HTTP probe failure: {probe_eval.reason if probe_eval else 'unknown'}",
                domain_state_version=ctx.domain_profile.version,
                similarity_score=probe_eval.similarity if probe_eval else None,
                escalated_from=decision.path,
            )

        browser_result = self._run_primary_waterfall(
            url=url,
            depth=depth,
            request=request,
            ctx=ctx,
            trace=trace,
            decision=decision,
            start_time=start,
        )
        if browser_result is not None:
            trace.finalize()
            browser_result.attempt_trace = trace
            return browser_result

        logger.warning("[Orchestrator] Primary waterfall exhausted for %s. Entering permutation fallback.", url)
        fallback_result = self._permutation_fallback(
            url=url,
            depth=depth,
            request=request,
            ctx=ctx,
            trace=trace,
            decision=decision,
            start_time=start,
        )
        trace.finalize()
        fallback_result.attempt_trace = trace
        return fallback_result

    def _run_url_pagination(
        self,
        *,
        url: str,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        results: List[PageResult] = []
        visited_urls: set[str] = set()
        previous_hash: Optional[str] = None
        next_url: Optional[str] = url

        for index in range(max(1, pagination.max_pages)):
            if not next_url or next_url in visited_urls:
                break
            visited_urls.add(next_url)
            page = self._fetch_single(url=next_url, depth=index, request=request)
            if not page.is_success():
                results.append(page)
                break

            content_hash = self._content_hash(page.clean_text or page.normalized_html or page.html)
            results.append(page)
            if on_page:
                on_page(page)
                self._release_page_payload(page, request)

            if self._is_effectively_empty(page):
                break
            if content_hash == previous_hash:
                break
            previous_hash = content_hash

            next_url = self._next_pagination_url(current_url=next_url, pagination=pagination)
            if next_url and results:
                time.sleep(self.crawl_delay)

        return results

    def _continue_url_list_pagination(
        self,
        *,
        first_page: PageResult,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        results: List[PageResult] = [first_page]
        seen = {first_page.url}
        if on_page and first_page.is_success():
            on_page(first_page)
            self._release_page_payload(first_page, request)

        for index, link in enumerate(pagination.page_urls[: max(pagination.max_pages - 1, 0)], start=1):
            if link in seen:
                continue
            seen.add(link)
            time.sleep(self.crawl_delay)
            page = self._fetch_single(url=link, depth=index, request=request)
            results.append(page)
            if on_page and page.is_success():
                on_page(page)
                self._release_page_payload(page, request)
        return results

    def _continue_url_pagination(
        self,
        *,
        first_page: PageResult,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        results: List[PageResult] = [first_page]
        visited_urls: set[str] = {first_page.url}
        previous_hash = self._content_hash(first_page.clean_text or first_page.normalized_html or first_page.html)

        if on_page and first_page.is_success():
            on_page(first_page)
            self._release_page_payload(first_page, request)

        next_url = pagination.next_url or self._next_pagination_url(current_url=first_page.url, pagination=pagination)
        for index in range(1, max(1, pagination.max_pages)):
            if not next_url or next_url in visited_urls:
                break
            visited_urls.add(next_url)
            time.sleep(self.crawl_delay)
            page = self._fetch_single(url=next_url, depth=index, request=request)
            results.append(page)
            if not page.is_success():
                break

            content_hash = self._content_hash(page.clean_text or page.normalized_html or page.html)
            if on_page:
                on_page(page)
                self._release_page_payload(page, request)
            if self._is_effectively_empty(page) or content_hash == previous_hash:
                break
            previous_hash = content_hash
            next_url = self._next_pagination_url(current_url=next_url, pagination=pagination)

        return results

    def _run_numbered_link_pagination(
        self,
        *,
        url: str,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        first_page = self._fetch_single(url=url, depth=0, request=request)
        results: List[PageResult] = [first_page]
        if on_page and first_page.is_success():
            on_page(first_page)
            self._release_page_payload(first_page, request)
        if not first_page.is_success():
            return results

        link_urls = self._extract_numbered_links(first_page.normalized_html or first_page.html, base_url=url)
        seen = {url}
        for index, link in enumerate(link_urls, start=1):
            if index >= pagination.max_pages or link in seen:
                continue
            seen.add(link)
            time.sleep(self.crawl_delay)
            page = self._fetch_single(url=link, depth=index, request=request)
            results.append(page)
            if on_page and page.is_success():
                on_page(page)
                self._release_page_payload(page, request)
        return results

    def _continue_numbered_link_pagination(
        self,
        *,
        first_page: PageResult,
        request: ScrapeRequest,
        pagination: PaginationConfig,
        on_page: Optional[Callable[[PageResult], None]] = None,
    ) -> List[PageResult]:
        results: List[PageResult] = [first_page]
        if on_page and first_page.is_success():
            on_page(first_page)
            self._release_page_payload(first_page, request)

        link_urls = self._extract_numbered_links(first_page.normalized_html or first_page.html, base_url=first_page.url)
        seen = {first_page.url}
        for index, link in enumerate(link_urls, start=1):
            if index >= pagination.max_pages or link in seen:
                continue
            seen.add(link)
            time.sleep(self.crawl_delay)
            page = self._fetch_single(url=link, depth=index, request=request)
            results.append(page)
            if on_page and page.is_success():
                on_page(page)
                self._release_page_payload(page, request)
        return results

    def _build_context(self, url: str, request: ScrapeRequest) -> FetchContext:
        domain = _base_domain(url)
        domain_profile = self.domain_profiles.get(domain)
        seed_profile = identity_manager.generate_profile(locale="en-US")
        profile_root = os.path.abspath(os.path.join("storage", "profiles", domain))
        os.makedirs(profile_root, exist_ok=True)

        session = self.session_store.get_or_create(
            domain=domain,
            session_key=request.session_key,
            profile_dir=profile_root,
            locale=seed_profile.get("locale", "en-US"),
            timezone_id=seed_profile.get("timezone_id", "America/New_York"),
            viewport_family=_viewport_family(seed_profile),
        )

        proxy_lease = self.proxy_provider.lease(
            domain=domain,
            session_key=session.session_key,
            policy=request.proxy_policy,
        )
        if proxy_lease is not None:
            self.session_store.set_proxy_affinity(session.session_key, proxy_lease.proxy_id)

        identity_profile = {
            **seed_profile,
            "locale": session.locale,
            "timezone_id": session.timezone_id,
            "user_data_dir": session.browser_profile_dir,
        }
        if proxy_lease is not None:
            identity_profile["proxy"] = proxy_lease.to_driver_proxy()

        return FetchContext(
            domain=domain,
            domain_profile=domain_profile,
            session=session,
            identity_profile=identity_profile,
            proxy_lease=proxy_lease,
        )

    def _attempt_http_probe(
        self,
        *,
        url: str,
        depth: int,
        request: ScrapeRequest,
        ctx: FetchContext,
        trace: AttemptTrace,
        decision: EngineDecision,
        start_time: float,
    ) -> Tuple[Optional[PageResult], Optional[ProbeEvaluation]]:
        probe_start = time.time()
        response = self.http_probe.fetch(
            url,
            headers=ctx.identity_profile.get("headers", {}),
            proxy=ctx.proxy_lease.to_driver_proxy() if ctx.proxy_lease else None,
        )
        detection = self.detector.detect(response.text, url=url) if response.text else {
            "is_blocked": True,
            "page_type": "ERROR" if response.error else "EMPTY",
            "confidence": 1.0 if response.error else 0.0,
            "reasons": [response.error] if response.error else ["Empty HTTP probe response"],
            "score": 100 if response.error else 0,
        }
        signal = classify_protection(detection, response.text)
        extraction = extract_html_bundle(response.text, base_url=url, mode=request.extraction_mode)
        evaluation = self.engine_picker.evaluate_http_probe(
            probe_text=extraction.clean_text,
            reference_text=ctx.domain_profile.browser_reference_text,
            is_blocked=bool(response.error) or detection.get("is_blocked", False) or signal.kind != "ALLOW",
            is_js_required=signal.kind == "JS_REQUIRED",
        )
        trace.add(
            AttemptResult(
                driver_name="http_probe",
                path=decision.path,
                elapsed=round(time.time() - probe_start, 2),
                html_size=len(response.text),
                blocked=bool(response.error) or detection.get("is_blocked", False),
                detection=detection,
                protection_signal=signal,
                status_code=response.status_code,
                error=response.error if response.error else None,
                session_key=ctx.session.session_key,
                action_count=0,
            )
        )
        self._log_attempt(trace.attempts[-1], ctx.domain)

        if not evaluation.accepted:
            self.domain_profiles.mark_failure(
                domain=ctx.domain,
                vendor=signal.vendor,
                http_trust=False if signal.kind in {"JS_REQUIRED", "INTERACTIVE_CHALLENGE", "HARD_BLOCK"} else None,
            )
            if signal.kind == "BROKEN_PROXY" and ctx.proxy_lease is not None:
                self.proxy_provider.mark_bad(ctx.proxy_lease, reason="http_probe_broken_proxy")
            return None, evaluation

        self.session_store.mark_success(ctx.session.session_key, "http_probe")
        self.domain_profiles.mark_success(
            domain=ctx.domain,
            driver_name="http_probe",
            session_key=ctx.session.session_key,
            preferred_path="http_probe",
            vendor=signal.vendor,
            similarity=evaluation.similarity,
            http_trust=evaluation.grant_http_trust,
        )
        result = PageResult(
            url=url,
            html=response.text,
            depth=depth,
            driver_used="http_probe",
            detection=detection,
            elapsed=round(time.time() - start_time, 2),
            normalized_html=extraction.normalized_html,
            clean_text=extraction.clean_text,
            markdown=extraction.markdown,
            engine_decision=EngineDecision(
                path=decision.path,
                reason=evaluation.reason,
                domain_state_version=ctx.domain_profile.version,
                similarity_score=evaluation.similarity,
                escalated_from=decision.escalated_from,
            ),
            session_key=ctx.session.session_key,
            protection_type=signal.kind,
        )
        return result, evaluation

    def _run_primary_waterfall(
        self,
        *,
        url: str,
        depth: int,
        request: ScrapeRequest,
        ctx: FetchContext,
        trace: AttemptTrace,
        decision: EngineDecision,
        start_time: float,
    ) -> Optional[PageResult]:
        for driver_name, driver_cls, kwargs in self._primary_driver_tasks(url, ctx):
            attempt = self._fetch_with_driver(
                name=driver_name,
                cls=driver_cls,
                kwargs=kwargs,
                url=url,
                actions=request.actions,
                session_key=ctx.session.session_key,
                path="browser",
            )
            trace.add(attempt)
            self._log_attempt(attempt, ctx.domain)

            signal = attempt.protection_signal
            if signal and signal.kind == "BROKEN_PROXY" and ctx.proxy_lease is not None:
                self.proxy_provider.mark_bad(ctx.proxy_lease, reason=signal.kind)
            if signal and signal.kind in {"INTERACTIVE_CHALLENGE", "HARD_BLOCK", "RATE_LIMIT"}:
                self.domain_profiles.mark_failure(
                    domain=ctx.domain,
                    vendor=signal.vendor,
                    http_trust=False if signal.kind != "RATE_LIMIT" else None,
                )

            if not attempt.blocked and attempt.detection and attempt.detection.get("html"):
                page = self._build_success_page(
                    url=url,
                    depth=depth,
                    driver_name=driver_name,
                    html=attempt.detection["html"],
                    detection=attempt.detection,
                    request=request,
                    ctx=ctx,
                    decision=decision,
                    start_time=start_time,
                    similarity_score=None,
                    protection_type=signal.kind if signal else None,
                )
                return page

        return None

    def _primary_driver_tasks(self, url: str, ctx: FetchContext) -> List[Tuple[str, Any, Dict[str, Any]]]:
        base_profile = ctx.identity_profile
        profile_root = ctx.session.browser_profile_dir
        os.makedirs(profile_root, exist_ok=True)

        # Detect if we have an active display on Linux/WSL.
        # If no DISPLAY or WAYLAND_DISPLAY environment variable is present, we must run headlessly.
        import sys
        has_display = True
        if sys.platform.startswith("linux"):
            has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        
        force_headless = not has_display

        return [
            (
                "cloakbrowser",
                CloakBrowserDriver,
                {
                    "headless": force_headless,
                    "identity_profile": {**base_profile, "headless": force_headless},
                    "user_data_dir": os.path.join(profile_root, "cloakbrowser"),
                },
            ),
            (
                "seleniumbase",
                SeleniumDriver,
                {
                    "headless": force_headless,
                    "identity_profile": {**base_profile, "headless": force_headless},
                    "user_data_dir": os.path.join(profile_root, "seleniumbase"),
                },
            ),
            (
                "nodriver",
                NodriverClient,
                {
                    "headless": force_headless,
                    "identity_profile": {**base_profile, "headless": force_headless},
                    "user_data_dir": os.path.join(profile_root, "nodriver"),
                },
            ),
            (
                "camoufox",
                CamoufoxDriver,
                {
                    "headless": force_headless,
                    "proxy": ctx.proxy_lease.to_driver_proxy() if ctx.proxy_lease else None,
                    "user_data_dir": os.path.join(profile_root, "camoufox"),
                },
            ),
        ]

    def _fetch_with_driver(
        self,
        *,
        name: str,
        cls: Any,
        kwargs: Dict[str, Any],
        url: str,
        actions: Iterable[Any],
        session_key: Optional[str],
        path: str,
    ) -> AttemptResult:
        os.makedirs(kwargs.get("user_data_dir", ""), exist_ok=True)
        start = time.time()
        try:
            driver = cls(**kwargs)
            html = driver.fetch(url, actions=actions)
            detection = self.detector.detect(html, url=url)
            detection["html"] = html
        except Exception as exc:
            logger.error("[Orchestrator] %s fetch failed: %s", name, exc)
            self.crashed_drivers.add(cls)
            detection = {
                "is_blocked": True,
                "page_type": "ERROR",
                "confidence": 1.0,
                "reasons": [str(exc)],
                "score": 100,
                "html": "",
            }
        signal = classify_protection(detection, detection.get("html", ""))
        attempt = AttemptResult(
            driver_name=name,
            path=path,
            elapsed=round(time.time() - start, 2),
            html_size=len(detection.get("html", "")),
            blocked=detection.get("is_blocked", True),
            detection=detection,
            protection_signal=signal,
            error=None if detection.get("html") else "; ".join(detection.get("reasons", [])),
            session_key=session_key,
            action_count=len(list(actions or [])),
        )
        return attempt

    def _build_success_page(
        self,
        *,
        url: str,
        depth: int,
        driver_name: str,
        html: str,
        detection: Dict[str, Any],
        request: ScrapeRequest,
        ctx: FetchContext,
        decision: EngineDecision,
        start_time: float,
        similarity_score: Optional[float],
        protection_type: Optional[str],
    ) -> PageResult:
        extraction = extract_html_bundle(html, base_url=url, mode=request.extraction_mode)
        self.session_store.mark_success(ctx.session.session_key, driver_name)
        signal = classify_protection(detection, html)
        self.domain_profiles.mark_success(
            domain=ctx.domain,
            driver_name=driver_name,
            session_key=ctx.session.session_key,
            preferred_path="browser",
            vendor=signal.vendor,
            reference_text=extraction.clean_text,
            similarity=similarity_score,
        )
        if ctx.proxy_lease is not None:
            self.proxy_provider.mark_good(ctx.proxy_lease)

        return PageResult(
            url=url,
            html=html,
            depth=depth,
            driver_used=driver_name,
            detection=detection,
            elapsed=round(time.time() - start_time, 2),
            normalized_html=extraction.normalized_html,
            clean_text=extraction.clean_text,
            markdown=extraction.markdown,
            engine_decision=EngineDecision(
                path=decision.path,
                reason=decision.reason,
                domain_state_version=ctx.domain_profile.version,
                similarity_score=similarity_score,
                escalated_from=decision.escalated_from,
            ),
            session_key=ctx.session.session_key,
            protection_type=protection_type or signal.kind,
        )

    def _permutation_fallback(
        self,
        *,
        url: str,
        depth: int,
        request: ScrapeRequest,
        ctx: FetchContext,
        trace: AttemptTrace,
        decision: EngineDecision,
        start_time: float,
    ) -> PageResult:
        # Detect if we have an active display on Linux/WSL.
        import sys
        has_display = True
        if sys.platform.startswith("linux"):
            has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        
        force_headless = not has_display

        profiles = [
            identity_manager.generate_profile(locale=ctx.session.locale),
            identity_manager.generate_profile(locale="en-GB"),
            identity_manager.generate_profile(locale="en-IN"),
        ]
        profiles[0]["headless"] = True
        profiles[1]["headless"] = force_headless if force_headless else False
        profiles[2]["headless"] = force_headless if force_headless else False

        for index, (browser_cls, profile) in enumerate(
            (pair for pair in ((browser, profile) for browser in BROWSER_CLASSES for profile in profiles)),
            start=1,
        ):
            if browser_cls in self.crashed_drivers:
                continue
            driver_name = browser_cls.__name__
            profile_root = os.path.join(
                ctx.session.browser_profile_dir,
                driver_name.lower().replace("driver", "").replace("client", ""),
            )
            os.makedirs(profile_root, exist_ok=True)
            kwargs = {
                "headless": profile.get("headless", False),
                "user_data_dir": profile_root,
                "proxy": ctx.proxy_lease.to_driver_proxy() if ctx.proxy_lease else None,
            }
            if driver_name != "CamoufoxDriver":
                kwargs["identity_profile"] = {**ctx.identity_profile, **profile}

            attempt = self._fetch_with_driver(
                name=driver_name,
                cls=browser_cls,
                kwargs=kwargs,
                url=url,
                actions=request.actions,
                session_key=ctx.session.session_key,
                path=f"permutation_{index}",
            )
            trace.add(attempt)
            self._log_attempt(attempt, ctx.domain)
            signal = attempt.protection_signal
            if not attempt.blocked and attempt.detection.get("html"):
                return self._build_success_page(
                    url=url,
                    depth=depth,
                    driver_name=driver_name,
                    html=attempt.detection["html"],
                    detection=attempt.detection,
                    request=request,
                    ctx=ctx,
                    decision=EngineDecision(
                        path="browser_permutation",
                        reason=f"Primary waterfall failed; permutation {index} succeeded",
                        domain_state_version=ctx.domain_profile.version,
                        escalated_from=decision.path,
                    ),
                    start_time=start_time,
                    similarity_score=None,
                    protection_type=signal.kind if signal else None,
                )

        self.session_store.mark_blocked(ctx.session.session_key, "all_drivers", burn=False)
        final_detection = {
            "is_blocked": True,
            "page_type": "BLOCKED",
            "confidence": 1.0,
            "reasons": ["All browser permutations exhausted"],
            "score": 100,
        }
        return PageResult(
            url=url,
            html="",
            depth=depth,
            driver_used="none",
            detection=final_detection,
            elapsed=round(time.time() - start_time, 2),
            error="All permutations exhausted",
            engine_decision=EngineDecision(
                path="browser_permutation",
                reason="All browser permutations exhausted",
                domain_state_version=ctx.domain_profile.version,
                escalated_from=decision.path,
            ),
            session_key=ctx.session.session_key,
            protection_type="HARD_BLOCK",
        )

    def _log_attempt(self, attempt: AttemptResult, domain: str) -> None:
        logger.info(
            "[Attempt] %s",
            json.dumps(
                {
                    "domain": domain,
                    "driver": attempt.driver_name,
                    "path": attempt.path,
                    "session_key": attempt.session_key,
                    "blocked": attempt.blocked,
                    "html_size": attempt.html_size,
                    "elapsed": attempt.elapsed,
                    "protection": attempt.protection_signal.to_dict() if attempt.protection_signal else None,
                    "retry_count": max(0, len(attempt.detection.get("reasons", [])) - 1),
                    "action_count": attempt.action_count,
                }
            ),
        )

    def _bfs_crawl(
        self,
        *,
        seed_url: str,
        request: ScrapeRequest,
        on_page: Optional[Callable[[PageResult], None]] = None,
        initial_pages: Optional[List[PageResult]] = None,
        visited_urls: Optional[set] = None,
        remaining_capacity: Optional[int] = None,
    ) -> List[PageResult]:
        seed_domain = _base_domain(seed_url)
        queue: deque = deque()
        visited_urls = visited_urls or set()
        initial_pages = initial_pages or []
        results: List[PageResult] = []
        max_pages = remaining_capacity if remaining_capacity is not None else self.max_pages

        for page in initial_pages:
            if not page.is_success():
                continue
            if page.html:
                new_links = extract_links(
                    html=page.html,
                    base_url=page.url,
                    same_domain_only=True,
                    max_links=500,
                )
                for link in new_links:
                    if link in visited_urls:
                        continue
                    if _base_domain(link) != seed_domain:
                        continue
                    if len(results) + len(queue) >= max_pages:
                        break
                    visited_urls.add(link)
                    queue.append((link, page.depth + 1))

        if seed_url not in visited_urls:
            queue.append((seed_url, 0))
            visited_urls.add(seed_url)

        logger.info(
            "[Orchestrator] BFS crawl started seed=%s max_pages=%s max_depth=%s",
            seed_url,
            max_pages,
            self.max_depth,
        )

        while queue:
            if len(results) >= max_pages:
                logger.warning("[Orchestrator] max_pages=%s reached; stopping crawl.", max_pages)
                break

            url, depth = queue.popleft()
            if depth > self.max_depth:
                continue

            page = self._fetch_single(
                url=url,
                depth=depth,
                request=ScrapeRequest(
                    url=url,
                    crawl=False,
                    actions=request.actions,
                    session_key=request.session_key,
                    allow_http_probe=request.allow_http_probe,
                    proxy_policy=request.proxy_policy,
                    extraction_mode=request.extraction_mode,
                    unlock_strategy=request.unlock_strategy,
                    pagination_mode=request.pagination_mode,
                    pagination=request.pagination,
                    stream_mode=request.stream_mode,
                ),
            )

            if page.is_success():
                results.append(page)
                if on_page:
                    try:
                        on_page(page)
                        self._release_page_payload(page, request)
                    except Exception as exc:
                        logger.warning("[Orchestrator] on_page callback error: %s", exc)

                new_links = extract_links(
                    html=page.html,
                    base_url=url,
                    same_domain_only=True,
                    max_links=500,
                )
                for link in new_links:
                    if link in visited_urls:
                        continue
                    if _base_domain(link) != seed_domain:
                        continue
                    if len(results) + len(queue) >= max_pages:
                        break
                    visited_urls.add(link)
                    queue.append((link, depth + 1))
            if queue:
                time.sleep(self.crawl_delay)

        logger.info(
            "[Orchestrator] BFS crawl complete pages_fetched=%s urls_visited=%s seed=%s",
            len(results),
            len(visited_urls),
            seed_url,
        )
        return results

    def _release_page_payload(self, page: PageResult, request: ScrapeRequest) -> None:
        if not request.stream_mode:
            return
        page.html = ""
        page.normalized_html = ""

    def _is_effectively_empty(self, page: PageResult) -> bool:
        return len((page.clean_text or "").strip()) < 200

    def _content_hash(self, content: str) -> str:
        import hashlib
        return hashlib.sha256((content or "").encode("utf-8", errors="ignore")).hexdigest()

    def _next_pagination_url(self, *, current_url: str, pagination: PaginationConfig) -> Optional[str]:
        pagination_type = pagination.type.strip().lower()
        if pagination_type == "url_param":
            if not pagination.param:
                return None
            return self._update_query_param(current_url, pagination.param, pagination.step)
        if pagination_type == "offset_limit":
            if not pagination.offset_param:
                return None
            step = pagination.limit_value or pagination.step or 1
            next_url = self._update_query_param(current_url, pagination.offset_param, step)
            if pagination.limit_param and pagination.limit_value is not None:
                next_url = self._set_query_param(next_url, pagination.limit_param, pagination.limit_value)
            return next_url
        if pagination_type == "url_path":
            return self._increment_url_path(current_url, pagination.pattern)
        return None

    def _update_query_param(self, url: str, param: str, step: int) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        current = 1 if param.lower() in {"page", "p", "pg"} and param not in query else 0
        if query.get(param):
            try:
                current = int(query[param][-1])
            except (TypeError, ValueError):
                current = 0
        query[param] = [str(current + step)]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _set_query_param(self, url: str, param: str, value: int) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query[param] = [str(value)]
        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _increment_url_path(self, url: str, pattern: Optional[str]) -> Optional[str]:
        parsed = urlparse(url)
        path = parsed.path or ""

        new_path = re.sub(r"(/page/)(\d+)(/?$)", lambda m: f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}", path)
        if new_path != path:
            return urlunparse(parsed._replace(path=new_path))

        new_path = re.sub(r"(/p)(\d+)(/?$)", lambda m: f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}", path)
        if new_path != path:
            return urlunparse(parsed._replace(path=new_path))

        new_path = re.sub(r"-(\d+)(/?$)", lambda m: f"-{int(m.group(1)) + 1}{m.group(2)}", path)
        if new_path != path:
            return urlunparse(parsed._replace(path=new_path))

        if pattern and "{page}" in pattern:
            match = re.search(r"(\d+)(?!.*\d)", path)
            if match:
                next_page = int(match.group(1)) + 1
                start, end = match.span(1)
                new_path = f"{path[:start]}{next_page}{path[end:]}"
                return urlunparse(parsed._replace(path=new_path))
        return None

    def _extract_numbered_links(self, html: str, base_url: str) -> List[str]:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html or "", "html.parser")
            anchors = soup.select(
                "nav[aria-label*='pagination'] a[href], .pagination a[href], ol.page-list a[href], "
                "a[aria-label^='Page '][href], a[data-ph-at-id='pagination-page-number-link'][href], "
                "[class*='pagination'] a[href]"
            )
            links: List[str] = []
            for anchor in anchors:
                text = anchor.get_text(strip=True)
                aria_label = str(anchor.get("aria-label") or "")
                data_text = str(anchor.get("data-ph-at-text") or "")
                if not (text.isdigit() or aria_label.lower().startswith("page ") or data_text.isdigit()):
                    continue
                href = anchor.get("href")
                if not href:
                    continue
                links.append(urljoin(base_url, href))
            return links
        except Exception:
            return []

    def _extract_offset_page_urls(self, html: str, current_url: str) -> List[str]:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html or "", "html.parser")
            anchors = soup.select(
                "a[aria-label^='Page '][href], "
                "a[data-ph-at-id='pagination-page-number-link'][href], "
                "ul.pagination a[href], "
                "[class*='pagination'] a[href]"
            )
            offset_params = {"from", "offset", "start", "page", "pg", "p", "cursor", "after", "before"}
            seen: set[str] = set()
            urls: List[str] = []

            for anchor in anchors:
                href = anchor.get("href") or ""
                if not href:
                    continue
                full_url = urljoin(current_url, href)
                if full_url == current_url or full_url in seen:
                    continue
                parsed = urlparse(full_url)
                query = parse_qs(parsed.query, keep_blank_values=True)
                fragment_query = parse_qs(parsed.fragment, keep_blank_values=True)
                keys = {key.lower() for key in query} | {key.lower() for key in fragment_query}
                if not keys.intersection(offset_params):
                    continue
                seen.add(full_url)
                urls.append(full_url)

            def sort_key(url: str) -> int:
                query = parse_qs(urlparse(url).query, keep_blank_values=True)
                for param in ("from", "offset", "start", "page", "pg", "p"):
                    if query.get(param):
                        try:
                            return int(query[param][0])
                        except (TypeError, ValueError):
                            return 0
                return 0

            return sorted(urls, key=sort_key)
        except Exception:
            return []

    def _detect_pagination_from_url(self, url: str) -> Optional[PaginationConfig]:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)

        for param in ("page", "p", "pg", "start", "offset", "from"):
            if param in query:
                if param == "offset" and any(limit_name in query for limit_name in ("limit", "size", "take")):
                    limit_param = next((name for name in ("limit", "size", "take") if name in query), None)
                    limit_value = 25
                    if limit_param and query.get(limit_param):
                        try:
                            limit_value = int(query[limit_param][-1])
                        except (TypeError, ValueError):
                            limit_value = 25
                    return PaginationConfig(
                        type="offset_limit",
                        offset_param="offset",
                        limit_param=limit_param,
                        limit_value=limit_value,
                    )

                step = 1
                if param in {"start", "from"}:
                    step = 10
                return PaginationConfig(type="url_param", param=param, step=step)

        path = parsed.path or ""
        if re.search(r"/page/\d+/?$", path):
            return PaginationConfig(type="url_path", pattern="/page/{page}")
        if re.search(r"/p\d+/?$", path):
            return PaginationConfig(type="url_path", pattern="/p{page}")
        if re.search(r"-\d+/?$", path):
            return PaginationConfig(type="url_path", pattern="-{page}")
        return None

    def _detect_pagination_from_page(
        self,
        *,
        first_page: PageResult,
        url: str,
        max_pages: int,
    ) -> Optional[PaginationConfig]:
        html = first_page.html or first_page.normalized_html
        detection = self._detect_pagination_heuristics(html=html, url=url)
        if not detection["has_pagination"]:
            if len(first_page.clean_text.split()) > 150:
                return PaginationConfig(type="scroll", max_pages=max_pages)
            return None

        mode = detection["mode"]
        if mode == "url_list":
            return PaginationConfig(
                type="url_list",
                max_pages=max_pages,
                page_urls=detection.get("page_urls") or [],
            )
        if mode == "url_param":
            return PaginationConfig(
                type="url_param",
                param=detection.get("param") or "page",
                step=int(detection.get("step") or 1),
                max_pages=max_pages,
                next_url=detection.get("next_url"),
            )
        if mode == "next_button":
            return PaginationConfig(
                type="click_next",
                selector=detection["next_selector"] or ", ".join(NEXT_PAGINATION_SELECTORS),
                max_pages=max_pages,
            )
        if mode == "page_numbers":
            numbered_links = self._extract_numbered_links(html, base_url=url)
            if numbered_links:
                return PaginationConfig(
                    type="numbered_links",
                    selector="nav[aria-label*='pagination'] a, .pagination a, ol.page-list a",
                    mode="href",
                    max_pages=max_pages,
                )
            return PaginationConfig(
                type="click_next",
                selector=", ".join(NEXT_PAGINATION_SELECTORS),
                max_pages=max_pages,
            )
        if mode == "load_more":
            return PaginationConfig(
                type="click_append",
                selector=", ".join(LOAD_MORE_SELECTORS),
                max_pages=max_pages,
            )
        return None

    def _request_with_detected_action(self, *, request: ScrapeRequest, detected: PaginationConfig) -> ScrapeRequest:
        payload = request.to_dict()
        actions = list(payload.get("actions") or [])
        action_kind = None
        if detected.type == "click_append":
            action_kind = "repeat_click_append"
        elif detected.type == "click_next":
            action_kind = "repeat_click_until_stable"
        elif detected.type == "scroll":
            action_kind = "scroll_until_stable"

        if action_kind:
            actions.append(
                {
                    "kind": action_kind,
                    "selector": detected.selector,
                    "max_iterations": detected.max_pages,
                    "wait_ms": 2000,
                    "optional": True,
                }
            )
        return ScrapeRequest(
            url=request.url,
            crawl=request.crawl,
            actions=[PageAction.from_any(action) for action in actions],
            session_key=request.session_key,
            allow_http_probe=request.allow_http_probe,
            proxy_policy=request.proxy_policy,
            extraction_mode=request.extraction_mode,
            unlock_strategy=request.unlock_strategy,
            pagination_mode=request.pagination_mode,
            pagination=request.pagination,
            stream_mode=request.stream_mode,
        )

    def _detect_pagination_heuristics(self, *, html: str, url: str) -> Dict[str, Any]:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html or "", "html.parser")
        except Exception:
            soup = None

        evidence: List[str] = []
        score = 0
        lowered_html = (html or "").lower()

        if soup is not None:
            page_text = soup.get_text(" ", strip=True)
            page_urls = self._extract_offset_page_urls(html, url)
            if len(page_urls) >= 2:
                evidence.append(f"offset page links in DOM: {len(page_urls)} found")
                return {
                    "has_pagination": True,
                    "mode": "url_list",
                    "confidence": 10,
                    "next_selector": None,
                    "page_urls": page_urls,
                    "evidence": evidence,
                }

            rel_next = soup.select_one("link[rel='next'][href], a[rel='next'][href]")
            if rel_next and rel_next.get("href"):
                next_url = urljoin(url, rel_next["href"])
                inferred = self._detect_pagination_from_url(next_url)
                evidence.append(f"rel=next href: {next_url}")
                return {
                    "has_pagination": True,
                    "mode": "url_param",
                    "confidence": 10,
                    "next_selector": None,
                    "param": inferred.param if inferred and inferred.param else "page",
                    "step": inferred.step if inferred else 1,
                    "next_url": next_url,
                    "evidence": evidence,
                }

            if soup.select_one(".mat-paginator, mat-paginator") and re.search(r"\b1\s*\D+\s*\d+\s+of\s+\d+", page_text, re.IGNORECASE):
                evidence.append("material paginator range supports page query")
                return {
                    "has_pagination": True,
                    "mode": "url_param",
                    "confidence": 9,
                    "next_selector": None,
                    "param": "page",
                    "step": 1,
                    "evidence": evidence,
                }

            for selector in NEXT_PAGINATION_SELECTORS:
                try:
                    element = soup.select_one(selector)
                except Exception:
                    continue
                if element is not None and not self._element_is_disabled(element):
                    evidence.append(f"selector match: {selector}")
                    return {
                        "has_pagination": True,
                        "mode": "next_button",
                        "confidence": 9,
                        "next_selector": selector,
                        "evidence": evidence,
                    }

            for element in soup.find_all(True, attrs={"aria-label": True}):
                label = str(element.get("aria-label") or "")
                label_lower = label.lower()
                if "next" in label_lower and "page" in label_lower and not self._element_is_disabled(element):
                    selector = self._selector_for_aria_element(element, label)
                    evidence.append(f"aria wildcard: {label}")
                    return {
                        "has_pagination": True,
                        "mode": "next_button",
                        "confidence": 9,
                        "next_selector": selector,
                        "evidence": evidence,
                    }

        url_detection = self._detect_pagination_from_url(url)
        if url_detection is not None:
            evidence.append(f"url pattern: {url_detection.type}")
            score += 3

        numbered_links = self._extract_numbered_links(html, base_url=url)
        if numbered_links:
            evidence.append(f"numbered href links: {len(numbered_links)} found")
            score += 4

        page_button_count = 0
        if soup is not None:
            try:
                page_button_count = len(
                    soup.select(
                        "ul.pagination li a, .paginate_button, [class*='page-number'], "
                        "[class*='pageNumber'], [aria-label*='Page ']"
                    )
                )
            except Exception:
                page_button_count = 0
            if page_button_count >= 2:
                evidence.append(f"numbered page buttons: {page_button_count} found")
                score += 3

            for element in soup.find_all(True, attrs={"aria-label": True}):
                label = str(element.get("aria-label") or "").lower()
                if ("prev" in label or "previous" in label) and self._element_is_disabled(element):
                    evidence.append("disabled previous button")
                    score += 2
                    break

            if soup.select_one(".mat-paginator, mat-paginator") and re.search(r"\b1\s*[–-]\s*\d+\s+of\s+\d+", soup.get_text(" ", strip=True), re.IGNORECASE):
                evidence.append("material paginator range supports page query")
                return {
                    "has_pagination": True,
                    "mode": "url_param",
                    "confidence": 9,
                    "next_selector": None,
                    "param": "page",
                    "step": 1,
                    "evidence": evidence,
                }

            for selector in LOAD_MORE_SELECTORS:
                try:
                    element = soup.select_one(selector)
                except Exception:
                    continue
                if element is not None and not self._element_is_disabled(element):
                    evidence.append(f"load-more selector match: {selector}")
                    return {
                        "has_pagination": True,
                        "mode": "load_more",
                        "confidence": 8,
                        "next_selector": selector,
                        "evidence": evidence,
                    }

            load_more = soup.find(
                lambda tag: tag.name in ("button", "a")
                and tag.get_text(strip=True).lower() in {"load more", "show more", "see more"}
            )
            if load_more is not None and not self._element_is_disabled(load_more):
                evidence.append("load-more text button")
                return {
                    "has_pagination": True,
                    "mode": "load_more",
                    "confidence": 8,
                    "next_selector": ", ".join(LOAD_MORE_SELECTORS),
                    "evidence": evidence,
                }

        if any(token in lowered_html for token in ("items per page", " of ", "total jobs", "mat-paginator")):
            evidence.append("pagination text/shell marker")
            score += 2

        if score >= 4:
            return {
                "has_pagination": True,
                "mode": "page_numbers" if numbered_links or page_button_count >= 2 else "load_more",
                "confidence": min(score + 2, 9),
                "next_selector": None,
                "evidence": evidence,
            }

        return {
            "has_pagination": False,
            "mode": "none",
            "confidence": max(1, 10 - score),
            "next_selector": None,
            "evidence": evidence,
        }

    def _element_is_disabled(self, element: Any) -> bool:
        classes = element.get("class", []) or []
        class_text = " ".join(str(item).lower() for item in classes)
        aria_disabled = str(element.get("aria-disabled", "")).lower()
        return element.has_attr("disabled") or aria_disabled == "true" or "disabled" in class_text

    def _selector_for_aria_element(self, element: Any, label: str) -> str:
        escaped = label.replace("\\", "\\\\").replace("'", "\\'")
        if element.name in {"button", "a"}:
            return f"{element.name}[aria-label='{escaped}']"
        return f"[aria-label='{escaped}']"
