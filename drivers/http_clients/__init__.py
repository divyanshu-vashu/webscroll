"""
HTTP Clients Module

This module provides HTTP client implementations with advanced TLS fingerprinting
and anti-bot bypass capabilities. All clients implement the BaseHttpClient interface
for consistency and can be used interchangeably.

Available clients:
- HttpxClient: Modern HTTP client with HTTP/2 support
- AiohttpClient: High-performance async HTTP client
- CurlCffiClient: Advanced TLS impersonation (when implemented)

Usage:
    from drivers.http_clients import HttpxClient, AiohttpClient
    from drivers.http_clients.tls_profiles import tls_manager
    
    # Get a TLS profile
    profile = tls_manager.get_best_profile()
    
    # Create client with TLS profile
    client = HttpxClient(tls_profile=profile.tls_profile)
    
    # Make request
    response = await client.get("https://example.com")
"""

from .base_http_client import (
    BaseHttpClient,
    HttpResponse,
    ProxyConfig,
    TlsProfile
)

from .httpx_client import HttpxClient
from .aiohttp_client import AiohttpClient
from .http_probe_client import HttpProbeClient
from .tls_profiles import (
    TlsProfileManager,
    BrowserTlsProfile,
    tls_manager
)

__all__ = [
    # Base classes and data structures
    "BaseHttpClient",
    "HttpResponse", 
    "ProxyConfig",
    "TlsProfile",
    
    # Client implementations
    "HttpxClient",
    "AiohttpClient",
    "HttpProbeClient",
    
    # TLS profile management
    "TlsProfileManager",
    "BrowserTlsProfile", 
    "tls_manager"
]
