# Fetch Reliability Survey: why agent web fetches fail, and keyless fallbacks that work

**Question:** Why do agent web search and page fetches fail, and what keyless fallback strategies do popular
open-source research/browsing agents use to get page content reliably?

**Scope:** portable "deep research" skill for AI coding agents. Primary harness: Claude Code (built-in
`WebSearch` / `WebFetch`). **No paid API keys.** Anti-detection projects are described factually; this
document deliberately contains **no operational instructions for defeating CAPTCHAs, paywalls, or login walls**.

**Compiled:** 2026-09-02. All URLs accessed 2026-09-02 unless noted.
**Method:** official docs + GitHub source, plus ~40 live `curl`/`urllib`/WebFetch probes run from this machine on
2026-09-02 (marked **[probe]**). Probe results are one-IP, one-day snapshots, not benchmarks.

---

## Fallback methods at a glance

| Method | Solves | Fails on | Needs key? | Needs install? | Portability | Example repo using it |
|---|---|---|---|---|---|---|
| **Keyless structured API** (Crossref, OpenAlex, arXiv, `gh`, Wikipedia REST, RSS/Atom) | Robots-clean, boilerplate-free, anti-bot-free access to the *exact* resource | Only works where the URL has a known shape | no | no | **highest** — `curl` only | gpt-researcher `ArxivScraper`; storm arXiv RM |
| **Harness tool** (Claude Code `WebFetch`) | Zero setup, 15-min cache, pre-approved doc domains | robots.txt refusals, JS pages, PDFs, verbatim quotes >125 chars, swallowed error bodies | no | no | **lowest** — Claude Code only | Claude Code skills |
| **Raw HTTP + browser-like headers** (`curl` / stdlib `urllib`) | Naive-UA 403s, redirects, content-type triage via `HEAD`, full raw text | Cloudflare/DataDome/Akamai challenges, JS pages, IP-reputation blocks | no | no | **highest** | smolagents ODR; gpt-researcher `bs`; storm `WebPageHelper` |
| **Reader proxy** — `r.jina.ai` | JS rendering **[probe]**, boilerplate removal, HTML→markdown, some anti-bot (their IPs) | per-domain anonymous abuse blocks (403), possible cached-not-live content, their outages | **no** (keyless tier works) | no | **high** — one GET | jina-ai/node-DeepResearch (keyed) |
| **Archive** — Wayback availability + `id_` snapshot; CDX | Dead links, robots-blocked publishers, fabricated-URL detection | Never-archived pages, `noarchive`, content drift; `archive.today` 429s **[probe]** | no | no | **high** | smolagents ODR `find_archived_url` |
| **Local extraction** — `pdftotext`, trafilatura, readability, markdownify | PDFs (incl. WebFetch's silently-saved binary), boilerplate | Nothing to extract if the fetch itself failed | no | **yes** (but `pdftotext` often present) | high, degrade-gracefully | storm (trafilatura); smolagents (pdfminer); gpt-researcher (PyMuPDF) |
| **Headless browser** — playwright-mcp, chrome-devtools-mcp, agent-browser | JS rendering, consent clicks, forms, client-side pagination | Turnstile/managed challenges, CAPTCHAs, login walls | no | **yes** — a browser (chrome-devtools-mcp and agent-browser reuse system Chrome) | medium — MCP or CLI | microsoft/playwright-mcp |
| **Managed scrape API** — Firecrawl, Tavily extract | Most of the above at once | Cost; self-hosted Firecrawl loses the anti-bot layer entirely | **yes** (cloud) | yes (self-host: Docker stack) | low | dzhng/deep-research; gpt-researcher |
| **Stealth fetchers** — curl_cffi, nodriver, Camoufox, Scrapling | TLS/JA3 + fingerprint mismatch detection | IP reputation; decays as vendors adapt; **ToS/legal grey area — excluded from this project's scope** | no | varies (curl_cffi light; Camoufox 313–663 MB) | medium | Scrapling `StealthyFetcher` |
| **Search snippet as evidence** | Something is better than nothing | Paraphrase only, no page-level provenance, unquotable | no | no | **highest** | storm (8 of 11 retrievers are snippet-only) |
## 1. Failure taxonomy

### 1.0 The meta-failure: silent failure

The single most important finding in this survey is that **most fetch failures do not look like failures.**
A block page is still a page: it has a `<title>`, prose, and a 200-ish status, so an LLM summarizes it with
full confidence.

- A test of 8 sites behind major anti-bot vendors (Cloudflare, Akamai, PerimeterX, CloudFront WAF, DataDome —
  Indeed, Zillow, Walmart, StockX, Booking, Amazon, Etsy, G2) found a naive fetch got **real content 0/8 times,
  a summarizable response body 8/8 times, and a signal the agent could use to know it had been blocked 0/8
  times.** Status codes seen were 403, 307 and **200**, all carrying full HTML block pages.
  "Nothing in the response said the fetch had failed... The quiet block page slips through because it looks
  like content." [https://tilion.dev/blog/cloudflare-blocks-agents]
- Design consequence: **every fallback chain needs a content-plausibility gate, not just a status-code check.**
  See §4.

**[probe]** `https://webcache.googleusercontent.com/search?q=cache:example.com` returns **HTTP 200, 300 KB**,
whose visible text is `"cache:example.com - Google Search ... Before you continue to Google We use cookies and
data, including IP addresses..."` — a consent wall, not a cache. A status-code-only check scores this as success.

### 1.1 Bot detection: 403 / 429 / 401 / silent 200

- Cloudflare announced "Content Independence Day" on **2025-07-01**, "changing the default to block AI crawlers
  unless they pay creators for their content." The same post states that generating referral traffic from
  OpenAI's crawlers is "750 times more difficult" than from Google search, and **Anthropic's ratio is "30,000
  times more difficult"** — i.e. Anthropic's crawlers fetch vastly more than they refer, which is exactly the
  economics driving publishers to block.
  [https://blog.cloudflare.com/content-independence-day-no-ai-crawl-without-compensation/]
- Between July 2025 and January 2026 the number of websites actively blocking AI crawlers was reported as
  **nearly 7x** the number blocking traditional search crawlers such as Googlebot. *(secondary reporting —
  unverified against a primary dataset)* [https://tilion.dev/blog/cloudflare-blocks-agents]
- DataDome's 2025 Global Bot Security Report found only ~7% of ~17,000 tested sites blocked advanced
  anti-fingerprinting bots — i.e. protection is common but *sophisticated* protection is not. *(secondary
  reporting; the primary report is gated — unverified)*
  [https://datadome.co/guides/scraping/scraper-crawler-bots-how-to-protect-your-website-against-intensive-scraping/]

**[probe] User-Agent alone does not rescue a blocked fetch.** Identical `curl` requests, default UA vs a full
Chrome 126 UA + `Accept-Language` + `Accept`:

| URL | default UA | browser UA |
|---|---|---|
| `https://www.reuters.com/` | 401 | **401** |
| `https://www.g2.com/` (DataDome) | 403 | **403** |
| `https://news.ycombinator.com/` | 200 | 200 |
| `https://arxiv.org/abs/2103.03874` | 200 | 200 |

Browser-like headers fix *naive-UA* filters (some CDNs 403 on `curl/8.x` alone), but they do **not** fix
IP-reputation, TLS-fingerprint, or challenge-based blocking. Treat UA hygiene as cheap and worth doing, never
as a solution.

### 1.2 JavaScript-rendered pages

- Anthropic's own docs state it plainly: "The web fetch tool currently does not support websites dynamically
  rendered with JavaScript. For pages that need a real browser (JavaScript rendering, clicking, or filling
  forms), consider the browser use tool."
  [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool]

**[probe]** Modern SPAs usually return *some* text, not zero — which is worse than returning nothing, because
it looks like a successful fetch. Raw HTML bytes vs. visible text after stripping tags/scripts:

| URL | raw HTML | visible text |
|---|---|---|
| `https://x.com/anthropicai` | 285,853 B | **2,378 chars** |
| `https://www.notion.so/` | 241,356 B | **2,588 chars** |
| `https://vercel.com/blog` | 447,165 B | **4,119 chars** |

A useful heuristic falls out of this: **a text:HTML ratio below roughly 1–2% on a page that should be an
article is a JS-rendering or block-page signal**, and should trigger the next fallback even on a 200.

### 1.3 robots.txt refusal

This is a *first-class* failure mode for Claude Code specifically, because Anthropic's fetcher self-identifies.

- Anthropic runs three separately-addressable crawlers: **ClaudeBot** (training data), **Claude-User**
  ("supports Claude AI users. When individuals ask questions to Claude, it may access websites using a
  Claude-User agent"), and **Claude-SearchBot** (search-quality indexing). The bots "respect 'do not crawl'
  signals by honoring industry standard directives in robots.txt", and support the non-standard `Crawl-delay`.
  Rules must be applied per-subdomain; blocking one token does not block the others. Anthropic publishes crawler
  IPs at `https://claude.com/crawling/bots.json`.
  [https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler]
- Claude Code's WebFetch was changed to **identify as `Claude-User`** so operators can recognize and allowlist
  it via robots.txt (reported for v2.1.172). *(This entry did not appear in the current official changelog page
  when fetched — **unverified** against the primary changelog.)*
  [https://code.claude.com/docs/en/changelog]
- The API-side `web_fetch` server tool returns error code **`url_not_allowed`**: "URL blocked by domain
  filtering rules (including your organization's settings) or by Anthropic-side restrictions, such as private
  addresses and `robots.txt`."
  [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool]

**[probe] Confirmed end-to-end.** `https://www.nytimes.com/robots.txt` contains:

```
User-agent: ClaudeBot
Disallow: /

User-agent: Claude-SearchBot
Disallow: /

User-agent: Claude-User
Disallow: /
```

and a Claude Code `WebFetch` of `https://www.nytimes.com/2024/01/01/technology/index.html` returned exactly:
`Claude Code is unable to fetch from www.nytimes.com`. No status code, no body, no stated reason.
*(The error string does not distinguish robots.txt refusal from a domain-safety-check denial — **unverified**
which of the two fired. Operationally it does not matter: the URL is unfetchable via WebFetch.)*

**Consequence for a research skill:** major news and reference publishers are permanently unreachable through
WebFetch regardless of network conditions, and the error is indistinguishable from a transient one. The skill
must not retry these; it must switch strategy or record UNFETCHABLE.

### 1.4 Paywalls, logins, consent walls, redirects

- Claude Code's WebFetch "fails on authenticated/private URLs" by design (tool description).
- Cross-host redirects are **not followed**: WebFetch "returns a text result naming the original URL and the
  redirect target instead of following it", requiring a second call. Same-host redirects are followed.
  This means any login/consent redirect that crosses hosts costs an extra turn and can loop.
  [https://code.claude.com/docs/en/tools-reference]
- GDPR consent interstitials frequently return **200 with real-looking prose** (the Google-cache probe in §1.0
  is the archetype). **[probe]** Several EU publishers (`spiegel.de`, `lemonde.fr`, `independent.co.uk`)
  returned 200 to a plain browser-UA `curl` from a US IP without an interstitial, so consent walls are
  jurisdiction- and IP-dependent and cannot be assumed either way.

### 1.5 Rate limits

- API `web_search` / `web_fetch` both define **`too_many_requests`: Rate limit exceeded**, returned inside a
  **HTTP 200** response body, not as an HTTP error.
  [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool]
- **[probe]** Keyless third-party limits measured today:
  - `api.github.com` unauthenticated: **60 requests/hour** (`"core": {"limit": 60}`).
  - `api.semanticscholar.org` keyless: **HTTP 429** on the second request in a burst.
  - `html.duckduckgo.com/html/` and `lite.duckduckgo.com/lite/`: **HTTP 202** with an "anomaly" page and
    **zero result links** — soft-blocked (see §2.6).
  - `r.jina.ai` anonymous: per-domain blocks (see §2.2).
  - `archive.ph`: **HTTP 429**.
  - No limit hit on `api.crossref.org`, `api.openalex.org`, `export.arxiv.org`, `en.wikipedia.org/api/rest_v1`,
    `archive.org/wayback/available`, `web.archive.org/cdx`.

### 1.6 PDFs and non-HTML content

- The API `web_fetch` supports **only text, HTML and PDF**; anything else returns `unsupported_content_type`.
  PDFs come back base64-encoded and are processed like an attached document.
  [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool]
- **Claude Code's local WebFetch behaves differently and worse.** **[probe]** `WebFetch` on
  `https://arxiv.org/pdf/2103.03874` produced: *"the PDF file you've shared appears to be in
  compressed/binary format (it's a PDF stream), making it difficult for me to extract the title"* — the
  extraction model was handed the raw PDF stream and failed.
- **But the same call silently wrote the bytes to disk**, appending:
  `[Binary content (application/pdf, 1.9MB) also saved to
  ~/.claude/projects/<project>/<session>/tool-results/webfetch-<ts>-<rand>.pdf]`
- **[probe]** `pdftotext -l 1 <that file>` immediately yielded
  `Measuring Mathematical Problem Solving With the MATH Dataset / arXiv:2103.03874v2 [cs.LG] 8 Nov 2021`.
- **This is the single highest-value operational trick in this survey:** a Claude Code WebFetch of a PDF is not
  a failed fetch, it is a *download*. The correct recovery is to read the path out of the tool result and run a
  local extractor on it — no re-download, no key, no network.

### 1.7 Very large pages and token limits

Claude Code's WebFetch pipeline (reverse-engineered from runtime behavior, not source — treat as
**approximately correct, unverified**):

| Stage | Limit |
|---|---|
| URL length | ~2 KB |
| HTTP fetch ceiling | ~10 MB |
| HTML→Markdown | Turndown |
| Truncation | **100,000 characters** |
| Extraction model | Haiku 3.5, empty system prompt, **125-char max quote length** |
| Tool-result budget | ~50,000 characters |
| Cache | 15 min TTL, keyed by URL |

[https://mikhail.io/2025/10/claude-code-web-tools/] and
[https://github.com/LiranYoffe/reverse-engineering-claude-code-web-tools]

The **125-character quote cap** is the important one for a research skill: WebFetch structurally cannot return
a long verbatim passage. If the skill needs quotable evidence longer than ~125 chars, WebFetch is the wrong
tool and a raw fetch is required.

On the API side, `max_content_tokens` truncates text (not PDFs); docs give ~2,500 tokens per 10 KB page,
~25,000 for a 100 KB doc page, ~125,000 for a 500 KB research PDF.
[https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool]

### 1.8 Claude Code `WebFetch` specifics — answers to the direct questions

| Question | Answer | Source |
|---|---|---|
| Does it respect robots.txt? | **Effectively yes.** It identifies as `Claude-User`, which honors robots.txt; a robots-disallowed publisher returned a flat refusal **[probe]**. API-side, robots.txt is named explicitly under `url_not_allowed`. | support.claude.com 8896518; platform.claude.com web-fetch-tool; **[probe]** |
| Does it route through a proxy? | **The page fetch is local**, from your machine/IP, and honors `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY` (no SOCKS). But **every fetch first sends the hostname to `api.anthropic.com`** for a domain safety check. | [https://code.claude.com/docs/en/network-config] |
| What is that preflight? | "Before fetching a URL, the WebFetch tool sends the requested hostname to `api.anthropic.com` to check it against a safety blocklist maintained by Anthropic. Only the hostname is sent, not the full URL, path, or page contents." Passing hostnames cached 5 min; blocked/failed hostnames re-checked next request. Runs on **all** providers, unaffected by `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`. If `api.anthropic.com` is blocked, **WebFetch fails entirely** unless you set `skipWebFetchPreflight: true`. | [https://code.claude.com/docs/en/data-usage] |
| Does it summarize rather than return raw HTML? | **Yes — lossy by design.** It converts HTML→Markdown (not configurable) and runs your prompt against it with "a small, fast model"; Claude receives *the extraction model's answer, not raw page content*. The docs warn: "a result that says a page doesn't mention something may only mean the prompt didn't ask about it." | [https://code.claude.com/docs/en/tools-reference] |
| Domain restrictions? | Permission rules `WebFetch(domain:example.com)` / `WebFetch(domain:*)`; allow-rules persist to `.claude/settings.local.json`. A set of built-in pre-approved documentation domains skips the prompt (reported as ~107 domains, **unverified**). `--restricted` / `CLAUDE_CODE_RESTRICTED=1` removes WebFetch entirely unless named in `--tools` (v2.1.248). | tools-reference; [https://code.claude.com/docs/en/changelog] |
| Caching | 15 min per URL; `CLAUDE_CODE_WEBFETCH_CACHE_TTL_MS` to change (v2.1.243). v2.1.239 fixed expired content being retained for the whole session. | [https://code.claude.com/docs/en/changelog] |
| HTTP → HTTPS | Auto-upgraded. | tools-reference |
| Does it surface HTTP error bodies? | **No.** anthropics/claude-code issue #68273, "WebFetch does not return response body on HTTP error codes" — the agent cannot see a proxy's or rate-limiter's explanation and "tries to circumvent the block instead". Opened 2026-06-13, **closed as not planned / stale**. | [https://github.com/anthropics/claude-code/issues/68273] |
| Availability | Not available on Amazon Bedrock, Google Cloud's Agent Platform, or Microsoft Foundry. | tools-reference |
| Tool description advice | "If an MCP-provided web fetch tool is available, prefer using that tool instead" (fewer restrictions); prefer `gh` CLI for GitHub URLs. | [https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/tool-description-webfetch.md] |

**Net:** WebFetch has at least six independent ways to fail that the caller cannot distinguish — robots refusal,
safety-blocklist denial, preflight network failure, HTTP error with a swallowed body, JS-empty page, and
Haiku-summarized-away content — and all of them can surface as either a short refusal string or a confident
but wrong summary.

### 1.9 What `WebSearch` returns

- Claude Code's `WebSearch` tool description: **"Search the web. Returns result blocks with titles and URLs.
  US-only."** with `allowed_domains` / `blocked_domains` filters.
- Under the hood it invokes the Anthropic API server tool `web_search_20250305` in a secondary conversation.
  Reverse-engineering reports that Claude Code extracts only `title` and `url` from each result and **discards
  `page_age` and `encrypted_content`**. [https://mikhail.io/2025/10/claude-code-web-tools/]
- The API-side result shape is `{url, title, page_age, encrypted_content}` — `encrypted_content` is opaque to
  the API caller and must be echoed back verbatim on later turns. Citations carry `cited_text` of **up to 150
  characters**. Search is billed at **$10 per 1,000 searches** on the API.
  [https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool]
- **Observed in this session:** results arrived as a `Links: [{title, url}, ...]` array **plus a paragraph of
  model-written prose synthesizing the underlying result content** — so there is real information beyond
  titles, but it is *paraphrase, not verbatim snippet*. **You cannot quote a WebSearch result.**
  *(Mechanism partly unverified.)*

**Consequence:** WebSearch is a URL discovery tool and a weak-evidence tool. It is never a substitute for
fetching, and anything it says must be recorded as paraphrase with no page-level provenance.

---

## 2. Fallback strategies in the wild

### 2.0 How six deep-research repos actually handle fetch failure

Read from source at pinned commits on 2026-09-02: gpt-researcher `6f99857`, open_deep_research `1b7d2e8`,
dzhng/deep-research `1f8f3e2`, node-DeepResearch `fd323b5`, smolagents `30bb116`, storm `fb951af`.

| Repo | Fetch mechanism | Fallback chain | Key required | User-Agent | What a failure leaves behind |
|---|---|---|---|---|---|
| **assafelovic/gpt-researcher** | own `requests` / Selenium / `zendriver`, or Tavily / Firecrawl API | **none across scrapers**; 1 HTTP retry + PDF re-route | no (bs default) | Chrome/119 Edg (config) | logged, then **silently dropped** |
| **langchain-ai/open_deep_research** | **none — never fetches a page**; Tavily/Anthropic/OpenAI search APIs only | n/a | `TAVILY_API_KEY` | **none** | summarizer failure → raw content + WARNING; tool errors → string to model |
| **dzhng/deep-research** | Firecrawl `search`+`scrape` in one call | none | `FIRECRAWL_KEY` | n/a (server-side) | `console.log`; **whole query's results discarded** |
| **jina-ai/node-DeepResearch** | `r.jina.ai` reader (POST) | none, but hostname blacklist + agent told to change angle | `JINA_API_KEY` | none (server-side) | `badURLs[]` + `badHostnames[]` — **best-in-class** |
| **smolagents open_deep_research** | `requests` + vendored `mdconvert` | **Wayback via `find_archived_url`** (model-driven) | no for fetching | Chrome/119 Edg (hardcoded) | **error page returned to the model as content** |
| **stanford-oval/storm** | `httpx(verify=False)` + trafilatura, Bing/Google paths only | none | Bing/Google keys | **none** (`python-httpx`) | `print()` to stdout, **silently dropped** |

Three design stances emerge: **outsource entirely** (open_deep_research, dzhng, jina), **fetch and hide
failures** (gpt-researcher, storm), and **fetch and hand the failure to the LLM** (smolagents). Only
node-DeepResearch keeps a first-class, queryable record of what failed.

#### gpt-researcher — the block-page detector worth copying

Dispatch at [`gpt_researcher/scraper/scraper.py:307-352`](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/scraper.py#L307-L352)
is **URL-shape-based, not a fallback chain**: `.pdf` path suffix → `PyMuPDFScraper`; `"arxiv.org" in link` →
`ArxivScraper`; otherwise the one configured scraper. If `bs` fails, nothing escalates to `browser` or
`firecrawl`.

Eight registered scrapers: `bs` (default, keyless `requests`+bs4), `web_base_loader`, `pdf` (PyMuPDF),
`arxiv` (abstract only), `browser` (Selenium, `headless=False`, visits google.com first to harvest cookies),
`nodriver` (`zendriver` CDP, ≤5 browsers, per-domain `Semaphore(1)`), `tavily_extract` (**key**),
`firecrawl` (**key**). The last two `pip install` their SDK at construction time
([scraper.py:160-192](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/scraper.py#L160-L192)).

UA at [`config/variables/default.py:20`](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/config/variables/default.py#L20):
`Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0`.

Retry is minimal: exactly **one** retry after `time.sleep(1)` on exception or
`RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}`; any status `>= 400` after that returns `None`.
`Content-Length > 10 MB` is skipped.
[[beautiful_soup.py:58-104]](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/beautiful_soup/beautiful_soup.py#L58-L104)

**The valuable part** — four *fetched-but-rejected* classes at
[scraper.py:232-281](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/scraper.py#L232-L281),
i.e. an implemented answer to §1.0's silent-failure problem:

- `len(content) < 100` → "Content too short or empty"
- `_looks_like_block_page` — case-insensitive scan of the **first 5000 chars** against `_BLOCK_PAGE_MARKERS`:
  `"attention required! | cloudflare"`, `"sorry, you have been blocked"`,
  `"anubis uses a proof-of-work scheme"`, `"please verify you are a human"`, …
- `_looks_like_word_list` — ≥200,000 chars with <1 sentence-terminator per 5000 chars
- `_looks_like_unextracted_pdf` — `%PDF-` prefix, or ≥2 of `endobj`/`endstream`/`/FlateDecode`/`xref`/`trailer`

All four still collapse to `raw_content: None` and are filtered out
([scraper.py:153-157](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/scraper.py#L153-L157)),
so the user sees only `"📄 Scraped N pages of content"` — the diff between requested and returned is the sole
failure signal. Sharp edge: `NoDriverScraper.scrape_async` returns **the exception string as page content**
(`return str(e), [], ""`,
[nodriver_scraper.py:246-251](https://github.com/assafelovic/gpt-researcher/blob/6f998577d547b1e54ec662dac63583aa11e3b84b/gpt_researcher/scraper/browser/nodriver_scraper.py#L246-L251)).

#### langchain-ai/open_deep_research — the deployed graph never fetches a page

Backends are `ANTHROPIC | OPENAI | TAVILY | NONE`
([configuration.py:11-17](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/configuration.py#L11-L17));
`anthropic` maps to the **server-side** `{"type": "web_search_20250305", "max_uses": 5}`. There is no
`requests`/`httpx`/`playwright`/`firecrawl`/`jina` anywhere in the shipped package and **no hardcoded
User-Agent**. Raw page text arrives only as Tavily's `raw_content` — **Tavily does the crawling, and any fetch
failure is invisible, expressed as a missing field.**

Truncation `max_content_length` default **50,000 chars**, then `summarize_webpage()` with
`openai:gpt-4.1-mini`, `max_tokens=8192`, `asyncio.wait_for(..., 60.0)`; on timeout or error it logs a WARNING
and **returns the original content**
([utils.py:206-213](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/utils.py#L206-L213)).
Note `asyncio.gather(*search_tasks)` at
[utils.py:172](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/utils.py#L172)
lacks `return_exceptions=True`, so **one** Tavily failure collapses the whole multi-query batch to an error
string. MCP tool loading fails silently (`except Exception: return []`).

The unregistered `src/legacy/` package *does* scrape, including a Google SERP path with a **randomized fake
Lynx User-Agent**
([legacy/utils.py:953-960](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/legacy/utils.py#L953-L960)) —
noted as a real-world example of SERP scraping, which is ToS-prohibited (§2.6).

#### dzhng/deep-research — one Firecrawl call, no fallback

`firecrawl.search(query, { timeout: 15000, limit: 5, scrapeOptions: { formats: ['markdown'] } })`
([src/deep-research.ts:222-226](https://github.com/dzhng/deep-research/blob/1f8f3e285bbc23e80b98a66a64effab9069f3ad4/src/deep-research.ts#L222-L226)).
Search and scrape are one server-side call, so there is **no per-URL error surface at all**. Concurrency
`FIRECRAWL_CONCURRENCY || 2`; per-page trim to **25,000 tokens**. The `catch` at
[deep-research.ts:275-285](https://github.com/dzhng/deep-research/blob/1f8f3e285bbc23e80b98a66a64effab9069f3ad4/src/deep-research.ts#L275-L285)
returns `{ learnings: [], visitedUrls: [] }` — and because the recursive call and the LLM call sit inside the
same `try`, a failure silently contributes nothing and no note reaches the report. `lodash.compact` drops
scrape failures before they are ever counted.

#### jina-ai/node-DeepResearch — the best failure bookkeeping of the six

Reads via `axiosClient.post('https://r.jina.ai/', { url }, ...)` with `Authorization: Bearer ${JINA_API_KEY}`
([src/tools/read.ts:40-48](https://github.com/jina-ai/node-DeepResearch/blob/fd323b521a51264d497bec333bfb997da1bf3210/src/tools/read.ts#L40-L48));
**the key is mandatory** (`src/config.ts:130`). Five behaviors worth copying
([src/utils/url-tools.ts:507-644](https://github.com/jina-ai/node-DeepResearch/blob/fd323b521a51264d497bec333bfb997da1bf3210/src/utils/url-tools.ts#L507-L644)):

1. **Blocked-content detection** — content ≤300 chars is run through an LLM spam classifier; if flagged,
   `throw new Error("Blocked content ${url}")` rather than ingested. (Compare §1.2's text-ratio heuristic.)
2. **Per-URL record** — `catch { logError(...); badURLs.push(url) }`.
3. **Hostname-level blacklisting** — DNS/TLS/refused-connection errors push the *hostname* to `badHostnames`,
   and every URL on that host is then purged from the candidate pool.
4. **`finally { visitedURLs.push(url) }`** — a URL is marked visited whether or not it succeeded, so it is
   never retried.
5. **The agent is told it failed** — on `!success`, `src/agent.ts:958-973` writes into the diary:
   *"you took the visit action and try to visit some URLs but failed to read the content. You need to think
   out of the box or cut from a completely different angle."*
   Final output separates `readURLs = visitedURLs.filter(u => !badURLs.includes(u))`.

#### smolagents open_deep_research — hands the 403 body to the model, then Wayback

`SimpleTextBrowser._fetch_page` is plain `requests.get(url, stream=True)`
([scripts/text_web_browser.py:263-323](https://github.com/huggingface/smolagents/blob/30bb1161095dbae2271e6bc3cc4c219cc3897a57/examples/open_deep_research/scripts/text_web_browser.py#L263-L323)),
UA `Chrome/119 ... Edg/119`, `timeout: 300`, **no retries**. Non-`text/*` responses are downloaded to
`downloads_folder/` and re-opened as `file://` — so **PDF links work through `visit_page` transparently**
(the same pattern as Claude Code's WebFetch binary-save in §1.6).

Conversion is a vendored 1002-line `mdconvert.py` (from AutoGen/Magentic-One), **not** `markitdown`; PDFs use
**pdfminer** (`pdfminer.high_level.extract_text`). Format detection is a **best-effort cascade**: candidate
extensions accumulated from `Content-Type`, `Content-Disposition`, URL path and `puremagic` byte-sniffing,
then every converter tried against every candidate before raising.

Large pages are **paginated, not truncated**: `viewport_size = 1024 * 5` (5,120 chars), `_split_pages` slices
on whitespace boundaries, the model sees `"Viewport position: Showing page N of M."` and gets `page_up`,
`page_down`, `find_on_page_ctrl_f`, `find_next`, `find_archived_url`.

On 403 the error page **becomes the content**
([text_web_browser.py:335-353](https://github.com/huggingface/smolagents/blob/30bb1161095dbae2271e6bc3cc4c219cc3897a57/examples/open_deep_research/scripts/text_web_browser.py#L335-L353)):
the page title is set to `Error 403` and the body to the rendered block page, returned verbatim to the LLM.
Nothing is dropped or retried — **the model decides**, typically by calling `find_archived_url`, which queries
`https://archive.org/wayback/available?url=...` and raises
`"Your url= was not archived on Wayback Machine, try a different url."` when there is no snapshot
([:445-484](https://github.com/huggingface/smolagents/blob/30bb1161095dbae2271e6bc3cc4c219cc3897a57/examples/open_deep_research/scripts/text_web_browser.py#L445-L484)).
This is the closest thing to a real fallback chain in any of the six, and it is the design this survey
recommends adapting.

Caveat: the example ships a checked-in 715-line `cookies.py` of Google/YouTube session cookies attached to
every request — noted as fact; not a pattern to copy.

The core library's `VisitWebpageTool`
([src/smolagents/default_tools.py:491-544](https://github.com/huggingface/smolagents/blob/30bb1161095dbae2271e6bc3cc4c219cc3897a57/src/smolagents/default_tools.py#L491-L544))
is far simpler and **not** used here: `requests.get(url, timeout=20)` → `markdownify` → truncate at 40,000
chars, returns `"Error fetching the webpage: {e}"` as a string, **no User-Agent at all**.

#### stanford-oval/storm — trafilatura behind Bing/Google only

Of 11 retrievers in [`knowledge_storm/rm.py`](https://github.com/stanford-oval/storm/blob/fb951af7744dab086e34962e9bc6fe878e145f83/knowledge_storm/rm.py),
**only three** ever fetch a page: `BingSearch` (:167), `SerperRM` (:537, gated behind
`ENABLE_EXTRA_SNIPPET_EXTRACTION`, default `False`), and `GoogleSearch` (:1096). The rest —
DuckDuckGo, Brave, SearXNG, Tavily, You.com, Azure — are **snippet-only**. Google explicitly discards its own
snippets: `# "snippet": ...  # Google search snippet is very short.` (rm.py:1085).

The fetcher, `WebPageHelper`
([knowledge_storm/utils.py:633-711](https://github.com/stanford-oval/storm/blob/fb951af7744dab086e34962e9bc6fe878e145f83/knowledge_storm/utils.py#L633-L711)):

```python
self.httpx_client = httpx.Client(verify=False)   # TLS verification DISABLED
...
res = self.httpx_client.get(url, timeout=4)
```

**4-second timeout, no retries, `follow_redirects` left at httpx's default `False`, no User-Agent anywhere in
the repo** (fetches identify as `python-httpx/<version>`). Extraction is
`trafilatura.extract(h, include_tables=False, include_comments=False, output_format="txt")`, then
`if article_text is not None and len(article_text) > min_char_count` — with **no `else` branch**, so failures
are dropped with no log at all. Defaults `min_char_count=150`, `snippet_chunk_size=1000`, `max_thread_num=10`.
Download errors go to `print()`, not `logging`.

Latent bugs found while reading (relevant to "does it actually fetch"): `DuckDuckGoSearchRM` and
`TavilySearchRM` construct a `WebPageHelper` and **never call it**; `TavilySearchRM` builds an `args` dict with
a misspelled `include_raw_contents` and then calls `search(query)` without passing it, so raw content is always
empty; `SerperRM` attaches extra snippets using a leaked loop variable.

**Takeaway for a keyless skill:** storm's fetch layer is one keyless idea worth lifting — `trafilatura.extract`
plus a `min_char_count` floor — and several worth avoiding: `verify=False`, no redirects, no UA, 4s timeout,
silent drops.

### 2.1 Headless browsers, MCP servers, and anti-detection projects

Star counts and versions from the GitHub API on 2026-09-02.

#### Headless / MCP — keyless, but each needs a browser

| Project | Stars | License | Key? | Install weight | Solves | Does not solve |
|---|---|---|---|---|---|---|
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 36.7k | Apache-2.0 | **none** | npm pkg tiny (86 KB) but needs a browser: `playwright@1.56.0` has **no postinstall**, so `npx @playwright/mcp install-browser` is an explicit step (or use system Chrome via `--browser chrome`) | JS rendering, consent clicks, forms, tabs, network capture | no stealth layer at all, no CAPTCHA, no proxy rotation |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 50.4k | Apache-2.0 | **none** | **lightest browser option**: 13.2 MB unpacked, zero runtime deps, **uses your installed Chrome** (no browser download) | ~57 tools: JS rendering, console, network, Lighthouse, tracing, heap | no stealth, no CAPTCHA; **telemetry on by default** (`--no-usage-statistics`); fails inside OS sandboxes |
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | 41.7k | Apache-2.0 | none for automation | `npm i -g agent-browser` + `agent-browser install` (Chrome for Testing), but detects existing Chrome/Brave/Playwright/Puppeteer | Rust CLI + MCP; **`read [url]` fetches without launching Chrome** — sends `Accept: text/markdown`, retries with `.md` appended, walks ancestors for `llms.txt`, falls back to readable text | stealth and CAPTCHA are third-party plugins it does not ship |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 112.0k | MIT | **LLM key required** (or a local model) | Chrome + heavy memory | full agentic browsing | maintainers say CAPTCHA/stealth/proxy rotation are **Cloud** features |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 24.1k | MIT | **LLM key required** for `act`/`observe`/`extract`; Browserbase key optional | local Chrome or hosted | accessibility-tree trimming, self-healing actions | OSS SDK ships no anti-detection/CAPTCHA/proxy layer |
| [puppeteer](https://github.com/puppeteer/puppeteer) / [playwright](https://github.com/microsoft/playwright) direct | 95.5k / 95.5k | Apache-2.0 | none | puppeteer **has** a postinstall Chrome download (often blocked by modern package managers → `npx puppeteer browsers install`); playwright does not | full control, deterministic | **zero anti-detection** — vanilla CDP Chromium leaks `navigator.webdriver`; every project below exists because of this |

**Correction worth recording:** `vercel/agent-browser` **404s**. The real repo is `vercel-labs/agent-browser`.

**The important nuance for a keyless skill:** two of these — `chrome-devtools-mcp` and `agent-browser` — reuse a
Chrome you already have rather than downloading one, which makes step 7 of the recommended chain (§4.1) far
cheaper than "install Playwright" suggests. `agent-browser read <url>` is also notable as a *non-browser*
markdown fetch path with `llms.txt` discovery built in.

**What headless browsers solve:** JS rendering (§1.2), cookie/consent interstitials (§1.4), forms, and
client-side pagination. **What they do not solve:** Cloudflare managed challenges/Turnstile, CAPTCHAs, or
login walls. Every project's answer to a login wall is *reuse credentials you already have* — a persistent
profile, a `storage-state` JSON, or a CDP connection to your own signed-in Chrome. `chrome-devtools-mcp` says
this outright: *"Some accounts may prevent sign-in when the browser is controlled via WebDriver"*, and the
documented remedy is to attach to your own Chrome.

#### Anti-detection projects — described factually, excluded from the recommended chain

> These sit in a **legal/ToS grey area**: circumventing bot mitigation frequently violates a site's Terms of
> Service and may, depending on jurisdiction, implicate anti-circumvention or computer-misuse law. Listed here
> as prior art for completeness. **They are deliberately not part of the recommendation in §4**, and this
> document gives no operational guidance for using them against CAPTCHAs, paywalls, or login walls.

| Project | Stars | License | Claim (their words) | Install |
|---|---|---|---|---|
| [nodriver](https://github.com/ultrafunkamsterdam/nodriver) | 4.7k | **AGPL-3.0** | *"the official successor of the Undetected-Chromedriver package… No more webdriver, no more selenium"*; direct CDP gives *"better resistance against web application firewalls"* | `pip install nodriver` + a system Chrome |
| [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) | 12.8k | GPL-3.0 | *"does not trigger anti-bot services like Distill Network / Imperva / DataDome"*, PyPI adds *"No guarantees are given"* | `pip install`, auto-downloads chromedriver |
| [camoufox](https://github.com/daijro/camoufox) | 11.6k | MPL-2.0 (wrapper MIT) | Firefox fork; *"data is intercepted at the C++ implementation level, making the changes undetectable through JavaScript inspection"* | **heavy**: 313–663 MB browser download per platform |
| [Scrapling](https://github.com/D4Vinci/Scrapling) | 77.8k | BSD-3 | `StealthyFetcher` claims it *"easily bypasses all types of Cloudflare's Turnstile/Interstitial automatically"* | `pip install "scrapling[fetchers]"` + `scrapling install` |
| [curl_cffi](https://github.com/lexiforest/curl_cffi) | 6.4k | MIT | *"can impersonate browsers' TLS/JA3 and HTTP/2 fingerprints"*; its CLI is pitched as *"a `web_fetch` replacement for 'agents'"* | **lightest here** — pre-compiled wheels, no browser, no key |
| [crawl4ai](https://github.com/unclecode/crawl4ai) | 80.9k | Apache-2.0 + attribution | *"Deploy anywhere, zero keys"*; LLM-free `JsonCssExtractionStrategy` + "Fit Markdown"; 0.7.x adds `browser_type="undetected"` | `pip install -U crawl4ai` + `crawl4ai-setup` (Chromium) |
| [firecrawl](https://github.com/firecrawl/firecrawl) (org renamed from `mendableai`) | 175.3k | **AGPL-3.0** | cloud *"covers 96% of the web"* | self-host = Docker + Playwright + Redis + Postgres + RabbitMQ |
| [crawlee](https://github.com/apify/crawlee) | 25.6k | Apache-2.0 | *"crawlers will appear human-like… even with the default configuration"* — browser-like headers, TLS fingerprint replication | `npm install crawlee playwright`; Playwright deliberately not bundled |

Three findings from this group matter to the recommendation:

1. **Self-hosted Firecrawl is not the cloud product.** The self-host guide states plainly: *"Fire-engine or
   its advanced anti-bot behavior… it is not included"*, and screenshots/actions *"require Fire-engine"*.
   Self-hosted baseline is *"bundled Playwright with basic fetch fallback"*. Authentication can be disabled
   (`USE_DB_AUTHENTICATION=false`) so it runs keyless — but you get Playwright, not the 96% number.
   Firecrawl is also the only project here with a clear ToS stance: *"It is the sole responsibility of end
   users to respect websites' policies when scraping… **By default, Firecrawl respects robots.txt
   directives.**"* [https://docs.firecrawl.dev/contributing/self-host]
2. **IP reputation dominates everything else**, stated most bluntly by undetected-chromedriver's own README:
   *"THIS PACKAGE DOES NOT, and i repeat DOES NOT hide your IP address, so when running from a datacenter
   (even smaller ones), chances are large you will not pass!"* Camoufox concurs that it *"is intended to be
   used with rotating proxies (preferably residential IPs)"*. A local keyless skill runs from one residential
   IP, which is actually the *favorable* case — but it also means no amount of client-side technique moves the
   needle once that IP is flagged.
3. **Every "bypasses X" claim is a snapshot, not a property.** Camoufox: *"Anti-bot providers test Camoufox
   over and over again to find even 1 unique inconsistency, then they immediately update their background
   scripts."* Stale projects decay fastest — undetected-chromedriver's last PyPI release is **3.5.5,
   2024-02-17**, ~2.5 years stale with 1,141 open issues, though the repo is **not** formally archived.

**Consequence for this project:** a skill built on any of these inherits a maintenance treadmill and a ToS
exposure it cannot discharge. The chain in §4 deliberately stops at "record UNFETCHABLE" instead.

### 2.2 Reader / proxy services that work without a key

All probed live on 2026-09-02.

| Service | Status today | Keyless limit | JS render? | Output | License / ToS |
|---|---|---|---|---|---|
| **`r.jina.ai`** | **200 OK** | **20 RPM** — header-confirmed | **Yes** (headless Chrome) | markdown / html / text / json / screenshot | Apache-2.0 code (`ghcr.io/jina-ai/reader:oss`); anon traffic "most aggressively rate-limited" |
| **urltomarkdown** | **200 OK** | none documented | No | markdown | MIT; one person's free dyno — best-effort |
| **Microlink** (`api.microlink.io`) | **200 OK** | daily per-IP quota | Yes | **metadata JSON only**, not article body | free tier |
| **Markdowner** (`md.dhr.wtf`) | **HTTP 500 on every conversion** | keyless | No | markdown | **broken today — do not depend on it** |
| **Mercury / Postlight Parser** | **DNS failure** — `mercury.postlight.com` and `reader.postlight.com` no longer resolve | — | — | — | **defunct as a hosted service**; the npm library still exists |
| **textance** | **404** | — | — | — | **dead** |

#### Jina Reader in detail — the strongest keyless rung

**[probe]** `curl https://r.jina.ai/https://example.com` with no key returned:

```
HTTP/2 200
content-type: text/plain; charset=utf-8
x-usage-tokens: 29
x-ratelimit-limit: 20, 20;w=60
x-ratelimit-remaining: 19
server: cloudflare
```

`x-ratelimit-limit: 20, 20;w=60` is **direct primary-source confirmation of 20 requests per 60 seconds
without a key**, and `x-ratelimit-remaining` decremented across repeated calls. The published tiers are
20 RPM keyless / 500 RPM with a free key / 5,000 RPM premium; `s.jina.ai` (search) is **blocked entirely**
without a key. Every new key carries **10M free tokens**. [https://jina.ai/reader/]

*Relevant to a "no paid keys" project: the free key costs nothing but a signup and buys a 25x rate increase.
Worth supporting as an optional env-var upgrade rather than assuming it.*

**JS rendering confirmed three ways [probe]:**

| Target | Result |
|---|---|
| `quotes.toscrape.com/js/` (quotes injected by JS) | quotes returned as clean rendered prose |
| `vercel.com/blog` | **17,773 B** of markdown vs only 4,119 chars of visible text from raw `curl` |
| `x.com/anthropicai` | 3,030 B of real profile content where raw `curl` yields an empty SPA shell |
| `www.reuters.com` | **403** `{"code":403,"name":"AbuseAlleviationError","status":40305,"message":"Anonymous access to domain www.reuters.com blocked until ... due to previous abuse found on ..."}` |
| 6 rapid sequential requests | all 200, ~1.1 s each |

The default engine runs the page in headless Chrome so client-side JS executes before extraction; `x-engine`
selects `browser` / `curl` / `auto`. PDFs are natively supported. Useful headers: `x-respond-with`,
`x-no-cache`, `x-timeout`, `x-target-selector`, `x-max-tokens`. [https://github.com/jina-ai/reader]

**Three consequences for the chain in §4:**

1. **Jina largely substitutes for a headless browser** on the JS-rendering failure mode (§1.2) at zero install
   cost. This is why it sits above "headless browser" in the recommended order.
2. **It serves cached content by default and says so** — the example.com response carried
   `Warning: This is a cached snapshot of the original page, consider retry with caching opt-out.` That is
   **not a live read**; record it as `snapshot_date`, or send `x-no-cache: true` when freshness matters.
3. **`AbuseAlleviationError` is a per-domain, anonymous-tier block caused by other users' behavior.** It will
   not clear on retry — advance the chain immediately.

**Watch item:** Elastic acquired commercial licensing rights to Jina AI on **2026-08-10** — the most likely
trigger for future changes to the keyless tier. Mitigation: the reader is self-hostable under Apache-2.0.

**Also worth knowing:** `agent-browser read <url>` is a keyless markdown fetch that does **not** launch Chrome —
it sends `Accept: text/markdown`, retries the URL with `.md` appended, walks ancestor paths for the nearest
`llms.txt`, then falls back to readable-text extraction. [https://github.com/vercel-labs/agent-browser]
Relatedly, the **`llms.txt` / `.md`-sibling convention** is the cheapest possible win on any docs domain —
Claude Code's own docs advertise `https://code.claude.com/docs/llms.txt` in every fetched page.


### 2.3 Archive copies

| Endpoint | Keyless? | **[probe]** 2026-09-02 | Use |
|---|---|---|---|
| `https://archive.org/wayback/available?url=<u>` | yes | 200 JSON | Convenience existence check — **but flakier than CDX** |
| `http://web.archive.org/cdx/search/cdx?url=<u>&output=json` | yes | 200 JSON | **The authority.** Full capture history, exact-match by default |
| `https://web.archive.org/web/<ts>id_/<url>` | yes | 200, pristine original HTML | **Raw archived bytes** — no Wayback toolbar/banner injected |
| `https://index.commoncrawl.org/CC-MAIN-2026-34-index?url=<u>&output=json` + WARC `Range:` fetch | yes | 200 / 206 | **Fully working keyless full-text fallback** (see below) |
| `https://archive.today` / `.ph` / `.is` | nominally | **429 + CAPTCHA** | **Exclude from automated chains** |
| `https://webcache.googleusercontent.com/search?q=cache:<u>` | n/a | **200 → ordinary Google SERP** | **Retired Feb 2024** |
| `https://cc.bingj.com/cache.aspx?...` | n/a | **400**; zero `cc.bingj.com` links in a live Bing SERP | **Retired 2024-12-11** |

**Both major search-engine caches are dead.** Google removed cache links in **February 2024** — Search Liaison
Danny Sullivan called it "one of our oldest features… meant for helping people access pages when way back, you
often couldn't depend on a page loading", and the `cache:` operator itself stopped working by September 2024
[https://searchengineland.com/google-search-officially-retires-cache-link-437122]. Microsoft followed on
**2024-12-11** [https://searchengineland.com/bing-officially-removes-cache-link-from-search-results-449220].
**The Wayback Machine and Common Crawl are the only remaining keyless archive fallbacks.**

#### The `id_` modifier matters

**[probe]** `https://web.archive.org/web/2020id_/https://example.com` → 200, resolved to
`.../20210101000012id_/http://example.com/`, **1,256 bytes of pristine original HTML with no toolbar
injection**. Without `id_`, Wayback rewrites URLs and injects its own banner JS/CSS, which pollutes
extraction. A partial timestamp (`2020`) is accepted and resolves to the nearest capture.

#### Wayback rate limits — no warning before the ban

Community-documented (the official API page states no limit at all — **not officially confirmed**):
~**60 requests/minute**; exceeding it returns **429**; ignoring 429s for over a minute triggers a
**firewall-level IP block for 1 hour, doubling on each repeat offense**. Save Page Now is separately capped at
15 URLs/min. [https://cirosantilli.com/wayback-machine-rate-limit],
[https://github.com/edgi-govdata-archiving/wayback/issues/137]

**[probe]** 12 consecutive availability calls and 8 consecutive CDX calls all returned 200, and **no
`x-ratelimit-*` or `Retry-After` headers are emitted at all**. You get **no advance warning** before the ban —
self-throttle to under ~1 req/sec.

Also **[probe]:** during heavy use the *availability* API intermittently returned empty results for URLs that
CDX confirmed had hundreds of captures, then recovered. **Prefer CDX as the authority; treat an availability
miss as soft evidence only.**

#### Common Crawl — a working keyless full-text fallback

**[probe]** `index.commoncrawl.org/collinfo.json` → 200, **127 collections**, newest `CC-MAIN-2026-34`
(August 2026). Querying `CC-MAIN-2026-34-index?url=example.com&output=json` returns records carrying
`filename`, `offset` and `length`; issuing an HTTP **`Range: bytes=<offset>-<offset+length>`** request against
`https://data.commoncrawl.org/<filename>` returned **HTTP 206**, which gunzips to the full original WARC
response including the HTML. Entirely keyless, no rate-limit error encountered. Coverage fallback, not a
freshness one — the newest index was ~1 month stale.

#### archive.today — hostile to agents, exclude it

**[probe]** `archive.ph/newest/...`, `archive.is/...` and both Memento TimeMap endpoints returned **429** with
a CAPTCHA interstitial: *"One more step. Please complete the security check… Completing the CAPTCHA proves you
are a human."* Memento (TimeMap/TimeGate) is the only official API and it is 429-gated too. Compounding this,
archive.today has been largely unresolvable from Cloudflare's 1.1.1.1 since 2018 (its nameservers return
invalid responses to resolvers that omit EDNS Client Subnet), and in 2026 Cloudflare additionally flagged it on
1.1.1.2. [https://kiledjian.com/2025/10/15/archivetoday-inside-the-web-archiving.html]

#### Distinguishing a fabricated URL from a dead or blocked one

This is the check that matters most for a research skill, and **[probe] the live HTTP status code cannot do
it.** Same domain, same path prefix, one real and one fabricated:

| URL | Live | Wayback CDX captures |
|---|---|---|
| `nytimes.com/2023/03/14/technology/openai-gpt4-chatgpt.html` (real, paywalled) | **403** | **438** |
| `nytimes.com/2023/03/14/technology/qzx-fake-article-9182.html` (fabricated) | **403** | **0** (`[]`) |

Both return 403. **Only the archive lookup separates them.** Full matrix **[probe]**:

| Class | Example | Live | CDX captures | CC 2026-34 |
|---|---|---|---|---|
| Real + live | `arxiv.org/abs/1706.03762` | 200 | 200+ | 3 hits |
| Real, moved | `blog.golang.org/gos-declaration-syntax` | 200 | 200+ | 0 |
| Real, dead (soft-404 redirect) | `blog.golang.org/go1.11` | **200** | 80 | 0 |
| Real, paywalled | `nytimes.com/.../openai-gpt4-chatgpt.html` | 403 | **438** | 0 |
| Real, bot-blocked | `wsj.com/tech/ai`, `reuters.com/technology/` | 401 | **5000+** | 0 |
| **Fabricated leaf, real domain** | `nytimes.com/.../qzx-fake-9182.html` | 403 | **0** | 0 |
| **Fabricated arXiv id** | `arxiv.org/abs/2410.99999` | 404 | **0** | 0 |
| **Fabricated plausible path** | `openai.com/research/gpt-9-technical-report-2027` | 403 | **0** | 0 |
| **Fabricated domain** | `nonexistent-domain-qzx9182.com/paper` | **000** (NXDOMAIN) | 0 | 0 |

**The decision procedure:**

1. **DNS resolution fails (`curl` exit 6 / code 000)** → the *domain* is fabricated. Strongest signal, and free.
   Check it first.
2. **Resolves and returns 2xx** → real and live. (But check for a soft-404: compare the final URL and content
   length, not just the status — `blog.golang.org/go1.11` returns 200 by redirecting to a generic page.)
3. **Resolves and returns 401/403/404/410** → **ambiguous. Conclude nothing yet.**
4. **Query CDX** (`?url=<exact url>&output=json&limit=1&fl=timestamp,statuscode`):
   - **≥1 capture with a 2xx status** → the URL is **REAL** — dead, moved, paywalled, or bot-blocked. Retrieve
     via `web/<ts>id_/<url>` and cite the archived copy with its snapshot date.
   - **`[]`** → **probably fabricated.**
5. **Corroborate before declaring a hallucination:** query the Common Crawl index for the same URL, and run a
   *prefix* CDX query (`matchType=prefix`) on the parent path. Parent has captures, exact URL has none → strong
   evidence of a **fabricated leaf on a real site**.

**Caveats that must be encoded, or you will produce false hallucination verdicts:**

- **Zero CDX captures ≠ proof of fabrication.** Real-but-obscure, very recent, `robots.txt`-excluded, or
  retroactively-excluded pages legitimately have zero captures — Wayback honors exclusion requests, which can
  *remove* captures of a page that genuinely existed.
- The availability API returns **HTTP 200 with `{"archived_snapshots": {}}`** on a miss. **Parse the body.**
- Verify the **exact** URL, not a normalized one — CDX matches exactly by default, which is precisely what
  makes it a good fabrication detector.
### 2.4 Request hygiene — what actually helps, measured

| Tactic | Verdict **[probe]** |
|---|---|
| Browser-like `User-Agent` + `Accept-Language` + `Accept` | **Cheap, do it.** Fixes naive-UA 403s; changed nothing on Reuters (401→401) or G2/DataDome (403→403). Not a bypass. |
| `HEAD` before `GET` | **Genuinely useful.** Returned `ct=application/pdf` for `arxiv.org/pdf/...` (route to a PDF extractor, skip HTML parsing) and `403` for `g2.com` **before** downloading a 300 KB block page. Low-cost triage. |
| Retry with exponential backoff | Correct for `429`/`5xx`/timeouts. **Wrong for `403`, robots refusals, and consent walls** — those are deterministic; retrying burns budget and looks like abuse. Gate retries on status class. |
| Follow `rel="canonical"` | Worth doing; **[probe]** `theguardian.com/technology` canonicalizes to `/uk/technology`. Prevents duplicate/variant registry entries. |
| **AMP variants** | **Effectively dead — do not build on it.** `rel="amphtml"` found on **0 of 6** major news sites probed (Verge, Ars Technica, BBC News, TechCrunch, Wired, CNN); `bbc.com/news/amp` → 404. |
| `?print=1` / reader-mode variants | Site-specific, no general convention. Low yield. **unverified** as a general tactic. |
| **RSS/Atom alternatives** | **High yield and underused.** `rel="alternate" application/rss+xml` present on 3/6 probed news sites; `news.ycombinator.com/rss`, `openai.com/news/rss.xml`, `blog.cloudflare.com/rss/`, `simonwillison.net/atom/everything/` all returned **200** with clean XML. Feeds bypass HTML boilerplate, JS rendering, and often the consent layer entirely. |
| Site/domain-specific keyless APIs | **Highest yield of all for research.** See below. |

#### Keyless structured APIs that replace scraping outright **[probe]**

| API | Status | Notes |
|---|---|---|
| `api.crossref.org/works/<doi>` | 200 | Full metadata. Polite pool: send a `User-Agent` with a `mailto:`. |
| `api.openalex.org/works/doi:<doi>` | 200 | Metadata, OA locations, citations. Keyless. |
| `export.arxiv.org/api/query?id_list=<id>` | 200 (use **https**; http → 301) | Title/abstract without touching the PDF. |
| `ar5iv.labs.arxiv.org/html/<id>` | 200 | **HTML rendering of an arXiv paper** — avoids PDF extraction entirely. |
| `arxiv.org/abs/<id>` | 200 | Plain HTML, no bot wall. |
| `en.wikipedia.org/api/rest_v1/page/summary/<title>` | 200 | Keyless. |
| `api.github.com` | 200 but **60 req/hr unauthenticated** | Claude Code's own tool description says prefer the `gh` CLI for GitHub URLs (authenticated, 5,000/hr). |
| `api.semanticscholar.org/graph/v1/...` | **429 on burst** | Keyless tier exists but is aggressively rate-limited. |
| `api.unpaywall.org/v2/<doi>?email=<e>` | 422 on the DOI probed | Requires a real `email` param; **unverified** working shape. |

**Design point:** for a *research* skill, the ordering "is there a structured keyless API for this resource?"
should come **before** "how do I scrape the HTML?" A DOI, an arXiv ID, a GitHub repo, or a Wikipedia title
each has a keyless, robots-clean, JSON path that no anti-bot system touches.

#### A note on robots.txt and raw scripts

**[probe]** `https://www.nytimes.com/` returns **HTTP 200 with 8,359 characters of real article text** to a
plain `curl` with a browser UA — while Claude Code's WebFetch refuses it, because WebFetch identifies as
`Claude-User`, which NYT's robots.txt disallows.

A script-based fallback therefore *works where the harness tool refuses*, but only because `curl` does not
consult robots.txt. **This is a policy decision the skill must make explicitly, not a bug to route around.**
Recommendation: the skill should read and honor `robots.txt` for its own scripted fetches by default, record
`robots: disallowed` in the registry, and require an explicit user opt-in to do otherwise. Anthropic publishes
per-bot robots semantics precisely so operators can express this preference
[https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler].

### 2.5 Content extraction

All keyless and local. Versions and licenses verified against the PyPI JSON API on 2026-09-02.

| Package | Version | License | Notes |
|---|---|---|---|
| `trafilatura` | 2.2.0 | Apache-2.0 | Best measured F1 (§3.1) |
| `resiliparse` | 1.0.9 | Apache-2.0 | **0.3x runtime** — 3x faster than baseline, F1 0.811. Pick when throughput dominates |
| `readability-lxml` | 0.9 | Apache-2.0 | The classic; measurably lower recall |
| `readabilipy` | 0.3.0 | MIT | Wraps Readability.js (needs Node ≥14) **but ships a pure-Python fallback** (`use_readability=False`) |
| `justext` | 3.0.2 | BSD-2 | F1 0.862 |
| `goose3` | 3.1.22 | Apache | Precision leader (0.936), weak recall |
| `newspaper4k` | 0.9.6 | MIT | |
| `markdownify` | 1.2.3 | MIT | HTML→markdown only, no boilerplate removal |
| `html2text` | 2025.4.15 | **GPL-3.0** | **F1 0.663 — below the "raw HTML, no extraction" floor of 0.667.** Do not use for article extraction |
| `pypdf` | 6.16.2 | BSD-3 | **Pure Python, zero native deps — safest keyless PDF default** |
| `pdfminer.six` | 20260107 | MIT | Pure Python, best layout analysis of the pure set |
| `pdftotext` (poppler) | system pkg | GPL-2 | Fastest and robust; **present on this machine by default [probe]**; not pip-installable |
| `pymupdf4llm` | 1.28.2 | **AGPL-3.0 or Artifex commercial** | Best markdown structure (tables → GFM, reading order). **License is the catch** |
| `markitdown` | 0.1.7 | MIT | Its `pdf` extra is `pdfminer.six + pdfplumber` — **pure Python, no key**. Avoid the `az-doc-intel`, `llm_client`, and transcription extras, which call external services |
| `defuddle` (kepano) | npm | MIT | `npx defuddle parse`; needs linkedom/JSDOM in Node. Makes no benchmark claims. **Caveat:** falls back to the third-party FxTwitter API for X/Twitter, so not fully offline on that path |
| `mozilla/readability` | npm | MPL-2.0 | Reference JS implementation; F1 0.947 on the ScrapingHub set |

**Recommended keyless PDF order:** `pdftotext` if present → `pypdf` → `pdfminer.six` → `markitdown[pdf]` for
markdown structure. Reach for `pymupdf4llm` only if AGPL is acceptable.

**The pattern worth copying from smolagents** (§2.0) is not any single extractor but its **best-effort
cascade**: accumulate candidate file types from `Content-Type`, `Content-Disposition`, the URL path, **and**
`puremagic` byte-sniffing, then try every converter against every candidate before giving up. A single
`Content-Type` guess is the common failure — `text/html` on a 404, `application/octet-stream` on a real PDF.

### 2.6 Search-side fallbacks

#### DuckDuckGo HTML/Lite — CAPTCHA-walled, and the status code lies

**[probe]** All three variants, with a realistic browser User-Agent:

```
POST https://html.duckduckgo.com/html/  (q=trafilatura)  -> HTTP 202, 14,208 bytes
GET  https://html.duckduckgo.com/html/?q=trafilatura     -> HTTP 202, 14,208 bytes
POST https://lite.duckduckgo.com/lite/  (q=trafilatura)  -> HTTP 202, 14,189 bytes
```

**Zero result links in any response.** The body is an image CAPTCHA:
`<div class="anomaly-modal__title">Unfortunately, bots use DuckDuckGo too.</div>` … *"Select all squares
containing a duck"*, with a form posting to `//duckduckgo.com/anomaly.js`.

**This is the mechanism behind the well-known `duckduckgo_search` / `ddgs` `RatelimitException: 202 Ratelimit`.**
The library is misreporting a CAPTCHA wall as a rate limit. It is **HTTP 202 with a challenge body, not 429** —
so **backoff and retry cannot fix it**; there is nothing to back off from. Reported across many projects
([ddgs#272](https://github.com/deedy5/ddgs/issues/272),
[open-webui#13947](https://github.com/open-webui/open-webui/discussions/13947),
[crewAI#136](https://github.com/crewAIInc/crewAI/issues/136),
[MetaGPT#1567](https://github.com/FoundationAgents/MetaGPT/issues/1567)); a fix shipped in `duckduckgo_search`
6.3.0 and the problem recurred by 6.3.7.

**Verdict:** unusable for agents from this IP as of 2026-09-02; may still work from some residential IPs.
Never build a chain that assumes it works, and treat a 202 as a **hard** failure that fails over immediately.

#### SearXNG — the only defensible keyless search, but self-hosted only

- **JSON output is off by default.** Stock `settings.yml` sets `search.formats` to HTML only, so `?format=json`
  returns **403**. You must add `json` under `search: formats:`, ensure no volume is mounted over
  `/etc/searxng`, and restart. [https://docs.searxng.org/dev/search_api.html],
  [https://github.com/searxng/searxng/issues/2505]
- **[probe] Public instances do not work either**, and one of them fails silently:
  `https://searx.be/search?q=trafilatura&format=json` → **HTTP 200 with `content-type: text/html`** and
  `<title>Verifying your browser…</title>`; `priv.au` → **429**; `search.bus-hit.me` → DNS failure.
  An agent checking only the status code would treat a CAPTCHA page as a successful search.
- Self-hosted it is genuinely keyless and returns clean JSON, but it is a service to run — which breaks the
  zero-install property. Offer it as an optional configured endpoint, never a default.

#### Google / Brave keyless scraping — prohibited, and now litigated

Google's ToS prohibit accessing the Services "through the use of any automated means (such as robots, spiders
or scrapers)", and `google.com/robots.txt` disallows `/search`. [https://policies.google.com/terms]
**In 2026 Google sued SerpApi** over scraping search results, alleging ToS violations and the use of proxies to
conceal identity — which raises the risk profile for third-party SERP APIs, not just direct scraping.
[https://www.seroundtable.com/google-sues-serpapi-40631.html]

Real projects do it anyway — `open_deep_research`'s legacy package generates a **randomized fake Lynx
User-Agent** for exactly this
([legacy/utils.py:953-960](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/legacy/utils.py#L953-L960)) —
noted as prior art, **not recommended**.

#### Query reformulation — the cheapest and most effective search-side fallback

This is what the surveyed agents actually rely on. node-DeepResearch makes it explicit: on a read failure it
writes into the agent's diary *"You need to think out of the box or cut from a completely different angle"*
(§2.0). Practical forms: drop rare terms; swap jargon for plain language; add `site:` to reach a domain that
*is* fetchable; and **search for the title of an unfetchable page** to find a mirror, a syndication, or a
discussion of it.

#### Using the search snippet as evidence

storm is the honest precedent: **8 of its 11 retrievers are snippet-only** and never fetch a page (§2.0), and
open_deep_research's shipped graph never fetches either. Snippet-only research is not a degraded mode — it is
the *modal* design in this field. The failure is not using snippets; it is **not labelling them**.

The literature is consistent that snippets are insufficient as verification evidence, though no single headline
number exists — it is a qualitative consensus. SURE-RAG frames evidence *sufficiency* as a task distinct from
relevance, requiring a supports/refutes/insufficient classification [https://arxiv.org/pdf/2605.03534];
noisy retrieval measurably degrades factual correctness [https://arxiv.org/pdf/2512.05012]; and the standard
mitigation is **escalation from snippet to full text**, as in DeepSciVerify's "LLM-driven evidence escalation"
[https://arxiv.org/pdf/2605.27710].

Claude Code's `WebSearch` compounds the problem by returning a model-written paraphrase rather than a verbatim
snippet (§1.9). So snippet-derived claims are `evidence_strength: paraphrase-only` and `quote_safe: false`
(§4.3): **a pointer, never a citation.**
### 2.7 Emerging: cryptographic bot identity (watch, don't build on yet)

**Web Bot Auth** layers on RFC 9421 HTTP Message Signatures so an agent proves its identity with a signature
rather than a spoofable UA/IP. The protocol draft `draft-meunier-webbotauth-httpsig-protocol-02` is dated
**2026-08-18** and is still an *individual* Internet-Draft, though an IETF working group is chartered and
Cloudflare, AWS WAF, Akamai and Vercel reportedly honor it in production, with OpenAI and Anthropic signing
traffic. [https://datatracker.ietf.org/doc/html/draft-meunier-web-bot-auth-architecture]
This is the medium-term fix for the whole taxonomy above — allowlisting by verified identity rather than
blocking by heuristic — but it is **not something a keyless local skill can use today**. Marked **unverified**
as to which of those vendors currently enforce it.


---

## 3. Measured reliability

Published numbers in this space are scarce, vendor-produced, or both. What exists:

### 3.1 Boilerplate extractor comparison — the best-documented numbers in this survey

Trafilatura's own evaluation, run **2026-08-04** on **990 documents** with **2,951 text and 2,966 boilerplate
segments** under Python 3.13 [https://trafilatura.readthedocs.io/en/latest/evaluation.html]:

| Tool | Precision | Recall | Accuracy | **F1** | Time (rel.) |
|---|---|---|---|---|---|
| html2text 2025.4.15 | 0.525 | 0.900 | 0.544 | **0.663** | 2.8x |
| *Raw HTML, no extraction (floor)* | 0.528 | 0.906 | 0.549 | *0.667* | 0.03x |
| beautifulsoup4 4.15.0 | 0.532 | 0.980 | 0.561 | 0.690 | 2.1x |
| inscriptis 2.7.4 | 0.534 | **0.991** | 0.564 | 0.694 | 1.1x |
| newspaper4k 0.9.6 | 0.878 | 0.736 | 0.817 | 0.801 | 6.6x |
| boilerpy3 1.0.7 | 0.818 | 0.796 | 0.810 | 0.807 | 1.6x |
| goose3 3.1.22 | **0.936** | 0.714 | 0.833 | 0.810 | 10.2x |
| resiliparse 1.0.9 | 0.705 | 0.955 | 0.778 | 0.811 | **0.3x** |
| readability-lxml 0.8.4.1 | 0.898 | 0.764 | 0.839 | 0.826 | 2.6x |
| news-please 1.6.16 | 0.932 | 0.758 | 0.852 | 0.836 | 20.5x |
| justext 3.0.2 | 0.864 | 0.859 | 0.862 | 0.862 | 2.3x |
| magic-html 0.1.8 | 0.887 | 0.891 | 0.889 | 0.889 | 3.5x |
| trafilatura 2.2.0 (precision) | 0.925 | 0.915 | 0.921 | 0.920 | 3.2x |
| **trafilatura 2.2.0 (standard)** | 0.906 | 0.943 | **0.923** | **0.924** | 3.2x |

Three readings that are *not* self-serving and matter more than the winner:

- **`html2text` scores 0.663 — below the 0.667 "do nothing, keep the raw HTML" floor.** On a full page it is
  worse than useless for article extraction. It is a markdown converter, not an extractor, and the two are
  routinely confused.
- **Extractors trade off in opposite directions.** goose3 leads precision (0.936) at 0.714 recall; inscriptis
  reaches 0.991 recall with 0.564 accuracy. The right choice depends on whether your failure mode is "missed
  the article body" or "swallowed the nav bar."
- **`resiliparse` runs at 0.3x — about 3x faster than the baseline — for F1 0.811.** If throughput dominates,
  that is the pick.

#### The second, independent benchmark

ScrapingHub's `article-extraction-benchmark` — **archived read-only by its owner on 2026-06-24**
[https://github.com/scrapinghub/article-extraction-benchmark]. Bootstrap estimation, HTML fetched through a
headless browser **with JavaScript disabled**:

| Tool | Version | **F1** | Precision | Recall |
|---|---|---|---|---|
| rs_trafilatura | 9261e08 | **0.970 ± 0.004** | 0.951 | 0.990 |
| go_trafilatura | ae7ea06 | 0.960 ± 0.007 | 0.940 | 0.980 |
| **trafilatura** | 2.0.0 | **0.958 ± 0.006** | 0.938 | 0.978 |
| **readability_js** | 0.6.0 | **0.947 ± 0.005** | 0.914 | 0.982 |
| go_readability | 9f5bf5c | 0.934 ± 0.009 | 0.900 | 0.971 |
| go_domdistiller | 25b8d04 | 0.927 ± 0.007 | 0.901 | 0.956 |

**Do not compare numbers across the two tables** — different corpora and different metrics (trafilatura scores
0.924 on its own set and 0.958 here). The only cross-benchmark conclusion is the **ordering**:
*trafilatura > readability > everything else*, which two independently-constructed evaluations agree on.

Caveat: the first table is the maintainer's own benchmark. The second is independent. Practical reading for a research skill: **recall matters more than precision** here, because a missed
paragraph is a silently lost fact while an extra nav-bar line is visible noise the model can ignore. That
favors trafilatura (0.943 recall) over readability-lxml (0.764) and goose3 (0.714) — a **~24-point recall gap**
against the two most commonly reeled-off alternatives.

### 3.2 Fetch success rates against protected sites

- **8/8 naive fetches produced a summarizable but wrong body** across Cloudflare, Akamai, PerimeterX,
  CloudFront WAF and DataDome targets; **0/8** produced real content; **0/8** produced a usable failure signal.
  The same author's stealth browser reached **5/8** (Cloudflare, CloudFront, PerimeterX targets), with DataDome
  and Amazon still blocking. [https://tilion.dev/blog/cloudflare-blocks-agents]
- Commercial scraping APIs, vendor-run benchmarks (treat as marketing, **unverified** methodology): Zyte
  reported at **93.14%** success at 2 req/s across 15 heavily protected sites in Proxyway's 2025 report
  [https://proxyway.com/research/web-scraping-api-report-2025]; Bright Data claims **98.44%** average across an
  11-provider comparison [https://brightdata.com/blog/web-data/best-web-scraping-apis]. These set the ceiling a
  paid service buys, and the gap to a keyless local fetch is the honest cost of "no API keys."
- In one operator's 24-hour window, **483 of 1,890** AI-agent requests failed (~25.6%), up 63% day-over-day.
  Single-site, single-day — **unverified** as representative. [https://tilion.dev/blog/cloudflare-blocks-agents]

### 3.3 Share of URLs failing per method — **no published data found**

Despite searching for it directly, **none of the six deep-research repos surveyed in §2.0 publishes a
per-method fetch success rate**, and the reason is visible in their code: gpt-researcher, storm and
dzhng/deep-research *discard* failures without recording them, so the data does not exist to publish. Only
jina-ai/node-DeepResearch keeps `badURLs`/`badHostnames` — and it does not report aggregates either.

**This gap is itself a finding.** A skill that records `fetch_method` + `status` per URL (§4.3) produces
exactly the dataset the field lacks, and can tune its own chain ordering from it after a few dozen research
runs. Recommend instrumenting from day one.

### 3.4 Probe summary from this survey

Not a benchmark — one IP, one day, 2026-09-02 — but the pass/fail pattern was consistent:

| Class | Result |
|---|---|
| Keyless structured APIs (Crossref, OpenAlex, arXiv, ar5iv, Wikipedia REST, Wayback, CDX) | **7/7 succeeded** |
| RSS/Atom feeds (HN, OpenAI, Cloudflare, simonwillison.net) | **4/4 succeeded** |
| Plain HTML on unprotected sites (HN, arXiv, NYT homepage) | **3/3 succeeded** |
| Protected sites via raw HTTP, with and without browser UA (Reuters 401, G2 403) | **0/2 succeeded, UA made no difference** |
| `r.jina.ai` keyless | succeeded on example.com, vercel.com/blog, x.com; **403 abuse-block on reuters.com** |
| DuckDuckGo HTML/lite endpoints | **0/2** — 202/200 with an anomaly page, zero result links |
| `archive.ph` | **429** |
| Google cache | **retired** — 200 consent page |
| Claude Code `WebFetch` on a robots-disallowed publisher | **refused** |
| Claude Code `WebFetch` on a PDF | **extraction failed, but the file was saved locally and `pdftotext` recovered it** |

---

## 4. Practical recommendation: a keyless fetch chain for a Claude Code skill

### 4.0 The portability constraint, measured

**[probe] on this machine (macOS, 2026-09-02):**

| Dependency | Present? |
|---|---|
| `curl` | yes |
| `python3` | yes (3.10) |
| `node` / `npx` | yes |
| `pdftotext` (poppler) | yes |
| `uv` / `uvx` | **no** |
| python `requests`, `httpx`, `bs4`, `trafilatura`, `readability`, `pypdf`, `fitz`, `markdownify`, `curl_cffi`, `playwright` | **all missing** |

This is the realistic baseline. **A portable skill must run on `curl` + Python standard library alone**, and
treat every extractor and browser as an *optional accelerator* detected at runtime, never a hard dependency.
Concretely: `urllib.request` + `html.parser` for the floor; `trafilatura` / `pdftotext` / Playwright used only
if `shutil.which()` or an import probe finds them; never fail because a library is absent.

### 4.1 The ordered fallback chain

Each step lists **when to move on**. The move-on criterion is the important half — §1.0 showed that status
codes alone are not a criterion.

1. **Is there a structured keyless API for this resource?** DOI → Crossref/OpenAlex; arXiv ID →
   `export.arxiv.org` or `ar5iv`; GitHub → `gh` CLI; Wikipedia → REST summary; a blog → its `/rss`.
   → **Move on if** no API matches the URL shape. *(This step is skipped by every repo surveyed and has the
   highest success rate of anything in this document.)*
2. **`WebFetch`** (harness tool). Cheap, cached 15 min, and pre-approved for many doc domains.
   → **Move on if** it returns a refusal string, a cross-host redirect notice (re-call once with the target
   first), a binary-saved notice, an answer that reads as a block/consent page, or an answer that fails to
   address the prompt.
   → **Special case:** if the result contains `[Binary content (...) also saved to <path>]`, **do not refetch** —
   jump to step 6 with that local path.
3. **Raw HTTP via a script** — `curl`/`urllib` with a browser-like `User-Agent`, `Accept-Language: en-US,en;q=0.9`,
   `Accept: text/html,...`, redirects followed, 20–30 s timeout, 10 MB cap. **`HEAD` first** to learn
   `Content-Type` and catch a 403 before downloading. Honor `robots.txt` by default (§2.4) and record the
   decision.
   → **Move on if** status ≥400 after one backoff retry *on 429/5xx only* (never retry 403/404), **or** the
   extracted text fails the plausibility gate in §4.2.
4. **Reader proxy — `r.jina.ai`** (keyless). One GET, returns markdown.
   → **Move on if** it returns 403 `AbuseAlleviationError` (per-domain anonymous blocks are real — **[probe]**
   `reuters.com` was blocked), a rate-limit error, or content failing the plausibility gate. Note that keyless
   Jina may return a **cached snapshot** ("Warning: This is a cached snapshot of the original page") — record
   that, it is not a live read.
5. **Wayback snapshot** — query **CDX**, not the availability API
   (`cdx/search/cdx?url=<exact url>&output=json&limit=1&fl=timestamp,statuscode`), then fetch
   `web.archive.org/web/<ts>id_/<url>` — the `id_` suppresses the injected toolbar (§2.3). Self-throttle to
   **under ~1 req/sec**: there are no warning headers before a 1-hour firewall ban.
   → **Move on if** CDX returns `[]`. **Record the snapshot timestamp alongside the access date** — the content
   is historical, and a claim sourced from a 2025 snapshot is not a claim about today.
   → **Then try Common Crawl** (index → WARC `Range:` fetch, §2.3) before giving up; it is keyless, confirmed
   working, and covers pages Wayback missed, at ~1 month staleness.
6. **Local extraction of anything already on disk** — `pdftotext` (or `pypdf`/`pymupdf4llm` if importable) on a
   WebFetch-saved binary or a downloaded PDF; `trafilatura`/`readability` on saved HTML.
   → **Move on if** no extractor is available or extraction yields <100 chars.
7. **Headless browser, only if already installed** — Playwright MCP / `chrome-devtools-mcp` / a local
   Playwright. Solves JS rendering and consent-click walls; does **not** solve managed challenges or CAPTCHAs.
   → **Skip entirely if** not installed. A ~150 MB Chromium download is not an acceptable implicit cost for a
   portable skill; make it explicit and opt-in.
8. **Record `UNFETCHABLE`** with the search snippet/synthesis as explicitly-weak evidence — and run the
   fabrication check from §2.3 *before* writing the row, because a 403 alone cannot tell a paywalled real
   article from an invented one (both returned 403 on `nytimes.com` **[probe]**; CDX said 438 captures vs 0).
   Order: DNS failure → fabricated domain; CDX ≥1 2xx capture → real-but-blocked, cite the snapshot; CDX `[]`
   plus zero Common Crawl hits plus a parent-path prefix query that *does* have captures → flag
   `possibly-fabricated` and do not cite.

**Out of scope by policy:** stealth/anti-detection fetchers (nodriver, Camoufox, curl_cffi impersonation,
StealthyFetcher) are documented in §2.1 as prior art and are **not** in this chain. They exist to defeat the
controls in §1.1, which is the boundary this project excludes.

### 4.2 The plausibility gate (the criterion that actually moves the chain)

Every step's output passes this before being accepted. Derived from gpt-researcher's `_reject()` family
(§2.0), node-DeepResearch's spam classifier, storm's `min_char_count`, and the §1.2 probes:

| Check | Threshold | Rationale |
|---|---|---|
| Length floor | `< 200` chars of extracted text → reject | storm uses 150; jina classifies below 300 |
| Text:HTML ratio | `< 1.5%` on a page expected to be an article → suspect JS-empty | §1.2 probes: 0.8–1.1% for SPAs |
| Block-page markers | case-insensitive scan of first 5,000 chars for `attention required! \| cloudflare`, `sorry, you have been blocked`, `please verify you are a human`, `checking your browser`, `anubis uses a proof-of-work scheme`, `enable javascript and cookies` | gpt-researcher `_BLOCK_PAGE_MARKERS` |
| Consent-wall markers | `before you continue`, `we use cookies and data`, `manage your privacy settings`, `accept all cookies` dominating the extracted text | §1.0 Google-cache probe |
| Unextracted PDF | leading `%PDF-`, or ≥2 of `endobj`/`endstream`/`/FlateDecode`/`xref`/`trailer` | gpt-researcher `_looks_like_unextracted_pdf`; route to step 6 |
| Word-list junk | ≥200,000 chars with <1 sentence terminator per 5,000 chars | gpt-researcher `_looks_like_word_list` |
| Prompt-relevance | the fetched text does not contain the entity/term the query was about | catches Haiku-summarized-away content (§1.8) |

**[probe] The ensemble was validated against real failures on 2026-09-02** — and the result is the argument
for using all of the checks rather than any one:

| URL | HTTP | HTML | text | text:HTML | markers hit | caught by |
|---|---|---|---|---|---|---|
| `g2.com` (DataDome) | 403 | 1,704 B | **50** | 2.93% | none | **length floor** |
| `reuters.com` | 401 | 771 B | **55** | 7.13% | none | **length floor** |
| Google "cache" consent wall | **200** | 301,356 B | 1,911 | **0.63%** | `before you continue`, `we use cookies and data` | **markers + ratio** |
| `html.duckduckgo.com` anomaly page | 200 | 31,069 B | 2,970 | 9.56% | none | **zero result links** (search-specific check) |
| `news.ycombinator.com` (good) | 200 | 33,773 B | 4,131 | 12.23% | none | passes |
| `arxiv.org/abs/...` (good) | 200 | 44,660 B | 5,283 | 11.83% | none | passes |

No single check caught everything. Hard blocks were short enough for the length floor but carried **no
marker text**; the consent wall was long enough to pass the floor and was caught only by markers and the ratio;
the DuckDuckGo soft-block passed every generic check and needed a result-count assertion. **Run the whole
ensemble, and log which check fired.**

A failed gate is **not** an error — it advances the chain and appends a reason to the registry.

### 4.3 What to record in the source registry

One row per URL, written whether the fetch succeeded or not. The repos surveyed almost universally fail here
(gpt-researcher, storm and dzhng drop failures entirely); node-DeepResearch's `badURLs`/`badHostnames` is the
model to follow.

```yaml
- url: https://example.com/article            # as requested
  canonical_url: https://example.com/article/ # from rel=canonical, if different
  status: ok | unfetchable | possibly-fabricated | skipped-robots
  fetch_method: keyless-api | webfetch | raw-http | jina-reader | wayback |
                local-extract | headless | search-snippet-only
  http_status: 200                            # null where the method hides it (WebFetch)
  accessed: 2026-09-02T04:21Z                 # when *we* fetched
  snapshot_date: null                         # Wayback/Jina-cache timestamp, if the content is historical
  content_type: text/html
  extracted_chars: 8359
  gate: passed | failed:block-page | failed:length | failed:js-empty
  attempts:                                   # the chain is the audit trail
    - {method: webfetch, result: "refused: unable to fetch"}
    - {method: raw-http, result: "403"}
    - {method: jina-reader, result: "403 AbuseAlleviationError"}
    - {method: wayback,   result: "snapshot 20250925030731"}
  robots: allowed | disallowed | not-checked
  evidence_strength: primary | archived | paraphrase-only
  quote_safe: true                            # false when the text came from a summarizer (§1.8: 125-char cap)
```

Two fields carry most of the value. **`evidence_strength`** stops an archived-2025 snapshot or a WebSearch
paraphrase from being cited as if it were a live primary read. **`quote_safe`** encodes that WebFetch output
is a Haiku paraphrase with a 125-character quote ceiling and therefore **cannot** back a verbatim quotation —
a raw fetch is required for that.

### 4.4 Preserving portability across harnesses

- **Put the chain in a plain script, not in prose.** One `fetch.py` (stdlib-only) or `fetch.mjs` that takes a
  URL and emits `{status, method, content, meta}` JSON. Every harness can shell out; only Claude Code has
  `WebFetch`.
- **Make harness tools the *optional* first rung, not the spine.** Steps 1 and 3–8 need no harness tool at all.
  On a harness without `WebFetch`, step 2 is skipped and nothing else changes.
- **Detect, never require.** `shutil.which("pdftotext")`, `importlib.util.find_spec("trafilatura")`,
  MCP-server presence — each upgrades a step; absence degrades it. §4.0 shows the bare machine is the common
  case.
- **Keep search behind a thin adapter.** `search(query) -> [{title, url}]`. Claude Code's `WebSearch` fills it;
  so does an SearXNG instance or a user-supplied key. Nothing downstream should know which.
- **Never let the registry depend on a tool.** It is YAML/JSON on disk, so a report produced under Claude Code
  is reproducible and auditable anywhere.
- **Budget explicitly.** Cap attempts per URL (≈4) and total fetches per research task; the surveyed repos cap
  concurrency (gpt-researcher 15 workers, dzhng 2, jina 5 URLs/step) but not per-URL retry cost.

---

## Recommended fallback chain

Ordered. Each step names the criterion for moving to the next. Steps 1 and 3–9 use no harness tool, so the
chain runs unchanged outside Claude Code.

1. **Structured keyless API, if the URL has a known shape.** DOI → `api.crossref.org` / `api.openalex.org`;
   arXiv → `export.arxiv.org` or `ar5iv.labs.arxiv.org/html/<id>`; GitHub → `gh` CLI; Wikipedia → REST summary;
   docs site → `llms.txt` or the `.md` sibling; blog → its RSS/Atom feed.
   **Move on if:** no API matches the URL shape.
2. **`WebFetch`** (Claude Code only). Cheap, cached 15 min, pre-approved on many doc domains.
   **Move on if:** a refusal string, a cross-host redirect notice (re-call once with the target first), or an
   answer that reads as a block/consent page or fails to address the prompt.
   **Jump to step 7 if:** the result contains `[Binary content (...) also saved to <path>]` — that is a
   completed download, not a failure.
3. **Raw HTTP** via `curl`/stdlib `urllib` with a browser-like `User-Agent`, `Accept-Language`, `Accept`;
   redirects followed; 20–30 s timeout; 10 MB cap. **`HEAD` first** to learn `Content-Type` and catch a 403
   before downloading. Honor `robots.txt` by default and record the decision.
   **Move on if:** status ≥400 after one backoff retry **on 429/5xx only** (never retry 403/404), or the text
   fails the plausibility gate (§4.2).
4. **`r.jina.ai`** — keyless, 20 RPM, **renders JavaScript**, handles PDFs.
   **Move on if:** `403 AbuseAlleviationError` (a per-domain anonymous block — will not clear on retry), a rate
   limit, or a gate failure. **Record `snapshot_date` if** the response carries
   `Warning: This is a cached snapshot`; send `x-no-cache: true` when freshness matters.
5. **`urltomarkdown`** — keyless, no JS rendering, no documented limit; best-effort.
   **Move on if:** non-200 or a gate failure.
6. **Archives.** CDX (`cdx/search/cdx?url=<exact>&output=json`) → fetch `web/<ts>id_/<url>`. Self-throttle
   below ~1 req/sec; there is no warning header before a 1-hour ban.
   **Move on if:** CDX returns `[]` — then try the **Common Crawl** index plus a WARC `Range:` fetch.
7. **Local extraction of anything already on disk.** `pdftotext` → `pypdf` → `pdfminer.six` for PDFs;
   `trafilatura` → `readability-lxml` for saved HTML. Use a smolagents-style type cascade
   (`Content-Type` + `Content-Disposition` + URL path + byte sniffing), not a single guess.
   **Move on if:** no extractor available, or output <200 chars.
8. **Headless browser — only if one is already installed.** `chrome-devtools-mcp` and `agent-browser` reuse
   your system Chrome and need no download; `playwright-mcp` needs an install step. Solves JS rendering and
   consent clicks; does **not** solve managed challenges, CAPTCHAs, or login walls.
   **Skip entirely if:** not installed. Do not make a browser download an implicit cost.
9. **Record `UNFETCHABLE`.** First run the fabrication check — DNS failure → fabricated domain; CDX ≥1 2xx
   capture → real-but-blocked (cite the snapshot); CDX `[]` + no Common Crawl hit + a parent-path prefix query
   that *does* have captures → `possibly-fabricated`, do not cite. Otherwise store the search
   snippet/synthesis as `evidence_strength: paraphrase-only`, `quote_safe: false`.

**Deliberately excluded:** stealth and anti-detection fetchers. They exist to defeat the controls in §1.1,
which is outside this project's scope, and they carry a ToS exposure and a maintenance treadmill a portable
skill cannot discharge.

---

## Sources

All accessed **2026-09-02**.

### Claude Code / Anthropic (primary)
- https://code.claude.com/docs/en/tools-reference
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/network-config
- https://code.claude.com/docs/en/data-usage
- https://code.claude.com/docs/en/changelog
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
- https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- https://claude.com/crawling/bots.json
- https://github.com/anthropics/claude-code/issues/68273
- https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/tool-description-webfetch.md
- https://mikhail.io/2025/10/claude-code-web-tools/ *(reverse-engineered, unverified)*
- https://github.com/LiranYoffe/reverse-engineering-claude-code-web-tools *(reverse-engineered, unverified)*

### Deep-research repos (source read at pinned commits)
- https://github.com/assafelovic/gpt-researcher — `6f99857`, `gpt_researcher/scraper/`
- https://github.com/langchain-ai/open_deep_research — `1b7d2e8`, `src/open_deep_research/`, `src/legacy/`
- https://github.com/dzhng/deep-research — `1f8f3e2`, `src/deep-research.ts`
- https://github.com/jina-ai/node-DeepResearch — `fd323b5`, `src/tools/read.ts`, `src/utils/url-tools.ts`
- https://github.com/huggingface/smolagents — `30bb116`, `examples/open_deep_research/scripts/`
- https://github.com/stanford-oval/storm — `fb951af`, `knowledge_storm/rm.py`, `knowledge_storm/utils.py`

### Browser automation / MCP
- https://github.com/microsoft/playwright-mcp
- https://github.com/ChromeDevTools/chrome-devtools-mcp
- https://github.com/vercel-labs/agent-browser *(note: `vercel/agent-browser` 404s)*
- https://github.com/browser-use/browser-use
- https://github.com/browserbase/stagehand
- https://github.com/puppeteer/puppeteer
- https://github.com/microsoft/playwright

### Anti-detection projects (documented as prior art, excluded from the recommendation)
- https://github.com/ultrafunkamsterdam/nodriver
- https://github.com/ultrafunkamsterdam/undetected-chromedriver
- https://github.com/daijro/camoufox
- https://github.com/D4Vinci/Scrapling · https://scrapling.readthedocs.io/en/latest/fetching/choosing.html
- https://github.com/lexiforest/curl_cffi
- https://github.com/unclecode/crawl4ai
- https://github.com/firecrawl/firecrawl · https://docs.firecrawl.dev/contributing/self-host
- https://github.com/apify/crawlee

### Readers / proxies
- https://jina.ai/reader/ · https://github.com/jina-ai/reader
- https://github.com/macsplit/urltomarkdown
- https://microlink.io/
- https://github.com/dhravya/markdowner *(HTTP 500 today)*

### Archives
- https://archive.org/help/wayback_api.php
- https://web.archive.org/cdx/search/cdx *(CDX server API)*
- https://index.commoncrawl.org/collinfo.json · https://data.commoncrawl.org/
- https://cirosantilli.com/wayback-machine-rate-limit *(community-documented limits, unverified officially)*
- https://github.com/edgi-govdata-archiving/wayback/issues/137
- https://kiledjian.com/2025/10/15/archivetoday-inside-the-web-archiving.html
- https://searchengineland.com/google-search-officially-retires-cache-link-437122
- https://searchengineland.com/google-search-completely-kills-the-cache-feature-446904
- https://searchengineland.com/bing-officially-removes-cache-link-from-search-results-449220

### Extractors and benchmarks
- https://trafilatura.readthedocs.io/en/latest/evaluation.html
- https://github.com/scrapinghub/article-extraction-benchmark *(archived read-only 2026-06-24)*
- https://github.com/mozilla/readability
- https://github.com/alan-turing-institute/ReadabiliPy
- https://github.com/kepano/defuddle
- https://github.com/microsoft/markitdown

### Search
- https://docs.searxng.org/dev/search_api.html
- https://github.com/searxng/searxng/issues/2505
- https://github.com/deedy5/ddgs/issues/272
- https://github.com/open-webui/open-webui/discussions/13947
- https://github.com/crewAIInc/crewAI/issues/136
- https://github.com/FoundationAgents/MetaGPT/issues/1567
- https://policies.google.com/terms
- https://www.seroundtable.com/google-sues-serpapi-40631.html

### Blocking, measurement, and standards
- https://blog.cloudflare.com/content-independence-day-no-ai-crawl-without-compensation/
- https://tilion.dev/blog/cloudflare-blocks-agents
- https://proxyway.com/research/web-scraping-api-report-2025 *(vendor benchmark, unverified methodology)*
- https://brightdata.com/blog/web-data/best-web-scraping-apis *(vendor claim, unverified)*
- https://datadome.co/guides/scraping/scraper-crawler-bots-how-to-protect-your-website-against-intensive-scraping/
- https://datatracker.ietf.org/doc/html/draft-meunier-web-bot-auth-architecture

### Snippet-as-evidence literature
- https://arxiv.org/pdf/2605.03534 *(SURE-RAG, evidence sufficiency)*
- https://arxiv.org/pdf/2512.05012 *(noisy retrieval degrades factuality)*
- https://arxiv.org/pdf/2605.27710 *(DeepSciVerify, evidence escalation)*
- https://arxiv.org/pdf/2412.15189 *(fact-checking pipelines)*

### Live probes
~40 `curl` / `urllib` / WebFetch requests run from this machine on 2026-09-02, covering bot-detection status
codes, UA sensitivity, JS-rendered text ratios, robots.txt refusal, PDF handling, Jina Reader, Wayback
availability + CDX + `id_`, Common Crawl index + WARC range, archive.today, Google/Bing cache, DuckDuckGo
HTML/Lite, SearXNG public instances, keyless scholarly APIs, RSS/AMP prevalence, and local tool availability.
Marked **[probe]** throughout. One IP, one day — indicative, not a benchmark.
