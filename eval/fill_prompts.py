#!/usr/bin/env python3
"""Fill the role prompts for one pilot run from files, so nothing is pasted by hand.

The main agent hands each filled file to a role agent as "cat this file and follow it"
(subagents cannot use file-writing tools; see eval/RUNBOOK.md). Question text comes
from the private question file and is never printed; the filled prompts are written
under the private results tree.

  fill_prompts.py researcher --run RUN --question-file Q.json --angle SLUG --round R --out FILE
        [--brief RUN/00-brief.md] [--source-target 4]  (hypothesis and disconfirmer parsed from the brief)
  fill_prompts.py verifier   --run RUN --question-file Q.json --batch N --round R --out FILE [--label vN]
  fill_prompts.py writer     --run RUN --question-file Q.json --out FILE [--length 1500] [--mode report]
  fill_prompts.py judge      --run RUN --question-file Q.json --out FILE [--report report.md] [--judge-out judge.json]

Every placeholder must be consumed; the script exits 2 if any `{{...}}` survives.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skill" / "deep-research"
PROMPTS = SKILL / "prompts"
SCRIPTS = SKILL / "scripts"
JUDGE_PROMPT = ROOT / "eval" / "prompts" / "judge.md"

ANGLE_RE = re.compile(r"^###\s*\d+\.\s*(?P<slug>[A-Za-z0-9_-]+)\s*[—–-]+\s*(?P<label>.+?)\s*$")


def load_question(path: Path) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["question"].strip()


def parse_angles(brief: Path) -> dict:
    """Return {slug: {label, hypothesis, disconfirm}} from a 00-brief.md written to prompts/brief.md."""
    angles, cur = {}, None
    for line in brief.read_text(encoding="utf-8").splitlines():
        m = ANGLE_RE.match(line)
        if m:
            cur = m.group("slug")
            angles[cur] = {"label": m.group("label"), "hypothesis": "", "disconfirm": ""}
            continue
        if cur is None:
            continue
        if line.startswith("Hypothesis:"):
            angles[cur]["hypothesis"] = line[len("Hypothesis:"):].strip()
        elif line.startswith("Would disconfirm:"):
            angles[cur]["disconfirm"] = line[len("Would disconfirm:"):].strip()
    return angles


def fill(template: Path, mapping: dict) -> str:
    text = template.read_text(encoding="utf-8")
    for key, val in mapping.items():
        text = text.replace("{{" + key + "}}", str(val))
    left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
    if left:
        sys.exit(f"unfilled placeholders in {template.name}: {', '.join(left)}")
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role", choices=["researcher", "verifier", "writer", "judge"])
    ap.add_argument("--run", required=True, help="run folder (absolute or repo-relative)")
    ap.add_argument("--question-file", required=True, help="eval/private/questions/<id>.json")
    ap.add_argument("--out", required=True, help="where to write the filled prompt")
    ap.add_argument("--angle", help="researcher: angle slug as written in the brief")
    ap.add_argument("--brief", help="researcher: brief to parse (default RUN/00-brief.md)")
    ap.add_argument("--source-target", type=int, default=4)
    ap.add_argument("--round", type=int, help="researcher and verifier")
    ap.add_argument("--batch", type=int, help="verifier: batch number (verify/batch-N.md)")
    ap.add_argument("--label", help="verifier: label (default v<batch>)")
    ap.add_argument("--length", type=int, default=1500, help="writer: LENGTH_TARGET")
    ap.add_argument("--mode", default="report", help="writer: brief|report")
    ap.add_argument("--report", default="report.md", help="judge: report file relative to RUN")
    ap.add_argument("--judge-out", default="judge.json", help="judge: output file relative to RUN")
    a = ap.parse_args()

    run = Path(a.run).resolve()
    qfile = Path(a.question_file).resolve()
    question = load_question(qfile)
    base = {"QUESTION": question, "RUN": str(run), "SCRIPTS": str(SCRIPTS)}

    if a.role == "researcher":
        if not (a.angle and a.round):
            sys.exit("researcher needs --angle and --round")
        brief = Path(a.brief).resolve() if a.brief else run / "00-brief.md"
        angles = parse_angles(brief)
        if a.angle not in angles:
            sys.exit(f"angle {a.angle!r} not in {brief} (found: {', '.join(angles) or 'none'})")
        ang = angles[a.angle]
        if not ang["hypothesis"] or not ang["disconfirm"]:
            sys.exit(f"angle {a.angle!r} lacks a Hypothesis: or Would disconfirm: line in the brief")
        text = fill(PROMPTS / "researcher.md", {**base, "ANGLE_SLUG": a.angle, "ANGLE_LABEL": ang["label"],
                    "HYPOTHESIS": ang["hypothesis"], "DISCONFIRM": ang["disconfirm"],
                    "SOURCE_TARGET": a.source_target, "ROUND": a.round})
    elif a.role == "verifier":
        if not (a.batch and a.round):
            sys.exit("verifier needs --batch and --round")
        label = a.label or f"v{a.batch}"
        batch = run / "verify" / f"batch-{a.batch}.md"
        text = fill(PROMPTS / "verifier.md", {**base, "BATCH_ID": a.batch, "VERIFIER_LABEL": label, "ROUND": a.round,
                    "CLAIMS_MD": f"Read your batch file {batch}: its first section, \"Claims to corroborate (central)\", "
                                 "lists these claims (id, importance, source [n], text, quote, current label).",
                    "SUPPORTING_CLAIMS_MD": "The second section of the same batch file, \"Claims to quote-check only\", lists these."})
    elif a.role == "writer":
        text = fill(PROMPTS / "writer.md", {**base, "LENGTH_TARGET": a.length, "MODE": a.mode,
                    "CLAIMS_MD": f"Read the full claim list by running: `python3 {SCRIPTS}/ledger.py --run {run} claims list --format md` "
                                 f"(all labels). Also read `{run}/verification.md`."})
    else:  # judge hand-off: the agent reads the judge prompt, the question file and the report itself
        text = "\n".join([
            "# Role: rubric judge (hand-off)", "",
            f"Read `{JUDGE_PROMPT}` and follow it exactly. Its placeholders are filled from files, which you read yourself:",
            f"- `{{{{QUESTION}}}}` and `{{{{RUBRIC_JSON}}}}`: the `question` and `rubric` fields of `{qfile}`",
            f"- `{{{{REPORT}}}}`: `{run / a.report}` (read the whole file)", "",
            f"Write the JSON the judge prompt specifies, and nothing else, to `{run / a.judge_out}` with a quoted shell heredoc "
            "(`cat > file <<'EOF'`; you have no file-writing tool). Then print the path and the number of items you marked pass. "
            "Do not quote the question or rubric text in your final message.", ""])

    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"{a.role}: {out} ({len(text)} chars)")


if __name__ == "__main__":
    main()
