#!/usr/bin/env python3
"""Run ledger for the deep-research skill (stdlib only).

Owns the numbering of sources ([n]) and claims (c001...) for one run folder,
so the model never invents a citation number, and owns the quote check at
claim-registration time, so a quote that is not in the fetched text is
rejected by the agent that still has the page open.

Contract: skill/deep-research/reference/contracts.md (sections 1, 2, 4, 5, 6).

  ledger.py --run DIR init --question Q [--slug S] [--preset P] [--mode M] [--root DIR]
  ledger.py --run DIR add-url URL [--angle A] [--round R] [--title T] [--ignore-robots] [--fresh]
  ledger.py --run DIR refetch N [--ignore-robots] [--fresh] [--keep-title]
  ledger.py --run DIR add-snippet URL --snippet TEXT [--angle A] [--title T]
  ledger.py --run DIR grade N --grade G [--published DATE] [--publisher P]
  ledger.py --run DIR claim add --source N --angle A --text T --quote Q --importance I [--round R]
  ledger.py --run DIR claim add --from-json FILE
  ledger.py --run DIR claim evidence ID (--supports N | --contradicts N) [--note TEXT] [--by LABEL]
  ledger.py --run DIR claim checked ID [--note TEXT] [--by LABEL]
  ledger.py --run DIR claim note ID --note TEXT
  ledger.py --run DIR claims list [--label L] [--importance I] [--angle A] [--round R] [--unchecked] [--format json|md]
  ledger.py --run DIR state [--format json|md]
  ledger.py --run DIR render
  ledger.py --run DIR finalize [--harness H] [--model M] [--agents N] [--rounds R] [--execution E] [--tokens T]

`--run` may be replaced by the environment variable DEEP_RESEARCH_RUN.
Exit codes: 0 ok; 1 the underlying fetch failed (add-url) or a problem was
reported; 2 usage / validation error; 3 quote not found in the source text.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import textmatch  # noqa: E402

SKILL_VERSION = "1.0.0"
IMPORTANCE = ("central", "supporting", "tangential")
GRADES = ("primary", "secondary", "blog", "forum", "unreliable")
LABELS = ("contradicted", "corroborated", "single-source", "unverified")
TWO_LEVEL_SUFFIXES = {"co.uk", "ac.uk", "org.uk", "gov.uk", "com.au", "co.jp", "co.nz", "com.br", "co.za"}
# Hosts that aggregate many independent works: two different URLs there are two sources,
# not one (a PubMed abstract and a PMC article of *different* papers are independent;
# the same paper mirrored on both is not, and that is left to the verifier's judgment).
REPOSITORY_HOSTS = ("ncbi.nlm.nih.gov", "europepmc.org", "arxiv.org", "ar5iv.labs.arxiv.org", "doi.org", "semanticscholar.org",
                    "researchgate.net", "biorxiv.org", "medrxiv.org", "ssrn.com", "jstor.org", "sciencedirect.com",
                    "springer.com", "wiley.com", "nature.com", "science.org", "cell.com", "thelancet.com", "bmj.com",
                    "jamanetwork.com", "nejm.org", "tandfonline.com", "sagepub.com", "oup.com", "academic.oup.com",
                    "cambridge.org", "mdpi.com", "frontiersin.org", "plos.org", "web.archive.org", "github.com",
                    "medium.com", "substack.com", "wordpress.com", "blogspot.com")


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def normalize_url(url: str) -> str:
    """Identity key for de-duplication: lowercase host, strip www., fragment,
    trailing slash and utm_* parameters."""
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return url.strip().lower()
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if p.port and not ((p.scheme == "http" and p.port == 80) or (p.scheme == "https" and p.port == 443)):
        host = f"{host}:{p.port}"
    path = re.sub(r"/+$", "", p.path) or ""
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((p.scheme.lower() or "https", host, path, urlencode(q), ""))


def host_of(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def registrable_domain(host: str) -> str:
    host = (host or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    if ".".join(labels[-2:]) in TWO_LEVEL_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def slugify(text: str, max_words: int = 6, max_len: int = 48) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "a", "an", "of", "in", "on", "for", "to", "and", "is", "are", "what", "how", "does", "do", "did", "with", "by"}
    words = [w for w in words if w not in stop] or words
    slug = "-".join(words[:max_words])
    return slug[:max_len].rstrip("-") or "run"


# ----------------------------------------------------------------------------
# lock + atomic json
# ----------------------------------------------------------------------------

class Lock:
    """Cross-process lock: O_EXCL lockfile, retry up to ~10 s, stale after 60 s."""

    def __init__(self, run: Path, timeout: float = 10.0, stale: float = 60.0):
        self.path = run / ".ledger.lock"
        self.timeout = timeout
        self.stale = stale
        self.fd = None

    def __enter__(self):
        deadline = time.time() + self.timeout
        delay = 0.05
        while True:
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise TimeoutError(f"could not acquire {self.path} within {self.timeout}s")
                time.sleep(delay)
                delay = min(delay * 1.7, 0.5)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def read_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, data) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ----------------------------------------------------------------------------
# run folder access
# ----------------------------------------------------------------------------

class Run:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.sources_path = self.path / "sources.json"
        self.claims_path = self.path / "claims.json"
        self.run_path = self.path / "run.json"

    def require(self) -> "Run":
        if not self.sources_path.exists() or not self.claims_path.exists():
            die(f"not a run folder (missing sources.json/claims.json): {self.path}")
        return self

    def lock(self) -> Lock:
        return Lock(self.path)

    def sources(self) -> dict:
        return read_json(self.sources_path, {"next_id": 1, "sources": []})

    def claims(self) -> dict:
        return read_json(self.claims_path, {"next_id": 1, "claims": []})

    def meta(self) -> dict:
        return read_json(self.run_path, {})

    def save_sources(self, data: dict) -> None:
        write_json_atomic(self.sources_path, data)

    def save_claims(self, data: dict) -> None:
        recompute_labels(data["claims"], {s["n"]: s for s in self.sources()["sources"]})
        write_json_atomic(self.claims_path, data)

    def source_by_n(self, n: int):
        for s in self.sources()["sources"]:
            if s["n"] == n:
                return s
        return None

    def raw_text(self, src: dict) -> str | None:
        tp = src.get("text_path")
        if not tp:
            return None
        p = self.path / tp
        if not p.exists():
            return None
        return p.read_text(encoding="utf-8", errors="replace")


# ----------------------------------------------------------------------------
# label derivation (contract §4)
# ----------------------------------------------------------------------------

def independence_key(url: str) -> str:
    """Two sources are independent when their keys differ: the registrable domain,
    except on repository/publisher hosts where each distinct URL is its own work."""
    host = host_of(url)
    dom = registrable_domain(host)
    if any(host == h or host.endswith("." + h) or dom == h for h in REPOSITORY_HOSTS):
        return normalize_url(url)
    return dom


def derive_label(claim: dict, sources_by_n: dict) -> str:
    if claim.get("quote_verified") is False:
        return "unverified"
    if claim.get("contradicts"):
        return "contradicted"
    hosts = set()
    orig = sources_by_n.get(claim.get("source"))
    if orig:
        hosts.add(independence_key(orig.get("url", "")))
    for ev in claim.get("supports", []):
        s = sources_by_n.get(ev.get("source"))
        if s:
            hosts.add(independence_key(s.get("url", "")))
    hosts.discard("")
    if len(hosts) >= 2:
        return "corroborated"
    if claim.get("checked"):
        return "single-source"
    return "unverified"


def recompute_labels(claims: list, sources_by_n: dict) -> None:
    for c in claims:
        c["label"] = derive_label(c, sources_by_n)
        if c.get("quote_verified") is False and "quote-not-in-source" not in c.setdefault("notes", []):
            c["notes"].append("quote-not-in-source")


# ----------------------------------------------------------------------------
# commands
# ----------------------------------------------------------------------------

def cmd_init(args) -> None:
    if args.run:
        run_dir = Path(args.run)
        slug = args.slug or run_dir.name
    else:
        slug = args.slug or slugify(args.question)
        run_dir = Path(args.root) / f"{_dt.date.today().isoformat()}-{slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "angles").mkdir(exist_ok=True)
    gi = run_dir / ".gitignore"
    if not gi.exists():
        gi.write_text("raw/\n.ledger.lock\n", encoding="utf-8")
    run = Run(run_dir)
    if not run.sources_path.exists():
        write_json_atomic(run.sources_path, {"next_id": 1, "sources": []})
    if not run.claims_path.exists():
        write_json_atomic(run.claims_path, {"next_id": 1, "claims": []})
    meta = run.meta()
    meta.update({
        "skill": "deep-research", "skill_version": SKILL_VERSION,
        "question": args.question, "slug": slug, "preset": args.preset, "mode": args.mode,
        "started": meta.get("started") or now_iso(),
    })
    write_json_atomic(run.run_path, meta)
    out({"run": str(run_dir.resolve()), "slug": slug, "preset": args.preset, "mode": args.mode})


def _find_existing(sources: list, url: str):
    key = normalize_url(url)
    for s in sources:
        if normalize_url(s.get("url", "")) == key:
            return s
    return None


def _summary(row: dict, duplicate: bool = False) -> dict:
    d = {k: row.get(k) for k in ("n", "status", "text_path", "extracted_chars", "evidence_strength",
                                  "quote_safe", "fetch_method", "title", "published", "snapshot_date", "url")}
    if duplicate:
        d["duplicate"] = True
    if row.get("notes"):
        d["notes"] = row["notes"]
    return d


def _new_row(n: int, url: str, angle: str | None, rnd: int, title: str | None) -> dict:
    return {
        "n": n, "url": url, "canonical_url": None, "title": title, "publisher": host_of(url) or None,
        "published": None, "accessed": now_iso(), "angle": angle, "round": rnd,
        "status": "pending", "fetch_method": "none", "http_status": None, "snapshot_date": None,
        "content_type": None, "extracted_chars": 0, "gate": "not-run", "robots": "not-checked",
        "evidence_strength": "paraphrase-only", "quote_safe": False, "grade": None, "health": None,
        "text_path": None, "attempts": [], "notes": "",
    }


def _fetch_script() -> Path:
    env = os.environ.get("DEEP_RESEARCH_FETCH")
    return Path(env) if env else Path(__file__).resolve().parent / "fetch.py"


def _run_fetch(run: Run, url: str, n: int, ignore_robots: bool, fresh: bool) -> tuple[dict | None, str]:
    script = _fetch_script()
    out_path = run.path / "raw" / f"{n}.txt"
    cmd = [sys.executable, str(script), url, "--out", str(out_path), "--id", str(n), "--json"]
    if ignore_robots:
        cmd.append("--ignore-robots")
    if fresh:
        cmd.append("--fresh")
    if not script.exists():
        return None, f"fetch script not found: {script}"
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, "fetch.py timed out after 600 s"
    except OSError as e:
        return None, f"could not run fetch.py: {e.__class__.__name__}: {e}"
    stdout = proc.stdout or ""
    text = stdout.split("\n-----TEXT-----\n", 1)[0].strip()
    try:
        rec = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                rec = json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                rec = None
        else:
            rec = None
    if rec is None:
        err = (proc.stderr or "").strip().splitlines()
        return None, f"fetch.py exit {proc.returncode}, no JSON record" + (f": {err[-1]}" if err else "")
    return rec, ""


def _apply_fetch_record(row: dict, rec: dict, run: Run, n: int, title_override: str | None) -> None:
    for k in ("canonical_url", "published", "accessed", "status", "fetch_method", "http_status",
              "snapshot_date", "content_type", "extracted_chars", "gate", "robots",
              "evidence_strength", "quote_safe", "attempts"):
        if k in rec and rec[k] is not None:
            row[k] = rec[k]
    row["title"] = title_override or rec.get("title") or row.get("title")
    row["publisher"] = rec.get("publisher") or row.get("publisher")
    row["accessed"] = rec.get("accessed") or row["accessed"]
    if rec.get("status") == "ok" and (run.path / "raw" / f"{n}.txt").exists():
        row["text_path"] = f"raw/{n}.txt"
    else:
        row["text_path"] = None
        row["quote_safe"] = False
    notes = []
    if rec.get("fabrication_check"):
        notes.append(f"fabrication_check: {rec['fabrication_check']}")
    if rec.get("status") != "ok" and rec.get("attempts"):
        real = [a for a in rec["attempts"] if a.get("method") != "fabrication-check" and not str(a.get("result", "")).startswith("skipped")]
        if real:
            last = real[-1]
            notes.append(f"last attempt: {last.get('method')}: {last.get('result')}")
    row["notes"] = "; ".join(notes)
    if row.get("status") in (None, "pending"):
        row["status"] = "unfetchable"


def cmd_add_url(args) -> None:
    run = Run(args.run).require()
    url = args.url.strip()
    if not re.match(r"^https?://", url, re.I):
        die(f"not an http(s) URL: {url}")
    with run.lock():
        data = run.sources()
        existing = _find_existing(data["sources"], url)
        if existing:
            out(_summary(existing, duplicate=True))
            return
        n = data["next_id"]
        data["next_id"] = n + 1
        row = _new_row(n, url, args.angle, args.round, args.title)
        data["sources"].append(row)
        run.save_sources(data)
    rec, err = _run_fetch(run, url, n, args.ignore_robots, args.fresh)
    with run.lock():
        data = run.sources()
        row = next(s for s in data["sources"] if s["n"] == n)
        if rec is None:
            row.update({"status": "unfetchable", "fetch_method": "none", "quote_safe": False,
                        "attempts": [{"method": "none", "result": err}], "notes": err})
        else:
            (run.path / "raw" / f"{n}.meta.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            _apply_fetch_record(row, rec, run, n, args.title)
        run.save_sources(data)
    out(_summary(row))
    sys.exit(0 if row["status"] == "ok" else 1)


def cmd_refetch(args) -> None:
    """Re-run the fetch chain for an existing source (after a fetch.py fix or for a re-audit)."""
    run = Run(args.run).require()
    row = run.source_by_n(args.n)
    if not row:
        die(f"no source [{args.n}]")
    rec, err = _run_fetch(run, row["url"], args.n, args.ignore_robots, args.fresh)
    with run.lock():
        data = run.sources()
        row = next(s for s in data["sources"] if s["n"] == args.n)
        keep_grade = row.get("grade")
        if rec is None:
            row.update({"status": "unfetchable", "fetch_method": "none", "quote_safe": False, "text_path": None,
                        "attempts": [{"method": "none", "result": err}], "notes": err})
        else:
            (run.path / "raw" / f"{args.n}.meta.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            _apply_fetch_record(row, rec, run, args.n, row.get("title") if args.keep_title else None)
            if rec.get("status") != "ok":
                try:
                    (run.path / "raw" / f"{args.n}.txt").unlink()
                except FileNotFoundError:
                    pass
        row["grade"] = keep_grade
        run.save_sources(data)
        cdata = run.claims()
        run.save_claims(cdata)  # labels may change if quote_safe changed
    out(_summary(row))
    sys.exit(0 if row["status"] == "ok" else 1)


def cmd_add_snippet(args) -> None:
    run = Run(args.run).require()
    url = args.url.strip()
    with run.lock():
        data = run.sources()
        existing = _find_existing(data["sources"], url)
        if existing:
            out(_summary(existing, duplicate=True))
            return
        n = data["next_id"]
        data["next_id"] = n + 1
        row = _new_row(n, url, args.angle, args.round, args.title)
        row.update({"status": "unfetchable", "fetch_method": "search-snippet-only", "gate": "not-run",
                    "evidence_strength": "paraphrase-only", "quote_safe": False,
                    "attempts": [{"method": "search-snippet-only", "result": "registered from search result"}],
                    "notes": "snippet: " + args.snippet.strip()})
        data["sources"].append(row)
        run.save_sources(data)
    out(_summary(row))


def cmd_grade(args) -> None:
    run = Run(args.run).require()
    if args.grade not in GRADES:
        die(f"grade must be one of {GRADES}")
    with run.lock():
        data = run.sources()
        row = next((s for s in data["sources"] if s["n"] == args.n), None)
        if not row:
            die(f"no source [{args.n}]")
        row["grade"] = args.grade
        if args.published:
            row["published"] = args.published
        if args.publisher:
            row["publisher"] = args.publisher
        run.save_sources(data)
    out({"n": row["n"], "grade": row["grade"], "published": row["published"], "publisher": row["publisher"]})


def _validate_claim(run: Run, sources_by_n: dict, item: dict) -> tuple[dict | None, str | None, str | None]:
    """Returns (claim, reason, nearest). reason None means valid."""
    try:
        n = int(item.get("source"))
    except (TypeError, ValueError):
        return None, "source must be an integer", None
    src = sources_by_n.get(n)
    if not src:
        return None, f"no source [{n}]", None
    text = (item.get("text") or "").strip()
    quote = (item.get("quote") or "").strip()
    imp = (item.get("importance") or "").strip()
    angle = (item.get("angle") or src.get("angle") or "").strip()
    if not text:
        return None, "text is empty", None
    if not quote:
        return None, "quote is empty", None
    if imp not in IMPORTANCE:
        return None, f"importance must be one of {IMPORTANCE}", None
    quote_verified = None
    if src.get("quote_safe"):
        raw = run.raw_text(src)
        if raw is None:
            return None, f"source [{n}] is quote_safe but {src.get('text_path')} is missing", None
        if not textmatch.contains(quote, raw):
            return None, f"quote not found in {src.get('text_path')}; copy the sentence verbatim", textmatch.best_window(quote, raw)
        quote_verified = True
    rnd = item.get("round") or src.get("round") or 1
    claim = {
        "id": None, "text": text, "quote": quote, "source": n, "angle": angle, "round": int(rnd),
        "importance": imp, "checked": False, "supports": [], "contradicts": [], "label": "unverified",
        "quote_verified": quote_verified, "notes": [], "created": now_iso(),
    }
    return claim, None, None


def cmd_claim_add(args) -> None:
    run = Run(args.run).require()
    if args.from_json:
        try:
            items = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            die(f"cannot read {args.from_json}: {e}")
        if not isinstance(items, list):
            die("--from-json must contain a JSON array")
    else:
        if not (args.source and args.text and args.quote and args.importance):
            die("claim add needs --source, --text, --quote, --importance (or --from-json FILE)")
        items = [{"source": args.source, "angle": args.angle, "text": args.text, "quote": args.quote,
                  "importance": args.importance, "round": args.round}]
    sources_by_n = {s["n"]: s for s in run.sources()["sources"]}
    valid, rejected = [], []
    for i, item in enumerate(items):
        claim, reason, nearest = _validate_claim(run, sources_by_n, item if isinstance(item, dict) else {})
        if claim:
            valid.append(claim)
        else:
            rejected.append({"index": i, "reason": reason, "nearest": nearest, "text": (item.get("text") if isinstance(item, dict) else None)})
    if valid:
        with run.lock():
            data = run.claims()
            for c in valid:
                c["id"] = f"c{data['next_id']:03d}"
                data["next_id"] += 1
                data["claims"].append(c)
            run.save_claims(data)
    if args.from_json:
        out({"added": [{"id": c["id"], "source": c["source"], "importance": c["importance"], "quote_verified": c["quote_verified"]} for c in valid],
             "rejected": rejected})
        sys.exit(3 if rejected else 0)
    if rejected:
        r = rejected[0]
        msg = {"error": r["reason"]}
        if r["nearest"]:
            msg["nearest"] = r["nearest"]
        print(json.dumps(msg, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(3 if "quote not found" in (r["reason"] or "") else 2)
    out(valid[0])


def _get_claim(data: dict, cid: str) -> dict:
    c = next((c for c in data["claims"] if c["id"] == cid), None)
    if not c:
        die(f"no claim {cid}")
    return c


def cmd_claim_evidence(args) -> None:
    run = Run(args.run).require()
    if (args.supports is None) == (args.contradicts is None):
        die("give exactly one of --supports N or --contradicts N")
    n = args.supports if args.supports is not None else args.contradicts
    src = run.source_by_n(n)
    if not src:
        die(f"no source [{n}]")
    with run.lock():
        data = run.claims()
        c = _get_claim(data, args.id)
        if args.supports is not None and n == c["source"]:
            die(f"[{n}] is the claim's own source; supporting evidence must be independent")
        ev = {"source": n, "note": (args.note or "").strip(), "by": args.by or ""}
        key = "supports" if args.supports is not None else "contradicts"
        if not any(e["source"] == n and e.get("by") == ev["by"] for e in c[key]):
            c[key].append(ev)
        c["checked"] = True
        run.save_claims(data)
        c = _get_claim(run.claims(), args.id)
    out(c)


def cmd_claim_checked(args) -> None:
    run = Run(args.run).require()
    with run.lock():
        data = run.claims()
        c = _get_claim(data, args.id)
        c["checked"] = True
        if args.note:
            c["notes"].append((f"[{args.by}] " if args.by else "") + args.note.strip())
        run.save_claims(data)
        c = _get_claim(run.claims(), args.id)
    out(c)


def cmd_claim_note(args) -> None:
    run = Run(args.run).require()
    with run.lock():
        data = run.claims()
        c = _get_claim(data, args.id)
        c["notes"].append((f"[{args.by}] " if args.by else "") + args.note.strip())
        run.save_claims(data)
    out(c)


def _claim_md(c: dict) -> str:
    sup = ",".join(f"[{e['source']}]" for e in c.get("supports", [])) or "-"
    con = ",".join(f"[{e['source']}]" for e in c.get("contradicts", [])) or "-"
    q = c["quote"].replace("\n", " ")
    line = f"- {c['id']} [{c['importance']}] [{c['source']}] {c['text']} — \"{q}\" ({c['label']}; supports {sup}; contradicts {con})"
    if c.get("notes"):
        line += " — notes: " + " | ".join(c["notes"])
    return line


def cmd_claims_list(args) -> None:
    run = Run(args.run).require()
    claims = run.claims()["claims"]
    if args.label:
        claims = [c for c in claims if c["label"] == args.label]
    if args.importance:
        claims = [c for c in claims if c["importance"] == args.importance]
    if args.angle:
        claims = [c for c in claims if c.get("angle") == args.angle]
    if args.round:
        claims = [c for c in claims if c.get("round") == args.round]
    if args.unchecked:
        claims = [c for c in claims if not c.get("checked")]
    if args.format == "md":
        print("\n".join(_claim_md(c) for c in claims) if claims else "(no claims)")
    else:
        out(claims)


def _counts(items, key):
    d: dict = {}
    for it in items:
        k = it.get(key) if isinstance(it, dict) else it
        d[k] = d.get(k, 0) + 1
    return dict(sorted(d.items(), key=lambda kv: str(kv[0])))


def build_state(run: Run) -> dict:
    meta = run.meta()
    sources = run.sources()["sources"]
    claims = run.claims()["claims"]
    central = [c for c in claims if c["importance"] == "central"]
    per_round: dict = {}
    for c in central:
        per_round[c.get("round", 1)] = per_round.get(c.get("round", 1), 0) + 1
    return {
        "question": meta.get("question"), "preset": meta.get("preset"), "mode": meta.get("mode"),
        "sources": {"total": len(sources), "by_status": _counts(sources, "status"), "by_method": _counts(sources, "fetch_method"),
                    "by_round": _counts(sources, "round")},
        "claims": {"total": len(claims), "by_label": _counts(claims, "label"), "by_importance": _counts(claims, "importance"),
                   "central_by_round": dict(sorted(per_round.items())), "unchecked": sum(1 for c in claims if not c.get("checked"))},
        "central_claims": [{"id": c["id"], "text": c["text"], "source": c["source"], "label": c["label"], "angle": c.get("angle")} for c in central],
        "problem_sources": [{"n": s["n"], "url": s["url"], "status": s["status"], "notes": s.get("notes", "")}
                            for s in sources if s["status"] not in ("ok",)],
    }


def cmd_state(args) -> None:
    run = Run(args.run).require()
    st = build_state(run)
    if args.format != "md":
        out(st)
        return
    lines = [f"# Working state", f"**Question:** {st['question']}", f"**Preset:** {st['preset']}  **Mode:** {st['mode']}", ""]
    s, c = st["sources"], st["claims"]
    lines.append(f"**Sources:** {s['total']} — by status {s['by_status']} — by method {s['by_method']} — by round {s['by_round']}")
    lines.append(f"**Claims:** {c['total']} — by label {c['by_label']} — by importance {c['by_importance']} — unchecked {c['unchecked']}")
    lines.append(f"**Central claims per round:** {c['central_by_round']}")
    lines.append("")
    lines.append("## Central claims")
    shown = st["central_claims"][:60]
    for cc in shown:
        lines.append(f"- {cc['id']} [{cc['source']}] ({cc['label']}, {cc['angle']}) {cc['text']}")
    if len(st["central_claims"]) > 60:
        lines.append(f"- … and {len(st['central_claims']) - 60} more")
    if st["problem_sources"]:
        lines.append("")
        lines.append("## Sources not fetched")
        for p in st["problem_sources"][:30]:
            lines.append(f"- [{p['n']}] {p['status']} {p['url']} {('— ' + p['notes']) if p['notes'] else ''}")
    print("\n".join(lines))


# ----------------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------------

def _cell(v) -> str:
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def render_sources_md(sources: list) -> str:
    lines = ["# Sources", "", "| [n] | Title | Publisher | Published | Accessed | Grade | Fetch | Health | Evidence | Notes |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in sorted(sources, key=lambda x: x["n"]):
        status = s.get("status")
        fetch = s.get("fetch_method") if status == "ok" else {"unfetchable": "UNFETCHABLE", "possibly-fabricated": "POSSIBLY-FABRICATED",
                                                                "skipped-robots": "SKIPPED-ROBOTS"}.get(status, str(status).upper())
        title = f"{s.get('title') or '(untitled)'} — {s.get('url')}"
        accessed = (s.get("accessed") or "")[:10]
        evidence = s.get("evidence_strength") or ""
        if s.get("snapshot_date"):
            evidence += f" ({s['snapshot_date']})"
        lines.append("| " + " | ".join(_cell(x) for x in (
            f"[{s['n']}]", title, s.get("publisher"), s.get("published"), accessed, s.get("grade"), fetch,
            s.get("health"), evidence, s.get("notes"))) + " |")
    return "\n".join(lines) + "\n"


def render_verification_md(claims: list) -> str:
    by_label = {l: [c for c in claims if c["label"] == l] for l in LABELS}
    by_imp = _counts(claims, "importance")
    lines = ["# Verification ledger", "",
             f"Claims: {len(claims)} — " + ", ".join(f"{l}: {len(v)}" for l, v in by_label.items()) +
             " — importance: " + ", ".join(f"{k}: {v}" for k, v in by_imp.items()), ""]
    for label in LABELS:
        lines.append(f"## {label.capitalize()} ({len(by_label[label])})")
        for c in by_label[label]:
            sup = ",".join(f"[{e['source']}]" for e in c.get("supports", [])) or "-"
            con = ",".join(f"[{e['source']}]" for e in c.get("contradicts", [])) or "-"
            q = c["quote"].replace("\n", " ")
            notes = " | ".join(c.get("notes", []))
            ev_notes = "; ".join(f"[{e['source']}] {e['note']}" for e in c.get("supports", []) + c.get("contradicts", []) if e.get("note"))
            lines.append(f"- **{c['id']}** ({c['importance']}, [{c['source']}]) {c['text']} — quote: \"{q}\" — supports: {sup} — contradicts: {con}"
                         + (f" — evidence: {ev_notes}" if ev_notes else "") + (f" — notes: {notes}" if notes else ""))
        lines.append("")
    return "\n".join(lines)


def do_render(run: Run) -> dict:
    with run.lock():
        sources = run.sources()["sources"]
        data = run.claims()
        recompute_labels(data["claims"], {s["n"]: s for s in sources})
        write_json_atomic(run.claims_path, data)
    (run.path / "sources.md").write_text(render_sources_md(sources), encoding="utf-8")
    (run.path / "verification.md").write_text(render_verification_md(data["claims"]), encoding="utf-8")
    return {"sources_md": str(run.path / "sources.md"), "verification_md": str(run.path / "verification.md")}


def cmd_render(args) -> None:
    out(do_render(Run(args.run).require()))


def cmd_finalize(args) -> None:
    run = Run(args.run).require()
    meta = run.meta()
    sources = run.sources()["sources"]
    claims = run.claims()["claims"]
    finished = now_iso()
    wall = None
    try:
        t0 = _dt.datetime.strptime(meta["started"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
        wall = int((_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds())
    except (KeyError, ValueError):
        pass
    st = _counts(sources, "status")
    meta.update({
        "finished": finished, "wall_clock_s": wall,
        "harness": args.harness, "model": args.model, "agents": args.agents, "rounds": args.rounds,
        "execution": args.execution, "tokens": args.tokens,
        "sources": {"total": len(sources), "ok": st.get("ok", 0), "unfetchable": st.get("unfetchable", 0),
                    "possibly_fabricated": st.get("possibly-fabricated", 0), "skipped_robots": st.get("skipped-robots", 0),
                    "by_method": _counts([s for s in sources if s["status"] == "ok"], "fetch_method")},
        "claims": {"total": len(claims), "by_label": _counts(claims, "label"), "by_importance": _counts(claims, "importance"),
                   "quote_verified": sum(1 for c in claims if c.get("quote_verified") is True),
                   "quote_failed": sum(1 for c in claims if c.get("quote_verified") is False),
                   "quote_unknown": sum(1 for c in claims if c.get("quote_verified") is None)},
        "health": _counts([s for s in sources if s.get("health")], "health"),
    })
    write_json_atomic(run.run_path, meta)
    do_render(run)
    out(meta)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="deep-research run ledger")
    p.add_argument("--run", default=os.environ.get("DEEP_RESEARCH_RUN"), help="run folder (or env DEEP_RESEARCH_RUN)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("--question", required=True)
    s.add_argument("--slug")
    s.add_argument("--preset", default="standard", choices=["quick", "standard", "deep"])
    s.add_argument("--mode", default="report", choices=["brief", "report"])
    s.add_argument("--root", default="research-runs")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("add-url")
    s.add_argument("url")
    s.add_argument("--angle")
    s.add_argument("--round", type=int, default=1)
    s.add_argument("--title")
    s.add_argument("--ignore-robots", action="store_true")
    s.add_argument("--fresh", action="store_true")
    s.set_defaults(fn=cmd_add_url)

    s = sub.add_parser("refetch")
    s.add_argument("n", type=int)
    s.add_argument("--ignore-robots", action="store_true")
    s.add_argument("--fresh", action="store_true")
    s.add_argument("--keep-title", action="store_true")
    s.set_defaults(fn=cmd_refetch)

    s = sub.add_parser("add-snippet")
    s.add_argument("url")
    s.add_argument("--snippet", required=True)
    s.add_argument("--angle")
    s.add_argument("--round", type=int, default=1)
    s.add_argument("--title")
    s.set_defaults(fn=cmd_add_snippet)

    s = sub.add_parser("grade")
    s.add_argument("n", type=int)
    s.add_argument("--grade", required=True)
    s.add_argument("--published")
    s.add_argument("--publisher")
    s.set_defaults(fn=cmd_grade)

    c = sub.add_parser("claim")
    csub = c.add_subparsers(dest="ccmd", required=True)
    s = csub.add_parser("add")
    s.add_argument("--source", type=int)
    s.add_argument("--angle")
    s.add_argument("--text")
    s.add_argument("--quote")
    s.add_argument("--importance")
    s.add_argument("--round", type=int)
    s.add_argument("--from-json")
    s.set_defaults(fn=cmd_claim_add)
    s = csub.add_parser("evidence")
    s.add_argument("id")
    s.add_argument("--supports", type=int)
    s.add_argument("--contradicts", type=int)
    s.add_argument("--note")
    s.add_argument("--by")
    s.set_defaults(fn=cmd_claim_evidence)
    s = csub.add_parser("checked")
    s.add_argument("id")
    s.add_argument("--note")
    s.add_argument("--by")
    s.set_defaults(fn=cmd_claim_checked)
    s = csub.add_parser("note")
    s.add_argument("id")
    s.add_argument("--note", required=True)
    s.add_argument("--by")
    s.set_defaults(fn=cmd_claim_note)

    c = sub.add_parser("claims")
    csub = c.add_subparsers(dest="ccmd", required=True)
    s = csub.add_parser("list")
    s.add_argument("--label", choices=LABELS)
    s.add_argument("--importance", choices=IMPORTANCE)
    s.add_argument("--angle")
    s.add_argument("--round", type=int)
    s.add_argument("--unchecked", action="store_true")
    s.add_argument("--format", default="json", choices=["json", "md"])
    s.set_defaults(fn=cmd_claims_list)

    s = sub.add_parser("state")
    s.add_argument("--format", default="json", choices=["json", "md"])
    s.set_defaults(fn=cmd_state)

    s = sub.add_parser("render")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("finalize")
    s.add_argument("--harness")
    s.add_argument("--model")
    s.add_argument("--agents", type=int)
    s.add_argument("--rounds", type=int)
    s.add_argument("--execution", choices=["parallel", "sequential"])
    s.add_argument("--tokens", type=int)
    s.set_defaults(fn=cmd_finalize)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    if args.cmd != "init" and not args.run:
        die("--run DIR is required (or set DEEP_RESEARCH_RUN)")
    args.fn(args)


if __name__ == "__main__":
    main()
