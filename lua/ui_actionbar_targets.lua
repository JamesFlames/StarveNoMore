-- ui_actionbar_targets.lua — click-to-complete action targets: the 3D
-- target-button plumbing (_spawnTargetButton / clearActionTargets), the
-- per-action spawn helpers (move/craft/cook/fight), their click handlers,
-- and the highlight helpers. Part of ui_actionbar (see ui_actionbar_core).


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
            or pa.type == "fight" or pa.type == "rally"
            or pa.type == "signature_heal") then
        gameState.pendingAction = nil
    end
    _clearTargetButtons()
    -- Posterize target buttons live in signatures.lua (clears its own list
    -- and the "posterize" pendingAction).
    if clearSignatureTargets then
        safecall(function() clearSignatureTargets() end, "SigTargets")
    end
    if UI then
        UI.hide("tradeDialog"); UI.hide("signatureTargetDialog")
        UI.hide("peekDialog"); UI.hide("rallyDialog")
    end
end

local function _armTargetTimeout()
    if _targetClearHandle then Wait.stop(_targetClearHandle) end
    _targetClearHandle = Wait.time(function()
        _targetClearHandle = nil
        clearActionTargets()
    end, TARGET_TIMEOUT)
end

local function _spawnTargetButton(obj, label, fnName, tooltip, wide, pos)
    obj.createButton({
        click_function = fnName,
        function_owner  = Global,
        label           = label,
        position        = pos or {0, 0.4, 0},
        rotation        = {0, 0, 0},
        width           = wide and 2000 or 1200,
        height          = wide and 560 or 420,
        font_size       = wide and 240 or 180,
        -- Bright, fully opaque, white text: these must read as "click me"
        -- from table height, not blend into the tile art.
        color           = {0.10, 0.55, 0.20, 1.0},
        font_color      = {1, 1, 1},
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
            -- Front edge of the tile, floated well above it: the tile
            -- centre is busy (standee slots, threat cards) and a button
            -- there disappears into the clutter.
            _spawnTargetButton(tile, label, "onMoveTargetClick",
                "Move " .. char.name .. " to " .. locName ..
                ((mode == "bonusmove") and " (free second step)" or " (1 action, 1 Hunger)"),
                true, {0, 0.7, -0.85})
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

-- Fight targets: everything fightable at the active player's tile gets a
-- FIGHT button — plus a FIGHT TOGETHER button when standing, fed allies
-- share the tile (group combat, Design §12.2).
local _fightTargetByGuid = {}

local function _alliesCanJoinFight(color)
    local char = gameState.activeChars[color]
    if not char then return false end
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == char.location
            and ch2.hunger >= 3 then
            return true
        end
    end
    return false
end

local function _spawnFightButtons(color)
    _fightTargetByGuid = {}
    local char = gameState.activeChars[color]
    if not char then return 0 end
    local group = _alliesCanJoinFight(color)
    local n = 0
    for _, target in ipairs(fightTargetsAt(char.location)) do
        local obj = target.obj
        _fightTargetByGuid[obj.guid] = obj
        obj.highlightOn("Red", HIGHLIGHT_DURATION)
        local hpNote = target.stats.hp
        if not target.boss then
            local dmg = (gameState.threatDamage or {})[obj.guid] or 0
            hpNote = math.max(0, target.stats.hp - dmg)
        end
        _spawnTargetButton(obj, "FIGHT", "onFightTargetClick",
            "Fight " .. target.stats.name .. " (HP " .. hpNote .. ", Atk " .. target.stats.attack ..
            ") — 1 action, you alone.", false, {0, 0.4, -0.6})
        if group then
            _spawnTargetButton(obj, "TOGETHER", "onFightTogetherClick",
                "Fight " .. target.stats.name .. " as a group — every standing ally here with Hunger 3+ joins: summed dice, shared counter-attacks.",
                false, {0, 0.4, 0.6})
        end
        n = n + 1
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

local function _resolveFightClick(obj, clickerColor, together)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "fight") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the fighting player may pick the target.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local target = _fightTargetByGuid[obj.guid]
    if not target then return end
    local color = pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()
    safecall(function() doFightTarget(color, target, together) end, "Fight")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onFightTargetClick(obj, clickerColor, altClick)
    _resolveFightClick(obj, clickerColor, false)
end

function onFightTogetherClick(obj, clickerColor, altClick)
    _resolveFightClick(obj, clickerColor, true)
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

