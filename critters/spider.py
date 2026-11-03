# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""Spider: the original orange critter. Waves its two front legs."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
from ._painter import rotate_all, eye

NAME = "Spider"
ORDER = 1
SOUND = "spider_boing.wav"         # or "spider_skitter.wav" (made by tools/make_sounds.py)
SOUND_DONE = "spider_done.wav"

COLOURS = {
    "normal": {"leg": "#C9682A", "abdomen": "#E8833A", "spot": "#F4B072", "head": "#F09A55",
               "dark": "#2B2B2B", "white": "#FFFFFF", "cheek": "#F5A3A3"},
    "alert":  {"leg": "#D9361A", "abdomen": "#FF5A36", "spot": "#FFD34D", "head": "#FF7A50",
               "dark": "#2B2B2B", "white": "#FFFFFF", "cheek": "#F5A3A3"},
}

STANDING_LEGS = [((310, 198), (272, 176), (254, 242)),
                 ((312, 208), (262, 198), (236, 242)),
                 ((318, 216), (282, 220), (268, 242)),
                 ((370, 198), (408, 176), (426, 242)),
                 ((368, 208), (418, 198), (444, 242)),
                 ((362, 216), (398, 220), (412, 242))]


def draw(p, f, c):
    for pts in STANDING_LEGS:
        p.line(pts, c["leg"], 7)

    # Body
    p.oval(340, 148, 50, 42, c["abdomen"])
    p.oval(322, 134, 7, 7, c["spot"])
    p.oval(350, 124, 5, 5, c["spot"])
    p.oval(360, 150, 6, 6, c["spot"])
    p.oval(340, 200, 36, 36, c["head"])

    # Little top eyes
    p.oval(333, 174, 3, 3, c["dark"])
    p.oval(347, 174, 3, 3, c["dark"])

    # Big eyes
    p.oval(326, 194, 11, 11, c["white"])
    p.oval(354, 194, 11, 11, c["white"])
    eye(p, f, 327, 195, 6, 7, c["dark"], c["white"])
    eye(p, f, 355, 195, 6, 7, c["dark"], c["white"])

    # Cheeks and smile
    p.oval(316, 212, 4.5, 4.5, c["cheek"])
    p.oval(364, 212, 4.5, 4.5, c["cheek"])
    p.curve((332, 214), (340, 221), (348, 214), c["dark"], 2.5)

    # Two waving front legs, drawn LAST so they wave in front of the body
    lsh, rsh = (308, 196), (372, 196)
    p.line([lsh] + rotate_all([(280, 160), (264, 118)], *lsh, f.wave), c["leg"], 7)
    p.line([rsh] + rotate_all([(400, 160), (416, 118)], *rsh, -f.wave), c["leg"], 7)
