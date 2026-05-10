# Asset Manifest

All visual assets the mod references. Each row gives the asset ID (used in `lua/assets.lua`), the local development path, and the planned final URL.

**Hosting strategy (Phase C.1):** during development we reference assets via `file:///` URLs from `art/`. Pre-publish, they will be uploaded to Steam Workshop (caching is automatic on `Mod Caching = on`) or, if a CDN is preferred, mirrored to imgur direct links (`https://i.imgur.com/xxxxx.png`). The Lua module `lua/assets.lua` is the single switching point — change URLs there only.

## Boards and tiles

| Asset ID | Local path | Final URL (placeholder until publish) |
|---|---|---|
| `BOARD_MAIN` | `art/board/main_board.png` | https://i.imgur.com/PLACEHOLDER_main.png |
| `TILE_JAMES` | `art/tiles/james.png` | https://i.imgur.com/PLACEHOLDER_t1.png |
| `TILE_RAYMAN` | `art/tiles/rayman.png` | https://i.imgur.com/PLACEHOLDER_t2.png |
| `TILE_ELLIE_LUCA` | `art/tiles/ellie_luca.png` | https://i.imgur.com/PLACEHOLDER_t3.png |
| `TILE_BASKETBALL` | `art/tiles/basketball.png` | https://i.imgur.com/PLACEHOLDER_t4.png |
| `TILE_BADMINTON` | `art/tiles/badminton.png` | https://i.imgur.com/PLACEHOLDER_t5.png |
| `PATH_COMPACT` | `art/board/path_compact.png` | https://i.imgur.com/PLACEHOLDER_pc.png |
| `PATH_SPRAWL` | `art/board/path_sprawl.png` | https://i.imgur.com/PLACEHOLDER_ps.png |
| `PATH_LINEAR` | `art/board/path_linear.png` | https://i.imgur.com/PLACEHOLDER_pl.png |

## Character art

| Asset ID | Local path | Final URL |
|---|---|---|
| `CHAR_JAMES_FRONT` | `art/characters/james_front.png` | placeholder |
| `CHAR_JAMES_BACK` | `art/characters/james_back.png` | placeholder |
| `CHAR_JAMES_GHOST` | `art/characters/james_ghost.png` | placeholder |
| `BOARD_JAMES` | `art/characters/board_james.png` | placeholder |
| ... | (similar set for COCO, RAYMAN, ELLIE, LUCA) | placeholder |

## Boss art

| Asset ID | Local path | Final URL |
|---|---|---|
| `BOSS_DEERCLOPS_FRONT` | `art/bosses/deerclops_front.png` | placeholder |
| `BOSS_DEERCLOPS_BACK` | `art/bosses/deerclops_back.png` | placeholder |
| `BOSS_EYE_FRONT` | `art/bosses/eye_front.png` | placeholder |
| `BOSS_EYE_BACK` | `art/bosses/eye_back.png` | placeholder |
| `BOSS_SOURCE_FRONT` | `art/bosses/source_front.png` | placeholder |
| `BOSS_SOURCE_BACK` | `art/bosses/source_back.png` | placeholder |

## Card atlases

| Asset ID | Local path | Final URL | Grid |
|---|---|---|---|
| `DECK_PHASE1_FACE` | `art/decks/phase1_face.png` | placeholder | 4x3 |
| `DECK_PHASE1_BACK` | `art/decks/phase1_back.png` | placeholder | 1x1 |
| `DECK_PHASE2_FACE` | `art/decks/phase2_face.png` | placeholder | 4x3 |
| `DECK_PHASE2_BACK` | `art/decks/phase2_back.png` | placeholder | 1x1 |
| `DECK_PHASE3_FACE` | `art/decks/phase3_face.png` | placeholder | 4x3 |
| `DECK_PHASE3_BACK` | `art/decks/phase3_back.png` | placeholder | 1x1 |
| `DECK_PHASE4_FACE` | `art/decks/phase4_face.png` | placeholder | 4x3 |
| `DECK_PHASE4_BACK` | `art/decks/phase4_back.png` | placeholder | 1x1 |
| `DECK_MARKET_FACE` | `art/decks/market_face.png` | placeholder | 7x8 |
| `DECK_MARKET_BACK` | `art/decks/market_back.png` | placeholder | 1x1 |
| `DECK_RECIPE_FACE` | `art/decks/recipe_face.png` | placeholder | 5x4 |
| `DECK_RECIPE_BACK` | `art/decks/recipe_back.png` | placeholder | 1x1 |
| `DECK_THREAT_FACE` | `art/decks/threat_face.png` | placeholder | 6x5 |
| `DECK_THREAT_BACK` | `art/decks/threat_back.png` | placeholder | 1x1 |
| `DECK_VISITOR_FACE` | `art/decks/visitor_face.png` | placeholder | 3x2 |
| `DECK_VISITOR_BACK` | `art/decks/visitor_back.png` | placeholder | 1x1 |
| `DECK_TROPHY_FACE` | `art/decks/trophy_face.png` | placeholder | 2x2 |
| `DECK_TROPHY_BACK` | `art/decks/trophy_back.png` | placeholder | 1x1 |

## Token / icon images

| Asset ID | Local path |
|---|---|
| `ICON_HEALTH` | `art/icons/icon_health.png` |
| `ICON_HUNGER` | `art/icons/icon_hunger.png` |
| `ICON_SANITY` | `art/icons/icon_sanity.png` |
| `ICON_WOOD` ... `ICON_BATTERY` | `art/icons/icon_*.png` |
| `ICON_MOVE` ... `ICON_CLEANSE` | `art/icons/icon_*.png` |
| `TOKEN_DOOM` | `art/tokens/doom_marker.png` |
| `TOKEN_HEART` | `art/tokens/telltale_heart.png` |
| `TOKEN_RESOURCE_*` | `art/tokens/resource_*.png` |
| `TOKEN_STAT_MARKER` | `art/tokens/stat_marker.png` |

## Severity legend

| Asset ID | Local path |
|---|---|
| `LEGEND_SEVERITY` | `art/legend/severity_legend.png` |

## UI backgrounds

| Asset ID | Local path |
|---|---|
| `UI_BG_BANNER` | `art/ui/bg_banner.png` |
| `UI_BG_HELP_PANEL` | `art/ui/bg_help_panel.png` |
| `UI_BG_MODAL` | `art/ui/bg_modal.png` |
| `UI_BG_BOARD_PANEL` | `art/ui/bg_board_panel.png` |

## Notes

- Final URLs above are placeholders. Before publishing the mod, art is produced (Phase B), uploaded (Phase C.2), and `lua/assets.lua` is regenerated (Phase C.3).
- During local development, `lua/assets.lua` defaults to `file:///` URLs pointing into `art/`. The `LOCAL_DEV` flag in `lua/assets.lua` controls this.
