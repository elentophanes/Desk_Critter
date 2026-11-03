# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""Cat: a round ginger cat. Waves a paw and swishes its tail."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import math
from ._painter import rotate_all, eye

NAME = "Cat"
ORDER = 3
SOUND = "cat.wav"                  # played instead of the chime (made by tools/make_meow.py)
SOUND_DONE = "cat_done.wav"        # quiet purr when Claude has finished (tools/make_sounds.py)

COLOURS = {
    "normal": {"fur": "#F2A65A", "stripe": "#D9822B", "belly": "#FFE8CC", "inner": "#F5A3A3",
               "dark": "#2B2B2B", "white": "#FFFFFF", "nose": "#E86F7A"},
    "alert":  {"fur": "#FF6A3D", "stripe": "#D9361A", "belly": "#FFE08A", "inner": "#FFB3A0",
               "dark": "#2B2B2B", "white": "#FFFFFF", "nose": "#D9361A"},
}


def draw(p, f, c):
    # Tail swishes slowly (faster when alerting), behind the body
    sway = math.sin(f.t * (6 if f.alert else 2)) * 10
    p.curve((370, 228), (420 + sway, 226), (sway + 414, 176), c["stripe"], 10)
    p.oval(sway + 414, 176, 5, 5, c["stripe"])

    # Body, belly and feet
    p.oval(340, 210, 38, 32, c["fur"])
    p.oval(340, 218, 22, 20, c["belly"])
    p.oval(320, 240, 12, 6, c["fur"])
    p.oval(360, 240, 12, 6, c["fur"])
    p.line([(316, 238), (316, 243)], c["stripe"], 1.5)
    p.line([(324, 238), (324, 243)], c["stripe"], 1.5)
    p.line([(356, 238), (356, 243)], c["stripe"], 1.5)
    p.line([(364, 238), (364, 243)], c["stripe"], 1.5)

    # Ears
    p.poly([(302, 150), (308, 106), (336, 132)], c["fur"])
    p.poly([(378, 150), (372, 106), (344, 132)], c["fur"])
    p.poly([(309, 140), (312, 117), (328, 133)], c["inner"])
    p.poly([(371, 140), (368, 117), (352, 133)], c["inner"])

    # Head with forehead stripes
    p.oval(340, 158, 42, 36, c["fur"])
    p.line([(340, 124), (340, 136)], c["stripe"], 3)
    p.line([(330, 126), (332, 136)], c["stripe"], 3)
    p.line([(350, 126), (348, 136)], c["stripe"], 3)

    # Eyes
    eye(p, f, 325, 156, 6, 8, c["dark"], c["white"])
    eye(p, f, 355, 156, 6, 8, c["dark"], c["white"])

    # Nose, mouth, cheeks, whiskers
    p.poly([(335, 168), (345, 168), (340, 174)], c["nose"])
    p.curve((340, 174), (337, 180), (331, 178), c["dark"], 2)
    p.curve((340, 174), (343, 180), (349, 178), c["dark"], 2)
    p.oval(316, 170, 4.5, 4.5, c["inner"])
    p.oval(364, 170, 4.5, 4.5, c["inner"])
    for y1, y2 in ((166, 162), (172, 174)):
        p.line([(312, y1), (290, y2)], c["dark"], 1.5)
        p.line([(368, y1), (390, y2)], c["dark"], 1.5)

    # Right paw waves, drawn last so it is in front
    sh = (370, 200)
    paw = [sh] + rotate_all([(394, 182), (404, 158)], *sh, -f.wave)
    p.line(paw, c["fur"], 12)
    p.oval(*paw[-1], 8, 8, c["fur"])
    p.oval(paw[-1][0], paw[-1][1] + 2, 3.5, 3, c["inner"])
