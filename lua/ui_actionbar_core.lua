-- ui_actionbar_core.lua — Action Bar shared core: Move adjacency graph,
-- target-highlight duration, market resource counting + affordability
-- (getPlayerResources / verifyAndPayResources / canAfford). Loaded before
-- the other ui_actionbar_* parts; they reference these chunk-locals.

-- ui_actionbar.lua  (G.3 Action Bar handlers + G.4 Cube animation + G.5 Stat display)

-----------------------------------------------------------------------
-- Default Compact path graph for Move-target highlights.
-- The design supports 3 path variants (Compact/Sprawl/Linear) plus a
-- scenarioFlags.shortcutPath edge between JamesHouse and BadmintonCourt;
-- those modifiers are applied dynamically below.
-----------------------------------------------------------------------
LOCATION_ADJACENCY = {
    JamesHouse      = {"EllieLucaHouse"},
    RaymanHouse     = {"EllieLucaHouse"},
    EllieLucaHouse  = {"JamesHouse", "RaymanHouse", "BasketballCourt", "BadmintonCourt"},
    BasketballCourt = {"EllieLucaHouse"},
    BadmintonCourt = {"EllieLucaHouse"},
}

function _adjacentLocations(loc)
    local out = {}
    for _, n in ipairs(LOCATION_ADJACENCY[loc] or {}) do
        out[#out+1] = n
    end
    -- Shortcut scenario: JamesHouse <-> BadmintonCourt edge
    local sFlags = gameState.scenarioFlags or {}
    if sFlags.shortcutPath then
        if loc == "JamesHouse" then out[#out+1] = "BadmintonCourt"
        elseif loc == "BadmintonCourt" then out[#out+1] = "JamesHouse" end
    end
    return out
end

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
local RESOURCE_TYPES = {"Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"}

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
