-- ui_controls.lua  (G.6 Confirm dialog + resource picker + UI toggle +
-- G.7 Tooltips + G.10 Host controls. The Week in Review and its chronicle
-- moved to ui_week_review.lua when this file passed the ~500-line budget.)

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
    "charRoster", "duskPanel", "combatPanel", "msgLog", "whatNowPanel",
    "reactionsPanel", "achievementsBtn", "achievementsPanel", "achToast",
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
        -- The Trophies button is permanent furniture like the banner, so it
        -- comes back with it rather than waiting on a state change.
        UI.setAttribute("achievementsBtn", "active", "true")
        if achievementsPanelOpen then UI.show("achievementsPanel") end
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
    local color = gameState.activeColor
    if not color then return end
    -- Safety net (I.6): this button forfeits whatever the active player has
    -- not spent, and it is one click away from every host at all times.
    -- confirmEndDayEarly passes straight through when nothing is at stake.
    safecall(function()
        confirmEndDayEarly(color, function()
            safecall(function()
                endPlayerTurn(color)
                refreshPhaseBanner()
                updateActivePlayerIndicator()
            end, "EndTurn")
        end)
    end, "EndTurnConfirm")
end

function onHostRestart(player, value, id)
    showConfirm(
        "Restart the game?",
        "This will reset all progress. Are you sure?",
        function()
            -- The achievement vault is the one thing that outlives a game:
            -- it records what this TABLE has done, not what this week did.
            -- Carried across the reset by hand, because the reset builds a
            -- fresh table rather than clearing the old one.
            local keptAchievements = gameState.achievements

            -- Reset gameState through the SAME door as a restored save:
            -- migrateGameState() (global.lua) is the one place defaults are
            -- declared. This used to be a hand-copied literal, and it had
            -- already drifted — fields migrateGameState guarantees
            -- (resources, dailyAlerts, messageLog, haunted, threatDamage,
            -- cluesFound, duskPending, schemaVersion, …) were simply absent
            -- after a Restart. That survived only because callers are
            -- defensive; the next field added without an `or {}` at its read
            -- site would have been a Restart-only crash.
            -- tests/test_full_campaign.py::test_restart_state_matches_fresh_load
            -- fails if the two ever diverge again.
            gameState = { achievements = keptAchievements }
            migrateGameState()
            -- Restart-specific, after the call: the chronicle is the PREVIOUS
            -- game's record, so it must not survive into the new one.
            -- ensureChronicle() rebuilds it on first use.
            gameState.chronicle = nil
            safecall(function() cancelGuidedSetup() end, "CancelSetup")
            UI.hide("achievementsPanel")
            achievementsPanelOpen = false
            UI.hide("weekReviewPanel")
            UI.hide("combatPanel")
            broadcastEvent("phase", "Game reset. Click Setup to begin a new game.")
            refreshPhaseBanner()
            UI.hide("actionBar")
            UI.hide("statDisplay")
            UI.hide("duskPanel")

            -- Clear any lingering 3D board buttons. Setup is driven from the
            -- Host Controls panel (btnSetup) — no redundant board button.
            local board = getMainBoard()
            if board then board.clearButtons() end
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
    local body = "Doom: " .. gameState.doom .. " / " .. getDoomLimit() .. "\n"

    -- Reason attribution: the night/tick handlers already broadcast WHY each
    -- change happened ("X loses 2 Sanity from Charlie"). Group those lines
    -- under the character they name, so each stat drop shows its cause.
    local startStats = gameState.dayStartStats or {}
    local function fmt(now, was)
        local d = now - was
        if d > 0 then return was .. "→" .. now .. " (+" .. d .. ")"
        elseif d < 0 then return was .. "→" .. now .. " (" .. d .. ")"
        else return tostring(now) end
    end

    for color, char in pairs(gameState.activeChars) do
        local ss = startStats[color]
        body = body .. "\n" .. char.name .. (char.down and " [DOWN]" or "") .. "\n"
        if ss then
            body = body .. "  HP " .. fmt(char.health, ss.health) ..
                " · Hunger " .. fmt(char.hunger, ss.hunger) ..
                " · Sanity " .. fmt(char.sanity, ss.sanity) .. "\n"
        end
        -- Reasons: dayLog lines that mention this character by name.
        for _, entry in ipairs(gameState.dayLog or {}) do
            if (entry.category == "damage" or entry.category == "warn" or entry.category == "gain")
                and entry.message:find(char.name, 1, true) then
                body = body .. "    • " .. entry.message .. "\n"
            end
        end
    end

    -- Table-wide events that didn't name a character (Doom threshold, boss).
    local general = {}
    for _, entry in ipairs(gameState.dayLog or {}) do
        if entry.category == "warn" or entry.category == "damage" then
            local named = false
            for _, ch in pairs(gameState.activeChars) do
                if entry.message:find(ch.name, 1, true) then named = true; break end
            end
            if not named and (entry.message:find("Doom") or entry.message:find("THRESHOLD")
                or entry.message:find("boss") or entry.message:find("Boss")) then
                table.insert(general, "  • " .. entry.message)
            end
        end
    end
    if #general > 0 then
        body = body .. "\nThe wider night:\n" .. table.concat(general, "\n") .. "\n"
    end

    body = body .. "\nNext: Day " .. (gameState.day + 1) .. " Dawn — click Begin Day."

    if #body > 3500 then body = body:sub(1, 3500) .. "\n…" end

    UI.setAttribute("summaryTitle", "text", title)
    UI.setAttribute("summaryBody", "text", body)
    UI.show("summaryPanel")
    -- No auto-dismiss: the player clicks Continue when they've read it
    -- (playtest: end-of-day report vanished before it could be read).
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
    ["Resource:Provisions"]        = "Provisions — found at all locations (esp. Ellie & Luca's). Restores Hunger; cook for greater effect.",
    ["Resource:EnergyDrink"] = "Energy Drink — found at James's House only. Restores 2 Sanity. James's addiction.",
    ["Resource:Battery"]     = "Battery — found at James's/Rayman's. Powers Flashlights, Radios, electronics.",
    -- Markers
    -- {doomLimit} / {totalDays} follow the chosen difficulty — never
    -- hardcode 30 / 7 (Long Weekend is 15 / 3).
    ["DoomMarker"]           = "Doom Marker. Current: {doom} / {doomLimit}. Next threshold: {thresh}. Moves itself whenever Doom changes.",
    ["DayCounter"]           = "Day Counter. Current: Day {day} of {totalDays}.",
    -- Decks
    ["MarketCardDeck"]       = "Market Deck. Craft items by spending resources. 5 face-up in the display.",
    ["ThreatCardDeck"]       = "Threat Deck. Drawn at Night. Soft threats resolve instantly; Hard ones must be fought; Persistent ones stay on the tile applying their rule until you Fight, Pry or Clear them. Threats left on the map fester at Dawn: +1 Doom each (max +3); bosses +2 each, no cap.",
    ["VisitorCardDeck"]      = "Visitor Deck. Absent characters may arrive via Dawn cards.",
    -- Supply
    ["TelltaleHeartSupply"]  = "Telltale Hearts (5 max). Cook: 1 Cloth + 1 Battery + 1 Provisions + 2 Health. Use to revive a Down character.",
    ["ResourceBag"]          = "Resource supply bag (kept under the table). Fully automated — your held counts are tracked for you; Gather adds, Craft/Cleanse spend, no tokens to move.",
    ["PathVariant"]          = "Decorative path tiles for an alternate map layout. Safe to ignore during play.",
    -- Locations
    ["Location:JamesHouse"]       = "James's House. Yields: Energy Drink, Battery, Junk Food. The Den: free trade once/day.",
    ["Location:RaymanHouse"]      = "Rayman's House. Yields: Sports Equipment, Sports Drink. The Garage: Rest +1 Health.",
    ["Location:EllieLucaHouse"]   = "Ellie & Luca's House. Yields: Provisions, Cloth, Pantry. The Kitchen: permanent Crockpot.",
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
                -- Substitute dynamic values. Limits come from the difficulty
                -- helpers, never literals (Long Weekend is 3 days / Doom 15).
                desc = desc:gsub("{doom}", tostring(gameState.doom))
                desc = desc:gsub("{doomLimit}", tostring(getDoomLimit()))
                desc = desc:gsub("{thresh}", tostring(getNextDoomThreshold() or getDoomLimit()))
                desc = desc:gsub("{day}", tostring(gameState.day))
                desc = desc:gsub("{totalDays}", tostring(getTotalDays()))
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
