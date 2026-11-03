# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Make critters/cat.wav: a synthetic "meow" for the cat critter. Standard library only.

    py tools\\make_meow.py            (Windows)
    python3 tools/make_meow.py        (macOS)

How it works (a tiny voice synthesiser):
  - a buzzy source: a fundamental plus its harmonics (like vocal cords), whose pitch
    rises and then falls: "mi-AAA-ow"
  - three resonant band-pass filters (formants, like the mouth) whose centre frequencies
    slide from an "ee" towards "ah" and then "oo": that slide is what makes it sound like
    a meow instead of a whistle
  - a soft start (the "m"), a long fade out, a little vibrato and a breath of noise

Tweak the numbers in the SHAPE section and run it again to change the meow.
Replace critters/cat.wav with any other short .wav (e.g. a real recording) if you prefer:
this script won't overwrite a file it didn't make unless you add --force (see make_sounds.py).
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import math
import os
import random
import sys

from make_sounds import save_wav

RATE = 22050                 # samples per second
SECONDS = 0.85
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "critters", "cat.wav")

# ---------------- SHAPE: (time 0..1, value) points, straight lines in between ----------------
PITCH = [(0.0, 520), (0.25, 820), (0.5, 760), (1.0, 470)]        # Hz
F1 = [(0.0, 350), (0.35, 950), (0.7, 750), (1.0, 500)]            # formant 1, Hz
F2 = [(0.0, 2300), (0.3, 1700), (0.7, 1100), (1.0, 850)]          # formant 2, Hz
F3 = [(0.0, 3200), (0.4, 2800), (1.0, 2500)]                      # formant 3, Hz
FORMANT_GAIN = (1.0, 0.7, 0.35)
BANDWIDTH = (90, 130, 220)                                        # Hz
VIBRATO_HZ, VIBRATO_DEPTH = 6.0, 0.015
NOISE = 0.03
VOLUME = 0.8                                                       # peak, 0..1


def curve(points, u):
    for (u0, v0), (u1, v1) in zip(points, points[1:]):
        if u <= u1:
            return v0 + (v1 - v0) * (u - u0) / (u1 - u0)
    return points[-1][1]


def envelope(u):
    attack = min(1.0, u / 0.10)
    attack = attack * attack * (3 - attack * 2)                    # smooth "m" onset
    release = 1.0 if u < 0.5 else (1 - (u - 0.5) / 0.5) ** 2       # long "ow" fade
    return attack * release


def main(args):
    save_wav(os.path.normpath(OUT), synth(), RATE, force="--force" in args)


def synth():
    rng = random.Random(1)
    n = int(RATE * SECONDS)
    phase = 0.0
    state = [[0.0, 0.0] for _ in range(3)]
    out = []
    for i in range(n):
        u = i / n
        f0 = curve(PITCH, u) * (1 + VIBRATO_DEPTH * math.sin(math.pi * 2 * VIBRATO_HZ * i / RATE))
        phase += math.pi * 2 * f0 / RATE
        # buzzy source: harmonics with falling strength, stopping below 5.5 kHz
        src = sum(math.sin(k * phase) / k for k in range(1, 1 + int(5500 / f0)))
        src += NOISE * (rng.random() * 2 - 1) * 4
        y = 0.0
        for j, (fpts, gain, bw) in enumerate(zip((F1, F2, F3), FORMANT_GAIN, BANDWIDTH)):
            f = curve(fpts, u)
            r = math.exp(-math.pi * bw / RATE)
            a1, a2 = -2 * r * math.cos(math.pi * 2 * f / RATE), r * r
            y1, y2 = state[j]
            yn = (1 - r) * src - a1 * y1 - a2 * y2
            state[j] = [yn, y1]
            y += gain * yn
        out.append(y * envelope(u))
    peak = max(abs(s) for s in out) or 1.0
    return [s / peak * VOLUME for s in out]


if __name__ == "__main__":
    main(sys.argv[1:])
