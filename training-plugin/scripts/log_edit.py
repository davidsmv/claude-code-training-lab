"""PostToolUse hook: append every edited file to an audit log.

The tool call has already happened, so this hook cannot block it. The log is
written to the project being worked on (not the plugin folder), because the
plugin may be installed somewhere else.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

event = json.load(sys.stdin)
tool = event.get("tool_name", "?")
file_path = event.get("tool_input", {}).get("file_path", "?")
project_dir = Path(event.get("cwd", "."))

log = project_dir / ".claude" / "plugin-audit.log"
log.parent.mkdir(parents=True, exist_ok=True)
with log.open("a", encoding="utf-8") as f:
    f.write(f"{datetime.now().isoformat(timespec='seconds')} {tool} {file_path}\n")

sys.exit(0)
