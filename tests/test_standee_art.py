"""The standee cutouts, checked as pixels rather than as intentions.

build_save gives each Figurine_Custom a ColorDiffuse that TTS applies as a
MULTIPLY over the WHOLE image, so a backdrop left opaque is not neutral — it
becomes a slab of the character's tint. That is why normalize_standee_art.py
can flood a plain backdrop away, opt-in per character via CUT_BACKGROUND.

The opt-in is a claim about a specific piece of art, and art gets redrawn
underneath it. James was the one entry until his art changed (2026-08) from a
figure on cream parchment into a designed card — illustrated scene, scribbled
border, name banner. Nothing in the pipeline fails loudly when that happens:
normalize() sees a border that is no longer plain, REFUSES, returns None, and
the PREVIOUS _standee.png stays on disk. New art in the repo, old art on the
table, green build. These tests are what makes that state fail.
"""
import os

import pytest
from conftest import ROOT

pytest.importorskip("PIL")
import normalize_standee_art as n  # noqa: E402  (scripts/ on sys.path via conftest)
from PIL import Image  # noqa: E402

CHARS = os.path.join(ROOT, "art", "characters")

FACES = [(c, f) for c in n.CHARACTERS for f in n.FACES]


def _source(char, face):
    return os.path.join(CHARS, f"{char}_{face}.png")


def _standee(char, face):
    return os.path.join(CHARS, f"{char}_{face}_standee.png")


def _open(path, char, face):
    if not os.path.isfile(path):
        pytest.skip(f"{char}_{face}: {os.path.basename(path)} not present")
    return Image.open(path)


def _opaque_fraction(img):
    if img.mode != "RGBA":
        return 1.0
    a = img.getchannel("A")
    return sum(1 for p in a.get_flattened_data() if p > 0) / float(a.size[0] * a.size[1])


# --------------------------------------------------------------------------
# The opt-in lists must match the art they make claims about


@pytest.mark.parametrize("char", sorted(n.CUT_BACKGROUND))
@pytest.mark.parametrize("face", n.FACES)
def test_listed_art_actually_has_a_plain_border(char, face):
    """The failure this module exists for.

    A character listed for background removal whose art is NOT a figure on a
    plain backdrop makes normalize() refuse and silently keep the old standee.
    Catch it here, where the message can say what to do, rather than on the
    table three playtests later.
    """
    img = _open(_source(char, face), char, face)
    if img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255:
        return  # already cut out upstream; the flood never runs
    uniform, spread = n._uniform_border(img)
    assert uniform, (
        f"{char}_{face} is in CUT_BACKGROUND but its border is not plain "
        f"(spread {spread} >= {n.UNIFORM_MAX_SPREAD}) — normalize_standee_art.py "
        f"will REFUSE it and leave the previous standee in place. If the art is "
        f"now a designed card, remove '{char}' from CUT_BACKGROUND.")


def test_enclosed_pocket_rule_only_covers_characters_being_cut():
    """CUT_ENCLOSED_BELOW clears backdrop the border flood could not reach, so
    it does nothing unless that flood runs at all."""
    stray = set(n.CUT_ENCLOSED_BELOW) - n.CUT_BACKGROUND
    assert not stray, (
        f"{sorted(stray)} in CUT_ENCLOSED_BELOW but not CUT_BACKGROUND — the "
        "enclosed-pocket pass only runs as part of background removal, so this "
        "entry has no effect and reads as though it does.")


# --------------------------------------------------------------------------
# Every standee, whichever path produced it


@pytest.mark.parametrize("char,face", FACES)
def test_every_standee_is_the_canvas_build_save_authors_against(char, face):
    img = _open(_standee(char, face), char, face)
    assert img.size == (n.OUT_W, n.OUT_H), (
        f"{char}_{face}_standee is {img.size}, not {(n.OUT_W, n.OUT_H)} — "
        "Figurine_Custom stretches its image to its own aspect, so an odd "
        "canvas squashes the figure. Rerun scripts/normalize_standee_art.py")


@pytest.mark.parametrize("char,face", FACES)
def test_standee_is_no_older_than_its_source(char, face):
    src, out = _source(char, face), _standee(char, face)
    if not (os.path.isfile(src) and os.path.isfile(out)):
        pytest.skip(f"{char}_{face}: source or standee absent")
    assert os.path.getmtime(out) >= os.path.getmtime(src), (
        f"{char}_{face}.png is newer than its _standee.png — the standee is "
        "stale and the game is still showing the old art. Rerun "
        "scripts/normalize_standee_art.py")


@pytest.mark.parametrize("char,face", FACES)
def test_a_designed_card_keeps_its_whole_illustration(char, face):
    """The counterweight to the cut, and it is not hypothetical.

    An early version of the pocket pass ran on the FLOODED image at the border
    flood's own tolerance. "Backdrop-coloured and still opaque" walked straight
    through James's jacket highlights and skin — one component covering 18% of
    the canvas — and cleared his jacket, face and shins. A designed card that
    comes back partly transparent has been eaten exactly that way.
    """
    if char in n.CUT_BACKGROUND:
        pytest.skip(f"{char} is a cutout, covered by the cutout tests")
    src = _open(_source(char, face), char, face)
    if src.mode == "RGBA" and src.getchannel("A").getextrema()[0] < 255:
        pytest.skip(f"{char}_{face}: source art is itself transparent")
    frac = _opaque_fraction(_open(_standee(char, face), char, face))
    assert frac == 1.0, (
        f"{frac:.1%} of {char}_{face}_standee is opaque, but the source is a "
        "designed card with no transparency — something cut into the artwork.")


@pytest.mark.parametrize("char", sorted(n.CUT_BACKGROUND))
@pytest.mark.parametrize("face", n.FACES)
def test_a_cutout_is_a_figure_and_not_a_slab_or_a_ghost(char, face):
    """A blunt whole-image check: a cut that has eaten the character, or one
    that never removed the backdrop, both show up as the opaque area long
    before anyone looks at the table."""
    frac = _opaque_fraction(_open(_standee(char, face), char, face))
    assert 0.18 < frac < 0.55, (
        f"{frac:.0%} of {char}_{face}_standee is opaque — expected a standing "
        "figure (~1/4 to 1/2). Too little means the cut ate the art; too much "
        "means the backdrop is still there and will render as a slab of tint.")
