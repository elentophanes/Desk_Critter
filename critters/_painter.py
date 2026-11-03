# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Drawing helpers shared by all critters.

Critters draw in "design coordinates": the same box for every critter, so the window
never has to change size when you switch. Feet stand on y = 242, the centre line
is x = 340, and the top must stay below y = 94 so there is room to bounce.

A Painter turns design coordinates into pixels. The core uses a Tk painter;
tools/preview_critters.py uses an SVG painter. Critters only ever call:
    p.line(points, colour, width)          polyline with round ends
    p.poly(points, colour)                 filled polygon
    p.oval(cx, cy, rx, ry, colour)         filled ellipse
    p.rrect(x1, y1, x2, y2, r, colour)     filled rounded rectangle
    p.curve(p0, p1, p2, colour, width)     quadratic curve (p1 = control point)
and the module-level helpers rotate(), rotate_all() and eye(), plus mix() and
done_pulse() for critters whose lights pulse green when Claude has finished.
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import math

# Shared design box: x 226..454, y 80..250
OX, OY = 226, 80
DW, DH = 228, 170

DONE_EYE = "#3CCB5A"      # green eyes when Claude has finished (f.done)


DONE_BRIGHT = "#7DFF9B"   # peak of the green "done" pulse (for critters with lights)
DONE_DIM = "#1F8F3C"      # trough of the pulse
DONE_GLOW = "#B9FFC9"     # pale green for halos and lit-up screens
DONE_PULSE = 1.0          # seconds per pulse


def done_pulse(f):
    """Heartbeat for 'done' lights: swings 0..1 once every DONE_PULSE seconds."""
    return 0.5 + math.sin(math.pi * 2 * getattr(f, "t", 0.0) / DONE_PULSE) * 0.5


def mix(a, b, k):
    """Colour between hex colours a (k=0) and b (k=1)."""
    ca, cb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * k) for x, y in zip(ca, cb))


def eye(p, f, cx, cy, rx, ry, dark, white, hl=(2, -3, 2)):
    """Standard critter eye: blinks, and turns green with a small pupil when f.done.
    hl = (dx, dy, r) of the white highlight relative to the eye centre."""
    if f.blink:
        p.oval(cx, cy, rx, 0.7, dark)
        return
    if getattr(f, "done", False):
        p.oval(cx, cy, rx, ry, DONE_EYE)
        p.oval(cx, cy + 0.5, 0.43 * rx, 0.43 * ry, dark)
    else:
        p.oval(cx, cy, rx, ry, dark)
    p.oval(cx + hl[0], cy + hl[1], hl[2], hl[2], white)


def rotate(px, py, cx, cy, deg):
    """Rotate point (px,py) around (cx,cy); positive deg = clockwise on screen."""
    a = math.radians(deg)
    dx, dy = px - cx, py - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a),
            cy + dx * math.sin(a) + dy * math.cos(a))


def bezier(p0, p1, p2, steps=10):
    """Points along a quadratic Bezier curve from p0 to p2 with control point p1."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t ** 2
        pts.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return pts


def rotate_all(points, cx, cy, deg):
    return [rotate(x, y, cx, cy, deg) for x, y in points]


def rrect_points(x1, y1, x2, y2, r, steps=5):
    """Outline of a rounded rectangle as a list of points."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = []
    for cx, cy, start in ((x2 - r, y1 + r, -90), (x2 - r, y2 - r, 0),
                          (x1 + r, y2 - r, 90), (x1 + r, y1 + r, 180)):
        for i in range(steps + 1):
            a = math.radians(start + i * 90 / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


class Painter:
    """Base class: converts design coordinates to pixels and forwards to a backend."""

    def __init__(self, scale):
        self.s = scale
        self.dy = 0.0          # vertical offset (bob / bounce), in design units

    def P(self, x, y):
        return ((x - OX) * self.s, (y - OY + self.dy) * self.s)

    # ---- API used by critters ----
    def line(self, pts, colour, width):
        self._line([self.P(x, y) for x, y in pts], colour, max(1.0, width * self.s))

    def oval(self, cx, cy, rx, ry, colour):
        x1, y1 = self.P(cx - rx, cy - ry)
        x2, y2 = self.P(cx + rx, cy + ry)
        self._oval(x1, y1, x2, y2, colour)

    def poly(self, pts, colour):
        self._poly([self.P(x, y) for x, y in pts], colour)

    def curve(self, p0, p1, p2, colour, width):
        self.line(bezier(p0, p1, p2), colour, width)

    def rrect(self, x1, y1, x2, y2, r, colour):
        self.poly(rrect_points(x1, y1, x2, y2, r), colour)

    # ---- backend ----
    def _line(self, pts, colour, width):
        raise NotImplementedError

    def _poly(self, pts, colour):
        raise NotImplementedError

    def _oval(self, x1, y1, x2, y2, colour):
        raise NotImplementedError
