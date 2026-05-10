"""
ComfyUI batch generator for Starve No More illustration assets.

Generates the 23 images that need AI illustration (not data-driven):
  - 5 location scene tiles (1024x1024)
  - 10 character standees (512x1024) — front + back per character
  - 8 boss/creature standees (512x1024)

Usage:
  1. Start ComfyUI (default: http://127.0.0.1:8000)
  2. Run: python scripts/generate_comfyui_assets.py
  3. Images save to ComfyUI output/ with prefixed filenames
  4. Copy final images into art/ subfolders and re-run build_save.py

Requires: ComfyUI running with flux1-dev-Q8_0.gguf, clip_l, t5xxl_fp16, ae.safetensors
"""

import json
import urllib.request
import random
import sys
import os

COMFYUI_URL = "http://127.0.0.1:8000"

# --------------------------------------------------------------------------
# Style prefix — Tim Burton / Edward Gorey aesthetic for the whole game
# --------------------------------------------------------------------------
STYLE = (
    "dark whimsical illustration, Tim Burton meets Edward Gorey style, "
    "ink crosshatching, muted desaturated palette with warm amber highlights, "
    "slightly exaggerated proportions, eerie cozy atmosphere, "
    "board game art, high detail, no text, no watermark"
)

NEGATIVE = (
    "blurry, low quality, watermark, text, deformed, photorealistic, "
    "3d render, anime, cartoon, chibi, neon colors, oversaturated"
)

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

    # ---- Character standees — FRONT (512x1024 portrait) ----
    ("snm_char_james_front", 512, 1024,
     "full body portrait of a teenage boy gamer, 16 years old, messy dark hair, "
     "hoodie with headphones around neck, holding a pocketknife and flashlight, "
     "confident smirk, standing pose facing viewer, transparent background, " + STYLE),

    ("snm_char_coco_front", 512, 1024,
     "full body portrait of a gentle teenage girl, 15 years old, long light hair, "
     "wearing a comfort blanket as a shawl, holding a first aid kit, "
     "serene calm expression, soft inner glow, standing pose facing viewer, "
     "transparent background, " + STYLE),

    ("snm_char_rayman_front", 512, 1024,
     "full body portrait of a tall athletic teenage boy, 17 years old, "
     "basketball jersey, holding a basketball under one arm, sports drink in other hand, "
     "determined expression, strong build, standing pose facing viewer, "
     "transparent background, " + STYLE),

    ("snm_char_ellie_front", 512, 1024,
     "full body portrait of a teenage girl cook, 16 years old, apron over casual clothes, "
     "holding a cooking knife and soup ladle, hair tied back, "
     "warm confident smile, standing pose facing viewer, transparent background, " + STYLE),

    ("snm_char_luca_front", 512, 1024,
     "full body portrait of a teenage boy orator, 15 years old, neat casual clothes, "
     "holding a notebook and pencil, expressive hand gesture, "
     "earnest inspiring expression, standing pose facing viewer, "
     "transparent background, " + STYLE),

    # ---- Character standees — BACK (512x1024) ----
    ("snm_char_james_back", 512, 1024,
     "back view of a teenage boy gamer, messy dark hair, hoodie with headphones, "
     "backpack with gaming stickers, standing pose from behind, "
     "transparent background, " + STYLE),

    ("snm_char_coco_back", 512, 1024,
     "back view of a gentle teenage girl, long light flowing hair, "
     "comfort blanket draped over shoulders, standing pose from behind, "
     "transparent background, " + STYLE),

    ("snm_char_rayman_back", 512, 1024,
     "back view of a tall athletic teenage boy in basketball jersey, "
     "number on back, basketball under arm, standing pose from behind, "
     "transparent background, " + STYLE),

    ("snm_char_ellie_back", 512, 1024,
     "back view of a teenage girl in apron, hair tied back, "
     "cooking utensils in apron pocket, standing pose from behind, "
     "transparent background, " + STYLE),

    ("snm_char_luca_back", 512, 1024,
     "back view of a teenage boy, neat casual clothes, "
     "notebook tucked under arm, standing pose from behind, "
     "transparent background, " + STYLE),

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


def build_workflow(positive_prompt, negative_prompt, width, height, filename_prefix):
    """Build a single-pass Flux Dev workflow (no ControlNet, no upscale)."""
    seed = random.randint(1, 2**53)

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
                "strength_model": 0.65,
                "strength_clip": 0.65
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
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": seed,
                "steps": 30,
                "cfg": 4.0,
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
    # Optional: filter by prefix
    filter_prefix = None
    if len(sys.argv) > 1:
        filter_prefix = sys.argv[1]
        print(f"Filtering assets matching: {filter_prefix}")

    assets = ASSETS
    if filter_prefix:
        assets = [a for a in ASSETS if filter_prefix in a[0]]

    if not assets:
        print("No matching assets found.")
        sys.exit(1)

    print(f"Starve No More — queueing {len(assets)} assets to ComfyUI at {COMFYUI_URL}")
    print(f"Style: Tim Burton / Edward Gorey illustration")
    print(f"Model: Flux Dev Q8 + c4r1mj34 LoRA (0.65)")
    print()

    success = 0
    for i, (prefix, w, h, prompt) in enumerate(assets, 1):
        workflow = build_workflow(prompt, NEGATIVE, w, h, prefix)
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
    print("After generation, copy outputs to the StarveNoMore art/ folders:")
    print("  Location tiles   -> art/tiles/")
    print("  Character fronts -> art/characters/")
    print("  Character backs  -> art/characters/")
    print("  Boss standees    -> art/bosses/")
    print()
    print("Then re-run: python scripts/build_save.py")


if __name__ == "__main__":
    main()
