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
        -- Terror Beaks are threat cards; manual placement (Dawn checklist)
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
        broadcastEvent("warn", "Power goes out! All Battery tokens returned to supply.")
        gameState.ongoingDawnEffects.charlieEverywhere = true
        broadcastEvent("warn", "ONGOING: Charlie checks affect every location tonight.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.charlieEverywhere = nil
    end,
}

DAWN_EFFECTS["P3_FRIEND_CHANGED"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Your friend looks wrong. The player to your left loses 2 Sanity and reveals one Item.")
        -- Manual resolution; the "left" direction depends on seating
    end,
}

DAWN_EFFECTS["P3_TRUTH_GLIMPSE"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A glimpse of the truth. Search the Market deck for a Clue card and reveal it face-up.")
        broadcastEvent("warn", "If found, the Clue cannot be claimed until Day 6.")
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
        broadcastEvent("proc", "An offering at the door. CHOOSE: Sacrifice 3 Food to reduce Doom by 2, OR ignore it and all players lose 1 Sanity.")
        -- Manual resolution — players decide together
    end,
}

