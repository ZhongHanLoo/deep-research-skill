# deep-research — file and CLI contracts (v1, 2026-09-03)

This file is the single source of truth for what each script reads and writes. Prompts, scripts and adapters all conform to it. Evidence for the choices is in `skill/DESIGN.md` and `research/literature/*`.

Constraints (REQ 6): Python 3.10+ standard library and `curl` only. Optional accelerators (`pdftotext`, `trafilatura`, `agent-browser`, a browser) are detected at runtime with `shutil.which` / import probes and never required. No API keys. No paywall, login or CAPTCHA circumvention. `robots.txt` honoured by default for scripted fetches.

## 1. Run folder

```
<run>/                         created by `ledger.py init`; default root `research-runs/`, name `<YYYY-MM-DD>-<slug>`
  .gitignore                   contains `raw/`
  00-brief.md                  written by the main agent (prompts/brief.md)
  angles/<angle>.md            one per research agent
  raw/<n>.txt                  raw extracted text for source n (UTF-8); absent when the fetch failed
  raw/<n>.meta.json            full fetch record for source n (see §3)
  sources.json                 machine registry, owned by ledger.py
  claims.json                  claim ledger, owned by ledger.py
  sources.md                   rendered from sources.json by `ledger.py render`
  verification.md              rendered from claims.json by `ledger.py render`
  report.md                    written by the writer agent
  run.json                     created by `ledger.py init`, completed by `ledger.py finalize`
```

All scripts take `--run <dir>` (or env `DEEP_RESEARCH_RUN`). Paths inside JSON files are relative to `<run>`.

Concurrency: several agents append to `sources.json` and `claims.json` at the same time. `ledger.py` must take a cross-process lock (`O_EXCL` lockfile `<run>/.ledger.lock`, stdlib only, retry with backoff up to ~10 s, stale lock older than 60 s is removed) around every read-modify-write.

## 2. `sources.json`

```json
{
  "next_id": 4,
  "sources": [
    {
      "n": 1,
      "url": "https://example.com/article",
      "canonical_url": null,
      "title": "Example article",
      "publisher": "example.com",
      "published": "2025-03-01",
      "accessed": "2026-09-03T14:02:11Z",
      "angle": "market-size",
      "round": 1,
      "status": "ok",
      "fetch_method": "raw-http",
      "http_status": 200,
      "snapshot_date": null,
      "content_type": "text/html",
      "extracted_chars": 8359,
      "gate": "passed",
      "robots": "allowed",
      "evidence_strength": "primary",
      "quote_safe": true,
      "grade": "secondary",
      "health": null,
      "text_path": "raw/1.txt",
      "attempts": [{"method": "raw-http", "result": "200"}],
      "notes": ""
    }
  ]
}
```

Field values:
- `status`: `ok` | `unfetchable` | `possibly-fabricated` | `skipped-robots`
- `fetch_method`: `keyless-api` | `raw-http` | `jina-reader` | `urltomarkdown` | `wayback` | `commoncrawl` | `local-extract` | `headless` | `search-snippet-only` | `none`
- `gate`: `passed` | `failed:length` | `failed:block-page` | `failed:consent-wall` | `failed:js-empty` | `failed:unextracted-pdf` | `failed:word-list` | `not-run`
- `robots`: `allowed` | `disallowed` | `not-checked`
- `evidence_strength`: `primary` (live read of the page) | `archived` (Wayback/Common Crawl/Jina-cached snapshot; `snapshot_date` set) | `paraphrase-only` (only a search snippet or harness summary exists)
- `quote_safe`: true only when `raw/<n>.txt` holds the page's own text (not a summary). Paraphrase-only sources are never quote_safe.
- `grade` (model-assigned source quality, set by the extractor): `primary` | `secondary` | `blog` | `forum` | `unreliable` | null
- `health` (set by cite_check.py): `LIVE` | `DEAD` | `ARCHIVED-ONLY` | `POSSIBLY-FABRICATED` | null
- `published`: ISO date or null. `title`/`publisher` best effort (from `<title>`, `og:site_name`, or host).

`sources.md` rendering (one gap-free numbered list, this exact column order):

```
# Sources

| [n] | Title | Publisher | Published | Accessed | Grade | Fetch | Health | Evidence |
|---|---|---|---|---|---|---|---|---|
| [1] | Example article — https://example.com/article | example.com | 2025-03-01 | 2026-09-03 | secondary | raw-http | LIVE | primary |
```
Rows with `status != ok` still appear, with Fetch = `UNFETCHABLE` / `POSSIBLY-FABRICATED` / `SKIPPED-ROBOTS` and the last attempt result in a trailing `Notes` column.

## 3. `raw/<n>.meta.json` = output of `fetch.py`

`fetch.py <url> [--out PATH] [--id N] [--ignore-robots] [--fresh] [--timeout S] [--max-bytes B] [--json]` prints one JSON object to stdout and, if `--out` is given, writes the extracted text there.

```json
{
  "url": "...", "final_url": "...", "canonical_url": null, "title": "...",
  "status": "ok", "fetch_method": "raw-http", "http_status": 200,
  "content_type": "text/html", "accessed": "2026-09-03T14:02:11Z",
  "snapshot_date": null, "extracted_chars": 8359, "gate": "passed",
  "robots": "allowed", "evidence_strength": "primary", "quote_safe": true,
  "published": "2025-03-01", "publisher": "example.com",
  "attempts": [{"method": "keyless-api", "result": "no matching shape"}, {"method": "raw-http", "result": "200"}],
  "text_path": "raw/1.txt",
  "fabrication_check": null
}
```

Chain order (fetch-reliability-survey §4.1 / "Recommended fallback chain"), each rung records one `attempts` entry:
1. `keyless-api`: DOI → `api.crossref.org/works/<doi>` (metadata + abstract) ; arXiv id → `export.arxiv.org/api/query?id_list=` for metadata and `ar5iv.labs.arxiv.org/html/<id>` for full text; Wikipedia → `en.wikipedia.org/api/rest_v1/page/summary/<title>` then the `?action=raw`-free HTML page via normal fetch; docs sites → try `<url>.md` and `/llms.txt` only when the URL looks like a docs page. GitHub → `gh` CLI if present else fall through. Skip rung if no shape matches.
2. (harness WebFetch is NOT used by the script; the prompt layer may use it for discovery only.)
3. `raw-http`: HEAD then GET with browser-like `User-Agent`, `Accept`, `Accept-Language: en-US,en;q=0.9`; follow redirects; 25 s timeout; 10 MB cap; robots.txt checked first (cache per host; on fetch error treat as allowed); one backoff retry on 429/5xx only. PDFs (content-type or `%PDF-` sniff) go to local extraction (`pdftotext` → `pypdf` → give up → `failed:unextracted-pdf`). HTML → text via stdlib `html.parser` extraction: drop script/style/nav/header/footer/aside/noscript, keep block structure as newlines, decode entities, collapse whitespace. Use `trafilatura` if importable.
4. `jina-reader`: `GET https://r.jina.ai/<url>` with `Accept: text/plain`, plus `x-no-cache: true` when `--fresh`. Detect `AbuseAlleviationError`, 429, cached-snapshot warning (→ `evidence_strength: archived`, snapshot_date from the warning if parseable else accessed date).
5. `urltomarkdown`: `GET https://urltomarkdown.herokuapp.com/?url=<url>`; best effort.
6. `wayback`: CDX `https://web.archive.org/cdx/search/cdx?url=<exact>&output=json&limit=1&fl=timestamp,statuscode&filter=statuscode:200&from=2015` (self-throttle ≥1 s between archive.org requests), then `https://web.archive.org/web/<ts>id_/<url>`; then `commoncrawl` (`index.commoncrawl.org/collinfo.json` newest index → `?url=<url>&output=json` → WARC `Range:` fetch → gunzip → strip WARC/HTTP headers).
7. `local-extract`: applies whenever a rung produced bytes on disk that are PDF or HTML (already part of rung 3/6 handling).
8. `headless`: only if `agent-browser` is on PATH (`agent-browser read <url>`); otherwise skipped with attempt result `not installed`.
9. `UNFETCHABLE` + fabrication check: DNS failure → `status: possibly-fabricated`, `fabrication_check: "dns-failure"`; else CDX exact ≥1 capture → real but blocked (already handled by rung 6 if a 2xx capture existed) → `status: unfetchable`; else CDX `[]` and Common Crawl no hit and CDX prefix query on parent path has captures → `status: possibly-fabricated`, `fabrication_check: "no-captures-parent-has-captures"`; otherwise `status: unfetchable`, `fabrication_check: "inconclusive"`. **Observed 2026-09-03:** CDX `matchType=prefix` returns `403 This type of CDX query requires authorization`, so the implementation falls back to an exact query on the host root; with the host archived but the leaf uncaptured it returns `possibly-fabricated` only when the live site answered 404/410 (`no-captures-host-archived`), and `unfetchable` on 401/403 (a paywall or bot wall is as likely as fabrication). The same 404/410 condition applies to the parent-prefix result: on 2026-09-03 a real, robots-excluded NEJM article (403 live, zero captures, parent path captured) would otherwise have been flagged.

Plausibility gate (survey §4.2) is applied to every rung's text: length < 200 chars → `failed:length`; block-page markers in first 5000 chars (`attention required! | cloudflare`, `sorry, you have been blocked`, `please verify you are a human`, `checking your browser`, `anubis uses a proof-of-work scheme`, `enable javascript and cookies`, `access denied`, `request blocked`) → `failed:block-page`; consent markers dominating (`before you continue`, `we use cookies and data`, `manage your privacy settings`, `accept all cookies` and text < 1500 chars) → `failed:consent-wall`; text:HTML ratio < 1.5% when HTML ≥ 20 kB → `failed:js-empty`; `%PDF-` prefix or ≥2 of `endobj|endstream|/FlateDecode|xref|trailer` → `failed:unextracted-pdf`; ≥200 000 chars with < 1 sentence terminator per 5000 chars → `failed:word-list`; > 5% replacement/control characters in the first 5000 chars → `failed:binary` (added 2026-09-03: undecoded gzip bodies from Wayback passed the gate). A failed gate advances the chain; the reason is recorded in `attempts`.

Exit code 0 on `ok`, 1 on `unfetchable`/`possibly-fabricated`/`skipped-robots`, 2 on usage error. Always print the JSON.

## 4. `claims.json`

```json
{
  "next_id": 3,
  "claims": [
    {
      "id": "c001",
      "text": "The global market was USD 4.2 billion in 2024.",
      "quote": "the global market reached USD 4.2 billion in 2024",
      "source": 1,
      "angle": "market-size",
      "round": 1,
      "importance": "central",
      "checked": false,
      "supports": [],
      "contradicts": [],
      "label": "unverified",
      "quote_verified": true,
      "notes": [],
      "created": "2026-09-03T14:05:00Z"
    }
  ]
}
```

- `importance`: `central` | `supporting` | `tangential` (extractor's judgment relative to the research question). Claims are atomic: one fact, ≤25 words; several claims may share one quote.
- `checked` with a note starting `quote-check:` means the claim was quote-checked only (no search); it stays `single-source`.
- `supports` / `contradicts`: lists of `{"source": n, "note": "...", "by": "<agent label>"}` added by verifiers. Union semantics: two verifiers can add independently.
- `checked`: true once any verifier has finished looking at the claim (set by `claim checked` or by any `claim evidence` call).
- `quote_verified`: true | false | null (null when the source is not quote_safe, so no check is possible).
- **`label` is derived, never set directly:**
  - `contradicted` if `contradicts` is non-empty
  - else `corroborated` if the set of distinct registrable hosts among {original source} ∪ `supports` has size ≥ 2
  - else `single-source` if `checked` is true
  - else `unverified`
  - Additionally, if `quote_verified` is `false`, the label is forced to `unverified` and a note `quote-not-in-source` is appended (cite_check.py sets this).
- Host independence: two sources count as independent when their registrable domains differ (compare `eTLD+1` approximated as last two labels, three for `co.uk`-style suffixes), **except on repository and publisher hosts** (PubMed/PMC, arXiv, DOI, major journal publishers, GitHub, Medium-style platforms; list `REPOSITORY_HOSTS` in `ledger.py`) where each distinct URL counts as its own source, and **except when the URL identifies the work itself** (RFC number on rfc-editor/datatracker/ietf/httpwg, DOI, arXiv id, PubMed/PMC id): then the work id is the key, so mirrors never corroborate each other. Added 2026-09-03 after the smoke test left two claims `single-source` although an independent paper on the same host supported them. The same paper mirrored on two hosts is still double-counted; the verifier prompt tells verifiers not to register mirrors as support.

`verification.md` rendering: sections in order `Contradicted`, `Corroborated`, `Single-source`, `Unverified`; each claim as `- **c001** (central, [1]) text — quote: "…" — supports: [3],[7] — contradicts: — notes`. Header line gives counts per label and per importance.

## 5. `ledger.py` CLI

All subcommands: `ledger.py --run DIR <cmd> ...`; output JSON to stdout unless `--format md`.

| Command | Effect |
|---|---|
| `init --question Q [--slug S] [--preset quick\|standard\|deep] [--mode brief\|report] [--root DIR]` | Creates the run folder, `.gitignore`, empty `sources.json`/`claims.json`, `run.json` with `started`, `question`, `preset`, `mode`. Prints `{"run": path}`. If `--run` is given, uses it as the folder. |
| `add-url URL [--angle A] [--round R] [--title T] [--ignore-robots] [--fresh]` | Assigns the next `n`, runs `fetch.py` (same directory, via `subprocess`), stores `raw/<n>.txt` + `raw/<n>.meta.json`, appends the row. If the URL (normalised: lowercase host, strip `www.`, strip fragment, strip trailing slash, strip `utm_*`) already exists, returns the existing row without refetching. Prints `{n, status, text_path, extracted_chars, evidence_strength, quote_safe, fetch_method, title, published}`. |
| `refetch N [--ignore-robots] [--fresh] [--keep-title]` | Re-runs the fetch chain for an existing source and rewrites its row (grade kept); removes `raw/<n>.txt` if the refetch fails. For re-audits and after fetch fixes. |
| `add-snippet URL --snippet TEXT [--angle A] [--title T]` | Registers a `search-snippet-only` source (`evidence_strength: paraphrase-only`, `quote_safe: false`, `status: unfetchable`) for pointers that could not be fetched but must be listed. |
| `grade N --grade G [--published DATE] [--publisher P]` | Sets the model-assigned grade and optional metadata. |
| `claim add --source N --angle A --text T --quote Q --importance I [--round R]` | Checks the quote against `raw/<N>.txt` with `textmatch.contains(quote, text)` when the source is quote_safe. If not contained: exit 3, nothing written, message `quote not found in raw/N.txt; copy the sentence verbatim`. If contained (or source not quote_safe → `quote_verified: null`), appends and prints the claim. |
| `claim add --from-json FILE` | Same for a JSON array of `{source, angle, text, quote, importance}`; validates all, writes the valid ones, reports rejected ones by index; exit 3 if any were rejected. |
| `claim evidence ID (--supports N \| --contradicts N) [--note TEXT] [--by LABEL]` | Appends evidence; sets `checked`; recomputes label. |
| `claim checked ID [--note TEXT] [--by LABEL]` | Marks looked-at with no evidence found; recomputes label. |
| `claim note ID --note TEXT` | Appends a note. |
| `claims list [--label L] [--importance I] [--angle A] [--round R] [--unchecked] [--format json\|md]` | Lists claims. `md` format is what the writer and verifiers read: `- c001 [central] [1] text — "quote" (label; supports [3]; contradicts [])`. |
| `state [--format md]` | Compact working state for the main agent (R2): question and preset from run.json; counts of sources by status and by fetch_method; counts of claims by label and by importance; per-round counts of central claims; the list of central claims (id, text, source, label); list of `unfetchable`/`possibly-fabricated` URLs. Under ~120 lines. |
| `render` | Writes `sources.md` and `verification.md`. |
| `finalize [--harness H] [--model M] [--agents N] [--rounds R] [--execution parallel\|sequential] [--tokens T]` | Completes `run.json`: `finished`, `wall_clock_s`, counts (sources by status/method, claims by label/importance, quote_verified counts, health counts), and the given metadata. Also calls `render`. |

## 6. `run.json`

```json
{
  "skill": "deep-research", "skill_version": "1.0.0",
  "question": "...", "slug": "...", "preset": "standard", "mode": "report",
  "started": "...", "finished": "...", "wall_clock_s": 1234,
  "harness": "claude-code", "model": "claude-sonnet-5", "agents": 5, "rounds": 2, "execution": "parallel",
  "tokens": null,
  "sources": {"total": 18, "ok": 15, "unfetchable": 2, "possibly_fabricated": 1, "skipped_robots": 0, "by_method": {"raw-http": 11, "jina-reader": 3, "wayback": 1}},
  "claims": {"total": 41, "by_label": {"corroborated": 20, "single-source": 12, "contradicted": 3, "unverified": 6}, "by_importance": {"central": 15, "supporting": 20, "tangential": 6}, "quote_verified": 38, "quote_failed": 1, "quote_unknown": 2},
  "health": {"LIVE": 14, "DEAD": 1, "ARCHIVED-ONLY": 2, "POSSIBLY-FABRICATED": 1}
}
```

## 7. `cite_check.py`

`cite_check.py --run DIR [--no-network] [--format md|json]`

1. **Quote containment**: for every claim whose source is `quote_safe`, run `textmatch.contains(quote, raw_text)`; set `quote_verified`; on false, force label `unverified` and add note `quote-not-in-source`. Report each failure with the claim id and the nearest matching passage (`textmatch.best_window`) so the writer/extractor can fix the quote.
2. **Citation integrity in `report.md`**: every `[n]` (also ranges/lists like `[3, 5]` and `[3][5]`) must exist in `sources.json`; report unknown numbers. Report sources with `status != ok` that are cited (allowed only when the report marks them as archived/paraphrase). Report claims labelled `contradicted` whose source is cited without the word "contradicted" or "disputed" within the same paragraph (warning only). Report any URL appearing literally in `report.md` that is not in `sources.json` (fabricated-citation guard).
2b. **Citation tracing**: the writer ends each cited sentence or table row with `<!-- cNNN [cMMM …] -->`. For each marker, the segment of the paragraph since the previous marker is checked: every `[n]` in it must be the own source of one named claim or a source in that claim's `supports`/`contradicts`; otherwise `citation-not-traced` (error). A marker naming an unknown id → `unknown-claim-id` (error). A cited segment with no marker → `citation-without-claim-marker` (warning). Added 2026-09-03 (decision in progress.md #32).
2c. **Coverage**: central claims labelled `corroborated` or `single-source` whose id appears in no marker are listed as `central-claim-unused` (info) and counted in the summary (added 2026-09-03 after the Stage B judge failed two rubric items whose facts were in the ledger).
2d. **Length**: words before `## Sources` (markers stripped) vs the preset/mode target from `run.json` (report: quick 600 / standard 1500 / deep 3000; brief 300); over target → `over-target` warning; over 120% of target → `over-length` error (added 2026-09-03: writers overshot by up to 70% and their self-reported counts were wrong).
3. **URL health** (skipped with `--no-network`): for each source with `status == ok` or cited in the report: HEAD (fallback GET, 15 s) → 2xx/3xx = `LIVE`; 4xx/5xx/timeout → CDX exact query; ≥1 capture → `ARCHIVED-ONLY`; no capture and DNS failure → `POSSIBLY-FABRICATED`; no capture otherwise → `DEAD`. Sources whose `fetch_method` is already `wayback`/`commoncrawl` are `ARCHIVED-ONLY` unless HEAD is 2xx. Throttle archive.org ≥1 s.
4. Writes results back to `sources.json`/`claims.json` (through ledger's lock) and re-renders `sources.md`/`verification.md`.
5. Prints a summary: counts, then a bullet list of actionable problems. Exit 0 when no problems, 1 when there are.

## 8. `textmatch.py` (shared, written by the project lead)

- `normalize(s) -> str`: NFKC, lowercase, curly quotes/dashes/ellipsis to ASCII, remove soft hyphens, collapse whitespace, strip leading/trailing punctuation.
- `contains(quote, text) -> bool`: exact normalised substring, else shingle fallback: word 6-grams of the quote, true if ≥ 80% present in normalised text and quote has ≥ 8 words.
- `best_window(quote, text, width=300) -> str`: the window of `text` around the highest-overlap position, for diagnostics.

## 9. Angle note `angles/<angle>.md` (written by research agents; free-form Markdown but with these headings)

```
# Angle: <label>
Hypothesis: … / Would disconfirm: …
## Queries issued
- `query` → k results
## Pointers (not evidence)
- [title](url) — why relevant
## Sources fetched
- [n] title — status, method, grade
## Claims extracted
- c012 (central) text
## Gaps / suggested sub-questions
- …
```
