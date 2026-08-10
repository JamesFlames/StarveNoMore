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
    -- Gather at James's House offers the Stash every time, so this is the
    -- button that raises a confirm most often — clicking it again answers it
    -- (confirmClickedOnItsOwnButton, ui_controls.lua).
    if confirmClickedOnItsOwnButton(player, id) then return end
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
        -- Say which of the several things went wrong. This line used to be a
        -- flat "No cards in the Market display", printed underneath the
        -- highlight pass's own "Affordable Market cards highlighted Green (1)"
        -- — two messages, one after the other, disagreeing about whether the
        -- Market existed.
        broadcastToColor("Can't offer a Market purchase: " ..
            (_craftScanProblem or "no Market cards are reachable") .. ".",
            color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
    broadcastToColor("Click CRAFT on a Market card (Green = you can afford it). Click Craft again to cancel.", color, BROADCAST_COLORS.proc)
end

function onActCook(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Check if at a Crockpot location (the kitchen, or a Portable Crockpot
    -- carried by anyone standing here — crockpotAt, helpers.lua).
    local char = gameState.activeChars[color]
    if char then
        if not crockpotAt(char.location or "") then
            broadcastToColor("No Crockpot here. Move to Ellie & Luca's House — or craft the Portable Crockpot.",
                color, BROADCAST_COLORS.damage)
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
    -- Recipes come from RECIPE_DATA (generated from content/cards_recipes.csv),
    -- NOT from cards on the table. Cook used to spawn a 3D button on each
    -- physical recipe card and highlight them; when those cards moved into the
    -- hidden library it reported "no recipe cards found" and painted an orange
    -- highlight on a card underneath the board.
    local n = 0
    safecall(function() n = _showCookDialog(color) end, "CookDialog")
    if n == 0 then
        gameState.pendingAction = nil
        broadcastToColor(cookShortfallMessage(color), color, BROADCAST_COLORS.damage)
        return
    end
    -- Same shape as Craft and Cleanse: the highlight lives beside theirs in
    -- ui_actionbar_targets.lua, not inlined here where it drifts from them.
    safecall(function() _highlightCookTargets() end, "CookHighlight")
end

-- Fill the cook dialog with the recipes this player can actually make.
COOK_DIALOG_SLOTS = 10
_cookDialogIds = {}

-- canAfford() answers for MARKET cards (it looks up MARKET_COSTS by card id);
-- a recipe hands us an explicit cost table, so check that directly.
local function _canPayCost(color, cost)
    local res = getPlayerResources(color)
    for r, qty in pairs(cost or {}) do
        if (res[r] or 0) < (qty or 0) then return false end
    end
    return true
end

-- Everything except the ingredients that can stop a cook. Cost was the only
-- filter, so the list still offered the once-per-game recipes already eaten,
-- Gumbo away from a pot, and the Telltale Heart with the supply gone — all of
-- which doCook refuses on the click, after the dialog has promised them.
local function _cookBlockedBy(color, id, recipe)
    local char = gameState.activeChars[color]
    if recipe.oncePerGame and (gameState.usedRecipes or {})[id] then
        return "already cooked once this game"
    end
    if recipe.special == "heart" and (gameState.heartCount or 0) >= HEART_SUPPLY_MAX then
        return "the Telltale Heart supply is gone"
    end
    if recipe.requiresCrockpot and char and not crockpotAt(char.location or "") then
        return "needs a Crockpot at your tile"
    end
    if char and (char.actionsLeft or 0) < (recipe.actionCost or 1) then
        return "needs " .. (recipe.actionCost or 1) .. " actions"
    end
    return nil
end

-- Why the Telltale Heart is not on the list, said in full.
--
-- It is the only way a Down character comes back, it is a RECIPE rather than a
-- Market card, and nothing in the game ever named its ingredients unless you
-- already had them — so a table with someone down went looking for it in the
-- Market, which will never have it. A missing recipe is normally fine to leave
-- silent; this one is the thing they are most likely to need and least likely
-- to find. Returns nil when it IS on the list (then it speaks for itself).
--
-- The cost is the live one, so Ellie's Crockpot Master discount is already in
-- the number a player is being told to go and gather.
function heartHint(color)
    local recipe = RECIPE_DATA and RECIPE_DATA.R_TELLTALE_HEART
    if not recipe then return nil end
    for _, id in ipairs(_cookDialogIds or {}) do
        if id == "R_TELLTALE_HEART" then return nil end
    end

    local cost = recipeIngredientCost(color, recipe)
    local blocked = _cookBlockedBy(color, "R_TELLTALE_HEART", recipe)
    local why
    if blocked then
        why = blocked
    else
        -- Fixed resource order, not pairs(): the shopping list a player is
        -- about to act on must not reshuffle between two openings of the same
        -- dialog. Oxford-free "a, b and c" rather than "a and b and c".
        local have, missing = getPlayerResources(color), {}
        for _, r in ipairs({"Provisions", "Wood", "Cloth", "Metal", "EnergyDrink", "Battery"}) do
            local short = (cost[r] or 0) - (have[r] or 0)
            if short > 0 then missing[#missing + 1] = short .. " more " .. _resLabel(r) end
        end
        if #missing == 0 then
            why = "not available right now"
        elseif #missing == 1 then
            why = "you need " .. missing[1]
        else
            why = "you need " .. table.concat(missing, ", ", 1, #missing - 1) ..
                  " and " .. missing[#missing]
        end
    end
    return "TELLTALE HEART (the only way to revive a Down character) is a recipe, " ..
           "not a Market card: " .. formatIngredientCost(cost) ..
           ", 1 action, and the cook pays 2 Health. Not on this list — " .. why .. "."
end

function _showCookDialog(color)
    if not UI then return 0 end
    local shown, hidden = 0, 0

    -- Stable order so the list doesn't shuffle between openings.
    local ids = {}
    for id in pairs(RECIPE_DATA or {}) do table.insert(ids, id) end
    table.sort(ids)

    -- What the player is short of, for the message when nothing is cookable.
    -- "Nothing you can cook" is true but unhelpful; every recipe in the game
    -- takes Provisions, so that is nearly always the actual answer.
    local shortOf = {}

    _cookDialogIds = {}
    for _, id in ipairs(ids) do
        local recipe = RECIPE_DATA[id]
        local cost = recipeIngredientCost(color, recipe)
        if not _canPayCost(color, cost) then
            local have = getPlayerResources(color)
            for r, qty in pairs(cost) do
                if (have[r] or 0) < qty then shortOf[r] = true end
            end
        elseif not _cookBlockedBy(color, id, recipe) then
            if shown < COOK_DIALOG_SLOTS then
                shown = shown + 1
                _cookDialogIds[shown] = id
                setButtonLabel("cookOpt" .. shown,
                    (recipe.name or id) .. "   (" .. formatIngredientCost(cost) .. ")")
                UI.setAttribute("cookOpt" .. shown, "active", "true")
            else
                hidden = hidden + 1
            end
        end
    end
    for i = shown + 1, COOK_DIALOG_SLOTS do
        UI.setAttribute("cookOpt" .. i, "active", "false")
    end
    if shown == 0 then
        UI.hide("cookDialog")
        _cookShortOf = shortOf
        return 0
    end

    -- Say what cooking DOES, at the moment of choosing. A meal is eaten on the
    -- spot — it moves the stat bars now and leaves nothing behind — and the
    -- word "cook" plus a dialog full of food names reads like crafting, which
    -- does put an item in your hand.
    UI.setAttribute("cookDialogHint", "text",
        "Ingredients are paid automatically from what you hold. The meal is eaten "
        .. "immediately — it restores stats right now and is not stored."
        .. (hidden > 0 and ("  (" .. hidden .. " more you could cook are not shown)") or "")
        .. (heartHint(color) and ("\n" .. heartHint(color)) or ""))
    UI.show("cookDialog")
    return shown
end

-- Set by the pass above when nothing was cookable, so onActCook can name the
-- resource instead of shrugging.
_cookShortOf = {}

-- `color` is optional, and only used to append the Telltale Heart's shopping
-- list — a player standing at the pot with nothing cookable is the single most
-- likely person to be hunting for it.
function cookShortfallMessage(color)
    local names = {}
    for _, r in ipairs({"Provisions", "Wood", "Cloth", "Metal", "EnergyDrink", "Battery"}) do
        if (_cookShortOf or {})[r] then names[#names + 1] = _resLabel(r) end
    end
    local msg
    if #names == 0 then
        msg = "Nothing you can cook right now — the recipes you can pay for are blocked " ..
              "(no Crockpot here, already cooked once, or not enough actions)."
    elseif (_cookShortOf or {}).Provisions then
        msg = "Nothing you can cook right now — you hold no Provisions, and every recipe needs them. " ..
              "Gather at a house, or buy food from the Market."
    else
        msg = "Nothing you can cook right now — you are short of " .. table.concat(names, ", ") .. "."
    end
    local heart = color and heartHint(color)
    return heart and (msg .. "  " .. heart) or msg
end

function onCookOptionClick(player, value, id)
    local slot = tonumber(id and id:match("cookOpt(%d+)")) or tonumber(value)
    local recipeId = _cookDialogIds and _cookDialogIds[slot]
    UI.hide("cookDialog")
    gameState.pendingAction = nil
    if not recipeId then return end
    doCook(player.color, recipeId)
    -- Repaint, like every other action handler (onCraftTargetClick,
    -- onMoveTargetClick, _resolveFightClick). Cooking was the one verb that
    -- resolved without one: the log said "Cook (Comfort Soup). (2 left)" and
    -- "James gains +3 hunger, +3 sanity", while the bar still showed three
    -- action cubes and the party panel still showed everyone's pre-meal bars.
    -- Reported as two bugs — "the cook was free" and "the others were not
    -- buffed" — and it was neither: it was one missing refresh.
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onCookCancel(player)
    UI.hide("cookDialog")
    gameState.pendingAction = nil
    broadcastToColor("Cook cancelled.", player.color, BROADCAST_COLORS.proc)
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
    if confirmClickedOnItsOwnButton(player, id) then return end
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
        end,
        nil, "actCleanse"
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

-- Every trade this character could actually make right now, plus a count of
-- the partners they cannot afford to reach.
--
-- One function, two callers, deliberately: the DIALOG builds its rows from
-- this and the BUTTON's precondition (canTrade, below) asks the same question.
-- They were separate, and drifted the way the comment above onActTrade warns
-- about — the dialog filtered by affordability while the bar lit Trade
-- unconditionally, so the only way to discover there was no trade available
-- was to spend a click finding out.
function tradeOffersFor(color)
    local char = gameState.activeChars[color]
    if not char then return {}, 0 end
    local actionsLeft = char.actionsLeft or 0
    local offers, unaffordable = {}, 0
    for _, c in ipairs(TRADE_COLORS) do
        local ch = gameState.activeChars[c]
        if ch and c ~= color and not ch.down then
            local same = (ch.location == char.location)
            local free = same and ((gameState.tradesThisTurn or {})[color] or 0) < 1
            if free or actionsLeft > 0 then
                local note
                if free then note = "same tile — free"
                elseif same then note = "same tile — 1 action"
                else note = "at " .. (ch.location or "?") .. " — 1 action" end
                offers[#offers + 1] = { color = c, name = ch.name, note = note, free = free }
            else
                unaffordable = unaffordable + 1
            end
        end
    end
    return offers, unaffordable
end

-- Trade is a free action once per turn at your own tile, so it is legal with
-- zero actions left — but only when there is somebody to trade with.
function canTrade(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    local offers, unaffordable = tradeOffersFor(color)
    if #offers > 0 then return true end
    if unaffordable > 0 then
        return false, "Every standing ally is away from your tile, which costs 1 action, and you have none left."
    end
    return false, "Nobody to trade with — every other character is Down or absent."
end

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

    -- Offer only trades this character can actually pay for. The dialog used
    -- to list every standing ally with its price beside it, including ones
    -- priced at "1 action" for a character holding zero — click it and the
    -- action bounces, which reads as the game changing its mind. A partner you
    -- cannot afford is not an option, so it is not shown.
    local offers, unaffordable = tradeOffersFor(color)
    local any = #offers > 0
    local shown = {}
    for _, o in ipairs(offers) do
        shown[o.color] = o
    end
    for _, c in ipairs(TRADE_COLORS) do
        local btn = "tradeBtn_" .. c
        local o = shown[c]
        if o then
            UI.setAttribute(btn, "active", "true")
            setButtonLabel(btn, o.name .. "  (" .. o.note .. ")")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    if not any then
        -- Say which of the two walls they hit; "no one to trade with" in front
        -- of a table of standing allies is just wrong.
        if unaffordable > 0 then
            broadcastToColor(
                "No trade you can afford right now: every standing ally is away from your tile, " ..
                "which costs 1 action, and you have none left. A trade at your OWN tile is still " ..
                "free — move to somebody, or trade at the start of your next turn.",
                color, BROADCAST_COLORS.damage)
        else
            broadcastToColor("No one to trade with — all allies are Down.", color, BROADCAST_COLORS.damage)
        end
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
            setButtonLabel(btn, ch.name .. "  (at " .. (ch.location or "?") .. ", " ..
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
-- The Ready button settles WHOEVER THE DUSK SEAT IS ON, not whoever clicked.
--
-- This is the same conclusion the character-pick queue reached after three
-- failed attempts (ui_setup.lua): in hotseat one person drives every seat and
-- TTS alone decides which colour their clicks carry, so inferring the target
-- from player.color settles the same character over and over. That is exactly
-- what a session logged — "Coco is settled / Coco is up again", five times,
-- with the count stuck at 1/3 and Rayman never asked. Passing the seat on in
-- gameState was half the fix; the click has to follow it.
--
-- A player who has NOT settled still settles themselves: in multiplayer you
-- are answering for your own character and the seat order is a nudge, not a
-- lock. It is only once your own answer is in that the button hands on.
function onDuskReadyClick(player, value, id)
    if noteInteraction then noteInteraction() end
    local color = player.color
    local mine = gameState.activeChars[color]
    local settled = (gameState.duskReady or {})[color]
    if not mine or settled then
        -- Either a driver with no character of their own on this seat, or
        -- someone already settled clicking on behalf of the seat that is up.
        color = gameState.activeColor or color
    end
    safecall(function() toggleDuskReady(color) end, "DuskReady")
end

function onDuskMoveClick(player, value, id)
    local color = player.color
    if not gameState.activeChars[color] then
        broadcastToColor("You have no character in this game.", color, BROADCAST_COLORS.damage)
        return
    end
    if noteInteraction then noteInteraction() end
    -- Safety net (I.6): a sport court with nobody else on it is the worst
    -- place to spend a night — extra Threat, no sleep regen, and Charlie has
    -- no shelter to keep her out. Passes straight through anywhere else.
    safecall(function()
        confirmSleepAloneAtCourt(color, value, function()
            safecall(function() doDuskMove(color, value) end, "DuskMove")
            refreshPhaseBanner()
        end)
    end, "DuskMoveConfirm")
end
