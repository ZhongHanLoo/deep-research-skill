# deep-research-skill

A portable **deep-research skill** for AI coding agents: invoke it (e.g. `/deep-research <question>`) and get a fact-checked, cited Markdown report plus a fully auditable run folder.

Built and tested on Claude Code. Written to the open Agent Skills standard (`SKILL.md`), harness-agnostic core, so it can be used from other harnesses.

## Status

Round 1, in progress (started 2026-09-02). Requirements locked (`REQUIREMENTS.md`), four literature surveys done, v1 design written (`skill/DESIGN.md`), and the skill implemented on 2026-09-03 (`skill/deep-research/`). Scripts pass their unit and live integration tests; a smoke test and a two-question cost probe at `standard` depth have run (Opus-judged rubric compliance 0.88 and 0.96); the remaining probe questions and the comparison against Claude Code's built-in `/deep-research` are next (`eval/RUNBOOK.md`).

## Install and use (Claude Code)

```
git clone https://github.com/ZhongHanLoo/deep-research-skill
mkdir -p ~/.claude/skills && ln -s "$(pwd)/deep-research-skill/skill/deep-research" ~/.claude/skills/deep-research
```
Then `/deep-research <question>` (options: `--preset quick|standard|deep`, `--mode brief|report`, `--agents N`, `--sequential`, `--yes`). Requires Python 3.10+ and `curl`; no API keys. A run writes `research-runs/<date>-<slug>/` with `report.md`, `sources.md`, `verification.md`, `claims.json`, `run.json`, per-angle notes and raw fetched text. Other harnesses: see `adapters/`.

## How it works, in one paragraph

Brief with hypotheses per angle → one researcher agent per angle (search for pointers, fetch raw text through a keyless nine-rung fallback chain, extract claims with verbatim quotes that a script checks against the fetched text) → a second, evidence-seeded decomposition round with a saturation stop → verifiers that look for independent corroborating and contradicting sources (labels are derived from registered evidence; uncertainty stays `unverified`) → one writer working only from the claim ledger → a model-free citation pass (quote containment, unknown citations, URL health via Wayback) → `run.json`. Design rationale with evidence tags: `skill/DESIGN.md`; file and CLI contracts: `skill/deep-research/reference/contracts.md`.

## Re-auditing this workflow (cold start)

1. Read `progress.md` (top "Current state", then the latest entries) and `REQUIREMENTS.md`.
2. Re-check the dated sources in `research/literature/*.md`; each claim there carries a URL or paper and the date it was read.
3. Re-run `skill/deep-research/tests/integration.sh` and `python3 skill/deep-research/tests/test_cite_check.py`; fetch rungs change (the surveys record what each service returned on 2026-09-02/03).
4. Re-run the pilot protocol in `research/literature/evaluation-survey.md` against the current baselines; record results under `evidence/`.

## Why this repo exists

This is both the skill and the **evidence behind it**. Every design choice is traced to a literature survey or an experiment recorded here, so a future round can re-check whether the workflow is still the best available and update it.

- `progress.md` — chronological log of plans, research, findings and decisions.
- `research/literature/` — sourced surveys (output formats of existing systems, evaluation methods, web-fetch reliability).
- `research/prior-art/README.md` — descriptions of the baselines compared against (versions, dates, links). Code of third parties is not redistributed here.
- `skill/DESIGN.md` — the v1 design, every choice tagged with its evidence.
- `skill/deep-research/` — the skill: `SKILL.md`, `prompts/` (role prompts), `scripts/` (fetch chain, ledger, citation check), `reference/contracts.md`, `tests/`.
- `adapters/` — per-harness notes (Claude Code tested; Hermes and Codex untested).
- `evidence/` — pilot evaluation results (to come; questions and rubrics stay private).

## License

MIT.
