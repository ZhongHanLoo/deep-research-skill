#!/usr/bin/env python3
"""Agreement between two rubric judges on the same reports: per-item agreement, Cohen's kappa,
and the list of disagreements with both justifications, for adjudication.

  judge_agreement.py <dir> [<dir> ...] [--a judge.json] [--b judge-sonnet.json] [--json OUT]

Each dir holds the two judge files for one report. Prints the 2x2 table (a pass/fail vs b
pass/fail), raw agreement, kappa, and every disagreement as `dir id a=pass|fail b=pass|fail`
with the two justifications, so a third reader can decide with the report open.
"""
import argparse, json, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--a", default="judge.json")
    ap.add_argument("--b", default="judge-sonnet.json")
    ap.add_argument("--json")
    args = ap.parse_args()
    pp = pf = fp = ff = 0
    dis = []
    missing = []
    for d in args.dirs:
        d = Path(d)
        if not (d / args.b).exists():
            missing.append(str(d)); continue
        ja = {i["id"]: i for i in json.loads((d / args.a).read_text())["items"]}
        jb = {i["id"]: i for i in json.loads((d / args.b).read_text())["items"]}
        for rid, ia in ja.items():
            ib = jb.get(rid)
            if ib is None:
                missing.append(f"{d}/{rid}"); continue
            a, b = bool(ia.get("pass")), bool(ib.get("pass"))
            if a and b: pp += 1
            elif a and not b: pf += 1
            elif b: fp += 1
            else: ff += 1
            if a != b:
                dis.append({"dir": str(d), "id": rid, "a": a, "b": b,
                            "a_justification": ia.get("justification", ""), "b_justification": ib.get("justification", "")})
    n = pp + pf + fp + ff
    if not n:
        print("no comparable items"); return 1
    po = (pp + ff) / n
    pa = ((pp + pf) / n) * ((pp + fp) / n) + ((fp + ff) / n) * ((pf + ff) / n)
    kappa = (po - pa) / (1 - pa) if pa < 1 else float("nan")
    print(f"n items {n}: both pass {pp}, A pass/B fail {pf}, A fail/B pass {fp}, both fail {ff}")
    print(f"raw agreement {po:.3f}, Cohen's kappa {kappa:.3f}; A pass rate {(pp + pf) / n:.3f}, B pass rate {(pp + fp) / n:.3f}")
    if missing:
        print("missing:", *missing, sep="\n  ")
    for x in dis:
        print(f"\n{x['dir']}  {x['id']}  A={'pass' if x['a'] else 'FAIL'}  B={'pass' if x['b'] else 'FAIL'}")
        print(f"  A: {x['a_justification']}")
        print(f"  B: {x['b_justification']}")
    if args.json:
        Path(args.json).write_text(json.dumps({"n": n, "pp": pp, "pf": pf, "fp": fp, "ff": ff, "agreement": po, "kappa": kappa,
                                               "disagreements": dis}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
