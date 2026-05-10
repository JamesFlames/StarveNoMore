-- ui_help.lua  (H.3/H.4 Help panel 5 tabs + H.5 What-now hints + H.7 Why-disabled + H.8 Notebook)

-----------------------------------------------------------------------
-- H.3 — Help Panel Content (5 tabs)
-----------------------------------------------------------------------

-- Static content loaded as Lua strings (from content/ markdown files)
HELP_QUICKSTART = [[GOAL: Survive 7 nights. Doom < 30. Don't all go Down.

EACH DAY:
1. Dawn - flip a Dawn card. Read it. Doom advances.
2. Day - 3 actions each: Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free.
3. Dusk - declare where you sleep.
4. Night - threats drawn. Fight or suffer. Charlie attacks the lightless.
5. Tick - lose 1 Hunger, 1 Sanity. Day advances.

THREE STATS:
- Health 0 = Down (ghost).
- Hunger 0 = starve (lose Health each Tick).
- Sanity 0 = Lost (also Down).
Below 3 in any stat: Bad Things Happen.

TRADE freely at the same tile - no action cost.

LIGHT: No light source at night = Charlie attack (d8 Sanity + d6 Health).

Hover anything for its rule. Click "?" for this menu. Click "What now?" if stuck.]]

HELP_GLOSSARY = [[STATS:
- Health: damage. 0 = Down.
- Hunger: depletes 1/day. 0 = starve.
- Sanity: darkness, events. 0 = Lost.
Below 3 = Bad Things Happen.

RESOURCES: Wood, Metal, Cloth, Food, Energy Drink, Battery.
Hand limit: 5 Items + 8 Resources.

LIGHT: Flashlight (Battery), Lantern/Campfire (Fire).
No light at night = Charlie: d8 Sanity + d6 Health.

PHASES:
1 (Days 1-2) Dusk of the Week
2 (Days 3-4) Strange Days + Deerclops
3 (Day 5) Long Nights + Eye of Terror
4 (Days 6-7) Final Hours + The Source

ACTIONS: Move(1), Gather(1), Craft(1), Cook(1), Fight(1), Rest(1), Cleanse(1), Trade(free).

SEVERITY: 1=flavor, 2=minor, 3=combat, 4=phase-shift, 5=boss.

DOWN: Ghost. Can't act. Drift 1 tile/round. -1 Sanity to co-located allies. 1 word/round.
Revive: Telltale Heart + 2 Health from reviver. Returns at half max.

DOOM: 0-30 track. Thresholds: 10(threats+1), 15(market 1/day), 20(-1 Sanity Tick), 25(bosses any), 30(defeat).
Cleanse: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink -> Doom -2.

WIN: Survive Day 7, Doom < 30.
Bonus: Pristine (all 5 alive), Truth (3 Clues), Hero (4 bosses).]]

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
    local text = "DOOM TRACK: " .. gameState.doom .. " / 30\n\n"

    text = text .. "Current phase doom rate: +" .. getDoomRate() .. " per day\n\n"

    text = text .. "THRESHOLDS:\n"
    local thresholds = {
        {10, "Night threat draws +1 at all locations.", gameState.doom >= 10},
        {15, "Market refresh slowed to 1 card per day.", gameState.doom >= 15},
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
-----------------------------------------------------------------------
WHATNOW_HINTS = {
    -- Pre-Game
    PreGame = {
        default = "Click 'Setup Game' on the Host Controls panel to begin. Hover anything to see what it does. Press '?' for help.",
    },
    -- Dawn
    Dawn = {
        default = "A new Dawn card has been revealed. Read the effect. When ready, the host clicks Begin Day.",
    },
    -- Day
    Day = {
        default = "It's your turn, {name}. You have {actionsLeft} action(s) left. Choose: Move, Gather, Craft, Cook, Fight, Rest, or Cleanse.",
        no_actions = "You've used all 3 actions. Click Pass to end your turn.",
    },
    -- Dusk
    Dusk = {
        default = "Declare where you'll sleep tonight. Characters sleep at their current tile. Sleeping at your own house is safest.",
    },
    -- Night
    Night = {
        default = "Night is resolving. Threats are drawn at each location. The host clicks Resolve Night.",
    },
    -- Tick
    Tick = {
        default = "End-of-round Tick. Everyone loses 1 Hunger and 1 Sanity. Check your stats.",
    },
    -- GameOver
    GameOver = {
        default = "Game over. Click Restart to play again.",
    },
}

-- Character-specific hints
WHATNOW_CHAR_HINTS = {
    James = {
        energy = "James, you haven't consumed an Energy Drink today. If you don't by end of day, you'll lose 2 Sanity tonight.",
        peek = "James, use Pattern Recognition to peek at any deck top. The Threat deck is usually the best target.",
    },
    Coco = {
        alone = "Coco, you're alone. Ending Night alone at a non-house tile = -3 Sanity. Move toward an ally.",
        touch = "Coco, your Touch of Hope is still available (once per game). Save it for a real emergency.",
    },
    Rayman = {
        hungry = "Rayman, your Hunger is low. You lose 2 Hunger per Tick. Get to the Kitchen or eat what you have.",
        court = "Rayman, you're at the Basketball Court. Court Master gives +1 attack die here. Fight if there's a Threat.",
    },
    Ellie = {
        kitchen = "Ellie, you're at the Kitchen. Cook with 1 fewer ingredient. Hot Stew feeds everyone here.",
        nofood = "Ellie, you can't eat raw food (Particular Eater). Gather at your house or trade for ingredients.",
    },
    Luca = {
        alone = "Luca, you're alone. Your Sanity won't regen without company. Move toward an ally.",
        rally = "Luca, use Rally to give a nearby ally a free action. It's one of the most powerful moves.",
    },
}

-- Stat warning hints
WHATNOW_STAT_HINTS = {
    low_hunger  = "{name}, Hunger at {hunger} (below 3). Can't Fight. Eat, Rest, or trade for Food.",
    low_sanity  = "{name}, Sanity at {sanity} (below 3). You'll hallucinate at Dawn. Use Comfort items or get near Coco/Luca.",
    low_health  = "{name}, Health at {health} (below 3). Movement costs +1 action. Use a Bandage or rest at your own house.",
}

-- Strategic hints
WHATNOW_STRATEGIC_HINTS = {
    doom_high   = "Doom is at {doom}. Consider Cleansing: 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink -> Doom -2.",
    ally_down   = "A teammate is Down. Cook a Telltale Heart (1 Cloth + 1 Battery + 1 Food + 2 Health) to revive them.",
    no_light    = "{name}, you have no light source. Charlie will attack tonight. Get a Flashlight, Lantern, or Fire.",
}

function onWhatNowClick(player, value, id)
    local color = player.color
    local char = gameState.activeChars[color]
    local sp = gameState.subPhase or "PreGame"

    -- Start with the phase-appropriate base hint
    local phaseHints = WHATNOW_HINTS[sp] or WHATNOW_HINTS["PreGame"]
    local hint = phaseHints.default or ""

    -- Check for no-actions state during Day
    if sp == "Day" and char and char.actionsLeft <= 0 then
        hint = phaseHints.no_actions or hint
    end

    -- Substitute placeholders
    if char then
        hint = substitutePlaceholders(hint, char)

        -- Add character-specific hints
        local charHints = WHATNOW_CHAR_HINTS[char.name]
        if charHints and sp == "Day" then
            -- James energy drink check
            if char.name == "James" and not gameState.jamesEnergyDrinkUsed then
                hint = hint .. "\n" .. charHints.energy
            end
            -- Rayman at court
            if char.name == "Rayman" and (char.location or ""):find("Basketball") then
                hint = hint .. "\n" .. charHints.court
            end
            -- Ellie at kitchen
            if char.name == "Ellie" and char.location == "EllieLucaHouse" then
                hint = hint .. "\n" .. charHints.kitchen
            end
            -- Luca/Coco alone check
            if char.name == "Coco" or char.name == "Luca" then
                local othersHere = 0
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location == char.location then
                        othersHere = othersHere + 1
                    end
                end
                if othersHere == 0 then
                    hint = hint .. "\n" .. (charHints.alone or "")
                end
            end
        end

        -- Add stat warnings
        if char.hunger < 3 and char.hunger > 0 then
            hint = hint .. "\n" .. substitutePlaceholders(WHATNOW_STAT_HINTS.low_hunger, char)
        end
        if char.sanity < 3 and char.sanity > 0 then
            hint = hint .. "\n" .. substitutePlaceholders(WHATNOW_STAT_HINTS.low_sanity, char)
        end
        if char.health < 3 and char.health > 0 then
            hint = hint .. "\n" .. substitutePlaceholders(WHATNOW_STAT_HINTS.low_health, char)
        end

        -- Strategic hints
        if gameState.doom >= 20 then
            hint = hint .. "\n" .. substitutePlaceholders(WHATNOW_STRATEGIC_HINTS.doom_high, char)
        end

        -- Ally down check
        for c2, ch2 in pairs(gameState.activeChars) do
            if ch2.down then
                hint = hint .. "\n" .. substitutePlaceholders(WHATNOW_STRATEGIC_HINTS.ally_down, char)
                break
            end
        end
    else
        hint = substitutePlaceholders(hint, nil)
    end

    -- Display to the requesting player
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
1. Dawn — flip a Dawn card. Read it. Doom advances.
2. Day — 3 actions each: Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free.
3. Dusk — declare where you sleep.
4. Night — threats drawn. Fight or suffer. Charlie attacks the lightless.
5. Tick — lose 1 Hunger, 1 Sanity. Day advances.

STATS: Health 0 = Down. Hunger 0 = starve. Sanity 0 = Lost.
Below 3 in any stat = Bad Things Happen.

HOVER anything for its rule. Press ? for Help. Click "What now?" if stuck.]]

NOTEBOOK_FULL_RULES = [[STARVE NO MORE — FULL RULES (ABRIDGED)

SETUP:
1. Click Setup Game. Pick a path graph. Pick characters. Read your briefing.

TURN STRUCTURE:
Dawn: Day Counter advances. Reveal Phase deck card. Doom advances.
Day: 3 actions each — Move(1), Gather(1), Craft(1), Cook(1), Fight(1), Rest(1), Cleanse(1), Trade(free).
Dusk: Declare sleep location.
Night: Threat draws per tile. Combat. Charlie check. Storytelling. Sleep.
Tick: -1 Hunger, -1 Sanity. Check victory/defeat.

COMBAT: Roll d6s. 5-6 = hit. 1 = fumble. Enemy counter-attacks.
DEATH: Health 0 or Sanity 0 = Down (ghost). Revive with Telltale Heart.
DOOM: 0-30. Thresholds at 10/15/20/25/30. Cleanse: Doom -2.
VICTORY: Survive Day 7, Doom < 30.]]

NOTEBOOK_CHARACTERS = [[CHARACTER REFERENCE

JAMES (White) — HP 8 / HU 6 / SA 10
Perks: Gaming Reflexes (reroll), Pattern Recognition (peek deck)
Constraint: Wired (Energy Drink/day or -2 Sanity)

COCO (Red) — HP 6 / HU 8 / SA 12
Perks: Calming Presence (-1 Sanity loss), Touch of Hope (1x +4 HP), Charlie Immune
Constraint: No Home (alone non-house = -3 Sanity)

RAYMAN (Yellow) — HP 12 / HU 10 / SA 6
Perks: Speed (+1 move), Court Master (+1 atk at Basketball Court), Defend
Constraints: Big Appetite (-2 Hunger/Tick), Loud (+1 Threat on move)

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
