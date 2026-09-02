# Research process architecture: how deep-research systems structure the work, and what the evidence says

Survey date: **2026-09-02**. Scope: the *process architecture* of deep-research systems — decomposition, search strategy, orchestration, verification, synthesis — and the published evidence for which choices improve **fact recall**, **coverage**, and **citation quality**.

Out of scope (covered by sibling surveys, not repeated here): output formats of finished reports (`output-formats-survey.md`), evaluation benchmarks and judging protocols (`evaluation-survey.md`), web-fetch reliability and fallbacks (`fetch-reliability-survey.md`). Benchmarks appear below **only** where they attribute failures to architecture.

Every factual sentence carries its source URL in brackets. Items marked **unverified** could not be confirmed from a primary source at the stated level of detail.

---

## 0. Comparison table of systems

| System | Decomposition | Search strategy | Orchestration | Verification | Synthesis | Context handling |
|---|---|---|---|---|---|---|
| **Claude Code built-in `/deep-research`** (v2.1.258 bundled workflow, read locally 2026-09-02) | Scope agent: 3-6 angles (prompt asks for 5), each a label + query + rationale; clarifying questions asked *before* invoking if underspecified | One WebSearch agent per angle, 4-6 results each; URL-dedup; fetch top ~15 (high-relevance results bypass the budget cap) | Script-driven fan-out: 1 scope + N search + M fetch + 3×claims verify + 1 synth agents; runtime caps 16 concurrent, 1000 agents/run [https://code.claude.com/docs/en/workflows] | 3 adversarial voters per claim, 2/3 refutations kill it, max 25 claims; verifier told "default to refuted=true if uncertain"; infra failures → "unverified" | Merge semantic duplicates, group into findings, confidence high/med/low, list refuted + unverified claims + open questions | All intermediate state in script variables, never in the session context window [https://code.claude.com/docs/en/workflows] |
| **Anthropic Research (claude.ai)** | Lead agent plans, writes plan to memory; subagent task descriptions must carry objective, output format, tool guidance, boundaries [https://www.anthropic.com/engineering/multi-agent-research-system] | "Start with short, broad queries, evaluate what's available, then progressively narrow"; 3+ parallel tool calls per subagent | Orchestrator-worker: Opus 4 lead + 3-5 Sonnet 4 subagents in parallel; effort scaling rules by query type | Separate **CitationAgent** inserts citations post-hoc over documents + draft | Lead synthesises subagent summaries; artifact system lets subagents write outputs that persist independently | Plan saved to Memory because context >200k truncates; fresh subagents spawned with clean contexts and handoffs |
| **OpenAI Deep Research** | Intent-to-planning: an explicit clarification step before planning [https://arxiv.org/html/2506.18096v1] | Single RL-trained o3-derived agent browsing iteratively; hundreds of steps [https://cdn.openai.com/deep-research-system-card.pdf] | Single agent (no subagents) | Trained-in, not a separate stage | One-pass long report | Trained for long-horizon focus rather than architectural context reset |
| **LangChain Open Deep Research** | Clarify (`allow_clarification` default `True`) → **research brief** compressed from the chat [https://www.langchain.com/blog/open-deep-research] | Supervisor decides parallel vs single-threaded; each researcher runs a ReAct loop; `max_react_tool_calls` default 10 | Supervisor + up to `max_concurrent_research_units` = 5 researchers, `max_researcher_iterations` = 6 [github.com/langchain-ai/open_deep_research @ 1b7d2e8, `src/open_deep_research/configuration.py`] | None as a stage | **One-shot** final report from the brief + findings; they abandoned parallel section-writing because results were "disjoint" | Per-researcher isolated context; explicit **compression** step prunes findings before returning to supervisor; separate summarization/compression/report models |
| **GPT Researcher (multi_agents)** | Editor plans outline/structure from initial browse; `MAX_SUBTOPICS` = 3, `MAX_ITERATIONS` = 3 [github.com/assafelovic/gpt-researcher @ 6f99857, `gpt_researcher/config/variables/default.py`] | Per-section parallel research; `MAX_SEARCH_RESULTS_PER_QUERY` = 5; deep mode `DEEP_RESEARCH_BREADTH` = 3, `DEEP_RESEARCH_DEPTH` = 2, concurrency 4 | Chief editor → researcher / editor / reviewer / revisor / writer / publisher [github.com/assafelovic/gpt-researcher `multi_agents/README.md`] | Reviewer/revisor loop until "satisfactory" (LLM-judged, no fixed bound) | Writer assembles sections + intro/conclusion/references; `TOTAL_WORDS` = 1200 | Section-scoped contexts; `BROWSE_CHUNK_MAX_LENGTH` = 8192 |
| **STORM** | **Perspective-guided**: N = 5 perspectives discovered from similar articles; M = 5 conversation rounds each [https://arxiv.org/html/2402.14207v2] | Each simulated writer asks questions; expert answers grounded in search; results filtered by Wikipedia reliability rules | Simulated multi-agent *conversation*, not parallel workers | Source filtering by reliability guidelines only | Draft outline → refined outline using conversations → sections written in parallel with per-section semantic retrieval (Sentence-BERT over collected refs) → dedup pass → lead section | Reference pool is the shared memory; per-section retrieval keeps section contexts small |
| **Co-STORM** | Multiple expert agents + a **moderator** that injects questions to surface "unknown unknowns"; human can join [https://arxiv.org/abs/2408.15232] | Round-table discourse, retrieval per turn | Turn-taking policy over expert agents + moderator + user | — | Dynamic **mind map** organises discovered information; report generated from it | Mind map is the externalised shared memory |
| **dzhng deep-research** | Follow-up questions up front; then SERP queries = `breadth` per level [github.com/dzhng/deep-research `src/deep-research.ts`] | Recursive tree: default breadth 4, depth 2; each level `newBreadth = Math.ceil(breadth/2)`, `newDepth = depth-1`; 5 results/query; 3 learnings extracted per query | Recursion with a concurrency limit; no roles | None | Learnings + visited URLs deduped, then one report | Only "learnings" (short extracted facts) propagate down the recursion — an early compression scheme |
| **Jina node-DeepResearch** | "Gaps queue" of sub-questions generated by a **reflect** action, deduped before enqueue [github.com/jina-ai/node-DeepResearch README] | Loop over search / visit / reflect / answer until token budget exhausted; search disabled next round if a query yields no new URLs | Single agent, action loop | "Definitive answer" evaluator: must address the question, be quality-evaluatable, and include references; failures reset context and retry | "Beast mode" forces a final answer when budget is exhausted | Two channels: intermediate sub-question answers vs raw page content |
| **WebThinker** | Knowledge gaps trigger a Deep Web Explorer sub-loop mid-reasoning [https://arxiv.org/html/2504.21776v2] | Think-Search-**Draft** interleaved; explorer can click links, not just search | Main LRM + assistant LLM for report edits | — | Report drafted incrementally with draft/check/edit tools during reasoning, not after | Explorer returns condensed findings into the main reasoning chain |
| **IterResearch / Tongyi DeepResearch** | Question fixed; sub-goals emerge per round | Rounds of tool calls; each round rebuilds the workspace | Single agent (standard) or **Research-Synthesis "heavy" mode**: n parallel agents + a synthesis model [https://arxiv.org/html/2510.24701v1] | Synthesis model reconciles n independent trajectories | Evolving report *is* the memory; final answer synthesised from it | **Markovian workspace reconstruction**: state = (question, evolving report, last interaction only); O(1) context instead of O(t) [https://arxiv.org/html/2511.07327] |
| **Kimi-Researcher** | Emergent from RL, not scripted | ~23 reasoning steps, >200 URLs explored per task [https://moonshotai.github.io/Kimi-Researcher/] | Deliberately **single agent**; they rejected multi-agent workflows as brittle and version-coupled | Emergent cross-source verification and "epistemic caution" behaviours | Single trajectory → report | Memory mechanism retains important info, discards documents; enables >50 iterations |
| **HF smolagents open-deep-research** | Manager agent + a text-browser agent | Text web browser + text inspector borrowed from Magentic-One | CodeAgent (actions as code) | — | Final answer | — |
| **Manus Wide Research** | One subagent per item ("10 items → 10 subagents; 500 → 500") [https://manus.im/blog/manus-wide-research-solve-context-problem] | Per-item independent research | Centralised orchestrator; **subagents never talk to each other** | Isolation is the safety mechanism: one subagent's hallucination cannot propagate | Controller aggregates | Context isolation per subagent is the explicit design goal |
| **Argus** | Searcher + Navigator cooperate; research framed as assembling complementary evidence pieces [https://arxiv.org/abs/2605.16217] | Parallel searchers, but coordinated to avoid duplicating each other's evidence | 1 → 8 → 64 searchers, all under one Navigator | Evidence-level assembly rather than answer-level voting | Navigator assembles the jigsaw | Navigator reasoning context stays below 21.5K tokens even at 64 searchers |

---

## 1. Question decomposition and planning

### 1.1 Perspective-based decomposition is the best-evidenced decomposition scheme

STORM is the only widely-cited system with a **clean ablation of decomposition itself**. Its pre-writing stage discovers N = 5 perspectives by surveying similar articles, then simulates M = 5 rounds of writer↔expert conversation per perspective [https://arxiv.org/html/2402.14207v2].

Outline-quality ablation (heading soft recall / heading entity recall) [https://arxiv.org/html/2402.14207v2]:

| Variant | GPT-3.5 soft recall | GPT-3.5 entity recall | GPT-4 soft recall | GPT-4 entity recall |
|---|---|---|---|---|
| STORM (full) | 86.26 | 40.52 | 92.73 | 45.91 |
| w/o Perspective | 84.49 | 40.12 | 92.39 | 42.70 |
| w/o Conversation | 77.97 | 31.98 | 88.75 | 39.30 |

Two things follow, and they matter for a prompt-only skill:

1. **Removing the multi-turn conversation hurts far more than removing perspectives.** Entity recall drops 40.52 → 31.98 (GPT-3.5) and 45.91 → 39.30 (GPT-4) when questions are generated in one shot instead of through grounded multi-turn dialogue. Dropping perspectives alone costs ~0.4-3.2 points [https://arxiv.org/html/2402.14207v2]. The value is in *iterating question generation against retrieved answers*, not in the persona labels per se.
2. Article-level gains are smaller than outline-level gains: STORM vs the oRAG baseline scores ROUGE-1 45.82 vs 44.26, entity recall 14.10 vs 12.57, rubric coverage 4.88 vs 4.70, relevance 4.45 vs 4.09 [https://arxiv.org/html/2402.14207v2]. Human experts judged 25% more STORM articles "organized" and 10% more "broad in coverage" than the outline-driven RAG baseline [https://arxiv.org/abs/2402.14207].

### 1.2 How many angles systems actually generate

- Claude Code `/deep-research`: schema enforces 3-6 angles; the prompt asks for exactly 5, with domain-specific templates offered as examples (broad/primary · academic · recent news · contrarian · practitioner; or state-of-art · benchmarks · limitations · adoption · cost) (workflow script, read locally 2026-09-02).
- STORM: 5 perspectives × 5 conversation rounds [https://arxiv.org/html/2402.14207v2].
- dzhng: `breadth` SERP queries per level, default 4, halved at each deeper level [github.com/dzhng/deep-research `src/deep-research.ts`].
- GPT Researcher: `MAX_SUBTOPICS` = 3, `MAX_ITERATIONS` = 3 sub-queries [github.com/assafelovic/gpt-researcher @ 6f99857].
- LangChain ODR: no fixed number — the supervisor decides; capped by `max_concurrent_research_units` = 5 [github.com/langchain-ai/open_deep_research @ 1b7d2e8].
- Anthropic: effort scaling is **prescribed in the prompt**: "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents with clearly divided responsibilities" [https://www.anthropic.com/engineering/multi-agent-research-system].

There is no published ablation that isolates *number of angles* as a variable. **unverified** whether 5 is better than 3 or 8.

### 1.3 Research briefs

LangChain ODR compresses the (possibly long) clarification exchange into "a comprehensive, yet focused research brief" that "serves as the success metric throughout subsequent phases" [https://www.langchain.com/blog/open-deep-research]. Anthropic's lead agent similarly "saves its plan to Memory to persist the context, since if the context window exceeds 200,000 tokens it will be truncated" [https://www.anthropic.com/engineering/multi-agent-research-system]. Both are engineering claims without ablations.

### 1.4 Delegation quality is a measured failure mode

Anthropic reports concrete harm from thin task descriptions: "Without detailed task descriptions, agents duplicate work, leave gaps, or fail to find necessary information… one subagent explored the 2021 automotive chip crisis while 2 others duplicated work investigating current 2025 supply chains" [https://www.anthropic.com/engineering/multi-agent-research-system]. Their prescription: "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."

### 1.5 Outline-first vs claims-first vs interleaved

AgentCPM-Report compares a static **plan-then-write** paradigm against **WARP** (Writing As Reasoning Policy), which alternates evidence-based drafting with reasoning-driven deepening, treating outline edits and content generation as equivalent state transitions [https://arxiv.org/html/2602.06540v1]:

| Paradigm (Qwen3-235B-A22B) | Insight | Comprehensiveness |
|---|---|---|
| Plan-then-write | 51.60 | 49.35 |
| WARP (interleaved) | 52.79 | 50.33 |

The gain is real but small (+1.19 / +0.98). The authors' argument is the **"insight ceiling"**: a static outline fixed before evidence arrives cannot capture insights that surface during articulation [https://arxiv.org/html/2602.06540v1]. Same paper: Comprehensiveness and Insight improve by nearly 6 points as deepening steps increase, **plateauing at around 9 steps** [https://arxiv.org/html/2602.06540v1].

WebThinker's ablation is the strongest evidence that drafting during search beats drafting after it: removing autonomous report drafting costs 8.1 → 6.6 (−18.5%) on the Glaive report-generation task, the single largest drop in their ablation [https://arxiv.org/html/2504.21776v2].

### 1.6 Hypothesis-driven search

Hypothesis-Conditioned Query Rewriting (HCQR) derives a working hypothesis first, then issues three queries — supporting evidence, discriminating evidence against alternatives, and verification of salient clues [https://arxiv.org/html/2603.19008]. Measured against plain query rewriting:

| Metric | Simple RAG | Standard rewriting | HCQR |
|---|---|---|---|
| Decision-Useful Rate, MedQA | 30.0% | 56.1% | 82.1% |
| Decision-Useful Rate, MMLU-Med | 48.7% | 55.3% | 70.3% |
| Accuracy, MedQA | — | 70.7% | 75.0% |
| Accuracy, MMLU-Med | — | 78.2% | 81.1% |
| "Entailed" context share | 14.3% | — | 34.7% |
| "Not useful" context share | 60.7% | — | 23.8% |

This is the largest *evidence-quality* effect in this survey from a purely prompt-time change. Caveat: the domain is multiple-choice medical QA with answer options available, which makes hypothesis formation easy; transfer to open-ended web research is **unverified**.

### 1.7 Clarifying questions

- Claude Code `/deep-research` instructs the caller to ask 2-3 clarifying questions *before* invoking the workflow if the question is underspecified (workflow `meta.whenToUse`, read locally 2026-09-02).
- LangChain ODR ships `allow_clarification` defaulting to `True` [github.com/langchain-ai/open_deep_research @ 1b7d2e8].
- OpenAI DR is classified as "Intent-to-Planning": it "actively clarifies user intent prior to planning through targeted questions"; Gemini DR is "Unified Intent-Planning" (proposes a plan and asks the user to confirm/revise); Grok/H2O/Manus are "Planning-Only" [https://arxiv.org/html/2506.18096v1].
- IntentRL frames this as the "autonomy-interaction dilemma": high autonomy on unclear requests produces long executions with poor results; training an agent to clarify "significantly improves both intent hit rate and downstream task performance, outperforming the built-in clarify modules of closed-source DR agents" [https://arxiv.org/abs/2602.03468]. Exact numbers and an optimal question count are **unverified** (not on the abstract page).

**Evidence summary for §1:** perspective/conversation-based decomposition improves outline coverage and entity recall (strong, STORM); interleaving drafting with search beats plan-then-write (moderate, two independent papers); hypothesis-conditioned querying sharply improves evidence usefulness (moderate, narrow domain); clarifying questions help (moderate, no clean public ablation on report quality); number-of-angles is unstudied (opinion only).

---

## 2. Search strategy

### 2.1 Agentic iteration beats single-shot search by a very large margin

The clearest number: in a controlled retrieval study, single-shot search achieved **8.41% recall@1** on average, while full agentic tool use reached **43.49%** (GPT-5-mini) and **49.59%** (Claude Sonnet 4.5) — 5.2× and 5.9× improvements. Multi-query search reached comparable recall@1 to full agentic use but with fewer iterations [search result summary of the agentic-retrieval literature, 2026-09-02 — **unverified**: I could not open the underlying paper's tables directly, so treat the exact figures as second-hand].

A cleaner primary anchor for the same direction: on BrowseComp-Plus, Search-R1 + BM25 scores 3.86% while GPT-5 scores 55.9%, and GPT-5 paired with a Qwen3-Embedding-8B retriever reaches **70.1% with fewer search calls** [https://arxiv.org/abs/2508.06600]. Better retrieval buys accuracy *and* saves search calls — the two are not in tension.

### 2.2 Breadth-first fan-out vs iterative depth

Three distinct shapes are in production:

**(a) Fixed tree (dzhng).** `deepResearch(query, breadth, depth)` generates `breadth` SERP queries, takes 5 results each, extracts 3 learnings per query, then recurses with `newBreadth = Math.ceil(breadth/2)`, `newDepth = depth-1`, passing accumulated learnings and follow-up questions down [github.com/dzhng/deep-research `src/deep-research.ts`]. Defaults breadth 4 / depth 2; recommended ranges breadth 3-10, depth 1-5 [github.com/dzhng/deep-research README]. Note the branching factor: at breadth 4 / depth 2 this issues 4 + 4×2 = 12 searches. There is no published ablation of breadth vs depth for this design.

**(b) Budget loop (Jina).** Actions are search / visit / reflect / answer; the loop runs until the token budget is exhausted, then "Beast Mode" forces an answer. An answer is accepted only if it addresses the question, is quality-evaluatable, and includes references; otherwise the attempt is stored and the context reset. Sub-questions are deduplicated before entering a "gaps queue". If a search returns no new URLs, search is disabled for the next iteration [github.com/jina-ai/node-DeepResearch README].

**(c) Workspace reconstruction (IterResearch / Tongyi).** Instead of appending observations, each round rebuilds the state as (question, evolving report, last interaction only), giving O(1) context growth instead of O(t) and bounded attention cost [https://arxiv.org/html/2511.07327].

### 2.3 The IterResearch numbers are the strongest architectural evidence in this survey

All from [https://arxiv.org/html/2511.07327]:

- **Paradigm ablation with identical training data**: mono-contextual agent 36.5% average vs IterResearch 49.1% — **+12.6pp** — despite the mono-agent getting a *larger* 64K context window.
- **As a pure prompting strategy on frontier models, no training**: on BrowseComp, OpenAI o3 goes ReAct 34.1% → IterResearch 46.8% (+12.7pp); DeepSeek-V3.1 goes 23.1% → 42.3% (+19.2pp). "IterResearch consistently outperforms ReAct across all benchmarks."
- **Interaction scaling** on a BrowseComp subset: 2 interactions → 5.5%; 2⁴ → 14.3%; 2⁷ → 50.1%; 2¹¹ → 42.5%. An agent trained with T_max = 32 reaches 42.5% when extended to 2048 interactions at inference, vs 15.2% at T_max = 32 — a 64× extrapolation that mono-contextual agents cannot do because they overflow.
- Named failure modes of ReAct-style accumulation: **"context suffocation"** (shrinking reasoning space) and **"noise contamination"** (errors permanently embedded in history).

That the "no training" variant works is what makes this transferable to a prompt-only skill: the periodic rewrite of a compact working state is a *prompt discipline*, not a trained behaviour.

### 2.4 Stopping criteria

| System | Stopping rule |
|---|---|
| Claude Code `/deep-research` | Hard budgets: `MAX_FETCH` = 15, `MAX_VERIFY_CLAIMS` = 25, fixed 5-phase pipeline, no loop (workflow script) |
| Jina | Token budget exhaustion → Beast Mode; plus a "definitive answer" evaluator that can reject and retry [github.com/jina-ai/node-DeepResearch] |
| LangChain ODR | `max_researcher_iterations` = 6, `max_react_tool_calls` = 10; supervisor may request more research if the brief is unmet [github.com/langchain-ai/open_deep_research @ 1b7d2e8] |
| dzhng | Depth counter reaches 0 |
| GPT Researcher | Reviewer loop "until it is satisfactory based on the reviewer feedback" — unbounded in principle [multi_agents/README.md] |
| Marco DeepResearch | Explicit 600-tool-call maximum budget [https://arxiv.org/abs/2603.28376] |

The enterprise deep-research literature names **premature stopping** as a first-class failure: "Enterprise deep research often fails to produce decision-ready reports due to uneven information coverage, context explosion, and premature stopping", addressed by "evidence-based completion criteria so agents iteratively collect information until sufficiency conditions are met" [https://arxiv.org/abs/2604.24978]. Their per-component ablation numbers are **unverified** (the PDF would not extract; the abstract asserts only that dependency-controlled context and evidence-sufficiency criteria "reduce premature stopping and improve consistency and depth").

### 2.5 Snippet-only vs full-page reading

BrowseComp-Plus's controlled corpus was built precisely to disentangle retrieval from reasoning [https://arxiv.org/abs/2508.06600]. Secondary summaries of its agent ablations report accuracy rising from **35.42% (preview/snippet only) to 43.61% (full document access)**, i.e. **+8.19pp**, with the caveat that the benefit was modest for weaker models, and that agents used the full-document tool sparingly — around **0.27 get-document calls per query** on average. **unverified**: sources disagree on whether the model was GPT-4.1 or GPT-4o, and I could not extract the table from the PDF. The direction (full text > snippets) is consistent across every source consulted; the exact figures should be re-checked before being relied on.

This matters directly for the pipeline shape. In Claude Code `/deep-research`, search agents return only `{url, title, snippet, relevance}` and **no claim is ever extracted from a snippet** — claims come only from fetched pages, each with a verbatim quote (workflow script). That is the architecturally correct choice on this evidence.

### 2.6 How many sources are actually read

- Kimi-Researcher: ~23 reasoning steps and **>200 URLs explored per task** [https://moonshotai.github.io/Kimi-Researcher/].
- Claude Code `/deep-research`: ~15 fetch slots, but the budget filter is `if (fetchSlots <= 0 && relRank[r.relevance] >= 1)` — only *medium and low* relevance results are dropped once the budget is gone, so high-relevance results are always fetched and the real count can exceed 15 (workflow script).
- LangChain ODR: bounded by 5 concurrent researchers × 10 tool calls × 6 supervisor iterations [github.com/langchain-ai/open_deep_research @ 1b7d2e8].
- dzhng at defaults: 12 searches × 5 results = up to 60 pages scraped.
- DEER finds the opposite problem at the other end: "`ref_amount` is low in Information Sufficiency, suggesting that systems tend to rely on a small number of references rather than leveraging a broad set of sources" [https://arxiv.org/html/2512.17776v4].

### 2.7 Query reformulation

Two findings pull in different directions:

- In conversational/multi-turn RAG, query rewriting is a large win — one 2026 SemEval system reports nDCG@5 0.3457 → 0.3938 with official rewrites and 0.4144 with custom rewrites [https://arxiv.org/pdf/2606.28352].
- In *agentic* search, trace analysis suggests the marginal value is lower, because "agents already know how to expand, narrow and change queries"; observed agent traces instead show high probability of terminating or **re-issuing a previously submitted query** rather than genuinely reformulating [https://arxiv.org/html/2602.17518v1].

Anthropic's prescription targets the same defect from the prompt side: "We counteracted this tendency by prompting agents to start with short, broad queries, evaluate what's available, then progressively narrow focus" — introduced because agents were writing overly long, over-specific queries that returned nothing [https://www.anthropic.com/engineering/multi-agent-research-system].

**Evidence summary for §2:** iterate rather than single-shot (strong); rebuild a compact workspace rather than accumulate history (strong, IterResearch, and it works without training); read full pages, never cite snippets (moderate-strong in direction, weak on exact magnitude); explicit stopping criteria based on evidence sufficiency rather than fixed counts (moderate); start broad then narrow (moderate, engineering report only); dedupe queries and detect no-new-URL saturation (weak-moderate).

---

## 3. Multi-agent orchestration

### 3.1 The headline pro-multi-agent evidence

Anthropic: "the multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on our internal research eval", with parallelisation cutting "research time by up to 90% for complex queries" via "(1) the lead agent spins up 3-5 subagents in parallel rather than serially; (2) the subagents use 3+ tools in parallel" [https://www.anthropic.com/engineering/multi-agent-research-system].

The cost side of the same post: "agents typically use about **4× more tokens** than chat interactions, and multi-agent systems use about **15× more tokens** than chats". Their explanatory analysis: "three factors explained 95% of the performance variance" and "**token usage by itself explains 80% of the variance**".

That last figure is the most important single number in this survey, and it cuts against the architecture claim as much as for it: if 80% of performance variance is explained by tokens spent, then a large part of "+90.2% from multi-agent" is "+90.2% from spending 15× the tokens". Anthropic's later, more cautious guidance puts multi-agent overhead at "typically **3-10× more tokens** than single-agent approaches for equivalent tasks" [https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them].

### 3.2 The independent evidence is more equivocal

**LiveResearchBench (17 systems, 100 expert-curated scenarios)** is the only public benchmark that groups systems by architecture [https://arxiv.org/html/2510.14240v2]:

| Metric | Single-agent web | Single-agent deep research | Multi-agent deep research |
|---|---|---|---|
| Presentation & organisation | 72.7 | 72.1 | **77.7** |
| Coverage & comprehensiveness | 64.7 | **76.3** | 66.8 |
| Factual & logical consistency | **69.7** | 61.2 | 65.9 |
| Citation association | 57.9 | 52.9 | **69.3** |
| Overall | 62.8 | 63.3 | **69.5** |

Multi-agent wins overall, and the paper attributes the win specifically to "explicit steps for aligning sub-agent outputs with citations" — i.e. to the **citation-alignment stage**, not to parallelism. Note that multi-agent is *worse* than single-agent deep research on coverage (66.8 vs 76.3) and worse than single-agent web on consistency. Their named bottleneck for multi-agent systems: when "retrieval into thousands" exceeds context windows, the systems lack "mechanisms to label related content" or compress effectively [https://arxiv.org/html/2510.14240v2].

**Against multi-agent, under matched compute:** "Recent work reports strong performance from multi-agent LLM systems (MAS), but these gains are often confounded by increased test-time computation. When computation is normalized, single-agent systems (SAS) can match or outperform MAS… We find that SAS consistently match or outperform MAS on multi-hop reasoning tasks when reasoning tokens are held constant" [https://arxiv.org/abs/2604.02460]. Models: Qwen3, DeepSeek-R1-Distill-Llama, Gemini 2.5. The authors' own scope limit is important: the claim is about **multi-hop reasoning under matched reasoning-token budgets**, and they concede "multi-agent systems become competitive when a single agent's effective context utilization is degraded, or when more compute is expended" — which is exactly the deep-research regime.

**Kimi-Researcher rejected the workflow-multi-agent design outright**, arguing workflow systems are "tied to specific LLM versions and need frequent manual updates as models or environments change, reducing scalability and flexibility", and instead trained one agent end-to-end to 26.9% pass@1 on HLE (40.17% pass@4) [https://moonshotai.github.io/Kimi-Researcher/].

### 3.3 What Anthropic itself says the decomposition rule is

Their 2026 guidance is notably narrower than the 2025 blog post. Multi-agent helps in exactly three situations — **context protection** ("each operating in its own clean context"), **parallelisation** ("explore a larger search space than a single agent can cover"), and **specialisation** — and the core principle is "**context-centric decomposition over problem-centric**. Divide work by what context agents actually need, not by task type" [https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them].

Two failed patterns are named explicitly: **sequential workflow phases** ("Planning, implementation, and testing of the same feature share too much context") and **problem-centric decomposition**, where teams built "elaborate multi-agent architectures only to discover that improved prompting on a single agent achieved equivalent results" [https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them].

And the one pattern they call most reliable is directly relevant to §4: "**A dedicated agent whose sole responsibility is testing or validating the main agent's work**" — reliable precisely because "verification requires minimal context transfer" [https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them].

### 3.4 Parallel rollouts duplicate rather than complement

Argus states the problem precisely: "deep research answers are composed of complementary pieces of evidence, which parallel rollouts often duplicate rather than complete, yielding diminishing returns while pushing the aggregation context toward the model's limit" [https://arxiv.org/abs/2605.16217]. Their fix — a Searcher/Navigator pair treating research as assembling complementary evidence — yields +5.5 points with a single searcher, +12.7 points averaged over eight benchmarks with 8 parallel searchers, and 86.2 on BrowseComp with 64 searchers, while the Navigator's reasoning context stays below 21.5K tokens [https://arxiv.org/abs/2605.16217].

Tongyi's Heavy mode is the simpler version of the same idea — n parallel agents plus a synthesis model over their *compressed* reports — and it buys real gains: HLE 32.9% → 38.3%, BrowseComp 43.4% → 58.3%, BrowseComp-ZH 46.7% → 58.1% [https://arxiv.org/html/2510.24701v1].

Manus takes context isolation to its limit: one subagent per item, up to 500; "the sub-agents do not communicate with each other, all coordination flows through the main controller"; "an error or hallucination in one sub-agent's job does not propagate to the others" [https://manus.im/blog/manus-wide-research-solve-context-problem]. Their quality claims ("no degradation curve, no fabrication threshold") are vendor assertions with no published measurement — **unverified**.

### 3.5 Context management: compression, files, and what is passed between agents

- **Compression as a first-class stage.** LangChain ODR gives compression its own model and token budget (`compression_model` = gpt-4.1, `compression_model_max_tokens` = 8192), separate from summarization (gpt-4.1-mini, 8192) and the final report (gpt-4.1, 10000); `max_content_length` = 50000 caps raw page text [github.com/langchain-ai/open_deep_research @ 1b7d2e8]. Rationale: "Each sub-agent cleans up its findings and returns them to the supervisor" rather than raw tool output, "preventing token bloat" [https://www.langchain.com/blog/open-deep-research].
- **Compression has measurable value and measurable risk.** ACON "reduces peak token usage by 26-54% while improving task success" and gives "up to 46% performance improvement by mitigating context distraction" for smaller models acting as long-horizon agents [https://arxiv.org/abs/2510.00615]. But the choice of summariser matters a great deal: changing only the summarising agent moved SWE-Verified accuracy from 49.0 to 55.5, **6.5 absolute points** [https://arxiv.org/html/2607.05378v1]. Naive truncation or generic summarisation "easily lose critical details essential for long-horizon reasoning" [https://arxiv.org/html/2607.05378v1].
- **Filesystem / artifacts as memory.** Anthropic: "Rather than requiring subagents to communicate everything through the lead agent, implement artifact systems where specialized agents can create outputs that persist independently" [https://www.anthropic.com/engineering/multi-agent-research-system].
- **Script variables as memory.** Claude Code workflows do the same thing without a filesystem: "Intermediate results stay in script variables instead of landing in Claude's context", and "a workflow script holds the loop, the branching, and the intermediate results itself, so Claude's context holds only the final answer" [https://code.claude.com/docs/en/workflows].

### 3.6 Practical limits of the Claude Code workflow runtime

Relevant to any skill designed for this harness [https://code.claude.com/docs/en/workflows]:

- Up to **16 concurrent agents** (fewer on fewer CPUs), **1,000 agents total per run**, **4,096 items** max in a single `parallel()`/`pipeline()` call.
- A `Large workflow` warning fires above **25 scheduled agents** or a projected **1.5M tokens**.
- Default size guideline is `medium` = "fewer than 15 agents"; `small` = <5, `large` = <50.
- Fan-out agents that share a prompt-cache prefix are staggered up to 5s so all but the first read the cached prefix.
- Failure resumption is coarse: "If a script starts A, B, C, and D in that order and B fails, relaunching returns A from cache and runs B, C, and D again."

**Evidence summary for §3:** context isolation per researcher (strong); compression before handoff (strong, but the summariser prompt is itself high-leverage); a dedicated citation/verification agent (moderate-strong — LiveResearchBench attributes the multi-agent win to citation alignment, and Anthropic calls verification the most reliable multi-agent pattern); raw parallelism as a quality lever (weak — confounded with token spend, and parallel rollouts duplicate evidence); one-agent-per-angle for *research* but never for *writing* (moderate — LangChain's disjointness finding).

---

## 4. Claim extraction and verification

### 4.1 The pipeline shapes in use

**Claude Code `/deep-research`** is the most explicit claim-centric design available. From the workflow script (constants `VOTES_PER_CLAIM = 3`, `REFUTATIONS_REQUIRED = 2`, `MAX_FETCH = 15`, `MAX_VERIFY_CLAIMS = 25`):

- Extraction: per fetched source, 2-5 **falsifiable** claims, each with a **direct quote**, an importance rating (central/supporting/tangential) and a source-quality grade (primary/secondary/blog/forum/unreliable), plus a publish date.
- Ranking: claims sorted by importance then source quality, truncated to 25.
- Verification: 3 independent adversarial voters per claim, each told "Be SKEPTICAL. Try to REFUTE this claim", each running its own WebSearch for contradicting evidence, against a 5-point checklist (quote actually supports the claim? contradicted? source quality sufficient for claim strength? outdated? marketing/press-release/cherry-picked/forum speculation?).
- Adjudication: ≥2 refute votes kills the claim; <2 refutes with ≥2 valid votes survives; too few valid votes → **unverified** (explicitly distinguished from refuted, so a rate-limit storm is reported as infra failure, not as "research found nothing").
- Transparency: refuted and unverified claims are listed in the report.

**Anthropic Research** places verification differently: a separate **CitationAgent** "processes the documents and research report to identify specific locations for citations" — attribution is a post-hoc pass over the finished draft rather than a gate on claims [https://www.anthropic.com/engineering/multi-agent-research-system].

**Hermes `grounded-citations`** (prior art in this repo) inverts the trust model: a ledger script owns the `url → [n]` mapping and rejects verbatim quotes that do not literally appear in fetched page text [research/prior-art/README.md].

### 4.2 Does verification actually help?

Yes, but the well-evidenced form is *decomposed, evidence-seeking* verification, not adversarial voting.

- **FineVerify** decomposes each question into checkable sub-questions, verifies sampled candidates against each sub-question, and selects the highest aggregated score. With 4 sampled trajectories it improves GPT-5-mini by **8.2pp** and Gemini-3-flash by **5.6%** on average across four agentic-search benchmarks; with 12 samples GPT-5-mini surpasses frontier GPT-5 on BrowseComp-Plus [https://arxiv.org/abs/2606.00660]. (An earlier PDF-derived extraction of this paper produced plausible-looking but fabricated figures — 15-25pp gains, 2-5% over-rejection — which the abstract does not support. Those numbers are **discarded**, and the episode is itself a data point about snippet/summary-mediated extraction.)
- **DeepVerifier / verification-time scaling**: rubric-guided iterative verification of a policy model's outputs gives "12%-48% improvement in meta-evaluation F1" over agent-as-judge and LLM-judge baselines, and "8%-11% accuracy gains on challenging subsets of GAIA and XBench-DeepSearch" [https://arxiv.org/abs/2601.15808].
- **DRIFT**, a claim-centric auditing framework (Claim Keeper ledger of commitments, Support Seeker classifying evidence as direct/weak/missing/conflicting, Dependency Tracer marking downstream propagation), improved error-localisation F1 by **up to 28 percentage points** over bare prompting [https://arxiv.org/html/2606.02060].
- **Marco DeepResearch** builds verification into every stage and reports that an 8B agent under a 600-tool-call budget approaches or surpasses several 30B-scale agents such as Tongyi DeepResearch-30B on BrowseComp/BrowseComp-ZH [https://arxiv.org/abs/2603.28376]. No component ablation is given in the abstract — **unverified**.

### 4.3 Where verification goes wrong, and why "default to refuted" is risky

Three independent lines of evidence bear on the Claude Code verifier design.

**(a) Intrinsic self-correction degrades accuracy.** Without external feedback, asking a model to review and revise its own answer *lowers* accuracy [https://arxiv.org/html/2310.01798v2]:

| Dataset | GPT-3.5 r0 → r1 → r2 | GPT-4 r0 → r1 → r2 |
|---|---|---|
| GSM8K | 75.9 → 75.1 → 74.7 | 95.5 → 91.5 → 89.0 |
| CommonSenseQA | 75.8 → 38.1 → 41.8 | 82.0 → 79.5 → 80.0 |
| HotpotQA | 26.0 → 25.0 → 25.0 | 49.0 → 49.0 → 43.0 |

And the direction of changes is asymmetric: "Among the remaining instances, the model is more likely to modify a correct answer to an incorrect one than to revise an incorrect answer to a correct one" [https://arxiv.org/html/2310.01798v2]. The mitigating factor in Claude Code's design is that its verifiers *do* run an external WebSearch, which is exactly the "external feedback" condition under which the paper says self-correction works.

**(b) Multi-agent debate underperforms self-consistency at matched budget.** Same paper, Table 7: at 6 responses, self-consistency 85.3% vs multi-agent debate 83.2%; at 9 responses, 88.2% vs 83.0% [https://arxiv.org/html/2310.01798v2]. Three *independent* verifiers voting is closer to self-consistency than to debate, which is the better side of this comparison — but only because the voters do not see each other's arguments.

**(c) A determined adversary can flip a judge.** The CW-POR study puts one agent defending a falsehood against one giving the true answer, with the same architecture judging: "even smaller models can forcefully and confidently advocate for false claims, eliciting high-confidence errors from their judging counterpart", and models showed *greater* misjudgment on non-adversarially-framed questions — a "false sense of security" effect [https://arxiv.org/html/2504.00374]. Per-model CW-POR rates are **unverified** (figures only, no table extracted).

Taken together: a verifier prompted "Be SKEPTICAL. Try to REFUTE this claim… **Default to refuted=true if uncertain**" (Claude Code workflow script, verbatim) is an asymmetric-loss design. It will preferentially delete true-but-hard-to-corroborate claims — which is precisely the failure mode that harms **fact recall**, the metric this project targets. No published false-refutation rate exists for this specific scheme; measuring it is a genuine gap.

### 4.4 Where errors actually occur in the trajectory

Span-level error localisation over 2,790 trajectories (MiroFlow, OAgent; GPT-5.4, Gemini-2.5-Pro, Claude-Sonnet-4.5, DeepSeek-V3.2; GAIA/XBench/BrowseComp) gives stage-normalised error rates: **retrieval 2.9%** (highest trajectory volume, lowest risk), **decision-making 60.5%**, **finalization 51.8%** [https://arxiv.org/html/2606.02060]. The authors' conclusion: failures "emerge from *how agents commit to information* rather than from search activity itself". (Intermediate stage figures in that extraction were flagged as estimates and are **not used here**.)

Hallucination taxonomy across six deep-research agents on 100 queries [https://arxiv.org/html/2601.22984]:

| System | Fabrication | Misattribution | Noise-induced | Intent-deviation | Intent-neglect | Propagation | Overall |
|---|---|---|---|---|---|---|---|
| OpenAI | 0.1477 | 0.0730 | 0.3121 | 0.0392 | 0.0401 | 0.0064 | 0.1546 |
| Qwen | 0.1161 | 0.1150 | 0.2374 | 0.0197 | 0.1070 | 0.0169 | 0.1560 |
| Gemini | 0.1086 | 0.1085 | 0.2786 | 0.0051 | 0.1866 | 0.0119 | 0.1749 |
| Perplexity | 0.1012 | 0.1208 | 0.3940 | 0.0297 | 0.1865 | 0.0016 | 0.2084 |

**Noise-induced failure — evidence was retrieved but not used — is by far the largest category** (0.24-0.48 across systems, vs 0.10-0.15 for fabrication), attributed to "long-context prioritization difficulties" [https://arxiv.org/html/2601.22984]. Also: ">57% of source errors occur in the early stage" for Gemini and OpenAI, so early errors compound [https://arxiv.org/html/2601.22984]. The same paper notes it does **not** ablate whether requiring citations prevents hallucination, and observes that systems trade fabrication against misattribution rather than achieving uniformly low error.

The practical implication for architecture is uncomfortable for verification-heavy designs: the dominant error is *under-use of retrieved evidence*, which a claim-refutation stage does not address at all. Extraction coverage and evidence prioritisation matter more than adjudication.

### 4.5 Source-quality grading

Claude Code grades every source primary/secondary/blog/forum/unreliable and uses it as a tiebreak in claim ranking (`qualRank`), and the verifier checklist asks "Is the source quality sufficient for the claim's strength? (extraordinary claims need primary sources)" (workflow script). STORM filters retrieved sources against Wikipedia reliability guidelines [https://arxiv.org/html/2402.14207v2]. LiveResearchBench's DeepEval scores "domain authoritativeness… penalizing reliance on low-quality or unverifiable outlets even if the content matches the claim" [https://arxiv.org/html/2510.14240v2]. I found **no ablation** measuring whether source-quality grading improves report accuracy — treat as sound practice with no direct quantitative support (**unverified**).

---

## 5. Synthesis and writing

### 5.1 Section-by-section with per-section retrieval

STORM writes each section separately, retrieving from the collected reference pool by semantic similarity (Sentence-BERT) using the section title and subsection headings as the query; sections are generated in parallel, then a pass prompts the model to "delete repeated information" across the concatenation, then the lead/summary section is written last [https://arxiv.org/html/2402.14207v2]. GPT Researcher does the analogous thing with parallel per-section researchers and a writer that assembles [multi_agents/README.md].

LangChain ODR tried this and **abandoned it**: early versions wrote report sections in parallel across sub-agents and produced "disjoint" results due to poor coordination; they restricted multi-agent work to research only and write the report in one shot from the brief plus findings [https://www.langchain.com/blog/open-deep-research]. This is the single clearest "multi-agent hurts" data point in the deep-research literature, and it is specifically about *writing*, not research.

### 5.2 Review/revise loops are not reliably beneficial

GPT Researcher runs reviewer → revisor "until it is satisfactory" [multi_agents/README.md]. But a dedicated study of multi-turn report revision finds revision cycles frequently *regress* reports — introducing new errors, dropping accurate citations, and contracting coverage — and recommends investing in first-pass quality over revision loops [https://arxiv.org/pdf/2601.13217]. **unverified**: exact percentages and the full system list were not extractable from the PDF; the qualitative conclusion was consistent across the extraction. This aligns with the intrinsic-self-correction result in §4.3.

The contrast with WebThinker matters: interleaving drafting *with retrieval* helps a lot (removing autonomous drafting: 8.1 → 6.6, −18.5% [https://arxiv.org/html/2504.21776v2]), while revising a finished draft *without new retrieval* does not. Whether a revision pass has fresh evidence attached appears to be the discriminating variable.

### 5.3 Deduplication and confidence ranking

- Claude Code's synthesis prompt explicitly instructs: "Identify claims that say the same thing — merge them, combine their sources", then group into findings, then assign confidence high/medium/low by source count and vote unanimity, then list caveats and 2-4 open questions (workflow script).
- STORM's dedup is a post-concatenation "delete repeated information" prompt [https://arxiv.org/html/2402.14207v2].
- dzhng dedups only at the string level (`new Set(...)` over learnings and URLs) — no semantic dedup [github.com/dzhng/deep-research `src/deep-research.ts`].

### 5.4 "Summary without analysis" is the field's dominant failure mode

This is the most consistently replicated finding across independent benchmarks:

- LiveResearchBench: "Most systems are **deep searchers, not deep researchers**… functioning as information collectors and organizers rather than writers of evidence-grounded, argumentative reports" [https://arxiv.org/html/2510.14240v2].
- DeepResearch Bench II: Presentation scores run **74.59-91.85%** while Information Recall runs **22.95-39.98%** and Analysis **35.89-51.91%**; Grok Deep Search scores 91.42 presentation against 33.52 recall. "High presentation scores are decoupled from recall or analysis — well-structured but shallow or incomplete reports are common" [https://arxiv.org/html/2601.08536v2].
- TaxoBench: "the best agent retrieves only **20.92%** of expert-cited papers, and none of 70 standard Bottom-Up runs reaches the experts' average depth of 4.86"; systems that match expert depth do so by fragmenting the taxonomy; humans lead depth-matched systems by **13.27pp** on ARI. The authors conclude retrieval and hierarchical organization are **separate bottlenecks** [https://arxiv.org/abs/2601.12369].
- DEER: Request Fulfillment scores 4.11-5.57 and Analytical Soundness 4.34-6.18 across models, the two lowest dimensions; and, strikingly, "Reasoning models without web search (`think`) outperform `think+search` and `deep` on report-quality metrics excluding information-related scores. This suggests that integrating diverse external information can blur the problem definition and argument structure" [https://arxiv.org/html/2512.17776v4].

That last DEER finding deserves emphasis for anyone designing a research pipeline: **adding retrieval measurably degrades argument structure unless the synthesis stage is designed to resist it.** Recall and coherence trade off, and most systems are optimising the wrong one.

### 5.5 Length control

LangChain ODR gives the report model its own token cap (`final_report_model_max_tokens` = 10000) [github.com/langchain-ai/open_deep_research @ 1b7d2e8]. GPT Researcher uses `TOTAL_WORDS` = 1200 [gpt-researcher @ 6f99857]. Claude Code's report schema requires a "3-5 sentence executive summary" and imposes no length cap on findings (workflow script). No comparative evidence found on length control's effect on quality (**unverified**).

---

## 6. Training-time vs prompt-time architectures

RL-trained research agents (Tongyi DeepResearch, WebSailor, WebThinker, Kimi-Researcher, OpenAI DR, Marco DeepResearch) and prompt/workflow-orchestrated systems (Claude Code `/deep-research`, LangChain ODR, GPT Researcher, STORM, dzhng, Jina) sit on a spectrum, and it is worth being precise about what crosses over.

**What transfers to a prompt-only skill:**

- **Workspace reconstruction.** IterResearch's biggest result is that it works *without any training*: on frontier models used purely as a prompting strategy, o3 goes 34.1% → 46.8% and DeepSeek-V3.1 goes 23.1% → 42.3% on BrowseComp vs ReAct [https://arxiv.org/html/2511.07327]. Periodically rewriting a compact "evolving report + last observation" state is a prompt discipline.
- **Parallel-then-synthesise (Heavy mode).** n independent trajectories plus a synthesis step over their *compressed* reports is architectural, not trained: HLE 32.9 → 38.3, BrowseComp 43.4 → 58.3 [https://arxiv.org/html/2510.24701v1].
- **Decomposed verification.** FineVerify's decompose-into-sub-questions-then-check is a prompt-time procedure [https://arxiv.org/abs/2606.00660], as is DRIFT's claim ledger [https://arxiv.org/html/2606.02060].
- **Interleaved draft-and-deepen.** WARP and WebThinker's think-search-draft are both expressible as prompt structure [https://arxiv.org/html/2602.06540v1; https://arxiv.org/html/2504.21776v2].
- **Broad-to-narrow query discipline and explicit effort scaling rules** [https://www.anthropic.com/engineering/multi-agent-research-system].

**What does not transfer:**

- Emergent behaviours Kimi-Researcher attributes to RL — cross-source verification reflexes and "epistemic caution" (extra searches even on easy questions) — are learned policies, though they can be *approximated* by explicitly instructing the behaviour [https://moonshotai.github.io/Kimi-Researcher/].
- Long-horizon focus over hundreds of steps without drift (OpenAI DR's trained property) [https://cdn.openai.com/deep-research-system-card.pdf].
- Interaction-count extrapolation (T_max 32 → 2048 at inference) depends on RL exposure to the paradigm [https://arxiv.org/html/2511.07327].
- Kimi's argument against workflow systems — that they are "tied to specific LLM versions and need frequent manual updates" — is a real maintenance cost that a prompt-only skill inherits [https://moonshotai.github.io/Kimi-Researcher/].

**Also worth noting:** HuggingFace's open-deep-research found the *action format* mattered more than tool sophistication — switching from code-writing actions to JSON tool calls dropped GAIA validation from 55.15% to 33% [https://huggingface.co/blog/open-deep-research]. For a Claude Code skill this is a reminder that the shape of the agent's action space is a first-order variable, not a detail.

---

## 7. Published ablations and quantitative evidence, collected

### 7.1 Decomposition on/off

| Ablation | Result | Source |
|---|---|---|
| STORM w/o Conversation (GPT-4), heading entity recall | 45.91 → 39.30 | https://arxiv.org/html/2402.14207v2 |
| STORM w/o Perspective (GPT-4), heading entity recall | 45.91 → 42.70 | https://arxiv.org/html/2402.14207v2 |
| STORM w/o Conversation (GPT-3.5), entity recall | 40.52 → 31.98 | https://arxiv.org/html/2402.14207v2 |
| Plan-then-write vs interleaved WARP | Insight 51.60 → 52.79; Comprehensiveness 49.35 → 50.33 | https://arxiv.org/html/2602.06540v1 |
| Hypothesis-conditioned vs plain query rewriting, Decision-Useful Rate (MedQA) | 56.1% → 82.1% | https://arxiv.org/html/2603.19008 |

### 7.2 Iterative vs single-pass search

| Ablation | Result | Source |
|---|---|---|
| Mono-context agent vs IterResearch, identical training data | 36.5% → 49.1% avg (+12.6pp), despite mono having a larger 64K context | https://arxiv.org/html/2511.07327 |
| ReAct vs IterResearch prompting, o3 on BrowseComp | 34.1% → 46.8% | https://arxiv.org/html/2511.07327 |
| ReAct vs IterResearch prompting, DeepSeek-V3.1 on BrowseComp | 23.1% → 42.3% | https://arxiv.org/html/2511.07327 |
| Interaction budget scaling (BrowseComp subset) | 2 → 5.5%; 2⁴ → 14.3%; 2⁷ → 50.1%; 2¹¹ → 42.5% (peak near 2⁷) | https://arxiv.org/html/2511.07327 |
| Deepening steps in report generation | ~+6 points on Comprehensiveness/Insight up to ~9 steps, then plateau | https://arxiv.org/html/2602.06540v1 |
| WebThinker w/o Deep Web Explorer (reasoning avg) | 45.4 → 38.3 (−15.1%) | https://arxiv.org/html/2504.21776v2 |
| WebThinker w/o link clicking | 45.4 → 42.6 (−6.2%) | https://arxiv.org/html/2504.21776v2 |
| WebThinker w/o autonomous report drafting (Glaive avg) | 8.1 → 6.6 (−18.5%) | https://arxiv.org/html/2504.21776v2 |
| WebThinker w/o report check & edit (Glaive avg) | 8.1 → 7.7 (−4.9%) | https://arxiv.org/html/2504.21776v2 |

### 7.3 Parallelism and number of sub-agents

| Ablation | Result | Source |
|---|---|---|
| Multi-agent (Opus 4 lead + Sonnet 4 subs) vs single-agent Opus 4, internal research eval | +90.2% | https://www.anthropic.com/engineering/multi-agent-research-system |
| Token usage alone as explanation of performance variance | 80% of variance (95% with three factors) | https://www.anthropic.com/engineering/multi-agent-research-system |
| Multi-agent token overhead | ~15× a chat; ~4× for single agents vs chat | https://www.anthropic.com/engineering/multi-agent-research-system |
| Multi-agent token overhead (later, narrower guidance) | 3-10× single-agent for equivalent tasks | https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them |
| Parallelisation effect on latency | up to 90% reduction in research time for complex queries | https://www.anthropic.com/engineering/multi-agent-research-system |
| LiveResearchBench, architecture class overall | single web 62.8, single deep 63.3, multi-agent 69.5 | https://arxiv.org/html/2510.14240v2 |
| LiveResearchBench, coverage by class | single deep 76.3 **>** multi-agent 66.8 | https://arxiv.org/html/2510.14240v2 |
| LiveResearchBench, citation association by class | multi-agent 69.3 **>** single web 57.9 **>** single deep 52.9 | https://arxiv.org/html/2510.14240v2 |
| Single vs multi-agent under matched reasoning tokens (multi-hop QA) | SAS consistently match or outperform MAS | https://arxiv.org/abs/2604.02460 |
| Argus, 1 searcher | +5.5 points | https://arxiv.org/abs/2605.16217 |
| Argus, 8 parallel searchers | +12.7 points avg over 8 benchmarks | https://arxiv.org/abs/2605.16217 |
| Argus, 64 searchers | 86.2 on BrowseComp; navigator context <21.5K tokens | https://arxiv.org/abs/2605.16217 |
| Tongyi standard vs Heavy (parallel + synthesis) | HLE 32.9→38.3; BrowseComp 43.4→58.3; BrowseComp-ZH 46.7→58.1 | https://arxiv.org/html/2510.24701v1 |
| Parallel section-*writing* across sub-agents | abandoned: results "disjoint" | https://www.langchain.com/blog/open-deep-research |

### 7.4 Verification on/off

| Ablation | Result | Source |
|---|---|---|
| FineVerify (4 samples) vs standard scaling | +8.2pp GPT-5-mini, +5.6% Gemini-3-flash, avg over 4 benchmarks | https://arxiv.org/abs/2606.00660 |
| FineVerify (12 samples) | GPT-5-mini surpasses frontier GPT-5 on BrowseComp-Plus | https://arxiv.org/abs/2606.00660 |
| DeepVerifier rubric-guided verification | +8-11% accuracy on hard GAIA/XBench-DeepSearch subsets; +12-48% meta-eval F1 | https://arxiv.org/abs/2601.15808 |
| DRIFT claim-ledger auditing vs bare prompting | up to +28pp error-localisation F1 | https://arxiv.org/html/2606.02060 |
| Intrinsic self-correction, GPT-4 GSM8K, rounds 0→1→2 | 95.5 → 91.5 → 89.0 | https://arxiv.org/html/2310.01798v2 |
| Intrinsic self-correction, GPT-3.5 CommonSenseQA | 75.8 → 38.1 → 41.8 | https://arxiv.org/html/2310.01798v2 |
| Self-consistency vs multi-agent debate at 9 responses | 88.2% vs 83.0% | https://arxiv.org/html/2310.01798v2 |
| Multi-turn report revision loops | frequent regressions: new errors, dropped citations, reduced coverage (**unverified** magnitudes) | https://arxiv.org/pdf/2601.13217 |

### 7.5 Compression vs raw handoff

| Ablation | Result | Source |
|---|---|---|
| ACON context compression | peak tokens −26-54% **while improving** task success; up to +46% for small models | https://arxiv.org/abs/2510.00615 |
| Swapping only the summarising agent | SWE-Verified 49.0 → 55.5 (+6.5pp) | https://arxiv.org/html/2607.05378v1 |
| Compression before supervisor handoff | qualitative: prevents token bloat and context-window failures | https://www.langchain.com/blog/open-deep-research |

### 7.6 Reasoning effort levels

FutureSearch's Deep Research Bench measurements [https://futuresearch.ai/effort-paradox/]:

| Model | Low | Medium | High | Cost low → high |
|---|---|---|---|---|
| Claude 4.5 Opus | 54.9% | — | 54.8% | $0.31 → $0.46 (+47%) |
| Claude 4.6 Opus | 53.1% | — | 55.0% | $0.24 → $0.55 (+128%) |
| Gemini 3 Flash | 49.9% | — | 47.9% | $0.05 → $0.14 (~3×) |
| GPT-5 | 49.6% | 48.6% | 48.1% | $0.25 → $0.35 → $0.39 |

Their explanation is directly architectural: "More cycles spent deliberating doesn't help when the bottleneck is information retrieval, not reasoning depth" [https://futuresearch.ai/effort-paradox/]. Anthropic models are the exception where higher effort pays [https://futuresearch.ai/effort-scaling/].

### 7.7 Retrieval quality and source count

| Finding | Result | Source |
|---|---|---|
| BrowseComp-Plus: retriever swap | GPT-5 55.9% → 70.1% with Qwen3-Embedding-8B, **with fewer search calls** | https://arxiv.org/abs/2508.06600 |
| BrowseComp-Plus: snippet vs full document | 35.42% → 43.61% (+8.19pp); ~0.27 get-document calls/query (**unverified** — model identity disputed, table not extracted) | https://arxiv.org/abs/2508.06600 (secondary summaries) |
| SAGE: BM25 vs LLM-based retrievers for DR agents | BM25 outperforms LLM retrievers by ~30%, because agents emit keyword-oriented sub-queries | https://arxiv.org/abs/2602.05975 |
| SAGE: corpus-level test-time scaling (metadata/keyword augmentation) | +8% short-form, +2% open-ended | https://arxiv.org/abs/2602.05975 |
| TaxoBench: expert-cited-paper retrieval | best agent recovers 20.92% | https://arxiv.org/abs/2601.12369 |
| DRB-II: information recall vs presentation | recall 22.95-39.98% vs presentation 74.59-91.85% | https://arxiv.org/html/2601.08536v2 |
| DEER: reference diversity | systems "rely on a small number of references rather than leveraging a broad set of sources" | https://arxiv.org/html/2512.17776v4 |
| Hallucination taxonomy: dominant category | noise-induced (retrieved-but-unused evidence) 0.24-0.48 vs fabrication 0.10-0.15 | https://arxiv.org/html/2601.22984 |
| Span-level errors by stage | retrieval 2.9%; decision-making 60.5%; finalization 51.8% | https://arxiv.org/html/2606.02060 |
| Kimi-Researcher URLs per task | >200 explored, ~23 reasoning steps | https://moonshotai.github.io/Kimi-Researcher/ |

### 7.8 The recall bottleneck, stated plainly

Four independent benchmark teams, using four different methodologies, converge on the same diagnosis:

1. **DRB-II**: "even the strongest agents fail to pass more than half of the rubrics, with especially large deficits in Information Recall and Analysis" [https://arxiv.org/html/2601.08536v2].
2. **TaxoBench**: best agent retrieves 20.92% of expert-cited papers; retrieval and organisation are "separate bottlenecks" [https://arxiv.org/abs/2601.12369].
3. **LiveResearchBench**: systems are "deep searchers, not deep researchers"; all models produce non-trivial citation errors, mostly **unsupported claims rather than invalid URLs**; Open Deep Research averaged 91.9 citation errors per market-analysis report [https://arxiv.org/html/2510.14240v2].
4. **Hallucination trajectory analysis**: the dominant error is failing to use evidence that was already retrieved [https://arxiv.org/html/2601.22984].

The architectural reading: **more searching does not fix this; more careful reading and extraction from what was already found does.** That reframes the whole design brief.

---

## 8. Design recommendation for a prompt-only, keyless Claude Code skill

Targets: **fact recall** and **citation support**. Each item is tagged with evidence strength and token-cost implication.

### Tier 1 — do these first

**R1. Extract claims only from full page text, never from search snippets; require a verbatim quote per claim.**
Evidence: **strong** (full-document access beats snippets [https://arxiv.org/abs/2508.06600]; unsupported claims, not bad URLs, are the dominant citation error [https://arxiv.org/html/2510.14240v2]; the local Hermes prior art rejects quotes absent from fetched text).
Cost: high — full pages are the largest token line item. Mitigate by extracting immediately and discarding raw text.
Status in Claude Code `/deep-research`: **already correct**. Search agents return only pointers; claims come only from `WebFetch` output with a required quote field.

**R2. Rebuild a compact working state each round instead of accumulating history.**
State = (question, evolving findings/report, last observation). Evidence: **strong**, and demonstrated to work as a pure prompting strategy without training (+12.7pp for o3, +19.2pp for DeepSeek-V3.1 on BrowseComp [https://arxiv.org/html/2511.07327]).
Cost: **negative** — this reduces tokens (O(1) instead of O(t) context).
Status: the built-in workflow sidesteps this by holding state in script variables — architecturally equivalent and arguably better [https://code.claude.com/docs/en/workflows]. A skill without the workflow runtime must do it explicitly, in files.

**R3. Spend the marginal token on reading more sources, not on more reasoning or more debate.**
Evidence: **strong**. The bottleneck is recall, not reasoning [https://arxiv.org/html/2601.08536v2; https://arxiv.org/abs/2601.12369], and higher reasoning effort is flat-to-negative on Deep Research Bench for three of four frontier models [https://futuresearch.ai/effort-paradox/].
Cost: reallocation, not increase.
Status: `/deep-research`'s `MAX_FETCH = 15` against `MAX_VERIFY_CLAIMS = 25 × 3 votes = 75 verifier agents` inverts this ratio. **This is the clearest improvement available**: the run spends roughly five times as many agents adjudicating claims as it does gathering them.

**R4. Use one agent per angle for *research*, and a single agent for *writing*.**
Evidence: **strong** for the split (LangChain abandoned parallel section-writing as "disjoint" [https://www.langchain.com/blog/open-deep-research]; multi-agent trails single-agent deep research on coverage 66.8 vs 76.3 [https://arxiv.org/html/2510.14240v2]).
Cost: moderate.
Status: already correct — one synthesis agent.

**R5. Compress each researcher's output before handoff, with a *purpose-written* compression prompt.**
Evidence: **strong** (ACON: −26-54% peak tokens while improving success [https://arxiv.org/abs/2510.00615]; swapping only the summariser moved a benchmark 6.5pp [https://arxiv.org/html/2607.05378v1]; LangChain gives compression its own model and budget).
Cost: **negative** overall.
Status: `/deep-research`'s structured `EXTRACT_SCHEMA` (2-5 claims + quote + grade + date) *is* a compression contract, and a good one. Keep it.

### Tier 2 — strong expected value, moderate evidence

**R6. Decompose by perspective *and* iterate question generation against retrieved answers.**
STORM's ablation says the iteration matters more than the personas (entity recall 40.52 → 31.98 without conversation, vs → 40.12 without perspectives) [https://arxiv.org/html/2402.14207v2].
Evidence: **strong** for iteration, **moderate** for perspectives. Cost: moderate (a second round of question generation per angle).
Status: `/deep-research` generates angles **once**, before any evidence exists — the "w/o Conversation" condition, which is the worse arm of STORM's own ablation. **Improvement: a second decomposition pass after the first search round, seeded by what was found.**

**R7. Condition queries on an explicit working hypothesis.**
Evidence: **moderate** (Decision-Useful Rate 56.1% → 82.1% vs plain rewriting, but in multiple-choice medical QA [https://arxiv.org/html/2603.19008]). Cost: negligible.
Status: absent from `/deep-research`. Low-cost addition to the Scope phase: for each angle, state what you expect to find and what would disconfirm it, then search for both.

**R8. Replace "adversarially refute, default to refuted" with "decompose into checkable sub-questions and seek corroboration".**
Evidence: **moderate-strong**. FineVerify's decompose-and-check gives +8.2pp [https://arxiv.org/abs/2606.00660]; DRIFT's claim ledger gives +28pp on error localisation [https://arxiv.org/html/2606.02060]; self-consistency beats debate at matched budget [https://arxiv.org/html/2310.01798v2]; adversarial advocacy can flip a judge with high confidence [https://arxiv.org/html/2504.00374].
Cost: comparable or lower than 3 votes/claim.
Status: this is the biggest design disagreement with `/deep-research`. Its verifier prompt says verbatim "Default to refuted=true if uncertain", which under a recall-oriented objective is the wrong asymmetry — it deletes true-but-thinly-sourced claims. **Recommendation: keep the 3-vote scheme's independence (it is closer to self-consistency than debate, which the evidence favours) but invert the default to "corroborate or label", and make `unverified` the outcome for uncertainty rather than `refuted`.** The built-in already has an `unverified` bucket; widen its mouth.

**R9. Add a post-hoc citation pass over the finished draft.**
Evidence: **moderate-strong** — LiveResearchBench attributes multi-agent systems' citation-association win (69.3 vs 52.9) specifically to "explicit steps for aligning sub-agent outputs with citations" [https://arxiv.org/html/2510.14240v2], and Anthropic ships a CitationAgent for exactly this [https://www.anthropic.com/engineering/multi-agent-research-system]. Anthropic also names a dedicated verification agent as the most reliable multi-agent pattern, precisely because it needs minimal context transfer [https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them].
Cost: low (one pass over draft + evidence ledger).
Status: `/deep-research` carries source URLs through the claim objects, which is structurally sound, but does not re-verify quote-to-source alignment in the final text. A cheap model-free check (quote containment in fetched raw text) closes this.

**R10. Interleave drafting with retrieval; do not run a blind revise loop.**
Evidence: **moderate** (drafting-during-search removal costs −18.5% [https://arxiv.org/html/2504.21776v2]; interleaved WARP beats plan-then-write [https://arxiv.org/html/2602.06540v1]; revision loops without new evidence regress reports [https://arxiv.org/pdf/2601.13217]; intrinsic self-correction degrades accuracy [https://arxiv.org/html/2310.01798v2]).
Cost: moderate.
Design rule: **every revision pass must be attached to new retrieval, or it should not run.**

**R11. Stop on evidence sufficiency, not on a fixed source count; detect saturation.**
Evidence: **moderate** (premature stopping named as a primary enterprise failure [https://arxiv.org/abs/2604.24978]; Jina's no-new-URLs heuristic disables search for the next round; deepening plateaus near 9 steps [https://arxiv.org/html/2602.06540v1]; interaction scaling peaks around 2⁷ [https://arxiv.org/html/2511.07327]).
Cost: variable, bounded by a hard ceiling.
Status: `/deep-research` uses fixed budgets only. Suggest: continue while new sources yield novel central claims; stop after two consecutive rounds with no novel central claim, or at the hard ceiling.

### Tier 3 — worth doing, weak evidence

**R12. Grade source quality (primary/secondary/blog/forum) and record it.** Evidence: **weak** — universal practice, no ablation found. Cost: negligible. Already in `/deep-research`; keep.

**R13. Ask 2-3 clarifying questions when underspecified, then write a research brief.** Evidence: **moderate** in direction [https://arxiv.org/abs/2602.03468; https://www.langchain.com/blog/open-deep-research], **weak** on magnitude. Cost: negligible. Already in `/deep-research` (as a pre-invocation instruction) and in the project's locked requirements.

**R14. Prescribe effort scaling rules in the prompt.** Evidence: **weak** (engineering report only, no ablation) but the failure it fixes is documented — agents spawning 50 subagents for simple queries [https://www.anthropic.com/engineering/multi-agent-research-system]. Cost: negative. Adopt Anthropic's tiers directly: 1 agent / 3-10 calls for fact-finding; 2-4 subagents / 10-15 calls for comparisons; >10 for genuinely complex research.

**R15. Prompt for broad-then-narrow queries.** Evidence: **weak-moderate** [https://www.anthropic.com/engineering/multi-agent-research-system], with the caveat that agentic search may already do this and that agents' real defect is re-issuing duplicate queries rather than under-reformulating [https://arxiv.org/html/2602.17518v1]. Cost: negligible. Add explicit query deduplication.

**R16. Prefer keyword-shaped queries over long natural-language ones.** Evidence: **weak-moderate** — SAGE found BM25 beat LLM-based retrievers by ~30% precisely because agents emit keyword-oriented sub-queries [https://arxiv.org/abs/2602.05975], which for a keyless skill using a plain web search tool argues for short keyword queries rather than sentence-length ones. Cost: negligible.

### Where the Claude Code built-in `/deep-research` is well-supported by evidence

- **Claims must be falsifiable, quoted, and sourced from fetched pages.** Directly addresses the field's dominant citation error (unsupported claims, not broken URLs) [https://arxiv.org/html/2510.14240v2].
- **Structured extraction schema as an implicit compression contract.** Matches the compression evidence [https://arxiv.org/abs/2510.00615].
- **Independent, non-communicating voters.** Closer to self-consistency than to debate, and self-consistency wins at matched budget [https://arxiv.org/html/2310.01798v2].
- **`unverified` distinguished from `refuted` on infra failure.** Well-designed; the docs confirm it as intended behaviour [https://code.claude.com/docs/en/workflows].
- **Refuted claims listed in the report for transparency.** Supports auditability.
- **Intermediate state kept out of the session context.** "Claude's context holds only the final answer" [https://code.claude.com/docs/en/workflows] — an unusually clean implementation of the context-isolation principle.
- **Semantic-duplicate merging and confidence ranking in synthesis.** Matches STORM's dedup pass and the redundancy findings.
- **High-relevance results bypass the fetch budget cap.** A small but correct choice: the budget never blocks the best source.

### Where it could be improved

1. **Budget allocation is inverted.** ~15 fetch agents vs ~75 verifier agents. Given that recall is the measured bottleneck and retrieval is the *lowest*-error stage (2.9% [https://arxiv.org/html/2606.02060]), shifting agents from verification to fetching should raise recall at equal cost. (**strong**)
2. **"Default to refuted=true if uncertain."** Optimises precision at the direct expense of recall — the wrong asymmetry for this project's stated targets, and unmeasured for false-refutation rate. (**strong reasoning, no direct measurement — a genuine gap worth measuring in the pilot**)
3. **Angles are generated once, before any evidence.** This is STORM's "w/o Conversation" arm, which loses 8.5 points of entity recall. A second, evidence-seeded decomposition round is cheap. (**moderate-strong**)
4. **No re-search loop.** Five parallel searches, one fetch round, done. Every iterative system in this survey outperforms its single-pass counterpart [https://arxiv.org/html/2511.07327]. Even one conditional second round, triggered by unanswered sub-questions, should help. (**strong**)
5. **No hypothesis conditioning.** Angles are topical, not evidentiary. (**moderate**)
6. **No quote-containment check.** Quotes are model-reported from `WebFetch` output; nothing verifies that the quote literally appears in the page. The Hermes prior art shows the model-free version of this check. (**moderate**)
7. **Claim cap of 25 across all sources** (5 per source × 15 sources = up to 75 extracted, 25 kept). For a recall-oriented objective, the cap discards up to two-thirds of extracted evidence before verification. (**moderate**)
8. **No saturation detection or evidence-sufficiency stopping.** Fixed budgets only. (**moderate**)
9. **No explicit "what this could not find" contract**, though the report schema does include `caveats` and `openQuestions`. (**weak-moderate**)

### The one-line version

The evidence says a research architecture should **spend its budget on reading more full pages and extracting more quoted claims, keep a compact rewritten working state instead of a growing transcript, decompose twice (once cold, once after evidence), verify by seeking corroboration rather than by attempting refutation, and write once from the assembled evidence** — because the measured bottleneck is not reasoning, not presentation, and not adjudication, but recall of, and faithful use of, evidence that was already within reach.

---

## Sources (all accessed 2026-09-02)

### Primary system documentation and source code
- Claude Code bundled `deep-research` workflow script, v2.1.258, read locally at `~/.claude/projects/<project>/workflows/scripts/deep-research-wf_*.js` (not redistributed)
- https://code.claude.com/docs/en/workflows
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them
- https://www.langchain.com/blog/open-deep-research
- https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/configuration.py
- https://github.com/langchain-ai/open_deep_research/blob/main/README.md
- https://github.com/assafelovic/gpt-researcher/blob/master/multi_agents/README.md
- https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/config/variables/default.py
- https://github.com/dzhng/deep-research/blob/main/src/deep-research.ts
- https://github.com/dzhng/deep-research/blob/main/README.md
- https://github.com/jina-ai/node-DeepResearch/blob/main/README.md
- https://github.com/stanford-oval/storm
- https://huggingface.co/blog/open-deep-research
- https://moonshotai.github.io/Kimi-Researcher/
- https://manus.im/blog/manus-wide-research-solve-context-problem
- https://cdn.openai.com/deep-research-system-card.pdf

### Papers: architectures
- https://arxiv.org/abs/2402.14207 · https://arxiv.org/html/2402.14207v2 (STORM)
- https://arxiv.org/abs/2408.15232 (Co-STORM)
- https://arxiv.org/abs/2504.21776 · https://arxiv.org/html/2504.21776v2 (WebThinker)
- https://arxiv.org/html/2511.07327 (IterResearch)
- https://arxiv.org/html/2510.24701v1 (Tongyi DeepResearch technical report)
- https://arxiv.org/abs/2605.16217 (Argus)
- https://arxiv.org/html/2602.06540v1 (AgentCPM-Report / WARP)
- https://arxiv.org/abs/2603.28376 (Marco DeepResearch)
- https://arxiv.org/abs/2604.24978 (Don't Stop Early)
- https://arxiv.org/abs/2602.03468 (IntentRL)
- https://arxiv.org/html/2603.19008 (Hypothesis-Conditioned Query Rewriting)
- https://arxiv.org/html/2604.02988v1 (Self-Optimizing Multi-Agent Systems for Deep Research)
- https://arxiv.org/html/2506.18096v1 (Deep Research Agents: A Systematic Examination and Roadmap)
- https://arxiv.org/abs/2508.12752 (Deep Research: A Survey of Autonomous Research Agents)

### Papers: verification, self-correction, context
- https://arxiv.org/abs/2606.00660 (FineVerify)
- https://arxiv.org/abs/2601.15808 (Inference-Time Scaling of Verification / DeepVerifier)
- https://arxiv.org/html/2606.02060 (Span-Level Error Localization / DRIFT / TELBench)
- https://arxiv.org/html/2310.01798v2 (LLMs Cannot Self-Correct Reasoning Yet)
- https://arxiv.org/html/2504.00374 (CW-POR: persuasion overrides truth in multi-agent debate)
- https://arxiv.org/abs/2604.02460 (Single-Agent LLMs Outperform Multi-Agent Systems Under Equal Thinking Token Budgets)
- https://arxiv.org/abs/2510.00615 (ACON context compression)
- https://arxiv.org/html/2607.05378v1 (CompactionRL)
- https://arxiv.org/pdf/2601.13217 (Beyond Single-shot Writing: unreliable multi-turn report revision)

### Papers/benchmarks cited only for architecture-attributed failures
- https://arxiv.org/html/2601.08536v2 (DeepResearch Bench II)
- https://arxiv.org/html/2510.14240v2 (LiveResearchBench)
- https://arxiv.org/html/2512.17776v4 (DEER)
- https://arxiv.org/abs/2601.12369 (TaxoBench / synthesis gap)
- https://arxiv.org/html/2601.22984 (Why Your Deep Research Agent Fails / PING taxonomy)
- https://arxiv.org/abs/2508.06600 (BrowseComp-Plus)
- https://arxiv.org/abs/2602.05975 (SAGE)
- https://arxiv.org/html/2602.17518v1 (A Picture of Agentic Search)
- https://arxiv.org/abs/2602.15112 (ResearchGym)
- https://arxiv.org/pdf/2606.28352 (SemEval-2026 Task 8 query rewriting)
- https://futuresearch.ai/effort-paradox/
- https://futuresearch.ai/effort-scaling/

### Notes on source reliability in this survey
Several arXiv PDFs (2601.12369, 2602.05975, 2605.16217, 2606.00660, 2603.07241, 2604.24978, 2506.06287, 2601.13217, 2602.17518 via PDF) could not be text-extracted through the fetch tool; where an abstract page (`/abs/`) or HTML rendering was available it was used instead, and any number that survived only through a PDF-derived summary is marked **unverified** in the body. One extraction (FineVerify via PDF) produced numbers the abstract contradicts; those were discarded and replaced with the abstract's figures. The Deep Research Bench original paper's failure-mode percentages could not be retrieved at all.
