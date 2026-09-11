# Pilot evaluation, September 2026 (Phase 2, Stages B and C)

Protocol: `research/literature/evaluation-survey.md` (rubric-based LLM judge, binary weighted items written before any run; generator Sonnet, judge Opus; model-free citation checks on the same yardstick for both workflows). Operator procedure: `eval/RUNBOOK.md`. Scoring: `eval/score.py` (`compliance()` = weighted share of rubric items passed; the judge's own arithmetic is never used). Questions, rubrics, run folders, judge outputs and per-agent token ledgers are in `eval/private/` (gitignored, to avoid leakage); the chronological record with every incident is `progress.md` entries #33-#41.

Five "stable" questions (facts that do not change month to month), one per domain, `standard` preset, `report` mode, 4 round-1 angles, 4 sources per angle per round, 2 rounds, all central claims corroborated, supporting claims quote-checked.

## Stage B: the skill (workflow B), 2026-09-03 to 2026-09-04

| Question (domain, topic) | Date | Sources (ok) | Claims corrob./single/contra. | Central | Report words | Judge passes | Compliance | Generation tokens (agents) | Wall clock |
|---|---|---|---|---|---|---|---|---|---|
| technology-3 (HTTP caching semantics) | 09-03 | 61 (61) | 69/53/1 | 85 | 1,798 | 9/12 → 10/12 after coverage pass | 0.77 → **0.88** | 1.50M (16) | ~2 h incl. an outage |
| science-health-3 (vitamin D, falls and fractures) | 09-03 | 103 (94) | 76/47/2 | 91 | 1,790 | 11/12 | **0.96** | 2.61M (22) | ~2 h |
| business-finance-3 (FDIC vs SIPC coverage) | 09-04 | 116 (110) | 99/95/0 | 100 | 1,799 | 11/12 → 12/12 after coverage pass | 0.92 → **1.00** | 2.10M (25 + 6 killed by a session limit) | 102 min |
| policy-law-3 (judicial deference: US, Canada, UK) | 09-04 | 106 (101) | 74/101/2 | 86 | 1,796 | 11/12 | **0.897** | 2.32M (19 + 2 killed) | 98 min |
| culture-history-3 (Rosetta Stone and decipherment) | 09-04 | 64 (63) | 48/107/3 | 59 | 1,770 | 12/12 | **1.00** | 1.85M (16) | 56 min |

Mean compliance 0.95 (0.88, 0.96, 1.00, 0.897, 1.00). Citation checks inside the skill (`cite_check.py`): 778/778 verbatim quotes verified against fetched text across the five runs; 0 unknown citation numbers; every `[n]` in every report traced to a registered claim; URL health at check time 373 LIVE / 40 ARCHIVED-ONLY / 12 DEAD-now-but-fetched-live / 8 UNKNOWN.

**Same-yardstick audit of the five skill reports** (`eval/cite_audit.py`, run 2026-09-05, network health at audit time; the audit parses the report's own source list, so it sees the report as a ledger-less reader would):

| Question | URLs in report | URL valid | Flagged possibly-fabricated | Citing sentences | Sentence-shingle containment |
|---|---|---|---|---|---|
| technology-3 | 61 | 0.984 | 0 | 30 | 0.10 |
| science-health-3 | 82 | 0.878 | 0 | 21 | 0.24 |
| business-finance-3 | 116 | 0.931 | 4 | 116 | 0.25 |
| policy-law-3 | 106 | 0.943 | 0 | 106 | 0.31 |
| culture-history-3 | 64 | 0.938 | 1 | 64 | 0.15 |

Of the 29 URLs flagged across the five reports, 10 were fetched with status `ok` during the run (bot walls that block the audit's plain fetch but not the run's Jina rung, and pages moved since; the run folders hold the text) and 19 were already unfetchable during the run: they appear in the reports' source tables as `UNFETCHABLE` or `SKIPPED-ROBOTS` rows (paywalled OUP and JAMA articles, congress.gov, finra.org, CanLII under robots, a guessed SCC item id) and were never quoted. The audit counts every URL in a report's source list, so those declared rows lower the skill's validity rate even though the report marks them. None is an invented citation. Per-question detail:
- technology-3: dl.acm.org (unfetchable, HTTP 403)
- science-health-3: academic.oup.com (unfetchable, HTTP 403); academic.oup.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); jamanetwork.com (unfetchable, HTTP 403); pmc.ncbi.nlm.nih.gov (unfetchable, HTTP 200); www.ebi.ac.uk (unfetchable, HTTP 404)
- business-finance-3: www.congress.gov (unfetchable, HTTP 403); www.congress.gov (unfetchable, HTTP 403); www.finra.org (unfetchable, HTTP 403); www.finra.org (unfetchable, HTTP 403); www.ftc.gov (possibly-fabricated, HTTP 404); www.investor.gov (possibly-fabricated, HTTP 404); www.investor.gov (possibly-fabricated, HTTP 404); www.sipc.org (possibly-fabricated, HTTP 404)
- policy-law-3: decisions.scc-csc.ca (unfetchable, HTTP 404); policyintegrity.org (unfetchable, HTTP 403); www.canlii.org (skipped-robots, HTTP None); www.canlii.org (skipped-robots, HTTP None); www.casemine.com (unfetchable, HTTP 200); www.mondaq.com (unfetchable, HTTP None)
- culture-history-3: research.britishmuseum.org (possibly-fabricated, HTTP 404); www.ancient-origins.net (unfetchable, HTTP 403); www.athenapub.com (unfetchable, HTTP None); www.sciencedirect.com (skipped-robots, HTTP None)

**Misses.** Four rubric items failed in total and all four were recall failures at the search/extraction stage (a rule in a spec section the researcher had fetched; a companion recommendation on the same guideline page; a sentence adjacent to the passage a researcher extracted from a judgment). None was a writing failure once the coverage pass existed: every fact that was in the claim ledger and wanted by a rubric was recovered.

**Changes made during Stage B, with the measured effect** (details and dates in `progress.md` #35-#39):
1. Coverage list of verified central claims the report never used (`cite_check.py`): +0.11 on technology-3, +0.08 on business-finance-3.
2. Script-enforced length ceiling; writer self-check with `cite_check.py --no-network` before finishing: the separate 100-260k-token fix/trim passes disappeared; the writer still drafts long and cuts inside its own run (2,846 → 1,770 words on culture-history-3).
3. Mechanical cap of 4 central claims per source in the ledger: held per source but not per run while researchers fetched 7-8 sources against a target of 4 (central 100 and 86 on 09-04).
4. "Stop at the source target; never exceed 5" in the researcher prompt (culture-history-3 only): every researcher stopped at 4, central claims 59, verifier batches 9 (from 12-21), verification cost 0.97M (from 1.3-1.5M), compliance 1.00 with the coverage list already empty. Per-batch verifier cost was unchanged (about 110k tokens per 8 central claims), so the central-claim count is the cost lever.
5. Adjacent-rule extraction instruction for specs, guidelines and regulator pages: one recall miss in three post-fix questions versus three in two pre-fix questions; the one miss was on a judgment, which the rule did not name.

**Cost structure at `standard`:** research 420-870k tokens, verification 790k-1.5M (about half of every run), writing 210-530k; 1.5-2.6M per question; judging 50-63k Opus tokens per report. A subscription session limit was hit at roughly 3.5M Sonnet tokens per five-hour window on 2026-09-03 (twice) and 2026-09-04; the ledger survives killed agents and `eval/make_batches.py` relaunches only what is unchecked.

## Stage C: the Claude Code built-in `/deep-research` (workflow A), 2026-09-04 to 2026-09-05 and 2026-09-11

The built-in workflow (architecture described in `research/prior-art/README.md`; the script the harness persists on launch was identical between Claude Code 2.1.258 and 2.1.263 apart from its `meta` literal) was run from the session as `Workflow({name: 'deep-research', args: <question>})` on two of the five stable questions, each paired with the skill's run of the same question. Constants untouched (3 votes per claim, 2 refutations to kill, 15 fetch slots, 25 claims verified). The report is a mechanical Markdown rendering of the JSON the workflow returns, judged by the same Opus judge and rubric as the skill's report.

**Model.** The built-in script sets no model, so its agents inherit the session model. The 2026-09-04/05 run therefore ran on Claude Fable (established 2026-09-11 from the agent transcripts; recorded at the time as "harness default"). For the 2026-09-11 run a copy of the persisted script was given `model: "sonnet"` at its five `agent()` call sites and nothing else was changed, so both workflows generated with Sonnet as the protocol requires; a first launch that had inherited Fable was abandoned after 19 agents and is not counted.

| | culture-history-3: built-in (A) | skill (B) | technology-3: built-in (A) | skill (B) |
|---|---|---|---|---|
| Run | 2026-09-05, Fable agents, third attempt | 2026-09-04, v1.0 | 2026-09-11, Sonnet agents, one attempt | 2026-09-10, v1.1 + post-tag edits |
| Rubric passes | 7/12 | 12/12 | 7/12 | 11/12 |
| Compliance | **0.655** | **1.00** | **0.577** | **0.923** |
| Tokens, completing run | 1.51M (100 agents, 11.5 min; search and fetch replayed from cache) | 1.85M (16 agents, 56 min) | 4.65M (109 agents, 8.2 min, fresh) | 1.64M (15 agents, 39 min) |
| Tokens, all attempts | 7.95M over three attempts in three windows | 1.85M in one | 4.65M in one (a paused Fable launch not counted) | 1.64M in one |
| Sources fetched / claims / verified | 18 / 89 / 25 (23 confirmed, 2 refuted, 9 dropped for budget) | 64 / 158 / 158 | 26 / 120 / 25 (24 confirmed, 1 refuted, 8 dropped for budget) | 77 / 131 / 131 (60 central) |
| Report | 8 merged findings, caveats, open questions, refuted list | 1,770-word report with claim markers | 8 merged findings, caveats, open questions, refuted list | report with claim markers |
| `cite_audit.py`: URL validity | 1.00 (18 URLs) | 0.94 (64) | 1.00 (26) | 0.92 (77; the non-ok rows are bot-walled or declared-unfetchable pages) |
| `cite_audit.py`: sentence-shingle containment | 0.14 (43 citing sentences) | 0.15 (64) | 0.05 (21) | 0.07 (77) |

`eval/score.py` over the two paired questions: B − A = +0.345 and +0.346, mean +0.345, B wins 2 of 2 (n = 2, so no interval is reported). The same holds against the skill's later v1.1 run of culture-history-3 (1.00).

**What the built-in missed, and why.** On culture-history-3: the scripts-versus-languages distinction, the month of the discovery, the historiography of the priority dispute (its own caveat says those claims "were not captured"), hence one of the four requested elements, and a timeline; its 23 confirmed claims came 17 from one institution's pages and 4 from one author's primary texts. On technology-3 it is accurate on everything the RFC texts state (dates, predecessors, section numbers, the directive definitions, the split between RFC 9111, RFC 5861 and RFC 8246) and fails every item that needs a vendor or browser page (no browser or CDN deviation, no RFC 9213, no Authorization rule, deliverables 3 beyond Vary and 4 declared undelivered in its own caveat). The workflow's journal shows why: its search and fetch stages did reach two Cloudflare docs pages, two Fastly docs pages and two MDN pages (21 central claims between them, graded primary or secondary), but the extractors marked 81 of 120 claims central, 50 of those from `primary` sources, and only 25 are verified, ranked by importance, then source quality, then fetch order. All 25 slots went to IETF pages; no vendor or browser claim was ever voted on, and the synthesis uses confirmed claims only. Both baselines have the same shape: a fixed verify budget, not search or fetch, decides coverage. The skill batches every central claim to a verifier (60 of 60 on this question), which is where its token budget goes instead.

**Cost finding, updated.** A fresh built-in run is 100-110 agents. With agents on Fable (2026-09-04) it did not fit inside one subscription window: attempts 1 and 2 (3.74M and 2.70M tokens) died at the verify and synthesis steps, and attempt 3 completed only because the resume cache replayed the search and fetch stages; the two failed attempts cost 6.44M tokens for no report. With agents on Sonnet (2026-09-11) the fresh run completed in one window at 4.65M tokens in 8.2 minutes, so the per-window limit is not a fixed token count across models. Per completing run the built-in costs 2.5-2.8 times the skill's tokens for a fresh run (4.65M vs 1.64M) and delivers a compliance 0.35 lower on both questions. On 2026-09-05 the user stopped the baseline at one question (`progress.md` #41); the second question was added on 2026-09-11 (`progress.md` #53) once the skill was at v1.2, and the user closed the baseline at n = 2 for this round the same morning: both paired gaps are +0.345, both misses come from the same verify-cut mechanism, and a further question would cost about 4.6M tokens.

## Confirmation runs after the changes (skill v1.1), 2026-09-10

culture-history-3 twice more, same round-1 brief and the same round-2 angles as the 2026-09-04 run, so only the skill differed (`progress.md` #42 and #43). The morning run used a researcher prompt that named the per-angle central cap ("16"); the afternoon run used the same prompt with the number removed (the cap itself unchanged). Everything else, including the operator, the models and the question, was the same.

| | 2026-09-04 (v1.0, stop rule as an operator line) | 2026-09-10 a.m. (v1.1, cap named in the prompt) | 2026-09-10 p.m. (v1.1, cap stated without a number) |
|---|---|---|---|
| Sources (ok) | 64 (63) | 84 (79) | 67 (64) |
| Claims corrob./single/contra. | 48/107/3 | 64/69/7 | 53/83/3 |
| Central claims | 59 | 80 (three of six angles at exactly 16) | 63 (per angle 8-14, none at the cap) |
| Verifier batches | 9 | 11 (16 launched: 5 killed by a machine-side network error and rebuilt from the ledger) | 9 (none killed) |
| Generation tokens | 1.85M (16 agents) | 2.17M known (23 launched, 18 completed; the killed agents' usage is unknown) | 1.85M (16 agents), 1.90M with one presentation pass |
| Report words, first draft → final | 2,846 → 1,770 | 2,241 → 1,732 | 1,955 → 1,620 (1,790 after the pass) |
| Citation checks | 158/158 quotes, 0 errors, 0 unused central | 140/140, 0 errors, 0 unused central | 139/139, 0 errors, 0 unused central |
| URL health | 54 LIVE / 7 ARCHIVED-ONLY / 1 DEAD / 1 UNKNOWN | 71 / 2 / 0 / 6 | 61 / 3 / 0 / 0 |
| Judge | 12/12, compliance 1.00 | 12/12, compliance 1.00 (first pass, no coverage pass) | 11/12, 0.966 first pass; 12/12, 1.00 after one presentation pass |
| `cite_audit.py`: URL valid / flagged / containment | 0.938 / 1 / 0.15 | 0.94 / 0 / 0.14 | 0.97 / 1 (a council archive URL whose host failed DNS; registered as possibly-fabricated, not cited) / 0.20 |
| Wall clock | 56 min | 75 min incl. about 17 min of outage and restart | 45 min (51 with the pass) |

Compliance held across all three runs and the 2026-09-04 judge's one criticism (low-grade corroborating sources) did not recur: in both v1.1 runs almost every fetched source was graded by the agent that registered it (75 of 79, then 58 of 64 with the six stragglers being exploratory fetches never used as evidence) and the report's confidence column read the grades. The afternoon run's one first-pass failure was a presentation item, the dated timeline the question asks for: the operator's writer fill did not request it (the morning fill had, by hand), the writer did not act on the brief's line about it, and one 46k-token presentation pass with no new retrieval (a cited timeline table built from claims already in the ledger) brought the report to 12/12. Fact recall and citation support did not move between the runs.

Cost is the finding. Every researcher stopped at 4 sources in all three runs, so the sources per angle were the same; what moved was how many claims researchers marked central. With the cap named in the prompt, three of six angles registered exactly 16 and the run cost 17% more on known tokens (more in truth, since five killed verifiers went uncounted). With the number removed, the central count fell back to the stop-rule level (63 against 59), verification to 9 batches, and the run cost the same 1.85M as on 2026-09-04. Per-batch verifier cost was about 116k tokens in all three runs, so the central count is the cost lever, the mechanical cap is a backstop that never bound in the afternoon run (highest angle 14), and the sentence announcing a number acted as a target. The prompt states the cap without a number; the default cap stays 16, env-overridable.

The other v1.1 changes behaved as designed in both runs: `--round` on every registration left no stray claims for the final batch build (0 both times); the same-author independence rule was applied by four verifiers in the morning and three in the afternoon (Robinson's pieces on The Past, OUPblog, Open Book Publishers and as Wikipedia's own source were declined as mutual corroboration; a LibreTexts page bylined by the British Museum was declined as independent of the Museum); the outline-with-budgets rule cut the writer's overshoot from +90% to +49% and then +30% without removing draft-then-cut; no menu-only page reached the ledger. The afternoon run also reached more primary texts (Wilson 1803 on Article 16, Young's 1823 *Account*, Budge 1905 and 1913, the Andrews/BM 1985 translation of the decree, the BM collection record via Wayback, a peer-reviewed conservation abstract) and its three contradictions are all real disagreements between graded sources over a date or a count (19 vs "likely 15" July 1799; 4 vs 16 plates in the *Lettre*; June vs July 1802 for the Museum gift).

The sentence-shingle containment metric is weak for both workflows (prose paraphrases its source), which is why the skill also checks its verbatim quotes inside the ledger (778/778 in the pilot, 140/140 and 139/139 in the confirmation runs). It is reported because it is the protocol's step-5 metric and applies equally to a report with no ledger.

## Fuller pilot, second to fourth domains: technology-3, science-health-3 and policy-law-3 on skill v1.1, 2026-09-10 evening to 2026-09-11

One `standard` run of technology-3 (HTTP caching semantics) with skill v1.1 plus the two post-tag edits of `progress.md` #44 (the writer prompt gives any presentation element the question asks for its own outline section; `grade --published ""` clears a wrong date). Round-1 brief copied verbatim from the 2026-09-03 run, so only the skill version changed; round 2 re-decomposed from the round-1 gaps (two angles: browser heuristics and bfcache, CDN stale handling and spec edges). The writer fill carried no operator line about presentation, on purpose (`progress.md` #45).

| | 2026-09-03 (v1.0 before any fix) | 2026-09-10 evening (v1.1 + #44) |
|---|---|---|
| Sources (ok) | 61 (61) | 77 (73; 4 unfetchable: three Crossref API lookups, one chromestatus page) |
| Claims corrob./single/contra. | 69/53/1 | 45/84/2 |
| Central claims | 85 | 60 (46 + 14; per angle 6-14, none at the cap) |
| Verifier batches | 11 | 8 (none killed) |
| Research / verification / writing tokens | about 0.42M / 0.79M / 0.29M | 0.62M / 0.84M / 0.18M |
| Generation tokens | 1.50M (16 agents) | 1.64M (15 agents), all known |
| Report words, first draft → final | not recorded → 1,798 | 1,790 → 1,510 |
| Citation checks | 123/123 quotes, 0 errors | 131/131 quotes, 127 citations to 48 sources, 0 errors, 6 central claims unused (duplicates of facts stated via a mirror host of the same RFC) |
| URL health | 57 LIVE / 4 DEAD | 66 LIVE / 0 DEAD / 7 UNKNOWN (archive lookup failed) |
| Judge | 9/12 → 10/12 after a coverage pass (0.77 → 0.88) | **11/12, weighted 0.923, first pass, no coverage pass** |
| `cite_audit.py`: URL valid / flagged / containment | 0.984 / 0 / 0.10 | 0.92 / 0 / 0.07 |
| Wall clock | about 2 h incl. an outage | 39 min |

What moved: compliance rose from 0.88 (after a 140k coverage pass) to 0.923 on the first pass, the run took a third of the wall clock, and the cost is level with the v1.0 run despite a second round-2 angle (the 2026-09-03 run had 85 central claims and 11 verifier batches; this one 60 and 8, at about 105k per batch). The presentation item that failed in 2026-09-03 passed: the writer's outline named a directive-definitions table as the presentation element the question asks for and gave it its own section and budget, with no operator line in the fill, which is what the #44 prompt rule was for. The one failure is the same recall item as on 2026-09-03: a normative rule in RFC 9111 that sat on a fetched page (the RFC was registered three times, from three mirror hosts) and was never extracted as a claim, so no writer pass could have added it; recorded as a recall failure of the adjacent-rule class, no retrieval added after judging. The judge also noted two internal inconsistencies of emphasis (a SHOULD versus "encouraged" for heuristic freshness; Chrome's bfcache change stated as settled in the table and as rolling out in the body).

Also observed: the URL dedup does not see mirror hosts (rfc-editor, httpwg, datatracker), so the same RFC appears up to three times in the sources list and verifiers had to apply the same-author rule to mirrors; the same-author rule was applied three times (an RFC co-author's vendor blog, a Google-authored draft against a Chromium thread, RFC mirrors); two contradictions were real (a "proprietary to Fastly" claim against the 2001 W3C edge-architecture note; a Firefox explanation retracted in its own source's editor's note); one quote overreach was flagged by a verifier; and the new `grade --published ""` clear was used once, on a placeholder date an agent reported itself.

### science-health-3, the same evening

One `standard` run of science-health-3 (vitamin D, falls and fractures) with the same skill plus the two `progress.md` #46 edits (RFC-mirror folding in the ledger; a researcher-prompt line to scan a specification's section list). Round-1 brief and round-2 angles copied verbatim from the 2026-09-03 run. At the user's request round 1 ran in parallel and verification mostly one agent at a time, to stay clear of the subscription window's limit (`progress.md` #47).

| | 2026-09-03 (v1.0 before any fix) | 2026-09-10 evening (v1.1 + #44 + #46) |
|---|---|---|
| Sources (ok) | 103 (94) | 85 (70; 15 paywalled pages unfetchable, listed but not cited) |
| Claims corrob./single/contra. | 76/47/2 | 45/74/0 |
| Central claims | 91 | 64 (47 + 17; per angle 5-14, none at the cap) |
| Verifier batches | 13 | 9 (none killed) |
| Research / verification / writing tokens | 0.73M / 1.34M / 0.17M + 0.10M fix pass + 0.26M trim pass | 0.73M / 1.07M / 0.15M + 0.04M coverage pass |
| Generation tokens | 2.61M (22 agents) | 1.95M before the pass, 1.99M with it (16 agents, all known) |
| Report words, first draft → final | not recorded → 1,790 | 1,969 → 1,478 (1,500 after the pass) |
| Citation checks | 126/126 quotes, 0 errors | 119/119 quotes, 77 citations to 22 sources, 0 errors, 0 unused central |
| URL health | 4 ARCHIVED-ONLY among 94 | 63 LIVE / 0 DEAD / 7 UNKNOWN |
| Judge | 11/12, 0.96, after a fix pass and a trim pass | 10/12, 0.893 first pass; **11/12, 0.964** after one coverage pass |
| `cite_audit.py`: URL valid / flagged / containment | 0.878 / 0 / 0.24 | 0.81 / 0 / 0.65 |
| Wall clock | about 2 h | 79 min (95 with the pass), verification mostly sequential |

Same final score at 24% lower cost, and the same single miss in both runs: the grade and population of the intervention a guideline body recommends instead of vitamin D, which sits on a page neither run fetched (both fetched pages refer to it in passing). Two things differed from the other domains: the first-pass score was lower because two rubric facts (a trial's dose arms; the alternative intervention) were in the ledger as `supporting` claims, which the writer's coverage list does not show (it lists unused central claims only), so one 36k coverage pass with no new retrieval lifted the score; and the writer's overshoot was +31%, back at the culture-history-3 level. The sequential mode cost no tokens and roughly 40 minutes of wall clock, and no agent was killed. Candidates recorded for the next change round: the coverage list should also name unused supporting claims that carry a number, a grade or a recommendation; the fetch gate should recognise Wiley's cookie wall (two "Cookies Turned Off" stubs were registered as `ok`); a guideline angle should fetch a companion statement that a fetched page names. The same-author rule again refused investigator press releases and co-authored commentaries as corroboration, which is why 74 claims stayed single-source: trial-specific figures often exist only in the investigators' own outputs.

### policy-law-3, after midnight

One `standard` run of policy-law-3 (judicial deference to agency statutory interpretation: US, Canada, UK) with the same skill plus the `progress.md` #48 edits (a supporting-claim coverage list in the citation script; Wiley's cookie wall in the fetch gate; a companion-statement line in the researcher prompt). Round-1 brief and round-2 angles copied verbatim from the 2026-09-04 run; parallel execution on a fresh window (`progress.md` #49).

| | 2026-09-04 (v1.0 with the central cap, no stop rule) | 2026-09-10/11 (v1.1 + #44 + #46 + #48) |
|---|---|---|
| Sources (ok) | 106 (101) | 90 (80; 8 unfetchable, 2 robots-skipped) |
| Claims corrob./single/contra. | 74/101/2 | 48/73/0 |
| Central claims | 86 | 55 (41 + 14; per angle 6-12, none at the cap) |
| Verifier batches | 11 plus rebuilds after a session-limit kill | 8 (none killed) |
| Research / verification / writing tokens | about 0.75M known / 1.24M / 0.33M | 0.83M / 0.93M / 0.21M + 0.04M fix pass |
| Generation tokens | 2.32M known (19 agents + 2 killed) | 2.01M (15 agents, all known) |
| Report words, first draft → final | 3,401 → 1,796 | 2,216 → 1,702 (1,708 after the pass) |
| Citation checks | 177/177 quotes, 0 errors | 121/121 quotes, 128 citations to 50 sources, 0 errors, 0 unused central; 23 unused supporting listed, 2 added |
| URL health | not comparable (before the UNKNOWN state) | 67 LIVE / 12 ARCHIVED-ONLY / 1 DEAD |
| Judge | 11/12, 0.897 | 10/12, 0.828 first pass; **11/12, 0.897** after one fix pass |
| Wall clock | 98 min | 44 min (66 with the pass) |

Same final score at 13% lower cost, with the same single miss in both runs: the passage of the judgment that bounds the holding (which deferential standards survive for agency factfinding and policy) sits in the fetched slip opinion and was extracted as a claim in neither run, although three prompt rules now ask for every holding and carve-out in cited sections. The first-pass miss that did not recur from 2026-09-04 was a writer inversion (a litigant's burden stated backwards against the ledger's own claims), fixed in one 39k pass with no new retrieval. The new supporting-claim coverage list surfaced two rubric-relevant facts on its first use. The audit's five "possibly fabricated" flags were all pages fetched live and `ok` in the ledger, so the flag measured that night's HEAD and archive lookups. Candidates recorded: a question-coverage check before writing (for each numbered part of the question, which claims answer it), since the remaining misses in two domains are passages on fetched pages that no prompt rule reached; and BAILII's block page as a gate marker.

### business-finance-3, the next night (2026-09-11)

One `standard` run of business-finance-3 (FDIC deposit insurance against SIPC customer protection) with the same skill plus the `progress.md` #50 edits (the Anubis block page in the fetch gate; the writer's outline opens with a question-coverage table). Round-1 brief copied verbatim from the 2026-09-04 run; round 2 re-decomposed from the round-1 state, as on 2026-09-04, and the re-decomposition lost one hypothesis line (see below). Prompts filled by the new `eval/fill_prompts.py`. The user paced the launches in waves of five agents with two holds between them (`progress.md` #51).

| | 2026-09-04 (v1.0 with the central cap, no stop rule) | 2026-09-11 (v1.1 + #44 + #46 + #48 + #50) |
|---|---|---|
| Sources (ok) | 116 (110) | 75 (73; 2 guessed URLs registered possibly-fabricated, uncited) |
| Claims corrob./single/contra. | 99/95/0 | 66/103/0 |
| Central claims | 100 | 73 (47 + 26; per angle 10-15, none at the cap) |
| Verifier batches | 12 plus rebuilds after a session-limit kill | 10 (none killed) |
| Research / verification / writing tokens | about 0.9M known / not separable / about 0.3M + coverage pass | 0.68M / 0.97M / 0.22M |
| Generation tokens | 2.10M known (25 agents + 6 killed) | 1.87M (17 agents, all known) |
| Report words, first draft → final | not recorded → 1,799 | 2,149 → 1,567 |
| Citation checks | 194/194 quotes, 0 errors | 169/169 quotes, 154 citations to 57 sources, 0 errors, 0 unused central; 39 unused supporting listed, 3 added |
| URL health | 86 LIVE / 15 ARCHIVED-ONLY / 3 DEAD / 6 UNKNOWN | 64 LIVE / 0 DEAD / 9 UNKNOWN |
| Judge | 11/12, 0.92 first pass; 12/12, 1.00 after a coverage pass | **11/12, 0.92 first pass**; no pass possible (the miss is in no claim) |
| `cite_audit.py`: URL valid / flagged / containment | 0.931 / 4 / 0.25 | 0.947 / 0 / 0.23 |
| Wall clock | 102 min | 74 min, of which about 25 min were holds for the user |

Same first-pass score at 11% lower cost, no agent killed, and the question-coverage table did what the #50 rule asked: from the prompt alone the writer opened its outline with twelve rows (the four numbered parts split by regime plus the brief's three sub-questions), marked nine full with claim ids and three as gaps before any prose, put the gaps into "What this report could not find" and named them in its final message. None of the three gaps was a rubric item, so no targeted pass was warranted. The one miss is a contrast the question does not name and the rubric expects (the FDIC's status as an independent government agency against SIPC's non-profit, non-governmental status); the phrase is on six fetched pages and in no claim, so it is the adjacent-passage class once more, and the coverage table's rows (question parts and brief sub-questions) could not reach it. The paired comparison on this question is weaker than the other four: the 2026-09-04 round-2 brief carried "FDIC's own pages state it is an independent agency" as a hypothesis line, its researcher extracted it and the report opened with it; tonight's re-decomposed round-2 brief did not carry the line. The coverage pass that took the 2026-09-04 run to 1.00 added facts that were already in its ledger.

Also observed: a round-2 researcher registered 6 content-bearing sources against the target of 4 (never exceed 5), the first overshoot in the v1.1 runs (it kept a statute section fetched under a misleading title and reported the overshoot itself); the per-source central cap demoted intended-central claims on three sources shared between angles, and each researcher reported the demotion correctly instead of working around it; verification corroborated 66 of 73 central claims, mostly from statute, regulation and Federal Register text on law.cornell.edu, ecfr.gov, congress.gov and federalregister.gov, and left the rest single-source with the search trail noted (secondary pages that restate the agency's own page, a Unified Agenda timetable field no other page quotes); the same-author rule was applied three times (a rewrite whose footnote cites the FDIC page, a CNN piece quoting CFPB, a law-firm sentence tracking FDIC's wording).

Across the five domains run on v1.1 (culture-history-3 three times, technology-3, science-health-3, policy-law-3, business-finance-3): compliance 0.90-1.00 as judged (0.79-1.00 after the policy-law-3 correction in the judge-reliability section below) for 1.6-2.0M Sonnet tokens per `standard` question (v1.0 on the same briefs: 0.88-1.00 for 1.5-2.6M), no agent killed since the evening of 2026-09-10, no fabricated URL in the ledger, every quote verified at registration, and each remaining miss a fact on a fetched page that no researcher extracted in full (where each sits: `decisions/adjacent-passage-class.md`).

## Judge reliability (model-only check, 2026-09-11)

The protocol's calibration step (ten reports hand-graded by a person; `eval/README.md` step 6) has not been done. In its place, two checks that need no human grades, reported as what they are:

1. **Quote check** (`eval/judge_quote_check.py`, model-free). Every Opus verdict quotes the report passage that decided it; the script tests whether each quoted span occurs in the report. Over the 120 items of the ten-report calibration pack (both built-in reports and eight skill reports across the five domains and two skill versions): no pass rests on a quote that is absent from the report; 81 items match outright, 10 passes have one paraphrased fragment beside a matched quote, 18 items carry no quote (presentation items and fails that describe an absence), 11 fails quote the report's own admission of a gap.
2. **Second judge and adjudication** (`eval/judge_agreement.py`). Ten Sonnet 5 judges graded the same reports blind with the same prompt (678k tokens). Agreement with Opus: 113 of 120 items, Cohen's kappa 0.79. The seven disagreements and all 17 shared fails were adjudicated by reading the report passages: five disagreements went to Opus, two to Sonnet, and every shared fail was confirmed. Against the adjudicated grades Opus has sensitivity 1.00 and specificity 0.91 (two lenient passes in 120, no wrong fail); Sonnet 0.98 and 0.86.

The two lenient passes are the same item in two reports: policy-law-3 r4 (weight 3), whose second half (a specific point about when a Chevron-era holding may be overruled) is absent from the report; Opus wrote "not spelled out" in its justification and passed anyway. The same half is absent from the other two judged policy-law-3 reports, so every policy-law-3 compliance in the tables above carries that pass: **0.897 as judged is 0.793 adjusted, on v1.0 and on the current skill alike**, and the five-domain range is 0.79-1.00 adjusted rather than 0.90-1.00. The paired comparison on that question is unchanged. No other lenient pass surfaced; the check is disagreement-driven, so a pass both judges share and both got wrong would not be caught by it.

## Post-cutoff questions on skill v1.2 (2026-09-11): technology-1 and science-health-2

Every run above is on the five `stable` questions. Ten of the fifteen questions are `post-cutoff` (facts that postdate the generator's training and must come from the web). Two ran on 2026-09-11 on skill v1.2 unchanged: a technology question about a schedule set in 2025 with steps that landed in 2026 (primary sources: standards-body records, CA documentation and IETF pages), and a public-health question about a national elimination-status determination pending in 2026 (primary sources: CDC surveillance and coverage pages, PAHO statements and a regional framework document, state health department releases). The second was chosen for the freshness traps its design carries: a surveillance count revised weekly that needs an as-of date, a review date that an agency moved after first announcing it, and three status statements (a region's, a trigger country's, and the country under review) that stale answers conflate.

| | technology-1 (post-cutoff) | science-health-2 (post-cutoff) | technology-3 (stable, the day before, same skill) |
|---|---|---|---|
| Sources / claims / central | 63 / 105 / 50 | 47 / 122 / 44 | 77 / 131 / 60 |
| Agents (killed) | 14 (0) | 13 (0) | 15 (0) |
| Generation tokens | **1.50M** | **1.46M** | 1.64M |
| Citation checks | 105/105 quotes, 128 citations, 0 errors | 122/122 quotes, 86 citations, 0 errors | 131/131, 0 errors |
| `cite_audit.py`: validity / containment | 0.95 / 0.30 | 0.92 / 0.47 | 0.92 / 0.07 |
| Compliance | 0.846 first pass, **0.923** after one coverage pass | **0.929** first pass (no pass) | 0.923 first pass |
| Wall clock | 43 min incl. the pass | 45 min | 39 min |

On technology-1 the two first-pass misses were writer compression of facts already in corroborated claims (a product's general-availability date and two scheduled dates), restored by one writer pass without new retrieval; the remaining miss is a date on a fetched page that no researcher extracted. On science-health-2 the one miss is a threshold sentence on the very CDC page from which nine central claims were registered, which no researcher extracted because neither the question nor the brief named it (the adjacent-passage class again; recorded as a recall failure, no retrieval added after judging). No freshness failure occurred on either question: every dated fact came from a primary page fetched during the run, the moved review date appears only as superseded history, the surveillance count carries its as-of date and a provisional flag, the three status statements are kept distinct, and the deaths a state health department had announced but the national confirmed-only line had not yet counted were reported with the lag explained, because the round-2 brief asked for state sources as the question does. No needed host failed to fetch (the JavaScript-heavy CDC pages came through the Jina reader rung). Two post-cutoff questions stand at 0.923 and 0.929 for 1.46-1.50M tokens, inside the stable-question range and at its cheap end; the other eight post-cutoff questions are unrun.

## Experiment after the pilot: a gap hunter for the adjacent-passage class (2026-09-11)

Every rubric miss on the current skill is a fact on a fetched page that no researcher extracted in full (in one case, science-health-3, the sentence was registered as a supporting claim but the item's grade and population parts were not; found 2026-09-11 afternoon, `decisions/adjacent-passage-class.md`, which locates all seven misses relative to the registered quotes: five sit next to registered quotes on pages at the per-source central cap and are definitional or threshold sentences, one is a far section of a judgment, one is on verifier-added pages only). Because each run caches its fetched page text, a fix could be tested offline: a "gap hunter" agent that runs once after research with the question, the brief, the claims list and grep access to the raw cache, and lists uncovered statements with verbatim quotes (`eval/experiments/gap-hunter.md`; variant 2, `gap-hunter-v2.md`, first writes the rubric a domain expert would use, then hunts for its items). Eight Sonnet agents over the four current-skill run folders, 110-156k tokens each (about 7% of a run). Result: 56 candidate facts, 55 quoted verbatim from the cache, several of real value (a trial absent from a ledger, a predecessor limit the writer had declared missing, an undated cited RFC), but only 1 of the 4 known rubric misses caught by variant 1 and 0 of 4 by variant 2. The checklist, not the reading, is the bottleneck: neither the question, the brief nor a model-written expert rubric produced the specific adjacent rule the human rubric author held essential. Not applied to the skill; recorded in `decisions/backlog.md` as an optional completeness stage for the `deep` preset.

## What the pilot measured against `skill/DESIGN.md` §7

1. False refutation: the built-in refuted 2 of 25 claims by 0-3 and 1-2 votes; both refuted claims were then re-asserted in its own findings (judge-recorded contradictions). The skill's "default unverified" produced 0 false contradictions in 778 claims (8 contradictions, all real source disagreements over dates or counts).
2. Second round: added 14-34 central claims per question (14, 25, 31, 34, 23 in run order; 23 of 59 on culture-history-3, including the primary texts), so it stays at `standard`.
3. Fetch success by chain rung: recorded per run in `sources.json` (`fetch_method`, `attempts`); across the five runs (450 registered sources): 62% raw-http, 26% Jina reader, 3% keyless API (Wikipedia, Crossref, arXiv), 3% Wayback, under 1% urltomarkdown, 4% unfetchable, 1 possibly-fabricated URL (an item id a researcher guessed), 1 robots-skipped.
4. Quote containment failure of model-reported quotes: 0 of 778 at the ledger (the script rejects a non-verbatim quote at registration, so the failure shows up as retries in researcher transcripts, not in the ledger).
5. Fetch ≥ verify allocation: not achieved (verification stayed about half of every run) until the source-target stop rule; then research 601k vs verification 971k on culture-history-3 with no loss of recall.

## Changes applied after the pilot (skill v1.1, 2026-09-10; confirmation run above)
Applied in `progress.md` #42, contract first (`skill/deep-research/reference/contracts.md` v1.1): a per-angle central cap in the ledger (16 = source target 4 × per-source cap 4, env-overridable) with the source-target stop rule moved into the researcher prompt; `--round` accepted by `claim add --from-json` so a claim carries its researcher's round, not its source's; verifiers grade the sources they add and the writer's confidence rule reads the grade; an author-level independence note for verifiers; a nav-only fetch gate for menu pages that pass the length gate; the writer's length target stated first with a per-section word budget drafted to; the adjacent-rule extraction instruction extended to judgments; a `claim unevidence` command as the ledger's one undo. After the morning confirmation run the per-angle figure was removed from the researcher prompt text; the afternoon re-test confirmed that the number, not the cap, had raised the central count (see above). v1.1 was tagged at that state.
