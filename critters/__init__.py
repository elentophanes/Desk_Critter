# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Critter registry.

Every .py file in this folder (not starting with "_") that defines NAME, COLOURS
and draw() is a critter. To add one, copy an existing critter file, rename it, and
change the drawing. It appears in the right-click "Critter" menu automatically.

Critter file contract
-------------------
    NAME    = "Robot"            # shown in the menu
    ORDER   = 2                  # menu position (optional)
    COLOURS = {"normal": {...}, "alert": {...}}   # same keys in both
    SOUND   = "robot.wav"        # optional: alert sound file in this folder (else the chime)
    SOUND_DONE = "robot_done.wav"   # optional: quiet sound when Claude has finished (else silent)
    def draw(p, f, col):         # p = Painter, f = Frame, col = COLOURS[...]

Frame fields (f):
    f.t       seconds since start
    f.wave    waving angle in degrees, swings about -14..+12 (faster when hovered/alerting)
    f.blink   True for a few frames now and then
    f.alert   True while alerting (Claude needs help): COLOURS["alert"] is used
    f.done    True when Claude has finished and doesn't need help: show green eyes
              (the eye() helper in _painter does this for you)
    f.hover   True while the mouse is over the critter
    f.busy    True while a Claude Code session is working (the core already draws the
              blue "working" dots above every critter; use this only for extra effects)
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import importlib
import pkgutil
from types import SimpleNamespace

Frame = SimpleNamespace


def discover(log=lambda msg: None):
    """Return {module_name: module} for every valid critter, in menu order."""
    found = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{info.name}")
        except Exception as e:                    # a broken critter must not stop the others
            log(f"critter '{info.name}' failed to load: {e}")
            continue
        if all(hasattr(mod, a) for a in ("NAME", "COLOURS", "draw")):
            found[info.name] = mod
        else:
            log(f"critter '{info.name}' skipped: needs NAME, COLOURS and draw()")
    return dict(sorted(found.items(), key=lambda kv: (getattr(kv[1], "ORDER", 99), kv[0])))
