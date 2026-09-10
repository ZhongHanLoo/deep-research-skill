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

## Stage C: the Claude Code built-in `/deep-research` (workflow A), 2026-09-04 to 2026-09-05

The built-in workflow (Claude Code 2.1.258; architecture described in `research/prior-art/README.md`) was run from the session as `Workflow({name: 'deep-research', args: <question>})` on culture-history-3, the same question as the skill's freshest run.

| | Built-in (A) | Skill (B) |
|---|---|---|
| Rubric passes | 7/12 | 12/12 |
| Compliance | **0.655** | **1.00** |
| Tokens, completing run | 1.51M (100 agents, 11.5 min; search and fetch stages replayed from cache) | 1.85M (16 agents, 56 min) |
| Tokens, all attempts | **7.95M** over three attempts in three windows | 1.85M in one |
| Sources fetched / claims / verified | 18 / 89 / 25 (23 confirmed, 2 refuted, 9 dropped for budget) | 64 / 158 / 158 (48 corroborated, 107 single-source, 3 contradicted) |
| Report | 8 merged findings, caveats, open questions, refuted list (JSON, rendered to Markdown mechanically) | 1,770-word report with claim markers |
| `cite_audit.py` (same yardstick): URL validity | 1.00 (18 URLs) | 0.94 (64 URLs; 4 unreachable at audit time, all fetched live during the run) |
| `cite_audit.py`: sentence-shingle containment | 0.14 (43 citing sentences) | 0.15 (64) |

`eval/score.py` on the one paired question: B − A = +0.345 (n = 1, so no interval). The built-in missed: the scripts-versus-languages distinction, the month of the discovery, the historiography of the priority dispute (its own caveat says those claims "were not captured"), hence one of the four requested elements, and a timeline. Its 23 confirmed claims came 17 from one institution's pages and 4 from one author's primary texts; verification of the top 25 of 89 claims with three votes each is where its budget goes.

**Cost finding.** A fresh built-in run (about 100 agents, 3.7M tokens) did not fit inside one subscription window on this account: attempts 1 and 2 (3.74M and 2.70M tokens) died at the verify and synthesis steps on the session limit; attempt 3 completed only because the workflow resume cache replayed the search and fetch stages. The two failed attempts cost 6.44M tokens for no report. On this evidence the user stopped the baseline at one question (decision 2026-09-05, `progress.md` #41): each further question would cost about two windows and 5-6M tokens, and the design changes queued from Stage B will change the skill before a fuller pilot.

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

## What the pilot measured against `skill/DESIGN.md` §7

1. False refutation: the built-in refuted 2 of 25 claims by 0-3 and 1-2 votes; both refuted claims were then re-asserted in its own findings (judge-recorded contradictions). The skill's "default unverified" produced 0 false contradictions in 778 claims (8 contradictions, all real source disagreements over dates or counts).
2. Second round: added 14-34 central claims per question (14, 25, 31, 34, 23 in run order; 23 of 59 on culture-history-3, including the primary texts), so it stays at `standard`.
3. Fetch success by chain rung: recorded per run in `sources.json` (`fetch_method`, `attempts`); across the five runs (450 registered sources): 62% raw-http, 26% Jina reader, 3% keyless API (Wikipedia, Crossref, arXiv), 3% Wayback, under 1% urltomarkdown, 4% unfetchable, 1 possibly-fabricated URL (an item id a researcher guessed), 1 robots-skipped.
4. Quote containment failure of model-reported quotes: 0 of 778 at the ledger (the script rejects a non-verbatim quote at registration, so the failure shows up as retries in researcher transcripts, not in the ledger).
5. Fetch ≥ verify allocation: not achieved (verification stayed about half of every run) until the source-target stop rule; then research 601k vs verification 971k on culture-history-3 with no loss of recall.

## Changes applied after the pilot (skill v1.1, 2026-09-10; confirmation run above)
Applied in `progress.md` #42, contract first (`skill/deep-research/reference/contracts.md` v1.1): a per-angle central cap in the ledger (16 = source target 4 × per-source cap 4, env-overridable) with the source-target stop rule moved into the researcher prompt; `--round` accepted by `claim add --from-json` so a claim carries its researcher's round, not its source's; verifiers grade the sources they add and the writer's confidence rule reads the grade; an author-level independence note for verifiers; a nav-only fetch gate for menu pages that pass the length gate; the writer's length target stated first with a per-section word budget drafted to; the adjacent-rule extraction instruction extended to judgments; a `claim unevidence` command as the ledger's one undo. After the morning confirmation run the per-angle figure was removed from the researcher prompt text; the afternoon re-test confirmed that the number, not the cap, had raised the central count (see above). v1.1 was tagged at that state.
