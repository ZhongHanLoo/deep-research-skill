#!/usr/bin/env python3
"""Offline unit tests for ledger.py using a stub fetch script. Run: python3 tests/test_ledger.py"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

S = Path(__file__).resolve().parent.parent / "scripts"
STUB = '''import sys, json, argparse
p=argparse.ArgumentParser(); p.add_argument("url"); p.add_argument("--out"); p.add_argument("--id"); p.add_argument("--json",action="store_true"); p.add_argument("--ignore-robots",action="store_true"); p.add_argument("--fresh",action="store_true")
a=p.parse_args()
text="Page about "+a.url+". The global market reached USD 4.2 billion in 2024, according to the report. Another sentence. A third sentence about growth. A fourth sentence about risk. A fifth sentence about regulation. A sixth sentence about history."
open(a.out,"w").write(text)
print(json.dumps({"url":a.url,"final_url":a.url,"title":"T","status":"ok","fetch_method":"raw-http","http_status":200,"content_type":"text/html","accessed":"2026-09-03T00:00:00Z","snapshot_date":None,"extracted_chars":len(text),"gate":"passed","robots":"allowed","evidence_strength":"primary","quote_safe":True,"published":None,"publisher":"x","attempts":[],"text_path":"raw/%s.txt"%a.id,"fabrication_check":None}))
'''


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.stub = self.d / "stub_fetch.py"
        self.stub.write_text(STUB)
        self.env = dict(os.environ, DEEP_RESEARCH_FETCH=str(self.stub))
        self.run = self.d / "run"
        self.L(["init", "--question", "What is the market size?", "--preset", "quick"], run=str(self.run))

    def L(self, args, run=None, env=None):
        p = subprocess.run([sys.executable, str(S / "ledger.py"), "--run", run or str(self.run), *args], capture_output=True, text=True, env=env or self.env)
        return p.returncode, p.stdout, p.stderr

    def add(self, source, text, quote, imp, env=None):
        return self.L(["claim", "add", "--source", str(source), "--angle", "a", "--text", text, "--quote", quote, "--importance", imp], env=env)

    def test_dedup_and_quote_check(self):
        self.L(["add-url", "https://www.Example.com/a/?utm_source=x", "--angle", "m"])
        code, out, _ = self.L(["add-url", "https://example.com/a", "--angle", "m"])
        self.assertIn('"duplicate": true', out)
        code, _, err = self.add(1, "bad", "not there at all", "central")
        self.assertEqual(code, 3)
        self.assertIn("nearest", err)
        code, out, _ = self.add(1, "ok", "reached USD 4.2 billion in 2024", "central")
        self.assertEqual(code, 0)

    def test_central_cap(self):
        self.L(["add-url", "https://example.com/a", "--angle", "m"])
        quotes = ["reached USD 4.2 billion in 2024", "Another sentence", "A third sentence about growth", "A fourth sentence about risk", "A fifth sentence about regulation", "A sixth sentence about history"]
        for i, q in enumerate(quotes):
            code, out, _ = self.add(1, f"fact {i}", q, "central")
            self.assertEqual(code, 0)
        claims = json.loads((self.run / "claims.json").read_text())["claims"]
        self.assertEqual(sum(1 for c in claims if c["importance"] == "central"), 4)
        self.assertEqual(sum(1 for c in claims if c["importance"] == "supporting"), 2)
        self.assertTrue(any("importance-capped" in n for c in claims for n in c["notes"]))
        # cap disabled via env
        env = dict(self.env, DEEP_RESEARCH_CENTRAL_CAP="0")
        code, out, _ = self.add(1, "fact 7", "Page about", "central", env=env)
        claims = json.loads((self.run / "claims.json").read_text())["claims"]
        self.assertEqual(sum(1 for c in claims if c["importance"] == "central"), 5)

    def test_independence_and_labels(self):
        for u in ["https://example.com/a", "https://sub.example.com/b", "https://news.bbc.co.uk/c", "https://datatracker.ietf.org/doc/html/rfc9111", "https://www.rfc-editor.org/rfc/rfc9111"]:
            self.L(["add-url", u, "--angle", "m"])
        self.add(1, "t", "reached USD 4.2 billion in 2024", "central")
        self.L(["claim", "evidence", "c001", "--supports", "2", "--note", "same domain", "--by", "v"])
        c = json.loads(self.L(["claims", "list"])[1])[0]
        self.assertEqual(c["label"], "single-source")
        self.L(["claim", "evidence", "c001", "--supports", "3", "--note", "bbc", "--by", "v"])
        self.assertEqual(json.loads(self.L(["claims", "list"])[1])[0]["label"], "corroborated")
        self.add(4, "rfc fact", "reached USD 4.2 billion in 2024", "central")
        self.L(["claim", "evidence", "c002", "--supports", "5", "--note", "mirror", "--by", "v"])
        self.assertEqual(json.loads(self.L(["claims", "list"])[1])[1]["label"], "single-source")  # mirror of same RFC
        self.L(["claim", "evidence", "c002", "--contradicts", "3", "--note", "x", "--by", "v"])
        self.assertEqual(json.loads(self.L(["claims", "list"])[1])[1]["label"], "contradicted")


if __name__ == "__main__":
    unittest.main()
