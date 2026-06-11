"""
drivers/identity/browserforge_manager.py

The Identity Layer -> "The Forger"
This layer is responsible for generating mathematically consistent browser fingerprints.
It uses BrowserForge to create matching sets of HTTP headers, User-Agent strings, and 
client hints to ensure the browser execution looks like a real, consistent user.
"""

import logging
from typing import Dict, Any, Optional, Tuple

try:
    from browserforge.headers import HeaderGenerator
except ImportError:
    HeaderGenerator = None
    logging.warning("browserforge is not installed. Please run `pip install browserforge`")

logger = logging.getLogger(__name__)

class BrowserForgeManager:
    """
    Generates consistent browser fingerprints and header sets using BrowserForge.
    Ensures that OS, browser, screen resolution, and headers match realistically
    to avoid impossible combinations (e.g., Linux OS with Safari User-Agent).
    """

    def __init__(self, 
                 browsers: Tuple[str, ...] = ("chrome", "edge"), 
                 operating_systems: Tuple[str, ...] = ("windows", "macos"),
                 device_type: str = "desktop"):
        """
        Initializes the BrowserForge generator with specific constraints to 
        maintain consistency across the generated profiles.
        """
        self.browsers = browsers
        self.operating_systems = operating_systems
        self.device_type = device_type
        
        if HeaderGenerator:
            self.generator = HeaderGenerator(
                browser=self.browsers,
                os=self.operating_systems,
                device=self.device_type,
                http_version=2,
            )
        else:
            self.generator = None

    def generate_profile(self, locale: str = "en-US") -> Dict[str, Any]:
        """
        Generates a consistent identity profile for browser clients to use.
        
        Args:
            locale (str): The desired locale string (e.g., "en-US", "en-GB")
            
        Returns:
            Dict containing headers, user_agent, viewport, and other consistent profile attributes.
        """
        if not self.generator:
            logger.warning("BrowserForge not available. Returning fallback static profile.")
            return self._get_fallback_profile(locale)

        try:
            # We can instantiate a local generator if we want to enforce the specific locale
            local_generator = HeaderGenerator(
                browser=self.browsers,
                os=self.operating_systems,
                device=self.device_type,
                locale=(locale,),
                http_version=2,
            )
            
            headers_obj = local_generator.generate()
            headers = dict(headers_obj)
            
            # Extract the exact User-Agent generated so the browser can match the HTTP headers
            user_agent = headers.get("User-Agent", self._get_fallback_ua())
            
            # Determine appropriate screen constraints based on the device type generated
            is_mobile = "?1" in headers.get("sec-ch-ua-mobile", "")
            if is_mobile:
                viewport = {"width": 390, "height": 844} # Typical mobile dimensions
            else:
                viewport = {"width": 1920, "height": 1080} # Typical desktop dimensions
            
            # Map common locales to appropriate timezones
            timezone_mapping = {
                "en-US": "America/New_York",
                "en-GB": "Europe/London",
                "de-DE": "Europe/Berlin",
                "en-IN": "Asia/Kolkata",
                "en-AU": "Australia/Sydney"
            }
            timezone_id = timezone_mapping.get(locale, "America/New_York")
            
            profile = {
                "headers": headers,
                "user_agent": user_agent,
                "viewport": viewport,
                "locale": locale,
                "timezone_id": timezone_id,
                "is_mobile": is_mobile,
                # Fields below can be populated later by the Orchestrator / Proxy Manager
                "proxy": None,
                "user_data_dir": None,
            }
            
            logger.info(f"Generated consistent identity profile: UA={user_agent[:40]}... Locale={locale}")
            return profile

        except Exception as e:
            logger.error(f"Failed to generate BrowserForge profile: {e}. Using fallback.")
            return self._get_fallback_profile(locale)

    def _get_fallback_ua(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def _get_fallback_profile(self, locale: str) -> Dict[str, Any]:
        """Returns a static, highly consistent fallback profile if generation fails."""
        ua = self._get_fallback_ua()
        return {
            "headers": {
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": f"{locale},en;q=0.9",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1"
            },
            "user_agent": ua,
            "viewport": {"width": 1920, "height": 1080},
            "locale": locale,
            "timezone_id": "America/New_York",
            "is_mobile": False,
            "proxy": None,
            "user_data_dir": None,
        }
