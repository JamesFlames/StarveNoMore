-- items.lua — USE ITEM: the single-use Market consumables.
--
-- Every one of these cards prints a mechanical effect, and until now there was
-- no way in the mod to apply any of them. There is no Use Item verb, no
-- manual stat editor, and stats live in gameState where a player cannot reach
-- them — so crafting a First Aid Kit produced a card in your hand that could
-- not do the thing written on its face, by any means the game provided.
--
-- Scope: the cards whose printed effect is a pure stat or Doom change. The
-- rest of the single-use set (Circle of Salt, Camera, Whistle, Pepper Spray,
-- Old Cellphone) needs machinery this verb does not have — boss movement
-- bans, deck reordering, pulling other characters around — and is listed in
-- tests/test_market_wiring.py as deliberately unwired rather than forgotten.
--
-- Targets are picked, not prompted, the same way the Scarcity surcharge picks
-- a resource and James's reroll picks a die: the item goes where it does the
-- most good, and the choice is announced. A prompt here would be a third
-- target dialog for a decision that is nearly always forced.

-- effect tables are { stat = amount }; `target` says who receives it:
--   "self"  — the user
--   "tile"  — whoever at the user's tile needs it most (the user included)
--   "ally"  — as "tile", but never the user
-- `doom` is a Doom-track delta instead of a stat change.
USE_ITEMS = {
    M_BANDAGE            = { label = "Bandage",             target = "self",
                             stats = { health = 2 } },
    M_FIRST_AID          = { label = "First Aid Kit",       target = "tile",
                             stats = { health = 4 }, key = "health" },
    M_ENERGY_BAR         = { label = "Energy Bar",          target = "self",
                             stats = { hunger = 3 } },
    M_PROTEIN_BAR        = { label = "Protein Bar",         target = "self",
                             stats = { hunger = 4 } },
    M_HOT_COCOA          = { label = "Hot Cocoa",           target = "self",
                             stats = { hunger = 2, sanity = 1 } },
    M_SPORTS_DRINK       = { label = "Sports Drink",        target = "self",
                             stats = { hunger = 2, sanity = 1 } },
    M_FRIENDSHIP_BRACELET = { label = "Friendship Bracelet", target = "ally",
                             stats = { sanity = 2 }, key = "sanity" },
    M_SCHOOL_BELL        = { label = "School Bell",         target = "self",
                             doom = -1 },

    -- Starting items (cards_starting.csv) whose printed effect is the same
    -- single-stat/single-target shape as the Market items above — wired the
    -- same way. "How do I get Luca to use Pep Talk?" had no answer: there is
    -- no Use Item verb outside this table, and USE_ITEM_ORDER only ever
    -- listed Market ids, so a card in your STARTING hand with a mechanical
    -- effect printed on it was unusable from the moment the game began, not
    -- just until your first Craft. The rest of the starting single-use set
    -- (Athletic Tape's heal-or-repair choice, Spare Battery's two different
    -- jobs, Whistle's reactive trigger, Loud Whistle/Notebook/Pantry Key's
    -- contextual triggers) needs machinery this verb does not have, same as
    -- the Market's own UNWIRED list (tests/test_market_wiring.py).
    S_PEP_TALK           = { label = "Pep Talk",            target = "ally",
                             stats = { sanity = 2 }, key = "sanity" },
    S_FIRST_AID_KIT       = { label = "First Aid Kit",       target = "tile",
                             stats = { health = 4 }, key = "health" },
    S_HOPEFUL_TEA         = { label = "Hopeful Tea",         target = "tile",
                             stats = { hunger = 1, sanity = 2 }, key = "sanity" },
    S_SPORTS_DRINK        = { label = "Sports Drink",        target = "self",
                             stats = { hunger = 2 } },
}

-- Stable order, so the dialog never reshuffles between openings.
USE_ITEM_ORDER = {
    "M_FIRST_AID", "M_BANDAGE", "M_PROTEIN_BAR", "M_ENERGY_BAR",
    "M_HOT_COCOA", "M_SPORTS_DRINK", "M_FRIENDSHIP_BRACELET", "M_SCHOOL_BELL",
    "S_FIRST_AID_KIT", "S_HOPEFUL_TEA", "S_PEP_TALK", "S_SPORTS_DRINK",
}

-- "+3 Hunger, +1 Sanity" for a dialog label / broadcast.
function describeItemEffect(spec)
    if spec.doom then
        return "Doom " .. (spec.doom > 0 and "+" or "") .. spec.doom
    end
    local parts = {}
    for _, stat in ipairs({"health", "hunger", "sanity"}) do
        if spec.stats and spec.stats[stat] then
            parts[#parts + 1] = "+" .. spec.stats[stat] .. " " .. stat
        end
    end
    return table.concat(parts, ", ")
end

-- Which item ids is this player actually carrying?
function usableItemsFor(color)
    local out = {}
    for _, id in ipairs(USE_ITEM_ORDER) do
        local spec = USE_ITEMS[id]
        if findCarriedItem(color, id, spec.label) then
            out[#out + 1] = id
        end
    end
    return out
end

-- Who the item lands on. "self" is the user; "tile"/"ally" pick whoever at
-- the user's tile is lowest in the stat the item restores, so a First Aid Kit
-- reaches the person actually bleeding. Ties go to the lowest seat colour via
-- the sorted scan, so it is deterministic rather than pairs()-order.
local function _recipient(color, spec)
    if spec.target == "self" then return color end
    local user = gameState.activeChars[color]
    if not user then return nil end
    local key = spec.key or "health"
    local best, bestVal = nil, nil
    local seats = {"White", "Red", "Yellow", "Green", "Blue"}
    for _, c in ipairs(seats) do
        local ch = gameState.activeChars[c]
        local eligible = ch and not ch.down and ch.location == user.location
        if eligible and spec.target == "ally" and c == color then eligible = false end
        if eligible and (bestVal == nil or ch[key] < bestVal) then
            best, bestVal = c, ch[key]
        end
    end
    -- "tile" always has a fallback (the user is on their own tile); "ally"
    -- genuinely can have none, and canUseItem refuses in that case.
    if not best and spec.target == "tile" then return color end
    return best
end

function canUseItem(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    local ids = usableItemsFor(color)
    if #ids == 0 then
        return false, "No usable item in hand or by your board."
    end
    -- A Friendship Bracelet with nobody to give it to is not usable, but any
    -- other carried item still is — so only refuse when NOTHING can land.
    for _, id in ipairs(ids) do
        if _recipient(color, USE_ITEMS[id]) then return true end
    end
    return false, "Nobody here to give it to."
end

-- Use one carried item. Free — these are consumables, not actions; the action
-- economy already prices the Craft that produced them.
function doUseItem(color, itemId)
    local spec = USE_ITEMS[itemId]
    if not spec then
        broadcastToColor("That isn't a usable item.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    if not char or char.down then return false end

    -- Re-checked here and not only in the precondition: without it a caller
    -- with an empty hand gets the effect for free, which is the hole Revive
    -- guards against and Stabilize used to have.
    local obj = findCarriedItem(color, itemId, spec.label)
    if not obj then
        broadcastToColor("You aren't carrying a " .. spec.label .. ".", color, BROADCAST_COLORS.damage)
        return false
    end

    local targetColor = _recipient(color, spec)
    if not targetColor and not spec.doom then
        broadcastToColor("Nobody here to give the " .. spec.label .. " to.",
            color, BROADCAST_COLORS.damage)
        return false
    end

    consumeCarriedItem(obj)   -- single-use, as every one of these cards prints

    if spec.doom then
        gameState.doom = math.max(0, gameState.doom + spec.doom)
        safecall(function() moveDoomMarker(gameState.doom) end, "DoomMarker")
        broadcastEvent("gain", char.name .. " rings the " .. spec.label ..
            " — Doom " .. spec.doom .. " (now " .. gameState.doom ..
            " / " .. getDoomLimit() .. ").")
        safecall(function() recordUsage("items", spec.label) end, "Usage")
        return true
    end

    local target = gameState.activeChars[targetColor]
    for stat, amount in pairs(spec.stats or {}) do
        local maxKey = "max" .. stat:sub(1, 1):upper() .. stat:sub(2)
        target[stat] = math.min(target[maxKey], target[stat] + amount)
    end

    if targetColor == color then
        broadcastEvent("gain", char.name .. " uses the " .. spec.label ..
            ": " .. describeItemEffect(spec) .. ".")
    else
        broadcastEvent("gain", char.name .. " uses the " .. spec.label .. " on " ..
            target.name .. ": " .. describeItemEffect(spec) .. ".")
    end
    safecall(function() recordUsage("items", spec.label) end, "Usage")
    safecall(function() refreshStatDisplay() end, "Stats")
    return true
end
