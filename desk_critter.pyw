# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Desk Critter - a little critter on your desktop that waves when something has finished
and bounces when something needs you: Claude, a long render, a compile, any command.
Version 3.1  (right-click: About Desk Critter, Check for updates, Mute sounds; tests in a Test submenu)
             3.0: renamed and published as Desk_Critter; general-purpose events
             2.9: tools/critter_run.py: run any command; working dots while it runs, then green eyes or an alert
             2.8: tools/critter_mcp.py: Claude Desktop tools "wave" and "alert", so chats can signal the critter
             2.7: tools/critter_event.py: wave or alert on demand, e.g. after a normal Claude chat reply
             2.6: every critter has its own alert sound and a quiet "done" sound
             2.5: critters can have their own alert sound: the cat meows
             2.4: "working right now": bouncing dots while a Claude Code session is busy
             2.3: Claude Code hooks: react even while Claude is the window in front
             2.2: Windows / macOS specifics moved to platforms/; macOS support
             2.1: robot and ESP32 board light up green much more clearly when done
             2.0: multiple critters: spider, robot, cat, owl, ESP32 board
             1.x: the original spider (taskbar flash, notifications, remembered position, green eyes)

What it does
  - A critter sits on top of the taskbar, bottom-right, above other windows
  - It blinks, bobs gently and waves; waves faster when the mouse is over it
  - Double-click: opens the Claude desktop app (falls back to claude.ai in the browser)
  - Drag with the left mouse button to move it; the position is remembered
    until you choose "Back to corner"
  - Right-click: menu (Open Claude / Critter > ... / Test > Alert, Done, Working /
    Mute sounds / Clear alert / Back to corner / About Desk Critter / Check for updates / Quit)

Critters
  Each critter is a file in the critters/ folder (see critters/__init__.py).
  Pick one from the right-click "Critter" menu, or start with
      pyw .\\desk_critter.pyw --critter robot
  The last choice (and the position) is remembered in desk_critter_settings.json.
      pyw .\\desk_critter.pyw --list      (prints the available critters)

Signals
  - Events file (~/.desk-critter/events.log), written by:
      critter_hook.py              Claude Code hooks (working, finished, needs you)
      tools/critter_run.py         any command (working while it runs, then finished or failed)
      tools/critter_event.py       by hand or from a script
      tools/critter_mcp.py         Claude Desktop chats (tools "wave" and "alert")
  - New system notifications from the Claude app: "needs help" -> alert, anything else -> done
  - Backup (Windows): the Claude app flashing its taskbar button -> alert
  Alert: the critter bounces, waves fast, switches to its alert colours and plays its sound.
  Done: green eyes, a happy wave and a quiet sound. Working: three bouncing blue dots.
  Alert and done clear when you switch to Claude, hover over the critter, or click it. If Claude
  was already in front when it started, the critter keeps it up for FRONT_HOLD_SECONDS first.
  With DEBUG_LOG on, events are written to desk_critter.log next to this script.

This file is the same on every operating system. Everything Windows- or macOS-specific
(transparent window, notification watcher, sound, launching Claude) is in platforms/.

Requirements: Python 3 on Windows; on macOS Python 3.13 (Tk 8.6, see README "macOS"). Standard library only.
Save as .pyw so it runs without a console window (double-click the file).
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"

import argparse
import json
import math
import os
import platform
import queue
import re
import sys
import threading
import time
import tkinter as tk
import urllib.request
import webbrowser

VERSION = "3.1"
PROJECT_URL = "https://github.com/elentophanes/Desk_Critter"
UPDATES_URL = "https://api.github.com/repos/elentophanes/Desk_Critter/tags?per_page=100"   # only used on request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import critters                                         # noqa: E402  (needs HERE on sys.path)
from critters._painter import Painter, DW, DH          # noqa: E402
from platforms import current as plat                 # noqa: E402  (Windows / macOS specifics)

# ---------------- Settings you may want to tweak ----------------
DEFAULT_CRITTER = "spider"
SCALE = 0.55            # overall size (1.0 = about 230 x 170 px)
MARGIN_RIGHT = 20       # px from the right edge of the screen
FPS = 30                # animation frames per second
WAVE_PERIOD_IDLE = 2.8  # seconds per full wave, normal
WAVE_PERIOD_HOVER = 0.7 # seconds per full wave, when hovered
BLINK_EVERY = 4.5       # seconds between blinks
CLAUDE_URL = "https://claude.ai"   # last resort only

# Alert behaviour
ALERT_WAVE_PERIOD = 0.35   # seconds per wave while alerting
ALERT_HOP_HEIGHT = 14      # bounce height (design units)
ALERT_HOP_PERIOD = 0.45    # seconds per hop
ALERT_SOUND = True         # play the critter's alert sound (or the chime) when an alert starts
ALERT_SOUND_REPEAT = 0     # repeat that sound every N seconds while alerting (0 = once)
DEBUG_LOG = True           # log events to desk_critter.log
WATCH_NOTIFICATIONS = True # react to new system notifications from the Claude app
NOTIFY_POLL_SECONDS = 1.5  # how often to check for new notifications
WATCH_TASKBAR_FLASH = True # also react when Claude flashes its taskbar button

# "Done" behaviour (Claude finished something and doesn't need help): green eyes
# A notification containing any of these (lower case) means Claude NEEDS HELP -> full alert.
# Every other Claude notification counts as "done".
NEEDS_HELP_PHRASES = ("needs your input", "waiting for your input", "allow claude to",
                      "needs your permission")
DONE_WAVE_PERIOD = 1.2     # seconds per wave while the eyes are green
DONE_SOUND = False         # also play the chime for "done" (Windows already plays its own sound)
CRITTER_DONE_SOUNDS = True   # play the critter's own quiet "done" sound (SOUND_DONE) if it has one
FLASH_IGNORE_AFTER_DONE = 15   # seconds: a taskbar flash this soon after a "done" is not an alert

# Events file (critter_hook.py defines the path, the tools import it; keep this the same)
WATCH_EVENTS = True        # react to events: Claude Code hooks, critter_run, critter_event, critter_mcp
EVENTS_PATH = os.path.join(os.path.expanduser("~"), ".desk-critter", "events.log")
EVENT_POLL_SECONDS = 0.4   # how often to look for new events
FRONT_HOLD_SECONDS = 10    # if Claude is already in front when an alert/done starts, show it this long
EVENT_KINDS = ("help", "done", "busy", "tick", "end")

# "Working" (a Claude Code session is busy with a turn): three bouncing dots above the critter
WORKING_COLOUR = "#4FA8F7"
WORKING_DOT_PERIOD = 1.1   # seconds per bounce of the dots
WORKING_WAVE_PERIOD = 1.6  # seconds per wave while working
WORKING_TIMEOUT = 600      # seconds without any hook event before a session stops counting as working

LOG_PATH = os.path.join(HERE, "desk_critter.log")
SETTINGS_PATH = os.path.join(HERE, "desk_critter_settings.json")


def load_settings():
    """Settings dict: {"critter": name, "position": [x, y] or None}."""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def log(text):
    if not DEBUG_LOG:
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
    except Exception:
        pass


def version_key(text):
    """'v3.10' or '3.10' -> (3, 10); None if it isn't a major.minor version."""
    m = re.fullmatch(r"v?(\d+)\.(\d+)", text.strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        log(f"could not save settings: {e}")


def update_error_text(e):
    """Plain-language reason for a failed update check."""
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 404:
            return "GitHub didn't find the project (it may not be public yet)."
        if e.code == 403:
            return "GitHub is limiting requests right now; try again in an hour."
        return f"GitHub answered with an error ({e.code})."
    if isinstance(e, (urllib.error.URLError, TimeoutError, OSError)):
        return "No connection to GitHub (offline, or blocked by a firewall)."
    return "GitHub's answer wasn't what was expected."


def latest_version(timeout=6):
    """Ask GitHub for the newest vX.Y tag. Returns e.g. 'v3.2'. Raises on network/HTTP errors."""
    req = urllib.request.Request(UPDATES_URL, headers={"User-Agent": f"Desk-Critter/{VERSION}",
                                                       "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        tags = json.loads(r.read().decode("utf-8"))
    versions = [t["name"] for t in tags if isinstance(t, dict) and version_key(t.get("name", ""))]
    if not versions:
        raise ValueError("no version tags found")
    return max(versions, key=version_key)


def update_message(latest, current=VERSION):
    """(newer_available, text) for the 'Check for updates' window."""
    if version_key(latest) > version_key(current):
        return True, (f"Desk Critter {latest.lstrip('v')} is available (you have {current}).\n\n"
                      "To update, see README \"Updating\": git pull, then py tools\\install.py.\n\n"
                      "Open the project page?")
    return False, f"You have the latest version ({current})."


def installed_version():
    """The tag written by tools/install.py next to this file ("v3.1 (abc1234)"), or None when run from a repo."""
    try:
        with open(os.path.join(HERE, "INSTALLED_VERSION.txt"), encoding="utf-8") as f:
            return f.read().split("installed by")[0].strip() or None
    except OSError:
        return None


def play_critter_sound(critter, attr):
    """Play the critter's sound file named by attr (e.g. SOUND = "owl.wav", next to its .py).
    True if it played."""
    sound = getattr(critter, attr, None)
    if not sound:
        return False
    path = os.path.join(os.path.dirname(os.path.abspath(critter.__file__)), sound)
    return os.path.isfile(path) and plat.play_sound(path)


def about_text(critter_name, tk_version):
    installed = installed_version()
    return "\n".join([
        f"Desk Critter {VERSION}",
        f"Installed copy: {installed}" if installed else "Running from a repo folder (not an installed copy)",
        "",
        "A little critter that waves when something has finished",
        "and bounces when something needs you.",
        "",
        f"Critter: {critter_name}",
        f"Python {platform.python_version()}, Tk {tk_version}, {platform.system()} ({plat.NAME})",
        f"Folder: {HERE}",
        "",
        PROJECT_URL,
        "Copyright (c) 2026 Elentophanes and contributors",
        "Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).",
        "Commercial use requires a separate license (see COMMERCIAL.md).",
        "",
        "Works with the Claude apps; not affiliated with Anthropic.",
    ])


def kind_of(text):
    """'help' if the notification means Claude is waiting for the user, otherwise 'done'."""
    low = text.lower()
    return "help" if any(p in low for p in NEEDS_HELP_PHRASES) else "done"


def play_chime(critter=None):
    """The critter's own alert sound if it has one, else the chime."""
    if not play_critter_sound(critter, "SOUND"):
        plat.play_chime()


class EventWatcher(threading.Thread):
    """Follows the events file (one event per line: time TAB kind TAB session TAB text), written by
    critter_hook.py and the tools/critter_* scripts, and reports each new line. Same on every OS."""

    def __init__(self, on_event):
        super().__init__(daemon=True)
        self.on_event = on_event

    @staticmethod
    def size():
        try:
            return os.path.getsize(EVENTS_PATH)
        except OSError:
            return 0

    def run(self):
        offset = self.size()                    # ignore events from before we started
        log(f"event watcher started ({EVENTS_PATH})")
        while True:
            time.sleep(EVENT_POLL_SECONDS)
            try:
                size = self.size()
                if size < offset:               # the hook started the file afresh
                    offset = 0
                if size == offset:
                    continue
                with open(EVENTS_PATH, "rb") as f:
                    f.seek(offset)
                    chunk = f.read()
                end = chunk.rfind(b"\n") + 1    # only complete lines
                offset += end
                for line in chunk[:end].decode("utf-8", "replace").splitlines():
                    parts = line.split("\t")       # time, kind, session, text (2.3: no session)
                    if len(parts) >= 3 and parts[1] in EVENT_KINDS:
                        session = parts[2] if len(parts) >= 4 else ""
                        self.on_event(parts[1], session, parts[-1])
            except Exception as e:
                log(f"event watcher error: {e}")


class TkPainter(Painter):
    """Painter backend that draws on a tkinter Canvas."""

    def __init__(self, canvas, scale):
        super().__init__(scale)
        self.c = canvas

    def _poly(self, pts, colour):
        flat = [v for pt in pts for v in pt]
        self.c.create_polygon(*flat, fill=colour, outline="")

    def _line(self, pts, colour, width):
        flat = [v for pt in pts for v in pt]
        self.c.create_line(*flat, fill=colour, width=width,
                           capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def _oval(self, x1, y1, x2, y2, colour):
        self.c.create_oval(x1, y1, x2, y2, fill=colour, outline="")


class DeskCritter:
    def __init__(self, critter_name=None):
        self.critters = critters.discover(log)
        if not self.critters:
            raise SystemExit("No critters found in the critters/ folder.")
        self.settings = load_settings()
        self.update_result = None                 # set by the update-check thread, shown by the tk loop
        self.update_pending = threading.Event()
        name = critter_name or self.settings.get("critter") or DEFAULT_CRITTER
        if name not in self.critters:
            log(f"critter '{name}' not found, using '{DEFAULT_CRITTER}'")
            name = DEFAULT_CRITTER if DEFAULT_CRITTER in self.critters else next(iter(self.critters))

        plat.init(log)
        self.s = SCALE * plat.dpi_scale()          # must come before the window is created

        self.root = tk.Tk()
        self.root.title(f"Desk Critter {VERSION}")
        background = plat.style_window(self.root)  # borderless, on top, see-through

        self.w = int(DW * self.s)
        self.h = int(DH * self.s)
        self.canvas = tk.Canvas(self.root, height=self.h, width=self.w,
                                highlightthickness=0, bg=background)
        self.canvas.pack()
        self.painter = TkPainter(self.canvas, self.s)

        self.hover = False
        self.phase = 0.0
        self.bob = 0.0
        self.last = time.monotonic()
        self.start = self.last
        self.drag_from = None
        self.dragged = False

        # Alert state. The watcher threads only set a flag; the tk loop acts on it.
        self.alert = False
        self.alert_since = 0.0
        self.last_chime = 0.0
        self.flash_pending = threading.Event()
        self.next_fg_check = 0.0
        # "Done" state (green eyes), set the same way by the notification watcher.
        self.done = False
        self.done_pending = threading.Event()
        self.help_pending = threading.Event()
        self.last_done = -1e9
        # "Working" state: Claude Code sessions reported by the hooks, {session id: [state, last seen]}
        self.sessions = {}
        self.finished = set()                      # sessions whose turn has ended
        self.working = False
        self.event_queue = queue.Queue()

        # Menu, with a "Critter" submenu listing every critter
        self.critter_var = tk.StringVar(value=name)
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(command=self.open_claude, label="Open Claude")
        critter_menu = tk.Menu(self.menu, tearoff=0)
        for key, mod in self.critters.items():
            critter_menu.add_radiobutton(value=key, label=mod.NAME, command=lambda k=key: self.switch_critter(k),
                                       variable=self.critter_var)
        self.menu.add_cascade(label="Critter", menu=critter_menu)
        test_menu = tk.Menu(self.menu, tearoff=0)
        test_menu.add_command(command=self.start_alert, label="Alert")
        test_menu.add_command(command=self.start_done, label="Done (green eyes)")
        test_menu.add_command(command=self.test_working, label="Working (dots, 8 s)")
        self.menu.add_cascade(menu=test_menu, label="Test")
        self.mute_var = tk.BooleanVar(value=bool(self.settings.get("mute")))
        self.menu.add_checkbutton(variable=self.mute_var, label="Mute sounds", command=self.toggle_mute)
        self.menu.add_command(label="Clear alert", command=self.clear_alert)
        self.menu.add_command(label="Back to corner", command=self.back_to_corner)
        self.menu.add_separator()
        self.menu.add_command(command=self.show_about, label="About Desk Critter…")
        self.menu.add_command(label="Check for updates…", command=self.check_updates)
        self.menu.add_command(command=self.root.destroy, label="Quit")

        c = self.canvas
        c.bind("<Enter>", self.on_enter)
        c.bind("<Leave>", lambda e: self.set_hover(False))
        c.bind("<Double-Button-1>", self.open_claude)
        c.bind("<ButtonPress-1>", self.drag_start)
        c.bind("<B1-Motion>", self.drag_move)
        c.bind("<ButtonRelease-1>", self.drag_end)
        for event in plat.MENU_EVENTS:
            c.bind(event, self.show_menu)

        self.switch_critter(name)
        self.place_at_start()
        self.keep_on_top()
        self.tick()
        # Look up the Claude app in the background so the first double-click is instant
        threading.Thread(target=plat.warm_up, daemon=True).start()
        plat.start_watchers(self.on_notification, self.flash_pending.set, NOTIFY_POLL_SECONDS,
                            WATCH_NOTIFICATIONS, WATCH_TASKBAR_FLASH)
        if WATCH_EVENTS:
            EventWatcher(self.on_event).start()
        log(f"platform: {plat.NAME}")

    # ---------- critters ----------
    def switch_critter(self, key):
        self.critter_key = key
        self.critter = self.critters[key]
        self.critter_var.set(key)
        self.root.title(f"Desk Critter {VERSION} - {self.critter.NAME}")
        if self.settings.get("critter") != key:
            self.settings["critter"] = key
            save_settings(self.settings)
        log(f"critter: {key}")

    # ---------- window behaviour ----------
    def place_in_corner(self):
        left, top, right, bottom = plat.work_area(self.root)
        x = right - self.w - MARGIN_RIGHT
        y = bottom - self.h
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")

    def place_at_start(self):
        """Go where the user last dragged us, if that spot is still on a screen."""
        pos = self.settings.get("position")
        if pos:
            try:
                x, y = int(pos[0]), int(pos[1])
                left, top, right, bottom = plat.virtual_screen(self.root)
                if left <= x <= right - self.w and top <= y <= bottom - self.h:
                    self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")
                    return
                log(f"saved position {pos} is off-screen, using the corner")
            except Exception:
                pass
        self.place_in_corner()

    def back_to_corner(self):
        self.place_in_corner()
        self.settings["position"] = None
        save_settings(self.settings)

    def muted(self):
        return bool(self.settings.get("mute"))

    def toggle_mute(self):
        """Menu: Mute sounds (remembered). The critter still bounces and waves."""
        self.settings["mute"] = bool(self.mute_var.get())
        save_settings(self.settings)
        log(f"sounds {'muted' if self.settings['mute'] else 'on'}")

    def check_updates(self):
        """Menu: ask GitHub for the newest version, in the background (only when the user asks)."""
        if getattr(self, "_checking", False):
            return
        self._checking = True
        log("checking for updates")

        def work():
            try:
                self.update_result = ("ok", latest_version())
            except Exception as e:
                log(f"update check error: {e!r}")
                self.update_result = ("error", update_error_text(e))
            self.update_pending.set()

        threading.Thread(target=work, daemon=True).start()

    def show_update_result(self):
        """tk thread: show what the update check found."""
        from tkinter import messagebox                  # only needed here
        self._checking = False
        status, value = self.update_result
        if status == "error":
            log(f"update check failed: {value}")
            messagebox.showinfo("Check for updates", f"Couldn't check for updates.\n\n{value}",
                                parent=self.root)
            return
        newer, text = update_message(value)
        log(f"update check: newest {value}, running {VERSION}")
        if newer:
            if messagebox.askyesno("Check for updates", text, parent=self.root):
                webbrowser.open(PROJECT_URL)
        else:
            messagebox.showinfo("Check for updates", text, parent=self.root)

    def keep_on_top(self):
        # Clicking the taskbar can push us behind it; re-assert every 2 s.
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.after(2000, self.keep_on_top)

    def show_about(self):
        """Menu: a small window with the version and where this copy runs from."""
        from tkinter import messagebox                  # only needed here
        try:
            tk_version = self.root.tk.call("info", "patchlevel")
        except Exception:
            tk_version = "?"
        log(f"about: version {VERSION}")
        messagebox.showinfo("About Desk Critter", about_text(self.critter.NAME, tk_version), parent=self.root)

    def on_enter(self, _e):
        self.set_hover(True)
        self.clear_alert()

    def set_hover(self, on):
        self.hover = on

    def drag_move(self, e):
        if self.drag_from:
            dx, dy = self.drag_from
            self.root.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")
            self.dragged = True

    def drag_start(self, e):
        self.clear_alert()
        self.drag_from = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())
        self.dragged = False

    def show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def drag_end(self, _e):
        if self.drag_from and self.dragged:     # a plain click doesn't count as a move
            self.settings["position"] = [self.root.winfo_x(), self.root.winfo_y()]
            save_settings(self.settings)
        self.drag_from = None

    # ---------- alerts ----------
    def on_notification(self, text):
        """Called from the watcher thread with a notification's text: only set a flag."""
        kind = kind_of(text)
        log(f"Claude notification ({kind}): {text}")
        (self.help_pending if kind == "help" else self.done_pending).set()

    def on_event(self, kind, session, text):
        """Called from the event watcher thread: only queue it for the tk loop."""
        if kind != "tick":                       # ticks arrive after every tool call: too noisy
            log(f"event ({kind}): {text}")
        self.event_queue.put((kind, session))

    def test_working(self):
        """Menu: pretend a session is working for a few seconds."""
        self.sessions["(test)"] = ["busy", time.monotonic() - WORKING_TIMEOUT + 8]

    def apply_event(self, kind, session, now):
        """Keep track of which Claude Code sessions are working (tk thread)."""
        if kind == "busy":                       # the user sent a prompt: a turn has started
            self.sessions[session] = ["busy", now]
            self.finished.discard(session)
        elif kind == "tick":                     # a tool call finished: still working
            if session not in self.finished:     # (a late tick must not undo "finished")
                self.sessions[session] = ["busy", now]
        elif kind == "help":                     # waiting for the user, so not working
            self.sessions[session] = ["wait", now]
            self.start_alert()
        elif kind == "done":
            self.sessions.pop(session, None)
            if len(self.finished) > 200:
                self.finished.clear()
            self.finished.add(session)
            self.start_done()
        elif kind == "end":                      # the session was closed
            self.sessions.pop(session, None)
            self.finished.discard(session)

    def first_fg_check(self, now):
        """When to start auto-clearing. Normally after a moment, once the user switches to Claude.
        If Claude is ALREADY in front (the user is looking at it), keep the signal up for a while."""
        return now + (FRONT_HOLD_SECONDS if self.claude_in_front() else 1.0)

    def draw_working_dots(self, t):
        """Three bouncing dots above the critter, like a typing indicator. Drawn by the core so
        every critter gets them without changes."""
        self.painter.dy = 0
        for i, x in enumerate((328, 340, 352)):
            lift = max(0.0, math.sin(math.pi * 2 * t / WORKING_DOT_PERIOD - i * 0.9))
            self.painter.oval(x, 88.5 - lift * 3.5, 3.4, 3.4, WORKING_COLOUR)

    def start_alert(self):
        now = time.monotonic()
        self.done = False
        if not self.alert:
            self.alert = True
            self.alert_since = now
            self.next_fg_check = self.first_fg_check(now)
            if ALERT_SOUND and not self.muted():
                play_chime(self.critter)
                self.last_chime = now

    def start_done(self):
        """Claude finished and doesn't need help: green eyes, no fuss."""
        now = time.monotonic()
        self.last_done = now
        if not self.alert and not self.done:   # a real alert takes priority
            self.done = True
            self.next_fg_check = self.first_fg_check(now)
            if self.muted():
                pass
            elif CRITTER_DONE_SOUNDS and play_critter_sound(self.critter, "SOUND_DONE"):
                pass
            elif DONE_SOUND:
                play_chime(self.critter)

    def claude_in_front(self):
        return plat.claude_in_front()

    def clear_alert(self):
        self.alert = False
        self.done = False

    # ---------- launching Claude ----------
    def open_claude(self, _event=None):
        self.clear_alert()
        if not plat.open_claude():
            webbrowser.open(CLAUDE_URL)

    # ---------- animation loop ----------
    def tick(self):
        now = time.monotonic()
        dt, self.last = now - self.last, now
        t = now - self.start

        # Did the Claude app flash its taskbar button or post a notification?
        if self.done_pending.is_set():
            self.done_pending.clear()
            self.start_done()
        if self.flash_pending.is_set():
            self.flash_pending.clear()
            # Claude may also flash its taskbar button for a "done" notification;
            # that must not turn the green eyes into a full alert.
            if now - self.last_done >= FLASH_IGNORE_AFTER_DONE:
                self.start_alert()
        if self.help_pending.is_set():
            self.help_pending.clear()
            self.start_alert()
        if self.update_pending.is_set():
            self.update_pending.clear()
            self.show_update_result()

        # Events (hooks, commands, chats), and which sessions are working right now
        while True:
            try:
                kind, session = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self.apply_event(kind, session, now)
        for session in [s for s, (_state, seen) in self.sessions.items() if now - seen > WORKING_TIMEOUT]:
            del self.sessions[session]           # no sign of life: closed or crashed mid-turn
        self.working = any(state == "busy" for state, _seen in self.sessions.values())

        if self.alert or self.done:
            # Auto-clear when the user brings Claude to the front
            if self.next_fg_check <= now:
                self.next_fg_check = now + 0.5
                if self.claude_in_front():
                    self.clear_alert()
        if self.alert:
            if ALERT_SOUND and ALERT_SOUND_REPEAT and not self.muted() and ALERT_SOUND_REPEAT <= now - self.last_chime:
                play_chime(self.critter)
                self.last_chime = now

        if self.alert:
            period = ALERT_WAVE_PERIOD
        elif self.done:
            period = DONE_WAVE_PERIOD
        elif self.hover:
            period = WAVE_PERIOD_HOVER
        else:
            period = WORKING_WAVE_PERIOD if self.working else WAVE_PERIOD_IDLE
        self.phase += dt * 2 * math.pi / period
        wave_deg = -1 + 13 * math.sin(self.phase)       # swings about +12 .. -14 degrees

        if self.alert:
            self.bob = -ALERT_HOP_HEIGHT * abs(math.sin(math.pi * (now - self.alert_since) / ALERT_HOP_PERIOD))
        else:
            self.bob = -1 - math.cos(math.pi * 2 * t / 2.6)  # 0 .. -2 design units
        blink = (t % BLINK_EVERY) > (BLINK_EVERY - 0.15)

        frame = critters.Frame(wave=wave_deg, t=t, blink=blink, alert=self.alert,
                              hover=self.hover, done=self.done, busy=self.working)
        colours = self.critter.COLOURS["alert" if self.alert else "normal"]
        self.canvas.delete("all")
        self.painter.dy = self.bob
        try:
            self.critter.draw(self.painter, frame, colours)
            if self.working and not self.alert:      # the alert bounce needs the headroom
                self.draw_working_dots(t)
        except Exception as e:                       # a buggy critter falls back to the spider
            log(f"critter '{self.critter_key}' failed to draw: {e!r}")
            if self.critter_key != DEFAULT_CRITTER and DEFAULT_CRITTER in self.critters:
                self.switch_critter(DEFAULT_CRITTER)
        self.root.after(int(1000 / FPS), self.tick)

    def run(self):
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description="Desk Critter - waves when something finishes, bounces when something needs you")
    ap.add_argument("--critter", help="which critter to show (file name in critters/, e.g. robot)")
    ap.add_argument("--list", help="list the available critters and exit", action="store_true")
    args = ap.parse_args()
    if args.list:
        for key, mod in critters.discover(print).items():
            print(f"{key:10} {mod.NAME}")
        return
    DeskCritter(args.critter).run()


if __name__ == "__main__":
    main()
