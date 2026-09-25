"""
Generate lua/audio_manifest.lua from the on-disk sounds/ tree.

Walks `sounds/` and emits a Lua table grouping URLs + durations by category:
  - AUDIO.AMBIENT_SUBURBAN  — sounds/ambient/suburban/*
  - AUDIO.AMBIENT_VARIED    — sounds/ambient/varied/*
  - AUDIO.AMBIENT_NIGHT     — sounds/ambient/night/*  (low drones for the Night phase)
  - AUDIO.CREATURES.<name>  — sounds/creatures/<name>/*  (bearger/deerclops/eye_of_terror/treeguard)
  - AUDIO.SFX.<key>         — sounds/sfx/*  (key = lowercased stem, trailing
                              "_sound" stripped: Character_Walk_Sound.ogg → character_walk)

Durations:
  - .wav files: read precisely via stdlib `wave` module
  - .ogg files: read exactly from the Ogg stream (ogg_duration), no tools needed
  - .mp3 files (and any .ogg that won't parse): ffprobe when available, else
    estimated from file size. The estimate only needs to be roughly right —
    we use it as a Wait.time after which we schedule the next track. A few
    seconds off-by means a few seconds of dead air before the next track starts.

(2026-07: compressed clips are OGG Vorbis — TTS rejected several of the
original MP3s with "Unsupported file format".)

Run: python scripts/generate_audio_manifest.py
Output: lua/audio_manifest.lua
"""

import os
import shutil
import subprocess
import wave

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOUNDS_DIR = os.path.join(REPO_ROOT, "sounds")
OUT_LUA = os.path.join(REPO_ROOT, "lua", "audio_manifest.lua")
URL_BASE = "http://localhost:8080"

# Size-estimate fallbacks (bytes/sec) when ffprobe is unavailable.
MP3_AVG_BPS = 16000   # 128 kbps
OGG_AVG_BPS = 14000   # Vorbis q4 ≈ 112 kbps

_FFPROBE = shutil.which("ffprobe")


def wav_duration(path):
    with wave.open(path, "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate) if rate else 0.0


def ogg_duration(path):
    """Exact duration read out of the Ogg stream itself. None if unparseable.

    The last Ogg page's granule position IS the stream's total sample count,
    and the Vorbis identification header carries the sample rate — so the
    exact answer is two seeks away, with no external tool and no dependency.

    Worth doing rather than falling back to size/OGG_AVG_BPS: that estimate
    assumes a fixed ~112 kbps, and a quieter track encodes far below it. On
    'battlegrounds_fall_night_ds_amb.ogg' (81 kbps) the estimate said 71.6 s
    for a 99.1 s track — a 28 % error, and AUDIO durations are what schedule
    the next ambient track, so the error is audible as a clip cut short.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(8192)
            if not head.startswith(b"OggS"):
                return None
            # Vorbis identification header: 0x01 "vorbis", version(4),
            # channels(1), sample_rate(4).
            i = head.find(b"\x01vorbis")
            if i < 0:
                return None
            rate = int.from_bytes(head[i + 12:i + 16], "little")
            if not rate:
                return None
            size = f.seek(0, os.SEEK_END)
            # The final page is near the end; 64 KiB covers a large page.
            tail_len = min(size, 65536)
            f.seek(size - tail_len)
            tail = f.read(tail_len)
            j = tail.rfind(b"OggS")
            if j < 0 or j + 14 > len(tail):
                return None
            # Page header: "OggS"(4) version(1) type(1) granule_position(8).
            granule = int.from_bytes(tail[j + 6:j + 14], "little")
            if granule in (0, 0xFFFFFFFFFFFFFFFF):
                return None
            return granule / float(rate)
    except OSError:
        return None


def probe_duration(path):
    """Precise duration via ffprobe, or None if unavailable/unreadable."""
    if not _FFPROBE:
        return None
    try:
        out = subprocess.run(
            [_FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except (ValueError, subprocess.SubprocessError, OSError):
        return None


def duration_for(path):
    p = path.lower()
    if p.endswith(".wav"):
        try:
            return wav_duration(path)
        except wave.Error:
            return os.path.getsize(path) / 88200.0  # fallback: 16-bit 44.1k mono
    if p.endswith(".ogg"):
        # Exact, and available everywhere — prefer it over ffprobe so the
        # manifest is byte-identical whether or not ffmpeg is installed
        # (a freshness test compares the committed file against a fresh run).
        d = ogg_duration(path)
        if d:
            return d
    if p.endswith((".mp3", ".ogg")):
        d = probe_duration(path)
        if d:
            return d
        bps = MP3_AVG_BPS if p.endswith(".mp3") else OGG_AVG_BPS
        return os.path.getsize(path) / float(bps)
    return None


def url_for(rel_path):
    # Forward slashes only; no URL encoding here — keep dev simple.
    rel = rel_path.replace("\\", "/")
    return f"{URL_BASE}/{rel}"


def list_clips(rel_dir):
    """Yield (filename, url, duration) for audio files directly under rel_dir."""
    abs_dir = os.path.join(REPO_ROOT, rel_dir)
    if not os.path.isdir(abs_dir):
        return []
    out = []
    for fname in sorted(os.listdir(abs_dir)):
        ap = os.path.join(abs_dir, fname)
        if not os.path.isfile(ap):
            continue
        if not fname.lower().endswith((".wav", ".mp3", ".ogg")):
            continue
        dur = duration_for(ap)
        if dur is None or dur <= 0:
            print(f"  warn: zero/unknown duration for {ap}; defaulting to 180")
            dur = 180.0
        rel = os.path.join(rel_dir, fname).replace("\\", "/")
        out.append((fname, url_for(rel), dur))
    return out


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit_table(lines, indent, items):
    """items: list of (filename, url, duration). Writes one entry per line."""
    pad = " " * indent
    for fname, url, dur in items:
        lines.append(f"{pad}{{ url = {lua_str(url)}, duration = {dur:.2f}, name = {lua_str(fname)} }},")


def main():
    suburban = list_clips("sounds/ambient/suburban")
    varied   = list_clips("sounds/ambient/varied")
    night    = list_clips("sounds/ambient/night")
    creatures = {}
    creatures_dir = os.path.join(SOUNDS_DIR, "creatures")
    if os.path.isdir(creatures_dir):
        for boss in sorted(os.listdir(creatures_dir)):
            full = os.path.join(creatures_dir, boss)
            if os.path.isdir(full):
                creatures[boss] = list_clips(f"sounds/creatures/{boss}")
    # All files under sounds/sfx/ become AUDIO.SFX.<key> entries.
    # Key = filename stem, lowercased, with a trailing "_sound" stripped.
    sfx_dir = os.path.join(SOUNDS_DIR, "sfx")
    sfx_entries = {}  # key -> (filename, url, duration)
    if os.path.isdir(sfx_dir):
        for fname in sorted(os.listdir(sfx_dir)):
            ap = os.path.join(sfx_dir, fname)
            if not os.path.isfile(ap):
                continue
            if not fname.lower().endswith((".wav", ".mp3", ".ogg")):
                continue
            stem = os.path.splitext(fname)[0]
            key = stem.lower()
            if key.endswith("_sound"):
                key = key[: -len("_sound")]
            dur = duration_for(ap) or 1.5
            sfx_entries[key] = (
                fname,
                url_for(f"sounds/sfx/{fname}"),
                dur,
            )

    L = []
    L.append("-- audio_manifest.lua")
    L.append("-- AUTO-GENERATED by scripts/generate_audio_manifest.py — do not edit by hand.")
    L.append("-- Sources: sounds/ambient/{suburban,varied,night}, sounds/creatures/*, sounds/sfx")
    L.append("-- Durations: exact for .wav and .ogg; .mp3 via ffprobe, else estimated from filesize.")
    L.append("")
    L.append("AUDIO = {}")
    L.append("")
    L.append("AUDIO.AMBIENT_SUBURBAN = {")
    emit_table(L, 4, suburban)
    L.append("}")
    L.append("")
    L.append("AUDIO.AMBIENT_VARIED = {")
    emit_table(L, 4, varied)
    L.append("}")
    L.append("")
    L.append("AUDIO.AMBIENT_NIGHT = {")
    emit_table(L, 4, night)
    L.append("}")
    L.append("")
    L.append("AUDIO.CREATURES = {}")
    for boss in sorted(creatures.keys()):
        L.append(f"AUDIO.CREATURES.{boss} = {{")
        emit_table(L, 4, creatures[boss])
        L.append("}")
        L.append("")
    L.append("AUDIO.SFX = {}")
    for key in sorted(sfx_entries.keys()):
        fname, url, dur = sfx_entries[key]
        L.append(f"AUDIO.SFX.{key} = {{ url = {lua_str(url)}, duration = {dur:.2f}, name = {lua_str(fname)} }}")
    L.append("")

    os.makedirs(os.path.dirname(OUT_LUA), exist_ok=True)
    with open(OUT_LUA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))

    # Summary
    counts = {
        "AMBIENT_SUBURBAN": len(suburban),
        "AMBIENT_VARIED":   len(varied),
        "AMBIENT_NIGHT":    len(night),
    }
    for boss, items in creatures.items():
        counts[f"CREATURES.{boss}"] = len(items)
    counts["SFX (total)"] = len(sfx_entries)
    print(f"wrote {os.path.relpath(OUT_LUA, REPO_ROOT)}")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if sfx_entries:
        print("  SFX keys: " + ", ".join(sorted(sfx_entries.keys())))


if __name__ == "__main__":
    main()
