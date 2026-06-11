Python Selenium: Bot Detection Prevention Techniques
Abdul Wajid
Abdul Wajid

Follow
3 min read
·
May 25, 2025





🚀 In today’s automation-driven world, everyone wants to build bots, but websites are getting smarter at spotting them.

Press enter or click to view image in full size

Python Web Scraping: Practical Ways to Bypass Anti-Bot Protection (Proxy Rotation, CAPTCHA Services)
#
python
#
webscraping
#
proxyrotation
#
captchaservice
 

Scrapers hit tripwires sooner or later. Sites rate-limit IPs, drop tricky CAPTCHAs, or stack other checks. Here’s how to set up Python scraping that keeps moving when defenses kick in.

In real projects you don’t get a dozen silver bullets. Without heavy custom R&D, two routes cover most needs. Rotate proxies to spread traffic. Send CAPTCHAs to services like 2Captcha or SolveCaptcha for tokens or text answers.

 

Web Page Scraping and Blocks: Quick Context
Scraping means programmatic collection of site data. In Python you usually reach for requests to talk HTTP and a parser like BeautifulSoup to read HTML. That works until the target guards the door.

Two headaches pop up most often.
IP blocking. Flood one address and the server might throw 429 Too Many Requests, or shove you onto a check page.
CAPTCHA. The site asks you to prove you’re human, from a simple checkbox to image puzzles.

You might also see empty payloads. The script runs, nothing meaningful lands, and you wonder where it went. Let’s cut through what prevents that.

Proxy Rotation for Scraping
Why proxies matter
High-throughput scraping from one IP screams automation. Blocks follow. A pool of proxies lets you change source IP per request so filters back off. At scale, skipping proxies looks sloppy.

 

What to pick
Free lists exist, sure, but they break, lag, or come pre-flagged. You can find a gem, though it takes hustle and local knowledge. Paid options fit serious runs. Datacenter for speed and price. Residential or mobile when you need more stealth and region variety.

Python wiring

requests supports proxy dicts out of the box. To rotate, cycle a list. Clean and simple.

import requests
import itertools

# Rotating set: http/https/socks5 supported, auth optional
PROXIES = [
    {"http": "http://111.222.333.444:8080", "https": "http://111.222.333.444:8080"},
    {"http": "http://user:pass@555.666.777.888:3128", "https": "http://user:pass@555.666.777.888:3128"},
    # {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"},
]

proxy_iter = itertools.cycle(PROXIES)
test_url = "http://httpbin.org/ip"

for idx in range(3):
    prx = next(proxy_iter)
    try:
        r = requests.get(test_url, proxies=prx, timeout=(5, 10))
        print(f"Request {idx + 1} via {prx['http']} -> {r.json()}")
    except requests.RequestException as exc:
        print(f"Request {idx + 1} via {prx['http']} failed: {exc}")
You’ll prune dead proxies quickly. Some drop. Some get banned. Most teams add health checks or pay for automatic rotation. Proxies cut CAPTCHA frequency, especially on reCAPTCHA, though stubborn sites still challenge you at low rates.

CAPTCHA Types and Why They Bite
 

Classic text CAPTCHA
Distorted letters or digits inside an image. OCR can read toy samples. Real noise and warping wreck naive OCR.

Google reCAPTCHA v2
The well-known box. Sometimes a checkbox that checks behavior, sometimes an image grid, sometimes invisible with behavioral triggers only.

Google reCAPTCHA v3
No puzzle on screen. The script assigns a hidden score from 0.0 to 1.0 based on activity. Low score means challenge or denial. You don’t “solve” it in the usual way. You present a token with an acceptable score.

hCaptcha and FunCaptcha (Arkose Labs)
hCaptcha serves object-finding tasks and shows up on Cloudflare and others. FunCaptcha uses micro-interactions like rotate or assemble gizmos. Both change tactics often.

Other stuff
GeeTest sliders, image permutations, audio prompts, math, one-off vendor puzzles. No one-size-fits-all trick. You tailor per family.

How People Actually Bypass CAPTCHA
You have two playbooks.

1) Prevent it from showing up
Tune the scraper for human-like behavior. Slow down. Spread requests across IPs. Rotate User-Agent to mimic real browsers. Randomize delays. Avoid the same click or URL paths. Respect robots.txt. Reuse cookies so you look like one person, not a parade of strangers. This often keeps gates open. We think this saves more budget than anything.

2) Solve it when it pops
When a page throws a challenge, send it to a specialized service. The service returns a token or the answer text. Most providers combine AI with human backup. Quick ones go through models in seconds. Tough ones reach human workers and still finish within a workable window.

 

2Captcha leans on a global crowd to deliver consistent results for a fee per solve. SolveCaptcha uses a hybrid flow. AI answers light tasks in 2–5 seconds. If detection spikes or confidence drops, humans step in. You cover nearly every common CAPTCHA with this, at the cost of a few seconds and small spend per attempt.

Plan for that. Every solve adds latency and minor cost. Avoid challenges when you can, solve when you must.

Solving Classic Text CAPTCHAs
The problem
You get an image with scrambled glyphs and need clean text.

Approach
You can try Tesseract through pytesseract. It wins with clean fonts but falls apart on gnarly sets unless you train a serious model. Send it to 2Captcha or SolveCaptcha instead. Both accept files or base64 and return text.

Install

pip install 2captcha-python solvecaptcha-python
2Captcha example

from twocaptcha import TwoCaptcha

client = TwoCaptcha('YOUR_2CAPTCHA_API_KEY')
out = client.normal('captcha.jpg')
print("Recognized text:", out['code'])
If the image lives behind dynamic markup, grab it with Selenium, crop the element, then send base64. Same end result.

SolveCaptcha example

from solvecaptcha import SolveCaptcha

cli = SolveCaptcha('YOUR_SOLVECAPTCHA_API_KEY')
res = cli.image('captcha.jpg')
print("Recognized text:", res['code'])
Set a sensible timeout at init. If the window expires you get an error. Retry logic helps in bursts.

Beating reCAPTCHA v2
The setup
The page embeds a widget that yields g-recaptcha-response after success. You need that token.

How services handle it
You pull the sitekeyfrom the page, usually inside a g-recaptcha element or iframe URL. Send your API key, the target URL, and that sitekey to the provider. They reply with a task ID, then a token a few seconds later. You place that token into the hidden field or through JS and submit.

2Captcha

from twocaptcha import TwoCaptcha

solver = TwoCaptcha('YOUR_2CAPTCHA_API_KEY')
ans = solver.recaptcha(sitekey="SITE_KEY_FROM_PAGE", url="https://target.site/page")
token = ans['code']
print("reCAPTCHA token:", token)
Under the hood the library posts a job then polls for completion with that job ID. Same rhythm if you call the HTTP API directly.

About proxies and IP consistency
Google often checks the IP context. If your HTTP request hits the site from a German proxy but the solve came from a worker somewhere else, the site may reject the token. Providers let you pass a proxy so the solve originates from the right region and IP class.

from twocaptcha import TwoCaptcha

solver = TwoCaptcha(
    'YOUR_2CAPTCHA_API_KEY',
    defaultTimeout=120,
    proxy={
        'type': 'HTTPS',
        'uri': 'login:password@123.45.67.89:3128'
    }
)
resp = solver.recaptcha(sitekey="...", url="https://target.site/page")
Finalizing
With requests, include g-recaptcha-response=TOKEN in your POST body. With Selenium, write the token into #g-recaptcha-response and trigger the form submit or the site’s callback.

reCAPTCHA v3 and Cloudflare Turnstile
reCAPTCHA v3
No visual puzzle. You request a token that carries a score. 2Captcha supports this. You pass sitekey, pageurl, version=3, and a minimum score like 0.3 or 0.7. Submit the token the same way as v2. If the site demands 0.9 and your token doesn’t meet it, you might need better behavior signals or a more realistic browser profile. Honestly, sometimes you just tighten the traffic pattern.

 

Turnstile
Cloudflare’s alternative with extra checks. The page expects a cf-turnstile-response token. Both 2Captcha and SolveCaptcha return those. You send site key and page URL. Average solve time sits around seconds territory according to our analysts and field logs. Inject the token and finish the form or AJAX call.

hCaptcha and FunCaptcha
hCaptcha
Looks like reCAPTCHA but runs on a different backend. You supply sitekey and pageurl. Many sites require IP match between solve and request. Proxyless can work on some installs, not all. Safer path uses the same proxy you use for page traffic.

 

from twocaptcha import TwoCaptcha

s = TwoCaptcha('YOUR_2CAPTCHA_API_KEY')
r = s.hcaptcha(sitekey="SITEKEY_HCAPTCHA", url="https://target.site/page")
token = r['code']
Place it into h-captcha-response then submit.

FunCaptcha (Arkose Labs)
These puzzles need real interaction in the browser. Services still solve them. You pass public_key, often an svc_url, and sometimes a blob captured from the page. 2Captcha exposes funcaptcha for this path. SolveCaptcha supports Arkose too. Arkose checks IP carefully. Residential proxies tend to work better. The response usually contains a token and sometimes a session pair. You wire both where the site expects them.

Image Selection, Coordinate Clicks, Sliders, GeeTest
Some puzzles ask you to click objects or drag sliders. You can build a computer vision workflow or let a provider return coordinates or a finished token set.

Clicks
Send the image, ask for n clicks. The service responds with x,y pairs. You replay them with Selenium.

 

GeeTest
Typical flow returns values like validate and challenge along with other fields. You insert them into JS hooks or hidden inputs, then continue the site’s verification chain. Both 2Captcha and SolveCaptcha support this pattern.

Vendor CAPTCHAs from Yandex, VK, and others also show up. Most land within these same service APIs.

Helpful Python Libraries for Solving
2captcha-python
Official 2Captcha client. Covers major CAPTCHA families, proxy settings, async modes, and stays current.

solvecaptcha-python
SolveCaptcha’s client. Works with reCAPTCHA, hCaptcha, FunCaptcha, Turnstile, GeeTest, and more. Syntax stays close to 2Captcha so swapping feels easy.

captcha_solver (RuCaptcha)
Client for RuCaptcha and 2Captcha.

2captcha-solver
Third-party with focus on reCAPTCHA v2 v3, hCaptcha, FunCaptcha. Has async variants for high concurrency.

captchatools
Multi-provider wrapper. You can set a primary and a fallback. If balance runs out or latency spikes, it switches. Supports proxies and async. According to our data, teams like the failover a lot.

twocaptcha-extension-python
Glue for Selenium or Playwright so you solve in the browser context without extensions. Handy when your automation lives inside a real browser.




