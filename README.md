# deep-research-skill

A portable **deep-research skill** for AI coding agents: invoke it (e.g. `/deep-research <question>`) and get a fact-checked, cited Markdown report plus a fully auditable run folder.

Built and tested on Claude Code. Written to the open Agent Skills standard (`SKILL.md`), harness-agnostic core, so it can be used from other harnesses.

## Status

Round 1, pilot complete (started 2026-09-02). Requirements locked (`REQUIREMENTS.md`), four literature surveys done, v1 design written (`skill/DESIGN.md`), the skill implemented on 2026-09-03 and revised to v1.1 on 2026-09-10 and v1.2 on 2026-09-11 (`skill/deep-research/`). Scripts pass their unit and live integration tests. The September 2026 pilot ran the skill on five stable questions at `standard` depth (Opus-judged rubric compliance 0.88-1.00, mean 0.95, 1.5-2.6M Sonnet tokens each) and the Claude Code built-in `/deep-research` on two of them (0.655 and 0.577 against the skill's 1.00 and 0.923, at 7.95M and 4.65M tokens; `evidence/pilot-2026-09/README.md`). A model-only judge check on 2026-09-11 (two Claude judges, kappa 0.79, disagreements adjudicated) found one lenient weight-3 pass repeated across the policy-law-3 reports, so that question is 0.79 adjusted and the five-domain range on the current skill is 0.79-1.00; the protocol's human calibration is still open. The first post-cutoff question (technology-1) ran on v1.2 on 2026-09-11: 0.923 after one coverage pass at 1.50M tokens, no freshness failure; the other nine post-cutoff questions are unrun. v1.1 applies what the pilot measured: researchers stop at the source target and the ledger caps central claims per angle (the cost lever), verifiers grade the sources they add, the writer drafts to a per-section word budget, and the fetch gate rejects menu-only pages. v1.2 adds the post-tag edits confirmed on four more domains against their v1.0 runs (0.90-1.00 at 1.6-2.0M tokens each, no agent killed): the writer opens its outline with a question-coverage table and gives presentation elements their own section, the citation script lists unused supporting claims that carry a number or grade, mirror hosts fold into one registration, and the fetch gate recognises cookie walls and bot-block pages.

## Install and use (Claude Code)

```
git clone https://github.com/ZhongHanLoo/deep-research-skill
mkdir -p ~/.claude/skills && ln -s "$(pwd)/deep-research-skill/skill/deep-research" ~/.claude/skills/deep-research
```
Then `/deep-research <question>` (options: `--preset quick|standard|deep`, `--mode brief|report`, `--agents N`, `--sequential`, `--yes`). Requires Python 3.10+ and `curl`; no API keys. A run writes `research-runs/<date>-<slug>/` with `report.md`, `sources.md`, `verification.md`, `claims.json`, `run.json`, the writer's `outline.md`, per-angle notes and raw fetched text. Other harnesses: see `adapters/`.

## How it works, in one paragraph

Brief with hypotheses per angle → one researcher agent per angle (search for pointers, fetch raw text through a keyless nine-rung fallback chain, extract claims with verbatim quotes that a script checks against the fetched text) → a second, evidence-seeded decomposition round with a saturation stop → verifiers that look for independent corroborating and contradicting sources (labels are derived from registered evidence; uncertainty stays `unverified`) → one writer working only from the claim ledger → a model-free citation pass (quote containment, unknown citations, URL health via Wayback) → `run.json`. Design rationale with evidence tags: `skill/DESIGN.md`; file and CLI contracts: `skill/deep-research/reference/contracts.md`.

## Re-auditing this workflow (cold start)

1. Read `progress.md` (top "Current state", then the latest entries) and `REQUIREMENTS.md`.
2. Re-check the dated sources in `research/literature/*.md`; each claim there carries a URL or paper and the date it was read.
3. Re-run `skill/deep-research/tests/integration.sh` and `python3 skill/deep-research/tests/test_cite_check.py`; fetch rungs change (the surveys record what each service returned on 2026-09-02/03).
4. Re-run the pilot protocol in `research/literature/evaluation-survey.md` against the current baselines, step by step from `eval/RUNBOOK.md` (the baseline needs the model override in step 8); record results under `evidence/`. The judge-calibration pack builder and the two judge checks are in `eval/` (`make_calibration_pack.py`, `judge_quote_check.py`, `judge_agreement.py`).
5. Open candidates for the next skill version are listed in `decisions/backlog.md`.

## Why this repo exists

This is both the skill and the **evidence behind it**. Every design choice is traced to a literature survey or an experiment recorded here, so a future round can re-check whether the workflow is still the best available and update it.

- `progress.md` — chronological log of plans, research, findings and decisions.
- `research/literature/` — sourced surveys (output formats of existing systems, evaluation methods, web-fetch reliability).
- `research/prior-art/README.md` — descriptions of the baselines compared against (versions, dates, links). Code of third parties is not redistributed here.
- `skill/DESIGN.md` — the v1 design, every choice tagged with its evidence.
- `skill/deep-research/` — the skill: `SKILL.md`, `prompts/` (role prompts), `scripts/` (fetch chain, ledger, citation check), `reference/contracts.md`, `tests/`.
- `adapters/` — per-harness notes (Claude Code tested; Hermes and Codex untested).
- `evidence/` — pilot evaluation results: `evidence/smoke-runs/` (a complete `quick` run folder) and `evidence/pilot-2026-09/README.md` (Stage B results on five questions, the Stage C comparison with the Claude Code built-in `/deep-research` on two of them, the judge-reliability check, costs, and what changed). Questions and rubrics stay private.

## License

MIT.
