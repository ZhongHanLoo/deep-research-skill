#!/usr/bin/env python3
"""Model-free citation pass for a deep-research run (stdlib only).

  cite_check.py --run DIR [--no-network] [--strict] [--format md|json]

1. Quote containment: every claim whose source is quote_safe must have its
   quote in raw/<n>.txt (textmatch rules); failures force the label to
   `unverified` with note `quote-not-in-source`.
2. Citation integrity in report.md: every [n] must exist; no literal URL
   outside the registry; unfetchable / possibly-fabricated sources cited only
   with a caveat; contradicted claims cited with a caveat.
2b. Citation tracing: the writer ends each cited sentence (or table row) with
   an HTML comment naming the claim ids it rests on, e.g. `<!-- c004 c014 -->`.
   Every [n] in that segment must be one of those claims' own source or a
   registered supporting/contradicting source; anything else is an error
   (`citation-not-traced`). Cited segments without a marker are warnings.
3. URL health for every source that is ok or cited: LIVE / DEAD /
   ARCHIVED-ONLY / POSSIBLY-FABRICATED (HEAD -> GET -> Wayback CDX -> DNS).
4. Writes quote_verified, labels, health back through the ledger lock and
   re-renders sources.md and verification.md.
Exit 0 when no error-severity problem remains, else 1 (--strict: warnings too).
Contract: skill/deep-research/reference/contracts.md §7.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch  # noqa: E402
import ledger  # noqa: E402
import textmatch  # noqa: E402

CAVEAT_CONTRADICTED = re.compile(r"contradict|disput|conflict|contested", re.I)
CAVEAT_WEAK = re.compile(r"snippet|could not be fetched|unfetchable|not fetched|search result only|paraphrase|archived snapshot|archive", re.I)
CITE_RE = re.compile(r"\[(\d+(?:\s*[-–]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*)\](?!\()")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
FENCE_RE = re.compile(r"```.*?```", re.S)
MARKER_RE = re.compile(r"<!--\s*((?:c\d{3,}\s*)+)-->")


def expand_cites(group: str) -> list[int]:
    nums = []
    for part in group.split(","):
        part = part.strip()
        m = re.match(r"(\d+)\s*[-–]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b >= a and b - a <= 50:
                nums.extend(range(a, b + 1))
        elif part.isdigit():
            nums.append(int(part))
    return nums


def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_quotes(run: ledger.Run, problems: list) -> dict:
    sources = {s["n"]: s for s in run.sources()["sources"]}
    counts = {"checked": 0, "verified": 0, "failed": 0, "unknown": 0}
    updates: dict[str, tuple] = {}
    for c in run.claims()["claims"]:
        src = sources.get(c["source"])
        if not src or not src.get("quote_safe"):
            counts["unknown"] += 1
            updates[c["id"]] = (None, None)
            continue
        raw = run.raw_text(src)
        if raw is None:
            counts["unknown"] += 1
            updates[c["id"]] = (None, None)
            problems.append({"kind": "raw-text-missing", "severity": "warning", "claim": c["id"], "n": c["source"],
                             "message": f"{c['id']}: {src.get('text_path')} is missing; quote cannot be checked", "hint": "re-fetch the source or accept label unverified"})
            continue
        counts["checked"] += 1
        ok = textmatch.contains(c["quote"], raw)
        if ok:
            counts["verified"] += 1
            updates[c["id"]] = (True, None)
        else:
            counts["failed"] += 1
            near = textmatch.best_window(c["quote"], raw, 240)
            updates[c["id"]] = (False, near)
            problems.append({"kind": "quote-not-in-source", "severity": "error", "claim": c["id"], "n": c["source"],
                             "message": f"{c['id']}: quote not found in {src.get('text_path')}: \"{c['quote'][:120]}\"",
                             "hint": f"nearest passage: \"{near[:240]}\" — re-copy verbatim or drop the claim"})
    with run.lock():
        data = run.claims()
        for c in data["claims"]:
            if c["id"] in updates:
                qv, _ = updates[c["id"]]
                c["quote_verified"] = qv
                if qv is not False and "quote-not-in-source" in c.get("notes", []):
                    c["notes"].remove("quote-not-in-source")
        run.save_claims(data)
    return counts


def check_report(run: ledger.Run, problems: list) -> dict:
    rp = run.path / "report.md"
    stats = {"report": rp.exists(), "citations": 0, "unknown": 0, "cited": [], "tracing": {}}
    if not rp.exists():
        problems.append({"kind": "report-missing", "severity": "warning", "message": "report.md not found; citation checks skipped", "hint": "run the writer first"})
        return stats
    text = FENCE_RE.sub("", rp.read_text(encoding="utf-8", errors="replace"))
    sources = {s["n"]: s for s in run.sources()["sources"]}
    claims = run.claims()["claims"]
    # split off the trailing Sources section
    m = re.search(r"^##\s+Sources\s*$", text, re.M)
    body, tail = (text[:m.start()], text[m.start():]) if m else (text, "")
    cited: set[int] = set()
    for grp in CITE_RE.findall(body):
        for n in expand_cites(grp):
            stats["citations"] += 1
            cited.add(n)
            if n not in sources:
                stats["unknown"] += 1
                problems.append({"kind": "unknown-citation", "severity": "error", "n": n, "message": f"[{n}] is cited but not in sources.json", "hint": "only ledger-assigned numbers may be cited"})
    stats["cited"] = sorted(cited)
    registry = {ledger.normalize_url(s["url"]) for s in sources.values()}
    registry |= {ledger.normalize_url(s["canonical_url"]) for s in sources.values() if s.get("canonical_url")}
    for u in URL_RE.findall(body):
        u = u.rstrip(".,;:")
        if ledger.normalize_url(u) not in registry:
            problems.append({"kind": "url-not-in-registry", "severity": "error", "message": f"literal URL not in the registry: {u}", "hint": "cite by [n]; register the URL with ledger.py add-url first"})
    for line in tail.splitlines():
        for u in URL_RE.findall(line):
            u = u.rstrip(".,;:")
            if ledger.normalize_url(u) not in registry and not re.match(r"^\s*(\|\s*)?\[\d+\]", line):
                problems.append({"kind": "url-not-in-registry", "severity": "error", "message": f"URL in Sources section not in the registry: {u}", "hint": "the Sources section must be copied from sources.md"})
    paras = paragraphs(body)
    for n in sorted(cited):
        s = sources.get(n)
        if not s:
            continue
        paras_n = [p for p in paras if any(n in expand_cites(g) for g in CITE_RE.findall(p))]
        if s.get("status") == "possibly-fabricated":
            problems.append({"kind": "possibly-fabricated-cited", "severity": "error", "n": n, "message": f"[{n}] is possibly fabricated ({s.get('notes','')}) and is cited", "hint": "remove the citation and the claims that depend on it"})
        elif s.get("status") != "ok":
            weak = s.get("evidence_strength") == "paraphrase-only"
            caveated = all(CAVEAT_WEAK.search(p) for p in paras_n) if paras_n else False
            sev = "error" if (weak and not caveated) else "warning"
            problems.append({"kind": "cites-unfetchable-source", "severity": sev, "n": n, "message": f"[{n}] was not fetched ({s.get('status')}, {s.get('evidence_strength')}) but is cited", "hint": "say in the same paragraph that only a search snippet was available, or drop the citation"})
        elif s.get("evidence_strength") == "archived":
            problems.append({"kind": "archived-only", "severity": "info", "n": n, "message": f"[{n}] is an archived copy ({s.get('snapshot_date')})", "hint": "cite as an archived snapshot"})
    stats["tracing"] = check_tracing(body, claims, sources, problems)
    used = set()
    for m in MARKER_RE.finditer(body):
        used.update(m.group(1).split())
    uncited = [c for c in claims if c["importance"] == "central" and c["label"] in ("corroborated", "single-source") and c["id"] not in used]
    stats["uncited_central"] = [c["id"] for c in uncited]
    for c in uncited:
        problems.append({"kind": "central-claim-unused", "severity": "info", "claim": c["id"], "n": c["source"],
                         "message": f"{c['id']} ({c['label']}, [{c['source']}]) is never used: {c['text'][:110]}",
                         "hint": "retrieved but unused evidence is the largest omission class; add it if it answers part of the question, else leave it"})
    contradicted_sources = {c["source"] for c in claims if c["label"] == "contradicted"}
    for n in sorted(contradicted_sources & cited):
        for p in paras:
            if any(n in expand_cites(g) for g in CITE_RE.findall(p)) and not CAVEAT_CONTRADICTED.search(p):
                problems.append({"kind": "contradicted-cited-without-caveat", "severity": "warning", "n": n, "message": f"[{n}] backs a contradicted claim and is cited without 'contradicted/disputed' in the paragraph: \"{p[:80]}…\"", "hint": "state the disagreement where the claim is used, or move it to the disagreements section"})
                break
    return stats


def check_tracing(body: str, claims: list, sources: dict, problems: list) -> dict:
    """Segment each paragraph at claim-id markers and check that the citations in
    a segment are backed by the claims named in the marker that closes it."""
    by_id = {c["id"]: c for c in claims}
    stats = {"markers": 0, "traced": 0, "untraced": 0, "unmarked_segments": 0, "unknown_claim_ids": 0}
    for para in paragraphs(body):
        pos = 0
        for m in MARKER_RE.finditer(para):
            stats["markers"] += 1
            segment = para[pos:m.start()]
            pos = m.end()
            ids = m.group(1).split()
            allowed: set[int] = set()
            for cid in ids:
                c = by_id.get(cid)
                if not c:
                    stats["unknown_claim_ids"] += 1
                    problems.append({"kind": "unknown-claim-id", "severity": "error", "claim": cid,
                                     "message": f"marker names {cid}, which is not in claims.json", "hint": "use ids from the claim list given to the writer"})
                    continue
                allowed.add(c["source"])
                allowed |= {e["source"] for e in c.get("supports", [])} | {e["source"] for e in c.get("contradicts", [])}
            if not allowed:
                continue  # marker had no valid ids; already reported as unknown-claim-id
            for grp in CITE_RE.findall(segment):
                for n in expand_cites(grp):
                    if n not in sources:
                        continue
                    if n in allowed:
                        stats["traced"] += 1
                    else:
                        stats["untraced"] += 1
                        problems.append({"kind": "citation-not-traced", "severity": "error", "n": n, "claim": " ".join(ids),
                                         "message": f"[{n}] is cited in a segment attributed to {' '.join(ids)}, but none of those claims rests on [{n}]",
                                         "hint": f"cite only the sources of the claims the sentence uses, or add the claim that [{n}] supports: \"{segment.strip()[:90]}…\""})
        tail = para[pos:]
        if CITE_RE.search(tail) and not tail.lstrip().startswith("|---"):
            stats["unmarked_segments"] += 1
            problems.append({"kind": "citation-without-claim-marker", "severity": "warning",
                             "message": f"cited text has no claim marker: \"{tail.strip()[:90]}…\"",
                             "hint": "end each cited sentence or table row with <!-- cNNN … --> naming the claims it uses"})
    return stats


def health_of(src: dict, timeout: float) -> str:
    url = src["url"]
    r = fetch.http(url, method="HEAD", timeout=timeout)
    if r.err == "dns-failure":
        return "POSSIBLY-FABRICATED"
    if r.err or r.status in (403, 404, 405, 410, 429, 500, 501, 502, 503):
        r = fetch.http(url, timeout=timeout, max_bytes=256 * 1024)
    if r.err is None and r.status is not None and 200 <= r.status < 400:
        if src.get("fetch_method") in ("wayback", "commoncrawl") and src.get("status") == "ok":
            return "LIVE"  # live now; the archived copy was used for text
        return "LIVE"
    if r.err == "dns-failure":
        return "POSSIBLY-FABRICATED"
    rows = fetch.cdx_query(url, timeout, limit="1", status_200=False)
    if rows:
        return "ARCHIVED-ONLY"
    if src.get("fetch_method") in ("wayback", "commoncrawl"):
        return "ARCHIVED-ONLY"
    if not fetch.dns_resolves(url):
        return "POSSIBLY-FABRICATED"
    return "DEAD"


def check_health(run: ledger.Run, cited: list[int], problems: list, timeout: float) -> dict:
    sources = run.sources()["sources"]
    todo = [s for s in sources if s.get("status") == "ok" or s["n"] in set(cited)]
    todo = [s for s in todo if s.get("fetch_method") != "search-snippet-only" or s["n"] in set(cited)]
    results: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for s, h in zip(todo, ex.map(lambda s: health_of(s, timeout), todo)):
            results[s["n"]] = h
    with run.lock():
        data = run.sources()
        for s in data["sources"]:
            if s["n"] in results:
                s["health"] = results[s["n"]]
        run.save_sources(data)
    counts: dict[str, int] = {}
    for n, h in results.items():
        counts[h] = counts.get(h, 0) + 1
        if h == "DEAD":
            problems.append({"kind": "dead-url", "severity": "warning", "n": n, "message": f"[{n}] does not resolve now and has no archive capture", "hint": "keep the citation only if the text was fetched live during the run (status ok); say so in methodology"})
        elif h == "POSSIBLY-FABRICATED" and n in set(cited):
            problems.append({"kind": "possibly-fabricated-cited", "severity": "error", "n": n, "message": f"[{n}] host does not resolve", "hint": "remove the citation"})
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="model-free citation pass")
    ap.add_argument("--run", default=None)
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--format", default="md", choices=["md", "json"])
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args(argv)
    run_dir = a.run or __import__("os").environ.get("DEEP_RESEARCH_RUN")
    if not run_dir:
        print("--run DIR required", file=sys.stderr)
        return 2
    run = ledger.Run(Path(run_dir)).require()
    problems: list = []
    q = check_quotes(run, problems)
    r = check_report(run, problems)
    h = check_health(run, r["cited"], problems, a.timeout) if not a.no_network else {}
    ledger.do_render(run)
    order = {"error": 0, "warning": 1, "info": 2}
    problems.sort(key=lambda p: (order.get(p["severity"], 3), str(p.get("n", "")), p.get("kind", "")))
    errors = [p for p in problems if p["severity"] == "error" or (a.strict and p["severity"] == "warning")]
    summary = {"quotes": q, "report": {"found": r["report"], "citations": r["citations"], "unknown": r["unknown"], "distinct_sources_cited": len(r["cited"]), "tracing": r.get("tracing", {})},
               "health": h, "problems": problems, "errors": len(errors)}
    if a.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("# Citation check")
        print(f"- Quotes: {q['checked']} checked, {q['verified']} verified, {q['failed']} failed, {q['unknown']} not checkable (source not quote_safe)")
        print(f"- Report: {'found' if r['report'] else 'missing'}; {r['citations']} citations to {len(r['cited'])} sources; {r['unknown']} unknown numbers")
        t = r.get("tracing") or {}
        if t:
            print(f"- Tracing: {t.get('markers', 0)} claim markers; {t.get('traced', 0)} citations traced, {t.get('untraced', 0)} not traced, {t.get('unmarked_segments', 0)} cited segments without a marker")
        if r.get("uncited_central") is not None:
            print(f"- Coverage: {len(r['uncited_central'])} verified central claims never used in the report (listed under Problems as info)")
        print(f"- Health: {h if h else 'skipped (--no-network)'}")
        print()
        print("## Problems" if problems else "## Problems: none")
        for p in problems:
            print(f"- [{p['severity']}] {p['kind']}: {p['message']} — {p['hint']}")
        print()
        print("## OK" if not errors else f"## {len(errors)} error(s) to fix")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
