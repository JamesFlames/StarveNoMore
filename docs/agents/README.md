# `docs/agents/` — the deep reference, one topic per file

[`agents.md`](../../agents.md) used to carry all of this in one ~18.6k-token
file, which meant a task needing one section paid for all of them. Same content,
split at its natural seams. Open the topic, not this index.

| File | ~tok | Open when you need to |
|---|---:|---|
| [architecture.md](architecture.md) | 1.2k | understand how the save is assembled, or why load order is the dependency graph |
| [file-structure.md](file-structure.md) | 1.7k | find what lives where, or what a directory is for |
| [design-reference.md](design-reference.md) | 0.9k | check characters, locations, phases, the Doom track, the win condition |
| [combat-and-actions.md](combat-and-actions.md) | 1.6k | change combat maths or any player action |
| [economy-and-session.md](economy-and-session.md) | 1.0k | change the resource economy, Dusk/difficulty/telemetry, or an A/B variant |
| [test-suite.md](test-suite.md) | 1.5k | know which module runs what gameplay, or run the release checklist |
| [test-guards.md](test-guards.md) | 2.2k | find the static guard that just failed, or add one |
| [content-wiring-guards.md](content-wiring-guards.md) | 1.2k | does each card / location / trophy actually do what it prints? |
| [regression-guards.md](regression-guards.md) | 0.7k | the eight recurring bug classes `test_regression_guards.py` pins |
| [balance-simulation.md](balance-simulation.md) | 1.8k | re-run the Monte Carlo after a rules change |
| [balance-location-defence.md](balance-location-defence.md) | 1.3k | read the batch-5 verdict on the §7.1-7.5 defence roll |
| [balance-scenarios.md](balance-scenarios.md) | 2.5k | which Scenario card is hard, and which team survives it |
| [balance-map-and-rosters.md](balance-map-and-rosters.md) | 2.2k | what the path variant, the roster and the player count are worth |
| [balance-recommendations.md](balance-recommendations.md) | 2.1k | priced rule changes, in the order to take them |
| [ux-affordances.md](ux-affordances.md) | 2.1k | keep "the next legal action is always visible" true |
| [audio.md](audio.md) | 1.2k | add or change a sound |
| [comfyui.md](comfyui.md) | 1.9k | regenerate card or board art |
| [derived-art.md](derived-art.md) | 0.7k | new tile or standee art that isn't showing up in game |
| [working-with-this-project.md](working-with-this-project.md) | 0.8k | make any change, day to day |

## What stayed in `agents.md`

The parts that get read *first*, and so should not cost an extra file open:
the **Documentation Map** (the index of every doc in the repo) and the
**Key Conventions** list.

## Related indexes, not here

- **"Where do I change X?"** → [`TASKMAP.md`](../../TASKMAP.md)
- **"Where is function X?"** → `python scripts/sym.py NAME`
- **Rules and design questions** → [`docs/design/`](../design/README.md)
- **`gameState` fields** → [`docs/gamestate.md`](../gamestate.md)
- **Talking to TTS** → [`docs/tts-interface.md`](../tts-interface.md) and
  [`docs/tts-runtime.md`](../tts-runtime.md)

## Adding a topic file

Keep each file under ~2.5k tokens — that is the budget this split exists to
hold. If a topic outgrows it, split it again at a real seam (as
`design-reference.md` and `combat-and-actions.md` were) rather than letting one
file drift back toward being the monolith. Add the row here **and** in
`agents.md`'s jump table; `tests/test_doc_agents_split.py` fails if the two
disagree or if a file is missing from either.
