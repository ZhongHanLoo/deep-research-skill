# Writer test: W1 (draft-to-budget) and W3 (entity status rows), offline, paired on one run folder

An offline A/B of two writer-prompt changes from `decisions/backlog.md` (v1.4 candidates W1 and W3). Two writer agents, each on its own scratch copy of one finished skill run folder (ledger, brief, `sources.md`, `verification.md`, raw cache; `report.md`, `outline.md` and every judge or audit file removed), so neither touches the real run. No search, no fetch, no ledger writes beyond what the writer prompt already allows (none).

- **Control:** `skill/deep-research/prompts/writer.md` as tagged, filled with `eval/fill_prompts.py writer` against its copy.
- **Treatment:** the same filled prompt with four passages inserted at their anchors (below). Nothing else differs; the filled prompts differ only in the copy's path and these passages (checked with `diff`).

Each writer is launched as "cat this file and follow it" (Sonnet), writes `outline.md` then `report.md` in its copy, self-checks with `cite_check.py --no-network`, and reports its first-draft and final word counts. Then one Opus judge per report (`eval/fill_prompts.py judge` against each copy); compliance computed from `judge.json` and the rubric weights, never from the judge's own arithmetic.

## Measures
1. Does the report cite the target `supporting` claim (an entity's institutional-status sentence the C1 line registered and the live writer left unused), and state the status in prose?
2. First-draft and final word counts as reported by each writer, against the 1,500 target (the live writer of this run drafted 1,928 and finished at 1,726).
3. Rubric compliance of each report under the current judge line.
4. Writer tokens per arm.

## Treatment insertions (exact text; anchor = the sentence in `prompts/writer.md` the passage follows)

W1 (a), "Outline first", after "budgets summing to the length target":
> Assign claim ids to a section in proportion to its budget, at most one id per 20 words (a 150-word section carries seven or eight); a central claim that does not fit its section's budget goes into a key-findings or timeline row, or into a one-line "also established" list at the end of the section, never into an extra paragraph.

W3 (a), "Outline first", after "this table is where that shows before the report is judged.":
> Add one row per body, programme, rule or threshold the question names, headed "what it is / status", with the claim id that says what kind of body it is, the level it treats as protective, the rule that applies instead, or the grade attached to it; these are usually `supporting` claims. A row with no claim is a gap like any other.

W1 (b), "Rules", self-check bullet, after "the length ceiling is enforced there.":
> After drafting each section, count its words (`wc -w` on the section, or the script's count) and trim it to its budget before starting the next section; the whole draft is never longer than the target plus 10%.

W3 (b), "Rules", self-check bullet, after "sat unused in supporting claims)":
> , and one pass over the "what it is / status" rows of your coverage table: each fact there is one clause in the section that first names the entity, cited to its claim

## Cautions
One sample per arm on one question; a win here shows the passages reach the target on this ledger, not that they survive a live run. Both arms see the same claims, so a difference in compliance comes from writing alone. Filled prompts, outputs and `tokens.json` are private (`eval/private/experiments/writer-w1w3-<date>/`); this file carries no question text.
