# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Desk Critter hook: lets Claude Code tell the critter directly that it has finished or needs you,
whatever window is in front (Windows notifications only appear when Claude is NOT in front).

Claude Code runs this as a "hook" (see README, "Trigger while Claude is in front"):
    UserPromptSubmit hook ->  python critter_hook.py busy    a turn has started (working)
    PostToolUse hook      ->  python critter_hook.py tick    a tool call finished (still working)
    Notification hook     ->  python critter_hook.py help    Claude needs you
    Stop hook             ->  python critter_hook.py done    the turn has finished
    SessionEnd hook       ->  python critter_hook.py end     the session was closed

It appends one line to ~/.desk-critter/events.log, which the running critter watches:
    <unix time> TAB <kind> TAB <session id> TAB <text>
It never prints anything and always exits 0, so it can never block or slow Claude down.
Standard library only; does not import the critter.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import json
import os
import sys
import time

EVENTS_PATH = os.path.join(os.path.expanduser("~"), ".desk-critter", "events.log")
MAX_BYTES = 64 * 1024        # start the file afresh when it gets this big
KINDS = ("help", "done", "busy", "tick", "end")
DEFAULT_TEXT = {"help": "Claude Code needs you", "done": "Claude Code finished", "busy": "Claude Code is working",
                "tick": "Claude Code is working", "end": "Claude Code session closed"}


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in KINDS:
        return                               # unknown kind (newer settings, older script): do nothing
    kind = sys.argv[1] if len(sys.argv) > 1 else None
    info = {}
    try:                                     # Claude Code passes details as JSON on stdin
        if sys.stdin is not None and not sys.stdin.isatty():
            info = json.loads(sys.stdin.read() or "{}")
    except Exception:
        info = {}
    event = str(info.get("hook_event_name", ""))
    if kind is None:
        kind = "help" if event == "Notification" else "done"
    project = os.path.basename(str(info.get("cwd", "")).rstrip("\\/"))
    text = str(info.get("message") or DEFAULT_TEXT[kind])
    if kind == "tick" and info.get("tool_name"):
        text = f"used {info['tool_name']}"
    if project:
        text = f"{project} | {text}"
    text = " ".join(text.split())[:300]      # one line, no tabs or newlines
    session = "".join(str(info.get("session_id", "")).split())[:80]

    ensure_events_dir()
    mode = "a"
    try:
        if os.path.getsize(EVENTS_PATH) > MAX_BYTES:
            mode = "w"
    except OSError:
        pass
    with open(EVENTS_PATH, mode, encoding="utf-8") as f:
        f.write(f"{time.time():.3f}\t{kind}\t{session}\t{text}\n")


def ensure_events_dir():
    """Create the events folder readable by you only (it holds project names and Claude's messages)."""
    folder = os.path.dirname(EVENTS_PATH)
    os.makedirs(folder, exist_ok=True, mode=0o700)
    if os.name != "nt":
        try:
            os.chmod(folder, 0o700)          # also tighten a folder made by an older version
        except OSError:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
