-- tick_victory.lua  (F.6 Tick + F.10 Victory/Defeat + F.11 Cleanse + F.13 Down/Ghost)
-- Design §11.5 (Tick), §16 (Victory/Defeat/Down)

-----------------------------------------------------------------------
-- F.6 — TICK (end-of-day decay)
-- Design §11.5: Every character loses 1 Hunger and 1 Sanity.
-----------------------------------------------------------------------
function resolveTick()
    gameState.subPhase = "Tick"
    safecall(function() setPhaseMood("Tick") end, "Mood")
    broadcastEvent("phase", "--- TICK (End of Day " .. gameState.day .. ") ---")

    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            -- Base tick: -1 Hunger, -1 Sanity
            local hungerLoss = 1
            local sanityLoss = 1

            -- Rayman's Big Appetite: -2 Hunger instead of -1
            if char.name == "Rayman" then hungerLoss = 2 end

            -- Winter scenario: hunger decay doubled
            local flags = gameState.scenarioFlags or {}
            if flags.hungerDecayX2 then
                hungerLoss = hungerLoss * 2
            end

            -- Doom 20 threshold: +1 Sanity loss
            if gameState.ongoingDawnEffects.doom20 then
                sanityLoss = sanityLoss + 1
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

            -- Low stat threshold effects (Design §10.1)
            if char.health > 0 and char.health < 3 then
                broadcastEvent("warn", char.name .. " is critically injured (Health < 3). Movement costs +1 action.")
            end
            if char.hunger > 0 and char.hunger < 3 then
                broadcastEvent("warn", char.name .. " is starving (Hunger < 3). Cannot fight or use [Effort] actions.")
            end
            if char.sanity > 0 and char.sanity < 3 then
                broadcastEvent("warn", char.name .. " is losing grip on reality (Sanity < 3). Will hallucinate at next Dawn.")
            end

            checkDownState(color)
        end
    end

    -- Ghost presence: each Down character drains -1 Sanity from co-located living players
    for color, char in pairs(gameState.activeChars) do
        if char.down then
            for c2, ch2 in pairs(gameState.activeChars) do
                if c2 ~= color and not ch2.down and ch2.location == char.location then
                    ch2.sanity = math.max(0, ch2.sanity - 1)
                    broadcastEvent("damage", char.name .. "'s ghost drains 1 Sanity from " .. ch2.name .. ".")
                    checkDownState(c2)
                end
            end
        end
    end

    -- Reset daily flags
    gameState.jamesEnergyDrinkUsed = false
    gameState.marketRefillUsed = false

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

    if char.health <= 0 then
        char.down = true
        char.health = 0
        local narration = DEATH_NARRATIONS[char.name] and DEATH_NARRATIONS[char.name].health
        if narration then
            broadcastEvent("damage", narration)
        end
        broadcastEvent("damage", char.name .. " is DOWN. Flip standee to ghost side.")
        broadcastEvent("proc", char.name .. " cannot act, cannot gather, cannot fight. Ghost drifts 1 free move/round.")
        checkDefeat()
    elseif char.sanity <= 0 then
        char.down = true
        char.sanity = 0
        local narration = DEATH_NARRATIONS[char.name] and DEATH_NARRATIONS[char.name].sanity
        if narration then
            broadcastEvent("damage", narration)
        end
        broadcastEvent("damage", char.name .. " is LOST. Flip standee to ghost side.")
        broadcastEvent("proc", char.name .. " cannot act. Ghost drifts. One whispered word per round.")
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
        standee.setPositionSmooth(tile.getPosition() + Vector(0, 1.5, 0))
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

    -- Resource cost is verified manually by the player (they discard tokens)
    -- The script handles the Doom reduction
    broadcastEvent("proc", char.name .. " performs a Cleansing ritual!")
    broadcastEvent("proc", "Required: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink. Discard these now.")

    gameState.doom = math.max(0, gameState.doom - 2)
    moveDoomMarker(gameState.doom)
    broadcastEvent("gain", "Doom reduced by 2! Now at " .. gameState.doom .. " / 30.")
end

-----------------------------------------------------------------------
-- F.10 — Victory and Defeat detection
-----------------------------------------------------------------------
function checkDefeat()
    -- Condition 1: Doom >= 30
    if gameState.doom >= 30 then
        broadcastEvent("damage", "DOOM REACHES 30 — THE WORLD IS CONSUMED.")
        broadcastEvent("phase", "=== DEFEAT ===")
        gameState.subPhase = "GameOver"
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
        gameState.subPhase = "GameOver"
        return true
    end

    return false
end

function checkVictory()
    -- Win: survive Day 7 (after Night/Tick) with Doom < 30
    if gameState.day >= 7 and gameState.subPhase == "Tick" and gameState.doom < 30 then
        broadcastEvent("gain", "DAY 7 SURVIVED! DOOM HELD AT " .. gameState.doom .. " / 30.")
        broadcastEvent("phase", "=== VICTORY ===")

        -- Check bonus victories
        checkBonusVictories()

        gameState.subPhase = "GameOver"
        return true
    end

    return false
end

function checkBonusVictories()
    -- Pristine Run: all five characters alive (not Down)
    local allAlive = true
    local count = 0
    for color, char in pairs(gameState.activeChars) do
        count = count + 1
        if char.down then allAlive = false end
    end
    if allAlive and count >= 5 then
        broadcastEvent("gain", "BONUS: Pristine Run — all five characters survived!")
    end

    -- Truth Run: all 3 Clue cards found
    local clueCount = gameState.clueCount or 0
    if clueCount >= 3 then
        broadcastEvent("gain", "BONUS: Truth Run — all 3 Clues discovered! The ending changes.")
    end

    -- Hero Run: all bosses defeated (tracked by defeat flags)
    local bossesDefeated = 0
    if gameState.ongoingDawnEffects.deerclopsDefeated then bossesDefeated = bossesDefeated + 1 end
    if gameState.ongoingDawnEffects.eyeDefeated then bossesDefeated = bossesDefeated + 1 end
    if gameState.ongoingDawnEffects.sourceDefeated then bossesDefeated = bossesDefeated + 1 end
    if bossesDefeated >= 3 then
        broadcastEvent("gain", "BONUS: Hero Run — all bosses defeated!")
    end
end
