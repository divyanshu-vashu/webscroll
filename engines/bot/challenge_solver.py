import logging
import asyncio
import random
from typing import Callable, Awaitable, Any

logger = logging.getLogger(__name__)

class ChallengeSolver:
    """
    Centralized logic to detect and bypass anti-bot challenges (like Cloudflare's Turnstile)
    and verify successful network connection / page loading.

    Acts as middleware before considering a page 'loaded'.
    Supports up to 200 seconds of fallback wait for slow network loads.
    """

    CHALLENGE_TITLES = ["just a moment", "attention required", "cloudflare", "verifying"]

    @classmethod
    async def solve_challenge(
        cls,
        url: str,
        evaluate_fn: Callable[[str], Awaitable[Any]],
        mouse_move_fn: Callable[[int, int], Awaitable[None]],
        mouse_click_fn: Callable[[int, int], Awaitable[None]],
        scroll_down_fn: Callable[[int], Awaitable[None]],
        scroll_up_fn: Callable[[int], Awaitable[None]],
        sleep_fn: Callable[[float], Awaitable[None]],
        max_attempts: int = 200
    ) -> bool:
        """
        Loops and evaluates page state (title, document readyState, and network status).
        If a challenge is detected, applies human signals.
        If a network/DNS/proxy error is detected, immediately raises an exception.
        Returns True if successfully bypassed and loaded, False if timed out.
        """
        logger.info(f"[ChallengeSolver] Verifying page load and security checks for {url} (max {max_attempts}s wait)...")

        # JavaScript execution script to check both title, readyState, and browser network/interstitial errors
        js_checker = """
        (function() {
            try {
                let title = (document.title || "").toLowerCase();
                let bodyText = (document.body ? document.body.innerText : "").toLowerCase();
                
                // 1. Check for standard browser network error screens (Chrome, Firefox, Safari)
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

                if (hasNetError) {
                    return { status: "error", message: "Network/DNS connection error" };
                }

                // 2. Check for anti-bot challenges in title
                let challengeTerms = ["just a moment", "attention required", "cloudflare", "verifying"];
                let isChallenge = challengeTerms.some(term => title.includes(term)) || 
                                  document.querySelector('iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"]') !== null;

                if (isChallenge) {
                    return { status: "challenge", title: document.title, readyState: document.readyState };
                }

                // 3. Otherwise check document ready state
                let isComplete = document.readyState === "complete";
                return { status: isComplete ? "complete" : "loading", title: document.title, readyState: document.readyState };
            } catch(e) {
                return { status: "loading", error: e.toString() };
            }
        })()
        """

        for i in range(max_attempts):
            try:
                raw_state = await evaluate_fn(js_checker)
                if raw_state is None or not isinstance(raw_state, dict):
                    state = {"status": "loading"}
                else:
                    state = raw_state
            except Exception as e:
                logger.debug(f"[ChallengeSolver] Error evaluating page state: {e}")
                state = {"status": "loading"}

            status = state.get("status", "loading")
            title = state.get("title", "")

            # If it's a network/DNS error, raise a clear error so waterfall can fallback immediately
            if status == "error":
                err_msg = state.get("message", "Network error")
                logger.error(f"[ChallengeSolver] ❌ Page failed to load: {err_msg} for {url}")
                raise RuntimeError(f"Page failed to load: {err_msg}")

            if status == "complete":
                logger.info(f"[ChallengeSolver] ✅ Page loaded successfully. Title: '{title}'")
                return True

            if status == "challenge":
                if i % 10 == 0:
                    logger.info(f"[ChallengeSolver] Attempt {i+1}: Challenged by '{title}'. Injecting human bypass signals...")
                    try:
                        # Find the challenge element position
                        js_find_widget = """(function() {
                            let el = document.querySelector('.cf-turnstile, .cf-turnstile-wrapper, #cf-turnstile-wrapper, iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"], #challenge-stage');
                            if (el) {
                                let r = el.getBoundingClientRect();
                                return {x: r.x, y: r.y, width: r.width, height: r.height};
                            }
                            return null;
                        })()"""
                        rect = await evaluate_fn(js_find_widget)

                        if rect and isinstance(rect, dict) and 'x' in rect:
                            target_x = int(rect['x'] + random.uniform(rect['width'] * 0.1, rect['width'] * 0.9))
                            target_y = int(rect['y'] + random.uniform(rect['height'] * 0.1, rect['height'] * 0.9))
                            logger.info(f"[ChallengeSolver] Found Turnstile widget at {rect}. Targeting ({target_x}, {target_y})")
                        else:
                            target_x = random.randint(250, 550)
                            target_y = random.randint(250, 550)
                            logger.info(f"[ChallengeSolver] Turnstile widget not found. Blind targeting ({target_x}, {target_y})")

                        # Mouse jitter simulation
                        for step in range(3):
                            jitter_x = target_x + random.randint(-50, 50)
                            jitter_y = target_y + random.randint(-50, 50)
                            await mouse_move_fn(jitter_x, jitter_y)
                            await sleep_fn(random.uniform(0.05, 0.2))

                        # Move & click
                        await mouse_move_fn(target_x, target_y)
                        await sleep_fn(random.uniform(0.1, 0.3))
                        await mouse_click_fn(target_x, target_y)

                    except Exception as interaction_err:
                        logger.debug(f"[ChallengeSolver] Interaction error: {interaction_err}")

                if i % 5 == 0:
                    try:
                        await scroll_down_fn(150)
                        await sleep_fn(0.2)
                        await scroll_up_fn(50)
                    except Exception as scroll_err:
                        logger.debug(f"[ChallengeSolver] Scroll error: {scroll_err}")

            # Pause 1 second before next poll
            await sleep_fn(1.0)

        logger.warning(f"[ChallengeSolver] ❌ Failed to load/bypass within {max_attempts} seconds.")
        return False

    @classmethod
    def solve_challenge_sync(
        cls,
        url: str,
        evaluate_fn: Callable[[str], Any],
        mouse_move_fn: Callable[[int, int], None],
        mouse_click_fn: Callable[[int, int], None],
        scroll_down_fn: Callable[[int], None],
        scroll_up_fn: Callable[[int], None],
        sleep_fn: Callable[[float], None],
        max_attempts: int = 200
    ) -> bool:
        """
        Synchronous version of solve_challenge.
        """
        logger.info(f"[ChallengeSolver] Verifying page load and security checks for {url} (sync, max {max_attempts}s wait)...")

        js_checker = """
        (function() {
            try {
                let title = (document.title || "").toLowerCase();
                let bodyText = (document.body ? document.body.innerText : "").toLowerCase();
                
                // 1. Check for standard browser network error screens (Chrome, Firefox, Safari)
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

                if (hasNetError) {
                    return { status: "error", message: "Network/DNS connection error" };
                }

                // 2. Check for anti-bot challenges in title
                let challengeTerms = ["just a moment", "attention required", "cloudflare", "verifying"];
                let isChallenge = challengeTerms.some(term => title.includes(term)) || 
                                  document.querySelector('iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"]') !== null;

                if (isChallenge) {
                    return { status: "challenge", title: document.title, readyState: document.readyState };
                }

                // 3. Otherwise check document ready state
                let isComplete = document.readyState === "complete";
                return { status: isComplete ? "complete" : "loading", title: document.title, readyState: document.readyState };
            } catch(e) {
                return { status: "loading", error: e.toString() };
            }
        })()
        """

        for i in range(max_attempts):
            try:
                raw_state = evaluate_fn(js_checker)
                if raw_state is None or not isinstance(raw_state, dict):
                    state = {"status": "loading"}
                else:
                    state = raw_state
            except Exception as e:
                logger.debug(f"[ChallengeSolver] Error evaluating page state: {e}")
                state = {"status": "loading"}

            status = state.get("status", "loading")
            title = state.get("title", "")

            # If it's a network/DNS error, raise a clear error so waterfall can fallback immediately
            if status == "error":
                err_msg = state.get("message", "Network error")
                logger.error(f"[ChallengeSolver] ❌ Page failed to load: {err_msg} for {url}")
                raise RuntimeError(f"Page failed to load: {err_msg}")

            if status == "complete":
                logger.info(f"[ChallengeSolver] ✅ Page loaded successfully. Title: '{title}'")
                return True

            if status == "challenge":
                if i % 10 == 0:
                    logger.info(f"[ChallengeSolver] Attempt {i+1}: Challenged by '{title}'. Injecting human bypass signals...")
                    try:
                        # Find the challenge element position
                        js_find_widget = """(function() {
                            let el = document.querySelector('.cf-turnstile, .cf-turnstile-wrapper, #cf-turnstile-wrapper, iframe[src*="challenges.cloudflare.com"], iframe[src*="turnstile"], #challenge-stage');
                            if (el) {
                                let r = el.getBoundingClientRect();
                                return {x: r.x, y: r.y, width: r.width, height: r.height};
                            }
                            return null;
                        })()"""
                        rect = evaluate_fn(js_find_widget)

                        if rect and isinstance(rect, dict) and 'x' in rect:
                            target_x = int(rect['x'] + random.uniform(rect['width'] * 0.1, rect['width'] * 0.9))
                            target_y = int(rect['y'] + random.uniform(rect['height'] * 0.1, rect['height'] * 0.9))
                            logger.info(f"[ChallengeSolver] Found Turnstile widget at {rect}. Targeting ({target_x}, {target_y})")
                        else:
                            target_x = random.randint(250, 550)
                            target_y = random.randint(250, 550)
                            logger.info(f"[ChallengeSolver] Turnstile widget not found. Blind targeting ({target_x}, {target_y})")

                        # Mouse jitter simulation
                        for step in range(3):
                            jitter_x = target_x + random.randint(-50, 50)
                            jitter_y = target_y + random.randint(-50, 50)
                            mouse_move_fn(jitter_x, jitter_y)
                            sleep_fn(random.uniform(0.05, 0.2))

                        # Move & click
                        mouse_move_fn(target_x, target_y)
                        sleep_fn(random.uniform(0.1, 0.3))
                        mouse_click_fn(target_x, target_y)

                    except Exception as interaction_err:
                        logger.debug(f"[ChallengeSolver] Interaction error: {interaction_err}")

                if i % 5 == 0:
                    try:
                        scroll_down_fn(150)
                        sleep_fn(0.2)
                        scroll_up_fn(50)
                    except Exception as scroll_err:
                        logger.debug(f"[ChallengeSolver] Scroll error: {scroll_err}")

            # Pause 1 second before next poll
            sleep_fn(1.0)

        logger.warning(f"[ChallengeSolver] ❌ Failed to load/bypass within {max_attempts} seconds.")
        return False
