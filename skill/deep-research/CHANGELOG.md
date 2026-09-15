# Changelog — deep-research skill

Versions are git tags on `github.com/ZhongHanLoo/deep-research-skill`. Every figure below is reproduced from `evidence/pilot-2026-09/README.md` (public tables) and `progress.md` (the dated log); questions and rubrics are private. "Compliance" is Opus-judged rubric compliance on the project's private question set, generator Sonnet, one run per cell unless stated.

## v1.3 — 2026-09-11 (current)
Prompt-only; contract unchanged (v1.1); `SKILL.md` and `ledger.py` report 1.3.0.
- `prompts/researcher.md`: a line that registers a page's own definitional, status, threshold and rule sentences as `supporting` claims even when they read as general (the class every remaining rubric miss belonged to; `decisions/adjacent-passage-class.md`); a stop-rule clause that a page counts once any claim is registered from it.
- `eval/prompts/judge.md` (evaluation tooling, not the skill): an item with several parts passes only if every part is present.
- Evidence, paired on the same briefs against v1.2 with the earlier report re-judged the same way: 1.00 vs 0.929 (+19% tokens), 0.84 vs 0.92 (−8%), 0.923 vs 0.923 (+4%). Mean 0.921 vs 0.924 at n=3: not shown better, not worse. The extraction line reached its target sentence on one of three live runs; the writer then left that claim unused. v1.3 stays current because it is mechanically no worse; the `v1.2` tag is the state with the most paired evidence.
- Tested and not applied (2026-09-15): two writer-prompt passages (claim-density rule and per-section word check; a "what it is / status" row per named entity) lost an offline A/B on one ledger, 0.84 vs 0.92 (`decisions/backlog.md` W1, W3; `eval/experiments/writer-w1w3.md`).

## v1.2 — 2026-09-11
Additive edits after the v1.1 tag, confirmed on four stable questions against their v1.0 runs (0.90-1.00 at 1.6-2.0M tokens, no agent killed) and a fifth domain (0.92 first pass):
- Writer: outline opens with a question-coverage table (one row per part of the question, gaps declared before judging); any presentation element the question asks for (a dated timeline, a comparison table) gets its own outline section and budget.
- `cite_check.py`: lists unused `supporting` claims that carry a number, grade or recommendation (surfaced two rubric facts on first use).
- `ledger.py add-url`: RFC mirrors and mobile Wikipedia fold into one registration.
- Researcher prompt: scans a specification's section list; fetches a body's companion statement.
- Fetch gate: recognises Wiley's cookie wall and Anubis/BAILII block pages.
- `grade --published ""` clears a wrong date. `eval/fill_prompts.py` fills every role prompt from files.
- Two post-cutoff questions on this version: 0.923 after one coverage pass (1.50M) and 0.929 first pass (1.46M), no freshness failure.

## v1.1 — 2026-09-10
Contract v1.1 first, then code, prompts, tests. Applies what the pilot measured:
- Researchers stop at the per-angle source target (never exceed it by more than one); the ledger caps `central` at 4 per source and 16 per angle (env `DEEP_RESEARCH_ANGLE_CENTRAL_CAP`), the rest written as `supporting`. The cap number is not quoted in prompts (quoting it raised central claims from 63 to 80 on the same brief).
- `claim add --from-json` accepts `--round`, so a claim carries its researcher's round.
- Verifiers grade every source they add; the writer's confidence rule reads the grade; author-level independence note for verifiers.
- Nav-only fetch gate for menu pages that pass the length gate.
- Writer: length target stated first with a per-section word budget.
- `claim unevidence`: the ledger's one undo, for the main agent.
- Confirmation on culture-history-3: 1.00, 1.85M tokens (v1.0: 1.00, 2.3M).

## v1.0 — 2026-09-03
First implementation from the literature surveys and `skill/DESIGN.md`: `SKILL.md`, role prompts (brief, researcher, verifier, writer), `scripts/{fetch,ledger,cite_check,textmatch}.py`, `reference/contracts.md`, offline tests and a live integration test. Smoke run (`evidence/smoke-runs/2026-09-03-coffee-health/`, quick preset, brief mode, 390k tokens) fixed four things before the pilot: bot-check interstitials served as 200s, a false fabrication verdict on a paywalled article, repository hosts counted as one domain, and subagents' lack of a file-writing tool. Pilot (five stable questions, `standard`): 0.88-1.00 first pass; the Claude Code built-in `/deep-research` on two of them: 0.655 and 0.577.
