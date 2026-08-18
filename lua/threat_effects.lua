-- threat_effects.lua — resolving Soft threats (Design §11.4 step 2).
--
-- A Soft threat is the one-shot kind: it lands, it does something, it goes
-- away. `drawThreatsAt` has always announced exactly that — "X is a soft
-- threat — resolves and discards" — and then did neither. The consequences
-- compounded, because an unresolved Soft card is not merely inert:
--
--   * it has hp = 0, so `fightTargetsAt` filters it out — unfightable;
--   * nothing else removes it, so it sits on the tile for the rest of the week;
--   * and `countFesteringThreats` counts every ThreatCard near a tile, so it
--     charged +1 Doom at every single Dawn, for ever, with no counterplay.
--
-- Twenty cards, each with a printed effect that never happened, each becoming
-- permanent Doom pressure instead. Resolving them is the fix; discarding them
-- is most of it.
--
-- SOFT_THREAT_EFFECTS[id] = function(location, name) — applies the card's
-- printed effect. Cards absent from the table still get discarded; the ones
-- that need a decision at the table announce that instead (MANUAL_SOFT).

-- Where a resolved Soft threat goes. West of the trophy pile (defeated
-- threats, combat_resolve.lua) so the kill count stays readable as a kill
-- count — these were weathered, not beaten.
local SOFT_DISCARD_POS = { -13.5, 1.5, 10.8 }

-- A threat card's CSV id, read off its tags. Every threat card the build
-- emits carries one, and it is the key into THREAT_STATS, THREAT_TYPE_BY_ID,
-- SOFT_THREAT_EFFECTS, PERSISTENT_THREAT_RULES and HARD_THREAT_SPECIALS —
-- so every caller that wants a card's row starts here. Nil for a hand-made
-- card with no id tag; each caller falls back on the nickname.
function threatIdOf(card)
    local id = nil
    pcall(function()
        for _, tag in ipairs(card.getTags() or {}) do
            if THREAT_STATS[tag] then id = tag; return end
        end
    end)
    return id
end

-- Everyone standing at `loc`.
local function _atTile(loc)
    local out = {}
    for color, ch in pairs(gameState.activeChars) do
        if not ch.down and ch.location == loc then out[#out + 1] = color end
    end
    return out
end

local function _loseAtTile(loc, stat, amount, why)
    for _, color in ipairs(_atTile(loc)) do
        local ch = gameState.activeChars[color]
        ch[stat] = math.max(0, ch[stat] - amount)
        broadcastEvent("damage", ch.name .. " loses " .. amount .. " " .. stat ..
            (why and (" — " .. why) or "") .. ".")
        checkDownState(color)
    end
end

SOFT_THREAT_EFFECTS = {
    T_HOWLING = function()
        allPlayersLose("sanity", 1)
    end,

    T_WHISPERS = function(loc)
        _loseAtTile(loc, "sanity", 1, "the whispering")
    end,

    T_BREATHING = function(loc)
        _loseAtTile(loc, "sanity", 2, "something breathing just out of sight")
    end,

    T_THE_TWIN = function(loc)
        _loseAtTile(loc, "sanity", 3, "you don't have a twin")
    end,

    T_CEILING_DRIP = function(loc)
        _loseAtTile(loc, "health", 1, "you don't look up")
    end,

    T_FURNACE = function()
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and not isSportCourt(ch.location or "") then
                ch.health = math.max(0, ch.health - 1)
                broadcastEvent("damage", ch.name .. " loses 1 Health — the heat indoors is wrong.")
                checkDownState(color)
            end
        end
    end,

    T_VOICES = function()
        -- 1 Sanity per ally standing somewhere else: being apart is the cost.
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down then
                local away = 0
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location ~= ch.location then
                        away = away + 1
                    end
                end
                if away > 0 then
                    ch.sanity = math.max(0, ch.sanity - away)
                    broadcastEvent("damage", ch.name .. " hears them calling from " .. away ..
                        " place(s) they are not — loses " .. away .. " Sanity.")
                    checkDownState(color)
                end
            end
        end
    end,

    T_BUZZING = function()
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down then
                local roll = gameRoll(1, 8)
                local loss = math.ceil(roll / 4)
                ch.sanity = math.max(0, ch.sanity - loss)
                broadcastEvent("damage", ch.name .. " rolls " .. roll .. " → loses " .. loss .. " Sanity.")
                checkDownState(color)
            end
        end
    end,

    T_PHONE_RINGS = function()
        broadcastEvent("proc", "It rings, and rings, and stops. You couldn't bring yourself to answer.")
    end,

    -- The two "your lights don't work tonight" cards ride the flags the night
    -- light check already reads, so they need no machinery of their own.
    T_LIGHTS_OUT = function()
        gameState.ongoingDawnEffects.flashlightsDisabled = true
        broadcastEvent("warn", "Every flashlight dies at once — only Fire counts as light tonight.")
    end,

    T_POWER_FLICKER = function()
        gameState.ongoingDawnEffects.flashlightsDisabled = true
        broadcastEvent("warn", "The power stutters — anything Battery-powered is dead tonight.")
    end,

    T_FIRE_OUT = function()
        gameState.ongoingDawnEffects.fireDisabled = true
        broadcastEvent("warn", "Every flame gutters out — Fire is no light at all tonight.")
    end,

    T_MOTH_CLOUD = function(loc)
        gameState.ongoingDawnEffects.flashlightsDisabled = true
        gameState.ongoingDawnEffects.fireDisabled = true
        broadcastEvent("warn", "They come off the walls in a sheet at " .. loc ..
            " — every light is smothered tonight.")
    end,

    T_FOOD_GONE_WRONG = function(loc)
        for _, color in ipairs(_atTile(loc)) do
            local took = takeResourceFromPlayer(color, "Provisions", 1)
            if took > 0 then
                broadcastEvent("damage", gameState.activeChars[color].name ..
                    " loses 1 Provisions — it had turned.")
            end
        end
    end,

    -- The card used to read "the player at the front-most house tile", and
    -- there is no front on this map — five tiles in a ring, no near edge, no
    -- reading order. It was in MANUAL_SOFT telling the table to "agree which
    -- house that is", which is not a rule, it is an argument; a player asked
    -- what it meant and there was no answer to give them.
    -- A doorbell is on a house and everybody indoors hears it, so that is what
    -- it does now: no judgement to make, and it stays in its severity-2 band
    -- next to The Furnace (1 Health at house tiles).
    T_RUNG_DOORBELL = function()
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and not isSportCourt(ch.location or "") then
                ch.sanity = math.max(0, ch.sanity - 1)
                broadcastEvent("damage", ch.name ..
                    " loses 1 Sanity — the doorbell, and nobody at the door.")
                checkDownState(color)
            end
        end
    end,

    T_ROACHES = function()
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == "EllieLucaHouse" then
                if takeResourceFromPlayer(color, "Provisions", 1) > 0 then
                    broadcastEvent("damage", ch.name .. " loses 1 Provisions to the roaches.")
                end
            end
        end
    end,

    -- Tomorrow is shorter. beginDayPhase already knows how to run a reduced
    -- day for P3_LONG_NIGHT; this borrows the same flag.
    T_CLOCK_STOPS = function()
        gameState.ongoingDawnEffects.reducedActions = true
        broadcastEvent("warn", "The clocks stop. Tomorrow ends one action early for everyone.")
    end,
}

-- Cards whose printed effect asks the table for a judgement the script has no
-- basis to make. They still resolve and discard; the instruction is announced
-- so it does not scroll past as flavour. Guarded by tests/test_soft_threats.py.
MANUAL_SOFT = {
    T_LOST_MEMORIES = "The player here discards a random Item card from their hand.",
    T_FRIEND_BLOOD  = "The player here chooses: lose 2 Health to ignore it, or 4 Sanity to walk past.",
    T_ECHO          = "Repeat the last Soft threat this week resolved. If there wasn't one, everyone loses 1 Sanity.",
}

-- Resolve one Soft threat, then take its card off the map. `id` is the CSV id
-- (the card's own tag); `card` may be nil or a dead handle, which is why the
-- effect never touches it.
function resolveSoftThreat(id, location, name, card)
    local label = name or (THREAT_STATS[id] and THREAT_STATS[id].name) or "Something"

    local effect = SOFT_THREAT_EFFECTS[id]
    if effect then
        safecall(function() effect(location, label) end, "SoftThreat:" .. tostring(id))
    end

    local manual = MANUAL_SOFT[id]
    if manual then
        broadcastEvent("warn", label .. " — TABLE STEP: " .. manual)
    elseif not effect then
        -- A Soft card with no entry either way: still discarded, but say so
        -- rather than pretending something happened.
        broadcastEvent("proc", label .. " passes over you. (No scripted effect.)")
    end

    -- Off the map, whatever happened. This is the half that matters most: an
    -- undiscarded Soft card is unfightable AND festers +1 Doom every Dawn.
    if card then
        safecall(function()
            card.setPositionSmooth(Vector(SOFT_DISCARD_POS[1], SOFT_DISCARD_POS[2], SOFT_DISCARD_POS[3]), false, true)
            card.setRotationSmooth({0, 180, 0}, false, true)
        end, "SoftDiscard")
    end
    broadcastEvent("proc", label .. " is spent — its card goes to the discard pile (NW corner).")
end

-- Safety net for a Soft card whose auto-discard (above) never ran — the
-- takeObject callback in drawThreatsAt (night.lua) can miss its landing if
-- the object handle went bad (two cards merging mid-flight) or a reload cut
-- the pending animation off mid-flight. Nothing else ever removes a loose
-- ThreatCard, so a card that slipped through stayed on its tile, unfightable
-- (Soft cards have 0 HP), festering +1 Doom every Dawn for the rest of the
-- week — for a threat whose printed effect had already fired or never will.
--
-- This does NOT re-run SOFT_THREAT_EFFECTS: there is no record of whether the
-- original draw's effect already applied, and firing it twice would be worse
-- than the mess it is cleaning up. It only clears the card off the map, the
-- same half of the job `resolveSoftThreat` calls "the half that matters
-- most." Called once per Dawn, before countFesteringThreats (day_loop.lua).
function sweepStuckSoftThreats()
    local swept = 0
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        -- Only loose, single cards: a merged Deck is a different, already
        -- counted mess (countFesteringThreats), and forcing it apart here
        -- could discard a Hard or Persistent card stacked alongside a Soft
        -- one.
        if obj.type == "Card" and not safeHasTag(obj, "ThreatCardDeck") then
            local ok, tType = pcall(identifyThreatType, obj)
            if ok and tType == "Soft" then
                local name = "A leftover Soft threat"
                pcall(function() name = obj.getNickname() or name end)
                safecall(function()
                    obj.setPositionSmooth(Vector(SOFT_DISCARD_POS[1], SOFT_DISCARD_POS[2], SOFT_DISCARD_POS[3]), false, true)
                    obj.setRotationSmooth({0, 180, 0}, false, true)
                end, "SoftSweep")
                broadcastEvent("warn", name .. " should have discarded when it was drawn and never did — clearing it now so it stops costing Doom.")
                swept = swept + 1
            end
        end
    end
    return swept
end
