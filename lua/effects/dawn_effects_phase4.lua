-- dawn_effects_phase4.lua — Phase 4 (Final Hours) Dawn card effects.
-- Part of dawn_effects (see dawn_effects.lua core).

-----------------------------------------------------------------------
-- Phase 4: Final Hours
-----------------------------------------------------------------------
DAWN_EFFECTS["P4_FINAL_HOURS"] = {
    -- (An earlier draft claimed "ONGOING: Doom rate is now +3 per day" but
    -- never implemented it, and a flat +3 would trample the per-player-count
    -- rates in Design §15.6. The card is now its immediate effect only.)
    onReveal = function(card)
        allPlayersLose("sanity", 2)
        gameState.doom = gameState.doom + 2
        moveDoomMarker(gameState.doom)
        broadcastEvent("warn", "The final hours begin. All players lose 2 Sanity. Doom +2.")
    end,
}

DAWN_EFFECTS["P4_SOURCE_NEAR"] = {
    onReveal = function(card)
        broadcastEvent("warn", "WARNING: Something worse approaches. The Source arrives next Dawn.")
    end,
}

DAWN_EFFECTS["P4_SOURCE_ARRIVES"] = {
    -- No arrival Doom — festering (+2/Dawn) is the boss's bill.
    onReveal = function(card)
        broadcastEvent("warn", "THE SOURCE ARRIVES at the center of the map!")
        gameState.ongoingDawnEffects.sourceActive = true
        -- Persistent boss HP (§12.6): the script tracks the Source's HP from
        -- here on — and at 5 HP it splits (checkSourcePhase, combat.lua).
        gameState.bossHP = gameState.bossHP or {}
        gameState.bossHP.source = SOURCE_MAX_HP or 8
        gameState.sourceSplit = false
        safecall(function() placeBossStandee("TheSource", "EllieLucaHouse") end, "BossPlace")
        broadcastEvent("warn", "ONGOING: The Source is the final boss. It MUST be destroyed before Day 7 ends — while it stands, there is no victory.")
        broadcastEvent("proc", "The Source: HP " .. gameState.bossHP.source ..
            " (script-tracked). At 5 HP it will SPLIT — two Terror Beaks peel off to adjacent tiles.")
        safecall(function() nudgeCameraToBoss("TheSource", "EllieLucaHouse") end, "CameraNudge")
        -- No audio folder for "the_source" yet — Audio.playBossLoop no-ops
        -- when CREATURES[name] is missing, so ambient continues normally.
        safecall(function() Audio.playBossLoop("the_source") end, "Audio")
    end,
}

DAWN_EFFECTS["P4_DESPAIR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Despair. Each player rolls Sanity d8, loses half (round up).")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 8)
                local loss = math.ceil(roll / 2)
                char.sanity = math.max(0, char.sanity - loss)
                broadcastEvent("damage", char.name .. " rolls " .. roll .. " → loses " .. loss .. " Sanity.")
            end
        end
        gameState.ongoingDawnEffects.restNoSanity = true
        broadcastEvent("warn", "ONGOING: Rest restores no Sanity until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.restNoSanity = nil
    end,
}

DAWN_EFFECTS["P4_SACRIFICE_OPTION"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A WAY OUT: Any one player may immediately become Down to reduce Doom by 5. (Optional.)")
        -- Manual resolution
    end,
}

DAWN_EFFECTS["P4_LAST_LIGHTS"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.onlyFireLight = true
        broadcastEvent("warn", "ONGOING: Only Fire is a light source until next Dawn. Batteries/Flashlights disabled.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.onlyFireLight = nil
    end,
}

DAWN_EFFECTS["P4_HOPE_REMAINS"] = {
    onReveal = function(card)
        allPlayersGain("sanity", 1)
        gameState.ongoingDawnEffects.doomReduced = true
        broadcastEvent("gain", "Hope remains. Doom advance reduced by 1 this Dawn only.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.doomReduced = nil
    end,
}

DAWN_EFFECTS["P4_THE_TRUTH"] = {
    onReveal = function(card)
        -- Check if the team has all 3 Clue cards
        local clueCount = gameState.clueCount or 0
        if clueCount >= 3 then
            broadcastEvent("gain", "The team has all 3 Clues! The Truth Trophy flips face-up on the trophy row.")
            local trophy = findOneByTag("TR_TRUTH")
            if trophy then
                trophy.setRotationSmooth({0, 180, 0}, false, true)  -- face up
                trophy.highlightOn("Yellow", 10)
            end
        else
            allPlayersLose("sanity", 2)
            broadcastEvent("damage", "The truth is worse than you imagined. Missing Clues — all lose 2 Sanity.")
        end
    end,
}

DAWN_EFFECTS["P4_ALL_TOGETHER"] = {
    onReveal = function(card)
        broadcastEvent("proc", "All Together. Move all standees to the same tile (player vote).")
        gameState.ongoingDawnEffects.togetherBonus = true
        broadcastEvent("gain", "ONGOING: All players gain +1 Sanity at Tick if sharing a tile with another player.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.togetherBonus = nil
    end,
}

DAWN_EFFECTS["P4_DAWN_BREAKS"] = {
    onReveal = function(card)
        broadcastEvent("gain", "Dawn breaks. Doom does NOT advance this Dawn.")
        gameState.ongoingDawnEffects.noDoomThisDawn = true
        if gameState.day == getTotalDays() then
            broadcastEvent("phase", "The final day — continue to the final Tick. Survival check!")
        end
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.noDoomThisDawn = nil
    end,
}

DAWN_EFFECTS["P4_GROUND_SPLITS"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The ground splits open! A random location tile is destroyed. Players there must flee. Resources there are lost.")
        -- Manual resolution: pick random tile, remove it, relocate players
    end,
}

DAWN_EFFECTS["P4_LAST_MEAL"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The last meal. All Food at every location is destroyed.")
        gameState.ongoingDawnEffects.recipeBonusHunger = true
        broadcastEvent("gain", "Recipes cooked today restore +2 extra Hunger.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.recipeBonusHunger = nil
    end,
}

DAWN_EFFECTS["P4_VOICES_RETURN"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The voices come back. Every player rolls Sanity d8.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 8)
                -- Check if an ally is at the same tile
                local hasAlly = false
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location == char.location then
                        hasAlly = true
                        break
                    end
                end
                local loss = roll
                if hasAlly then
                    loss = math.floor(roll / 2)
                    broadcastEvent("damage", char.name .. " rolls " .. roll .. " (halved with ally) -> loses " .. loss .. " Sanity.")
                else
                    broadcastEvent("damage", char.name .. " rolls " .. roll .. " -> loses " .. loss .. " Sanity.")
                end
                char.sanity = math.max(0, char.sanity - loss)
            end
        end
    end,
}

DAWN_EFFECTS["P4_BARGAIN"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The Source offers a bargain. Choose one player to negotiate.")
        broadcastEvent("warn", "That player rolls d6: on 4+ Doom -3. On 1-3: that player goes Down immediately.")
        -- Manual resolution
    end,
}

DAWN_EFFECTS["P4_MEMORY_FLOOD"] = {
    onReveal = function(card)
        allPlayersGain("sanity", 2)
        allPlayersLose("health", 1)
        broadcastEvent("proc", "A flood of memories. +2 Sanity, -1 Health. The memories are sharp.")
        gameState.ongoingDawnEffects.homeSanityBonus = true
        broadcastEvent("gain", "ONGOING: Players at their own home gain +2 Sanity at sleep instead of +1.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.homeSanityBonus = nil
    end,
}

