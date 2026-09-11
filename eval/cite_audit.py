#!/usr/bin/env python3
"""Model-free citation audit for a report that has no ledger (baseline workflow A).

  cite_audit.py REPORT.md [--out cite.json] [--timeout 15] [--ledger RUN | --no-ledger]

Parses every URL cited in the Markdown (inline links, bare URLs, numbered
reference lists), fetches each through the skill's keyless chain
(skill/deep-research/scripts/fetch.py), and for every sentence that cites a
URL tests whether an 8-word shingle of that sentence (or a quoted span inside
it) appears in the fetched text. Reports URL-valid rate, fabricated/dead rate,
and quote-containment rate, matching evaluation-survey.md protocol step 5.
Same checks the skill applies to itself via cite_check.py, so both workflows
are measured with one yardstick.

Two guards added 2026-09-11 after a background audit returned 32 of 64 URLs as
"possibly-fabricated" during a DNS outage (progress #67): a DNS canary before
any fetch and a mass-failure guard after it (exit 3, `network_failure: true`,
fabricated rate withheld). And when the report sits in a skill run folder (or
`--ledger RUN` is given), a URL the run fetched live (`sources.json` status ok
with a raw text file) is never counted fabricated: if it is unreachable now it
is reported as `cached-unreachable`, its cached text is used for containment,
and `url_valid_rate` keeps its live meaning (resolves now) so the A side, which
has no ledger, is measured the same way.
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

URL_RE = re.compile(r"https?://[^\s<>\"'\]]+")

CANARY_HOSTS = ("example.com", "web.archive.org", "www.rfc-editor.org")
MASS_FAILURE_SHARE = 0.5
MASS_FAILURE_MIN = 5


def dns_canary(hosts=CANARY_HOSTS) -> bool:
    """True if at least one well-known host resolves; False means the machine has no DNS."""
    import socket
    for h in hosts:
        try:
            socket.gethostbyname(h)
            return True
        except OSError:
            continue
    return False


def load_ledger(run: Path | None) -> dict[str, dict]:
    """url -> {status, text} for sources the run fetched live (status ok, raw text on disk)."""
    if run is None or not (run / "sources.json").exists():
        return {}
    data = json.loads((run / "sources.json").read_text(encoding="utf-8"))
    srcs = data.get("sources", data) if isinstance(data, dict) else data
    if isinstance(srcs, dict):
        srcs = list(srcs.values())
    out: dict[str, dict] = {}
    for rec in srcs:
        if rec.get("status") != "ok" or not rec.get("text_path"):
            continue
        tp = run / rec["text_path"]
        if not tp.exists():
            continue
        text = tp.read_text(encoding="utf-8", errors="replace")
        for u in {rec.get("url"), rec.get("canonical_url"), rec.get("final_url")}:
            if u:
                out[clean_url(u)] = {"status": "ok", "text": text, "n": rec.get("n")}
    return out


def classify(rec: dict, cached: dict | None) -> dict:
    """Merge a live fetch record with the ledger's cached fetch of the same URL."""
    page = {"status": rec["status"], "method": rec["fetch_method"], "http_status": rec.get("http_status"),
            "fabrication_check": rec.get("fabrication_check"), "text": rec.pop("_text", "") or "", "cached": bool(cached)}
    if cached and page["status"] != "ok":
        # fetched live during the run: cannot be fabricated, and its text is on disk
        page["status"] = "cached-unreachable"
        page["text"] = cached["text"]
    return page


def mass_failure(pages: dict[str, dict]) -> bool:
    dns = sum(1 for p in pages.values() if p["fabrication_check"] == "dns-failure" and p["status"] == "possibly-fabricated")
    return dns >= MASS_FAILURE_MIN and dns / max(len(pages), 1) >= MASS_FAILURE_SHARE


def clean_url(u: str) -> str:
    """Strip trailing punctuation and an unbalanced closing parenthesis (added 2026-09-05:
    Wikipedia titles like Capitulation_of_Alexandria_(1801) were truncated at the ')')."""
    u = u.rstrip(".,;:!?")
    while u.endswith(")") and u.count(")") > u.count("("):
        u = u[:-1]
    return u
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
    ap.add_argument("--ledger", help="skill run folder whose sources.json and raw/ back the report (default: the report's own folder if it has sources.json)")
    ap.add_argument("--no-ledger", action="store_true", help="ignore any ledger next to the report")
    a = ap.parse_args()
    text = Path(a.report).read_text(encoding="utf-8", errors="replace")
    numref = {int(n): clean_url(u) for n, u in NUMREF_RE.findall(text)}
    urls = {clean_url(u) for u in URL_RE.findall(text)} | set(numref.values())
    urls |= {u for _, u in MDLINK_RE.findall(text)}
    # sentence -> cited urls
    citing: list[tuple[str, set[str]]] = []
    for s in sentences(text):
        if s.startswith("#") or re.match(r"^\[?\d+\]?[.:)]?\s+\S*https?://", s) or re.match(r"^\[\d+\]\s", s):
            continue  # headings and reference-list entries are not citing sentences
        cited = {clean_url(u) for u in URL_RE.findall(s)} | {u for _, u in MDLINK_RE.findall(s)}
        cited |= {numref[int(n)] for n in CITE_NUM_RE.findall(s) if int(n) in numref}
        if cited:
            citing.append((s, cited))

    run = None if a.no_ledger else (Path(a.ledger) if a.ledger else Path(a.report).resolve().parent)
    ledger = load_ledger(run)
    if not dns_canary():
        print(json.dumps({"network_failure": True, "reason": "dns canary failed: none of " + ", ".join(CANARY_HOSTS) + " resolves; re-run later"}))
        return 3

    class Opts:
        timeout = a.timeout; max_bytes = 10 * 1024 * 1024; ignore_robots = False; fresh = False; out = None; id = None
    pages: dict[str, dict] = {}
    for u in sorted(urls):
        rec = fetch.run_chain(u, Opts())
        pages[u] = classify(rec, ledger.get(u))
    per_url = {u: {k: v for k, v in p.items() if k != "text"} for u, p in pages.items()}
    valid = sum(1 for p in pages.values() if p["status"] == "ok")
    cached_unreachable = sum(1 for p in pages.values() if p["status"] == "cached-unreachable")
    fabricated = sum(1 for p in pages.values() if p["status"] == "possibly-fabricated")
    failure = mass_failure(pages)
    checked = supported = 0
    details = []
    for s, cited in citing:
        texts = [pages[u]["text"] for u in cited if pages.get(u, {}).get("status") in ("ok", "cached-unreachable")]
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
               "cached_unreachable": cached_unreachable, "ledger": str(run) if ledger else None,
               "fabricated": None if failure else fabricated,
               "fabricated_rate": None if failure else (round(fabricated / len(urls), 3) if urls else None),
               "network_failure": failure,
               "citing_sentences": len(citing), "checked": checked, "contained": supported,
               "quote_containment_rate": round(supported / checked, 3) if checked else None,
               "per_url": per_url, "sentences": details}
    if failure:
        summary["reason"] = "half or more of the URLs failed DNS at once; fabricated counts withheld; re-run later"
    js = json.dumps(summary, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(js, encoding="utf-8")
    print(js if not a.out else json.dumps({k: summary[k] for k in ("urls", "url_valid_rate", "cached_unreachable", "fabricated_rate", "network_failure", "citing_sentences", "quote_containment_rate")}))
    return 3 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
