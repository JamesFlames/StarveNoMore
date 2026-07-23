# TTS runtime contract — physical world + API gotchas

Hard-won facts about how Tabletop Simulator actually behaves. **Read this
before placing objects, rotating anything, changing lighting/audio, or
writing takeObject callbacks.** Every rule here was learned from a live
failure; the linked guards keep the fixed ones fixed.

## The physical world

### Heights (the #1 invisible-object trap)

- The glass table's **playing surface is at world y ≈ 1.55**, and the main
  board's top surface is roughly flush with it. Both constants live in
  `build_save.py` (`TABLE_SURFACE_Y` / `SURFACE_Y`) — author every
  surface-level spawn through them.
- An object authored at `0 < y < 1.55` starts **inside the tabletop**:
  locked → invisible forever; unlocked → falls through the glass table's
  broken partial-hull collider and rests ~0.8 under the surface ("the
  player boards were invisible until I picked them up").
  Unity even logs the broken collider at TTS start:
  `Couldn't create a Convex Mesh ... glas_table_top_bottom`.
- Objects dropped from **above** the surface land reliably; the collider
  only bites objects that *start* inside it. So: spawn high, let physics
  settle. Locked objects don't settle — author their resting y exactly.
- `DOOM_MARKER_Y` (setup.lua) mirrors the doom marker's build height —
  a test guards the mirror (`test_cross_refs.py`).
- Deliberately **under the table** (y ≈ −2.5, `LIBRARY_Y`): decks,
  supply bags, bench — players never see them; scripts reach them by tag.
- Guard: `test_build_output.py::test_no_objects_embedded_in_tabletop`
  fails the build if anything spawns in the dead band. Check a *live*
  session with `python scripts/inspect_save.py --live --band`.

### Rotations (two conventions, don't mix them)

- **Flat art objects** (Custom_Tile, Custom_Board, cards/decks): at
  `rotY=0` TTS renders the image rotated 180° in the default view. So
  either the object carries `ry=180` (tiles, cards) **or** its PNG is
  pre-rotated 180° by the generator (main board, player boards, tokens —
  see `board_geometry.py`'s docstring for the pixel↔world mapping).
- **Gadgets with engine-rendered text** (Counter, Notecard, 3DText): text
  reads correctly at `ry=0`. The Quick Start notecard was upside down for
  weeks because it carried the card convention.
- Flat 3DText labels: `rx=90, ry=0`.
- `rotZ=180` = face-down (cards); rotY is yaw, rotZ is flip.

### Placement misc

- Cards are ~2.3 × 3.2 world units; slots closer than ~3.6 shove each
  other on deal.
- A card smooth-moved onto another card **merges into a deck** and
  destroys both handles (see callback rule below). Discard-then-reveal
  flows must teleport (`setPosition`) the old card away, not glide it.
- 3D `createButton` positions are object-local and multiplied by the
  object's scale (main board scale 12: local 0.75 y ≈ world 1.71).
- Locked objects don't smooth-move reliably: unlock → move → re-lock
  (see `moveDoomMarker`).

## Lua API gotchas

- **Lighting**: runtime API is `Lighting.light_intensity`,
  `Lighting.ambient_intensity`, `Lighting.setAmbientSkyColor{...}` — then
  **`Lighting.apply()`** or nothing changes. The PascalCase names
  (`LightIntensity`…) exist only in the save JSON; at runtime they throw
  `cannot access field LightIntensity of userdata<LuaLighting>`.
- **Dead object handles**: a `takeObject` callback can receive a handle
  whose object was already destroyed (merged into a deck mid-flight).
  *Any* field access then throws `cannot access field getNickname of
  userdata<LuaObject>`. Wrap callback bodies in `pcall`/`safecall` and
  recover by re-finding the object by tag (see `revealDawnCard`,
  day_loop.lua).
- **`UI.setAttribute(id, "text", ...)` on a Button resets its styling** —
  the label reverts to near-black. Re-assert `textColor` (and `color`)
  after every text change (see `refreshDuskReadyLabel`).
- **`<ProgressBar>`: `fillImageColor` is the fill; `color` is the empty
  track.** The fill defaults to white, so a bar with only `color="#FF4444"`
  set shows WHITE when full and red as it drains — the opposite of what
  you usually want. For colored-full-draining-to-white, set
  `fillImageColor` to the stat colour and `color` to white. Lua that
  recolours a bar by state must set `fillImageColor`, not `color`.
- **Broadcasts render behind the Phase Banner and fade in seconds.**
  Player-facing information goes through `broadcastEvent` (which also
  feeds the persistent Message Log panel) or a dedicated panel — never a
  bare `broadcastToAll` for anything the player must be able to re-read.
- **One global MusicPlayer**: every SFX/roar interrupts the ambient track;
  `audio.lua` owns the resume machinery — route all audio through it.
- TTS XML colors: hex of length 3/4/6/8 only; `rgb()` components are
  0–1 floats (0–255 clamps to white). `test_xml_quality.py` guards this.
- Error lines are reported as `<Global:NNNN>` against the concatenated
  bundle — decode with `python scripts/inspect_save.py --error NNNN`.

## Asset caching (the "my fix didn't do anything" trap)

TTS caches every `file:///` and `localhost` asset under
`Documents\My Games\Tabletop Simulator\Mods\` **forever**. After
regenerating art or sounds, the game silently keeps showing the old
version — symptoms like "the printed frame and the object don't line up"
are usually a stale cached board image, not a geometry bug.
`iwanttoplay` purges this mod's cache entries on every deploy; the manual
equivalent is deleting `Mods` files whose names contain
`reposStarveNoMore` or `localhost8080`.
