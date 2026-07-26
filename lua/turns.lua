-- turns.lua — the turn engine, split from day_loop.lua (500-line budget).
-- Owns: whose turn it is (advanceToNextPlayer / endPlayerTurn), the action
-- economy (spendAction), the Day-phase kickoff (beginDayPhase), and the
-- idle nudge. Phase transitions (Dawn/Dusk/Night) stay in day_loop.lua.

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
function beginDayPhase()
    gameState.subPhase = "Day"
    gameState.turnIndex = 1
    safecall(function() setPhaseMood("Day") end, "Mood")
    noteInteraction()
    startIdleWatcher()

    -- Reset all players' actions and trade counters
    gameState.combatContext = nil   -- no fight carries across into a new Day
    gameState.tradesThisTurn = {}
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char.actionsLeft = ACTIONS_PER_TURN
        else
            char.actionsLeft = 0
        end
    end

    if gameState.turnStyle == "rotate" then
        broadcastEvent("proc", "Rotation turns: take 1 action, then the next player goes — around the table until everyone has used all "
            .. ACTIONS_PER_TURN .. ". Passing without acting forfeits your remaining actions.")
    end

    -- Start the first player's turn
    advanceToNextPlayer()
end

function advanceToNextPlayer()
    -- New turn: reset idle tracking
    gameState.idleNudgedThisTurn = false
    noteInteraction()
    gameState.actedThisVisit = false

    -- Find the next standing player with actions left. Full-turn default
    -- marches once down the turn order; the rotation variant (§11.2) wraps
    -- around the table until every action is spent.
    local n = #gameState.turnOrder
    local rotate = (gameState.turnStyle == "rotate")
    local tries = 0
    while n > 0 and ((rotate and tries < n) or (not rotate and gameState.turnIndex <= n)) do
        if rotate then
            gameState.turnIndex = ((gameState.turnIndex - 1) % n) + 1
        end
        local color = gameState.turnOrder[gameState.turnIndex]
        local char = gameState.activeChars[color]
        if char and not char.down and char.actionsLeft > 0 then
            gameState.activeColor = color
            -- Per-turn perk windows reset with each new turn (§6.1 / §6.5).
            gameState.jamesRerollUsed = false
            gameState.lucaRallyUsed = false
            -- Backboard Block (§6.3) holds "until Rayman's next turn".
            if char.name == "Rayman" and gameState.raymanDefending then
                gameState.raymanDefending = false
                broadcastEvent("proc", "Rayman's Backboard Block ends — he steps out of the defensive stance.")
            end
            safecall(function() markTurnStart() end, "Telemetry")
            broadcastEvent("proc", char.name .. "'s turn. " .. char.actionsLeft .. " action(s) remaining.")
            -- G.2: Update UI for new active player
            refreshPhaseBanner()
            updateActivePlayerIndicator()
            pulseHandZone(color)
            -- Audible turn-start cue for players watching the board, not the banner
            safecall(function() Audio.playTurnPing() end, "Audio")
            -- If the custom panels are toggled off, the new active player
            -- has no action bar — say how to get it back.
            if customUIHidden then
                printToColor("Your controls are hidden — click 'Show UI' (top right) to bring back the action bar.",
                             color, {1, 0.85, 0.4})
            end
            return
        end
        gameState.turnIndex = gameState.turnIndex + 1
        tries = tries + 1
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
    safecall(function() recordTurnEnd(color) end, "Telemetry")
    local char = gameState.activeChars[color]
    if char then
        char.feastActive = nil   -- The Feast's free cooking ends with her turn
        if gameState.turnStyle == "rotate" and gameState.actedThisVisit and char.actionsLeft > 0 then
            -- Rotation variant: acted this visit — remaining actions stay
            -- banked and priority passes around the table.
            broadcastEvent("proc", char.name .. " passes. (" .. char.actionsLeft .. " action(s) banked)")
        else
            if gameState.turnStyle == "rotate" and not gameState.actedThisVisit and char.actionsLeft > 0 then
                broadcastEvent("proc", char.name .. " passes without acting — remaining actions forfeited.")
            end
            char.actionsLeft = 0
        end
    end
    -- Drop any half-finished targeted action (MOVE HERE / CRAFT / COOK buttons)
    safecall(function() clearActionTargets() end, "ClearTargets")
    safecall(function() finishCombat() end, "FinishCombat")  -- an open press window resolves before priority passes
    gameState.undoSnapshot = nil  -- undo can't cross a turn boundary
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
        broadcastToColor("No actions remaining. Click End Turn.", color, BROADCAST_COLORS.damage)
        return false
    end
    if gameState.turnStyle == "rotate" and gameState.actedThisVisit then
        broadcastToColor("Rotation turns: that was your 1 action for this go-around. Click End Turn — your remaining actions are kept for your next go.",
            color, BROADCAST_COLORS.damage)
        return false
    end
    -- QoL: Snapshot before spending so undo is possible
    safecall(function() snapshotForUndo(color) end, "Undo")
    char.actionsLeft = char.actionsLeft - 1
    gameState.actedThisVisit = true
    broadcastEvent("proc", char.name .. " uses " .. actionName .. ". (" .. char.actionsLeft .. " left)")
    return true
end

-----------------------------------------------------------------------
-- Dusk ready-check: each seated player with a living character clicks
-- Ready; when everyone eligible is ready, Night begins automatically.
-- The host's Resolve Night button remains as a manual override (and
-- the only path when no eligible player is seated, e.g. hotseat).
-----------------------------------------------------------------------
function countDuskReady()
    local ready, total = 0, 0
    for color, ch in pairs(gameState.activeChars) do
        if not ch.down then
            local seated = false
            pcall(function()
                local p = Player[color]
                seated = (p and p.seated) or false
            end)
            if seated then
                total = total + 1
                if (gameState.duskReady or {})[color] then ready = ready + 1 end
            end
        end
    end
    return ready, total
end

function refreshDuskReadyLabel()
    if not UI then return end
    local ready, total = countDuskReady()
    if total > 0 then
        setButtonLabel("duskReadyBtn",
            "I'm settled — Ready for Night  (" .. ready .. "/" .. total .. ")",
            "#AAFFCC", "#192D23F2")
    else
        setButtonLabel("duskReadyBtn", "Host: click Resolve Night when settled",
            "#AAFFCC", "#192D23F2")
    end
end

function toggleDuskReady(color)
    if gameState.subPhase ~= "Dusk" then return end
    local char = gameState.activeChars[color]
    if not char then
        broadcastToColor("You have no character in this game.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.duskReady = gameState.duskReady or {}
    gameState.duskReady[color] = not gameState.duskReady[color] or nil

    local ready, total = countDuskReady()
    if gameState.duskReady[color] then
        broadcastEvent("proc", char.name .. " is settled for the night. (" .. ready .. "/" .. total .. " ready)")
    else
        broadcastEvent("proc", char.name .. " is up again. (" .. ready .. "/" .. total .. " ready)")
    end
    refreshDuskReadyLabel()

    if total > 0 and ready >= total then
        broadcastEvent("phase", "Everyone is settled — night falls.")
        Wait.time(function()
            if gameState.subPhase == "Dusk" then beginNight() end
        end, 1.5)
    end
end
