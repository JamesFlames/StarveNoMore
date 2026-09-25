# Publishing to the Steam Workshop

How *Starve No More* gets from this repo to a Tabletop Simulator Workshop item:
where the assets live, the one command that builds the release, and what is
still to do before the first upload. Measured against the current tree, not
guessed.

*Part of the [agent reference](agents/README.md); the index lives in [`agents.md`](../agents.md).*

## The short answer on hosting

**Steam does not host your images and audio for you as a side effect of
publishing a mod.** A TTS Workshop item is only the save JSON — the Lua bundle,
the XML UI and `ObjectStates` — plus a thumbnail. Every image and sound inside
it is a **URL**, and TTS fetches those URLs on each player's machine when the
mod loads. Publish with `file:///C:/Users/GGPC/...` in there (which is exactly
what the dev save `saves/StarveNoMore.json` contains) and every other player
gets a table of grey rectangles and total silence.

**This repo is the host.** It is public, and GitHub serves any committed file
at `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>` — and
`art/` and `sounds/` already sit at the paths the build expects. The published
save points at a **release tag**:

```
https://raw.githubusercontent.com/JamesFlames/StarveNoMore/v1.0/art/board/main_board.png
```

A tag never moves, which is what TTS needs: it caches every asset by URL,
forever, so a file replaced behind a URL a player already has never reaches
them. Every release gets a new tag, and so new URLs; old tags stay, so saves
in progress keep loading.

## Releasing

```bash
python scripts/check.py                      # green, committed, pushed main
git tag v1.0 && git push origin v1.0
python scripts/publish.py v1.0 --install
```

`scripts/publish.py` refuses unless HEAD *is* the pushed tag and no tracked file
is modified — so the save and the files its URLs serve come from one commit.
Then it:

1. runs `build_save.py --publish https://raw.githubusercontent.com/<owner>/<repo>/<tag>`
   → `saves/StarveNoMore.publish.json` (git-ignored; the dev saves are not
   touched). Every `file:///` and `http://localhost:8080` URL is rewritten,
   including `_BASE` in `lua/assets.lua`, and the build hard-fails if a local
   URL survives;
2. checks every asset the save references is a file **committed at the tag** —
   art that exists only on your disk would 404 for everyone else;
3. `HEAD`-checks every asset URL against GitHub (`--offline` skips this);
4. with `--install`, copies the save and its cover into the TTS Saves folder
   as `StarveNoMore Workshop <tag>`.

A full commit SHA already on `origin/main` works in place of a tag, to check a
release candidate without cutting one. `tests/test_publish_build.py` guards the
same rules in `check.py`: no local URLs, no URL that needs escaping, nothing
referenced that git doesn't track.

## The payload

| | Files | Size |
|---|---|---|
| Art on the table's objects (`ASSET_MAP` in `build_save.py`) | 87 | 35.9 MB |
| Art the scripts swap in at setup (the 15 board variants in `BOARD_ART_URLS`, `lua/assets.lua`) | 15 | 7.4 MB |
| Sound (`sounds/`, all of it) | 64 | 4.5 MB |
| **Total** | **166** | **47.8 MB** |

A player fetches only the board variant their setup picks, so a first load is a
little under the total, and TTS keeps its own copy after that. `art/` on disk is
much larger — card illustrations, ComfyUI renders and the hand-drawn originals
are build *inputs* the save never references; GitHub serves them too, but no
player ever asks for them.

Unused assets were removed in 2026-09 (boss art with no card, the board scenes
and stat icons nothing loaded, 13 day tracks the game never picked, the Bearger
sounds). Keep it that way: an asset nothing references still costs a reader's
attention, and one the game references must be committed.

Everything is inside TTS's stated limits: no image exceeds 4096×4096 (largest
is `art/decks/threat_face.jpg` at 3264×4095), all art is PNG/JPG in RGB, and all
audio is `.ogg`/`.wav`, both of which the Music Player supports. Largest single
file is 2.02 MB. Keep new filenames to `[A-Za-z0-9-._~]` — a test rejects any
URL a host would need to escape.

## Why GitHub, and the fallback

| Option | Verdict |
|---|---|
| **GitHub raw, pinned to a tag** | **Chosen.** No second service or upload step — the files are already here — and tags give immutable, versioned URLs for free. |
| **jsDelivr** (`https://cdn.jsdelivr.net/gh/<owner>/<repo>@<tag>`) | **The fallback.** A free CDN in front of the same public repo and tag. |
| **Cloudflare R2** | Needs an account, an upload per release, and — for real use — a custom domain on Cloudflare: its docs say the free `r2.dev` URL "is rate-limited and should only be used for development purposes". |
| **TTS Steam Cloud** | Durable and free, but every file gets an opaque `steamusercontent.com` hash, so the build can't generate URLs — 166 hand-copied links per release. The Cloud Manager's *Upload All* rewrites the links on objects, not the URLs inside the Lua bundle, which is where the board variants and all the audio live. |
| **GitHub Pages** | Serves only the latest deploy, so no per-release URLs without hand-kept version folders. |
| **Imgur / random image hosts** | The classic dead-TTS-mod cause. No. |

**The one risk:** since May 2025 GitHub rate-limits anonymous downloads from
`raw.githubusercontent.com`, and publishes no number for it. Measured
2026-09-25: the full asset set (186 files, before the cleanup) fetched twice
back-to-back from one machine — every request 200, 68 s cold and 9 s warm.
That covers a table of players; it doesn't prove a LAN party of first-time
players behind one IP. If players ever report missing art, switch to jsDelivr —
the same tag, so nothing moves: build with
`python scripts/build_save.py --publish https://cdn.jsdelivr.net/gh/JamesFlames/StarveNoMore@<tag>`
and `Update Workshop`. (jsDelivr served all 186 too, but slowly the first time:
it pulls each file from GitHub on first request.)

**What must never happen**, because every published copy breaks at once: the
repo going private, renamed or deleted; a released tag deleted or moved; assets
moved into Git LFS (raw serves an LFS file as its small pointer text, not the
content).

## The work

### Phase B — verify the publish save

- **B1.** `python scripts/publish.py <tag> --install` — see *Releasing*.
- **B2. Play it on a clean machine** — not yours. The whole point is proving no
  local path leaked. Ideally a machine that has never run `serve_art.bat`, with
  TTS's mod cache cleared, so a stale cached copy can't mask a broken URL.
  A full 7-day game: every board variant, every scenario, at least one boss
  (audio only loads when a boss arrives), the Rulebook, the achievements panel.
- **B3. Time the cold load** and write the number into the Workshop description.
  ~48 MB over a domestic NZ connection is not instant, and players blame the
  mod, not their line, when a table sits half-drawn.

### Phase C — the Workshop item

Done from inside TTS: load `StarveNoMore Workshop <tag>` (do **not** click
Setup Game — the upload captures the table exactly as it is), then
`Upload → Workshop Upload`.

- **C1. Thumbnail.** Mandatory — the upload fails without one. `saves/StarveNoMore.png`
  (895 KB, square, Coco's standee) is already the right shape; TTS normalises
  cached Workshop thumbnails to 256×256, so check it reads at that size.
- **C2. Description.** Gameplay, player count, rules pointer, credits (Klei for
  the audio — R1), the cold-load time from B3. `PlayerRules.md` is the source
  to crib from.
- **C3. Tags and player count.** 3–5 players (plus the solo toggle),
  co-op/board game type. The docs are explicit: tick only what applies.
- **C4. Upload hidden first** — that's TTS's default — verify by subscribing
  from a second account, *then* flip to public. You get a 9-digit Workshop ID
  back.
- **C5. Record the ID and the released tag** in `README.md` so future updates
  go to the same item via `Update Workshop` rather than creating a duplicate.
- **C6. Updating.** Commit and push the change, cut the next tag (`v1.1`), run
  `publish.py v1.1 --install`, load it, and `Upload → Workshop Upload → Update
  Workshop` with the item's ID. Every release gets a new tag — even a Lua-only
  change — so the save and its assets always come from one commit.

### Phase R — before you press upload

- **R1. Audio provenance — settled (2026-09).** The day tracks and the
  creature clips in `sounds/` are Klei assets from *Don't Starve*
  (`dontstarve_dlc003_…`, `suburbs_fall_day_amb_dsh`, `deerclops_*`, the
  Treeguard's `Leif_*`, the Eye of Terror's `Tentacle_*`). Klei was emailed
  about this use and raised no objection, so the audio stays. Keep that email
  as the record, and credit Klei for the audio in the Workshop description and
  `CREDITS.md` (R3). The synthesized SFX (`scripts/generate_hit_sfx.py`, the
  drones, the chime) are this repo's own.
- **R2. Names and likenesses.** Deerclops, Treeguard, Charlie and the Eye of
  Terror are Klei's creatures, and the boss art depicts them. The R1 email was
  about the audio; decide whether it covers these too, or ask the same
  question about names and art. Also worth a thought: the characters are
  named after real people — fine, but it's a public item now.
- **R3. Credits and licence.** Add a `CREDITS.md` (art provenance, including
  which pieces are ComfyUI-generated, audio sources, the DST/Hogwarts
  Battle/Catan/Cthulhu Wars design debts already noted in `README.md`) and a
  `LICENSE` for the code. The repo currently has neither — and since the repo
  is now public *and* the asset host, the licence also answers "may I reuse
  this art?".

## Things that are *not* in scope, and why

- **Steam achievements stay impossible.** A Workshop mod has no appid and no
  Steamworks surface; `steam/achievements.json` is a manifest for a future
  standalone app, nothing more. See [`docs/achievements.md`](achievements.md).
  The in-game 24 keep working exactly as they do now — including the caveat
  that a fresh load from the Workshop starts the vault empty (Save & Play keeps
  it; the *Copy my code* button is the migration path). Say so in the
  description or you'll get bug reports.
- **`PlayerRules.html` does not need hosting.** Nothing in the save links to it
  — the whole rulebook is in-game via `lua/ui_help_pages.lua`.
- **No DLC dependency.** The mod uses only base TTS features, so anyone who
  owns Tabletop Simulator can subscribe.

## Order of play

Hosting is done (GitHub, via `publish.py`) and R1 is settled. Next: decide R2,
write R3, cut the first tag and run B1–B3, then Phase C.
