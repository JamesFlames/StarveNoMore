-- dawn_effects_phase1.lua — Phase 1 (Dusk of the Week) Dawn card effects.
-- Adds entries to the DAWN_EFFECTS table declared in dawn_effects.lua and
-- uses its chunk-local helpers (allPlayersLose etc.); loads after it.

-----------------------------------------------------------------------
-- Phase 1: Dusk of the Week
-----------------------------------------------------------------------
DAWN_EFFECTS["P1_QUIET_EVENING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A quiet evening. No effect.")
    end,
}

DAWN_EFFECTS["P1_LIGHTS_FLICKER"] = {
    -- Dare (design_batch3.md §2): the court floodlights are on all night.
    -- Opt in by sleeping at a court: +2 Threats there, 2 Market cards at Dawn
    -- for survivors (paid out beside Moonlit Salvage in BeginDay).
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.dareCourtGlow = true
        broadcastEvent("warn", "DARE: the court floodlights glow all night. Sleep at a sport court — it draws +2 extra Threats, but survivors claim 2 Market cards at Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.dareCourtGlow = nil
    end,
}

DAWN_EFFECTS["P1_PHONES_DEAD"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Phones are dead. All players discard 1 Battery (if held).")
        -- Resource discard is manual in this phase; broadcast the instruction
    end,
}

DAWN_EFFECTS["P1_SOMETHING_WATCHED"] = {
    onReveal = function(card)
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.max(0, target.sanity - 1)
            broadcastEvent("damage", target.name .. " (lowest Sanity) loses 1 more Sanity.")
        end
    end,
}

DAWN_EFFECTS["P1_FRESH_FOOD"] = {
    onReveal = function(card)
        broadcastEvent("gain", "2 Food added to Ellie & Luca's House resource bag.")
        -- Physical token spawn would be handled by a resource-bag helper in Phase G
    end,
}

DAWN_EFFECTS["P1_NEIGHBORHOOD_QUIET"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.noHouseThreats = true
        broadcastEvent("proc", "No threats spawn at house tiles tonight. Charlie checks ignore the Basketball Court until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.noHouseThreats = nil
    end,
}

DAWN_EFFECTS["P1_SCHOOL_CLOSED"] = {
    onReveal = function(card)
        broadcastEvent("proc", "School is closed! Move all standees at the Basketball Court to an adjacent tile.")
        -- Physical movement is manual; broadcast instruction
    end,
}

DAWN_EFFECTS["P1_OLD_FRIEND_VISIT"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An old friend calls. Choose one player — they gain +2 Sanity.")
        -- Player choice is manual
    end,
}

DAWN_EFFECTS["P1_BREEZE"] = {
    onReveal = function(card)
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local loc = char.location or ""
                if loc:find("Court") or loc:find("Badminton") or loc:find("Basketball") then
                    char.hunger = math.max(0, char.hunger - 1)
                    broadcastEvent("damage", char.name .. " at a sport court loses 1 Hunger from the breeze.")
                end
            end
        end
    end,
}

DAWN_EFFECTS["P1_STRAY_CAT"] = {
    onReveal = function(card)
        local highest, target = -1, nil
        for color, char in pairs(gameState.activeChars) do
            if not char.down and char.sanity > highest then
                highest = char.sanity
                target = char
            end
        end
        if target then
            gameState.ongoingDawnEffects.strayCat = target.name
            broadcastEvent("gain", "A stray cat follows " .. target.name .. " (+1 Sanity at Tick while it stays).")
            broadcastEvent("proc", "If " .. target.name .. " takes damage, the cat flees.")
        end
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.strayCat = nil
    end,
}

DAWN_EFFECTS["P1_BIKE_FOUND"] = {
    onReveal = function(card)
        broadcastEvent("gain", "Someone left a bicycle! One player at a sport court may take the Bicycle token (Move costs 0 Hunger).")
    end,
}

DAWN_EFFECTS["P1_GARDEN_GROWS"] = {
    onReveal = function(card)
        broadcastEvent("gain", "The garden still grows. Add 1 Food to every house tile's resource area.")
    end,
}

DAWN_EFFECTS["P1_STRANGE_RADIO"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A strange radio signal. All players roll d6.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 6)
                if roll == 6 then
                    broadcastEvent("gain", char.name .. " rolls 6 — peek at Market deck for a Clue card!")
                elseif roll == 1 then
                    char.sanity = math.max(0, char.sanity - 1)
                    broadcastEvent("damage", char.name .. " rolls 1 — loses 1 Sanity.")
                else
                    broadcastEvent("proc", char.name .. " rolls " .. roll .. " — no effect.")
                end
            end
        end
    end,
}

DAWN_EFFECTS["P1_PHOTO_FOUND"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An old photograph. Choose one player — they gain +1 Sanity and may peek at the top Threat card.")
    end,
}

DAWN_EFFECTS["P1_RUMOR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A rumor on the street. Reveal the next Dawn card, then place it back on top.")
        local phase = gameState.phase
        local deck = getPhaseDeck(phase)
        if deck and deck.getQuantity and deck.getQuantity() > 0 then
            deck.takeObject({
                position = deck.getPosition() + Vector(5, 2, 0),
                rotation = {0, 180, 0},
                smooth   = true,
                callback_function = function(peeked)
                    local name = peeked.getNickname() or "???"
                    broadcastEvent("proc", "Peeked: " .. name .. ". Returning to top of deck.")
                    Wait.time(function()
                        deck.putObject(peeked)
                    end, 3.0)
                end
            })
        end
    end,
}

