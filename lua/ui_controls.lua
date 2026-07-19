-- ui_controls.lua  (G.6 Confirm dialog + G.7 Tooltips + G.10 Host controls)

-----------------------------------------------------------------------
-- G.6 — Confirm-before-spend dialog
-----------------------------------------------------------------------
local pendingConfirmCallback = nil
local pendingConfirmCancel   = nil

-- onCancel is optional: when given, "Cancel" runs it instead of just
-- aborting (e.g. the Stash confirm, where Cancel means "take the normal
-- random draw"). Without UI, the fallback takes the Confirm branch.
function showConfirm(title, body, onConfirm, onCancel)
    if not UI then
        -- Fallback: just execute
        if onConfirm then onConfirm() end
        return
    end
    UI.setAttribute("confirmTitle", "text", title)
    UI.setAttribute("confirmBody", "text", body)
    pendingConfirmCallback = onConfirm
    pendingConfirmCancel   = onCancel
    UI.show("confirmDialog")
end

function onConfirmYes(player, value, id)
    UI.hide("confirmDialog")
    pendingConfirmCancel = nil
    if pendingConfirmCallback then
        local cb = pendingConfirmCallback
        pendingConfirmCallback = nil
        safecall(function() cb() end, "ConfirmAction")
    end
end

function onConfirmNo(player, value, id)
    UI.hide("confirmDialog")
    pendingConfirmCallback = nil
    local cb = pendingConfirmCancel
    pendingConfirmCancel = nil
    if cb then
        safecall(function() cb() end, "ConfirmCancel")
    else
        broadcastEvent("proc", "Action cancelled.")
    end
end

-----------------------------------------------------------------------
-- Resource picker — a small 6-button chooser for the rare "pick any
-- resource" moments (Ellie's Knows the Pantry). Delivers `count` tokens
-- of the chosen type to the player's board. Without UI (headless), it
-- falls back to a sensible automatic draw so play never stalls.
-----------------------------------------------------------------------
local pendingResourcePick = nil   -- { color=, count= }

function showResourcePicker(color, count, prompt)
    count = count or 1
    if not UI then
        local ch = gameState.activeChars[color]
        gatherRandomResources(color, (ch and ch.location) or "EllieLucaHouse", count)
        return
    end
    pendingResourcePick = { color = color, count = count }
    UI.setAttribute("resourcePickTitle", "text", prompt or "Take which resource?")
    UI.setAttribute("resourcePickBody", "text", "Choose a resource — " .. count ..
        " token(s) go straight to your board.")
    UI.show("resourcePickerDialog")
    broadcastToColor("Pick your resources from the panel — no bag to rummage through.",
        color, BROADCAST_COLORS.proc)
end

function onResourcePickClick(player, value, id)
    UI.hide("resourcePickerDialog")
    local pick = pendingResourcePick
    pendingResourcePick = nil
    if not pick or pick.color ~= player.color then return end
    local char = gameState.activeChars[pick.color]
    giveResource(pick.color, value, pick.count)
    local who = (char and char.name) or pick.color
    broadcastEvent("gain", who .. " takes " .. pick.count .. " " ..
        (value == "EnergyDrink" and "Energy Drink" or value) ..
        " (delivered to your board).")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onResourcePickCancel(player, value, id)
    UI.hide("resourcePickerDialog")
    local pick = pendingResourcePick
    pendingResourcePick = nil
    if not pick then return end
    local char = gameState.activeChars[pick.color]
    gatherRandomResources(pick.color, (char and char.location) or "EllieLucaHouse", pick.count)
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

-----------------------------------------------------------------------
-- Custom-UI toggle: one always-visible button hides/shows every panel
-- this mod draws, so the default TTS controls underneath (chat, drawing
-- tools, object context menus) are reachable. The refresh functions all
-- early-out while customUIHidden is true, so a phase change can't
-- resurrect a panel behind the player's back.
-----------------------------------------------------------------------
customUIHidden = false

CUSTOM_UI_PANELS = {
    "phaseBanner", "cycleStrip", "dawnChecklist", "hostControls",
    "rulesPanel", "actionBar", "actionTooltip", "statDisplay",
    "charRoster", "duskPanel", "combatPanel",
}

function onToggleCustomUI(player, value, id)
    customUIHidden = not customUIHidden
    if customUIHidden then
        for _, panelId in ipairs(CUSTOM_UI_PANELS) do
            UI.setAttribute(panelId, "active", "false")
        end
        UI.setAttribute("uiToggle", "text", "Show UI")
        broadcastEvent("proc", "Custom panels hidden — the standard Tabletop Simulator controls are free. Click 'Show UI' (top right) to bring them back.")
    else
        UI.setAttribute("uiToggle", "text", "Hide UI")
        -- The banner is always on; every state-driven panel (including
        -- Host Controls) returns via the normal refresh path.
        UI.setAttribute("phaseBanner", "active", "true")
        if gameState.subPhase == "Dusk" then UI.show("duskPanel") end
        refreshPhaseBanner()
        safecall(function() refreshCombatPanel() end, "CombatPanel")
    end
end

-----------------------------------------------------------------------
-- G.10 — Host control panel handlers
-- (The old onHostSetup, which ran the bare seat-order Setup(), is gone:
-- every UI path now goes through the guided walkthrough. The bare
-- Setup() remains for tests and console use only.)
-----------------------------------------------------------------------

-----------------------------------------------------------------------
-- Contextual Host Controls: only the buttons that are valid in the
-- current sub-phase are shown, and the panel shrinks to fit. Refreshed
-- from refreshPhaseBanner (ui_banner.lua) on every state change.
--   PreGame          → Setup
--   PreDawn          → Begin Day (+ Restart)
--   Day              → End Turn (+ Restart)
--   Dusk / Night     → Resolve Night (+ Restart; during Night it is the
--                      manual fallback if the automatic chain stalls)
--   Dawn / Tick      → nothing but Restart (both auto-advance)
--   GameOver         → Restart
-----------------------------------------------------------------------
function refreshHostControls()
    if not UI then return end
    if customUIHidden then return end
    local sp = gameState.subPhase or "PreGame"
    local show = {
        -- Hidden while the guided walkthrough runs: showing "Setup Game"
        -- next to "Pick Your Character" read as two competing instructions.
        btnSetup        = not gameState.started
                          and not (isGuidedSetupRunning and isGuidedSetupRunning()),
        btnBeginDay     = gameState.started and sp == "PreDawn",
        btnResolveNight = sp == "Dusk" or sp == "Night",
        btnEndTurn      = sp == "Day" and gameState.activeColor ~= nil,
        btnRestart      = gameState.started or sp == "GameOver",
    }
    local count = 0
    for id, on in pairs(show) do
        UI.setAttribute(id, "active", on and "true" or "false")
        if on then count = count + 1 end
    end
    -- No valid buttons right now (e.g. mid-walkthrough, auto-advancing
    -- phases before the first Restart) → no panel at all.
    if count == 0 then
        UI.setAttribute("hostControls", "active", "false")
        return
    end
    UI.setAttribute("hostControls", "active", "true")
    -- Title (~38px incl. padding) + one 38px button + 6px gap per row.
    UI.setAttribute("hostControls", "height", tostring(46 + count * 44))
end
function onHostBeginDay(player, value, id)
    if not gameState.started then
        broadcastToColor("Run Setup first.", player.color, BROADCAST_COLORS.damage)
        return
    end
    if gameState.subPhase ~= "PreDawn" then
        broadcastToColor("Begin Day is only available between days (currently: " ..
            tostring(gameState.subPhase) .. ").", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function()
        BeginDay()
        refreshPhaseBanner()
        updateActivePlayerIndicator()
    end, "BeginDay")
end

function onHostResolveNight(player, value, id)
    if gameState.subPhase == "Dusk" then
        -- Close the scramble window and start the Night phase.
        safecall(function() beginNight() end, "BeginNight")
        return
    end
    if gameState.subPhase ~= "Night" then
        broadcastToColor("Not in the Dusk or Night phase.", player.color, BROADCAST_COLORS.damage)
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
                turnStyle = "full", actedThisVisit = false,
                combatContext = nil,
                scenario = nil, scenarioFlags = {},
                dayLog = {}, activeDawn = nil,
                ongoingDawnEffects = {},
                activeChars = {},
                chronicle = nil,   -- lazily rebuilt by ensureChronicle()
            }
            safecall(function() cancelGuidedSetup() end, "CancelSetup")
            UI.hide("weekReviewPanel")
            UI.hide("combatPanel")
            broadcastEvent("phase", "Game reset. Click Setup to begin a new game.")
            refreshPhaseBanner()
            UI.hide("actionBar")
            UI.hide("statDisplay")
            UI.hide("duskPanel")

            -- Restore the board's 3D Setup button (cleared when clicked).
            local board = getMainBoard()
            if board then board.clearButtons() end
            safecall(function() createSetupButton() end, "SetupButton")
        end
    )
end

-- Help panel + What-now handlers are defined in ui_help.lua (Phase H)

-----------------------------------------------------------------------
-- Summary panel (I.4 stub)
-----------------------------------------------------------------------
function showEndOfDaySummary()
    -- Chronicle the day while its dayLog is still intact (wiped at next Dawn).
    safecall(function() recordDayInChronicle() end, "Chronicle")

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

    body = body .. "Doom: " .. gameState.doom .. " / " .. getDoomLimit() .. "\n\n"

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
-- Week in Review chronicle (design_batch1.md §3)
-- A persistent record across the whole campaign — dayLog is wiped each
-- Dawn, the chronicle is not. Accumulated by small hooks at sites that
-- already fire (cook, kill, Charlie, Down, revive, day-end), narrated
-- back at game end by showWeekInReview().
-----------------------------------------------------------------------
function ensureChronicle()
    -- Lazy init: saves from before the chronicle existed load cleanly.
    if not gameState.chronicle then
        gameState.chronicle = {
            days = {}, meals = {}, kills = {},
            peakDoom = { value = 0, day = 0 },
            maxCharlieStreak = { value = 0, name = "" },
            downs = 0, revives = 0,
            setup = {}, turns = {},
            beats = { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 },
        }
    end
    return gameState.chronicle
end

local BOSS_NAME_PATTERNS = { "deerclops", "eye of terror", "eyeofterror", "source", "treeguard" }

function recordKillInChronicle(threatName, colors)
    local ch = ensureChronicle()
    local who = {}
    for _, color in ipairs(colors or {}) do
        local c = gameState.activeChars[color]
        if c then table.insert(who, c.name) end
    end
    local lower = string.lower(threatName or "")
    local isBoss = false
    for _, p in ipairs(BOSS_NAME_PATTERNS) do
        if string.find(lower, p, 1, true) then isBoss = true break end
    end
    table.insert(ch.kills, { who = table.concat(who, " & "), threat = threatName or "?",
                             day = gameState.day, boss = isBoss })
end

function recordMealInChronicle(cookName)
    local ch = ensureChronicle()
    ch.meals[cookName] = (ch.meals[cookName] or 0) + 1
end

function recordCharlieInChronicle(charName, streak)
    local ch = ensureChronicle()
    if streak > ch.maxCharlieStreak.value then
        ch.maxCharlieStreak.value = streak
        ch.maxCharlieStreak.name = charName
    end
end

-- Called at day end (from showEndOfDaySummary), while the day's dayLog is
-- still intact — BeginDay wipes it at the next Dawn.
function recordDayInChronicle()
    local ch = ensureChronicle()
    local day = gameState.day

    local damageCount = 0
    local headline = nil
    for _, e in ipairs(gameState.dayLog or {}) do
        if e.category == "damage" then
            damageCount = damageCount + 1
            -- Headline precedence 1: somebody fell tonight.
            if not headline and (e.message:find("is DOWN") or e.message:find("is LOST")) then
                headline = e.message
            end
        end
    end
    -- Precedence 2: a boss fell today.
    if not headline then
        for _, k in ipairs(ch.kills) do
            if k.day == day and k.boss then
                headline = "The " .. k.threat .. " fell to " .. k.who .. "."
                break
            end
        end
    end
    -- Precedence 3: a bruising day / a quiet one.
    if not headline then
        if damageCount >= 4 then headline = "A bruising day — the neighborhood bit back " .. damageCount .. " times."
        elseif damageCount > 0 then headline = "The team took some knocks and kept moving."
        else headline = "A quiet day. Nobody trusted it." end
    end

    ch.days[day] = { headline = headline, damageTonight = damageCount }
    if gameState.doom > ch.peakDoom.value then
        ch.peakDoom.value = gameState.doom
        ch.peakDoom.day = day
    end
end

function showWeekInReview()
    -- The game can end before the day-end summary fires (victory/defeat are
    -- checked first in resolveTick) — chronicle the final day now. Safe to
    -- call twice: it overwrites the same day's entry.
    safecall(function() recordDayInChronicle() end, "Chronicle")

    local ch = ensureChronicle()
    local lines = {}

    for day = 1, 7 do
        local d = ch.days[day]
        if d then table.insert(lines, "Day " .. day .. " — " .. d.headline) end
    end
    if #lines > 0 then table.insert(lines, "") end

    -- The darkest night: most damage entries in one day.
    local worstDay, worstDmg = nil, 0
    for day, d in pairs(ch.days) do
        if d.damageTonight > worstDmg then worstDay, worstDmg = day, d.damageTonight end
    end
    if worstDay then
        table.insert(lines, "Darkest night: Day " .. worstDay .. " (" .. worstDmg .. " wounds and frights)")
    end

    -- Best kill: prefer a boss, else the last kill.
    local best = nil
    for _, k in ipairs(ch.kills) do
        if k.boss then best = k break end
    end
    if not best and #ch.kills > 0 then best = ch.kills[#ch.kills] end
    if best then
        table.insert(lines, "Best kill: " .. best.threat .. " — " .. best.who .. " (Day " .. best.day .. ")")
    end
    table.insert(lines, "Threats defeated: " .. #ch.kills)

    -- Camp mother: most meals cooked.
    local cook, meals = nil, 0
    for name, n in pairs(ch.meals) do
        if n > meals then cook, meals = name, n end
    end
    if cook then table.insert(lines, "Kept everyone fed: " .. cook .. " (" .. meals .. " meals)") end

    if ch.maxCharlieStreak.value > 0 then
        table.insert(lines, "Held the line in the dark: " .. ch.maxCharlieStreak.name ..
            " (" .. ch.maxCharlieStreak.value .. " night(s) of Charlie)")
    end
    table.insert(lines, "Doom high-water mark: " .. ch.peakDoom.value .. " / " .. getDoomLimit() .. " (Day " .. ch.peakDoom.day .. ")")
    if ch.downs > 0 then
        table.insert(lines, "The fallen: " .. ch.downs .. " down" .. (ch.revives > 0 and (" — " .. ch.revives .. " brought back") or ""))
    else
        table.insert(lines, "Nobody fell. Not once.")
    end

    local title = (gameState.gameOverCause == "victory") and "THE WEEK YOU SURVIVED" or "THE WEEK THAT TOOK YOU"
    local body = table.concat(lines, "\n")
    broadcastEvent("phase", "=== WEEK IN REVIEW ===")
    for _, l in ipairs(lines) do
        if l ~= "" then broadcastEvent("proc", l) end
    end

    if UI then
        UI.setAttribute("weekReviewTitle", "text", title)
        UI.setAttribute("weekReviewBody", "text", body)
        UI.show("weekReviewPanel")
    end
end

function onWeekReviewClose(player, value, id)
    UI.hide("weekReviewPanel")
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
    ["ThreatCardDeck"]       = "Threat Deck. Drawn at Night. Soft threats resolve instantly; Hard ones must be fought. Threats left on the map fester at Dawn: +1 Doom each (max +3); bosses +2 each, no cap.",
    ["VisitorCardDeck"]      = "Visitor Deck. Absent characters may arrive via Dawn cards.",
    -- Supply
    ["TelltaleHeartSupply"]  = "Telltale Hearts (5 max). Cook: 1 Cloth + 1 Battery + 1 Food + 2 Health. Use to revive a Down character.",
    ["ResourceBag"]          = "Resource supply bag (kept under the table). Fully automated — Gather delivers tokens to your board, and the Discard Tray returns what you spend.",
    ["DiscardTray"]          = "Discard Tray. Spending resources (craft costs, cook ingredients)? Drop the tokens here — they return to the supply by themselves.",
    ["PathVariant"]          = "Decorative path tiles for an alternate map layout. Safe to ignore during play.",
    -- Locations
    ["Location:JamesHouse"]       = "James's House. Yields: Energy Drink, Battery, Junk Food. The Den: free trade once/day.",
    ["Location:RaymanHouse"]      = "Rayman's House. Yields: Sports Equipment, Sports Drink. The Garage: Rest +1 Health.",
    ["Location:EllieLucaHouse"]   = "Ellie & Luca's House. Yields: Food, Cloth, Pantry. The Kitchen: permanent Crockpot.",
    ["Location:BasketballCourt"]  = "Basketball Court. Yields: Wood, Metal, Cloth. Echoes: d6 on gather (6=bonus, 1-2=Sanity loss). Moonlit Salvage: survive a night here, gather 2 at Dawn.",
    ["Location:BadmintonCourt"]   = "Badminton Court. Yields: Cloth, Wood, Metal. The Net: +1 die defending. Moonlit Salvage: survive a night here, gather 2 at Dawn.",
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
        doomMarker.setDescription("Doom: " .. gameState.doom .. " / " .. getDoomLimit() .. ". Next threshold at " .. nextT .. ".")
    end

    -- Update Day counter tooltip
    local dayCounter = getDayCounter()
    if dayCounter then
        dayCounter.setDescription("Day " .. gameState.day .. " of " .. getTotalDays() .. ".")
    end
end
