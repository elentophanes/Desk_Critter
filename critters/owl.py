# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""Owl: a round little owl with big eyes. Flaps both wings."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
from ._painter import rotate_all, eye

NAME = "Owl"
ORDER = 4
SOUND = "owl.wav"                  # made by tools/make_sounds.py
SOUND_DONE = "owl_done.wav"

COLOURS = {
    "normal": {"body": "#C98B5A", "wing": "#9C6A42", "belly": "#F3D9B1", "face": "#FFF4E6",
               "beak": "#F2A33A", "dark": "#2B2B2B", "white": "#FFFFFF", "mark": "#D8B48A"},
    "alert":  {"body": "#FF6A3D", "wing": "#D9361A", "belly": "#FFE08A", "face": "#FFF4E6",
               "beak": "#FFB000", "dark": "#2B2B2B", "white": "#FFFFFF", "mark": "#FFC266"},
}


def draw(p, f, c):
    # Feet
    for x in (326, 354):
        for dx in (-5, 0, 5):
            p.line([(x, 236), (x + dx, 244)], c["beak"], 3)

    # Ear tufts and body
    p.poly([(306, 150), (304, 126), (324, 140)], c["wing"])
    p.poly([(374, 150), (376, 126), (356, 140)], c["wing"])
    p.oval(340, 188, 46, 52, c["body"])

    # Belly with feather marks
    p.oval(340, 210, 28, 28, c["belly"])
    for x, y in ((330, 202), (350, 202), (340, 214), (330, 224), (350, 224)):
        p.curve((x - 5, y), (x, y + 5), (x + 5, y), c["mark"], 2)

    # Eye discs and eyes
    p.oval(322, 166, 17, 17, c["face"])
    p.oval(358, 166, 17, 17, c["face"])
    eye(p, f, 323, 167, 7.5, 8, c["dark"], c["white"], hl=(2, -3, 2.5))
    eye(p, f, 357, 167, 7.5, 8, c["dark"], c["white"], hl=(2, -3, 2.5))

    # Beak
    p.poly([(334, 182), (346, 182), (340, 194)], c["beak"])

    # Wings flap, drawn last so they are in front
    flap = f.wave * 1.6
    lsh, rsh = (300, 180), (380, 180)
    p.poly(rotate_all([lsh, (284, 196), (286, 222), (302, 216)], *lsh, flap), c["wing"])
    p.poly(rotate_all([rsh, (396, 196), (394, 222), (378, 216)], *rsh, -flap), c["wing"])
