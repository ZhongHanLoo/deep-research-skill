# How deep-research agents are evaluated, and how a small team can compare two research workflows

Literature survey, compiled 2026-09-02. Scope: evaluation of web-only "deep research" agents that produce cited long-form reports; adjacent proxy benchmarks; citation/factuality evaluation; LLM-as-judge practice; efficiency metrics; and a lightweight protocol a single developer can run. Every fact is followed by its source URL in brackets. Items I could not confirm from a primary source are marked "unverified".

---

## Summary table of benchmarks

| Name | Year | #Tasks | What it measures | Scoring method | Runnable locally? | Notes |
|---|---|---|---|---|---|---|
| DeepResearch Bench (Du et al.) | 2025 | 100 PhD-level tasks, 22 fields | Report quality (RACE: comprehensiveness, insight, instruction-following, readability) + citation quality (FACT: citation accuracy, effective citations) | LLM judge; RACE is reference-relative with task-specific dynamic criteria; FACT scrapes cited URLs and judges support | Yes (Python; needs OpenAI/OpenRouter key + Jina key). Judge migrated from Gemini-2.5-Pro to GPT-5.5 | Human agreement 71.33% pairwise vs 68.44% human baseline. Leaderboard: Gemini-2.5-Pro DR 48.88, OpenAI DR 46.98, Perplexity DR 42.25 |
| DeepResearch Bench II | 2026 | 132 tasks (66 EN / 66 ZH), 22 domains | Information recall, analysis, presentation | 9,430 binary rubrics grounded in expert-written articles; Gemini-2.5-Pro judge, 50 rubrics/pass | Yes (CC-BY-NC-SA); ~$0.25 per task to judge | 91.75% accuracy vs human labels. Best system (o3) 45.4% overall; recall 40%, presentation 89% |
| DeepResearchGym | 2025 | Top 1,000 Researchy Questions | Key-point recall/contradiction, citation precision/recall, clarity, insightfulness | LLM judge (gpt-4.1-mini); ground-truth clicked documents | Yes; free reproducible search API over ClueWeb22 + FineWeb | Human/auto agreement 0.72-0.89; search latency <0.5 s |
| ResearchRubrics (Scale AI) | 2025 (ICLR 2026) | 101 prompts, 2,500+ rubrics, 9 domains | Factual grounding, reasoning soundness, clarity | Binary satisfied/not per rubric, weighted compliance; Gemini 2.5 Pro judge via LiteLLM | Yes (pip install; needs LiteLLM key; reports cost) | Gemini DR and OpenAI DR <68% compliance |
| Deep Research Bench (FutureSearch) | 2025, live | 89 instances (paper) -> 169 (leaderboard, Jun 2026), 8 task categories | Short-answer web research: find number, validate claim, compile dataset, etc. | Binary / recall / F1 / probability-difference per category; Gemini 2.5 Flash assists; offline RetroSearch corpus | Partially. Tasks and RetroSearch not fully public (unverified); public leaderboard reports cost per task | Top: Opus 4.6 (high) 0.553 at $0.53/task; Gemini 3 Flash (low) 0.498 at $0.10 |
| ResearcherBench (GAIR) | 2025 | 65 frontier-AI research questions, 35 subjects | Insight coverage (weighted expert rubrics), faithfulness, groundedness | LLM judge; claim extraction + URL scraping (Jina) + binary support | Yes (GitHub; OpenAI + Jina keys) | OpenAI DR coverage 0.70, faithfulness 0.84, groundedness 0.34 |
| LiveResearchBench (Salesforce) | 2025 (ICLR 2026) | 100 tasks, 7 domains, 3 settings (daily life, enterprise, academia) | Coverage, presentation, citation accuracy/association, consistency, depth (DeepEval) | Checklist (binary), pointwise error counting, pairwise with position-swap; GPT-5 + Gemini-2.5-Pro ensemble | Yes (GitHub, CC BY-NC-SA; needs OpenAI + Gemini keys) | 98.3% / 92.5% / 85.9% human agreement for presentation / depth / citation. Tasks are time-sensitive by design |
| ReportBench | 2025 | 100 prompts reverse-engineered from 678 arXiv surveys | Reference overlap with survey, factuality of cited and uncited statements | gpt-4o extraction; gemini-2.5-pro/flash majority vote | Yes (code/data released) | OpenAI DR cited-statement match 78.9%; Gemini DR 72.9% |
| DEER | 2025 (ICML 2026) | 50 tasks, 13 domains (from HLE questions) | 7 dimensions / 25 sub-dimensions / 101 rubric items + claim verification | GPT-5.2 judge with expert guidance; GPT-5-mini verifier | Yes (GitHub); ~$0.5-1.0 per report | Pearson 0.73 vs 0.81 human-human; OpenAI DR best at 6.50/10 |
| DRACO (Perplexity) | 2026 | 100 tasks, 10 domains, 3,934 criteria | Factual accuracy (52%), breadth/depth (22%), presentation (14%), citation quality (12%) | Task-specific rubrics; "capable judge model, low temperature" | Yes (HF dataset, MIT per dataset card; paper says CC BY-NC-ND, unverified which applies) | Best-system saturation ~71% |
| Dr. Bench | 2025 | 214 tasks, 10 domains | Semantic quality, topical focus, retrieval trustworthiness | Manually built reference bundles + LLM metrics | Release status unverified | DRAs beat search-augmented reasoning models |
| DeepResearchEval | 2026 | Auto-generated (count unverified) | Adaptive point-wise quality + active fact-checking without citations | LLM judge, web search verifier | Yes (GitHub) | Persona-driven task generation |
| Wiki Live Challenge | 2026 | 100 newest Wikipedia Good Articles | Writing quality (39 criteria) + factuality vs human article | LLM judge vs human reference | Yes (unverified) | Large gap to human GAs |
| MiroEval | 2026 | 100 tasks (70 text, 30 multimodal) | Synthesis rubrics, factuality, process audit | LLM judge + human verification | Yes (unverified) | Process quality predicts outcome |
| DRBench (enterprise) | 2025 | 100 tasks, 10 domains | Insight recall, factual accuracy, report quality over private + web data | Human-in-the-loop synthesis, LLM judge | Yes (unverified) | Enterprise-specific, not pure web |
| BrowseComp (proxy) | 2025 | 1,266 questions | Locating hard-to-find facts | Short answer vs reference (LLM grader) | Yes (data public; live web needed) | OpenAI DR 51.5%; explicitly excludes long answers |
| BrowseComp-Plus (proxy) | 2025 | 830 queries, 100K docs | Same, on fixed corpus; also search calls, evidence recall, citation accuracy | LLM grader | Yes (fixed corpus, reproducible) | GPT-5 55.9% -> 70.1% with Qwen3-Embedding-8B |
| GAIA (proxy) | 2023 | 466 questions, 3 levels | Tool-use assistant tasks | Exact-match short answers | Yes (300 public answers) | Humans 92% vs GPT-4+plugins 15% (2023) |
| Humanity's Last Exam (proxy) | 2025 | 2,500 questions | Expert-level closed-form knowledge | Exact match / MC | Yes | OpenAI DR 26.6% (Feb 2025); frontier ~59% by 2026; ~30% of chem/bio answers may be wrong |
| SimpleQA (proxy) | 2024 | 4,326 questions | Short-form factuality + calibration | LLM grader: correct / incorrect / not attempted | Yes | Perplexity DR 93.9% |
| WebWalkerQA (proxy) | 2025 | 680 QA pairs, 1,373 pages | Website traversal depth | GPT-4 CoT judge | Yes | Best ~37.5% |
| WebArena / Mind2Web (proxy) | 2023 | 812 / 2,000+ tasks | Web UI task completion | Functional correctness / step SR | Yes (self-host) | GUI action, not research |

---

## 1. Benchmarks specifically for deep-research report generation

### DeepResearch Bench (Du et al., 2025)
- 100 PhD-level research tasks crafted by domain experts across 22 fields; two frameworks, RACE (report quality) and FACT (retrieval/citation) [https://arxiv.org/abs/2506.11763].
- RACE: a judge LLM derives per-task dimension weights over Comprehensiveness, Insight/Depth, Instruction-Following, Readability (averaged over T trials), generates task-specific criteria, scores target and a high-quality reference report against the same criteria, and reports the relative score S(target) / (S(target) + S(reference)); isolated pointwise scoring was found "insufficiently discriminative" [https://arxiv.org/html/2506.11763].
- Human validation: 50 Chinese tasks, 4 agents, 3 expert annotators per task; RACE pairwise agreement 71.33% vs 68.44% human inter-agreement; human evaluation took ~1.5 h per query, 225 person-hours total [https://arxiv.org/html/2506.11763].
- FACT: judge LLM extracts statement-URL pairs, dedupes, fetches pages via Jina Reader, judges binary support; metrics are citation accuracy (share supported) and effective citations (supported pairs per task) [https://arxiv.org/html/2506.11763].
- Results: Gemini-2.5-Pro Deep Research 48.88 RACE, 81.44% citation accuracy, 111.21 effective citations; OpenAI DR 46.98 / 77.96% / 40.79; Perplexity DR 42.25 / 90.24% / 31.26; Grok Deeper Search 40.24 / 83.59% / 8.15; Claude-3.7-Sonnet with search reached 40.67 RACE [https://deepresearch-bench.github.io/] [https://arxiv.org/html/2506.11763].
- Runnable locally: Python 3.9+, OpenAI/OpenRouter key and Jina key; the repo has migrated the RACE judge from Gemini-2.5-Pro to GPT-5.5 and FACT to gpt-5.4-mini; human inter-annotator baseline listed as 68.78% [https://github.com/Ayanami0730/deep_research_bench]. Code/data CC-BY-4.0 [https://arxiv.org/abs/2506.11763].
- Caveat: a judge change alters absolute scores, so leaderboard numbers computed under different judges are not comparable (my inference).

### DeepResearch Bench II (2026)
- 132 tasks across 22 domains (66 English, 66 Chinese); 9,430 binary rubrics (~71/task) derived from 132 expert-written investigative articles with licence verification [https://arxiv.org/html/2601.08536].
- Three dimensions: information recall (~53 rubrics/task), analysis (~13), presentation (~6); Gemini-2.5-Pro judge, 50 rubrics per pass, task score = share passed; 91.75% accuracy and 89.57 F1 vs human annotations; ~$0.25 per task to evaluate [https://arxiv.org/html/2601.08536].
- Best model (OpenAI o3-based agent) 45.40% overall: recall 39.98%, analysis 49.85%, presentation 89.16% - i.e. presentation is nearly solved, recall is the bottleneck [https://arxiv.org/html/2601.08536]. Licence CC-BY-NC-SA 4.0 [https://arxiv.org/pdf/2601.08536].

### DeepResearchGym (2025)
- Open-source sandbox pairing a reproducible search API (ClueWeb22 + FineWeb, dense retriever + DiskANN) with an evaluation protocol extending Researchy Questions [https://arxiv.org/abs/2505.19253].
- Metrics: Key Point Recall and Key Point Contradiction vs ground-truth clicked documents; citation recall/precision with graded support (1.0 / 0.5 / 0.0); clarity and insightfulness via LLM judge (gpt-4.1-mini-2025-04-14); evaluated on top 1,000 Researchy Questions [https://arxiv.org/html/2505.19253].
- Human study on 210 queries: inter-annotator Cohen's kappa 0.87; auto-to-human agreement 0.72-0.89 across metrics; search latency under 0.5 s; system rankings consistent between Gym and commercial APIs, but per-query retrieval faithfulness was sensitive to search infrastructure [https://arxiv.org/html/2505.19253].

### ResearchRubrics (Scale AI, ICLR 2026)
- 101 prompts, 2,500+ expert rubrics, 9 domains, 2,800+ hours of human labour; complexity axes: conceptual breadth, logical nesting, exploration; Gemini DR and OpenAI DR under 68% compliance, mostly from missed implicit context and weak reasoning over retrieved information [https://scale.com/research/researchrubrics] [https://arxiv.org/abs/2511.07685].
- Scoring: each rubric Satisfied (1) / Not Satisfied (0); compliance = sum(weight x score) / sum(positive weights); judge is Gemini 2.5 Pro via LiteLLM; local run = pip install, download HF dataset, drop Markdown reports into agent_responses/, run evaluate_reports_batch.py; output JSONL includes cost [https://github.com/scaleapi/researchrubrics].

### Deep Research Bench (FutureSearch)
- Paper version: 89 task instances in 8 categories - Find Number (18), Find Dataset (12), Find Original Source (11), Validate Claim (12), Derive Number (10), Gather Evidence (9), Populate Reference Class (10), Compile Dataset (7); scoring is binary for number/source tasks, recall for dataset/evidence, F1 for compile/populate, absolute probability difference for Validate Claim; Gemini 2.5 Flash assists grading; RetroSearch is a frozen scraped-web store with Common Crawl fallback [https://arxiv.org/html/2506.06287].
- Trace analysis: hallucination 0.014-0.159 per step and "not the primary limiter"; repeated tool calls 0.044-0.293 per step; forgetting was the strongest predictor of failure (coef -0.843) [https://arxiv.org/html/2506.06287]. Top paper-era score: o3 at 0.51; ChatGPT-o3 beat dedicated "Deep Research" products [https://arxiv.org/html/2506.06287] [https://futuresearch.ai/deep-research-bench/].
- Live leaderboard (updated 2026-06-10, 169 tasks): Opus 4.6 (high) 0.553 at $0.53/task; Sonnet 4.6 (high) 0.549 at $0.46; GPT-5.5 (high) 0.540 at $0.36; Gemini 3 Flash (low) 0.498 at $0.10; scores averaged per category then overall [https://drb.futuresearch.ai/].
- "Effort paradox": higher reasoning effort often lowers DRB accuracy - GPT-5 49.6% (low) -> 48.1% (high) with +56% cost; Gemini 3 Flash 49.9% -> 47.9% with 3x cost; Claude 4.6 Opus the exception (+1.9 pts, 2x cost, 3x latency) [https://futuresearch.ai/effort-paradox/].
- Note: this benchmark scores short verifiable answers, not report prose; it is closer to a proxy than a report benchmark, but its task types (find source, validate claim) map well onto research sub-skills.

### ResearcherBench (GAIR, 2025)
- 65 frontier-AI research questions from lab discussions and interviews, 35 subjects, three types (technical details, literature review, open consulting); rubric assessment of insight quality plus factual assessment of faithfulness (citation accuracy) and groundedness (citation coverage) [https://arxiv.org/abs/2507.16280].
- Pipeline: Claude-3.7-Sonnet extracts insights that experts turn into weighted criteria (1-3); claims are extracted, cited URLs scraped (Jina), a judge gives binary support. Results: OpenAI DR coverage 0.7032 / faithfulness 0.84 / groundedness 0.34; Gemini DR 0.6929 / 0.86 / 0.59; Claude Research 0.6113; Perplexity DR 0.4800 / 0.85 / 0.56; Grok3 DeepSearch 0.4414 / 0.69 / 0.32 [https://github.com/GAIR-NLP/ResearcherBench].

### LiveResearchBench (Salesforce, ICLR 2026)
- 100 expert-curated tasks, 1,500+ hours of labour, 7 domains, 10 categories, designed to be user-centric, dynamic (needs fresh web data) and unambiguous; 17 systems evaluated [https://arxiv.org/abs/2510.14240].
- DeepEval protocols: checklist (binary) for presentation (10 fixed questions) and coverage (custom checklist per query); pointwise error-counting (10-100 scale) for consistency and citation; pairwise comparison with position-swap averaging for depth over five dimensions (granularity, insight, critique, evidence, density); judges GPT-5 and Gemini-2.5-Pro, multi-provider grading recommended [https://github.com/SalesforceAIResearch/LiveResearchBench].
- Human agreement: presentation 98.3%, depth 92.5%, citation traceability 85.9%; Claude 4 Sonnet as judge showed "inconsistent and low agreement"; single holistic ratings fell below 60% agreement [https://arxiv.org/html/2510.14240].
- Findings: coverage leaders Grok-4 Heavy DR 89.3, o3 DR 85.0, GPT-5 83.4; citation association leaders Deerflow+ (GPT-5) 77.0 and Open Deep Research (GPT-5) 76.9; multi-agent systems averaged 69.5 vs 62.8 for single-agent web search; unsupported claims outnumber invalid URLs among citation errors [https://arxiv.org/html/2510.14240].

### ReportBench (2025)
- 100 prompts reverse-engineered from 678 arXiv survey papers; metrics: cited-reference precision/recall vs the survey's bibliography and factuality of cited and uncited statements; gpt-4o for extraction/consistency, gemini-2.5-pro + flash majority vote for uncited claims [https://arxiv.org/html/2508.15804].
- OpenAI DR: reference precision 0.385, recall 0.033, 9.89 refs/report, cited-statement match 78.87%, uncited accuracy 95.83%; Gemini DR: precision 0.145, recall 0.036, 32.42 refs/report, 72.94% cited match, 92.21% uncited accuracy [https://arxiv.org/html/2508.15804].

### DEER (ICML 2026)
- 50 report tasks in 13 domains derived from HLE questions; taxonomy of 7 dimensions / 25 sub-dimensions / 101 rubric items plus task-specific Expert Evaluation Guidance; claim-verification module classifies atomic claims into six types and back-tracks omitted citations [https://arxiv.org/abs/2512.17776] [https://arxiv.org/html/2512.17776].
- GPT-5.2 judge for quality, GPT-5-mini for verification; ~$0.5-1.0 per report; Pearson 0.73 with experts (human-human 0.81), pairwise agreement 0.84; systems score 5.98-6.50 on presentation but ~4-5 on request fulfilment and analytical soundness; OpenAI DR best overall at 6.50 [https://arxiv.org/html/2512.17776].

### 2026 additions and others
- DRACO (Perplexity): 100 open-ended tasks from anonymised real Perplexity DR requests, 10 domains, 40 countries; 3,934 criteria (accuracy 52%, breadth/depth 22%, presentation 14%, citation 12%), validated by 26 experts; best-system saturation ~71%; HF dataset card says MIT while the paper abstract page says CC BY-NC-ND 4.0 (licence conflict, unverified) [https://huggingface.co/datasets/perplexity-ai/draco] [https://arxiv.org/abs/2602.11685].
- Dr. Bench: 214 expert-curated tasks, 10 domains, manually built reference bundles, metrics for semantic quality, topical focus and retrieval trustworthiness [https://arxiv.org/abs/2510.02190].
- DeepResearchEval: persona-driven automatic task construction with qualification and search-necessity filters; adaptive point-wise criteria and active fact-checking that verifies statements even without citations [https://arxiv.org/abs/2601.09688].
- Wiki Live Challenge: 100 newest Wikipedia Good Articles as human-expert references; Wiki Eval with 39 writing-quality criteria plus factuality vs the human article; large gap remains [https://arxiv.org/abs/2602.01590].
- MiroEval: 100 tasks (70 text, 30 multimodal), 13 systems, adds process auditing; process quality predicts outcomes; multimodal tasks cost most systems 3-10 points [https://arxiv.org/abs/2603.28407].
- DRBench (enterprise): 100 tasks over emails, chats, files and the open web; insight recall, factual accuracy, report quality [https://arxiv.org/abs/2510.00172].
- DeepWideSearch: 220 questions, 15 domains, needs both multi-hop depth and wide collection; SOTA success only 2.39%; failures: no reflection, over-reliance on internal knowledge, insufficient retrieval, context overflow [https://arxiv.org/abs/2510.20168].
- Search-time contamination: agents encounter benchmark pages during live search; three severities (metadata, question-context, explicit answer leakage); inflation up to 4% across six public benchmarks; mitigations: isolated sandboxes, transparent search trajectories, controlled benchmark access [https://arxiv.org/abs/2606.05241].
- The 2025 roadmap survey criticises QA-style evaluation of DR agents and calls for benchmarks reflecting multi-stage, evidence-grounded report workflows [https://arxiv.org/html/2506.18096].

Cross-cutting observations (my synthesis): (a) every 2025-26 report benchmark converged on fine-grained binary rubrics or checklists judged by a frontier LLM, with pairwise comparison reserved for subjective depth; (b) judging cost is now modest ($0.25-1.00 per report); (c) recall of key facts is the consistent bottleneck while formatting is near-saturated; (d) citation support (not URL validity) is the dominant citation error.

---

## 2. Adjacent agentic browsing / QA benchmarks used as proxies

- BrowseComp: 1,266 questions requiring persistent browsing for entangled facts; answers are short and verifiable; authors state it "sidesteps challenges of a true user query distribution, like generating long answers or resolving ambiguity" and liken it to competitive programming for coding agents [https://arxiv.org/abs/2504.12516]. OpenAI Deep Research scored 51.5% vs GPT-4o 0.6% and o1 9.9%; it fully solved 16% of tasks and always failed on 14% [https://gigazine.net/gsc_news/en/20250411-openai-browsecomp-benchmark-browsing-agent/].
- BrowseComp-Plus: 830 queries over a fixed 100,195-document corpus with human-verified evidence and hard negatives; isolates retriever from agent; reports search calls, evidence recall and citation accuracy; Search-R1+BM25 3.86%, GPT-5 55.9%, GPT-5+Qwen3-Embedding-8B 70.1% with fewer calls [https://arxiv.org/abs/2508.06600] [https://github.com/texttron/BrowseComp-Plus].
- GAIA: 466 questions (300 with public answers), three difficulty levels, requiring reasoning, multimodality, browsing, tool use; humans 92% vs GPT-4+plugins 15% at release [https://arxiv.org/abs/2311.12983]. OpenAI reported 67.36% pass@1 on the validation set for Deep Research (secondary source; 72.57% figure also circulated, likely cons@64 - unverified) [https://www.helicone.ai/blog/openai-deep-research].
- Humanity's Last Exam: 2,500 expert-level questions (41% maths), 24% multiple choice, rest exact-match, 14% multimodal; OpenAI DR reached 26.6% in Feb 2025; frontier models ~59% by 2026; an independent audit found ~30% of text-only chemistry/biology answers may be wrong, prompting HLE-Rolling [https://en.wikipedia.org/wiki/Humanity's_Last_Exam] [https://fortune.com/2025/02/12/openai-deepresearch-humanity-last-exam/].
- SimpleQA: 4,326 short fact questions with single indisputable, time-stable answers; graded correct / incorrect / not attempted to reward abstention [https://openai.com/index/introducing-simpleqa/] [https://arxiv.org/abs/2411.04368]. Perplexity DR reported 93.9% SimpleQA and 21.1% HLE [https://x.com/perplexity_ai/status/1890452359773405675].
- WebWalkerQA: 680 QA pairs over 1,373 pages in conference/organisation/education/game domains; single-source (depth 2-4) and multi-source (depth 2-8); GPT-4 CoT judge; best ~37.5% [https://arxiv.org/html/2501.07572].
- WebArena: self-hosted e-commerce/forum/GitLab/CMS sites, functional-correctness scoring; GPT-4 agent 14.41% vs humans 78.24% at release [https://arxiv.org/abs/2307.13854]. Mind2Web: 2,000+ tasks from 137 sites in 31 domains, step and task success rates [https://arxiv.org/abs/2306.06070]. Online-Mind2Web shows ~90% WebVoyager scores collapse under live conditions [https://github.com/OSU-NLP-Group/Online-Mind2Web].

Why these are only proxies for report quality: they score a single short answer, so they cannot detect omitted sub-topics, shallow synthesis, unsupported claims, mis-attributed citations, or poor structure - the exact properties the report benchmarks above find weakest. BrowseComp's authors say so explicitly [https://arxiv.org/abs/2504.12516]; FutureSearch found ChatGPT-o3 beating dedicated Deep Research products on short answers even though report benchmarks rank the DR products higher [https://arxiv.org/html/2506.06287]; and live-web QA scores are vulnerable to search-time contamination [https://arxiv.org/abs/2606.05241]. They remain useful for the retrieval sub-skill (finding and verifying a fact) and as a sanity check that a workflow can locate hard-to-find sources.

---

## 3. Citation and factuality evaluation

Foundational metrics
- FActScore decomposes text into atomic facts and reports the share supported by a knowledge source; the automated estimator has <2% error vs humans; ChatGPT biographies were ~58% factually precise; human annotation of 6,500 generations would have cost $26k [https://arxiv.org/abs/2305.14251].
- ALCE (ASQA, QAMPARI, ELI5) defines citation recall (is each statement fully supported by its citations, via NLI) and citation precision (does each citation contribute support), plus fluency and correctness; even the best model lacked complete citation support 50% of the time on ELI5 [https://arxiv.org/abs/2305.14627].
- SAFE / long-form factuality extends this with search-backed atomic-claim checking and explicit precision and recall framing [https://arxiv.org/pdf/2403.18802]; VeriScore restricts to verifiable claims [https://arxiv.org/pdf/2406.19276].

How deep-research benchmarks operationalise citations
- Statement-URL pair extraction -> fetch page -> LLM support judgment -> citation accuracy and effective-citation count (DeepResearch Bench FACT) [https://arxiv.org/html/2506.11763]; the same pattern in ResearcherBench (faithfulness = supported share, groundedness = share of content with any citation) [https://github.com/GAIR-NLP/ResearcherBench]; graded 1 / 0.5 / 0 support in DeepResearchGym [https://arxiv.org/html/2505.19253]; DEER verifies both cited and uncited claims and back-tracks omitted citations [https://arxiv.org/html/2512.17776]; ReportBench separates cited-statement match (72.9-78.9%) from uncited-statement accuracy (92-96%) [https://arxiv.org/html/2508.15804].

Independent audits of commercial systems
- "Cited but Not Verified" (2026): a Markdown-AST citation parser plus three checks - Link Works (HTTP), Relevant Content (LLM), Fact Check (LLM); across 14 models frontier systems keep >94% link validity and >80% relevance but only 39-77% fact-check accuracy; factual accuracy fell ~42% as tool calls scaled from 2 to 150 while link validity stayed >92%; open models produced cited reports only 17-40% of the time [https://arxiv.org/html/2605.06635].
- "Detecting and Correcting Reference Hallucinations" (2026): HEAD requests + Wayback Machine lookup + headless browser to separate fabricated from stale URLs; Gemini 2.5 Pro Deep Research 13.3% hallucinated / 18.5% non-resolving URLs, OpenAI DR 3.5% / 10.1%, Claude 3.0-3.2% / 7.8-8.5%; the urlhealth tool in a self-correction loop cut non-resolving citations 6-79x to under 1% [https://arxiv.org/html/2604.03173v1].
- Tow Center / CJR (Mar 2025): 200 tests, eight engines asked to identify the source of verbatim news excerpts; incorrect 37% (Perplexity) to 94% (Grok-3); over half of Gemini and Grok-3 answers cited fabricated or broken URLs (Grok-3: 154 broken of 200); ChatGPT signalled uncertainty only 15 times in 200 answers; engines pointed to syndicated copies and bypassed robots.txt [https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php].
- Bibliographic reference retrieval across 8 chatbots: none fully accurate (unverified detail) [https://arxiv.org/pdf/2505.18059].

What vendors report
- OpenAI reported HLE 26.6% and GAIA results at launch and acknowledged the agent can hallucinate facts, struggle to distinguish authoritative information from rumour, show weak confidence calibration and make formatting errors (launch page returned HTTP 403 on 2026-09-02; limitations as relayed by a secondary source) [https://www.helicone.ai/blog/openai-deep-research]. OpenAI does not publish a citation-accuracy number (unverified).
- Google reported human raters preferred Gemini 2.5 Pro Deep Research over OpenAI DR by >2:1, with instruction following 60.6/39.4, comprehensiveness 76.9/23.1, completeness 73.3/26.7, writing quality 58.2/41.8 - internal, pairwise, no citation metric [https://www.neowin.net/news/google-launches-gemini-25-pro-powered-deep-research-outperforming-chatgpt-deep-research/].
- Perplexity reported SimpleQA 93.9% and HLE 21.1% and "most tasks under 3 minutes"; no citation-accuracy figure [https://x.com/perplexity_ai/status/1890452359773405675] [https://techcrunch.com/2025/02/15/perplexity-launches-its-own-freemium-deep-research-product/]. Third-party benchmarks nonetheless rank Perplexity highest on citation accuracy (90.24%) with far fewer citations [https://deepresearch-bench.github.io/].
- Parallel.ai's vendor benchmark reports a cost-per-thousand-queries vs accuracy frontier (e.g. GPT-5 38% on a 100-question BrowseComp sample at $488 CPM); vendor-run, treat as indicative [https://parallel.ai/blog/deep-research-benchmarks].

Known failure modes (consolidated): fabricated URLs (Grok-3, Gemini in CJR; 13.3% Gemini DR) [https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php] [https://arxiv.org/html/2604.03173v1]; stale-but-real URLs from a partially stale index [https://arxiv.org/html/2604.03173v1]; real URL, unrelated content; real relevant URL that does not support the specific claim (the largest bucket) [https://arxiv.org/html/2605.06635] [https://arxiv.org/html/2510.14240]; citing syndicated copies instead of originals [https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php]; uncited claims (groundedness 0.34 for OpenAI DR) [https://github.com/GAIR-NLP/ResearcherBench]; degradation with very long tool-call chains [https://arxiv.org/html/2605.06635]; low reference recall vs expert bibliographies (3%) [https://arxiv.org/html/2508.15804].

---

## 4. LLM-as-judge practice for long reports

Pairwise vs rubric scoring
- Pointwise absolute scores were "insufficiently discriminative" for long reports, motivating reference-relative scoring in DeepResearch Bench [https://arxiv.org/html/2506.11763]. Single holistic ratings fell below 60% human agreement in LiveResearchBench, whereas binary checklists reached 98.3% (presentation) and position-swapped pairwise reached 92.5% (depth) [https://arxiv.org/html/2510.14240].
- The field has therefore split the job: binary rubric/checklist items for coverage, recall and presentation (DRB II, ResearchRubrics, DRACO, DEER), error-counting for consistency and citations, and pairwise only for subjective depth [https://arxiv.org/html/2601.08536] [https://github.com/SalesforceAIResearch/LiveResearchBench].
- Pointwise rubric grading is more position-sensitive than pairwise when several responses appear in one prompt; randomise order and repeat with reversed order [https://arxiv.org/pdf/2602.02219].

Known biases
- Zheng et al. (MT-Bench) identified position bias, verbosity bias and self-enhancement bias and limited reasoning ability in GPT-4 judges [https://arxiv.org/pdf/2306.05685].
- Position bias depends strongly on the quality gap (small gaps amplify it) and appears in GPT-4 and Claude alike [https://aclanthology.org/2025.ijcnlp-long.18.pdf]. "Coin Flip Judge" (2026): pairwise verdicts flipped 13.6% on average across 50 repeated trials, 28% of questions flipped >20%; cross-judge agreement 76% (kappa 0.51); GPT-4o-mini preferred position A 72%; equivalent prompts changed outcomes 25% of the time; 11 repeated trials needed for a majority vote to recover the 50-trial verdict with 95% probability [https://arxiv.org/abs/2606.13685].
- Self-preference: GPT-4 showed the largest self-preference (0.520 on an equal-opportunity metric; TPR 0.945 vs TNR 0.425 for its own outputs); the effect tracks low perplexity of the text rather than explicit self-recognition [https://arxiv.org/html/2410.21819].
- Length: AlpacaEval favoured longer outputs; Length-Controlled AlpacaEval regresses out length difference via a GLM and correlates better with humans [https://openreview.net/pdf/76a4afefba676b543f4c4ca61529f92e828e171f.pdf]. Verbosity bias is judge-specific: Gemini/Llama favoured length (+0.24 to +0.44), Claude Sonnet 4 favoured concision (-0.12), GPT-4o neutral [https://arxiv.org/html/2604.23178].
- "Reliability without Validity" (2026, 21 judges, ~541k judgments): test-retest >0.95 yet two production judges had position bias >0.10; kappa deflates exact-match agreement by 33-41 points; proposes a minimum viable validation protocol [https://arxiv.org/abs/2606.19544].
- Autorubric (2026) finds no universal mitigation stack; failures are criterion-specific and judge-family-specific, so rubric and judge choices must be explicit and auditable [https://arxiv.org/abs/2603.00077].

Mitigations with evidence
- Position swap + averaging is standard (LiveResearchBench depth protocol) [https://github.com/SalesforceAIResearch/LiveResearchBench]; but on adversarial sets position swap hurt (-3 to -13 pp) while forced chain-of-thought was universally positive; combined CoT+rubric+swap gave +11.5 pp for Claude Sonnet 4 on MT-Bench; Gemini 2.5 Flash with the combined strategy hit 71% agreement at ~$0.001 per evaluation [https://arxiv.org/html/2604.23178].
- Multiple judges from different providers (GPT-5 + Gemini-2.5-Pro ensemble) [https://github.com/SalesforceAIResearch/LiveResearchBench]; majority vote of gemini-2.5-pro and flash [https://arxiv.org/html/2508.15804]; down-weight a judge on its own family's outputs [https://arxiv.org/html/2410.21819].
- Rubric anchoring: task-specific expert guidance raised DEER judge-human Pearson to 0.73 [https://arxiv.org/html/2512.17776]; reference-relative scoring in RACE [https://arxiv.org/html/2506.11763]; grounding rubrics in expert-written articles rather than LLM-generated criteria (DRB II, Wiki Live Challenge) [https://arxiv.org/html/2601.08536] [https://arxiv.org/abs/2602.01590].
- Statistical correction: estimate judge sensitivity/specificity on a small human-labelled set and report bias-corrected scores with confidence intervals [https://arxiv.org/abs/2511.21140].

Judge models used by the benchmarks: Gemini-2.5-Pro (DeepResearch Bench original, DRB II, ResearchRubrics), GPT-5.5 / gpt-5.4-mini (DeepResearch Bench current), gpt-4.1-mini (DeepResearchGym), Gemini 2.5 Flash (FutureSearch DRB), GPT-5 + Gemini-2.5-Pro (LiveResearchBench), gpt-4o + gemini-2.5-pro/flash (ReportBench), GPT-5.2 + GPT-5-mini (DEER), Claude-3.7-Sonnet for insight extraction only (ResearcherBench). Claude 4 Sonnet was rejected as a judge in LiveResearchBench for low agreement [https://arxiv.org/html/2510.14240]. Implication: judging with the same family that generated the report (e.g. Claude judging a Claude Code skill) invites self-preference; use a different-family judge or a two-family ensemble.

---

## 5. Cost, latency and efficiency metrics reported

- Cost per task: FutureSearch DRB leaderboard reports dollars per task alongside accuracy ($0.10-0.53 for top systems) [https://drb.futuresearch.ai/]; higher effort settings raised cost 47-200% with flat or negative accuracy change [https://futuresearch.ai/effort-paradox/].
- Cost per question for agent frameworks: OWL (GPT-5) $2.75 and WebSailor (Claude Sonnet 4) $1.40 per question; parallel tool calling cut cost to $65.7 per 100 tasks (-35.9%) and wall-clock from 1,522.6 s to 904.2 s (-40.6%) at equal accuracy (secondary summary, unverified which paper) [https://arxiv.org/pdf/2602.07359] [https://arxiv.org/pdf/2510.20168].
- W&D: scaling parallel tool calls reached 62.2% BrowseComp with GPT-5-medium vs 54.9% for GPT-5-high, with fewer turns [https://arxiv.org/abs/2602.07359].
- Tokens, wall-clock and dollars vary by an order of magnitude across agents but none correlates strongly with pass rate on long-horizon agent tasks [https://arxiv.org/html/2607.07946v1].
- Judging cost: ~$0.25 per task (DRB II, Gemini-2.5-Pro, batch 50) [https://arxiv.org/html/2601.08536]; $0.5-1.0 per report (DEER) [https://arxiv.org/html/2512.17776]; ~$0.001 per pairwise judgment with Gemini 2.5 Flash [https://arxiv.org/html/2604.23178]; human expert judging ~1.5 h per report [https://arxiv.org/html/2506.11763].
- Source counts: effective citations per report range from 8 (Grok) to 111 (Gemini DR) [https://deepresearch-bench.github.io/]; references per report 9.9 (OpenAI DR) vs 32.4 (Gemini DR) [https://arxiv.org/html/2508.15804]; BrowseComp-Plus reports number of search calls as an efficiency metric [https://arxiv.org/abs/2508.06600]; WebWalkerQA reports action counts [https://arxiv.org/html/2501.07572].
- Latency: OpenAI DR 5-30 min per query; Perplexity 2-4 min [https://www.helicone.ai/blog/openai-deep-research] [https://techcrunch.com/2025/02/15/perplexity-launches-its-own-freemium-deep-research-product/].
- Process metrics: per-step hallucination rate, repeated-tool-call rate and forgetting (FutureSearch trace evaluation) [https://arxiv.org/html/2506.06287]; process audits predict outcomes (MiroEval) [https://arxiv.org/abs/2603.28407]; fact-check accuracy drops ~42% from 2 to 150 tool calls [https://arxiv.org/html/2605.06635].
- Vendor price-performance: cost per thousand queries vs accuracy / win-rate frontier [https://parallel.ai/blog/deep-research-benchmarks].

---

## 6. Practical recommendation: a lightweight protocol for one developer

Design constraints drawn from the literature
- Sample size. With ~100 paired items you can only resolve fairly large gaps. Paired designs need a median 2.15x fewer items than unpaired, and the required N depends on the within-pair correlation; report a resolution ratio rather than pretending small differences are real [https://arxiv.org/html/2605.30315v1]. CLT intervals are unreliable under a few hundred items; use bootstrap, Wilson or Bayesian intervals [https://arxiv.org/abs/2503.01747]. Miller's framework gives paired-difference standard errors and cluster adjustments (topic clusters can inflate SE ~3x) [https://arxiv.org/abs/2411.00640]. Practical reading: 30-50 questions detects only large effects; 100 is a reasonable single-developer ceiling; treat anything under ~5-point rubric difference as a tie unless intervals say otherwise.
- Freshness. Choose questions whose answers postdate the models' training cutoff so parametric recall cannot substitute for research (LiveResearchBench's "dynamic" criterion) [https://arxiv.org/abs/2510.14240], and keep the question set off the public web to avoid search-time contamination [https://arxiv.org/abs/2606.05241].
- Judge choice. Use a judge from a different model family than the workflows under test, or a two-family ensemble; require chain-of-thought; swap positions on pairwise items; repeat noisy items [https://arxiv.org/html/2604.23178] [https://arxiv.org/abs/2606.13685] [https://arxiv.org/html/2410.21819].
- Rubrics. Binary, task-specific, written before seeing outputs, ideally grounded in a reference document you trust (expert article, official statistics page) rather than LLM-generated criteria [https://arxiv.org/html/2601.08536] [https://arxiv.org/abs/2602.01590].
- Citations. Automate the cheap checks (URL resolves; page contains the quoted span or close paraphrase) and reserve LLM support-judgment for the sampled remainder [https://arxiv.org/html/2605.06635] [https://arxiv.org/html/2604.03173v1].
- Controls. Same underlying model, same tool budget and same harness for both workflows; otherwise you are measuring the model, not the workflow (FutureSearch effort results show settings alone move scores 2-3 points) [https://futuresearch.ai/effort-paradox/].

---

## Recommended protocol

1. Fix the comparison. Define workflow A and workflow B as prompts/skills only. Pin the same model ID, same reasoning-effort setting, same search/fetch tools, same maximum tool calls and wall-clock budget, same output format (Markdown with inline URL citations). Log tokens, tool calls and wall-clock per run.
2. Build a 40-60 question set (aim for 50; go to 100 if budget allows). Mix domains roughly evenly: technology/software, science/health, business/finance, policy/law, culture/history, plus 5-10 "practical" questions like the ones your users will ask. Half should require post-cutoff information (events, releases, prices, versions since the model's cutoff); at least 10 should have a checkable expert reference (an official report, a standards page, a Wikipedia Good Article). Write each question with an explicit deliverable ("compare X and Y on A, B, C; cite primary sources").
3. Write rubrics before generating any report. For each question, 8-15 binary items: 5-8 recall items ("mentions that Z happened on DATE"), 2-4 analysis items ("explains why", "notes trade-off"), 1-2 instruction items, 1 presentation item. Reuse ResearchRubrics' weighted-compliance formula. Store rubrics locally; do not publish them.
4. Generate reports: run A and B on every question, in randomised order, at least twice each if budget allows (variance across runs is real). Save report Markdown, tool trace, token counts and wall-clock.
5. Automated citation checks (no LLM): parse citations from Markdown (links, footnotes, numbered refs); HEAD/GET each URL with a browser-like user agent and a 15 s timeout; record resolves / 404 / blocked / timeout; for non-resolving URLs query the Wayback Machine availability API to label fabricated vs stale; fetch resolving pages, strip to text, and test whether any quoted span (or a normalised 8-12-word shingle from the citing sentence) appears in the page; report URL-valid rate, fabricated rate, and quote-containment rate per workflow.
6. LLM citation support check: sample up to 10 statement-URL pairs per report (all, if fewer), give the judge the claim and the fetched page text, ask supported / partially / not supported / page unavailable; compute citation accuracy and effective citations as in FACT and ResearcherBench.
7. Rubric judging: for each report, a judge from a different family than the generator scores each binary item with a one-line justification, 20-30 items per call, temperature 0. Run a second judge family on a 20% sample and report agreement (Cohen's kappa, not raw match). Compute weighted compliance per report.
8. Pairwise depth/usefulness judgment: for each question, show A and B side by side and ask for a forced choice on depth, synthesis and overall usefulness with chain-of-thought; run twice with positions swapped; treat disagreement as a tie. Include a length penalty by also asking "is the longer report better only because it is longer?" or by regressing preference on length difference (Length-Controlled AlpacaEval style).
9. Analysis: primary metric is mean rubric compliance difference (B minus A) with a paired bootstrap 95% interval; secondary metrics are citation accuracy, fabricated-URL rate, pairwise win rate (with ties), tokens, tool calls, wall-clock. Cluster bootstrap by domain. Declare a winner only if the primary interval excludes zero and citation metrics are not worse; otherwise report "no resolvable difference at N".
10. Calibrate the judge once: hand-grade 10 reports yourself (about 3-4 hours) against the same rubrics; compute judge sensitivity/specificity and report bias-corrected compliance following the LLM-judge reporting framework; re-check if you change the judge model.
11. Guard against leakage: never paste questions to public sites; inspect traces for hits on your own eval files or on benchmark-hosting domains; refresh 20% of the question set every quarter.
12. Budget estimate (my calculation from the cost figures above): 50 questions x 2 workflows x 2 runs = 200 reports; generation dominates cost (roughly $0.3-3 per report depending on model); judging ~$0.25-1.00 per report ($50-200); URL checks are free. A single developer can complete one full comparison in a day of compute plus half a day of setup.

---

## Sources (all accessed 2026-09-02)

1. DeepResearch Bench paper - https://arxiv.org/abs/2506.11763 and https://arxiv.org/html/2506.11763
2. DeepResearch Bench repo - https://github.com/Ayanami0730/deep_research_bench
3. DeepResearch Bench leaderboard - https://deepresearch-bench.github.io/
4. DeepResearch Bench II - https://arxiv.org/html/2601.08536 and https://arxiv.org/pdf/2601.08536
5. DeepResearchGym - https://arxiv.org/abs/2505.19253 and https://arxiv.org/html/2505.19253
6. ResearchRubrics - https://arxiv.org/abs/2511.07685 ; https://scale.com/research/researchrubrics ; https://github.com/scaleapi/researchrubrics
7. FutureSearch Deep Research Bench paper - https://arxiv.org/abs/2506.06287 and https://arxiv.org/html/2506.06287
8. FutureSearch DRB leaderboard - https://drb.futuresearch.ai/ ; overview https://futuresearch.ai/deep-research-bench/
9. FutureSearch effort paradox - https://futuresearch.ai/effort-paradox/
10. ResearcherBench - https://arxiv.org/abs/2507.16280 ; https://github.com/GAIR-NLP/ResearcherBench
11. LiveResearchBench - https://arxiv.org/abs/2510.14240 ; https://arxiv.org/html/2510.14240 ; https://github.com/SalesforceAIResearch/LiveResearchBench
12. ReportBench - https://arxiv.org/html/2508.15804
13. DEER - https://arxiv.org/abs/2512.17776 ; https://arxiv.org/html/2512.17776
14. DRACO - https://arxiv.org/abs/2602.11685 ; https://huggingface.co/datasets/perplexity-ai/draco
15. Dr. Bench - https://arxiv.org/abs/2510.02190
16. DeepResearchEval - https://arxiv.org/abs/2601.09688
17. Wiki Live Challenge - https://arxiv.org/abs/2602.01590
18. MiroEval - https://arxiv.org/abs/2603.28407
19. DRBench (enterprise) - https://arxiv.org/abs/2510.00172
20. DeepWideSearch - https://arxiv.org/abs/2510.20168
21. Search-Time Contamination in Deep Research Agents - https://arxiv.org/abs/2606.05241
22. Deep Research Agents: A Systematic Examination and Roadmap - https://arxiv.org/html/2506.18096
23. BrowseComp - https://arxiv.org/abs/2504.12516 ; https://gigazine.net/gsc_news/en/20250411-openai-browsecomp-benchmark-browsing-agent/
24. BrowseComp-Plus - https://arxiv.org/abs/2508.06600 ; https://github.com/texttron/BrowseComp-Plus
25. GAIA - https://arxiv.org/abs/2311.12983
26. Humanity's Last Exam - https://en.wikipedia.org/wiki/Humanity's_Last_Exam ; https://fortune.com/2025/02/12/openai-deepresearch-humanity-last-exam/
27. SimpleQA - https://openai.com/index/introducing-simpleqa/ ; https://arxiv.org/abs/2411.04368
28. WebWalkerQA - https://arxiv.org/html/2501.07572
29. WebArena - https://arxiv.org/abs/2307.13854 ; Mind2Web - https://arxiv.org/abs/2306.06070 ; Online-Mind2Web - https://github.com/OSU-NLP-Group/Online-Mind2Web
30. FActScore - https://arxiv.org/abs/2305.14251
31. ALCE - https://arxiv.org/abs/2305.14627
32. Long-form factuality (SAFE) - https://arxiv.org/pdf/2403.18802 ; VeriScore - https://arxiv.org/pdf/2406.19276
33. Cited but Not Verified - https://arxiv.org/html/2605.06635
34. Detecting and Correcting Reference Hallucinations - https://arxiv.org/html/2604.03173v1
35. Tow Center / CJR, AI Search Has a Citation Problem - https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php
36. Bibliographic reference retrieval across 8 chatbots - https://arxiv.org/pdf/2505.18059
37. OpenAI Deep Research (secondary, launch page 403) - https://www.helicone.ai/blog/openai-deep-research
38. Gemini Deep Research rater preference (secondary) - https://www.neowin.net/news/google-launches-gemini-25-pro-powered-deep-research-outperforming-chatgpt-deep-research/
39. Perplexity Deep Research - https://x.com/perplexity_ai/status/1890452359773405675 ; https://techcrunch.com/2025/02/15/perplexity-launches-its-own-freemium-deep-research-product/
40. Parallel.ai deep research benchmarks (vendor) - https://parallel.ai/blog/deep-research-benchmarks
41. Judging LLM-as-a-Judge (Zheng et al.) - https://arxiv.org/pdf/2306.05685
42. Systematic study of position bias - https://aclanthology.org/2025.ijcnlp-long.18.pdf
43. Position bias in rubric-based judging - https://arxiv.org/pdf/2602.02219
44. Self-Preference Bias in LLM-as-a-Judge - https://arxiv.org/html/2410.21819
45. Length-Controlled AlpacaEval - https://openreview.net/pdf/76a4afefba676b543f4c4ca61529f92e828e171f.pdf
46. Judging the Judges: bias mitigation evaluation - https://arxiv.org/html/2604.23178
47. The Coin Flip Judge? - https://arxiv.org/abs/2606.13685
48. Reliability without Validity - https://arxiv.org/abs/2606.19544
49. Autorubric - https://arxiv.org/abs/2603.00077
50. How to Correctly Report LLM-as-a-Judge Evaluations - https://arxiv.org/abs/2511.21140
51. Adding Error Bars to Evals (Miller) - https://arxiv.org/abs/2411.00640
52. Resolution Diagnostics for Paired LLM Evaluation - https://arxiv.org/html/2605.30315v1
53. Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints - https://arxiv.org/abs/2503.01747
54. W&D: Scaling Parallel Tool Calling - https://arxiv.org/abs/2602.07359
55. DeepSWE (token/cost vs pass rate observation) - https://arxiv.org/html/2607.07946v1
