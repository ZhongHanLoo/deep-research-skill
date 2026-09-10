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
- 2026-09-10: **Skill v1.1.** The seven changes queued from the pilot were applied (contracts v1.1 first, then `ledger.py`/`fetch.py`, prompts, tests; progress.md #42). Confirmation run of culture-history-3: compliance 1.00 again, cost up (80 central claims vs 59; 2.17M+ tokens vs 1.85M) because the prompt named the per-angle cap and researchers filled it; the numerals were removed from `prompts/researcher.md`, not yet re-tested. Re-test the same afternoon with the un-numbered prompt (progress.md #43, `eval/private/results/2026-09-10-B2/`): central 63, 1.85M tokens (1.90M with a presentation pass), compliance 0.966 first pass (the dated timeline was missing because the writer fill did not ask for it) and 1.00 after one pass. The cap default stays 16; **v1.1 tagged**. The two small follow-ups from #43 were applied after the tag on 2026-09-10 evening (progress.md #44): the writer prompt gives any requested presentation element its own outline section (prompt-only, not re-tested), and `grade --published ""` clears a wrong date (contract §5, code, test; four suites pass). **Fuller pilot, second domain (2026-09-10 evening, progress.md #45):** technology-3 on v1.1: compliance 0.923 first pass (v1.0: 0.88 after a coverage pass), 1.64M tokens, 39 min, the presentation item passed from the prompt rule alone, the one miss is the same adjacent-rule recall failure as in 2026-09-03. Next: the user's call between more v1.1 questions (science-health-3 is the remaining stable question below 1.00) and the built-in baseline on a second question.
- 2026-09-05: **Stage C closed at n=1.** The built-in `/deep-research` was run on one stable question (0.655 vs the skill's 1.00; 7.95M tokens over three attempts because a fresh run does not fit one subscription window). The user chose not to run the other four; the comparison is reported as n=1 plus the cost finding (`evidence/pilot-2026-09/README.md`). Next: apply the design changes queued in progress.md #38/#39/#41, then decide on a fuller pilot.
- 2026-09-02: **Harness** = Claude Code only (build + test). Portability to other harnesses is a design constraint (Agent Skills standard `SKILL.md`, harness-agnostic core), not a test target.

## Files that must stay current
- `CLAUDE.md` (this file): project conventions and orientation. Update whenever conventions, structure, or scope change.
- `progress.md`: the chronological live log of everything we planned, researched, found, and decided. **Update it after every meaningful step, on your own, without being asked.** It is the recovery point after context compaction or a fresh session. Read it first at the start of any session.

## Working rules
- **Subagents:** always launch Agent-tool subagents with `model: "opus"` (user preference, 2026-09-02). Do not let them inherit Fable. If Opus returns repeated `529 Overloaded` (six failures on 2026-09-03), do the work in the main session rather than burning retries; for deep-research smoke/pilot runs the generator is Sonnet per REQ 4.
- **Pilot runs:** follow `eval/RUNBOOK.md` step by step (main agent = the session; Sonnet role agents; Opus judges). Record per-agent tokens in `eval/private/results/<date>-B/tokens.json` (killed agents: record `null`). A subscription session limit is hit after roughly 3.5M Sonnet tokens per window (2026-09-03 twice, 2026-09-04 at 00:55; the window reset at 01:00); the ledger survives killed agents, so re-run `eval/make_batches.py` (new `--start`, keep `--round` while round 2 is still running) and relaunch only what is unchecked. Tell researchers to stop at the source target (4; never exceed 5): that line cut central claims from 85-100 to 59 and the run to 1.85M tokens on 2026-09-04 (culture-history-3). Expect 1.85-2.3M Sonnet tokens per `standard` question; if the question's rubric or brief asks for a presentation element (a dated timeline, a comparison table), the writer prompt now gives it its own section (rule added 2026-09-10 after the tag, confirmed on technology-3 the same evening); naming it in the writer fill as well is harmless (the 2026-09-10 afternoon run lost one rubric item to a missing timeline and needed a 46k presentation pass); do not start a question when the window's budget is near that limit. A machine-side DNS failure ("Can't reach the API server, ENOTFOUND", 2026-09-10 at 08:52 and 09:18) kills every running agent at once: rebuild verifier batches as for a rate-limit kill, and resume a killed writer in place with SendMessage (its context survives) rather than relaunching it. Since v1.1 the researcher prompt carries the stop rule, `--round`, and the ledger-file rules itself; the per-angle central cap is mechanical (16, env `DEEP_RESEARCH_ANGLE_CENTRAL_CAP`) and must not be quoted as a number in prompts (it anchors researchers to it: 80 central claims with the number in the prompt vs 63 without, both on 2026-09-10, and 59 on 2026-09-04). Verifiers grade what they add; grade any straggler from the main session before `render` (a bash script, not a zsh `$VAR` command string). After the last round, run `make_batches.py` once more without `--round` (stray claims on earlier-round sources).
- **Subagents cannot use the Write/Edit tools:** every role prompt tells them to create files with quoted shell heredocs and absolute paths, and never to edit `claims.json`/`sources.json` directly or run ledger commands with placeholder values (the only undos are `ledger.py claim unevidence` and `grade N --grade G --published ""` to clear a wrong date, both for the main session). Role prompts are filled from files and handed to agents as "cat this file and follow it" (`eval/RUNBOOK.md`). The judge prompt is filled by pointing the agent at the question file and the report, never by pasting rubric text.
- **Timestamps in progress.md:** run `date` before writing a clock time; do not estimate (session 3 wrote wrong times and had to correct them).
- **Scripts contract:** `skill/deep-research/reference/contracts.md` is binding for prompts, scripts and adapters; change it first, then the code. Tests: `skill/deep-research/tests/integration.sh` (live network) and, offline, `tests/test_ledger.py`, `tests/test_cite_check.py`, `tests/test_fetch_gate.py` (run all four before committing a script change).
- **Shell:** the interactive shell is zsh; `echo ====` fails (`=cmd` expansion) and `$VAR` with spaces is not word-split. Put multi-step tests in a `bash` script file.
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
evidence/        # public results: smoke-runs/ (one full run folder), pilot-2026-09/README.md (Stage B and C results); questions/rubrics stay in eval/private/
skill/DESIGN.md  # v1 design with evidence tags
skill/deep-research/   # the portable skill (v1.1): SKILL.md, prompts/, scripts/{fetch,ledger,cite_check,textmatch}.py, reference/contracts.md, tests/{test_ledger,test_cite_check,test_fetch_gate}.py + integration.sh
adapters/        # per-harness notes (claude-code/ tested; hermes.md, codex.md untested)
decisions/       # ADR-style decision records (optional; may fold into progress.md)
```
