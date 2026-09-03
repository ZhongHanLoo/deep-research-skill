# eval — pilot comparison tooling (public; questions and rubrics stay in `eval/private/`, gitignored)

Protocol: `research/literature/evaluation-survey.md` "Recommended protocol"; decisions in `progress.md` #11-#13, #32. Round-1 pilot (REQ 4): 12-15 questions across five domains, workflow A = Claude Code built-in `/deep-research`, workflow B = this skill; generator Claude Sonnet for both; judge Claude Opus (same-family limitation recorded).

## Procedure
1. Questions and rubrics are written before any report (`eval/private/questions/*.json`, format in `eval/private/README.md`).
2. Generate reports. B: run the skill at the preset named in the question file; the run folder goes to `eval/private/results/<date>-B/<question-id>/`. A: the user invokes `/deep-research "<question>"` in Claude Code and saves the returned report as `eval/private/results/<date>-A/<question-id>/report.md` (plus the workflow stats it prints as `run.json` if available).
3. Model-free citation checks: for B, `cite_check.py` already ran; for A, `eval/cite_audit.py` parses inline URLs from the Markdown, resolves them, and tests quote containment (to come with the first A report; A has no ledger).
4. Rubric judging: for each report, give an Opus agent `eval/prompts/judge.md` filled with the question, rubric and report; it returns JSON, saved as `results/<date>-<workflow>/<question-id>/judge.json`. Reports are judged in random order, one report per call, without seeing the other workflow's report.
5. Scoring: `python3 eval/score.py --questions eval/private/questions --a eval/private/results/<date>-A --b eval/private/results/<date>-B` prints weighted compliance per report, the paired B−A difference with a bootstrap 95% interval (and a domain-cluster bootstrap), plus citation and cost columns from `run.json` where present.
6. Calibration: 10 reports hand-graded by the user against the same rubrics; `score.py --calibration <file>` reports judge sensitivity/specificity.
