# Prior art (baselines)

Descriptions only. Third-party code is not redistributed in this repository; local working copies are gitignored.

## 1. Claude Code built-in `/deep-research` workflow
- **Observed:** 2026-09-02, Claude Code 2.1.258 (bundled Workflow named `deep-research`).
- **Scope:** web research only. Source comment: "Ported from bughunter architecture. WebSearch/WebFetch instead of git/grep."
- **Pipeline:** Scope (decompose question into 3-6 angles; ask 2-3 clarifying questions first if underspecified) -> Search (one parallel WebSearch agent per angle) -> URL-dedup -> Fetch+Extract (top 15 sources; extract falsifiable claims, each with a direct quote and a source-quality grade) -> Verify (3 adversarial votes per claim; 2/3 refutations drop it; max 25 claims; uncheckable claims labelled "unverified") -> Synthesize (merge semantic duplicates, rank by confidence, cite sources; note claims killed in verification).
- **Constants:** VOTES_PER_CLAIM=3, REFUTATIONS_REQUIRED=2, MAX_FETCH=15, MAX_VERIFY_CLAIMS=25.
- **Behaviour changes noted in the changelog:** 2.1.197 verifier failures reported as `unverified` rather than "all claims refuted"; 2.1.207 Fetch-phase agent chips show hostname; 2.1.218 runs only when invoked manually.
- **Output:** one cited report delivered into the session; per-agent results visible in `/workflows`; the orchestration script is written to disk.
- **Role here:** primary baseline for the pilot comparison.

## 2. Hermes Agent `grounded-citations` skill
- **Source:** https://github.com/NousResearch/hermes-agent (bundled skill `research/grounded-citations`, v1.1.0, MIT, by Hermes Agent + Teknium). Observed locally 2026-09-02.
- **Idea:** a ledger script owns the `url -> [n]` mapping so citation numbers come from retrieval, never model memory; verbatim quotes are rejected unless they literally appear in the fetched page text; model-knowledge claims are flagged `[unverified]`; `verify --evidence` fails drafts whose cited sources carry no evidence.
- **Role here:** design reference for the source registry, claim ledger and quote verification.

See `research/literature/output-formats-survey.md` for 17 further systems compared (OpenAI, Gemini, Perplexity, Anthropic, STORM, GPT Researcher, LangChain Open Deep Research, and others).
