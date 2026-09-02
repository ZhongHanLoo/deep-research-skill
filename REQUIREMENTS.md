# Requirements — Round 1 (locked 2026-09-02)

Consolidated answers to the twelve gap questions. Rationale and sources are in `progress.md` (entries #1-#25) and `research/literature/`.

| # | Question | Decision |
|---|---|---|
| 1 | What counts as research | **Web research only.** No codebase or local-document research this round. |
| 2 | What a finished run produces | **One run folder:** `report.md` (self-contained deliverable: exec summary, findings table with confidence and source count, body with numbered `[n]` citations, verification labels per claim, "what this could not find", methodology note), `angles/<angle>.md` (one note per research agent), `sources.md` (numbered registry: title, publisher, publish date, access date, quality grade, URL health, fetch method), `00-brief.md` (plan written before research), `verification.md` + `claims.json` (human- and machine-readable claim ledger), `run.json` (harness, model, timings, agents, tokens). Controls: depth preset (quick / standard / deep) and mode (brief answer / full report). Default toward shorter reports. |
| 3 | How we judge a workflow better | Rubric-based protocol from `research/literature/evaluation-survey.md`: 40-60 fresh mixed-domain questions with pre-written binary rubrics; same model, effort and tool budget for every workflow; model-free citation checks (URL resolution, Wayback, quote containment); LLM judge with forced reasoning; paired bootstrap on rubric compliance as primary metric; 10 hand-graded reports for calibration. |
| 4 | Literature-only vs empirical | **Literature-first design, then a pilot:** ~12-15 questions, our skill vs Claude Code built-in `/deep-research`, 1 run each (~30 reports). **Judge = Claude Opus, generator = Claude Sonnet.** Same-family judge is a recorded limitation (symmetric bias). Full protocol deferred to a later round. |
| 5 | Harness | **Claude Code only** for build and test. Portability is a design constraint (Agent Skills `SKILL.md`, harness-agnostic core, glue kept separate), not a test target. |
| 6 | Tooling | **No API keys.** Core assumes generic web search + page fetch, `curl`, Python stdlib. Ships a keyless 9-step fetch fallback chain with a content plausibility gate (`research/literature/fetch-reliability-survey.md`). Search results are pointers, never citations; verbatim quotes only from raw text, never from summaries. Headless browser and paid APIs optional, auto-detected. Wayback check in core. Paywall / login / CAPTCHA circumvention out of scope. |
| 7 | Budget | **No wall-clock limit.** User chooses agent count (recommendation shown, derived from depth preset and angle count) and parallel vs sequential execution. Both modes produce the same run folder. |
| 8 | Autonomy | Clarifying questions only if the question is underspecified (max 2-3). **One plan checkpoint** after `00-brief.md`: confirm angles, agent count, execution mode. Fully autonomous afterwards. Skip flag for batch runs. |
| 9 | GitHub | `github.com/ZhongHanLoo/deep-research-skill`, public, MIT, standalone (no dependency on other skills). Baselines described, not redistributed. Evaluation questions and rubrics kept private. |
| 10 | Re-audit | **Manual, user-triggered.** No schedule. Repo must support a cold-start re-audit. |
| 11 | Prior-art preferences | None stated. Design from survey findings. |
| 12 | Domain / language | **General-purpose, English-first.** Pilot questions spread across five domains (technology/software, science/health, business/finance, policy/law, culture/history). |

## Design constraints that fall out of the surveys
- Optimise for **fact recall** and **citation support**, the two measured weaknesses of current systems; presentation is near-saturated.
- Every source records **how** it was fetched and how strong the evidence is; failures are recorded, not dropped.
- Verification status is part of the report, not only of the trace.
- Length is a ceiling with a target range, separate from depth.
