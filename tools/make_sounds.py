# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Make the critters' sound files (critters/*.wav). Standard library only.

    py tools\\make_sounds.py              make them all          (Windows)
    py tools\\make_sounds.py owl robot    only those names
    python3 tools/make_sounds.py          (macOS)

The cat's meow has its own script (tools/make_meow.py); everything else is here.
Each sound is one small function below: change its numbers and run again.

    name               when              what it is
    owl                alert             "whoo ... whooo": two breathy notes swooping up
    owl_done           done              a single quiet "whoo"
    robot              alert             R2-D2-style warble of electronic chirps
    robot_done         done              happy rising "bee-doo!"
    esp32              alert             piezo buzzer "bip-bip-biiip"
    esp32_done         done              quick rising two-tone "OK" chirp
    spider_skitter     alert (option)    eight tiny feet scurrying
    spider_boing       alert (option)    cartoon spring "boing"
    spider_done        done              three soft taps
    cat_done           done              a short purr

Your own recordings are safe: the script only overwrites a .wav that is still exactly as it
made it (it keeps fingerprints in tools/generated_sounds.json). A file you replaced or edited is
skipped with a message; add --force to overwrite it anyway:
    py tools\\make_sounds.py owl --force

Which file a critter plays is set in its critters/<name>.py:
    SOUND = "owl.wav"            alert sound (else the normal chime)
    SOUND_DONE = "owl_done.wav"  done sound (else silent)
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import hashlib
import json
import math
import os
import random
import struct
import sys
import wave

RATE = 22050
TAU = math.pi * 2
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "critters")
FINGERPRINTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_sounds.json")


# ---------------- building blocks ----------------
def silence(seconds):
    return [0.0] * int(RATE * seconds)


def env(i, n, attack=0.01, release=0.05):
    """Simple fade in / fade out over a note of n samples (times in seconds)."""
    a, r = int(attack * RATE) or 1, int(release * RATE) or 1
    return min(1.0, i / a, (n - i) / r)


def resonate(samples, freq, bandwidth):
    """Band-pass filter (one resonance), like a mouth shape or a tiny metal part."""
    r = math.exp(-math.pi * bandwidth / RATE)
    a1, a2 = -2 * r * math.cos(TAU * freq / RATE), r * r
    y1 = y2 = 0.0
    out = []
    for x in samples:
        y = (1 - r) * x - a1 * y1 - a2 * y2
        y2, y1 = y1, y
        out.append(y)
    return out


def tone(seconds, freq, harmonics=(1.0,), attack=0.01, release=0.05, vibrato=(0, 0)):
    """A note. freq is a number or a function of u (0..1 through the note).
    harmonics = strengths of harmonic 1, 2, 3, ..."""
    n = int(RATE * seconds)
    f_of = freq if callable(freq) else (lambda u: freq)
    vib_hz, vib_depth = vibrato
    out, phase = [], 0.0
    for i in range(n):
        u = i / n
        f = f_of(u) * (1 + vib_depth * math.sin(TAU * vib_hz * i / RATE))
        phase += TAU * f / RATE
        s = sum(h * math.sin(k * phase) for k, h in enumerate(harmonics, 1) if k * f < RATE / 2)
        out.append(s * env(i, n, attack, release))
    return out


def noise(seconds, seed=1):
    rng = random.Random(seed)
    return [rng.random() * 2 - 1 for _ in range(int(RATE * seconds))]


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def scale(samples, factor):
    return [s * factor for s in samples]


# ---------------- saving, without overwriting your recordings ----------------
def fingerprint(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def save_wav(path, samples, rate=RATE, force=False):
    """Write samples (-1..1) as a 16-bit mono .wav, unless the existing file is not ours.
    Returns True if written."""
    name = os.path.basename(path)
    prints = load_fingerprints()
    if os.path.exists(path) and not force and prints.get(name) != fingerprint(path):
        print(f"skipped {name}: it was replaced or changed since it was generated "
              f"(a recording?). Add --force to overwrite it.")
        return False
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    prints[name] = fingerprint(path)
    with open(FINGERPRINTS, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(prints.items())), f, indent=2)
    print(f"wrote {os.path.normpath(path)}  ({len(samples) / rate:.2f} s)")
    return True


def load_fingerprints():
    try:
        with open(FINGERPRINTS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write(name, samples, volume, force=False):
    peak = max(abs(s) for s in samples) or 1.0
    save_wav(os.path.join(OUT_DIR, name + ".wav"), [s / peak * volume for s in samples], force=force)


# ---------------- owl ----------------
def hoo(seconds, f_peak, f_end, seed):
    """One owl "whooo": a breathy "wh" puff, then the pitch swoops UP into the note and
    slides gently down. Mostly a pure tone (real owl hoots are), plus a little breath."""
    def pitch(u):
        if u < 0.2:                                        # the "w": swoop up from below
            return f_peak * (0.72 + math.sin(u / 0.2 * math.pi / 2) * 0.28)
        return f_peak + (f_end - f_peak) * (u - 0.2) / 0.8
    voice = tone(seconds, pitch, (1.0, 0.18, 0.05), attack=seconds * 0.22,
                 release=0.55 * seconds, vibrato=(5, 0.012))
    n = int(RATE * seconds)
    wh = resonate(noise(seconds, seed), 1.6 * f_peak, 900)              # the breathy "wh"
    a, peak_at = int(RATE * 0.08), int(RATE * 0.10)                     # fade in gently, never a thump
    wh = [x * min(1.0, i / a) * (1.0 if peak_at > i else max(0.3, 1 - (i - peak_at) / (0.25 * n)))
          * env(i, n, 0.01, seconds * 0.5) for i, x in enumerate(wh)]
    return mix(voice, scale(wh, 1.5))


def owl():
    return hoo(0.42, 640, 600, 1) + silence(0.22) + hoo(0.70, 650, 560, 2)     # "whoo ... whooo"


def owl_done():
    return hoo(0.45, 620, 570, 3)


# ---------------- robot ----------------
def chirp(seconds, f0, f1, trill=0.0):
    """Electronic chirp gliding f0 -> f1, optionally with a fast trill."""
    return tone(seconds, lambda u: (f0 + (f1 - f0) * u) * (1 + trill * math.sin(28 * TAU * u * seconds)),
                (1.0, 0.0, 0.2), attack=0.005, release=0.02)


def robot():
    rng = random.Random(7)
    out = []
    for _ in range(8):
        f0, f1 = rng.uniform(900, 2400), rng.uniform(900, 2400)
        out += chirp(rng.uniform(0.05, 0.1), f0, f1, trill=rng.choice((0, 0, 0.08)))
        out += silence(rng.uniform(0.01, 0.04))
    return out


def robot_done():
    return chirp(0.11, 880, 900) + silence(0.03) + chirp(0.22, 1100, 1760)


# ---------------- ESP32 board ----------------
PIEZO_HZ = 2000
PIEZO = (1.0, 0, 0.33, 0, 0.2)        # odd harmonics = square-ish, like a buzzer


def bip(seconds, freq=PIEZO_HZ):
    return tone(seconds, freq, PIEZO, attack=0.002, release=0.004)


def esp32():
    return bip(0.07) + silence(0.07) + bip(0.07) + silence(0.07) + bip(0.30)


def esp32_done():
    return bip(0.06, 2000) + silence(0.03) + bip(0.09, 2700)


# ---------------- spider ----------------
def click(freq, seed, decay=0.003):
    """One tiny tap: a burst of noise ringing at freq, gone in a few milliseconds."""
    n = int(0.03 * RATE)
    burst = [x * math.exp(-i / (decay * RATE)) for i, x in enumerate(noise(0.03, seed))]
    return resonate(burst, freq, 600)[:n]


def spider_skitter():
    rng = random.Random(3)
    out = silence(0.6)
    for k in range(18):                       # two quick scurries of tiny feet
        t = (k * 0.022 if k < 9 else 0.30 + (k - 9) * 0.022) + rng.uniform(0, 0.008)
        c = scale(click(rng.uniform(3000, 5000), k), rng.uniform(0.5, 1.0))
        start = int(t * RATE)
        for i, x in enumerate(c):
            out[start + i] += x
    return out


def spider_boing():
    seconds = 0.75
    return tone(seconds, lambda u: 220 + 70 * u + math.exp(-4 * u) * 90 * math.sin(11 * TAU * u * seconds),
                (1.0, 0.3, 0.15), attack=0.004, release=0.85 * seconds)


def spider_done():
    out = []
    for k, f in enumerate((3200, 3600, 4000)):
        out += click(f, 10 + k, decay=0.004) + silence(0.07)
    return out


# ---------------- cat ----------------
def cat_done():
    """Purr: a low rumble pulsing ~26 times a second, breathing in and out once."""
    out = []
    for seconds, bright, seed in ((0.55, 1.0, 4), (0.65, 0.7, 5)):     # in, out
        rumble = noise(seconds, seed)
        rumble = mix(resonate(rumble, 160, 90), scale(resonate(rumble, 450, 200), bright * 0.6))
        n = len(rumble)
        out += [x * (0.55 + 0.45 * math.sin(TAU * 26 * i / RATE)) * env(i, n, 0.12, 0.2)
                for i, x in enumerate(rumble)]
        out += silence(0.06)
    return out


# ---------------- name -> (function, loudness 0..1) ----------------
SOUNDS = {
    "owl": (owl, 0.8),
    "owl_done": (owl_done, 0.5),
    "robot": (robot, 0.6),
    "robot_done": (robot_done, 0.45),
    "esp32": (esp32, 0.45),           # piezo pitch is loud to the ear; keep the peak lower
    "esp32_done": (esp32_done, 0.35),
    "spider_skitter": (spider_skitter, 0.8),
    "spider_boing": (spider_boing, 0.7),
    "spider_done": (spider_done, 0.5),
    "cat_done": (cat_done, 0.7),
}


def main(args):
    force = "--force" in args
    names = [a for a in args if a != "--force"]
    for name in names or SOUNDS:
        if name not in SOUNDS:
            print(f"unknown sound '{name}'; choose from: {', '.join(SOUNDS)}")
            continue
        func, volume = SOUNDS[name]
        write(name, func(), volume, force)


if __name__ == "__main__":
    main(sys.argv[1:])
