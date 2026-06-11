"""
Test script for HTTP clients

This script demonstrates the usage of the HTTP client implementations
with TLS profiles for anti-bot bypass.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from drivers.http_clients import HttpxClient, AiohttpClient, tls_manager


async def test_httpx_client():
    """Test the httpx client with TLS profiles."""
    print("Testing HttpxClient...")
    
    # Get the best TLS profile
    profile = tls_manager.get_best_profile()
    print(f"Using profile: {profile.name}")
    print(f"User-Agent: {profile.user_agent}")
    
    # Create client with TLS profile and matching headers
    headers = {
        'User-Agent': profile.user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    async with HttpxClient(
        timeout=30,
        max_retries=3,
        tls_profile=profile.tls_profile,
        headers=headers,
        http2=True
    ) as client:
        try:
            # Test with a simple website
            response = await client.get("https://httpbin.org/user-agent")
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")
            print(f"Headers: {dict(response.headers)}")
            
            if response.is_success:
                print("✓ Request successful!")
                print(f"Response preview: {response.text[:200]}...")
            else:
                print(f"✗ Request failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_aiohttp_client():
    """Test the aiohttp client with TLS profiles."""
    print("\nTesting AiohttpClient...")
    
    # Get a random TLS profile
    profile = tls_manager.get_random_profile()
    print(f"Using profile: {profile.name}")
    print(f"User-Agent: {profile.user_agent}")
    
    # Create client with TLS profile and matching headers
    headers = {
        'User-Agent': profile.user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    async with AiohttpClient(
        timeout=30,
        max_retries=3,
        tls_profile=profile.tls_profile,
        headers=headers
    ) as client:
        try:
            # Test with a simple website
            response = await client.get("https://httpbin.org/headers")
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")
            
            if response.is_success:
                print("✓ Request successful!")
                print(f"Response preview: {response.text[:200]}...")
            else:
                print(f"✗ Request failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_tls_profiles():
    """Test TLS profile management."""
    print("\nTesting TLS Profile Manager...")
    
    # List all available profiles
    profiles = tls_manager.get_profiles_by_priority()
    print(f"Available profiles ({len(profiles)}):")
    for profile in profiles:
        print(f"  - {profile.name} (Priority: {profile.priority})")
    
    # Test Chrome profiles
    chrome_profiles = tls_manager.get_chrome_profiles()
    print(f"\nChrome profiles ({len(chrome_profiles)}):")
    for profile in chrome_profiles:
        print(f"  - {profile.name}")
    
    # Test Firefox profiles
    firefox_profiles = tls_manager.get_firefox_profiles()
    print(f"\nFirefox profiles ({len(firefox_profiles)}):")
    for profile in firefox_profiles:
        print(f"  - {profile.name}")
    
    # Test profile validation
    best_profile = tls_manager.get_best_profile()
    is_valid = tls_manager.validate_profile_consistency(best_profile)
    print(f"\nProfile validation for {best_profile.name}: {'✓ Valid' if is_valid else '✗ Invalid'}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("HTTP CLIENT TESTS")
    print("=" * 60)
    
    # Test TLS profiles first
    await test_tls_profiles()
    
    # Test HTTP clients
    await test_httpx_client()
    await test_aiohttp_client()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
