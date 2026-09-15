# Retrieval Landscape Survey: reaching real sources in 2026, and what fits a verbatim-quote ledger

**Question:** What retrieval and platform-access options exist in 2026 for an AI research agent to gather web evidence beyond plain
page fetches, which of them fit a "raw text on disk, verbatim quotes" ledger, and what do the named tools actually do?

**Scope:** round 2 of the portable `deep-research` skill. Harnesses in priority order: Claude Code, Hermes agent (Nous Research),
Codex. The motivating use case is research where the evidence does **not** live on tidy article pages — trading bots, where it sits
in GitHub repositories, Reddit threads, X/Twitter posts, Discord and Telegram communities, exchange API documentation, blogs and
papers.

**Constraint that does not move:** our fetch chain is keyless (curl + Python stdlib, Jina Reader, Wayback, urltomarkdown, keyless
APIs), quotes come only from raw page text saved on disk, and the skill **never** circumvents CAPTCHAs, paywalls or logins. This
document therefore describes access paths and platform terms **factually** and contains **no operational instructions for defeating
CAPTCHAs, paywalls, logins or rate limits.** Where a path exists only by circumvention it is marked out of scope and dropped.

**Compiled:** 2026-09-15. All URLs accessed 2026-09-15 unless noted. **Method:** official documentation, terms-of-service pages,
GitHub repositories and papers, plus about twenty live keyless `curl` probes run from this machine on 2026-09-15 (marked
**[probe]**; one request each, a normal browser user agent, no retries on 403/429) and a first-hand inspection of the Hermes agent
installed on this machine (marked **[local]**). Probes are one-IP, one-day snapshots, not benchmarks.

**How to read the verdicts.** Our ledger needs one thing from a retrieval option: the **raw text of a named source, byte-for-byte,
on disk**, so `cite_check.py` can find a quote in it and a later `cite_audit.py` can re-verify it. That splits every option into
three classes:

- **Fetch rung** — returns page text verbatim. Can carry quotes. This is what the ledger consumes.
- **Search rung** — returns pointers (URLs, titles, snippets). Useful for discovery; a snippet is a paraphrase or an excerpt out of
  context and is **not** quotable evidence; the URL still has to be fetched.
- **Answer service** — returns a synthesized answer with citations. Cannot be a rung at all: it is a competing workflow, not a
  source of evidence, and its prose has no page to check a quote against.

---

## 1. The four tools named by the user

### 1.1 Perplexity — an answer service, plus a search API that returns snippets, not pages

**Product and API state, 2026.** The legacy Sonar Chat Completions endpoint is being replaced: the docs state "Sonar Chat
Completions is now Agent API. Sonar will be supported until September 27, 2026", with the Agent API launched 2026-08-13.
[https://docs.perplexity.ai/getting-started/models]

**Model names** (current models page): **Sonar** (search), **Sonar Pro** (search), **Sonar Reasoning Pro** (reasoning), **Sonar Deep
Research** ("exhaustive searches and generating comprehensive reports"). A Router API and an Embeddings API are also listed.
`sonar-reasoning` without "Pro" no longer appears. [https://docs.perplexity.ai/getting-started/models;
https://docs.perplexity.ai/llms.txt]

**What comes back — the question that decides everything for us.** The **Search API** returns ranked results with `title`, `url`,
`snippet` ("content snippet extracted from the page"), `date` and `last_updated`, where snippet depth is a *budget*
(`search_context_size`, `max_tokens`, `max_tokens_per_page`) and the reference documents **no parameter that returns full page
text** [https://docs.perplexity.ai/api-reference/search-post]. The **Agent API** exposes `web_search`, `fetch_url` and
`finance_search`, returning `search_results`, `fetch_url_results` (`url`, `title`, `snippet`) and an `output` message with citation
annotations [https://docs.perplexity.ai/docs/agent-api/overview]. **`fetch_url` is the closest thing to a page endpoint and still is
not raw text:** it gives fuller page content than search, but "fetched content is extracted into snippets for model context and may
be truncated for longer pages", and is "best-effort" — paywalls, non-HTML, timeouts and robots.txt yield failure markers rather than
page text [https://docs.perplexity.ai/docs/agent-api/tools/fetch-url].

**Verdict: no Perplexity endpoint returns source page text verbatim.** A quote checked against a Perplexity response cannot be
byte-exact against the source, so Perplexity cannot be a fetch rung for our ledger. It can only be a **search rung** (pointers we
then fetch ourselves) or a competing answer service.

**Pricing, as published** [https://docs.perplexity.ai/getting-started/pricing]: Sonar $1/M in and $1/M out plus a $5-12 per 1K
request fee by search context size; Sonar Pro $3/M and $15/M plus $6-14 per 1K; Sonar Deep Research $2/M in, $8/M out, plus $2/M
citation tokens, $3/M reasoning tokens and $5 per 1K searches; **Search API $5.00 per 1,000 requests**; Agent API tool fees $0.0025
per web search and **$0.0005 per `fetch_url`**. Sonar Reasoning Pro's rates were **not sourced**.

**Consumer subscription tiers: names only, and not from a primary source.** `perplexity.ai/pricing` returned 403 to automated
fetching. Secondary sources give five tier names — Free, Pro, Max, Enterprise Pro, Enterprise Max
[https://www.usecarly.com/blog/perplexity-pricing/] — and the last two are corroborated by a Perplexity help-centre article title
[https://www.perplexity.ai/enterprise]. **Consumer prices are deliberately omitted: they could not be verified against a Perplexity
page.**

**Terms worth knowing before adopting** (API ToS, last updated 2026-01-23)
[https://www.perplexity.ai/hub/legal/perplexity-api-terms-of-service]:
- §2.1 grants the right to submit input, receive output "and display such Output, in each case, solely within the Customer
  Applications in accordance with the API Documentation." **There is no general redistribution grant** — display is scoped to your
  own application.
- §2.3.1: the customer "owns all Output" and Perplexity "asserts no ownership rights in any Output" — but ownership and the §2.1
  display scope are different things, and the display scope binds.
- §2.5 allows suspension where an application is judged, among other things, "competitive with Perplexity".
- Searching the ToS for caching, retention, resale and citation-display requirements returned **no clauses**; retention is deferred
  to the DPA [https://www.perplexity.ai/hub/legal/dpa].

### 1.2 MiroThinker / MiroFlow (MiroMind) — open weights, open framework, keyed tool stack

**Two artefacts.** **MiroThinker** is the open-weight agent *model* series [https://github.com/MiroMindAI/MiroThinker]; **MiroFlow**
is the *framework* — modular, multi-turn, with hierarchical sub-agent orchestration [https://github.com/MiroMindAI/MiroFlow]. Both
**Apache-2.0**, code and weights alike; the hosted product is `dr.miromind.ai`.

**Sizes and dates** (README news section and HF cards): **2026-03-11, MiroThinker-1.7** — 30B (`-mini`) and 235B, 256K context, 300
max tool calls, HF card licence `apache-2.0`, base `Qwen/Qwen3-235B-A22B-Thinking-2507`
[https://huggingface.co/miromind-ai/MiroThinker-1.7]; **2026-01-05, v1.5** — 30B and 235B, 400 tool calls; **2025-11-13, v1.0** — 8B
/ 30B / 72B, 600 tool calls, "interactive scaling" [https://arxiv.org/abs/2511.11793]; earlier v0.2 (2025-09-08) and v0.1
(2025-08-08).

**Benchmarks, as the org repo reports them** [https://github.com/MiroMindAI/MiroThinker]: MiroThinker-1.7 — BrowseComp 74.0,
BrowseComp-ZH 75.3, GAIA-Val-165 82.7, HLE-Text 42.9; v1.5-235B — HLE-Text 39.2, BrowseComp 69.8, GAIA-Val-165 80.8. MiroFlow
reports GAIA Validation 82.4%, HLE 27.2%, BrowseComp-EN 33.2%, xBench-DeepSearch 72.0% [https://github.com/MiroMindAI/MiroFlow].

**Sources disagree inside one README.** Its summary line says "It achieves a 88.2 on the challenging BrowseComp benchmark" while the
1.7 section reports **74.0**. The only candidate for 88.2 is **MiroThinker-H1**, which the same README calls "Our proprietary agent"
— i.e. not open weights. **Do not quote 88.2 as an open-model number.** [https://github.com/MiroMindAI/MiroThinker] The H1 paper's
abstract gives no numeric results [https://arxiv.org/abs/2603.15726]. Third-party forks carry stale figures; cite only the
MiroMindAI org repo.

**Tool stack — and here is the finding that matters to us.** The README states the policy verbatim: "By default, we use open-source
tools wherever possible, **except for the code tool E2B and the Google search tool Serper**." The tool table keys `tool-python` to
`E2B_API_KEY`, `search_and_scrape_webpage` to `SERPER_API_KEY`, and `jina_scrape_llm_summary` to `JINA_API_KEY` with
`JINA_BASE_URL="https://r.jina.ai"`. [https://github.com/MiroMindAI/MiroThinker] MiroFlow's tool configs match — Serper plus Jina
for search and scraping, E2B for code, Anthropic/OpenAI models for browsing, with Wikipedia content and revision history, Wayback
archive search and website scraping in the search server; Jina is the **default scraper** and Serper the fallback for
`scrape_website`. [https://github.com/MiroMindAI/MiroFlow/blob/main/docs/mkdocs/docs/tool_searching.md;
https://github.com/MiroMindAI/MiroFlow/tree/main/config/tool]

**Fit verdict.** The state-of-the-art open stack reaches pages with **Jina Reader plus a keyed SERP API** — the same two rungs we
already use, one keyed where ours is keyless. **Nobody has a secret retrieval channel we are missing.** MiroThinker is a model to
run, not a rung to add, and its `jina_scrape_llm_summary` tool summarises with an LLM before returning, which would destroy verbatim
quoting if copied.

---

### 1.3 "Toast 1" — found: a Mixedbread search agent, not a report writer

The name is ambiguous. "Toast" is also Toast Inc., the restaurant point-of-sale company, which ships its own AI products
[https://pos.toasttab.com/news/toast-debuts-toast-iq-grow-spring-release-2026]. The product meant here is **Toast 1** (`toast-1`)
from **Mixedbread**, the embeddings company, announced **2026-08-13**. [https://www.mixedbread.com/blog/toast-1]

- **What it is:** "Toast 1, our first specialised search agent, is available today." Given a question it writes its own subqueries,
  calls search tools, reads what it finds "and returns only the curated evidence"; it runs standalone or as a subagent.
  [https://www.mixedbread.com/blog/toast-1]
- **Its native surface is a document store, not the open web.** The official harness describes toast-1 as "a model trained to drive
  retrieval tools over a document store and end with a ranked list, an answer, or both", with the example tool declared as `{"type":
  "search_corpus", "store_identifiers": [...]}`. The blog says it is backend agnostic and strongest with Mixedbread Search.
  [https://github.com/mixedbread-ai/toast-harness; https://www.mixedbread.com/blog/toast-1]
- **The retrieval loop is opaque to the caller.** The harness states the hosted `search_corpus` tool "runs inside the API for as
  many rounds as the model wants; none of them come back as tool calls, and the answer arrives as plain content."
  [https://github.com/mixedbread-ai/toast-harness]
- **Access:** OpenAI-compatible Chat Completions at `https://api.mixedbread.com/v1`, model `toast-1`, key `MXBAI_API_KEY`. The
  harness (`pip install toast-harness`) is **Apache-2.0**; the model is not released — "No checkpoint, no tokenizer", and no Toast 1
  model exists on the Mixedbread HuggingFace org [https://github.com/mixedbread-ai/toast-harness;
  https://huggingface.co/mixedbread-ai]. **Parameter count, architecture and base model are not disclosed anywhere found** — stated
  rather than guessed.
- **Published cost:** about $0.016-0.023 per query at roughly eight-second median latency, $0.05-0.07 at about eleven seconds for
  the premium fusion configuration; launch token pricing $0.30/M input, $0.036/M cached, $0.72/M output. Plans: **Starter** (free,
  $5 credits), **Scale** ($20/month including $20 credits, then pay-as-you-go), **Enterprise** — "every plan is billed at the same
  usage rates." [https://www.mixedbread.com/blog/toast-1; https://www.mixedbread.com/pricing]
- **Benchmarks (vendor-reported):** BrowseComp Plus, OfficeQA Pro V2, LongSeal and Harvey LAB Firm Knowledge — GPT-5.6 Sol with
  Toast 1 at 70% answer correctness on OfficeQA Pro V2 for about $1.15 per task against Claude Fable 5 at 60% for about $4, and an
  identical Harvey LAB score with 3.5x fewer tokens (80.6M to 23M) [https://www.mixedbread.com/blog/toast-1]. One widely-shared
  secondary post calls Toast 1 an embedding model
  [https://dev.to/trismegistus/toast-1-a-new-embedding-model-that-rivals-openai-at-a-fraction-of-the-cost-3k79]; the primary sources
  say search agent, and the secondary source is wrong.

**Fit verdict.** Toast 1 occupies the slot our researcher agents occupy, so it is a **partial replacement for part of our workflow,
not a rung under it.** Two properties block it from our ledger as published: hidden retrieval rounds leave no per-source trace to
grade, and nothing states the evidence is byte-exact page text. It is also corpus-first where our problem is the open web.

### 1.4 "Agent-Reach" — found: MIT scaffolding whose hard platforms run on user cookies

`github.com/Panniantong/Agent-Reach` — "Give your AI agent eyes to see the entire internet. Read & search Twitter, Reddit, YouTube,
GitHub, Bilibili, XiaoHongShu — one CLI, zero API fees." MIT, Python, created 2026-02-24, last pushed 2026-09-15, **81,971 stars**.
**[probe]** `api.github.com/repos/Panniantong/Agent-Reach`, 2026-09-15.

- **What it actually is:** not a proxy, crawler or data API, but a **selection, install, health-check and routing layer over
  third-party tools**, shipped as an Agent Skill for Claude Code, Cursor, OpenClaw and Windsurf. An independent review states it
  plainly: "Agent Reach is the setup and routing layer, not a proxy, crawler fleet or unified data API."
  [https://wavect.io/blog/agent-reach-open-source-review/; https://github.com/Panniantong/Agent-Reach/blob/main/docs/README_en.md]
- **Routing:** every platform gets an ordered primary/fallback backend list — `web.py -> Jina Reader`, `youtube.py -> yt-dlp`,
  `github.py -> gh CLI`, `rss.py -> feedparser`, `exa_search.py -> Exa via mcporter`, plus twitter/reddit/xhs/bilibili/linkedin
  modules — and `agent-reach doctor` reports which routes work; backends churn (Bilibili 412-blocked yt-dlp in June 2026, so it
  switched to bili-cli) [https://github.com/Panniantong/Agent-Reach/blob/main/docs/README_en.md]. **This is our architecture** — an
  ordered ladder plus a health check plus a plausibility gate — pointed at social platforms instead of article pages, and four of
  its zero-config routes (`gh`, `yt-dlp`, `feedparser`, Jina Reader) are keyless.
- **Its two headline platforms run on the user's browser cookies.** The README's own pain-point table says "Reddit | Server IPs get
  403'd" and "Twitter API | Pay-per-use, moderate usage ~$215/month"; the platform table says of Reddit "No zero-config path
  (anonymous endpoints blocked)" and of Twitter/X "Cookie unlocks search, timeline, tweet reading, articles." Cookies are said to
  stay local. [https://github.com/Panniantong/Agent-Reach/blob/main/docs/README_en.md]
- **The repository warns that this gets accounts banned.** The Chinese README carries a warning absent from the English one: for
  cookie-login platforms (Twitter, XiaoHongShu and others), calling them via script/API "存在被平台检测并封号的风险" — there is a risk of
  platform detection and account ban — and it advises using a dedicated throwaway account rather than a main account, for two
  reasons: detection of non-browser API call behaviour, and cookies being equivalent to full login rights.
  [https://github.com/Panniantong/Agent-Reach/blob/main/README.md, lines 263-267]
- The same review disputes the headline — "Several social channels still need cookies, a logged-in browser session, a free key or a
  proxy" — and states the legal position: "The hard limits here are legal, not technical. Reading platforms through cookies and
  scrapers crosses many terms-of-service lines... The ability to retrieve content does not grant a right to collect, retain, enrich
  or republish it." [https://wavect.io/blog/agent-reach-open-source-review/]

**Fit verdict.** Agent-Reach's README and our probe #1 agree, from different methods and networks, that Reddit's anonymous endpoints
do not serve automated traffic in 2026. Replaying a logged-in human's session cookies to read a platform that sells an API for
exactly that purpose is on the far side of the line this project drew on 2026-09-02, and the repository itself says it risks bans,
so **we do not adopt its Reddit or X routes.** The right reading of Agent-Reach is not "a tool to plug in" but **confirmation that
the hard platforms are hard, and that the market's answer is cookies — which we decline.**

---

## 2. Comparable deep-research systems and retrieval services

The organising question is fidelity: **can this thing hand back text a character-by-character quote checker can use?** Of fifteen
systems examined, only a handful can, and only a few return genuinely unmodified bytes.

### 2.1 The fidelity ladder

| Tier | System | Field | Notes |
|---|---|---|---|
| **Unmodified bytes** | **Crawl4AI** | `result.html` | "Original, unmodified page HTML" — **keyless, self-hosted, Apache-2.0** |
| | **Firecrawl** | `rawHtml` | "Unmodified HTML as received from the page"; self-host keyless; **set `maxAge: 0`** |
| | **Zyte API** | `httpResponseBody` (base64) | Documented raw bytes; `browserHtml` is HTML5-normalised and must not be used |
| | **ScrapingBee** | `return_page_source=true` | Must override `render_js`, which defaults true; 2 MB cap |
| | **browser-use** | CDP `evaluate` → `outerHTML` | Byte-exact but needs Chrome; heavy for a fetch rung |
| | **SerpApi** | `raw_html_file` | Raw HTML **of the results page only**; expires after 31 days |
| **Deterministic conversion** | **Jina Reader** | default markdown / `text` | **Keyless at 20 RPM**; boilerplate stripped; `html` mode **not** byte-exact |
| | **Tavily** | `raw_content`, **`query` omitted** | Markdown/text; no raw-HTML option |
| | **STORM** | `raw_search_results.json` | Persists verbatim trafilatura text; **tables excluded** |
| | **GPT Researcher** | `get_research_sources()` | Verbatim in memory; **nothing on disk unless you persist it** |
| | **Kimi `/v1/tools/fetch`** | `markdown` | Non-model endpoint, $0.002/call; extracted, not raw |
| **Chunks / snippets** | Brave LLM Context, Exa `text`, Tavily `content`, Serper, Perplexity | — | Not quotable with confidence |
| **Model rewrite — unusable** | OpenAI DR, Gemini DR and grounding, Kimi-Researcher, Tongyi, LangChain ODR | — | Synthesis only |

Each tier claim is sourced at its own entry in §2.2-§2.4 below.

### 2.2 Answer services — cannot be a rung

- **OpenAI deep research API** (`o3-deep-research`, `o4-mini-deep-research`, Responses API) returns a report with `url_citation`
  annotations. Two `include` options exist and neither returns page text: `web_search_call.action.sources` is "the complete list of
  URLs the model consulted" and `web_search_call.results` gives image metadata or "the search result snippets the model consulted"
  [https://developers.openai.com/api/docs/guides/tools-web-search; https://developers.openai.com/api/docs/guides/deep-research].
  Official model pages price `o3-deep-research` at $10 in / $40 out per 1M and `o4-mini-deep-research` at $2 / $8
  [https://developers.openai.com/api/docs/models/o3-deep-research]. **Notable inversion:** deep research accepts a remote MCP server
  implementing `search` and `fetch`, which would let *us* own the fetch rung and keep the raw text
  [https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/deep-research].
- **Gemini Deep Research** runs on the Interactions API as `deep-research-preview-04-2026` and `deep-research-max-preview-04-2026`,
  requires `background=True`, and returns a step sequence plus a report with `url_citation` annotations — **no step carries a
  fetched page body** [https://ai.google.dev/gemini-api/docs/interactions/deep-research]. Reported HLE 46.4%, BrowseComp 59.2%
  [https://blog.google/technology/developers/deep-research-agent-gemini-api/]. Google's own pages disagree on price: the Deep
  Research doc estimates $1-3 per task ($3-7 for Max) while the pricing page says all inference is "charged at standard Gemini list
  rates" [https://ai.google.dev/gemini-api/docs/pricing].
- **Kimi-Researcher** (2025-06-20) reports HLE 26.9% pass@1 and xbench-DeepSearch 69%; its weights were promised "in the following
  months" and, as of 2026-09-15, no Research/Researcher model appears on Moonshot's HuggingFace or GitHub organisations
  [https://moonshotai.github.io/Kimi-Researcher/]. Moonshot does ship standalone keyed **fetch and search endpoints**
  (`/v1/tools/fetch` returns `{url, title, markdown}`), which are plain HTTP with no model in the path
  [https://platform.kimi.ai/docs/api/tools-fetch.md].
- **Perplexity** and **Toast 1**: see §1.1 and §1.3.

### 2.3 Open deep-research systems — comparators, and a warning

| System | Licence | Stars / pushed | Fetch fidelity |
|---|---|---|---|
| **Tongyi DeepResearch** (30.5B / 3.3B MoE) | Apache-2.0 | 19,947 / 2026-02-27 | **summarise-only** |
| **GPT Researcher** | Apache-2.0 | 29,464 / 2026-08-27 | verbatim in memory, not on disk |
| **STORM** (Stanford OVAL) | MIT | 31,385 / **2025-09-30** | verbatim on disk |
| **LangChain Open Deep Research** | MIT | — / 2026-09-15 | **discards raw text** |
| **smolagents open Deep Research** | Apache-2.0 | — | markdown, whitespace-normalised |

- **Tongyi DeepResearch** reports HLE 32.9, BrowseComp 43.4, GAIA 70.9, xbench 75.0, WebWalkerQA 72.2, FRAMES 90.6 (Avg@3, max 128
  tool calls) [https://arxiv.org/abs/2510.24701]. Its `tool_visit.py` fetches through `r.jina.ai` into a local variable, truncates,
  and feeds an extractor prompt to a summariser LLM; only `evidence` and `summary` are returned and **nothing is written to disk.**
  Its own tool description is "Visit webpage(s) and return the summary of the content"
  [https://github.com/Alibaba-NLP/DeepResearch]. The model card says 30B/3B while the README and paper say 30.5B/3.3B; the latter
  two agree.
- **GPT Researcher** keeps full extracted text as `raw_content` and exposes it through `get_research_sources()`, but persists only
  the rendered report — **to quote-check, you must save `raw_content` yourself.** Its own DeepResearch Bench comparison (10 EN
  tasks, both arms on the same model) reports RACE 0.512 vs 0.503, but **effective verified citations 35.2 vs 18.6 (+89%)**
  [https://github.com/assafelovic/gpt-researcher/blob/master/deep_agents/BENCHMARK.md] — self-run against a baseline the same
  authors configured.
- **STORM** is the only one of these that **persists verbatim source text to disk** (`raw_search_results.json`, `url_to_info.json`),
  via trafilatura plus a 1,000-character splitter — though tables are excluded by default and `chunk_overlap=0` means a sentence
  straddling a boundary exists in no single snippet [https://github.com/stanford-oval/storm]. Its human expert study found STORM
  beat its baseline on organisation (p=0.005) but **not on verifiability (3.85 → 3.80, p=0.843)**
  [https://arxiv.org/abs/2402.14207]. Last push 2025-09-30 — a maintenance signal.
- **LangChain Open Deep Research** requests `include_raw_content=True` from Tavily and immediately summarises it away; the raw text
  never leaves the search function [https://github.com/langchain-ai/open_deep_research]. Its README claims a #6 DeepResearch Bench
  ranking at 0.4344 while the leaderboard CSV records 43.44 at rank 35 — **sources disagree; the primary CSV is what we cite** — and
  its **citation accuracy of 34.74**, against 78.30 for the best system, is the clearest published cost of discarding source text.

### 2.4 Fetch and search services — the traps that matter

- **Jina Reader is the only zero-friction keyless rung, and the most permissive licence in the set.** 20 RPM without a key, 500 RPM
  with a free key [https://jina.ai/reader/]; every new key comes with 10M free tokens. Its terms §4.3 state Jina "claims no rights
  to such Output and imposes no restrictions on the Customer regarding the use of the Output" [https://jina.ai/legal/]. Two
  cautions: **a probe on 2026-09-15 returned the warning "This is a cached snapshot of the original page, consider retry with
  caching opt-out"** — freshness is not guaranteed by default; and `x-respond-with: readerlm-v2` is a 1.54B model rewrite that must
  never be used for quotes. Its `html` mode is a re-serialised DOM, not the original bytes. Jina AI was acquired by Elastic in
  October 2025.
- **Firecrawl:** `markdown` is a deterministic filter with "no LLM involved", but `onlyMainContent` defaults **true**,
  `onlyCleanContent` is an LLM pass, and **`maxAge` defaults to 48 hours** — a scrape can return a two-day-old page unless `maxAge:
  0` is set [https://docs.firecrawl.dev/api-reference/endpoint/scrape]. Core is **AGPL-3.0**, SDKs MIT
  [https://api.github.com/repos/mendableai/firecrawl].
- **Tavily's silent elision:** on `/extract` and `/crawl`, `raw_content` is the full page **only when no `query` is supplied**; with
  a query it contains "the top-ranked chunks joined by `[...]` separator". A quote spanning such a boundary could verify as a false
  match. **Omit `query` for verification workloads.** [https://docs.tavily.com/documentation/api-reference/endpoint/extract]
- **Exa** returns "the clean page body as markdown" with the transformation undocumented, serves from cache unless `maxAgeHours: 0`
  is passed, and **contradicts itself on highlights** — the contents reference calls them "relevant passages copied from the page"
  while the search reference calls them "LLM-identified relevant snippets" [https://exa.ai/docs/reference/get-contents;
  https://exa.ai/docs/changelog].
- **Brave Search API — the one hard legal blocker in this survey.** Its terms (last updated 2026-09-01) define "Search Results" to
  include any API output, then forbid users to "store, cache, or create a database of Search Results, in whole or in part, other
  than transient storage required for operation", and forbid using them to "create, evaluate, train, re-train, fine-tune,
  **benchmark** or otherwise improve artificial intelligence models or services"
  [https://api-dashboard.search.brave.com/documentation/resources/terms-of-service]. **Saving Brave output to `raw/<n>.txt` for
  later verification, and scoring a pilot with it, both sit outside that licence as written.** Pricing is $5.00 per 1,000 Search
  requests with $5 in free credits monthly, and the free credit carries an attribution obligation [https://brave.com/search/api/].
- **Crawl4AI is the strongest open-source fit**: Apache-2.0, keyless, self-hosted, and `result.html` is the "Original, unmodified
  page HTML" [https://github.com/unclecode/crawl4ai]. Two cautions: the licence's attribution addendum says distributions "must
  include" an attribution while the README calls attribution "recommended" — **sources disagree**; and versions 0.8.7 and 0.9.3
  fixed critical Docker-server CVEs, so pin ≥0.9.3 if self-hosting.
- **SerpAPI-class services return pointers.** Serper's own published examples carry ellipses mid-snippet, so its output is unusable
  for character-level checking [https://serper.dev/terms]; SerpApi does return the raw HTML of the *results page* and retains it 31
  days [https://serpapi.com/legal].

**The conclusion this section forces:** every service that hands back something quotable does so because it fetched the page and
gave you the bytes. **Nothing here gives verbatim text our own `curl` could not have obtained** — what the paid tier sells is
getting through, not getting more — and the one service that would have been a tempting default, Brave, is the one whose terms our
verification design cannot satisfy.

---

## 3. Platform access, and what each platform's terms actually say

Facts and terms only. Where a route exists only by circumventing a login, paywall, CAPTCHA, bot check or published rate limit, it is
named **out of scope** and not described further.

**A finding that frames the rest:** several platform policy pages refuse the automated clients those policies govern.
`support.reddithelp.com` returned 403 to every automated client tried, three Discord policy pages returned 403, `developer.x.com`
returned 402, and the Reddit help pages had to be read through the Wayback Machine. Terms marked *(snippet-sourced)* below should be
re-read in a browser before anyone builds on them.

### 3.1 Reddit — no keyless path remains

- **Probes (§6):** `/r/<sub>/hot.json` returned **403 with an HTML block page**; `old.reddit.com` returned **302 to a login URL**.
  **[probe]**
- **Reddit says so itself.** The Data API Wiki (updated 2026-05-11) states: "Clients must authenticate with a registered OAuth
  token. We can and will freely throttle or block unidentified Data API users" and "Traffic not using OAuth or login credentials
  will be blocked, and the default rate limit will not apply."
  [https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki]
- **The widely-repeated "10 QPM unauthenticated" figure is obsolete** — unauthenticated traffic is blocked, not throttled, though
  third-party write-ups still quote it [https://www.socialcrawl.dev/blog/reddit-data-api-2026].
- **Published OAuth limit:** "The limit is: 100 queries per minute (QPM) per OAuth client id. QPM limits will be an average over a
  time window (currently 10 minutes) to support bursting requests." The archived pre-2023 wiki still says 60/minute; both are shown
  [same wiki URL; https://github.com/reddit-archive/reddit/wiki/API]. Required user-agent format is `<platform>:<app ID>:<version>
  (by /u/<username>)`, and "NEVER lie about your User-Agent."
- **robots.txt is a blanket deny** — `User-agent: *` / `Disallow: /`, commented "Reddit believes in an open internet, but not the
  misuse of public content" [https://www.reddit.com/robots.txt] — though Reddit adds that "Our robots.txt is for search engines, not
  Data API users."
- **Data API Terms** (effective 2023-06-19, last revised **2026-07-20**): §3.1 — commercial use or "research in excess of rate
  limits" requires "a separate agreement with Reddit"; §2.4 — no right "to use User Content… for training a machine learning or AI
  model, without the express permission of rightsholders"; §3.2 — no circumventing call limits, and no retaining data "beyond your
  approved use case… you must immediately delete any data not required for it" [https://www.redditinc.com/policies/data-api-terms].
- The Developer Terms go further, barring access "through any means (including… indexing, caching, or crawling…) to train large
  language, artificial intelligence, or other algorithmic models" without permission
  [https://www.redditinc.com/policies/developer-terms].
- **Retention duty:** deleted content must be deleted downstream, "we strongly recommend routinely deleting any stored user data and
  content within 48 hours", and retaining anonymized deleted content is "a violation of our terms and policies" [Data API Wiki].
- **A researcher programme exists** (page updated 2026-06-02): university affiliation, IRB or ethics approval and an institutional
  sponsor, non-commercial, at most one year, queried through BigQuery, all queries logged
  [https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program].
- **Consequence for us.** The only sanctioned route is the registered OAuth API within its limits, and the §3.2 retention clause
  bears directly on our run folder, which keeps `raw/<n>.txt` so a later audit can re-verify a quote. A Reddit adapter must treat
  that text as retained for the run's verification purpose only and deletable on request. **Our reading, not legal advice; settle it
  before shipping.** (Inference.)

### 3.2 X/Twitter — one narrow keyless path survives, and it is undocumented

- **Probe (§6):** `x.com/<handle>` returned **200, 57,733 bytes, 479 visible characters, no post text.** **[probe]**
- **Pricing is pay-per-usage since February 2026:** "X API v2 uses pay-per-usage pricing… No subscriptions. Pay only for what you
  use", with credits bought in the developer console; **Posts: Read $0.005 per resource**, and "Pay-per-usage plans are capped at 3
  million Post reads per monthly billing cycle" [https://docs.x.com/x-api/getting-started/pricing]; a third-party tracker says 2
  million, and both are shown [https://www.socialcrawl.dev/blog/x-twitter-api-2026]. The withdrawal of the Free/Basic/Pro tiers is
  **secondary-sourced only** — no first-party announcement was retrievable
  [https://roboin.io/article/en/2026/02/08/x-transitions-api-to-pay-per-use-model-ending-free-plan/] — corroborated negatively by
  the absence of any tier list in X's current pricing docs.
- **The keyless path that does work: oEmbed.** `GET https://publish.x.com/oembed?url=<post URL>` returned **200, JSON, no
  credentials, containing the post text verbatim** with `author_name` and the date [https://publish.x.com/oembed]. Limits: one post
  at a time by known URL, no search or timelines — and it now appears nowhere in X's documentation index, so it works but is
  **effectively undocumented; treat as unsupported.**
- **Everything else is closed.** `x.com/robots.txt` ends `User-agent: *` / `Disallow: /`, allowing only Googlebot, Bingbot and
  facebookexternalhit and explicitly disallowing `Google-Extended`, `FacebookBot` and the Meta AI crawlers
  [https://x.com/robots.txt]. Internal syndication endpoints are not published interfaces: **out of scope.**
- **Terms.** X's ToS (in force 2026-04-10) forbids accessing or searching the services "by any means (automated or otherwise) other
  than through our currently available, published interfaces… (NOTE: crawling or scraping the Services in any form, for any purpose
  without our prior written consent is expressly prohibited)" [https://x.com/en/tos]. The Developer Agreement (effective 2026-04-27)
  prohibits using the API or content "to fine-tune or train a foundation or frontier model"
  [https://docs.x.com/developer-terms/agreement]; the Developer Policy caps redistribution at 1,500,000 Post IDs per entity per 30
  days, with an academic carve-out [https://docs.x.com/developer-terms/policy].
- **Mirrors.** X Corp sent a cease-and-desist to the Nitter project on 2026-08-24 and nitter.net and XCancel went offline the next
  day [https://techcrunch.com/2026/08/25/x-sends-cease-and-desist-to-open-source-project-nitter-over-alleged-scraping/]; scraping
  mirrors sit outside a non-circumventing policy regardless.
- On this machine Hermes reaches X two keyed ways only: the official `xurl` CLI (OAuth 2.0 PKCE) and xAI's `x_search` tool (default
  `grok-4.5`, billable). **[local]**

### 3.3 GitHub — the most permissive large platform, and the best keyless surface here

- **Documented limits:** unauthenticated **60 requests/hour**; a personal access token **5,000/hour**; GitHub App installations from
  5,000 up to 12,500/hour; and "Some endpoints, like the search endpoints, have more restrictive limits"
  [https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api].
- **Probes (§6):** a keyless repo call returned 200 with `x-ratelimit-limit: 60` and `x-ratelimit-remaining: 56`; `GET /rate_limit`
  reported `core 60`, `search 10`, `code_search 60` and **`graphql 0`** — GraphQL has no unauthenticated allowance at all; and `GET
  /search/code` returned **401 "Requires authentication"**, matching the documented "The Search code endpoint requires you to
  authenticate and limits you to 10 requests per minute" [https://docs.github.com/en/rest/search/search]. **[probe]**
- **`raw.githubusercontent.com` is keyless, verbatim and undocumented.** Our probe returned 200 and 12,770 bytes of README markdown
  with **no `x-ratelimit-*` headers at all**. **[probe]** GitHub's 2025-05-08 changelog confirms new unauthenticated limits apply to
  "file downloads from raw.githubusercontent.com" but **publishes no number**
  [https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/], and a docs issue asking for it
  closed without a staff answer [https://github.com/github/docs/issues/8031]. Usable; budget conservatively and cache.
- **Terms are unusually friendly to this use.** The Acceptable Use Policies **expressly permit researchers and archivists** to use
  public information under conditions, while prohibiting "automated excessive bulk activity"
  [https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies]; ToS §D.5 (effective 2026-04-27)
  grants every user "a nonexclusive, worldwide license to use, display, perform and reproduce" public repository content, so
  **repository content is quotable** [https://docs.github.com/en/site-policy/github-terms/github-terms-of-service].

### 3.4 Hacker News — the friendliest surface in this survey

- **Probe (§6):** the Algolia search API returned 200 keyless. **[probe]** Published limit: "We are limiting the number of API
  requests from a single IP to 10,000 per hour" [https://hn.algolia.com/api] — a string in the page's JavaScript bundle, since a
  plain fetch of that SPA returns 86 visible characters. No rate-limit headers come back, so budgeting is client-side.
- **It returns comment and story text verbatim.** Indexed attributes include `story_text` and `comment_text` alongside `title`,
  `url`, `author`, `points` and `num_comments` [https://raw.githubusercontent.com/algolia/hn-search/master/README.md]; a live
  `tags=comment` hit carried a 1,607-character `comment_text`. `/items/:id` returns an entire comment tree with verbatim `text` in
  one call.
- **The official Firebase API is also keyless** — its README states "there is currently no rate limit" and documents `text` as "The
  comment, story or poll text. HTML." [https://raw.githubusercontent.com/HackerNews/API/master/README.md].
- **Sources disagree in effect.** `news.ycombinator.com/robots.txt` sets `Crawl-delay: 30` and disallows only state-changing paths,
  while YC's Terms of Use — scoped to "the Y Combinator website (including all subdomains)" — say "you will not engage in or use any
  data mining, robots, scraping or similar data gathering or extraction methods" [https://news.ycombinator.com/robots.txt;
  https://www.ycombinator.com/legal]. Both are shown. The defensible posture: take HN content through the two machine interfaces YC
  itself publishes rather than through HTML, and honour the crawl delay where no API equivalent exists.

### 3.5 Stack Exchange — keyless, with the body, plus a licence obligation

- **Probe (§6):** `filter=withbody` returned 200, `quota_max: 300`, `quota_remaining: 299`, and a 2,944-byte question body.
  **[probe]**
- **The documented throttles** [https://api.stackexchange.com/docs/throttle]: "If a single IP is making more than 30 requests a
  second, new requests will be dropped"; a token-less application shares an IP-based quota "which by default is 10,000"; and "If an
  application receives a response with the `backoff` field set, it must wait that many seconds before hitting the same method
  again". **Sources disagree on the keyless number — 300/day observed live versus 10,000/day documented** — because the documented
  figure attaches to a registered key. Plan against 300 and read `quota_remaining` from every response.
- **Bodies are excluded by default and verbatim with a filter**; `body_markdown` (the original Markdown source) is available through
  a custom filter creatable keyless [https://api.stackexchange.com/docs/filters]. Anonymous access is page-capped at page 25
  [https://api.stackexchange.com/docs].
- **Licence metadata comes back per item.** Every question object carries `content_license` (CC BY-SA 2.5 before 2011-04-08, 3.0 to
  2018-05-02, **4.0 after**) [https://stackoverflow.com/help/licensing] — read the field, do not infer from the date. Attribution is
  a terms obligation with a carve-out that suits a text deliverable: "For applications that lack access to web browsing services,
  simple text versions of URLs (instead of hyperlinks) will be sufficient" [https://stackexchange.com/legal/api-terms-of-use].
- **Every Stack Exchange web property now disallows all crawling** — `stackoverflow.com/robots.txt` is a `License:` pointer,
  `User-agent: *`, `Content-signal: search=no, ai-train=no`, `Disallow: /` [https://stackoverflow.com/robots.txt] — while
  `api.stackexchange.com` publishes no robots.txt, so the deny does not attach to the API host.
- The Acceptable Use Policy's scraping clause is **purpose-based**, prohibiting automated collection for building a competing
  service or for "training, testing, indexing, benchmarking, or improving any generative AI, chatbot, large language, or machine
  learning tool" [https://stackoverflow.com/legal/acceptable-use-policy]. Low-volume read-and-cite is not among the listed purposes;
  note "indexing". The separate MCP server terms go further — "You may not use the MCP Service for the long-term or programmatic
  storage, indexing, or caching of Stack Overflow Content" [https://stackoverflow.com/legal/mcp-server-terms-of-use] — so **use the
  REST API, not the MCP server, for anything that writes to disk.** (Inference from the two documents.)

### 3.6 YouTube — the terms settle it

- The Terms of Service (effective 2025-03-17) prohibit "access[ing] the Service using any automated means (such as robots, botnets
  or scrapers) except: (a) in the case of public search engines, in accordance with YouTube's robots.txt file; (b) with YouTube's
  prior written permission; or (c) as permitted by applicable law" [https://www.youtube.com/t/terms]. `youtube.com/robots.txt`
  disallows the entire `/api/` path for all non-Mediapartners crawlers [https://www.youtube.com/robots.txt], which closes carve-out
  (a) for the undocumented `timedtext` endpoint.
- The Developer Policies (last updated 2026-09-14) are decisive twice over: III.E.6 "must not… scrape YouTube Applications", and
  III.I.14 forbids using "any technology other than YouTube API Services to access or retrieve API Data". Retention of API data is
  capped at **30 calendar days** absent specific consent [https://developers.google.com/youtube/terms/developer-policies].
- The official path does not help: `captions.download` "requires the user to have permission to edit the video" and `captions.list`
  returns track metadata only — "the API response does not contain the actual captions"
  [https://developers.google.com/youtube/v3/docs/captions/download; https://developers.google.com/youtube/v3/docs/captions/list].
  **There is no permitted route to transcripts for videos we do not own.**
- **Verdict: do not adopt a YouTube rung.** This reverses the intuition that transcripts are "just public text", and it is the
  clearest terms-based exclusion in this survey.

### 3.7 Discord and Telegram — one closed, one with a documented public page

- **Discord.** Reading message content requires a bot token, a human with Manage Server permission to invite the bot, **and** the
  privileged Message Content intent, which is review-gated
  [https://support-dev.discord.com/hc/en-us/articles/5324827539479-Message-Content-Intent-Review-Policy]. The unauthenticated
  endpoints that exist (`/guilds/{id}/widget.json`, `/guilds/{id}/preview`) return counts and anonymised member fields, never
  message content [https://docs.discord.com/developers/resources/guild]. **Probe (§6):** a keyless invite-page fetch returned **200,
  18,381 bytes, 54 visible characters**, carrying only Discord's generic marketing metadata. **[probe]** The ToS (effective
  2025-09-29) prohibits "scraping our services without our written consent, including by using any robot, spider, crawler, scraper"
  [https://discord.com/terms], and the Developer Policy states "You may not mine or scrape any data, content, or information
  available on or through Discord services"
  [https://github.com/discord/discord-api-docs/blob/main/docs/policies_and_agreements/Developer_Policy.md]. A clause barring use of
  message content to train AI models appears in the live policy but not the versioned repository copy — *(snippet-sourced)*
  [https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy]. **Verdict: leave out.** Access is an
  arrangement with a community, not a retrieval rung.
- **Telegram.** **Probe (§6):** `t.me/s/durov` returned **146,102 bytes with 16,122 visible characters of post text**, keyless.
  **[probe]** And unlike most such paths, **it is documented**: Telegram announced it on 2019-05-31 — "You can now view any public
  channel from the web – even if you aren't logged in to Telegram" [https://telegram.org/blog/privacy-discussions-web-bots] — and
  its channels page notes such content "can be seen on the Web without a Telegram account and are indexed by search engines"
  [https://telegram.org/tour/channels]. `t.me/robots.txt` returns 404, so no robots directive applies either way. The page carries
  full post text, ISO-8601 timestamps, view counts and `?before=` paging. **But the terms restrict bulk and AI use.** The API ToS
  prohibit "using, accessing or aggregating data obtained from the Telegram platform to train, fine-tune or otherwise engage in the
  development… of artificial intelligence, machine learning models" [https://core.telegram.org/api/terms], and the Content Licensing
  and AI Scraping Terms extend a prohibition on "scraping, indexing, harvesting, aggregation" to "anyone accessing user-generated
  content beyond ordinary platform use" [https://telegram.org/tos/content-licensing]. Both are undated. **Reading and quoting a
  handful of posts with attribution is ordinary platform use; harvesting a channel is not, and training on it is expressly
  prohibited.** Adopt only with that limit in the adapter. (Inference, flagged.) A Telegram **bot** cannot read channel history: the
  Bot API has no history method and updates "will not be kept longer than 24 hours" [https://core.telegram.org/bots/api].

### 3.8 Scholarly and news — three of these tightened in 2025-2026

- **arXiv.** Binding terms: "make no more than one request every three seconds… a single connection at a time"; metadata is CC0;
  e-print content is not — users may "retrieve, store, and use the content… for research purposes" but must not "store and serve
  arXiv e-prints… from your servers" [https://info.arxiv.org/help/api/tou.html]. **Probe:** 200, 4,297 bytes of Atom with verbatim
  abstracts. **[probe]** Users have reported repeated 429s since late February 2026, with staff replying "Yes, we have made changes
  recently and over time" and no new figure [https://groups.google.com/a/arxiv.org/g/api/c/ycq8giRdZsQ] — treat 1-per-3s as a floor,
  not a guarantee.
- **OpenAlex — the biggest change in this survey: API keys became mandatory in February 2026.** The announcement of 2026-01-14
  states "API calls will require a key starting one month from today (Feb 13)" and "No more polite pool! No more email parameter in
  your calls" [https://groups.google.com/g/openalex-users/c/rI1GIAySpVQ]. **Probe (§6) confirms the new economics first-hand:** a
  keyless call returned 200 with `x-ratelimit-limit: 1000`, `x-ratelimit-credits-used: 10`, **`x-ratelimit-limit-usd: 0.1`**, and
  the `mailto` parameter made no difference. **[probe]** The help centre gives a keyless budget of **$0.10/day** and a free-key
  budget of **$1/day** [https://help.openalex.org/access/example-costs/]. Old docs URLs now redirect and the GitHub docs source
  still carries the abolished polite-pool instructions — a stale source anyone re-auditing this will hit. Data is CC0, the **bulk S3
  snapshot remains free and keyless** [https://help.openalex.org/download/download-to-machine], and OpenAlex ships
  `abstract_inverted_index`, not a plaintext abstract.
- **Semantic Scholar.** **Probe:** a first, single, polite keyless request returned **429** with "Please wait and try again or apply
  for a key for higher rate limits". **[probe]** Published keyless figures disagree — "1000 requests per second shared among all
  unauthenticated users" [https://www.semanticscholar.org/product/api] versus "5,000 requests per 5 minutes… shared pool"
  [https://github.com/allenai/s2-folks/blob/main/API_RELEASE_NOTES.md] — and either way the pool was exhausted when we arrived.
  Abstracts are verbatim (Springer excepted); full text is not served, only an `openAccessPdf` link.
- **GDELT.** **Probe:** a first DOC 2.0 request returned **429** whose body is itself the policy: "Please limit requests to one
  every 5 seconds… All high-traffic users should switch to our ngrams dataset". **[probe]** The DOC API returns `url`, `title`,
  `seendate`, `domain`, `language`, `sourcecountry` — **no body text**, so it is a search rung at best
  [https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/]. Its terms are unusually permissive — "unlimited and unrestricted use…
  without fee", conditioned on citation — but that covers GDELT's metadata, **not** the linked articles
  [https://www.gdeltproject.org/about.html].
- **Common Crawl CC-NEWS** is the keyless way to get news **bodies** — gzipped WARC files over plain HTTPS, no credentials, still
  updating through 2026 [https://data.commoncrawl.org/crawl-data/CC-NEWS/2026/index.html] — but its terms state crawled content "may
  be subject to separate terms of use… from the owners", so **Common Crawl's licence does not launder publishers' copyright**
  [https://commoncrawl.org/terms-of-use].
- **Wikimedia — the cheapest throughput lesson in this survey.** The 2026 limits are per minute and global: **unidentified requests
  10/min, requests carrying a User-Agent 200/min** [https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits], with the UA policy
  naming `python-requests` and `curl` as blockable [https://foundation.wikimedia.org/wiki/Policy:User-Agent_policy]. **A
  descriptive, honest user agent is a 20x throughput increase for free** — and we already send one.

### 3.9 Blogs, docs and the trading-bot long tail

- **Medium** returned **403 with a Cloudflare interstitial** ("Sorry, you have been blocked… You are unable to access medium.com")
  and **Substack** (`substack.com/@handle`) returned **302 to a search URL**. **[probe]** Our gate already classifies the former as
  `failed:block-page`, and Wayback is the existing answer.
- **Exchange API documentation mostly moves under you rather than blocking you:** a Binance developer docs URL returned **302** to a
  changelog path and a Coinbase docs URL **308**. **[probe]** Neither is a bot wall; both are redirects an adapter must follow and a
  citation must pin — so cite dated or versioned documentation URLs where the vendor publishes them, and record the post-redirect
  URL in the source row. (Inference.)

---

## 4. The benchmarks these systems report, and why they miss what our pilot measures

Every system in §1 and §2 markets itself on a benchmark number, and almost none of those numbers describes the thing our pilot
grades. This section exists so round 2 does not chase a leaderboard that answers a different question.

| Benchmark | Items | Task shape | Scoring | Source |
|---|---|---|---|---|
| **BrowseComp** | 1,266 | short answers, "hard to find, easy to verify" | model grader, semantic equivalence | [2504.12516](https://arxiv.org/abs/2504.12516) |
| **BrowseComp-ZH / -Plus** | 289 / 830 | same, Chinese web / **fixed 100,195-doc corpus** | same | [2504.19314](https://arxiv.org/abs/2504.19314), [2508.06600](https://arxiv.org/abs/2508.06600) |
| **GAIA** | 466 (166 public) | 3 levels, tool use, files | **quasi-exact match on the final answer only** | [2311.12983](https://arxiv.org/abs/2311.12983) |
| **HLE** | 2,500 | closed-book expert questions | accuracy + calibration | [2501.14249](https://arxiv.org/abs/2501.14249) |
| **SimpleQA** | 4,326 | one indisputable short answer | classifier: correct / incorrect / **not attempted** | [2411.04368](https://arxiv.org/html/2411.04368v1) |
| **WebWalkerQA** | 680 | *vertical* traversal into subpages | short-answer accuracy | [2501.07572](https://arxiv.org/abs/2501.07572) |
| **xbench-DeepSearch** | 100 | search tasks, kept encrypted to avoid crawling | accuracy | [2506.13651](https://arxiv.org/abs/2506.13651) |
| **FRAMES** | 824 | multi-hop over 2-15 Wikipedia articles | factuality + retrieval + reasoning | [frames-benchmark](https://huggingface.co/datasets/google/frames-benchmark) |
| **Mind2Web / WebArena** | 2,000+ / 4 site clones | acting on websites | step success / **programmatic functional correctness** | [2306.06070](https://arxiv.org/abs/2306.06070), [2307.13854](https://arxiv.org/abs/2307.13854) |
| **DeepResearch Bench** | **100 PhD-level tasks**, 50 ZH / 50 EN | long-form research report | **RACE** rubric judge + **FACT** citation pipeline | [2506.11763](https://arxiv.org/abs/2506.11763) |
| **ResearchQA** | 21K queries, 160K rubric items | scholarly long-form answers | query-specific rubric items | [2509.00496](https://arxiv.org/abs/2509.00496) |
| **LiveDRBench** | 100 tasks | deep research on the live web | claim/subclaim precision and recall | [2508.04183](https://arxiv.org/html/2508.04183v1) |

Reference points: BrowseComp — GPT-4o 0.6%, o1 9.9%, Deep Research 51.5%, human trainers 29.2% with about 71% giving up after two
hours [https://arxiv.org/html/2504.12516v1]; WebArena GPT-4 agent 14.41% against a human 78.24% [https://arxiv.org/abs/2307.13854].

**Three families, and where we sit.** Short-answer retrieval (BrowseComp, GAIA, SimpleQA, WebWalkerQA, xbench, FRAMES) measures
whether the agent found the needle. Task execution (Mind2Web, WebArena, and AssistantBench [https://arxiv.org/abs/2407.15711])
measures acting, which our skill deliberately does not do. Only the third family — DeepResearch Bench, ResearchQA, LiveDRBench — is
in the same business as our pilot.

**We are closest to DeepResearch Bench, and differ in one specific way.** Its RACE score uses criteria and weights **generated per
task by the judge**, normalised against a reference report as `target / (target + reference)` [https://arxiv.org/abs/2506.11763].
Ours uses **human-written, question-specific rubrics fixed in advance**, scored absolutely, with no reference in the denominator.
Our numbers are therefore **not comparable** to a RACE score in either direction.

The half worth borrowing is **FACT**: extract statement-URL pairs, deduplicate, re-fetch, make a binary support judgment, and report
citation accuracy and average effective citations — reported at 92-96% agreement with human support labels [same paper]. That is
`cite_audit.py` under another name, and reporting our audit against a published protocol is cheaper than inventing a metric. The
published spread is stark: LangChain Open Deep Research scores **citation accuracy 34.74** where the best system scores 78.30
(§2.3).

**Published limitations, including two that cut against us.**
- **The short-answer benchmarks disclaim generalisation themselves.** BrowseComp "sidesteps challenges of a true user query
  distribution, like generating long answers or resolving ambiguity" [https://arxiv.org/html/2504.12516v1]; SimpleQA's limitations
  section says whether short-answer factuality correlates with "lengthy, multi-fact responses remains an open research question"
  [https://arxiv.org/html/2411.04368v1]; GAIA grades only the final answer [https://arxiv.org/html/2311.12983v1]. **A high
  BrowseComp score is not evidence that a system writes a good report** — which is what several products in §1-§2 invite the reader
  to assume.
- **Search-time contamination.** Agents retrieve the public benchmark files mid-run; a 2026 study measures this on BrowseComp, GAIA,
  PubMedQA, MedQA and MMLU and reports inflated scores **and changed model rankings** once contaminated items are excluded
  [https://arxiv.org/pdf/2606.05241]. xbench's answer is to ship the dataset encrypted
  [https://huggingface.co/datasets/xbench/DeepSearch]. **This argues for keeping our eval questions private, which we already do,
  and against ever publishing them.**
- **Two credible positions in tension.** BrowseComp-Plus argues "dynamic and opaque web APIs hinder fair comparisons and
  reproducibility" and uses a fixed corpus [https://arxiv.org/abs/2508.06600]; LiveDRBench argues static corpora misrepresent a
  changing web [https://arxiv.org/html/2508.04183v1]. Our pilot is live-web by construction.
- **The strongest caution lands on our own protocol.** A 2026 meta-evaluation finds human pairwise preference too coarse to capture
  expert expectations, finds pairwise rankings validate whole *systems* but not individual *metrics*, and concludes that reliable
  metric-level validation needs metric-wise expert annotations [https://arxiv.org/abs/2603.06942]. Our calibration state — a
  model-only stand-in, Opus/Sonnet kappa 0.79, the ten-report hand-grading pack still ungraded — is exactly that gap.
- **Long-form research is not near ceiling, and our numbers are on an easier instrument.** No ResearchQA system exceeds roughly
  70-75% rubric-item coverage [https://arxiv.org/abs/2509.00496] and LiveDRBench's best F1 is 0.55
  [https://arxiv.org/html/2508.04183v1]. Our 0.92-1.00 compliance figures come from a handful of hand-written rubrics, not a broad
  held-out set, and **must never be quoted alongside those numbers as if they were the same scale.** (Inference from the scoring
  definitions, not a measured comparison.)
- **Judge swaps break comparability.** DeepResearch Bench's official evaluator moved from Gemini-2.5-Pro to GPT-5.5 on 2026-05-11
  [https://github.com/Ayanami0730/deep_research_bench]. We hit the same hazard with our v1.3 judge-prompt change and handled it the
  same way: re-judge before pairing.

---

## 5. Hermes agent (Nous Research) — the second harness, inspected first-hand

Facts marked **[local]** were read from the installation on this machine: **Hermes Agent v0.21.3 (2026.9.14)**, install method
`git`, Python 3.11.16, at `~/.hermes/hermes-agent`, inspected 2026-09-15. Hermes Agent is **MIT-licensed**
[https://github.com/NousResearch/hermes-agent/blob/main/LICENSE] and its installer bundles Python 3.11, Node, ripgrep and ffmpeg
[https://hermes-agent.nousresearch.com/docs/getting-started/installation].

### 5.1 Tools it ships with

- **Web search and extract are provider-backed, chosen from environment keys.** `tools/web_tools.py` auto-detects a backend in this
  order: `tavily`, `perplexity`, `exa`, `parallel`, `keenable`, `firecrawl`, `firecrawl` again via the Nous managed **Tool Gateway**
  subscription, `searxng` (self-hosted), `brave-free`, and a `ddgs` DuckDuckGo path; the default when nothing is configured is
  `firecrawl`, and search and extract backends can be set independently. **[local]** The docs match — `web_search` returns
  titles/URLs/descriptions and **`web_extract`** returns clean markdown or text from pages and PDFs — but web search, image
  generation, TTS and browser automation route through the Nous Portal Tool Gateway for paid subscribers, so `web_search` is **not
  unconditionally keyless** [https://hermes-agent.nousresearch.com/docs/user-guide/features/tools].
- **X is keyed twice over.** `tools/x_search_tool.py` registers `x_search` only with an xAI credential (`XAI_API_KEY` or `hermes
  auth add xai-oauth`), calling xAI's `x_search` Responses tool with default model `grok-4.5`; the code notes the OAuth path answers
  in a degraded mode while an API key returns real posts, and each call bills. Separately the `social-media/xurl` skill wraps the X
  developer platform's **official CLI** (OAuth 2.0 PKCE, raw v2 access). **There is no keyless X read path on Hermes either.**
  **[local]**
- Also present: `terminal` and `process`, `execute_code` (sandboxed Python that can call Hermes tools by RPC), file tools, and
  browser backends over CDP, Lightpanda and Camoufox. Camoufox is an anti-detection browser fork — recorded here as an observed fact
  about the install, **not** a recommendation. **[local]**

### 5.2 Skill layout, and whether it can run our scripts

- **Three-tier precedence:** project-local `<repo>/.hermes/skills/` or `<repo>/.agents/skills/` (a cross-tool convention), then
  user-local `~/.hermes/skills/<category>/<name>/SKILL.md`, then `skills.external_dirs`. Per-skill directories carry `SKILL.md` plus
  `references/`, `templates/`, **`scripts/` ("helper scripts callable from the skill")**, `examples/` and `assets/`
  [https://hermes-agent.nousresearch.com/docs/user-guide/features/skills]. Frontmatter is YAML with `name`, `description`,
  `version`, `author`, `license`, `platforms` and a `metadata.hermes` block, validated by
  `tools/skill_manager_tool.py::_validate_frontmatter`. **[local]**
- **Hermes states its skills "are compatible with the agentskills.io open standard"**, and agentskills.io states the format "was
  originally developed by Anthropic, released as an open standard" [https://agentskills.io/] — so the layout is the Agent Skills
  standard plus additive metadata: an adapter concern, not a core one.
- **Skills bundle and run scripts.** `research/grounded-citations` ships a 678-line `scripts/sources.py` described as "stdlib-only
  Python 3" and invoked as `python "$S" <command>`; `web/blocked-page-recovery` ships `scripts/recover_page.py`. **So a Hermes skill
  can run our Python scripts as-is, provided they stay stdlib-only** — which ours are. **[local]** One caution: inside the
  `execute_code` sandbox only a fixed tool subset is callable, so an adapter should drive our scripts through `terminal`.
- Models are provider-agnostic, but the docs warn **Hermes 4 (70B/405B) is not tool-call-tuned and "will struggle with multi-step
  agent loops"** — a Hermes port of our skill should not be evaluated on it
  [https://hermes-agent.nousresearch.com/docs/integrations/nous-portal].

### 5.3 Hermes already ships two skills that overlap ours

**`web/blocked-page-recovery` v1.0.0 (MIT)** is a fallback ladder — Wayback → archive.today (domain rotation) → Jina Reader (only
with `JINA_API_KEY`) → an API-first pivot (look for `/api/`, `.json` or RSS on the same host) → a real browser last — with a bundled
script that "validates every body" against **"fake successes"**, and a provenance rule that an archived copy must be cited with its
snapshot date and never presented as live. **[local]** That is our `fetch.py` ladder and our plausibility gate, arrived at
independently by another team in the second target harness. Two differences favour us: it puts Jina behind a key where we use the
keyless tier, and its API-first pivot is an instruction to the model where ours would be code. The convergence is evidence that the
ladder in `fetch-reliability-survey.md` is the standard answer, not a local invention.

**`research/grounded-citations` v1.2.0 (MIT, "Hermes Agent + Teknium")** is the comparison that matters: **a quote-checked source
ledger in the second harness.** In its own words: "A ledger script owns the `url → [n]` mapping so the numbers and URLs come from
retrieval, never from memory"; `sources.py quote <id> --text … --from page.txt` attaches evidence and "The quote is rejected unless
it appears verbatim in the evidence text (insensitive to whitespace, case, and markdown markup)"; unsourceable claims are marked
`[unverified]`; `verify --evidence` "fails the draft if any cited source has no attached quote". Its "Multi-Platform Sweeps" section
fans out across Reddit, RSS, YouTube, `gh search` and X, instructing the agent to "Keep opinion and measurement apart: a Reddit
thread is evidence that users *report* something, not that it is true." **[local]**

**Does Hermes already have what we built?** Partly, and honestly: a script-owned URL→id ledger, verbatim-quote rejection against
saved page text, an evidence gate that fails a draft, and a multi-platform fan-out instruction. Anyone claiming our quote check is
novel should read this skill first.

**What ours adds**, observed from its command set (`reset`, `add`, `ingest`, `quote`, `list`, `render`, `verify`) and its SKILL.md
rather than a full code audit:
- **It is a *source* ledger, not a *claim* ledger.** Quotes hang off sources; there are no claim objects, so no claim status, no
  `central` vs `supporting` distinction, and nothing for a verifier to grade.
- **No corroboration model.** Cross-checking is prose advice ("two independent sources are corroboration"), not a field a script can
  enforce or count.
- **No source grading and no link health** — grepping the SKILL.md for grade, health, link-check or archive returns nothing, and
  there is no separate verifier role.
- **No post-hoc re-verification** — no equivalent of `cite_audit.py` re-fetching a published report's URLs.
- **No multi-agent decomposition or run folder.** It is a citation discipline for one agent's draft, not a workflow producing
  `report.md`, `angles/*.md`, `verification.md` and `run.json`.

**Inference, stated as inference:** the projects are complementary, and the honest positioning for round 2 is that our
differentiator is **the claim ledger with grading, corroboration and post-hoc audit** — not the verbatim quote check, which is now
table stakes in at least two harnesses.

---

## 6. Live probes from this machine [probe]

About twenty keyless requests were made from this machine on 2026-09-15 (18:35-18:40 UTC, one residential-class IP on macOS, `curl`
with a normal Chrome user agent, one request each, no retries on 403/429, no cookies, no key). The ten that carry findings are
tabulated here; the rest are reported where they matter in §1.4 and §3. "Verbatim-quotable" means the bytes on disk contain the
source's own wording, so `cite_check.py` could match a quote against them.

| # | Target | Status | Bytes | Verbatim-quotable? | Note |
|---|---|---|---|---|---|
| 1 | `www.reddit.com/r/algotrading/hot.json?limit=2` | **403** | 189,908 | **no** | HTML block page, not JSON |
| 2 | `old.reddit.com/r/algotrading/` | **302** | 0 | **no** | redirects to a login URL |
| 3 | `api.github.com/repos/freqtrade/freqtrade` | 200 | 7,144 | yes (metadata) | `x-ratelimit-limit: 60` |
| 4 | `raw.githubusercontent.com/.../README.md` | 200 | 12,770 | **yes** (source file) | plain markdown, no key |
| 5 | `hn.algolia.com/api/v1/search?query=trading+bot` | 200 | 2,521 | yes (titles/URLs) | pointers + story metadata |
| 6 | `export.arxiv.org/api/query?...` | 200 | 4,297 | **yes** (abstracts) | Atom XML |
| 7 | `api.openalex.org/works?search=...&mailto=` | 200 | 56,753 | yes (metadata/abstract idx) | credit headers returned |
| 8 | `x.com/freqtrade` | **200** | 57,733 | **no** | 479 visible chars, no post text |
| 9 | `t.me/s/durov` | 200 | 146,102 | **yes** | 16,122 visible chars of post text |
| 10 | `api.stackexchange.com/2.3/questions?...&filter=withbody` | 200 | 3,817 | **yes** (question body) | `quota_max: 300` |

Two of these change the round-2 plan, and both are the silent-failure pattern from `fetch-reliability-survey.md` §1.0 — a block is
still a page.

- **Reddit's public `.json` path did not work from this machine.** It returned **HTTP 403 with a 189,908-byte HTML body** whose
  entire visible text is *"You've been blocked by network security. If you think you've been blocked by mistake, file a ticket below
  and we'll look into it. File a ticket"* — 143 visible characters inside 190 KB of markup, `content-type: text/html` on a `.json`
  URL. A status check catches this one; a "did I get bytes?" check does not. **`old.reddit.com` returned 302 to a login URL** with a
  zero-byte body; following it would be a login wall, which is out of scope. *(One IP, one day: proof we cannot rely on the path,
  not that Reddit blocks everyone.)*
- **`x.com/freqtrade` returned HTTP 200 and 57,733 bytes containing no posts.** Stripped of markup the body has **479 visible
  characters**: the handle, follower counts, "Log in or sign up for X", and *"@freqtrade hasn't posted"*. `og:title` carries
  `freqtrade (@freqtrade) on X`. So a keyless X fetch yields a 200, a plausible title, real byte volume, and **no evidence** — the
  worst shape a fetch can have for a ledger, because the fetch gate sees success. Any X evidence must come from the official API
  (keyed).
- **GitHub keyless works and is honest about its budget** — `x-ratelimit-limit: 60`, `x-ratelimit-remaining: 56`,
  `x-ratelimit-resource: core` — so an adapter can read its remaining budget instead of guessing.
- **`raw.githubusercontent.com` is the strongest new fetch rung here**: keyless, 200, and the bytes are the repository file itself —
  what a verbatim quote check wants, with no markup to strip. **Telegram's public channel preview returned real post text
  keylessly** (146 KB of HTML carrying 16,122 visible characters, quotable as-is), and **Stack Exchange's keyless API answered with
  the post body** (`quota_max: 300`, `quota_remaining: 299`, a 2,944-byte HTML question body), showing its remaining daily quota in
  every response.

---

## 7. Fit table: what can plug into our ledger

**Rung meaning:** *Fetch* = returns text we can save to `raw/<n>.txt` and quote from. *Search* = pointers only; a snippet is not
evidence. *Neither* = an answer service or a competing workflow. **Cost class** is what the cited page says. **Terms fit** is our
reading of the cited terms for *our* use — polite, low-volume, attributed research fetching with no circumvention — and is not legal
advice.

| Option | Rung | Key | Cost class | Terms fit | Verdict |
|---|---|---|---|---|---|
| **`raw.githubusercontent.com`** | **Fetch** | keyless | free | AUP permits researchers/archivists; limits undocumented | **adopt** |
| **GitHub REST API** | Fetch (metadata) | keyless (token raises 60→5,000/hr) | free | as above | **adopt** |
| **GitHub code search** | Search | **token required** (401 keyless) | free | as above | adopt with token |
| **Stack Exchange API 2.3** (`withbody`) | **Fetch** | keyless (300/day) or key (10,000) | free | AUP purpose-based; CC BY-SA attribution required | **adopt** |
| **HN Algolia + Firebase** | Search + Fetch (comment text) | keyless | free | APIs are first-party; YC ToU forbids scraping the site | **adopt (APIs only)** |
| **Telegram `t.me/s/<channel>`** | **Fetch** | keyless | free | documented public page; bulk/AI use prohibited | **adopt, read-and-quote only** |
| **arXiv API** | Fetch (abstracts) | keyless, 1 req/3 s | free | research use permitted; do not re-serve e-prints | already rung 1 |
| **Jina Reader** | **Fetch** | keyless 20 RPM / **free key 500 RPM** | free | "imposes no restrictions… regarding the use of the Output" | already rung 4; **add the free key** |
| **Wayback / Common Crawl** | Fetch | keyless | free | CC terms do not launder publisher copyright | already rung 6 |
| **OpenAlex** | Search (metadata) | **key now effectively required** | keyless ≈$0.10/day | CC0 data | low priority |
| **Semantic Scholar** | Search (abstracts) | keyless pool exhausted; key advised | free | attribution required | low priority |
| **GDELT DOC 2.0** | Search | keyless, 1 req/5 s | free | unusually permissive for its metadata | low priority |
| **Reddit Data API** | Fetch (post text) | **OAuth required** | free within limits; research above them needs an agreement | retention clause constrains `raw/` | **keyed adapter, off by default** |
| **X API v2** | Fetch (post text) | **keyed, pay-per-use** | $0.005 per post read | scraping prohibited; API is the only route | **keyed adapter, off by default** |
| **X `publish.x.com/oembed`** | Fetch (one post) | keyless | free | official endpoint, now undocumented | narrow, opportunistic |
| **Crawl4AI** (`result.html`) | **Fetch (raw bytes)** | keyless, self-hosted | free (Apache-2.0) | attribution addendum; pin ≥0.9.3 | optional JS rung |
| **Firecrawl** (`rawHtml`) | **Fetch (raw bytes)** | keyed cloud / keyless self-host | 1,000 credits free/mo | AGPL-3.0 core | optional keyed rung |
| **Tavily** (`/extract`, no `query`) | Fetch | keyed | 1,000 credits free/mo | no storage prohibition found | optional keyed rung |
| **Zyte** (`httpResponseBody`) | **Fetch (raw bytes)** | keyed | ~$0.13-1.27 per 1,000 | customer bears lawful-use responsibility | optional, best-documented fidelity |
| **Exa** | Search (+ processed text) | keyed | $7 per 1,000 searches | — | not for quotes |
| **Brave Search API** | Search | keyed | $5 per 1,000; $5 free credits/mo | **storing results and benchmarking with them are prohibited** | **excluded** |
| **SerpApi / Serper** | Search | keyed | $25+/mo; 2,500 free queries | permissive terms | optional keyed rung |
| **Perplexity Search / Agent API** | Search / Neither | keyed | $5 per 1,000 searches | display scoped to your app; "competitive" suspension clause | not a rung |
| **OpenAI / Gemini deep research** | Neither | keyed | $1-7 per task (Gemini estimate) | — | competing workflow |
| **Toast 1 (Mixedbread)** | Neither (opaque) | keyed | ~$0.016-0.023 per query | — | competing workflow |
| **MiroThinker / MiroFlow** | Neither (a model + framework) | Apache-2.0, keyed tools | — | — | comparator |
| **Agent-Reach** | Fetch via cookies | user session | free | cookie routes outside our scope | **excluded** |
| **YouTube transcripts** | — | OAuth + ownership | — | ToS III.I.14 forbids non-API retrieval | **excluded** |
| **Discord** | — | invited bot + intent | — | scraping prohibited; no public read path | **excluded** |
| **Hermes `grounded-citations`** | n/a (a ledger) | — | MIT | — | overlaps ours; see §5.3 |

---

## 8. Recommendations for round 2

### 8.1 Verified versus inferred

**Verified** (primary source or dated probe, all above): no Perplexity endpoint returns verbatim page text; MiroThinker and MiroFlow
reach pages with Jina plus a keyed SERP API; Toast 1 is closed-weights, corpus-first, with a hidden retrieval loop; Agent-Reach is
MIT scaffolding whose Reddit and X routes replay a user's browser cookies and whose own README warns of bans; Reddit blocks
unauthenticated traffic by policy and did so to us; a keyless X page fetch returns 200 with no posts while `publish.x.com/oembed`
returns one verbatim; `raw.githubusercontent.com`, the GitHub REST API, HN Algolia, arXiv, Stack Exchange with `filter=withbody` and
`t.me/s/<channel>` all returned quotable text keylessly; GDELT and Semantic Scholar refused a first polite request; OpenAlex now
meters keyless callers in credits; Brave's terms forbid storing results and benchmarking with them; Hermes ships both a fetch ladder
and a verbatim-quote source ledger of its own.

**Inference** (reasoned, not measured): that the adapters below raise rubric compliance on community-evidence questions; that our
differentiator is the claim ledger rather than the quote check; that per-rung cost and failure profiles will resemble the existing
chain's. **None of this is tested.** Round 2 should run one question — the trading-bot brief is the obvious candidate — before any
of it is believed.

### 8.2 Add these five rungs

All are **additive**: the default keyless chain is unchanged, each is skipped when unconfigured, and every one produces raw text on
disk that `cite_check.py` can verify.

1. **GitHub — `raw.githubusercontent.com` plus the REST API, keyless, optional token.** The strongest new fetch rung here: the bytes
   are the repository file itself, so a quote from a README, a config or a source line is byte-exact with no markup to strip, and
   the API publishes its remaining budget in `x-ratelimit-*`. Today we reach GitHub only through `gh` when it happens to be
   installed. For the trading-bot use case this is where the primary evidence lives. Budget conservatively on `raw.`, whose limits
   GitHub declines to document.
2. **Stack Exchange API 2.3 with `filter=withbody`, keyless.** Returns question and answer bodies — the thing a quote needs —
   reports its own remaining quota, and signals politeness explicitly through `backoff`. The adapter must carry `content_license`
   into the source row and honour the attribution obligation, which the terms let a text deliverable satisfy with a plain URL.
3. **Hacker News, keyless: Algolia to find threads, Firebase or `/items/:id` for the text.** Community reasoning about tooling lives
   here, and both interfaces are first-party and return comment text verbatim. Use the APIs, never the HTML.
4. **Telegram public channel previews (`t.me/s/<channel>`), keyless, tightly bounded.** The only community platform that returned
   real post text to a plain fetch, and Telegram announced the path itself in 2019. Write the adapter to the limit the terms draw:
   read and quote a few posts with attribution; never harvest a channel; never train.
5. **The official Reddit and X APIs, keyed, off by default.** These are the only routes to the two platforms we will take. A run
   without credentials must **declare the gap in the report** rather than silently substituting a worse source — a 200 from a
   logged-out X page is the most dangerous artefact in this survey precisely because it looks like success.

**Plus one free upgrade that is not a new rung:** get a **free Jina Reader key**. It raises our existing rung from 20 to 500
requests per minute at no cost — a 25x throughput increase — and while we are there, send the cache opt-out, because Reader served
us a cached snapshot unprompted on 2026-09-15.

**Two optional keyed rungs for JS-only pages**, in preference order: **Crawl4AI** self-hosted (Apache-2.0, keyless, `result.html` is
unmodified) and **Firecrawl** with `rawHtml` and `maxAge: 0`. Both return raw bytes; both are opt-in.

### 8.3 Leave these out, and why

- **Brave Search API.** Its 2026-09-01 terms forbid storing or caching results and forbid using them to "benchmark… artificial
  intelligence models or services". Our design saves raw text to disk and scores a pilot with it. **This is a terms conflict, not a
  preference.**
- **YouTube transcripts.** The Developer Policies forbid using "any technology other than YouTube API Services" to retrieve the
  data, and the official caption download requires edit permission on the video. There is no permitted route for videos we do not
  own.
- **Discord.** No public read path; scraping is prohibited; a keyless invite fetch returns marketing metadata. Reading a server is
  an arrangement with a community, not a rung.
- **Cookie and session-replay routes** (Agent-Reach's Reddit and X backends and anything like them) and **anti-detection browsers**,
  including the Camoufox backend in the Hermes install: outside our scope decision, and documented by their own authors as
  ban-risking. **Answer services as retrieval layers** — Perplexity, Toast 1, OpenAI and Gemini deep research — return no verbatim
  page text, and attaching a quote to their prose is the precise failure `cite_check.py` exists to catch.
- **Exa and Tavily-with-a-query as quote sources.** Exa's transformation is undocumented and its own docs disagree on whether
  highlights are copied or model-generated; Tavily's `raw_content` silently becomes elided chunks joined by `[...]` when a `query`
  is passed, which could make a spanning quote verify falsely.

### 8.4 Does anything here replace our workflow?

**No — but two things replace parts of it, and one overlaps it more than we assumed.**

- **Toast 1 and the hosted deep-research APIs replace the researcher-agent layer**, not the ledger. They return curated evidence or
  a finished report; neither exposes a per-source trace we could grade, and neither states that its text is byte-exact. If anyone
  revisits them, byte-exactness is the deciding question.
- **Hermes's `grounded-citations` skill overlaps our quote check almost exactly** — script-owned URL→id ledger, verbatim rejection
  against saved page text, an evidence gate that fails a draft. What it lacks is a *claim* ledger: no claim objects, no
  corroboration labels, no source grades, no link health, no post-hoc audit, no run folder. **That, not the quote check, is what we
  should be claiming as the contribution.**
- **The negative result is the most useful finding for round 2.** The best open stacks reach pages with Jina Reader plus a keyed
  SERP API — the two rungs we already have — and Agent-Reach, with 82,000 stars and a mandate to reach exactly the platforms our
  user cares about, resorts to browser cookies for two of them. **There is no retrieval channel we are missing.** What is missing is
  coverage of a handful of specific, permitted, mostly keyless platform APIs — which is what §8.2 adds.

---

## Sources

All URLs accessed **2026-09-15** unless the text gives another date; bracketed dates are the document's own stated effective,
revision or publication date. Secondary sources are cited inline at the point of use and marked there; this list is the primary set.

**§1 named tools.** docs.perplexity.ai: /getting-started/models, /api-reference/search-post, /docs/agent-api/overview,
/docs/agent-api/tools/fetch-url, /getting-started/pricing · perplexity.ai/hub/legal/perplexity-api-terms-of-service [2026-01-23] ·
github.com/MiroMindAI/MiroThinker and /MiroFlow (+ docs/mkdocs/docs/tool_searching.md) · huggingface.co/miromind-ai/MiroThinker-1.7
· arxiv.org/abs/2511.11793, /abs/2603.15726 · mixedbread.com/blog/toast-1 [2026-08-13] and /pricing ·
github.com/mixedbread-ai/toast-harness · huggingface.co/mixedbread-ai · github.com/Panniantong/Agent-Reach (README,
docs/README_en.md) · api.github.com/repos/Panniantong/Agent-Reach · wavect.io/blog/agent-reach-open-source-review/

**§2 systems and services.** developers.openai.com/api/docs/guides/deep-research, /guides/tools-web-search,
/api/docs/models/o3-deep-research · ai.google.dev/gemini-api/docs/interactions/deep-research [2026-08-26], /docs/url-context,
/docs/pricing · blog.google/technology/developers/deep-research-agent-gemini-api/ ·
firebase.google.com/docs/ai-logic/grounding-google-search · moonshotai.github.io/Kimi-Researcher/ [2025-06-20] ·
platform.kimi.ai/docs/api/tools-fetch.md · github.com/Alibaba-NLP/DeepResearch + arxiv.org/abs/2510.24701 ·
github.com/assafelovic/gpt-researcher (+ deep_agents/BENCHMARK.md) · github.com/stanford-oval/storm + arxiv.org/abs/2402.14207,
/abs/2408.15232 · github.com/langchain-ai/open_deep_research · huggingface.co/blog/open-deep-research [2025-02-04] ·
github.com/browser-use/browser-use · github.com/unclecode/crawl4ai · docs.firecrawl.dev/api-reference/endpoint/scrape +
api.github.com/repos/mendableai/firecrawl · exa.ai/docs/reference/get-contents, /docs/changelog ·
docs.tavily.com/documentation/api-reference/endpoint/extract · jina.ai/reader/, jina.ai/legal/ [2026-05-04] · brave.com/search/api/,
api-dashboard.search.brave.com/documentation/services/llm-context and /resources/terms-of-service [2026-09-01] ·
docs.zyte.com/zyte-api/usage/http.html · serpapi.com/legal [2026-08-27] · serper.dev/terms · scrapingbee.com/documentation/

**§3 platforms and terms.** support.reddithelp.com Data API Wiki [2026-05-11] and Reddit for Researchers [2026-06-02] ·
redditinc.com/policies/data-api-terms [rev. 2026-07-20], /policies/developer-terms · reddit.com/robots.txt ·
docs.x.com/x-api/getting-started/pricing, /x-api/introduction, /developer-terms/agreement [2026-04-27], /developer-terms/policy ·
x.com/en/tos [2026-04-10], x.com/robots.txt · publish.x.com/oembed · techcrunch.com/2026/08/25 (Nitter cease-and-desist) ·
docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api, /en/rest/search/search,
/en/site-policy/github-terms/github-terms-of-service [2026-04-27], /en/site-policy/acceptable-use-policies ·
github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/ · github.com/github/docs/issues/8031 ·
hn.algolia.com/api · raw.githubusercontent.com/algolia/hn-search/master/README.md, /HackerNews/API/master/README.md ·
news.ycombinator.com/robots.txt · ycombinator.com/legal · api.stackexchange.com/docs/throttle, /docs/filters ·
stackoverflow.com/help/licensing, /robots.txt, /legal/acceptable-use-policy, /legal/mcp-server-terms-of-use ·
stackexchange.com/legal/api-terms-of-use · youtube.com/t/terms [2025-03-17], /robots.txt ·
developers.google.com/youtube/terms/developer-policies [2026-09-14], /youtube/v3/docs/captions/download, /captions/list ·
github.com/jdepoix/youtube-transcript-api · discord.com/terms [2025-09-29] · docs.discord.com/developers/resources/guild ·
github.com/discord/discord-api-docs (Developer_Policy.md) · core.telegram.org/api/terms, /bots/api ·
telegram.org/blog/privacy-discussions-web-bots [2019-05-31], /tour/channels, /tos/content-licensing ·
info.arxiv.org/help/api/tou.html · groups.google.com/a/arxiv.org/g/api/c/ycq8giRdZsQ ·
groups.google.com/g/openalex-users/c/rI1GIAySpVQ [2026-01-14] · help.openalex.org/access/example-costs/,
/download/download-to-machine · semanticscholar.org/product/api · github.com/allenai/s2-folks (API_RELEASE_NOTES.md) ·
blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ · gdeltproject.org/about.html · commoncrawl.org/terms-of-use · data.commoncrawl.org
CC-NEWS index · mediawiki.org/wiki/Wikimedia_APIs/Rate_limits [2026-06-03] · foundation.wikimedia.org/wiki/Policy:User-Agent_policy

**§4 benchmarks.** arxiv.org/abs/: 2504.12516 (BrowseComp), 2504.19314, 2508.06600, 2311.12983 (GAIA), 2501.14249 (HLE), 2411.04368
(SimpleQA), 2501.07572 (WebWalker), 2506.13651 (xbench), 2407.15711 (AssistantBench), 2306.06070 (Mind2Web), 2307.13854 (WebArena),
2506.11763 (DeepResearch Bench), 2509.00496 (ResearchQA), 2508.04183 (LiveDRBench), 2606.05241 (search-time contamination),
2603.06942 (meta-evaluation of long-form judges) · github.com/openai/mle-bench · github.com/Ayanami0730/deep_research_bench ·
huggingface.co/datasets/google/frames-benchmark, /datasets/xbench/DeepSearch

**§5 Hermes.** github.com/NousResearch/hermes-agent (LICENSE) · hermes-agent.nousresearch.com/docs/getting-started/installation,
/docs/reference/tools-reference/, /docs/user-guide/features/tools, /docs/user-guide/features/skills, /docs/user-guide/features/mcp,
/docs/integrations/nous-portal · agentskills.io · **[local]** inspection of `~/.hermes` and `~/.hermes/hermes-agent/tools`, Hermes
Agent v0.21.3 (2026.9.14), 2026-09-15.

**§6 probes.** About twenty keyless requests from this machine on 2026-09-15, 18:35-18:40 UTC; the ten that carry findings are
listed with targets, status codes and byte counts in §6, the others at the point of use. Raw bodies and response headers were kept
in the session scratchpad, not committed to the repository.
