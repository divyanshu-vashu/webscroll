Playwright's headless browsers leak fingerprint signals like navigator.webdriver, missing plugins, and the HeadlessChrome User-Agent marker that anti-bot systems instantly detect. Stealth plugins patch these leaks, but the ecosystem is split between Python and Node.js with different packages and APIs.

This guide covers stealth setup in both languages with working code, evasion module breakdowns, detection testing, plugin limitations, and what to do when stealth alone is not enough.


Web Scraping with Playwright and Python
Playwright is the new, big browser automation toolkit - can it be used for web scraping? In this introduction article, we'll take a look how can we use Playwright and Python to scrape dynamic websites.
Quick Start: If you want a working stealth setup right now, here is a minimal Python async example:

python
# Install: pip install playwright-stealth && playwright install chromium
import asyncio
from playwright_stealth import Stealth
from playwright.async_api import async_playwright


async def main():
    async with Stealth().use_async(async_playwright()) as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://web-scraping.dev/products")
        title = await page.title()
        print(f"Page title: {title}")
        products = await page.evaluate("""
            Array.from(document.querySelectorAll('.product')).slice(0, 5).map(item => ({
                title: item.querySelector('h3 a')?.textContent?.trim(),
                price: item.querySelector('.price')?.textContent?.trim()
            }))
        """)
        for product in products:
            print(f"{product['title']}: {product['price']}")
        await browser.close()

asyncio.run(main())
The rest of this article explains why stealth patching works, what the plugin modifies, and where the approach breaks down.

Key Takeaways
Playwright stealth is not built into Playwright — it refers to third-party packages that patch browser fingerprint leaks in Chromium: playwright-stealth in Python and playwright-extra with the stealth plugin in Node.js.
Stealth plugins work by fixing obvious browser-level detection signals like navigator.webdriver, missing plugins, inconsistent User-Agent data, and unrealistic WebGL or codec fingerprints before page scripts run.
Python is the stronger ecosystem in 2026: playwright-stealth is actively maintained with a modern context-manager API, while the Node.js stealth stack still relies on packages that have seen little recent maintenance.
Stealth only solves fingerprint-level detection. It does not fix IP reputation, TLS fingerprinting, behavioral analysis, or advanced JavaScript challenges from anti-bot systems like Cloudflare and DataDome.
For production Playwright scraping, Scrapfly Cloud Browser is the simplest upgrade path once stealth plugins hit their limit, because teams can keep their existing Playwright workflows while offloading browser fingerprinting, proxy routing, and anti-bot bypass to managed infrastructure.
Get web scraping tips in your inbox
Trusted by 100K+ developers and 30K+ enterprises. Unsubscribe anytime.
Subscribe
How Websites Detect Playwright
Before discussing solutions, it's important to understand the signals that give Playwright away. Anti-bot systems look at various signals together, and even a single inconsistency can trigger a block.

Key Signals that Websites Use to Detect Playwright
navigator.webdriver Automation frameworks like Playwright set this to true, easily detected by anti-bot systems.

User-Agent String Headless Chromium includes HeadlessChrome. Mismatches between User-Agent and other properties like Client Hints or navigator.userAgent raise suspicion.

Browser Plugins and Codecs Real Chrome shows plugins such as PDF Viewer, but headless Chromium reports none. Media codecs and WebGL strings also differ, revealing automation.

Behavioral Signals Automated browsers show unnatural patterns, like instant navigation and no mouse movement. Anti-bot services use this data to calculate trust scores.

Tools to Monitor Browser Leaks
You can check what your browser is leaking using the Scrapfly Browser Fingerprint Tool. This tool shows detected automation signals, fingerprint inconsistencies, and suspicious markers in real time.


How to Know What Anti-Bot Service a Website is Using?
In this article we'll take a look at two popular tools: WhatWaf and Wafw00f which can identify what WAF service is used.
What Is Playwright Stealth?
Playwright stealth is not a built-in feature of Playwright. There is no stealth mode toggle you can flip in the library itself. The term refers to third-party packages that patch browser fingerprints to make Playwright sessions appear more like genuine user sessions. The ecosystem splits across two languages with different packages and different integration patterns, which causes a fair amount of confusion.

Python: playwright-stealth
The Python package is called playwright-stealth. The package was originally introduced a new context manager API with breaking changes from the older v1.x stealth_async(page) pattern. The latest release is v2.0.2, which continues the v2.x API line.

If you encounter tutorials using stealth_async(page) or stealth_sync(page), those are outdated patterns from v1.x that should not be used with the current version.

The playwright-stealth package is a port, not a wrapper. The package bundles its own JavaScript evasion files that mirror the core evasions from the original Puppeteer stealth plugin, plus a few Python-specific additions like navigator.platform, error.prototype, and chrome.hairline. One important gotcha: chrome.runtime evasion is disabled by default in v2.x because enabling the module can cause compatibility issues on certain sites.

Node.js: playwright-extra + stealth plugin
The Node.js approach uses two packages together playwright-extra a wrapper around Playwright that adds plugin support and puppeteer-extra-plugin-stealth the original stealth plugin from the Puppeteer ecosystem.

The naming is confusing, the Node.js setup uses the actual original Puppeteer stealth plugin directly, not a port. The playwright-extra wrapper makes the stealth plugin compatible with Playwright's API while the stealth plugin code remains the same one used in Puppeteer.

Both packages only work with Chromium. Firefox and WebKit are not supported by either stealth implementation, because the evasion modules target Chrome-specific APIs.


Puppeteer Stealth: Complete Guide to Avoiding Detection
Complete guide to puppeteer-extra-plugin-stealth for avoiding bot detection. Learn how detection works, configure stealth evasion modules, implement complementary techniques, and scale with cloud browsers.
With the ecosystem clear, let us walk through the installation and usage for each language, starting with Python.

Playwright Stealth in Python
The Python ecosystem uses the playwright-stealth package to patch browser fingerprints. It works as a wrapper around Playwright's browser contexts, injecting evasion scripts before any page code runs. Let's go through the setup and usage.

Installation & Setup
Install the stealth package and the Playwright browser binary:

shell
pip install playwright-stealth
playwright install chromium
The first command installs the stealth package from PyPI. The second command downloads the Chromium browser binary that Playwright controls during automation.

The playwright-stealth package version 2.0+ provides two primary integration patterns: a context manager that wraps async_playwright() or sync_playwright(), and a manual apply_stealth_async() method for situations where the context manager does not fit your code architecture. Both approaches produce the same result: stealth evasions injected before any page scripts execute.

Async API Example
The async pattern is recommended for scraping workloads because it allows concurrent page operations without blocking. The Stealth().use_async() context manager intercepts the Playwright instance and automatically applies all evasion patches to every browser context created within it.

python
import asyncio
from playwright_stealth import Stealth
from playwright.async_api import async_playwright


async def main():
    async with Stealth().use_async(async_playwright()) as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        # Navigate to the target page
        await page.goto("https://web-scraping.dev/products")
        await page.wait_for_selector(".product")

        # Extract product data
        products = await page.evaluate("""
            Array.from(document.querySelectorAll('.product')).map(item => ({
                title: item.querySelector('h3 a')?.textContent?.trim(),
                price: item.querySelector('.price')?.textContent?.trim()
            }))
        """)

        for product in products:
            print(f"{product['title']}: {product['price']}")

        await browser.close()


asyncio.run(main())
Every page created within the Stealth().use_async() context manager receives stealth patches before any site scripts execute. There is no need to call a separate function on each page or context.

Sync API Example
The synchronous API works well for quick scripts, prototyping, and workflows that do not need concurrency:

python
from playwright_stealth import Stealth
from playwright.sync_api import sync_playwright

with Stealth().use_sync(sync_playwright()) as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()

    page.goto("https://web-scraping.dev/products")
    page.wait_for_selector(".product")

    title = page.title()
    print(f"Page title: {title}")

    browser.close()
The sync pattern mirrors the async version with blocking calls instead of await. The Stealth().use_sync() context manager applies the same evasion patches automatically to all browser contexts created within the block.

For cases where the context manager pattern does not fit your architecture, the manual application method gives you explicit control over which browser contexts receive stealth patches:

python
import asyncio
from playwright_stealth import Stealth
from playwright.async_api import async_playwright


async def main():
    stealth = Stealth()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        # Manually apply stealth to this specific context
        await stealth.apply_stealth_async(context)

        page = await context.new_page()
        await page.goto("https://web-scraping.dev/products")
        print(await page.title())

        await browser.close()


asyncio.run(main())
The context manager path is cleaner for most cases, but apply_stealth_async() is useful when you need to apply stealth selectively, for example, when some contexts require stealth while others do not. Both patterns produce identical evasion behavior.

With Python covered, the Node.js setup follows the same principles but uses a different integration pattern that reflects its Puppeteer heritage.

Playwright Stealth in Node.js
The Node.js ecosystem uses playwright-extra combined with the puppeteer-extra-plugin-stealth plugin. This setup builds on the same evasion modules originally created for Puppeteer, adapted to work with Playwright's API through a thin wrapper.

Installation & Setup
Install three packages: the Playwright wrapper, Playwright itself, and the stealth plugin:

shell
npm install playwright playwright-extra puppeteer-extra-plugin-stealth
The command installs Playwright along with the playwright-extra wrapper and the stealth plugin. All three packages are required for the stealth setup to work.

The critical detail here is importing from playwright-extra instead of playwright. The playwright-extra wrapper extends Playwright with a plugin system while keeping the rest of the API identical. If you import from the regular playwright package, the stealth plugin will not be applied and you will get no error telling you why.

Stealth Plugin Example
Register the stealth plugin with the chromium launcher before creating any browser instances. Everything launched through the wrapped chromium object will have stealth evasions applied automatically.

ESM (Modern JavaScript)
CommonJS
javascript
// stealth-scraper.mjs
import { chromium } from 'playwright-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

chromium.use(StealthPlugin());

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Navigate to the target page
    await page.goto('https://web-scraping.dev/products');
    await page.waitForSelector('.product');

    // Extract product data
    const products = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('.product')).map(item => ({
            title: item.querySelector('h3 a')?.textContent?.trim(),
            price: item.querySelector('.price')?.textContent?.trim()
        }));
    });

    console.log(products);
    await browser.close();
})();
The underlying evasion modules are identical to what the Python package uses. The same core modules run in both languages. The difference is integration: Node.js uses the original puppeteer-extra-plugin-stealth package directly, while Python bundles its own ported JavaScript files.

TypeScript works without additional setup since playwright-extra ships with type declarations. The import syntax is the same as the ESM example above.


Web Scraping with Playwright and JavaScript
Learn about Playwright - a browser automation toolkit for server side Javascript like NodeJS, Deno or Bun.
With both languages set up, the next question is what exactly these stealth patches modify in the browser environment, and why each modification matters.

What Playwright Stealth Actually Patches
Both packages apply around many evasion modules that modify the browser environment before any website scripts run. When a site blocks you despite stealth being active, knowing what's patched and what's not helps you figure out why.

Chrome API Emulation
Headless Chrome is missing several Chrome-specific APIs that real browsers have. Stealth patches fake these so fingerprinting scripts find what they expect:

chrome.app, chrome.csi, chrome.loadTimes - Chrome-specific APIs that don't exist in headless mode. Sites check for their presence as a quick headless test.
chrome.runtime - Patches the extensions API behavior. This one is disabled by default in Python v2.x because it can interfere with some sites. Enable it explicitly if needed.
Navigator Properties
The navigator object is a goldmine for detection scripts. Stealth patches several of its properties:

navigator.webdriver - The big one. Automation frameworks set this to true, and every anti-bot system checks it.
navigator.plugins - Real Chrome reports plugins like PDF Viewer. Headless Chrome reports zero.
navigator.languages - Sets realistic language preferences instead of the empty default.
navigator.permissions - Fixes Permissions.query() which behaves differently in automated browsers.
navigator.vendor and navigator.platform (Python only) - Consistency patches so these values match the User-Agent.
navigator.hardwareConcurrency - Masks CPU core count, since cloud environments typically expose 1-2 cores which is unusual for real devices.
Rendering and Media
webgl.vendor - Spoofs WebGL renderer and vendor strings to match real Chrome GPU info.
media.codecs - Fakes the supported codec list, which differs between headed and headless Chrome.
Automation Markers
iframe.contentWindow - Fixes cross-origin iframe behavior that differs in automated browsers.
defaultArgs / sourceurl (Node.js) - Removes the --enable-automation flag and sourceURL markers from injected scripts.
error.prototype (Python only) - Patches stack traces that can reveal the automation framework.
User-Agent Consistency
user-agent-override - Patches the User-Agent across all surfaces: HTTP headers, navigator.userAgent, and Client Hints (Sec-CH-UA). This prevents the mismatch problem discussed earlier.
Platform-Specific Extras
chrome.hairline (Python only) - Adds CSS hairline feature detection missing in headless.
window.outerdimensions (Node.js only) - Fixes outerWidth/outerHeight which return 0 in headless mode.
The core 14 modules are shared across both packages. Python adds chrome.hairline, error.prototype, navigator.platform, and sec_ch_ua. Node.js adds defaultArgs, sourceurl, and window.outerdimensions.

Customizing Modules
All modules are enabled by default except chrome.runtime in Python. You can toggle them through the configuration API:

python
# Python: Constructor params control individual modules
stealth = Stealth(
    chrome_runtime=True,          # Enable chrome.runtime (disabled by default)
    navigator_webdriver=True,     # Keep webdriver patch (default: True)
    navigator_languages_override=("en-US", "en"),  # Custom languages
    webgl_vendor_override="Intel Inc.",  # Custom WebGL vendor
)
javascript
// Node.js: enabledEvasions Set controls which modules load
const stealth = StealthPlugin({
    enabledEvasions: new Set([
        'chrome.app',
        'chrome.csi',
        'chrome.loadTimes',
        'navigator.webdriver',
        'navigator.plugins',
        'navigator.languages',
        'navigator.permissions',
        'navigator.vendor',
        'media.codecs',
        'iframe.contentWindow',
        // omit modules you want disabled
    ])
});
chromium.use(stealth);
In Python, you pass keyword arguments to enable or disable each module. In Node.js, you pass a Set of module names and only listed modules activate.

For most scraping tasks, the defaults work fine. Toggling modules is mainly useful for debugging when a site still blocks you despite stealth being active. All evasion modules work exclusively with Chromium. Firefox and WebKit are not supported.

Now that you know what stealth patches, you need to verify that it's actually working. That's what the next section covers.

Testing Your Stealth Setup
Applying stealth patches without verifying them is a common mistake. Detection test sites let you confirm that evasions are working before you point your scraper at a production target and wonder why it gets blocked.

Scrapfly's browser fingerprint tool is the most straightforward verification tool. The page tests browser fingerprint properties including navigator.webdriver, plugin count, language settings, WebGL renderer strings, and several other signals. Results display as green (passed) or red (detected) indicators for each property.

The most reliable way to verify is to take a screenshot of the test page and inspect the results visually:

python
import asyncio
from playwright_stealth import Stealth
from playwright.async_api import async_playwright


async def verify_stealth():
    async with Stealth().use_async(async_playwright()) as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        # Run the fingerprint test
        await page.goto("https://scrapfly.io/web-scraping-tools/browser-fingerprint")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="stealth_result.png", full_page=True)

        # Verify key properties programmatically
        checks = await page.evaluate("""() => ({
            webdriver: navigator.webdriver,
            pluginCount: navigator.plugins.length,
            languages: navigator.languages,
            vendor: navigator.vendor
        })""")

        print(f"webdriver: {checks['webdriver']}")
        print(f"plugins: {checks['pluginCount']}")
        print(f"languages: {checks['languages']}")
        print(f"vendor: {checks['vendor']}")

        await browser.close()


asyncio.run(verify_stealth())
The script launches a stealth-patched browser and saves a full-page screenshot for visual inspection. The page.evaluate() call extracts key fingerprint values programmatically so you can verify results without opening the screenshot each time.

For a quick verification checklist, here is what to look for in your test results:

navigator.webdriver returns false (not true)
Plugin count is greater than zero (real Chrome reports at least 5 plugins)
Languages array is populated with realistic values (not empty)
Vendor string is "Google Inc."
No "HeadlessChrome" substring in the User-Agent
Limitations of Playwright Stealth
Stealth plugins address fingerprint-level detection by patching JavaScript properties and browser environment signals that reveal automation. Fingerprint-level patching is one layer in a multi-layer detection stack, and being clear about where that layer ends prevents wasted debugging time.

What Stealth Does Not Handle
IP reputation is evaluated before your browser JavaScript even runs. Datacenter IPs, known VPN ranges, and flagged subnets get blocked at the network level. No amount of fingerprint patching changes where your traffic originates from.

TLS fingerprinting analyzes the cryptographic handshake between your client and the server. The JA3 fingerprint produced by Playwright's Chromium does not always match what a real user's Chrome produces, especially across different operating systems and network stacks.

JavaScript challenges from advanced anti-bot systems like Cloudflare go beyond property checks. These systems execute cryptographic proof-of-work challenges, analyze execution timing, and verify results server-side. JavaScript challenges evolve faster than open-source stealth modules can keep pace with.

Behavioral analysis tracks mouse trajectories, scroll patterns, click timing, and navigation sequences. A scraper that loads a page, waits a fixed interval, extracts data, and leaves produces a statistically distinct pattern from real browsing. Stealth patches do nothing to address behavioral detection.

Stealth is a starting point, not a complete solution. The stealth approach eliminates the most obvious detection signals and buys you access to sites with basic protection. For sites running Cloudflare, DataDome, or PerimeterX, the limitations above become the reason your scraper gets blocked, not a missing stealth configuration option.


5 Tools to Scrape Without Blocking and How it All Works
Tutorial on how to avoid web scraper blocking. What is javascript and TLS (JA3) fingerprinting and what role request headers play in blocking.
When stealth plugins hit their ceiling, the question becomes what replaces them at production scale. Managed browser infrastructure fills that gap.

Beyond Stealth Plugins: Scaling with Scrapfly
Stealth plugins don't scale well. Scrapfly's cloud browsers handle resource management, fingerprint rotation, and anti-bot bypasses so you don't have to.

scrapfly middleware
The Scrapfly Cloud Browser API addresses these pain points while letting Playwright developers keep their existing code.

python
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(
            "wss://browser.scrapfly.io?api_key=YOUR_API_KEY&proxy_pool=residential&os=windows"
        )
        page = await browser.new_page()
        await page.goto("https://web-scraping.dev/products")
        await page.wait_for_selector(".product")

        products = await page.evaluate("""
            Array.from(document.querySelectorAll('.product')).map(item => ({
                title: item.querySelector('h3 a')?.textContent?.trim(),
                price: item.querySelector('.price')?.textContent?.trim()
            }))
        """)

        for product in products:
            print(f"{product['title']}: {product['price']}")

        await browser.close()


asyncio.run(main())
The code above connects to the Scrapfly Cloud Browser through a CDP WebSocket URL instead of launching a local Chromium instance. The proxy_pool=residential and os=windows parameters configure proxy routing and operating system fingerprint at the connection level.

Not every scraping task needs a full browser. For static pages or JavaScript-rendered content that does not require multi-step browser interaction, the Scrapfly Scrape API handles anti-bot bypass with asp=true and JavaScript rendering with render_js=true through simple HTTP calls.

FAQ
Does playwright-stealth still work in 2026?
What is the difference between playwright-stealth and playwright-extra?
Can Playwright bypass Cloudflare bot detection?
Is playwright-stealth the same as puppeteer-stealth?
Does Playwright stealth work with Firefox or WebKit?
Summary
In this guide, we covered how to set up Playwright stealth in both Python and Node.js, what each evasion module patches, and how to verify your setup against detection test pages. Here are the key takeaways:

playwright-stealth (Python) is actively maintained and works well for basic to moderate fingerprint evasion.
playwright-extra with puppeteer-extra-plugin-stealth (Node.js) shares the same core modules but hasn't been updated since 2023.
Stealth plugins patch browser fingerprints like navigator.webdriver, plugins, and User-Agent consistency, but they can't address TLS fingerprinting, behavioral analysis, or advanced challenges from services like Cloudflare.
Both packages only support Chromium.



Bot Detection as The Biggest Limitation of Playwright

Playwright is one of the most popular Python libraries for browser automation. In detail, it is reliable and widely used because it is developed and maintained directly by Microsoft. Its high-level and intuitive API makes it easy to control headless or headed browsers in different programming languages. That means Playwright is a great tool for cross-browser and cross-platform bot development, automated testing, and web scraping.

Playwright is one of the most popular Python libraries for browser automation. In detail, it is reliable and widely used because it is developed and maintained directly by Microsoft. Its high-level and intuitive API makes it easy to control headless or headed browsers in different programming languages. That means Playwright is a great tool for cross-browser and cross-platform bot development, automated testing, and web scraping.

The main issue with the library is that it can be easily detected and blocked by anti-bot technologies, especially when using browsers in headless mode. How is that possible? Well, Playwright automatically changes the value of special properties and headers when controlling headless browsers. For example, it sets the navigator.webdriver Chrome setting to true.

Bot detection solutions are aware of those configurations and analyze them to verify whether the current user is a human or a bot. When these mechanisms detect any suspicious settings, they categorize the user as a bot and block it right away.

For example, consider this bot detection test for headless mode. Visit the page in your browser, and you will see:

Webpage displaying 'You are not Chrome headless' message
Perfect, that is the result you would expect!

Now, try visiting the same page in Playwright vanilla and extract the answer from the page:

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # launch the browser
        browser = await p.chromium.launch()
        # open a new page
        page = await browser.new_page()

        # visit the target page
        await page.goto("https://arh.antoinevastel.com/bots/areyouheadless")

        # extract the answer contained on the page
        answer_element = page.locator("#res")
        answer = await answer_element.text_content()

        # print the resulting answer
        print(f'The result is: "{answer}"')

        # close the browser and release its resources
        await browser.close()

asyncio.run(main())
Execute the Python program, and it will print:

The result is: "You are Chrome headless"
That means that the bot automation test page has been able to detect the request made by your automated script as coming from a headless browser.

In other words, Playwright is a limited tool that can be easily stopped by bot detection technologies. To avoid that, you can manually override default configurations and hope for a win. Otherwise, install the Playwright Stealth plugin!

Playwright Stealth Plugin: What It Is and How It Works
playwright-stealth is a Python package that extends Playwright by overriding specific configurations to avoid bot detection. Playwright Stealth is a port of the puppeteer-extra-plugin-stealth npm package, which uses built-in evasion modules to avoid leaks and change properties that expose automated browsers as bots. For example, it deletes the navigator.webdriver property and removes “HeadlessChrome” from the User-Agent header set by Chrome in headless mode by default.

The objective of the Stealth plugin is to enable an automated headless browser instance to successfully pass all bot detection tests on sannysoft.com. At the time of writing, that objective has been met. However, as mentioned in the official documentation, there are still methods for detecting headless browsers. So, what works today, may not work tomorrow. Bypassing all bot detection mechanisms is not entirely achievable, but the library aims to make this process as challenging as possible.

How To Use Playwright Stealth to Avoid Bot Detection
Follow the steps below to learn how to integrate Playwright Stealth into a playwright Python script to avoid getting blocked.

Step 1: Set Up a Playwright Python Project
Disclaimer: If you already have a Playwright Python project in place, you can skip this step.

First, make sure you have Python 3 installed on your machine. Otherwise, download the installer, execute it, and follow the installation wizard.

Next, use the commands below to set up a Python project called playwright-demo:

mkdir playwright-demo
cd playwright-demo
These commands create the playwright-demo folder and enter it in the terminal.

Initialize a Python virtual environment and activate it:

python -m venv env
env/Scripts/activate
Launch the following command to install Playwright:

pip install playwright
This will take a while, so be patient.

After that, install the required browsers with:

playwright install
Open the project folder in the Python IDE of your choice and create an index.py file. Initialize it with the following lines:

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # browser automation logic...

        await browser.close()

asyncio.run(main())
The above script launches an instance of Chromium in headless mode, opens a new page, and finally closes the browser. This is what a basic Playwright Python script looks like.

To execute it, run:

python index.py
Great, you now have a Playwright project ready to be extended with the Stealth Plugin!

Step 2: Install and Use the Stealth Plugin
Install the Playwright Stealth plugin with:

pip install playwright-stealth
Open your index.py file and add the import below to your Playwright script:

from playwright_stealth import stealth_async
Or if you are using the sync API:

from playwright_stealth import stealth_sync
To register it in Playwright, pass the page object to the imported function as follows:

await stealth_async(page)
Or if you are using the sync API:

stealth_async(page)
The stealth_async() function will extend page by overriding some default configurations to avoid bot detection.

Fantastic! It only remains to visit the target page and repeat the test.

Step 3: Put It All Together
Integrate the Stealth plugin into the Playwright script presented at the beginning of the article:

import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
async def main():
    async with async_playwright() as p:
        # launch the browser
        browser = await p.chromium.launch()
        # open a new page
        page = await browser.new_page()

        # register the Playwright Stealth plugin
        await stealth_async(page)

        # visit the target page
        await page.goto("https://arh.antoinevastel.com/bots/areyouheadless")

        # extract the message contained on the page
        message_element = page.locator("#res")
        message = await message_element.text_content()

        # print the resulting message
        print(f'The result is: "{message}"')

        # close the browser and release its resources
        await browser.close()

asyncio.run(main())
Execute it again, and this time it will print:

The result is: "You are not Chrome headless"
Et voilà! The target page, equipped with bot detection capabilities, can no longer flag your Playwright automated script as a bot.

Well done! You have now mastered the art of Playwright Stealth, and no bot detection technology can intimidate you any longer.

Extra: Playwright Stealth in JavaScript
If you are a Playwright JavaScript user and want to achieve the same result, you need to use the puppeteer-extra-plugin-stealth npm package. This works for both Puppeteer Extra and Playwright Extra. If you are not familiar with these projects, they are essentially enhanced versions of the two browser automation libraries. Specifically, they add extension functionality via plugins to Puppeteer and Playwright, respectively.

Thus, suppose you have the following Playwright JavaScript script and want to integrate it with the Stealth plugin:

import { chromium } from "playwright"

(async () => {
    // set up the browser and launch it
    const browser = await chromium.launch()
    // open a new blank page
    const page = await browser.newPage()

    // navigate the page to the target page
    await page.goto("https://arh.antoinevastel.com/bots/areyouheadless")

    // extract the message contained on the page
    const messageElement = page.locator('#res')
    const message = await messageElement.textContent()

    // print the resulting message
    console.log(`The result is: "${message}"`)

  // close the browser and release its resources
  await browser.close()
})()
First, install playwright-extra and puppeteer-extra-plugin-stealth:

npm install playwright-extra puppeteer-extra-plugin-stealth
Next, import chromium from playwright-extra instead of playwright and import StealthPlugin from puppeteer-extra-plugin-stealth:

import { chromium } from "playwright-extra"
import StealthPlugin from "puppeteer-extra-plugin-stealth"
Then, register the Stealth Plugin with:

chromium.use(StealthPlugin())
Put it all together, and you will get:

import { chromium } from "playwright-extra"
import StealthPlugin from "puppeteer-extra-plugin-stealth"

(async () => {
    // configure the Stealth plugin
    chromium.use(StealthPlugin())

    // set up the browser and launch it
    const browser = await chromium.launch()
    // open a new blank page
    const page = await browser.newPage()

    // navigate the page to the target page
    await page.goto("https://arh.antoinevastel.com/bots/areyouheadless")

    // extract the message contained on the page
    const messageElement = page.locator('#res')
    const message = await messageElement.textContent()

    // print the resulting message
    console.log(`The result is: "${message}"`)

    // close the browser and release its resources
    await browser.close()
})()
Awesome! You just integrated the Stealth plugin into Playwright in JavaScript.
