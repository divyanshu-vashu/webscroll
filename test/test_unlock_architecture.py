import tempfile
import unittest

from engines.strategy_engine.domain_profile_store import DomainProfileStore
from engines.strategy_engine.engine_picker import MIN_SIMILARITY_FOR_HTTP_TRUST, UnlockFirstEnginePicker
from engines.strategy_engine.models import DomainAccessProfile, PaginationConfig, ScrapeRequest
from engines.strategy_engine.orchestrator import StrategyOrchestrator
from engines.strategy_engine.protection_policy import classify_protection
from engines.text_engine.extraction_pipeline import extract_content


class UnlockArchitectureTests(unittest.TestCase):
    def test_detection_ignores_plain_cloudflare_mentions(self):
        detection = {
            "is_blocked": False,
            "page_type": "NORMAL",
            "confidence": 0.05,
            "reasons": ["Article mentions Cloudflare earnings"],
        }
        signal = classify_protection(detection, html="<html><body>Cloudflare earnings beat estimates</body></html>")
        self.assertEqual(signal.kind, "ALLOW")

    def test_detection_flags_interactive_challenge(self):
        detection = {
            "is_blocked": True,
            "page_type": "CLOUDFLARE",
            "confidence": 0.92,
            "reasons": ["CF browser verification element", "CF Turnstile form field"],
        }
        signal = classify_protection(detection, html='<input name="cf-turnstile-response" />')
        self.assertEqual(signal.kind, "INTERACTIVE_CHALLENGE")
        self.assertEqual(signal.vendor, "Cloudflare")

    def test_engine_picker_stays_browser_first_for_unknown_domain(self):
        picker = UnlockFirstEnginePicker()
        decision = picker.decide(
            ScrapeRequest(url="https://example.com"),
            DomainAccessProfile(domain="example.com"),
        )
        self.assertEqual(decision.path, "browser")

    def test_engine_picker_can_trial_http_after_browser_successes(self):
        picker = UnlockFirstEnginePicker()
        profile = DomainAccessProfile(
            domain="example.com",
            browser_success_count=2,
            browser_reference_text="hello world " * 200,
        )
        decision = picker.decide(ScrapeRequest(url="https://example.com"), profile)
        self.assertEqual(decision.path, "http_probe_trial")

    def test_http_probe_evaluation_requires_similarity(self):
        picker = UnlockFirstEnginePicker()
        accepted = picker.evaluate_http_probe(
            probe_text="hello world " * 200,
            reference_text="hello world " * 200,
            is_blocked=False,
            is_js_required=False,
        )
        self.assertTrue(accepted.accepted)
        self.assertGreaterEqual(accepted.similarity or 0.0, MIN_SIMILARITY_FOR_HTTP_TRUST)

    def test_domain_profile_store_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DomainProfileStore(path=f"{tmpdir}/profiles.json")
            store.mark_success(
                domain="example.com",
                driver_name="seleniumbase",
                session_key="example",
                preferred_path="browser",
                reference_text="sample text",
            )
            profile = store.get("example.com")
            self.assertEqual(profile.last_good_driver, "seleniumbase")
            self.assertEqual(profile.browser_success_count, 1)

    def test_extraction_pipeline_removes_nav_and_keeps_product_text(self):
        html = """
        <html>
          <body>
            <nav>Home Products Support</nav>
            <main>
              <h1>Gorenje RB-492</h1>
              <div class="price">$499</div>
              <table><tr><th>Height</th><td>84.5 cm</td></tr></table>
            </main>
            <footer>Footer links</footer>
          </body>
        </html>
        """
        result = extract_content(html, base_url="https://example.com/product/1")
        self.assertIn("Gorenje RB-492", result.clean_text)
        self.assertIn("$499", result.clean_text)
        self.assertNotIn("Footer links", result.clean_text)
        self.assertNotIn("Home Products Support", result.clean_text)

    def test_scrape_request_parses_pagination_config(self):
        request = ScrapeRequest.from_any(
            url="https://example.com/jobs?page=1",
            pagination_mode=True,
            pagination={"type": "url_param", "param": "page", "step": 1, "max_pages": 5},
        )
        self.assertTrue(request.pagination_mode)
        self.assertIsNotNone(request.pagination)
        self.assertEqual(request.pagination.type, "url_param")
        self.assertEqual(request.pagination.param, "page")

    def test_orchestrator_increments_query_param_pagination(self):
        orchestrator = StrategyOrchestrator()
        next_url = orchestrator._next_pagination_url(
            current_url="https://example.com/jobs?page=2",
            pagination=PaginationConfig(type="url_param", param="page", step=1),
        )
        self.assertEqual(next_url, "https://example.com/jobs?page=3")

    def test_orchestrator_increments_offset_limit_pagination(self):
        orchestrator = StrategyOrchestrator()
        next_url = orchestrator._next_pagination_url(
            current_url="https://example.com/jobs?offset=25&limit=25",
            pagination=PaginationConfig(
                type="offset_limit",
                offset_param="offset",
                limit_param="limit",
                limit_value=25,
            ),
        )
        self.assertIn("offset=50", next_url)
        self.assertIn("limit=25", next_url)

    def test_orchestrator_increments_path_pagination(self):
        orchestrator = StrategyOrchestrator()
        next_url = orchestrator._next_pagination_url(
            current_url="https://example.com/jobs/page/3",
            pagination=PaginationConfig(type="url_path", pattern="/page/{page}"),
        )
        self.assertEqual(next_url, "https://example.com/jobs/page/4")

    def test_auto_detects_url_param_pagination(self):
        orchestrator = StrategyOrchestrator()
        detected = orchestrator._detect_pagination_from_url("https://example.com/jobs?page=1")
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "url_param")
        self.assertEqual(detected.param, "page")

    def test_auto_detects_numbered_links_from_page(self):
        orchestrator = StrategyOrchestrator()
        page = type("Page", (), {
            "normalized_html": """
                <nav aria-label="pagination">
                  <a href="/jobs?page=2">2</a>
                  <a href="/jobs?page=3">3</a>
                </nav>
            """,
            "html": "",
            "clean_text": "Jobs page 1",
        })()
        detected = orchestrator._detect_pagination_from_page(
            first_page=page,
            url="https://example.com/jobs?page=1",
            max_pages=10,
        )
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "numbered_links")

    def test_auto_detects_load_more_from_page(self):
        orchestrator = StrategyOrchestrator()
        page = type("Page", (), {
            "normalized_html": '<button data-testid="load-more">Load More</button>',
            "html": "",
            "clean_text": "Jobs page 1",
        })()
        detected = orchestrator._detect_pagination_from_page(
            first_page=page,
            url="https://example.com/jobs",
            max_pages=10,
        )
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "click_append")

    def test_auto_detects_angular_material_next_paginator(self):
        orchestrator = StrategyOrchestrator()
        page = type("Page", (), {
            "html": """
                <mat-paginator class="mat-paginator">
                  <button class="mat-focus-indicator mat-paginator-navigation-previous mat-button-disabled"
                          aria-label="Previous Page of Job Search Results" disabled="true"></button>
                  <button class="mat-focus-indicator mat-paginator-navigation-next"
                          aria-label="Next Page of Job Search Results"></button>
                </mat-paginator>
            """,
            "normalized_html": "",
            "clean_text": "1 - 10 of 319 Items per page",
        })()
        detected = orchestrator._detect_pagination_from_page(
            first_page=page,
            url="https://jobs.zs.com/jobs",
            max_pages=10,
        )
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "url_param")
        self.assertEqual(detected.param, "page")

    def test_auto_detects_rel_next_as_url_pagination(self):
        orchestrator = StrategyOrchestrator()
        page = type("Page", (), {
            "html": """
                <html>
                  <head>
                    <link rel="next" href="https://careers.adobe.com/us/en/c/engineering-and-product-jobs?from=10&amp;s=1">
                  </head>
                  <body>Showing Search results 576</body>
                </html>
            """,
            "normalized_html": "",
            "clean_text": "Showing Search results 576",
        })()
        detected = orchestrator._detect_pagination_from_page(
            first_page=page,
            url="https://careers.adobe.com/us/en/c/engineering-and-product-jobs",
            max_pages=10,
        )
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "url_param")
        self.assertEqual(detected.param, "from")
        self.assertEqual(detected.step, 10)
        self.assertIn("from=10", detected.next_url)

    def test_auto_detects_adobe_offset_page_url_list(self):
        orchestrator = StrategyOrchestrator()
        page = type("Page", (), {
            "html": """
                <ul class="pagination">
                  <li><a aria-label="Page 1" href="https://careers.adobe.com/us/en/c/engineering-and-product-jobs?s=1">1</a></li>
                  <li><a aria-label="Page 2" href="https://careers.adobe.com/us/en/c/engineering-and-product-jobs?from=10&amp;s=1">2</a></li>
                  <li><a aria-label="Page 3" href="https://careers.adobe.com/us/en/c/engineering-and-product-jobs?from=20&amp;s=1">3</a></li>
                </ul>
            """,
            "normalized_html": "",
            "clean_text": "Showing Search results 576",
        })()
        detected = orchestrator._detect_pagination_from_page(
            first_page=page,
            url="https://careers.adobe.com/us/en/c/engineering-and-product-jobs",
            max_pages=10,
        )
        self.assertIsNotNone(detected)
        self.assertEqual(detected.type, "url_list")
        self.assertEqual(len(detected.page_urls), 3)
        self.assertIn("from=10", detected.page_urls[1])

    def test_pagination_mode_uses_auto_even_with_explicit_config(self):
        orchestrator = StrategyOrchestrator()
        request = ScrapeRequest(
            url="https://example.com/jobs",
            pagination_mode=True,
            pagination=PaginationConfig(type="click_append", max_pages=7),
        )
        captured = {}

        def fake_auto(**kwargs):
            captured["pagination"] = kwargs["pagination"]
            return []

        orchestrator._run_auto_pagination = fake_auto
        orchestrator._run_pagination(url=request.url, request=request)
        self.assertEqual(captured["pagination"].type, "auto")
        self.assertEqual(captured["pagination"].max_pages, 7)

    def test_crawl_and_pagination_uses_combined_flow(self):
        orchestrator = StrategyOrchestrator()
        request = ScrapeRequest(
            url="https://example.com/jobs",
            crawl=True,
            pagination_mode=True,
        )
        called = {}

        def fake_combined(**kwargs):
            called["seed_url"] = kwargs["seed_url"]
            return []

        orchestrator._crawl_with_pagination = fake_combined
        orchestrator.run(url=request.url, crawl=True, request=request)
        self.assertEqual(called["seed_url"], "https://example.com/jobs")


if __name__ == "__main__":
    unittest.main()
