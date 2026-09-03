#!/usr/bin/env python3
"""Score judged reports and compare two workflows (stdlib only).

  score.py --questions DIR --a DIR --b DIR [--iters 10000] [--seed 0] [--calibration FILE]

Layout expected: <a|b>/<question-id>/judge.json  ({"items":[{"id","pass"}...]})
                 <a|b>/<question-id>/run.json    (optional: tokens, wall_clock_s, health, claims)
                 <a|b>/<question-id>/cite.json   (optional: {"url_valid_rate","quote_containment_rate","fabricated_rate"})
Primary metric: weighted rubric compliance = sum(w * pass) / sum(w) per report; paired difference B-A
with a paired bootstrap 95% interval and a domain-cluster bootstrap interval.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path


def load_questions(d: Path) -> dict:
    qs = {}
    for f in sorted(d.glob("*.json")):
        q = json.loads(f.read_text(encoding="utf-8"))
        qs[q["id"]] = q
    return qs


def compliance(q: dict, judge: dict) -> float | None:
    weights = {r["id"]: float(r.get("weight", 1)) for r in q["rubric"]}
    got = {it["id"]: bool(it.get("pass")) for it in judge.get("items", [])}
    tot = sum(weights.values())
    if not tot:
        return None
    return sum(w for rid, w in weights.items() if got.get(rid)) / tot


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def bootstrap_ci(diffs: list[float], iters: int, rng: random.Random) -> tuple[float, float]:
    n = len(diffs)
    means = []
    for _ in range(iters):
        s = [diffs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters) - 1]


def cluster_bootstrap_ci(by_domain: dict[str, list[float]], iters: int, rng: random.Random) -> tuple[float, float]:
    doms = list(by_domain)
    means = []
    for _ in range(iters):
        pool = []
        for _ in doms:
            pool.extend(by_domain[doms[rng.randrange(len(doms))]])
        means.append(sum(pool) / len(pool))
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters) - 1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", required=True)
    ap.add_argument("--a", required=True, help="baseline results dir")
    ap.add_argument("--b", required=True, help="skill results dir")
    ap.add_argument("--iters", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--calibration", help="JSON: {question_id: {workflow: {item_id: bool}}} hand grades")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    qs = load_questions(Path(args.questions))
    rows = []
    for qid, q in qs.items():
        ja = read_json(Path(args.a) / qid / "judge.json")
        jb = read_json(Path(args.b) / qid / "judge.json")
        if not ja or not jb:
            continue
        ra, rb = read_json(Path(args.a) / qid / "run.json") or {}, read_json(Path(args.b) / qid / "run.json") or {}
        ca, cb = read_json(Path(args.a) / qid / "cite.json") or {}, read_json(Path(args.b) / qid / "cite.json") or {}
        rows.append({"id": qid, "domain": q["domain"], "a": compliance(q, ja), "b": compliance(q, jb),
                     "tok_a": ra.get("tokens"), "tok_b": rb.get("tokens"), "wall_a": ra.get("wall_clock_s"), "wall_b": rb.get("wall_clock_s"),
                     "cite_a": ca.get("quote_containment_rate"), "cite_b": cb.get("quote_containment_rate")})
    if not rows:
        print("no paired judged reports found")
        return 1
    print("| question | domain | A | B | B-A | tokens A/B | cite A/B |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        f = lambda v: "" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
        print(f"| {r['id']} | {r['domain']} | {f(r['a'])} | {f(r['b'])} | {f(r['b'] - r['a'])} | {f(r['tok_a'])}/{f(r['tok_b'])} | {f(r['cite_a'])}/{f(r['cite_b'])} |")
    diffs = [r["b"] - r["a"] for r in rows]
    mean = sum(diffs) / len(diffs)
    lo, hi = bootstrap_ci(diffs, args.iters, rng)
    by_dom: dict[str, list[float]] = {}
    for r in rows:
        by_dom.setdefault(r["domain"], []).append(r["b"] - r["a"])
    clo, chi = cluster_bootstrap_ci(by_dom, args.iters, rng)
    print()
    print(f"n = {len(rows)} paired questions; mean compliance A = {statistics.mean(r['a'] for r in rows):.3f}, B = {statistics.mean(r['b'] for r in rows):.3f}")
    print(f"B - A = {mean:+.3f}; paired bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}]; domain-cluster bootstrap 95% CI [{clo:+.3f}, {chi:+.3f}]")
    wins = sum(1 for d in diffs if d > 0); losses = sum(1 for d in diffs if d < 0)
    print(f"B wins {wins}, loses {losses}, ties {len(diffs) - wins - losses}")
    verdict = "B better" if lo > 0 else "A better" if hi < 0 else f"no resolvable difference at n={len(rows)}"
    print(f"Verdict on the primary metric: {verdict} (citation metrics must not be worse; see columns)")
    if args.calibration:
        cal = read_json(Path(args.calibration)) or {}
        tp = fp = fn = tn = 0
        for qid, per_wf in cal.items():
            for wf, items in per_wf.items():
                j = read_json(Path(args.a if wf == "A" else args.b) / qid / "judge.json") or {}
                got = {it["id"]: bool(it.get("pass")) for it in j.get("items", [])}
                for rid, human in items.items():
                    m = got.get(rid)
                    if m is None:
                        continue
                    tp += human and m; fp += (not human) and m; fn += human and (not m); tn += (not human) and (not m)
        if tp + fn and tn + fp:
            print(f"Judge calibration vs hand grades: sensitivity {tp / (tp + fn):.2f}, specificity {tn / (tn + fp):.2f}, n items {tp + fp + fn + tn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
