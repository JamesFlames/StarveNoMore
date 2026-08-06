-- turns.lua — the turn engine, split from day_loop.lua (500-line budget).
-- Owns: whose turn it is (advanceToNextPlayer / endPlayerTurn), the action
-- economy (spendAction), the Day-phase kickoff (beginDayPhase), and the
-- idle nudge. Phase transitions (Dawn/Dusk/Night) stay in day_loop.lua.

-----------------------------------------------------------------------
-- Idle-detection nudge: if the active player hasn't taken an action in
-- IDLE_THRESHOLD seconds, surface a "click What next?" prompt once per
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
        printToColor("Idle for " .. elapsed .. "s. Click 'Rules' or 'What next?' on the Phase Banner for a context hint.",
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
    gameState.sledUsedThisTurn = {}   -- Antler Sled: once per turn (trophies.lua)

    -- P3_LONG_NIGHT (reducedActions): the day is short — 2 actions, not 3.
    -- Read here rather than in spendAction because the budget is what the
    -- action bar and the What-now hints count down from; a mid-day check
    -- would let a player plan three actions and be refused the third.
    local budget = ACTIONS_PER_TURN
    if gameState.ongoingDawnEffects.reducedActions then
        budget = math.max(1, ACTIONS_PER_TURN - 1)
        broadcastEvent("warn", "The night ran long — only " .. budget ..
            " actions each today.")
    end

    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char.actionsLeft = budget
            -- P3_ALLY_MISSING: the one who vanished this morning came back
            -- running (missingAlly is set by the Dawn effect, which resolves
            -- before this reset — which is why it is banked rather than read
            -- from the ongoing flag at spend time).
            if gameState.missingAlly == color then
                char.actionsLeft = char.actionsLeft + 1
                broadcastEvent("gain", char.name .. " is running on adrenaline — +1 action today.")
            end
        else
            char.actionsLeft = 0
        end
    end

    if gameState.turnStyle == "rotate" then
        broadcastEvent("proc", "Rotation turns: take 1 action, then the next player goes — around the table until everyone has used all "
            .. budget .. ". Passing without acting forfeits your remaining actions.")
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
            -- Per-turn perk window resets with each new turn (§6.1).
            gameState.jamesRerollUsed = false
            -- Rally does NOT reset here any more. It became firable on other
            -- players' turns (§6.5, §11.2 downtime relief), and a per-turn
            -- reset would then have handed Luca one rally per PLAYER turn —
            -- up to +4 actions a day at 5 players, which is a power spike, not
            -- a downtime cure. It resets once per round in BeginDay instead,
            -- which keeps his old effective power (one rally a day) and
            -- changes only WHEN he may spend it. That is the whole point:
            -- an interruption-shaped decision instead of a pre-allocation.
            -- Backboard Block (§6.3) holds "until Rayman's next turn".
            if char.name == "Rayman" and gameState.raymanDefending then
                gameState.raymanDefending = false
                broadcastEvent("proc", "Rayman's Backboard Block ends — he steps out of the defensive stance.")
            end
            safecall(function() markTurnStart() end, "Telemetry")
            broadcastEvent("proc", char.name .. "'s turn. " .. char.actionsLeft .. " action(s) remaining.")
            -- The guided opening (§15.9): a concrete 3-action plan, once, on
            -- Day 1. The hardest turn in the game is the one with the least
            -- context, and it is the first one.
            safecall(function() offerOpeningSuggestion(color) end, "Opening")
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
    -- The general mid-game checkpoint: everything a turn could have earned
    -- (a craft, a cook, a Signature, a revive, a Clue) is banked by now.
    safecall(function() checkAchievements("turnEnd") end, "Achievements")
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
    -- Option utilization (§20.2 item 8): every action verb funnels through
    -- here, so this one hook answers "which of the 8 action types does anyone
    -- take, and which tiles does anyone stand on?" — the two cheapest and most
    -- actionable columns of the unused-content report.
    safecall(function()
        recordUsage("actions", actionName)
        recordUsage("locations", char.location)
    end, "Usage")
    -- Feedback at the piece. Every action verb funnels through here, so one
    -- hook shakes the standee that just acted — the answer to "did that
    -- register?" arrives where the player is already looking, instead of as
    -- one more line in a log nobody reads mid-turn.
    safecall(function() jiggleStandee(char.name) end, "Jiggle")
    broadcastEvent("proc", char.name .. " uses " .. actionName .. ". (" .. char.actionsLeft .. " left)")
    return true
end

-----------------------------------------------------------------------
-- Dusk ready-check: each seated player with a living character clicks
-- Ready; when everyone eligible is ready, Night begins automatically.
-- The host's Resolve Night button remains as a manual override (and
-- the only path when no eligible player is seated, e.g. hotseat).
-----------------------------------------------------------------------
-----------------------------------------------------------------------
-- Secret Dusk commitment (§11.3 variant) — reveal.
--
-- Under the variant, doDuskMove banks each scramble in gameState.duskPending
-- instead of moving the standee. This applies them ALL AT ONCE, at the moment
-- Night begins, so no player can react to another player's declaration.
--
-- Why the reveal is a separate step rather than "apply on click": the whole
-- value of the variant is that the alpha player can argue but cannot confirm
-- compliance (§19.5). If moves landed as they were clicked, the last player to
-- commit would see everyone else's board and the variant would be theatre.
--
-- Staying put is a commitment too, and a silent one — it needs no bookkeeping
-- here, which is why "I thought you were coming with me" is the outcome the
-- variant exists to generate.
-----------------------------------------------------------------------
function revealDuskCommitments()
    if not gameState.duskSecret then return end
    local pending = gameState.duskPending or {}
    gameState.duskPending = {}

    -- Ordered, so the reveal reads the same for everybody watching.
    local order = {}
    for _, color in ipairs({"White", "Red", "Yellow", "Green", "Blue"}) do
        if pending[color] then table.insert(order, color) end
    end
    if #order == 0 then
        broadcastEvent("phase", "Nobody moved. Everyone sleeps where they stood.")
        return
    end

    broadcastEvent("phase", "--- THE LIGHT GOES. Everyone moves at once. ---")
    for _, color in ipairs(order) do
        local char = gameState.activeChars[color]
        local target = pending[color]
        if char and not char.down and target then
            local hungerCost = 1 + sportCourtSurcharge(char.location, target)
            char.hunger = math.max(0, char.hunger - hungerCost)
            char.location = target
            if char.name == "Rayman" then
                gameState.raymanMovedToday = true
                gameState.raymanTilesMovedToday = (gameState.raymanTilesMovedToday or 0) + 1
            end
            broadcastEvent("warn", char.name .. " went to " .. target .. ". (-" .. hungerCost .. " Hunger)")
            safecall(function()
                local standee = getCharacterStandee(char.name)
                local tile = getLocationTile(target)
                if standee and tile then
                    standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
                end
            end, "DuskReveal")
            safecall(function() checkWrongnessEntry(color) end, "Wrongness")
            checkDownState(color)
        end
    end

    -- Name who ended up alone. Under secret commitment that can happen by
    -- miscoordination rather than by choice, and it is the beat the variant
    -- was added for — so it is said out loud rather than discovered at Tick.
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local alone = true
            for c2, ch2 in pairs(gameState.activeChars) do
                if c2 ~= color and not ch2.down and ch2.location == char.location then
                    alone = false; break
                end
            end
            if alone then
                broadcastEvent("warn", char.name .. " is alone at " .. (char.location or "?") .. ".")
            end
        end
    end
end

-- ready, total, and the NAMES of the characters still to settle. The third
-- return is what the Dusk button needs to explain itself; older callers that
-- want two values are unaffected.
function countDuskReady()
    local ready, total, waiting = 0, 0, {}
    for color, ch in pairs(gameState.activeChars) do
        if not ch.down then
            local seated = false
            pcall(function()
                local p = Player[color]
                seated = (p and p.seated) or false
            end)
            if seated then
                total = total + 1
                if (gameState.duskReady or {})[color] then
                    ready = ready + 1
                else
                    waiting[#waiting + 1] = ch.name
                end
            end
        end
    end
    table.sort(waiting)   -- pairs() order would reshuffle the label each refresh
    return ready, total, waiting
end

function refreshDuskReadyLabel()
    if not UI then return end
    local ready, total, waiting = countDuskReady()
    if total > 0 then
        -- Name who is still outstanding, and say the button toggles.
        --
        -- It read "I'm settled — Ready for Night (1/2)" and nothing else, so a
        -- hotseat player watching the count refuse to reach 2/2 kept pressing
        -- it — settling and un-settling the SAME character, with 1/2 and 0/2
        -- alternating in the log. The count could not move, because the other
        -- character had never been readied and nothing on screen said whose
        -- turn to settle it was. Both facts belong on the button.
        local label = "I'm settled — Ready for Night  (" .. ready .. "/" .. total .. ")"
        if #waiting > 0 then
            label = label .. "\nStill to settle: " .. table.concat(waiting, ", ") ..
                    "  ·  clicking again un-settles you"
        end
        setButtonLabel("duskReadyBtn", label, "#AAFFCC", "#192D23F2")
    else
        setButtonLabel("duskReadyBtn", "Host: click Resolve Night when settled",
            "#AAFFCC", "#192D23F2")
    end
end

-- The next character down the turn order who still has to settle: seated,
-- standing, and not yet ready. `after` is the colour to start looking AFTER;
-- nil starts at the top of the order. Returns nil when nobody is left.
function nextDuskSeat(after)
    local order = gameState.turnOrder or {}
    local n = #order
    if n == 0 then return nil end
    local start = 0
    if after then
        for i, c in ipairs(order) do
            if c == after then start = i break end
        end
    end
    for step = 1, n do
        local color = order[((start + step - 1) % n) + 1]
        local ch = gameState.activeChars[color]
        if ch and not ch.down and not (gameState.duskReady or {})[color] then
            -- Same seated test countDuskReady uses: an empty chair is not
            -- waited on, so it must not be handed the seat either.
            local seated = false
            pcall(function()
                local p = Player[color]
                seated = (p and p.seated) or false
            end)
            if seated then return color end
        end
    end
    return nil
end

-- Hand Dusk's seat to `color` (nil once everyone has settled).
--
-- Dusk has no turn order of its own — the design is that everyone scrambles
-- and settles at once — and that is exactly what broke in hotseat, where one
-- person drives every seat. "Everyone at once" meant one player clicking the
-- SAME character's ready button over and over: the log filled with "Coco is
-- settled / Coco is up again" while the count sat at 1/3 and the other two
-- were never asked, because nothing moved the driver off Coco's chair. So
-- Dusk now passes the seat like a turn does. syncTtsTurnColor (ui_banner.lua)
-- moves the hotseat driver with it; multiplayer is unaffected, since nothing
-- here refuses a click from a player whose seat is not the current one.
function setDuskSeat(color)
    -- State first, then the three UI channels behind safecall: a refresh that
    -- throws must not leave the seat un-passed, which is the one thing this
    -- function exists to do.
    gameState.activeColor = color
    safecall(function() refreshPhaseBanner() end, "DuskBanner")
    safecall(function() updateActivePlayerIndicator() end, "DuskIndicator")
    if color then safecall(function() pulseHandZone(color) end, "DuskPulse") end
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
        setDuskSeat(nil)
        broadcastEvent("phase", "Everyone is settled — night falls.")
        Wait.time(function()
            if gameState.subPhase == "Dusk" then beginNight() end
        end, 1.5)
        return
    end

    if gameState.duskReady[color] then
        -- Settled: pass the seat on so the next character can be scrambled
        -- and settled without anyone changing colour by hand.
        local nxt = nextDuskSeat(color)
        if nxt then
            setDuskSeat(nxt)
            local nch = gameState.activeChars[nxt]
            broadcastEvent("proc", (nch and nch.name or nxt) ..
                " is up — scramble now if you must, then click 'I'm settled'.")
        end
    else
        -- Un-settled: they want the table back, so the seat returns to them.
        setDuskSeat(color)
    end
end
