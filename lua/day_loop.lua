-- day_loop.lua  (F.4 — Day Advance / BeginDay + turn management)

-----------------------------------------------------------------------
-- Idle-detection nudge: if the active player hasn't taken an action in
-- IDLE_THRESHOLD seconds, surface a "click What now?" prompt once per
-- turn. Watcher only runs during Day sub-phase.
-----------------------------------------------------------------------
local IDLE_THRESHOLD = 45  -- seconds
local _idleWatcher = nil

function noteInteraction()
    gameState.lastInteractionAt = os.time()
end

function _checkIdle()
    if gameState.subPhase ~= "Day" then return end
    local active = gameState.activeColor
    if not active then return end
    if gameState.idleNudgedThisTurn then return end
    local last = gameState.lastInteractionAt or 0
    local elapsed = os.time() - last
    if elapsed >= IDLE_THRESHOLD then
        gameState.idleNudgedThisTurn = true
        printToColor("Idle for " .. elapsed .. "s. Click '?' or 'What now?' on the Phase Banner for a context hint.",
                     active, {1, 0.85, 0.4})
    end
end

function startIdleWatcher()
    if _idleWatcher then Wait.stop(_idleWatcher) end
    _idleWatcher = Wait.time(_checkIdle, 10, -1)
end

function stopIdleWatcher()
    if _idleWatcher then Wait.stop(_idleWatcher); _idleWatcher = nil end
end

function BeginDay()
    -- Phase 1: Dawn
    gameState.subPhase = "Dawn"
    gameState.dayLog = {}
    gameState.dailyAlerts = {}  -- reset one-per-day urgent-hint flags
    safecall(function() setPhaseMood("Dawn") end, "Mood")
    safecall(function() Audio.startDayAmbience() end, "Audio")

    -- QoL: Snapshot start-of-day stats for end-of-day comparison
    gameState.dayStartStats = {}
    for color, char in pairs(gameState.activeChars) do
        gameState.dayStartStats[color] = {
            health = char.health,
            hunger = char.hunger,
            sanity = char.sanity,
        }
    end

    -- Advance Day Counter
    local counter = getDayCounter()
    if counter then counter.setValue(gameState.day) end

    -- Determine which phase deck we're in
    gameState.phase = getPhaseForDay(gameState.day)

    broadcastEvent("phase", "--- Day " .. gameState.day .. " of 7 --- Phase " .. gameState.phase .. " ---")

    -- Advance Doom by phase rate
    local rate = getDoomRate()
    gameState.doom = gameState.doom + rate
    moveDoomMarker(gameState.doom)
    broadcastEvent("warn", "Doom advances +" .. rate .. " to " .. gameState.doom .. " / 30.")

    -- Check doom thresholds
    checkDoomThresholds()

    -- Check defeat
    if checkDefeat() then return end

    -- Draw and reveal top Dawn card
    revealDawnCard()

    -- After dawn resolves, transition to Day phase
    Wait.time(function()
        beginDayPhase()
    end, 2.0)
end

function checkDoomThresholds()
    local d = gameState.doom
    if d >= 10 and not gameState.ongoingDawnEffects.doom10 then
        gameState.ongoingDawnEffects.doom10 = true
        broadcastEvent("warn", "DOOM THRESHOLD 10: Night threat draws +1 at all locations.")
        safecall(function() nudgeCameraToDoom() end, "CameraNudge")
    end
    if d >= 15 and not gameState.ongoingDawnEffects.doom15 then
        gameState.ongoingDawnEffects.doom15 = true
        broadcastEvent("warn", "DOOM THRESHOLD 15: Market refresh slowed to 1 card per day.")
    end
    if d >= 20 and not gameState.ongoingDawnEffects.doom20 then
        gameState.ongoingDawnEffects.doom20 = true
        broadcastEvent("warn", "DOOM THRESHOLD 20: All characters lose +1 Sanity at Tick.")
    end
    if d >= 25 and not gameState.ongoingDawnEffects.doom25 then
        gameState.ongoingDawnEffects.doom25 = true
        broadcastEvent("warn", "DOOM THRESHOLD 25: Boss-level threats can appear in any phase.")
    end
end

function revealDawnCard()
    local phase = gameState.phase
    local deck = getPhaseDeck(phase)

    if not deck then
        broadcastEvent("proc", "No Phase " .. phase .. " deck found — skipping Dawn card.")
        gameState.activeDawn = nil
        return
    end

    -- Take the top card
    local qty = deck.getQuantity and deck.getQuantity() or 1
    if qty <= 0 then
        broadcastEvent("proc", "Phase " .. phase .. " deck is empty — no Dawn card.")
        gameState.activeDawn = nil
        return
    end

    deck.takeObject({
        position = deck.getPosition() + Vector(3, 1, 0),
        rotation = {0, 180, 0},  -- face up
        smooth   = true,
        callback_function = function(card)
            local name = card.getNickname() or "Unknown Dawn"
            local desc = card.getDescription() or ""
            broadcastEvent("phase", "DAWN: " .. name)
            broadcastEvent("proc", desc)

            gameState.activeDawn = {
                id = name,
                title = name,
                description = desc,
            }

            -- Dispatch dawn effect
            dispatchDawnEffect(card)
        end
    })
end

function beginDayPhase()
    gameState.subPhase = "Day"
    gameState.turnIndex = 1
    safecall(function() setPhaseMood("Day") end, "Mood")
    noteInteraction()
    startIdleWatcher()

    -- Reset all players' actions and trade counters
    gameState.tradesThisTurn = {}
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char.actionsLeft = ACTIONS_PER_TURN
        else
            char.actionsLeft = 0
        end
    end

    -- Start the first player's turn
    advanceToNextPlayer()
end

function advanceToNextPlayer()
    -- New turn: reset idle tracking
    gameState.idleNudgedThisTurn = false
    noteInteraction()
    -- Find next non-down player
    local startIdx = gameState.turnIndex
    while gameState.turnIndex <= #gameState.turnOrder do
        local color = gameState.turnOrder[gameState.turnIndex]
        local char = gameState.activeChars[color]
        if char and not char.down and char.actionsLeft > 0 then
            gameState.activeColor = color
            broadcastEvent("proc", char.name .. "'s turn. " .. char.actionsLeft .. " action(s) remaining.")
            -- G.2: Update UI for new active player
            refreshPhaseBanner()
            updateActivePlayerIndicator()
            pulseHandZone(color)
            return
        end
        gameState.turnIndex = gameState.turnIndex + 1
    end

    -- All players done — advance to Dusk
    gameState.activeColor = nil
    stopIdleWatcher()
    broadcastEvent("phase", "All players have finished. Advancing to Dusk.")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
    beginDusk()
end

function endPlayerTurn(color)
    local char = gameState.activeChars[color]
    if char then char.actionsLeft = 0 end
    gameState.turnIndex = gameState.turnIndex + 1
    advanceToNextPlayer()
end

function spendAction(color, actionName)
    local char = gameState.activeChars[color]
    if not char then
        broadcastEvent("damage", "Error: no character for " .. color)
        return false
    end
    if char.down then
        broadcastToColor("You are Down and cannot act.", color, BROADCAST_COLORS.damage)
        return false
    end
    if char.actionsLeft <= 0 then
        broadcastToColor("No actions remaining. Click Pass to end your turn.", color, BROADCAST_COLORS.damage)
        return false
    end
    -- QoL: Snapshot before spending so undo is possible
    safecall(function() snapshotForUndo(color) end, "Undo")
    char.actionsLeft = char.actionsLeft - 1
    broadcastEvent("proc", char.name .. " uses " .. actionName .. ". (" .. char.actionsLeft .. " left)")
    return true
end

-----------------------------------------------------------------------
-- Dusk
-----------------------------------------------------------------------
function beginDusk()
    gameState.subPhase = "Dusk"
    safecall(function() setPhaseMood("Dusk") end, "Mood")
    refreshPhaseBanner()
    broadcastEvent("phase", "DUSK — Declare where you will sleep tonight. (Characters sleep at their current tile.)")

    -- QoL: Threat preview — show threat level per location before sleep
    broadcastEvent("proc", "--- THREAT PREVIEW ---")
    for _, locName in ipairs({"JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"}) do
        local baseRate = LOCATION_THREAT_RATE[locName] or 0
        if gameState.ongoingDawnEffects.doom10 then baseRate = baseRate + 1 end
        if gameState.ongoingDawnEffects.bloodMoon then baseRate = baseRate + 1 end
        local barricades = (gameState.barricades or {})[locName] or 0
        baseRate = math.max(0, baseRate - barricades)

        -- Count players here
        local playersHere = {}
        for color, char in pairs(gameState.activeChars) do
            if not char.down and char.location == locName then
                table.insert(playersHere, char.name)
            end
        end

        if #playersHere > 0 then
            local risk = "safe"
            if baseRate >= 3 then risk = "DANGEROUS"
            elseif baseRate >= 2 then risk = "risky"
            elseif baseRate >= 1 then risk = "moderate" end
            local barricadeNote = barricades > 0 and " [barricaded]" or ""
            broadcastEvent("proc", "  " .. locName .. ": " .. table.concat(playersHere, ", ") ..
                " | Threat draws: " .. baseRate .. " (" .. risk .. ")" .. barricadeNote)
        end
    end

    -- James end-of-Day reminder: if his Energy Drink is still unconsumed,
    -- the Wired constraint will hit him at Tick. Surface this once per day.
    do
        local jamesColor, jamesChar = nil, nil
        for c, ch in pairs(gameState.activeChars) do
            if ch.name == "James" and not ch.down then jamesColor, jamesChar = c, ch; break end
        end
        if jamesChar and not gameState.jamesEnergyDrinkUsed then
            gameState.dailyAlerts = gameState.dailyAlerts or {}
            gameState.dailyAlerts[jamesColor] = gameState.dailyAlerts[jamesColor] or {}
            if not gameState.dailyAlerts[jamesColor].jamesEnergy then
                gameState.dailyAlerts[jamesColor].jamesEnergy = true
                printToColor("Reminder: you haven't drunk an Energy Drink today. Wired triggers at Tick: −2 Sanity tonight unless one is consumed first.",
                             jamesColor, {1, 0.85, 0.4})
            end
        end
    end

    -- Per-player Dusk warnings: advisory printToColor messages. Players
    -- can't move during Dusk, but the warning surfaces consequences in case
    -- they need to use a held item or accept the risk.
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local loc = char.location
            local othersHere = 0
            for c2, ch2 in pairs(gameState.activeChars) do
                if c2 ~= color and not ch2.down and ch2.location == loc then
                    othersHere = othersHere + 1
                end
            end

            -- Alone at a sport court
            if (loc == "BasketballCourt" or loc == "BadmintonCourt") and othersHere == 0 then
                printToColor("Warning: alone at " .. loc .. " — +1 Threat draw and no sleep regen tonight.",
                             color, {1, 0.85, 0.4})
            end

            -- Coco alone at non-house tile
            if char.name == "Coco" and othersHere == 0 then
                local isHouse = (loc == "JamesHouse" or loc == "RaymanHouse" or loc == "EllieLucaHouse")
                if not isHouse then
                    printToColor("Warning: Coco alone at non-house tile — −3 Sanity (No Home constraint).",
                                 color, {1, 0.85, 0.4})
                end
            end
        end
    end

    -- Public no-light reminder (item tracking is private to each hand zone,
    -- so we broadcast a generic prompt rather than naming who lacks a light).
    broadcastEvent("warn", "Reminder: anyone without a Flashlight (Battery), Lantern, or Fire suffers a Charlie attack tonight (1d8 Sanity + 1d6 Health). Coco is immune.")

    Wait.time(function()
        beginNight()
    end, 5.0)  -- extra time for players to read the preview and move if needed
end

-----------------------------------------------------------------------
-- Night trigger (F.9 lives in night.lua)
-----------------------------------------------------------------------
function beginNight()
    gameState.subPhase = "Night"
    safecall(function() setPhaseMood("Night") end, "Mood")
    safecall(function() Audio.stopAmbience() end, "Audio")
    refreshPhaseBanner()
    broadcastEvent("phase", "NIGHT — Resolving threats and sleep.")
    safecall(function() ResolveNight() end, "Night")
end
