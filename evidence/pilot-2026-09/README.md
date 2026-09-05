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

Every URL flagged here was fetched with status `ok` during its run (the run folders hold the text); the flags are bot walls and pages that have since moved, not invented citations. Per-question detail:
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

The sentence-shingle containment metric is weak for both workflows (prose paraphrases its source), which is why the skill also checks its verbatim quotes inside the ledger (778/778). It is reported because it is the protocol's step-5 metric and applies equally to a report with no ledger.

## What the pilot measured against `skill/DESIGN.md` §7

1. False refutation: the built-in refuted 2 of 25 claims by 0-3 and 1-2 votes; both refuted claims were then re-asserted in its own findings (judge-recorded contradictions). The skill's "default unverified" produced 0 false contradictions in 778 claims (8 contradictions, all real source disagreements over dates or counts).
2. Second round: added 14-34 central claims per question (14, 25, 31, 34, 23 in run order; 23 of 59 on culture-history-3, including the primary texts), so it stays at `standard`.
3. Fetch success by chain rung: recorded per run in `sources.json` (`fetch_method`, `attempts`); across the five runs (450 registered sources): 62% raw-http, 26% Jina reader, 3% keyless API (Wikipedia, Crossref, arXiv), 3% Wayback, under 1% urltomarkdown, 4% unfetchable, 1 possibly-fabricated URL (an item id a researcher guessed), 1 robots-skipped.
4. Quote containment failure of model-reported quotes: 0 of 778 at the ledger (the script rejects a non-verbatim quote at registration, so the failure shows up as retries in researcher transcripts, not in the ledger).
5. Fetch ≥ verify allocation: not achieved (verification stayed about half of every run) until the source-target stop rule; then research 601k vs verification 971k on culture-history-3 with no loss of recall.

## Queued changes (not applied; after this pilot)
Per-angle or per-run central cap in the ledger; `--round` on `claim add --from-json` (claims on an earlier round's source were stored with that round and missed a batch build); verifiers grade the sources they add and the writer's confidence rule reads grades; author-level independence check; a "no sentences" gate for nav-only pages that pass the length gate; the writer prompt's length target before its structure did not stop draft-then-cut; extend the adjacent-rule instruction to judgments; a `claim unevidence` command.
