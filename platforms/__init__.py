# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Operating-system specific code.

desk_critter.pyw knows nothing about Windows or macOS; it calls the functions of
`platforms.current`, which is one of:
    windows.py   Windows 10/11 (the original, fully tested)
    macos.py     macOS (tested on a real Mac up to v2.4; needs Python 3.13 / Tk 8.6)
    _base.py     anything else: a plain window, no alerts

Every platform module provides the names listed in _base.py.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import sys

if sys.platform == "win32":
    from . import windows as current
elif sys.platform == "darwin":
    from . import macos as current
else:
    from . import _base as current
