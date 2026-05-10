-- ui_actionbar.lua  (G.3 Action Bar handlers + G.4 Cube animation + G.5 Stat display)

-----------------------------------------------------------------------
-- G.3 — Action Bar button handlers (called from XML onClick)
-----------------------------------------------------------------------
function onActMove(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    -- Move requires target selection; broadcast instruction
    broadcastToColor("Click a location tile to move there.", color, BROADCAST_COLORS.proc)
    gameState.pendingAction = { type = "move", color = color }
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
