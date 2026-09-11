# Role: extraction test (offline, one page)

This is an offline test of one extraction instruction. You are given one fetched page (raw text already on disk), the research question, and the hypothesis of the angle that fetched the page. Do not search, do not fetch, do not run any ledger command, do not read any other file. Read the whole page (`cat` it in parts if it is long), then extract claims exactly as the instruction below says, as if you were the researcher registering them.

Research question: {{QUESTION}}

Angle hypothesis (the frame the researcher was working in): {{HYPOTHESIS}}

Page: `{{PAGE}}` (raw text, verbatim quotes must be copied from it)

## Extraction instruction

{{STEP5 = step 5 of prompts/researcher.md, copied at fill time}}
{{VARIANT = empty for the control arm; for the treatment arm the C1 line: **Also register, as `supporting`, the page's own sentences that define or classify anything the question names**: what kind of body an institution is, the level or threshold a source treats as protective or as a limit, the rule that applies unless or instead, the grade or strength attached to a recommendation, and which standard governs which kind of question. These read as general knowledge next to your hypothesis; register them anyway, each with its verbatim sentence, because the report must state them and a `supporting` claim costs only a quote check. The preference for numbers over generalities does not apply to them.}}

{{GUIDE = the specifications/guidelines bullet of prompts/researcher.md, copied at fill time}}

## Output

Write `{{OUT}}` with a quoted shell heredoc (`cat > '{{OUT}}' <<'EOF' ... EOF`). One Markdown table, columns: `#`, `importance` (central / supporting / tangential), `claim` (your words, 25 words or fewer), `quote` (verbatim from the page, 10-60 words). Nothing else in the file. Do not edit any other file. When done, reply with the number of claims by importance.
