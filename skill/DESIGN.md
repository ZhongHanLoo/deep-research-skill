# deep-research skill — v1 design (draft 2026-09-02; implementation notes 2026-09-03)

Targets, in order: **fact recall**, **citation support**, then presentation. Every choice below cites its evidence: `R#` = recommendation in `research/literature/architecture-survey.md`; `OUT` = output-formats survey; `EVAL` = evaluation survey; `FETCH` = fetch-reliability survey; `REQ` = `REQUIREMENTS.md`.

## 1. Pipeline

```
0 Clarify ──► 1 Brief ──► [checkpoint] ──► 2 Search ──► 3 Fetch+Extract ──► 4 Re-decompose ──┐
                                               ▲                                              │ (loop ≤ N rounds,
                                               └──────────────── new angles / sub-questions ◄─┘  stop on saturation)
                                                                    │
                                         5 Corroborate ──► 6 Synthesize ──► 7 Citation pass ──► 8 Finalize
```

| Phase | What happens | Agent(s) | Evidence |
|---|---|---|---|
| 0 Clarify | Only if the question is underspecified: ask 2-3 questions. Otherwise skip. | main | R13, REQ 8 |
| 1 Brief | Write `00-brief.md`: refined question, 3-6 angles, **per angle a working hypothesis and what would disconfirm it**, depth preset, recommended agent count and mode. Show it; user confirms/adjusts (skippable). | main | R7, R13, R14, REQ 7-8 |
| 2 Search | One agent per angle. Short keyword-shaped queries, broad then narrow, deduplicated. Returns **pointers only** (URL, title, why relevant); no claims from snippets. Writes `angles/<angle>.md` (search section). | per angle | R1, R15, R16, FETCH (search output is a paraphrase, never a citation) |
| 3 Fetch + Extract | Fetch each selected URL through the keyless fallback chain (`scripts/fetch.py`), raw text to `raw/<n>.txt`. Extract **2-8 atomic falsifiable claims per source (one fact, ≤25 words), each with a verbatim quote**, source-quality grade, publish date. Append to `claims.json`; register source in `sources.md` with fetch method and evidence strength. **No global claim cap.** | per angle (same agent as search, or fetch pool) | R1, R3, R5, R12, FETCH chain, OUT |
| 4 Re-decompose | Main agent rebuilds a **compact working state** (question, findings so far, unanswered sub-questions) from files, not transcript. Generates a second round of angles/sub-questions seeded by evidence. Loop to 2 while new sources yield novel central claims; **stop after 2 consecutive rounds with no novel central claim, or at the round ceiling**. | main | R2, R6, R11 |
| 5 Corroborate | **Two tiers (added 2026-09-03 after the smoke test showed one 8-claim corroboration batch costing more than a researcher):** central claims are corroborated (decompose into checkable sub-questions, search for **corroborating** and contradicting evidence, independent voters if agent budget allows); the next tier is only quote-checked in context (does the quote support the claim?) and stays `single-source`. Outcome labels: `corroborated` (≥2 independent sources), `single-source`, `contradicted` (with the contradicting source), `unverified` (could not check). **Default under uncertainty is `unverified`, never `contradicted`.** Contradicted claims are kept in `verification.md` and listed in the report, not silently dropped. | verifier pool, sized ≤ fetch pool | R8, R3, EVAL (citation support is the dominant error) |
| 6 Synthesize | **One writer**, from `claims.json` + `verification.md` only (not raw pages). Order: exec summary (5-10 lines) → key-findings table (finding, confidence, #sources) → body with `[n]` citations → disagreements → **what this report could not find** → methodology note. Merge semantic duplicates; cap the share of claims any single source supports; no restating across sections. Length is a target range with a ceiling per depth preset. | writer | R4, OUT implications 3,6,8, EVAL |
| 7 Citation pass | **Model-free** (`scripts/cite_check.py`): every quote must appear (normalised) in the raw text it cites, else the claim is downgraded to `unverified` and flagged; every URL gets health status (LIVE / DEAD / ARCHIVED-ONLY) via HEAD + Wayback CDX; fabrication check on dead URLs; **every cited sentence names its claim ids in an HTML comment and each `[n]` must be a source those claims rest on** (added 2026-09-03: the smoke test's writer cited a corroborating source for a fact it did not support, the dominant error class in EVAL). Then one model pass fixing what the script flagged. | script + main | R9, EVAL (citation support), FETCH fabrication procedure, Hermes prior art |
| 8 Finalize | Write `run.json` (harness, model, depth, mode, agents, rounds, sources fetched/failed by method, claims by label, tokens if available, wall-clock). | main | REQ 2-3 |

**No revision loop without new retrieval** (R10). If the writer finds a gap, it emits a sub-question that re-enters phase 2, or records it under "could not find".

## 2. Budget allocation and presets

Principle: the marginal agent goes to **reading**, not adjudicating (R3). Fetch pool ≥ verifier pool, always.

| Preset | Angles (round 1) | Max rounds | Sources fetched (target) | Verifier budget | Report length target |
|---|---|---|---|---|---|
| quick | 2-3 | 1 | 6-8 | corroborate ≤8 central; quote-check other central | 300-600 words or `brief` answer |
| standard | 3-5 | 2 | 12-18 | corroborate all central; quote-check supporting | 800-1500 words |
| deep | 5-6 | 3 | 25-40 | corroborate central + supporting (two voters); quote-check tangential | 1500-3000 words, hard ceiling 3500 |

Recommended agent count shown at the checkpoint = number of round-1 angles (+1 writer). The user may set any count; **sequential mode** runs the same agent prompts one at a time and produces an identical run folder (REQ 7). Effort-scaling rule stated in the prompt: simple fact-finding → 1 agent; comparison → 2-4; open-ended → 5+ (R14).

## 3. Run folder (contract from REQ 2)

```
research-runs/<YYYY-MM-DD>-<slug>/
  00-brief.md       question, clarifications, angles + hypotheses, preset, agent plan
  angles/<a>.md     per-agent: queries issued, pointers found, sources fetched, extracted claims (summary)
  raw/<n>.txt       raw fetched text (gitignored by default; needed for quote containment)
  sources.md        [n] | title | publisher | published | accessed | grade | fetch_method | health | evidence_strength
  claims.json       [{id, text, quote, source_n, angle, grade, label, corroborated_by[], contradicted_by[], quote_verified}]
  verification.md   human-readable ledger by label; contradicted claims with counter-evidence
  report.md         deliverable
  run.json          metadata
```

## 4. Scripts (Python stdlib + curl only; FETCH portability constraint)

- `scripts/fetch.py <url>` — 9-step keyless chain (structured API by URL shape → harness fetch is *not* used here → raw HTTP with browser-like headers, HEAD first, robots.txt honoured → r.jina.ai (20 RPM) → urltomarkdown → Wayback CDX/id_ → Common Crawl → local PDF/HTML extraction → optional installed browser → UNFETCHABLE). Content plausibility gate (block-page markers, min length, title/URL consistency). Emits JSON: text path, method, status, snapshot_date, evidence_strength, quote_safe.
- `scripts/ledger.py` — owns `sources.md` numbering and `claims.json` append/update (Hermes ledger idea: the model never invents `[n]`).
- `scripts/cite_check.py` — quote containment (normalised whitespace/quotes/case, shingle fallback), URL health, Wayback fabrication check; rewrites labels; produces a summary for the writer.
- `run.json` is created by `ledger.py init` and completed by `ledger.py finalize` (the separate `runmeta.py` from the first draft was folded into the ledger, 2026-09-03).

Harness-side fetch (Claude Code `WebFetch`) is used only as a *discovery* aid, never as the source of quotes (FETCH: 125-char quote cap, summary not page).

## 5. Portability

- Core = `skill/deep-research/SKILL.md` (Agent Skills frontmatter) + `scripts/` + `prompts/` (one Markdown file per role: brief, researcher [search + fetch + extract in one agent per angle, so pointers never leave the agent that fetches them], verifier, writer) + `reference/contracts.md` (binding file and CLI contracts). No Claude-only syntax in prompts.
- Parallelism is expressed as "run these N role prompts, each with its angle, then continue"; Claude Code adapter maps this to subagents; a harness without subagents runs them sequentially.
- Adapter notes live in `adapters/<harness>.md`; only Claude Code is tested (REQ 5).

## 6. Departures from Claude Code built-in `/deep-research`, with evidence

| Built-in | v1 | Why |
|---|---|---|
| 15 fetch agents vs ~75 verifier agents | fetch pool ≥ verifier pool | recall is the bottleneck; retrieval is the lowest-error stage (R3, strong) |
| "Default to refuted=true if uncertain" | default `unverified`; seek corroboration | precision/recall asymmetry wrong for our target (R8, moderate-strong) |
| Angles generated once, cold | second evidence-seeded round + saturation stop | STORM ablation, IterResearch (R6, R11) |
| 25-claim cap before verification | no cap; verifier budget scales with preset | cap discards up to 2/3 of evidence (R3) |
| Quotes model-reported from WebFetch summaries | quotes from raw text, model-free containment check | WebFetch 125-char cap; unsupported-claim error dominates (R1, R9, FETCH) |
| Fixed pipeline, one shot | compact working state rebuilt from files each round | IterResearch as prompting strategy (R2, strong) |
| Report in chat only | run folder with ledgers, health, could-not-find | REQ 2, OUT critiques |

Kept from the built-in: quoted falsifiable claims from fetched pages; structured extraction as compression; independent voters; `unverified` vs `refuted` distinction; refuted/contradicted claims listed; state out of the session context; dedup + confidence ranking.

## 7. Things the pilot must measure (open questions)

1. False-refutation rate of the built-in's "default refuted" vs our "default unverified" (no published measurement exists).
2. Whether the second decomposition round adds novel central claims often enough to justify its cost at `standard` depth.
3. Fetch success rate by chain step (nobody publishes this).
4. Quote-containment failure rate of model-reported quotes.
5. Whether fetch ≥ verify allocation raises rubric recall without hurting citation support.

## 8. Not in v1

Codebase/local-document research; paid search APIs; browser automation beyond an already-installed browser; non-English; mid-run human checkpoints; automated re-audit.
