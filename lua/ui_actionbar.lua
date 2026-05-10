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
    for r, qty in pairs(cost) do
        if (res[r] or 0) < qty then return false end
    end
    return true
end

local function _highlightMoveTargets(color)
    local char = gameState.activeChars[color]
    if not char or not char.location then return end
    local neighbours = _adjacentLocations(char.location)
    -- Rayman's Speed perk: 2 tiles per Move action, so chain-add second-step neighbours.
    if char.name == "Rayman" then
        local seen = {}
        for _, n in ipairs(neighbours) do seen[n] = true end
        for _, n in ipairs(neighbours) do
            for _, n2 in ipairs(_adjacentLocations(n)) do
                if n2 ~= char.location and not seen[n2] then
                    seen[n2] = true
                    neighbours[#neighbours+1] = n2
                end
            end
        end
    end
    for _, locName in ipairs(neighbours) do
        local tile = getLocationTile(locName)
        if tile then tile.highlightOn("Green", HIGHLIGHT_DURATION) end
    end
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
    -- Cleanse cost: 1 each of Wood, Cloth, Battery, Energy Drink.
    for _, resType in ipairs({"Wood", "Cloth", "Battery", "EnergyDrink"}) do
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
    -- Move requires target selection; broadcast instruction
    broadcastToColor("Click a location tile to move there.", color, BROADCAST_COLORS.proc)
    gameState.pendingAction = { type = "move", color = color }
    safecall(function() _highlightMoveTargets(color) end, "MoveHighlight")
    -- The actual move is completed when the player clicks a tile (see onObjectClick handler)
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
    broadcastToColor("Click a Market card to craft it.", color, BROADCAST_COLORS.proc)
    gameState.pendingAction = { type = "craft", color = color }
    safecall(function() _highlightCraftTargets(color) end, "CraftHighlight")
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
    broadcastToColor("Click a Recipe card to cook it.", color, BROADCAST_COLORS.proc)
    gameState.pendingAction = { type = "cook", color = color }
    safecall(function() _highlightCookTargets() end, "CookHighlight")
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

function onActCleanse(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Highlight the resource bags being consumed so the player can see the cost.
    safecall(function() _highlightCleanseTargets() end, "CleanseHighlight")
    -- Show confirm dialog
    showConfirm(
        "Cleanse the Doom Track?",
        "Cost: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink\nDoom will decrease by 2.",
        function()
            safecall(function() doCleanse(color) end, "Cleanse")
            refreshPhaseBanner()
        end
    )
end

function onActPass(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    safecall(function() doPass(color) end, "Pass")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
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
