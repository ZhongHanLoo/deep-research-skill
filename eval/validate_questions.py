#!/usr/bin/env python3
"""Validate eval question files against the format in eval/private/README.md.

  validate_questions.py DIR   -> prints one line per file, exits 1 on any problem
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DOMAINS = {"technology", "science-health", "business-finance", "policy-law", "culture-history"}
TYPES = {"recall", "analysis", "instruction", "presentation"}


def check(q: dict, name: str) -> list[str]:
    p = []
    for k in ("id", "domain", "freshness", "mode", "preset", "question", "reference_documents", "rubric", "notes", "author", "written"):
        if k not in q:
            p.append(f"missing key {k}")
    if p:
        return p
    if q["id"] != name:
        p.append(f"id {q['id']} != filename {name}")
    if q["domain"] not in DOMAINS:
        p.append(f"bad domain {q['domain']}")
    if q["freshness"] not in ("post-cutoff", "stable"):
        p.append("freshness must be post-cutoff|stable")
    if q["mode"] not in ("report", "brief") or q["preset"] not in ("quick", "standard", "deep"):
        p.append("bad mode/preset")
    if len(q["question"].split()) < 15:
        p.append("question too short to carry a deliverable")
    if not q["reference_documents"]:
        p.append("no reference_documents")
    for r in q["reference_documents"]:
        if not re.match(r"^https?://", r.get("url", "")) or not re.match(r"^\d{4}-\d{2}-\d{2}$", r.get("accessed", "")):
            p.append(f"reference doc needs url + accessed date: {r}")
    items = q["rubric"]
    if not 8 <= len(items) <= 12:
        p.append(f"{len(items)} rubric items (need 8-12)")
    counts = {t: 0 for t in TYPES}
    ids = set()
    for it in items:
        if it.get("id") in ids:
            p.append(f"duplicate item id {it.get('id')}")
        ids.add(it.get("id"))
        if it.get("type") not in TYPES:
            p.append(f"{it.get('id')}: bad type {it.get('type')}")
            continue
        counts[it["type"]] += 1
        if not isinstance(it.get("weight"), (int, float)) or not 1 <= it["weight"] <= 3:
            p.append(f"{it['id']}: weight must be 1-3")
        if len(it.get("item", "").split()) < 5:
            p.append(f"{it['id']}: item text too short")
        if it["type"] == "recall" and not re.match(r"^https?://", it.get("evidence") or ""):
            p.append(f"{it['id']}: recall item needs an evidence URL")
    if not 5 <= counts["recall"] <= 8:
        p.append(f"{counts['recall']} recall items (need 5-8)")
    if not 2 <= counts["analysis"] <= 3:
        p.append(f"{counts['analysis']} analysis items (need 2-3)")
    if counts["instruction"] != 1 or counts["presentation"] != 1:
        p.append("need exactly 1 instruction and 1 presentation item")
    return p


def main() -> int:
    d = Path(sys.argv[1])
    bad = 0
    files = sorted(d.glob("*.json"))
    for f in files:
        try:
            q = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"{f.name}: invalid JSON ({e})"); bad += 1; continue
        probs = check(q, f.stem)
        if probs:
            bad += 1
            print(f"{f.name}: " + "; ".join(probs))
        else:
            print(f"{f.name}: ok ({len(q['rubric'])} items, {q['freshness']}, {len(q['reference_documents'])} refs)")
    print(f"{len(files)} files, {bad} with problems")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
