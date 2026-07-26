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
        broadcastEvent("proc", "Phones are dead. Each player loses 1 Battery (if held) — taken automatically.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down and takeResourceFromPlayer(color, "Battery", 1) > 0 then
                broadcastEvent("damage", char.name .. " loses 1 Battery.")
            end
        end
    end,
}

DAWN_EFFECTS["P1_SOMETHING_WATCHED"] = {
    onReveal = function(card)
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.max(0, target.sanity - 1)
            broadcastEvent("damage", target.name .. " (lowest Sanity) loses 1 more Sanity.")
            -- Dare (scripted — the Threat deck is out of reach): look closer.
            showConfirm("Dare — look closer?",
                target.name .. " may lose 1 MORE Sanity to make out what's watching: the top Threat card is revealed to everyone.",
                function()
                    local ch = lowestStatPlayer("sanity") or target
                    ch.sanity = math.max(0, ch.sanity - 1)
                    broadcastEvent("damage", ch.name .. " stares back. (-1 Sanity, now " .. ch.sanity .. ")")
                    local deck = getThreatDeck()
                    local top = deck and deck.getObjects and deck.getObjects()[1]
                    local name = top and ((top.nickname ~= "" and top.nickname) or top.name) or "???"
                    broadcastEvent("warn", "In the dark: " .. name .. " is the next Threat to come.")
                    safecall(function() recordBeat("dare") end, "Telemetry")
                    refreshPhaseBanner()
                end)
        end
    end,
}

DAWN_EFFECTS["P1_FRESH_FOOD"] = {
    onReveal = function(card)
        broadcastEvent("gain", "Fresh food! 2 Food appear at Ellie & Luca's House.")
        safecall(function() spawnResourceAtTile("EllieLucaHouse", "Food", 2) end, "FreshFood")
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
        -- Scripted default: the call goes to whoever needs it most.
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.min(target.maxSanity, target.sanity + 2)
            broadcastEvent("gain", "An old friend calls " .. target.name ..
                " (lowest Sanity): +2 Sanity. (Now " .. target.sanity .. ")")
        else
            broadcastEvent("proc", "An old friend calls... but nobody picks up.")
        end
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
        broadcastEvent("gain", "The garden still grows. 1 Food appears at every house.")
        safecall(function()
            for _, house in ipairs({"JamesHouse", "RaymanHouse", "EllieLucaHouse"}) do
                spawnResourceAtTile(house, "Food", 1)
            end
        end, "GardenGrows")
    end,
}

DAWN_EFFECTS["P1_STRANGE_RADIO"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A strange radio signal. All players roll d6.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 6)
                if roll == 6 then
                    -- Scripted peek (the Market deck is out of reach):
                    -- privately learn how deep the nearest Clue sits.
                    broadcastEvent("gain", char.name .. " rolls 6 — the static whispers about a Clue...")
                    safecall(function()
                        local deck = getMarketDeck()
                        local msg = "The signal fades — no Clue left in the Market deck."
                        if deck and deck.getObjects then
                            for i, o in ipairs(deck.getObjects()) do
                                local nick = (o.nickname ~= "" and o.nickname) or o.name or ""
                                if nick:find("Clue") then
                                    msg = "The radio whispers: " .. nick .. " is " .. i ..
                                        " card(s) down the Market deck. Tell the team — or don't."
                                    break
                                end
                            end
                        end
                        printToColor(msg, color, {0.5, 1, 0.5})
                    end, "RadioClue")
                elseif roll == 1 then
                    char.sanity = math.max(0, char.sanity - 1)
                    broadcastEvent("damage", char.name .. " rolls 1 — loses 1 Sanity.")
                else
                    broadcastEvent("proc", char.name .. " rolls " .. roll .. " — no effect.")
                end
            end
        end
        -- Dare (scripted): decode the rest of the broadcast.
        showConfirm("Dare — decode the signal?",
            "Spend 2 Battery and the next 3 Dawn cards are announced to everyone. " ..
            "(Paid automatically by whoever holds them.)",
            function()
                -- Charge the 2 Battery for real — resources are virtual and
                -- auto-paid now, so nothing is left to the honor system.
                -- Any player who holds enough can foot the bill.
                local payer = nil
                for c, ch in pairs(gameState.activeChars) do
                    if not ch.down and (getPlayerResources(c).Battery or 0) >= 2 then
                        payer = c; break
                    end
                end
                if not payer then
                    broadcastEvent("damage", "Nobody has 2 Battery to spare — the signal stays noise.")
                    return
                end
                if not verifyAndPayResources(payer, { Battery = 2 }, "decoding the signal") then return end

                local deck = getPhaseDeck(gameState.phase)
                local names = {}
                if deck and deck.getObjects then
                    for i, o in ipairs(deck.getObjects()) do
                        if i > 3 then break end
                        table.insert(names, (o.nickname ~= "" and o.nickname) or o.name or "???")
                    end
                end
                if #names > 0 then
                    broadcastEvent("warn", "The signal decodes. Coming Dawns: " .. table.concat(names, "  >  "))
                else
                    broadcastEvent("proc", "The signal decodes into static — nothing left in this phase's deck.")
                end
                safecall(function() recordBeat("dare") end, "Telemetry")
            end)
    end,
}

DAWN_EFFECTS["P1_PHOTO_FOUND"] = {
    onReveal = function(card)
        -- Scripted default: comfort goes to whoever needs it most, and the
        -- photo's warning is read out for everyone.
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.min(target.maxSanity, target.sanity + 1)
            broadcastEvent("gain", "An old photograph steadies " .. target.name ..
                " (lowest Sanity): +1 Sanity. (Now " .. target.sanity .. ")")
        end
        local deck = getThreatDeck()
        local top = deck and deck.getObjects and deck.getObjects()[1]
        if top then
            local name = (top.nickname ~= "" and top.nickname) or top.name or "???"
            broadcastEvent("warn", "Something in the photo's background: " .. name .. " is the next Threat to come.")
        end
    end,
}

DAWN_EFFECTS["P1_RUMOR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A rumor on the street. Reveal the next Dawn card, then place it back on top.")
        local phase = gameState.phase
        local deck = getPhaseDeck(phase)
        if deck and deck.getQuantity and deck.getQuantity() > 0 then
            deck.takeObject({
                -- Fixed board spot (the deck lives in the under-table library)
                position = {-7.5, 2.5, 7},
                rotation = {0, 180, 0},
                smooth   = true,
                callback_function = function(peeked)
                    -- pcall: a drawn card can arrive as a dead handle (merged
                    -- at the reveal spot) — see docs/tts-interface.md.
                    pcall(function()
                        broadcastEvent("proc", "Peeked: " .. (peeked.getNickname() or "???") ..
                            ". Returning to top of deck.")
                        Wait.time(function() pcall(function() deck.putObject(peeked) end) end, 3.0)
                    end)
                end
            })
        end
    end,
}

