# Claude Code Training Lab

An independent, hands-on learning workspace for Claude Code and related agent integrations. It is not official Anthropic training.

## What is here

- `docs/claude-concepts-guide.html` — an interactive study guide with lessons and quizzes on permissions, skills, hooks, plugins, MCP, caching, code review, and enterprise security. Open it in a browser; it has no build step.
- `caching-example/` — Python examples that compare prompt-caching patterns. Running them sends requests to the Anthropic API and may incur usage charges.
- `mcp-server/` — a small in-memory MCP server that demonstrates tools, resources, and prompts.
- `training-plugin/` — a sample plugin with a skill, read-only reviewer, and hooks.
- `.claude/`, `src/`, and `config/` — project configuration and small exercises used by the guide.

## Python examples

Requires Python 3.10 or later. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate` instead. Set `ANTHROPIC_API_KEY` in your environment before running the caching demo:

```powershell
python caching-example/cache_demo.py automatic
```

The MCP server is configured in `.mcp.json` to launch with `python`; start Claude Code from the activated environment so it uses the interpreter where the requirements are installed.

## Safety and sharing

Examples are for learning, not production controls. Review any settings and hook before enabling them in another project. Never put API keys or other credentials in tracked files; the local Claude settings file is excluded by `.gitignore`.

No license is included yet. Until one is chosen, the default copyright rules apply; public visibility alone does not grant permission to reuse this material. Check that you have permission to publish any course-derived material before sharing it.
