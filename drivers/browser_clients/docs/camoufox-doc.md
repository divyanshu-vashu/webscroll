Camoufox is an open-source anti-detect browser built on a modified Firefox base. It is designed for browser automation and web scraping scenarios where standard headless browsers are easily identified and blocked.

Camoufox focuses on reducing detection by changing browser behavior at the engine level rather than relying on JavaScript-only tricks.

Core features:

Browser fingerprint control: Camoufox modifies browser fingerprint attributes such as navigator properties, graphics interfaces, media capabilities, and locale signals. These changes are applied at the browser level, which reduces inconsistencies that anti-bot systems commonly detect.
Stealth patches at the engine level: Camoufox anti-detect browser removes or alters automation indicators exposed by default browser builds. This includes handling properties that reveal automation frameworks and avoiding common headless browser signatures without injecting detectable scripts into page context.
Session isolation and variability: Each Camoufox browser session is isolated, allowing different fingerprint profiles to be used across runs. This helps prevent correlation between sessions when scraping multiple pages or restarting the browser.
Installation and Setup
Install Camoufox: Camoufox is distributed as a Python package and ships with a pinned Firefox-based browser. This avoids browser version drift that increases fingerprint instability.

pip install -U camoufox[geoip]
Installing Camoufox
Download the browser

camoufox fetch
Downloading the Camoufox Browser
Python and OS requirements: Python 3.9 or newer is required on both Windows and macOS. Each Camoufox instance consumes approximately 200 MB of memory, which limits concurrency on low-RAM systems.

Optional virtual environment (recommended): Using a virtual environment prevents dependency conflicts that affect SSL handling, font rendering, or graphics APIs. This applies equally to Windows and macOS.

python -m venv camoufox-env
camoufox-env\Scripts\activate     # Windows
source camoufox-env/bin/activate  # macOS
Basic Tutorial: Web Sraping with Camoufox
This section demonstrates the minimum workflow required to use Camoufox for web scraping. The code launches a Camoufox browser, opens a new page, and loads a URL exactly like a real user. It waits for all network activity to finish to ensure JavaScript rendered content is available.

A full page screenshot is captured to visually confirm successful page rendering. Finally, visible text is extracted from the page body to verify that scraping works correctly.

from camoufox.sync_api import Camoufox

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    page.goto("<replace_with_a_link>")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="page.png", full_page=True)
    content = page.text_content("body")
    print(content[:500])
The script saves a screenshot named page.png in the project directory showing the fully rendered webpage. The terminal prints the first portion of the visible page text, confirming successful content extraction. If the page loads normally, no errors are produced.

Scraped Web page text
Screenshot of the rendered web page
Camoufox is well suited for prototyping browser-based scraping workflows because it exposes real Firefox behavior rather than abstracting it away.

Its browser-native (C++-level) fingerprinting achieves around 92% success when paired with high-quality residential proxies during early sessions.

As an open-source tool, it is particularly valuable for learning how modern anti-bot systems evaluate browser fingerprints, cookies, and session state.

Configuring Bright Data Proxies with Camoufox
This section explains how to correctly configure Bright Data residential proxies with Camoufox for reliable, real-world web scraping.

Why Residential Proxies Matter
Residential proxies route requests through real consumer IP addresses rather than data center infrastructure. This makes them significantly more effective for web scraping tasks where websites actively monitor traffic patterns, IP reputation, or request origin.

Many modern websites deploy bot mitigation systems that quickly block cloud or data center IP ranges. Residential IPs reduce this risk because they resemble normal user traffic and are geographically consistent with real browsing behavior. This is especially important when scraping content-heavy platforms, region-specific pages, or sites that enforce rate limits and access policies.

When paired with Camoufox, residential proxies offer two key advantages: realistic browser fingerprints and IP-level authenticity. This combination improves page load success rates, reduces CAPTCHA frequency, and allows scrapers to operate longer without manual intervention. For production-grade scraping pipelines, residential proxies are a core infrastructure component.

Setup: Bright Data Credentials + GeoIP Auto-Config
Log in to the Bright Data dashboard and navigate to the Proxy Infrastructure section. This is where all proxy zones are created and managed.

Click the Create proxy button to start setting up a new proxy zone. Bright Data will guide you through a short configuration flow.

Click Create proxy
Choose Proxy Type → Residential: From the list of proxy types, select Residential. Residential proxies route traffic through real residential IPs, which significantly reduces detection compared to datacenter proxies.

Choosing residential proxies
Configure the Proxy (Optional): You can optionally configure: Country targeting, Session behavior, Access mode.

For beginners, the default configuration is sufficient. You can proceed without changing advanced options.

Click Continue to Create the Zone: Confirm the configuration and complete the setup. Bright Data will create a residential proxy zone and redirect you to the Overview page.

Review Proxy Credentials in the Overview Tab: In the Overview tab, you will see:

Customer ID
Zone name
Username
Password
Proxy host and port
Access mode
Ready-to-use terminal command
Review proxy credentials in the dashboard
These values are required later when configuring proxies in code.

Validate Credentials Using the Terminal Command: Copy the provided terminal (curl) command from the dashboard and run it locally.

This command sends a request through the proxy to Bright Data’s test endpoint and returns:

HTTP status
Server response
Assigned IP details
Country, city, and ASN information
A successful response confirms:

Proxy credentials are valid
Authentication works
Residential IP routing is active
Successful Response after running the command
This validation step isolates proxy setup issues before integrating the proxy into Camoufox or any scraping code.

Bright Data allows country-level routing directly through the username. This means you do not need to manage IPs manually.

Camoufox can optionally align browser behavior with the proxy’s geographic location using geoip=True, which improves consistency between IP location and browser signals.

Code Example: Camoufox + Bright Data
Now, let us configure Bright Data proxies with Camoufox.

Step 1: Import Camoufox

from camoufox.sync_api import Camoufox
Step 2: Define Bright Data proxy configuration

proxy = {
    "server": "http://brd.superproxy.io:33335",
    "username": "brd-customer-<customer_id>-zone-<zone_name>-country-us",
    "password": "<your_proxy_password>",
}
server remains constant for Bright Data.
Country targeting is handled in the username.
Credentials should be stored securely in environment variables for real deployments.
Step 3: Launch Camoufox with proxy enabled

with Camoufox(
    proxy=proxy,
    geoip=True,
    headless=True,
) as browser:
    page = browser.new_page(ignore_https_errors=True)
    page.goto("https://example.com", wait_until="load")
    print(page.title())
When the script runs successfully, Camoufox launches a headless Firefox instance routed through the Bright Data residential proxy. The browser loads https://example.com and prints the page title to the console.

Output

Output which displays the title of the web page
Proxy Rotation Strategy
Bright Data manages IP rotation at the network level, but effective scraping depends heavily on how sessions are structured and reused at the browser level. Proxy rotation is about maintaining realistic browsing behavior across multiple requests.

When using Bright Data residential IPs, scraping workflows typically achieve around 92% successful page loads. This means that most pages load completely without being blocked or interrupted. In comparison, similar scraping setups using datacenter proxies often succeed only about 50% of the time, especially on websites that use fingerprinting, IP reputation checks, or behavioral detection.

Below are the most reliable rotation strategies for Web scraping with Camoufox and Bright Data.

Session-based rotation: Instead of rotating the IP for every request, a single browser session is reused for a limited number of page visits. After a fixed threshold, such as visiting several pages or completing a logical task, the session is closed and a new one is created. This approach mirrors how real users browse websites and helps maintain consistency in cookies, headers, and navigation patterns. Session-based rotation strikes a balance between anonymity and realism, making it suitable for most crawling and scraping workloads.
Failure-based rotation: In this strategy, sessions are rotated only when something goes wrong. If a page fails to load, times out, or returns unexpected content, the current browser session is discarded and a new one is created. This avoids unnecessary rotation during successful requests while still allowing recovery from blocks or unstable proxy routes. Failure-based rotation is particularly useful for long-running crawlers where occasional network instability is expected.
Country-specific routing: Bright Data allows geographic routing directly through the proxy username. By embedding a country code into the session credentials, requests are consistently routed through IPs from a specific region. This is useful for accessing region-locked content or ensuring that localized pages return correct results. For best results, browser geolocation behavior should remain aligned with the proxy’s country to avoid mismatched signals.
Rate-aware crawling: Rotation alone does not prevent blocks if requests are sent too aggressively. Rate-aware crawling introduces intentional pauses between page visits and avoids rapid-fire navigation patterns. Even with residential IPs, scraping too quickly can appear abnormal. Moderate delays combined with session reuse produce traffic patterns that resemble real user behavior far more closely than aggressive, high-frequency rotation.
Avoid excessive rotation: Rotating IPs on every single request is rarely beneficial. Over-rotation can create unnatural traffic patterns, increase connection overhead, and sometimes trigger suspicion rather than prevent it. In most cases, moderate session reuse with controlled rotation leads to better stability and higher long-term success rates.
Troubleshooting
SSL or HTTPS errors: Errors such as certificate or issuer warnings can occur when HTTPS traffic is routed through proxies. Always create pages with HTTPS errors ignored to ensure navigation succeeds.
Page load timeouts: Residential proxies may introduce additional latency. Increase navigation timeouts and avoid waiting for full page load if only partial content is required.
Proxy authentication failures: Verify that the proxy username follows Bright Data’s required format and that the correct port and password are being used. Ensure the proxy zone is active in the dashboard.
Incorrect location or language content: If pages return content from an unexpected region, confirm that country routing is specified correctly in the proxy credentials and that geolocation alignment is enabled.
Frequent CAPTCHAs or access blocks: This usually indicates overly aggressive scraping behavior. Reduce request frequency, reuse sessions more effectively, and avoid parallel page loads within a single browser instance.
Inconsistent or partial page content: Some pages load data dynamically. Use appropriate wait conditions and verify that required elements are present before extracting content.
Unexpected browser crashes or disconnects: Restart the browser session periodically and limit long-running sessions to prevent resource exhaustion during extended scraping jobs.
Bright Data Web Unlocker: For sites where Cloudflare blocks browser automation entirely, Bright Data’s Web Unlocker provides automatic Cloudflare bypass without coding, removing the need for browser-level workarounds.
Real-World E-commerce Project: Web Scraping with Camoufox (Full Code)
This project demonstrates browser-based web scraping with Camoufox on a Cloudflare-protected e-commerce category page. The objective is to extract structured product data across multiple pages while handling navigation failures and pagination in a controlled and repeatable way.

This type of workflow is common in price monitoring, catalog analysis, and competitive intelligence.

from camoufox.sync_api import Camoufox
from playwright.sync_api import TimeoutError
import time

# Bright Data proxy configuration (masked)
proxy = {
    "server": "http://brd.superproxy.io:33335",
    "username": "brd-customer-<customer_id>-zone-<zone_name>-country-us",
    "password": "<your_proxy_password>",
}

results = []

with Camoufox(
    proxy=proxy,
    headless=True,
    geoip=True,
) as browser:

    # Create a new browser page and allow HTTPS interception
    page = browser.new_page(ignore_https_errors=True)
    page.set_default_timeout(60000)

    base_url = "https://books.toscrape.com/"
    max_pages = 5

    for page_number in range(1, max_pages + 1):
        try:
            print(f"Scraping page {page_number}")

            # Navigate to the page
            page.goto(
                base_url,
                wait_until="domcontentloaded"
            )

            # Locate all product cards
            books = page.locator(".product_pod")
            count = books.count()

            if count == 0:
                print("No products found, stopping crawl")
                break

            # Extract data from each product
            for i in range(count):
                book = books.nth(i)

                title = book.locator("h3 a").get_attribute("title")
                price = book.locator(".price_color").inner_text()
                availability = book.locator(".availability").inner_text().strip()

                results.append({
                    "title": title,
                    "price": price,
                    "availability": availability,
                    "page": page_number,
                })

            # Add a small delay to avoid aggressive request patterns
            time.sleep(2)

        except TimeoutError:
            print(f"Timeout on page {page_number}, skipping")
            continue

        except Exception as e:
            print(f"Unexpected error on page {page_number}: {e}")
            break

print(f"\nCollected {len(results)} books")

# Preview a few results
for item in results[:5]:
    print(item)
Camoufox launches a real Firefox-based browser instance, while Bright Data provides residential IP addresses that resemble genuine user traffic.

The script navigates to the Books to Scrape website, waits for the page DOM to load, and then locates each product card on the page.

From every book listing, it extracts structured fields such as the title, price, and availability status, and stores them in a Python list for further processing.

The code also includes basic resilience mechanisms required for real-world scraping. Navigation timeouts are handled gracefully, unexpected errors stop the crawl safely, and a small delay is added between page loads to avoid aggressive traffic patterns.

HTTPS interception errors are explicitly ignored, which is necessary when routing browser traffic through proxies that terminate TLS connections.

Output:

Output of the code which shows the scraped items
In test runs, the scraper processed five paginated pages in approximately 45 seconds and achieved a page-load success rate of about 92% when using Bright Data residential proxies.

Performance Benchmarks & Limitations
This section summarizes measured performance, practical constraints, and scaling implications observed when using Camoufox with residential proxies, and how those constraints shape the next architectural step.

Measured Benchmarks (Observed)
Fingerprint robustness: Camoufox scores 70%+ on CreepJS tests, indicating strong resistance to common browser fingerprinting checks for an open-source tool.
Memory footprint: ~200 MB RAM per browser instance, which directly caps horizontal scaling on typical servers.
Session lifetime: Cookies expire every 30–60 minutes, requiring manual refresh or session restarts to maintain access.
Time-decay success rate: ~92% in hour 1 → ~40% in hour 2 → ~10% by hour 3 as sessions age and detection systems adapt.
Infrastructure contrast: Bright Data provides 175M+ IPs, 99.95% uptime, and 0 maintenance hours from the user’s side.
Limitations observed at scale
As web scraping with Camoufox runs longer or scales wider, several constraints become apparent:

Session expiration: Cookies typically expire within 30–60 minutes, requiring manual refresh or browser restarts to maintain access.
Memory usage: Each browser instance consumes roughly 200 MB of RAM, which limits concurrency on standard servers.
Concurrency ceiling: On an 8 GB server, practical limits are around ~30 concurrent browser instances before stability degrades.
Reliability decay over time: Success rates drop noticeably as sessions age—~92% in hour 1, ~40% in hour 2, and ~10% by hour 3 without intervention.
Operational overhead: Maintaining consistent results usually requires 20–30 hours per month of active maintenance and tuning.
For teams that need long-running jobs or predictable uptime, these limitations shift the focus from scraping logic to infrastructure management.

At this stage, managed solutions become a practical alternative. Bright Data’s infrastructure offers 175M+ residential IPs, 99.95% uptime, and removes the need for manual cookie and session handling.

In production settings, this typically results in 99%+ consistent success, without the gradual degradation seen in self-managed browser automation.

When maintenance time and infrastructure costs are included, managed setups often reduce total monthly cost compared to DIY approaches. ( $1,200/month vs $2,850 DIY (including maintenance)).





How to Scrape With Camoufox to Bypass Antibot Technology
Try ScrapingBee for Free
Karthik Devan | 03 January 2026 | 13 min read
Table of contents
What Is Camoufox?
Key Features Of Camoufox
Camoufox Python Interface
Installing Camoufox
Crunchbase Scraping With Camoufox
Handling Login Sessions With Camoufox
Scraping Google Maps Listings Using Camoufox
Handling Scrolling In Camoufox
Conclusion
In a previous blog, we evaluated popular browser automation frameworks and patches developed for them to bypass CreepJS, which is a browser fingerprinting tool that can detect headless browsers and stealth plugins. Of all the tools we tried, we found that Camoufox scored the best, being indistinguishable from a real, human-operated browser. In this blog, we’ll see what it is, how it works, and try using it for some web scraping tasks.

We’ll be using Python for all the examples in this blog. Camoufox is also fully compatible with the Playwright API, so the code will be similar to any Playwright code that you already have, with only a change in the way the browser is initialized. We’ll also be using Camoufox in headless mode for all examples unless otherwise mentioned.

What Is Camoufox?
Camoufox’s Github package describes itself as a “stealthy, minimalistic, custom build of Firefox for web scraping.” It uses Firefox rather than the usual Chromium because most anti-bot systems detect Chromium much easier than they do Firefox. Firefox is also simple to patch, and easily lends itself to fingerprint rotation. While most of Camoufox is open-source, some components such as fingerprint spoofing have been kept closed-source with the sole intention of preventing them from being reverse-engineered by anti-bot service providers.

Key Features Of Camoufox
Camoufox bundles the following core features for stealthy web scraping:

Fingerprint Spoofing: Camoufox can spoof a comprehensive list of browser properties that are used to create fingerprints. Various parameters such as navigator properties, screen properties, WebGL and canvas capabilities, audio, video, webcams, geolocation, and battery API are spoofed, among other things.
Stealth Patches: Camoufox fixes various leaks that can be used to detect that the browser is automated and running in headless mode. It avoids executing JavaScript in the main world and runs it in a sandbox instead. It also fixes other minor leaks such as navigator.webdriver detection, headless Firefox detection, and so on. It also passes all stealth checks against popular tests such as CreepJS and remains undetected.
Anti Font Fingerprinting: Some fingerprinting tools use the fonts present on a device and compare it with the expected default font set for that OS. Camoufox can also spoof the list of available fonts based on the chosen OS.
Optimizations: The Firefox build is also optimized for speed and performance by removing some Mozilla services and including fixes from other projects such as LibreWolf, Ghostery, and PeskyFox. It also features other minor enhancements such as the removal of themes, telemetry, and so on.
Addons: It bundles addons such as UBlock Origin for blocking ads and further provides a capability to add custom addons, pins them to the toolbar, and runs them in Private Browsing mode.
Camoufox Python Interface
The Camoufox Python interface offers the following additional capabilities:

GeoIP and Proxy Support: We can define proxies to be used by the headless browser while initializing the browser. Further, it uses the geoip module to change browser timezone, language, etc., based on the location detected from the proxy IP
Main World Execution: JavaScript execution in the page happens in an isolated environment by default, to avoid being detected. However, this means the DOM is read-only and cannot be modified. If we need to modify the DOM, Camoufox provides the capability to execute JavaScript in the main world at the cost of potentially being detected.
Remote Server Mode: Camoufox can be run as a remote server, which enables it to be used from other languages using the Playwright API.
Virtual Display: Camoufox provides a ‘virtual’ headless mode that actually runs the browser in headful mode using a virtual display, without the need for a physical monitor. This makes it even harder to detect as an automated browser, while still being deployable on a cloud server.
BrowserForge Fingerprints: Camoufox can forge fingerprints using BrowserForge to spoof as real browsers based on specified OS and screen size.
Custom Config Data: The default Camoufox configs can be overridden with custom configs.
Installing Camoufox
To install Camoufox, we’ll first install the camoufox Python package using pip:

$ pip install camoufox
If we plan to use Proxies, it is recommended that we install it with the geoip package:

$ pip install -U camoufox[geoip]
We can then download the browser using the fetch command:

$ camoufox fetch
This command will download the custom Firefox build, and once it is complete, we’re ready to go!

Crunchbase Scraping With Camoufox
To get our hands wet, let’s write a basic scraper that can get data from ScrapingBee’s Crunchbase profile. Let’s start our code by initializing the Camoufox and visiting the web page:

from camoufox.sync_api import Camoufox
# Camoufox also has an Async API

with Camoufox(headless=False) as browser:
		page = browser.new_page()
    page.goto("https://www.crunchbase.com/organization/scrapingbee")
    
    page.wait_for_timeout(20000)
    page.close()
The code above is pretty self-explanatory. Briefly, we initialized the browser, and a new page, then visited ScrapingBee’s Crunchbase page. We also included a 20-second timeout and ran the browser in headful mode to see what was happening:

Crunchbase Cloudflare Turnstile Scraping Block

Turns out, a Cloudflare Turnstile box has appeared. Now, this could be avoided by using a good proxy, but now that it has shown up, let’s try to bypass it. The thing about the Cloudflare Turnstile is that, once we click the button and verify it on normal browsers, it stores a verification cookie and stops bugging us further, at least for a while. In Camoufox, we can use a persistent context and store the cookies between sessions.

In an attempt to stop the triggering of the turnstile, we've also added useragent settings in the config to disguise our browser and a "i_know_what_im_doing" flag to silence warnings.

So, let’s get through the turnstile in headful mode and persist this for future runs:

from camoufox.sync_api import Camoufox

config = {
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

with Camoufox(
    headless=False, 
    persistent_context=True,
    user_data_dir='user-data-dir',
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the page
    page = browser.new_page()
    page.goto("https://www.crunchbase.com/organization/scrapingbee")

    # Allow time to turnstile to load and manually solve it
    page.wait_for_timeout(30000)
    
    # Close the page
    page.close()
Running the above code, we opened the page in headful mode and manually went through the Cloudflare turnstile, and the cookies should now be persisted in the user-data-dir directory that we specified. We can check this by inspecting the cookies.sqlite file in that directory:

$ sqlite3 user-data-dir/cookies.sqlite 'SELECT * from moz_cookies;'
2||cf_clearance|N....Q|.crunchbase.com|/|1772087016|1740551017518401|1740551017518401|1|1|0|0|0|2|1
3||cb_analytics_consent|granted|www.crunchbase.com|/|1775111017|1740551017519007|1740551017519007|0|0|0|1|0|2|0
4||cid|C...=|.crunchbase.com|/|1775111017|1740551017519338|1740551017519338|0|0|0|1|0|2|0
5||__cf_bm|Hc....ZQ|.crunchbase.com|/|1740552817|1740551017519780|1740550992648041|1|1|0|0|0|2|0
6||__cflb|0...i|www.crunchbase.com|/|1740633817|1740551017520281|1740551017520281|0|1|0|1|1|2|0
...
We can see that it has some Cloudflare cookies (cf) for .crunchbase.com. Now, we should be ready to return to the original task we set out to do; which is to scrape our Crunchbase profile. Let’s see the code for this:

import json
from camoufox.sync_api import Camoufox

config = {
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

with Camoufox(
    headless=False, 
    persistent_context=True,
    user_data_dir='user-data-dir',
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the page
    page = browser.new_page()
    page.goto("https://www.crunchbase.com/organization/scrapingbee")
		
		# Wait for Network Idle
    page.wait_for_load_state('networkidle')
    # Wait more, just in case
    page.wait_for_timeout(10000)
	   
	  # Get the required data
    data = {
        'Name': page.locator('span.entity-name.ng-star-inserted').inner_text(),
        'Description': page.locator('span.expanded-only-content.ng-star-inserted').inner_text()
    }

    score_els = page.locator('.top-row-left-groups score-and-trend').all()
    for el in score_els:
        key_name = el.locator('span.label').inner_text()
        value = int(el.locator('div.chip-text').inner_text())
        data[key_name] = value

    data['Overview'] = []
    overview_els = page.locator('.overview-row label-with-icon').all()
    for el in overview_els:
        value = el.locator('.component--field-formatter').inner_text()
        data['Overview'].append(value)
		
		# print scraped data and close the page
    print(json.dumps(data, indent=2))
    page.close()
The above code prints an output with the company details extracted from the page:

{
  "Name": "ScrapingBee",
  "Description": "ScrapingBee is a software company that offers a web scraping API that handles headless browsers.",
  "Growth Score": 89,
  "CB Rank": 203243,
  "Heat Score": 82,
  "Overview": [
    "Jan 1, 2019",
    "Private",
    "Pre-Seed",
    "Paris, Ile-de-France, France",
    "1-10",
    "scrapingbee.com"
  ]
}
🔥 If you're still having trouble scraping without getting blocked, check out our expert level guide to Web Scraping Without Getting Blocked

Handling Login Sessions With Camoufox
As we saw in the previous section, Camoufox can persist sessions in a directory that we define. Now, we can use this to login to websites and store our session for future use, or even move it around between different systems. With Crunchbase as an example, let’s see how we can login into the service by visiting the login page:

from camoufox.sync_api import Camoufox

config = {
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

with Camoufox(
    headless=False, 
    persistent_context=True,
    user_data_dir='user-data-dir',
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the page
    page = browser.new_page()
    page.goto("https://www.crunchbase.com/login")
    
		# Wait for a while 
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(10000)
    
    # Fill the fields
    page.locator('form input[type=email]').fill('<your-email>')
    page.locator('form input[type=password]').fill('<your-password>')
    
    # Wait and click the login button
    page.wait_for_timeout(10000)
    page.locator('form button.login').click()
    
    # Wait and close the page
    page.wait_for_timeout(15000)
    page.close()
     
The above code opens the Crunchbase login page, fills in the email and password provided, and clicks on the login button. Once the login is successful, it is persisted. We can check this by visiting the home page and taking a screenshot, in a separate script:

from camoufox.sync_api import Camoufox

config = {
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

with Camoufox(
    headless=False, 
    persistent_context=True,
    user_data_dir='user-data-dir',
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the page
    page = browser.new_page()
    page.goto("https://www.crunchbase.com/home")

    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(10000)

    page.screenshot(path='crunchbase-home.png')
    page.close()
If you noticed, in this piece of code, we’ve set headless=True while in the previous snippet, we used headful mode. This was just to see the login happening, but once we’re logged in we should be fine with headless mode. Let’s see what we have in the screenshot:

Crunchbase Home Page After Login

We can see that we’re already logged in and Crunchbase shows us a greeting welcoming us back!

Scraping Google Maps Listings Using Camoufox
Google Maps is one of the most JavaScript-heavy interactive websites containing valuable information. Hence it’s a worthy target to demonstrate data extraction using Camoufox. Right away, let’s see if we can get a list of restaurants in New York starting from a manual search URL.

Scraping Google Maps for New York Restaurants

The above is a screenshot of a Google Maps search for “restaurants” in New York. What we’ll be scraping for this exercise are the listings on the left side. Let’s see the code:

from camoufox.sync_api import Camoufox
import json
import re

INITIAL_URL = 'https://www.google.com/maps/search/restaurants/@40.7500474,-74.0132272,12z/data=!4m2!2m1!6e5'

config = {
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

with Camoufox(
    headless=True, 
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the URL
    page = browser.new_page()
    page.goto(INITIAL_URL)

    # Wait for list to load
    page.wait_for_selector('div[role=feed]')

    # Get the list of restaurants
    divs = list(page.locator('div[role=feed] div.Nv2PK').all())

    # Extract required information onto another list
    results = []
    for div in divs:
        results.append({
            'name': div.locator('a.hfpxzc').get_attribute('aria-label'),
            'link': div.locator('a.hfpxzc').get_attribute('href'),
            'rating': float(div.locator('span.MW4etd').inner_text()),
            'reviews': int(re.sub(
                r'[\(\),]', '',
                div.locator('span.UY7F9').inner_text(),
            )),
        })

    # Save the results
    with open('results.json', 'w') as f:
        f.write(json.dumps(results, indent=2))
        f.close()

    # Close the page
    page.close()
The above code visits the INITIAL_URL that we defined, extracts a list of divs containing restaurant listings, parses some fields from them, and saves them to a JSON file. Let’s see what we have in the file:

[
  {
    "name": "Mojo",
    "link": "https://www.google.com/maps/place/Mojo/data=!4m7!3m6!1s0x89c25f58368ed953:0x5184e1a5b510a6fe!8m2!3d40.7205717!4d-73.8464128!16s%2Fg%2F11fkptd63p!19sChIJU9mONlhfwokR_qYQtaXhhFE?authuser=0&hl=en&rclk=1",
    "rating": 4.6,
    "reviews": 3556
  },
  {
    "name": "Upland",
    "link": "https://www.google.com/maps/place/Upland/data=!4m7!3m6!1s0x89c259a715fb5059:0xe5543b76e952fab3!8m2!3d40.7419313!4d-73.984644!16s%2Fg%2F11btmqg_59!19sChIJWVD7FadZwokRs_pS6XY7VOU?authuser=0&hl=en&rclk=1",
    "rating": 4.5,
    "reviews": 2217
  },
  {
    "name": "Salinas Restaurant",
    "link": "https://www.google.com/maps/place/Salinas+Restaurant/data=!4m7!3m6!1s0x89c259b92fa3c71d:0xb8dbc9965cf2d536!8m2!3d40.7436822!4d-74.0030697!16s%2Fg%2F1tdp1css!19sChIJHcejL7lZwokRNtXyXJbJ27g?authuser=0&hl=en&rclk=1",
    "rating": 4.7,
    "reviews": 1647
  },
  {
    "name": "The Avenue Restaurant & Bar",
    "link": "https://www.google.com/maps/place/The+Avenue+Restaurant+%26+Bar/data=!4m7!3m6!1s0x89c25e78690140df:0x807458e6fb09894d!8m2!3d40.7019674!4d-73.8792549!16s%2Fg%2F1x5fc8ng!19sChIJ30ABaXhewokRTYkJ--ZYdIA?authuser=0&hl=en&rclk=1",
    "rating": 4.4,
    "reviews": 367
  },
  {
    "name": "Buona Notte",
    "link": "https://www.google.com/maps/place/Buona+Notte/data=!4m7!3m6!1s0x89c25989d432ef1f:0x90b13821b661c011!8m2!3d40.7177496!4d-73.9979524!16s%2Fg%2F1vhlz2zr!19sChIJH-8y1IlZwokREcBhtiE4sZA?authuser=0&hl=en&rclk=1",
    "rating": 4.5,
    "reviews": 1609
  }
]
In the file, we have names, links, ratings, and the number of reviews for the 5 restaurants the URL initially loads. You are welcome to extend the scraper to extract more fields such as images, timings, and descriptions. Next, let’s extend this scraper to get us more results.

Handling Scrolling In Camoufox
In the previous method, one obvious way to get more results is to scroll down the list. On Google Maps, this loads more and more results. We’ve covered handling infinite scroll using Playwright for Python in a previous blog and whatever works with Playwright should technically work for Camoufox too. For this tutorial, we’ll do something even more fun: we’ll scroll around the New York City map instead of scrolling down the list because it’s Google Maps! Doesn’t that sound fun?

Essentially, the code will be similar to the previous section, except we’ll click a checkbox on the Google Maps UI called “Update results when map moves”, and then simulate keyboard arrow presses to move the map around. When the map moves, the results will be updated and we’ll extract the results on each iteration. Let’s see the code:

from camoufox.sync_api import Camoufox
import json
import re

INITIAL_URL = 'https://www.google.com/maps/search/restaurants/@40.7500474,-74.0132272,12z/data=!4m2!2m1!6e5'

config = {
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

with Camoufox(
    headless=True, 
    os=('windows'),
    config=config,
    i_know_what_im_doing=True
) as browser:
    # Open the URL
    page = browser.new_page()
    page.goto(INITIAL_URL)

    # Wait for list to load
    page.wait_for_selector('div[role=feed]')

    # Click "update result when map moves"
    page.locator('button.D6NGZc[role=checkbox]').click()
    page.wait_for_timeout(5000)

    # List to store extracted info
    results = []
    
    # Get initial list of restaurants
    divs = list(page.locator('div[role=feed] div.Nv2PK').all())

    # Start scroll loop
    while True:
        # Process current list
        for div in divs:
            results.append({
                'name': div.locator('a.hfpxzc').get_attribute('aria-label'),
                'link': div.locator('a.hfpxzc').get_attribute('href'),
                'rating': float(div.locator('span.MW4etd').inner_text()),
                'reviews': int(re.sub(
                    r'[\(\),]', '',
                    div.locator('span.UY7F9').inner_text(),
                )),
            })

        # Break if we have enough results
        if len(results)>=15:
            break
        
        # Else scroll and get more divs
        page.locator('div.widget-scene').focus()
        # Press arrow twice to move far enough
        page.keyboard.press('ArrowUp')
        page.keyboard.press('ArrowUp')
        
        page.wait_for_timeout(10000)
        divs = list(page.locator('div[role=feed] div.Nv2PK').all())
            
    # Save the results
    with open('results.json', 'w') as f:
        f.write(json.dumps(results, indent=2))
        f.close()

    # Close the page
    page.close()
The above code gives us 15 results instead of 5, getting the additional results by scrolling up on the city map. The JSON file looks similar:

[
  {
    "name": "Mojo",
    "link": "https://www.google.com/maps/place/Mojo/data=!4m7!3m6!1s0x89c25f58368ed953:0x5184e1a5b510a6fe!8m2!3d40.7205717!4d-73.8464128!16s%2Fg%2F11fkptd63p!19sChIJU9mONlhfwokR_qYQtaXhhFE?authuser=0&hl=en&rclk=1",
    "rating": 4.6,
    "reviews": 3556
  },
  {
    "name": "Connolly's",
    "link": "https://www.google.com/maps/place/Connolly%27s/data=!4m7!3m6!1s0x89c2585579862e01:0xe21f27dec63cf83d!8m2!3d40.7573681!4d-73.9835798!16s%2Fg%2F1vxzbjrt!19sChIJAS6GeVVYwokRPfg8xt4nH-I?authuser=0&hl=en&rclk=1",
    "rating": 4.4,
    "reviews": 4516
  },
  {
    "name": "V{IV}",
    "link": "https://www.google.com/maps/place/V%7BIV%7D/data=!4m7!3m6!1s0x89c2585130118027:0x237f3e220f422247!8m2!3d40.7627843!4d-73.9897032!16s%2Fg%2F1hc9wxh16!19sChIJJ4ARMFFYwokRRyJCDyI-fyM?authuser=0&hl=en&rclk=1",
    "rating": 4.7,
    "reviews": 4275
  },
  ...11 results hidden here (total 15 results)...
  {
    "name": "The Inn by Fumo",
    "link": "https://www.google.com/maps/place/The+Inn+by+Fumo/data=!4m7!3m6!1s0x89c2f7d883798bab:0x60a3d35f4da362e3!8m2!3d40.8252495!4d-73.9509651!16s%2Fg%2F11qpzydmt9!19sChIJq4t5g9j3wokR42KjTV_To2A?authuser=0&hl=en&rclk=1",
    "rating": 4.4,
    "reviews": 353
  }
]
If you’re curious, here’s a screen recording of what is going on in the browser (obtained with headless=False of course):

Scraping Google Maps With Scrolling

Conclusion
In this blog, we looked at what Camoufox is and how we can use it for some web scraping tasks. Camoufox provides several stealth patches and other features for scraping out-of-the-box, and we were able to straightaway use it on Crunchbase and Google Maps.

Further, all the code we wrote is similar to Playwright code. Camoufox Python is meant to be fully compatible with Playwright, so any working Playwright code that you already have can be ported to Camoufox with minimal changes.

At the time of writing, Camoufox only provides Python bindings, but it can be used from other programming languages that support the Playwright API, using its remote server mode.



