-- assets.lua
-- Single source of truth for all image URLs.
-- During local dev: run scripts/serve_art.bat, then set LOCAL_DEV = true.
-- Before publishing: set LOCAL_DEV = false and fill in the LIVE_* strings.

-- TTS has no require() — this file is concatenated into the global script.
-- ASSETS is a global table referenced by all other modules.

-- The local dev server (scripts/serve_art.bat) now serves the repo root,
-- so paths under art/ go via the /art prefix. Sound URLs go through
-- audio_manifest.lua which uses its own /sounds prefix.
local _BASE = "http://localhost:8080/art"
local function _url(path) return _BASE .. "/" .. path end

ASSETS = {
    -- Boards
    BOARD_MAIN            = url("board/main_board.png"),
    PATH_COMPACT          = url("board/path_compact.png"),
    PATH_SPRAWL           = url("board/path_sprawl.png"),
    PATH_LINEAR           = url("board/path_linear.png"),
    PATH_RING             = url("board/path_ring.png"),
    PATH_STAR             = url("board/path_star.png"),

    -- Location tiles
    TILE_JAMES            = url("tiles/jameshome.png"),
    TILE_RAYMAN           = url("tiles/raymanhome.png"),
    TILE_ELLIE_LUCA       = url("tiles/ellielucahome.png"),
    TILE_BASKETBALL       = url("tiles/basketballcourt.png"),
    TILE_BADMINTON        = url("tiles/badmintoncourt.png"),

    -- Character standees
    CHAR_JAMES_FRONT      = url("characters/james_front.png"),
    CHAR_JAMES_BACK       = url("characters/james_back.png"),
    CHAR_COCO_FRONT       = url("characters/coco_front.png"),
    CHAR_COCO_BACK        = url("characters/coco_back.png"),
    CHAR_RAYMAN_FRONT     = url("characters/rayman_front.png"),
    CHAR_RAYMAN_BACK      = url("characters/rayman_back.png"),
    CHAR_ELLIE_FRONT      = url("characters/ellie_front.png"),
    CHAR_ELLIE_BACK       = url("characters/ellie_back.png"),
    CHAR_LUCA_FRONT       = url("characters/luca_front.png"),
    CHAR_LUCA_BACK        = url("characters/luca_back.png"),

    -- Player boards
    BOARD_JAMES           = url("characters/board_james.png"),
    BOARD_COCO            = url("characters/board_coco.png"),
    BOARD_RAYMAN          = url("characters/board_rayman.png"),
    BOARD_ELLIE           = url("characters/board_ellie.png"),
    BOARD_LUCA            = url("characters/board_luca.png"),

    -- Bosses
    BOSS_DEERCLOPS        = url("bosses/deerclops.png"),
    BOSS_CHARLIE          = url("bosses/charlie.png"),
    BOSS_EYE_OF_TERROR    = url("bosses/eye_of_terror.png"),
    BOSS_THE_SOURCE       = url("bosses/the_source.png"),
    BOSS_BEARGER          = url("bosses/bearger.png"),
    BOSS_HOUND            = url("bosses/hound.png"),
    BOSS_SPIDER_QUEEN     = url("bosses/spider_queen.png"),
    BOSS_TREEGUARD        = url("bosses/treeguard.png"),

    -- Card deck atlases (face + back)
    DECK_PHASE1_FACE      = url("decks/phase1_face.png"),
    DECK_PHASE1_BACK      = url("decks/phase1_back.png"),
    DECK_PHASE2_FACE      = url("decks/phase2_face.png"),
    DECK_PHASE2_BACK      = url("decks/phase2_back.png"),
    DECK_PHASE3_FACE      = url("decks/phase3_face.png"),
    DECK_PHASE3_BACK      = url("decks/phase3_back.png"),
    DECK_PHASE4_FACE      = url("decks/phase4_face.png"),
    DECK_PHASE4_BACK      = url("decks/phase4_back.png"),
    DECK_MARKET_FACE      = url("decks/market_face.png"),
    DECK_MARKET_BACK      = url("decks/market_back.png"),
    DECK_RECIPE_FACE      = url("decks/recipe_face.png"),
    DECK_RECIPE_BACK      = url("decks/recipe_back.png"),
    DECK_THREAT_FACE      = url("decks/threat_face.png"),
    DECK_THREAT_BACK      = url("decks/threat_back.png"),
    DECK_VISITOR_FACE     = url("decks/visitor_face.png"),
    DECK_VISITOR_BACK     = url("decks/visitor_back.png"),
    DECK_TROPHY_FACE      = url("decks/trophy_face.png"),
    DECK_TROPHY_BACK      = url("decks/trophy_back.png"),

    -- Stat + resource icons
    ICON_HEALTH           = url("icons/icon_health.png"),
    ICON_HUNGER           = url("icons/icon_hunger.png"),
    ICON_SANITY           = url("icons/icon_sanity.png"),

    -- Tokens
    TOKEN_DOOM            = url("tokens/doom_marker.png"),
    TOKEN_HEART           = url("tokens/telltale_heart.png"),
    TOKEN_WOOD            = url("tokens/resource_wood.png"),
    TOKEN_METAL           = url("tokens/resource_metal.png"),
    TOKEN_CLOTH           = url("tokens/resource_cloth.png"),
    TOKEN_FOOD            = url("tokens/resource_food.png"),
    TOKEN_ENERGY          = url("tokens/resource_energy.png"),
    TOKEN_BATTERY         = url("tokens/resource_battery.png"),
    TOKEN_SANITY_D8       = url("tokens/sanity_d8.png"),

    -- Severity legend
    LEGEND_SEVERITY       = url("legend/severity_legend.png"),
}
