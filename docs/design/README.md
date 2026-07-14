# docs/design/ — the design doc, split by topic

The canonical design of **Starve No More**, split from the former single
1,500-line `StarveNoMoreDesignConcept.md` so each topic loads on its own. The
root [`StarveNoMoreDesignConcept.md`](../../StarveNoMoreDesignConcept.md) is now a
thin index (Document Purpose + the Section → file jump table).

| File | Sections | Topic |
|---|---|---|
| [01-pitch-pillars.md](01-pitch-pillars.md) | §1–4 | Pitch, Design Pillars, Player Count & Audience, Core Loop |
| [02-components-characters.md](02-components-characters.md) | §5–6 | Components List, Characters |
| [03-locations-economy.md](03-locations-economy.md) | §7–8 | Locations, Resources & the Economy |
| [04-decks.md](04-decks.md) | §9 | The Card Decks |
| [05-stats-turn-structure.md](05-stats-turn-structure.md) | §10–11 | Stats & Player Boards, Turn Structure |
| [06-combat-crafting.md](06-combat-crafting.md) | §12–13 | Combat, Crafting & Cooking |
| [07-week-arc-doom.md](07-week-arc-doom.md) | §14–15 | Week Arc & Pacing, Doom Track & Scheduled Threats |
| [08-victory-setup.md](08-victory-setup.md) | §16–17 | Victory & Defeat, Setup |
| [09-tts-implementation.md](09-tts-implementation.md) | §18 | Tabletop Simulator Implementation |
| [10-rationale-balancing.md](10-rationale-balancing.md) | §19–20 | Design Rationale, Balancing & Playtest Plan, Closing Notes |

Prose references to section numbers (e.g. "§6.7") throughout `lua/` and
`scripts/` stay valid — use the table above (or the index) to jump to the file.
