# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
macOS: read-only probe of the notification database. Run this FIRST on the Mac:

    python3 diag/notif_probe_mac.py

and send back everything it prints. It shows whether the database can be opened
(Full Disk Access), which apps have notifications stored, and the latest Claude ones.
Nothing is changed.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os
import platform
import plistlib
import sqlite3
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("macOS", platform.mac_ver()[0], "| Python", platform.python_version(), "|", sys.executable)
# The probe itself doesn't need Tk; the critter does. Tk is checked in a separate process,
# because Apple's old built-in Tk can stop Python dead instead of raising an error.
try:
    r = subprocess.run([sys.executable, "-c", "import tkinter; print(tkinter.Tcl().eval('info patchlevel'))"],
                       text=True, capture_output=True, timeout=20)
    tk_version = r.stdout.strip() if r.returncode == 0 else ""
    tk_problem = (r.stderr.strip().splitlines() or ["exit code %d" % r.returncode])[-1]
except Exception as e:
    tk_version, tk_problem = "", repr(e)
if tk_version:
    print("Tk", tk_version, "(OK)" if tuple(int(n) for n in tk_version.split(".")[:2]) >= (8, 6)
          else "(TOO OLD for the critter window)")
else:
    print("Tk NOT usable:", tk_problem)
if not tk_version or tk_version.startswith("8.5"):
    print("  -> the critter window needs Tk 8.6 or newer. Install Python 3 from")
    print("     https://www.python.org/downloads/macos/ (its installer includes Tk),")
    print("     quit and reopen Terminal, and use that python3. The probe continues anyway.")
print()
if sys.platform != "darwin":
    sys.exit("This probe is for macOS.")

from platforms import macos                                              # noqa: E402

print("frontmost app:", repr(macos.frontmost_app()))

con = None
for path in macos.notification_db_candidates():
    try:
        c = sqlite3.connect(macos.sqlite_ro_uri(path), uri=True, timeout=2)
        n = c.execute("select count(*) from record").fetchone()[0]
        print(f"OPENED   {path}  ({n} records)")
        con = con or c
    except Exception as e:
        print(f"FAILED   {path}  -> {e}")
if con is None:
    sys.exit("\nCould not open the notification database.\n"
             "Open System Settings > Privacy & Security > Full Disk Access, switch it on for Terminal\n"
             "(or whichever app you run python3 from), quit and reopen Terminal, and run this again.")

print("\ntables:")
for name, sql in con.execute("select name, sql from sqlite_master where type='table' order by name"):
    print("  ", name, "::", " ".join((sql or "").split())[:200])

print("\napps with stored notifications:")
for ident, n in con.execute("select a.identifier, count(r.rec_id) from app a left join record r "
                            "on r.app_id = a.app_id group by a.identifier order by 2 desc limit 40"):
    mark = "  <-- Claude" if "claude" in (ident or "").lower() else ""
    print(f"  {n:4d}  {ident}{mark}")

print("\nlatest Claude notifications (pattern", macos.NOTIFY_APP_MATCH + "):")
rows = con.execute("select r.rec_id, a.identifier, r.data from record r join app a on a.app_id = r.app_id "
                   "where lower(a.identifier) like ? order by r.rec_id desc limit 8",
                   (macos.NOTIFY_APP_MATCH,)).fetchall()
if not rows:
    print("  none stored. Let Claude finish a reply while another app is in front, then run this again.")
for rid, ident, data in rows:
    print(f"  #{rid} {ident}: {macos.notification_text(data)!r}")
if rows:
    try:
        d = plistlib.loads(bytes(rows[0][2]))
        print("\nkeys of the newest record:", sorted(d))
        print("keys of its 'req' part:   ", sorted(d.get("req") or {}))
    except Exception as e:
        print("\ncould not decode the newest record:", e)
con.close()
