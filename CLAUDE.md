# Claude Code Training Lab

This repository contains an interactive HTML study guide and small Python examples for learning Claude Code and agent integrations. Read [README.md](README.md) for setup and usage.

## Project layout

- `claude-concepts-guide.html` — self-contained guide; open directly in a browser.
- `caching-example/` — API prompt-caching demonstrations; requests can incur API usage charges.
- `mcp-server/` — example MCP server; install dependencies from `requirements.txt`.
- `training-plugin/` — sample skill, subagent, and hooks.
- `src/` and `config/` — small training exercises and sample configuration.

There is no automated test suite or build system yet. For Python changes, run `python -m compileall src caching-example mcp-server training-plugin`. Validate plugin changes with `claude plugin validate ./training-plugin --strict` when Claude Code is installed. Keep credentials and machine-specific settings out of committed files.
