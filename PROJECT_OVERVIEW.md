This is a massive breakthrough in your architecture.

Decoupling the Harvesting (Part 1) from the AI Analysis & Structuring (Part 2)
is exactly how Enterprise systems are built.

  - Part 1 (web-intel) focuses only on defeating anti-bot systems, rendering the
    page, and outputting clean .html and .txt.
  - Part 2 (webintel-agent) will later consume those files and use AI to extract
    the complex data (founders, prices, hiring spikes).

By doing this, if your AI prompt changes tomorrow, you don't have to re-scrape
the website! You just re-read the .txt file.

Here is your completely redesigned Project Overview, Folder Structure, and Agile
Plan tailored exactly to your 7-domain use case and your HTML/TXT output
requirement.

📄 PROJECT OVERVIEW: web-intel (Part 1: The Harvester)

Goal: Build a modular, stealthy extraction platform that defeats anti-bot
protections to reliably harvest raw web data.

Scope Restriction: This system does NOT use AI. It does NOT extract JSON or
structured fields (like emails or prices). Its sole responsibility is to take a
target URL, bypass security, render the page, and save exactly two files
categorized by their business domain:

1.  domain_name.html (Raw source code for future debugging or deep parsing)
2.  domain_name.txt (Cleaned, visible text stripped of HTML tags for AI
    consumption)

The 7 Business Domains (Storage & Routing)

Data will be routed into 7 distinct storage pipelines because each requires
different crawl frequencies and strategies:

1.  Company Intelligence (Clearbit/Crunchbase style) - Slow crawl, high
    accuracy.
2.  Hiring & Talent (Greenhouse/LinkedIn style) - Fast crawl, highly dynamic.
3.  Sales & Lead (Apollo style) - Heavy anti-bot protection.
4.  Market & Financial (SEC/Bloomberg style) - Document heavy.
5.  E-commerce & Pricing (Keepa style) - Aggressive rotation, time-series heavy.
6.  AI Training Data (Common Crawl style) - High volume, infrastructure level.
7.  Other - Catch-all.

📂 REVISED PRODUCTION FOLDER STRUCTURE

web-intel/
│
├── main.py                     # Entry point: python main.py --file target_lists/urls_to_scrape.csv --crawl=true
│
├── core/                       # Shared infrastructure
│   ├── config.py               
│   ├── logger.py               
│   └── exceptions.py           
│
├── drivers/                    # 🛠️ THE LAYERED EXECUTION STACK
│   │
│   ├── browser_clients/        # LAYER 1: Browser Control (Choose One)
│   │   ├── base_browser.py     # Interface for all drivers
│   │   ├── playwright_driver.py# Standard modern automation
│   │   ├── patchright_driver.py# Stealth Playwright (Primary)
│   │   ├── camoufox_driver.py  # Stealth Firefox
│   │   ├── nodriver_client.py  # Driverless Chromium
│   │   └── selenium_driver.py  # Legacy automation fallback
│   │
│   ├── identity/               # LAYER 2: Browser Fingerprint (Combine)
│   │   ├── browserforge_manager.py  # Core fingerprint generation
│   │   ├── header_profiles.py       # User-Agent, Sec-Ch-Ua, Accept-Language
│   │   ├── screen_profiles.py       # Resolution and Viewport matching
│   │   ├── locale_profiles.py       # Timezone and Language consistency
│   │   └── rendering_spoofing.py    # WebGL and Canvas identity
│   │
│   ├── http_clients/           # LAYER 3: TLS / Protocol (For raw requests)
│   │   ├── httpx_client.py     # Basic async HTTP
│   │   ├── curl_cffi_client.py # TLS Impersonation (Chrome/Edge)
│   │   ├── aiohttp_client.py   # Raw async requests
│   │   └── tls_profiles.py     # JA3 / HTTP2 tuning profiles
│   │
│   ├── proxies/                # LAYER 4: Network/IP 
│   │   ├── proxy_router.py     # Routes to premium residential/ISP IPs
│   │   └── auth_manager.py     # Handles proxy authentication
│   │
│   ├── humanization/           # LAYER 5: Behavior
│   │   ├── ghost_cursor.py     # Realistic mouse curves
│   │   ├── typing_behavior.py  # Variable keystroke delays
│   │   ├── scrolling_behavior.py # Human scroll pausing/acceleration
│   │   └── idle_behavior.py    # Micro-pauses simulating reading
│   │
│   └── sessions/               # LAYER 6: Persistence (Rule: Enabled by default)
│       ├── session_manager.py  # Orchestrates the below files
│       ├── cookie_manager.py   # Injects/Extracts trusted cookies
│       └── persistent_context.py # Manages localStorage/Cache directories
│
├── engines/                    # 🧠 THE "BRAINS" (Routing & Processing)
│   │
│   ├── strategy_engine/        # Selects the right combination of Layers 1-6
│   │   └── orchestrator.py     
│   │
│   ├── profiler_engine/        # Detects Cloudflare / Datadome from response
│   │   └── bot_detector.py
│   │
│   ├── comparator_engine/      # Detects "Verify you are human" fake HTML
│   │   └── content_validator.py
│   │
│   └── text_engine/            # converts HTML -> Clean TXT
│       ├── html_cleaner.py     # Removes <script>, <style>, <nav>
│       └── text_extractor.py   # Extracts pure visible text
│
├── target_lists/               # 📥 INPUT: Agnostic URLs
│   └── urls_to_scrape.csv      # Just URLs. No domains. No business logic.
│
├── storage/                    # 📤 OUTPUT: For Part 2 (webintel-agent)
│   └── extracted/              # Flat, blind storage grouped by target
│       ├── target_site_hash_1/
│       │   ├── raw.html
│       │   ├── clean.txt
│       │   └── metadata.json
│       │
│       └── target_site_hash_2/
│           ├── raw.html
│           ├── clean.txt
│           └── metadata.json
│
├── requirements.txt
└── .gitignore

🚀 AGILE EXECUTION PLAN (How to start building)

Do not build everything at once. Follow these Sprints to build vertical slices.

Sprint 1: The Core Pipeline (No Browsers)

Goal: Prove you can take a URL, fetch it fast, clean the text, and save the
.html and .txt to the correct domain folder.

  - Build: drivers/http_clients/httpx_client.py (Simple GET request).
  - Build: engines/text_engine/text_extractor.py (Use BeautifulSoup to remove
    <script> and <style>, then extract .get_text()).
  - Build: The storage/ folder router.
  - Test: Pass https://example.com, and verify example.html
    and example.txt appear in the storage/7_other/ folder.

Sprint 2: The Anti-Bot Foundation (Persistent Sessions)

Goal: Introduce the browser layer with strictly consistent identity to defeat
basic protections.

  - Build: drivers/identity/fingerprint_generator.py (BrowserForge).
  - Build: drivers/sessions/session_manager.py (Save browser contexts).
  - Build: drivers/browser_clients/patchright_driver.py (Combine identity +
    session).
  - Test: Scrape a protected site. Close the bot. Run it again. Ensure it
    doesn't get a CAPTCHA the second time because the session persisted.

Sprint 3: The Intelligence Layer (Profiler & Comparator)

Goal: Stop saving "Fake" HTML (Challenge pages) into the storage folders.

  - Build: engines/comparator_engine/content_validator.py.
  - Logic: Check if the output HTML contains "Just a moment..." or
    "cf-browser-verification".
  - Action: If it detects a bot page, it raises a BlockedError, deletes the bad
    HTML, and tells the strategy_engine to try a stealthier method.

📋 TICKETS FOR JUNIOR DEVELOPERS

Because you decoupled the architecture so well, junior devs can work without
breaking the system.

Ticket 1: The HTML-to-Text Cleaner

  - Folder: engines/text_engine/html_cleaner.py
  - Task: Write a Python function that takes a raw HTML string. Use
    BeautifulSoup. Remove all <script>, <style>, <header>, <footer>, and <nav>
    tags (because we only care about main content). Return the clean visible
    text as a string.
  - Why it's great: Zero network requests. Pure string manipulation. Essential
    for the future AI agent.

Ticket 2: The Storage Router

  - Folder: core/utils/storage_utils.py
  - Task: Write a function save_output(domain_name, html_content, text_content,
    category_id). Based on the category_id (1 through 7), it should
    automatically write the .html and .txt files into the correct storage/.../
    directory.
  - Why it's great: Teaches basic OS/File system operations safely.

Ticket 3: The Fake Content Detector

  - Folder: engines/comparator_engine/content_validator.py
  - Task: Create a list of "Blocked Page Signatures" (e.g., ["Access Denied",
    "Pardon Our Interruption", "Cloudflare", "Datadome"]). Write a function that
    checks the raw HTML against these signatures. Return True if it's a block
    page, False if it's real content.
  - Why it's great: They start learning what Anti-Bot protections actually look
    like in the code.

Ticket 4: The Ghost Cursor Integration

  - Folder: drivers/humanization/ghost_cursor.py
  - Task: Take a standard Playwright Page object. Implement the Python
    playwright-ghost-cursor library to make the mouse move randomly across the
    screen and scroll down twice before returning the page.
  - Why it's great: Fun, visual, self-contained. Completely separated from
    scraping logic.


ticket 4:

Edited search_engine.py
Viewed orchestrator.py:41-51

Here is how a robust, production-grade anti-bot architecture handles Identity, Humanization, and Sessions. 

In a modular system, you must strictly separate **Decision Making** from **Execution**. If the Orchestrator tries to do humanization or manage cookies itself, the code will turn into unmaintainable spaghetti. 

Here is the exact separation of concerns:

### 1. The Identity Layer (`drivers/identity/`) -> "The Forger"
This layer is responsible for **generating and storing who you are**.
* **BrowserForge / Fingerprints:** Generates mathematically consistent profiles (User-Agent, WebGL vendor, Canvas noise, Screen resolution, Locale).
* **Session Manager:** Loads and saves cookies and `user_data_dir` to disk (e.g., `storage/sessions/profile_uuid.json`).
* **Output:** It yields a simple dictionary (an `IdentityProfile`) that contains the proxy, headers, session path, and fingerprint data. It does *not* interact with browsers directly.

### 2. The Orchestrator (`strategy_engine/orchestrator.py`) -> "The Strategist"
The Orchestrator is purely a **decision engine**. It does not know *how* to scroll a page or *how* to set a cookie.
* **Permutation Matrix:** It requests a list of `IdentityProfiles` from the Identity Layer. It then combines them with `BrowserClients` (Playwright, Patchright, etc.).
* **The Loop:** It tries a permutation, waits for the result, runs the `BotDetector`, and if blocked, moves to the next permutation. 
* **State Management:** It tells the Identity Layer to "mark proxy X as burned" or "save session Y as successful" based on the BotDetector's result.

### 3. The Browser Clients (`drivers/browser_clients/`) -> "The Actor"
This is where **Humanization** and **Session Application** happen. The browser client receives an `IdentityProfile` from the Orchestrator and executes it.
* **Applying Identity:** The client configures the browser context. It injects the proxies, sets the User-Agent, overrides `navigator.webdriver`, and loads the session cookies into the context.
* **Humanization (Action):** Once the page loads, the Browser Client executes human-like behaviors. It handles random bezier-curve mouse movements, scroll jitter, realistic typing delays, and waiting for CAPTCHAs to settle. 
* *Note: Playwright handles humanization differently than Selenium, which is why humanization logic MUST live inside the specific browser client, not the orchestrator.*

---

### How the Flow Actually Looks in Code (Sprint 2)

Here is how the Orchestrator will interact with Identity and Browser Clients when fully implemented:

```python
# In orchestrator.py (The Strategist)

from drivers.identity.profile_manager import get_profiles

def _permutation_fallback(self, url: str):
    # 1. Ask Identity layer for 5 highly-trusted profiles (with sessions/proxies)
    profiles = get_profiles(tier="premium", count=5)
    
    permutations = [
        (BrowserClass, profile) 
        for BrowserClass in [PatchrightDriver, PlaywrightDriver] 
        for profile in profiles
    ]

    for BrowserClass, profile in permutations:
        # 2. Orchestrator simply passes the profile to the Actor
        driver = BrowserClass(identity_profile=profile)
        
        # 3. The Driver handles session loading, fetching, and humanization internally!
        html = driver.fetch(url) 
        
        # 4. Orchestrator checks if it worked
        detection = self.detector.detect(html)
        if not detection["is_blocked"]:
            # Tell Identity layer to save these cookies for next time!
            profile.save_session(driver.get_cookies())
            return html
```

And inside a Browser Client (e.g., `patchright_driver.py`):

```python
# In patchright_driver.py (The Actor)

class PatchrightDriver:
    def __init__(self, identity_profile: dict):
        self.profile = identity_profile
        
    def fetch(self, url):
        # 1. Apply Identity & Session
        context = browser.new_context(
            user_agent=self.profile["user_agent"],
            proxy=self.profile["proxy"],
            storage_state=self.profile["session_file"] # Load cookies
        )
        page = context.new_page()
        
        # Apply Canvas/WebGL spoofing via JS injection
        page.add_init_script(self.profile["stealth_js_payload"])
        
        # 2. Go to URL
        page.goto(url)
        
        # 3. HUMANIZATION (Happens here, inside the driver!)
        self._simulate_human_behavior(page)
        
        return page.content()

    def _simulate_human_behavior(self, page):
        """Randomized scrolling, mouse movements, waiting for elements."""
        page.mouse.move(x=random.randint(100, 500), y=random.randint(100, 500))
        page.evaluate("window.scrollBy(0, window.innerHeight / 2)")
        time.sleep(random.uniform(1.2, 3.5))
```

### Summary of Where Code Belongs:
* **Cookie Management / Proxy Rotation:** `drivers/identity/`
* **Retries / Fallback Logic / Bot Checking:** `engines/strategy_engine/orchestrator.py`
* **Mouse Movement / Scrolling / Setting UA:** `drivers/browser_clients/*_driver.py`


Why this design guarantees success for Part 2:

When you start building Part 2 (webintel-agent), that AI system will simply
iterate through storage/1_company_intelligence/, pick up the .txt files, and
feed them into an LLM with the prompt: "Extract the founders and email addresses
from this text."

Because Part 1 handled all the dirty work of proxies, TLS spoofing, and
Cloudflare bypasses, your AI agent never has to worry about getting blocked.




You are absolutely right, and I apologize for missing that boundary.

If Part 1 knows about "Company Intelligence" or "Hiring", business logic has
leaked into the extraction layer. Part 1 should be completely blind. It is just
a dumb, powerful engine: you feed it a URL, it bypasses the bot protection, and
it spits out the text.

Part 2 (The Agent) is the one that cares about why the data was scraped.

Here is the corrected, strictly domain-agnostic output design for Part 1.

The Corrected Output Structure (Zero Business Logic)

All outputs go into a single, flat extraction folder. They are grouped by a
unique ID (like a hash of the URL or a timestamp) so Part 2 can easily pick them
up.

storage/
└── extracted/
    ├── clearbit_com_8f2a1/        # Grouped only by target site + hash
    │   ├── raw.html               
    │   ├── clean.txt              
    │   └── metadata.json          # Technical data only
    │
    ├── stripe_com_careers_3b9x2/
    │   ├── raw.html
    │   ├── clean.txt
    │   └── metadata.json
    │
    └── amazon_com_B08FX_9z1c4/
        ├── raw.html
        ├── clean.txt
        └── metadata.json

The Corrected Input (No Categorized Folders)

You simply pass URLs to Part 1.

web-intel/
├── main.py                     # CLI runner: "python main.py --url https://clearbit.com"
├── target_lists/               
│   └── urls_to_scrape.csv      # Just a raw list of URLs. No domains. No categories.

The Corrected metadata.json (Technical Data Only)

When Part 2 reads this folder, it only needs the URL to know what it's looking
at, and the technical status.

{
  "target_url": "https://clearbit.com/about",
  "extracted_at": "2025-10-24T10:00:00Z",
  "extraction_tier_used": 3,
  "driver_used": "patchright_driver",
  "status_code": 200,
  "was_blocked": false,
  "word_count": 1450
}

How this perfectly supports your API future:

Because Part 1 knows absolutely nothing about your business domains:

1.  Part 2 says: "Hey Part 1, scrape https://linkedin.com/jobs/123"
2.  Part 1 scrapes it, saves raw.html and clean.txt, and returns the folder path
    or the text directly.
3.  Part 2 says: "Thanks, I am the Hiring Agent, I will now parse this text."

This is the perfect decoupling. Part 1 is officially just a Stealth Harvester.
No business logic allowed.




You don't have to tell them "build anti-bot logic." You can hand out hyper-specific tickets based on the layers:
"Build the Nodriver Client" -> Go to Layer 1, implement nodriver_client.py so it accepts our session_manager.
"Build Human Scrolling" -> Go to Layer 5, write a script in scrolling_behavior.py that scrolls down 300px, pauses for 1 second, and scrolls down again.
"Implement WebGL spoofing" -> Go to Layer 2, write the script in rendering_spoofing.py that injects fake WebGL vendor strings into the page.
By structuring it this way, all 6 layers are available as building blocks. The strategy_engine just snaps them together (e.g., Camoufox + Browserforge + Residential Proxy + Ghost Cursor + Persistent Session) depending on how hard the target website is.


IMPORTANT RULE

More tools ≠ more stealth

BAD:

100 stealth patches
+
random fingerprints
+
random headers

This creates:

impossible browser identity

REAL Goal

Modern anti-bot systems check:

Consistency

NOT:

number of stealth libraries

Example of GOOD Consistency

Property

Value

Browser

Chrome 136

OS

Windows 11

GPU

NVIDIA

timezone

India

language

en-IN

IP

Bangalore residential

screen

laptop resolution

This looks human.

Example of BAD Fingerprint

Property

Value

Browser

Chrome

OS

Linux

fonts

Mac

GPU

iPhone

timezone

Germany

IP

India

Impossible combination.

Instantly suspicious.



## release phase rule 
phase 1 : basic [ search , site , crawl ] + engine + driver [ browser clinet + identity only/-]
phase 2: http client
phase 3 : seesion + humanizaion+ proxy 
phase 4 : click not to robot 

