# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Run any command and let the critter show how it went. Standard library only.

    py tools\\critter_run.py openscad -o part.stl part.scad
    py tools\\critter_run.py --name "ESP32 upload" arduino-cli upload -p COM5 --fqbn esp32:esp32:esp32 sketch
    python3 tools/critter_run.py make                                   (macOS)

While the command runs the critter shows its blue "working" dots. When it ends:
    exit code 0           green eyes and a wave     "openscad finished (2 min 13 s)"
    any other exit code   alert                     "openscad failed (exit 1, 4 s)"
    can't be started      alert                     "openscad: command not found"
    Ctrl+C                the dots just stop (no alert)

The command's own output appears as usual, and critter_run exits with the command's exit code,
so it can be used inside scripts. Options (before the command):
    --name TEXT   what to call the job in the critter's log (default: the program's name)
    --            end of options (needed only if the command itself starts with "--")

It writes to the same events file as the Claude Code hooks (see tools/critter_event.py), so the
critter needs no changes; any critter from v2.4 on shows the dots.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from critter_event import send          # writes the line the critter follows

TICK_SECONDS = 60      # "still working" this often; the critter drops the dots after 600 s of silence


def duration(seconds):
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} min {seconds} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def safe_send(kind, text, session):
    """Never let a problem with the events file break the user's command."""
    try:
        send(kind, text, session)
    except Exception as e:
        print(f"critter_run: could not tell the critter ({e})", file=sys.stderr)


def main(args):
    name, command = parse(list(args))
    if not command:
        print(__doc__.strip())
        return 2
    name = name or os.path.splitext(os.path.basename(command[0]))[0]
    session = f"run-{os.getpid()}"

    exe = shutil.which(command[0])
    if exe is None:
        safe_send("help", f"{name}: command not found ({command[0]})", session)
        safe_send("end", "", session)
        print(f"critter_run: command not found: {command[0]}", file=sys.stderr)
        return 127
    argv = [exe] + command[1:]
    use_shell = os.name == "nt" and exe.lower().endswith((".bat", ".cmd"))   # batch files need cmd.exe

    start = time.monotonic()
    safe_send("busy", f"{name} running", session)
    try:
        proc = subprocess.Popen(subprocess.list2cmdline(argv) if use_shell else argv, shell=use_shell)
    except OSError as e:
        safe_send("help", f"{name}: could not start ({e})", session)
        safe_send("end", "", session)
        print(f"critter_run: could not start {command[0]}: {e}", file=sys.stderr)
        return 126

    try:
        while True:
            try:
                code = proc.wait(timeout=TICK_SECONDS)
                break
            except subprocess.TimeoutExpired:
                safe_send("tick", f"{name} still running ({duration(time.monotonic() - start)})", session)
    except KeyboardInterrupt:                 # Ctrl+C reaches the command too; let it stop
        try:
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            proc.kill()
        safe_send("end", f"{name} interrupted", session)
        print(f"\ncritter_run: {name} interrupted", file=sys.stderr)
        return 130

    took = duration(time.monotonic() - start)
    if code == 0:
        text = f"{name} finished ({took})"
        safe_send("done", text, session)
    else:
        how = f"exit {code}" if code > 0 else f"stopped by signal {-code}"
        text = f"{name} failed ({how}, {took})"
        safe_send("help", text, session)
        safe_send("end", "", session)        # not working any more (the alert stays up)
    print(f"critter_run: {text}", file=sys.stderr)
    return code if code >= 0 else 1


def parse(args):
    name = None
    while args:
        if args[0] == "--name" and len(args) > 1:
            name, args = args[1], args[2:]
        elif args[0] == "--":
            args = args[1:]
            break
        else:
            break
    return name, args


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
