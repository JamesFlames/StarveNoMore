-- ui_actionbar_handlers.lua — Action Bar button handlers (onActMove ...
-- onActPass), the Press-the-Attack combat panel, and the trade / peek /
-- rally / undo / dusk handlers. Part of ui_actionbar (see ui_actionbar_core).

-----------------------------------------------------------------------
-- G.3 — Action Bar button handlers (called from XML onClick)
-----------------------------------------------------------------------
function onActMove(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Clicking Move again while a move is pending cancels it.
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and (pa.type == "move" or pa.type == "bonusmove") then
        broadcastToColor("Move cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    gameState.pendingAction = { type = "move", color = color }
    local n = 0
    safecall(function() n = _spawnMoveButtons(color, "move") end, "MoveTargets")
    if n == 0 then
        gameState.pendingAction = nil
        broadcastToColor("No adjacent location tiles found.", color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
    broadcastToColor("Click the green MOVE HERE button floating at the front of a glowing tile (1 action, 1 Hunger). Click Move again to cancel.", color, BROADCAST_COLORS.proc)
end

function onActGather(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    safecall(function() doGather(color) end, "Gather")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onActCraft(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Clicking Craft again while a craft is pending cancels it.
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and pa.type == "craft" then
        broadcastToColor("Craft cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    gameState.pendingAction = { type = "craft", color = color }
    safecall(function() _highlightCraftTargets(color) end, "CraftHighlight")
    local n = 0
    safecall(function() n = _spawnCraftButtons() end, "CraftTargets")
    if n == 0 then
        gameState.pendingAction = nil
        broadcastToColor("No cards in the Market display.", color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
    broadcastToColor("Click CRAFT on a Market card (Green = you can afford it). Click Craft again to cancel.", color, BROADCAST_COLORS.proc)
end

function onActCook(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Check if at a Crockpot location
    local char = gameState.activeChars[color]
    if char then
        local loc = char.location or ""
        local hasCrockpot = (loc == "EllieLucaHouse")
        -- Also check portable crockpot item (manual for now)
        if not hasCrockpot then
            broadcastToColor("No Crockpot here. Move to Ellie & Luca's House to cook.", color, BROADCAST_COLORS.damage)
            return
        end
    end
    -- Clicking Cook again while a cook is pending cancels it.
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and pa.type == "cook" then
        broadcastToColor("Cook cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    gameState.pendingAction = { type = "cook", color = color }
    safecall(function() _highlightCookTargets() end, "CookHighlight")
    local n = 0
    safecall(function() n = _spawnCookButtons() end, "CookTargets")
    if n == 0 then
        gameState.pendingAction = nil
        broadcastToColor("No recipe cards found on the table.", color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
    broadcastToColor("Click COOK on a recipe card. Click Cook again to cancel.", color, BROADCAST_COLORS.proc)
end

function onActFight(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Clicking Fight again while a fight is pending cancels it.
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and pa.type == "fight" then
        broadcastToColor("Fight cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    local ok, why = canFight(color)
    if not ok then
        broadcastToColor(why or "Can't fight right now.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.pendingAction = { type = "fight", color = color }
    local n = 0
    safecall(function() n = _spawnFightButtons(color) end, "FightTargets")
    if n == 0 then
        gameState.pendingAction = nil
        broadcastToColor("Nothing to fight here.", color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
    broadcastToColor("Click FIGHT on a glowing threat (1 action). TOGETHER pulls in every standing ally here with Hunger 3+. Click Fight again to cancel.",
        color, BROADCAST_COLORS.proc)
end

function onActRest(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Show rest choice dialog
    UI.show("restChoiceDialog")
    gameState.pendingAction = { type = "rest", color = color }
end

function onRestHunger(player, value, id)
    UI.hide("restChoiceDialog")
    local pa = gameState.pendingAction
    if pa and pa.type == "rest" then
        safecall(function() doRest(pa.color, "hunger") end, "Rest")
        gameState.pendingAction = nil
        refreshPhaseBanner()
        updateActivePlayerIndicator()
    end
end

function onRestSanity(player, value, id)
    UI.hide("restChoiceDialog")
    local pa = gameState.pendingAction
    if pa and pa.type == "rest" then
        safecall(function() doRest(pa.color, "sanity") end, "Rest")
        gameState.pendingAction = nil
        refreshPhaseBanner()
        updateActivePlayerIndicator()
    end
end

function onActPry(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    safecall(function() doPry(color) end, "Pry")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onActCleanse(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Highlight the resource bags being consumed so the player can see the cost.
    safecall(function() _highlightCleanseTargets() end, "CleanseHighlight")
    -- Show confirm dialog
    showConfirm(
        "Cleanse the Doom Track?",
        "Cost: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink\n(taken automatically from beside your player board)\nDoom will decrease by 2.",
        function()
            safecall(function() doCleanse(color) end, "Cleanse")
            refreshPhaseBanner()
        end
    )
end

function onActPass(player, value, id)
    local color = player.color
    -- Hotseat convenience: when the HOST clicks Pass on someone else's
    -- turn, it ends the ACTIVE player's turn (same as Host Controls >
    -- End Turn) — ending turns is the most-used control when one person
    -- drives several characters, so it lives on the big bottom bar too.
    if player.host and gameState.subPhase == "Day" and gameState.activeColor
        and color ~= gameState.activeColor then
        local activeChar = gameState.activeChars[gameState.activeColor]
        broadcastEvent("proc", "Host ends " ..
            ((activeChar and activeChar.name) or gameState.activeColor) .. "'s turn.")
        clearActionTargets()
        safecall(function() endPlayerTurn(gameState.activeColor) end, "EndTurn")
        refreshPhaseBanner()
        updateActivePlayerIndicator()
        return
    end
    if not validateActivePlayer(color) then return end
    clearActionTargets()
    safecall(function() doPass(color) end, "Pass")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

-----------------------------------------------------------------------
-- Press the Attack panel (Design §12.5). Shown while a press window is
-- open; driven by the live gameState.combatContext.
-----------------------------------------------------------------------
function refreshCombatPanel()
    if not UI then return end
    if customUIHidden then return end
    local ctx = gameState.combatContext
    if ctx and ctx.open then
        UI.setAttribute("combatStatus", "text",
            (ctx.threat.name or "Threat") .. " — HP " .. math.max(0, ctx.threatHP)
            .. "   (Press: −1 Sanity for another die, until you miss)")
        UI.show("combatPanel")
    else
        UI.hide("combatPanel")
    end
end

function onPressAttack(player, value, id)
    local color = player.color
    local ctx = gameState.combatContext
    if not ctx or not ctx.open then return end
    local char = gameState.activeChars[color]
    if not char then return end
    -- A press that would zero this player's Sanity puts them Down — confirm.
    if char.sanity == 1 then
        showConfirm(
            "Press again?",
            char.name .. " is at 1 Sanity. Pressing drops them to 0 — they will go Lost, mid-fight.",
            function()
                safecall(function() pressAttack(color, true) end, "Press")
                refreshCombatPanel(); refreshPhaseBanner()
            end)
        return
    end
    safecall(function() pressAttack(color, false) end, "Press")
    refreshCombatPanel(); refreshPhaseBanner()
end

function onFinishCombat(player, value, id)
    safecall(function() finishCombat() end, "FinishCombat")
    refreshCombatPanel(); refreshPhaseBanner()
end

-----------------------------------------------------------------------
-- Trade: pick a partner from a dialog, then doTrade handles the free /
-- 1-action cost rules (free once per turn at the same tile).
-----------------------------------------------------------------------
local TRADE_COLORS = {"White", "Red", "Yellow", "Green", "Blue"}

function onActTrade(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and pa.type == "trade" then
        broadcastToColor("Trade cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    local char = gameState.activeChars[color]
    if not char then return end

    local any = false
    for _, c in ipairs(TRADE_COLORS) do
        local ch = gameState.activeChars[c]
        local btn = "tradeBtn_" .. c
        if ch and c ~= color and not ch.down then
            any = true
            local same = (ch.location == char.location)
            local free = same and ((gameState.tradesThisTurn or {})[color] or 0) < 1
            local note
            if free then note = "same tile — free"
            elseif same then note = "same tile — 1 action"
            else note = "at " .. (ch.location or "?") .. " — 1 action" end
            UI.setAttribute(btn, "active", "true")
            UI.setAttribute(btn, "text", ch.name .. "  (" .. note .. ")")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    if not any then
        broadcastToColor("No one to trade with — all allies are Down.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.pendingAction = { type = "trade", color = color }
    UI.show("tradeDialog")
end

function onTradeTargetClick(player, value, id)
    UI.hide("tradeDialog")
    local pa = gameState.pendingAction
    if not (pa and pa.type == "trade" and pa.color == player.color) then return end
    gameState.pendingAction = nil
    safecall(function() doTrade(pa.color, value) end, "Trade")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onTradeCancel(player, value, id)
    UI.hide("tradeDialog")
    local pa = gameState.pendingAction
    if pa and pa.type == "trade" then gameState.pendingAction = nil end
end

-----------------------------------------------------------------------
-- Pattern Recognition (James, §6.1): pick a deck in a dialog, the top
-- card's name goes to James alone. Free action, once per day (doPeek).
-----------------------------------------------------------------------
function onActPeek(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canPeek(color)
    if not ok then
        broadcastToColor(why or "Can't peek right now.", color, BROADCAST_COLORS.damage)
        return
    end
    UI.show("peekDialog")
end

function onPeekDeckClick(player, value, id)
    UI.hide("peekDialog")
    safecall(function() doPeek(player.color, value) end, "Peek")
    refreshPhaseBanner()
end

function onPeekCancel(player, value, id)
    UI.hide("peekDialog")
end

-----------------------------------------------------------------------
-- Rally (Luca, §6.5): pick an eligible ally in a dialog; they gain a
-- free non-movement action. Free for Luca, once per turn (doRally).
-----------------------------------------------------------------------
local RALLY_COLORS = {"White", "Red", "Yellow", "Green", "Blue"}

function onActRally(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canRally(color)
    if not ok then
        broadcastToColor(why or "Can't Rally right now.", color, BROADCAST_COLORS.damage)
        return
    end
    local eligible = {}
    for _, c in ipairs(rallyTargets(color)) do eligible[c] = true end
    for _, c in ipairs(RALLY_COLORS) do
        local btn = "rallyBtn_" .. c
        local ch = gameState.activeChars[c]
        if eligible[c] and ch then
            UI.setAttribute(btn, "active", "true")
            UI.setAttribute(btn, "text", ch.name .. "  (at " .. (ch.location or "?") .. ", " ..
                (ch.actionsLeft or 0) .. " action(s) left)")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    gameState.pendingAction = { type = "rally", color = color }
    UI.show("rallyDialog")
end

function onRallyTargetClick(player, value, id)
    UI.hide("rallyDialog")
    local pa = gameState.pendingAction
    if not (pa and pa.type == "rally" and pa.color == player.color) then return end
    gameState.pendingAction = nil
    safecall(function() doRally(pa.color, value) end, "Rally")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onRallyCancel(player, value, id)
    UI.hide("rallyDialog")
    local pa = gameState.pendingAction
    if pa and pa.type == "rally" then gameState.pendingAction = nil end
end

-----------------------------------------------------------------------
-- Undo: one-step rollback of the last action's stat / position / Doom
-- bookkeeping (snapshot taken in spendAction via snapshotForUndo).
-----------------------------------------------------------------------
function onActUndo(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    clearActionTargets()
    safecall(function() doUndo(color) end, "Undo")
    updateActivePlayerIndicator()
end

-----------------------------------------------------------------------
-- Dusk scramble panel handler (Design §11.3). Any seated player may
-- scramble their own character once during Dusk; rules are enforced in
-- doDuskMove (actions.lua).
-----------------------------------------------------------------------
function onDuskReadyClick(player, value, id)
    if noteInteraction then noteInteraction() end
    safecall(function() toggleDuskReady(player.color) end, "DuskReady")
end

function onDuskMoveClick(player, value, id)
    local color = player.color
    if not gameState.activeChars[color] then
        broadcastToColor("You have no character in this game.", color, BROADCAST_COLORS.damage)
        return
    end
    if noteInteraction then noteInteraction() end
    safecall(function() doDuskMove(color, value) end, "DuskMove")
    refreshPhaseBanner()
end
