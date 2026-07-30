# Regression Guards — `test_regression_guards.py`

Generic guards for the *classes* of bug that keep recurring in playtest, each
encoding one hard-won lesson (see [`../tts-runtime.md`](../tts-runtime.md) and
[`../tts-interface.md`](../tts-interface.md)). Split out of
[test-guards.md](test-guards.md), which lists the rest of the static suite.

*Part of the [agent reference](README.md); the index and the documentation map live in [`agents.md`](../../agents.md).*

Generic guards for the *classes* of bug that keep recurring in playtest, each
encoding one hard-won lesson (see [`../tts-runtime.md`](../tts-runtime.md) and
[`../tts-interface.md`](../tts-interface.md)):

1. laid-out object groups (player boards, location tiles) must not overlap at spawn — physics scatters an overlapping stack (the root cause of "Gather shows 0");
2. text-gadget objects (Notecard/Counter) must be upright (rotY≈0), not 180 (the upside-down Quick Start);
3. button text must clear a minimum contrast (3.0) against its own background (the dark-on-dark readability complaints); transparent click-overlays are excluded;
4. **every `takeObject` callback that dereferences its object handle must wrap it in pcall/safecall** — a dead handle throws "cannot access field … of userdata"; that crash hit three times in one session and the guard immediately found five more latent ones;
5. every tag passed to `findOneByTag`/`findAllByTag`/`getObjectsWithTag` — literal (`"DoomMarker"`) or namespaced (`"Location:" .. name`) — must exist in the built save, because a typo'd tag fails **silently** (returns nil, feature quietly does nothing);
6. player-facing text must not name a component that was removed from the save (a Dawn card told players to use the Discard Tray after it was deleted); keyed by tag, so it only fires once the component is really gone;
7. no player-facing string may hardcode the Standard `of 7` / `/ 30` — those are wrong on Long Weekend (3 days, Doom 15) and Nightmare; use `getTotalDays()` / `getDoomLimit()` or the `{totalDays}` / `{doomLimit}` tooltip placeholders;
8. `gameState` fields must be initialised (literal default, `migrateGameState`, or a lazy init earlier in the same function) before being indexed — otherwise a fresh setup or loaded old save crashes with "attempt to index a nil value".

Runtime companions live in `test_lua_actions.py`: `TestResourceModelRobustness`
(held resources stay correct when a board is dragged away — the
gather-shows-zero class), `TestStatDisplayNeverStale` (the left stat box shows
live stats with no active player, not a frozen snapshot), and
`TestDifficultyAwareText` (the Doom help panel and the Day/Doom tooltips print
the *active difficulty's* limits, with no unsubstituted `{placeholders}`).
