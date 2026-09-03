# Claude Code adapter

The core skill (`skill/deep-research/`) is harness-agnostic. This adapter only maps its roles onto Claude Code tools. Tested harness for round 1 (REQ 5).

## Install
```
# project-local
mkdir -p .claude/skills && ln -s "$(pwd)/skill/deep-research" .claude/skills/deep-research
# or user-wide
ln -s "$(pwd)/skill/deep-research" ~/.claude/skills/deep-research
```
Invoke with `/deep-research <question>` (optionally `--preset quick|standard|deep --mode brief|report --agents N --sequential --yes`).

## Tool mapping
| Skill concept | Claude Code |
|---|---|
| web search tool | `WebSearch` (results are pointers only) |
| researcher / verifier / writer agents | `Agent` tool, `subagent_type: general-purpose`, one call per role prompt; parallel = several Agent calls in one message |
| scripts | `Bash` running `python3 <skill dir>/scripts/...` |
| harness fetch | `WebFetch` may be used for *discovery* (is this page relevant?) but never for quotes; the scripts fetch raw text |
| plan checkpoint | `AskUserQuestion` or a plain message; skipped with `--yes` |

## Notes
- Subagents inherit no context: fill every placeholder in the role prompt (question, run dir, absolute scripts path, angle, hypothesis, round, targets).
- Pass the skill's absolute `scripts/` path; subagents run from the project cwd.
- `WebFetch` output is a model summary with a 125-character quote cap (see `research/literature/fetch-reliability-survey.md` §1.8); it is never `quote_safe`.
- Model choice for the pilot: generator = Sonnet for all roles, judge = Opus (REQ 4).
