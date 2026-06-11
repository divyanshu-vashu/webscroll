import logging
from typing import Any, Dict, Iterable, Optional

try:
    import nodriver as uc
except Exception:  # pragma: no cover - optional dependency
    uc = None

logger = logging.getLogger(__name__)

class NodriverClient:
    """
    Nodriver browser client for stealth web scraping.
    Fully asynchronous successor to undetected_chromedriver, built to bypass Cloudflare and other protections.
    """
    def __init__(
        self, 
        headless: bool = False,
        proxy: Optional[Dict[str, str]] = None, 
        user_data_dir: Optional[str] = None,
        identity_profile: Optional[Dict[str, Any]] = None
    ):
        self.headless = headless
        self.proxy = proxy
        self.user_data_dir = user_data_dir
        self.identity_profile = identity_profile
        
        # Use the User-Agent from the identity profile if available
        self.user_agent = None
        if identity_profile and "user_agent" in identity_profile:
            self.user_agent = identity_profile["user_agent"]

    async def _fetch_async(self, url: str) -> str:
        browser_args = []
        
        # Note: We intentionally DO NOT spoof the --user-agent via CLI flags here. 
        # Spoofing UA without spoofing navigator.userAgentData (Client Hints) causes a mismatch
        # that Cloudflare Turnstile instantly detects, leading to endless "Just a moment..." loops.
        # It's much safer to let nodriver use the genuine, installed Chrome's User-Agent.
        
        if self.proxy:
            proxy_server = self.proxy.get("server")
            if proxy_server:
                # Nodriver proxy support is noted as limited in the docs, but this is the standard Chrome arg
                # The browser.create_context() approach is another option but currently unstable
                browser_args.append(f"--proxy-server={proxy_server}")

        logger.info(f"Launching Nodriver (headless={self.headless}, profile={self.user_data_dir}) to fetch {url}...")
        
        # Start the browser with the given profile and args
        if uc is None:
            raise RuntimeError("nodriver is not installed")
        browser = await uc.start(
            headless=self.headless,
            user_data_dir=self.user_data_dir,
            browser_args=browser_args,
            no_sandbox=True
        )
        
        try:
            page = await browser.get(url)
            
            # --- SMART BYPASS LOGIC (CENTRALIZED) ---
            from engines.bot.challenge_solver import ChallengeSolver
            
            await ChallengeSolver.solve_challenge(
                url=url,
                evaluate_fn=lambda script: page.evaluate(script),
                mouse_move_fn=lambda x, y: page.mouse_move(x, y),
                mouse_click_fn=lambda x, y: page.mouse_click(x, y),
                scroll_down_fn=lambda amount: page.scroll_down(amount),
                scroll_up_fn=lambda amount: page.scroll_up(amount),
                sleep_fn=lambda delay: page.sleep(delay),
                max_attempts=200
            )

            # Final extraction
            html_content = await page.evaluate("document.documentElement.outerHTML")
            return html_content
            
        except Exception as e:
            logger.error(f"Nodriver extraction failed for {url}: {e}")
            raise
            
        finally:
            # Clean up and close the browser instance
            browser.stop()

    def fetch(self, url: str, actions: Optional[Iterable[Any]] = None) -> str:
        """
        Synchronous wrapper to fetch the raw HTML of a URL using Nodriver.
        Returns the rendered HTML content.
        This allows it to be used synchronously by the PermutationEngine.
        """
        if actions:
            logger.info("[Nodriver] Actions requested but not yet implemented; proceeding with plain fetch.")
        if uc is None:
            raise RuntimeError("nodriver is not installed")
        
        # Reset event loop to avoid conflict with other drivers
        import asyncio
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        return new_loop.run_until_complete(self._fetch_async(url))
