-- ui_actionbar_display.lua — active-player validation, Action Bar refresh +
-- action-cube animation, per-button enable/disable + reasons, the stat
-- display, and the action tooltips. Part of ui_actionbar (see core).


-----------------------------------------------------------------------
-- Validate that this player is the active player
-----------------------------------------------------------------------
function validateActivePlayer(color)
    if gameState.subPhase ~= "Day" then
        broadcastToColor("Actions can only be taken during the Day phase.", color, BROADCAST_COLORS.damage)
        return false
    end
    if color ~= gameState.activeColor then
        -- Say WHOSE turn it is and how to become them (hotseat players sit
        -- on one seat but drive several characters).
        local active = gameState.activeColor
        local activeChar = active and gameState.activeChars[active]
        local msg
        if activeChar then
            -- "Change Color" is Tabletop Simulator's own control, and its
            -- name says nothing about what it does here. Spell it out: in this
            -- game one seat colour = one character, so switching colour is how
            -- you take over a character. It does NOT change whose turn it is.
            msg = "It's " .. activeChar.name .. "'s turn — " .. activeChar.name ..
                " is the " .. active .. " seat, and you are sitting in the " ..
                tostring(color) .. " seat.\n\n" ..
                "Each seat colour IS a character, so to play " .. activeChar.name ..
                " you take that seat: click your name in the player list (top " ..
                "right) and choose " .. active .. ". That only changes which " ..
                "character YOU control — it does not change whose turn it is, " ..
                "and nobody's cards or stats move.\n\n" ..
                "To simply move play on instead, use Host Controls > End Turn."
        else
            msg = "It's not your turn."
        end
        broadcastToColor(msg, color, BROADCAST_COLORS.damage)
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
    if customUIHidden then return end

    -- Show/hide action bar based on game state
    if gameState.subPhase == "Day" and gameState.activeColor then
        UI.show("actionBar")
        UI.show("statDisplay")

        local char = gameState.activeChars[gameState.activeColor]
        if char then
            local left = char.actionsLeft or 0
            setActionCubes(left)

            -- Show/hide buttons based on availability. safecall: one bad
            -- precondition check must not blank the whole bar.
            safecall(function() refreshActionButtonStates(gameState.activeColor) end, "ActionButtons")
        end
    else
        UI.hide("actionBar")
        UI.hide("actionTooltip")
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

    -- Fight: needs actions, Hunger >= 3, and something fightable here
    if canFight then
        local fightOk, fightWhy = canFight(color)
        setActionEnabled("actFight", fightOk and true or false)
        setActionTooltip("actFight",
            fightOk and "Fight a threat or boss at this location (click a FIGHT button on the target). 1 action."
                    or ("Fight (1 action). Unavailable: " .. (fightWhy or "")))
    else
        setActionEnabled("actFight", not noActions and not tooHungry)
    end

    -- Pattern Recognition (James only, §6.1): free peek, once per day
    UI.setAttribute("actPeek", "active", char.name == "James" and "true" or "false")
    if char.name == "James" then
        local peekOk, peekWhy = canPeek(color)
        setActionEnabled("actPeek", peekOk and true or false)
        setActionTooltip("actPeek",
            peekOk and "Pattern Recognition: peek at the top card of any deck — free action, once per day."
                   or ("Pattern Recognition (free). Unavailable: " .. (peekWhy or "")))
    end

    -- Rally (Luca only, §6.5): free, once per ROUND, needs a nearby ally.
    -- Also firable off-turn from the Reactions panel (ui_reactions.lua).
    UI.setAttribute("actRally", "active", char.name == "Luca" and "true" or "false")
    if char.name == "Luca" then
        local rallyOk, rallyWhy = canRally(color)
        setActionEnabled("actRally", rallyOk and true or false)
        setActionTooltip("actRally",
            rallyOk and "Rally: give an ally at your tile or adjacent a free non-movement action — free, once per round. You may also fire it on THEIR turn, from the Reactions panel."
                    or ("Rally (free). Unavailable: " .. (rallyWhy or "")))
    end

    -- Rest: always available if actions remain
    setActionEnabled("actRest", not noActions)

    -- Cleanse: need actions (resource check is manual)
    setActionEnabled("actCleanse", not noActions)

    -- Trade: free once per turn at your tile — legal even with 0 actions
    setActionEnabled("actTrade", true)

    -- Pry (§13.5): free action, but only lit when a sealed thing is at the
    -- tile and the player holds a tool
    if canPry then
        local pryOk, pryWhy = canPry(color)
        setActionEnabled("actPry", pryOk and true or false)
        setActionTooltip("actPry",
            pryOk and ("Pry open the sealed thing here — free action (you hold a " .. tostring(pryWhy) .. ").")
                  or ("Pry (free action). Unavailable: " .. (pryWhy or "")))
    end

    -- Signature (§6.7): once per game, per-character preconditions
    local sig = SIGNATURES and SIGNATURES[char.name]
    if sig then
        local sigOk, sigWhy = canUseSignature(color)
        setActionEnabled("actSignature", sigOk and true or false)
        UI.setAttribute("actSignature", "text", sig.name)
        -- Setting a Button's text from Lua resets its styling — re-assert.
        UI.setAttribute("actSignature", "textColor", "#EECCFF")
        setActionTooltip("actSignature",
            sigOk and (sig.desc .. " " .. sig.cost .. " Once per game.")
                  or (sig.desc .. " Unavailable: " .. (sigWhy or "")))
    end

    -- Undo: only when a snapshot of your own last action exists
    local snap = gameState.undoSnapshot
    setActionEnabled("actUndo", snap ~= nil and snap.color == color)

    -- End Turn: always available
    setActionEnabled("actPass", true)

    -- H.7: Update why-disabled tooltip text
    safecall(function() refreshActionButtonReasons(color) end, "ActionTooltips")
end

-- Unavailable actions are HIDDEN, not dimmed: a bar of grey buttons made
-- players wonder which ones they could click. What remains is exactly
-- what the player can do right now.
-- Which action buttons are currently offered. getNextCTA (ui_banner.lua)
-- highlights the single entry when a player has exactly one thing they can
-- do, so "the only thing available" is never something you have to hunt for.
ENABLED_ACTIONS = {}

function setActionEnabled(buttonId, enabled)
    ENABLED_ACTIONS[buttonId] = enabled or nil
    if enabled then
        -- Colour comes from the shared constants, never a literal: this line
        -- used to re-apply the OLD dark plate at runtime and overwrite the
        -- XML, and because it set `color` without `textColor` the result was
        -- the dark-text-on-dark-plate bar all over again. Set both, in one
        -- call, so the pair can never come apart (docs/tts-interface.md).
        UI.setAttributes(buttonId, {
            active       = "true",
            interactable = "true",
            color        = BTN_DARK_PLATE,
            textColor    = BTN_ON_DARK,
        })
    else
        UI.setAttribute(buttonId, "active", "false")
    end
end

-----------------------------------------------------------------------
-- G.5 — Stat display refresh
-----------------------------------------------------------------------
-- One-glance perk/constraint summary per character. The full briefing
-- shows once at setup; this line keeps the rules visible mid-game.
CHAR_TRAIT_LINES = {
    James  = "Perks: peek a deck, reroll dice.\nSignature: All-Nighter (1×).\nWired: drink 1 Energy Drink/day or −2 Sanity at Tick.",
    Coco   = "Perks: −1 Sanity losses nearby, Charlie-immune.\nSignature: Touch of Hope (1×).\nNo Home: alone at a non-house at night = −3 Sanity.",
    Rayman = "Perks: 2-tile Move, +1 die at B-ball Court, Defend.\nSignature: Posterize (1×).\nBig Appetite: −2 Hunger/Tick. Loud: moving today = +1 Threat at his night tile.",
    Ellie  = "Perks: cook with −1 ingredient, Comfort Food +1 to allies.\nSignature: The Feast (1×).\nParticular Eater: can't eat raw food.",
    Luca   = "Perks: Rally (ally free action), Calm Words, Storyteller.\nSignature: The Speech (1×).\nNeeds Audience: no solo Sanity regen.",
}

function refreshStatDisplay()
    if not UI then return end

    -- Which character to show. During Day it's the active player; outside
    -- the Day (Dawn/Dusk/Night/Tick/PreDawn) there's no active player, so
    -- fall back to the last one shown, then any living character. The old
    -- code early-returned here, leaving the bars frozen at their pre-night
    -- values — the "left box still showed max HP after the night" bug.
    local showColor = gameState.activeColor or gameState.lastActiveColor
    if not showColor or not gameState.activeChars[showColor] then
        for c, ch in pairs(gameState.activeChars) do
            if not ch.down then showColor = c; break end
        end
        showColor = showColor or next(gameState.activeChars)
    end
    if not showColor then
        UI.setAttribute("statCharName", "text", "—")
        return
    end
    gameState.lastActiveColor = showColor

    local char = gameState.activeChars[showColor]
    if not char then return end

    UI.setAttribute("statCharName", "text", char.name .. (char.down and " [DOWN]" or ""))

    -- Health bar
    local hPct = (char.maxHealth > 0) and math.floor(char.health / char.maxHealth * 100) or 0
    UI.setAttribute("statHealthBar", "percentage", tostring(hPct))
    UI.setAttribute("statHealthVal", "text", char.health .. "/" .. char.maxHealth)
    -- fillImageColor (not color) is the fill; color is now the white empty
    -- track. Fill brightens when the stat is critically low.
    if char.health < 3 then
        UI.setAttribute("statHealthBar", "fillImageColor", "#FF2222")
    else
        UI.setAttribute("statHealthBar", "fillImageColor", "#FF4444")
    end

    -- Hunger bar
    local huPct = (char.maxHunger > 0) and math.floor(char.hunger / char.maxHunger * 100) or 0
    UI.setAttribute("statHungerBar", "percentage", tostring(huPct))
    UI.setAttribute("statHungerVal", "text", char.hunger .. "/" .. char.maxHunger)
    if char.hunger < 3 then
        UI.setAttribute("statHungerBar", "fillImageColor", "#FF6600")
    else
        UI.setAttribute("statHungerBar", "fillImageColor", "#FFAA22")
    end

    -- Sanity bar
    local sPct = (char.maxSanity > 0) and math.floor(char.sanity / char.maxSanity * 100) or 0
    UI.setAttribute("statSanityBar", "percentage", tostring(sPct))
    UI.setAttribute("statSanityVal", "text", char.sanity .. "/" .. char.maxSanity)
    if char.sanity < 3 then
        UI.setAttribute("statSanityBar", "fillImageColor", "#FF44FF")
    else
        UI.setAttribute("statSanityBar", "fillImageColor", "#4488FF")
    end

    -- Location
    local locName = char.location or "Unknown"
    UI.setAttribute("statLocation", "text", "Location: " .. locName)

    -- What you hold: live count of the resource tokens by your board, so
    -- nobody has to eyeball-count tokens after a Gather.
    safecall(function()
        local res = getPlayerResources(showColor)
        UI.setAttribute("statResources", "text", string.format(
            "Holding: Wood %d · Metal %d · Cloth %d\nFood %d · Energy %d · Battery %d",
            res.Wood or 0, res.Metal or 0, res.Cloth or 0,
            res.Food or 0, res.EnergyDrink or 0, res.Battery or 0))
    end, "StatResources")

    -- Perks + constraint reminder
    UI.setAttribute("statPerks", "text", CHAR_TRAIT_LINES[char.name] or "")
end

-----------------------------------------------------------------------
-- Action-button tooltips — shown in the actionTooltip panel just above
-- the action bar (opaque, unlike the native transparent tooltip that
-- rendered on top of the buttons), and only after a hover delay so they
-- don't nag experienced players. Texts are dynamic: setActionTooltip
-- (ui_help.lua) rewrites them with why-disabled reasons on every state
-- change.
-- (The manual +/- stat buttons that used to live here are gone: every
-- stat change is automated by the action/night/tick handlers.)
-----------------------------------------------------------------------
ACTION_TOOLTIP_DELAY = 2  -- seconds of hover before the tooltip appears

ACTION_TOOLTIPS = {
    actMove      = "Move to an adjacent location. Costs 1 action + 1 Hunger.",
    actGather    = "Gather a resource here — it's delivered to your board automatically. Costs 1 action.",
    actCraft     = "Craft an item from the Market. Costs 1 action + resources.",
    actCook      = "Cook a recipe at a Crockpot location. Costs 1 action + ingredients.",
    actFight     = "Fight a threat or boss at this location — click FIGHT on the target (TOGETHER = group fight). Costs 1 action.",
    actPeek      = "Pattern Recognition (James): peek at the top card of any deck. Free action, once per day.",
    actRally     = "Rally (Luca): give an ally at your tile or adjacent a free non-movement action. Free, once per round — and firable on their turn from the Reactions panel.",
    actRest      = "Rest: +1 Hunger or +2 Sanity. At your own house: also +1 Health.",
    actCleanse   = "Cleanse the Doom track (-2). Costs 1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink.",
    actTrade     = "Trade resources/items with another player. Free once per turn at your tile; otherwise 1 action.",
    actSignature = "Your character's Signature Move — once per game.",
    actPry       = "Pry open a sealed thing at your tile (free action; needs a Crowbar, Lockpick, or Pry Bar).",
    actUndo      = "Undo your last action's stat, position, and Doom changes (once per action).",
    actPass      = "End your turn. Remaining actions are forfeited. (Host: clicking this on someone else's turn ends THEIR turn — handy in hotseat.)",
}

local actionTooltipWaits = {}  -- hovering player's color -> pending Wait id

function onActionTooltipEnter(player, value, id)
    local tip = ACTION_TOOLTIPS[id]
    if not tip then return end
    local color = player.color
    if actionTooltipWaits[color] then Wait.stop(actionTooltipWaits[color]) end
    actionTooltipWaits[color] = Wait.time(function()
        actionTooltipWaits[color] = nil
        UI.setAttribute("actionTooltipText", "text", ACTION_TOOLTIPS[id] or tip)
        UI.setAttribute("actionTooltip", "visibility", color)
        UI.show("actionTooltip")
    end, ACTION_TOOLTIP_DELAY)
end

function onActionTooltipExit(player, value, id)
    local color = player.color
    if actionTooltipWaits[color] then
        Wait.stop(actionTooltipWaits[color])
        actionTooltipWaits[color] = nil
    end
    UI.hide("actionTooltip")
end
