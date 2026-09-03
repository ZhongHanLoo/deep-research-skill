#!/usr/bin/env bash
# End-to-end exercise of the scripts on live URLs (no model involved).
# Usage: tests/integration.sh [run-root]   (default: a temp dir)
set -u
S="$(cd "$(dirname "$0")/../scripts" && pwd)"
ROOT="${1:-$(mktemp -d)}"
L="python3 $S/ledger.py"
echo "root: $ROOT"
RUN=$($L init --question "What did the Transformer paper (Vaswani et al. 2017) change about sequence modelling?" --preset quick --mode brief --root "$ROOT" | python3 -c 'import json,sys;print(json.load(sys.stdin)["run"])') || exit 1
echo "run: $RUN"
L="python3 $S/ledger.py --run $RUN"
$L add-url "https://arxiv.org/abs/1706.03762" --angle paper --round 1
$L add-url "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)" --angle background --round 1
$L add-url "https://arxiv.org/abs/1706.03762" --angle paper --round 1   # dedup
$L add-url "https://www.nytimes.com/2023/03/14/technology/qzx-fake-article-9182.html" --angle fake --round 1
$L add-snippet "https://www.reuters.com/technology/" --snippet "Reuters technology section" --angle background --title "Reuters technology"
$L grade 1 --grade primary --published 2017-06-12 --publisher arXiv
$L grade 2 --grade secondary
# quote taken from raw/1.txt automatically: first sentence containing 'attention'
Q=$(python3 - "$RUN/raw/1.txt" <<'PY'
import re,sys
t=open(sys.argv[1],encoding='utf-8',errors='replace').read()
m=re.search(r'([^.\n]{40,200}attention[^.\n]{0,120}\.)', t, re.I)
print(m.group(1).strip() if m else '')
PY
)
echo "quote: $Q"
$L claim add --source 1 --angle paper --text "The Transformer relies on attention mechanisms." --quote "$Q" --importance central
$L claim add --source 1 --angle paper --text "Bad quote test." --quote "this sentence is definitely not in the paper text at all" --importance tangential; echo "exit(expected 3)=$?"
$L claim add --source 2 --angle background --text "Wikipedia claim with fake quote." --quote "zzz not present zzz" --importance supporting; echo "exit(expected 3)=$?"
$L claim add --source 4 --angle background --text "Snippet-only claim." --quote "Reuters technology section" --importance tangential
$L claim evidence c001 --supports 2 --note "Wikipedia describes the same architecture" --by v1
$L claims list --format md
$L state --format md | head -40
$L render
python3 $S/cite_check.py --run "$RUN" --no-network; echo "cite_check(no report yet) exit=$?"
cat > "$RUN/report.md" <<'MD'
# Transformer
**Question:** what changed.

## Summary
The Transformer relies on attention mechanisms [1][2]. Only a search snippet was available for [4], so it is weak evidence. Unknown cite [9]. Literal https://example.org/not-registered here.

## Sources
[1] arXiv
[2] Wikipedia
MD
python3 $S/cite_check.py --run "$RUN"; echo "cite_check exit=$?"
$L finalize --harness test --model none --agents 0 --rounds 1 --execution sequential
echo "---- sources.md"; cat "$RUN/sources.md"
echo "---- verification.md"; cat "$RUN/verification.md"
echo "---- run.json"; cat "$RUN/run.json"
