# Security

Desk Critter can start with Windows and runs on Claude Code events, so a bug in it, or a tampered copy of
it, could affect your computer. Thank you for helping keep it safe.

The only official source is **<https://github.com/elentophanes/Desk_Critter>**. From v3.2 every release
is signed; see [Verify your copy](README.md#verify-your-copy) in the README.

## How to report

Use GitHub's private reporting form:

1. Go to <https://github.com/elentophanes/Desk_Critter/security>.
2. Click **Report a vulnerability**.
3. Describe what you found (see below for what helps).

Only the maintainer can see the report. **Please don't open a public issue** for a vulnerability or a
malicious copy, so that it isn't advertised before it's dealt with.

This is a one-person, non-commercial project, so replies are best effort.

## Vulnerabilities

[PRIVACY.md](PRIVACY.md) lists everything Desk Critter is meant to access. Please report anything that
lets someone make it do more than that, for example:

- getting `tools/install.py` to install a tag that isn't signed by the maintainer key, without `--allow-unsigned`
- making the critter, `critter_hook.py` or the Claude Desktop tool (`tools/critter_mcp.py`) run commands,
  open web pages or write files they shouldn't
- the update check (**Check for updates…**) doing anything beyond reading version numbers from GitHub

Helpful to include: the Desk Critter version (right-click → **About Desk Critter…**), Windows or macOS
version, Python version, and the steps to reproduce it.

Problems that need someone to already control your computer or your GitHub account are out of scope;
there, Desk Critter can't protect you.

## Fake or modified copies

The licence ([PolyForm Noncommercial](LICENSE)) allows non-commercial copies and changes, as long as the
copyright notice is kept. A modified copy is not a problem in itself. Please report a copy that:

- claims to be the official Desk Critter, or uses the name to look official
- fails the checks in [Verify your copy](README.md#verify-your-copy) (wrong signature, unsigned tag
  presented as a release, ZIP that doesn't match `SHA256SUMS`)
- has had the copyright notice or licence removed
- is sold, or used commercially without a licence (see [COMMERCIAL.md](COMMERCIAL.md))
- contains changes that could harm users

Helpful to include:

- where you found it (link) and how you got it
- the output of the verification commands
- the SHA256 of the file you got: `Get-FileHash <file>` (Windows) or `shasum -a 256 <file>` (macOS)

**Don't run a copy that fails verification.** If you already ran it, say so in the report.

## Supported versions

| Version | Supported |
|---|---|
| Newest release (v3.2 or later) | Yes: fixes come as a new signed release |
| v3.1 and earlier | No: not signed; please update |

## Signing keys

Releases are signed with the keys listed in [Verify your copy](README.md#verify-your-copy). If a key ever
has to be replaced, the change will be announced in the README and in the release notes, and the new key
will be listed on the maintainer's GitHub profile. A release signed with any key not listed there is not
an official release.
