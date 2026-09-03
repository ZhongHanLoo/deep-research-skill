#!/usr/bin/env python3
"""Write verifier batch files for a run: unchecked central claims in batches of 8
(corroborate) plus a share of unchecked supporting/tangential claims (quote-check).

  make_batches.py --run DIR [--round R] [--start K] [--size 8]

Writes <run>/verify/batch-<k>.md and prints the count. Re-run after an interruption:
only still-unchecked claims are included.
"""
import argparse, math, subprocess, sys
from pathlib import Path

L = Path(__file__).resolve().parent.parent / "skill" / "deep-research" / "scripts" / "ledger.py"


def md(run, args):
    p = subprocess.run([sys.executable, str(L), "--run", run, "claims", "list", "--format", "md", *args], capture_output=True, text=True)
    return [l for l in p.stdout.strip().splitlines() if l.startswith("- ")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--round", type=int)
    ap.add_argument("--start", type=int, default=1, help="first batch number")
    ap.add_argument("--size", type=int, default=8)
    a = ap.parse_args()
    rnd = ["--round", str(a.round)] if a.round else []
    central = md(a.run, ["--importance", "central", "--unchecked", *rnd])
    supp = md(a.run, ["--importance", "supporting", "--unchecked", *rnd]) + md(a.run, ["--importance", "tangential", "--unchecked", *rnd])
    nb = math.ceil(len(central) / a.size) or (1 if supp else 0)
    per = math.ceil(len(supp) / nb) if nb else 0
    out = Path(a.run) / "verify"
    out.mkdir(exist_ok=True)
    for k in range(nb):
        body = "## Claims to corroborate (central)\n" + ("\n".join(central[k * a.size:(k + 1) * a.size]) or "(none)")
        body += "\n\n## Claims to quote-check only (supporting; no searching)\n" + ("\n".join(supp[k * per:(k + 1) * per]) or "(none)") + "\n"
        (out / f"batch-{a.start + k}.md").write_text(body, encoding="utf-8")
    print(f"{nb} batch files (batch-{a.start}..batch-{a.start + nb - 1}); {len(central)} central to corroborate, {len(supp)} supporting/tangential to quote-check")


if __name__ == "__main__":
    main()
