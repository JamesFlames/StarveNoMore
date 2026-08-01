-- ui_actionbar_situational.lua — the situational action verbs.
--
-- Eight rules were fully implemented and unreachable: the code existed, the
-- *consumers* of its state existed, and no button, dialog or handler ever
-- called it. The UI meanwhile told players to do these things — "use a
-- Telltale Heart at this tile to revive", "Wired: drink 1 Energy Drink/day",
-- "Perks: ... Defend" — so each read as a broken rule rather than a missing
-- one. What they had in common was being *conditional*, with no home on a bar
-- whose fourteen buttons are all unconditional.
--
--   Revive        reviveCharacter (tick_victory)    §16.4  hearts were cooked, never spent
--   Stabilize     doStabilize (actions_social)      §12.3  the Bandage revive
--   Defend        doDefend (actions_social)         Rayman; combat_resolve reads raymanDefending
--   Energy Drink  doEnergyDrink (actions_social)    James; four files read jamesEnergyDrinkUsed
--   Eat Uncooked  doEatUncooked (actions_social)    §8.4; Ellie's Particular Eater lived here
--   Barricade     doBarricade (actions_social)      day_loop reads gameState.barricades
--   Appease       doAppeaseTreeguard (treeguard)    the non-violent Treeguard resolution
--   Ghost Drift   ghostDrift (tick_victory)         §16.4; a Down player's only decision
--
-- The first seven follow the Peek/Rally pattern: hidden by default, shown by
-- refreshSituationalButtons only while their precondition holds. Each `canX`
-- returns (ok, reason), and the reason doubles as the refusal broadcast and
-- the why-disabled tooltip, exactly like canFight/canPeek/canRally.
--
-- Ghost Drift is the exception and rides the Reactions panel instead: it
-- belongs to a player who is by definition NOT the active one, and
-- refreshActionBar hides the whole bar for them.

-----------------------------------------------------------------------
-- Preconditions
-----------------------------------------------------------------------

local function held(color, resType)
    return (getPlayerResources(color) or {})[resType] or 0
end

-- Down allies sharing this character's tile — the target set for both
-- Revive (§16.4, costs a Telltale Heart) and Stabilize (§12.3, a Bandage).
function downedAlliesHere(color)
    local char = gameState.activeChars[color]
    local out = {}
    if not char then return out end
    for c, ch in pairs(gameState.activeChars) do
        if c ~= color and ch.down and ch.location == char.location then
            table.insert(out, c)
        end
    end
    table.sort(out)   -- pairs() order is arbitrary; the dialog must be stable
    return out
end

function canRevive(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if (gameState.heartCount or 0) < 1 then
        return false, "No Telltale Heart. Cook one at the Crockpot (1 Cloth + 1 Battery + 1 Provisions + 2 Health)."
    end
    if char.health <= REVIVE_HEALTH_COST then
        return false, "Reviving costs " .. REVIVE_HEALTH_COST .. " Health and you have " ..
            char.health .. " — it would put you Down too."
    end
    if #downedAlliesHere(color) == 0 then
        return false, "Nobody is Down at " .. (char.location or "your tile") .. "."
    end
    return true
end

function canStabilize(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if char.actionsLeft <= 0 then return false, "No actions remaining." end
    if #downedAlliesHere(color) == 0 then
        return false, "Nobody is Down at " .. (char.location or "your tile") .. "."
    end
    if not findCarriedItem(color, "M_BANDAGE", "Bandage") then
        return false, "No Bandage in hand or by your board — craft one (1 Cloth)."
    end
    return true
end

function canDefend(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.name ~= "Rayman" then return false, "Only Rayman can Defend." end
    if char.down then return false, "You are Down." end
    if char.actionsLeft <= 0 then return false, "No actions remaining." end
    if gameState.raymanDefending then return false, "Backboard Block is already up." end
    return true
end

function canEnergyDrink(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if held(color, "EnergyDrink") < 1 then
        return false, "No Energy Drink token. Gather at James's House."
    end
    -- James may always drink: for him it is not the Sanity, it is Wired.
    if char.name ~= "James" and char.sanity >= char.maxSanity then
        return false, "Sanity is already full."
    end
    return true
end

function canEatUncooked(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    -- Particular Eater (§6.4). Checked here as well as inside doEatUncooked so the
    -- button never appears for Ellie in the first place.
    if char.name == "Ellie" then
        return false, "Ellie can't eat uncooked food (Particular Eater). Cook it first."
    end
    if held(color, "Provisions") < 1 then return false, "No Provisions token to eat." end
    if char.hunger >= char.maxHunger then return false, "Hunger is already full." end
    return true
end

-- Flee (§12.4) — the escape valve, and the rule Last Nerve exists to protect.
-- It had no button at all: `doFlee` was implemented, correct, and reachable
-- only from the test suite, while six places in the UI told the player to use
-- it ("Too hungry to fight (Hunger < 3). Flee is always legal", the threat-draw
-- warning, the Hunger tooltip, the notebook, What-now, the Active Rules panel).
-- A starving player was told four ways to run and given no way to do it.
--
-- Deliberately NOT gated on the action budget or on Hunger: "always legal, even
-- starving" is the whole point, and doFlee charges Sanity (0 on Last Nerve),
-- never an action.
function canFlee(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if #fightTargetsAt(char.location) == 0 then
        return false, "Nothing to flee from at " .. (char.location or "your tile") .. "."
    end
    if #adjacentLocations(char.location or "") == 0 then
        return false, "Nowhere to run from " .. (char.location or "?") .. "."
    end
    return true
end

function canBarricade(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if char.actionsLeft <= 0 then return false, "No actions remaining." end
    if held(color, "Wood") < 1 then return false, "Barricading costs 1 Wood." end
    local loc = char.location or ""
    if ((gameState.barricades or {})[loc] or 0) > 0 then
        return false, loc .. " is already barricaded tonight."
    end
    local roots = persistentBlocksBarricade(loc)
    if roots then
        return false, loc .. " cannot be barricaded — " .. roots .. " holds the floor."
    end
    return true
end

function canAppeaseTreeguard(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    local tg = gameState.treeguard
    if not (tg and tg.active) then return false, "No Treeguard is awake." end
    if char.location ~= tg.location then
        return false, "The Treeguard is at " .. tostring(tg.location) .. "."
    end
    if char.actionsLeft <= 0 then return false, "No actions remaining." end
    if held(color, "Wood") < 2 then return false, "Appeasing costs 2 Wood." end
    return true
end

-- Ghost drift (§16.4): a Down character moves one tile per round, free. It is
-- the only decision a ghost still has — design §05 calls a Down player with no
-- decisions left the co-op form of player elimination — so it is deliberately
-- gated on neither the turn order nor the action budget.
function canDrift(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if not char.down then return false, "Only a Down character drifts." end
    if gameState.subPhase ~= "Day" then return false, "Ghosts drift during the Day." end
    if (gameState.driftedThisRound or {})[color] then
        return false, "Already drifted this round — one tile per round."
    end
    return true
end

-----------------------------------------------------------------------
-- Revive / Stabilize: one shared target dialog
--
-- Both pick a Down ally at the same tile, and both are rare. A second
-- five-button panel would be XML for no gain, so pendingAction.type says
-- which verb the click resolves to.
-----------------------------------------------------------------------
local DOWNED_SEATS = {"White", "Red", "Yellow", "Green", "Blue"}

-- `seats` is the eligible seat list; the panel is otherwise identical for
-- every verb that picks one ally, so the Antler Sled reuses it rather than
-- adding a third five-button panel to the XML.
local function showSeatTargets(color, kind, title, note, seats, extra)
    local eligible = {}
    for _, c in ipairs(seats) do eligible[c] = true end
    for _, c in ipairs(DOWNED_SEATS) do
        local btn = "downedBtn_" .. c
        local ch = gameState.activeChars[c]
        if eligible[c] and ch then
            UI.setAttribute(btn, "active", "true")
            setButtonLabel(btn, ch.name .. "  (at " .. (ch.location or "?") .. ")")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    UI.setAttribute("downedTitle", "text", title)
    UI.setAttribute("downedNote", "text", note)
    gameState.pendingAction = { type = kind, color = color }
    if extra then
        for k, v in pairs(extra) do gameState.pendingAction[k] = v end
    end
    UI.show("downedDialog")
end

-- The Antler Sled's ally pick (trophies.lua calls this once the mover has
-- arrived, so only "who comes too" is left to decide).
function showSledTargets(color, toLoc, candidates, title, note)
    showSeatTargets(color, "sled", title, note, candidates, { toLoc = toLoc })
end

local function showDownedTargets(color, kind, title, note)
    local eligible = {}
    for _, c in ipairs(downedAlliesHere(color)) do eligible[c] = true end
    for _, c in ipairs(DOWNED_SEATS) do
        local btn = "downedBtn_" .. c
        local ch = gameState.activeChars[c]
        if eligible[c] and ch then
            UI.setAttribute(btn, "active", "true")
            setButtonLabel(btn, ch.name .. "  (Down at " .. (ch.location or "?") .. ")")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    UI.setAttribute("downedTitle", "text", title)
    UI.setAttribute("downedNote", "text", note)
    gameState.pendingAction = { type = kind, color = color }
    UI.show("downedDialog")
end

function onActRevive(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canRevive(color)
    if not ok then
        broadcastToColor(why or "Can't revive right now.", color, BROADCAST_COLORS.damage)
        return
    end
    showDownedTargets(color, "revive", "Revive — spend a Telltale Heart on whom?",
        "You pay " .. REVIVE_HEALTH_COST .. " Health; they return at half their maximums. " ..
        (gameState.heartCount or 0) .. " Heart(s) in the supply.")
end

function onActStabilize(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canStabilize(color)
    if not ok then
        broadcastToColor(why or "Can't stabilize right now.", color, BROADCAST_COLORS.damage)
        return
    end
    showDownedTargets(color, "stabilize", "Stabilize — patch up whom?",
        "1 action + a Bandage. They come back at 1 Health — not a full revival.")
end

function onDownedTargetClick(player, value, id)
    UI.hide("downedDialog")
    local pa = gameState.pendingAction
    if not (pa and pa.color == player.color) then return end
    if pa.type ~= "revive" and pa.type ~= "stabilize" and pa.type ~= "sled" then return end
    gameState.pendingAction = nil

    local color = pa.color
    if pa.type == "sled" then
        safecall(function() bringAllyOnSled(color, value, pa.toLoc) end, "AntlerSled")
        refreshPhaseBanner()
        updateActivePlayerIndicator()
        return
    end
    if pa.type == "stabilize" then
        safecall(function() doStabilize(color, value) end, "Stabilize")
    else
        -- Spending the LAST Heart is a decision, not a click: with none left,
        -- the next character to go Down stays Down (ui_mood.lua, I.6).
        local reviver = gameState.activeChars[color]
        local target = gameState.activeChars[value]
        confirmLastHeart(reviver and reviver.name or "?", target and target.name or "?",
            function() safecall(function() reviveCharacter(color, value) end, "Revive") end)
    end
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onDownedCancel(player, value, id)
    UI.hide("downedDialog")
    local pa = gameState.pendingAction
    if pa and (pa.type == "revive" or pa.type == "stabilize" or pa.type == "sled") then
        -- Declining the Sled does NOT spend it: nobody came along, so the
        -- once-per-turn window is still open for a later Move this turn.
        gameState.pendingAction = nil
    end
end

-----------------------------------------------------------------------
-- The one-click verbs
-----------------------------------------------------------------------

-- Every one of these is the same five steps, and writing them out five times
-- is how one of them ends up missing its precondition check.
local function runSituational(player, canFn, doFn, label, cost)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canFn(color)
    if not ok then
        broadcastToColor(why or ("Can't " .. label .. " right now."), color,
                         BROADCAST_COLORS.damage)
        return
    end
    -- Pay first: a failed payment must not hand out the effect.
    if cost and not verifyAndPayResources(color, cost, "the " .. label) then return end
    safecall(function() doFn(color) end, label)
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onActDefend(player, value, id)
    runSituational(player, canDefend, doDefend, "Defend")
end

function onActEnergyDrink(player, value, id)
    runSituational(player, canEnergyDrink, doEnergyDrink, "Energy Drink",
                   { EnergyDrink = 1 })
end

function onActEatUncooked(player, value, id)
    runSituational(player, canEatUncooked, doEatUncooked, "uncooked Provisions", { Provisions = 1 })
end

-- Barricade and Appease pay their own resources inside the action (and refund
-- the spent action if unaffordable), so no cost table here.
-- Use Item (items.lua): the single-use Market consumables, which had no verb
-- at all — no button, no manual stat editor, so a crafted First Aid Kit could
-- not do the thing printed on it. Same dialog shape as Cook: a list of what
-- you can actually use right now.
USE_ITEM_DIALOG_SLOTS = 8
_useItemDialogIds = {}

function onActUseItem(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canUseItem(color)
    if not ok then
        broadcastToColor(why or "Nothing to use.", color, BROADCAST_COLORS.damage)
        return
    end
    if not UI then return end

    local shown = 0
    _useItemDialogIds = {}
    for _, itemId in ipairs(usableItemsFor(color)) do
        if shown < USE_ITEM_DIALOG_SLOTS then
            shown = shown + 1
            _useItemDialogIds[shown] = itemId
            local spec = USE_ITEMS[itemId]
            setButtonLabel("useItemOpt" .. shown,
                spec.label .. "   (" .. describeItemEffect(spec) .. ")")
            UI.setAttribute("useItemOpt" .. shown, "active", "true")
        end
    end
    for i = shown + 1, USE_ITEM_DIALOG_SLOTS do
        UI.setAttribute("useItemOpt" .. i, "active", "false")
    end
    UI.show("useItemDialog")
end

function onUseItemOptionClick(player, value, id)
    local slot = tonumber(id and id:match("useItemOpt(%d+)")) or tonumber(value)
    local itemId = _useItemDialogIds and _useItemDialogIds[slot]
    UI.hide("useItemDialog")
    if not itemId then return end
    safecall(function() doUseItem(player.color, itemId) end, "UseItem")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onUseItemCancel(player, value, id)
    UI.hide("useItemDialog")
end

-- Flee picks a destination exactly the way Move does, so it rides the same
-- tile buttons rather than growing a second set (see _spawnMoveButtons).
function onActFlee(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local ok, why = canFlee(color)
    if not ok then
        broadcastToColor(why or "Can't flee right now.", color, BROADCAST_COLORS.damage)
        return
    end
    -- Clicking Flee again while a flee is pending cancels it.
    local pa = gameState.pendingAction
    clearActionTargets()
    if pa and pa.color == color and pa.type == "flee" then
        broadcastToColor("Flee cancelled.", color, BROADCAST_COLORS.proc)
        return
    end
    gameState.pendingAction = { type = "flee", color = color }
    if _spawnMoveButtons(color, "flee") == 0 then
        gameState.pendingAction = nil
        broadcastToColor("Nowhere to run — no neighbouring tile is on the table.",
            color, BROADCAST_COLORS.damage)
        return
    end
    _armTargetTimeout()
end

function onActBarricade(player, value, id)
    runSituational(player, canBarricade, doBarricade, "Barricade")
end

function onActAppease(player, value, id)
    runSituational(player, canAppeaseTreeguard, doAppeaseTreeguard, "Appease")
end

-- Clear: the removal path for the Persistent threats that are neither
-- fightable (hp 0) nor sealed (no Pry reward). Without it those cards sat on
-- the tile applying their rule and charging +1 Doom every Dawn, permanently.
function onActClear(player, value, id)
    runSituational(player, canClearPersistent, doClearPersistent, "Clear")
end

-----------------------------------------------------------------------
-- Bar refresh. Driven from refreshActionButtonStates (display), so these
-- appear and vanish in the same pass as Peek/Rally/Pry.
--
-- Functions are referenced directly rather than looked up by name in _G:
-- this codebase has no dynamic dispatch anywhere, which is precisely what
-- makes "is this function reachable?" answerable by reading it.
-----------------------------------------------------------------------
SITUATIONAL_ACTIONS = {
    { id = "actRevive", can = canRevive,
      tip = "Revive a Down ally at your tile with a Telltale Heart. You pay " ..
            REVIVE_HEALTH_COST .. " Health; they return at half their maximums." },
    { id = "actStabilize", can = canStabilize,
      tip = "Stabilize a Down ally at your tile with a Bandage — 1 action. " ..
            "They return at 1 Health. Not a full revival." },
    { id = "actDefend", can = canDefend,
      tip = "Backboard Block — 1 action. Counter-attack damage is redirected " ..
            "to Rayman until his next turn." },
    { id = "actEnergy", can = canEnergyDrink,
      tip = "Drink an Energy Drink — free. +2 Sanity, and for James it " ..
            "satisfies Wired for today (no -2 Sanity at Tick)." },
    { id = "actEatUncooked", can = canEatUncooked,
      tip = "Eat a Provisions token uncooked — free. +1 Hunger, -1 Sanity." },
    { id = "actUseItem", can = canUseItem,
      tip = "Use a single-use item you are carrying — free. The card is " ..
            "spent; healing items go to whoever at your tile needs them most." },
    { id = "actFlee", can = canFlee,
      tip = "Run from what's here — 1 tile away, 1 Sanity, no action. Always " ..
            "legal, even starving, and free while you are on your Last Nerve. " ..
            "The threat stays behind and festers at Dawn." },
    { id = "actBarricade", can = canBarricade,
      tip = "Barricade this tile — 1 action + 1 Wood. It draws one fewer " ..
            "Threat tonight, then the barricade is gone." },
    { id = "actAppease", can = canAppeaseTreeguard,
      tip = "Plant saplings and send the Treeguard back to sleep — 1 action " ..
            "+ 2 Wood. No fight, and no salvage." },
    { id = "actClear", can = canClearPersistent,
      tip = "Clear a Persistent threat that cannot be fought or pried — " ..
            CLEAR_PERSISTENT_ACTIONS .. " actions + " .. CLEAR_PERSISTENT_WOOD ..
            " Wood. Its rule stops, and so does its +1 Doom every Dawn." },
}

function refreshSituationalButtons(color)
    for _, entry in ipairs(SITUATIONAL_ACTIONS) do
        local ok, why = entry.can(color)
        setActionEnabled(entry.id, ok and true or false)
        setActionTooltip(entry.id,
            ok and entry.tip or (entry.tip .. "  Unavailable: " .. (why or "")))
    end
end
