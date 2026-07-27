# TTS physical contract — heights, sizes, rotations

Hard-won facts about how Tabletop Simulator lays objects out in the world:
heights, mesh sizes, rotations, where things can and cannot sit. **Read this
before placing or rotating anything.** Every rule was learned from a live
failure; the linked guards keep the fixed ones fixed.

For the API side — the Lua surface, the XML UI, object handles, and how to
measure a running game — see **[tts-interface.md](tts-interface.md)**.

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
  "Exactly" means derived from the piece's own thickness, not padded: a
  locked tile authored a tenth of a unit high hangs there for the whole
  game and reads as floating from a seated camera. `SURFACE_Y` already
  *is* `TABLE_SURFACE_Y + half a 0.1-thick tile`, so a flat tile goes at
  `SURFACE_Y`, with nothing added — and give the tile `Thickness: 0.1` so
  that arithmetic stays true. Guard:
  `test_locked_table_level_tiles_rest_on_the_table_rather_than_hover`.
- `DOOM_MARKER_Y` (setup.lua) mirrors the doom marker's build height —
  a test guards the mirror (`test_cross_refs.py`).
- Deliberately **under the table** (y ≈ −2.5, `LIBRARY_Y`): decks,
  supply bags, bench — players never see them; scripts reach them by tag.
- Guard: `test_build_output.py::test_no_objects_embedded_in_tabletop`
  fails the build if anything spawns in the dead band. Check a *live*
  session with `python scripts/inspect_save.py --live --band`.

### Mesh extents ≠ 1, and bounds ≠ artwork

Two separate traps, both of which cost a full session.

**A TTS primitive's mesh is not 1 unit per scale.** World size =
`mesh_extent × Transform scale`, so a scale that "looks right" as a world
size is off by the mesh factor. A `Custom_Tile` is **1.98 world units per
unit of scale** (measured: the 2.5-scale location tiles report 4.95).
Authoring the board at scale 12 on the assumption of local −1..+1 painted
its art across **±110 world units** while every object sat inside ±12 —
every piece in a heap in the middle, printed rings far outside them.
Nothing was misplaced; *the board was*.

**`Custom_Board` frames your image in a brown border that cannot be
removed.** Its bounds therefore describe the FRAME while the art covers only
the inner area, so every printed feature sits pulled toward the centre
relative to physical pieces — worst at the corners. This is unfixable by
tuning numbers, and it is invisible to `getBoundsNormalized()`, which
happily reports the frame. **Use a `Custom_Tile` for a board-sized surface**
(the documented workaround); the image then fills it exactly.

- [`scripts/board_geometry.py`](../scripts/board_geometry.py) keeps the
  three numbers separate and derives the scale: `BOARD_WORLD_HALF` (the
  world square the art is authored across) / `BOARD_MESH_HALF` (measured) /
  `BOARD_TRANSFORM_SCALE` (= world / mesh). Snap points convert with
  `world_to_local()` — divide by the **transform scale**, not the world
  half-extent.
- Heights derive from the board tile's own thickness
  (`BOARD_SURFACE_Y`, `BOARD_PIECE_Y` in `build_save.py`) rather than a
  guessed constant, so they can't rot when the board changes.
- Guards: `test_board_art_spans_the_world_square_the_pieces_live_in`,
  `test_board_snap_points_round_trip_to_world_coordinates`,
  `test_board_pieces_sit_above_the_board_surface`, plus
  `auditBoardGeometry()` at load.
- **Re-measure, don't re-guess** — and be aware of what you're measuring:
  `getBoundsNormalized().size` reports the collider, which may include
  decoration the artwork does not.

**A `Custom_Tile`'s `Thickness` is multiplied by `scaleY`, not by the XZ
scale.** `BOARD_WORLD_THICKNESS` used to multiply by `BOARD_TRANSFORM_SCALE`
(12.12), overstating the board's thickness twelvefold. `BOARD_SURFACE_Y` — the
"top of the board" every on-board piece is authored against — therefore sat
0.13 above the board's actual face, and the location tiles, Doom marker and
Day Counter all hung in the air.

The observation that settled it is worth copying, because it isolates a single
factor with no instrumentation at all: *"almost everything is levitating above
the board, apart from the quickstart note."* The Quick Start sits on the
**felt** via `SURFACE_Y`, which never had the bogus factor; everything on the
**board** went through `BOARD_SURFACE_Y`, which did. One constant, exactly that
split. When a height bug hits some objects and not others, sort them by which
surface constant they were authored against before touching any numbers.

`auditObjectFootprints` now reports `thick / bottom / top / gapOverBoard` per
probe, so the next height question is answered from the Message Log instead of
from a screenshot.

### Hiding things under the table

- Anything parked below the table (decks, supply bags, benched boards)
  only *reads* as hidden while something opaque is over it. Keep it inside
  the board footprint (±`BOARD_WORLD_HALF`) and use an **opaque table** —
  `Table_Glass` shows the entire library through the top.
- Valid TTS tables: `Table_Circular`, `Table_Custom`, `Table_Glass`,
  `Table_Hexagon`, `Table_None`, `Table_Octagon`, `Table_Plastic`,
  `Table_Poker`, `Table_RPG`, `Table_Square` (read out of the game's own
  `resources.assets`). There is **no** "Kraken" table. `Table_RPG` is the
  large opaque one.
- Guards: `test_under_table_objects_stay_within_the_board_footprint`,
  `test_the_table_is_not_see_through`.

### Rotations (two conventions, don't mix them)

- **Flat art objects** (Custom_Tile, Custom_Board, cards/decks): at
  `rotY=0` TTS renders the image rotated 180° in the default view. So
  either the object carries `ry=180` (tiles, cards) **or** its PNG is
  pre-rotated 180° by the generator (main board, player boards, tokens —
  see `board_geometry.py`'s docstring for the pixel↔world mapping).
  Do **both** and they cancel into a 180° error: the main board shipped
  with `ry=180` on top of its pre-rotated PNG and the whole printed map
  turned about its centre — the DAY COUNTER frame ended up opposite the
  gadget, every location ring opposite its tile.
- **Anything carrying AttachedSnapPoints must stay at `rotY=0`.** Snaps are
  object-LOCAL, so the object's rotation moves them too, while the pieces
  they line up with are authored in absolute world coordinates. A board at
  `ry=180` negates all 31 doom snaps and every `Snap:Location:*`. Rotate the
  image, never the board. Guard:
  `test_board_snap_points_round_trip_to_world_coordinates`.
- **Gadgets with engine-rendered text** (Counter, Notecard, 3DText): text
  reads correctly at `ry=0`. The Quick Start notecard was upside down for
  weeks because it carried the card convention.
- Flat 3DText labels: `rx=90, ry=0`.
- `rotZ=180` = face-down (cards); rotY is yaw, rotZ is flip.

#### Diagnosing "everything is 180° out"

A player reports the pieces and the printed art disagree. Which one moved?
**The art. Every time.** Work it out from the chain, not from the screenshot:

- An object's position in the save is a **literal world coordinate**. There
  is no engine transform between what you wrote and where it sits.
- A board image's orientation goes through several engine-dependent steps
  (the flat-art convention, the object's own `rotY`, the generator's
  pre-rotation). It is the only link in the chain that can be wrong.

So when the two disagree, fix the art — do not "correct" the object
positions to match a mis-rendered board, which re-breaks every piece placed
correctly against `path_layouts.LOCATION_WORLD`.

**Do not try to reason from the camera in a screenshot.** The player can
orbit anywhere, and a rotated camera flips the pieces and the art *together*,
which makes a genuinely-wrong board look right. What is camera-invariant is
the **relationship** between a printed feature and the object that belongs on
it. Pick a pair with one printed half and one physical half and compare only
those: the DAY COUNTER frame vs. the Day Counter gadget, a location ring vs.
its tile, doom cell 0 vs. the Doom marker. Both halves are authored from the
same constant (`DAY_COUNTER_WORLD`, `LOCATION_WORLD`, `doom_step_world`), so
if they are not on top of each other, the art is off — regardless of where
either one appears on screen.

Confirm off-table in one command before touching anything:

```bash
python scripts/inspect_save.py --live --objects
```

If the Day Counter reads `pos (-8.00, 1.73, 8.00)` and the location tiles
read their `LOCATION_WORLD` values, the pieces are fine by definition and the
board's `rotY` / PNG pre-rotation is the bug.

### Hand zones are a hard boundary, and they don't obey the mesh rule

A `HandTrigger` is the one placement constraint that isn't visible in any
screenshot, so it gets forgotten until cards start disappearing.

- **Its Transform scale IS its world size** — 1 unit per unit, *not* the
  1.98 factor a `Custom_Tile` uses. The zones here are
  `sx=HAND_ZONE_LEN(14), sy=6, sz=HAND_ZONE_DEPTH(6)` at `x=±22`, so each
  one occupies a 6-deep slab and its inner face — `HAND_ZONE_INNER`, 19.0 —
  is the line that matters.
- **Anything unlocked that crosses that line joins a private hand.** A card
  meant to lie face up where the table can read it must stay outside it;
  "beside the player board, pushed outward" is only safe while the board
  itself is inside the line. `dealStartingHands` pushes items 3.2 outward
  from a board whose own outer edge is already at the line, so its cards
  land inside the owner's zone — reasoned from the geometry, not yet
  observed at the table; check it when you next play.
- Locked objects should be immune (they can't be picked up at all, so
  nothing can put them in a hand) — but that is inference, not a
  measurement, so don't lean on it: keep them inside the line anyway.
- **Seats are derived from the zones**, so moving a zone moves that player's
  camera. Prefer moving the furniture, not the zone.
- Guard: `test_player_boards_are_square_to_the_board_and_face_it` measures
  both edges out of the built save — the market column on one side, the hand
  zone on the other.

### The table's space budget

The west flank is full. Anything new on it displaces something else, and the
arithmetic is not obvious from looking at the table, so it is written down
here rather than re-derived (which has cost a session):

| From the centre outward (west) | x, near edge → far edge |
|---|---|
| Printed map (`BOARD_WORLD_HALF`) | → −12.0 |
| Market slot frame (card inside it: −12.30 → −14.60) | −12.20 → −14.70 |
| *gangway* | *0.72* |
| Player board (turned 90°, so only 3.56 across) | −15.42 → −18.98 |
| Hand zone (`HAND_ZONE_INNER` → outer) | −19.0 → −25.0 |

Two consequences to check before adding anything to a flank:

- **The player boards are already at their outer limit.** They sit hard
  against the hand zone, so a wider Market column cannot be paid for by
  pushing them further out. `build_save.py` asserts this at build time.
- **You cannot buy space by sliding a column along z instead.** Five
  3.7-long market slots need 18.5 units, and the two player boards at z=±4
  chop the ~29-unit flank into bands of 7.9 / 2.9 / 7.9 — four slots fit,
  never five.

North is clear of furniture but the felt runs out there; south holds Coco's
board at z=−14.3. Every number above is derived in `build_save.py`, so read
the constants rather than copying these figures.

### Placement misc

- Cards are ~2.3 × 3.2 world units (`MARKET_CARD_W` / `_L`); slots closer
  than ~3.6 shove each other on deal. Size a slot marker from the card, not
  by eye — a **TTS `Notecard` is much larger than a card**, which is how the
  five market slot markers ended up lying across the printed map.
- Code that matches a card to a slot does it by distance
  (`_slotOccupied`, `doCraft`, `_spawnCraftButtons` all use ~2 units), so
  slot centres must stay well over 4 apart or a card answers for its
  neighbour.
- A card smooth-moved onto another card **merges into a deck** and
  destroys both handles (see callback rule below). Discard-then-reveal
  flows must teleport (`setPosition`) the old card away, not glide it.
- 3D `createButton` positions are object-local and multiplied by the
  object's scale (see the mesh-extent note above before picking one).
- Locked objects don't smooth-move reliably: unlock → move → re-lock
  (see `moveDoomMarker`).

## Asset caching

TTS caches every `file:///` and `localhost` asset forever, so regenerated
art can silently keep showing the old version. `iwanttoplay` purges this
mod's entries on every deploy — details in
[tts-interface.md](tts-interface.md#deploying).

**Do not reach for the cache to explain misalignment.** Two sessions were
lost blaming it for pieces that were actually mis-scaled or mis-parented. If
the art is the *wrong picture*, suspect the cache. If things are the wrong
**size or place**, measure.
