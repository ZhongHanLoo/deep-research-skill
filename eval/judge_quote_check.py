#!/usr/bin/env python3
"""Model-free check of a rubric judge's verdicts: every justification in judge.json quotes the
report passage that decided the item; this script tests whether each quoted span actually occurs
in the report. A pass whose deciding quote is not in the report is a suspect verdict; so is a fail
whose justification quotes text that is there. Run it on any run folder (report.md + judge.json)
or on a calibration pack's graded/ tree.

  judge_quote_check.py <dir> [<dir> ...] [--report report.md] [--judge judge.json] [--min-words 3] [--json OUT]

Matching: quotes are the spans inside '...', "...", ‘...’ or “...” in the justification; both
sides are normalised (case, whitespace, curly quotes and dashes, ellipses split the quote into
fragments); a fragment matches if it is a substring of the report, otherwise if the fraction of
its word 3-shingles found in the report is at least 0.8 (a near-quote with a small edit).
Fragments shorter than --min-words are ignored (they are labels, not passages).
"""
import argparse, json, re, sys
from pathlib import Path


def norm(s):
    s = s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


QUOTE_RE = re.compile(r"[\"“]([^\"“”]{6,}?)[\"”]|(?<![A-Za-z])['‘]([^'’]{6,}?)['’](?![A-Za-z])")


def quotes_in(text):
    out = []
    for m in QUOTE_RE.finditer(text):
        q = m.group(1) or m.group(2)
        for frag in re.split(r"\s*(?:\.\.\.|…|\[\.\.\.\])\s*", q):
            frag = frag.strip(" .,;:")
            if frag:
                out.append(frag)
    return out


def shingles(words, k=3):
    return {tuple(words[i:i + k]) for i in range(max(0, len(words) - k + 1))}


def match(frag, report_norm, report_shingles, min_words):
    f = norm(frag)
    words = re.findall(r"[a-z0-9§][a-z0-9§.'/-]*", f)
    if len(words) < min_words:
        return None
    if f in report_norm:
        return 1.0
    sh = shingles(words)
    if not sh:
        return 1.0 if f in report_norm else 0.0
    return sum(1 for s in sh if s in report_shingles) / len(sh)


def check_dir(d, report_name, judge_name, min_words):
    d = Path(d)
    report = (d / report_name).read_text()
    judge = json.loads((d / judge_name).read_text())
    rn = norm(report)
    rs = shingles(re.findall(r"[a-z0-9§][a-z0-9§.'/-]*", rn))
    rows = []
    for it in judge.get("items", []):
        frags = quotes_in(it.get("justification", ""))
        scores = [(fr, match(fr, rn, rs, min_words)) for fr in frags]
        scored = [(fr, sc) for fr, sc in scores if sc is not None]
        matched = [fr for fr, sc in scored if sc >= 0.8]
        unmatched = [(fr, round(sc, 2)) for fr, sc in scored if sc < 0.8]
        if not scored:
            flag = "no-quote"
        elif it.get("pass") and unmatched:
            flag = "PASS-QUOTE-MISSING" if not matched else "pass-partial"
        elif not it.get("pass") and matched:
            flag = "fail-quotes-present"
        else:
            flag = "ok"
        rows.append({"dir": str(d), "id": it["id"], "pass": bool(it.get("pass")), "quotes": len(scored),
                     "matched": len(matched), "unmatched": unmatched, "flag": flag})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--report", default="report.md")
    ap.add_argument("--judge", default="judge.json")
    ap.add_argument("--min-words", type=int, default=3)
    ap.add_argument("--json")
    a = ap.parse_args()
    allrows = []
    for d in a.dirs:
        allrows += check_dir(d, a.report, a.judge, a.min_words)
    from collections import Counter
    c = Counter(r["flag"] for r in allrows)
    print(f"{len(allrows)} items over {len(a.dirs)} reports: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    for r in allrows:
        if r["flag"] not in ("ok",):
            print(f"  {r['dir']}  {r['id']}  {'pass' if r['pass'] else 'FAIL'}  {r['flag']}  quotes {r['matched']}/{r['quotes']}"
                  + (f"  unmatched: {r['unmatched'][:2]}" if r["unmatched"] else ""))
    if a.json:
        Path(a.json).write_text(json.dumps(allrows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
