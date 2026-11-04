# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Make a signed release (maintainer only). Run it in the PUBLIC clone, after the wm release of this
version has been merged into public main (WORKFLOW.md section 6, step 7), with everything committed:

    py tools\\release.py 3.2              tag v3.2, build the release files, sign and check everything
    py tools\\release.py 3.2 --check      only the checks in step 1; changes nothing
    py tools\\release.py 3.2 --reuse-tag  v3.2 already exists (an earlier run stopped): check it, then build

  1. checks: this is the public repo (not Desk_Critter-master), on main, nothing uncommitted, same as
     origin/main, VERSION in desk_critter.pyw is 3.2, v3.2 not tagged yet, diag/check.py and
     diag/test_security.py pass, minisign and its secret key are found
  2. git tag -s v3.2, then checks the signature against .github/allowed_signers
  3. Desk_Critter-v3.2.zip   made with git archive, so it holds exactly what the tag holds
  4. SHA256SUMS and SHA256SUMS.minisig (minisign asks for its password),
     then checks the signature against .github/minisign.pub
  5. prints the commands to push the tag and publish the GitHub Release

The three files go to release_out\\v3.2 NEXT TO the repo folder (like wm_out), not inside it, so the
next robocopy /MIR into the public clone can't remove them; --out chooses another folder.
Nothing is pushed or uploaded, and nothing is deleted: if one of the files already exists, it stops.
Needs Git with SSH signing set up, and minisign with its secret key in
%USERPROFILE%\\.minisign\\desk_critter.key (or give --minisign-key).
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from install import verify_tag                          # noqa: E402  (same check the installer uses)

MINISIGN_PUB = os.path.join(REPO, ".github", "minisign.pub")
DEFAULT_KEY = os.path.join(os.path.expanduser("~"), ".minisign", "desk_critter.key")


def run(*cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, cwd=REPO, text=True)
    if check and r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd)}\n{r.stderr or r.stdout}")
    return r.stdout.strip()


def ok(text):
    print("  OK  ", text)


def fail(text):
    sys.exit(f"  STOP  {text}")


def checks(version, tag, args, dist):
    print("[1] checks")
    remote = run("git", "remote", "get-url", "origin", check=False)
    if "desk_critter-master" in remote.lower():
        fail("this is the master repo. Releases are signed in the PUBLIC clone after the wm release "
             "(WORKFLOW.md section 6).")
    ok(f"public repo ({remote or 'no origin'})")
    if run("git", "rev-parse", "--abbrev-ref", "HEAD") != "main":
        fail("not on main. Releases are made from main: git switch main")
    ok("on main")
    if run("git", "status", "--porcelain"):
        fail("there are uncommitted changes (git status). Commit or stash them first.")
    ok("nothing uncommitted")
    if subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=REPO).returncode:
        print("  !!   could not fetch origin/main; comparing with the last fetched copy")
    if run("git", "rev-parse", "HEAD") != run("git", "rev-parse", "origin/main"):
        fail("main is not the same as origin/main. Pull or push first, so the release is what GitHub has.")
    ok("same as origin/main")

    src = open(os.path.join(REPO, "desk_critter.pyw"), encoding="utf-8").read()
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', src, re.M)
    if not m or m.group(1) != version:
        fail(f'desk_critter.pyw says VERSION = "{m.group(1) if m else "?"}", not "{version}". '
             "Update it, commit and push, then run this again.")
    ok(f'VERSION = "{version}"')

    exists = bool(run("git", "tag", "--list", tag))
    if exists and not args.reuse_tag:
        fail(f"{tag} already exists. If an earlier run stopped after tagging, add --reuse-tag.")
    if not exists and args.reuse_tag:
        fail(f"--reuse-tag given, but {tag} does not exist")
    if exists and run("git", "rev-parse", tag + "^{commit}") != run("git", "rev-parse", "HEAD"):
        fail(f"{tag} exists but points at a different commit than HEAD")
    ok(f"{tag} {'exists and points at HEAD' if exists else 'is free'}")

    if run("git", "config", "gpg.format", check=False) != "ssh" or not run("git", "config", "user.signingkey", check=False):
        fail("Git SSH signing is not set up (gpg.format / user.signingkey); see step 1 of the security setup")
    ok("Git SSH signing is set up")

    for test in ("check.py", "test_security.py"):
        if not os.path.isfile(os.path.join(REPO, "diag", test)):
            fail(f"diag/{test} is missing")
        r = subprocess.run([sys.executable, os.path.join("diag", test)], capture_output=True, cwd=REPO, text=True)
        if r.returncode:
            fail(f"diag/{test} found problems:\n" + r.stdout[-2000:] + r.stderr[-2000:])
        ok(f"diag/{test} passed")

    minisign = shutil.which("minisign")
    if not minisign:
        fail("minisign not found. Install it (winget install jedisct1.minisign) and reopen PowerShell.")
    if not os.path.isfile(args.minisign_key):
        fail(f"minisign secret key not found: {args.minisign_key} (use --minisign-key)")
    ok(f"minisign and its key found ({args.minisign_key})")

    names = [f"Desk_Critter-{tag}.zip", "SHA256SUMS", "SHA256SUMS.minisig"]
    there = [n for n in names if os.path.exists(os.path.join(dist, n))]
    if there:
        fail(f"already in {dist}: {', '.join(there)}. Move or delete them yourself, then run this again.")
    ok(f"output folder: {dist}")
    return minisign, names


def main():
    ap = argparse.ArgumentParser(description="Make a signed Desk Critter release (maintainer only)")
    ap.add_argument("version", help="major.minor, e.g. 3.2 (the minor can go past 9: 3.10)")
    ap.add_argument("--check", help="only run the checks; change nothing", action="store_true")
    ap.add_argument("--reuse-tag", help="the tag already exists from an earlier run", action="store_true")
    ap.add_argument("--minisign-key", default=DEFAULT_KEY, help=f"minisign secret key (default {DEFAULT_KEY})")
    ap.add_argument("--out", help="folder for the release files (default: release_out\\vX.Y next to the repo)")
    args = ap.parse_args()

    version = args.version.lstrip("v")
    if not re.fullmatch(r"\d+\.\d+", version):
        fail(f"'{args.version}' is not major.minor, e.g. 3.2")
    tag = "v" + version
    dist = os.path.abspath(args.out or os.path.join(os.path.dirname(REPO), "release_out", tag))
    minisign, (zip_name, sums_name, sig_name) = checks(version, tag, args, dist)
    if args.check:
        print("\nAll checks passed (--check: nothing was changed).")
        return

    print(f"\n[2] signed tag {tag}")
    if not args.reuse_tag:
        if subprocess.run(["git", "tag", "-s", tag, "-m", f"Desk Critter {version}"], cwd=REPO).returncode:
            fail("git tag -s failed (is ssh-agent running with your key loaded?)")
    good, details = verify_tag(tag)
    if not good:
        fail(f"{tag} does not verify against .github/allowed_signers:\n{details}\n"
             f"Nothing was pushed. To remove the local tag: git tag -d {tag}")
    ok(f"{tag} signature verified")

    print(f"\n[3] {zip_name}")
    os.makedirs(dist, exist_ok=True)
    zip_path = os.path.join(dist, zip_name)
    run("git", "archive", "--format=zip", f"--prefix=Desk_Critter-{tag}/", "-o", zip_path, tag)
    digest = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
    ok(f"{os.path.getsize(zip_path):,} bytes, SHA256 {digest}")

    print(f"\n[4] {sums_name} and {sig_name}")
    sums_path, sig_path = os.path.join(dist, sums_name), os.path.join(dist, sig_name)
    with open(sums_path, "w", encoding="ascii", newline="\n") as f:
        f.write(f"{digest}  {zip_name}\n")
    print("  minisign will ask for its password:")
    if subprocess.run([minisign, "-S", "-s", args.minisign_key, "-m", sums_path, "-x", sig_path,
                       "-t", f"Desk Critter {tag} SHA256SUMS"], cwd=REPO).returncode:
        fail("minisign could not sign (wrong password?). The tag is made; run again with --reuse-tag.")
    r = subprocess.run([minisign, "-V", "-p", MINISIGN_PUB, "-m", sums_path, "-x", sig_path],
                       capture_output=True, cwd=REPO, text=True)
    if r.returncode:
        fail(f"the new signature does not verify against .github/minisign.pub:\n{r.stdout}{r.stderr}")
    ok("SHA256SUMS signature verified against .github/minisign.pub")

    rel = dist
    files = " ".join('"' + os.path.join(rel, n) + '"' for n in (zip_name, sums_name, sig_name))
    print(f"""
[5] Done. Nothing has been pushed yet. To publish:

  git push origin {tag}

  then EITHER with the GitHub CLI:
    gh release create {tag} {files} --verify-tag --title "Desk Critter {version}" --notes "See README: Verify your copy"

  OR on github.com: Releases > Draft a new release > choose tag {tag} > attach these three files from {rel}:
    {zip_name}
    {sums_name}
    {sig_name}
""")


if __name__ == "__main__":
    main()
