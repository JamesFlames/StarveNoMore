-- ui_help.lua  (H.3/H.4 Help panel 5 tabs + H.5 What-now hints + H.7 Why-disabled + H.8 Notebook)

-----------------------------------------------------------------------
-- H.3 — Help Panel Content (5 tabs)
-----------------------------------------------------------------------

-- Static content loaded as Lua strings (from content/ markdown files)
HELP_QUICKSTART = [[GOAL: Survive 7 nights. Doom < 30. Don't all go Down. And when The Source arrives (Days 6-7), destroy it — outlasting it is not enough.

EACH DAY:
1. Dawn - flip a Dawn card. Read it. Doom advances (+1 per threat left on the map, +2 per boss!).
2. Day - 3 actions each: Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free.
3. Dusk - last chance: scramble 1 tile (1 Hunger) or stay. You sleep where you stand.
4. Night - threats drawn. Fight or suffer. Charlie attacks the lightless.
5. Tick - lose 1 Hunger, 1 Sanity. Day advances.

THREE STATS:
- Health 0 = Down (ghost).
- Hunger 0 = starve (lose Health each Tick).
- Sanity 0 = Lost (also Down).
Below 3 in any stat: Bad Things Happen.

TRADE freely at the same tile - no action cost.

LIGHT: No light source at night = Charlie attack (2 Sanity + 1 Health, worse each consecutive dark night).

Hover anything for its rule. Click "?" for this menu. Click "What now?" if stuck.]]

HELP_GLOSSARY = [[STATS:
- Health: damage. 0 = Down.
- Hunger: depletes 1/day. 0 = starve.
- Sanity: darkness, events. 0 = Lost.
Below 3 = Bad Things Happen.

RESOURCES: Wood, Metal, Cloth, Food, Energy Drink, Battery.
Hand limit: 5 Items + 8 Resources.

LIGHT: Flashlight (Battery), Lantern/Campfire (Fire).
No light at night = Charlie: 2 Sanity + 1 Health, +1 each per consecutive dark night.

PHASES:
1 (Days 1-2) Dusk of the Week
2 (Days 3-4) Strange Days + Deerclops
3 (Day 5) Long Nights + Eye of Terror
4 (Days 6-7) Final Hours + The Source

ACTIONS: Move(1), Gather(1), Craft(1), Cook(1), Fight(1), Rest(1), Cleanse(1), Trade(free).

COMBAT: 5-6 = hit. Landed a hit? PRESS THE ATTACK: 1 Sanity per bonus die until you miss (press dice never fumble; the enemy waits until you stop). Boss kills: Deerclops Doom -2, Eye Doom -3, +3 resources, + Trophy.

VARIANTS (optional, set at setup): Rotation turns - 1 action per visit, cycling; pass after acting banks the rest. Scenario - a week-long twist (see Rules in effect panel).

SEVERITY: 1=flavor, 2=minor, 3=combat, 4=phase-shift, 5=boss.

DOWN: Ghost. Can't act. Drift 1 tile/round. 1 word/round. Going Down feeds Doom +1.
Revive: Telltale Heart + 2 Health from reviver. Returns at half max.

DOOM: 0-30 track. Advances each Dawn by phase rate, +1 per threat left on the map (max +3), +2 per boss / +1 Treeguard (no cap), +1 whenever someone goes Down.
Thresholds: 10(threats+1), 15(crafts +1 resource), 20(-1 Sanity Tick), 25(bosses any), 30(defeat).
Cleanse: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink -> Doom -2.

SLEEP: Houses sleep 2 comfortably. Extra sleepers get the floor: no regen.
Survive a night at a sport court: salvage 2 resources at Dawn.

WIN: Survive Day 7, Doom < 30, and The Source destroyed (if it still stands at the end of Day 7, you lose).
Bonus: Pristine (all 5 alive), Truth (3 Clues), Hero (all 3 phase bosses).]]

-- Dynamic content generators
function getHelpCharContent(player)
    local color = player and player.color or gameState.activeColor
    local char = color and gameState.activeChars[color]
    if not char then return "No character assigned yet. Complete Setup first." end

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
            UI.setAttribute(tabId, "color", "rgba(20,50,60,0.9)")
            UI.setAttribute(tabId, "textColor", "#88DDFF")
        else
            UI.setAttribute(tabId, "color", "rgba(20,40,40,0.8)")
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

    broadcastToColor(hint, color, BROADCAST_COLORS.gain)
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
    UI.setAttribute(buttonId, "tooltip", text)
end

-----------------------------------------------------------------------
-- H.8 — Notebook tab population
-----------------------------------------------------------------------
NOTEBOOK_QUICKSTART = [[STARVE NO MORE — QUICK START

GOAL: Survive 7 nights. Doom < 30. Don't all go Down.

EACH DAY:
1. Dawn — flip a Dawn card. Read it. Doom advances (+1 per threat left on the map).
2. Day — 3 actions each: Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free.
3. Dusk — last chance: scramble 1 tile (1 Hunger) or stay. You sleep where you stand.
4. Night — threats drawn. Fight or suffer. Charlie attacks the lightless.
5. Tick — lose 1 Hunger, 1 Sanity. Day advances.

STATS: Health 0 = Down. Hunger 0 = starve. Sanity 0 = Lost.
Below 3 in any stat = Bad Things Happen.

HOVER anything for its rule. Press ? for Help. Click "What now?" if stuck.]]

NOTEBOOK_FULL_RULES = [[STARVE NO MORE — FULL RULES (ABRIDGED)

SETUP:
1. Click Setup Game. Pick a path graph. Pick characters. Read your briefing.

TURN STRUCTURE:
Dawn: Day Counter advances. Doom advances (phase rate + 1 per festering threat, max +3; bosses +2 each, Treeguard +1, no cap). Court survivors salvage 2 resources. Reveal Phase deck card.
Day: 3 actions each — Move(1), Gather(1), Craft(1), Cook(1), Fight(1), Rest(1), Cleanse(1), Trade(free).
Dusk: Scramble 1 tile (1 Hunger, optional, once). You sleep where you stand.
Night: Threat draws per tile. Combat. Charlie check (2 Sanity + 1 Health, escalating). Storytelling. Sleep — houses sleep 2; extras get the floor (no regen).
Tick: -1 Hunger, -1 Sanity. Check victory/defeat.

COMBAT: Roll d6s. 5-6 = hit. 1 = fumble only on a total whiff. Hit? Press the Attack: 1 Sanity per bonus die until you miss; then the enemy counters. Boss kills rebate Doom (-2/-3) and drop spoils.
DEATH: Health 0 or Sanity 0 = Down (ghost). Doom +1. Revive with Telltale Heart.
DOOM: 0-30. Thresholds at 10/15/20/25/30. Cleanse: Doom -2.
VICTORY: Survive Day 7, Doom < 30, and The Source destroyed if it arrived.]]

NOTEBOOK_CHARACTERS = [[CHARACTER REFERENCE

JAMES (White) — HP 8 / HU 6 / SA 10
Perks: Gaming Reflexes (reroll), Pattern Recognition (peek deck)
Constraint: Wired (Energy Drink/day or -2 Sanity)

COCO (Red) — HP 6 / HU 8 / SA 12
Perks: Calming Presence (-1 Sanity loss), Touch of Hope (1x +4 HP), Charlie Immune
Constraint: No Home (alone non-house = -3 Sanity)

RAYMAN (Yellow) — HP 12 / HU 10 / SA 6
Perks: Speed (+1 move), Court Master (+1 atk at Basketball Court), Defend
Constraints: Big Appetite (-2 Hunger/Tick), Loud (moved today = +1 Threat at his Night tile)

ELLIE (Green) — HP 8 / HU 10 / SA 8
Perks: Crockpot Master (-1 ingredient), Comfort Food (+1 shared), Knows Pantry
Constraint: Particular Eater (no raw food)

LUCA (Blue) — HP 7 / HU 8 / SA 10
Perks: Rally (free ally action), Calm Words (d6 negate Sanity loss), Storyteller (+1 Sanity Night)
Constraint: Needs Audience (no solo Sanity regen)]]

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
