"""Offline tests for eval/cite_audit.py: the DNS-outage guards and the ledger-cache rule (2026-09-11, progress #68)."""
import io, json, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval"))
import cite_audit  # noqa: E402


def fake_chain(status, fab=None, text=""):
    def run_chain(url, opts):
        return {"status": status, "fetch_method": "none" if status != "ok" else "raw-http",
                "http_status": 200 if status == "ok" else None, "fabrication_check": fab, "_text": text}
    return run_chain


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "raw").mkdir()
        (self.tmp / "raw" / "1.txt").write_text("The agency is an independent agency of the government and insures deposits up to a limit per depositor.")
        (self.tmp / "sources.json").write_text(json.dumps({"sources": [
            {"n": 1, "url": "https://a.example/page", "status": "ok", "text_path": "raw/1.txt"},
            {"n": 2, "url": "https://b.example/gone", "status": "unfetchable", "text_path": None}]}))
        (self.tmp / "report.md").write_text(
            "# R\n\nIntro sentence without a citation.\n\nThe agency is an independent agency of the government and insures deposits up to a limit per depositor [1].\n"
            "Another sentence citing a guessed page [2].\nA third sentence citing a fresh page [3].\n\n"
            "## Sources\n[1] https://a.example/page\n[2] https://b.example/gone\n[3] https://c.example/new\n")
        self._chain, self._canary = cite_audit.fetch.run_chain, cite_audit.dns_canary

    def tearDown(self):
        cite_audit.fetch.run_chain, cite_audit.dns_canary = self._chain, self._canary

    def run_audit(self, *args):
        out = self.tmp / "cite.json"
        sys.argv = ["cite_audit.py", str(self.tmp / "report.md"), "--out", str(out), *args]
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cite_audit.main()
        return code, (json.loads(out.read_text()) if out.exists() else None), buf.getvalue()

    def test_ledger_cached_url_is_never_fabricated(self):
        cite_audit.dns_canary = lambda hosts=None: True
        cite_audit.fetch.run_chain = fake_chain("possibly-fabricated", "dns-failure")
        # only 3 URLs: below the mass-failure minimum, so the guard stays off and the cache rule is what is tested
        code, js, _ = self.run_audit()
        self.assertEqual(code, 0)
        self.assertEqual(js["per_url"]["https://a.example/page"]["status"], "cached-unreachable")
        self.assertEqual(js["cached_unreachable"], 1)
        self.assertEqual(js["fabricated"], 2)          # the guessed page and the fresh page, not the cached one
        self.assertEqual(js["contained"], 1)           # containment ran on the cached text
        self.assertEqual(js["url_valid"], 0)           # live validity keeps its meaning

    def test_no_ledger_flag_disables_cache(self):
        cite_audit.dns_canary = lambda hosts=None: True
        cite_audit.fetch.run_chain = fake_chain("possibly-fabricated", "dns-failure")
        code, js, _ = self.run_audit("--no-ledger")
        self.assertEqual(js["fabricated"], 3)
        self.assertIsNone(js["ledger"])

    def test_mass_dns_failure_withholds_fabricated_and_exits_3(self):
        cite_audit.dns_canary = lambda hosts=None: True
        cite_audit.MASS_FAILURE_MIN = 2
        try:
            cite_audit.fetch.run_chain = fake_chain("possibly-fabricated", "dns-failure")
            code, js, _ = self.run_audit("--no-ledger")
        finally:
            cite_audit.MASS_FAILURE_MIN = 5
        self.assertEqual(code, 3)
        self.assertTrue(js["network_failure"])
        self.assertIsNone(js["fabricated_rate"])

    def test_dns_canary_failure_exits_3_without_fetching(self):
        cite_audit.dns_canary = lambda hosts=None: False
        cite_audit.fetch.run_chain = lambda u, o: (_ for _ in ()).throw(AssertionError("must not fetch"))
        code, js, out = self.run_audit()
        self.assertEqual(code, 3)
        self.assertIsNone(js)
        self.assertIn("dns canary failed", out)

    def test_live_ok_is_unchanged(self):
        cite_audit.dns_canary = lambda hosts=None: True
        cite_audit.fetch.run_chain = fake_chain("ok", None, "insures deposits up to a limit per depositor")
        code, js, _ = self.run_audit()
        self.assertEqual(code, 0)
        self.assertEqual(js["url_valid"], 3)
        self.assertEqual(js["fabricated"], 0)
        self.assertFalse(js["network_failure"])


if __name__ == "__main__":
    unittest.main()
