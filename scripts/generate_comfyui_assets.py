"""
ComfyUI batch generator for Starve No More illustration assets.

Generates:
  - 5 location scene tiles (1024x1024)
  - 2 path decoration variants (1024x1024)
  - 10 character standees (512x1024) — front + back per character
  - 8 boss/creature standees (512x1024)
  - ~150 card illustrations (1024x1024) — one per row of content/cards_*.csv
  - 24 achievement icons (1024x1024) — one per row of content/achievements.csv

Usage:
  1. Start ComfyUI (default: http://127.0.0.1:8000)
  2. Run: python scripts/generate_comfyui_assets.py [options]
  3. Images save to ComfyUI output/ with prefixed filenames
  4. python scripts/sync_comfyui_output.py   # copies outputs into repo art/
  5. python scripts/generate_card_atlases.py  # composites cards
  6. python scripts/generate_achievement_icons.py  # crops/frames the icons
  7. python scripts/build_save.py             # packages the TTS save

Options:
  --cards-only         Queue only card illustrations
  --no-cards           Queue only the board assets (tiles, paths, chars, bosses)
  --deck NAME          Limit cards to one deck (phase1..4, market, recipes,
                       threats, visitors, trophies). May be repeated.
  --only ID            Queue only one card by exact id (e.g. P1_QUIET_EVENING)
  --achievements-only  Queue only the achievement icons
  --no-achievements    Skip the achievement icons
  --skip-existing      Skip any prompt whose ComfyUI output PNG already exists
  [substring]          Backward-compatible positional filter (e.g. snm_boss)

Requires: ComfyUI running with flux1-dev-Q8_0.gguf, clip_l, t5xxl_fp16, ae.safetensors
"""

import argparse
import csv
import glob
import json
import os
import random
import sys
import urllib.request

COMFYUI_URL = "http://127.0.0.1:8000"
COMFYUI_OUTPUT_DIR = r"c:\Users\GGPC\Documents\ComfyUI\output"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")

# --------------------------------------------------------------------------
# Locked art direction — Don't Starve Together aesthetic with a modern,
# urban (North American suburban) twist. Applies to EVERY image this
# script generates. Keep this in sync with agents.md "ComfyUI Workflow".
# --------------------------------------------------------------------------
STYLE = (
    "Don't Starve Together aesthetic, Tim Burton meets Edward Gorey, "
    "hand-drawn ink-line gothic cartoon, scratchy crosshatch shading, "
    "muted desaturated palette with warm amber highlights and one saturated red for danger, "
    "silhouette-distinct shapes, spindly limbs, slightly exaggerated proportions, "
    "eerie cozy atmosphere — but transplanted into a modern North American suburb: "
    "contemporary clothing and props, smartphones, energy drink cans, gaming PCs, "
    "basketball hoops, badminton nets, suburban houses and streetlights — "
    "all rendered in the same hand-drawn DST style (no photoreal, no 3D), "
    "board game illustration, high detail, no text, no watermark, no UI"
)

NEGATIVE = (
    "blurry, low quality, watermark, text, deformed, photorealistic, "
    "3d render, anime, cartoon, chibi, neon colors, oversaturated"
)

# STYLE minus the scene-prop enumeration, for single-object icons.
#
# STYLE names concrete props ("suburban houses and streetlights", "gaming PCs",
# "basketball hoops") because a card illustration is a *scene* and those props
# furnish it. An achievement icon has no scene to furnish, so Flux attaches the
# props to the only thing in frame and renders the prop AS the subject: a first
# pass at the 24 icons came back with a glowing streetlight or amber orb
# dominating ~20 of them, whatever the row's art_notes actually asked for.
# Keep the aesthetic, drop the furniture. See docs/comfyui-achievement-icons.md.
ICON_STYLE = (
    "Don't Starve Together aesthetic, Tim Burton meets Edward Gorey, "
    "hand-drawn ink-line gothic cartoon, scratchy crosshatch shading, "
    "muted desaturated palette with one saturated red for danger, "
    "silhouette-distinct shapes, slightly exaggerated proportions, "
    "a modern North American suburban object rendered in the same hand-drawn "
    "DST style (no photoreal, no 3D), board game illustration, high detail, "
    "no text, no watermark, no UI"
)

# Card-specific qualifier appended after the per-deck prefix and art_notes.
CARD_QUALIFIER = (
    "full-bleed square card illustration, no text, no border, no UI, "
    "single coherent scene"
)

# --------------------------------------------------------------------------
# Achievement icons. Different job from a card: an icon is read at 46px in the
# panel and 64px in the Steam overlay, so it needs ONE object, centred, on a
# dark field, with nothing in the corners (generate_achievement_icons.py
# vignettes and frames it, which eats the edges). Everything that makes a card
# illustration good — a scene, a horizon, several figures — makes an icon mud.
#
# The glow trap (2026-07): an earlier prefix asked for "a plain dark
# background, dramatic single warm light source, heavy contrast" and Flux
# obliged too literally — it made the *subject itself* the light source and
# shrank it to a fifth of the frame. Don't describe the lighting as a source
# in the frame; describe it as falling from outside it. The wording below
# deliberately mirrors the `market` deck prefix ("a single object portrait ...
# soft warm side-light"), which is proven on this exact model + LoRA. Note
# also that Flux barely honours negations in a positive prompt — "no horizon,
# no background scenery" mostly just reinforced the emptiness. Put exclusions
# in NEGATIVE, not here.
#
# Expect high seed variance regardless of wording: one object on a dark field
# is close to a degenerate region, and a bad seed yields a pure black frame or
# an off-prompt neon blob. That is a re-roll, not a prompt bug — see
# docs/comfyui-achievement-icons.md, "Prefix fault vs. seed variance".
# --------------------------------------------------------------------------
ACHIEVEMENT_PREFIX = (
    "a single object portrait on a moody desaturated backdrop, "
    "even diffuse lighting, crisp hand-drawn ink outlines"
)

ACHIEVEMENT_QUALIFIER = (
    "icon composition, subject centred and filling two thirds of the frame, "
    "readable as a shape at thumbnail size, evenly lit, square"
)

# Same as the cards. This was briefly dropped to 0.35 while chasing the glowing
# orb, but the orb was the cfg 4.0 problem below, not the LoRA — and c4r1mj34
# is what supplies the DST ink line, so a weak one just makes icons that don't
# match the deck.
ICON_LORA_STRENGTH = 0.85

# Flux Dev is guidance-distilled: it wants a FluxGuidance node plus cfg 1.0,
# not true CFG. The cards' cfg 4.0 is off-spec and is the best explanation for
# the blown-out "glowing orb", the pure-black frames and the prompt drift the
# icon batch kept producing. Icons opt in; cards stay as they were.
ICON_FLUX_GUIDANCE = 3.5

# Per-deck visual framing. Combined with the row's art_notes column.
# Each prefix carries the scene + lighting context for that deck. The shared
# style (DST aesthetic, ink linework, modern-urban twist) lives in STYLE.
CARD_DECK_PREFIXES = {
    "phase1":   "an ominous suburban scene at dawn, warm amber streetlights against deep blue sky, atmospheric, calm-before-storm",
    "phase2":   "a tense suburban scene as things grow strange, warm amber light spilling onto cracked pavement, deep blue dusk, eerie",
    "phase3":   "a frightening suburban scene at long night, cold deep blue night with scattered warm amber light sources, long shadows",
    "phase4":   "an apocalyptic suburban scene in the final hours, broken amber streetlights, deep navy sky with sickly red horizon, urban decay",
    "market":   "a single object portrait on a moody desaturated backdrop, soft warm side-light, props from a modern suburban home",
    "recipes":  "food in or beside a crockpot, warm overhead kitchen light, steam rising, modern suburban kitchen",
    "threats":  "a creature portrait, dramatic chiaroscuro, eerie, single saturated red accent",
    "visitors": "a character portrait, three-quarter view, soft warm side-light, modern suburban teenager",
    "trophies": "a single trophy artifact on display, ceremonial low warm light, museum-style backdrop",
}

# --------------------------------------------------------------------------
# Asset definitions: (filename_prefix, width, height, prompt)
# --------------------------------------------------------------------------
ASSETS = [
    # ---- Location tiles (1024x1024 square scenes) ----
    ("snm_loc_jameshome", 1024, 1024,
     "interior of a teenage boy's messy bedroom, gaming PC with glowing monitor, "
     "energy drink cans, posters on walls, dim desk lamp light, cozy clutter, "
     "seen from above like a board game tile, " + STYLE),

    ("snm_loc_raymanhome", 1024, 1024,
     "interior of a sporty teenager's bedroom, basketball trophies on shelf, "
     "sports posters, sneakers by the door, athletic tape on desk, "
     "warm overhead light, seen from above like a board game tile, " + STYLE),

    ("snm_loc_ellielucahome", 1024, 1024,
     "interior of a shared sibling house, cozy kitchen with crockpot on counter, "
     "bookshelf with notebooks, reading lamp, two beds visible in back room, "
     "homey warm lighting, seen from above like a board game tile, " + STYLE),

    ("snm_loc_basketballcourt", 1024, 1024,
     "abandoned outdoor basketball court at dusk, cracked concrete, "
     "rusty hoop with torn net, overgrown weeds at edges, fog rolling in, "
     "a few scattered supplies on the ground, eerie streetlight glow, "
     "seen from above like a board game tile, " + STYLE),

    ("snm_loc_badmintoncourt", 1024, 1024,
     "abandoned outdoor badminton court at dusk, cracked pavement, "
     "sagging net between rusty poles, overgrown weeds pushing through cracks, "
     "scattered shuttlecocks on the ground, chain-link fence with ivy, "
     "dim yellow security light casting long shadows, "
     "seen from above like a board game tile, " + STYLE),

    # ---- Path decoration variants (1024x1024) ----
    ("snm_path_ring", 1024, 1024,
     "top-down view of a suburban cul-de-sac neighborhood arranged in a ring shape, "
     "five houses connected by winding paths forming a circle, streetlights and hedges, "
     "board game path overlay with faint grid lines, " + STYLE),

    ("snm_path_star", 1024, 1024,
     "top-down view of a suburban neighborhood paths arranged in a star pattern, "
     "five locations at star points connected by paths through a central crossroads, "
     "streetlights and fences along walkways, board game path overlay, " + STYLE),

    # ---- Character standees ----
    # Character standee art (snm_char_*) is HAND-DRAWN by the project owner —
    # do NOT auto-generate or replace these. Existing files in art/characters/
    # are authoritative. If a regen is ever needed, add the prompts back here
    # explicitly and commit that change deliberately.

    # ---- Boss / creature standees (512x1024) ----
    ("snm_boss_deerclops", 512, 1024,
     "towering one-eyed deer monster, Deerclops from Don't Starve inspired, "
     "massive antlers, single glowing eye, dark fur, looming over a basketball court, "
     "menacing stance, ice crystals forming around hooves, " + STYLE),

    ("snm_boss_eye_of_terror", 512, 1024,
     "giant floating eyeball creature, Eye of Terror, tentacle-like optic nerves trailing below, "
     "bloodshot iris glowing sickly green, hovering over a suburban house, "
     "reality warping around it, " + STYLE),

    ("snm_boss_the_source", 512, 1024,
     "eldritch cosmic horror entity, The Source, amorphous dark mass with many eyes, "
     "tendrils of shadow reaching outward, faint stars visible within its form, "
     "the ground cracks beneath it, final boss energy, " + STYLE),

    ("snm_boss_charlie", 512, 1024,
     "shadowy feminine figure lurking in darkness, Charlie from Don't Starve inspired, "
     "barely visible silhouette with glowing white eyes, "
     "wisps of shadow extending like claws, pure darkness incarnate, " + STYLE),

    ("snm_boss_hound", 512, 1024,
     "dark shadowy hellhound, skeletal features visible through matted fur, "
     "glowing red eyes, bared fangs dripping shadow, low aggressive stance, "
     "smoke trailing from body, " + STYLE),

    ("snm_boss_spider_queen", 512, 1024,
     "enormous spider queen monster, bloated abdomen, many gleaming eyes, "
     "legs like gnarled tree branches, web strands trailing, "
     "crown-like formation of chitin on head, " + STYLE),

    ("snm_boss_treeguard", 512, 1024,
     "living tree monster, Treeguard, massive trunk body with branch-arms, "
     "angry knothole face with glowing amber eyes, roots for legs, "
     "leaves falling as it moves, towering and ancient, " + STYLE),

    ("snm_boss_bearger", 512, 1024,
     "massive bear-badger hybrid monster, Bearger, enormously fat and powerful, "
     "tiny angry eyes, huge claws, standing upright and roaring, "
     "ground shaking beneath its weight, fur matted and dark, " + STYLE),
]


# --------------------------------------------------------------------------
# Card illustration loading — reads content/cards_*.csv and builds
# (filename_prefix, w, h, prompt) tuples in the same shape as ASSETS.
# --------------------------------------------------------------------------

# Order matters only for log readability.
CARD_DECK_FILES = [
    ("phase1",   "cards_phase1.csv"),
    ("phase2",   "cards_phase2.csv"),
    ("phase3",   "cards_phase3.csv"),
    ("phase4",   "cards_phase4.csv"),
    ("market",   "cards_market.csv"),
    ("recipes",  "cards_recipes.csv"),
    ("threats",  "cards_threats.csv"),
    ("visitors", "cards_visitors.csv"),
    ("trophies", "cards_trophies.csv"),
    ("starting", "cards_starting.csv"),
]


def _row_subject(deck, row):
    """Per-row subject line — usually art_notes; falls back per deck."""
    notes = (row.get("art_notes") or "").strip()
    if notes:
        return notes
    if deck == "visitors":
        # No art_notes column today.
        char = row.get("character", "an unknown visitor")
        trig = row.get("trigger", "")
        return f"a portrait of {char}, {trig}".strip(", ")
    name = row.get("title") or row.get("name") or row.get("id") or "unknown"
    return name


def build_card_prompt(deck, row):
    """Compose a full prompt for one card row."""
    parts = [
        CARD_DECK_PREFIXES.get(deck, ""),
        _row_subject(deck, row),
        CARD_QUALIFIER,
        STYLE,
    ]
    return ", ".join(p for p in parts if p)


def load_card_assets(deck_filter=None, only_id=None):
    """Yield (filename_prefix, w, h, prompt, deck, card_id) tuples.

    deck_filter: optional iterable of deck names to include (e.g. {"phase1"}).
    only_id: optional exact card id (e.g. "P1_QUIET_EVENING").
    """
    out = []
    for deck, fname in CARD_DECK_FILES:
        if deck_filter and deck not in deck_filter:
            continue
        path = os.path.join(CONTENT_DIR, fname)
        if not os.path.isfile(path):
            print(f"  warn: missing {path}")
            continue
        with open(path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                card_id = (row.get("id") or "").strip()
                if not card_id:
                    continue
                if only_id and card_id != only_id:
                    continue
                prefix = f"snm_card_{card_id}"
                prompt = build_card_prompt(deck, row)
                out.append((prefix, 1024, 1024, prompt, deck, card_id))
    return out


def load_achievement_assets(only_id=None):
    """Yield (filename_prefix, w, h, prompt) for content/achievements.csv.

    The `art_notes` column is the subject; the icon framing and the shared
    STYLE do the rest, so adding an achievement means adding a CSV row and
    nothing else. Output lands as snm_ach_<base>_00001_.png, which
    sync_comfyui_output.py files under art/achievements/src/ — the *source*
    tree, not the icons themselves: generate_achievement_icons.py crops,
    vignettes and frames those into the sizes the mod and Steam want.
    """
    path = os.path.join(CONTENT_DIR, "achievements.csv")
    if not os.path.isfile(path):
        print(f"  warn: missing {path}")
        return []
    out = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            aid = (row.get("id") or "").strip()
            if not aid or (only_id and aid != only_id):
                continue
            subject = (row.get("art_notes") or "").strip() or row.get("name", aid)
            prompt = ", ".join([ACHIEVEMENT_PREFIX, subject, ACHIEVEMENT_QUALIFIER, ICON_STYLE])
            out.append((f"snm_ach_{aid[2:].lower()}", 1024, 1024, prompt))
    return out


def output_already_exists(filename_prefix):
    """True if ComfyUI has already written <prefix>_*.png to its output dir."""
    pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"{filename_prefix}_*.png")
    return bool(glob.glob(pattern))


def build_workflow(positive_prompt, negative_prompt, width, height, filename_prefix,
                   lora_strength=0.85, flux_guidance=None):
    """Build a single-pass Flux Dev workflow (no ControlNet, no upscale).

    `flux_guidance` switches the sampler to the configuration Flux Dev is
    actually distilled for: a FluxGuidance node carrying the guidance scale,
    and KSampler at cfg 1.0 (true CFG > 1 on a distilled model blows out
    highlights and drifts off-prompt). Cards deliberately stay on the original
    cfg 4.0 path — 200+ of them were rendered that way. See
    docs/comfyui-achievement-icons.md.
    """
    seed = random.randint(1, 2**53)
    positive_link = ["4", 0]
    cfg = 4.0
    guidance_node = {}
    if flux_guidance is not None:
        guidance_node = {
            "11": {
                "class_type": "FluxGuidance",
                "inputs": {
                    "conditioning": ["4", 0],
                    "guidance": flux_guidance
                }
            }
        }
        positive_link = ["11", 0]
        cfg = 1.0

    return {
        # UnetLoaderGGUF
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {
                "unet_name": "flux1-dev-Q8_0.gguf"
            }
        },
        # DualCLIPLoader
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp16.safetensors",
                "type": "flux",
                "device": "default"
            }
        },
        # LoraLoader — c4r1mj34 for stylized illustration look
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["2", 0],
                "lora_name": "flux\\c4r1mj34.safetensors",
                "strength_model": lora_strength,
                "strength_clip": lora_strength
            }
        },
        # CLIPTextEncode (positive)
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["3", 1],
                "text": positive_prompt
            }
        },
        # CLIPTextEncode (negative)
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["3", 1],
                "text": negative_prompt
            }
        },
        # EmptyLatentImage
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
        # KSampler
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["3", 0],
                "positive": positive_link,
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": 30,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        # VAELoader
        "8": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        # VAEDecode
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["8", 0]
            }
        },
        # SaveImage
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["9", 0],
                "filename_prefix": filename_prefix
            }
        },
        **guidance_node,
    }


def queue_prompt(workflow):
    """Send a workflow to ComfyUI's queue."""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(
        description="Queue Starve No More illustration prompts to ComfyUI."
    )
    parser.add_argument("filter", nargs="?", default=None,
                        help="Backward-compatible substring filter on filename "
                             "(e.g. 'snm_boss').")
    parser.add_argument("--cards-only", action="store_true",
                        help="Queue only card illustrations (skip board assets).")
    parser.add_argument("--no-cards", action="store_true",
                        help="Queue only the board assets (skip card illustrations).")
    parser.add_argument("--deck", action="append", default=[],
                        choices=[d for d, _ in CARD_DECK_FILES],
                        help="Limit cards to one deck. May be repeated.")
    parser.add_argument("--only", default=None,
                        help="Queue only one card (or achievement) by exact id "
                             "(e.g. P1_QUIET_EVENING, A_HERO).")
    parser.add_argument("--achievements-only", action="store_true",
                        help="Queue only the achievement icons.")
    parser.add_argument("--no-achievements", action="store_true",
                        help="Skip the achievement icons.")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip prompts whose ComfyUI output PNG already exists.")
    args = parser.parse_args()

    if args.cards_only and args.no_cards:
        parser.error("--cards-only and --no-cards are mutually exclusive")
    if args.achievements_only and args.no_achievements:
        parser.error("--achievements-only and --no-achievements are mutually exclusive")

    # ---- Assemble the prompt list ----
    assets = []  # list of (prefix, w, h, prompt) — stripped of card-only fields

    if not args.cards_only and not args.achievements_only:
        for tup in ASSETS:
            assets.append(tup)

    if not args.no_cards and not args.achievements_only:
        deck_filter = set(args.deck) if args.deck else None
        for prefix, w, h, prompt, _deck, _cid in load_card_assets(deck_filter, args.only):
            assets.append((prefix, w, h, prompt))

    if not args.no_achievements and not args.cards_only:
        only = args.only if (args.only or "").startswith("A_") else None
        assets.extend(load_achievement_assets(only))

    if args.filter:
        assets = [a for a in assets if args.filter in a[0]]
        print(f"Filtering assets matching: {args.filter}")

    if args.skip_existing:
        before = len(assets)
        assets = [a for a in assets if not output_already_exists(a[0])]
        skipped = before - len(assets)
        if skipped:
            print(f"Skipping {skipped} prompts whose output already exists.")

    if not assets:
        print("No matching assets to queue.")
        sys.exit(0 if args.skip_existing else 1)

    print(f"Starve No More — queueing {len(assets)} assets to ComfyUI at {COMFYUI_URL}")
    print("Style: Don't Starve Together aesthetic + modern urban (suburban) twist")
    print("Model: Flux Dev Q8 + c4r1mj34 LoRA (0.85)")
    print()

    success = 0
    for i, (prefix, w, h, prompt) in enumerate(assets, 1):
        # Icons take the LoRA at reduced strength: at 0.85 it dominates a
        # single-object composition and keeps painting a glowing lamp/orb as
        # the subject. Cards keep the full 0.85 the deck art was built with.
        is_icon = prefix.startswith("snm_ach_")
        lora = ICON_LORA_STRENGTH if is_icon else 0.85
        workflow = build_workflow(
            prompt, NEGATIVE, w, h, prefix,
            lora_strength=lora,
            flux_guidance=ICON_FLUX_GUIDANCE if is_icon else None,
        )
        try:
            result = queue_prompt(workflow)
            pid = result.get("prompt_id", "?")
            print(f"  [{i}/{len(assets)}] {prefix} ({w}x{h}) — queued ({pid[:8]})")
            success += 1
        except Exception as e:
            print(f"  [{i}/{len(assets)}] {prefix} — FAILED: {e}")

    print()
    print(f"Done: {success}/{len(assets)} queued.")
    print()
    print("Wait for ComfyUI to finish, then:")
    print("  python scripts/sync_comfyui_output.py          # copy outputs into repo art/")
    print("  python scripts/generate_card_atlases.py        # composite card faces")
    print("  python scripts/generate_achievement_icons.py   # crop/frame the icons")
    print("  python scripts/build_save.py                   # rebuild the TTS save")


if __name__ == "__main__":
    main()
