#!/usr/bin/env python3
"""Shared text matching for quote containment (stdlib only).

Used by ledger.py (at claim-add time) and cite_check.py (final pass).
"""
from __future__ import annotations

import re
import unicodedata

_TRANSLATE = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "‒": "-", "−": "-",
    "…": "...", " ": " ", "­": "",
}
_TRANS_TABLE = {ord(k): v for k, v in _TRANSLATE.items()}
_WS = re.compile(r"\s+")
_EDGE_PUNCT = re.compile(r"^[\s\"'.,;:!?()\[\]{}<>«»„“”‘’\-–—…*_`]+|[\s\"'.,;:!?()\[\]{}<>«»„“”‘’\-–—…*_`]+$")
_WORD = re.compile(r"[a-z0-9]+")


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(_TRANS_TABLE)
    s = s.lower()
    s = _WS.sub(" ", s)
    s = _EDGE_PUNCT.sub("", s)
    return s.strip()


def _words(s: str) -> list[str]:
    return _WORD.findall(normalize(s))


def _shingles(words: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def contains(quote: str, text: str, *, n: int = 6, threshold: float = 0.8) -> bool:
    """True if `quote` appears in `text` after normalisation.

    Exact normalised substring first; otherwise a word 6-gram shingle test
    (>= 80% of the quote's shingles present) for quotes of at least 8 words,
    which tolerates minor extraction differences (dropped footnote markers,
    hyphenation) without accepting paraphrase.
    """
    q = normalize(quote)
    if not q:
        return False
    t = normalize(text)
    if q in t:
        return True
    # Compare on word-only forms too (punctuation-insensitive exact match).
    qw = _words(quote)
    tw = _words(text)
    if len(qw) < 8:
        return " ".join(qw) in " ".join(tw) if qw else False
    if " ".join(qw) in " ".join(tw):
        return True
    qs = _shingles(qw, n)
    if not qs:
        return False
    ts = _shingles(tw, n)
    hit = sum(1 for sh in qs if sh in ts)
    return hit / len(qs) >= threshold


def best_window(quote: str, text: str, width: int = 300) -> str:
    """Return the slice of `text` (original form, whitespace-collapsed) with the
    highest word overlap with `quote`; for diagnostics when contains() is false."""
    flat = _WS.sub(" ", text or "")
    qw = set(_words(quote))
    if not qw or not flat:
        return ""
    best_i, best_score = 0, -1
    step = max(1, width // 3)
    for i in range(0, max(1, len(flat) - width + 1), step):
        win = flat[i:i + width]
        score = len(qw & set(_WORD.findall(normalize(win))))
        if score > best_score:
            best_i, best_score = i, score
    return flat[best_i:best_i + width]


if __name__ == "__main__":
    import sys
    q, path = sys.argv[1], sys.argv[2]
    body = open(path, encoding="utf-8", errors="replace").read()
    ok = contains(q, body)
    print("CONTAINED" if ok else "NOT FOUND")
    if not ok:
        print("nearest:", best_window(q, body))
    sys.exit(0 if ok else 1)
