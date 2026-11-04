# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Defaults for every platform. windows.py and macos.py start with
`from ._base import *` and replace what they can do better.

The contract (what desk_critter.pyw calls):
    NAME                      short name for the log
    MENU_EVENTS               tk events that open the right-click menu
    init(log_func)            give the platform code the core's log function
    dpi_scale()               call BEFORE creating the tk window; returns the DPI factor
    style_window(root)        make the window borderless, on top and see-through;
                              returns the background colour the canvas must use
    work_area(root)           (left, top, right, bottom) of the screen minus taskbar/Dock
    virtual_screen(root)      (left, top, right, bottom) of all monitors together
    play_chime()              the alert sound
    play_sound(path)          play a .wav file (a critter's own sound); False if it can't
    claude_in_front()         True if the Claude app is the foreground window
    warm_up()                 optional slow preparation, run in a background thread
    open_claude()             start / bring up the Claude app; True if it worked
    start_watchers(on_text, on_flash, poll_seconds, watch_notifications, watch_flash)
                              start background threads that call
                                  on_text(text)   for every new Claude notification
                                  on_flash()      when Claude flashes its taskbar button
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
TRANSPARENT = "#ff00fe"   # on Windows this exact colour becomes see-through
NAME = "generic"
MENU_EVENTS = ("<Button-3>",)

_log = [lambda text: None]


def log(text):
    _log[0](text)


def init(log_func):
    _log[0] = log_func


def sqlite_ro_uri(path):
    """'file:...?mode=ro' for sqlite3.connect(..., uri=True). The path is URL-quoted, so a '#', '?'
    or '%' in it (e.g. in a user name) cannot cut off '?mode=ro' and open the file read-write."""
    from urllib.request import pathname2url
    return "file:" + pathname2url(path) + "?mode=ro"


def dpi_scale():
    return 1.0


def style_window(root):
    root.overrideredirect(True)          # no border, no taskbar button
    root.attributes("-topmost", True)
    root.config(bg=TRANSPARENT)
    return TRANSPARENT                   # no transparency here: shows a magenta box


def work_area(root):
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 48


def play_chime():
    pass


def virtual_screen(root):
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def play_sound(path):
    return False


def claude_in_front():
    return False


def warm_up():
    pass


def open_claude():
    return False


def start_watchers(on_text, on_flash, poll_seconds=1.5, watch_notifications=True, watch_flash=True):
    log("no notification watcher on this operating system")
