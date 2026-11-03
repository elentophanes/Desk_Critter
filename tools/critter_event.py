# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Make the running critter wave or alert on demand: from you, a script, or Claude.

    py tools\\critter_event.py done                    green eyes and a happy wave
    py tools\\critter_event.py help                    alert: bounce, alert colours, sound
    py tools\\critter_event.py done "Report ready"      with your own text (shown in the critter's log)
    python3 tools/critter_event.py done               (macOS)

Use it at the end of your own scripts, or anywhere a program can run a command. (To run a command
AND get the working dots while it runs, use tools/critter_run.py instead. For Claude Desktop chats
there is tools/critter_mcp.py.) send() is also the shared writer the other tools use.

It appends one line to the events file the critter follows (~/.desk-critter/events.log):
    <unix time> TAB <kind> TAB manual TAB <text>
The critter follows that file and reacts within half a second. Standard library only.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from critter_hook import EVENTS_PATH, MAX_BYTES     # same file and size limit as the hook

KINDS = ("done", "help")                                  # what the command line accepts
ALL_KINDS = ("done", "help", "busy", "tick", "end")       # what send() accepts (critter_run.py uses all)
DEFAULT_TEXT = {"done": "finished", "help": "needs you", "busy": "working",
                "tick": "still working", "end": "stopped"}
SESSION = "manual"


def send(kind, text="", session=SESSION):
    """Append one event line for the critter. Returns the text that was sent."""
    if kind not in ALL_KINDS:
        raise ValueError(f"kind must be one of {ALL_KINDS}")
    text = " ".join(str(text).split())[:300] or DEFAULT_TEXT[kind]     # one line, no tabs
    os.makedirs(os.path.dirname(EVENTS_PATH), exist_ok=True)
    mode = "a"
    try:
        if os.path.getsize(EVENTS_PATH) > MAX_BYTES:
            mode = "w"                   # start afresh, like the hook (the critter notices)
    except OSError:
        pass
    with open(EVENTS_PATH, mode, encoding="utf-8") as f:
        f.write(f"{time.time():.3f}\t{kind}\t{session}\t{text}\n")
    return text


def main(args):
    if not args or args[0] not in KINDS:
        print(__doc__.strip())
        return 2
    text = send(args[0], " ".join(args[1:]))
    print(f"sent '{args[0]}' to the critter: {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
