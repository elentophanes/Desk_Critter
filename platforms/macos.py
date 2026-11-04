# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
macOS. Tested on a real Mac; see README "macOS". Needs Python 3.13 (Tk 8.6): Tk 9.0 draws a black box.

Standard library only. What differs from Windows:
  - transparency uses tk's "-transparent" window attribute
  - the right-click menu also opens with Control-click (and tk calls the right button <Button-2>)
  - "is Claude in front?" asks the `lsappinfo` command
  - sounds (the critter's .wav files, or the Glass chime) are played with `afplay`
  - notifications are read (read-only) from macOS' notification database. macOS protects it:
    the program that runs Python (Terminal, or Python itself) needs
    System Settings > Privacy & Security > Full Disk Access. Without it the watcher keeps
    retrying and says so in desk_critter.log.
  - there is no taskbar-flash watcher (no equivalent on macOS)

If notifications aren't picked up, diag/notif_probe_mac.py shows whether the database can be read.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os
import plistlib
import subprocess
import threading
import time

from ._base import *                                   # noqa: F401,F403  (defaults)
from ._base import log, sqlite_ro_uri

NAME = "macos"
MENU_EVENTS = ("<Button-2>", "<Button-3>", "<Control-Button-1>")

# ---------------- Settings you may want to tweak ----------------
CLAUDE_APP_NAME = "Claude"                 # as shown in /Applications
ALERT_APP_MATCH = "claude"                 # frontmost app's name must contain this (lower case)
NOTIFY_APP_MATCH = "%claude%"              # SQL LIKE pattern for the notification's bundle id (lower case)
DOCK_HEIGHT = 90                           # px kept free at the bottom for the Dock
CHIME_SOUND = "/System/Library/Sounds/Glass.aiff"
RETRY_SECONDS = 30                         # how often to retry when the database can't be opened


# ---------------- window ----------------
def style_window(root):
    root.overrideredirect(True)            # no title bar
    # Tk/Cocoa bug (since macOS Big Sur): overrideredirect alone sometimes leaves the
    # native title bar with traffic-light buttons. Tk's own (Aqua-specific, long-standing,
    # NOT the same as real OS fullscreen) "plain" window style removes it cleanly.
    try:
        root.tk.call("::tk::unsupported::MacWindowStyle", "style", root._w, "plain", "none")
    except Exception as e:
        log(f"MacWindowStyle 'plain' not available: {e}")
    root.attributes("-topmost", True)
    try:
        root.attributes("-transparent", True)
        root.config(bg="systemTransparent")
        return "systemTransparent"
    except Exception as e:                 # very old Tk: plain window instead
        log(f"transparency not available: {e}")
        root.config(bg="#2B2B2B")
        return "#2B2B2B"


def work_area(root):
    # tk can't tell us where the Dock is; leave room for a Dock at the bottom.
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - DOCK_HEIGHT


def play_chime():
    try:
        subprocess.Popen(["afplay", CHIME_SOUND], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception:
        pass


def virtual_screen(root):
    # Main display only. A critter left on a second display returns to the corner after a restart.
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def frontmost_app():
    """Name of the app in front, lower case ('' if unknown)."""
    try:
        asn = subprocess.run(["lsappinfo", "front"], text=True, capture_output=True, timeout=2).stdout.strip()
        if not asn:
            return ""
        out = subprocess.run(["lsappinfo", "info", "-only", "name", asn],
                             text=True, capture_output=True, timeout=2).stdout
        return out.split("=", 1)[-1].strip().strip('"').lower()     # "LSDisplayName"="Claude"
    except Exception:
        return ""


def play_sound(path):
    try:
        subprocess.Popen(["afplay", path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return True
    except Exception as e:
        log(f"could not play {path}: {e}")
        return False


def claude_in_front():
    return ALERT_APP_MATCH in frontmost_app()


def open_claude():
    try:
        return subprocess.run(["open", "-a", CLAUDE_APP_NAME], timeout=10, capture_output=True).returncode == 0
    except Exception:
        return False


# ---------------- notification watcher ----------------
def notification_db_candidates():
    """Places macOS has kept its notification database (newest macOS first)."""
    paths = [os.path.expanduser("~/Library/Group Containers/group.com.apple.usernoted/db2/db")]
    try:
        d = subprocess.run(["getconf", "DARWIN_USER_DIR"], capture_output=True, text=True, timeout=5).stdout.strip()
        if d:
            paths.append(os.path.join(d, "com.apple.notificationcenter", "db2", "db"))
    except Exception:
        pass
    return paths


def notification_text(data):
    """Title | subtitle | body from one notification record (a binary property list)."""
    try:
        req = plistlib.loads(bytes(data)).get("req") or {}
    except Exception:
        return ""
    parts = [req.get(k) for k in ("titl", "subt", "body")]
    return " | ".join(p.strip() for p in parts if isinstance(p, str) and p.strip())


class NotificationWatcher(threading.Thread):
    """Polls macOS' notification database (read-only) for new Claude notifications."""

    QUERY = ("select r.rec_id, r.data from record r join app a on a.app_id = r.app_id "
             "where lower(a.identifier) like ? and r.rec_id > ? order by r.rec_id")
    LATEST = ("select max(r.rec_id) from record r join app a on a.app_id = r.app_id "
              "where lower(a.identifier) like ?")

    def __init__(self, on_text, poll_seconds):
        super().__init__(daemon=True)
        self.on_text = on_text
        self.poll_seconds = poll_seconds

    def run(self):
        last, said = None, None
        while True:
            try:
                con, path = self.connect()
            except Exception as e:
                msg = (f"notification watcher: cannot read the notification database ({e}). "
                       "Give Terminal/Python 'Full Disk Access' in System Settings > Privacy & Security; "
                       f"retrying every {RETRY_SECONDS} s")
                if msg != said:
                    log(msg)
                    said = msg
                time.sleep(RETRY_SECONDS)
                continue
            try:
                cur = con.cursor()
                if last is None:                        # ignore notifications from before we started
                    last = cur.execute(self.LATEST, (NOTIFY_APP_MATCH,)).fetchone()[0] or 0
                    log(f"notification watcher started (last Claude id {last}, {path})")
                    said = None
                for rid, data in cur.execute(self.QUERY, (NOTIFY_APP_MATCH, last)).fetchall():
                    last = max(last, rid)
                    self.on_text(notification_text(data))
            except Exception as e:
                log(f"notification watcher error: {e}")
            finally:
                con.close()
            time.sleep(self.poll_seconds)

    def connect(self):
        import sqlite3
        errors = []
        for path in notification_db_candidates():
            try:
                con = sqlite3.connect(sqlite_ro_uri(path), uri=True, timeout=2)
                con.execute("select count(*) from record").fetchone()
                return con, path
            except Exception as e:
                errors.append(f"{path}: {e}")
        raise OSError("; ".join(errors))


def start_watchers(on_text, on_flash, poll_seconds=1.5, watch_notifications=True, watch_flash=True):
    if watch_notifications:
        NotificationWatcher(on_text, poll_seconds).start()
