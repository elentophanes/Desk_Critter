# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""Robot: a small orange robot with an antenna light. Waves its right arm."""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
from ._painter import rotate_all, eye, mix, done_pulse, DONE_EYE, DONE_BRIGHT, DONE_DIM, DONE_GLOW

NAME = "Robot"
ORDER = 2
SOUND = "robot.wav"                # made by tools/make_sounds.py
SOUND_DONE = "robot_done.wav"

COLOURS = {
    "normal": {"body": "#E8833A", "trim": "#B85E1F", "face": "#FFF4E6", "led": "#6EC6F5",
               "dark": "#2B2B2B", "cheek": "#F5B7A8", "white": "#FFFFFF"},
    "alert":  {"body": "#FF5A36", "trim": "#D9361A", "face": "#FFF4E6", "led": "#FFD34D",
               "dark": "#2B2B2B", "cheek": "#F5A3A3", "white": "#FFFFFF"},
}


def draw(p, f, c):
    # When Claude has finished, every light goes green with a slow heartbeat pulse: antenna
    # (with a glow), all three chest lights, and the face screen gets a pale green tint.
    # The idle lights are blue so that green is a clear change.
    done = getattr(f, "done", False)
    pulse = done_pulse(f)                                  # 0..1
    led = mix(DONE_DIM, DONE_BRIGHT, pulse) if done else c["led"]
    side = mix(DONE_EYE, DONE_BRIGHT, pulse) if done else c["face"]
    face = mix(c["face"], DONE_GLOW, 0.45 + 0.55 * pulse) if done else c["face"]

    # Left arm hangs down, behind the body
    p.line([(306, 202), (292, 222), (290, 232)], c["trim"], 10)
    p.oval(290, 234, 6, 6, c["trim"])

    # Legs and feet
    p.rrect(318, 226, 331, 240, 4, c["trim"])
    p.rrect(349, 226, 362, 240, 4, c["trim"])
    p.oval(324, 242, 11, 5, c["trim"])
    p.oval(356, 242, 11, 5, c["trim"])

    # Body with three status lights
    p.rrect(304, 192, 376, 232, 14, c["body"])
    p.oval(328, 212, 4, 4, side)
    p.oval(340, 212, 4, 4, led)
    p.oval(352, 212, 4, 4, side)

    # Antenna with light (and a glow ring when done)
    p.line([(340, 128), (340, 110)], c["trim"], 3)
    if done:
        r = 8.5 + pulse * 2
        p.oval(340, 104, r, r, mix(DONE_DIM, DONE_GLOW, 0.3 + 0.7 * pulse))
    p.oval(340, 104, 6, 6, led)

    # Ears and head
    p.rrect(288, 148, 298, 172, 4, c["trim"])
    p.rrect(382, 148, 392, 172, 4, c["trim"])
    p.rrect(294, 126, 386, 190, 20, c["body"])
    p.rrect(306, 138, 374, 180, 13, face)

    # Eyes
    eye(p, f, 325, 157, 6, 8, c["dark"], c["white"])
    eye(p, f, 355, 157, 6, 8, c["dark"], c["white"])

    # Cheeks and smile
    p.oval(314, 170, 4, 4, c["cheek"])
    p.oval(366, 170, 4, 4, c["cheek"])
    p.curve((333, 170), (340, 177), (347, 170), c["dark"], 2.5)

    # Right arm waves, drawn last so it is in front
    sh = (374, 200)
    arm = [sh] + rotate_all([(394, 180), (402, 154)], *sh, -f.wave)
    p.line(arm, c["trim"], 10)
    p.oval(*arm[-1], 7, 7, c["trim"])
