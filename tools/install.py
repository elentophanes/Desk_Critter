# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Install a tagged version of Desk Critter into a folder outside the repo, so the critter
you use every day is not affected by work going on in the repo.

    py tools\\install.py                 install the newest tag into %USERPROFILE%\\Tools\\Desk_Critter
    py tools\\install.py v3.0            install that tag
    py tools\\install.py --dest D:\\X     install somewhere else
    py tools\\install.py --startup       also create the "start with Windows" shortcut (Windows only)

Only program files are copied (desk_critter.pyw, critter_hook.py, critters/,
platforms/, README.md, LICENSE, tools/critter_event.py, tools/critter_mcp.py, tools/critter_run.py),
exactly as they are in the tag. Existing files are overwritten; nothing is ever deleted, so the
settings file and log in the destination are kept. Quit the critter before installing, start it after.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import argparse
import io
import os
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = ["desk_critter.pyw", "critter_hook.py", "critters", "platforms", "README.md", "LICENSE",
           "tools/critter_event.py", "tools/critter_mcp.py", "tools/critter_run.py"]
DEFAULT_DEST = os.path.join(os.path.expanduser("~"), "Tools", "Desk_Critter")
SHORTCUT_NAME = "Desk Critter.lnk"


def git(*args, binary=False):
    r = subprocess.run(["git", "-C", REPO, *args], text=not binary, capture_output=True)
    if r.returncode:
        err = r.stderr if not binary else r.stderr.decode(errors="replace")
        sys.exit(f"git {' '.join(args)} failed:\n{err}")
    return r.stdout


def version_key(tag):
    return [int(n) for n in tag.lstrip("v").split(".") if n.isdigit()]


def make_startup_shortcut(dest):
    """Shortcut in the user's Startup folder: pyw.exe "<dest>\\desk_critter.pyw"."""
    ps = r'''
$startup = [Environment]::GetFolderPath('Startup')
$lnk = Join-Path $startup $env:CB_NAME
$pyw = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source
if (-not $pyw) { $pyw = (Get-Command pythonw.exe).Source }
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = $pyw
$s.Arguments = '"' + (Join-Path $env:CB_DEST 'desk_critter.pyw') + '"'
$s.WorkingDirectory = $env:CB_DEST
$s.Description = 'Desk Critter - starts the desktop critter at sign-in'
$s.Save()
"$lnk  ->  $($s.TargetPath) $($s.Arguments)"
'''
    env = dict(os.environ, CB_DEST=dest, CB_NAME=SHORTCUT_NAME)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, env=env)
    if r.returncode:
        sys.exit("could not create the startup shortcut:\n" + r.stderr)
    print("startup shortcut:", r.stdout.strip())


def main():
    ap = argparse.ArgumentParser(description="Install a tagged Desk Critter outside the repo")
    ap.add_argument("tag", nargs="?", help="version tag, e.g. v2.1 (default: the newest tag)")
    ap.add_argument("--dest", default=DEFAULT_DEST, help=f"where to install (default: {DEFAULT_DEST})")
    ap.add_argument("--startup", action="store_true", help="create the start-with-Windows shortcut")
    args = ap.parse_args()

    tags = sorted(git("tag", "--list", "v*").split(), key=version_key)
    tag = args.tag or (tags[-1] if tags else sys.exit("no version tags found"))
    if tag not in tags:
        sys.exit(f"unknown tag {tag}; available: {', '.join(tags)}")

    present = set(git("ls-tree", "-r", "-t", "--name-only", tag).split("\n"))   # files and folders, at any depth
    paths = [p for p in PROGRAM if p in present]
    data = git("archive", "--format=zip", tag, *paths, binary=True)

    dest = os.path.abspath(args.dest)
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest)
        count = sum(1 for n in z.namelist() if not n.endswith("/"))
    with open(os.path.join(dest, "INSTALLED_VERSION.txt"), "w", encoding="utf-8") as f:
        f.write(f"{tag}  ({git('rev-parse', '--short', tag + '^{commit}').strip()})  installed by tools/install.py\n")
    print(f"installed {tag}: {count} files -> {dest}")

    if args.startup:
        if sys.platform != "win32":
            sys.exit("--startup is for Windows only")
        make_startup_shortcut(dest)


if __name__ == "__main__":
    main()
