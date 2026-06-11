"""
Base HTTP Client Interface

This module defines the common interface that all HTTP clients must implement.
Following the modular architecture principles, this ensures consistency across
different HTTP implementations (httpx, aiohttp, curl_cffi).
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import asyncio


@dataclass
class HttpResponse:
    """Standard HTTP response container for all HTTP clients."""
    status_code: int
    content: bytes
    text: str
    headers: Dict[str, str]
    url: str
    cookies: Dict[str, str]
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx status code)."""
        return 200 <= self.status_code < 300
    
    @property
    def is_blocked(self) -> bool:
        """Check if response indicates bot detection/blocking."""
        blocking_indicators = [
            403,  # Forbidden
            429,  # Too Many Requests
            503,  # Service Unavailable
        ]
        return self.status_code in blocking_indicators


@dataclass
class ProxyConfig:
    """Proxy configuration for HTTP requests."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, https, socks4, socks5
    
    @property
    def proxy_url(self) -> str:
        """Generate proxy URL with authentication if provided."""
        if self.username and self.password:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"


@dataclass
class TlsProfile:
    """TLS configuration for anti-bot bypass."""
    ja3_fingerprint: Optional[str] = None
    http2_fingerprint: Optional[str] = None
    cipher_suites: Optional[list] = None
    extensions: Optional[list] = None
    curves: Optional[list] = None


class BaseHttpClient(ABC):
    """
    Abstract base class for all HTTP clients.
    
    This interface ensures that all HTTP implementations (httpx, aiohttp, curl_cffi)
    provide the same functionality and return standardized responses.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        proxy_config: Optional[ProxyConfig] = None,
        tls_profile: Optional[TlsProfile] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy_config = proxy_config
        self.tls_profile = tls_profile
        self.headers = headers or {}
        self._session = None
    
    @abstractmethod
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP GET request."""
        pass
    
    @abstractmethod
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP POST request."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the HTTP client session."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _merge_headers(self, request_headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge default headers with request-specific headers."""
        merged = self.headers.copy()
        if request_headers:
            merged.update(request_headers)
        return merged
    
    async def _retry_request(
        self,
        request_func,
        *args,
        **kwargs
    ) -> HttpResponse:
        """
        Retry mechanism for failed requests.
        
        Implements exponential backoff and handles common failure scenarios.
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await request_func(*args, **kwargs)
                
                # If successful or not a retryable status, return immediately
                if response.is_success or not self._is_retryable_status(response.status_code):
                    return response
                
                # Log retry attempt for debugging
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        # This shouldn't happen, but just in case
        raise RuntimeError("All retry attempts failed without exception")
    
    def _is_retryable_status(self, status_code: int) -> bool:
        """Determine if a status code is worth retrying."""
        retryable_codes = {
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        return status_code in retryable_codes
