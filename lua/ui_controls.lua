-- ui_controls.lua  (G.6 Confirm dialog + G.7 Tooltips + G.10 Host controls)

-----------------------------------------------------------------------
-- G.6 — Confirm-before-spend dialog
-----------------------------------------------------------------------
local pendingConfirmCallback = nil

function showConfirm(title, body, onConfirm)
    if not UI then
        -- Fallback: just execute
        if onConfirm then onConfirm() end
        return
    end
    UI.setAttribute("confirmTitle", "text", title)
    UI.setAttribute("confirmBody", "text", body)
    pendingConfirmCallback = onConfirm
    UI.show("confirmDialog")
end

function onConfirmYes(player, value, id)
    UI.hide("confirmDialog")
    if pendingConfirmCallback then
        local cb = pendingConfirmCallback
        pendingConfirmCallback = nil
        safecall(function() cb() end, "ConfirmAction")
    end
end

function onConfirmNo(player, value, id)
    UI.hide("confirmDialog")
    pendingConfirmCallback = nil
    broadcastEvent("proc", "Action cancelled.")
end

-----------------------------------------------------------------------
-- G.10 — Host control panel handlers
-----------------------------------------------------------------------
function onHostSetup(player, value, id)
    safecall(function() Setup(player.color) end, "Setup")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onHostBeginDay(player, value, id)
    if not gameState.started then
        broadcastToColor("Run Setup first.", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function()
        BeginDay()
        refreshPhaseBanner()
        updateActivePlayerIndicator()
    end, "BeginDay")
end

function onHostResolveNight(player, value, id)
    if gameState.subPhase ~= "Night" then
        broadcastToColor("Not in the Night phase.", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function() ResolveNight() end, "ResolveNight")
end

function onHostEndTurn(player, value, id)
    if gameState.activeColor then
        safecall(function()
            endPlayerTurn(gameState.activeColor)
            refreshPhaseBanner()
            updateActivePlayerIndicator()
        end, "EndTurn")
    end
end

function onHostRestart(player, value, id)
    showConfirm(
        "Restart the game?",
        "This will reset all progress. Are you sure?",
        function()
            -- Reset gameState
            gameState = {
                day = 1, phase = 1, doom = 0,
                started = false, welcomed = false,
                subPhase = "PreGame",
                activeColor = nil, turnOrder = {}, turnIndex = 0,
                playerCount = 0, pathVariant = nil,
                dayLog = {}, activeDawn = nil,
                ongoingDawnEffects = {},
                activeChars = {},
            }
            broadcastEvent("phase", "Game reset. Click Setup to begin a new game.")
            refreshPhaseBanner()
            UI.hide("actionBar")
            UI.hide("statDisplay")
        end
    )
end

-- Help panel + What-now handlers are defined in ui_help.lua (Phase H)

-----------------------------------------------------------------------
-- Summary panel (I.4 stub)
-----------------------------------------------------------------------
function showEndOfDaySummary()
    if not UI then return end

    local title = "End of Day " .. gameState.day
    local body = ""

    -- Compile from dayLog
    local damage = {}
    local gains = {}
    for _, entry in ipairs(gameState.dayLog or {}) do
        if entry.category == "damage" or entry.category == "warn" then
            table.insert(damage, "- " .. entry.message)
        elseif entry.category == "gain" then
            table.insert(gains, "- " .. entry.message)
        end
    end

    body = body .. "Doom: " .. gameState.doom .. " / 30\n\n"

    -- QoL: Stat comparison (start-of-day vs now)
    local startStats = gameState.dayStartStats or {}
    local statLines = {}
    for color, char in pairs(gameState.activeChars) do
        local ss = startStats[color]
        if ss then
            local function delta(now, was) return now - was end
            local function fmt(now, was)
                local d = delta(now, was)
                if d > 0 then return was .. " -> " .. now .. " (+" .. d .. ")"
                elseif d < 0 then return was .. " -> " .. now .. " (" .. d .. ")"
                else return tostring(now) .. " (unchanged)" end
            end
            table.insert(statLines, char.name .. ":  H:" .. fmt(char.health, ss.health) ..
                "  Hu:" .. fmt(char.hunger, ss.hunger) ..
                "  S:" .. fmt(char.sanity, ss.sanity))
        end
    end
    if #statLines > 0 then
        body = body .. "Stat Changes:\n" .. table.concat(statLines, "\n") .. "\n\n"
    end

    if #damage > 0 then
        body = body .. "Losses:\n" .. table.concat(damage, "\n") .. "\n\n"
    end
    if #gains > 0 then
        body = body .. "Gains:\n" .. table.concat(gains, "\n") .. "\n\n"
    end
    body = body .. "Next: Day " .. (gameState.day + 1) .. " Dawn"

    -- Truncate if too long
    if #body > 800 then
        body = body:sub(1, 800) .. "\n..."
    end

    UI.setAttribute("summaryTitle", "text", title)
    UI.setAttribute("summaryBody", "text", body)
    UI.show("summaryPanel")

    -- Auto-dismiss after 8 seconds
    Wait.time(function()
        UI.hide("summaryPanel")
    end, 8.0)
end

function onSummaryClose(player, value, id)
    UI.hide("summaryPanel")
end

-----------------------------------------------------------------------
-- G.7 ��� Tooltips on every interactable
-- Runs at end of Setup to populate descriptions from tag data
-----------------------------------------------------------------------
TOOLTIP_DATA = {
    -- Resources
    ["Resource:Wood"]        = "Wood — found at Basketball/Badminton Courts. Used in crafting and as fuel.",
    ["Resource:Metal"]       = "Metal — found at Basketball Court and Rayman's House. Used in weapons and tools.",
    ["Resource:Cloth"]       = "Cloth — found at all locations. Used in bandages, insulation, bedrolls.",
    ["Resource:Food"]        = "Food — found at all locations (esp. Ellie & Luca's). Restores Hunger; cook for greater effect.",
    ["Resource:EnergyDrink"] = "Energy Drink — found at James's House only. Restores 2 Sanity. James's addiction.",
    ["Resource:Battery"]     = "Battery — found at James's/Rayman's. Powers Flashlights, Radios, electronics.",
    -- Markers
    ["DoomMarker"]           = "Doom Marker. Current: {doom} / 30. Next threshold: {thresh}.",
    ["DayCounter"]           = "Day Counter. Current: Day {day} of 7.",
    -- Decks
    ["MarketCardDeck"]       = "Market Deck. Craft items by spending resources. 5 face-up in the display.",
    ["ThreatCardDeck"]       = "Threat Deck. Drawn at Night. Soft threats resolve instantly; Hard ones must be fought.",
    ["VisitorCardDeck"]      = "Visitor Deck. Absent characters may arrive via Dawn cards.",
    -- Supply
    ["TelltaleHeartSupply"]  = "Telltale Hearts (5 max). Cook: 1 Cloth + 1 Battery + 1 Food + 2 Health. Use to revive a Down character.",
    -- Locations
    ["Location:JamesHouse"]       = "James's House. Yields: Energy Drink, Battery, Junk Food. The Den: free trade once/day.",
    ["Location:RaymanHouse"]      = "Rayman's House. Yields: Sports Equipment, Sports Drink. The Garage: Rest +1 Health.",
    ["Location:EllieLucaHouse"]   = "Ellie & Luca's House. Yields: Food, Cloth, Pantry. The Kitchen: permanent Crockpot.",
    ["Location:BasketballCourt"]  = "Basketball Court. Yields: Wood, Metal, Cloth. Echoes: d6 on gather (6=bonus, 1-2=Sanity loss).",
    ["Location:BadmintonCourt"]   = "Badminton Court. Yields: Cloth, Wood, Metal. The Net: +1 die defending.",
    -- Severity Legend
    ["SeverityLegend"]       = "Severity dot legend: 1=flavor, 2=minor, 3=combat, 4=phase-shift, 5=boss/apocalyptic.",
}

function applyTooltips()
    for _, obj in ipairs(getAllObjects()) do
        for tag, tip in pairs(TOOLTIP_DATA) do
            if obj.hasTag(tag) then
                local desc = tip
                -- Substitute dynamic values
                desc = desc:gsub("{doom}", tostring(gameState.doom))
                desc = desc:gsub("{thresh}", tostring(getNextDoomThreshold() or 30))
                desc = desc:gsub("{day}", tostring(gameState.day))
                obj.setDescription(desc)
                break
            end
        end
    end
end

-----------------------------------------------------------------------
-- Refresh dynamic tooltips (called periodically or on state change)
-----------------------------------------------------------------------
function refreshDynamicTooltips()
    -- Update Doom marker tooltip
    local doomMarker = getDoomMarker()
    if doomMarker then
        local nextT = getNextDoomThreshold() or 30
        doomMarker.setDescription("Doom: " .. gameState.doom .. " / 30. Next threshold at " .. nextT .. ".")
    end

    -- Update Day counter tooltip
    local dayCounter = getDayCounter()
    if dayCounter then
        dayCounter.setDescription("Day " .. gameState.day .. " of 7.")
    end
end
