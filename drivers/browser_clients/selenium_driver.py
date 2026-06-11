import hashlib
import logging
import re
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


class SeleniumDriver:
    """
    SeleniumBase browser client.

    The current UC flow is intentionally preserved because it is the strongest
    working unlock path in this repo. The only extension added here is an
    optional post-load action pipeline.
    """

    def __init__(
        self,
        headless: bool = False,
        proxy: Optional[Dict[str, str]] = None,
        user_data_dir: Optional[str] = None,
        identity_profile: Optional[Dict] = None,
    ):
        profile = identity_profile or {}

        self.headless = profile.get("headless", headless)
        self.user_data_dir = user_data_dir

        raw_headers: Dict = profile.get("headers", {})
        self.extra_headers: Dict[str, str] = {
            str(k): str(v) for k, v in raw_headers.items() if k.lower() != "user-agent"
        }
        self.user_agent: Optional[str] = raw_headers.get("User-Agent") or raw_headers.get("user-agent")

        self.proxy_string: Optional[str] = None
        target_proxy = profile.get("proxy") or proxy
        if target_proxy and "server" in target_proxy:
            server = (
                target_proxy["server"]
                .replace("http://", "")
                .replace("https://", "")
            )
            user = target_proxy.get("username", "")
            pwd = target_proxy.get("password", "")
            self.proxy_string = f"{user}:{pwd}@{server}" if (user and pwd) else server

    def fetch(self, url: str, actions: Optional[Iterable[Any]] = None) -> str:
        return self.fetch_with_actions(url, actions=actions)

    def fetch_with_actions(self, url: str, actions: Optional[Iterable[Any]] = None) -> str:
        """
        Fetch the rendered HTML using SeleniumBase UC Mode.
        """
        from seleniumbase import SB

        logger.info(f"[SeleniumBase] Launching UC Mode (headed=True) -> {url}")

        sb_kwargs = {
            "uc": True,
            "headless": False,
            "headed": True,
        }
        if self.user_data_dir:
            sb_kwargs["user_data_dir"] = self.user_data_dir
        if self.user_agent:
            sb_kwargs["agent"] = self.user_agent
        if self.proxy_string:
            sb_kwargs["proxy"] = self.proxy_string

        try:
            with SB(**sb_kwargs) as sb:
                logger.info("[SeleniumBase] Navigating to URL with reconnect bypass...")
                sb.uc_open_with_reconnect(url, reconnect_time=6)

                try:
                    sb.sleep(2)
                    if sb.is_element_visible('iframe[src*="challenges.cloudflare.com"]'):
                        logger.info("[SeleniumBase] Turnstile detected, clicking via UC GUI...")
                        sb.uc_gui_click_captcha()
                        sb.sleep(3)
                except Exception as exc:
                    logger.debug(f"[SeleniumBase] Native CAPTCHA click attempt (non-fatal): {exc}")

                if self.extra_headers:
                    try:
                        sb.driver.execute_cdp_cmd("Network.enable", {})
                        sb.driver.execute_cdp_cmd(
                            "Network.setExtraHTTPHeaders",
                            {"headers": self.extra_headers},
                        )
                        logger.info(f"[SeleniumBase] Headers injected: {list(self.extra_headers.keys())}")
                    except Exception as exc:
                        logger.warning(f"[SeleniumBase] Header injection failed (non-fatal): {exc}")

                state = sb.execute_script(self._page_state_checker())
                if state == "error":
                    logger.error("[SeleniumBase] Page failed to load due to a network or DNS error.")
                    raise RuntimeError("Page failed to load: Network/DNS connection error")

                self._run_actions(sb, actions or [])
                html_content = sb.get_page_source()
                logger.info(f"[SeleniumBase] Done - size={len(html_content)} bytes")
                return html_content

        except Exception as exc:
            logger.error(f"[SeleniumBase] Failed for {url}: {exc}")
            raise

    def _page_state_checker(self) -> str:
        return """
        (function() {
            try {
                let title = (document.title || "").toLowerCase();
                let bodyText = (document.body ? document.body.innerText : "").toLowerCase();
                let hasNetError =
                    document.querySelector('.neterror, #main-frame-error, #main-message, .error-code') !== null ||
                    title.includes("can't be reached") ||
                    title.includes("not found") ||
                    bodyText.includes("dns_probe_finished") ||
                    bodyText.includes("err_connection_refused") ||
                    bodyText.includes("err_name_not_resolved") ||
                    bodyText.includes("err_proxy_connection_failed") ||
                    bodyText.includes("err_internet_disconnected") ||
                    bodyText.includes("server ip address could not be found") ||
                    bodyText.includes("site can't be reached") ||
                    bodyText.includes("open your computer's proxy settings") ||
                    bodyText.includes("connection refused");
                return hasNetError ? "error" : (document.readyState === "complete" ? "complete" : "loading");
            } catch(e) {
                return "error";
            }
        })()
        """

    def _run_actions(self, sb, actions: Iterable[Any]) -> None:
        actions = list(actions or [])
        if not actions:
            return

        logger.info(f"[SeleniumBase] Running {len(actions)} post-load actions")
        for raw_action in actions:
            action = self._normalize_action(raw_action)
            kind = action.get("kind", "").strip().lower()
            selector = action.get("selector")
            value = action.get("value")
            timeout_ms = int(action.get("timeout_ms", 5000))
            optional = bool(action.get("optional", False))

            try:
                if kind == "wait":
                    sb.sleep(self._coerce_wait_seconds(value=value, timeout_ms=timeout_ms))
                elif kind == "click":
                    sb.click(selector)
                elif kind == "type":
                    sb.type(selector, value or "")
                elif kind == "scroll":
                    self._scroll(sb, value)
                elif kind == "wait_for_selector":
                    sb.wait_for_element(selector, timeout=max(timeout_ms / 1000.0, 1.0))
                elif kind == "dismiss_banner":
                    self._dismiss_banner(sb, selector)
                elif kind == "solve_challenge":
                    self._solve_challenge(sb)
                elif kind == "repeat_click_until_stable":
                    self._repeat_click_until_stable(sb, action)
                elif kind == "repeat_click_append":
                    self._repeat_click_append(sb, action)
                elif kind == "scroll_until_stable":
                    self._scroll_until_stable(sb, action)
                elif kind == "extract_html":
                    logger.debug("[SeleniumBase] extract_html action encountered; capture happens after actions.")
                else:
                    raise ValueError(f"Unsupported SeleniumBase action kind: {kind}")
            except Exception as exc:
                if optional:
                    logger.warning(f"[SeleniumBase] Optional action '{kind}' failed: {exc}")
                    continue
                raise

    def _normalize_action(self, raw_action: Any) -> Dict[str, Any]:
        if hasattr(raw_action, "to_dict"):
            return raw_action.to_dict()
        if isinstance(raw_action, dict):
            return raw_action
        raise TypeError(f"Unsupported SeleniumBase action payload: {type(raw_action)!r}")

    def _coerce_wait_seconds(self, *, value: Optional[str], timeout_ms: int) -> float:
        if value in (None, ""):
            return max(timeout_ms / 1000.0, 0.25)
        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            return max(timeout_ms / 1000.0, 0.25)

    def _scroll(self, sb, value: Optional[str]) -> None:
        direction = str(value or "bottom").strip().lower()
        if direction in {"bottom", "down"}:
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        elif direction in {"top", "up"}:
            sb.execute_script("window.scrollTo(0, 0);")
        else:
            try:
                amount = int(float(direction))
            except ValueError:
                amount = 600
            sb.execute_script(f"window.scrollBy(0, {amount});")
        sb.sleep(0.5)

    def _dismiss_banner(self, sb, selector: Optional[str]) -> None:
        if selector:
            if sb.is_element_visible(selector):
                sb.click(selector)
            return

        common_selectors = [
            'button:contains("Accept")',
            'button:contains("I agree")',
            'button:contains("Allow all")',
            'button:contains("Got it")',
            '[id*="cookie"] button',
            '[class*="cookie"] button',
        ]
        for candidate in common_selectors:
            try:
                if sb.is_element_visible(candidate):
                    sb.click(candidate)
                    sb.sleep(0.5)
                    return
            except Exception:
                continue

    def _solve_challenge(self, sb) -> None:
        try:
            sb.solve_captcha()
        except Exception as exc:
            logger.debug(f"[SeleniumBase] solve_captcha failed (non-fatal): {exc}")
        try:
            sb.uc_gui_click_captcha()
        except Exception as exc:
            logger.debug(f"[SeleniumBase] uc_gui_click_captcha failed (non-fatal): {exc}")

    def _repeat_click_until_stable(self, sb, action: Dict[str, Any]) -> None:
        selector = action.get("selector")
        if not selector:
            raise ValueError("repeat_click_until_stable requires a selector")

        max_iterations = max(int(action.get("max_iterations", 10)), 1)
        wait_seconds = max(int(action.get("wait_ms", 1500)) / 1000.0, 0.25)
        previous_hash = None
        stable_hits = 0

        for _ in range(max_iterations):
            target = self._first_clickable_selector(sb, selector)
            if not target:
                break
            before_hash = self._dom_hash(sb)
            sb.click(target)
            sb.sleep(wait_seconds)
            after_hash = self._dom_hash(sb)
            if after_hash == before_hash or after_hash == previous_hash:
                stable_hits += 1
            else:
                stable_hits = 0
            previous_hash = after_hash
            if stable_hits >= 1:
                break

    def _repeat_click_append(self, sb, action: Dict[str, Any]) -> None:
        selector = action.get("selector")
        if not selector:
            raise ValueError("repeat_click_append requires a selector")

        max_iterations = max(int(action.get("max_iterations", 10)), 1)
        wait_seconds = max(int(action.get("wait_ms", 1500)) / 1000.0, 0.25)
        previous_size = self._dom_size(sb)

        for _ in range(max_iterations):
            target = self._first_clickable_selector(sb, selector)
            if not target:
                break
            sb.click(target)
            sb.sleep(wait_seconds)
            current_size = self._dom_size(sb)
            if current_size <= previous_size:
                break
            previous_size = current_size

    def _scroll_until_stable(self, sb, action: Dict[str, Any]) -> None:
        max_scrolls = max(int(action.get("max_iterations", 10)), 1)
        wait_seconds = max(int(action.get("wait_ms", 1500)) / 1000.0, 0.25)
        scroll_step_px = int(action.get("scroll_step_px", 800))
        previous_hash = None
        stable_hits = 0

        for _ in range(max_scrolls):
            sb.execute_script(f"window.scrollBy(0, {scroll_step_px});")
            sb.sleep(wait_seconds)
            current_hash = self._dom_hash(sb)
            if current_hash == previous_hash:
                stable_hits += 1
            else:
                stable_hits = 0
            previous_hash = current_hash
            if stable_hits >= 1:
                break

    def _dom_hash(self, sb) -> str:
        html = sb.get_page_source() or ""
        return hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()

    def _dom_size(self, sb) -> int:
        html = sb.get_page_source() or ""
        return len(html)

    def _first_clickable_selector(self, sb, selector: str) -> Optional[str]:
        selectors = [part.strip() for part in re.split(r"\s*,\s*", selector) if part.strip()]
        for candidate in selectors:
            try:
                if sb.is_element_visible(candidate):
                    return candidate
            except Exception:
                continue
        return None
