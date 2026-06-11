"""
aiohttp HTTP Client Implementation

This module provides an aiohttp-based HTTP client with advanced TLS configuration
and anti-bot bypass capabilities. aiohttp is chosen for its performance and
flexibility in handling custom TLS configurations.
"""

import asyncio
import ssl
from typing import Any, AsyncGenerator, Dict, Optional, Union
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from .base_http_client import (
    BaseHttpClient, 
    HttpResponse, 
    ProxyConfig, 
    TlsProfile
)


class AiohttpClient(BaseHttpClient):
    """
    aiohttp-based HTTP client with TLS fingerprinting capabilities.
    
    This client is optimized for high-performance async requests and provides
    fine-grained control over TLS settings for anti-bot bypass.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        proxy_config: Optional[ProxyConfig] = None,
        tls_profile: Optional[TlsProfile] = None,
        headers: Optional[Dict[str, str]] = None,
        connector_limit: int = 100,
        force_close: bool = False
    ):
        super().__init__(timeout, max_retries, proxy_config, tls_profile, headers)
        self.connector_limit = connector_limit
        self.force_close = force_close
        self._session: Optional[ClientSession] = None
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session with custom configuration."""
        if self._session is None or self._session.closed:
            # Create SSL context for TLS fingerprinting
            ssl_context = self._create_ssl_context()
            
            # Configure connector
            connector_kwargs = {
                'limit': self.connector_limit,
                'force_close': self.force_close,
                'ssl': ssl_context,
            }
            
            # Add proxy configuration if provided
            if self.proxy_config:
                connector_kwargs['proxy'] = self.proxy_config.proxy_url
            
            connector = TCPConnector(**connector_kwargs)
            
            # Configure timeout
            timeout = ClientTimeout(total=self.timeout)
            
            # Create session
            self._session = ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        
        return self._session
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context with custom TLS configuration for anti-bot bypass.
        """
        context = ssl.create_default_context()
        
        if self.tls_profile:
            # Apply custom TLS profile settings
            if self.tls_profile.cipher_suites:
                context.set_ciphers(':'.join(self.tls_profile.cipher_suites))
            
            # Configure SSL options for stealth
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_COMPRESSION
            
            # Set minimum TLS version
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return context
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP GET request with retry logic."""
        async def _get_request():
            session = await self._get_session()
            merged_headers = self._merge_headers(headers)
            
            async with session.get(
                url,
                params=params,
                headers=merged_headers,
                **kwargs
            ) as response:
                return await self._convert_response(response)
        
        return await self._retry_request(_get_request)
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP POST request with retry logic."""
        async def _post_request():
            session = await self._get_session()
            merged_headers = self._merge_headers(headers)
            
            async with session.post(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                **kwargs
            ) as response:
                return await self._convert_response(response)
        
        return await self._retry_request(_post_request)
    
    async def _convert_response(self, response: aiohttp.ClientResponse) -> HttpResponse:
        """Convert aiohttp response to standardized HttpResponse."""
        content = await response.read()
        text = await response.text(errors='replace')
        
        # Convert cookies to dict
        cookies = {}
        for cookie in response.cookies.values():
            cookies[cookie.key] = cookie.value
        
        return HttpResponse(
            status_code=response.status,
            content=content,
            text=text,
            headers=dict(response.headers),
            url=str(response.url),
            cookies=cookies
        )
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def download_stream(
        self,
        url: str,
        chunk_size: int = 8192,
        headers: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream download large files in chunks.
        
        Useful for downloading large HTML files or media content.
        """
        session = await self._get_session()
        merged_headers = self._merge_headers(headers)
        
        async with session.get(url, headers=merged_headers) as response:
            if response.status != 200:
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=f"Failed to download: {response.status}"
                )
            
            async for chunk in response.content.iter_chunked(chunk_size):
                yield chunk
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session for debugging."""
        if not self._session:
            return {"status": "not_initialized"}
        
        return {
            "status": "active" if not self._session.closed else "closed",
            "timeout": self._session.timeout.total,
            "connector_limit": self._session.connector.limit,
            "proxy_configured": bool(self.proxy_config),
            "tls_profile_configured": bool(self.tls_profile)
        }
