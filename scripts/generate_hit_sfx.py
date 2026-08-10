"""generate_hit_sfx.py — synthesize the two combat impact sounds.

Combat had no audio of its own: a fight was dice text scrolling past in the
log while the table stayed silent. These are the two beats a player needs to
hear without reading anything —

    Hit_Land_Sound.wav   -> AUDIO.SFX.hit_land    you connected
    Hit_Taken_Sound.wav  -> AUDIO.SFX.hit_taken   something connected with you

They are deliberately a matched pair with opposite shapes, because the whole
job is telling them apart from across the table while looking at the board
rather than the screen:

    land   bright, short, ends UP-tight   — a clean crack, over quickly
    taken  darker, longer, bends DOWN     — a dull thud that sags

Synthesized rather than sourced, like tick_chime / turn_ping / night_growl
before them: no licence to track, no binary anyone has to go find again, and
the shape is editable here instead of in an audio tool. Stdlib only (`wave`,
`math`, `random`) so this runs anywhere the rest of the pipeline does.

Deterministic: the noise is drawn from a SEEDED generator, so re-running this
produces byte-identical files and a clean `git status`. Do not remove the
seed — an unseeded rebuild would show up as a spurious binary diff in every
commit that happened to touch audio.

Run:  python scripts/generate_hit_sfx.py
Then: python scripts/generate_audio_manifest.py   (or just scripts/check.py)
"""

import math
import os
import random
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX = os.path.join(ROOT, "sounds", "sfx")

RATE = 44100
AMPLITUDE = 0.82          # peak before the 16-bit conversion; leaves headroom


def _envelope(t, duration, attack, curve):
    """Fast attack, exponential decay. `curve` is how sharply it falls."""
    if t < attack:
        return t / attack
    frac = (t - attack) / max(1e-6, duration - attack)
    return math.exp(-curve * frac)


def _impact(duration, f_start, f_end, noise_level, noise_decay, curve, seed):
    """One percussive hit: a pitch-bending sine body plus a noise transient.

    The body carries the weight and the bend carries the meaning (down = you
    got hurt). The noise is the initial crack — it decays much faster than the
    body, which is what makes it read as an impact rather than a beep.
    """
    rng = random.Random(seed)
    n = int(RATE * duration)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / RATE
        frac = t / duration
        # Exponential pitch glide: linear in Hz sounds like a siren, not a hit.
        freq = f_start * ((f_end / f_start) ** frac)
        phase += 2.0 * math.pi * freq / RATE
        body = math.sin(phase)
        # A little second harmonic gives the body some edge so it survives
        # small laptop speakers, which roll off everything under ~150 Hz.
        body += 0.3 * math.sin(2.0 * phase)
        noise = (rng.random() * 2.0 - 1.0) * noise_level * math.exp(-noise_decay * frac)
        out.append((body * 0.7 + noise) * _envelope(t, duration, 0.002, curve))
    return out


def _normalize(samples):
    peak = max(abs(s) for s in samples) or 1.0
    return [s / peak * AMPLITUDE for s in samples]


def _write(path, samples):
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    return os.path.getsize(path) / 1024.0


def hit_land():
    """You connected: a short bright crack that ends before you notice it."""
    return _impact(duration=0.22, f_start=420, f_end=190,
                   noise_level=0.55, noise_decay=34, curve=7.5, seed=20260810)


def hit_taken():
    """Something connected with YOU: lower, longer, and it sags away."""
    body = _impact(duration=0.44, f_start=190, f_end=62,
                   noise_level=0.32, noise_decay=22, curve=4.2, seed=20260811)
    # A second, softer knock 60 ms in. One impact reads as a bump; the
    # double-knock reads as taking a blow — it is the same trick a punch
    # foley uses, and it costs nothing here.
    knock = _impact(duration=0.30, f_start=150, f_end=55,
                    noise_level=0.22, noise_decay=26, curve=5.0, seed=20260812)
    offset = int(RATE * 0.06)
    for i, s in enumerate(knock):
        j = i + offset
        if j < len(body):
            body[j] += s * 0.55
    return body


def main():
    if not os.path.isdir(SFX):
        raise SystemExit(f"no sounds/sfx directory at {SFX}")
    print(f"Synthesizing combat impact SFX into {SFX}")
    for fname, maker in (("Hit_Land_Sound.wav", hit_land),
                         ("Hit_Taken_Sound.wav", hit_taken)):
        samples = _normalize(maker())
        path = os.path.join(SFX, fname)
        kb = _write(path, samples)
        key = fname[:-len("_Sound.wav")].lower()
        print(f"  {fname:22s} {len(samples) / RATE:.2f}s  {kb:6.1f} KB  "
              f"-> AUDIO.SFX.{key}")
    print("\nnow run: python scripts/generate_audio_manifest.py")


if __name__ == "__main__":
    main()
