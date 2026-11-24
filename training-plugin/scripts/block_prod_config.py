"""PreToolUse hook: block edits to production config files.

Claude Code passes the tool call as JSON on stdin. Exiting with code 2 blocks
the call, and whatever is written to stderr is shown to the agent as feedback.
"""
import json
import sys

PROTECTED = ("config/production", "config\\production")

event = json.load(sys.stdin)
file_path = event.get("tool_input", {}).get("file_path", "")

if any(part in file_path for part in PROTECTED):
    print(
        f"Blocked by training-plugin: {file_path} is a production config file and must not be edited.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
