SeleniumBase README

SeleniumBase

PyPI version SeleniumBase PyPI downloads 
SeleniumBase SeleniumBase GitHub Actions SeleniumBase on GitHub

Stealthy Chromium Automation and E2E Testing.
🚀 Start | 🏰 Features | 🎛️ Options | 📚 Examples | 💻 Scripts | 🗾 Locale
📗 API | 📘 Stealth API | 🔠 DesignPatterns | 🔴 Recorder | 📊 Dashboard
🎖️ GUI | 📰 TestPage | 👤 UC Mode | 🐙 CDP Mode | 📶 Charts | 🖥️ Farm
👁️ How | 🚝 Migration | 🎭 Stealthy Playwright | 🛂 MasterQA | 🚎 Tours
🤖 CI/CD | 🟨 JSMgr | 🌏 Translator | 🎞️ Presenter | 🖼️ Visual | 🗂️ CPlans

🐙 CDP Mode bypasses bot-detection and handles CAPTCHAs by driving the browser directly through the Chrome DevTools Protocol. Includes Stealthy Playwright Mode, which extends these advanced anti-detection patches to Playwright scripts.

📚 The SeleniumBase/examples/ folder includes over 100 ready-to-run examples of E2E testing. Examples that start with test_ or end with _test.py/_tests.py are specifically designed to run with pytest. Other examples run directly with raw python (those files generally start with raw_ to avoid confusion).

🥷 Stealthy CDP Mode examples are located in ./examples/cdp_mode/.

🎭 Stealthy Playwright examples are located in ./examples/cdp_mode/playwright.

⚙️ Stealthy architecture flowchart:
Stealthy architecture flowchart

(For maximum stealth, use CDP Mode, which includes Stealthy Playwright Mode)

📝 This example verifies that Pure CDP Mode is stealthy on BrowserScan:

from seleniumbase import sb_cdp

url = "https://www.browserscan.net/bot-detection"
sb = sb_cdp.Chrome(url, locale="en", ad_block=True)
sb.flash("Test Results", duration=3, pause=1)
sb.assert_element('strong:contains("Normal")')
print("Bot Not detected")
sb.flash('strong:contains("Normal")', duration=3, pause=2)
Stealthy architecture flowchart 📝 This example demonstrates the drop-in patch that makes Playwright stealthy:
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome(locale="en", ad_block=True)
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://www.browserscan.net/bot-detection")
    page.wait_for_timeout(500)
    sb.flash("Test Results", duration=3, pause=1)
    sb.assert_element('strong:contains("Normal")')
    sb.flash('strong:contains("Normal")', duration=3, pause=2)
-------- 💡 You can set which Chromium browser to use via command-line options:
python SCRIPT.py --use-chromium  # Use the unbranded Chromium browser
python SCRIPT.py --cft  # Use Chrome-for-testing
python SCRIPT.py --edge  # Use Microsoft Edge
python SCRIPT.py --brave  # Use Brave browser
Google Chrome is the default browser if not specified. Only unbranded Chromium and Chrome-for-Testing are installed automatically if not already installed. You can also set the browser via method args, eg: `cft=True`, `use_chromium=True`, `browser="edge"`, `browser="brave"`, etc. Eg:
sb = sb_cdp.Chrome(url, use_chromium=True)
--------
📝 This example scrapes Hacker News listings with Pure CDP Mode:

from seleniumbase import sb_cdp

url = "https://news.ycombinator.com/submitted?id=seleniumbase"
sb = sb_cdp.Chrome(url)
elements = sb.find_elements("span.titleline > a")
for element in elements:
    print("* " + element.text)
--------
📝 This example saves Google Search results with UC + CDP Mode:
(Results are saved as PDF, HTML, and PNG files)

from seleniumbase import SB

with SB(uc=True, test=True) as sb:
    url = "https://google.com/ncr"
    sb.activate_cdp_mode(url)
    sb.click_if_visible('button:contains("Accept all")')
    sb.type('[name="q"]', "SeleniumBase GitHub page")
    sb.click('[value="Google Search"]')
    sb.sleep(4)  # The "AI Overview" sometimes loads
    print(sb.get_page_title())
    sb.save_as_pdf_to_logs()
    sb.save_page_source_to_logs()
    sb.save_screenshot_to_logs()
    print("Logs have been saved to: ./latest_logs/")
--------
📝 This example bypasses Cloudflare's challenge page with UC + CDP Mode:

from seleniumbase import SB

with SB(uc=True, test=True, locale="en") as sb:
    url = "https://gitlab.com/users/sign_in"
    sb.activate_cdp_mode(url)
    sb.sleep(2)
    sb.solve_captcha()
    # (The rest is for testing and demo purposes)
    sb.assert_text("Username", '[for="user_login"]', timeout=3)
    sb.assert_element('label[for="user_login"]')
    sb.highlight('button:contains("Sign in")')
    sb.highlight('h1:contains("GitLab")')
    sb.post_message("SeleniumBase wasn't detected", duration=4)
SeleniumBase SeleniumBase ----
📝 This example handles a CAPTCHA page with Pure CDP Mode:

from seleniumbase import sb_cdp

url = "https://gitlab.com/users/sign_in"
sb = sb_cdp.Chrome(url, incognito=True)
sb.sleep(2)
sb.solve_captcha()
sb.highlight('h1:contains("GitLab")')
sb.highlight('button:contains("Sign in")')
--------
📝 This example tests an e-commerce site with pytest:

from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)  # Call pytest

class MyTestClass(BaseCase):
    def test_swag_labs(self):
        self.open("https://www.saucedemo.com")
        self.type("#user-name", "standard_user")
        self.type("#password", "secret_sauce\n")
        self.assert_element("div.inventory_list")
        self.click('button[name*="backpack"]')
        self.click("#shopping_cart_container a")
        self.assert_text("Backpack", "div.cart_item")
        self.click("button#checkout")
        self.type("input#first-name", "SeleniumBase")
        self.type("input#last-name", "Automation")
        self.type("input#postal-code", "77123")
        self.click("input#continue")
        self.click("button#finish")
        self.assert_text("Thank you for your order!")
> `pytest test_get_swag.py` SeleniumBase Test --------
📝 This example tests another e-commerce site with pytest:

pytest test_coffee_cart.py --demo
SeleniumBase Coffee Cart Test

>
(--demo mode slows down tests and highlights actions)

--------
📝 This example covers multiple actions with pytest:

pytest test_demo_site.py
SeleniumBase Example

> Easy to type, click, select, toggle, drag & drop, and more. (For more examples, see the SeleniumBase/examples/ folder.) --------
SeleniumBase

Explore the README:

Get Started / Installation
Basic Example / Usage
Common Test Methods
Fun Facts / Learn More
Demo Mode / Debugging
Command-line Options
Directory Configuration
SeleniumBase Dashboard
Generating Test Reports
--------
▶️ How is SeleniumBase different from raw Selenium? (click to expand)
--------
📚 Learn about different ways of writing tests:

📗📝 Here's test_simple_login.py, which uses BaseCase class inheritance, and runs with pytest or pynose. (Use self.driver to access Selenium's raw driver.)

from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class TestSimpleLogin(BaseCase):
    def test_simple_login(self):
        self.open("seleniumbase.io/simple/login")
        self.type("#username", "demo_user")
        self.type("#password", "secret_pass")
        self.click('a:contains("Sign in")')
        self.assert_exact_text("Welcome!", "h1")
        self.assert_element("img#image1")
        self.highlight("#image1")
        self.click_link("Sign out")
        self.assert_text("signed out", "#top_message")
📘📝 Here's raw_login_sb.py, which uses the SB Context Manager. Runs with pure python. (Use sb.driver to access Selenium's raw driver.)

from seleniumbase import SB

with SB() as sb:
    sb.open("seleniumbase.io/simple/login")
    sb.type("#username", "demo_user")
    sb.type("#password", "secret_pass")
    sb.click('a:contains("Sign in")')
    sb.assert_exact_text("Welcome!", "h1")
    sb.assert_element("img#image1")
    sb.highlight("#image1")
    sb.click_link("Sign out")
    sb.assert_text("signed out", "#top_message")
📙📝 Here's raw_login_driver.py, which uses the Driver Manager. Runs with pure python. (The driver is an improved version of Selenium's raw driver, with more methods.)

from seleniumbase import Driver

driver = Driver()
try:
    driver.open("seleniumbase.io/simple/login")
    driver.type("#username", "demo_user")
    driver.type("#password", "secret_pass")
    driver.click('a:contains("Sign in")')
    driver.assert_exact_text("Welcome!", "h1")
    driver.assert_element("img#image1")
    driver.highlight("#image1")
    driver.click_link("Sign out")
    driver.assert_text("signed out", "#top_message")
finally:
    driver.quit()
--------
SeleniumBase Set up Python & Git:
Supported Python Versions 🔵 Add Python and Git to your System PATH. 🔵 Using a Python virtual env is recommended.
SeleniumBase Install SeleniumBase:
**You can install `seleniumbase` from [PyPI](https://pypi.org/project/seleniumbase/) or [GitHub](https://github.com/seleniumbase/SeleniumBase):** 🔵 **How to install `seleniumbase` from PyPI:**
pip install seleniumbase
* (Add `--upgrade` OR `-U` to upgrade SeleniumBase.) * (Add `--force-reinstall` to upgrade indirect packages.) 🔵 **How to install `seleniumbase` from a GitHub clone:**
git clone https://github.com/seleniumbase/SeleniumBase.git
cd SeleniumBase/
pip install -e .
🔵 **How to upgrade an existing install from a GitHub clone:**
git pull
pip install -e .
🔵 **Type `seleniumbase` or `sbase` to verify that SeleniumBase was installed successfully:**
 ___      _          _             ___              
/ __| ___| |___ _ _ (_)_  _ _ __  | _ ) __ _ ______ 
\__ \/ -_) / -_) ' \| | \| | '  \ | _ \/ _` (_-< -_)
|___/\___|_\___|_||_|_|\_,_|_|_|_\|___/\__,_/__|___|
----------------------------------------------------

╭──────────────────────────────────────────────────╮
│  * USAGE: "seleniumbase [COMMAND] [PARAMETERS]"  │
│  *    OR:        "sbase [COMMAND] [PARAMETERS]"  │
│                                                  │
│ COMMANDS:        PARAMETERS / DESCRIPTIONS:      │
│    get / install    [DRIVER_NAME] [OPTIONS]      │
│    methods          (List common Python methods) │
│    options          (List common pytest options) │
│    behave-options   (List common behave options) │
│    gui / commander  [OPTIONAL PATH or TEST FILE] │
│    behave-gui       (SBase Commander for Behave) │
│    caseplans        [OPTIONAL PATH or TEST FILE] │
│    mkdir            [DIRECTORY] [OPTIONS]        │
│    mkfile           [FILE.py] [OPTIONS]          │
│    mkrec / codegen  [FILE.py] [OPTIONS]          │
│    recorder         (Open Recorder Desktop App.) │
│    record           (If args: mkrec. Else: App.) │
│    mkpres           [FILE.py] [LANG]             │
│    mkchart          [FILE.py] [LANG]             │
│    print            [FILE] [OPTIONS]             │
│    translate        [SB_FILE.py] [LANG] [ACTION] │
│    convert          [WEBDRIVER_UNITTEST_FILE.py] │
│    extract-objects  [SB_FILE.py]                 │
│    inject-objects   [SB_FILE.py] [OPTIONS]       │
│    objectify        [SB_FILE.py] [OPTIONS]       │
│    revert-objects   [SB_FILE.py] [OPTIONS]       │
│    encrypt / obfuscate                           │
│    decrypt / unobfuscate                         │
│    proxy            (Start a basic proxy server) │
│    download server  (Get Selenium Grid JAR file) │
│    grid-hub         [start|stop] [OPTIONS]       │
│    grid-node        [start|stop] --hub=[HOST/IP] │
│                                                  │
│ *  EXAMPLE => "sbase get chromedriver stable"    │
│ *  For command info => "sbase help [COMMAND]"    │
│ *  For info on all commands => "sbase --help"    │
╰──────────────────────────────────────────────────╯
🔵 Downloading webdrivers:
✅ SeleniumBase automatically downloads webdrivers as needed, such as `chromedriver`.
▶️ Here's sample output from a chromedriver download. (click to expand)
SeleniumBase Basic Example / Usage:
🔵 If you've cloned SeleniumBase, you can run tests from the [examples/](https://github.com/seleniumbase/SeleniumBase/tree/master/examples) folder.
Here's my_first_test.py:

cd examples/
pytest my_first_test.py
SeleniumBase Test
Here's the full code for my_first_test.py:

from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class MyTestClass(BaseCase):
    def test_swag_labs(self):
        self.open("https://www.saucedemo.com")
        self.type("#user-name", "standard_user")
        self.type("#password", "secret_sauce\n")
        self.assert_element("div.inventory_list")
        self.assert_exact_text("Products", "span.title")
        self.click('button[name*="backpack"]')
        self.click("#shopping_cart_container a")
        self.assert_exact_text("Your Cart", "span.title")
        self.assert_text("Backpack", "div.cart_item")
        self.click("button#checkout")
        self.type("#first-name", "SeleniumBase")
        self.type("#last-name", "Automation")
        self.type("#postal-code", "77123")
        self.click("input#continue")
        self.assert_text("Checkout: Overview")
        self.assert_text("Backpack", "div.cart_item")
        self.assert_text("29.99", "div.inventory_item_price")
        self.click("button#finish")
        self.assert_exact_text("Thank you for your order!", "h2")
        self.assert_element('img[alt="Pony Express"]')
        self.js_click("a#logout_sidebar_link")
        self.assert_element("div#login_button_container")
* By default, **[CSS Selectors](https://www.w3schools.com/cssref/css_selectors.asp)** are used for finding page elements. * If you're new to CSS Selectors, games like [CSS Diner](http://flukeout.github.io/) can help you learn. * For more reading, [here's an advanced guide on CSS attribute selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/Attribute_selectors).
SeleniumBase Here are some common SeleniumBase methods:
self.open(url)  # Navigate the browser window to the URL.
self.activate_cdp_mode()  # Activate CDP Mode from UC Mode.
self.type(selector, text)  # Update the field with the text.
self.click(selector)  # Click the element with the selector.
self.click_link(link_text)  # Click the link containing text.
self.go_back()  # Navigate back to the previous URL.
self.select_option_by_text(dropdown_selector, option)
self.hover_and_click(hover_selector, click_selector)
self.drag_and_drop(drag_selector, drop_selector)
self.get_text(selector)  # Get the text from the element.
self.get_current_url()  # Get the URL of the current page.
self.get_page_source()  # Get the HTML of the current page.
self.get_attribute(selector, attribute)  # Get element attribute.
self.get_title()  # Get the title of the current page.
self.switch_to_frame(frame)  # Switch into the iframe container.
self.switch_to_default_content()  # Leave the iframe container.
self.open_new_window()  # Open a new window in the same browser.
self.switch_to_window(window)  # Switch to the browser window.
self.switch_to_default_window()  # Switch to the original window.
self.get_new_driver(OPTIONS)  # Open a new driver with OPTIONS.
self.switch_to_driver(driver)  # Switch to the browser driver.
self.switch_to_default_driver()  # Switch to the original driver.
self.wait_for_element(selector)  # Wait until element is visible.
self.is_element_visible(selector)  # Return element visibility.
self.is_text_visible(text, selector)  # Return text visibility.
self.sleep(seconds)  # Do nothing for the given amount of time.
self.save_screenshot(name)  # Save a screenshot in .png format.
self.assert_element(selector)  # Verify the element is visible.
self.assert_text(text, selector)  # Verify text in the element.
self.assert_exact_text(text, selector)  # Verify text is exact.
self.assert_title(title)  # Verify the title of the web page.
self.assert_downloaded_file(file)  # Verify file was downloaded.
self.assert_no_404_errors()  # Verify there are no broken links.
self.assert_no_js_errors()  # Verify there are no JS errors.
🔵 For the complete list of SeleniumBase methods, see: Method Summary
SeleniumBase Fun Facts / Learn More:
✅ SeleniumBase automatically handles common WebDriver actions such as launching web browsers before tests, saving screenshots during failures, and closing web browsers after tests.

✅ SeleniumBase lets you customize tests via command-line options.

✅ SeleniumBase uses simple syntax for commands. Example:

self.type("input", "dogs\n")  # (The "\n" presses ENTER)
Most SeleniumBase scripts can be run with pytest, pynose, or pure python. Not all test runners can run all test formats. For example, tests that use the `sb` pytest fixture can only be run with `pytest`. (See Syntax Formats) There's also a Gherkin test format that runs with behave.
pytest coffee_cart_tests.py --rs
pytest test_sb_fixture.py --demo
pytest test_suite.py --rs --html=report.html --dashboard

pynose basic_test.py --mobile
pynose test_suite.py --headless --report --show-report

python raw_sb.py
python raw_test_scripts.py

behave realworld.feature
behave calculator.feature -D rs -D dashboard
✅ pytest includes automatic test discovery. If you don't specify a specific file or folder to run, pytest will automatically search through all subdirectories for tests to run based on the following criteria:

* Python files that start with `test_` or end with `_test.py`. * Python methods that start with `test_`. With a SeleniumBase [pytest.ini](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/pytest.ini) file present, you can modify default discovery settings. The Python class name can be anything because `seleniumbase.BaseCase` inherits `unittest.TestCase` to trigger autodiscovery.
✅ You can do a pre-flight check to see which tests would get discovered by pytest before the actual run:

pytest --co -q
✅ You can be more specific when calling pytest or pynose on a file:

pytest [FILE_NAME.py]::[CLASS_NAME]::[METHOD_NAME]

pynose [FILE_NAME.py]:[CLASS_NAME].[METHOD_NAME]
✅ No More Flaky Tests! SeleniumBase methods automatically wait for page elements to finish loading before interacting with them (up to a timeout limit).

NO MORE FLAKY TESTS! ✅ SeleniumBase supports all major browsers and operating systems:
Browsers: Chrome, Edge, Firefox, and Safari.

Systems: Linux/Ubuntu, macOS, and Windows.

✅ SeleniumBase works on all popular CI/CD platforms:
GitHub Actions integration Jenkins integration Azure integration Google Cloud integration AWS integration Your Computer

✅ SeleniumBase includes an automated/manual hybrid solution called MasterQA to speed up manual testing with automation while manual testers handle validation.

✅ SeleniumBase supports running tests while offline (assuming webdrivers have previously been downloaded when online).

✅ For a full list of SeleniumBase features, Click Here.

SeleniumBase Demo Mode / Debugging:
🔵 Demo Mode helps you see what a test is doing. If a test is moving too fast for your eyes, run it in Demo Mode to pause the browser briefly between actions, highlight page elements being acted on, and display assertions:
pytest my_first_test.py --demo
🔵 `time.sleep(seconds)` can be used to make a test wait at a specific spot:
import time; time.sleep(3)  # Do nothing for 3 seconds.
🔵 **Debug Mode** with Python's built-in **[pdb](https://docs.python.org/3/library/pdb.html)** library helps you debug tests:
breakpoint()  # Shortcut for "import pdb; pdb.set_trace()"
> (**`pdb`** commands: `n`, `c`, `s`, `u`, `d` => `next`, `continue`, `step`, `up`, `down`) 🔵 To pause an active test that throws an exception or error, (*and keep the browser window open while **Debug Mode** begins in the console*), add **`--pdb`** as a `pytest` option:
pytest test_fail.py --pdb
🔵 To start tests in Debug Mode, add **`--trace`** as a `pytest` option:
pytest test_coffee_cart.py --trace
SeleniumBase test with the pdbp (Pdb+) debugger
🔵 Command-line Options:
✅ Here are some useful command-line options that come with pytest:
-v  # Verbose mode. Prints the full name of each test and shows more details.
-q  # Quiet mode. Print fewer details in the console output when running tests.
-x  # Stop running the tests after the first failure is reached.
--html=report.html  # Creates a detailed pytest-html report after tests finish.
--co | --collect-only  # Show what tests would get run. (Without running them)
--co -q  # (Both options together!) - Do a dry run with full test names shown.
-n=NUM  # Multithread the tests using that many threads. (Speed up test runs!)
-s  # See print statements. (Should be on by default with pytest.ini present.)
--junit-xml=report.xml  # Creates a junit-xml report after tests finish.
--pdb  # If a test fails, enter Post Mortem Debug Mode. (Don't use with CI!)
--trace  # Enter Debug Mode at the beginning of each test. (Don't use with CI!)
-m=MARKER  # Run tests with the specified pytest marker.
✅ SeleniumBase provides additional pytest command-line options for tests:
--browser=BROWSER  # (The web browser to use. Default: "chrome".)
--chrome  # (Shortcut for "--browser=chrome". On by default.)
--edge  # (Shortcut for "--browser=edge".)
--firefox  # (Shortcut for "--browser=firefox".)
--safari  # (Shortcut for "--browser=safari".)
--opera  # (Shortcut for "--browser=opera".)
--brave  # (Shortcut for "--browser=brave".)
--comet  # (Shortcut for "--browser=comet".)
--atlas  # (Shortcut for "--browser=atlas".)
--settings-file=FILE  # (Override default SeleniumBase settings.)
--env=ENV  # (Set the test env. Access with "self.env" in tests.)
--account=STR  # (Set account. Access with "self.account" in tests.)
--data=STRING  # (Extra test data. Access with "self.data" in tests.)
--var1=STRING  # (Extra test data. Access with "self.var1" in tests.)
--var2=STRING  # (Extra test data. Access with "self.var2" in tests.)
--var3=STRING  # (Extra test data. Access with "self.var3" in tests.)
--variables=DICT  # (Extra test data. Access with "self.variables".)
--user-data-dir=DIR  # (Set the Chrome user data directory to use.)
--protocol=PROTOCOL  # (The Selenium Grid protocol: http|https.)
--server=SERVER  # (The Selenium Grid server/IP used for tests.)
--port=PORT  # (The Selenium Grid port used by the test server.)
--cap-file=FILE  # (The web browser's desired capabilities to use.)
--cap-string=STRING  # (The web browser's desired capabilities to use.)
--proxy=SERVER:PORT  # (Connect to a proxy server:port as tests are running)
--proxy=USERNAME:PASSWORD@SERVER:PORT  # (Use an authenticated proxy server)
--proxy-bypass-list=STRING # (";"-separated hosts to bypass, Eg "*.foo.com")
--proxy-pac-url=URL  # (Connect to a proxy server using a PAC_URL.pac file.)
--proxy-pac-url=USERNAME:PASSWORD@URL  # (Authenticated proxy with PAC URL.)
--proxy-driver  # (If a driver download is needed, will use: --proxy=PROXY.)
--multi-proxy  # (Allow multiple authenticated proxies when multi-threaded.)
--agent=STRING  # (Modify the web browser's User-Agent string.)
--mobile  # (Use the mobile device emulator while running tests.)
--metrics=STRING  # (Set mobile metrics: "CSSWidth,CSSHeight,PixelRatio".)
--chromium-arg="ARG=N,ARG2"  # (Set Chromium args, ","-separated, no spaces.)
--firefox-arg="ARG=N,ARG2"  # (Set Firefox args, comma-separated, no spaces.)
--firefox-pref=SET  # (Set a Firefox preference:value set, comma-separated.)
--extension-zip=ZIP  # (Load a Chrome Extension .zip|.crx, comma-separated.)
--extension-dir=DIR  # (Load a Chrome Extension directory, comma-separated.)
--disable-features="F1,F2"  # (Disable features, comma-separated, no spaces.)
--binary-location=PATH  # (Set path of the Chromium browser binary to use.)
--driver-version=VER  # (Set the chromedriver or uc_driver version to use.)
--sjw  # (Skip JS Waits for readyState to be "complete" or Angular to load.)
--wfa  # (Wait for AngularJS to be done loading after specific web actions.)
--pls=PLS  # (Set pageLoadStrategy on Chrome: "normal", "eager", or "none".)
--headless  # (The default headless mode. Linux uses this mode by default.)
--headless1  # (Use Chrome's old headless mode. Fast, but has limitations.)
--headless2  # (Use Chrome's new headless mode, which supports extensions.)
--headed  # (Run tests in headed/GUI mode on Linux OS, where not default.)
--xvfb  # (Run tests using the Xvfb virtual display server on Linux OS.)
--xvfb-metrics=STRING  # (Set Xvfb display size on Linux: "Width,Height".)
--locale=LOCALE_CODE  # (Set the Language Locale Code for the web browser.)
--interval=SECONDS  # (The autoplay interval for presentations & tour steps)
--start-page=URL  # (The starting URL for the web browser when tests begin.)
--archive-logs  # (Archive existing log files instead of deleting them.)
--archive-downloads  # (Archive old downloads instead of deleting them.)
--time-limit=SECONDS  # (Safely fail any test that exceeds the time limit.)
--slow  # (Slow down the automation. Faster than using Demo Mode.)
--demo  # (Slow down and visually see test actions as they occur.)
--demo-sleep=SECONDS  # (Set the wait time after Slow & Demo Mode actions.)
--highlights=NUM  # (Number of highlight animations for Demo Mode actions.)
--message-duration=SECONDS  # (The time length for Messenger alerts.)
--check-js  # (Check for JavaScript errors after page loads.)
--ad-block  # (Block some types of display ads from loading.)
--host-resolver-rules=RULES  # (Set host-resolver-rules, comma-separated.)
--block-images  # (Block images from loading during tests.)
--do-not-track  # (Indicate to websites that you don't want to be tracked.)
--verify-delay=SECONDS  # (The delay before MasterQA verification checks.)
--ee | --esc-end  # (Lets the user end the current test via the ESC key.)
--recorder  # (Enables the Recorder for turning browser actions into code.)
--rec-behave  # (Same as Recorder Mode, but also generates behave-gherkin.)
--rec-sleep  # (If the Recorder is enabled, also records self.sleep calls.)
--rec-print  # (If the Recorder is enabled, prints output after tests end.)
--disable-cookies  # (Disable Cookies on websites. Pages might break!)
--disable-js  # (Disable JavaScript on websites. Pages might break!)
--disable-csp  # (Disable the Content Security Policy of websites.)
--disable-ws  # (Disable Web Security on Chromium-based browsers.)
--enable-ws  # (Enable Web Security on Chromium-based browsers.)
--enable-sync  # (Enable "Chrome Sync" on websites.)
--uc | --undetected  # (Use undetected-chromedriver to evade bot-detection.)
--uc-cdp-events  # (Capture CDP events when running in "--undetected" mode.)
--log-cdp  # ("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
--remote-debug  # (Sync to Chrome Remote Debugger chrome://inspect/#devices)
--ftrace | --final-trace  # (Debug Mode after each test. Don't use with CI!)
--dashboard  # (Enable the SeleniumBase Dashboard. Saved at: dashboard.html)
--dash-title=STRING  # (Set the title shown for the generated dashboard.)
--enable-3d-apis  # (Enables WebGL and 3D APIs.)
--swiftshader  # (Chrome "--use-gl=angle" / "--use-angle=swiftshader-webgl")
--incognito  # (Enable Chrome's Incognito mode.)
--guest  # (Enable Chrome's Guest mode.)
--dark  # (Enable Chrome's Dark mode.)
--devtools  # (Open Chrome's DevTools when the browser opens.)
--rs | --reuse-session  # (Reuse browser session for all tests.)
--rcs | --reuse-class-session  # (Reuse session for tests in class.)
--crumbs  # (Delete all cookies between tests reusing a session.)
--disable-beforeunload  # (Disable the "beforeunload" event on Chrome.)
--window-position=X,Y  # (Set the browser's starting window position.)
--window-size=WIDTH,HEIGHT  # (Set the browser's starting window size.)
--maximize  # (Start tests with the browser window maximized.)
--screenshot  # (Save a screenshot at the end of each test.)
--no-screenshot  # (No screenshots saved unless tests directly ask it.)
--visual-baseline  # (Set the visual baseline for Visual/Layout tests.)
--wire  # (Use selenium-wire's webdriver for replacing selenium webdriver.)
--external-pdf  # (Set Chromium "plugins.always_open_pdf_externally":True.)
--timeout-multiplier=MULTIPLIER  # (Multiplies the default timeout values.)
--list-fail-page  # (After each failing test, list the URL of the failure.)
(See the full list of command-line option definitions **[here](https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/plugins/pytest_plugin.py)**. For detailed examples of command-line options, see **[customizing_test_runs.md](help_docs/customizing_test_runs.md)**) -------- 🔵 During test failures, logs and screenshots from the most recent test run will get saved to the `latest_logs/` folder. Those logs will get moved to `archived_logs/` if you add --archive_logs to command-line options, or have `ARCHIVE_EXISTING_LOGS` set to True in [settings.py](https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/config/settings.py), otherwise log files with be cleaned up at the start of the next test run. The `test_suite.py` collection contains tests that fail on purpose so that you can see how logging works.
cd examples/

pytest test_suite.py --chrome

pytest test_suite.py --firefox
An easy way to override seleniumbase/config/settings.py is by using a custom settings file. Here's the command-line option to add to tests: (See [examples/custom_settings.py](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/custom_settings.py)) `--settings_file=custom_settings.py` (Settings include default timeout values, a two-factor auth key, DB credentials, S3 credentials, and other important settings used by tests.) 🔵 To pass additional data from the command-line to tests, add `--data="ANY STRING"`. Inside your tests, you can use `self.data` to access that.
SeleniumBase Directory Configuration:
🔵 When running tests with **`pytest`**, you'll want a copy of **[pytest.ini](https://github.com/seleniumbase/SeleniumBase/blob/master/pytest.ini)** in your root folders. When running tests with **`pynose`**, you'll want a copy of **[setup.cfg](https://github.com/seleniumbase/SeleniumBase/blob/master/setup.cfg)** in your root folders. These files specify default configuration details for tests. Test folders should also include a blank **[__init__.py](https://github.com/seleniumbase/SeleniumBase/blob/master/examples/offline_examples/__init__.py)** file to allow your test files to import other files from that folder. 🔵 `sbase mkdir DIR` creates a folder with config files and sample tests:
sbase mkdir ui_tests
> That new folder will have these files:
ui_tests/
├── __init__.py
├── my_first_test.py
├── parameterized_test.py
├── pytest.ini
├── requirements.txt
├── setup.cfg
├── test_demo_site.py
└── boilerplates/
    ├── __init__.py
    ├── base_test_case.py
    ├── boilerplate_test.py
    ├── classic_obj_test.py
    ├── page_objects.py
    ├── sb_fixture_test.py
    └── samples/
        ├── __init__.py
        ├── google_objects.py
        ├── google_test.py
        ├── sb_swag_test.py
        └── swag_labs_test.py
ProTip™: You can also create a boilerplate folder without any sample tests in it by adding `-b` or `--basic` to the `sbase mkdir` command:
sbase mkdir ui_tests --basic
> That new folder will have these files:
ui_tests/
├── __init__.py
├── pytest.ini
├── requirements.txt
└── setup.cfg
Of those files, the `pytest.ini` config file is the most important, followed by a blank `__init__.py` file. There's also a `setup.cfg` file (for pynose). Finally, the `requirements.txt` file can be used to help you install seleniumbase into your environments (if it's not already installed). ProTip™: Add `--gha` to include a GitHub Actions `.yml` file with default settings:
ui_tests/
└── .github                    
    └── workflows/             
        └── python-package.yml
--------
SeleniumBase Log files from failed tests:
Let's try an example of a test that fails:
""" test_fail.py """
from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class MyTestClass(BaseCase):

    def test_find_army_of_robots_on_xkcd_desert_island(self):
        self.open("https://xkcd.com/731/")
        self.assert_element("div#ARMY_OF_ROBOTS", timeout=1)  # This should fail
You can run it from the `examples/` folder like this:
pytest test_fail.py
🔵 You'll notice that a logs folder, `./latest_logs/`, was created to hold information (and screenshots) about the failing test. During test runs, past results get moved to the archived_logs folder if you have ARCHIVE_EXISTING_LOGS set to True in [settings.py](https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/config/settings.py), or if your run tests with `--archive-logs`. If you choose not to archive existing logs, they will be deleted and replaced by the logs of the latest test run. --------
SeleniumBase SeleniumBase Dashboard:
🔵 The `--dashboard` option for pytest generates a SeleniumBase Dashboard located at `dashboard.html`, which updates automatically as tests run and produce results. Example:
pytest --dashboard --rs --headless
The SeleniumBase Dashboard 🔵 Additionally, you can host your own SeleniumBase Dashboard Server on a port of your choice. Here's an example of that using Python's `http.server`:
python -m http.server 1948
🔵 Now you can navigate to `http://localhost:1948/dashboard.html` in order to view the dashboard as a web app. This requires two different terminal windows: one for running the server, and another for running the tests, which should be run from the same directory. (Use Ctrl+C to stop the http server.) 🔵 Here's a full example of what the SeleniumBase Dashboard may look like:
pytest test_suite.py test_image_saving.py --dashboard --rs --headless
The SeleniumBase Dashboard --------
SeleniumBase Generating Test Reports:
🔵 pytest HTML Reports:
✅ Using `--html=report.html` gives you a fancy report of the name specified after your test suite completes.
pytest test_suite.py --html=report.html
Example Pytest Report ✅ When combining pytest html reports with SeleniumBase Dashboard usage, the pie chart from the Dashboard will get added to the html report. Additionally, if you set the html report URL to be the same as the Dashboard URL when also using the dashboard, (example: `--dashboard --html=dashboard.html`), then the Dashboard will become an advanced html report when all the tests complete. ✅ Here's an example of an upgraded html report:
pytest test_suite.py --dashboard --html=report.html
Dashboard Pytest HTML Report If viewing pytest html reports in [Jenkins](https://www.jenkins.io/), you may need to [configure Jenkins settings](https://stackoverflow.com/a/46197356/7058266) for the html to render correctly. This is due to [Jenkins CSP changes](https://www.jenkins.io/doc/book/system-administration/security/configuring-content-security-policy/). You can also use `--junit-xml=report.xml` to get an xml report instead. Jenkins can use this file to display better reporting for your tests.
pytest test_suite.py --junit-xml=report.xml
🔵 pynose Reports:
The `--report` option gives you a fancy report after your test suite completes.
pynose test_suite.py --report
Example pynose Report (NOTE: You can add `--show-report` to immediately display pynose reports after the test suite completes. Only use `--show-report` when running tests locally because it pauses the test run.)
🔵 behave Dashboard & Reports:
(The [behave_bdd/](https://github.com/seleniumbase/SeleniumBase/tree/master/examples/behave_bdd) folder can be found in the [examples/](https://github.com/seleniumbase/SeleniumBase/tree/master/examples) folder.)
behave behave_bdd/features/ -D dashboard -D headless
SeleniumBase You can also use `--junit` to get `.xml` reports for each behave feature. Jenkins can use these files to display better reporting for your tests.
behave behave_bdd/features/ --junit -D rs -D headless
🔵 Allure Reports:
See: [https://allurereport.org/docs/pytest/](https://allurereport.org/docs/pytest/) SeleniumBase no longer includes `allure-pytest` as part of installed dependencies. If you want to use it, install it first:
pip install allure-pytest
Now your tests can create Allure results files, which can be processed by Allure Reports.
pytest test_suite.py --alluredir=allure_results
--------
SeleniumBase Using a Proxy Server:
If you wish to use a proxy server for your browser tests (Chromium or Firefox), you can add `--proxy=IP_ADDRESS:PORT` as an argument on the command line.
pytest proxy_test.py --proxy=IP_ADDRESS:PORT
If the proxy server that you wish to use requires authentication, you can do the following (Chromium only):
pytest proxy_test.py --proxy=USERNAME:PASSWORD@IP_ADDRESS:PORT
SeleniumBase also supports SOCKS4 and SOCKS5 proxies:
pytest proxy_test.py --proxy="socks4://IP_ADDRESS:PORT"

pytest proxy_test.py --proxy="socks5://IP_ADDRESS:PORT"
To make things easier, you can add your frequently-used proxies to PROXY_LIST in [proxy_list.py](https://github.com/seleniumbase/SeleniumBase/blob/master/seleniumbase/config/proxy_list.py), and then use `--proxy=KEY_FROM_PROXY_LIST` to use the IP_ADDRESS:PORT of that key.
pytest proxy_test.py --proxy=proxy1
SeleniumBase Changing the User-Agent:
🔵 If you wish to change the User-Agent for your browser tests (Chromium and Firefox only), you can add `--agent="USER AGENT STRING"` as an argument on the command-line.
pytest user_agent_test.py --agent="Mozilla/5.0 (Nintendo 3DS; U; ; en) Version/1.7412.EU"
SeleniumBase Handling Pop-Up Alerts:
🔵 self.accept_alert() automatically waits for and accepts alert pop-ups. self.dismiss_alert() automatically waits for and dismisses alert pop-ups. On occasion, some methods like self.click(SELECTOR) might dismiss a pop-up on its own because they call JavaScript to make sure that the readyState of the page is complete before advancing. If you're trying to accept a pop-up that got dismissed this way, use this workaround: Call self.find_element(SELECTOR).click() instead, (which will let the pop-up remain on the screen), and then use self.accept_alert() to accept the pop-up (more on that here). If pop-ups are intermittent, wrap code in a try/except block.
SeleniumBase Building Guided Tours for Websites:
🔵 Learn about SeleniumBase Interactive Walkthroughs (in the `examples/tour_examples/` folder). It's great for prototyping a website onboarding experience. --------
SeleniumBase Production Environments & Integrations:
▶️ Here are some things you can do to set up a production environment for your testing. (click to expand)
SeleniumBase Detailed Method Specifications and Examples:
🔵 **Navigating to a web page: (and related commands)**
self.open("https://xkcd.com/378/")  # This method opens the specified page.

self.go_back()  # This method navigates the browser to the previous page.

self.go_forward()  # This method navigates the browser forward in history.

self.refresh_page()  # This method reloads the current page.

self.get_current_url()  # This method returns the current page URL.

self.get_page_source()  # This method returns the current page source.
ProTip™: You can use the self.get_page_source() method with Python's find() command to parse through HTML to find something specific. (For more advanced parsing, see the BeautifulSoup example.)
source = self.get_page_source()
head_open_tag = source.find('<head>')
head_close_tag = source.find('</head>', head_open_tag)
everything_inside_head = source[head_open_tag+len('<head>'):head_close_tag]
🔵 **Clicking:** To click an element on the page:
self.click("div#my_id")
**ProTip™:** In most web browsers, you can right-click on a page and select `Inspect Element` to see the CSS selector details that you'll need to create your own scripts. 🔵 **Typing Text:** self.type(selector, text) # updates the text from the specified element with the specified value. An exception is raised if the element is missing or if the text field is not editable. Example:
self.type("input#id_value", "2012")
You can also use self.add_text() or the WebDriver .send_keys() command, but those won't clear the text box first if there's already text inside. 🔵 **Getting the text from an element on a page:**
text = self.get_text("header h2")
🔵 **Getting the attribute value from an element on a page:**
attribute = self.get_attribute("#comic img", "title")
🔵 **Asserting existence of an element on a page within some number of seconds:**
self.wait_for_element_present("div.my_class", timeout=10)
(NOTE: You can also use: `self.assert_element_present(ELEMENT)`) 🔵 **Asserting visibility of an element on a page within some number of seconds:**
self.wait_for_element_visible("a.my_class", timeout=5)
(NOTE: The short versions of that are `self.find_element(ELEMENT)` and `self.assert_element(ELEMENT)`. The `find_element()` version returns the element.) Since the line above returns the element, you can combine that with `.click()` as shown below:
self.find_element("a.my_class", timeout=5).click()

# But you're better off using the following statement, which does the same thing
self.click("a.my_class")  # DO IT THIS WAY!
**ProTip™:** You can use dots to signify class names (Ex: `div.class_name`) as a simplified version of `div[class="class_name"]` within a CSS selector. You can also use `*=` to search for any partial value in a CSS selector as shown below:
self.click('a[name*="partial_name"]')
🔵 **Asserting visibility of text inside an element on a page within some number of seconds:**
self.assert_text("Make it so!", "div#trek div.picard div.quotes")
self.assert_text("Tea. Earl Grey. Hot.", "div#trek div.picard div.quotes", timeout=3)
(NOTE: `self.find_text(TEXT, ELEMENT)` and `self.wait_for_text(TEXT, ELEMENT)` also do this. For backwards compatibility, older method names were kept, but the default timeout may be different.) 🔵 **Asserting Anything:**
self.assert_true(var1 == var2)

self.assert_false(var1 == var2)

self.assert_equal(var1, var2)
🔵 **Useful Conditional Statements: (with creative examples)** ❓ `is_element_visible(selector):` (visible on the page)
if self.is_element_visible('div#warning'):
    print("Red Alert: Something bad might be happening!")
❓ `is_element_present(selector):` (present in the HTML)
if self.is_element_present('div#top_secret img.tracking_cookie'):
    self.contact_cookie_monster()  # Not a real SeleniumBase method
else:
    current_url = self.get_current_url()
    self.contact_the_nsa(url=current_url, message="Dark Zone Found")  # Not a real SeleniumBase method
def is_there_a_cloaked_klingon_ship_on_this_page():
    if self.is_element_present("div.ships div.klingon"):
        return not self.is_element_visible("div.ships div.klingon")
    return False
❓ `is_text_visible(text, selector):` (text visible on element)
if self.is_text_visible("You Shall Not Pass!", "h1"):
    self.open("https://www.youtube.com/watch?v=3xYXUeSmb-Y")
▶️ Click for a longer example of is_text_visible():
❓ `is_link_text_visible(link_text):`
if self.is_link_text_visible("Stop! Hammer time!"):
    self.click_link("Stop! Hammer time!")
🔵 Switching Tabs:
If your test opens up a new tab/window, you can switch to it. (SeleniumBase automatically switches to new tabs that don't open to about:blank URLs.)

self.switch_to_window(1)  # This switches to the new tab (0 is the first one)
🔵 How to handle iframes:
🔵 iframes follow the same principle as new windows: You must first switch to the iframe if you want to perform actions in there:
self.switch_to_frame("iframe")
# ... Now perform actions inside the iframe
self.switch_to_parent_frame()  # Exit the current iframe
To exit from multiple iframes, use `self.switch_to_default_content()`. (If inside a single iframe, this has the same effect as `self.switch_to_parent_frame()`.)
self.switch_to_frame('iframe[name="frame1"]')
self.switch_to_frame('iframe[name="frame2"]')
# ... Now perform actions inside the inner iframe
self.switch_to_default_content()  # Back to the main page
🔵 You can also use a context manager to act inside iframes:
with self.frame_switch("iframe"):
    # ... Now perform actions while inside the code block
# You have left the iframe
This also works with nested iframes:
with self.frame_switch('iframe[name="frame1"]'):
    with self.frame_switch('iframe[name="frame2"]'):
        # ... Now perform actions while inside the code block
    # You are now back inside the first iframe
# You have left all the iframes
🔵 How to execute custom jQuery scripts:
jQuery is a powerful JavaScript library that allows you to perform advanced actions in a web browser. If the web page you're on already has jQuery loaded, you can start executing jQuery scripts immediately. You'd know this because the web page would contain something like the following in the HTML:

<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.3/jquery.min.js"></script>
🔵 It's OK if you want to use jQuery on a page that doesn't have it loaded yet. To do so, run the following command first:
self.activate_jquery()
▶️ Here are some examples of using jQuery in your scripts. (click to expand)
🔵 How to handle a restrictive CSP:
❗ Some websites have a restrictive [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) to prevent users from loading jQuery and other external libraries onto their websites. If you need to use jQuery or another JS library on those websites, add `--disable-csp` as a `pytest` command-line option to load a Chromium extension that bypasses the CSP.
🔵 More JavaScript fun:
▶️ In this example, JavaScript creates a referral button on a page, which is then clicked. (click to expand)
🔵 How to use deferred asserts:
Let's say you want to verify multiple different elements on a web page in a single test, but you don't want the test to fail until you verified several elements at once so that you don't have to rerun the test to find more missing elements on the same page. That's where deferred asserts come in. Here's an example:

from seleniumbase import BaseCase
BaseCase.main(__name__, __file__)

class DeferredAssertTests(BaseCase):
    def test_deferred_asserts(self):
        self.open("https://xkcd.com/993/")
        self.wait_for_element("#comic")
        self.deferred_assert_element('img[alt="Brand Identity"]')
        self.deferred_assert_element('img[alt="Rocket Ship"]')  # Will Fail
        self.deferred_assert_element("#comicmap")
        self.deferred_assert_text("Fake Item", "ul.comicNav")  # Will Fail
        self.deferred_assert_text("Random", "ul.comicNav")
        self.deferred_assert_element('a[name="Super Fake !!!"]')  # Will Fail
        self.deferred_assert_exact_text("Brand Identity", "#ctitle")
        self.deferred_assert_exact_text("Fake Food", "#comic")  # Will Fail
        self.process_deferred_asserts()
deferred_assert_element() and deferred_assert_text() will save any exceptions that would be raised. To flush out all the failed deferred asserts into a single exception, make sure to call self.process_deferred_asserts() at the end of your test method. If your test hits multiple pages, you can call self.process_deferred_asserts() before navigating to a new page so that the screenshot from your log files matches the URL where the deferred asserts were made.
🔵 How to access raw WebDriver:
If you need access to any commands that come with standard WebDriver, you can call them directly like this:

self.driver.delete_all_cookies()
capabilities = self.driver.capabilities
self.driver.find_elements("partial link text", "GitHub")
(In general, you'll want to use the SeleniumBase versions of methods when available.)
🔵 How to retry failing tests automatically:
You can use pytest --reruns=NUM to retry failing tests that many times. Add --reruns-delay=SECONDS to wait that many seconds between retries. Example:

pytest --reruns=1 --reruns-delay=1
You can use the @retry_on_exception() decorator to retry failing methods. (First import: from seleniumbase import decorators). To learn more about SeleniumBase decorators, click here.

-------- > "Catch bugs in QA before deploying code to Production!"



Stealthy Playwright Mode 🎭
🎭 Stealthy Playwright Mode is a subset of SeleniumBase CDP Mode where Playwright attaches to a stealthy browser session via the remote-debugging URL. This lets Playwright bypass bot-detection while allowing APIs of both frameworks to work in tandem. Under the hood, Playwright calls connect_over_cdp() to achieve this stealth.


(See Stealthy Playwright Mode on YouTube! ▶️)

🛠️ Installation¶
To use Stealthy Playwright Mode, simply install the necessary Python packages:

pip install seleniumbase playwright
Note: Just as standard Playwright can use channel="chrome" to bypass internal binary downloads, Stealthy Playwright Mode achieves the same by attaching to the system Chrome browser launched by SeleniumBase. This lets you skip the large playwright install step entirely.

💻 Usage¶
Stealthy Playwright Mode comes in three different formats: 1. sb_cdp "sync" format 2. SB() "nested sync" format 3. cdp_driver "async" format

1. The lightweight "sync" format (sb_cdp)¶
Ideal for standalone scripts that primarily use Playwright but need SeleniumBase's stealth and CAPTCHA-solving power without the overhead of WebDriver.

from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://example.com")
2. The full-suite "nested sync" format (SB())¶
Best for hybrid projects where you need to switch between WebDriver and Playwright APIs in the same session.

from playwright.sync_api import sync_playwright
from seleniumbase import SB

with SB(uc=True) as sb:
    sb.activate_cdp_mode()
    endpoint_url = sb.cdp.get_endpoint_url()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint_url)
        page = browser.contexts[0].pages[0]
        page.goto("https://example.com")
3. The "async" format (cdp_driver)¶
Designed for modern asynchronous Python. This allows you to run multiple concurrent stealth sessions using async/await and Playwright's async_api.

import asyncio
from seleniumbase import cdp_driver
from playwright.async_api import async_playwright

async def main():
    driver = await cdp_driver.start_async()
    endpoint_url = driver.get_endpoint_url()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(endpoint_url)
        page = browser.contexts[0].pages[0]
        await page.goto("https://example.com")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
💡 Key differences of the 3 stealthy formats¶
sb_cdp: Simplest setup. CDP launches a stealthy browser. (No WebDriver)

SB(): Maximum utility. Gives you the full range of APIs: WebDriver, CDP, and Playwright. (WebDriver launches a stealthy browser.)

cdp_driver: Best for performance. asyncio handles non-blocking tasks. CDP launches a stealthy browser. (No WebDriver)

🎭 Converting regular Playwright scripts to Stealthy Playwright Mode:¶
If you have a regular Playwright script that looks like this:

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_context().new_page()
    page.goto("https://example.com")
Then the Stealthy Playwright Mode version of that would look like this:

from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://example.com")
🎭 Stealthy Playwright Mode details¶
The sb_cdp and cdp_driver formats don't use WebDriver at all, meaning that chromedriver isn't needed. From these two formats, Stealthy Playwright Mode can call CDP Mode methods and Playwright methods.

The SB() format requires WebDriver, therefore chromedriver will be downloaded, modified for stealth, and renamed as uc_driver if not already present. The SB() format has access to Selenium WebDriver methods via the SeleniumBase API. When using Stealthy Playwright Mode from the SB() format, all the APIs are accessible: Selenium, SeleniumBase, UC Mode, CDP Mode, and Playwright.

Default timeout values are different between Playwright and SeleniumBase. For instance, a 30-second default timeout in a Playwright method might only be 10 seconds in the equivalent SeleniumBase method.

When specifying custom timeout values, Playwright uses milliseconds, whereas SeleniumBase uses seconds. Eg. page.wait_for_timeout(2000) in Playwright is the equivalent of sb.sleep(2) in SeleniumBase.

Although hard sleeps are generally discouraged, they become a tactical tool in stealth mode because that extra waiting helps the automation look more human. Hard sleeps are used in multiple examples to prevent rate limits from being exceeded.

🎭 A few examples of Stealthy Playwright Mode:¶
🎭 Here's an example that queries Microsoft Copilot:

from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://copilot.microsoft.com")
    page.wait_for_selector("textarea#userInput")
    page.wait_for_timeout(1000)
    query = "Playwright Python connect_over_cdp() sync example"
    page.fill("textarea#userInput", query)
    page.click('button[data-testid="submit-button"]')
    page.wait_for_timeout(4000)
    sb.solve_captcha()
    page.wait_for_selector('button[data-testid*="-thumbs-up"]')
    page.wait_for_timeout(4000)
    page.click('button[data-testid*="scroll-to-bottom"]')
    page.wait_for_timeout(3000)
    chat_results = '[data-testid="highlighted-chats"]'
    result = page.locator(chat_results).inner_text()
    print(result.replace("\n\n", " \n"))
(From examples/cdp_mode/playwright/raw_copilot_sync.py)

🎭 Here's an example that solves the Bing CAPTCHA:

from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome(locale="en")
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://www.bing.com/turing/captcha/challenge")
    page.wait_for_timeout(2000)
    sb.solve_captcha()
    page.wait_for_timeout(2000)
(From examples/cdp_mode/playwright/raw_bing_cap_sync.py)

🎭 For all included examples, see examples/cdp_mode/playwright.¶
🎭 More details about Stealthy Playwright Mode:¶
Stealthy Playwright Mode uses the system's Chrome browser by default. There's also the option of setting use_chromium=True to use the unbranded Chromium browser instead, which still supports extensions. (With regular Playwright, you would generally need to run playwright install to download a special version of Chrome before running Playwright scripts, unless you set channel="chrome" to use the system's Chrome browser instead.)

Playwright's :has-text() selector is the equivalent of SeleniumBase's :contains() selector, except for one small difference: :has-text() isn't case-sensitive, but :contains() is.

In the sync formats, get_endpoint_url() also applies nest-asyncio so that nested event loops are allowed. (Python doesn't allow nested event loops by default). Without this, you'd get the error: "Cannot run the event loop while another loop is running" when calling CDP Mode methods (such as solve_captcha()) from within the Playwright context manager. This nest-asyncio call is done behind-the-scenes so that users don't need to handle this on their own.

🎭 Proxy with auth in Stealthy Playwright Mode:¶
To use an authenticated proxy in Stealthy Playwright Mode, do these two things:
1. Set theproxy arg when launching Chrome. -- Eg: sb_cdp.Chrome(proxy="USER:PASS@IP:PORT") or cdp_driver.start_async("USER:PASS@IP:PORT").
2. Open the URL with SeleniumBase before using endpoint_url to connect to the browser with Playwright.

⚠️ If any trouble with the above, set use_chromium=True so that you can use the base Chromium browser, which still allows extensions, unlike regular branded Chrome, which removed the --load-extension command-line switch. (An extension is used to set the auth for the proxy, which is needed when CDP can't set the proxy alone, such as for navigation after the initial page load).

In the sync format, use sb.open(url) to open the url before connecting Playwright:

sb = sb_cdp.Chrome(use_chromium=True, proxy="user:pass@server:port")
sb.open(url)
endpoint_url = sb.get_endpoint_url()
# ...
In the async format, use, driver.get(url) to open the url before connecting Playwright:

driver = await cdp_driver.start_async(use_chromium=True, proxy="user:pass@server:port")
await driver.get(url)
endpoint_url = driver.get_endpoint_url()
# ...
Here's an example of using an authenticated proxy with Stealthy Playwright Mode:
(The URL is opened before attaching Playwright so that proxy settings take effect)

from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome(use_chromium=True, proxy="user:pass@server:port")
sb.open(url)
endpoint_url = sb.get_endpoint_url()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    # ...
(Fill in the url and the proxy details to complete the script.)
Here's the same thing for the async format:

import asyncio
from playwright.async_api import async_playwright
from seleniumbase import cdp_driver

async def main():
    driver = await cdp_driver.start_async(use_chromium=True, proxy="user:pass@server:port")
    await driver.get(url)
    endpoint_url = driver.get_endpoint_url()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(endpoint_url)
        page = browser.contexts[0].pages[0]
        # ...

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
(Fill in the url and the proxy details to complete the script.)
🎭 This flowchart shows how Stealthy Playwright Mode fits into CDP Mode:
¶
Stealthy architecture flowchart

(See the CDP Mode ReadMe for more information about that.)

🎭 See examples/cdp_mode/playwright for Stealthy Playwight Mode examples.¶



===============================
Guide to SeleniumBase — A Better & Easier Selenium
by Ziad Shamndy
Apr 18, 2026
11 min read
#headless-browser
#selenium
Guide to SeleniumBase — A Better & Easier Selenium
In the world of browser automation, Selenium has long been a key tool for browser automation, but it often involves tedious setups and limited features. SeleniumBase streamlines the process, enhancing Selenium’s capabilities with powerful, user-friendly tools for developers and testers alike.

This guide explores what SeleniumBase is, its features, and its practical use cases. And how it simplifies tasks like web scraping, testing, and screenshot capturing, all while being beginner-friendly and highly adaptable

Key Takeaways
Learn SeleniumBase browser automation with simplified syntax, built-in features, and enhanced capabilities for testing and web scraping workflows.

SeleniumBase simplifies browser automation with intuitive syntax that reduces boilerplate code compared to traditional Selenium
Built-in features eliminate external dependencies including screenshot capture, proxy support, and Cloudflare bypass without additional setup
Cross-browser compatibility supports Chrome, Firefox, Edge, and Safari with minimal configuration changes
Enhanced element locators improve reliability with more robust methods for finding and interacting with page elements
Perfect for both testing and scraping with pytest integration for testing and undetected ChromeDriver for web scraping
Visual testing capabilities with automated screenshot capture and text overlays for debugging and documentation
Proxy integration for advanced scenarios with built-in proxy support for IP rotation and geo-targeting
Detection resistance features with undetected ChromeDriver mode to help bypass anti-bot measures
Get web scraping tips in your inbox
Trusted by 100K+ developers and 30K+ enterprises. Unsubscribe anytime.
Subscribe
What is SeleniumBase?
SeleniumBase is an open-source framework built on top of Selenium, providing a more intuitive, feature-rich interface for browser automation. Its primary goal is to simplify complex tasks with prebuilt methods and utilities while adding additional functionality like Cloudflare bypass, proxy integration, and enhanced debugging.

Why SeleniumBase?
SeleniumBase takes browser automation to the next level by simplifying workflows, enhancing features, and offering unmatched versatility.

Ease of Use: With its clean and concise syntax, SeleniumBase allows you to achieve in a few lines what might take dozens with traditional Selenium, reducing development time and effort.

Enhanced Features: SeleniumBase expands Selenium’s functionality with built-in tools like seleniumBase screenshot capture, enhanced element locators, and advanced configurations, all designed to make automation more efficient and user-friendly.

Versatility: From robust test automation frameworks to advanced web scraping, SeleniumBase adapts to a variety of automation needs, making it a valuable tool for developers and testers alike.

Use Cases for SeleniumBase
SeleniumBase is a versatile tool designed to simplify browser automation across a wide range of applications. Here are some detailed examples of its use cases, showcasing its adaptability and power:

1. Web Application Testing
SeleniumBase is ideal for automating functional, and end-to-end (E2E) tests for web applications. Its simplified syntax, built-in assertions, and cross-browser support make it easy to simulate user actions and verify application behavior.

Example: Testing an e-commerce site by simulating user login, adding items to the cart, and completing the checkout process.
Key Features Used: Assertions, multi-browser testing, and headless mode for CI/CD pipelines.
2. Data Scraping and Extraction
SeleniumBase simplifies web scraping by handling dynamic content, JavaScript rendering, and anti-bot measures like Cloudflare. With its built-in proxy support, it can bypass restrictions and collect data efficiently.

Example: Scraping product details, prices, and availability from an online store.
Key Features Used: Dynamic content handling, proxy integration, and Cloudflare bypass.
3. Performance Monitoring
Monitor web application performance by automating repetitive actions and analyzing load times, response times, or element visibility. SeleniumBase can help identify bottlenecks or performance regressions.

Example: Automating the navigation through critical workflows and measuring load times for key pages.
Key Features Used: Customizable wait times, JavaScript execution, and detailed logs.
4. Visual Testing
Automate visual testing by capturing screenshots of web pages or individual elements to compare against baselines. SeleniumBase also supports annotated screenshots for better debugging and documentation.

Example: Verifying UI consistency across browsers and screen resolutions.
Key Features Used: SeleniumBase screenshot capturing, text overlays, and folder management for test assets.
For production-scale needs, consider a dedicated Screenshot API. See our screenshot API comparison for provider options.

By understanding these use cases, you can unlock the full potential of SeleniumBase to streamline testing, automate workflows, and solve complex challenges efficiently.

SeleniumBase Features
What sets SeleniumBase apart are the built-in tools and utilities that eliminate the need for external dependencies or custom scripts. Let’s break them down:

Feature	Description
Simplified Syntax	Reduces boilerplate code with cleaner, more intuitive commands.
Screenshots	Automate visual testing with a single command to capture webpage screenshots.
SeleniumBase Cloudflare Handling	Overcome anti-bot protections effortlessly while scraping protected sites.
Proxy Support	Seamlessly configure SeleniumBase proxy for advanced scraping scenarios.
Enhanced Element Locators	Use seleniumbase find element methods for more reliable interactions.
Cross-Browser Compatibility	Supports Chrome, Firefox, Edge, and Safari with minimal configuration.
Options for Testing	Includes integrated testing utilities, customizable options, and reports.
These features significantly reduce development time while boosting the reliability of your scripts.

Scrapfly
Need a cloud browser for scraping?
Run headless browsers at scale with Scrapfly Cloud Browser — no infrastructure to manage.

Try Free →
SeleniumBase Examples
SeleniumBase provides a streamlined way to automate tasks, making it easy to create complex workflows with minimal code.

Using SeleniumBase for Testing
SeleniumBase integrates seamlessly with testing frameworks like pytest, offering tools such as assertions, reports, and headless browsing.

This example demonstrates a full test for an e-commerce website from official github example

python
from seleniumbase import BaseCase

BaseCase.main(__name__, __file__)

class MyTestClass(BaseCase):
    def test_swag_labs(self):
        # Open the website
        self.open("https://www.saucedemo.com")

        # Log in
        self.type("#user-name", "standard_user")
        self.type("#password", "secret_sauce\n")

        # Verify inventory page
        self.assert_element("div.inventory_list")
        self.assert_exact_text("Products", "span.title")

        # Add a product to the cart
        self.click('button[name*="backpack"]')
        self.click("#shopping_cart_container a")

        # Verify cart page
        self.assert_exact_text("Your Cart", "span.title")
        self.assert_text("Backpack", "div.cart_item")

        # Proceed to checkout
        self.click("button#checkout")
        self.type("#first-name", "SeleniumBase")
        self.type("#last-name", "Automation")
        self.type("#postal-code", "77123")
        self.click("input#continue")

        # Verify checkout overview
        self.assert_text("Checkout: Overview")
        self.assert_text("Backpack", "div.cart_item")
        self.assert_text("29.99", "div.inventory_item_price")

        # Complete the order
        self.click("button#finish")
        self.assert_exact_text("Thank you for your order!", "h2")
        self.assert_element('img[alt="Pony Express"]')

        # Log out
        self.js_click("a#logout_sidebar_link")
        self.assert_element("div#login_button_container")
Output
Here’s how the script executes in real-time:

With SeleniumBase, even complex workflows like e-commerce testing become straightforward and manageable.

Using SeleniumBase for Scraping
Web scraping often involves challenges like dynamic content rendering, bot detection mechanisms, and IP-based restrictions. SeleniumBase simplifies these tasks with features designed to handle such complexities, including undetected ChromeDriver mode and proxy integration.

Basic Scraping Example
The following example demonstrates how to scrape data from a product page using SeleniumBase. This basic script extracts the title, description, price, and variants of a product, and saves the data as a JSON file.

python
import json
from seleniumbase import BaseCase

class ScrapeProductPage(BaseCase):
    def test_scrape_product(self):
        # Open the product page
        self.open("https://web-scraping.dev/product/1")

        # Extract product title
        product_title = self.get_text("h3")

        # Extract description
        description = self.get_text(".product-description")

        # Extract price
        price = self.get_text("span.product-price")

        # # Extract variants
        variant_elements = self.find_elements("a.variant")
        variants = [variant.text for variant in variant_elements]

        # Combine all data into a dictionary
        product_data = {
            "title": product_title,
            "description": description,
            "price": price,
            "variants": variants,
        }

        # Convert the dictionary to JSON and print
        product_json = json.dumps(product_data, indent=4)
        print(product_json)

        # Save JSON to a file
        with open("product_data.json", "w") as file:
            file.write(product_json)
This example is straightforward and works well for websites with minimal anti-bot measures or static content.

Enhancing Scraping with Undetected ChromeDriver Mode
Some websites detect traditional ChromeDriver usage and block automated interactions. SeleniumBase supports undetected ChromeDriver mode, which allows your scraping tasks to appear as legitimate browser sessions.

Now, that we know what failure looks like let's bypass this challenge using the Undetected ChromeDriver:

python
import undetected_chromedriver as uc
import time

# Add the driver options
options = uc.ChromeOptions()
options.headless = False

# Configure the undetected_chromedriver options
driver = uc.Chrome(options=options)

with driver:
    # Go to the target website
    driver.get("https://nowsecure.nl/")
# Wait for security check
time.sleep(4)

# Take a screenshot
driver.save_screenshot('screenshot.png')
# Close the browsers
driver.quit()
We initialize an undetected_chromedriver object, go to the target website and take a screenshot. Here is the screenshot we got:

Driver passing Cloudflare detection
You can learn more about Undetected ChromeDrive in our dedicated article:


Web Scraping Without Blocking With Undetected ChromeDriver
In this tutorial we'll be taking a look at a new popular web scraping tool Undetected ChromeDriver which is a Selenium extension that allows to bypass many scraper blocking techniques.
How to Add Proxies to Undetected ChromeDriver?
Proxies are essential for avoiding IP blocking while scraping by splitting the traffic between multiple IP addresses. Here is how you can add proxies to the Undetected ChromeDriver:

python
import undetected_chromedriver as uc

# Add the driver options
options = uc.ChromeOptions()
options.headless = False
# For proxies without authentication
options.add_argument(f'--proxy-server=https://proxy_ip:port')
# For proxies with authentication
options.add_argument(f'--proxy-server=https://proxy_username:proxy_password@proxy_ip:proxy_port')
# Configure that driver options
driver = uc.Chrome(options=options)
Although you can add proxies to the undetected chrome driver, there is no direct implementation for proxy rotation.


How to Rotate Proxies in Web Scraping
In this article we explore proxy rotation. How does it affect web scraping success and blocking rates and how can we smartly distribute our traffic through a pool of proxies for the best results.
With these advanced features like undetected ChromeDriver and proxy integration, SeleniumBase enables scalable, efficient, and secure scraping for a wide range of use cases.
Using SeleniumBase for Screenshot Capture
Visual debugging, documentation, and error handling often require capturing precise screenshots during automation runs. SeleniumBase offers robust tools for saving images, including elements, sections of pages, and entire web pages, with optional text overlays.

Here’s a detailed example from SeleniumBase’s official documentation that highlights its powerful image-saving capabilities.

python
import os
from seleniumbase import BaseCase

BaseCase.main(__name__, __file__)

class ImageTests(BaseCase):
    def test_save_element_as_image(self):
        self.open("https://xkcd.com/1117/")
        selector = "#comic"
        folder = "images_exported"
        file_name = "comic.png"
        self.save_element_as_image_file(selector, file_name, folder)
        print(f'Image saved at: {os.path.join(folder, file_name)}')

    def test_add_text_overlay(self):
        self.open("https://xkcd.com/1117/")
        selector = "#comic"
        folder = "images_exported"
        file_name = "image_with_overlay.png"
        overlay_text = "This is an XKCD comic!"
        self.save_element_as_image_file(selector, file_name, folder, overlay_text)
        print(f'Annotated image saved at: {os.path.join(folder, file_name)}')
This example demonstrates how SeleniumBase simplifies screenshot capture, allowing users to save specific elements or entire pages with ease. Additionally, the ability to add text overlays enhances the utility of screenshots for debugging, documentation, and reporting purposes.

Power-Up with Scrapfly
scrapfly middleware
ScrapFly provides web scraping, screenshot, and extraction APIs for data collection at scale.

Anti-bot protection bypass - scrape web pages without blocking!
Rotating residential proxies - prevent IP address and geographic blocks.
JavaScript rendering - scrape dynamic web pages through cloud browsers.
Full browser automation - control browsers to scroll, input and click on objects.
Format conversion - scrape as HTML, JSON, Text, or Markdown.
Full screenshot customization - scroll and capture exact areas.
Comprehensive options - block banners, use dark mode, and more.
LLM prompts - extract data or ask questions using LLMs
Extraction models - automatically find objects like products, articles, jobs, and more.
Extraction templates - extract data using your own specification.
Python and Typescript SDKs, as well as Scrapy and no-code tool integrations.
FAQ
