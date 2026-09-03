# Hermes adapter (untested, 2026-09-03)

Hermes Agent loads skills from `~/.hermes/skills/<category>/<skill>/SKILL.md` and uses the same Agent Skills frontmatter (`name`, `description`; optional `version`, `license`, `platforms`, `metadata.hermes.tags`) as the core skill, so it can be linked in unchanged:

```
mkdir -p ~/.hermes/skills/research && ln -s "$(pwd)/skill/deep-research" ~/.hermes/skills/research/deep-research
```

Mapping: web search = Hermes's web search tool; agents = Hermes delegation if enabled, otherwise run the role prompts sequentially in the main session (the run folder is identical); scripts = shell tool with `python3`. Hermes ships its own `grounded-citations` ledger; this skill does not depend on it (REQ 9: standalone). Status: not tested in round 1 (REQ 5).
