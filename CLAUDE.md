# ResearchWorkflow

## What this project is
We are designing, evidencing, and packaging the best possible **deep-research workflow** for AI coding agents, delivered as a portable **skill** (e.g. `/deep-research`) that works across harnesses: Claude Code, Codex, Hermes, and others. The repo will also hold the literature review, evidence, benchmarks, and decision log so the workflow can be re-audited and updated in future rounds.

## Requirements
All twelve gap questions are locked in `REQUIREMENTS.md` (2026-09-02). Read it before designing or implementing anything.

## Scope decisions so far
- 2026-09-02: **Web research only** for this round. No codebase or local-document research.
- 2026-09-02: **Output contract** = one run folder: `report.md` (deliverable), `angles/*.md` (per-agent notes), `sources.md`, `00-brief.md`, `verification.md` + `claims.json`, `run.json`. Controls: depth preset (quick/standard/deep), mode (brief/report). Details in progress.md entry #11.
- 2026-09-02: **Evaluation** = rubric-based LLM-judge protocol in `research/literature/evaluation-survey.md`; pilot first (~30 reports), judge = Claude Opus, generator = Sonnet, model-free citation checks, 10 hand-graded calibration reports.
- 2026-09-02: **Round 1 approach** = design from literature, then pilot comparison against Claude Code built-in `/deep-research`.
- 2026-09-02: **Tooling** = generic search + fetch, `curl` + Python stdlib only; keyless 9-step fetch fallback chain (see `research/literature/fetch-reliability-survey.md`); quotes only from raw text, never WebFetch summaries; no paywall/login/CAPTCHA circumvention.
- 2026-09-02: **Budget** = no wall-clock limit; user chooses agent count (with a shown recommendation) and parallel vs sequential; both modes produce the same run folder.
- 2026-09-02: **Autonomy** = clarify only if underspecified; one plan checkpoint (angles, agent count, parallel/sequential); then fully autonomous; skip flag for batch runs.
- 2026-09-02: **GitHub** = `ZhongHanLoo/deep-research-skill`, public, MIT, standalone (no skill dependencies); baselines described not redistributed; eval questions/rubrics private.
- 2026-09-02: **Re-audit** = manual, user-triggered; no schedule. Repo must support a cold-start re-audit (dated sources, evidence, README how-to).
- 2026-09-02: **Harness** = Claude Code only (build + test). Portability to other harnesses is a design constraint (Agent Skills standard `SKILL.md`, harness-agnostic core), not a test target.

## Files that must stay current
- `CLAUDE.md` (this file): project conventions and orientation. Update whenever conventions, structure, or scope change.
- `progress.md`: the chronological live log of everything we planned, researched, found, and decided. **Update it after every meaningful step, on your own, without being asked.** It is the recovery point after context compaction or a fresh session. Read it first at the start of any session.

## Working rules
- **Subagents:** always launch Agent-tool subagents with `model: "opus"` (user preference, 2026-09-02). Do not let them inherit Fable.
- Start every session by reading `progress.md` (at least the "Current state" section at the top and the latest entries at the bottom).
- Log to `progress.md` in chronological order: plan -> research conducted -> findings (with sources) -> decision and rationale. Convert relative dates to absolute (YYYY-MM-DD).
- Every claim in the literature review must carry a source (URL, paper, repo, commit) so a future round can re-verify it.
- Keep the skill itself harness-agnostic: plain Markdown instructions plus optional scripts; harness-specific glue (Claude Code `SKILL.md` frontmatter, Hermes skill layout, Codex equivalents) lives in thin adapter directories, never inside the core workflow text.
- Prefer evidence over opinion: when choosing between workflow designs, record what was compared, how, and the result.
- Git: repo is `github.com/ZhongHanLoo/deep-research-skill` (public, MIT). Commit at natural milestones; push when the user asks or at the end of a work session. Never commit `research/prior-art/*` code copies or `eval/private/` (gitignored). Local commit identity: ZH <ZhongHanLoo@users.noreply.github.com>.

## Environment notes (observed 2026-09-02)
- Claude Code plugins installed: superpowers 5.1.0, claude-mem 13.5.6, elements-of-style 1.0.0.
- Hermes installed at `~/.local/bin/hermes`; its skills live in `~/.hermes/skills/<category>/<skill>/`.
- Codex not found on PATH.

## Repo layout (planned, revise as it evolves)
```
CLAUDE.md
progress.md
research/
  prior-art/     # extracted/copied artifacts of existing systems (e.g. Claude Code built-in workflow script)
  literature/    # survey documents, each with dated source lists
evidence/        # benchmark runs, transcripts, scoring rubrics, results
skill/           # the portable deep-research skill (core, harness-agnostic)
adapters/        # per-harness packaging (claude-code/, hermes/, codex/)
decisions/       # ADR-style decision records (optional; may fold into progress.md)
```
