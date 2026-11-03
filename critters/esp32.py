# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""ESP32: a little dev board with legs. LED eyes, waves two jumper-wire arms."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
from ._painter import rotate_all, mix, done_pulse, DONE_EYE, DONE_BRIGHT, DONE_DIM, DONE_GLOW

NAME = "ESP32 board"
ORDER = 5
SOUND = "esp32.wav"                # made by tools/make_sounds.py
SOUND_DONE = "esp32_done.wav"

COLOURS = {
    "normal": {"pcb": "#1F6F8B", "edge": "#164F63", "shield": "#C9CED6", "shield_dark": "#9AA1AB",
               "trace": "#E8C15A", "pin": "#E8C15A", "led": "#4FC3F7", "wire": "#E8833A",
               "dark": "#2B2B2B", "white": "#FFFFFF"},
    "alert":  {"pcb": "#FF5A36", "edge": "#D9361A", "shield": "#E3E6EA", "shield_dark": "#B5BAC2",
               "trace": "#FFD34D", "pin": "#FFD34D", "led": "#FF3B30", "wire": "#FFD34D",
               "dark": "#2B2B2B", "white": "#FFFFFF"},
}


def draw(p, f, c):
    # When Claude has finished, the whole board lights up green: antenna trace, header pins
    # and LED eyes, with a slow heartbeat pulse (blue LEDs alone did not stand out from green).
    done = getattr(f, "done", False)
    pulse = done_pulse(f)                                  # 0..1
    lit = mix(DONE_EYE, DONE_BRIGHT, pulse) if done else None

    # Pin legs and feet
    for x0, x1 in ((318, 312), (362, 368)):
        p.line([(x0, 226), (x1, 240)], c["pin"], 4)
        p.oval(x1, 242, 7, 3.5, c["dark"])

    # Board
    p.rrect(298, 116, 382, 230, 7, c["edge"])
    p.rrect(301, 119, 379, 227, 5, c["pcb"])

    # PCB antenna trace along the top
    p.line([(308, 136), (308, 126), (318, 126), (318, 134), (328, 134), (328, 126),
            (338, 126), (338, 134), (348, 134), (348, 126), (358, 126), (358, 134),
            (368, 134), (368, 126), (372, 126)], lit or c["trace"], 2.6 if done else 2)

    # Header pins down both sides
    for y in range(146, 222, 10):
        p.oval(307, y, 2.6, 2.6, lit or c["pin"])
        p.oval(373, y, 2.6, 2.6, lit or c["pin"])

    # Metal shield with the face
    p.rrect(314, 142, 366, 194, 4, c["shield_dark"])
    p.rrect(316, 144, 364, 192, 3, c["shield"])
    # LED eyes: pulsing green with a glow halo when Claude has finished
    ry = 0.8 if f.blink else 6
    led = mix(DONE_DIM, DONE_BRIGHT, pulse) if done else c["led"]
    if done and not f.blink:
        halo = mix(c["shield"], DONE_GLOW, 0.4 + pulse * 0.6)
        r = 8.5 + 1.5 * pulse
        p.oval(330, 162, r, r, halo)
        p.oval(350, 162, r, r, halo)
    p.oval(330, 162, 6, ry, led)
    p.oval(350, 162, 6, ry, led)
    if not f.blink:
        p.oval(332, 160, 1.8, 1.8, c["white"])
        p.oval(352, 160, 1.8, 1.8, c["white"])
    p.curve((333, 176), (340, 183), (347, 176), c["dark"], 2.5)

    # USB port at the bottom edge
    p.rrect(330, 214, 350, 228, 3, c["shield_dark"])
    p.rrect(334, 218, 346, 224, 2, c["dark"])

    # Jumper-wire arms wave, drawn last so they are in front
    lsh, rsh = (302, 172), (378, 172)
    left = [lsh] + rotate_all([(282, 156), (270, 128)], *lsh, f.wave)
    right = [rsh] + rotate_all([(398, 156), (410, 128)], *rsh, -f.wave)
    for arm in (left, right):
        p.line(arm, c["wire"], 5)
        p.rrect(arm[-1][0] - 4, arm[-1][1] - 6, 4 + arm[-1][0], 6 + arm[-1][1], 2, c["dark"])
