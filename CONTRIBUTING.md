# Contributing to Desk_Critter

Thanks for your interest! Hobbyists and individual developers are very welcome to report issues,
suggest features, and send pull requests — including new critters.

## Before your first pull request: sign the CLA

Desk_Critter is free for non-commercial use and **dual-licensed** for commercial use. For that to
work, every contribution needs to be usable under both licenses. So before your first pull request
can be merged, you'll be asked to sign the
[Contributor License Agreement (CLA)](CLA.md).

- It's a one-time click-through handled automatically by the CLA Assistant bot on your pull request.
- **You keep the copyright** to your contribution. You grant the project owner a license to use and
  relicense it, including under commercial terms.
- If you're contributing on work time or with work equipment, check that your employer is OK with it
  first — many employment contracts give the employer rights to code you write.

## How to contribute

1. **Open an issue first** for anything bigger than a small fix, so we can agree on the approach.
2. Fork the repo and create a branch from `main` (e.g. `feature/new-avatar` or `fix/tray-icon`).
3. Keep changes focused — one feature or fix per pull request.
4. Test on Windows before submitting, and describe what you tested in the PR.
5. Add the license header (see below) to any new source file.

## Development notes

- **Python standard library only**: no pip packages, so the critter keeps running on a plain Python install.
- Before opening a pull request, run `py diag\check.py` (Mac: `python3 diag/check.py`); it must end with `all OK`.
- New critters: see README "Adding your own critter" and the contract at the top of `critters/__init__.py`.
- Never commit personal paths, user names or machine details; use placeholders like `C:\Users\<you>`.

## Versioning

The project uses `major.minor` versions. The minor number can exceed 9 (e.g. `1.9`, `1.10`, `1.11`);
the major number changes for significant changes. Stable baselines are tagged so they can be reverted to.

## Artwork / avatars

Avatar artwork you contribute is covered by the CLA in the same way as code. Only submit artwork you
created yourself, or that you have the right to license. No copyrighted characters, logos or
brand mascots, please.

## License header for new source files

```python
# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
```
