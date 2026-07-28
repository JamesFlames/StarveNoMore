# `docs/agents/` — the deep reference, one topic per file

[`agents.md`](../../agents.md) used to carry all of this in one ~18.6k-token
file, which meant a task needing one section paid for all of them. Same content,
split at its natural seams. Open the topic, not this index.

| File | ~tok | Open when you need to |
|---|---:|---|
| [architecture.md](architecture.md) | 1.2k | understand how the save is assembled, or why load order is the dependency graph |
| [file-structure.md](file-structure.md) | 1.7k | find what lives where, or what a directory is for |
| [design-reference.md](design-reference.md) | 0.9k | check characters, locations, phases, the Doom track, the win condition |
| [combat-and-actions.md](combat-and-actions.md) | 2.2k | change combat maths or any player action |
| [test-suite.md](test-suite.md) | 2.4k | know which module covers what, or run the release checklist |
| [balance-simulation.md](balance-simulation.md) | 1.7k | re-run the Monte Carlo after a rules change |
| [ux-affordances.md](ux-affordances.md) | 2.1k | keep "the next legal action is always visible" true |
| [audio.md](audio.md) | 1.2k | add or change a sound |
| [comfyui.md](comfyui.md) | 2.2k | regenerate card or board art |
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
