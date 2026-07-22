-- ui_help.lua  (H.3/H.4 Help panel 5 tabs + H.5 What-now hints + H.7 Why-disabled + H.8 Notebook)

-----------------------------------------------------------------------
-- H.3 — Help Panel Content (5 tabs)
--
-- The static text (HELP_QUICKSTART, HELP_GLOSSARY, NOTEBOOK_*) lives in
-- lua/notebook_data.lua, AUTO-GENERATED from content/notebook/*.md and
-- content/help/glossary.md — the player docs are single-sourced. Edit the
-- markdown, run scripts/generate_notebook.py, rebuild.
-----------------------------------------------------------------------

-- Dynamic content generators
function getHelpCharContent(player)
    local color = player and player.color or gameState.activeColor
    local char = color and gameState.activeChars[color]
    if not char then
        if not gameState.started then
            return "No character assigned yet. Complete Setup first."
        end
        -- Mid-game but this SEAT has no character (common in hotseat: one
        -- person on one seat driving several characters). Point at the fix
        -- instead of implying setup never happened.
        local lines = { "The " .. tostring(color) .. " seat has no character. This game's seats:" }
        for c, ch in pairs(gameState.activeChars) do
            table.insert(lines, "  " .. ch.name .. " — " .. c .. " seat")
        end
        table.insert(lines, "")
        table.insert(lines, "To act as one of them, switch to their seat: click your name in the player list (top right) and Change Color.")
        return table.concat(lines, "\n")
    end

    local text = char.name .. " — Current Stats:\n"
    text = text .. "Health: " .. char.health .. "/" .. char.maxHealth
    if char.health < 3 then text = text .. " [LOW!]" end
    text = text .. "\nHunger: " .. char.hunger .. "/" .. char.maxHunger
    if char.hunger < 3 then text = text .. " [LOW!]" end
    text = text .. "\nSanity: " .. char.sanity .. "/" .. char.maxSanity
    if char.sanity < 3 then text = text .. " [LOW!]" end
    text = text .. "\nLocation: " .. (char.location or "Unknown")
    if char.down then text = text .. "\n\n[DOWN - GHOST STATE]" end

    -- Add briefing text
    local briefing = CHAR_BRIEFINGS and CHAR_BRIEFINGS[char.name]
    if briefing then
        text = text .. "\n\n--- Character Info ---\n" .. briefing
    end

    return text
end

function getHelpDawnContent()
    local dawn = gameState.activeDawn
    if not dawn then return "No active Dawn card. The next Dawn card will be revealed when the host clicks Begin Day." end

    local text = "Active Dawn Card:\n" .. (dawn.title or dawn.id or "Unknown")
    text = text .. "\n\n" .. (dawn.description or "No description.")

    -- List ongoing effects
    local ongoings = {}
    for key, val in pairs(gameState.ongoingDawnEffects or {}) do
        if val then
            table.insert(ongoings, "- " .. key)
        end
    end
    if #ongoings > 0 then
        text = text .. "\n\nActive Ongoing Effects:\n" .. table.concat(ongoings, "\n")
    else
        text = text .. "\n\nNo ongoing effects active."
    end

    return text
end

function getHelpDoomContent()
    local text = "DOOM TRACK: " .. gameState.doom .. " / " .. getDoomLimit() .. "\n\n"

    text = text .. "Current phase doom rate: +" .. getDoomRate() .. " per day (scaled by player count)\n"
    text = text .. "Festering at Dawn: +1 per threat on the map (max +3); bosses +2 each, Treeguard +1 (no cap).\n\n"

    text = text .. "THRESHOLDS:\n"
    local thresholds = {
        {10, "Night threat draws +1 at all locations.", gameState.doom >= 10},
        {15, "Scarcity: every craft costs +1 extra resource (your choice).", gameState.doom >= 15},
        {20, "All characters lose +1 Sanity at Tick.", gameState.doom >= 20},
        {25, "Boss-level threats can appear in any phase.", gameState.doom >= 25},
        {30, "DEFEAT — the neighborhood is consumed.", gameState.doom >= 30},
    }

    for _, t in ipairs(thresholds) do
        local marker = t[3] and "[ACTIVE] " or "         "
        text = text .. marker .. t[1] .. ": " .. t[2] .. "\n"
    end

    text = text .. "\nCLEANSE ACTION:\n"
    text = text .. "Spend 1 action + 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink -> Doom -2\n"

    local nextT = getNextDoomThreshold()
    if nextT then
        local remaining = nextT - gameState.doom
        text = text .. "\nNext threshold in " .. remaining .. " steps."
    end

    return text
end

-----------------------------------------------------------------------
-- H.4 — Help panel tab switching
-----------------------------------------------------------------------
local currentHelpTab = "quick"

function onHelpClick(player, value, id)
    local visible = UI.getAttribute("helpPanel", "active")
    if visible == "true" then
        UI.hide("helpPanel")
    else
        refreshHelpPanel(player)
        UI.show("helpPanel")
    end
end

function onHelpClose(player, value, id)
    UI.hide("helpPanel")
end

function onHelpTab(player, value, id)
    if id == "helpTabQuick" then currentHelpTab = "quick"
    elseif id == "helpTabChar" then currentHelpTab = "char"
    elseif id == "helpTabDawn" then currentHelpTab = "dawn"
    elseif id == "helpTabDoom" then currentHelpTab = "doom"
    elseif id == "helpTabGlossary" then currentHelpTab = "glossary"
    end

    refreshHelpPanel(player)
end

function refreshHelpPanel(player)
    -- Highlight active tab
    local tabs = {"helpTabQuick", "helpTabChar", "helpTabDawn", "helpTabDoom", "helpTabGlossary"}
    local tabKeys = {"quick", "char", "dawn", "doom", "glossary"}
    for i, tabId in ipairs(tabs) do
        if tabKeys[i] == currentHelpTab then
            UI.setAttribute(tabId, "color", "#14323CE6")
            UI.setAttribute(tabId, "textColor", "#88DDFF")
        else
            UI.setAttribute(tabId, "color", "#142828CC")
            UI.setAttribute(tabId, "textColor", "#AACCCC")
        end
    end

    local title = ""
    local body = ""

    if currentHelpTab == "quick" then
        title = "Quick Start"
        body = HELP_QUICKSTART
    elseif currentHelpTab == "char" then
        title = "Your Character"
        body = getHelpCharContent(player)
    elseif currentHelpTab == "dawn" then
        title = "Active Dawn Card"
        body = getHelpDawnContent()
    elseif currentHelpTab == "doom" then
        title = "Doom Track"
        body = getHelpDoomContent()
    elseif currentHelpTab == "glossary" then
        title = "Glossary"
        body = HELP_GLOSSARY
    end

    UI.setAttribute("helpTabTitle", "text", title)
    UI.setAttribute("helpBody", "text", body)
end

-----------------------------------------------------------------------
-- H.5 — "What now?" context-aware hint system
--
-- The WHATNOW_HINTS table itself is auto-generated from
-- content/help/whatnow_hints.md by scripts/generate_whatnow_hints.py.
-- The dispatch below picks the right entries based on game state.
--
-- Group keys (in WHATNOW_HINTS):
--   PreGame, Dawn, Day, Dusk, Night, Tick, PostGame   (sub-phase bases)
--   Stats                                              (low_hunger / sanity / health / critical_any)
--   James | Coco | Rayman | Ellie | Luca               (per-character)
--   Location                                           (at_own_house / at_kitchen_not_ellie / at_basketball_court / at_badminton_court)
--   Strategic                                          (doom_high / ally_down / no_light_source / market_good_item / enemy_at_location)
-----------------------------------------------------------------------

local function _appendHint(hint, line, char)
    if not line or line == "" then return hint end
    local rendered = substitutePlaceholders(line, char)
    if hint == "" then return rendered end
    return hint .. "\n" .. rendered
end

function onWhatNowClick(player, value, id)
    local color = player.color
    local char = gameState.activeChars[color]
    local sp = gameState.subPhase or "PreGame"
    -- The Lua subPhase uses "GameOver"; the markdown groups it under "PostGame".
    -- "PreDawn" (the pause between Tick and the next Begin Day) uses the Tick
    -- group's between_days hint.
    local groupKey = sp
    if sp == "GameOver" then groupKey = "PostGame" end
    if sp == "PreDawn" then groupKey = "Tick" end

    -- 1) Phase-base hint
    local phaseHints = WHATNOW_HINTS[groupKey] or WHATNOW_HINTS.PreGame or {}
    local base = phaseHints.default or ""

    -- Post-game: pick the hint matching how the game actually ended
    -- (victory / defeat_doom / defeat_down / defeat_source).
    if groupKey == "PostGame" and gameState.gameOverCause then
        base = phaseHints[gameState.gameOverCause] or base
    end

    -- Day no-actions override
    if sp == "Day" and char and (char.actionsLeft or 0) <= 0 then
        base = phaseHints.no_actions or base
    end
    -- Between-days override
    if sp == "PreDawn" then
        base = phaseHints.between_days or base
    end

    local hint = ""
    hint = _appendHint(hint, base, char)

    if char then
        -- 2) Character-specific Day hints
        if sp == "Day" then
            local charHints = WHATNOW_HINTS[char.name] or {}

            if char.name == "James" and not gameState.jamesEnergyDrinkUsed then
                hint = _appendHint(hint, charHints.james_no_energy_drink, char)
            end
            if char.name == "James" and not gameState.jamesPeekUsed then
                hint = _appendHint(hint, charHints.james_has_peek, char)
            end
            if char.name == "Luca" and not gameState.lucaRallyUsed then
                hint = _appendHint(hint, charHints.luca_rally_unused, char)
            end

            -- Signature nudge (§6.7): from Day 5 on, remind holders that the
            -- big move is still in the tank — the finale is what it's for.
            if not char.signatureUsed and gameState.day >= 5 then
                hint = _appendHint(hint, charHints.signature_unused, char)
            end

            if char.name == "Rayman" and (char.location or ""):find("Basketball") then
                hint = _appendHint(hint, charHints.rayman_at_court, char)
            end
            if char.name == "Rayman" and char.hunger > 0 and char.hunger < 4 then
                hint = _appendHint(hint, charHints.rayman_hungry, char)
            end

            if char.name == "Ellie" and char.location == "EllieLucaHouse" then
                hint = _appendHint(hint, charHints.ellie_at_kitchen, char)
            end

            -- Coco / Luca alone check
            if char.name == "Coco" or char.name == "Luca" then
                local othersHere = 0
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location == char.location then
                        othersHere = othersHere + 1
                    end
                end
                if othersHere == 0 then
                    if char.name == "Coco" then
                        hint = _appendHint(hint, charHints.coco_alone, char)
                    else
                        hint = _appendHint(hint, charHints.luca_alone, char)
                    end
                end
            end
        end

        -- 3) Stat warnings (Stats group)
        local stats = WHATNOW_HINTS.Stats or {}
        if char.hunger > 0 and char.hunger < 3 then
            hint = _appendHint(hint, stats.low_hunger, char)
        end
        if char.sanity > 0 and char.sanity < 3 then
            hint = _appendHint(hint, stats.low_sanity, char)
        end
        if char.health > 0 and char.health < 3 then
            hint = _appendHint(hint, stats.low_health, char)
        end

        -- 4) Strategic
        local strat = WHATNOW_HINTS.Strategic or {}
        if gameState.doom >= 20 then
            hint = _appendHint(hint, strat.doom_high, char)
        end
        for c2, ch2 in pairs(gameState.activeChars) do
            if ch2.down then
                hint = _appendHint(hint, strat.ally_down, char)
                break
            end
        end

        -- 5) Location (only during Day; Dusk/Night have their own bases)
        if sp == "Day" and char.location then
            local locHints = WHATNOW_HINTS.Location or {}
            local home = CHARACTER_HOMES and CHARACTER_HOMES[char.name]
            if home and home == char.location then
                hint = _appendHint(hint, locHints.at_own_house, char)
            end
            if char.location == "EllieLucaHouse" and char.name ~= "Ellie" then
                hint = _appendHint(hint, locHints.at_kitchen_not_ellie, char)
            end
            if char.location == "BasketballCourt" then
                hint = _appendHint(hint, locHints.at_basketball_court, char)
            elseif char.location == "BadmintonCourt" then
                hint = _appendHint(hint, locHints.at_badminton_court, char)
            end
        end
    end

    -- Into the What-now panel, not a broadcast: broadcasts render behind
    -- the Phase Banner and fade before they can be read. The panel stays
    -- until "Got it", and is visible only to the asking player.
    if UI then
        UI.setAttribute("whatNowBody", "text", hint)
        UI.setAttribute("whatNowPanel", "visibility", color)
        UI.show("whatNowPanel")
    end
    -- Chat copy so the hint also survives in the persistent chat log.
    printToColor(hint, color, BROADCAST_COLORS.gain)
end

function onWhatNowClose(player, value, id)
    UI.hide("whatNowPanel")
end

function substitutePlaceholders(text, char)
    if char then
        text = text:gsub("{name}", char.name or "?")
        text = text:gsub("{actionsLeft}", tostring(char.actionsLeft or 0))
        text = text:gsub("{location}", char.location or "?")
        text = text:gsub("{hunger}", tostring(char.hunger or 0))
        text = text:gsub("{health}", tostring(char.health or 0))
        text = text:gsub("{sanity}", tostring(char.sanity or 0))
    end
    text = text:gsub("{doom}", tostring(gameState.doom or 0))
    text = text:gsub("{day}", tostring(gameState.day or 1))
    return text
end

-----------------------------------------------------------------------
-- H.7 — Why-disabled tooltips on action buttons
-----------------------------------------------------------------------
function refreshActionButtonReasons(color)
    local char = gameState.activeChars[color]
    if not char then return end

    local noActions = char.actionsLeft <= 0
    local loc = char.location or ""
    local hasCrockpot = (loc == "EllieLucaHouse")
    local tooHungry = char.hunger < 3

    -- Update tooltips on disabled buttons with reasons
    if noActions then
        setActionTooltip("actMove", "No actions remaining. Click Pass.")
        setActionTooltip("actGather", "No actions remaining. Click Pass.")
        setActionTooltip("actCraft", "No actions remaining. Click Pass.")
        setActionTooltip("actCook", "No actions remaining. Click Pass.")
        setActionTooltip("actFight", "No actions remaining. Click Pass.")
        setActionTooltip("actRest", "No actions remaining. Click Pass.")
        setActionTooltip("actCleanse", "No actions remaining. Click Pass.")
        setActionTooltip("actTrade", "Trade is still free once per turn at your tile — even with 0 actions.")
        setActionTooltip("actUndo", "Undo your last action's stat, position, and Doom changes.")
    else
        setActionTooltip("actMove", "Move to an adjacent location. Costs 1 action + 1 Hunger.")
        setActionTooltip("actGather", "Gather 1 resource from this location. Costs 1 action.")
        setActionTooltip("actCraft", "Craft an item from the Market. Costs 1 action + resources.")

        if hasCrockpot then
            setActionTooltip("actCook", "Cook a recipe at the Crockpot. Costs 1 action + ingredients.")
        else
            setActionTooltip("actCook", "No Crockpot here. Move to Ellie & Luca's House to cook.")
        end

        if tooHungry then
            setActionTooltip("actFight", "Too hungry to fight (Hunger below 3). Eat first.")
        else
            setActionTooltip("actFight", "Fight a threat at this location. Costs 1 action.")
        end

        setActionTooltip("actRest", "Rest: +1 Hunger or +2 Sanity. At your own house: also +1 Health.")
        setActionTooltip("actCleanse", "Cleanse Doom -2. Costs 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink.")
        setActionTooltip("actTrade", "Trade with another player. Free once per turn at your tile; otherwise 1 action.")
        setActionTooltip("actUndo", "Undo your last action's stat, position, and Doom changes (once per action).")
    end
end

function setActionTooltip(buttonId, text)
    -- Feeds the delayed actionTooltip panel (ui_actionbar.lua) rather than
    -- the native tooltip attribute: the native one shows instantly, semi-
    -- transparent, directly on top of the action bar.
    ACTION_TOOLTIPS[buttonId] = text
end

-----------------------------------------------------------------------
-- H.8 — Notebook tab population. Tab bodies (NOTEBOOK_*) come from
-- lua/notebook_data.lua (generated from content/notebook/*.md).
-----------------------------------------------------------------------
function populateNotebook()
    if not Notes then return end

    Notes.setNotebookTabs({
        {
            title = "Quick Start",
            body  = NOTEBOOK_QUICKSTART,
            color = "Grey",
        },
        {
            title = "Full Rules",
            body  = NOTEBOOK_FULL_RULES,
            color = "Grey",
        },
        {
            title = "Characters",
            body  = NOTEBOOK_CHARACTERS,
            color = "Grey",
        },
    })
end
