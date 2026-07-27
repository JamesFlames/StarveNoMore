-- tick_victory.lua  (F.6 Tick + F.10 Victory/Defeat + F.11 Cleanse + F.13 Down/Ghost)
-- Design §11.5 (Tick), §16 (Victory/Defeat/Down)

-----------------------------------------------------------------------
-- F.6 — TICK (end-of-day decay)
-- Design §11.5: Every character loses 1 Hunger and 1 Sanity.
-----------------------------------------------------------------------
function resolveTick()
    gameState.subPhase = "Tick"
    safecall(function() setPhaseMood("Tick") end, "Mood")
    safecall(function() Audio.playChime() end, "Audio")
    broadcastEvent("phase", "--- TICK (End of Day " .. gameState.day .. ") ---")

    -- Calming Presence (§6.2): allies sharing Coco's tile lose 1 less
    -- Sanity at Tick (minimum 0). Resolved once, before the decay loop.
    local cocoLocation = nil
    for _, char in pairs(gameState.activeChars) do
        if char.name == "Coco" and not char.down then
            cocoLocation = char.location
            break
        end
    end

    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            -- Base tick: -1 Hunger, -1 Sanity
            local hungerLoss = 1
            local sanityLoss = 1

            -- Rayman's Big Appetite: -2 Hunger instead of -1.
            -- 3-player relief (§20.1, batch 4 W2): with only three characters
            -- absorbing his overheads, the big appetite only bites on days he
            -- earned it — fought, or moved 2+ tiles. A quiet day costs 1.
            if char.name == "Rayman" then
                hungerLoss = 2
                if gameState.playerCount == 3 and not gameState.raymanFoughtToday
                    and (gameState.raymanTilesMovedToday or 0) < 2 then
                    hungerLoss = 1
                    broadcastEvent("proc", "Rayman had a quiet day — Big Appetite eases to -1 Hunger (3-player relief).")
                end
            end

            -- Winter scenario: hunger decay doubled
            local flags = gameState.scenarioFlags or {}
            if flags.hungerDecayX2 then
                hungerLoss = hungerLoss * 2
            end

            -- Doom 20 threshold: +1 Sanity loss
            if gameState.ongoingDawnEffects.doom20 then
                sanityLoss = sanityLoss + 1
            end

            -- Calming Presence (§6.2): sharing Coco's tile softens the night.
            if cocoLocation and char.name ~= "Coco" and char.location == cocoLocation
                and sanityLoss > 0 then
                sanityLoss = sanityLoss - 1
                broadcastEvent("gain", char.name .. " loses 1 less Sanity beside Coco (Calming Presence).")
            end

            -- "All Together" bonus: +1 Sanity if sharing tile
            if gameState.ongoingDawnEffects.togetherBonus then
                local othersHere = 0
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location == char.location then
                        othersHere = othersHere + 1
                    end
                end
                if othersHere > 0 then
                    sanityLoss = math.max(0, sanityLoss - 1)
                    broadcastEvent("gain", char.name .. " gains comfort from allies nearby (All Together).")
                end
            end

            char.hunger = math.max(0, char.hunger - hungerLoss)
            char.sanity = math.max(0, char.sanity - sanityLoss)

            broadcastEvent("proc", char.name .. ": -" .. hungerLoss .. " Hunger, -" .. sanityLoss .. " Sanity. " ..
                "Now H:" .. char.health .. " Hu:" .. char.hunger .. " S:" .. char.sanity)

            -- Hunger 0: lose 1 Health (starvation)
            if char.hunger <= 0 then
                char.health = math.max(0, char.health - 1)
                broadcastEvent("damage", char.name .. " is starving! Loses 1 Health.")
            end

            -- James's Wired constraint: if he didn't consume an Energy Drink, -2 Sanity
            -- (Tracked via flag set by the Energy Drink consumption action)
            if char.name == "James" and not gameState.jamesEnergyDrinkUsed then
                char.sanity = math.max(0, char.sanity - 2)
                broadcastEvent("damage", "James didn't get his Energy Drink — loses 2 Sanity (Wired).")
            end

            -- All-Nighter crash (Signature, §6.7): the extra actions get billed now.
            local pendingSanity = (gameState.pendingSanityPenalty or {})[color]
            if pendingSanity then
                char.sanity = math.max(0, char.sanity - pendingSanity)
                gameState.pendingSanityPenalty[color] = nil
                broadcastEvent("damage", char.name .. " crashes after the All-Nighter — loses " ..
                    pendingSanity .. " Sanity. (Now " .. char.sanity .. ")")
            end

            -- Low stat threshold effects (Design §10.1)
            if char.health > 0 and char.health < 3 then
                broadcastEvent("warn", char.name .. " is critically injured (Health < 3). Movement costs +1 action.")
            end
            if char.hunger > 0 and char.hunger < 3 then
                broadcastEvent("warn", char.name .. " is starving (Hunger < 3). Cannot fight or use [Effort] actions — but may always Flee (1 tile, and free while any stat is below 3).")
            end
            if char.sanity > 0 and char.sanity < 3 then
                broadcastEvent("warn", char.name .. " is losing grip on reality (Sanity < 3). Haunted: draws a personal Threat at next Dawn that allies can't help with.")
            end

            checkDownState(color)
        end
    end

    -- Charlie streak: a night without an attack resets her interest.
    for color, char in pairs(gameState.activeChars) do
        if char.charlieHitTonight then
            char.charlieHitTonight = nil
        else
            char.charlieStreak = 0
        end
    end

    -- Reset daily flags
    gameState.jamesEnergyDrinkUsed = false
    gameState.pendingSanityPenalty = {}   -- any crash owed by a Down character is moot

    -- Check victory/defeat
    if checkDefeat() then
        refreshPhaseBanner()
        return
    end
    if checkVictory() then
        refreshPhaseBanner()
        return
    end

    -- Show end-of-round summary (I.4)
    safecall(function() showEndOfDaySummary() end, "Summary")

    -- The day is on the chronicle now, so the day-count achievements can see
    -- it. (Game-over runs its own check from showWeekInReview.)
    safecall(function() checkAchievements("dayEnd") end, "Achievements")

    -- Advance to next day
    gameState.day = gameState.day + 1
    gameState.subPhase = "PreDawn"
    refreshPhaseBanner()
    refreshDynamicTooltips()
    broadcastEvent("phase", "Day " .. (gameState.day - 1) .. " complete. Click 'Begin Day' to start Day " .. gameState.day .. ".")
end

-----------------------------------------------------------------------
-- F.13 — Down / Ghost state
-----------------------------------------------------------------------
-----------------------------------------------------------------------
-- Character-specific death narrations
-----------------------------------------------------------------------
DEATH_NARRATIONS = {
    James = {
        health = "James's screen glows, but he doesn't see it anymore. The headphones play static to no one.",
        sanity = "James stares at his hands, opening and closing them. He can't remember what buttons do.",
    },
    Coco = {
        health = "Coco folds gently, like a paper crane in rain. The blanket settles around her, empty.",
        sanity = "Coco smiles at something none of you can see. She hasn't blinked in a very long time.",
    },
    Rayman = {
        health = "The biggest one of you falls first. The ground shakes. Then nothing.",
        sanity = "Rayman throws the basketball at the wall. Again. Again. Again. He won't stop.",
    },
    Ellie = {
        health = "The crockpot boils over. Nobody turns it off. Ellie's apron is on the floor.",
        sanity = "Ellie is cooking something. You don't ask what. You don't want to know the recipe.",
    },
    Luca = {
        health = "Luca's notebook falls open. The last page is just one word, written smaller and smaller.",
        sanity = "Luca is still talking. Perfect sentences. Perfect grammar. None of it means anything anymore.",
    },
}

function checkDownState(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    local wentDown = false
    if char.health <= 0 then
        char.down = true
        char.health = 0
        local narration = DEATH_NARRATIONS[char.name] and DEATH_NARRATIONS[char.name].health
        if narration then
            broadcastEvent("damage", narration)
        end
        broadcastEvent("damage", char.name .. " is DOWN. Flip standee to ghost side.")
        broadcastEvent("proc", char.name .. " cannot act, cannot gather, cannot fight. Ghost drifts 1 free move/round.")
        wentDown = true
    elseif char.sanity <= 0 then
        char.down = true
        char.sanity = 0
        local narration = DEATH_NARRATIONS[char.name] and DEATH_NARRATIONS[char.name].sanity
        if narration then
            broadcastEvent("damage", narration)
        end
        broadcastEvent("damage", char.name .. " is LOST. Flip standee to ghost side.")
        broadcastEvent("proc", char.name .. " cannot act. Ghost drifts. One whispered word per round.")
        wentDown = true
    end

    if wentDown then
        safecall(function() Audio.playDeath() end, "Audio")
        safecall(function() ensureChronicle().downs = ensureChronicle().downs + 1 end, "Chronicle")

        -- A fallen friend feeds the dark: Doom +1 (Design §16.4)
        gameState.doom = math.min(getDoomLimit(), gameState.doom + 1)
        safecall(function() moveDoomMarker(gameState.doom) end, "DoomMarker")
        broadcastEvent("warn", char.name .. " falling feeds the dark — Doom +1 (now " .. gameState.doom .. " / " .. getDoomLimit() .. ").")
        safecall(function() checkDoomThresholds() end, "DoomThresholds")

        -- Auto-broadcast revival hint to the team (once per character per day).
        gameState.dailyAlerts = gameState.dailyAlerts or {}
        gameState.dailyAlerts[color] = gameState.dailyAlerts[color] or {}
        if not gameState.dailyAlerts[color].downHint then
            gameState.dailyAlerts[color].downHint = true
            broadcastEvent("warn", "To revive " .. char.name .. ": cook a Telltale Heart at a Crockpot (1 Cloth + 1 Battery + 1 Food + 2 cook Health), then use it at " .. char.name .. "'s tile.")
        end
        checkDefeat()
    end
end

-----------------------------------------------------------------------
-- Revival with Telltale Heart  — Design §16.4
-----------------------------------------------------------------------
function reviveCharacter(reviverColor, targetColor)
    local reviver = gameState.activeChars[reviverColor]
    local target = gameState.activeChars[targetColor]

    if not reviver or not target then
        broadcastEvent("damage", "Invalid revive target.")
        return false
    end

    if not target.down then
        broadcastEvent("proc", target.name .. " is not Down.")
        return false
    end

    if reviver.down then
        broadcastEvent("damage", reviver.name .. " is Down and cannot revive.")
        return false
    end

    -- Must be at the same location
    if reviver.location ~= target.location then
        broadcastEvent("damage", reviver.name .. " must be at " .. target.name .. "'s location to revive.")
        return false
    end

    -- Requires a Telltale Heart token at the location (manual check in Phase G)
    -- For now, assume the player has confirmed they have one

    -- Reviver pays 2 Health
    reviver.health = math.max(0, reviver.health - 2)
    broadcastEvent("damage", reviver.name .. " pays 2 Health to revive " .. target.name .. ".")

    -- Revived character returns at half starting maximums
    local stats = CHARACTER_STATS[target.name]
    if stats then
        target.health = math.ceil(stats.health / 2)
        target.hunger = math.ceil(stats.hunger / 2)
        target.sanity = math.ceil(stats.sanity / 2)
    else
        target.health = 1
        target.hunger = 1
        target.sanity = 1
    end

    target.down = false

    -- Return heart token to supply
    gameState.heartCount = math.max(0, (gameState.heartCount or 0) - 1)

    broadcastEvent("gain", target.name .. " is REVIVED! Health " .. target.health ..
        ", Hunger " .. target.hunger .. ", Sanity " .. target.sanity .. ".")
    safecall(function() ensureChronicle().revives = ensureChronicle().revives + 1 end, "Chronicle")

    checkDownState(reviverColor)
    return true
end

-----------------------------------------------------------------------
-- Ghost drift (1 free move per round for Down characters)
-----------------------------------------------------------------------
function ghostDrift(color, newLocation)
    local char = gameState.activeChars[color]
    if not char or not char.down then return end

    char.location = newLocation
    broadcastEvent("proc", char.name .. "'s ghost drifts to " .. newLocation .. ".")

    -- Move standee
    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(newLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end
end

-----------------------------------------------------------------------
-- F.11 — Cleanse Doom action
-- Design §15.3: Spend 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink + 1 Action → Doom -2
-----------------------------------------------------------------------
function doCleanse(color)
    if not spendAction(color, "Cleanse") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Auto-verify and pay the cost; refund the action if the player can't.
    if not verifyAndPayResources(color, CLEANSE_COST, "Cleanse") then
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    broadcastEvent("proc", char.name .. " performs a Cleansing ritual!")
    gameState.doom = math.max(0, gameState.doom - CLEANSE_REDUCTION)
    moveDoomMarker(gameState.doom)
    broadcastEvent("gain", "Doom reduced by " .. CLEANSE_REDUCTION .. "! Now at " .. gameState.doom .. " / " .. getDoomLimit() .. ".")
end

-----------------------------------------------------------------------
-- F.10 — Victory and Defeat detection
-----------------------------------------------------------------------
function checkDefeat()
    -- Condition 1: Doom at the track limit (30; 15 on Long Weekend)
    if gameState.doom >= getDoomLimit() then
        broadcastEvent("damage", "DOOM REACHES " .. getDoomLimit() .. " — THE WORLD IS CONSUMED.")
        broadcastEvent("phase", "=== DEFEAT ===")
        gameState.gameOverCause = "defeat_doom"
        gameState.subPhase = "GameOver"
        safecall(function() showWeekInReview() end, "WeekReview")
        return true
    end

    -- Condition 2: All characters simultaneously Down
    local allDown = true
    local anyActive = false
    for color, char in pairs(gameState.activeChars) do
        anyActive = true
        if not char.down then
            allDown = false
            break
        end
    end

    if anyActive and allDown then
        broadcastEvent("damage", "ALL CHARACTERS ARE DOWN — HOPE IS LOST.")
        broadcastEvent("phase", "=== DEFEAT ===")
        gameState.gameOverCause = "defeat_all_down"
        gameState.subPhase = "GameOver"
        safecall(function() showWeekInReview() end, "WeekReview")
        return true
    end

    return false
end

function checkVictory()
    -- Win: survive Day 7 (after Night/Tick) with Doom < 30 AND the Source
    -- stopped. Design §16.3(3): if the final boss still stands at the end
    -- of Day 7, surviving around it was not enough.
    if gameState.day >= getTotalDays() and gameState.subPhase == "Tick" then
        local sourceKilled = (gameState.bossesDefeated or {}).source
            or gameState.ongoingDawnEffects.sourceDefeated
        if not sourceKilled and isBossOnMap("Boss:TheSource") then
            broadcastEvent("damage", "DAY 7 ENDS — AND THE SOURCE STILL STANDS.")
            broadcastEvent("damage", "Surviving was never going to be enough. The neighborhood is lost.")
            broadcastEvent("phase", "=== DEFEAT ===")
            gameState.gameOverCause = "defeat_source"
            gameState.subPhase = "GameOver"
            safecall(function() showWeekInReview() end, "WeekReview")
            return true
        end

        if gameState.doom < getDoomLimit() then
            broadcastEvent("gain", "DAY " .. gameState.day .. " SURVIVED! DOOM HELD AT " .. gameState.doom .. " / " .. getDoomLimit() .. ".")
            broadcastEvent("phase", "=== VICTORY ===")

            -- Check bonus victories
            checkBonusVictories()

            gameState.gameOverCause = "victory"
            gameState.subPhase = "GameOver"
            safecall(function() showWeekInReview() end, "WeekReview")
            return true
        end
    end

    return false
end

function checkBonusVictories()
    -- Pristine Run (Design §16.2): every character IN PLAY is alive, with no
    -- revivals. The gate used to be `count >= 5`, which made the bonus
    -- unreachable at the recommended 4 players and at the 3-player minimum
    -- (§6.6 turns the spare characters into Visitor NPCs, so a 4-player game
    -- can never have five on their feet). `count > 0` keeps an empty roster
    -- from satisfying it trivially; the revive check is what "pristine" means
    -- once the roster size stops carrying that weight.
    local allAlive = true
    local count = 0
    for color, char in pairs(gameState.activeChars) do
        count = count + 1
        if char.down then allAlive = false end
    end
    local revived = ((gameState.chronicle or {}).revives or 0) > 0
    if allAlive and count > 0 and not revived then
        broadcastEvent("gain", "BONUS: Pristine Run — all " .. count ..
            " characters reached the end on their feet, and nobody had to be brought back!")
    end

    -- Truth Run: all 3 Clue cards found
    local clueCount = gameState.clueCount or 0
    if clueCount >= 3 then
        broadcastEvent("gain", "BONUS: Truth Run — all 3 Clues discovered! The ending changes.")
    end

    -- Hero Run: all three phase bosses defeated (Deerclops, Eye, Source).
    -- The Treeguard mini-boss doesn't count (Design §14.2). Kills are
    -- recorded in gameState.bossesDefeated (persistent) by markBossDefeated;
    -- the ongoingDawnEffects flags are checked too for save compatibility.
    local bd = gameState.bossesDefeated or {}
    local e = gameState.ongoingDawnEffects
    local bossesDefeated = 0
    if bd.deerclops or e.deerclopsDefeated then bossesDefeated = bossesDefeated + 1 end
    if bd.eye or e.eyeDefeated then bossesDefeated = bossesDefeated + 1 end
    if bd.source or e.sourceDefeated then bossesDefeated = bossesDefeated + 1 end
    if bossesDefeated >= 3 then
        broadcastEvent("gain", "BONUS: Hero Run — all three phase bosses defeated!")
    end
end
