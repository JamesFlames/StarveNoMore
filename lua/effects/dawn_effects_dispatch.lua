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
    P1_PHONES_DEAD      = { "Every player discards 1 Battery (if held)." },
    P1_FRESH_FOOD       = { "Add 2 Food to Ellie & Luca's House resource bag." },
    P1_SCHOOL_CLOSED    = { "Move every standee at the Basketball Court to an adjacent tile." },
    P1_OLD_FRIEND_VISIT = { "Choose one player: +2 Sanity (use their +S button)." },
    P1_BIKE_FOUND       = { "One player at a sport court may take the Bicycle token." },
    P1_GARDEN_GROWS     = { "Add 1 Food to every house tile's resource area." },
    P1_SOMETHING_WATCHED = { "Optional DARE: the watched player may lose 1 more Sanity (-S button) to peek at the top Threat card." },
    P1_STRANGE_RADIO    = { "Anyone who rolled a 6: peek at the Market deck for a Clue.",
                            "Optional DARE: spend 2 Battery to peek the next 3 Dawn cards (host: draw + show + return in order)." },
    P1_PHOTO_FOUND      = { "Choose one player: +1 Sanity and peek at the top Threat card." },
    P2_FOOD_SPOILS      = { "Every player discards 1 Food.",
                            "Optional DARE: eat it anyway — announce it: +2 Hunger and -1 Health instead of discarding." },
    P2_VISITOR          = { "Resolve the revealed Visitor card's instructions." },
    P2_SUPPLY_DROP      = { "Add 1 Metal + 1 Cloth to the nearest house tile.",
                            "Draw 1 Threat at that house tile." },
    P2_MIRROR_CRACK     = { "Every player discards 1 Battery (if held)." },
    P3_POWER_OUT        = { "Return all Battery tokens to the supply." },
    P3_FRIEND_CHANGED   = { "Player to your left: -2 Sanity and reveals one Item." },
    P3_TRUTH_GLIMPSE    = { "Search the Market deck for a Clue card; reveal it face-up (claimable Day 6+)." },
    P3_WALLS_CLOSE      = { "If a house holds more than its capacity, excess players move now." },
    P3_ALLY_MISSING     = { "Player with fewest items: discard all items, move their standee to a random tile." },
    P3_OFFERING         = { "Team choice: sacrifice 3 Food for Doom -2, OR everyone loses 1 Sanity." },
    P3_EYE_SPLITS       = { "Place 3 Terror Beak threat cards at tiles adjacent to the Eye." },
    P4_SACRIFICE_OPTION = { "Optional: one player may go Down to reduce Doom by 5." },
    P4_GROUND_SPLITS    = { "Destroy a random location tile; players there flee; its resources are lost." },
    P4_LAST_MEAL        = { "Remove all Food tokens from every location." },
    P4_ALL_TOGETHER     = { "Vote on a tile; move all standees there." },
    P4_BARGAIN          = { "Choose a negotiator: roll d6 — 4+: Doom -3; 1-3: they go Down." },
}

-----------------------------------------------------------------------
-- Dispatch entry point (called from day_loop.lua -> revealDawnCard)
-----------------------------------------------------------------------
function dispatchDawnEffect(card)
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
    local id = nil
    if card.getTags then
        for _, tag in ipairs(card.getTags()) do
            if DAWN_EFFECTS[tag] then id = tag; break end
        end
    end
    if not id then
        id = (card.getNickname() or ""):match("^%s*(.-)%s*$") or ""
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
