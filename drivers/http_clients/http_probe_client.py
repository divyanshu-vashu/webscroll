from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import httpx


@dataclass
class HttpProbeResponse:
    status_code: int
    text: str
    headers: Dict[str, str] = field(default_factory=dict)
    final_url: str = ""
    cookies: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    transport: str = "httpx"

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300 and not self.error


class HttpProbeClient:
    def __init__(self, timeout: int = 25):
        self.timeout = timeout

    def fetch(self, url: str, *, headers: Optional[Dict[str, str]] = None, proxy: Optional[Dict[str, str]] = None) -> HttpProbeResponse:
        headers = headers or {}
        proxy_url = None
        if proxy and proxy.get("server"):
            server = proxy["server"]
            user = proxy.get("username")
            password = proxy.get("password")
            if user and password and "@" not in server:
                proxy_url = server.replace("://", f"://{user}:{password}@")
            else:
                proxy_url = server

        try:
            try:
                from curl_cffi import requests as curl_requests

                with curl_requests.Session(impersonate="chrome") as session:
                    response = session.get(
                        url,
                        headers=headers,
                        proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None,
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                    return HttpProbeResponse(
                        status_code=response.status_code,
                        text=response.text or "",
                        headers=dict(response.headers),
                        final_url=str(response.url),
                        cookies=response.cookies.get_dict(),
                        transport="curl_cffi",
                    )
            except Exception:
                with httpx.Client(
                    timeout=self.timeout,
                    headers=headers,
                    proxies=proxy_url,
                    follow_redirects=True,
                    http2=True,
                ) as client:
                    response = client.get(url)
                    return HttpProbeResponse(
                        status_code=response.status_code,
                        text=response.text or "",
                        headers=dict(response.headers),
                        final_url=str(response.url),
                        cookies=dict(response.cookies),
                        transport="httpx",
                    )
        except Exception as exc:
            return HttpProbeResponse(status_code=0, text="", error=str(exc))
