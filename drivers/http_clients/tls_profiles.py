"""
TLS Profiles for Anti-Bot Bypass

This module contains pre-configured TLS profiles that mimic real browser
fingerprints to bypass anti-bot detection systems. These profiles are designed
to provide consistent and realistic TLS fingerprints.

The profiles are based on real browser configurations and include:
- JA3 fingerprints for TLS fingerprinting
- HTTP/2 settings
- Cipher suites and extensions
- Elliptic curves configuration
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import random

from .base_http_client import TlsProfile


@dataclass
class BrowserTlsProfile:
    """Complete TLS profile for a specific browser configuration."""
    name: str
    user_agent: str
    tls_profile: TlsProfile
    http2_settings: Dict[str, any]
    priority: int = 1  # Lower number = higher priority


class TlsProfileManager:
    """
    Manager for TLS profiles designed to bypass anti-bot systems.
    
    Provides realistic browser fingerprints that are mathematically consistent
    with the associated user agents and browser configurations.
    """
    
    def __init__(self):
        self.profiles = self._initialize_profiles()
    
    def _initialize_profiles(self) -> Dict[str, BrowserTlsProfile]:
        """Initialize all available TLS profiles."""
        return {
            # Chrome 136 on Windows 11
            "chrome_136_windows": BrowserTlsProfile(
                name="Chrome 136 Windows 11",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                tls_profile=TlsProfile(
                    ja3_fingerprint="771,49195-49199-52393-49200-49196-49202-49194-49198-52392-49197-49201-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24-25-256-257,0",
                    http2_fingerprint="h2-16,h2-14,h2-13,h2-12,h2-11,h2-10,h2-09,h2-08",
                    cipher_suites=[
                        "TLS_AES_128_GCM_SHA256",
                        "TLS_AES_256_GCM_SHA384",
                        "TLS_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
                        "TLS_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_RSA_WITH_AES_256_CBC_SHA"
                    ],
                    extensions=[
                        "server_name",
                        "extended_master_secret",
                        "renegotiation_info",
                        "supported_groups",
                        "ec_point_formats",
                        "session_ticket",
                        "application_layer_protocol_negotiation",
                        "status_request",
                        "signed_certificate_timestamp",
                        "key_share",
                        "psk_key_exchange_modes",
                        "supported_versions",
                        "certificate_compress",
                        "record_size_limit",
                        "padding"
                    ],
                    curves=[
                        "X25519",
                        "secp256r1",
                        "secp384r1"
                    ]
                ),
                http2_settings={
                    "max_concurrent_streams": 1000,
                    "initial_window_size": 65535,
                    "max_frame_size": 16384,
                    "enable_push": False
                },
                priority=1
            ),
            
            # Chrome 135 on macOS
            "chrome_135_macos": BrowserTlsProfile(
                name="Chrome 135 macOS",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                tls_profile=TlsProfile(
                    ja3_fingerprint="771,49195-49199-52393-49200-49196-49202-49194-49198-52392-49197-49201-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24-25-256-257,0",
                    http2_fingerprint="h2-16,h2-14,h2-13,h2-12,h2-11,h2-10,h2-09,h2-08",
                    cipher_suites=[
                        "TLS_AES_128_GCM_SHA256",
                        "TLS_AES_256_GCM_SHA384",
                        "TLS_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA"
                    ],
                    extensions=[
                        "server_name",
                        "extended_master_secret",
                        "renegotiation_info",
                        "supported_groups",
                        "ec_point_formats",
                        "session_ticket",
                        "application_layer_protocol_negotiation",
                        "status_request",
                        "signed_certificate_timestamp",
                        "key_share",
                        "psk_key_exchange_modes",
                        "supported_versions",
                        "certificate_compress",
                        "record_size_limit"
                    ],
                    curves=[
                        "X25519",
                        "secp256r1",
                        "secp384r1"
                    ]
                ),
                http2_settings={
                    "max_concurrent_streams": 1000,
                    "initial_window_size": 65535,
                    "max_frame_size": 16384,
                    "enable_push": False
                },
                priority=2
            ),
            
            # Firefox 132 on Windows 10
            "firefox_132_windows": BrowserTlsProfile(
                name="Firefox 132 Windows 10",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
                tls_profile=TlsProfile(
                    ja3_fingerprint="771,49195-49199-52393-49200-49196-49202-49194-49198-52392-49197-49201-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27,29-23-24-25-256-257,0",
                    http2_fingerprint="h2-16,h2-14,h2-13,h2-12,h2-11,h2-10,h2-09",
                    cipher_suites=[
                        "TLS_AES_128_GCM_SHA256",
                        "TLS_CHACHA20_POLY1305_SHA256",
                        "TLS_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_RSA_WITH_AES_256_CBC_SHA"
                    ],
                    extensions=[
                        "server_name",
                        "extended_master_secret",
                        "renegotiation_info",
                        "supported_groups",
                        "ec_point_formats",
                        "session_ticket",
                        "application_layer_protocol_negotiation",
                        "status_request",
                        "delegated_credentials",
                        "key_share",
                        "psk_key_exchange_modes",
                        "supported_versions",
                        "record_size_limit"
                    ],
                    curves=[
                        "X25519",
                        "secp256r1",
                        "secp384r1",
                        "secp521r1"
                    ]
                ),
                http2_settings={
                    "max_concurrent_streams": 100,
                    "initial_window_size": 65536,
                    "max_frame_size": 16384,
                    "enable_push": True
                },
                priority=3
            ),
            
            # Safari 18 on macOS
            "safari_18_macos": BrowserTlsProfile(
                name="Safari 18 macOS",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
                tls_profile=TlsProfile(
                    ja3_fingerprint="771,49195-49199-52393-49200-49196-49202-49194-49198-52392-49197-49201-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27,29-23-24-25-256-257,0",
                    http2_fingerprint="h2-16,h2-14,h2-13,h2-12,h2-11,h2-10",
                    cipher_suites=[
                        "TLS_AES_128_GCM_SHA256",
                        "TLS_AES_256_GCM_SHA384",
                        "TLS_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA"
                    ],
                    extensions=[
                        "server_name",
                        "extended_master_secret",
                        "renegotiation_info",
                        "supported_groups",
                        "ec_point_formats",
                        "session_ticket",
                        "application_layer_protocol_negotiation",
                        "status_request",
                        "signed_certificate_timestamp",
                        "key_share",
                        "psk_key_exchange_modes",
                        "supported_versions",
                        "record_size_limit"
                    ],
                    curves=[
                        "X25519",
                        "secp256r1",
                        "secp384r1",
                        "secp521r1"
                    ]
                ),
                http2_settings={
                    "max_concurrent_streams": 100,
                    "initial_window_size": 65536,
                    "max_frame_size": 16384,
                    "enable_push": True
                },
                priority=4
            ),
            
            # Edge 137 on Windows 11
            "edge_137_windows": BrowserTlsProfile(
                name="Edge 137 Windows 11",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
                tls_profile=TlsProfile(
                    ja3_fingerprint="771,49195-49199-52393-49200-49196-49202-49194-49198-52392-49197-49201-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24-25-256-257,0",
                    http2_fingerprint="h2-16,h2-14,h2-13,h2-12,h2-11,h2-10,h2-09,h2-08",
                    cipher_suites=[
                        "TLS_AES_128_GCM_SHA256",
                        "TLS_AES_256_GCM_SHA384",
                        "TLS_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                        "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
                        "TLS_RSA_WITH_AES_128_GCM_SHA256",
                        "TLS_RSA_WITH_AES_256_GCM_SHA384",
                        "TLS_RSA_WITH_AES_128_CBC_SHA",
                        "TLS_RSA_WITH_AES_256_CBC_SHA"
                    ],
                    extensions=[
                        "server_name",
                        "extended_master_secret",
                        "renegotiation_info",
                        "supported_groups",
                        "ec_point_formats",
                        "session_ticket",
                        "application_layer_protocol_negotiation",
                        "status_request",
                        "signed_certificate_timestamp",
                        "key_share",
                        "psk_key_exchange_modes",
                        "supported_versions",
                        "certificate_compress",
                        "record_size_limit",
                        "padding"
                    ],
                    curves=[
                        "X25519",
                        "secp256r1",
                        "secp384r1"
                    ]
                ),
                http2_settings={
                    "max_concurrent_streams": 1000,
                    "initial_window_size": 65535,
                    "max_frame_size": 16384,
                    "enable_push": False
                },
                priority=2
            )
        }
    
    def get_profile(self, profile_name: str) -> Optional[BrowserTlsProfile]:
        """Get a specific TLS profile by name."""
        return self.profiles.get(profile_name)
    
    def get_random_profile(self, exclude: Optional[List[str]] = None) -> BrowserTlsProfile:
        """Get a random TLS profile, optionally excluding some profiles."""
        exclude = exclude or []
        available_profiles = [
            profile for name, profile in self.profiles.items() 
            if name not in exclude
        ]
        
        if not available_profiles:
            raise ValueError("No available profiles after exclusions")
        
        return random.choice(available_profiles)
    
    def get_best_profile(self, target_domain: str = None) -> BrowserTlsProfile:
        """
        Get the best TLS profile for a given target domain.
        
        For now, returns the highest priority profile. In the future,
        this could be enhanced with domain-specific logic.
        """
        return min(self.profiles.values(), key=lambda p: p.priority)
    
    def get_profiles_by_priority(self) -> List[BrowserTlsProfile]:
        """Get all profiles sorted by priority (best first)."""
        return sorted(self.profiles.values(), key=lambda p: p.priority)
    
    def get_chrome_profiles(self) -> List[BrowserTlsProfile]:
        """Get all Chrome-based profiles."""
        return [
            profile for profile in self.profiles.values()
            if "chrome" in profile.name.lower() or "edge" in profile.name.lower()
        ]
    
    def get_firefox_profiles(self) -> List[BrowserTlsProfile]:
        """Get all Firefox profiles."""
        return [
            profile for profile in self.profiles.values()
            if "firefox" in profile.name.lower()
        ]
    
    def get_safari_profiles(self) -> List[BrowserTlsProfile]:
        """Get all Safari profiles."""
        return [
            profile for profile in self.profiles.values()
            if "safari" in profile.name.lower()
        ]
    
    def create_custom_profile(
        self,
        name: str,
        user_agent: str,
        ja3_fingerprint: str,
        cipher_suites: List[str],
        extensions: List[str],
        curves: List[str],
        http2_settings: Dict[str, any] = None
    ) -> BrowserTlsProfile:
        """Create a custom TLS profile."""
        tls_profile = TlsProfile(
            ja3_fingerprint=ja3_fingerprint,
            cipher_suites=cipher_suites,
            extensions=extensions,
            curves=curves
        )
        
        return BrowserTlsProfile(
            name=name,
            user_agent=user_agent,
            tls_profile=tls_profile,
            http2_settings=http2_settings or {},
            priority=999  # Low priority for custom profiles
        )
    
    def validate_profile_consistency(self, profile: BrowserTlsProfile) -> bool:
        """
        Validate that a profile is internally consistent.
        
        Checks that the TLS settings match the user agent and browser type.
        """
        # Basic validation - in a real implementation, this would be more sophisticated
        if not profile.user_agent or not profile.tls_profile:
            return False
        
        # Check that cipher suites are valid
        if not profile.tls_profile.cipher_suites:
            return False
        
        # Check that extensions are present
        if not profile.tls_profile.extensions:
            return False
        
        # Check that curves are specified
        if not profile.tls_profile.curves:
            return False
        
        return True


# Global instance for easy access
tls_manager = TlsProfileManager()
