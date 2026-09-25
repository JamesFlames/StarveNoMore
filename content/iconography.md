# Iconography Spec

Visual vocabulary used across cards, board, sliders, and UI panels. Each icon must have a **unique silhouette** so colorblind players can read it without color cues.

## Stats

| Icon | Symbol | File ID | Notes |
|---|---|---|---|
| ❤ Health | filled heart | — | Red. Cardiac silhouette. |
| 🍴 Hunger | crossed fork & knife | — | Warm orange. |
| 🧠 Sanity | abstract brain spiral | — | Cool purple/teal. |

The standalone `icon_<stat>.png` files were removed in 2026-09 — nothing loaded
them — and `scripts/generate_assets.py` no longer writes them.

## Resources

| Icon | Symbol | File ID | Notes |
|---|---|---|---|
| Wood | log silhouette with rings | `icon_wood.png` | Brown. |
| Metal | gear | `icon_metal.png` | Grey. |
| Cloth | folded bolt | `icon_cloth.png` | Off-white. |
| Provisions | apple | `icon_food.png` | Red. |
| Energy Drink | can with bolt | `icon_energy.png` | Yellow. |
| Battery | AA-shape | `icon_battery.png` | Blue. |

## Actions (Action Bar buttons)

| Icon | Symbol | File ID | Notes |
|---|---|---|---|
| Move | walking figure | `icon_move.png` | |
| Gather | open hand | `icon_gather.png` | |
| Craft | wrench/screwdriver crossed | `icon_craft.png` | |
| Cook | crockpot with steam | `icon_cook.png` | |
| Fight | crossed swords | `icon_fight.png` | |
| Rest | bed/zzz | `icon_rest.png` | |
| Cleanse | salt circle | `icon_cleanse.png` | |
| Trade (free) | two-arrow loop | `icon_trade.png` | |

## Keywords

| Icon | Symbol | File ID | Notes |
|---|---|---|---|
| Combat damage | sword tip | `icon_damage.png` | |
| Defense | shield | `icon_defense.png` | |
| Light source / Fire | flame | `icon_fire.png` | Distinguishes fire from electric. |
| Electric light | lightbulb | `icon_lamp.png` | Disabled when "Charlie ignores Flashlights". |
| Darkness — Charlie risk | crescent moon | `icon_dark.png` | |
| Range | arc/arrow | `icon_range.png` | For ranged weapons. |
| Persistent | infinity loop | `icon_persistent.png` | Item stays equipped. |
| Single-use | crossed-out one | `icon_singleuse.png` | |

## Severity dots

Five-tier ladder, embedded in the top-right corner of every Dawn and Threat card.

| Render | Meaning |
|---|---|
| ●○○○○ | Atmospheric flavor only |
| ●●○○○ | Minor stat hit |
| ●●●○○ | Combat or lasting effect |
| ●●●●○ | Phase-shift event |
| ●●●●● | Boss arrival / apocalyptic |

The legend reproducing this ladder is printed permanently next to the Threat deck (`art/legend/severity_legend.png`).

## Color contracts

- Use the same icon color across components (e.g., Hunger is *always* warm orange, on cards, sliders, buttons, and broadcasts).
- Threshold zones on stat sliders shade red (the "<3 = Bad Things" zone).
- Doom track shades from cool to warm as the marker advances; thresholds are highlighted with red.
- Active player's hand zone glow uses their seat color (`Player[color].seated_color`).
