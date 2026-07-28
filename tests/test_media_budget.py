"""No single tracked binary may be huge.

`sounds/ambient/varied/battlegrounds fall night_ds_amb.wav` was 17 MB — by
itself ~6 % of all tracked media — because it escaped the ambient-audio
compression pass (commit 04a96a2) and nothing noticed for a month. Converted to
OGG q4 like its neighbours it is 1.0 MB, so the fix was cheap; *finding* it was
the expensive part.

Git keeps every version of a binary forever, and history is not worth rewriting
to reclaim one (see the plan's non-goals: it breaks every existing clone for a
one-time saving). So the only cheap moment to catch an oversized asset is
before it is committed the first time. This is that check.

Over budget does not mean "delete it" — it means compress it the way its
neighbours are compressed: OGG q4 for ambient audio, JPEG q88 for face
atlases, PNG only where alpha is actually needed.
"""
import os
import subprocess

import pytest
from conftest import ROOT

# Comfortable headroom over the current largest tracked asset (~2.9 MB) —
# high enough that no legitimate art or audio file trips it, low enough that
# an uncompressed WAV or a full-resolution render cannot slip in.
MAX_BYTES = 4 * 1024 * 1024

BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tga",
               ".wav", ".ogg", ".mp3", ".flac", ".aiff",
               ".zip", ".7z", ".gz", ".pdf", ".mp4", ".mov"}

# Assets that are deliberately allowed over the cap, each with a reason.
# Keep this empty if you can; an entry here is a permanent exception.
OVERSIZE_ALLOWLIST = {}


def tracked_binaries():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return None
    if out.returncode != 0:  # pragma: no cover
        return None
    return [f for f in out.stdout.split("\0")
            if f and os.path.splitext(f)[1].lower() in BINARY_EXTS]


def test_no_tracked_binary_is_oversized():
    files = tracked_binaries()
    if files is None:  # pragma: no cover
        pytest.skip("git not available")
    assert files, "no tracked binaries found — is this a git checkout?"

    over = []
    for rel in files:
        if rel in OVERSIZE_ALLOWLIST:
            continue
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        size = os.path.getsize(path)
        if size > MAX_BYTES:
            over.append((size, rel))

    over.sort(reverse=True)
    assert not over, (
        f"tracked binary file(s) over the {MAX_BYTES // (1024 * 1024)} MB budget:\n"
        + "".join(f"  {s / 1e6:6.1f} MB  {r}\n" for s, r in over)
        + "Compress it the way its neighbours are compressed (ambient audio -> "
          "OGG q4, deck face atlases -> JPEG q88), or add it to "
          "OVERSIZE_ALLOWLIST in this file with a reason. Do NOT rewrite git "
          "history to reclaim an old blob — that breaks every existing clone "
          "for a one-time saving."
    )


def test_no_uncompressed_ambient_audio():
    """Ambient tracks are minutes long; WAV is the wrong format for them.

    Short SFX stay WAV on purpose (they are tiny and latency-sensitive), so
    this only covers the ambient tree.
    """
    files = tracked_binaries()
    if files is None:  # pragma: no cover
        pytest.skip("git not available")
    # Only files still on disk: a deletion that is staged but not yet
    # committed still shows in `git ls-files`, and failing on one would be
    # confusing exactly while someone is doing the right thing.
    wavs = sorted(f for f in files
                  if f.startswith("sounds/ambient/") and f.lower().endswith(".wav")
                  and os.path.isfile(os.path.join(ROOT, f)))
    assert not wavs, (
        f"uncompressed WAV(s) under sounds/ambient/: {wavs} — convert to OGG "
        "q4 (ffmpeg -c:a libvorbis -q:a 4) and rerun "
        "scripts/generate_audio_manifest.py"
    )
