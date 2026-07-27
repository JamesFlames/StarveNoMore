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
-- Night omen — the VISUAL TWIN of the Dusk growl (Design §15.8).
--
-- Night Sounds used to be audio-only, which made it the one place the
-- game's double-coding discipline lapsed: "the next threat is Hard" is a
-- gameable bit ("veterans learn to brace" is the design's own phrasing),
-- and it was unavailable to deaf and hard-of-hearing players, to anyone
-- muted, and to anyone in voice chat with game audio down — a large slice
-- of a virtual-tabletop audience. §18.19 item 2 now forbids that.
--
-- The twin must carry the same bit and NO MORE: not which threat, not
-- where. A waning-moon glyph in the banner is exactly as non-specific as
-- the growl, so the design intent (dread without data) survives the fix.
-- U+25D0 is Geometric Shapes, the same block as the ■ and ▸ the UI already
-- renders — not an emoji, which TTS's font does not reliably carry.
-----------------------------------------------------------------------
NIGHT_OMEN_GLYPH = "◐"

function setNightOmen(on)
    gameState.nightOmen = on and true or false
    if UI then
        UI.setAttribute("bannerOmen", "text", on and NIGHT_OMEN_GLYPH or "")
    end
end

-----------------------------------------------------------------------
-- G.1 — Refresh the Phase Banner with current gameState
-----------------------------------------------------------------------
function refreshPhaseBanner()
    if not UI then return end  -- guard against early calls

    -- The omen is banner state, so a reload mid-Dusk must not silently drop
    -- the only visual channel a muted player has.
    UI.setAttribute("bannerOmen", "text",
                    gameState.nightOmen and NIGHT_OMEN_GLYPH or "")

    -- Day field with flavor text
    local dayText = "Day " .. gameState.day .. " of " .. getTotalDays()
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
    local doomText = "Doom " .. gameState.doom .. " / " .. getDoomLimit()
    if nextThresh then
        doomText = doomText .. "  (next: " .. nextThresh .. ")"
    end
    UI.setAttribute("bannerDoom", "text", doomText)

    -- The physical marker follows the Doom value wherever it changed
    -- (dawn ticks, festering, cleanse, boss kills, dawn effects) — every
    -- one of those paths refreshes the banner. No-op when already there.
    safecall(function() moveDoomMarker(gameState.doom) end, "DoomMarker")

    -- Doom color: yellow normally, orange at 15+, red at 25+
    if gameState.doom >= 25 then
        UI.setAttribute("bannerDoom", "color", "#FF5555")
    elseif gameState.doom >= 15 then
        UI.setAttribute("bannerDoom", "color", "#FF8844")
    else
        UI.setAttribute("bannerDoom", "color", "#FFDD66")
    end

    -- Active player field
    local spLabel = gameState.subPhase or "pre-game"
    if spLabel == "PreDawn" then spLabel = "between days" end
    local activeText = "— " .. spLabel .. " —"
    if gameState.activeColor then
        local char = gameState.activeChars[gameState.activeColor]
        if char then
            -- Include the seat colour so "whose turn" is unambiguous even
            -- when one person drives several characters (hotseat).
            activeText = char.name .. "'s turn (" .. gameState.activeColor .. ")"
        end
    end
    UI.setAttribute("bannerActive", "text", activeText)

    -- Next action suggestion (I.8)
    UI.setAttribute("bannerNext", "text", recommendNext())

    -- Refresh stat display and action bar
    refreshStatDisplay()
    refreshActionBar()
    refreshCharRoster()
    refreshStandeeTooltips()

    -- "Rules in effect" panel + day-cycle strip + Dawn checklist (ui_rules.lua)
    safecall(function() refreshRulesPanel() end, "RulesPanel")
    safecall(function() refreshCycleStrip() end, "CycleStrip")
    safecall(function() refreshDawnChecklist() end, "DawnChecklist")

    -- Off-turn reactions (ui_reactions.lua): Witness, Luca's off-turn Rally.
    -- Refreshed here so a reaction appears the moment it becomes available —
    -- an off-turn option nobody notices is not a downtime cure.
    safecall(function() refreshReactionsPanel() end, "Reactions")

    -- Host Controls show only the buttons valid right now (ui_controls.lua)
    safecall(function() refreshHostControls() end, "HostControls")

    -- Pulse the next clickable thing so it's not just text-described
    highlightCTA(getNextCTA())
end

-----------------------------------------------------------------------
-- All-characters roster panel (Design §10.2 — "any player can glance
-- at any other player's board and see their stats"). Always-visible
-- once the game is started; dims down characters; hides rows for
-- inactive characters (3- or 4-player games).
-----------------------------------------------------------------------
local ROSTER_NAMES = {"James", "Coco", "Rayman", "Ellie", "Luca"}

local function _pct(num, den)
    if not den or den <= 0 then return "0" end
    return tostring(math.floor(math.max(0, num) / den * 100))
end

function refreshCharRoster()
    if not UI then return end
    if customUIHidden then return end
    if not gameState.started then
        UI.hide("charRoster")
        return
    end
    UI.show("charRoster")

    -- Build a name -> color lookup for the current game.
    local nameToColor = {}
    for color, ch in pairs(gameState.activeChars or {}) do
        if ch and ch.name then nameToColor[ch.name] = color end
    end

    local shown = 0
    for _, name in ipairs(ROSTER_NAMES) do
        local color = nameToColor[name]
        local char = color and gameState.activeChars[color]
        local rowId = "rosterRow_" .. name
        if not char then
            -- Character is not in this game — hide their row entirely.
            UI.setAttribute(rowId, "active", "false")
        else
            shown = shown + 1
            UI.setAttribute(rowId, "active", "true")
            -- Dim the row if Down.
            if char.down then
                UI.setAttribute(rowId, "color", "#280A0A99")
                UI.setAttribute("rosterName_" .. name, "text", name .. " ✗")
            else
                UI.setAttribute(rowId, "color", "#14141480")
                UI.setAttribute("rosterName_" .. name, "text", name)
            end
            UI.setAttribute("rosterHealth_" .. name, "percentage", _pct(char.health, char.maxHealth))
            UI.setAttribute("rosterHealthVal_" .. name, "text", char.health .. "/" .. char.maxHealth)
            UI.setAttribute("rosterHunger_" .. name, "percentage", _pct(char.hunger, char.maxHunger))
            UI.setAttribute("rosterHungerVal_" .. name, "text", char.hunger .. "/" .. char.maxHunger)
            UI.setAttribute("rosterSanity_" .. name, "percentage", _pct(char.sanity, char.maxSanity))
            UI.setAttribute("rosterSanityVal_" .. name, "text", char.sanity .. "/" .. char.maxSanity)
        end
    end

    -- Fit the panel to the party: header (~30px) + one row (56px + 3 gap)
    -- per character actually in this game — a 3-player party gets a
    -- 3-row box, not a 5-row one.
    UI.setAttribute("charRoster", "height", tostring(30 + shown * 59))
end

-----------------------------------------------------------------------
-- Live standee tooltips (Option C): hovering a character standee in
-- the world shows that character's CURRENT Health/Hunger/Sanity, not
-- the starting values baked at build time.
-----------------------------------------------------------------------
function refreshStandeeTooltips()
    for color, char in pairs(gameState.activeChars or {}) do
        local standee = getCharacterStandee(char.name)
        if standee then
            local desc
            if char.down then
                desc = char.name .. " — DOWN (ghost). Use a Telltale Heart at this tile to revive."
            else
                desc = string.format("%s — Health %d/%d • Hunger %d/%d • Sanity %d/%d • At %s",
                    char.name,
                    char.health, char.maxHealth,
                    char.hunger, char.maxHunger,
                    char.sanity, char.maxSanity,
                    char.location or "?")
            end
            standee.setDescription(desc)
        end
    end
end

function getNextDoomThreshold()
    local thresholds = { DOOM_THRESHOLDS.night, DOOM_THRESHOLDS.scarcity,
                         DOOM_THRESHOLDS.tick, DOOM_THRESHOLDS.anyPhaseBosses,
                         getDoomLimit() }
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
        return "Scramble 1 tile (1 Hunger) or stay — then host clicks Resolve Night"
    elseif sp == "Night" then
        return "Night — resolving threats and sleep"
    elseif sp == "Tick" then
        return "End-of-round processing..."
    elseif sp == "PreDawn" then
        return "Host: click Begin Day to start Day " .. gameState.day
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
-- "Always-obvious next step": pulse the recommended CTA (Phase Banner I.x)
--
-- Toggles outlineSize between 0 and 4 with a warm accent color every 0.6s
-- on the XML element(s) the active player should click next. Mapping is in
-- getNextCTA() and is driven by gameState.subPhase + actionsLeft.
-----------------------------------------------------------------------
local _highlightHandle = nil
local _highlightIds = {}
local _highlightOn = false

function clearHighlight()
    if _highlightHandle then
        Wait.stop(_highlightHandle)
        _highlightHandle = nil
    end
    for _, id in ipairs(_highlightIds) do
        if UI then
            UI.setAttribute(id, "outlineSize", "0")
        end
    end
    _highlightIds = {}
    _highlightOn = false
end

function highlightCTA(ids)
    -- If the caller asked for the same set we're already pulsing, no-op.
    if ids and _highlightIds and #ids == #_highlightIds then
        local same = true
        for i, v in ipairs(ids) do
            if _highlightIds[i] ~= v then same = false; break end
        end
        if same then return end
    end

    clearHighlight()
    if not ids or #ids == 0 then return end

    _highlightIds = ids
    _highlightOn = false

    local function pulseStep()
        _highlightOn = not _highlightOn
        local size = _highlightOn and "4" or "0"
        for _, id in ipairs(_highlightIds) do
            if UI then
                UI.setAttribute(id, "outline", "#ffd966")
                UI.setAttribute(id, "outlineSize", size)
            end
        end
    end

    pulseStep()
    _highlightHandle = Wait.time(pulseStep, 0.6, -1)
end

function getNextCTA()
    local sp = gameState.subPhase or "PreGame"

    if sp == "PreGame" then
        return {"btnSetup"}
    elseif sp == "Day" then
        if gameState.activeColor then
            local char = gameState.activeChars and gameState.activeChars[gameState.activeColor]
            if char and (char.actionsLeft or 0) <= 0 then
                return {"actPass"}
            end
        end
        -- If exactly one action is on offer, point at THAT button rather than
        -- glowing the whole bar: with one option, "what can I do?" should have
        -- a one-button answer.
        local offered = {}
        for id, on in pairs(ENABLED_ACTIONS or {}) do
            if on then offered[#offered + 1] = id end
        end
        if #offered == 1 then return offered end
        return {"actionBar"}
    elseif sp == "Tick" or sp == "PreDawn" then
        return {"btnBeginDay"}
    elseif sp == "Dusk" then
        return {"btnResolveNight"}
    elseif sp == "Night" then
        return {"btnResolveNight"}
    elseif sp == "GameOver" then
        return {"btnRestart"}
    end
    -- Dawn auto-resolves through the dispatch.
    return {}
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
