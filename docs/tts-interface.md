# Interfacing with Tabletop Simulator

How this mod talks to TTS: the save format, the Lua API, the XML UI layer,
and how to get real numbers out of a running game. **Read this before
calling a TTS API you haven't used here before, or before debugging a
runtime error.**

Its sibling, [tts-runtime.md](tts-runtime.md), covers the *physical* side —
heights, mesh sizes, rotations, where objects can and can't sit.

## The shape of the integration

A TTS mod is **one JSON save file**. `scripts/build_save.py` assembles it:

| Save field | Comes from | Notes |
|---|---|---|
| `LuaScript` | every `lua/*.lua`, concatenated | ONE shared global namespace, no `require`; order is `scripts/load_order.json` |
| `XmlUI` | every `xml/*.xml`, concatenated | screen-space UI, not world objects |
| `ObjectStates` | built in Python from `content/*.csv` | positions, tags, snap points, custom images |
| `LuaScriptState` | written by TTS at runtime | our `gameState`, via `onSave` |

Two consequences worth internalising:

- **The Lua is one chunk.** A global defined twice means the later
  definition silently wins (`test_lua_statics.py` guards this), and a
  `local` at file scope is visible to every file loaded *after* it.
- **Errors are reported against the concatenated bundle**, not your file:
  `<Global:8845>`. Decode with `python scripts/inspect_save.py --error 8845`.

## Rule 1: only call API that actually exists

A method TTS doesn't have fails **only at runtime, and only on the code
path that reaches it**:

```
cannot access field setNotebookTabs of userdata<LuaNotes>
cannot access field LightIntensity of userdata<LuaLighting>
```

Both shipped. The Notebook one is the instructive case: the whole Notebook
was empty every game and **every test passed**, because `tests/tts_stub.lua`
had invented a `Notes.setNotebookTabs()` the real API lacks. When the model
is wrong in the same direction as the code, the suite confirms the bug
instead of catching it.

- The real Notes API is `addNotebookTab` / `editNotebookTab` /
  `getNotebookTabs` / `removeNotebookTab`. There is **no** `setNotebookTabs`.
- `Lighting` uses snake_case properties (`light_intensity`,
  `ambient_intensity`) plus setters — and then **`Lighting.apply()`** or
  nothing changes. The PascalCase names exist only in the save JSON.
- Guard: **`tests/test_tts_api_surface.py`** holds a curated allowlist of
  the singleton API and checks it from *both* sides — Lua may only **call**
  what's on it, and the stub may only **define** what's on it. Adding a
  method means adding it there, which is the moment to go and verify it.

> The allowlist is curated, not machine-derived. Searching the game binary
> for method names produces false positives (`Wait.time`, `UI.setAttribute`,
> `Lighting.apply` and `JSON.encode` are all real but absent from its string
> table). It is only as good as the check you do when you add a name.

### The mirror image: a stub *gap* hides coverage

A stub that invents an API gives you a false pass. A stub that's **missing**
one gives you no test at all — quieter, and easier to live with for months.
`tts_stub.lua`'s Vector had no `distance()`, so every code path that matches
an object to a position by distance (`doCraft`, `_spawnCraftButtons`) threw
`attempt to call method 'distance' (a nil value)` the moment a test touched
it. Nobody had: the entire Craft purchase path was untested, and it looked
like a deliberate omission rather than a wall.

When a test dies on a missing stub method, **that is the finding** — the
feature has no coverage. Add the method to `tts_stub.lua` (with a comment
saying which caller needs it) and write the test; never route around it by
testing a lower-level helper instead.

## Rule 2: an object handle has a lifetime

This is the most-repeated bug in the mod — pry, dawn reveal, threat reveal,
gather, the wrongness reveal. A handle can outlive its object (merged into a
deck mid-flight, destroyed by a player, stacked by physics); *any* field
access then throws `cannot access field getNickname of userdata<LuaObject>`
and takes the whole action down.

- **Read through the shared guards in `helpers.lua`:** `safeNickname(obj)`,
  `safeHasTag(obj, tag)`, `isLiveObject(obj)`. Never touch `obj.*` directly
  on a handle that came from a callback, a stored GUID, or a scan.
- **Filter at the source.** `findAllByTag` / `findOneByTag` skip dead
  handles, and `getPlayerCarriedObjects` pcall-guards `getPosition`. One
  stale handle used to make *every tag lookup in the mod* throw.
- **Re-finding the object is not enough.** `revealDawnCard` re-found the
  card and still died: after a merge, what sits on the reveal spot is a
  *deck*, not a card. Snapshot what you need **while the handle is known
  good** — `takeObject`'s return value is alive the instant it returns — and
  drive the rest off that snapshot (`_cardSnapshot`, day_loop.lua).
- **`reload()` destroys and respawns.** Swapping a custom image needs it, so
  capture snap points first and re-apply them to the fresh object
  (`applyPathVariant`, ui_actionbar_core.lua).
- **A deck that drops to ONE card stops being a deck.** TTS destroys the
  container and leaves that card loose where the deck was. The handle you are
  holding still passes `isLiveObject` — it is simply no longer a container —
  and `takeObject` on it throws. So the *last* card of any deck is never
  taken; find it (`getObjectFromGUID` on the guid you snapshotted) and place
  it (`dealStartingHands`, setup.lua). `tests/tts_stub.lua` models the
  collapse, so the suite sees this now; it did not before, and the bug below
  is what that blind spot cost.
- Guards: `tests/test_dead_handles.py` (a runtime sweep that drops a
  poisoned handle on the table and runs the real entry points over it, plus
  a static scan for unguarded dereferences) and
  `TestDawnRevealSurvivesDeadHandles`. Note the static scan tracks risky
  variable **names per file**, so reusing a name like `card` for a
  `getObjectFromGUID` result marks every other `card` in that file too.

## Rule 3: `pcall` does not catch everything

Lua `pcall` catches Lua errors. A TTS API can instead throw a **.NET
exception** — `Value cannot be null. Parameter name: key` is the one to
recognise, a C# dictionary indexed with null — and that unwinds the entire
call stack straight past every `pcall` and `safecall` in it.

It cost a live table a whole game. `dealStartingHands` called `takeObject` on
a collapsed deck (see above); the throw blew through the `safecall` around
that call, the `safecall` around `dealStartingHands`, *and* the
`pcall(runGuidedSetupFinalize)` whose entire job was to make setup failures
survivable. Nothing after it ran: no `gameState.started`, no HUD refresh, no
Host Controls. The table sat in PreGame with a full party and no button to
press, and the only way out was reloading the mod.

- **Do not rely on a wrapper for recovery.** Order the work so the cheap
  state is committed *before* anything touches an object, and schedule the
  recovery on a `Wait` callback as well — a Wait runs on a fresh stack and
  survives whatever happened to this one (`finalizeGuidedSetup`, ui_setup.lua).
- The tests cannot see this: `lupa` runs real Lua 5.2, where `pcall` catches
  everything the stub can throw. Only the running game raises it.

## Rule 4: TTS's Lua is MoonSharp's, not PUC Lua's

**This is the one class of bug the test suite structurally cannot catch.**
`tests/` runs the real bundle under real Lua 5.2 (lupa); the game runs
MoonSharp. Where they disagree, the suite is green and the game throws, and no
runtime test can help because the runtime under test is the wrong runtime. The
only defence is not writing the idiom, so both known cases have a helper in
`helpers.lua` and a static guard in `tests/test_moonsharp_safety.py`:

| Idiom | MoonSharp | Real Lua | Use |
|---|---|---|---|
| `s:match("^%s*(.-)%s*$")` | "pattern too complex" past ~200 chars | fine | `trim(s)` |
| `table.remove(t, 1)` on an empty `t` | "position out of bounds" | returns `nil` | `popFirst(t)` |

Both shipped and reached players. Both were found by reading an error in the
chat log. When a third turns up, add the helper and add it to that guard —
each entry is a bug that would otherwise only ever be found by a player.

### The pattern case in detail

TTS runs MoonSharp, whose pattern matcher gives up with **"pattern too
complex"** on an unbounded lazy capture once the subject passes a couple of
hundred characters. The standard Lua trim, `s:match("^%s*(.-)%s*$")`, is
exactly that shape.

The Help panel used one to detect headings and the rulebook has 400- and
600-character paragraphs, so pressing '?' threw before a single page
rendered — every tab, not just the Rulebook. Real Lua 5.x matches it happily,
so the suite was green the whole time. Trim with `find` + `sub` instead
(`trimLine`, ui_help_pages.lua). Anchored classes like `^%s*$` are fine; it is
`(.-)` spanning a long subject that breaks.

## The XML UI layer

- **`UI.setAttribute(id, "text", ...)` on a Button resets its styling.** The
  label reverts to near-black. Re-asserting the colour in a *second* call is
  a race. Use **`setButtonLabel(id, text, textColor, color)`** (helpers.lua),
  which sets text and colours in one `UI.setAttributes`.
- **Never hardcode a plate colour at runtime.** `setActionEnabled` did, which
  silently overwrote the XML palette and reintroduced dark-on-dark. Colours
  live in `BTN_DARK_PLATE` / `BTN_ON_DARK`. Guard:
  `test_action_buttons_do_not_hardcode_a_plate_colour`.
- **TTS dims a *disabled* button's text toward its plate.** On a dark plate
  the label disappears entirely. House rule: **light plate, dark text** —
  a dimmed dark label on a light plate still reads.
  `test_button_text_contrast` enforces contrast on static XML.
- **`<ProgressBar>`: `fillImageColor` is the fill; `color` is the empty
  track.** The fill defaults to white, so a bar with only `color="#FF4444"`
  shows WHITE when full and red as it drains — the opposite of what you
  want. Lua recolouring a bar by state must set `fillImageColor`.
- **Colours**: hex of length 3/4/6/8 only; `rgb()` components are 0–1 floats
  (0–255 clamps to white). `test_xml_quality.py` guards this.
- XML ids are indexed in [`SYMBOLS.md`](../SYMBOLS.md) → file:line + handler.

## Talking to players

- **Broadcasts render behind the Phase Banner and fade in seconds.** Anything
  the player must be able to re-read goes through `broadcastEvent` (which
  also feeds the persistent Message Log) or a dedicated panel — never a bare
  `broadcastToAll`.
- **The rule bites hardest on actions whose only product is information.**
  Peek read the top of the Threat deck correctly and handed the answer to
  `broadcastToColor`: the player spent a once-per-day free action and
  reported "nothing happened". Private *and* durable means a panel with
  per-player `visibility` (`peekResultPanel`, `whatNowPanel`) — the Message
  Log is durable but public.
- Note what a "does this function mention `broadcastEvent`?" scan would have
  said about Peek: **fine**. It called `broadcastEvent` for the public
  flavour line while the payload evaporated. The guard that works is
  behavioural — `tests/test_lua_durable_output.py` drives each information
  action with a sentinel card and looks for that sentinel in the durable
  channels. It also forces every new `do*` verb to be classified as
  information- or effect-producing, so the question gets asked once per action
  instead of never.
- **A `Notecard` renders one fixed-size page and clips the overflow** — no
  scrollbar, no ellipsis, no warning. The Quick Start card carried the full
  ~1900-character rules and cut off mid-word. Long text belongs in the
  Notebook tab or the `?` panel; the card gets a brief inside
  `QUICKSTART_CARD_BUDGET`. Guard: `TestQuickStartCardFits`.
- **One global MusicPlayer**: every SFX interrupts the ambient track;
  `audio.lua` owns the resume machinery, so route all audio through it.
- **Seat colour IS a character** in this game. TTS's own "Change Color"
  control therefore changes *which character you control* — not whose turn
  it is. Say that explicitly in any message that mentions it; the TTS label
  alone tells the player nothing.

## Getting real numbers out of a running game

Reasoning about TTS from the save file alone has been wrong more often than
right here. Measure instead:

- **`auditBoardGeometry()`** — the board's real world size vs. the square the
  art is authored across, and the corrected Transform scale. Silent when
  correct.
- **`auditObjectFootprints()`** — each key object's real size, and how far
  its rendered centre sits from its transform origin. Gated behind
  `MEASURE_FOOTPRINTS` in `lua/audit.lua`.

Both run at load and report into the Message Log, which the autosave
persists. Read them off disk with:

```bash
python scripts/inspect_save.py --live
```

> Lua `print()` does **not** reach Unity's `Player.log` — that file only
> carries engine output. The Message Log is the channel that survives to
> disk. (A whole debugging round was lost to that assumption.)

**Sample late.** A custom image is still downloading shortly after load, and
the object's bounds read differently until it lands. The geometry probe
samples at 1s and 12s and labels them `[early]` / `[late]`; trust the late
one. Two wrong Transform scales came from believing an early reading.

## Deploying

`iwanttoplay` = regenerate → build → full pytest gate → install save → purge
this mod's stale asset cache → asset server → launch TTS.
Flags: `--skip-tests`, `--no-launch`.

**Asset caching**: TTS caches every `file:///` and `localhost` asset under
`Documents\My Games\Tabletop Simulator\Mods\` forever, so regenerated art can
silently keep showing the old version. `iwanttoplay` purges this mod's
entries on every deploy.

> Don't reach for the cache as an explanation of misalignment. Two separate
> sessions were lost blaming it for pieces that were actually mis-scaled or
> mis-parented. If the *art is the wrong picture*, suspect the cache. If
> things are the wrong **size or place**, measure — see
> [tts-runtime.md](tts-runtime.md).

**The save's cover thumbnail must be square.** A PNG with the same basename
as the save is what the Save & Load browser shows for it, and the browser
fits that PNG to the **width** of a square tile. Our cover was 16:9 for a
while, so it covered a bit over half the tile's height and the rest showed
bare UI panel. `scripts/generate_cover.py` renders 1024×1024 now; keep it
1:1. (TTS normalises the Workshop thumbnails it caches under
`Mods/Workshop/` to exactly 256×256 — same square tile, and a handy way to
confirm this without launching the game.)
