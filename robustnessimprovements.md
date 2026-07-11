# Robustness & Structure Improvements

The best ways to make this project harder to break, ranked by how much pain
each one prevents. Legend: **[x] implemented** (in this pass or already in
place) · **[ ] recommended next** (listed so it isn't forgotten; each says
why it waited).

The governing convention (from agents.md) behind most of this list:
**"If a change requires remembering to update a second file, add the test
that remembers instead."**

## 1. Guard the failure modes TTS hides (all hit by real playtests)

TTS fails *silently* on bad UI input — the game keeps running and just looks
wrong. Every class of silent failure the table has already hit now has a test:

- [x] **UI colors must be TTS-parseable.** TTS reads `rgb()/rgba()` components
  as 0–1 floats; 0–255 values clamp to white, which once turned every "dark"
  panel white and made all pale text unreadable. `tests/test_xml_quality.py`
  validates every color in the XML **and** every color string literal in the
  Lua (`#hex` length 3/4/6/8, rgb components ≤ 1.0).
- [x] **XML well-formedness.** A malformed `global_ui.xml` makes the whole UI
  vanish with no error (`test_xml_quality.py::test_xml_well_formed`).
- [x] **No literal `\n` in XML.** Renders as the two characters "\n" on
  buttons — players saw exactly this on the setup walkthrough. Use `&#10;`
  (`test_xml_quality.py::test_no_literal_backslash_n`).
- [x] **`<Image image="X">` must resolve.** Names must have a
  `CustomUIAssets` entry in the built save and the asset file must exist
  under `art/` (`test_xml_quality.py::test_xml_image_assets_exist`).
- [x] **Dynamically-built UI ids must exist.** The XML↔Lua contract test only
  sees literal ids; the per-character ids Lua composes at runtime
  (`"card" .. name`, roster rows) are enumerated and checked
  (`test_xml_quality.py::test_per_character_dynamic_ui_ids_exist`).

## 2. Static analysis

- [x] **luacheck in the test suite.** `tests/test_lua_lint.py` runs
  `luacheck lua` against the generated `.luacheckrc` (all bundle globals
  declared, noise classes disabled — anything it reports is a real hazard,
  typically a typo'd global). Skips with a pointer when luacheck isn't
  installed; CI's dedicated `luacheck` job always runs it. A companion test
  asserts `.luacheckrc` still exists and is the generated file.
- [x] **ruff for Python** (`scripts/`, `tests/`) — already in CI.
- [ ] **Flip CI's luacheck job to hard-fail** (`continue-on-error: false`)
  after eyeballing one green run — it was left soft on purpose when added,
  and luacheck isn't installed on the dev machine to verify locally.

## 3. Mirror tests (constants that exist in two places)

- [x] **Standee slot offsets**: `CHAR_SLOT_X/Z` in `scripts/build_save.py`
  (initial placement baked into the save) must equal the slot math in
  `lua/helpers.lua getCharSlotPosition` (runtime placement) — drift means
  standees teleport on their first move
  (`test_cross_refs.py::test_char_slot_offsets_mirror_helpers`).
- [x] **`TOOLTIP_DATA` keys ↔ save tags**: every tooltip key must be a tag
  some object in the built save actually carries, or `applyTooltips()`
  silently does nothing (`test_cross_refs.py::test_tooltip_data_tags_exist_in_save`).
- [x] **Starting-hand decks ↔ CSV**: the save must contain one
  `StartingHand:<name>` deck per character with exactly the CSV's card count
  (`test_cross_refs.py::test_starting_hand_decks_in_save_match_csv`).
- [x] **`S_` joined the card-id universe**, so a starting-item id typo'd in
  Lua fails the hardcoded-id check like every other prefix
  (`conftest.CSV_FOR_PREFIX`, `test_cross_refs.CARD_ID_RE`).
- [x] Already in place before this pass, kept: Dawn card↔handler pairing,
  effect-flag↔Rules-panel labels, atlas grids, MARKET_COSTS coverage,
  sim↔lua constant mirrors, generated-file freshness, save-fixture migration.

## 4. Content as data, not code

- [x] **Starting hands are a CSV** (`content/cards_starting.csv`), flowing
  through the same pipeline as every other deck: CSV → atlas
  (`generate_card_atlases.py`) → save decks (`build_save.py`) → dealt at
  setup (`dealStartingHands`, `lua/setup.lua`). No hand-maintained item
  tables; schema-checked like the other CSVs.
- [x] **Printed weapon bonuses are script-applied.** `getAttackDice` had a
  "would be checked" TODO while market cards printed "+1 Attack die" that
  the script never rolled. `generate_market_data.py` now parses
  "+N Attack die" from the market and starting CSVs into `WEAPON_DICE`, and
  combat adds the best single carried weapon automatically. Card text is the
  single source of truth.

## 5. Code-level hardening

- [x] **`onLoad` save decode wrapped in pcall** (`lua/global.lua`) — a corrupt
  `LuaScriptState` now yields "starting fresh" instead of killing the whole
  mod script.
- [x] **The dead bare-setup UI path is gone.** `onHostSetup` (seat-order
  `Setup()`, no guard) was unreachable from the XML but one refactor away
  from resurrecting the party-overwrite bug; removed. Every UI path runs the
  guided walkthrough; both paths refuse to run on a started game and wipe
  the previous party first. The bare `Setup()` remains for tests/console.
- [x] **One definition of "carried"**: `getPlayerCarriedObjects` in
  `lua/helpers.lua` (hand + player-board area) is shared by the night light
  check and the combat weapon check, so the two can never disagree about
  where items count from.
- [x] **Setup idempotency** (previous pass, recorded here): market deal skips
  occupied slots, party state is wiped before assignment, re-setup is
  refused once started.

## 6. Structure — recommended next

- [ ] **Split `xml/global_ui.xml` (~1,300 lines) into per-domain files**
  (hud.xml / dialogs.xml / setup.xml). `build_save.py` already concatenates
  every `xml/*.xml`, and `conftest.xml_source` would need a one-line glob
  change. Deferred: pure churn with no behavior change — best done as its
  own commit when the UI is next touched broadly.
- [ ] **Publication asset switch test.** `lua/assets.lua` has a `LOCAL_DEV`
  switch and `build_save.py` bakes `file:///` URLs; before any public
  release, add a `--publish` build mode (hosted URLs) plus a test that a
  published save contains no `file:///` or `localhost` URLs.
- [ ] **Adversarial fuzzing.** `test_full_campaign.py` plays random verbs;
  extend with hostile sequences (undo spam, mid-combat restarts, re-entrant
  setup clicks) as bugs of that shape appear.
- [ ] **In-TTS screenshot spot-checks** stay manual (release checklist step
  5) — TTS has no headless mode, so panel layout/contrast can only be
  eyeballed. Keep the checklist honest.
