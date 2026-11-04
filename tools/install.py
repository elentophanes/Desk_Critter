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
    py tools\\install.py v3.1 --allow-unsigned    install an older tag that has no signature

Before copying anything, the tag's signature is checked against the key in .github/allowed_signers
(git verify-tag). Unsigned tags, and tags signed by any other key, are refused unless you add
--allow-unsigned. Tags from v3.2 on are signed; older ones are not. This needs ssh-keygen, which
comes with Windows 10/11 (OpenSSH Client) and macOS.

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
import re
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = ["desk_critter.pyw", "critter_hook.py", "critters", "platforms", "README.md", "LICENSE",
           "tools/critter_event.py", "tools/critter_mcp.py", "tools/critter_run.py"]
DEFAULT_DEST = os.path.join(os.path.expanduser("~"), "Tools", "Desk_Critter")
ALLOWED_SIGNERS = os.path.join(REPO, ".github", "allowed_signers")      # the maintainer's public signing key
SHORTCUT_NAME = "Desk Critter.lnk"


def verify_tag(tag):
    """(True, details) if the tag is signed by a key in .github/allowed_signers, else (False, reason).

    Only that file is trusted, not any signers list in your own Git settings. Git refuses
    signatures from keys that aren't listed; minTrustLevel=fully makes that explicit.
    Checking always uses plain ssh-keygen, whatever signing program your Git settings name
    (some, like password-manager signers, can sign but not check).
    """
    if not os.path.isfile(ALLOWED_SIGNERS):
        return False, f"{os.path.relpath(ALLOWED_SIGNERS, REPO)} is missing, so there is no key to check against"
    r = subprocess.run(["git", "-C", REPO,
                        "-c", "gpg.ssh.allowedSignersFile=" + ALLOWED_SIGNERS.replace("\\", "/"),
                        "-c", "gpg.minTrustLevel=fully",
                        "-c", "gpg.ssh.program=ssh-keygen",
                        "verify-tag", tag], text=True, capture_output=True)
    out = (r.stderr + r.stdout).strip()
    if r.returncode == 0:
        return True, out
    if "ssh-keygen" in out and ("cannot run" in out or "not found" in out or "No such file" in out):
        return False, ("ssh-keygen was not found, so the signature can't be checked.\n"
                       "  Windows: Settings > Apps > Optional features > add 'OpenSSH Client'.\n" + out)
    if "No principal matched" in out:
        fp = re.search(r"SHA256:[A-Za-z0-9+/]+", out)
        return False, (f"{tag} is signed, but NOT by the Desk Critter maintainer key"
                       f"{' (it was signed by ' + fp.group(0) + ')' if fp else ''}.\n"
                       "  This copy may have been tampered with. Please report it: see SECURITY.md.")
    if "no signature found" in out or "cannot verify a non-tag object" in out:
        return False, f"{tag} is not signed."
    return False, out or f"git verify-tag {tag} failed"


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
    ap.add_argument("--allow-unsigned", action="store_true",
                    help="install even if the tag is unsigned or its signature can't be checked (older tags)")
    args = ap.parse_args()

    tags = sorted(git("tag", "--list", "v*").split(), key=version_key)
    tag = args.tag or (tags[-1] if tags else sys.exit("no version tags found"))
    if tag not in tags:
        sys.exit(f"unknown tag {tag}; available: {', '.join(tags)}")

    signed, details = verify_tag(tag)
    if signed:
        print(f"signature OK: {tag} is signed by the Desk Critter maintainer key")
    elif args.allow_unsigned:
        print(f"WARNING: installing {tag} WITHOUT a verified signature (--allow-unsigned):\n  {details}")
    else:
        sys.exit(f"Not installing {tag}: its signature could not be verified.\n  {details}\n\n"
                 "Make sure you cloned https://github.com/elentophanes/Desk_Critter and see README\n"
                 "\"Verify your copy\". Tags before v3.2 are unsigned; to install one anyway, add --allow-unsigned.")

    present = set(git("ls-tree", "-r", "-t", "--name-only", tag).split("\n"))   # files and folders, at any depth
    paths = [p for p in PROGRAM if p in present]
    data = git("archive", "--format=zip", tag, *paths, binary=True)

    dest = os.path.abspath(args.dest)
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest)
        count = sum(1 for n in z.namelist() if not n.endswith("/"))
    with open(os.path.join(dest, "INSTALLED_VERSION.txt"), "w", encoding="utf-8") as f:
        f.write(f"{tag}  ({git('rev-parse', '--short', tag + '^{commit}').strip()})  installed by tools/install.py"
                f"{'' if signed else ' (signature NOT verified)'}\n")
    print(f"installed {tag}: {count} files -> {dest}")

    if args.startup:
        if sys.platform != "win32":
            sys.exit("--startup is for Windows only")
        make_startup_shortcut(dest)


if __name__ == "__main__":
    main()
