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

function getPlayerResources(color)
    local counts = {}
    for _, r in ipairs(RESOURCE_TYPES) do counts[r] = 0 end

    local charName = colorToCharacter(color)
    if not charName then return counts end
    local board = getPlayerBoard(charName)
    if not board then return counts end

    -- Build a generous bounding box around the player board so resources
    -- placed alongside the board still count.
    local pos = board.getPosition()
    local b = board.getBoundsNormalized()
    local pad = 1.5
    local minX = pos.x - b.size.x * 0.5 - pad
    local maxX = pos.x + b.size.x * 0.5 + pad
    local minZ = pos.z - b.size.z * 0.5 - pad
    local maxZ = pos.z + b.size.z * 0.5 + pad

    for _, obj in ipairs(findAllByTag("Resource")) do
        local p = obj.getPosition()
        if p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
            for _, tag in ipairs(obj.getTags()) do
                local resType = tag:match("^Resource:(.+)$")
                if resType and counts[resType] ~= nil then
                    counts[resType] = counts[resType] + 1
                    break
                end
            end
        end
    end
    return counts
end

-----------------------------------------------------------------------
-- Verify-and-pay for fixed resource costs (Cleanse, Appease, Barricade).
-- Verifies the tokens sit in the payer's board area, then returns them
-- to their supply bags (or deletes them if the bag is gone). Returns
-- false — with a shortfall message — and takes nothing when unpaid.
-----------------------------------------------------------------------
local RESOURCE_LABELS = { EnergyDrink = "Energy Drink" }

local function _resLabel(resType) return RESOURCE_LABELS[resType] or resType end

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
            ". Resource tokens must sit next to your player board.", color, BROADCAST_COLORS.damage)
        return false
    end

    -- Pay: pull matching tokens out of the board area, back into supply.
    local board = getPlayerBoard(char.name)
    if not board then return false end
    local pos = board.getPosition()
    local b = board.getBoundsNormalized()
    local pad = 1.5
    local minX = pos.x - b.size.x * 0.5 - pad
    local maxX = pos.x + b.size.x * 0.5 + pad
    local minZ = pos.z - b.size.z * 0.5 - pad
    local maxZ = pos.z + b.size.z * 0.5 + pad

    local remaining = {}
    for r, q in pairs(cost) do remaining[r] = q end
    for _, obj in ipairs(findAllByTag("Resource")) do
        local p = obj.getPosition()
        if p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
            for _, tag in ipairs(obj.getTags()) do
                local resType = tag:match("^Resource:(.+)$")
                if resType and (remaining[resType] or 0) > 0 then
                    remaining[resType] = remaining[resType] - 1
                    local bag = getResourceBag(resType)
                    if bag then
                        pcall(function() bag.putObject(obj) end)
                    else
                        pcall(function() obj.destruct() end)
                    end
                    break
                end
            end
        end
    end

    local parts = {}
    for r, q in pairs(cost) do table.insert(parts, q .. " " .. _resLabel(r)) end
    broadcastEvent("proc", char.name .. " pays " .. table.concat(parts, " + ") ..
        " for " .. label .. " (tokens returned to supply automatically).")
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
