# Starve No More — Design Concept

> A cooperative survival board game for 3–5 players. Suburban friends caught when something cosmic descends on their neighborhood must scavenge, cook, fight, and hold their sanity together for seven nights. Aesthetic and tone modeled on *Don't Starve Together*; mechanical DNA drawn from *Don't Starve Together*, *Harry Potter: Hogwarts Battle*, *Settlers of Catan*, and *Cthulhu Wars*. Designed to be implemented in **Tabletop Simulator** (Berserk Games, app `286160`).

---

## Document Purpose

This is the design brief for **Starve No More**. It is intended as the single source of truth used to:

1. Communicate the game's vision, theme, and rules.
2. Drive prototype playtesting.
3. Hand off to the Tabletop Simulator implementation phase as a buildable spec.

The document references and is consistent with:
- [Archive/PrinciplesOfGoodBoardGames.md](Archive/PrinciplesOfGoodBoardGames.md) — general design theory.
- [Archive/DontStarveVideoGamePrinciples.md](Archive/DontStarveVideoGamePrinciples.md) — DST-derived design pillars.
- InterestingGames.md — mechanical patterns from HPHB, Catan, Cthulhu Wars (notes retired 2026-07; recover from git history).
- [Archive/HowToCreateGamesInTabletopSimulator.md](Archive/HowToCreateGamesInTabletopSimulator.md) — implementation reference (frozen).

---

## Table of Contents

The design is split by topic under [`docs/design/`](docs/design/) so an agent (or
reader) loads only the section it needs. Each file is self-contained and links
back here. Prose cross-references to section numbers (e.g. "§6.7", "§18.10") stay
valid — the **Section → file** column below is the jump table.

| Section | Topic | File |
|---|---|---|
| §1–4 | Pitch, Design Pillars, Player Count & Audience, The Core Loop | [`docs/design/01-pitch-pillars.md`](docs/design/01-pitch-pillars.md) |
| §5–6 | Components List, Characters | [`docs/design/02-components-characters.md`](docs/design/02-components-characters.md) |
| §7–8 | Locations, Resources & the Economy | [`docs/design/03-locations-economy.md`](docs/design/03-locations-economy.md) |
| §9 | The Card Decks | [`docs/design/04-decks.md`](docs/design/04-decks.md) |
| §10–11 | Stats & Player Boards, Turn Structure | [`docs/design/05-stats-turn-structure.md`](docs/design/05-stats-turn-structure.md) |
| §12–13 | Combat, Crafting & Cooking | [`docs/design/06-combat-crafting.md`](docs/design/06-combat-crafting.md) |
| §14–15 | The Week Arc & Pacing, The Doom Track & Scheduled Threats | [`docs/design/07-week-arc-doom.md`](docs/design/07-week-arc-doom.md) |
| §16–17 | Victory & Defeat Conditions, Setup | [`docs/design/08-victory-setup.md`](docs/design/08-victory-setup.md) |
| §18 | Tabletop Simulator Implementation (the largest section) | [`docs/design/09-tts-implementation.md`](docs/design/09-tts-implementation.md) |
| §19–20 | Design Rationale Cross-Reference, Balancing & Playtest Plan, Closing Notes | [`docs/design/10-rationale-balancing.md`](docs/design/10-rationale-balancing.md) |

For "which code file implements X?" see [`TASKMAP.md`](TASKMAP.md); for "where is
Lua function X?" grep [`SYMBOLS.md`](SYMBOLS.md).
