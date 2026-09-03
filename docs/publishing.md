# Publishing to the Steam Workshop

How *Starve No More* gets from this repo to a Tabletop Simulator Workshop item:
where the assets have to live, what already works, and what still has to be
built. Measured against the current tree, not guessed.

*Part of the [agent reference](agents/README.md); the index lives in [`agents.md`](../agents.md).*

## The short answer on hosting

**Steam does not host your images and audio for you as a side effect of
publishing a mod.** A TTS Workshop item is only the save JSON — the Lua bundle,
the XML UI and `ObjectStates`. Every image and sound inside it is a **URL**, and
TTS fetches those URLs on the player's machine when the mod loads. Publish with
`file:///C:/Users/GGPC/...` in there (which is exactly what
`saves/StarveNoMore.json` contains today) and every other player gets a table of
grey rectangles and total silence.

Steam does give you somewhere to put them: the **TTS Cloud Manager**
(`Upload → Cloud Manager`) is 100 GB of Steam Cloud tied to your Steam account,
free, and the official docs say files uploaded through it "persist
indefinitely". Third-party hosts also work — TTS takes any URL — but the same
docs warn that third parties "may have rules or restrictions that prevent your
assets from being shared correctly or being hosted indefinitely".

So: assets must be hosted somewhere with a stable public URL *before* the
Workshop upload, and the save must be built pointing at that host.

## What already exists

Most of the plumbing is done. `scripts/build_save.py` has a publish mode:

```bash
python scripts/build_save.py --publish https://your.host/starvenomore
# → saves/StarveNoMore.publish.json
```

It rewrites **172 asset URLs** — 87 art files, 84 sounds, plus the `_BASE`
literal in `lua/assets.lua` — from `file:///` and `http://localhost:8080` to
`<base>/art/...` and `<base>/sounds/...`, writes a *separate* save so the dev
files stay byte-stable, and hard-fails if any local URL survives.
`tests/test_publish_build.py` proves both halves end-to-end and runs in
`python scripts/check.py`.

Verified working on the current tree: 172 URLs rewritten, zero `file:///`,
zero `localhost`, committed dev saves untouched.

What that means: **the build side of publishing is not the work.** The work is
picking a host, getting 171 files onto it, and everything in "Before you press
upload" below.

## The payload

| | Files | Size |
|---|---|---|
| Art (`art/`, referenced by the save) | 87 | 35.9 MB |
| Sound (`sounds/`, all of it) | 84 | 18.8 MB |
| **Total a first-time player downloads** | **171** | **54.7 MB** |

`art/` on disk is 274 MB; only 35.9 MB of it is actually reachable from the
save (the rest is sources, variants and ComfyUI output). **Upload the
referenced set, not the folder** — see task H1.

Everything is already inside TTS's stated limits: no image exceeds 4096×4096
(largest is `art/decks/threat_face.jpg` at 3264×4095), all art is PNG/JPG in
RGB, and all audio is `.ogg`/`.wav`, both of which the Music Player supports.
Largest single file is 2.02 MB. Nothing needs re-encoding to be legal — though
task H1 is worth doing anyway for load time.

## Decision: where to host

| Option | Cost (NZD) | Stable paths? | Verdict |
|---|---|---|---|
| **TTS Steam Cloud** | $0, 100 GB, permanent | ✗ — each upload returns an opaque `steamusercontent.com` hash | Durable and free, but 171 hand-copied URLs and the build stops being reproducible |
| **Cloudflare R2** | $0 (free tier: 10 GB storage, **zero egress**) | ✓ — you choose the paths | **Recommended** |
| **GitHub Pages** | $0 | ✓ | Works, but Pages is documented as a site host, not an asset CDN; a soft-limit warning on a published mod is a bad day |
| **Imgur / random image hosts** | $0 | ✗ | The classic dead-TTS-mod cause. No. |

R2 free tier is 10 GB-month of storage with no egress charge, against a 54.7 MB
payload — this mod costs **NZD $0.00/month** and would stay free past ~180×
its current size. Even paid, R2 Standard is US$0.015/GB-month ≈ **NZD
$0.025/GB-month** (at ~1.69 NZD/USD, Sept 2026), so the whole mod is about
**NZD $0.0014/month** if the free tier ever vanished. A custom domain is
optional (~NZD $20–30/yr); the default `r2.dev` or a Workers route is fine.

Why not Steam Cloud as primary, despite being the "official" answer: its URLs
are unguessable per-file hashes, so `--publish <base>` cannot generate them.
You would need a checked-in `asset_name → steamusercontent URL` map, 171
manual copy-pastes to populate it, and another round every time art
regenerates. That trades this repo's whole "rebuild it from source in 22
seconds" property for a saved NZD $0.00. The Cloud Manager's **Upload All**
button doesn't rescue this either — it only migrates files TTS has *currently
loaded*, and this mod loads board variants, scenario art and boss audio lazily,
so a single pass would miss most of the payload.

**Recommendation: Cloudflare R2 as the live host, Steam Cloud as a belt-and-braces
mirror later if you ever want it (task R4).**

## The work

### Phase H — host the assets

- **H1. Build a publish asset bundle.** New `scripts/collect_publish_assets.py`:
  parse the same `ASSET_MAP` + `lua/assets.lua` the build uses, copy exactly the
  referenced 171 files into `dist/publish/{art,sounds}/`, and fail loudly on a
  referenced file that doesn't exist. Prevents shipping 274 MB and prevents a
  silent missing-asset hole. Roughly a two-hour job.
- **H2. ~~Fix the one filename that will break on a real host.~~ DONE.**
  `sounds/ambient/varied/battlegrounds fall night_ds_amb.ogg` had a space in
  it and the publish build emitted it raw. Renamed to underscores;
  `test_publish_build.py::test_publish_urls_need_no_escaping` now asserts
  every asset URL is RFC 3986 unreserved characters plus `/` and `:`, so the
  next one fails in `check.py` rather than in the Workshop. Keep new asset
  filenames to `[A-Za-z0-9-._~]`.
- **H3. Stand up the bucket.** Cloudflare account → R2 bucket `starvenomore` →
  public access (r2.dev subdomain or a Workers route) → upload
  `dist/publish/` preserving the `art/` and `sounds/` prefixes (`rclone` or
  `wrangler r2 object put`). Note the base URL.
- **H4. Set cache headers.** Long `Cache-Control` (these files are immutable in
  practice) so repeat loads are cheap. TTS's own Mod Caching already keeps
  downloaded assets locally between sessions, so this mostly helps first loads.
- **H5. Smoke-test the URLs.** Script it: `HEAD` all 171, assert 200 and a
  sane `Content-Type`. A 403 on one board variant is invisible until the one
  player who picks that scenario complains.

### Phase B — build and verify the publish save

- **B1.** `python scripts/build_save.py --publish https://<r2-base>` →
  `saves/StarveNoMore.publish.json`.
- **B2. Play it on a clean machine** — not yours. The whole point is proving no
  local path leaked. Ideally a machine that has never run `serve_art.bat`, with
  TTS's mod cache cleared, so a stale cached copy can't mask a broken URL.
  A full 7-day game: every board variant, every scenario, at least one boss
  (audio only loads when a boss arrives), the Rulebook, the achievements panel.
- **B3. Time the cold load** and write the number into the Workshop description.
  55 MB over a domestic NZ connection is not instant and players blame the mod,
  not their line, when a table sits half-drawn.
- **B4. Wire it into `check.py`** or a `scripts/publish.py` one-shot that does
  H1 → B1 → H5 in order, so releasing is one command like everything else here.

### Phase C — the Workshop item

Done from inside TTS: load `StarveNoMore.publish.json`, then
`Upload → Workshop Upload`.

- **C1. Thumbnail.** Mandatory — the upload fails without one. `saves/StarveNoMore.png`
  (895 KB, square, Coco's standee) is already the right shape; TTS normalises
  cached Workshop thumbnails to 256×256, so check it reads at that size.
- **C2. Description.** Gameplay, player count, rules pointer, credits, the
  cold-load warning from B3. `PlayerRules.md` is the source to crib from.
- **C3. Tags and player count.** 3–5 players (plus the solo toggle),
  co-op/board game type. The docs are explicit: tick only what applies.
- **C4. Upload hidden first** — that's TTS's default — verify by subscribing
  from a second account, *then* flip to public. You get a 9-digit Workshop ID
  back; record it in the repo.
- **C5. Record the ID and the base URL** in `README.md` so future updates go to
  the same item via `Update Workshop` rather than creating a duplicate.

### Phase R — before you press upload (do these first)

- **R1. Audio provenance — the real blocker.** `sounds/` is full of files named
  `dontstarve_dlc003_amb_temperate_interior_city_day.ogg`,
  `hamlet_amb_cave_st_lp.ogg`, `bearger_*`, `deerclops_*`. Those are Klei
  assets from *Don't Starve*. A private table is one thing; a public Workshop
  item redistributing another studio's audio is a DMCA target and a real risk
  of losing the item. Klei is famously relaxed about fan work, but "relaxed"
  is not a licence. Decide deliberately:
  (a) ask Klei for written permission, (b) replace the ripped tracks with
  CC0/CC-BY audio (freesound.org, Kenney) or generated ambience — the manifest
  is auto-generated, so swapping files is cheap, or (c) publish
  friends-only/unlisted and skip the question. The synthesized SFX
  (`scripts/generate_hit_sfx.py`, the drones, the chime) are already yours and
  are not affected.
- **R2. Names and likenesses.** Bearger, Deerclops, Treeguard and Charlie are
  Klei's creature names; the same call as R1 applies to text and art, and
  renaming is cheaper than re-recording. Also worth a thought: the characters
  are named after real people — fine, but it's a public item now.
- **R3. Credits and licence.** Add a `CREDITS.md` (art provenance, including
  which pieces are ComfyUI-generated, audio sources, the DST/Hogwarts
  Battle/Catan/Cthulhu Wars design debts already noted in `README.md`) and a
  `LICENSE` for the code. The repo currently has neither.
- **R4. Optional durability mirror.** Once live and stable, also push the 171
  files through the TTS Cloud Manager and keep the URL map in
  `content/cloud_urls.json`. Costs nothing, and if R2 ever goes away you can
  rebuild against Steam Cloud without re-uploading under pressure.

## Things that are *not* in scope, and why

- **Steam achievements stay impossible.** A Workshop mod has no appid and no
  Steamworks surface; `steam/achievements.json` is a manifest for a future
  standalone app, nothing more. See [`docs/achievements.md`](achievements.md).
  The in-game 24 keep working exactly as they do now — including the caveat
  that a fresh load from the Workshop starts the vault empty (Save & Play keeps
  it; the *Copy my code* button is the migration path). Say so in the
  description or you'll get bug reports.
- **`PlayerRules.html` does not need hosting.** Nothing in the save links to it
  — the whole rulebook is in-game via `lua/ui_help_pages.lua`. The docstring in
  `build_save.py` that says to upload it is stale.
- **No DLC dependency.** The mod uses only base TTS features, so anyone who
  owns Tabletop Simulator can subscribe.

## Order of play

R1 first — it's the only item that can invalidate everything downstream.
Then H1, H3–H5, B1–B4, R3, then Phase C. (H2 is already done.)
