-- dawn_effects_phase3.lua — Phase 3 (Long Nights) Dawn card effects.
-- Part of dawn_effects (see dawn_effects.lua core).

-----------------------------------------------------------------------
-- Phase 3: Long Nights
-----------------------------------------------------------------------
DAWN_EFFECTS["P3_LONG_NIGHT"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 2)
        gameState.doom = gameState.doom + 1
        moveDoomMarker(gameState.doom)
        gameState.ongoingDawnEffects.reducedActions = true
        broadcastEvent("warn", "Doom +1. ONGOING: Day phase has only 2 actions per player.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.reducedActions = nil
    end,
}

DAWN_EFFECTS["P3_EYE_NEAR"] = {
    onReveal = function(card)
        broadcastEvent("warn", "WARNING: The Eye of Terror approaches! It arrives next Dawn at a random house tile.")
    end,
}

DAWN_EFFECTS["P3_EYE_ARRIVES"] = {
    -- No arrival Doom — festering (+2/Dawn) is the boss's bill.
    onReveal = function(card)
        local houses = { "JamesHouse", "RaymanHouse", "EllieLucaHouse" }
        local lair = houses[gameRoll(#houses)]
        broadcastEvent("warn", "THE EYE OF TERROR ARRIVES at " .. lair .. "!")
        gameState.ongoingDawnEffects.eyeActive = true
        gameState.eyeLocation = lair
        gameState.bossHP = gameState.bossHP or {}
        gameState.bossHP.eye = BOSS_BASE_STATS["Boss:EyeOfTerror"].hp
        safecall(function() placeBossStandee("EyeOfTerror", lair) end, "BossPlace")
        broadcastEvent("warn", "ONGOING: Each Dawn, draw 1 extra Threat at the Eye's location. It festers Doom +2 each Dawn it stands.")
        broadcastEvent("proc", "Eye of Terror: HP " .. gameState.bossHP.eye .. ", Atk " ..
            BOSS_BASE_STATS["Boss:EyeOfTerror"].attack .. " — Fight it at its tile; the script tracks its HP.")
        safecall(function() nudgeCameraToBoss("EyeOfTerror", lair) end, "CameraNudge")
        safecall(function() Audio.playBossLoop("eye_of_terror") end, "Audio")
    end,
    onCleanup = function()
        if gameState.ongoingDawnEffects.eyeDefeated then
            gameState.ongoingDawnEffects.eyeActive = nil
            gameState.ongoingDawnEffects.eyeDefeated = nil
            safecall(function() Audio.stopBossLoop("eye_of_terror") end, "Audio")
        end
    end,
}

DAWN_EFFECTS["P3_EYE_SPLITS"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The Eye of Terror SPLITS into 3 Terror Beaks at adjacent tiles!")
        gameState.ongoingDawnEffects.eyeActive = nil
        gameState.eyeLocation = nil
        if gameState.bossHP then gameState.bossHP.eye = nil end
        -- The Eye itself is gone — its standee returns to the pool.
        safecall(function() poolBossStandee("EyeOfTerror") end, "BossPool")
        safecall(function() Audio.stopBossLoop("eye_of_terror") end, "Audio")
        -- Terror Beaks: pulled from the Threat deck and placed automatically
        -- at tiles adjacent to where the Eye stood (default: the map hub).
        safecall(function()
            local origin = gameState.eyeLocation or "EllieLucaHouse"
            local spots = {}
            for _, n in ipairs(LOCATION_ADJACENCY[origin] or {"EllieLucaHouse"}) do
                table.insert(spots, n)
            end
            local deck = getThreatDeck()
            if not deck or not deck.getObjects then return end
            local placed = 0
            for _, o in ipairs(deck.getObjects()) do
                local nick = (o.nickname ~= "" and o.nickname) or o.name or ""
                if placed >= 3 then break end
                if nick == "Terror Beak" then
                    placed = placed + 1
                    local loc = spots[((placed - 1) % #spots) + 1]
                    local tile = getLocationTile(loc)
                    local pos = tile and (tile.getPosition() + Vector(2, 1.5, 0.5 + placed * 0.3)) or Vector(0, 2, 0)
                    deck.takeObject({ guid = o.guid, position = pos,
                                      rotation = {0, 180, 0}, smooth = true })
                    broadcastEvent("warn", "A Terror Beak lands at " .. loc .. "!")
                end
            end
            if placed == 0 then
                broadcastEvent("proc", "No Terror Beaks left in the Threat deck — the split fizzles.")
            end
        end, "EyeSplit")
    end,
}

DAWN_EFFECTS["P3_HUNGER_PANG"] = {
    onReveal = function(card)
        allPlayersLose("hunger", 2)
    end,
}

DAWN_EFFECTS["P3_SCREAMS"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.max(0, target.sanity - 2)
            broadcastEvent("damage", target.name .. " (lowest Sanity) loses 2 more Sanity from screams.")
        end
    end,
}

DAWN_EFFECTS["P3_POWER_OUT"] = {
    onReveal = function(card)
        broadcastEvent("warn", "Power goes out! Every Battery token returns to the supply — taken automatically.")
        for color, char in pairs(gameState.activeChars) do
            local n = takeResourceFromPlayer(color, "Battery", 99)
            if n > 0 then
                broadcastEvent("damage", char.name .. " loses " .. n .. " Battery to the outage.")
            end
        end
        gameState.ongoingDawnEffects.charlieEverywhere = true
        broadcastEvent("warn", "ONGOING: Charlie checks affect every location tonight.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.charlieEverywhere = nil
    end,
}

DAWN_EFFECTS["P3_FRIEND_CHANGED"] = {
    onReveal = function(card)
        -- Scripted: one random standing character takes the hit (physical
        -- seating order isn't knowable to the script); the reveal is theirs.
        local standing = {}
        for _, c in ipairs(gameState.turnOrder or {}) do
            local ch = gameState.activeChars[c]
            if ch and not ch.down then table.insert(standing, ch) end
        end
        local target = #standing > 0 and standing[gameRoll(1, #standing)] or nil
        if target then
            target.sanity = math.max(0, target.sanity - 2)
            broadcastEvent("damage", target.name .. "'s friend looks wrong: -2 Sanity (now " ..
                target.sanity .. "). " .. target.name .. ": show the table one Item from your hand.")
        end
    end,
}

DAWN_EFFECTS["P3_TRUTH_GLIMPSE"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A glimpse of the truth. Searching the Market deck for a Clue card...")
        local deck = getMarketDeck()
        local found = false
        if deck and deck.getObjects then
            for _, o in ipairs(deck.getObjects()) do
                local nick = (o.nickname ~= "" and o.nickname) or o.name or ""
                if nick:find("Clue") then
                    found = true
                    -- Revealed face-up below the Market display column.
                    deck.takeObject({ guid = o.guid, position = {-12.5, 1.5, -9},
                                      rotation = {0, 180, 0}, smooth = true })
                    broadcastEvent("gain", "Revealed: " .. nick .. " — face-up under the Market display.")
                    broadcastEvent("warn", "The Clue cannot be claimed until Day 6.")
                    break
                end
            end
        end
        if not found then
            broadcastEvent("proc", "No Clue cards left in the Market deck.")
        end
    end,
}

DAWN_EFFECTS["P3_LULL"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The calm before... No immediate effect.")
        gameState.ongoingDawnEffects.charliePaused = true
        broadcastEvent("gain", "ONGOING: All Charlie checks are paused until next Dawn. Gather while you can!")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.charliePaused = nil
    end,
}

DAWN_EFFECTS["P3_GRAVITY_WRONG"] = {
    onReveal = function(card)
        allPlayersLose("health", 1)
        gameState.ongoingDawnEffects.moveCostPlus1 = true
        gameState.ongoingDawnEffects.restNoHealth = true
        broadcastEvent("warn", "Gravity feels wrong. Movement costs +1 action this day.")
        broadcastEvent("warn", "ONGOING: Rest restores no Health until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.moveCostPlus1 = nil
        gameState.ongoingDawnEffects.restNoHealth = nil
    end,
}

DAWN_EFFECTS["P3_TIME_SKIP"] = {
    onReveal = function(card)
        gameState.day = math.min(getTotalDays(), gameState.day + 1)
        gameState.doom = gameState.doom + 1
        moveDoomMarker(gameState.doom)
        allPlayersLose("hunger", 1)
        broadcastEvent("warn", "You lost a day! Day counter advances by 1. Doom +1. All players lose 1 Hunger.")
    end,
}

DAWN_EFFECTS["P3_WALLS_CLOSE"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.reducedCapacity = true
        broadcastEvent("warn", "The walls are closer. Each house tile loses 1 character capacity (max 4).")
        broadcastEvent("proc", "Excess players must move at Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.reducedCapacity = nil
    end,
}

DAWN_EFFECTS["P3_ALLY_MISSING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "One of you was gone this morning. The player with the fewest items loses all items and reappears at a random tile.")
        gameState.ongoingDawnEffects.missingAllyBonus = true
        broadcastEvent("gain", "ONGOING: That player gets +1 action this day (adrenaline).")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.missingAllyBonus = nil
    end,
}

DAWN_EFFECTS["P3_OFFERING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An offering at the door. CHOOSE: sacrifice 3 Food (taken from the team's boards) for Doom -2, OR ignore it and everyone loses 1 Sanity.")
        showConfirm("The Offering",
            "Sacrifice 3 Food (taken automatically from the team's boards) to reduce Doom by 2?\n\nCancel: refuse — every player loses 1 Sanity.",
            function()
                -- Pool the payment across the whole team, in turn order.
                local need = 3
                for _, c in ipairs(gameState.turnOrder or {}) do
                    if need <= 0 then break end
                    need = need - takeResourceFromPlayer(c, "Food", need)
                end
                if need > 0 then
                    broadcastEvent("damage", "The team can't scrape 3 Food together — the offering is refused. Everyone loses 1 Sanity.")
                    allPlayersLose("sanity", 1)
                else
                    gameState.doom = math.max(0, gameState.doom - 2)
                    moveDoomMarker(gameState.doom)
                    broadcastEvent("gain", "The offering is accepted: 3 Food given, Doom -2 (now " ..
                        gameState.doom .. " / " .. getDoomLimit() .. ").")
                end
                refreshPhaseBanner()
            end,
            function()
                broadcastEvent("damage", "The offering is refused. Every player loses 1 Sanity.")
                allPlayersLose("sanity", 1)
                refreshPhaseBanner()
            end)
    end,
}

