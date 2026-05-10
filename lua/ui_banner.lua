-- ui_banner.lua  (G.1 Phase Banner refresh + G.2 Active-Player Indicator + G.8 broadcast)

-----------------------------------------------------------------------
-- Phase names for display
-----------------------------------------------------------------------
PHASE_NAMES = {
    [1] = "Dusk of the Week",
    [2] = "Strange Days",
    [3] = "Long Nights",
    [4] = "Final Hours",
}

-----------------------------------------------------------------------
-- Day-specific flavor text (shown in phase banner)
-----------------------------------------------------------------------
DAY_FLAVOR = {
    [1] = "The first night was strange.",
    [2] = "You tell yourself it was nothing.",
    [3] = "The street feels longer than it used to.",
    [4] = "You've stopped counting the sounds.",
    [5] = "Nobody came. Nobody is coming.",
    [6] = "The walls breathe if you listen closely.",
    [7] = "One way or another, it ends today.",
}

-----------------------------------------------------------------------
-- G.1 — Refresh the Phase Banner with current gameState
-----------------------------------------------------------------------
function refreshPhaseBanner()
    if not UI then return end  -- guard against early calls

    -- Day field with flavor text
    local dayText = "Day " .. gameState.day .. " of 7"
    local flavor = DAY_FLAVOR[gameState.day]
    if flavor and gameState.started then
        dayText = dayText .. "  —  " .. flavor
    end
    UI.setAttribute("bannerDay", "text", dayText)

    -- Phase field
    local phaseName = PHASE_NAMES[gameState.phase] or ("Phase " .. gameState.phase)
    UI.setAttribute("bannerPhase", "text", phaseName)

    -- Doom field with next threshold
    local nextThresh = getNextDoomThreshold()
    local doomText = "Doom " .. gameState.doom .. " / 30"
    if nextThresh then
        doomText = doomText .. "  (next: " .. nextThresh .. ")"
    end
    UI.setAttribute("bannerDoom", "text", doomText)

    -- Doom color: yellow normally, orange at 15+, red at 25+
    if gameState.doom >= 25 then
        UI.setAttribute("bannerDoom", "color", "#FF5555")
    elseif gameState.doom >= 15 then
        UI.setAttribute("bannerDoom", "color", "#FF8844")
    else
        UI.setAttribute("bannerDoom", "color", "#FFDD66")
    end

    -- Active player field
    local activeText = "— " .. (gameState.subPhase or "pre-game") .. " —"
    if gameState.activeColor then
        local char = gameState.activeChars[gameState.activeColor]
        if char then
            activeText = char.name .. "'s turn"
        end
    end
    UI.setAttribute("bannerActive", "text", activeText)

    -- Next action suggestion (I.8)
    UI.setAttribute("bannerNext", "text", recommendNext())

    -- Refresh stat display and action bar
    refreshStatDisplay()
    refreshActionBar()
end

function getNextDoomThreshold()
    local thresholds = {10, 15, 20, 25, 30}
    for _, t in ipairs(thresholds) do
        if gameState.doom < t then return t end
    end
    return nil
end

-----------------------------------------------------------------------
-- I.8 — Recommend the next action based on sub-phase
-----------------------------------------------------------------------
function recommendNext()
    local sp = gameState.subPhase or "PreGame"

    if sp == "PreGame" then
        return "Click Setup to begin"
    elseif sp == "Dawn" then
        return "Dawn phase — revealing Dawn card..."
    elseif sp == "Day" then
        if gameState.activeColor then
            local char = gameState.activeChars[gameState.activeColor]
            if char and char.actionsLeft > 0 then
                return "Take an action (" .. char.actionsLeft .. " left)"
            else
                return "Click Pass to end your turn"
            end
        end
        return "Day phase"
    elseif sp == "Dusk" then
        return "Declare your sleep location"
    elseif sp == "Night" then
        return "Night — resolving threats and sleep"
    elseif sp == "Tick" then
        return "End-of-round processing..."
    elseif sp == "GameOver" then
        return "Game over. Click Restart to play again."
    end
    return ""
end

-----------------------------------------------------------------------
-- G.2 — Active-Player Indicator (4 channels)
-----------------------------------------------------------------------
local bobTimerId = nil

function updateActivePlayerIndicator()
    local activeColor = gameState.activeColor

    -- Channel 1: Banner (handled by refreshPhaseBanner)

    -- Channel 2: Hand zone glow
    for _, color in ipairs({"White", "Red", "Yellow", "Green", "Blue"}) do
        local zone = getHandZone(color)
        if zone then
            if color == activeColor then
                zone.setColorTint(stringToColorTint(color))
            else
                zone.setColorTint({0.15, 0.15, 0.15})
            end
        end
    end

    -- Channel 3: Standee bob (cancel previous, start new)
    stopStandeeBob()
    if activeColor then
        local char = gameState.activeChars[activeColor]
        if char and not char.down then
            startStandeeBob(char.name)
        end
    end

    -- Channel 4: Board brightness
    for color, char in pairs(gameState.activeChars) do
        local board = getPlayerBoard(char.name)
        if board then
            if color == activeColor then
                board.setColorTint({1.0, 1.0, 1.0})
            else
                board.setColorTint({0.6, 0.6, 0.6})
            end
        end
    end
end

function stringToColorTint(color)
    local tints = {
        White  = {0.9, 0.9, 0.9},
        Red    = {0.9, 0.3, 0.3},
        Yellow = {0.9, 0.9, 0.3},
        Green  = {0.3, 0.9, 0.3},
        Blue   = {0.3, 0.5, 0.9},
    }
    return tints[color] or {0.5, 0.5, 0.5}
end

-----------------------------------------------------------------------
-- Standee bob animation (Channel 3)
-----------------------------------------------------------------------
function startStandeeBob(charName)
    local standee = getCharacterStandee(charName)
    if not standee then return end

    local baseRot = standee.getRotation()
    local bobUp = true

    bobTimerId = Wait.time(function()
        if not standee or standee.isDestroyed() then
            stopStandeeBob()
            return
        end
        local r = standee.getRotation()
        if bobUp then
            standee.setRotationSmooth({r.x, r.y, 5}, false, false)
        else
            standee.setRotationSmooth({r.x, r.y, -5}, false, false)
        end
        bobUp = not bobUp
    end, 2.0, -1)  -- repeat every 2s indefinitely
end

function stopStandeeBob()
    if bobTimerId then
        Wait.stop(bobTimerId)
        bobTimerId = nil
    end
    -- Reset all standees to neutral rotation
    for _, char in pairs(gameState.activeChars) do
        local standee = getCharacterStandee(char.name)
        if standee and not standee.isDestroyed() then
            local r = standee.getRotation()
            standee.setRotationSmooth({r.x, r.y, 0}, false, false)
        end
    end
end

-----------------------------------------------------------------------
-- G.9 — Hand zone glow pulse at turn change
-----------------------------------------------------------------------
function pulseHandZone(color)
    local zone = getHandZone(color)
    if not zone then return end

    -- Brief bright flash then settle to active tint
    zone.setColorTint({1, 1, 1})
    Wait.time(function()
        zone.setColorTint(stringToColorTint(color))
    end, 0.5)
end
