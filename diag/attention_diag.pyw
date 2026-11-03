# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Diagnostic recorder for Spider Critter (temporary - not part of the critter itself).
Logs what the Claude app's windows do, plus any Windows notification pop-ups,
to attention_diag.log next to this file. Stops by itself after RUN_MINUTES.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import ctypes, os, sys, time, threading
from ctypes import wintypes

RUN_MINUTES = 20
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attention_diag.log")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND,
                                  wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD)

class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.RegisterWindowMessageW.restype = wintypes.UINT
user32.SetWinEventHook.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.HMODULE, WINEVENTPROC,
                                   wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
user32.SetWinEventHook.restype = wintypes.HANDLE
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]

_lock = threading.Lock()
def pname(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024); n = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(h)
    return ""

def log(s):
    with _lock, open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + s + "\n")

def cls(h):
    b = ctypes.create_unicode_buffer(256); user32.GetClassNameW(h, b, 256); return b.value

def title(h):
    b = ctypes.create_unicode_buffer(512); user32.GetWindowTextW(h, b, 512); return b.value

def interesting(h):
    p = pname(h); c = cls(h); t = title(h)
    if "claude" in p:
        return True
    if p in ("shellexperiencehost.exe", "explorer.exe") and ("notification" in t.lower() or "CoreWindow" in c):
        return True
    return False

EVENTS = {0x8002: "SHOW", 0x8003: "HIDE", 0x800C: "NAMECHANGE", 0x0003: "FOREGROUND",
          0x0002: "ALERT", 0x8005: "FOCUS"}
last_title = {}

def on_winevent(hook, event, hwnd, idObject, idChild, thread, t):
    try:
        if not hwnd or idObject != 0:      # OBJID_WINDOW only
            return
        if user32.GetAncestor(hwnd, 2) != hwnd:   # top-level windows only
            return
        if not interesting(hwnd):
            return
        ti = title(hwnd)
        if event == 0x800C and last_title.get(hwnd) == ti:
            return
        last_title[hwnd] = ti
        log(f"{EVENTS.get(event, hex(event)):11} {pname(hwnd)} class={cls(hwnd)!r} title={ti!r}")
    except Exception as e:
        log(f"err {e}")

_cb = WINEVENTPROC(on_winevent)
SHELL_CODES = {1: "CREATED", 2: "DESTROYED", 4: "ACTIVATED", 6: "REDRAW", 0x8006: "FLASH",
               0x8004: "RUDEACTIVATED", 13: "MONITORCHANGED", 16: "APPCOMMAND"}

def wndproc(hwnd, msg, wp, lp):
    if msg == shell_msg:
        h = wintypes.HWND(lp)
        try:
            if interesting(h) or wp == 0x8006:
                log(f"SHELL {SHELL_CODES.get(wp, hex(wp)):9} {pname(h)} title={title(h)!r}")
        except Exception as e:
            log(f"err {e}")
    return user32.DefWindowProcW(hwnd, msg, wp, lp)

_wp = WNDPROC(wndproc)

def main():
    global shell_msg
    log(f"=== diag started, will stop after {RUN_MINUTES} min ===")
    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW(); wc.lpfnWndProc = _wp; wc.hInstance = hinst; wc.lpszClassName = "ClaudeAttnDiag"
    user32.RegisterClassW(ctypes.byref(wc))
    hwnd = user32.CreateWindowExW(0, "ClaudeAttnDiag", "ClaudeAttnDiag", 0, 0, 0, 0, 0, None, None, hinst, None)
    shell_msg = user32.RegisterWindowMessageW("SHELLHOOK")
    user32.RegisterShellHookWindow(hwnd)
    for lo, hi in ((0x0002, 0x0003), (0x8002, 0x8003), (0x800C, 0x800C)):
        user32.SetWinEventHook(lo, hi, None, _cb, 0, 0, 0x0002)   # OUTOFCONTEXT | SKIPOWNPROCESS
    user32.SetTimer(hwnd, 1, 60 * RUN_MINUTES * 1000, None)
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0113:   # WM_TIMER
            break
        user32.TranslateMessage(ctypes.byref(msg)); user32.DispatchMessageW(ctypes.byref(msg))
    log("=== diag stopped ===")

main()
