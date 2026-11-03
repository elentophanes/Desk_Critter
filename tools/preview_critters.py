# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Render every critter to an SVG gallery (no Windows or tkinter needed).

    py tools\\preview_critters.py                 -> critters_preview.svg in the repo folder
    py tools\\preview_critters.py out.svg robot   -> only the robot

Each critter is drawn four times: arms down, arms up, done (green eyes),
and in alert colours mid-bounce.
Useful for checking a new or changed critter before running it on the taskbar.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import critters                                       # noqa: E402
from critters._painter import Painter, DW, DH        # noqa: E402

SCALE = 1.0
CELL_W, CELL_H = DW * SCALE, DH * SCALE + 24


class SvgPainter(Painter):
    def __init__(self, scale, x0=0.0, y0=0.0):
        super().__init__(scale)
        self.x0, self.y0 = x0, y0
        self.parts = []

    def _pts(self, pts):
        return " ".join(f"{x + self.x0:.1f},{y + self.y0:.1f}" for x, y in pts)

    def _line(self, pts, colour, width):
        self.parts.append(f'<polyline points="{self._pts(pts)}" fill="none" stroke="{colour}" '
                          f'stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')

    def _poly(self, pts, colour):
        self.parts.append(f'<polygon points="{self._pts(pts)}" fill="{colour}"/>')

    def _oval(self, x1, y1, x2, y2, colour):
        cx, cy = (x1 + x2) / 2 + self.x0, (y1 + y2) / 2 + self.y0
        self.parts.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{abs(x2 - x1) / 2:.1f}" '
                          f'ry="{abs(y2 - y1) / 2:.1f}" fill="{colour}"/>')


POSES = [("wave down", dict(wave=12, alert=False, done=False, dy=0)),
         ("wave up", dict(wave=-14, alert=False, done=False, dy=0)),
         ("done", dict(wave=-4, alert=False, done=True, dy=0)),
         ("alert", dict(wave=-6, alert=True, done=False, dy=-14))]


def render(selected=None):
    found = critters.discover(print)
    if selected:
        found = {k: v for k, v in found.items() if k in selected}
    rows = []
    for r, (key, mod) in enumerate(found.items()):
        for col, (label, pose) in enumerate(POSES):
            p = SvgPainter(SCALE, col * CELL_W, r * CELL_H)
            p.dy = pose["dy"]
            f = SimpleNamespace(t=1.0, wave=pose["wave"], blink=False, alert=pose["alert"],
                                done=pose["done"], hover=False)
            mod.draw(p, f, mod.COLOURS["alert" if pose["alert"] else "normal"])
            ground = r * CELL_H + (250 - 80) * SCALE
            rows.append(f'<rect x="{col * CELL_W + 4}" y="{ground - 6}" width="{CELL_W - 8}" '
                        f'height="8" rx="3" fill="#2A2D34"/>')
            rows.extend(p.parts)
            rows.append(f'<text x="{col * CELL_W + 8}" y="{r * CELL_H + CELL_H - 6}" '
                        f'font-family="sans-serif" font-size="12" fill="#888">{mod.NAME} - {label}</text>')
    w, h = CELL_W * len(POSES), CELL_H * max(1, len(found))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
            f'viewBox="0 0 {w:.0f} {h:.0f}">' + "".join(rows) + "</svg>")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "critters_preview.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(sys.argv[2:] or None))
    print("wrote", out)
