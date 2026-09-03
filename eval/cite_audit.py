#!/usr/bin/env python3
"""Model-free citation audit for a report that has no ledger (baseline workflow A).

  cite_audit.py REPORT.md [--out cite.json] [--timeout 15]

Parses every URL cited in the Markdown (inline links, bare URLs, numbered
reference lists), fetches each through the skill's keyless chain
(skill/deep-research/scripts/fetch.py), and for every sentence that cites a
URL tests whether an 8-word shingle of that sentence (or a quoted span inside
it) appears in the fetched text. Reports URL-valid rate, fabricated/dead rate,
and quote-containment rate, matching evaluation-survey.md protocol step 5.
Same checks the skill applies to itself via cite_check.py, so both workflows
are measured with one yardstick.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "deep-research" / "scripts"))
import fetch  # noqa: E402
import textmatch  # noqa: E402

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
MDLINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
NUMREF_RE = re.compile(r"^\s*\[?(\d+)\]?[.:)]?\s+.*?(https?://\S+)", re.M)
QUOTE_RE = re.compile(r"[\"“]([^\"”]{20,400})[\"”]")
CITE_NUM_RE = re.compile(r"\[(\d+)\]")


def sentences(text: str) -> list[str]:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\[\(“\"])|\n+", text) if s.strip()]


def shingles(sentence: str, n: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", sentence)
    return [" ".join(words[i:i + n]) for i in range(0, max(1, len(words) - n + 1), max(1, n // 2))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--out")
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    text = Path(a.report).read_text(encoding="utf-8", errors="replace")
    numref = {int(n): u.rstrip(".,;)") for n, u in NUMREF_RE.findall(text)}
    urls = {u.rstrip(".,;)") for u in URL_RE.findall(text)} | set(numref.values())
    urls |= {u for _, u in MDLINK_RE.findall(text)}
    # sentence -> cited urls
    citing: list[tuple[str, set[str]]] = []
    for s in sentences(text):
        if s.startswith("#") or re.match(r"^\[?\d+\]?[.:)]?\s+\S*https?://", s) or re.match(r"^\[\d+\]\s", s):
            continue  # headings and reference-list entries are not citing sentences
        cited = {u.rstrip(".,;)") for u in URL_RE.findall(s)} | {u for _, u in MDLINK_RE.findall(s)}
        cited |= {numref[int(n)] for n in CITE_NUM_RE.findall(s) if int(n) in numref}
        if cited:
            citing.append((s, cited))

    class Opts:
        timeout = a.timeout; max_bytes = 10 * 1024 * 1024; ignore_robots = False; fresh = False; out = None; id = None
    pages: dict[str, dict] = {}
    for u in sorted(urls):
        rec = fetch.run_chain(u, Opts())
        pages[u] = {"status": rec["status"], "method": rec["fetch_method"], "http_status": rec.get("http_status"),
                    "fabrication_check": rec.get("fabrication_check"), "text": rec.pop("_text", "") or ""}
    per_url = {u: {k: v for k, v in p.items() if k != "text"} for u, p in pages.items()}
    valid = sum(1 for p in pages.values() if p["status"] == "ok")
    fabricated = sum(1 for p in pages.values() if p["status"] == "possibly-fabricated")
    checked = supported = 0
    details = []
    for s, cited in citing:
        texts = [pages[u]["text"] for u in cited if pages.get(u, {}).get("status") == "ok"]
        if not texts:
            details.append({"sentence": s[:200], "result": "unfetchable"})
            continue
        checked += 1
        quoted = QUOTE_RE.findall(s)
        probes = quoted if quoted else shingles(s)
        ok = any(textmatch.contains(p, t) for p in probes for t in texts)
        supported += ok
        details.append({"sentence": s[:200], "result": "contained" if ok else "not-contained", "probe": "quote" if quoted else "shingle"})
    summary = {"urls": len(urls), "url_valid": valid, "url_valid_rate": round(valid / len(urls), 3) if urls else None,
               "fabricated": fabricated, "fabricated_rate": round(fabricated / len(urls), 3) if urls else None,
               "citing_sentences": len(citing), "checked": checked, "contained": supported,
               "quote_containment_rate": round(supported / checked, 3) if checked else None,
               "per_url": per_url, "sentences": details}
    js = json.dumps(summary, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(js, encoding="utf-8")
    print(js if not a.out else json.dumps({k: summary[k] for k in ("urls", "url_valid_rate", "fabricated_rate", "citing_sentences", "quote_containment_rate")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
