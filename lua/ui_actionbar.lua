-- ui_actionbar.lua  (G.3 Action Bar handlers + G.4 Cube animation + G.5 Stat display)

-----------------------------------------------------------------------
-- Default Compact path graph for Move-target highlights.
-- The design supports 3 path variants (Compact/Sprawl/Linear) plus a
-- scenarioFlags.shortcutPath edge between JamesHouse and BadmintonCourt;
-- those modifiers are applied dynamically below.
-----------------------------------------------------------------------
LOCATION_ADJACENCY = {
    JamesHouse      = {"EllieLucaHouse"},
    RaymanHouse     = {"EllieLucaHouse"},
    EllieLucaHouse  = {"JamesHouse", "RaymanHouse", "BasketballCourt", "BadmintonCourt"},
    BasketballCourt = {"EllieLucaHouse"},
    BadmintonCourt = {"EllieLucaHouse"},
}

local function _adjacentLocations(loc)
    local out = {}
    for _, n in ipairs(LOCATION_ADJACENCY[loc] or {}) do
        out[#out+1] = n
    end
    -- Shortcut scenario: JamesHouse <-> BadmintonCourt edge
    local sFlags = gameState.scenarioFlags or {}
    if sFlags.shortcutPath then
        if loc == "JamesHouse" then out[#out+1] = "BadmintonCourt"
        elseif loc == "BadmintonCourt" then out[#out+1] = "JamesHouse" end
    end
    return out
end

-----------------------------------------------------------------------
-- Highlight helpers — flash legal targets when an action is selected.
-- Uses TTS's per-object highlightOn(color, duration) so it doesn't compete
-- with the global Phase Banner CTA pulse on XML elements.
-----------------------------------------------------------------------
local HIGHLIGHT_DURATION = 8  -- seconds

-----------------------------------------------------------------------
-- Market affordability: count Resource:* tokens near a player's board
-- and compare against the per-card costs in MARKET_COSTS (auto-loaded
-- from content/cards_market.csv via scripts/generate_market_data.py).
-----------------------------------------------------------------------
local RESOURCE_TYPES = {"Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"}

function getPlayerResources(color)
    local counts = {}
    for _, r in ipairs(RESOURCE_TYPES) do counts[r] = 0 end

    local charName = colorToCharacter(color)
    if not charName then return counts end
    local board = getPlayerBoard(charName)
    if not board then return counts end

    -- Build a generous bounding box around the player board so resources
    -- placed alongside the board still count.
    local pos = board.getPosition()
    local b = board.getBoundsNormalized()
    local pad = 1.5
    local minX = pos.x - b.size.x * 0.5 - pad
    local maxX = pos.x + b.size.x * 0.5 + pad
    local minZ = pos.z - b.size.z * 0.5 - pad
    local maxZ = pos.z + b.size.z * 0.5 + pad

    for _, obj in ipairs(findAllByTag("Resource")) do
        local p = obj.getPosition()
        if p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
            for _, tag in ipairs(obj.getTags()) do
                local resType = tag:match("^Resource:(.+)$")
                if resType and counts[resType] ~= nil then
                    counts[resType] = counts[resType] + 1
                    break
                end
            end
        end
    end
    return counts
end

-----------------------------------------------------------------------
-- Verify-and-pay for fixed resource costs (Cleanse, Appease, Barricade).
-- Verifies the tokens sit in the payer's board area, then returns them
-- to their supply bags (or deletes them if the bag is gone). Returns
-- false — with a shortfall message — and takes nothing when unpaid.
-----------------------------------------------------------------------
local RESOURCE_LABELS = { EnergyDrink = "Energy Drink" }

local function _resLabel(resType) return RESOURCE_LABELS[resType] or resType end

function verifyAndPayResources(color, cost, label)
    local char = gameState.activeChars[color]
    if not char then return false end

    local have = getPlayerResources(color)
    local missing = {}
    for resType, qty in pairs(cost) do
        if (have[resType] or 0) < qty then
            table.insert(missing, qty .. " " .. _resLabel(resType) .. " (have " .. (have[resType] or 0) .. ")")
        end
    end
    if #missing > 0 then
        broadcastToColor("Can't pay for " .. label .. " — missing: " .. table.concat(missing, ", ") ..
            ". Resource tokens must sit next to your player board.", color, BROADCAST_COLORS.damage)
        return false
    end

    -- Pay: pull matching tokens out of the board area, back into supply.
    local board = getPlayerBoard(char.name)
    if not board then return false end
    local pos = board.getPosition()
    local b = board.getBoundsNormalized()
    local pad = 1.5
    local minX = pos.x - b.size.x * 0.5 - pad
    local maxX = pos.x + b.size.x * 0.5 + pad
    local minZ = pos.z - b.size.z * 0.5 - pad
    local maxZ = pos.z + b.size.z * 0.5 + pad

    local remaining = {}
    for r, q in pairs(cost) do remaining[r] = q end
    for _, obj in ipairs(findAllByTag("Resource")) do
        local p = obj.getPosition()
        if p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
            for _, tag in ipairs(obj.getTags()) do
                local resType = tag:match("^Resource:(.+)$")
                if resType and (remaining[resType] or 0) > 0 then
                    remaining[resType] = remaining[resType] - 1
                    local bag = getResourceBag(resType)
                    if bag then
                        pcall(function() bag.putObject(obj) end)
                    else
                        pcall(function() obj.destruct() end)
                    end
                    break
                end
            end
        end
    end

    local parts = {}
    for r, q in pairs(cost) do table.insert(parts, q .. " " .. _resLabel(r)) end
    broadcastEvent("proc", char.name .. " pays " .. table.concat(parts, " + ") ..
        " for " .. label .. " (tokens returned to supply automatically).")
    return true
end

local function _cardIdFromTags(card)
    if not card or not card.getTags then return nil end
    for _, tag in ipairs(card.getTags()) do
        if tag:match("^M_") then return tag end
    end
    return nil
end

function canAfford(color, cardId)
    if not cardId or not MARKET_COSTS then return true end
    local cost = MARKET_COSTS[cardId]
    if not cost or next(cost) == nil then return true end  -- free or unknown
    local res = getPlayerResources(color)
    local totalCost = 0
    local totalHeld = 0
    for _, qty in pairs(res) do totalHeld = totalHeld + qty end
    for r, qty in pairs(cost) do
        if (res[r] or 0) < qty then return false end
        totalCost = totalCost + qty
    end
    -- Scarcity (Doom >= 15): every craft costs +1 extra resource of any type
    if gameState.ongoingDawnEffects and gameState.ongoingDawnEffects.doom15 then
        if totalHeld < totalCost + 1 then return false end
    end
    return true
end

-----------------------------------------------------------------------
-- Click-to-complete action targets (Move / Craft / Cook).
--
-- Selecting one of these actions spawns a clickable 3D button on every
-- legal target object (tile / market card / recipe card). Clicking the
-- button consumes gameState.pendingAction and calls the matching do*
-- handler. Buttons are cleared when the action completes, is cancelled
-- (click the same action again), the turn ends, or after a timeout.
--
-- Rayman's Speed perk is a chained flow: his Move spawns a second round
-- of FREE MOVE buttons around his new tile (doRaymanBonusMove).
-----------------------------------------------------------------------
local _targetButtonObjs  = {}   -- objects we added buttons to
local _craftSlotByGuid   = {}   -- market card guid -> slot index for doCraft
local _recipeIdByGuid    = {}   -- recipe card guid -> recipe id for doCook
local _targetClearHandle = nil
local TARGET_TIMEOUT = 30       -- seconds before stale target buttons vanish

local function _clearTargetButtons()
    if _targetClearHandle then Wait.stop(_targetClearHandle); _targetClearHandle = nil end
    for _, obj in ipairs(_targetButtonObjs) do
        if obj and not obj.isDestroyed() then
            pcall(function() obj.clearButtons() end)
        end
    end
    _targetButtonObjs = {}
    _craftSlotByGuid  = {}
    _recipeIdByGuid   = {}
end

-- Global: also cancels a pending targeted action. Called from turn-end
-- (day_loop.lua) and from every action-button handler.
function clearActionTargets()
    local pa = gameState.pendingAction
    if pa and (pa.type == "move" or pa.type == "bonusmove"
            or pa.type == "craft" or pa.type == "cook" or pa.type == "trade"
            or pa.type == "signature_heal") then
        gameState.pendingAction = nil
    end
    _clearTargetButtons()
    -- Posterize target buttons live in signatures.lua (clears its own list
    -- and the "posterize" pendingAction).
    if clearSignatureTargets then
        safecall(function() clearSignatureTargets() end, "SigTargets")
    end
    if UI then UI.hide("tradeDialog"); UI.hide("signatureTargetDialog") end
end

local function _armTargetTimeout()
    if _targetClearHandle then Wait.stop(_targetClearHandle) end
    _targetClearHandle = Wait.time(function()
        _targetClearHandle = nil
        clearActionTargets()
    end, TARGET_TIMEOUT)
end

local function _spawnTargetButton(obj, label, fnName, tooltip, wide)
    obj.createButton({
        click_function = fnName,
        function_owner  = Global,
        label           = label,
        position        = {0, 0.4, 0},
        rotation        = {0, 0, 0},
        width           = wide and 2000 or 1200,
        height          = wide and 560 or 420,
        font_size       = wide and 240 or 180,
        color           = {0.08, 0.28, 0.14, 0.95},
        font_color      = {0.75, 1, 0.75},
        tooltip         = tooltip,
    })
    table.insert(_targetButtonObjs, obj)
end

-- Move targets are always 1-step neighbours; Rayman's 2-tile Speed is
-- delivered as a chained free second hop, so his buttons are 1-step too.
local function _spawnMoveButtons(color, mode)
    local char = gameState.activeChars[color]
    if not char or not char.location then return 0 end
    local label = (mode == "bonusmove") and "FREE MOVE" or "MOVE HERE"
    local n = 0
    for _, locName in ipairs(_adjacentLocations(char.location)) do
        local tile = getLocationTile(locName)
        if tile then
            tile.highlightOn("Green", HIGHLIGHT_DURATION)
            _spawnTargetButton(tile, label, "onMoveTargetClick",
                "Move " .. char.name .. " to " .. locName ..
                ((mode == "bonusmove") and " (free second step)" or " (1 action, 1 Hunger)"),
                true)
            n = n + 1
        end
    end
    return n
end

local function _spawnCraftButtons()
    local n = 0
    for i, slot in ipairs(getMarketSlots()) do
        local slotPos = slot.getPosition()
        for _, card in ipairs(findAllByTag("MarketCard")) do
            if card.type == "Card" and card.getPosition():distance(slotPos) < 2 then
                _craftSlotByGuid[card.getGUID()] = i
                _spawnTargetButton(card, "CRAFT", "onCraftTargetClick",
                    "Craft " .. (card.getNickname() or "this item") .. " (1 action + resources)",
                    false)
                n = n + 1
                break
            end
        end
    end
    return n
end

local function _recipeIdFromCard(card)
    for _, tag in ipairs(card.getTags()) do
        if RECIPE_DATA and RECIPE_DATA[tag] then return tag end
    end
    local nick = card.getNickname() or ""
    if RECIPE_DATA then
        for id, r in pairs(RECIPE_DATA) do
            if r.name == nick then return id end
        end
    end
    return nil
end

local function _spawnCookButtons()
    local n = 0
    for _, card in ipairs(findAllByTag("RecipeCard")) do
        local rid = _recipeIdFromCard(card)
        if rid then
            _recipeIdByGuid[card.getGUID()] = rid
            _spawnTargetButton(card, "COOK", "onCookTargetClick",
                "Cook " .. (RECIPE_DATA[rid].name or rid) .. " (1 action + ingredients)",
                false)
            n = n + 1
        end
    end
    return n
end

-----------------------------------------------------------------------
-- Target-button click handlers (createButton click_functions)
-----------------------------------------------------------------------
function onMoveTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and (pa.type == "move" or pa.type == "bonusmove")) then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the moving player may choose the destination.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local loc = nil
    for _, tag in ipairs(obj.getTags()) do
        loc = tag:match("^Location:(.+)")
        if loc then break end
    end
    if not loc then return end

    local mode, color = pa.type, pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()

    if mode == "move" then
        safecall(function() doMove(color, loc) end, "Move")
        -- Rayman's Speed: doMove grants a free second 1-tile step.
        if gameState.raymanBonusMove then
            gameState.pendingAction = { type = "bonusmove", color = color }
            _spawnMoveButtons(color, "bonusmove")
            _armTargetTimeout()
            broadcastToColor("Speed: click FREE MOVE on a green tile for your second step — or take another action to skip it.",
                color, BROADCAST_COLORS.gain)
        end
    else
        safecall(function() doRaymanBonusMove(color, loc) end, "BonusMove")
    end
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onCraftTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "craft") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the crafting player may pick the card.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local slotIndex = _craftSlotByGuid[obj.getGUID()]
    if not slotIndex then return end
    local color = pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()
    safecall(function() doCraft(color, slotIndex) end, "Craft")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onCookTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "cook") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the cooking player may pick the recipe.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local rid = _recipeIdByGuid[obj.getGUID()]
    if not rid then return end
    local color = pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()
    safecall(function() doCook(color, rid) end, "Cook")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

local function _highlightCraftTargets(color)
    local deck = getMarketDeck()
    if deck then deck.highlightOn("Yellow", HIGHLIGHT_DURATION) end
    -- Empty market slots — neutral hint that this is where cards go
    for _, slot in ipairs(getMarketSlots()) do
        slot.highlightOn("Yellow", HIGHLIGHT_DURATION)
    end
    -- Per-card affordability: each individual MarketCard (those that have
    -- been dealt out of the deck) gets Green if the active player can
    -- afford it, Yellow otherwise.
    local affordableCount = 0
    for _, card in ipairs(findAllByTag("MarketCard")) do
        if card.type == "Card" then
            local cardId = _cardIdFromTags(card)
            if color and cardId and canAfford(color, cardId) then
                card.highlightOn("Green", HIGHLIGHT_DURATION)
                affordableCount = affordableCount + 1
            else
                card.highlightOn("Yellow", HIGHLIGHT_DURATION)
            end
        end
    end
    if color then
        local res = getPlayerResources(color)
        local resStr = string.format("Wood %d / Metal %d / Cloth %d / Food %d / Energy %d / Battery %d",
            res.Wood or 0, res.Metal or 0, res.Cloth or 0, res.Food or 0,
            res.EnergyDrink or 0, res.Battery or 0)
        printToColor("Affordable Market cards highlighted Green (" .. affordableCount .. "). Your bag: " .. resStr,
                     color, {0.7, 1.0, 0.7})
    end
end

local function _highlightCookTargets()
    -- Recipe cards live on a reference rack; tag is "RecipeCard".
    for _, card in ipairs(findAllByTag("RecipeCard")) do
        card.highlightOn("Orange", HIGHLIGHT_DURATION)
    end
    -- Crockpot is at EllieLucaHouse; highlight that tile too.
    local tile = getLocationTile("EllieLucaHouse")
    if tile then tile.highlightOn("Orange", HIGHLIGHT_DURATION) end
end

local function _highlightCleanseTargets()
    -- Cleanse cost bundle (CLEANSE_COST, global.lua).
    for resType in pairs(CLEANSE_COST) do
        local bag = getResourceBag(resType)
        if bag then bag.highlightOn("White", HIGHLIGHT_DURATION) end
    end
end

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
    broadcastToColor("Click MOVE HERE on a green tile (1 action, 1 Hunger). Click Move again to cancel.", color, BROADCAST_COLORS.proc)
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
    safecall(function() doFight(color) end, "Fight")
    refreshPhaseBanner()
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

-----------------------------------------------------------------------
-- Validate that this player is the active player
-----------------------------------------------------------------------
function validateActivePlayer(color)
    if gameState.subPhase ~= "Day" then
        broadcastToColor("Actions can only be taken during the Day phase.", color, BROADCAST_COLORS.damage)
        return false
    end
    if color ~= gameState.activeColor then
        broadcastToColor("It's not your turn.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    if not char then return false end
    if char.down then
        broadcastToColor("You are Down and cannot act.", color, BROADCAST_COLORS.damage)
        return false
    end
    -- Reset idle timer whenever the active player interacts.
    if noteInteraction then noteInteraction() end
    return true
end

-----------------------------------------------------------------------
-- G.4 — Action Cube animation
-----------------------------------------------------------------------
function refreshActionBar()
    if not UI then return end

    -- Show/hide action bar based on game state
    if gameState.subPhase == "Day" and gameState.activeColor then
        UI.show("actionBar")
        UI.show("statDisplay")

        local char = gameState.activeChars[gameState.activeColor]
        if char then
            local left = char.actionsLeft or 0
            setActionCubes(left)

            -- Dim buttons based on availability
            refreshActionButtonStates(gameState.activeColor)
        end
    else
        UI.hide("actionBar")
        -- Keep stat display visible during other phases if game started
        if gameState.started then
            UI.show("statDisplay")
        else
            UI.hide("statDisplay")
        end
    end
end

function setActionCubes(remaining)
    local colors = {"#66FF66", "#66FF66", "#66FF66"}
    for i = remaining + 1, 3 do
        colors[i] = "#333333"
    end
    UI.setAttribute("cube1", "color", colors[1])
    UI.setAttribute("cube2", "color", colors[2])
    UI.setAttribute("cube3", "color", colors[3])
    UI.setAttribute("cubeLabel", "text", remaining .. " remaining")
end

-----------------------------------------------------------------------
-- Dim/enable action buttons based on game state (G.3 + H.7)
-----------------------------------------------------------------------
function refreshActionButtonStates(color)
    local char = gameState.activeChars[color]
    if not char then return end

    local noActions = char.actionsLeft <= 0
    local loc = char.location or ""
    local hasCrockpot = (loc == "EllieLucaHouse")
    local tooHungry = char.hunger < 3

    -- Move: always available if actions remain
    setActionEnabled("actMove", not noActions)

    -- Gather: available if actions remain
    setActionEnabled("actGather", not noActions)

    -- Craft: available if actions remain (resource check is manual)
    setActionEnabled("actCraft", not noActions)

    -- Cook: only at crockpot locations
    setActionEnabled("actCook", not noActions and hasCrockpot)

    -- Fight: need actions and hunger >= 3
    setActionEnabled("actFight", not noActions and not tooHungry)

    -- Rest: always available if actions remain
    setActionEnabled("actRest", not noActions)

    -- Cleanse: need actions (resource check is manual)
    setActionEnabled("actCleanse", not noActions)

    -- Trade: free once per turn at your tile — legal even with 0 actions
    setActionEnabled("actTrade", true)

    -- Pry (§13.5): free action, but only lit when a sealed thing is at the
    -- tile and the player holds a tool
    if canPry then
        local pryOk, pryWhy = canPry(color)
        setActionEnabled("actPry", pryOk and true or false)
        UI.setAttribute("actPry", "tooltip",
            pryOk and ("Pry open the sealed thing here — free action (you hold a " .. tostring(pryWhy) .. ").")
                  or ("Pry (free action). Unavailable: " .. (pryWhy or "")))
    end

    -- Signature (§6.7): once per game, per-character preconditions
    local sig = SIGNATURES and SIGNATURES[char.name]
    if sig then
        local sigOk, sigWhy = canUseSignature(color)
        setActionEnabled("actSignature", sigOk and true or false)
        UI.setAttribute("actSignature", "text", sig.name)
        UI.setAttribute("actSignature", "tooltip",
            sigOk and (sig.desc .. " " .. sig.cost .. " Once per game.")
                  or (sig.desc .. " Unavailable: " .. (sigWhy or "")))
    end

    -- Undo: only when a snapshot of your own last action exists
    local snap = gameState.undoSnapshot
    setActionEnabled("actUndo", snap ~= nil and snap.color == color)

    -- Pass: always available
    setActionEnabled("actPass", true)

    -- H.7: Update why-disabled tooltip text
    safecall(function() refreshActionButtonReasons(color) end, "ActionTooltips")
end

function setActionEnabled(buttonId, enabled)
    if enabled then
        UI.setAttribute(buttonId, "interactable", "true")
        UI.setAttribute(buttonId, "color", "rgba(30,50,40,0.9)")
    else
        UI.setAttribute(buttonId, "interactable", "false")
        UI.setAttribute(buttonId, "color", "rgba(20,20,20,0.6)")
    end
end

-----------------------------------------------------------------------
-- G.5 — Stat display refresh
-----------------------------------------------------------------------
-- One-glance perk/constraint summary per character. The full briefing
-- shows once at setup; this line keeps the rules visible mid-game.
CHAR_TRAIT_LINES = {
    James  = "Perks: peek a deck, reroll dice.\nSignature: All-Nighter (1×).\nWired: drink 1 Energy Drink/day or −2 Sanity at Tick.",
    Coco   = "Perks: −1 Sanity losses nearby, Charlie-immune.\nSignature: Touch of Hope (1×).\nNo Home: alone at a non-house at night = −3 Sanity.",
    Rayman = "Perks: 2-tile Move, +1 die at B-ball Court, Defend.\nSignature: Posterize (1×).\nBig Appetite: −2 Hunger/Tick. Loud: moving today = +1 Threat at his night tile.",
    Ellie  = "Perks: cook with −1 ingredient, Comfort Food +1 to allies.\nSignature: The Feast (1×).\nParticular Eater: can't eat raw food.",
    Luca   = "Perks: Rally (ally free action), Calm Words, Storyteller.\nSignature: The Speech (1×).\nNeeds Audience: no solo Sanity regen.",
}

function refreshStatDisplay()
    if not UI then return end

    -- Pick which character to show: active player during Day, or the local player
    local showColor = gameState.activeColor
    if not showColor then
        -- Show nothing specific
        UI.setAttribute("statCharName", "text", "—")
        return
    end

    local char = gameState.activeChars[showColor]
    if not char then return end

    UI.setAttribute("statCharName", "text", char.name .. (char.down and " [DOWN]" or ""))

    -- Health bar
    local hPct = (char.maxHealth > 0) and math.floor(char.health / char.maxHealth * 100) or 0
    UI.setAttribute("statHealthBar", "percentage", tostring(hPct))
    UI.setAttribute("statHealthVal", "text", char.health .. "/" .. char.maxHealth)
    -- Color: red if below threshold
    if char.health < 3 then
        UI.setAttribute("statHealthBar", "color", "#FF2222")
    else
        UI.setAttribute("statHealthBar", "color", "#FF4444")
    end

    -- Hunger bar
    local huPct = (char.maxHunger > 0) and math.floor(char.hunger / char.maxHunger * 100) or 0
    UI.setAttribute("statHungerBar", "percentage", tostring(huPct))
    UI.setAttribute("statHungerVal", "text", char.hunger .. "/" .. char.maxHunger)
    if char.hunger < 3 then
        UI.setAttribute("statHungerBar", "color", "#FF6600")
    else
        UI.setAttribute("statHungerBar", "color", "#FFAA22")
    end

    -- Sanity bar
    local sPct = (char.maxSanity > 0) and math.floor(char.sanity / char.maxSanity * 100) or 0
    UI.setAttribute("statSanityBar", "percentage", tostring(sPct))
    UI.setAttribute("statSanityVal", "text", char.sanity .. "/" .. char.maxSanity)
    if char.sanity < 3 then
        UI.setAttribute("statSanityBar", "color", "#FF44FF")
    else
        UI.setAttribute("statSanityBar", "color", "#4488FF")
    end

    -- Location
    local locName = char.location or "Unknown"
    UI.setAttribute("statLocation", "text", "Location: " .. locName)

    -- Perks + constraint reminder
    UI.setAttribute("statPerks", "text", CHAR_TRAIT_LINES[char.name] or "")
end

-----------------------------------------------------------------------
-- Stat adjust buttons (G.5 manual +/-)
-----------------------------------------------------------------------
function onStatHealthMinus(player)  modStatFromUI(player.color, "health", -1) end
function onStatHealthPlus(player)   modStatFromUI(player.color, "health", 1) end
function onStatHungerMinus(player)  modStatFromUI(player.color, "hunger", -1) end
function onStatHungerPlus(player)   modStatFromUI(player.color, "hunger", 1) end
function onStatSanityMinus(player)  modStatFromUI(player.color, "sanity", -1) end
function onStatSanityPlus(player)   modStatFromUI(player.color, "sanity", 1) end

function modStatFromUI(color, stat, delta)
    -- Allow any seated player to adjust stats for edge-case manual corrections
    local activeColor = gameState.activeColor or color
    local char = gameState.activeChars[activeColor]
    if not char then return end

    local maxKey = "max" .. stat:sub(1,1):upper() .. stat:sub(2)
    char[stat] = math.max(0, math.min(char[maxKey], char[stat] + delta))

    local verb = delta > 0 and "gains" or "loses"
    broadcastEvent("proc", char.name .. " " .. verb .. " " .. math.abs(delta) .. " " .. stat .. ". Now: " .. char[stat])

    checkDownState(activeColor)
    refreshStatDisplay()
end
