# What a finished deep-research run produces: survey of existing systems

Date of survey: 2026-09-02. Purpose: inform the output contract of a portable "deep research" skill for AI coding agents. Every fact is followed by its source URL in brackets; items I could not confirm from a primary or near-primary source are marked **unverified**. A few vendor pages (OpenAI help center, OpenAI launch post, Perplexity blog/help center) returned HTTP 403 to the fetch tool, so those systems lean on API docs, Wikipedia, and secondary write-ups.

---

## 1. Comparison table

| System | Output medium | Format / length | Citation style | Intermediate artifacts exposed | User controls |
|---|---|---|---|---|---|
| OpenAI Deep Research (ChatGPT) | Report rendered in chat; since Feb 2026 a full-screen document viewer; export PDF/DOCX (Markdown reported, unverified) | Long structured report with headings, TOC, tables; runs 5-30 min; a hands-on run produced ~12,000 words | Inline hyperlinks/citation chips per claim; sources panel; can produce APA/MLA reference list on request | Clarifying questions before start; live "activity"/reasoning summary; sources sidebar; interruptible mid-run | Clarifying-question answers; restrict to domains/time ranges/connected apps (PubMed, arXiv, MCP); ask for alternate scope/audience/depth |
| OpenAI Deep Research API (o3-deep-research, o4-mini-deep-research) | Responses API `message` item with `output_text` + `annotations` | No enforced structure; prompt-driven (tables, headers requested via rewriting step); tens of minutes | `url_citation` annotations with `start_index`, `end_index`, `title`, `url` (character-span, per claim) | Output array lists `web_search_call` (search/open_page/find_in_page), `code_interpreter_call`, `mcp_tool_call`, reasoning summaries | `max_tool_calls` (primary cost/latency knob), `background=true`, webhooks; recommended 3-step clarify -> rewrite -> research pipeline |
| Google Gemini Deep Research (app) | Report in a Canvas panel; Export to Google Docs; Audio Overview; Copy contents; Share | Multi-section report with key findings; 5-10 min typical, longer for complex | Inline links to original sources; on Docs export a "works cited" section | Editable research plan before execution; "Show thinking"; "Sites browsed" list during run | Edit plan (natural language); follow-up questions/refine sections in Docs; higher limits on paid tiers |
| Gemini Deep Research (API, Interactions API) | `interaction.outputs[-1].text` (Markdown report); optional generated images | Markdown with `#` headers and bullets; max 60 min, most <20 min; two tiers (preview vs Max) | `citations` returned in response (exact format not documented) | Streamed thought summaries (`thinking_summaries: auto`), `content.delta` events; `collaborative_planning=True` returns a plan for approval first | `background=true` required; plan approve/modify; MCP/File Search tools; follow-up turns via `previous_interaction_id` |
| Perplexity Deep Research / Research mode | Chat answer (report); export PDF, save as document, publish as Perplexity Page | "Full-length, structured answer"; API example ~11k completion tokens; 2-4 min typical | Inline numbered citations; API returns `citations[]` URLs + `search_results[]` (title, url, date, snippet) | Visible reasoning/search steps during run; sources counter (**UI detail partly unverified**) | Mode selection; API bills reasoning/citation tokens and search queries separately; Advanced Research on Max tier (**unverified details**) |
| Anthropic multi-agent Research (Claude.ai) | Chat answer / "comprehensive report" with inline citations | "Answers in minutes" (Research) to 5-45 min across "hundreds of sources" (Advanced Research) | Inline citations linking directly to source material; a dedicated CitationAgent inserts them post-hoc | Internally: lead-agent research plan saved to memory, subagent findings; user sees search progress (not documented in detail) | Toggle Research on; connect Google Workspace/integrations; no documented depth knob |
| Claude Code `/deep-research` (bundled workflow) | One cited report delivered into the session at the end (no per-turn transcript) | Claims ranked by confidence; note listing claims killed in verification; unverifiable claims flagged "unverified" | Each surviving claim cites the sources it came from; each extracted claim carries a direct quote and source-quality grade | `/workflows` progress view: phases, per-agent prompt/tool calls/result; the orchestration script is written to disk and can be saved/rerun | Size guideline (small/medium/large), pause/stop/restart agents, edit and relaunch script, `args` input |
| Stanford STORM / Co-STORM | Files on disk per topic (outline txt, article txt, polished article, url_to_info.json, logs) | Wikipedia-like multi-section article + outline; polish step adds a summary section | Inline numbered `[n]` per sentence mapped to `url_to_info.json` | conversation_log.json, raw_search_results.json, direct vs refined outline; Co-STORM: dynamic mind map + discourse turns | `--max-conv-turn`, `--max-perspective`, `--search-top-k`, `--retrieve-top-k`, stage toggles; Co-STORM: observe or inject utterances |
| GPT Researcher (assafelovic) | Markdown string; multi-agent mode publishes MD/PDF/DOCX to `outputs/` | Default `TOTAL_WORDS=1200` ("at least"); 5-6 pages typical; detailed/deep reports longer; ~5 min, ~$0.4 | Markdown hyperlinks at end of sentence/paragraph `([in-text citation](url))` in APA (default; MLA/CMS/Harvard/IEEE) + deduplicated reference list | `get_source_urls()`, `get_research_context()`, `get_costs()`; multi-agent: Editor plan, Reviewer/Revisor feedback, optional human feedback | `report_type` (research/resource/outline/custom/subtopic/detailed/deep), `REPORT_FORMAT`, `TOTAL_WORDS`, `MAX_SUBTOPICS`, `DEEP_RESEARCH_BREADTH/DEPTH`, tone, `publish_formats`, `guidelines` |
| LangChain Open Deep Research | `final_report` state key (Markdown) in LangGraph Studio | Markdown `#`/`##`/`###`; "fairly long and verbose"; sections "as long as necessary" | Inline `[1]` per unique URL, sequential without gaps; `### Sources` list, one per line | Clarifying question(s) (configurable), research brief, compressed per-subagent findings (internal) | `allow_clarification`, `max_concurrent_research_units`, `max_researcher_iterations`, `max_react_tool_calls`, per-role models, `search_api` |
| Hugging Face open-deep-research (smolagents) | Short final-answer string (GAIA-style) | Not a report; benchmark answer | None | Agent step trace | Model choice; no report/format knobs |
| dzhng/deep-research | `report.md` or `answer.md` on disk | Markdown report with all sources/references appended, or a concise answer | Sources list at end (format not specified) | Follow-up clarifying questions before run; learnings + visited URLs accumulated | `breadth` (3-10, default 4), `depth` (1-5, default 2), report vs answer mode, `CONCURRENCY_LIMIT` |
| Jina node-DeepResearch | OpenAI-compatible chat completion (streaming) | Concise answer, explicitly not a long report | GitHub-flavored footnotes `[^1]`; `visitedURLs`/`readURLs` | `<think>` reasoning in stream; definitive-answer evaluator | Token budget ("Beast Mode" when exhausted) |
| Tongyi DeepResearch | Answer to information-seeking benchmarks (BrowseComp, HLE, xbench) | Answer-oriented; no report component documented | Not documented | ReAct trace; IterResearch "heavy" mode | ReAct vs heavy mode |
| WebThinker | Markdown report file (report mode) | Long-form multi-section report drafted during reasoning | Not documented in README/abstract | Draft/check/edit tool calls interleaved with search | QA mode vs report mode |
| Kimi-Researcher / Kimi Deep Research | Report; exports Markdown, PDF, PPT, Word, Excel, interactive HTML; charts | ~26 cited sources per report (vendor claim); 23 reasoning steps, 200+ URLs per task | Inline footnote-style `[^n^]`; click-to-jump with source highlight (vendor claim) | Live search queries and fetched URLs shown during run | Choose output format up front or in follow-ups; multi-turn refinement |
| Grok DeepSearch / DeeperSearch | Chat answer with numbered inline citations; API returns citation fields | 3-10 tool calls per query (DeepSearch); DeeperSearch more iterations | Numbered inline clickable citations; web and X sources not consistently distinguished | Visible reasoning trace | DeepSearch vs DeeperSearch toggle |
| Manus Wide Research | Files: spreadsheets/tables, reports, slide decks, dashboards, PDFs | Item-per-agent structured datasets | Not documented | Task decomposition, parallel agents, synthesis | Post-hoc modifications ("add a column", "re-research items 20-30") |
| Exa Research / deep search types | Async task: `output.content` (Markdown text or JSON matching `outputSchema`) + `output.grounding` | Structured JSON or Markdown report | Field-level citations with confidence (low/medium/high); `citations[]` url/title | Streamed citations | `outputSchema`, model/type tier (fast/standard/pro; deep-lite/deep/deep-reasoning) |
| Firecrawl /deep-research (legacy alpha) | JSON: `finalAnalysis`, `sources[]`, `activities[]` | Synthesized analysis text; optional JSON schema | Sources array (url/title/description) | `activities` (search/extract/analyze/reasoning/synthesis/thought) with depth and timestamps | `maxDepth` (1-10, default 7), `timeLimit` (30-300 s), `maxUrls` (default 20), `systemPrompt`, `analysisPrompt` |

---

## 2. Per-system notes

### 2.1 OpenAI Deep Research (ChatGPT) and the Deep Research API

**ChatGPT product**
- Launched Feb 3, 2025; "generates cited reports on a user-specified topic by autonomously browsing the web for 5 to 30 minutes"; produces "reports with citations, reasoning summaries, and sidebar information"; export PDF and DOCX. [https://en.wikipedia.org/wiki/ChatGPT_Deep_Research]
- Model history: o3-based at launch; lightweight o4-mini variant April 2025; upgraded to a GPT-5.2-based model Feb 2026. [https://en.wikipedia.org/wiki/ChatGPT_Deep_Research], [https://winbuzzer.com/2026/02/11/chatgpt-deep-research-gpt-52-upgrade-xcxwbn/]
- Feb 2026 UI: full-screen formatted report viewer with table of contents; users can "restrict searches to specific domains or defined time ranges", search connected apps (PubMed, arXiv examples) and MCP sources; live progress shows active queries; users can interrupt with follow-ups or add sources. [https://winbuzzer.com/2026/02/11/chatgpt-deep-research-gpt-52-upgrade-xcxwbn/]
- OpenAI's own guidance: outputs are "traceable, structured output with clear citations"; you can "watch the live progress and the running plan; interrupt to clarify, narrow scope, or add sources" and "request alternate versions (e.g., different scope, audience, or depth)"; "Validate before relying... you should still review the underlying sources". [https://academy.openai.com/public/clubs/work-users-ynjqu/resources/deep-research]
- Search-result summaries (secondary) state completed research shows a table of contents, a "sources used" section, an activity history, and downloads in Markdown, Word and PDF. Markdown export is **unverified** against a primary page (OpenAI help center returned 403). [https://help.openai.com/en/articles/10500283-deep-research-faq]
- PDF export was first spotted in testing because the copy button "doesn't retain the formatting". [https://www.bleepingcomputer.com/news/artificial-intelligence/chatgpt-is-finally-adding-download-as-pdf-for-deep-research/]
- Hands-on (Feb 2025): clarifying questions asked first (geography, subject, age levels); ~8 minutes; report ~12,000 words; references as inline links; reasoning panel shows "Searched for... Read more from..."; can generate APA7/MLA reference lists on request; critique: "description and summary, but lacked any analysis", struggles with source quality, cannot reach paywalled content. [https://leonfurze.com/2025/02/15/hands-on-with-deep-research/]
- Acknowledged limits: "occasionally makes factual hallucinations (errors) or incorrect inferences", "may also reference rumors, and may not accurately convey uncertainty". HLE 26.6% (o3 version). Usage limits June 2025: Pro 250/mo, Plus/Team/Enterprise 25/mo, Free 5 lightweight/mo. [https://en.wikipedia.org/wiki/ChatGPT_Deep_Research]

**API (o3-deep-research, o4-mini-deep-research)**
- Two models, "optimized for browsing and data analysis". Final answer is a `message` item; each citation is an annotation `{url, title, start_index, end_index}` marking the exact character span. Output array also exposes `web_search_call` (actions `search`, `open_page`, `find_in_page`), `code_interpreter_call`, `mcp_tool_call`, `file_search_call`. [https://developers.openai.com/api/docs/guides/deep-research]
- "The API does not automatically ask clarifying questions"; recommended pattern: clarification (optional) -> prompt rewriting (optional) -> deep research, using a smaller model. `max_tool_calls` is "the primary tool available to you to constrain cost and latency"; background mode recommended because tasks "can take tens of minutes". No fixed report structure is mandated. [https://developers.openai.com/api/docs/guides/deep-research]
- Azure docs show the annotation type is `url_citation`, and publish the full rewriting prompt: request tables where helpful, "include the expected output format in the prompt", format "as a report with the appropriate headers", prefer "official or primary websites... rather than aggregator sites or SEO-heavy blogs" and "the original paper or official journal publication rather than survey papers", match user language. [https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/deep-research]
- Cookbook example prompt: "include specific figures, trends, statistics", "summarize data in a way that could be turned into charts or tables", "inline citations and return all source metadata"; report text at `response.output[-1].content[0].text`, annotations alongside. [https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api]

### 2.2 Google Gemini Deep Research

- Launch (Dec 2024): "creates a multi-step research plan for you to either revise or approve"; browses by "searching, finding interesting pieces of information and then starting a new search based on what it's learned"; report contains "key findings... neatly organized with links to the original sources", exportable to a Google Doc. [https://blog.google/products/gemini/google-gemini-deep-research/]
- Help center: plan shown, "click Edit plan"; report delivered in a Canvas panel; Share & export: Export to Docs, Share Canvas, Copy Contents; Audio Overview; custom visualizations by prompt; "usually takes about 5-10 minutes"; file/image upload supported; daily and concurrent limits, higher on AI Pro/Ultra. [https://support.google.com/gemini/answer/15719111?hl=en&co=GENIE.Platform%3DDesktop]
- Tips post: during the run users get "Show thinking" and "Sites browsed"; Docs export puts "all of Deep Research's citations... in a works cited section"; Audio Overview gives "a podcast-style discussion of your report"; advice "Don't overthink it. You can always adjust your question." [https://blog.google/products/gemini/tips-how-to-use-deep-research/]
- API (Interactions API, 2026): models `deep-research-preview-04-2026` and `deep-research-max-preview-04-2026`; "You must use background execution"; outputs "detailed, cited reports" plus optional images streamed as `image` deltas; `collaborative_planning=True` "returns a proposed research plan instead of executing immediately"; tools: Google Search, URL Context, Code Execution, MCP, File Search; ~$1-3 per task (Max ~$3-7); "maximum research time of 60 minutes. Most tasks should complete within 20 minutes." Citation representation "the `citations` provided in the response" is not documented in detail (**format unverified**). [https://ai.google.dev/gemini-api/docs/deep-research]
- Practical guide: report read from `interaction.outputs[-1].text` as Markdown with `#` headers and bullets; streaming events `interaction.start`, `content.delta` (text or thought summaries), `interaction.complete`; follow-ups via `previous_interaction_id` (visualize, translate). [https://www.philschmid.de/gemini-deep-research-getting-started]
- Critique: report "sourced from low-quality sites" (bellesandgals.com, jasondeegan.com, glassalmanac.com), missed an AP/Guardian primary article a plain Google search found; "can't differentiate between high- and low-quality sources". [https://oftechandlearning.com/watch-out-low-quality-sources-using-google-deep-research/]

### 2.3 Perplexity Deep Research

- Product: "In about 2-4 minutes, receive a full-length, structured answer complete with sources"; export as PDF, save as a document, or publish as a shareable Perplexity Page; HLE 21.1%, SimpleQA 93.9%. [https://www.geeksforgeeks.org/websites-apps/deep-research-in-perplexity/]
- Secondary summaries: "performs dozens of searches, reads hundreds of sources"; a report may draw on "over 200 sources"; renamed "Research" in May 2025 with tiered limits (**unverified**: Perplexity blog and help center returned 403). [https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research], [https://www.perplexity.ai/help-center/en/articles/10738684-what-is-research-mode]
- API (`sonar-deep-research`): response carries `citations` (array of URLs) and `search_results` (title, url, date, snippet); worked example: 11,395 completion tokens, 19,028 citation tokens, 21 search queries, 193,947 reasoning tokens, $0.816 total; pricing $2/M input, $8/M output, $2/M citation tokens, $5/1K searches, $3/M reasoning tokens; Sonar chat completions supported until Sept 27, 2026 (migrating to Agent API). [https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research]
- In the hands-on comparison, Perplexity cited 57 sources versus OpenAI's 21 and Google's 17, favouring official government sites. [https://leonfurze.com/2025/02/15/hands-on-with-deep-research/]
- Perplexity publishes the DRACO benchmark; secondary reports say "Perplexity Deep Research with Opus 4.5 or 4.6" tops all four DRACO dimensions and that an "Advanced Deep Research" tier exists for Max users (**unverified**, source page 403). [https://arxiv.org/abs/2602.11685]

### 2.4 Anthropic multi-agent Research and Claude.ai Research

- Architecture: orchestrator-worker; LeadResearcher plans, "saves its plan to Memory" because context over 200k tokens is truncated; subagents return findings; then "the system exits the research loop and passes all findings to a CitationAgent, which processes the documents and research report to identify specific locations for citations". [https://www.anthropic.com/engineering/built-multi-agent-research-system]
- Effort scaling rules embedded in prompts: "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents." Evaluation rubric: factual accuracy, citation accuracy ("do the cited sources match the claims?"), completeness, source quality ("primary sources over lower-quality secondary sources"), tool efficiency. Multi-agent used ~15x the tokens of chat. [https://www.anthropic.com/engineering/built-multi-agent-research-system]
- Product: Research "conducting multiple searches that build on each other"; "thorough answers in minutes, complete with easy-to-check citations"; searches web plus Gmail/Calendar/Docs when connected; paid plans only; uses standard usage limits faster. [https://support.claude.com/en/articles/11088861-using-research-on-claude-ai]
- Launch: "will provide inline citations that you can use to verify the source". [https://claude.com/blog/research]
- Advanced Research (May 2025): "deeper investigations across hundreds of internal and external sources, delivering more comprehensive reports in anywhere from five to 45 minutes"; "clear citations that link directly to the original material"; available on Pro, Max, Team, Enterprise as of June 2025. [https://claude.com/blog/integrations]
- No public documentation of export formats or length controls for Claude.ai Research was found (**unverified/absent**).

### 2.5 Claude Code built-in `/deep-research` workflow

- Official docs: `/deep-research <question>` "fans out web searches on a question across several angles, fetches and cross-checks the sources it finds, votes on each claim, and returns a cited report with claims that didn't survive cross-checking filtered out"; requires WebSearch. The report "lands in your session" and "cites the sources each claim came from"; "When the verifier agents can't check a claim, such as after a rate limit or API error, the report lists that claim as unverified instead of counting it as refuted." [https://code.claude.com/docs/en/workflows]
- Intermediate visibility: `/workflows` progress view shows each phase with agent count, tokens, elapsed time; drill into an agent "to read its prompt, recent tool calls, and result"; script written under `~/.claude/projects/`; saveable to `.claude/workflows/`; controls: pause/resume, stop/restart agents, `args` input, size guideline small/medium/large (default medium, <15 agents), "Large workflow" warning above 25 agents or 1.5M projected tokens. [https://code.claude.com/docs/en/workflows]
- Third-party autopsy of the script: Scope -> 5 angles (broad, technical, recent, contrarian, practitioner); 5 blind parallel searchers; dedup and cap at 15 sources; "Each source yields 2-5 falsifiable claims, each with a direct quote and a source-quality grade"; "Three skeptics per claim, each told to refute it. Two rejections out of three and the claim dies"; synthesizer "merges survivors, ranks by confidence, writes the report with a note listing what got killed". Critique: single-pass, "The orchestrator does not loop"; ~2.36M tokens for one query. [https://steel.dev/blog/claude-code-deep-research-autopsy]

### 2.6 Stanford STORM and Co-STORM

- STORM writes "Wikipedia-like articles from scratch based on Internet search" in two stages: pre-writing (research + outline) and writing (article with citations); runner steps `do_research`, `do_generate_outline`, `do_generate_article`, `do_polish_article`. Authors: "the system cannot produce publication-ready articles that often require a significant number of edits". [https://github.com/stanford-oval/storm/blob/main/README.md]
- On-disk artifacts per topic: `conversation_log.json` (information-seeking conversation), `raw_search_results.json`, `direct_gen_outline.txt` (parametric-knowledge outline), `storm_gen_outline.txt` (refined outline), `url_to_info.json` ("Sources that are used in the final article"), `storm_gen_article.txt`, `storm_gen_article_polished.txt`. Flags: `--max-conv-turn` 3, `--max-perspective` 3, `--search-top-k` 3, `--retrieve-top-k` 3, `--max-thread-num` 3, `--remove-duplicate`; polish "adding a summarization section". [https://raw.githubusercontent.com/stanford-oval/storm/main/examples/storm_examples/run_storm_wiki_gpt.py]
- Paper: +25% absolute on organization and +10% on coverage vs baseline; Wikipedia editors flagged "source bias transfer" and "over-association of unrelated facts". [https://arxiv.org/abs/2402.14207]
- Co-STORM: LM agents converse; a "dynamic mind map" organizes uncovered information; the mind map scaffolds "a comprehensive report as takeaways"; users "observe and occasionally steer"; 70% preferred it over a search engine, 78% over a RAG chatbot. Runner: warm start, `step()` (observe or inject utterance), `generate_report()`. [https://arxiv.org/abs/2408.15232], [https://github.com/stanford-oval/storm/blob/main/README.md]
- Inline `[n]` numbering per sentence is the observed format in generated articles; the README does not state it explicitly (**format inferred, unverified**).

### 2.7 GPT Researcher (assafelovic)

- "Generate detailed reports exceeding 2,000 words"; "An average run generates a 5-6 page research report in multiple formats such as PDF, Docx and Markdown"; aggregates "over 20 sources". Deep research: "Tree-like exploration with configurable depth and breadth", "~5 minutes", "~$0.4 per research (using o3-mini on high)". [https://github.com/assafelovic/gpt-researcher/blob/master/README.md]
- Report prompt: "at least {total_words} words"; "You MUST write the report with markdown syntax and {report_format} format"; in-text citations "with markdown hyperlink placed at the end of the sentence or paragraph that references them like this: ([in-text citation](url))"; "You MUST write all used source urls at the end of the report as references... only one reference for each"; "Use markdown tables when presenting structured data"; optional tone. Report types map to distinct prompts: research, resource, outline, custom, subtopic, deep. [https://raw.githubusercontent.com/assafelovic/gpt-researcher/master/gpt_researcher/prompts.py]
- Config defaults: `REPORT_FORMAT=APA` (MLA, CMS, Harvard, IEEE available), `TOTAL_WORDS=1200`, `MAX_SUBTOPICS=3`, `REPORT_SOURCE=web|doc`, `DEEP_RESEARCH_BREADTH=3`, `DEEP_RESEARCH_DEPTH=2`, `MAX_ITERATIONS=3`. [https://docs.gptr.dev/docs/gpt-researcher/gptr/config]
- Deep research doc states breadth 4, depth 2, concurrency 4 as defaults and real-time progress callbacks (**minor inconsistency with config page**). [https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research]
- Programmatic accessors: `get_source_urls()`, `get_research_context()`, `get_costs()`. [https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package]
- Multi-agent (LangGraph) mode: Chief Editor, Researcher, Editor (plans outline), Reviewer, Revisor, Writer ("introduction, conclusion and references section"), Publisher; `task.json` options `max_sections`, `publish_formats` (markdown/pdf/docx), `include_human_feedback`, `follow_guidelines`, `guidelines[]`, `verbose`. [https://raw.githubusercontent.com/assafelovic/gpt-researcher/master/multi_agents/README.md]

### 2.8 LangChain Open Deep Research

- Three phases: Scope ("User Clarification" then "Brief Generation" into "a comprehensive, yet focused research brief"), Research (supervisor delegates subtopics to sub-agents; "an additional LLM call to clean sub-agent research findings"), Write (final report "in one-shot, steered by the brief"). [https://www.langchain.com/blog/open-deep-research]
- Final report prompt: Markdown `#` title / `##` sections / `###` subsections; "Assign each unique URL a single citation number"; inline `[1]`; end with `### Sources` listing each source on its own line, "Number sources sequentially without gaps (1,2,3,4...)"; sections "as long as necessary", report expected to be "fairly long and verbose"; respond in the user's language; no self-referential language. [https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/src/open_deep_research/prompts.py]
- Config: `allow_clarification`, `max_concurrent_research_units`, `max_researcher_iterations`, `max_react_tool_calls`, `max_structured_output_retries`, `max_content_length`, per-role models (summarization/research/compression/final report), `search_api`; RACE score 0.4344 (#6) on Deep Research Bench; output in `final_report` state key via LangGraph Studio. [https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/README.md]

### 2.9 Hugging Face open-deep-research (smolagents)

- Replication of OpenAI Deep Research on GAIA: 55% pass@1 on validation vs 67% for OpenAI; run via `python run.py --model-id "o1" "Your question"`; output is a final answer string; no report or citation component. [https://raw.githubusercontent.com/huggingface/smolagents/main/examples/open_deep_research/README.md]
- Uses CodeAgent (code actions ~30% fewer tokens than JSON), text-based browser and text inspector adapted from Magentic-One; authors acknowledge missing visual browsing, report generation and citation handling relative to OpenAI's product. [https://huggingface.co/blog/open-deep-research]

### 2.10 Other notable open-source and commercial agents (brief)

- **dzhng/deep-research**: generates follow-up questions first; recursive breadth (3-10, default 4) / depth (1-5, default 2); accumulates learnings and visited URLs; writes `report.md` (comprehensive Markdown "includes all sources and references") or `answer.md` (concise); `CONCURRENCY_LIMIT` env var. [https://github.com/dzhng/deep-research/blob/main/README.md]
- **Jina node-DeepResearch**: "quick, concise answers from deep search" rather than long reports; citations "in Github-flavored markdown footnote format, e.g. [^1], [^2]"; returns visited/read URLs; loop until token budget exceeded then "Beast Mode" forces an answer; OpenAI-compatible streaming with `<think>` tags; evaluator checks "Is answer definitive?". [https://github.com/jina-ai/node-DeepResearch/blob/main/README.md]
- **Tongyi DeepResearch (Alibaba)**: answer-oriented agent evaluated on HLE, BrowseComp, xbench-DeepSearch; ReAct vs IterResearch "heavy" mode; no report/citation component documented in README. [https://github.com/Alibaba-NLP/DeepResearch]
- **Step-DeepResearch (StepFun)**: SFT data uses `\cite{}` markers so "relevant references are appended at critical information points"; reports must "strictly follow the preset plan structure"; ADR-Bench scores information completeness, content depth, requirement fitness, readability; patch-style editing cuts output tokens >70%. [https://arxiv.org/html/2512.20491v3]
- **WebThinker**: "Autonomous Think-Search-and-Draft" interleaves reasoning, search and report writing; tools to draft a section, check the report, edit the report; Markdown reports; evaluated listwise by DeepSeek-R1 and GPT-4o against Grok3 DeeperSearch and Gemini 2.0 Deep Research on 30 test reports. [https://arxiv.org/abs/2504.21776], [https://raw.githubusercontent.com/RUC-NLPIR/WebThinker/main/README.md]
- **Kimi-Researcher / Kimi Deep Research**: "average of 23 reasoning steps", "over 200 URLs per task"; HLE 26.9% pass@1; citations as `[^5^]`-style markers. Product page: outputs "Markdown reports, PDFs, PowerPoint decks, Word documents, Excel spreadsheets, and interactive HTML reports", "embedded charts", "Every claim is cited and traceable", live search queries displayed, multi-turn refinement; ~26 sources per report is a vendor claim from search snippets (**unverified**). [https://moonshotai.github.io/Kimi-Researcher/], [https://www.kimi.ai/features/deep-research]
- **Grok DeepSearch / DeeperSearch**: 4-step process; "up to 10 times per query, with a minimum requirement of 3 function calls"; web + X sources; output "includes citations and a detailed reasoning trace"; secondary critique that X and web citations are not consistently distinguished. [https://www.tryprofound.com/blog/understanding-grok-a-comprehensive-guide-to-grok-websearch-grok-deepsearch]
- **Manus Wide Research**: "hundreds of independent agents that work in parallel", one item per agent; deliverables are sortable tables/spreadsheets, structured datasets, reports with visualizations, batch-processed files; post-hoc edits ("Add a column for pricing", "Re-research items 20-30"); citation handling not documented. [https://manus.im/docs/features/wide-research]
- **Exa**: async research/deep search returns `output.content` ("String by default, or object when outputSchema is provided") and `output.grounding` with field-level "Sources supporting this output field" and low/medium/high confidence; `citations[]` with url/title; types `deep-lite`/`deep`/`deep-reasoning`; `costDollars` breakdown per response. Separate `exa-research-*` model names appear in search summaries but not on the fetched page (**unverified**). [https://exa.ai/docs/reference/research/create-a-task]
- **Firecrawl /deep-research (alpha, legacy)**: params `maxDepth` (1-10, default 7), `timeLimit` (30-300 s, default 270), `maxUrls` (default 20), `systemPrompt`, `analysisPrompt`, JSON schema output; response has `finalAnalysis`, `sources[]` (url/title/description), `activities[]` (search/extract/analyze/reasoning/synthesis/thought with depth and timestamp); unmaintained after June 30, 2025. [https://docs.firecrawl.dev/features/alpha/deep-research]

### 2.11 Published critiques of deep-research output quality

- **Reference hallucination at scale** (10 models, 53,090 DRBench URLs + 168,021 ExpertQA URLs): "3-13% of citation URLs are hallucinated", "5-18% are non-resolving overall"; deep research agents worse than search-augmented LLMs (10.7% vs 4.8% hallucinated); the `urlhealth` tool (LIVE/DEAD/LIKELY_HALLUCINATED/UNKNOWN) plus agentic self-correction "reduces non-resolving citation URLs by 6-79x... to under 1%". [https://arxiv.org/html/2604.03173v1]
- **Claim-level auditability**: risk shifts "from isolated factual errors to scientifically styled outputs whose claim-evidence links are weak, missing, or misleading"; proposes provenance coverage, provenance soundness, contradiction transparency, audit effort; recommends "persistent, queryable provenance graphs that encode claim-evidence relations (including conflicts)" validated during synthesis, not after. [https://arxiv.org/abs/2602.13855]
- **Trajectory-level hallucination (PING taxonomy)**: Propagation, Intent, Noise-induced, Grounding errors across plan-search-summarize; six agents on 100 adversarial tasks (DeepHalluBench) all show "non-negligible reliability gaps"; failures traced to hallucination propagation between stages. [https://arxiv.org/abs/2601.22984]
- **DRACO** (Perplexity, 100 tasks, 10 domains, 3,934 rubric criteria): weights factual accuracy 52%, breadth/depth 22%, presentation 14%, citation quality 12%; citation criteria carry negative weights (-150 to +10) so bad citations are penalised; best-system saturation ~71%. Secondary summaries report best scores of ~65% citation quality and ~68% factual accuracy as the weakest axes (**exact numbers unverified against paper body**). [https://huggingface.co/datasets/perplexity-ai/draco], [https://arxiv.org/abs/2602.11685]
- **DeepResearch Bench** (100 PhD-level tasks, 22 fields): RACE (comprehensiveness, insight/depth, instruction following, readability) and FACT (effective citation count, citation accuracy); Gemini 2.5 Pro Deep Research averaged 111.21 effective citations but its citation accuracy, like OpenAI's, trailed Perplexity's (secondary summary). [https://arxiv.org/abs/2506.11763]
- **DeepResearch-ReportEval** (100 queries, 12 categories, four commercial systems): scores quality, redundancy, factuality; finds redundancy, over-reliance on limited sources recycled across sections, and citation/factuality errors that inflate length without adding insight. [https://arxiv.org/abs/2510.07861]
- **Practitioner critiques**: 12,000-word report that was "description and summary, but lacked any analysis"; source-quality judgement weak; paywalls unreachable. [https://leonfurze.com/2025/02/15/hands-on-with-deep-research/] A report "completely missed a major entity" because it was privately held with little web footprint, producing "the illusion of knowledge"; "the worst results are often, paradoxically, for the most popular topics... contaminated by slop". [https://stratechery.com/2025/deep-research-and-knowledge-value/] Gemini cited content farms and missed an AP/Guardian primary. [https://oftechandlearning.com/watch-out-low-quality-sources-using-google-deep-research/] OpenAI itself: hallucinations, rumor citation, poor uncertainty conveyance. [https://en.wikipedia.org/wiki/ChatGPT_Deep_Research]

---

## 3. Patterns and takeaways

### What is common
1. **The unit of output is one Markdown-ish report with inline citations and a trailing source list.** Every report-producing system (OpenAI, Gemini, Perplexity, Claude, GPT Researcher, Open Deep Research, STORM, WebThinker, Kimi) converges on headings + inline citation markers + a sources section. Answer-oriented systems (Jina, HF, Tongyi) deliberately opt out and produce a short answer with footnotes.
2. **Per-claim citation is the norm, implemented three ways**: character-span annotations (OpenAI `url_citation` start/end index; Exa field-level grounding), numbered markers resolved in a sources list (Open Deep Research `[1]` + `### Sources`, STORM `[n]` + `url_to_info.json`, Jina/Kimi `[^n]`), or Markdown hyperlinks at sentence end (GPT Researcher). Nobody records access dates by default.
3. **A pre-research scoping artifact is standard**: clarifying questions (ChatGPT, dzhng, Open Deep Research, OpenAI's recommended API wrapper), or an editable plan (Gemini app "Edit plan", Gemini API `collaborative_planning`, Claude Code's approval of planned phases).
4. **Process is exposed as a live trace, not as a deliverable**: activity/thinking panels (ChatGPT, Gemini "Show thinking"/"Sites browsed", Grok, Kimi, Claude Code `/workflows`), tool-call items in API output arrays (OpenAI, Firecrawl `activities`). Only STORM and Claude Code persist intermediate artifacts (outline, conversation log, search results; the orchestration script and per-agent results).
5. **Depth is controlled by budget knobs, not by target length**: `max_tool_calls` (OpenAI), breadth/depth (dzhng, GPT Researcher), iterations/concurrency (Open Deep Research), `maxDepth`/`timeLimit`/`maxUrls` (Firecrawl), token budget (Jina), size guideline (Claude Code), tier choice (Gemini Max, Grok DeeperSearch, Exa pro). GPT Researcher (`TOTAL_WORDS`, default 1200 "at least") is the only one with an explicit word-count control, and it is a floor, not a ceiling.
6. **Export is an afterthought layered on**: PDF/DOCX (ChatGPT), Google Docs with works-cited (Gemini), PDF/Page (Perplexity), MD/PDF/DOCX (GPT Researcher), MD/PDF/PPT/Word/Excel/HTML (Kimi). Open-source CLI tools write files directly (`report.md`, STORM's directory, GPT Researcher `outputs/`).

### What differs
- **Verification as a first-class stage** exists only in Claude Code `/deep-research` (3-skeptic vote, killed-claims note, "unverified" label on uncheckable claims), Anthropic's CitationAgent (post-hoc citation placement), and GPT Researcher's multi-agent Reviewer/Revisor. Most systems have no verification artifact at all.
- **Source-quality signalling**: Claude Code grades each source; OpenAI's rewriting prompt tells the model to prefer primary sources; Anthropic's eval rubric scores source quality; no consumer product exposes a per-source quality grade to the user.
- **Structured output**: Exa (JSON schema + field-level grounding with confidence), Firecrawl (JSON schema), Manus (tables/spreadsheets) support machine-readable deliverables; the chat products do not.
- **Length**: commercial reports run very long (12k words observed; Perplexity API ~11k completion tokens; Open Deep Research prompt asks for "fairly long and verbose"), while critiques consistently flag padding, redundancy, and summary-without-analysis.
- **Answer vs report**: benchmark-driven agents (GAIA, BrowseComp, HLE) return a terse answer; product-driven ones return a report. Only dzhng and Jina let the caller choose.

### Design implications for an output contract (portable deep-research skill)
1. **Ship a report file plus a machine-readable sidecar.** Write `report.md` (headings, exec summary, tables) and a `sources.json`/`claims.json` carrying, per claim: text, quote, URL, source-quality grade, verification status, access date. This mirrors STORM's `url_to_info.json`, OpenAI's span annotations, and the "provenance graph" recommendation from the auditability literature, and it is what the chat products lack.
2. **Cite per claim with sequential numbered markers and a gap-free source list that includes access date and a URL health status.** Numbered `[n]` + `## Sources` (Open Deep Research style) is the most portable across renderers; add access date and LIVE/DEAD/UNKNOWN status because 5-18% of deep-research URLs do not resolve and 3-13% are fabricated.
3. **Make verification status part of the report, not the trace.** Follow Claude Code: state which claims were confirmed by multiple independent sources, which are single-source, which failed cross-checking (and were dropped), and which could not be checked ("unverified"). Include a short "What this report could not find" section to counter the illusion-of-completeness problem Thompson describes.
4. **Emit the scoping artifact before research and keep it in the output.** A research brief / plan (Open Deep Research brief, Gemini plan) should be written to disk (`plan.md`) and echoed in the report header so the reader can see what was and was not in scope; support an optional approval pause.
5. **Give the caller explicit depth and length controls with sane defaults, separated.** Depth: max sources / max tool calls / breadth x depth (as in dzhng, GPT Researcher, Firecrawl). Length: a target word range (not just a floor) and a "brief answer vs full report" mode switch (dzhng's `answer.md` vs `report.md`). Default toward shorter reports; every critique in the literature is about excess length and redundancy, none about brevity.
6. **Encode source-quality preferences and a redundancy rule in the synthesis prompt.** Prefer primary/official sources over aggregators and SEO blogs (OpenAI's rewriting prompt, Anthropic's rubric), require a direct quote per extracted claim (Claude Code), cap the share of claims any single source may support, and forbid restating the same finding across sections (ReportEval's redundancy finding).
7. **Persist intermediate artifacts on disk for auditability and resumability.** Per-angle search notes, fetched-source extracts, and the verification log should live in a run directory (as STORM and Claude Code do) so a later agent or human can audit or resume without re-running; keep them out of the main report.
8. **Put the exec summary and a confidence/coverage table first.** Every commercial product added a TOC/summary view after launch; front-load a 5-10 line summary, a table of key findings with confidence and source count, then the body, then sources. This is also what makes the report usable as context for a downstream coding agent with a limited context window.

---

## 4. Sources (all accessed 2026-09-02)

OpenAI
- https://developers.openai.com/api/docs/guides/deep-research
- https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api
- https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/deep-research
- https://academy.openai.com/public/clubs/work-users-ynjqu/resources/deep-research
- https://en.wikipedia.org/wiki/ChatGPT_Deep_Research
- https://winbuzzer.com/2026/02/11/chatgpt-deep-research-gpt-52-upgrade-xcxwbn/
- https://www.bleepingcomputer.com/news/artificial-intelligence/chatgpt-is-finally-adding-download-as-pdf-for-deep-research/
- https://help.openai.com/en/articles/10500283-deep-research-faq (403; facts taken from search snippet only)
- https://leonfurze.com/2025/02/15/hands-on-with-deep-research/
- https://stratechery.com/2025/deep-research-and-knowledge-value/

Google Gemini
- https://blog.google/products/gemini/google-gemini-deep-research/
- https://blog.google/products/gemini/tips-how-to-use-deep-research/
- https://support.google.com/gemini/answer/15719111?hl=en&co=GENIE.Platform%3DDesktop
- https://ai.google.dev/gemini-api/docs/deep-research
- https://www.philschmid.de/gemini-deep-research-getting-started
- https://oftechandlearning.com/watch-out-low-quality-sources-using-google-deep-research/

Perplexity
- https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research
- https://www.geeksforgeeks.org/websites-apps/deep-research-in-perplexity/
- https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research (403; search snippet only)
- https://www.perplexity.ai/help-center/en/articles/10738684-what-is-research-mode (403; search snippet only)

Anthropic / Claude
- https://www.anthropic.com/engineering/built-multi-agent-research-system
- https://support.claude.com/en/articles/11088861-using-research-on-claude-ai
- https://claude.com/blog/research
- https://claude.com/blog/integrations
- https://code.claude.com/docs/en/workflows
- https://steel.dev/blog/claude-code-deep-research-autopsy

STORM / Co-STORM
- https://github.com/stanford-oval/storm/blob/main/README.md
- https://raw.githubusercontent.com/stanford-oval/storm/main/examples/storm_examples/run_storm_wiki_gpt.py
- https://arxiv.org/abs/2402.14207
- https://arxiv.org/abs/2408.15232

GPT Researcher
- https://github.com/assafelovic/gpt-researcher/blob/master/README.md
- https://docs.gptr.dev/docs/gpt-researcher/gptr/config
- https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package
- https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research
- https://raw.githubusercontent.com/assafelovic/gpt-researcher/master/gpt_researcher/prompts.py
- https://raw.githubusercontent.com/assafelovic/gpt-researcher/master/multi_agents/README.md

LangChain Open Deep Research
- https://www.langchain.com/blog/open-deep-research
- https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/README.md
- https://raw.githubusercontent.com/langchain-ai/open_deep_research/main/src/open_deep_research/prompts.py

Hugging Face
- https://huggingface.co/blog/open-deep-research
- https://raw.githubusercontent.com/huggingface/smolagents/main/examples/open_deep_research/README.md

Other agents
- https://github.com/dzhng/deep-research/blob/main/README.md
- https://github.com/jina-ai/node-DeepResearch/blob/main/README.md
- https://github.com/Alibaba-NLP/DeepResearch
- https://arxiv.org/html/2512.20491v3
- https://arxiv.org/abs/2504.21776
- https://raw.githubusercontent.com/RUC-NLPIR/WebThinker/main/README.md
- https://moonshotai.github.io/Kimi-Researcher/
- https://www.kimi.ai/features/deep-research
- https://www.tryprofound.com/blog/understanding-grok-a-comprehensive-guide-to-grok-websearch-grok-deepsearch
- https://manus.im/docs/features/wide-research
- https://exa.ai/docs/reference/research/create-a-task
- https://docs.firecrawl.dev/features/alpha/deep-research

Critiques and benchmarks
- https://arxiv.org/html/2604.03173v1
- https://arxiv.org/abs/2602.13855
- https://arxiv.org/abs/2601.22984
- https://arxiv.org/abs/2602.11685
- https://huggingface.co/datasets/perplexity-ai/draco
- https://arxiv.org/abs/2506.11763
- https://arxiv.org/abs/2510.07861
