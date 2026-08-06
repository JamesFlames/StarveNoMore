-- ui_actionbar_core.lua — Action Bar shared core: Move adjacency graph,
-- target-highlight duration, market resource counting + affordability
-- (getPlayerResources / verifyAndPayResources / canAfford). Loaded before
-- the other ui_actionbar_* parts; they reference these chunk-locals.

-- ui_actionbar.lua  (G.3 Action Bar handlers + G.4 Cube animation + G.5 Stat display)

-----------------------------------------------------------------------
-- The map graph, per path variant. THE PRINTED LINES ARE THE MAP: each
-- variant has its own board image (art/board/main_board_<variant>.png) and
-- setup swaps the board to the picked one, so what a player can see is
-- exactly what they can walk. Mirrors scripts/path_layouts.py, which the
-- art generator reads;
-- tests/test_regression_guards.py::test_path_layouts_mirror_the_lua_table
-- keeps the two in lockstep.
--
-- Before this, adjacency was a hard-coded star while the board printed eight
-- edges and the variant was decorative: "the path layout assigned was ring,
-- but I see everything connecting to Ellie & Luca's House... it didn't let me
-- move from James's house to the badminton court, even though I could see a
-- line."
--
-- scenarioFlags.shortcutPath adds a JamesHouse <-> BadmintonCourt edge; that
-- modifier is applied dynamically below.
-----------------------------------------------------------------------
PATH_LAYOUTS = {
    Star = {{"BadmintonCourt","EllieLucaHouse"}, {"BasketballCourt","EllieLucaHouse"}, {"EllieLucaHouse","JamesHouse"}, {"EllieLucaHouse","RaymanHouse"}},
    Ring = {{"BadmintonCourt","EllieLucaHouse"}, {"BadmintonCourt","JamesHouse"}, {"BasketballCourt","JamesHouse"}, {"BasketballCourt","RaymanHouse"}, {"EllieLucaHouse","RaymanHouse"}},
    Compact = {{"BadmintonCourt","EllieLucaHouse"}, {"BadmintonCourt","RaymanHouse"}, {"BasketballCourt","EllieLucaHouse"}, {"BasketballCourt","JamesHouse"}, {"EllieLucaHouse","JamesHouse"}, {"EllieLucaHouse","RaymanHouse"}},
    Sprawl = {{"BadmintonCourt","BasketballCourt"}, {"BadmintonCourt","EllieLucaHouse"}, {"BadmintonCourt","JamesHouse"}, {"BadmintonCourt","RaymanHouse"}, {"BasketballCourt","EllieLucaHouse"}, {"BasketballCourt","JamesHouse"}, {"BasketballCourt","RaymanHouse"}, {"EllieLucaHouse","JamesHouse"}, {"EllieLucaHouse","RaymanHouse"}, {"JamesHouse","RaymanHouse"}},
    Linear = {{"BadmintonCourt","EllieLucaHouse"}, {"BadmintonCourt","RaymanHouse"}, {"BasketballCourt","EllieLucaHouse"}, {"BasketballCourt","JamesHouse"}},
}

-- The variant the shipped save's board image is drawn for (mirrors
-- path_layouts.DEFAULT_VARIANT), used until setup picks one.
DEFAULT_PATH_VARIANT = "Ring"

MAP_LOCATIONS = {"JamesHouse", "RaymanHouse", "EllieLucaHouse",
                 "BasketballCourt", "BadmintonCourt"}

function buildAdjacency(variant)
    local edges = PATH_LAYOUTS[variant] or PATH_LAYOUTS[DEFAULT_PATH_VARIANT]
    local adj = {}
    for _, loc in ipairs(MAP_LOCATIONS) do adj[loc] = {} end
    for _, e in ipairs(edges) do
        if adj[e[1]] and adj[e[2]] then
            table.insert(adj[e[1]], e[2])
            table.insert(adj[e[2]], e[1])
        end
    end
    return adj
end

LOCATION_ADJACENCY = buildAdjacency(DEFAULT_PATH_VARIANT)

-- Point the map at a variant: rebuild the Move graph AND repaint the board so
-- the printed lines match. Called from both setup paths.
-- The board image encodes TWO choices: the path variant (the printed routes)
-- and the difficulty (the length of the printed Doom track). Both are picked
-- during setup, in that order, so the art is resolved from whatever is
-- current rather than baked in when the variant is clicked.
function boardArtUrl(variant)
    local byLimit = BOARD_ART_URLS and BOARD_ART_URLS[variant]
    if not byLimit then return nil end
    return byLimit[getDoomLimit()] or byLimit[30]
end

function applyPathVariant(variant)
    if not PATH_LAYOUTS[variant] then variant = DEFAULT_PATH_VARIANT end
    gameState.pathVariant = variant
    LOCATION_ADJACENCY = buildAdjacency(variant)

    local board = getMainBoard()
    local url = boardArtUrl(variant)
    if not board or not url then return variant end

    -- Swapping a Custom_Board's image requires reload(), which DESTROYS the
    -- object and returns a fresh one — the old handle is dead immediately
    -- after (docs/tts-interface.md). Snap points are captured first and
    -- re-applied, because the Doom track and every location slot live on them.
    local snaps = nil
    pcall(function() snaps = board.getSnapPoints() end)

    safecall(function()
        local custom = board.getCustomObject()
        if not custom or custom.image == url then return end
        custom.image = url
        board.setCustomObject(custom)
        local fresh = board.reload()
        if fresh and snaps then
            Wait.time(function()
                pcall(function() fresh.setSnapPoints(snaps) end)
            end, 0.5)
        end
    end, "PathVariantArt")

    return variant
end

-- The walkable neighbours of a tile live in adjacentLocations() (helpers.lua)
-- so Move, the Dusk scramble, Flee and the standee-drag all answer "is that
-- one step away?" the same way. They did not: three of them open-coded
-- LOCATION_ADJACENCY plus the Shortcut edge, and Flee open-coded only the
-- first half — so under SC_SHORTCUT you could walk the shortcut but not run
-- down it, which is the one direction that rule exists for.

-----------------------------------------------------------------------
-- Highlight helpers — flash legal targets when an action is selected.
-- Uses TTS's per-object highlightOn(color, duration) so it doesn't compete
-- with the global Phase Banner CTA pulse on XML elements.
-----------------------------------------------------------------------
HIGHLIGHT_DURATION = 30  -- seconds; matches TARGET_TIMEOUT so the glow
                               -- never dies while the target buttons remain

-----------------------------------------------------------------------
-- Market affordability: count Resource:* tokens near a player's board
-- and compare against the per-card costs in MARKET_COSTS (auto-loaded
-- from content/cards_market.csv via scripts/generate_market_data.py).
-----------------------------------------------------------------------
local RESOURCE_TYPES = {"Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"}

-- Authoritative held-resource count, read from gameState (NOT from token
-- positions — see the note in helpers.lua). Returns a fresh table with all
-- six keys so callers can index freely.
function getPlayerResources(color)
    local counts = {}
    for _, r in ipairs(RESOURCE_TYPES) do counts[r] = 0 end
    local held = gameState.resources and gameState.resources[color]
    if held then
        for _, r in ipairs(RESOURCE_TYPES) do counts[r] = held[r] or 0 end
    end
    return counts
end

-----------------------------------------------------------------------
-- Verify-and-pay for fixed resource costs (Cleanse, Appease, Barricade).
-- Reads the authoritative held counts (gameState), and on success deducts
-- them and clears the matching decorative tokens. Returns false — with a
-- shortfall message — and takes nothing when unpaid.
-----------------------------------------------------------------------
RESOURCE_LABELS = { EnergyDrink = "Energy Drink" }

function _resLabel(resType) return RESOURCE_LABELS[resType] or resType end

function verifyAndPayResources(color, cost, label)
    local char = gameState.activeChars[color]
    if not char then return false end

    local have = getPlayerResources(color)
    local missing = {}
    for resType, qty in pairs(cost) do
        if (have[resType] or 0) < qty then
            table.insert(missing, qty .. " " .. _resLabel(resType) .. " (have " .. (have[resType] or 0) .. ")")
        end
    end
    if #missing > 0 then
        broadcastToColor("Can't pay for " .. label .. " — missing: " .. table.concat(missing, ", ") ..
            ". Gather more first.", color, BROADCAST_COLORS.damage)
        return false
    end

    -- Pay: deduct the authoritative counts, then clear the visual tokens.
    local held = ensurePlayerResources(color)
    for resType, qty in pairs(cost) do
        held[resType] = math.max(0, (held[resType] or 0) - qty)
        removeVisualTokens(color, resType, qty)
    end

    local parts = {}
    for r, q in pairs(cost) do table.insert(parts, q .. " " .. _resLabel(r)) end
    broadcastEvent("proc", char.name .. " pays " .. table.concat(parts, " + ") .. " for " .. label .. ".")
    safecall(function() refreshStatDisplay() end, "StatDisplay")
    return true
end

function _cardIdFromTags(card)
    if not card or not card.getTags then return nil end
    for _, tag in ipairs(card.getTags()) do
        if tag:match("^M_") then return tag end
    end
    return nil
end

function canAfford(color, cardId)
    if not cardId or not MARKET_COSTS then return true end
    local cost = MARKET_COSTS[cardId]
    if not cost or next(cost) == nil then return true end  -- free or unknown
    local res = getPlayerResources(color)
    local totalCost = 0
    local totalHeld = 0
    for _, qty in pairs(res) do totalHeld = totalHeld + qty end
    for r, qty in pairs(cost) do
        if (res[r] or 0) < qty then return false end
        totalCost = totalCost + qty
    end
    -- Scarcity (Doom >= 15): every craft costs +1 extra resource of any type
    if gameState.ongoingDawnEffects and gameState.ongoingDawnEffects.doom15 then
        if totalHeld < totalCost + 1 then return false end
    end
    return true
end
