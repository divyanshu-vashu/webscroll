# SKILL.md — web-intel AI Agent Editor Guide

> This file serves as the ground truth for AI agents (Claude, Cursor, Antigravity) to understand the **Stealth Harvester** architecture. Follow these rules strictly to ensure code consistency and maintain modularity.

---

## ⚠️ CRITICAL ENVIRONMENT RULE

**ALWAYS** use the local virtual environment. Before running any script or command, you **MUST** activate:
`C:\Users\Divyanshu\code\tn\webscroll\.venv\Scripts\activate`

---

## 🎯 Project Goal: The Stealth Harvester
**web-intel** is a modular, domain-agnostic web extraction platform. It is strictly a "Harvester" and does **NOT** contain business logic or AI extraction.

- **Input:** A URL or a list of URLs.
- **Process:** Bypass anti-bot systems (Cloudflare, DataDome, etc.), render JavaScript, and clean content.
- **Output:** Two primary files per target: `raw.html` and `clean.txt` (for future AI consumption).

---

## 🏗️ Modular Architecture & Separation of Concerns

The project is split into **Drivers** (Execution) and **Engines** (Intelligence).

### 1. The Execution Stack (Drivers)
Organized into 6 functional layers:
1.  **Browser Clients:** The "Actors" (Playwright, Patchright, Nodriver). Humanization logic lives here.
2.  **Identity:** The "Forgers" (BrowserForge). Generates mathematically consistent profiles.
3.  **HTTP Clients:** TLS/Protocol layer for raw requests (curl_cffi).
4.  **Proxies:** Network routing and authentication.
5.  **Humanization:** Realistic behavior patterns (ghost-cursor, scrolling).
6.  **Sessions:** Persistent context and cookie management.

### 2. The Brains (Engines)
1.  **Strategy Engine:** The "Strategist" (Orchestrator). Selects the best permutation of drivers/profiles.
2.  **Profiler Engine:** Detects anti-bot systems (BotDetector).
3.  **Comparator Engine:** Validates content (ContentValidator) to avoid saving "Access Denied" pages.
4.  **Text Engine:** Converts HTML to clean, visible text (HtmlCleaner).

---

## 📏 Code Modularity & "Shared Lib" Rules

To prevent spaghetti code, follow these strict placement rules:

1.  **No Logic Leakage:**
    *   **The Strategist** (`engines/strategy_engine/`) must **NEVER** handle humanization or set cookies directly. It only passes an `IdentityProfile` to an Actor.
    *   **The Actor** (`drivers/browser_clients/`) handles execution, humanization, and applying the identity.
    *   **The Forger** (`drivers/identity/`) only generates data; it never touches a browser.

2.  **Shared Property Rule:**
    *   If multiple **Browser Clients** (e.g., Playwright and Selenium) need the same utility, create `drivers/lib/`.
    *   If multiple **Engines** need the same logic, create `engines/lib/`.
    *   If a utility is shared **across both Drivers and Engines**, create a top-level `lib/` directory.

3.  **Domain Agnosticism:** Never hardcode business categories (e.g., "Real Estate", "Hiring") in this project. It only knows about URLs and Technical Status.

---

## 💾 Storage & Output Convention

All outputs are saved to `storage/extracted/` using a unique hash/slug of the target URL:

```
storage/extracted/{target_site_hash}/
├── raw.html          # Full source code
├── clean.txt         # Stripped visible text
└── metadata.json     # Technical metadata (timestamp, driver used, status code)
```

---

## 🛡️ The Consistency Rule (Anti-Bot Philosophy)
**Consistency > Stealth Patches.**
Anti-bot systems look for "impossible" identities. Ensure the Browser version, OS, Fonts, GPU, Timezone, and Proxy IP location all match perfectly within a single `IdentityProfile`.

---

## 🚀 Release Phases

- **Phase 1:** Basic Search/Crawl + Engine + Driver (Identity only).
- **Phase 2:** Session Persistence + Humanization + Proxies.
- **Phase 3:** Advanced "Not a Robot" interaction.
- **Phase 4:** High-performance HTTP Clients.
