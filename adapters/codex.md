# Codex adapter (untested, 2026-09-03)

Codex was not installed on the build machine (`codex` not on PATH, 2026-09-02). The core skill needs only: a web search tool that returns URLs, a shell to run `python3 scripts/*.py`, and either a way to launch sub-agents or a willingness to run the role prompts one after another. Place `skill/deep-research/` where Codex discovers skills (`~/.agents/skills/` per the Agent Skills convention, or the project's `AGENTS.md` pointing at `SKILL.md`). Status: not tested in round 1 (REQ 5).
