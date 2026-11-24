"""PostToolUse hook: append every edited file to an audit log.

The tool call has already happened, so this hook cannot block it. It is the
right place for side effects such as logging, formatting, or running tests.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

event = json.load(sys.stdin)
tool = event.get("tool_name", "?")
file_path = event.get("tool_input", {}).get("file_path", "?")

log = Path(__file__).parent / "audit.log"
with log.open("a", encoding="utf-8") as f:
    f.write(f"{datetime.now().isoformat(timespec='seconds')} {tool} {file_path}\n")

sys.exit(0)
