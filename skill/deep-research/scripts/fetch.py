#!/usr/bin/env python3
"""Keyless page fetcher for the deep-research skill (Python stdlib only).

Runs an ordered fallback chain and prints one JSON record describing what was
obtained and how (contract: skill/deep-research/reference/contracts.md §3;
evidence: research/literature/fetch-reliability-survey.md §4).

Chain (each rung records one `attempts` entry and is skipped when it does not
apply):
  1. keyless-api      DOI -> Crossref; arXiv -> export API + ar5iv HTML;
                      Wikipedia -> REST HTML; GitHub -> `gh` CLI if installed;
                      docs pages -> `.md` sibling
  3. raw-http         HEAD then GET, browser-like headers, robots.txt honoured,
                      one retry on 429/5xx, PDF -> pdftotext/pypdf
  4. jina-reader      https://r.jina.ai/<url> (20 requests/min without a key)
  5. urltomarkdown    https://urltomarkdown.herokuapp.com/?url=<url>
  6. wayback          CDX lookup -> web/<ts>id_/<url>;  then commoncrawl
  8. headless         `agent-browser read <url>` only if already installed
  9. UNFETCHABLE      with a fabrication check (DNS, CDX exact, CC, CDX prefix)
(Rung 2, the harness's own fetch tool, is not used by this script; rung 7,
local extraction, is applied inside rungs 3 and 6 whenever bytes are PDF/HTML.)

Every rung's text passes the plausibility gate (length, block-page markers,
consent wall, text:HTML ratio, unextracted PDF, word-list junk).

Policy: no paywall/login/CAPTCHA circumvention, no stealth clients; archive
copies are labelled `archived` with their snapshot date; robots.txt is honoured
for direct fetches unless --ignore-robots is given (recorded either way).

Exit codes: 0 ok; 1 unfetchable / possibly-fabricated / skipped-robots; 2 usage.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import html as _html
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from urllib import error, request, robotparser
from urllib.parse import quote, unquote, urlsplit, urlunsplit

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
POLITE_MAILTO = "mailto:zhonghanloo@gmail.com"
SERVICE_UA = f"deep-research-skill/1.0 (+https://github.com/ZhongHanLoo/deep-research-skill; {POLITE_MAILTO})"
SERVICE_HEADERS = {"User-Agent": SERVICE_UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
MIN_CHARS = 200
BLOCK_MARKERS = ("attention required! | cloudflare", "sorry, you have been blocked", "please verify you are a human",
                 "checking your browser", "anubis uses a proof-of-work scheme", "enable javascript and cookies",
                 "access denied", "request blocked", "just a moment...", "client challenge",
                 "a required part of this site couldn't load", "are you a robot", "verify you are human",
                 "javascript is disabled in your browser", "please enable cookies")
CONSENT_MARKERS = ("before you continue", "we use cookies and data", "manage your privacy settings", "accept all cookies")

_last_archive_call = 0.0


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

class Resp:
    def __init__(self, status=None, headers=None, body=b"", final_url="", err=None):
        self.status = status
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.body = body
        self.final_url = final_url
        self.err = err

    @property
    def ok(self) -> bool:
        return self.err is None and self.status is not None and 200 <= self.status < 300

    def content_type(self) -> str:
        return (self.headers.get("content-type") or "").split(";")[0].strip().lower()

    def describe(self) -> str:
        return str(self.status) if self.err is None else self.err


_ARCHIVE_STAMP = os.path.join(tempfile.gettempdir(), "deep-research-archive.stamp")


def throttle_archive(url: str) -> None:
    """Keep >= 1 s between archive.org requests, across processes (parallel agents)."""
    global _last_archive_call
    if "archive.org" not in url:
        return
    for _ in range(50):
        try:
            last = os.stat(_ARCHIVE_STAMP).st_mtime
        except OSError:
            last = 0.0
        wait = 1.05 - (time.time() - max(last, _last_archive_call))
        if wait <= 0:
            break
        time.sleep(wait)
    try:
        with open(_ARCHIVE_STAMP, "a"):
            os.utime(_ARCHIVE_STAMP, None)
    except OSError:
        pass
    _last_archive_call = time.time()


def http(url: str, *, method: str = "GET", headers: dict | None = None, timeout: float = 25.0,
         max_bytes: int = 10 * 1024 * 1024, data: bytes | None = None, service: bool = False) -> Resp:
    """One request. Never raises; network errors land in Resp.err.
    service=True sends the honest tool User-Agent (APIs, readers, archives);
    otherwise browser-like headers are used for direct page reads."""
    throttle_archive(url)
    hdrs = dict(SERVICE_HEADERS if service else BASE_HEADERS)
    if headers:
        hdrs.update(headers)
    req = request.Request(url, headers=hdrs, method=method, data=data)
    try:
        with request.urlopen(req, timeout=timeout) as r:
            body = b""
            if method != "HEAD":
                while len(body) < max_bytes:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    body += chunk
            return Resp(r.status, dict(r.headers), body, r.geturl())
    except error.HTTPError as e:
        try:
            body = e.read(min(max_bytes, 1 << 20))
        except Exception:
            body = b""
        return Resp(e.code, dict(e.headers or {}), body, e.geturl() if hasattr(e, "geturl") else url)
    except error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.gaierror) or "nodename nor servname" in str(reason) or "Name or service not known" in str(reason):
            return Resp(err="dns-failure")
        if isinstance(reason, socket.timeout) or "timed out" in str(reason):
            return Resp(err="timeout")
        return Resp(err=f"URLError: {str(reason)[:80]}")
    except socket.timeout:
        return Resp(err="timeout")
    except Exception as e:  # noqa: BLE001
        return Resp(err=f"{e.__class__.__name__}: {str(e)[:80]}")


def dns_resolves(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    try:
        socket.getaddrinfo(host, None)
        return True
    except (socket.gaierror, UnicodeError, OSError):
        return False


# ----------------------------------------------------------------------------
# robots.txt
# ----------------------------------------------------------------------------

_robots_cache: dict[str, robotparser.RobotFileParser | None] = {}


def robots_allowed(url: str, timeout: float) -> bool:
    p = urlsplit(url)
    key = f"{p.scheme}://{p.netloc}"
    if key not in _robots_cache:
        r = http(f"{key}/robots.txt", timeout=min(timeout, 10), max_bytes=512 * 1024)
        rp = None
        if r.ok and r.body:
            rp = robotparser.RobotFileParser()
            try:
                rp.parse(r.body.decode("utf-8", "replace").splitlines())
            except Exception:  # noqa: BLE001
                rp = None
        _robots_cache[key] = rp
    rp = _robots_cache[key]
    if rp is None:
        return True
    try:
        return rp.can_fetch("*", url)
    except Exception:  # noqa: BLE001
        return True


# ----------------------------------------------------------------------------
# extraction
# ----------------------------------------------------------------------------

DROP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "iframe", "template"}
BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "section", "article", "blockquote",
              "pre", "td", "th", "dt", "dd", "table", "ul", "ol", "hr", "figcaption", "main"}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
        self.title_parts: list[str] = []
        self.in_title = False
        self.canonical = None
        self.site_name = None
        self.dates: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in DROP_TAGS:
            self.skip += 1
        elif tag == "title":
            self.in_title = True
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical" and a.get("href"):
            self.canonical = a["href"]
        elif tag == "meta":
            prop = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            content = a.get("content") or ""
            if prop == "og:site_name":
                self.site_name = content
            elif prop in ("article:published_time", "datepublished", "date", "pubdate", "dc.date", "dc.date.issued",
                          "publish-date", "publication_date", "sailthru.date", "parsely-pub-date"):
                self.dates.append(content)
        elif tag == "time" and a.get("datetime"):
            self.dates.append(a["datetime"])
        if tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag in ("td", "th"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in DROP_TAGS:
            self.skip = max(0, self.skip - 1)
        elif tag == "title":
            self.in_title = False
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
            return
        if self.skip == 0 and data:
            self.parts.append(data)


def iso_date(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    m = re.search(r"(\d{4})(\d{2})(\d{2})", s)
    if m and s.strip().isdigit():
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    for fmt in ("%B %d, %Y", "%d %B %Y", "%b %d, %Y", "%d %b %Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return _dt.datetime.strptime(s.strip()[:40], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def html_to_text(markup: str) -> tuple[str, dict]:
    meta: dict = {"title": None, "canonical_url": None, "publisher": None, "published": None}
    if importlib.util.find_spec("trafilatura") is not None:
        try:
            import trafilatura  # type: ignore
            t = trafilatura.extract(markup, include_comments=False, include_tables=True) or ""
            if len(t) >= MIN_CHARS:
                ex = TextExtractor()
                try:
                    ex.feed(markup)
                except Exception:  # noqa: BLE001
                    pass
                meta.update(_meta_from(ex, markup))
                return t, meta
        except Exception:  # noqa: BLE001
            pass
    ex = TextExtractor()
    try:
        ex.feed(markup)
        ex.close()
    except Exception:  # noqa: BLE001
        pass
    text = "".join(ex.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    meta.update(_meta_from(ex, markup))
    return text, meta


def _meta_from(ex: TextExtractor, markup: str) -> dict:
    title = re.sub(r"\s+", " ", "".join(ex.title_parts)).strip() or None
    published = None
    for d in ex.dates:
        published = iso_date(d)
        if published:
            break
    if not published:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', markup)
        if m:
            published = iso_date(m.group(1))
    return {"title": title, "canonical_url": ex.canonical, "publisher": ex.site_name, "published": published}


def decode_body(resp: Resp) -> str:
    ct = resp.headers.get("content-type") or ""
    m = re.search(r"charset=([\w\-]+)", ct, re.I)
    enc = m.group(1) if m else None
    if not enc:
        head = resp.body[:4096].decode("ascii", "ignore")
        m = re.search(r'<meta[^>]+charset=["\']?([\w\-]+)', head, re.I)
        enc = m.group(1) if m else "utf-8"
    try:
        return resp.body.decode(enc, "replace")
    except LookupError:
        return resp.body.decode("utf-8", "replace")


def is_pdf(resp: Resp) -> bool:
    return resp.content_type() == "application/pdf" or resp.body[:5] == b"%PDF-"


def extract_pdf(data: bytes) -> tuple[str | None, str]:
    """Returns (text, extractor). Prefers pdftotext, then pypdf."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        if shutil.which("pdftotext"):
            try:
                p = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True, timeout=120)
                t = p.stdout.decode("utf-8", "replace")
                t = re.sub(r"-\n(?=[a-z])", "", t)  # de-hyphenate line breaks
                t = re.sub(r"[ \t]*\n[ \t]*", "\n", t)
                if len(t.strip()) >= MIN_CHARS:
                    return t.strip(), "pdftotext"
            except Exception:  # noqa: BLE001
                pass
        if importlib.util.find_spec("pypdf") is not None:
            try:
                from pypdf import PdfReader  # type: ignore
                reader = PdfReader(path)
                t = "\n".join((pg.extract_text() or "") for pg in reader.pages)
                if len(t.strip()) >= MIN_CHARS:
                    return t.strip(), "pypdf"
            except Exception:  # noqa: BLE001
                pass
        return None, "none"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# ----------------------------------------------------------------------------
# plausibility gate (survey §4.2)
# ----------------------------------------------------------------------------

def gate(text: str, html_len: int | None = None, title: str | None = None) -> str:
    t = text or ""
    if title and any(m in title.lower() for m in BLOCK_MARKERS):
        return "failed:block-page"
    if t[:5] == "%PDF-" or sum(1 for k in ("endobj", "endstream", "/FlateDecode", "xref", "trailer") if k in t[:200000]) >= 2:
        return "failed:unextracted-pdf"
    if len(t) < MIN_CHARS:
        return "failed:length"
    head = t[:5000].lower()
    if any(m in head for m in BLOCK_MARKERS):
        return "failed:block-page"
    if len(t) < 1500 and any(m in head for m in CONSENT_MARKERS):
        return "failed:consent-wall"
    if html_len and html_len >= 20000 and len(t) / html_len < 0.015:
        return "failed:js-empty"
    if len(t) >= 200000:
        terms = len(re.findall(r"[.!?](\s|$)", t))
        if terms < len(t) / 5000:
            return "failed:word-list"
    return "passed"


# ----------------------------------------------------------------------------
# chain context and results
# ----------------------------------------------------------------------------

class Ctx:
    def __init__(self, url: str, opts):
        self.url = url
        self.opts = opts
        self.attempts: list[dict] = []
        self.robots = "not-checked"
        self.raw_status: int | None = None
        self.partial: dict = {}  # metadata gathered by keyless rung (title, published, abstract...)

    def attempt(self, method: str, result: str) -> None:
        self.attempts.append({"method": method, "result": result[:200]})


def make_result(method: str, text: str, *, http_status=None, content_type=None, snapshot_date=None,
                evidence_strength="primary", quote_safe=True, meta=None, final_url=None) -> dict:
    meta = meta or {}
    return {"method": method, "text": text, "http_status": http_status, "content_type": content_type,
            "snapshot_date": snapshot_date, "evidence_strength": evidence_strength, "quote_safe": quote_safe,
            "title": meta.get("title"), "published": meta.get("published"), "publisher": meta.get("publisher"),
            "canonical_url": meta.get("canonical_url"), "final_url": final_url}


def bytes_to_text(resp: Resp, ctx: Ctx, method: str) -> tuple[str | None, dict, str]:
    """Turn a response into text via the type cascade. Returns (text, meta, note)."""
    if is_pdf(resp):
        t, ex = extract_pdf(resp.body)
        if t is None:
            return None, {}, "failed:unextracted-pdf (no extractor)" if ex == "none" else "failed:unextracted-pdf"
        return t, {"title": None}, f"pdf via {ex}"
    ct = resp.content_type()
    body = decode_body(resp)
    if ct in ("text/plain", "text/markdown") or (ct == "" and "<" not in body[:200]):
        return body.strip(), {}, "plain text"
    text, meta = html_to_text(body)
    return text, meta, "html"


# ----------------------------------------------------------------------------
# rung 1: keyless structured APIs
# ----------------------------------------------------------------------------

ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf|html)/((?:\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)", re.I)
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s?#]+)")
WIKI_RE = re.compile(r"^https?://([a-z\-]+)\.(?:m\.)?wikipedia\.org/wiki/([^?#]+)", re.I)
GITHUB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)(?:/(blob|issues|pull)/([^?#]+))?/?$", re.I)


def rung_keyless_api(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    m = ARXIV_RE.search(url)
    if m:
        aid = m.group(1)
        r = http(f"https://export.arxiv.org/api/query?id_list={aid}", timeout=T, service=True)
        meta: dict = {"publisher": "arXiv"}
        if r.ok:
            x = r.body.decode("utf-8", "replace")
            if re.search(r"<title>\s*Error\s*</title>", x) or "incorrect id format" in x.lower() or "not recognized" in x.lower():
                ctx.attempt("keyless-api", "arxiv export: id not found")
                ctx.raw_status = 404
                return None
            t = re.search(r"<entry>.*?<title>(.*?)</title>", x, re.S)
            d = re.search(r"<published>(.*?)</published>", x)
            meta["title"] = re.sub(r"\s+", " ", _html.unescape(t.group(1))).strip() if t else None
            meta["published"] = iso_date(d.group(1)) if d else None
            a = re.search(r"<summary>(.*?)</summary>", x, re.S)
            ctx.partial = {**meta, "abstract": re.sub(r"\s+", " ", _html.unescape(a.group(1))).strip() if a else ""}
        if "/pdf/" not in url.lower():
            r2 = http(f"https://ar5iv.labs.arxiv.org/html/{aid}", timeout=T, max_bytes=ctx.opts.max_bytes, service=True)
            if r2.ok:
                text, m2 = html_to_text(decode_body(r2))
                g = gate(text, len(r2.body))
                if g == "passed":
                    ctx.attempt("keyless-api", f"arxiv export + ar5iv {r2.status}")
                    meta = {**m2, **{k: v for k, v in meta.items() if v}}
                    meta["canonical_url"] = f"https://arxiv.org/abs/{aid}"
                    return make_result("keyless-api", text, http_status=r2.status, content_type="text/html", meta=meta, final_url=r2.final_url)
                ctx.attempt("keyless-api", f"ar5iv {g}; falling through")
            else:
                ctx.attempt("keyless-api", f"ar5iv {r2.describe()}; falling through")
        else:
            ctx.attempt("keyless-api", "arxiv metadata only (pdf requested); falling through")
        return None
    m = WIKI_RE.match(url)
    if m:
        lang, title = m.group(1), m.group(2)
        r = http(f"https://{lang}.wikipedia.org/api/rest_v1/page/html/{quote(unquote(title), safe='')}", timeout=T, max_bytes=ctx.opts.max_bytes, service=True)
        if r.ok:
            text, meta = html_to_text(decode_body(r))
            g = gate(text, len(r.body))
            if g == "passed":
                meta["publisher"] = "Wikipedia"
                meta["title"] = meta.get("title") or unquote(title).replace("_", " ")
                meta["canonical_url"] = url.split("#")[0]
                ctx.attempt("keyless-api", f"wikipedia rest {r.status}")
                return make_result("keyless-api", text, http_status=r.status, content_type="text/html", meta=meta, final_url=url)
            ctx.attempt("keyless-api", f"wikipedia rest {g}")
        else:
            ctx.attempt("keyless-api", f"wikipedia rest {r.describe()}")
        return None
    m = DOI_RE.search(url) if ("doi.org/" in url.lower() or re.search(r"/10\.\d{4,9}/", url)) else None
    if m:
        doi = m.group(1).rstrip("/.")
        r = http(f"https://api.crossref.org/works/{quote(doi, safe='/')}", headers={"Accept": "application/json"}, timeout=T, service=True)
        if r.ok:
            try:
                msg = json.loads(r.body.decode("utf-8", "replace"))["message"]
                title = " ".join(msg.get("title") or []) or None
                parts = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0]
                published = "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts) if p is not None) if parts and parts[0] else None
                if published and len(published) == 4:
                    published += "-01-01"
                abstract = re.sub(r"<[^>]+>", " ", msg.get("abstract") or "")
                abstract = re.sub(r"\s+", " ", _html.unescape(abstract)).strip()
                ctx.partial = {"title": title, "published": published, "publisher": msg.get("publisher"),
                               "abstract": abstract, "canonical_url": msg.get("URL")}
                ctx.attempt("keyless-api", f"crossref {r.status} metadata{' + abstract' if abstract else ''}; trying full text")
            except (ValueError, KeyError, TypeError):
                ctx.attempt("keyless-api", "crossref response unparseable")
        else:
            ctx.attempt("keyless-api", f"crossref {r.describe()}")
        return None
    m = GITHUB_RE.match(url)
    if m and shutil.which("gh"):
        owner, repo, kind, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            if kind is None:
                p = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/readme", "-H", "Accept: application/vnd.github.raw"], capture_output=True, text=True, timeout=60)
            elif kind.lower() == "blob":
                ref, _, path = rest.partition("/")
                p = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"], capture_output=True, text=True, timeout=60)
            elif kind.lower() == "issues":
                p = subprocess.run(["gh", "issue", "view", url, "--comments"], capture_output=True, text=True, timeout=60)
            else:
                p = subprocess.run(["gh", "pr", "view", url, "--comments"], capture_output=True, text=True, timeout=60)
            if p.returncode == 0 and gate(p.stdout) == "passed":
                ctx.attempt("keyless-api", "gh cli")
                return make_result("keyless-api", p.stdout.strip(), content_type="text/plain", meta={"publisher": "GitHub", "title": f"{owner}/{repo}" + (f" {kind} {rest}" if kind else "")}, final_url=url)
            ctx.attempt("keyless-api", f"gh cli exit {p.returncode}")
        except Exception as e:  # noqa: BLE001
            ctx.attempt("keyless-api", f"gh cli {e.__class__.__name__}")
        return None
    p = urlsplit(url)
    if (p.hostname or "").startswith("docs.") or "/docs/" in p.path:
        cand = url.split("#")[0].rstrip("/") + ".md"
        r = http(cand, headers={"Accept": "text/markdown, text/plain;q=0.9, */*;q=0.1"}, timeout=T)
        if r.ok and r.content_type() in ("text/markdown", "text/plain") and gate(r.body.decode("utf-8", "replace")) == "passed":
            text = r.body.decode("utf-8", "replace").strip()
            title = re.search(r"^#\s+(.+)$", text, re.M)
            ctx.attempt("keyless-api", f"docs .md sibling {r.status}")
            return make_result("keyless-api", text, http_status=r.status, content_type=r.content_type(), meta={"title": title.group(1).strip() if title else None, "publisher": p.hostname}, final_url=r.final_url)
        ctx.attempt("keyless-api", f"docs .md sibling {r.describe() if r.err else str(r.status) + ' ' + r.content_type()}")
        return None
    ctx.attempt("keyless-api", "no matching shape")
    return None


# ----------------------------------------------------------------------------
# rung 3: raw HTTP
# ----------------------------------------------------------------------------

def soft_404_note(requested: str, final: str) -> str:
    rp = urlsplit(requested).path.rstrip("/")
    fp = urlsplit(final or requested).path.rstrip("/")
    if rp and rp != fp and fp.lower() in ("", "/404", "/home", "/index.html", "/index.htm"):
        return "; soft-404-suspected"
    return ""


def rung_raw_http(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    if not ctx.opts.ignore_robots:
        allowed = robots_allowed(url, T)
        ctx.robots = "allowed" if allowed else "disallowed"
        if not allowed:
            ctx.attempt("raw-http", "skipped: robots.txt disallows")
            return None
    else:
        ctx.robots = "not-checked"
    head = http(url, method="HEAD", timeout=T)
    if head.err == "dns-failure":
        ctx.attempt("raw-http", "dns-failure")
        ctx.raw_status = None
        return None
    if head.err is None and head.status in (401, 403, 404, 410):
        ctx.raw_status = head.status
        # some servers reject HEAD but serve GET; try GET once for 403/404 only if cheap
        if head.status in (401, 410):
            ctx.attempt("raw-http", f"HEAD {head.status}")
            return None
    r = http(url, timeout=T, max_bytes=ctx.opts.max_bytes)
    if r.err is None and r.status in (429, 500, 502, 503, 504):
        time.sleep(2.0)
        r = http(url, timeout=T, max_bytes=ctx.opts.max_bytes)
    if r.err:
        ctx.attempt("raw-http", r.err)
        return None
    ctx.raw_status = r.status
    if not r.ok:
        ctx.attempt("raw-http", f"{r.status}")
        return None
    text, meta, note = bytes_to_text(r, ctx, "raw-http")
    if text is None:
        ctx.attempt("raw-http", f"{r.status} {note}")
        return None
    g = gate(text, len(r.body) if not is_pdf(r) else None, meta.get("title"))
    if g != "passed":
        ctx.attempt("raw-http", f"{r.status} {note} {g}")
        return None
    ctx.attempt("raw-http", f"{r.status} {note}" + soft_404_note(url, r.final_url))
    return make_result("raw-http", text, http_status=r.status, content_type=r.content_type() or ("application/pdf" if is_pdf(r) else None),
                       meta=meta, final_url=r.final_url)


# ----------------------------------------------------------------------------
# rung 4: Jina reader   rung 5: urltomarkdown
# ----------------------------------------------------------------------------

def rung_jina(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    hdrs = {"Accept": "text/plain"}
    if ctx.opts.fresh:
        hdrs["x-no-cache"] = "true"
    r = http(f"https://r.jina.ai/{url}", headers=hdrs, timeout=max(T, 40), max_bytes=ctx.opts.max_bytes, service=True)
    if r.err:
        ctx.attempt("jina-reader", r.err)
        return None
    body = r.body.decode("utf-8", "replace")
    if r.status == 403 and "AbuseAlleviationError" in body:
        ctx.attempt("jina-reader", "403 AbuseAlleviationError (anonymous access to this domain blocked)")
        return None
    if r.status == 429:
        ctx.attempt("jina-reader", "429 rate limited (20 requests/min without a key)")
        return None
    if not r.ok:
        ctx.attempt("jina-reader", f"{r.status}")
        return None
    meta: dict = {}
    head, sep, rest = body.partition("Markdown Content:\n")
    if sep:
        for line in head.splitlines():
            if line.startswith("Title:"):
                meta["title"] = line[6:].strip() or None
            elif line.startswith("Published Time:"):
                meta["published"] = iso_date(line[15:].strip())
        text = rest.strip()
    else:
        text = body.strip()
    snapshot = None
    strength = "primary"
    if "cached snapshot" in body[:2000].lower():
        strength = "archived"
        snapshot = now_iso()[:10]
    g = gate(text)
    if g != "passed":
        ctx.attempt("jina-reader", f"{r.status} {g}")
        return None
    ctx.attempt("jina-reader", f"{r.status}" + (" (cached snapshot)" if snapshot else ""))
    return make_result("jina-reader", text, http_status=r.status, content_type="text/markdown", snapshot_date=snapshot,
                       evidence_strength=strength, meta={**meta, "publisher": urlsplit(url).hostname}, final_url=url)


def rung_urltomarkdown(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    r = http(f"https://urltomarkdown.herokuapp.com/?url={quote(url, safe='')}&title=true", timeout=max(T, 40), max_bytes=ctx.opts.max_bytes, service=True)
    if r.err or not r.ok:
        ctx.attempt("urltomarkdown", r.describe())
        return None
    text = r.body.decode("utf-8", "replace").strip()
    g = gate(text)
    if g != "passed":
        ctx.attempt("urltomarkdown", f"{r.status} {g}")
        return None
    ctx.attempt("urltomarkdown", f"{r.status}")
    title = r.headers.get("x-title")
    return make_result("urltomarkdown", text, http_status=r.status, content_type="text/markdown",
                       meta={"title": unquote(title) if title else None, "publisher": urlsplit(url).hostname}, final_url=url)


# ----------------------------------------------------------------------------
# rung 6: archives
# ----------------------------------------------------------------------------

def cdx_query(url: str, timeout: float, *, limit: str = "-1", prefix: bool = False, status_200: bool = True) -> list | None:
    """Returns list of rows [timestamp, statuscode, original] (no header), or None on error."""
    q = f"https://web.archive.org/cdx/search/cdx?url={quote(url, safe='')}&output=json&limit={limit}&fl=timestamp,statuscode,original"
    if status_200:
        q += "&filter=statuscode:200"
    if prefix:
        q += "&matchType=prefix"
    r = http(q, timeout=timeout, service=True)
    if r.err or r.status in (429, 503):
        time.sleep(3.0)
        r = http(q, timeout=timeout, service=True)
    if r.err or not r.ok:
        return None
    try:
        rows = json.loads(r.body.decode("utf-8", "replace") or "[]")
    except ValueError:
        return None
    return rows[1:] if rows else []


def rung_wayback(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    rows = cdx_query(url, T, limit="-1")
    if rows is None:
        ctx.attempt("wayback", "cdx error")
        return None
    if not rows:
        ctx.attempt("wayback", "cdx: no 200 captures")
        return None
    ts = rows[-1][0]
    r = http(f"https://web.archive.org/web/{ts}id_/{url}", timeout=max(T, 40), max_bytes=ctx.opts.max_bytes, service=True)
    if r.err or not r.ok:
        ctx.attempt("wayback", f"snapshot {ts}: {r.describe()}")
        return None
    text, meta, note = bytes_to_text(r, ctx, "wayback")
    if text is None:
        ctx.attempt("wayback", f"snapshot {ts}: {note}")
        return None
    g = gate(text, len(r.body) if not is_pdf(r) else None)
    if g != "passed":
        ctx.attempt("wayback", f"snapshot {ts}: {g}")
        return None
    snap = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
    ctx.attempt("wayback", f"snapshot {ts}")
    return make_result("wayback", text, http_status=r.status, content_type=r.content_type(), snapshot_date=snap,
                       evidence_strength="archived", meta=meta, final_url=f"https://web.archive.org/web/{ts}/{url}")


_cc_index_cache: str | None = None


def cc_newest_index(timeout: float) -> str | None:
    global _cc_index_cache
    if _cc_index_cache:
        return _cc_index_cache
    r = http("https://index.commoncrawl.org/collinfo.json", timeout=timeout, service=True)
    if r.err or not r.ok:
        return None
    try:
        colls = json.loads(r.body.decode("utf-8", "replace"))
        _cc_index_cache = colls[0]["cdx-api"]
        return _cc_index_cache
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def cc_lookup(url: str, timeout: float) -> list[dict]:
    api = cc_newest_index(timeout)
    if not api:
        return []
    r = http(f"{api}?url={quote(url, safe='')}&output=json&limit=3&filter=status:200", timeout=timeout, service=True)
    if r.err or r.status == 404 or not r.ok:
        return []
    hits = []
    for line in r.body.decode("utf-8", "replace").splitlines():
        try:
            hits.append(json.loads(line))
        except ValueError:
            continue
    return hits


def rung_commoncrawl(ctx: Ctx) -> dict | None:
    url, T = ctx.url, ctx.opts.timeout
    hits = cc_lookup(url, T)
    if not hits:
        ctx.attempt("commoncrawl", "no hit in newest index")
        return None
    h = hits[-1]
    try:
        off, ln = int(h["offset"]), int(h["length"])
        r = http(f"https://data.commoncrawl.org/{h['filename']}", headers={"Range": f"bytes={off}-{off + ln - 1}"}, timeout=max(T, 40), service=True)
        if r.err or r.status not in (200, 206):
            ctx.attempt("commoncrawl", f"warc fetch {r.describe()}")
            return None
        raw = gzip.decompress(r.body)
        parts = raw.split(b"\r\n\r\n", 2)
        if len(parts) < 3:
            ctx.attempt("commoncrawl", "warc record malformed")
            return None
        http_hdr, body = parts[1], parts[2]
        ct = ""
        m = re.search(rb"content-type:\s*([^\r\n]+)", http_hdr, re.I)
        if m:
            ct = m.group(1).decode("ascii", "ignore")
        resp = Resp(200, {"content-type": ct}, body, url)
        text, meta, note = bytes_to_text(resp, ctx, "commoncrawl")
        if text is None:
            ctx.attempt("commoncrawl", note)
            return None
        g = gate(text, len(body) if not is_pdf(resp) else None)
        if g != "passed":
            ctx.attempt("commoncrawl", g)
            return None
        ts = str(h.get("timestamp", ""))
        snap = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else None
        ctx.attempt("commoncrawl", f"record {ts}")
        return make_result("commoncrawl", text, http_status=200, content_type=ct.split(";")[0].strip() or None,
                           snapshot_date=snap, evidence_strength="archived", meta=meta, final_url=url)
    except Exception as e:  # noqa: BLE001
        ctx.attempt("commoncrawl", f"{e.__class__.__name__}")
        return None


# ----------------------------------------------------------------------------
# rung 8: headless (only if installed)     rung 9: fabrication check
# ----------------------------------------------------------------------------

def rung_headless(ctx: Ctx) -> dict | None:
    if not shutil.which("agent-browser"):
        ctx.attempt("headless", "not installed")
        return None
    try:
        p = subprocess.run(["agent-browser", "read", ctx.url], capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        ctx.attempt("headless", f"{e.__class__.__name__}")
        return None
    text = (p.stdout or "").strip()
    g = gate(text) if p.returncode == 0 else f"exit {p.returncode}"
    if g != "passed":
        ctx.attempt("headless", g)
        return None
    ctx.attempt("headless", "agent-browser read")
    return make_result("headless", text, content_type="text/markdown", meta={"publisher": urlsplit(ctx.url).hostname}, final_url=ctx.url)


def fabrication_check(ctx: Ctx) -> tuple[str, str]:
    """Returns (status, fabrication_check). Survey §2.3 procedure, adapted:
    CDX prefix queries need authorization since 2026-09 (403), so the parent-path
    step is replaced by a host-root exact query, and `possibly-fabricated` is
    only concluded when DNS fails or the site itself answered 404/410; a 401/403
    with no captures stays `unfetchable` (paywall or bot wall are as likely)."""
    url, T = ctx.url, ctx.opts.timeout
    if not dns_resolves(url):
        return "possibly-fabricated", "dns-failure"
    rows = cdx_query(url, T, limit="1", status_200=False)
    if rows:
        return "unfetchable", "archived-captures-exist"
    if cc_lookup(url, T):
        return "unfetchable", "commoncrawl-hit"
    p = urlsplit(url)
    parent_path = p.path.rsplit("/", 1)[0] + "/" if "/" in p.path.strip("/") else "/"
    parent = urlunsplit((p.scheme, p.netloc, parent_path, "", ""))
    prows = cdx_query(parent, T, limit="1", prefix=True, status_200=False)
    if prows is None:  # prefix query refused or archive unreachable: fall back to host root, exact
        prows = cdx_query(urlunsplit((p.scheme, p.netloc, "/", "", "")), T, limit="1", status_200=False)
        evidence = "no-captures-host-archived"
    else:
        evidence = "no-captures-parent-has-captures"
    if prows:
        if ctx.raw_status in (404, 410) or evidence == "no-captures-parent-has-captures":
            return "possibly-fabricated", evidence
        return "unfetchable", evidence + f" (http {ctx.raw_status}; paywall or bot wall as likely as fabrication)"
    if rows is None and prows is None:
        return "unfetchable", "inconclusive (archive unreachable)"
    return "unfetchable", "inconclusive"


# ----------------------------------------------------------------------------
# orchestrator
# ----------------------------------------------------------------------------

def run_chain(url: str, opts) -> dict:
    ctx = Ctx(url, opts)
    rec = {"url": url, "final_url": None, "canonical_url": None, "title": None, "status": "unfetchable",
           "fetch_method": "none", "http_status": None, "content_type": None, "accessed": now_iso(),
           "snapshot_date": None, "extracted_chars": 0, "gate": "not-run", "robots": "not-checked",
           "evidence_strength": "paraphrase-only", "quote_safe": False, "published": None,
           "publisher": urlsplit(url).hostname, "attempts": ctx.attempts, "text_path": None, "fabrication_check": None}
    result = None
    for rung in (rung_keyless_api, rung_raw_http, rung_jina, rung_urltomarkdown, rung_wayback, rung_commoncrawl, rung_headless):
        if rung in (rung_jina, rung_urltomarkdown, rung_headless) and ctx.raw_status in (404, 410):
            ctx.attempt(rung.__name__.replace("rung_", "").replace("_", "-"), f"skipped: site answered {ctx.raw_status}")
            continue
        try:
            result = rung(ctx)
        except Exception as e:  # noqa: BLE001
            ctx.attempt(rung.__name__.replace("rung_", "").replace("_", "-"), f"crash {e.__class__.__name__}: {str(e)[:60]}")
            result = None
        if result:
            break
    rec["robots"] = ctx.robots
    if not result and ctx.partial.get("abstract") and len(ctx.partial["abstract"]) >= MIN_CHARS:
        ctx.attempt("keyless-api", "abstract-only (full text unavailable)")
        result = make_result("keyless-api", ctx.partial["abstract"], content_type="text/plain", meta=ctx.partial, final_url=url)
    if result:
        text = result["text"]
        rec.update({"status": "ok", "fetch_method": result["method"], "http_status": result["http_status"],
                    "content_type": result["content_type"], "snapshot_date": result["snapshot_date"],
                    "extracted_chars": len(text), "gate": "passed", "evidence_strength": result["evidence_strength"],
                    "quote_safe": result["quote_safe"], "final_url": result["final_url"] or url,
                    "canonical_url": result.get("canonical_url"),
                    "title": result.get("title") or ctx.partial.get("title"),
                    "published": result.get("published") or ctx.partial.get("published"),
                    "publisher": result.get("publisher") or ctx.partial.get("publisher") or rec["publisher"]})
        if opts.out:
            os.makedirs(os.path.dirname(os.path.abspath(opts.out)) or ".", exist_ok=True)
            with open(opts.out, "w", encoding="utf-8") as f:
                f.write(text)
            rec["text_path"] = f"raw/{opts.id}.txt" if opts.id else opts.out
        rec["_text"] = text
    else:
        failed_gates = [a["result"] for a in ctx.attempts if "failed:" in a["result"]]
        rec["gate"] = failed_gates[-1].split(" ")[-1] if failed_gates else "not-run"
        rec["http_status"] = ctx.raw_status
        if ctx.robots == "disallowed":
            rec["status"] = "skipped-robots"
            rec["fabrication_check"] = None
        else:
            status, fab = fabrication_check(ctx)
            rec["status"], rec["fabrication_check"] = status, fab
            ctx.attempt("fabrication-check", fab)
        rec["title"] = ctx.partial.get("title")
        rec["published"] = ctx.partial.get("published")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="keyless page fetch with fallback chain")
    ap.add_argument("url")
    ap.add_argument("--out", help="write extracted text here")
    ap.add_argument("--id", help="source number; sets text_path to raw/<id>.txt")
    ap.add_argument("--ignore-robots", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="ask the reader proxy for an uncached read")
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--max-bytes", type=int, default=10 * 1024 * 1024)
    ap.add_argument("--json", action="store_true", help="(default) print the JSON record")
    ap.add_argument("--print-text", action="store_true", help="also dump the text after the record")
    opts = ap.parse_args(argv)
    if not re.match(r"^https?://", opts.url, re.I):
        print(json.dumps({"error": "url must start with http:// or https://"}), file=sys.stderr)
        return 2
    rec = run_chain(opts.url, opts)
    text = rec.pop("_text", None)
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    if opts.print_text and text:
        print("-----TEXT-----")
        print(text)
    return 0 if rec["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
