#!/usr/bin/env python3
"""Build and collect the judge-calibration pack (protocol step 10 of the evaluation survey;
eval/README.md step 6): the user hand-grades ten judged reports against their rubrics, blind to
the judge's verdicts and to which workflow wrote each report; `score.py --calibration` then
reports the judge's sensitivity and specificity against the hand grades.

Everything the script reads or writes stays under eval/private/ (gitignored). No question or
rubric text lives in this file.

  make_calibration_pack.py build   --manifest eval/private/calibration/manifest.json --out eval/private/calibration [--seed 0]
  make_calibration_pack.py collect --out eval/private/calibration

Manifest: {"reports": [{"key": "<qid or qid.tag>", "workflow": "A|B", "question_id": "<qid>",
                        "run_dir": "<run folder>", "report": "report.md", "judge": "judge.json"}]}
`key` is the folder name score.py will look for under <out>/graded/<workflow>/; use "<qid>.<tag>"
when the same question appears twice for one workflow.

build  writes <out>/pack/NN/{report.md, sheet.md} in a seeded random order with the judge's
       verdicts and the workflow hidden, <out>/pack/README.md (grading instructions),
       <out>/graded/<workflow>/<key>/{report.md, judge.json} (what score.py reads) and
       <out>/key.json (NN -> key; for the collect step, not for the grader).
collect parses the "Your grade" column of every sheet (P/F), writes <out>/calibration.json in
       score.py's format {key: {workflow: {item_id: bool}}} and prints the score.py command.
"""
import argparse, json, random, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "eval" / "private" / "questions"

RULES = """# Judge calibration pack: how to grade

Ten reports, numbered 01-10 in random order. For each, open `sheet.md`, read the whole
`report.md`, and fill the **Your grade** column with `P` (pass) or `F` (fail) for every rubric
item. Apply the same rule the judge is given:

> Decide pass only if the report states the fact or does the thing the item describes,
> explicitly and correctly; a vague or partial mention is a fail. Judge only what the report
> says; do not use outside knowledge to fill gaps, and do not reward length.

The rubric author's `evidence` column is the source the item was written from; it is there for
reference, not something the report must cite. A one-line note per item is welcome but optional.
Do not open `../key.json` or `../graded/` until every sheet is filled: they reveal which run and
which workflow each report came from and what the judge decided. When done, say "graded" and the
session runs `make_calibration_pack.py collect` and `score.py --calibration`.
"""


def load_manifest(path):
    m = json.loads(Path(path).read_text())
    for r in m["reports"]:
        for k in ("key", "workflow", "question_id", "run_dir", "report", "judge"):
            assert k in r, f"manifest entry missing {k}: {r}"
        assert r["workflow"] in ("A", "B")
    return m["reports"]


def build(args):
    out = Path(args.out)
    reports = load_manifest(args.manifest)
    keys = [(r["workflow"], r["key"]) for r in reports]
    assert len(keys) == len(set(keys)), "duplicate (workflow, key) in manifest"
    order = list(range(len(reports)))
    random.Random(args.seed).shuffle(order)
    pack = out / "pack"
    if pack.exists():
        shutil.rmtree(pack)
    graded = out / "graded"
    if graded.exists():
        shutil.rmtree(graded)
    pack.mkdir(parents=True)
    (pack / "README.md").write_text(RULES)
    key = {}
    for n, idx in enumerate(order, 1):
        r = reports[idx]
        run = ROOT / r["run_dir"]
        report_src = run / r["report"]
        judge_src = run / r["judge"]
        assert report_src.exists(), report_src
        assert judge_src.exists(), judge_src
        q = json.loads((QUESTIONS / f"{r['question_id']}.json").read_text())
        judge_items = {it["id"] for it in json.loads(judge_src.read_text())["items"]}
        rubric_ids = {it["id"] for it in q["rubric"]}
        assert judge_items == rubric_ids, f"{r['key']}: judge items {judge_items ^ rubric_ids} differ from rubric"
        d = pack / f"{n:02d}"
        d.mkdir()
        shutil.copy(report_src, d / "report.md")
        lines = [f"# Report {n:02d}: grading sheet", "",
                 "Fill **Your grade** with `P` or `F` for every row. Read the whole `report.md` first.", "",
                 "## Question the report was asked to answer", "", q["question"], "",
                 "## Rubric", "",
                 "| id | type | weight | item | rubric author's evidence | Your grade | Note |",
                 "|---|---|---|---|---|---|---|"]
        for it in q["rubric"]:
            ev = it.get("evidence") or ""
            item = it["item"].replace("|", "\\|")
            lines.append(f"| {it['id']} | {it['type']} | {it['weight']} | {item} | {ev} |  |  |")
        lines += ["", "## Optional holistic notes", "",
                  "- Factual sentences with no citation (up to 5):", "- Contradictions inside the report:",
                  "- One-line verdict:", ""]
        (d / "sheet.md").write_text("\n".join(lines))
        g = graded / r["workflow"] / r["key"]
        g.mkdir(parents=True)
        shutil.copy(report_src, g / "report.md")
        shutil.copy(judge_src, g / "judge.json")
        key[f"{n:02d}"] = {"key": r["key"], "workflow": r["workflow"], "question_id": r["question_id"],
                           "run_dir": r["run_dir"], "report": r["report"], "judge": r["judge"]}
    (out / "key.json").write_text(json.dumps(key, indent=1))
    words = sum(len((pack / n / "report.md").read_text().split()) for n in key)
    print(f"pack: {len(key)} reports, {words} words of report text, under {pack}")
    print(f"graded copies under {graded}; key at {out / 'key.json'}")


GRADE = {"p": True, "pass": True, "true": True, "t": True, "y": True, "yes": True, "1": True,
         "f": False, "fail": False, "false": False, "n": False, "no": False, "0": False}


def collect(args):
    out = Path(args.out)
    key = json.loads((out / "key.json").read_text())
    cal = {}
    missing = []
    for n, meta in sorted(key.items()):
        sheet = (out / "pack" / n / "sheet.md").read_text().split("\n")
        grades = {}
        for line in sheet:
            m = re.match(r"^\|\s*([a-z]\d+)\s*\|", line)
            if not m:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            g = cells[5].lower()
            if g not in GRADE:
                missing.append(f"{n}/{m.group(1)}: {cells[5]!r}")
                continue
            grades[m.group(1)] = GRADE[g]
        cal.setdefault(meta["key"], {})[meta["workflow"]] = grades
    if missing:
        print("unfilled or unreadable grades:", *missing, sep="\n  ")
        return 2
    (out / "calibration.json").write_text(json.dumps(cal, indent=1))
    n_items = sum(len(g) for per in cal.values() for g in per.values())
    print(f"wrote {out / 'calibration.json'}: {len(key)} reports, {n_items} items")
    print("now run (A and B must both be present so score.py reaches the calibration step):")
    print(f"  python3 eval/score.py --questions eval/private/questions --a {out}/graded/A --b {out}/graded/B --calibration {out}/calibration.json")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--manifest", required=True); b.add_argument("--out", required=True); b.add_argument("--seed", type=int, default=0)
    c = sub.add_parser("collect"); c.add_argument("--out", required=True)
    args = ap.parse_args()
    return build(args) if args.cmd == "build" else collect(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
