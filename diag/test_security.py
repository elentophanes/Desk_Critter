# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Tests for the v3.2 security fixes. No screen needed, and it does NOT touch your real critter:
everything runs in a temporary folder (a fake home folder), which is removed at the end.

    py diag\\test_security.py          (macOS: python3 diag/test_security.py)

Checks: private events folder, hook/tool event lines, read-only notification-database URIs
(also with '#' or '%' in the path), critter_run's batch-file guard, log rotation, the 1 MB
update-check limit, the event watcher, and the exact-name Claude launcher.
Prints PASS/FAIL per check; exit code 0 when all pass. Standard library only.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import types
import warnings

with warnings.catch_warnings():          # deprecated in Python 3.14, still the only way to
    warnings.simplefilter("ignore", DeprecationWarning)   # get Windows URL rules on a Mac/Linux
    import nturl2path

REPO = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSIX = os.name != "nt"                       # folder permissions are a Mac/Linux thing
TRUE = [sys.executable, "-c", "pass"]          # a command that succeeds, on every OS
FALSE = [sys.executable, "-c", "raise SystemExit(1)"]
sys.path.insert(0, REPO)
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"   [{detail}]" if detail else ""))


tmp = tempfile.mkdtemp(prefix="critter_test_")
home = os.path.join(tmp, "home")
os.makedirs(home)
env = dict(os.environ, HOME=home, USERPROFILE=home)
events = os.path.join(home, ".desk-critter", "events.log")

# ---- 1. hook: private folder, correct line --------------------------------------------
stdin = json.dumps({"hook_event_name": "Stop", "cwd": "/x/MyProj", "session_id": "s 1\t2",
                    "message": "line1\nline2\tTAB"})
r = subprocess.run([sys.executable, os.path.join(REPO, "critter_hook.py"), "done"], text=True,
                   input=stdin, capture_output=True, env=env)
mode = stat.S_IMODE(os.stat(os.path.dirname(events)).st_mode)
check("hook exits 0 and prints nothing", r.returncode == 0 and not r.stdout and not r.stderr)
check("hook creates ~/.desk-critter as 0700", mode == 0o700 or not POSIX, oct(mode) if POSIX else "skipped on Windows")
line = open(events, encoding="utf-8").read().splitlines()[-1].split("\t")
check("hook line has 4 fields, text sanitised", len(line) == 4 and line[1] == "done" and line[2] == "s12"
      and line[3] == "MyProj | line1 line2 TAB", line)

if POSIX:
    os.chmod(os.path.dirname(events), 0o755)                  # folder left by an older version
    subprocess.run([sys.executable, os.path.join(REPO, "critter_hook.py"), "busy"], input="{}", text=True, env=env)
    mode = stat.S_IMODE(os.stat(os.path.dirname(events)).st_mode)
    check("hook tightens an existing 0755 folder to 0700", mode == 0o700, oct(mode))

r = subprocess.run([sys.executable, os.path.join(REPO, "critter_hook.py"), "busy"], text=True,
                   input="not json{", env=env, capture_output=True)
check("hook survives bad JSON (exit 0)", r.returncode == 0)

# ---- 2. critter_event and MCP selftest -----------------------------------------------
r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "critter_event.py"), "help", "Report", "ready"],
                   capture_output=True, env=env, text=True)
last = open(events, encoding="utf-8").read().splitlines()[-1].split("\t")
check("critter_event writes help line", r.returncode == 0 and last[1:] == ["help", "manual", "Report ready"], last)
r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "critter_mcp.py"), "--selftest"],
                   capture_output=True, env=env, text=True)
last = open(events, encoding="utf-8").read().splitlines()[-1].split("\t")
check("MCP selftest: tools listed and wave sent", r.returncode == 0 and '"wave"' in r.stdout
      and last[1:] == ["done", "claude-chat", "self-test"], r.stderr[-200:])

# ---- 3. read-only sqlite URI ---------------------------------------------------------
from platforms._base import sqlite_ro_uri
for odd in ("a#b", "pct%41", "sp ace") + (("q?x",) if POSIX else ()):   # no "?" in Windows names
    d = os.path.join(tmp, odd)
    os.makedirs(d)
    db = os.path.join(d, "db")
    c = sqlite3.connect(db); c.execute("create table record(x)"); c.execute("insert into record values (42)")
    c.commit(); c.close()
    before = set(os.listdir(tmp))
    con = sqlite3.connect(sqlite_ro_uri(db), uri=True)
    got = con.execute("select x from record").fetchone()[0]
    try:
        con.execute("insert into record values (1)"); writable = True
    except sqlite3.OperationalError:
        writable = False
    con.close()
    check(f"new URI opens the right file read-only ({odd!r})", got == 42 and not writable
          and set(os.listdir(tmp)) == before)
# Show the old bug: '#' truncates the path and drops ?mode=ro
d = os.path.join(tmp, "a#b")
old = "file:" + os.path.join(d, "db") + "?mode=ro"
try:
    sqlite3.connect(old, uri=True).execute("select x from record").fetchone(); old_ok = True
except sqlite3.Error:
    old_ok = False
check("old URI really was broken with '#' (bug reproduced)", not old_ok)
w = "file:" + nturl2path.pathname2url(r"C:\Users\Jo#n %x\AppData\Local\wpndatabase.db") + "?mode=ro"
check("Windows path quoted correctly", w == "file:///C:/Users/Jo%23n%20%25x/AppData/Local/wpndatabase.db?mode=ro", w)

# ---- 4. critter_run batch-file guard -------------------------------------------------
sys.path.insert(0, os.path.join(REPO, "tools"))
os.environ["HOME"] = os.environ["USERPROFILE"] = home     # critter_event reads ~ on import
import critter_run
check("unsafe_for_cmd finds & and |", critter_run.unsafe_for_cmd(["a&b", "c|d", "ok"]) == "&|")
check("unsafe_for_cmd passes normal args", critter_run.unsafe_for_cmd(["-o", "part.stl", r"C:\x y\p.scad"]) == "")
launched = []
real_which, real_popen, real_osname = critter_run.shutil.which, critter_run.subprocess.Popen, critter_run.os.name


class FakeProc:
    def wait(self, timeout=None):
        return 0


critter_run.shutil.which = lambda c: r"C:\tools\build.bat"
critter_run.subprocess.Popen = lambda *a, **k: launched.append((a, k)) or FakeProc()
critter_run.os.name = "nt"
try:
    err = io.StringIO(); sys.stderr, saved = err, sys.stderr
    code_bad = critter_run.main(["build", "x & calc.exe"])
    n_bad = len(launched)
    code_ok = critter_run.main(["build", "release", "--fast"])
finally:
    sys.stderr = saved
    critter_run.shutil.which, critter_run.subprocess.Popen, critter_run.os.name = real_which, real_popen, real_osname
check("batch file with '&' refused, nothing launched", code_bad == 2 and n_bad == 0)
check("batch file with normal args still runs via cmd", code_ok == 0 and len(launched) == 1
      and launched[0][1].get("shell") is True and launched[0][0][0] == r"C:\tools\build.bat release --fast",
      launched)
r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "critter_run.py"), "--name", "T", *TRUE],
                   capture_output=True, env=env, text=True)
check("critter_run real command -> exit 0, done event", r.returncode == 0 and
      open(events).read().splitlines()[-1].split("\t")[1] == "done")
r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "critter_run.py"), *FALSE], capture_output=True,
                   env=env, text=True)
check("critter_run failing command -> exit 1", r.returncode == 1)

# ---- 5. main app: log rotation, update read cap, event watcher (tkinter stubbed) ------
tkstub = types.ModuleType("tkinter"); tkstub.ROUND = "round"
sys.modules["tkinter"] = tkstub
loader = importlib.machinery.SourceFileLoader("desk_critter", os.path.join(REPO, "desk_critter.pyw"))
spec = importlib.util.spec_from_loader("desk_critter", loader)
dc = importlib.util.module_from_spec(spec); loader.exec_module(dc)
check("VERSION is 3.2", dc.VERSION == "3.2")
dc.LOG_PATH = os.path.join(tmp, "desk_critter.log")
dc.LOG_MAX_BYTES = 1000
for i in range(100):
    dc.log(f"line {i:03d} " + "x" * 40)
size, old_size = os.path.getsize(dc.LOG_PATH), os.path.getsize(dc.LOG_PATH + ".1")
check("log rotates: current and .1 both stay near the cap", size <= 1100 and 900 < old_size <= 1100, (size, old_size))
check("newest line is in the current log", "line 099" in open(dc.LOG_PATH).read())


class FakeResp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): pass


big = json.dumps([{"name": "v3.1"}, {"name": "v3.10"}, {"name": "junk"}]).encode()
dc.urllib.request.urlopen = lambda req, timeout=0: FakeResp(big)
check("update check still finds newest tag", dc.latest_version() == "v3.10")
dc.urllib.request.urlopen = lambda req, timeout=0: FakeResp(b"[" + b" " * 2_000_000 + b"]")
try:
    dc.latest_version(); capped = False
except ValueError:
    capped = True                      # truncated at 1 MB -> invalid JSON, not 2 MB read
check("update check reads at most 1 MB", capped)

dc.EVENTS_PATH = events
got = []
dc.EVENT_POLL_SECONDS = 0.05
dc.EventWatcher(lambda k, s, t: got.append((k, s, t))).start()
time.sleep(0.2)
subprocess.run([sys.executable, os.path.join(REPO, "tools", "critter_event.py"), "done", "watched"], env=env)
time.sleep(0.4)
check("event watcher sees a new event", ("done", "manual", "watched") in got, got)

# ---- 6. static checks ---------------------------------------------------------------
win = open(os.path.join(REPO, "platforms", "windows.py"), encoding="utf-8").read()
check("Windows launcher only accepts Name -eq 'Claude'", "Where-Object Name -eq 'Claude'" in win and "-like '*Claude*'" not in win)
leftover = "\n".join(f"{os.path.relpath(os.path.join(d, n), REPO)}: {l.strip()}"
                     for d, _dirs, names in os.walk(REPO) if ".git" not in d
                     for n in names if n.endswith((".py", ".pyw")) and n != "test_security.py"
                     for l in open(os.path.join(d, n), encoding="utf-8") if '"file:" +' in l)
check("no raw 'file:' + path URIs left (except notif_probe with pathname2url)",
      all("pathname2url" in l for l in leftover.splitlines()), leftover)

shutil.rmtree(tmp, ignore_errors=True)          # only the temporary folder this test made
print(f"\n{sum(ok for _, ok in results)}/{len(results)} passed")
sys.exit(0 if all(ok for _, ok in results) else 1)
