#!/usr/bin/env python3
"""Offline unit tests for cite_check.py (no network). Run: python3 tests/test_cite_check.py"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

S = Path(__file__).resolve().parent.parent / "scripts"


def src(n, url, status="ok", quote_safe=True, strength="primary", method="raw-http"):
    return {"n": n, "url": url, "canonical_url": None, "title": f"T{n}", "publisher": "x", "published": None,
            "accessed": "2026-09-03T00:00:00Z", "angle": "a", "round": 1, "status": status, "fetch_method": method,
            "http_status": 200, "snapshot_date": None, "content_type": "text/html", "extracted_chars": 100, "gate": "passed",
            "robots": "allowed", "evidence_strength": strength, "quote_safe": quote_safe, "grade": None, "health": None,
            "text_path": f"raw/{n}.txt" if status == "ok" else None, "attempts": [], "notes": ""}


def claim(cid, n, quote, contradicts=None):
    return {"id": cid, "text": "t", "quote": quote, "source": n, "angle": "a", "round": 1, "importance": "central",
            "checked": bool(contradicts), "supports": [], "contradicts": contradicts or [], "label": "unverified",
            "quote_verified": None, "notes": [], "created": "2026-09-03T00:00:00Z"}


class CiteCheckTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "raw").mkdir()
        text = ("The global market reached USD 4.2 billion in 2024, according to the annual report published by the association. "
                "Growth was driven by three factors that analysts consider durable over the coming decade.")
        (self.d / "raw" / "1.txt").write_text(text)
        (self.d / "raw" / "2.txt").write_text("Other page. " * 30)
        (self.d / "raw" / "3.txt").write_text("Third page says the market was USD 3 billion. " * 10)
        sources = [src(1, "https://a.com/x"), src(2, "https://b.org/y"), src(3, "https://c.net/z"),
                   src(4, "https://d.com/snippet", status="unfetchable", quote_safe=False, strength="paraphrase-only", method="search-snippet-only")]
        claims = [
            claim("c001", 1, "reached USD 4.2 billion in 2024"),
            claim("c002", 1, "Growth was driven by three factors that analysts consider durable over the coming decade extra"),  # shingle-tolerant
            claim("c003", 1, "the market grew to 4.2 billion dollars last year according to analysts"),  # paraphrase -> fail
            claim("c004", 2, "Other page", contradicts=[{"source": 3, "note": "says 3bn", "by": "v"}]),
        ]
        (self.d / "sources.json").write_text(json.dumps({"next_id": 5, "sources": sources}))
        (self.d / "claims.json").write_text(json.dumps({"next_id": 5, "claims": claims}))
        (self.d / "run.json").write_text(json.dumps({"question": "q", "preset": "quick", "mode": "brief"}))
        (self.d / "report.md").write_text(
            "# R\n\n## Summary\nMarket size [1]. Range cite [2-3]. Multi [1, 3][2]. Unknown [9].\n\n"
            "Paragraph citing [2] without caveat.\n\n"
            "Paragraph citing [2] which is disputed by [3].\n\n"
            "Weak: only a search snippet was available for [4].\n\n"
            "Literal https://example.org/nope here.\n\n"
            "```\nhttps://code.example/ignored [7]\n```\n\n"
            "## Sources\n[1] https://a.com/x\n[2] https://b.org/y\n")

    def run_cc(self, *extra):
        p = subprocess.run([sys.executable, str(S / "cite_check.py"), "--run", str(self.d), "--no-network", "--format", "json", *extra],
                           capture_output=True, text=True)
        return p.returncode, json.loads(p.stdout)

    def test_all(self):
        code, out = self.run_cc()
        kinds = [(p["kind"], p.get("n"), p.get("claim")) for p in out["problems"]]
        self.assertEqual(code, 1)
        self.assertEqual(out["quotes"], {"checked": 4, "verified": 3, "failed": 1, "unknown": 0})
        self.assertIn(("quote-not-in-source", 1, "c003"), kinds)
        self.assertIn(("unknown-citation", 9, None), kinds)
        self.assertNotIn(("unknown-citation", 7, None), kinds)  # inside code fence
        self.assertIn(("url-not-in-registry", None, None), kinds)
        self.assertFalse(any(k == "url-not-in-registry" and "code.example" in p["message"] for (k, _, _), p in zip(kinds, out["problems"])))
        self.assertIn(("contradicted-cited-without-caveat", 2, None), kinds)
        cu = [p for p in out["problems"] if p["kind"] == "cites-unfetchable-source"]
        self.assertEqual(len(cu), 1)
        self.assertEqual(cu[0]["severity"], "warning")  # caveated
        self.assertEqual(out["report"]["distinct_sources_cited"], 5)  # 1,2,3,4,9
        claims = json.loads((self.d / "claims.json").read_text())["claims"]
        by = {c["id"]: c for c in claims}
        self.assertTrue(by["c001"]["quote_verified"] and by["c002"]["quote_verified"])
        self.assertFalse(by["c003"]["quote_verified"])
        self.assertEqual(by["c003"]["label"], "unverified")
        self.assertIn("quote-not-in-source", by["c003"]["notes"])
        self.assertEqual(by["c004"]["label"], "contradicted")
        self.assertTrue((self.d / "sources.md").exists() and (self.d / "verification.md").exists())

    def test_tracing(self):
        (self.d / "report.md").write_text(
            "# R\n\nMarket size is large [1]. <!-- c001 -->\n\n"
            "Cross-cited [1][3]. <!-- c001 -->\n\n"          # [3] not a source of c001 -> error
            "Contradiction noted, disputed by [3]. <!-- c004 -->\n\n"  # c004 contradicts [3] -> allowed
            "Unknown id [1]. <!-- c999 -->\n\n"
            "No marker here [2].\n\n"
            "| # | Finding | Sources |\n|---|---|---|\n| 1 | x | [1] <!-- c001 --> |\n| 2 | y | [2] <!-- c001 --> |\n\n"
            "## Sources\n[1] https://a.com/x\n[2] https://b.org/y\n[3] https://c.net/z\n")
        code, out = self.run_cc()
        kinds = [(p["kind"], p.get("n")) for p in out["problems"]]
        self.assertIn(("citation-not-traced", 3), kinds)
        self.assertIn(("citation-not-traced", 2), kinds)   # table row 2 cites [2] under c001
        self.assertIn(("unknown-claim-id", None), kinds)
        self.assertIn(("citation-without-claim-marker", None), kinds)
        self.assertFalse(any(k == "citation-not-traced" and n == 1 for k, n in kinds))
        t = out["report"]["tracing"]
        self.assertEqual(t["markers"], 6)
        self.assertEqual(t["unmarked_segments"], 1)

    def test_strict(self):
        (self.d / "report.md").write_text("# R\n\nOnly [1] here. <!-- c001 -->\n\n## Sources\n[1] https://a.com/x\n")
        (self.d / "claims.json").write_text(json.dumps({"next_id": 2, "claims": [claim("c001", 1, "reached USD 4.2 billion in 2024")]}))
        code, out = self.run_cc()
        self.assertEqual(code, 0)
        self.assertEqual(out["errors"], 0)


if __name__ == "__main__":
    unittest.main()
