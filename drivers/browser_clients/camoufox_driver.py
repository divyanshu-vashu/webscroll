import logging
from typing import Any, Dict, Iterable, Optional

try:
    from camoufox.sync_api import Camoufox
except Exception:  # pragma: no cover - optional dependency
    Camoufox = None

logger = logging.getLogger(__name__)

class CamoufoxDriver:
    """
    Camoufox browser client for stealth web scraping.
    Built to bypass Cloudflare and other anti-bot technologies.
    """
    def __init__(
        self, 
        headless: bool = True, 
        proxy: Optional[Dict[str, str]] = None, 
        user_data_dir: Optional[str] = None
    ):
        """
        Initializes the Camoufox driver configuration.
        
        Args:
            headless: Run browser in headless mode. 
                      Note: False can sometimes help pass interactive captchas.
            proxy: Dictionary with proxy details (server, username, password).
            user_data_dir: Path to persist browser session/cookies (helps bypass turnstiles).
        """
        self.headless = headless
        self.proxy = proxy
        self.user_data_dir = user_data_dir
        
        # High-stealth config replicating a standard Windows Firefox user
        self.config = {
            'window.outerHeight': 1056,
            'window.outerWidth': 1920,
            'window.innerHeight': 1008,
            'window.innerWidth': 1920,
            'window.history.length': 4,
            'navigator.userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'navigator.appCodeName': 'Mozilla',
            'navigator.appName': 'Netscape',
            'navigator.appVersion': '5.0 (Windows)',
            'navigator.oscpu': 'Windows NT 10.0; Win64; x64',
            'navigator.language': 'en-US',
            'navigator.languages': ['en-US'],
            'navigator.platform': 'Win32',
            'navigator.hardwareConcurrency': 12,
            'navigator.product': 'Gecko',
            'navigator.productSub': '20030107',
            'navigator.maxTouchPoints': 10,
        }

    def fetch(self, url: str, actions: Optional[Iterable[Any]] = None) -> str:
        """
        Fetches the raw HTML of a URL using Camoufox.
        Returns the rendered HTML content.
        """
        if actions:
            logger.info("[Camoufox] Actions requested but not yet implemented; proceeding with plain fetch.")
        kwargs = {
            "headless": self.headless,
            "os": ("windows"),
            "config": self.config,
            "i_know_what_im_doing": True
        }
        
        if self.proxy:
            kwargs["proxy"] = self.proxy
            kwargs["geoip"] = True  # Aligns browser timezone/language with proxy IP
            
        if self.user_data_dir:
            kwargs["persistent_context"] = True
            kwargs["user_data_dir"] = self.user_data_dir

        logger.info(f"Launching Camoufox to fetch {url}...")
        
        try:
            if Camoufox is None:
                raise RuntimeError("camoufox is not installed")
            
            # Reset event loop to avoid conflict with other drivers
            try:
                import asyncio
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
            except Exception as e:
                logger.debug(f"Failed to reset asyncio loop in CamoufoxDriver: {e}")

            with Camoufox(**kwargs) as browser:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded")
                
                # Wait for network idle to ensure dynamic JS has loaded
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    logger.warning(f"Network idle wait timed out, proceeding anyway: {e}")
                    
                # Small human-like pause to let any late-rendering elements pop in
                page.wait_for_timeout(2000)
                
                html_content = page.content()
                page.close()
                
                return html_content
        except Exception as e:
            logger.error(f"Camoufox extraction failed for {url}: {e}")
            raise


def main():
    import sys
    url=sys.argv[1]
    driver = CamoufoxDriver()
    html = driver.fetch("https://www.mediamarkt.at/de/product/_gorenje-rb-492-pw-kuhlschrank-e-845-mm-hoch-weiss-142380563.html")
    print(html)



if __name__ == "__main__":
    main()
