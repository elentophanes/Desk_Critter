# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Windows 10/11: transparent window, notification-store watcher, taskbar-flash
watcher, launching the Claude Store app. Standard library only (ctypes, sqlite3, winsound).
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import ctypes
import os
import re
import subprocess
import threading
import time
from ctypes import wintypes

from ._base import *                                   # noqa: F401,F403  (defaults)
from ._base import TRANSPARENT, log, sqlite_ro_uri

NAME = "windows"

# ---------------- Settings you may want to tweak ----------------
ALERT_PROCESS_MATCH = "claude"         # a window's program name must contain this to count as Claude
NOTIFY_APP_MATCH = "Claude_%!Claude"   # SQL LIKE pattern for Claude's notification AppID

# Where the Claude desktop app might be installed (checked in order).
_LA = os.environ.get("LOCALAPPDATA", "")
_PF = os.environ.get("ProgramFiles", r"C:\Program Files")
CLAUDE_EXE_CANDIDATES = [
    os.path.join(_LA, "AnthropicClaude", "claude.exe"),
    os.path.join(_LA, "Programs", "Claude", "Claude.exe"),
    os.path.join(_LA, "Programs", "claude-desktop", "Claude.exe"),
    os.path.join(_PF, "Claude", "Claude.exe"),
    os.path.join(_PF, "AnthropicClaude", "claude.exe"),
]
# Optional: paste the AppID from  Get-StartApps | ? Name -like "*Claude*"
# here to skip auto-detection, e.g. "Claude_xxxxx!Claude"
CLAUDE_APP_ID = ""


# ---------------- window ----------------
def dpi_scale():
    """Keep the critter crisp on high-DPI screens. Returns the DPI scale factor."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    try:
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except Exception:
        return 1.0


def style_window(root):
    root.overrideredirect(True)          # no border, no taskbar button
    root.attributes("-topmost", True)
    root.config(bg=TRANSPARENT)
    root.attributes("-transparentcolor", TRANSPARENT)
    return TRANSPARENT


def work_area(root):
    """Screen area not covered by the taskbar: (left, top, right, bottom)."""
    r = wintypes.RECT()
    if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):   # SPI_GETWORKAREA
        return r.left, r.top, r.right, r.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 48


def virtual_screen(root):
    """Bounding box of all monitors together: (left, top, right, bottom)."""
    gsm = ctypes.windll.user32.GetSystemMetrics
    x, y, w, h = gsm(76), gsm(77), gsm(78), gsm(79)    # SM_X/Y/CX/CYVIRTUALSCREEN
    if w and h:
        return x, y, x + w, y + h
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def play_chime():
    try:
        import winsound
        winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass


def play_sound(path):
    try:
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    except Exception as e:
        log(f"could not play {path}: {e}")
        return False


# ---------------- Win32 plumbing ----------------
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                             wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]


user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                   wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT
user32.RegisterShellHookWindow.argtypes = [wintypes.HWND]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]

HSHELL_FLASH = 0x8006


def window_title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def process_name(hwnd):
    """Program file name (lower case) that owns a window, e.g. 'claude.exe'."""
    try:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = kernel32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(h)
    except Exception:
        pass
    return ""


def claude_in_front():
    return ALERT_PROCESS_MATCH in process_name(user32.GetForegroundWindow())


# ---------------- notification watcher ----------------
class NotificationWatcher(threading.Thread):
    """Polls Windows' notification database (read-only) for new Claude notifications."""

    DB = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db")
    QUERY = ("select n.Id, cast(n.Payload as text) from Notification n "
             "join NotificationHandler h on h.RecordId = n.HandlerId "
             "where h.PrimaryId like ? and n.Id > ? order by n.Id")

    def __init__(self, on_text, poll_seconds):
        super().__init__(daemon=True)
        self.on_text = on_text
        self.poll_seconds = poll_seconds

    def latest_id(self, cur):
        row = cur.execute(self.QUERY.replace("n.Id, cast(n.Payload as text)", "max(n.Id)")
                          .replace(" order by n.Id", ""), (NOTIFY_APP_MATCH, -1)).fetchone()
        return row[0] or 0

    @staticmethod
    def text_of(payload):
        parts = re.findall(r"<text[^>]*>(.*?)</text>", payload or "", re.S)
        return " | ".join(p.strip() for p in parts)

    def run(self):
        import sqlite3
        if not os.path.exists(self.DB):
            log("notification watcher: database not found, disabled")
            return
        last = None
        while True:
            try:
                con = sqlite3.connect(sqlite_ro_uri(self.DB), uri=True, timeout=2)
                try:
                    cur = con.cursor()
                    if last is None:                    # ignore notifications from before we started
                        last = self.latest_id(cur)
                        log(f"notification watcher started (last Claude id {last})")
                    for nid, payload in cur.execute(self.QUERY, (NOTIFY_APP_MATCH, last)).fetchall():
                        last = max(last, nid)
                        self.on_text(self.text_of(payload))
                finally:
                    con.close()
            except Exception as e:
                log(f"notification watcher error: {e}")
            time.sleep(self.poll_seconds)


# ---------------- taskbar-flash watcher ----------------
class FlashWatcher(threading.Thread):
    """Hidden window that receives shell-hook messages and reports taskbar flashes."""

    def __init__(self, on_flash, react):
        super().__init__(daemon=True)
        self.on_flash = on_flash
        self.react = react
        self.msg_id = 0
        self._proc = WNDPROC(self._wndproc)    # keep a reference so it isn't freed

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if self.msg_id and msg == self.msg_id and wparam == HSHELL_FLASH:
            target = wintypes.HWND(lparam)
            name = process_name(target)
            if ALERT_PROCESS_MATCH in name:
                log(f"taskbar flash: {name} | {window_title(target)!r}")
                if self.react:
                    self.on_flash()
            else:                              # privacy: other programs' names and window titles aren't read or logged
                log("taskbar flash (other program)")
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def run(self):
        hinst = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._proc
        wc.hInstance = hinst
        wc.lpszClassName = "DeskCritterFlashWatcher"
        user32.RegisterClassW(ctypes.byref(wc))
        hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "DeskCritterFlashWatcher",
                                      0, 0, 0, 0, 0, None, None, hinst, None)
        self.msg_id = user32.RegisterWindowMessageW("SHELLHOOK")
        ok = user32.RegisterShellHookWindow(hwnd)
        log(f"flash watcher started (hook registered: {bool(ok)})")
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


def start_watchers(on_text, on_flash, poll_seconds=1.5, watch_notifications=True, watch_flash=True):
    FlashWatcher(on_flash, watch_flash).start()     # always runs, so flashes are at least logged
    if watch_notifications:
        NotificationWatcher(on_text, poll_seconds).start()


# ---------------- launching Claude ----------------
_claude = None


def find_claude():
    """Work out how to launch the Claude app. Result is cached after the first call.
    Returns ("exe", path), ("appid", id) or (None, None)."""
    global _claude
    if _claude:
        return _claude
    found = (None, None)
    if CLAUDE_APP_ID:
        found = ("appid", CLAUDE_APP_ID)
    else:
        for path in CLAUDE_EXE_CANDIDATES:
            if os.path.isfile(path):
                found = ("exe", path)
                break
    if found[0] is None:
        # Ask Windows for the Start-menu entry (works for Store/MSIX installs too).
        # Only the entry named exactly "Claude": any other app with "Claude" in its name
        # (e.g. "Claude Code", or something pretending) must not be what a double-click starts.
        # If yours is named differently, set CLAUDE_APP_ID above.
        ps = ("Get-StartApps | Where-Object Name -eq 'Claude' | "
              "Select-Object -First 1 -ExpandProperty AppID")
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                text=True, capture_output=True, timeout=15,
                creationflags=0x08000000,          # CREATE_NO_WINDOW
            ).stdout.strip()
            if out:
                found = ("appid", out.splitlines()[0].strip())
        except Exception:
            pass
    _claude = found if found[0] else None
    return found


def warm_up():
    find_claude()        # so the first double-click is instant


def open_claude():
    kind, target = find_claude()
    try:
        if kind == "exe":
            subprocess.Popen([target])
            return True
        if kind == "appid":
            os.startfile("shell:AppsFolder\\" + target)
            return True
    except Exception:
        pass
    return False
