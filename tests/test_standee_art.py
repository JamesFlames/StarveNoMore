"""The standee cutouts, checked as pixels rather than as intentions.

build_save gives each Figurine_Custom a ColorDiffuse that TTS applies as a
MULTIPLY over the WHOLE image, so any backdrop left opaque is not neutral — it
becomes a slab of the character's tint. James's is a strong blue.

The border flood in normalize_standee_art.py only starts at the edges, by
design, so it cannot reach anything the figure encloses. That left a cream
wedge between his shins that read as a skirt on the table, and cream slabs
under both arms.
"""
import os

import pytest
from conftest import ROOT

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

CHARS = os.path.join(ROOT, "art", "characters")

# Probes in output-canvas fractions (the standee is normalised to 512x1024, so
# these are stable). Measured on the current art.
TRANSPARENT = [
    ((0.50, 0.78), "the gap between the legs"),
]
OPAQUE = [
    ((0.50, 0.20), "his face"),
    ((0.50, 0.45), "his jacket"),
    ((0.50, 0.62), "his thighs"),
]


def _alpha(img, fx, fy):
    w, h = img.size
    return img.getchannel("A").getpixel((int(fx * w), int(fy * h)))


@pytest.fixture(scope="module")
def james():
    path = os.path.join(CHARS, "james_front_standee.png")
    if not os.path.isfile(path):
        pytest.skip("james_front_standee.png not generated")
    return Image.open(path).convert("RGBA")


@pytest.mark.parametrize("probe,label", TRANSPARENT)
def test_enclosed_backdrop_is_cut(james, probe, label):
    assert _alpha(james, *probe) == 0, (
        f"{label} is still opaque — it will render as a slab of James's blue "
        "tint. Rerun scripts/normalize_standee_art.py")


@pytest.mark.parametrize("probe,label", OPAQUE)
def test_the_figure_itself_survives(james, probe, label):
    """The counterweight, and it is not hypothetical.

    The first attempt ran the pocket detection on the FLOODED image at the
    border flood's own tolerance. "Backdrop-coloured and still opaque" then
    walked straight through the jacket highlights and the skin — one component
    covering 18% of the canvas — and cleared his jacket, face and shins while
    leaving the leg gap exactly as it found it.
    """
    assert _alpha(james, *probe) == 255, (
        f"{label} was cut away — the pocket pass is eating the figure")


def test_the_cutout_keeps_most_of_the_figure(james):
    """A blunt whole-image check: a cutout that has eaten the character shows
    up as a collapsed opaque area long before anyone looks at the table."""
    a = james.getchannel("A")
    opaque = sum(1 for p in a.get_flattened_data() if p > 0)
    frac = opaque / float(james.size[0] * james.size[1])
    assert 0.18 < frac < 0.55, (
        f"{frac:.0%} of the canvas is opaque — expected a standing figure "
        "(~1/4 to 1/2). Too little means the cut ate the art; too much means "
        "the backdrop is still there.")
