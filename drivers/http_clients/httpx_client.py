"""
httpx HTTP Client Implementation

This module provides an httpx-based HTTP client with modern HTTP/2 support
and advanced TLS configuration for anti-bot bypass. httpx is chosen for its
clean API and excellent HTTP/2 support.
"""

import asyncio
from typing import Dict, Optional, Any, AsyncGenerator
import httpx
from httpx import AsyncClient, Response, Timeout

from .base_http_client import (
    BaseHttpClient, 
    HttpResponse, 
    ProxyConfig, 
    TlsProfile
)


class HttpxClient(BaseHttpClient):
    """
    httpx-based HTTP client with HTTP/2 and TLS fingerprinting capabilities.
    
    This client provides modern HTTP features including HTTP/2 support,
    connection pooling, and fine-grained TLS control for anti-bot bypass.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        proxy_config: Optional[ProxyConfig] = None,
        tls_profile: Optional[TlsProfile] = None,
        headers: Optional[Dict[str, str]] = None,
        http2: bool = True,
        limits: Optional[httpx.Limits] = None,
        verify: bool = True
    ):
        super().__init__(timeout, max_retries, proxy_config, tls_profile, headers)
        self.http2 = http2
        self.limits = limits or httpx.Limits(max_keepalive_connections=20, max_connections=100)
        self.verify = verify
        self._client: Optional[AsyncClient] = None
    
    async def _get_client(self) -> AsyncClient:
        """Get or create httpx client with custom configuration."""
        if self._client is None:
            # Configure proxy
            proxies = None
            if self.proxy_config:
                proxies = {
                    'http://': self.proxy_config.proxy_url,
                    'https://': self.proxy_config.proxy_url,
                }
            
            # Create client with advanced configuration
            self._client = AsyncClient(
                timeout=Timeout(self.timeout),
                headers=self.headers,
                proxies=proxies,
                http2=self.http2,
                limits=self.limits,
                verify=self._create_ssl_context() if self.tls_profile else self.verify,
                follow_redirects=True
            )
        
        return self._client
    
    def _create_ssl_context(self):
        """
        Create SSL context with custom TLS configuration for anti-bot bypass.
        httpx uses this for advanced TLS fingerprinting.
        """
        import ssl
        
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
            
            # Configure ALPN for HTTP/2
            if self.http2:
                context.set_alpn_protocols(['h2', 'http/1.1'])
        
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
            client = await self._get_client()
            merged_headers = self._merge_headers(headers)
            
            response = await client.get(
                url,
                params=params,
                headers=merged_headers,
                **kwargs
            )
            return self._convert_response(response)
        
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
            client = await self._get_client()
            merged_headers = self._merge_headers(headers)
            
            response = await client.post(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                **kwargs
            )
            return self._convert_response(response)
        
        return await self._retry_request(_post_request)
    
    def _convert_response(self, response: Response) -> HttpResponse:
        """Convert httpx response to standardized HttpResponse."""
        return HttpResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            url=str(response.url),
            cookies=dict(response.cookies)
        )
    
    async def close(self) -> None:
        """Close the httpx client."""
        if self._client:
            await self._client.aclose()
    
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
        client = await self._get_client()
        merged_headers = self._merge_headers(headers)
        
        async with client.stream('GET', url, headers=merged_headers) as response:
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Failed to download: {response.status_code}",
                    request=response.request,
                    response=response
                )
            
            async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                yield chunk
    
    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP HEAD request."""
        async def _head_request():
            client = await self._get_client()
            merged_headers = self._merge_headers(headers)
            
            response = await client.head(
                url,
                headers=merged_headers,
                **kwargs
            )
            return self._convert_response(response)
        
        return await self._retry_request(_head_request)
    
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP PUT request with retry logic."""
        async def _put_request():
            client = await self._get_client()
            merged_headers = self._merge_headers(headers)
            
            response = await client.put(
                url,
                data=data,
                json=json,
                headers=merged_headers,
                **kwargs
            )
            return self._convert_response(response)
        
        return await self._retry_request(_put_request)
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> HttpResponse:
        """Perform HTTP DELETE request with retry logic."""
        async def _delete_request():
            client = await self._get_client()
            merged_headers = self._merge_headers(headers)
            
            response = await client.delete(
                url,
                headers=merged_headers,
                **kwargs
            )
            return self._convert_response(response)
        
        return await self._retry_request(_delete_request)
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the current client for debugging."""
        if not self._client:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "timeout": self._client.timeout.total,
            "http2_enabled": self.http2,
            "limits": {
                "max_connections": self.limits.max_connections,
                "max_keepalive_connections": self.limits.max_keepalive_connections
            },
            "proxy_configured": bool(self.proxy_config),
            "tls_profile_configured": bool(self.tls_profile),
            "verify_ssl": self.verify
        }
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics for monitoring."""
        if not self._client:
            return {"status": "no_client"}
        
        # httpx doesn't expose detailed pool stats, but we can provide basic info
        return {
            "limits": {
                "max_connections": self.limits.max_connections,
                "max_keepalive_connections": self.limits.max_keepalive_connections,
                "keepalive_expiry": self.limits.keepalive_expiry
            }
        }
