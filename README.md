# deep-research-skill

A portable **deep-research skill** for AI coding agents: invoke it (e.g. `/deep-research <question>`) and get a fact-checked, cited Markdown report plus a fully auditable run folder.

Built and tested on Claude Code. Written to the open Agent Skills standard (`SKILL.md`), harness-agnostic core, so it can be used from other harnesses.

## Status

Round 1, in progress (started 2026-09-02). Requirements are being locked and the literature review is underway. No skill code yet.

## Why this repo exists

This is both the skill and the **evidence behind it**. Every design choice is traced to a literature survey or an experiment recorded here, so a future round can re-check whether the workflow is still the best available and update it.

- `progress.md` — chronological log of plans, research, findings and decisions.
- `research/literature/` — sourced surveys (output formats of existing systems, evaluation methods, web-fetch reliability).
- `research/prior-art/README.md` — descriptions of the baselines compared against (versions, dates, links). Code of third parties is not redistributed here.
- `skill/` — the skill (to come).
- `evidence/` — pilot evaluation results (to come; questions and rubrics stay private).

## License

MIT.
