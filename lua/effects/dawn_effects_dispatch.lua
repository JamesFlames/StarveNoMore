-- dawn_effects_dispatch.lua — anti-stacking Dawn cards, the DAWN_MANUAL_STEPS
-- checklist table, and dispatchDawnEffect (the entry point called from
-- day_loop.lua). Loads last among the dawn_effects parts.

-----------------------------------------------------------------------
-- Anti-stacking Dawn cards: the thing outside notices crowds.
-----------------------------------------------------------------------
local function mostPopulatedLocations()
    local pops = {}
    local maxPop = 0
    for _, char in pairs(gameState.activeChars) do
        if not char.down and char.location then
            pops[char.location] = (pops[char.location] or 0) + 1
            if pops[char.location] > maxPop then maxPop = pops[char.location] end
        end
    end
    local locs = {}
    for loc, n in pairs(pops) do
        if n == maxPop and maxPop >= 2 then table.insert(locs, loc) end
    end
    return locs, maxPop
end

DAWN_EFFECTS["P2_DRAWN_TO_CROWDS"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.crowdThreat = true
        broadcastEvent("warn", "ONGOING: Tonight, the most-populated location draws +1 Threat. It has learned where you gather.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.crowdThreat = nil
    end,
}

DAWN_EFFECTS["P3_HUNTS_THE_HERD"] = {
    onReveal = function(card)
        local locs = mostPopulatedLocations()
        if #locs == 0 then
            broadcastEvent("proc", "Everyone is scattered — it circles, finding no herd. No effect.")
        else
            for _, loc in ipairs(locs) do
                for _, char in pairs(gameState.activeChars) do
                    if not char.down and char.location == loc then
                        char.sanity = math.max(0, char.sanity - 1)
                        broadcastEvent("damage", char.name .. " feels watched at " .. loc .. " — loses 1 Sanity.")
                    end
                end
            end
        end
        gameState.ongoingDawnEffects.crowdThreat = true
        broadcastEvent("warn", "ONGOING: Tonight, the most-populated location draws +1 Threat.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.crowdThreat = nil
    end,
}

-----------------------------------------------------------------------
-- Manual steps per Dawn card — things the script cannot do for the
-- players (physical token moves, group choices, deck searches). These
-- feed the tickable Dawn checklist panel (ui_rules.lua) so instructions
-- don't just scroll away in chat. Cards absent here are fully scripted.
-----------------------------------------------------------------------
DAWN_MANUAL_STEPS = {
    -- (2026-07: most token/deck steps became fully scripted when the
    -- supply and decks moved to the under-table library — discards are
    -- taken automatically, deck searches and peeks resolve themselves.
    -- What remains is genuinely the players': standee moves, hand-card
    -- reveals, and group votes.)
    P1_SCHOOL_CLOSED    = { "Move every standee at the Basketball Court to an adjacent tile." },
    P1_BIKE_FOUND       = { "One player at a sport court claims the bike: announce it — your Moves cost 0 Hunger today." },
    P2_VISITOR          = { "Resolve the revealed Visitor card's instructions." },
    P3_FRIEND_CHANGED   = { "The named player: show the table one Item from your hand." },
    P3_WALLS_CLOSE      = { "If a house holds more than its capacity, excess players move now." },
    P3_ALLY_MISSING     = { "Player with fewest items: discard all items, move their standee to a random tile." },
    P4_SACRIFICE_OPTION = { "Optional: one player may go Down to reduce Doom by 5." },
    P4_GROUND_SPLITS    = { "Destroy a random location tile; players there flee; its resources are lost." },
    P4_LAST_MEAL        = { "Remove all Provisions tokens from every location." },
    P4_ALL_TOGETHER     = { "Vote on a tile; move all standees there." },
    P4_BARGAIN          = { "Choose a negotiator: roll d6 — 4+: Doom -3; 1-3: they go Down." },
}

-----------------------------------------------------------------------
-- Dispatch entry point (called from day_loop.lua -> revealDawnCard)
-----------------------------------------------------------------------
function dispatchDawnEffect(card, info)
    -- Clean up previous Dawn's ongoing effects
    if gameState.activeDawn and gameState.activeDawn.prevId then
        local prev = DAWN_EFFECTS[gameState.activeDawn.prevId]
        if prev and prev.onCleanup then
            safecall(function() prev.onCleanup() end, "DawnCleanup:" .. gameState.activeDawn.prevId)
        end
    end

    -- Resolve the card's effect ID. Cards are tagged with their CSV id
    -- (e.g. "P1_QUIET_EVENING") by build_save.py; the nickname holds the
    -- display title, so check tags first and fall back to the nickname.
    -- `info` is the snapshot day_loop took while the handle was known good;
    -- `card` may be nil or already destroyed, so it is only a fallback and
    -- every read of it is pcall-guarded.
    local tags = info and info.tags or nil
    if not tags and card then
        pcall(function()
            if card.getTags then tags = card.getTags() end
        end)
    end

    local id = nil
    for _, tag in ipairs(tags or {}) do
        if DAWN_EFFECTS[tag] then id = tag; break end
    end
    if not id then
        local name = (info and info.name) or ""
        if name == "" and card then
            pcall(function() name = card.getNickname() or "" end)
        end
        id = name:match("^%s*(.-)%s*$") or ""
    end

    local handler = DAWN_EFFECTS[id]
    if handler and handler.onReveal then
        safecall(function() handler.onReveal(card) end, "DawnEffect:" .. id)
    else
        broadcastEvent("proc", "No scripted effect for Dawn card: " .. id)
    end

    -- Populate the tickable manual-steps checklist (ui_rules.lua panel).
    gameState.dawnChecklist = {}
    for _, step in ipairs(DAWN_MANUAL_STEPS[id] or {}) do
        table.insert(gameState.dawnChecklist, { text = step, done = false })
    end
    if #gameState.dawnChecklist > 0 then
        broadcastEvent("warn", "This Dawn card needs " .. #gameState.dawnChecklist ..
            " manual step(s) — see the checklist panel (top right). Tick each when done.")
    end
    safecall(function() refreshDawnChecklist() end, "DawnChecklist")

    -- Track for next-dawn cleanup
    if gameState.activeDawn then
        gameState.activeDawn.prevId = id
    end
end
