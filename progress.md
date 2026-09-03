# progress.md — live chronological log

> Purpose: single source of truth for where we are and how we got here. Survives context compaction and new sessions. Append new entries at the bottom; keep "Current state" at the top accurate.

## Current state (keep updated)
- **Phase:** 1 — design v1 from literature. Requirements locked in `REQUIREMENTS.md` (2026-09-02).
- **Last action (2026-09-03, session 2):** implemented `skill/deep-research/` (SKILL.md, prompts, fetch/ledger/cite_check scripts, contracts, adapters, tests); scripts pass offline unit tests and a live integration test (entry #30).
- **Next action:** smoke-test the whole workflow with model agents on 1-2 questions (generator Sonnet per REQ 4), fix what breaks, then start Phase 2 (pilot vs Claude Code built-in `/deep-research`). User has not yet given feedback on `skill/DESIGN.md`; v1 proceeds as drafted (entry #29).
- **Session log:** session 1 ended 2026-09-02 after entry #27 (HEAD 7222c8e). Session 2 started 2026-09-03.
- **Open questions:** user feedback on DESIGN.md (verification default, budget split) still welcome; both are preset/prompt parameters.

---

## 2026-09-02 #1 — Project kickoff
**Plan / user intent (paraphrased from the user's brief):**
- Build the best "research architecture workflow": what happens when a user invokes something like `/deep-research` in an agent harness.
- Package it as a **skill** usable from any harness (Claude Code, Codex, Hermes, ...).
- Publish to GitHub with all findings and evidence, so future rounds can re-research whether the workflow is still best and update it.
- Maintain `CLAUDE.md` and `progress.md` autonomously as the project evolves.

**Actions taken:**
- Inspected the empty project directory `/Users/lzh/Desktop/ResearchWorkflow`.
- Checked environment: Claude Code plugins (superpowers, claude-mem, elements-of-style); Hermes present with skills at `~/.hermes/skills/<category>/<skill>/`; Codex not on PATH.
- Created `CLAUDE.md` (conventions) and this file.

**Decisions:**
- Core skill will be harness-agnostic Markdown + optional scripts; harness-specific packaging in thin adapters. (Rationale: portability was the user's explicit requirement.)
- Not initializing git yet; wait for user's answers on the GitHub plan.

## 2026-09-02 #2 — Gap questions posed to user (awaiting answers)
(Numbering below is canonical; it matches the list the user saw. Corrected 2026-09-02 after a numbering mismatch confused the user.)
1. Definition of "research": web/literature research, codebase research, or both?
2. Output contract: what does a finished run produce (files, format, length, citation style)?
3. Quality bar and evaluation: how do we judge one workflow better than another?
4. Scope of this first round: design from literature only, or also run empirical head-to-head comparisons of candidate workflows now?
5. Harness priority order and minimum viable set (Claude Code, Hermes confirmed installed; Codex not on PATH; OpenCode, Gemini CLI, Cursor?).
6. Tooling assumptions: built-in WebSearch/WebFetch only, or external APIs (Exa, Tavily, Semantic Scholar, arXiv)? Paid keys?
7. Cost/latency budget per run (tokens, wall-clock, subagent count).
8. Autonomy level: fully autonomous vs clarifying-question phase vs human checkpoints.
9. GitHub: repo name, public vs private, license, may we depend on existing skills (e.g. superpowers)?
10. Re-audit cadence/trigger for future rounds.
11. Prior art the user already likes/dislikes.
12. Language/domain focus.

**Findings:** none yet.
**Decisions:** none yet; blocked on answers.

## 2026-09-02 #3 — Q1 sub-question: what is Claude Code's built-in deep research?
**User asked:** is "Claude Code deep research" web research or codebase research?

**Research conducted:**
- Searched installed plugins/skills for anything named deep-research: none in Claude Code plugins; only `~/.hermes/skills/research/research-paper-writing/` mentions it.
- A docs-lookup subagent reported no built-in feature. **That was wrong**: the Claude Code changelog (versions 2.1.197, 2.1.207, 2.1.218) references `/deep-research`, and the binary (Claude Code 2.1.258) contains a built-in Workflow named `deep-research`.
- Extracted the full built-in workflow script to `research/prior-art/claude-code-builtin-deep-research.workflow.js` (443 lines).

**Findings (built-in `/deep-research`, Claude Code 2.1.258):**
- It is **web research only**. Description: "Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report." Source comment: "Ported from bughunter architecture. WebSearch/WebFetch instead of git/grep."
- Pipeline: Scope (decompose into 3-6 angles) -> Search (parallel WebSearch agents, one per angle) -> URL-dedup -> Fetch+Extract (top 15 sources, extract falsifiable claims) -> Verify (3 votes per claim, 2/3 refutations kill a claim, max 25 claims) -> Synthesize (merge semantic dupes, rank by confidence, cite).
- Constants: VOTES_PER_CLAIM=3, REFUTATIONS_REQUIRED=2, MAX_FETCH=15, MAX_VERIFY_CLAIMS=25.
- Pre-invocation rule: if the question is underspecified, ask 2-3 clarifying questions first.
- Since 2.1.218 it only runs when invoked manually (Claude no longer auto-launches it).
- Codebase research in Claude Code is handled separately (Explore subagents, `/code-review`, the "bughunter" workflow the deep-research script was ported from).

**Decisions:** none yet. This is prior art #1 for the literature review and the most direct baseline to beat.

## 2026-09-02 #4 — Q1 decided: web research only
**Decision:** The skill covers **web research only** for this round (no codebase or local-document research). Rationale: matches the built-in Claude Code `/deep-research` baseline for a fair comparison; keeps scope tight. Codebase research may be a later extension.

## 2026-09-02 #5 — Q2 (output contract): user's proposal and Claude's recommendation
**User's proposal:** each agent returns its own markdown file; one markdown file gathers all findings and concludes the research.
**Claude's recommendation (pending user confirmation):** adopt the proposal, and structure it as a per-run directory:
```
research-runs/<YYYY-MM-DD>-<slug>/
  00-brief.md          # refined question, scope, angles, assumptions, depth setting
  angles/<angle>.md    # one file per search/fetch agent: findings, claims, quotes, per-claim URLs, confidence
  sources.md           # registry of every fetched URL: title, publisher, date, accessed date, fetch status
  verification.md      # claim ledger: claim -> supported / refuted / unverified, with evidence
  report.md            # the deliverable: exec summary, findings, disagreements, gaps, numbered citations, methodology appendix
  run.json             # metadata: harness, model, timings, agent count, token cost (feeds Q3 evaluation)
```
Key points: report.md must be self-contained (agent files are audit trail, not required reading); numbered inline citations [n] mapped to sources.md with access dates; adaptive length with depth presets (quick / standard / deep); agents hand off via files, not return values, to protect the synthesizer's context.

## 2026-09-02 #6 — Q2 provisionally accepted; survey requested
**User:** the recommended output contract "looks right", but wants to see what finished runs look like in other research workflows before finalizing. Has no answer for Q3 (evaluation) and wants a recommendation.
**Plan:** two parallel literature surveys, written to `research/literature/`:
1. `output-formats-survey.md` — what a finished run produces in OpenAI Deep Research, Gemini Deep Research, Perplexity Deep Research, Anthropic's multi-agent research system, STORM/Co-STORM, GPT Researcher, LangChain Open Deep Research, HF open-deep-research, Claude Code built-in, and other notable open-source agents. Format, length, citation style, intermediate artifacts, file outputs.
2. `evaluation-survey.md` — how deep-research agents are evaluated: benchmarks (e.g. DeepResearch Bench, BrowseComp, GAIA, HLE, ResearchQA-type), rubrics (citation accuracy, coverage, factuality), LLM-as-judge practices, cost/latency reporting.

## 2026-09-02 #7 — Evaluation survey completed (`research/literature/evaluation-survey.md`, 265 lines, ~55 sources)
**Key findings:**
- Report-level benchmarks (DeepResearch Bench I/II, ResearchRubrics, LiveResearchBench, DEER, DRACO, ReportBench, ResearcherBench, FutureSearch Deep Research Bench) have converged on **fine-grained binary rubrics graded by a frontier LLM judge**; pairwise comparison is reserved for subjective depth. Judging costs ~$0.25-1.00/report.
- **Recall of key facts is the bottleneck**: DeepResearch Bench II best agent ~40% recall vs ~89% presentation quality.
- **Citation support, not URL validity, is the dominant citation error**: frontier systems >94% valid links but only 39-77% fact-check accuracy. Fabricated URLs still occur (Gemini 2.5 Pro DR 13.3%). Wayback lookups separate fabricated from stale; a URL-health self-correction loop cuts non-resolving citations below 1%.
- Public leaderboards: DeepResearch Bench Gemini 2.5 Pro DR 48.88 / OpenAI DR 46.98 / Perplexity 42.25 (Perplexity best citation accuracy ~90%). FutureSearch DRB (June 2026): Opus 4.6 0.553 at $0.53/task.
- Short-answer proxies (BrowseComp, GAIA, HLE, SimpleQA...) miss omissions, shallow synthesis and citation faults; contamination inflates up to 4%.
- Judge biases: position (verdict flips 13.6%), verbosity, self-preference. Mitigations with evidence: forced chain-of-thought, position swap, two-family judge ensemble, expert-grounded rubrics, small human calibration set. LiveResearchBench rejected Claude 4 Sonnet as judge for low human agreement.
- Efficiency: higher reasoning effort often costs 50-200% more for flat/negative accuracy; cost does not correlate with pass rate.
- Statistics: paired designs need ~2x fewer items; 50-100 questions only resolve large gaps; use paired bootstrap, cluster by domain.
**Recommended protocol (12 steps, in file):** 40-60 fresh mixed-domain questions with pre-written binary rubrics; pin model/effort/tool budget across workflows; automated URL resolution + Wayback + quote-containment checks; sampled LLM citation-support judgments; different-family judge with CoT; swapped-position pairwise for depth; 20% second-judge kappa; paired bootstrap on rubric compliance as primary metric; hand-grade 10 reports to calibrate. Budget: ~200 reports per comparison, roughly one day of compute.
**Implication for the skill design:** the skill should build in URL health checks and claim-level citation support checks (the two measurable weaknesses of current systems), and optimise for fact recall, not presentation.

## 2026-09-02 #8 — Output-formats survey completed (`research/literature/output-formats-survey.md`, 248 lines, ~55 sources; 19 systems compared)
**Key findings:**
- Every report-producing system converges on **one Markdown-style report: headings, inline per-claim citations, trailing source list**. Answer-oriented agents (Jina, HF open-deep-research, Tongyi) return a short answer with footnotes instead. Only dzhng/deep-research and Jina let the caller choose answer vs report.
- Citation mechanics split three ways: character-span annotations (OpenAI `url_citation`, Exa field-level grounding with confidence), numbered `[n]` + gap-free source list (LangChain ODR, STORM), or sentence-end hyperlinks in APA (GPT Researcher). **Nobody records access dates by default.**
- A pre-research scoping artifact is standard: clarifying questions (ChatGPT, dzhng, ODR) or an editable plan (Gemini "Edit plan", Gemini API `collaborative_planning`, Claude Code phase approval).
- Process is shown as a live trace but rarely persisted; **only STORM and Claude Code keep intermediate artifacts on disk** (STORM: outline, conversation_log.json, url_to_info.json; Claude Code: script + per-agent results).
- Depth is controlled by budget knobs (max_tool_calls, breadth/depth, iterations, maxUrls/timeLimit, token budget, size guideline), not target length. GPT Researcher's TOTAL_WORDS=1200 is the only length control and it is a floor.
- **Verification as a first-class stage exists only in Claude Code /deep-research, Anthropic's CitationAgent, and GPT Researcher's Reviewer/Revisor.** No consumer product exposes per-source quality grades.
- Export (PDF/DOCX/Docs/PPT) is layered on late; CLI tools write report.md directly.
- Critiques: 3-13% fabricated URLs and 5-18% non-resolving; citation quality and factual accuracy weakest axes; redundancy and over-reliance on few sources inflate length; 12k-word reports that summarise without analysing; content-farm sources; "illusion of knowledge" when key entities are missing. **Every critique is about excess length; none about brevity.**

## 2026-09-02 #9 — Q2 revised recommendation (after survey)
The user's proposal (per-agent markdown + one synthesis markdown) is validated: it matches STORM and Claude Code, the only two systems that persist intermediate artifacts, and addresses the auditability gap every chat product has. Revisions to the earlier proposal (entry #5) driven by the survey:
1. **Add a machine-readable sidecar** `claims.json` (per claim: text, direct quote, URL, source-quality grade, verification status, access date) alongside `sources.md`. Mirrors STORM's url_to_info.json and OpenAI span annotations; enables automated eval (Q3).
2. **Sources list carries access date + URL health status (LIVE/DEAD/ARCHIVED-ONLY).** Nobody does this; 5-18% of deep-research URLs do not resolve.
3. **Verification status goes inside report.md**, not only in verification.md: multi-source confirmed / single-source / dropped after cross-check / unverified. Plus a "What this report could not find" section.
4. **Plan echoed in report header** so scope is visible; optional approval pause after 00-brief.md (Gemini/ODR pattern). Rename 00-brief.md -> plan.md? Keep `00-brief.md` (contains brief + plan).
5. **Separate depth from length.** Depth presets (quick/standard/deep) control sources/angles/claims budget; length is a target word *range* (ceiling, not floor) with a `brief` (answer.md-style) vs `report` mode. Default shorter.
6. **Synthesis prompt rules:** prefer primary/official sources; one direct quote per extracted claim; cap share of claims any single source supports; no restating a finding across sections.
7. **Front-load** a 5-10 line exec summary and a key-findings table (finding | confidence | #sources) before the body, so the report is usable as context for a downstream agent.
8. **Numbered [n] citations with gap-free source list** chosen as most portable across renderers (vs span annotations or APA hyperlinks).
Revised run directory:
```
research-runs/<YYYY-MM-DD>-<slug>/
  00-brief.md        refined question, clarifications, plan/angles, depth+length settings (approval point)
  angles/<angle>.md  per-agent notes: findings, quotes, URLs, confidence
  sources.md         [n] registry: title, publisher, pub date, access date, quality grade, URL health
  claims.json        machine-readable claim ledger (feeds eval)
  verification.md    human-readable verification log
  report.md          exec summary -> findings table -> body with [n] -> could-not-find -> methodology -> sources
  run.json           harness, model, timings, agents, tokens, cost
```
**Status:** presented to user; awaiting confirmation.

## 2026-09-02 #10 — Q3 recommendation (evaluation)
Adopt the 12-step protocol from entry #7 / `evaluation-survey.md`: rubric-based LLM-judge scoring on 40-60 fresh mixed-domain questions, automated citation checks, different-family judge, paired bootstrap, 10 hand-graded calibration reports. Baselines to compare against: Claude Code built-in /deep-research (prior art #1), and the skill's own earlier versions in future rounds. **Status:** presented; awaiting confirmation.

## 2026-09-02 #11 — Q3 decided; Q2 restated
**Q3 decision (user: "i am ok with question 3"):** adopt the evaluation protocol in entry #7 / `research/literature/evaluation-survey.md` (rubric-based LLM-judge scoring on 40-60 fresh mixed-domain questions, automated citation checks, different-family judge, paired bootstrap, 10 hand-graded calibration reports). Baseline #1: Claude Code built-in `/deep-research`.
**Q2 restated for the user in plain terms** (the consolidated answer, superseding entries #5 and #9 as the reference):
A finished run = one folder containing: (1) `report.md`, the deliverable, self-contained, short-first (summary + findings table), numbered citations, verification labels, a "could not find" section; (2) one markdown note per research agent under `angles/`; (3) `sources.md`, the numbered source list with access date and link health; (4) `00-brief.md`, the plan written before research starts; (5) `verification.md` + `claims.json`, the fact-check record (human and machine readable); (6) `run.json`, cost/time metadata. User controls: depth preset (quick/standard/deep) and output mode (brief answer vs full report).
**Process note:** numbering mismatch between chat and progress.md corrected in entry #2.

## 2026-09-02 #12 — Q2 decided; Q4 discussion
**Q2 decision (user: "question 2 is clear now"):** output contract as stated in entry #11 is final for this round.
**Q4 (user concerns):** not sure there is enough token budget for an empirical comparison; worried the result depends on which model is used and may be skewed.
**Claude's recommendation:** hybrid. (a) Design v1 from the literature and prior art. (b) Run a *pilot* comparison, not the full protocol: ~12-15 questions, 2 workflows (our skill vs Claude Code built-in `/deep-research`), 1 run each, standard depth; ~30 reports. (c) Scale to the full 40-60 question protocol only if the pilot shows a gap worth measuring or in a later round. On model skew: the protocol pins the same model and budget for both workflows, so the comparison is fair *for that model*; transfer to other models is a stated limitation and a reason for future re-audit rounds. Use one mid-tier model (e.g. Sonnet) for generation in the pilot and a different-family judge.

## 2026-09-02 #13 — Q4 follow-up: judge without external API keys; cost with keys
**User context:** Claude subscription plan (no per-token billing); may or may not have OpenAI/Gemini API keys.
**Without external keys:** the judge must be Claude. Consequences: (a) self-preference bias is present but *symmetric* — both workflows produce Claude text, so it does not favour one workflow over the other, though it inflates absolute scores; (b) LiveResearchBench found Claude 4 Sonnet an unreliable judge (low human agreement), so use Opus as judge and Sonnet as generator; (c) binary rubric items are less bias-prone than holistic/pairwise ratings — keep pairwise depth judgments minimal or skip; (d) the automated citation checks (URL resolution, Wayback, quote containment) are model-free and unaffected; (e) hand-grading 10 reports remains the calibration anchor. Generation and judging both consume subscription quota rather than dollars.
**With external keys (estimates from evaluation-survey.md lines 84, 172, 205):** judging ~$0.25-1.00 per report (Gemini 2.5 Pro ~$0.25 batched; GPT-5.2-class ~$0.5-1.0); Gemini 2.5 Flash pairwise ~$0.001 each. Pilot (30 reports): judging ~$8-30. Full protocol (200 reports): ~$50-200. Generation stays on the Claude subscription in both cases.

## 2026-09-02 #14 — Q4 decided
**Decision (user):** literature-first design of v1, then a pilot comparison (~12-15 questions, our skill vs Claude Code built-in `/deep-research`, 1 run each, ~30 reports). Judge with **Claude Opus** for now; generate with Sonnet. Known limitation to record in evidence: same-family judge (symmetric self-preference; absolute scores inflated, comparison still fair). Revisit judge choice if a Gemini/OpenAI key becomes available. Automated citation checks (model-free) and 10 hand-graded calibration reports remain part of the pilot.

## 2026-09-02 #15 — Q5 (harness priority): environment facts gathered
**Findings:**
- Hermes skills use the same format as Claude Code skills: a `SKILL.md` with YAML frontmatter (`name`, `description`, `version`, `license`, `metadata`), i.e. the open Agent Skills standard. Hermes also loads repo-local skills from `./.hermes/skills` and **`./.agents/skills`** (the cross-harness convention) once the project is trusted, and installs from registries (skills.sh, GitHub, ClawHub) via `hermes skills install`.
- Codex: not installed locally. Codex CLI is believed to support the same Agent Skills standard (`.agents/skills/*/SKILL.md`) — **to verify when we package the adapter**.
- Gemini CLI, OpenCode: binaries not installed (only a stale `~/.gemini` config dir exists).
- **Prior art #2:** Hermes ships `grounded-citations` (MIT, by Hermes Agent + Teknium): a ledger script owns the `url -> [n]` mapping so citation numbers come from retrieval, not model memory; verbatim quotes are rejected unless they literally appear in fetched page text; model-knowledge claims flagged `[unverified]`; `verify --evidence` fails drafts with evidence-less sources. Copied to `research/prior-art/hermes-grounded-citations/`. Directly relevant to our sources.md / claims.json / verification design.
**Recommendation (pending user):** Priority 1 Claude Code (baseline and eval live there). Priority 2 Hermes (installed, same skill format). Priority 3 Codex (same standard, verify later). Package the core once as `skill/deep-research/SKILL.md` and expose it via `.agents/skills/` so all three load it; keep harness-specific glue (e.g. Claude Code subagent invocation vs Hermes delegate tool) in small adapter notes. Minimum viable set for round 1: Claude Code + Hermes.

## 2026-09-02 #16 — Q5 decided
**Decision (user):** Claude Code is the only harness we build for and test on. Hermes and Codex were examples, not requirements. The goal is that the skill *can* be used by any harness, so portability is a design constraint (plain Markdown `SKILL.md` per the Agent Skills standard, no Claude-only syntax in the core, harness-specific glue kept separate), not a testing obligation. Hermes may be used for an optional zero-cost smoke test since it is installed, but it is not a deliverable.

## 2026-09-02 #17 — Q6 (tooling): user input and fetch-reliability concern
**User:** has no API keys (Exa/Tavily/Brave/Firecrawl/Jina). Notes that built-in web search and page fetching sometimes fail, and has seen repositories that let agents browse the web without such restrictions.
**Observed evidence today:** our own survey agent got HTTP 403 from help.openai.com and perplexity.ai blog/help pages (see output-formats-survey.md header note).
**Plan:** Opus subagent survey of fetch-failure causes and the fallback strategies used by popular open-source research/browsing agents (headless browsers, reader proxies, archive copies, UA/retry strategies), written to `research/literature/fetch-reliability-survey.md`. Then decide the core fallback chain for the skill.
**Working position (pending survey):** core skill assumes only generic search + fetch; add a keyless fallback chain for failed fetches; free Wayback availability check in core; academic APIs optional. Anything that defeats paywalls, logins, or CAPTCHAs is out of scope.

## 2026-09-02 #18 — Fetch-reliability survey completed (`research/literature/fetch-reliability-survey.md`, 1,256 lines, ~40 sources + ~40 live probes; Opus agent)
**Key findings:**
- **Failures are silent.** On 8 sites behind Cloudflare/Akamai/PerimeterX/DataDome, naive fetch got real content 0/8 but a summarizable body 8/8; status codes were 403, 307 and even 200. => every fallback needs a *content plausibility gate*, not a status-code check.
- **Claude Code WebFetch facts:** fetches locally from the user's IP (honours HTTPS_PROXY) after a hostname preflight to api.anthropic.com; identifies as `Claude-User`, so robots.txt refusals are real (nytimes.com disallows it; plain curl gets content); returns a Haiku summary with a **125-char quote cap** (cannot back verbatim quotes); no JS; swallows HTTP error bodies. **WebSearch returns titles+URLs plus a model paraphrase, not verbatim snippets** — a pointer, never a citation.
- **PDFs:** WebFetch fails extraction but silently saves the file and names the path; `pdftotext` on it works. Treat as a download, not a failure.
- **Repo survey (6 repos, pinned commits):** open_deep_research never fetches pages (search-API only); dzhng = one Firecrawl call; gpt-researcher and STORM silently drop failures; smolagents returns the 403 body then tries Wayback; only node-DeepResearch tracks badURLs/badHostnames. **No repo publishes fetch success rates because they discard failures** — recording them is itself a contribution.
- **Reusable pieces:** gpt-researcher's `_BLOCK_PAGE_MARKERS` reject-list; smolagents' `find_archived_url` + content-type cascade.
- **Keyless rungs that work today:** `r.jina.ai` (20 RPM confirmed by headers, renders JS, handles PDFs), `urltomarkdown`, Wayback CDX + `id_` raw snapshot, Common Crawl index + WARC Range fetch. **Dead:** Markdowner (500), Mercury (DNS dead), Google/Bing caches (retired), DuckDuckGo HTML/Lite (CAPTCHA at HTTP 202; retrying cannot help).
- **Fabrication detection:** live status cannot do it (real paywalled and fabricated NYT URLs both 403); Wayback CDX separates them (438 captures vs 0). Order: DNS fail -> fake domain; CDX capture -> real-but-blocked, cite snapshot; CDX empty + no Common Crawl + parent path has captures -> possibly-fabricated, do not cite.
- **Extractors:** trafilatura best (F1 0.924/0.958); html2text scores below the raw-HTML floor; resiliparse 3x faster at F1 0.811.
- **Portability constraint measured on this machine:** no `uv`, zero third-party Python libs => chain must run on `curl` + Python stdlib; everything else detected, never required.
**Recommended 9-step fallback chain (in file):** structured keyless API by URL shape (Crossref/OpenAlex/arXiv/GitHub/Wikipedia/llms.txt/RSS) -> WebFetch -> raw HTTP with browser-like headers, HEAD first, honour robots.txt, retry only 429/5xx -> r.jina.ai -> urltomarkdown -> Wayback CDX / Common Crawl -> local extraction of saved files -> headless browser only if already installed -> UNFETCHABLE with fabrication check; registry records fetch_method, evidence_strength, quote_safe, snapshot_date. Stealth/anti-detection fetchers documented as prior art and **excluded**.

## 2026-09-02 #19 — Q6 recommendation (pending user)
Core skill assumes only generic search + fetch, plus `curl` and Python stdlib. Ship the 9-step keyless fallback chain as a small script (`fetch.py`) with a content plausibility gate; record fetch method and evidence strength per source; treat WebSearch output as pointers, never citations; verbatim quotes only from raw text (steps 3-7), never from WebFetch summaries. Headless browser and paid APIs are optional, auto-detected. Paywall/login/CAPTCHA circumvention out of scope.

## 2026-09-02 #20 — Q6 and Q7 decided
**Q6 decision (user: "ok with question 6"):** as in entry #19 — generic search + fetch only, curl + Python stdlib, 9-step keyless fallback chain script with content plausibility gate, per-source fetch_method/evidence_strength, quotes only from raw text, optional auto-detected browser/APIs, no paywall/login/CAPTCHA circumvention.
**Q7 decision (user):** wall-clock time is not a constraint. The user chooses the **number of agents** at invocation, with a recommendation shown (derived from the depth preset and the question's angle count). The user also chooses **parallel vs sequential** execution. Implication for design: the depth presets set defaults for agent count; the skill must present the recommendation and accept overrides; sequential mode must produce identical outputs (same run folder) with agents run one at a time, so results are comparable and the skill works on harnesses without parallel subagents.

## 2026-09-02 #21 — Q8 decided
**Decision (user):** (1) clarifying questions only if the question is underspecified (2-3 max); (2) one plan checkpoint after `00-brief.md` is written, where the user confirms/adjusts angles, agent count (recommendation shown) and parallel vs sequential; (3) fully autonomous thereafter, no mid-run pauses. A skip flag runs with recommendations and no checkpoint (for batch/pilot runs).

## 2026-09-02 #22 — Q9 (GitHub) discussion
**Environment:** `gh` authenticated as ZhongHanLoo; git global user.name/email not set.
**Claude's recommendations:** repo `deep-research-skill`; public; MIT; no dependencies on other skills (standalone for portability); eval questions and rubrics kept private (separate private repo or gitignored) to avoid leakage.
**User challenged:** why include the Claude Code and Hermes workflows in the repository at all?
**Decision:** they are not included. The repo carries a `research/prior-art/README.md` describing each baseline (name, version, date, pipeline summary, link to source at pinned commit). Local copies in `research/prior-art/` remain gitignored working references only. Rationale: the re-audit only needs to know what the baselines were; copying code adds licensing risk (the Claude Code script is proprietary, extracted from the binary) and no value.
**Still awaiting user:** repo name, git name/email for commits, confirmation of public + MIT.

## 2026-09-02 #23 — Q9 decided and executed
**Decision (user: "use my github account, do what you think is best"):** repo `ZhongHanLoo/deep-research-skill`, public, MIT, standalone. Commit identity set locally to `ZH <ZhongHanLoo@users.noreply.github.com>` (GitHub profile name; no-reply address so the user's personal email is not exposed).
**Executed:** `git init` (branch main); `.gitignore` excludes `research/prior-art/*` except its README, and `eval/private/`; added LICENSE (MIT), README.md, `research/prior-art/README.md` (descriptions of the Claude Code built-in and Hermes grounded-citations baselines, no code); initial commit; GitHub repo created and pushed.

## 2026-09-02 #24 — Q10 decided
**Decision (user):** re-audit is **manual**, triggered by the user whenever they choose. No scheduled cadence or automated event triggers. What needs updating is determined during the re-audit itself. Design implication: the repo must make a re-audit easy to start cold — `progress.md`, the surveys with dated source lists, and the pilot evidence are the inputs; a short "How to run a re-audit" section in the README will point at them.

## 2026-09-02 #25 — Q11, Q12 decided; requirements locked; Phase 0 closed
**Decisions (user: "no preference on both, go with the defaults"):** Q11 no prior-art preferences, design from survey findings. Q12 general-purpose, English-first, pilot questions across five domains.
**Requirements consolidated in `REQUIREMENTS.md`.**
**Phase 1 plan (design v1 from literature):**
1. Architecture survey (Opus agent): how existing systems and papers handle question decomposition, search strategy (breadth vs depth, iterative vs one-shot), multi-agent orchestration (lead/subagent, file handoff, context management), claim extraction and verification, synthesis; what published evidence/ablations say actually improves recall and citation quality. Output: `research/literature/architecture-survey.md`.
2. v1 design document (`skill/DESIGN.md`): phases, agent roles, prompts outline, file contracts per Q2, fallback chain per Q6, controls per Q7/Q8, with each choice traced to survey evidence.
3. Implement `skill/deep-research/` (SKILL.md + scripts: fetch chain, source ledger, claims/verification, URL health) and Claude Code adapter.
4. Smoke-test on 2-3 questions; iterate.
5. Phase 2: pilot evaluation per Q3/Q4.

## 2026-09-02 #26 — Architecture survey completed (`research/literature/architecture-survey.md`, 645 lines, 53 sources; Opus agent)
**Key findings:**
- **Recall bottleneck confirmed by four independent teams:** DRB-II recall 23-40% vs presentation 75-92%; TaxoBench best agent retrieves 21% of expert-cited papers; LiveResearchBench "deep searchers, not deep researchers"; PING taxonomy: the largest hallucination class is *noise-induced* (evidence retrieved but unused, 0.24-0.48) vs fabrication (0.10-0.15).
- **Strongest transferable result:** IterResearch's *workspace reconstruction* (rebuild a compact state each round: question, evolving findings, last observation) works as a pure prompting strategy: o3 34.1->46.8%, DeepSeek-V3.1 23.1->42.3% on BrowseComp vs ReAct; +12.6pp over a mono-context agent with a larger window. Reduces tokens.
- **STORM ablation: iteration beats personas.** Removing the conversation loop costs entity recall 40.5->32.0; removing perspectives costs only 40.5->40.1. Generating angles once before evidence is STORM's losing arm.
- **Multi-agent evidence weaker than the headline:** Anthropic's +90.2% sits beside "token usage explains 80% of variance" and 15x cost; LiveResearchBench has multi-agent behind single-agent on coverage (66.8 vs 76.3) and credits multi-agent's citation win to explicit citation-alignment steps; single-agent matches multi-agent at matched token budgets (Tran & Kiela). LangChain abandoned parallel section-writing as "disjoint".
- **Verification: corroboration beats refutation.** FineVerify decompose-and-check +8.2pp; DRIFT claim ledger +28pp F1; self-consistency beats debate at matched budget (88.2 vs 83.0); intrinsic self-correction degrades accuracy; adversarial advocates flip judges. Retrieval is the *lowest*-error stage (2.9%).
- **Drafting:** interleaving drafting with retrieval helps (removing it: -18.5% WebThinker); revising without new evidence regresses. Rule: every revision pass must carry new retrieval.
- **Higher reasoning effort is flat-to-negative** on Deep Research Bench for 3 of 4 frontier models; spend marginal tokens on reading more sources.
- **Built-in `/deep-research` well-supported on:** quoted claims from fetched pages only; structured extraction as compression; independent voters; `unverified` vs `refuted`; refuted claims listed; state out of session context; dedup + confidence ranking.
- **Built-in weaknesses (ranked):** (1) budget inverted: ~15 fetch agents vs ~75 verifier agents; (2) verifier instruction "Default to refuted=true if uncertain" optimises precision against recall; (3) angles generated once, cold; (4) no re-search loop; (5) no hypothesis conditioning; (6) no quote-containment check; (7) 25-claim cap discards up to 2/3 of extracted evidence; (8) fixed budgets, no saturation stop; (9) no explicit could-not-find contract.
- **Caveat:** one PDF extraction produced fabricated numbers contradicted by the abstract; discarded. Surviving PDF-only figures marked unverified.
**16 design recommendations R1-R16 in the file, tagged by evidence strength.** One-line version: spend budget on reading more full pages and extracting more quoted claims; keep a compact rewritten working state; decompose twice (cold, then evidence-seeded); verify by corroboration not refutation; write once from assembled evidence.

## 2026-09-02 #27 — v1 design document drafted (`skill/DESIGN.md`)
Written from REQUIREMENTS.md + the four surveys. Every phase and parameter carries an evidence tag (R# from architecture-survey.md, or the other surveys). Key departures from the built-in: fetch budget >= verification budget; verification default is `unverified`, not `refuted`, and seeks corroboration; second evidence-seeded decomposition round with saturation stop; no claim cap before verification; model-free quote-containment + URL-health pass; compact working state in files. **Status:** awaiting user review before implementation.

## 2026-09-02 #28 — Session 1 closed
User paused to read `skill/DESIGN.md` and return with feedback. Points flagged for their attention: verification default (`unverified` vs built-in `refuted`) and budget allocation (fetch pool >= verifier pool). Nothing else pending. Repo clean and pushed.

## 2026-09-03 #29 — Session 2 opened; implementation of `skill/deep-research/` started
**Context:** user asked to continue; no feedback on `skill/DESIGN.md` was recorded, so v1 proceeds as drafted (the two flagged points, `unverified` default and fetch ≥ verify budget, are prompt/preset parameters and cheap to change later).
**Plan for the session:** (1) write binding contracts (`skill/deep-research/reference/contracts.md`: run folder, `sources.json`, `claims.json`, `run.json`, fetch record, CLI of each script, angle-note headings); (2) three Opus subagents in parallel for `scripts/fetch.py`, `scripts/ledger.py`, `scripts/cite_check.py`; (3) main agent writes `SKILL.md`, `prompts/{brief,researcher,verifier,writer}.md`, `adapters/claude-code/README.md`; (4) integration test of the scripts on live URLs; (5) smoke test of the whole workflow.
**Decisions made while implementing (deviations from DESIGN.md, now recorded there):**
- `searcher.md` + `extractor.md` merged into one `researcher.md`: the same agent searches, fetches and extracts for its angle, so pointers never cross an agent boundary (DESIGN phase 3 already allowed this).
- `runmeta.py` folded into `ledger.py init/finalize`.
- Claim labels are **derived** by the ledger from registered evidence (`contradicts` non-empty → contradicted; ≥2 distinct registrable domains among original+supports → corroborated; checked but nothing found → single-source; else unverified). Verifiers register evidence, never labels; two independent verifiers therefore merge naturally at `deep` preset.
- `ledger.py claim add` rejects a quote that is not contained in `raw/<n>.txt` (normalised exact match, or ≥80% of word 6-gram shingles for quotes ≥8 words) at write time, so bad quotes are fixed by the agent that has the page open, not discovered at the end. `cite_check.py` re-checks everything at the end.
- Sources that could not be fetched are still registered (`add-snippet`, `evidence_strength: paraphrase-only`, `quote_safe: false`) so the report can list them as weak evidence; the writer must caveat them.
- Shared `scripts/textmatch.py` (normalise, contains, best_window) written and unit-tested by the main agent.

## 2026-09-03 #30 — Skill implemented: `skill/deep-research/` (scripts, prompts, SKILL.md, adapters); tests pass
**Process note:** all three Opus subagents (fetch.py, ledger.py, cite_check.py) were terminated by API `529 Overloaded`, twice each (six failures, ~15:15-15:40 BST). Rather than keep retrying, the main agent wrote the three scripts itself against the contracts. Recorded in CLAUDE.md as a working rule.
**Delivered (all Python 3.10 stdlib + curl, no keys):**
- `scripts/fetch.py` (~750 lines): the nine-rung chain from `fetch-reliability-survey.md` §4 with the seven-check plausibility gate, robots.txt honoured, cross-process 1 s throttle for archive.org, PDF via `pdftotext`/`pypdf`, Crossref/arXiv/Wikipedia/GitHub/docs-`.md` keyless APIs, Jina, urltomarkdown, Wayback CDX + `id_`, Common Crawl WARC range fetch, `agent-browser` if installed, fabrication check.
- `scripts/ledger.py` (~700 lines): run folder init, `[n]` numbering with URL de-dup, quote check at claim-add time (exit 3 with nearest passage), evidence registration with **derived** labels, `state` for the compact working state (R2), renderers for `sources.md`/`verification.md`, `finalize` → `run.json`, O_EXCL lock + atomic writes (20 concurrent writers: no lost claim).
- `scripts/cite_check.py` (~250 lines): quote containment, `[n]`/range/list citation parsing outside code fences, literal-URL guard, unfetchable/possibly-fabricated/contradicted-without-caveat checks, URL health (HEAD→GET→CDX→DNS), write-back and re-render; exit 1 on errors.
- `scripts/textmatch.py`: normalisation + exact/shingle containment (≥80% of word 6-grams for quotes ≥8 words).
- `SKILL.md` (~1050 words), `prompts/{brief,researcher,verifier,writer}.md`, `reference/contracts.md`, `adapters/{claude-code/README.md,hermes.md,codex.md}`, `tests/{integration.sh,test_cite_check.py}`.
**Live test results (2026-09-03, sequential after fixes):**
| URL | result |
|---|---|
| arxiv.org/abs/1706.03762 | ok, keyless-api (export API + ar5iv), 40.8k chars, published 2017-06-12 |
| en.wikipedia.org/wiki/Transformer_(…) | ok, keyless-api (REST HTML), 110k chars |
| news.ycombinator.com | ok, raw-http, 3.9k |
| doi.org/10.1038/s41586-020-2649-2 | Nature "Client Challenge" block page caught by gate; Jina `AbuseAlleviationError`; no archive; **abstract-only** via Crossref (1.3k chars) |
| reuters.com/technology/ | robots.txt disallows raw fetch; Jina blocked; Wayback snapshot `failed:js-empty` → `skipped-robots` (no false ok) |
| blog.golang.org/go1.11 (soft-404) | raw-http 200 but `failed:length`; **Jina 200** 9.4k chars |
| nytimes.com/…/openai-gpt4-chatgpt.html (real, paywalled) | raw 403; Jina blocked; **Wayback snapshot 2026-02-01**, 11.3k chars, evidence `archived` |
| nytimes.com/…/qzx-fake-article-9182.html (fabricated) | 403 everywhere; CDX 0 captures → `unfetchable`, `no-captures-host-archived (http 403; paywall or bot wall as likely as fabrication)` |
| nonexistent-domain-qzx9182.com/paper | `possibly-fabricated`, `dns-failure` |
| arxiv.org/abs/2410.99999 (fabricated id) | 404 → proxy rungs skipped → `possibly-fabricated`, `no-captures-parent-has-captures` |
| arxiv.org/pdf/1706.03762 | ok, raw-http, pdftotext, 39.9k |
| code.claude.com/docs/en/skills | ok, keyless-api (`.md` sibling), 99k |
**Findings that changed the code (and the contract):**
1. **Jina's Cloudflare front returns 403 to a browser User-Agent sent from a non-browser TLS client** but 200 to an honest tool UA. All service rungs (Jina, urltomarkdown, archive.org, Crossref, arXiv, Wikipedia, Common Crawl) now identify as `deep-research-skill/1.0 (+repo; mailto)`; browser-like headers remain only for direct page reads (survey §2.4 evidence).
2. **CDX `matchType=prefix` now answers `403 This type of CDX query requires authorization`** for at least nytimes.com (it still worked for arxiv.org). Fabrication check falls back to a host-root exact query and only concludes `possibly-fabricated` on DNS failure, on a prefix result, or when the live site said 404/410; a 403 with no captures stays `unfetchable`. Contract §3 step 9 updated.
3. **Reader proxies re-render 404 pages as 200** (fake arXiv id passed the gate via Jina). After a live 404/410 the proxy rungs are skipped.
4. **Block-page markers extended** with `just a moment...`, `client challenge`, `a required part of this site couldn't load`, `are you a robot`, `verify you are human`, `javascript is disabled in your browser`, `please enable cookies`; the page `<title>` is checked too (Nature's 209-char challenge page had passed the length floor).
5. urltomarkdown returned 502/504 on most calls (one 200); kept as best-effort.
6. Parallel processes each throttling archive.org independently caused CDX errors in the first parallel test; the throttle is now a shared mtime stamp in the temp dir.
**Test evidence:** `tests/test_cite_check.py` 2/2 pass (offline: shingle-tolerant quote, paraphrase failure → forced `unverified`, range/list citations, code-fence exclusion, literal URL guard, contradicted-without-caveat, caveated snippet source). `tests/integration.sh` (live) passes end to end: init → add-url ×4 (dedup, unfetchable, snippet) → grade → claim add (accept / reject exit 3) → evidence → corroborated label → render → cite_check (reports the deliberate errors, exit 1) → finalize with health LIVE ×2.
**Next:** smoke-test the full workflow with model agents (generator Sonnet per REQ 4) on 1-2 questions; then Phase 2 pilot.
