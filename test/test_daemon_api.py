import json
import unittest
from pathlib import Path
import httpx
import time

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path("test/output-response")


class TestDaemonAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_health_endpoint(self):
        """Test health check endpoint on the running server."""
        try:
            response = httpx.get(f"{BASE_URL}/health")
        except httpx.ConnectError:
            self.fail(f"Could not connect to daemon at {BASE_URL}. Ensure the daemon server is running.")

        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        (OUTPUT_DIR / "health.json").write_text(json.dumps(resp_json, indent=2), encoding="utf-8")
        
        self.assertEqual(
            resp_json,
            {"status": "ok", "message": "WebScroll Daemon is running"}
        )

    def test_job_scrape_submission_and_poll(self):
        """Test submitting a scrape job for Adobe Careers and polling until completion."""
        adobe_url = "https://careers.adobe.com/us/en/c/engineering-and-product-jobs"
        payload = {
            "url": adobe_url,
            "crawl": False,
            "actions": [],
            "max_pages": 1,
            "max_depth": 1
        }
        
        try:
            response = httpx.post(f"{BASE_URL}/job/scrape", json=payload, timeout=10.0)
        except httpx.ConnectError:
            self.fail(f"Could not connect to daemon at {BASE_URL}.")

        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        (OUTPUT_DIR / "job_submission.json").write_text(json.dumps(resp_json, indent=2), encoding="utf-8")

        self.assertIn("job_id", resp_json)
        self.assertEqual(resp_json["status"], "queued")
        job_id = resp_json["job_id"]

        # Poll job status
        completed = False
        for _ in range(360):  # Poll up to 360 seconds (6 minutes) to allow browser fallbacks to finish
            time.sleep(1)
            status_resp = httpx.get(f"{BASE_URL}/job/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            status_json = status_resp.json()
            status = status_json["status"]
            if status in ("done", "failed"):
                completed = True
                (OUTPUT_DIR / "job_result.json").write_text(json.dumps(status_json, indent=2), encoding="utf-8")
                
                # We assert the status is 'done', but if it failed due to system environment issues (e.g. no driver installed), we report that error
                if status == "failed":
                    self.fail(f"Job failed in background execution: {status_json.get('error')}")
                
                self.assertIsNotNone(status_json.get("results"))
                self.assertGreater(len(status_json["results"]), 0)
                self.assertEqual(status_json["results"][0]["url"], adobe_url)
                break
        
        self.assertTrue(completed, "Job did not complete within timeout limit.")

    def test_search_razorpay_career(self):
        """Test submitting a web search query for 'razorpay career'."""
        payload = {
            "query": "razorpay career",
            "mode": "text",
            "top_k": 5,
            "scrape_results": True
        }
        
        try:
            response = httpx.post(f"{BASE_URL}/search", json=payload, timeout=3600.0)
        except httpx.ConnectError:
            self.fail(f"Could not connect to daemon at {BASE_URL}.")

        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        (OUTPUT_DIR / "search_result.json").write_text(json.dumps(resp_json, indent=2), encoding="utf-8")

        self.assertEqual(resp_json["query"], "razorpay career")
        self.assertEqual(resp_json["mode"], "text")
        self.assertGreater(len(resp_json["urls_found"]), 0)


if __name__ == "__main__":
    unittest.main()
