-- actions.lua  (Player action dispatcher — Move, Gather, Rest, Fight, etc.)
-- Design §11.2: Each player has 3 actions per Day.

-----------------------------------------------------------------------
-- QoL: Undo last action (once per turn, before ending turn)
-----------------------------------------------------------------------
function snapshotForUndo(color)
    local char = gameState.activeChars[color]
    if not char then return end
    gameState.undoSnapshot = {
        color = color,
        health = char.health,
        hunger = char.hunger,
        sanity = char.sanity,
        location = char.location,
        actionsLeft = char.actionsLeft,
        doom = gameState.doom,
        raymanMovedToday = gameState.raymanMovedToday,
        raymanBonusMove = gameState.raymanBonusMove,
    }
end

function doUndo(color)
    local snap = gameState.undoSnapshot
    if not snap or snap.color ~= color then
        broadcastToColor("Nothing to undo.", color, BROADCAST_COLORS.damage)
        return
    end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Restore snapshot
    char.health = snap.health
    char.hunger = snap.hunger
    char.sanity = snap.sanity
    char.actionsLeft = snap.actionsLeft
    gameState.doom = snap.doom
    gameState.raymanMovedToday = snap.raymanMovedToday
    gameState.raymanBonusMove = snap.raymanBonusMove

    -- Move standee back if location changed
    if char.location ~= snap.location then
        char.location = snap.location
        local standee = getCharacterStandee(char.name)
        local tile = getLocationTile(snap.location)
        if standee and tile then
            standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
        end
    end

    moveDoomMarker(gameState.doom)
    gameState.undoSnapshot = nil  -- can only undo once
    -- Rotation variant: the undone action no longer counts as this visit's
    -- one action, so the player may act again before passing.
    gameState.actedThisVisit = false

    broadcastEvent("proc", char.name .. " undoes their last action.")
    refreshPhaseBanner()
end

-----------------------------------------------------------------------
-- MOVE (1 action, costs 1 Hunger)  — Design §11.2
-- Rayman moves 2 spaces for 1 action.
-----------------------------------------------------------------------
function doMove(color, targetLocation)
    if not spendAction(color, "Move") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Low Health penalty: movement costs +1 action
    if char.health < 3 and char.health > 0 then
        if char.actionsLeft <= 0 then
            broadcastEvent("damage", char.name .. " is critically injured — movement requires an extra action you don't have.")
            -- Refund the action
            char.actionsLeft = char.actionsLeft + 1
            return
        end
        char.actionsLeft = char.actionsLeft - 1
        broadcastEvent("warn", char.name .. " spends an extra action to move (Health < 3).")
    end

    -- Movement costs 1 Hunger
    local hungerCost = 1

    -- Shortcut scenario: free movement between JamesHouse and BadmintonCourt
    local sFlags = gameState.scenarioFlags or {}
    if sFlags.shortcutPath then
        local from = char.location or ""
        local shortcutPair = (from == "JamesHouse" and targetLocation == "BadmintonCourt") or
                             (from == "BadmintonCourt" and targetLocation == "JamesHouse")
        if shortcutPair then
            hungerCost = 0
            broadcastEvent("gain", char.name .. " uses the Shortcut — free movement!")
        end
    end

    char.hunger = math.max(0, char.hunger - hungerCost)
    char.location = targetLocation

    broadcastEvent("proc", char.name .. " moves to " .. targetLocation .. ". (-" .. hungerCost .. " Hunger)")

    -- Move the standee
    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    -- Audio cues: walk SFX always; meet SFX if another character is already
    -- at the destination (greet on arrival).
    local othersAtTarget = false
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == targetLocation then
            othersAtTarget = true; break
        end
    end
    if othersAtTarget then
        safecall(function() Audio.playMeet() end, "Audio")
    else
        safecall(function() Audio.playWalk() end, "Audio")
    end

    -- Coco's perk: Wanderer's Gift — +1 Sanity when moving to a new location
    if char.name == "Coco" then
        char.sanity = math.min(char.maxSanity, char.sanity + 1)
        broadcastEvent("gain", "Coco gains +1 Sanity from Wanderer's Gift (moving to a new place).")
    end

    -- The Wrongness (batch 3): arriving where something is wrong resolves it.
    safecall(function() checkWrongnessEntry(color) end, "Wrongness")

    -- Rayman's perk: can move again for free (2 spaces per action)
    -- Loud constraint: any movement today means his Night location draws +1 Threat.
    if char.name == "Rayman" then
        gameState.raymanMovedToday = true
        gameState.raymanTilesMovedToday = (gameState.raymanTilesMovedToday or 0) + 1
        broadcastEvent("gain", "Rayman can move a second space for free (Speed). Click Move again or pass.")
        broadcastEvent("warn", "Loud: Rayman moved today — wherever he spends the Night draws +1 Threat.")
        -- The second move is handled as a separate call with no action cost
        -- Tracked via a flag
        gameState.raymanBonusMove = true
    end
end

-- Rayman's free second move
function doRaymanBonusMove(color, targetLocation)
    if not gameState.raymanBonusMove then return end
    gameState.raymanBonusMove = false

    local char = gameState.activeChars[color]
    if not char or char.name ~= "Rayman" then return end
    gameState.raymanTilesMovedToday = (gameState.raymanTilesMovedToday or 0) + 1

    char.hunger = math.max(0, char.hunger - 1)
    char.location = targetLocation

    broadcastEvent("proc", "Rayman moves again to " .. targetLocation .. ". (-1 Hunger)")

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    safecall(function() checkWrongnessEntry(color) end, "Wrongness")

    local othersAtTarget = false
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == targetLocation then
            othersAtTarget = true; break
        end
    end
    if othersAtTarget then
        safecall(function() Audio.playMeet() end, "Audio")
    else
        safecall(function() Audio.playWalk() end, "Audio")
    end
end

-----------------------------------------------------------------------
-- DUSK SCRAMBLE (Design §11.3) — during Dusk each character may make one
-- 1-tile move, paying 1 Hunger. No action cost (all actions are spent by
-- Dusk anyway). This is the last chance to get somewhere safe — or daring.
-----------------------------------------------------------------------
function doDuskMove(color, targetLocation)
    if gameState.subPhase ~= "Dusk" then
        broadcastToColor("Scramble moves are only allowed during Dusk.", color, BROADCAST_COLORS.damage)
        return
    end

    local char = gameState.activeChars[color]
    if not char then return end
    if char.down then
        broadcastToColor("You are Down and cannot scramble.", color, BROADCAST_COLORS.damage)
        return
    end

    gameState.duskMoves = gameState.duskMoves or {}
    if gameState.duskMoves[color] then
        broadcastToColor("You've already scrambled this Dusk (1 tile max).", color, BROADCAST_COLORS.damage)
        return
    end

    if targetLocation == char.location then
        broadcastToColor("You're already at " .. targetLocation .. ".", color, BROADCAST_COLORS.damage)
        return
    end

    -- One tile only, even for Rayman — everyone is tired at Dusk.
    local adjacent = false
    for _, n in ipairs(LOCATION_ADJACENCY[char.location] or {}) do
        if n == targetLocation then adjacent = true; break end
    end
    local sFlags = gameState.scenarioFlags or {}
    if sFlags.shortcutPath then
        if (char.location == "JamesHouse" and targetLocation == "BadmintonCourt") or
           (char.location == "BadmintonCourt" and targetLocation == "JamesHouse") then
            adjacent = true
        end
    end
    if not adjacent then
        broadcastToColor(targetLocation .. " is not adjacent to " .. (char.location or "?") ..
            ". Scramble reaches 1 tile only.", color, BROADCAST_COLORS.damage)
        return
    end

    gameState.duskMoves[color] = true
    char.hunger = math.max(0, char.hunger - 1)
    char.location = targetLocation
    if char.name == "Rayman" then
        gameState.raymanMovedToday = true
        gameState.raymanTilesMovedToday = (gameState.raymanTilesMovedToday or 0) + 1
    end

    broadcastEvent("warn", char.name .. " scrambles to " .. targetLocation .. " as the light fades. (-1 Hunger)")

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    safecall(function() checkWrongnessEntry(color) end, "Wrongness")

    local othersAtTarget = false
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == targetLocation then
            othersAtTarget = true; break
        end
    end
    if othersAtTarget then
        safecall(function() Audio.playMeet() end, "Audio")
    else
        safecall(function() Audio.playWalk() end, "Audio")
    end

    checkDownState(color)
end

-----------------------------------------------------------------------
-- GATHER (1 action) — Design §8.1
-- Draw 1 resource from the location's resource bag.
-----------------------------------------------------------------------
function doGather(color)
    local char = gameState.activeChars[color]
    if not char then return end

    local loc = char.location or ""

    -- The Treeguard guards the timber: no gathering at its lair (Design §14.2).
    local tg = gameState.treeguard
    if tg and tg.active and loc == tg.location then
        broadcastToColor("The Treeguard looms over the timber — no Gathering at " .. loc ..
            " while it stands. Fight it, or Appease it (2 Wood at its tile).", color, BROADCAST_COLORS.damage)
        return
    end

    if not spendAction(color, "Gather") then return end

    broadcastEvent("proc", char.name .. " gathers at " .. loc .. ".")

    -- Determine which resource bags are available at this location
    -- Each location has tagged Infinite_Bag objects nearby
    -- For scripted mode, broadcast instruction; physical pickup is manual
    broadcastEvent("proc", "Draw 1 resource from " .. loc .. "'s resource bag.")

    -- The Stash (Design §7.1): a gather at James's House may take
    -- 2 Energy Drinks instead of the random draw.
    if loc == "JamesHouse" then
        broadcastEvent("gain", "The Stash: instead of a random draw, you may take 2 Energy Drinks.")
    end

    -- Dare — the porch light (P2_PORCH_LIGHT, design_batch3.md §2): the
    -- first Gather at a house today may become 3 resources for 2 Sanity.
    -- Offered, never imposed: the gather above stands either way.
    local isHouse = (loc == "JamesHouse" or loc == "RaymanHouse" or loc == "EllieLucaHouse")
    if gameState.ongoingDawnEffects.darePorchLight and isHouse then
        showConfirm("Dare — the porch light",
            "Upgrade this Gather to 3 resources — and lose 2 Sanity from what you see through the window?",
            function()
                if not gameState.ongoingDawnEffects.darePorchLight then return end  -- someone beat you to it
                gameState.ongoingDawnEffects.darePorchLight = nil
                local ch = gameState.activeChars[color]
                if not ch or ch.down then return end
                safecall(function() recordBeat("dare") end, "Telemetry")
                ch.sanity = math.max(0, ch.sanity - 2)
                broadcastEvent("gain", ch.name .. " takes the dare — draw 2 extra resources from " .. loc .. "'s bag (3 total).")
                broadcastEvent("damage", ch.name .. " loses 2 Sanity from what they see through the window. (Now " .. ch.sanity .. ")")
                checkDownState(color)
                refreshPhaseBanner()
            end)
    end

    -- Ellie's perk: "Knows the Pantry" (§6.4) — at her own house she picks
    -- exactly what she needs (no random draw), and takes 1 extra.
    if char.name == "Ellie" and loc == "EllieLucaHouse" then
        broadcastEvent("gain", "Ellie knows the pantry — pick the exact resources you want (no random draw), and take 1 extra!")
    end

    -- Backpack item: gather 2 instead of 1 (checked manually)
end

-----------------------------------------------------------------------
-- REST (1 action) — Design §11.2
-- Recover 1 Hunger OR 2 Sanity (player's choice). At own house: also +1 Health.
-----------------------------------------------------------------------
function doRest(color, choice)
    if not spendAction(color, "Rest") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Check ongoing restrictions
    if choice == "hunger" and gameState.ongoingDawnEffects.restNoHunger then
        broadcastEvent("warn", "Rest cannot restore Hunger (ongoing Dawn effect).")
        choice = "sanity"
    end
    if choice == "sanity" and gameState.ongoingDawnEffects.restNoSanity then
        broadcastEvent("warn", "Rest cannot restore Sanity (ongoing Dawn effect).")
        choice = "hunger"
    end

    -- Needs an Audience (§6.5): alone, Luca's Sanity does not regenerate.
    if choice == "sanity" and char.name == "Luca" and not charHasCompany(color) then
        broadcastEvent("warn", "Needs an Audience: Luca is alone — his Sanity won't regenerate. He rests for Hunger instead.")
        choice = "hunger"
    end

    if choice == "hunger" then
        char.hunger = math.min(char.maxHunger, char.hunger + 1)
        broadcastEvent("gain", char.name .. " rests: +1 Hunger. (Now " .. char.hunger .. ")")
    else
        char.sanity = math.min(char.maxSanity, char.sanity + 2)
        broadcastEvent("gain", char.name .. " rests: +2 Sanity. (Now " .. char.sanity .. ")")
    end

    -- At own house: also +1 Health. Nothing Left to Lose (Design §15.2):
    -- at Doom 25, Rest heals +1 Health anywhere — non-stacking with the
    -- home bonus (one +1 Health either way).
    local home = CHARACTER_HOMES[char.name]
    if home and char.location == home then
        char.health = math.min(char.maxHealth, char.health + 1)
        broadcastEvent("gain", char.name .. " rests at home: +1 Health. (Now " .. char.health .. ")")
    elseif gameState.ongoingDawnEffects.doom25 then
        char.health = math.min(char.maxHealth, char.health + 1)
        broadcastEvent("gain", char.name .. " rests: +1 Health (Nothing Left to Lose). (Now " .. char.health .. ")")
    end
end

-----------------------------------------------------------------------
-- FIGHT (1 action) — Design §11.2 / §12
-- Click-to-complete like Move/Craft/Cook: onActFight (ui_actionbar.lua)
-- spawns a FIGHT button on every fightable thing at the tile; the click
-- lands here and resolves through beginCombat (combat.lua) with real
-- statlines — THREAT_STATS for cards, boss standlines for standees.
-----------------------------------------------------------------------
local FIGHT_RADIUS = 7   -- same "at this tile" radius as festering / Pry

-- Phase-boss statlines, mirroring the standee descriptions baked by
-- build_save.py (bosses list) and the balance sim's BOSSES table. The
-- Source reads SOURCE_MAX_HP (combat.lua, loaded earlier) so the batch-4
-- calibration knob stays single-sourced; the Treeguard resolves through
-- TREEGUARD_STATS at call time (treeguard.lua loads after this file).
BOSS_BASE_STATS = {
    ["Boss:Deerclops"]   = { name = "Deerclops",     hp = 6,             attack = 3 },
    ["Boss:EyeOfTerror"] = { name = "Eye of Terror", hp = 8,             attack = 3 },
    ["Boss:TheSource"]   = { name = "The Source",    hp = SOURCE_MAX_HP, attack = 3 },
}

-- Card-text combat riders the statline columns can't express.
COMBAT_SPECIALS = {
    T_ROOMMATE = { sanityCostPerAttack = 1 },   -- "1 Sanity per attack die rolled"
}

function threatStatsForCard(card)
    if card.getTags then
        for _, tag in ipairs(card.getTags()) do
            if THREAT_STATS and THREAT_STATS[tag] then return THREAT_STATS[tag], tag end
        end
    end
    local nick = (card.getNickname and card.getNickname()) or ""
    local s = THREAT_STATS_BY_NAME and THREAT_STATS_BY_NAME[nick]
    if s then
        for id, stats in pairs(THREAT_STATS) do
            if stats == s then return s, id end
        end
    end
    return nil, nil
end

function bossStatsFor(obj)
    for tag, s in pairs(BOSS_BASE_STATS) do
        if obj.hasTag and obj.hasTag(tag) then
            return { name = s.name, hp = s.hp, attack = s.attack }
        end
    end
    if obj.hasTag and obj.hasTag("Boss:Treeguard") and TREEGUARD_STATS then
        return { name = TREEGUARD_STATS.name, hp = TREEGUARD_STATS.hp, attack = TREEGUARD_STATS.attack }
    end
    return nil   -- Charlie's standee (and anything unknown) can't be fought
end

-- Everything fightable at a tile: { {obj, stats, boss}, ... }
function fightTargetsAt(locName)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    local function near(obj)
        local p = obj.getPosition()
        local dx, dz = p.x - tp.x, p.z - tp.z
        return (dx * dx + dz * dz) <= (FIGHT_RADIUS * FIGHT_RADIUS)
    end
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        if obj.type == "Card" and near(obj) then
            local stats = threatStatsForCard(obj)
            if stats and stats.hp > 0 then
                table.insert(out, { obj = obj, stats = stats, boss = false })
            end
        end
    end
    for _, obj in ipairs(findAllByTag("Boss")) do
        if near(obj) then
            local stats = bossStatsFor(obj)
            if stats then table.insert(out, { obj = obj, stats = stats, boss = true }) end
        end
    end
    return out
end

-- Precondition check; the reason doubles as the why-disabled tooltip.
function canFight(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if (char.actionsLeft or 0) <= 0 then return false, "No actions left." end
    if char.hunger < 3 then
        return false, "Too hungry to fight (Hunger < 3). Flee is always legal: 1 tile, 1 Sanity."
    end
    if #fightTargetsAt(char.location) == 0 then
        return false, "Nothing to fight at " .. (char.location or "?") .. "."
    end
    return true, nil
end

-- The FIGHT / FIGHT TOGETHER button click lands here (ui_actionbar.lua).
-- together = true pulls in every standing, fed (Hunger >= 3) ally at the
-- tile: summed dice, shared counter-attacks (Design §12.2).
function doFightTarget(color, targetObj, together)
    local char = gameState.activeChars[color]
    if not char or char.down then return end
    if char.hunger < 3 then
        broadcastEvent("damage", char.name .. " is too hungry to fight (Hunger < 3)! You can still Flee: move 1 tile away, paying 1 Sanity.")
        return
    end

    local isBoss = targetObj.hasTag and targetObj.hasTag("Boss")
    local stats, cardId
    if isBoss then
        stats = bossStatsFor(targetObj)
    else
        stats, cardId = threatStatsForCard(targetObj)
    end
    if not stats or (stats.hp or 0) <= 0 then
        broadcastToColor("That can't be fought.", color, BROADCAST_COLORS.damage)
        return
    end

    if not spendAction(color, "Fight") then return end

    local participants = { color }
    if together then
        for c2, ch2 in pairs(gameState.activeChars) do
            if c2 ~= color and not ch2.down and ch2.location == char.location then
                if ch2.hunger >= 3 then
                    table.insert(participants, c2)
                else
                    broadcastEvent("warn", ch2.name .. " is too hungry to join the fight (Hunger < 3).")
                end
            end
        end
    end

    local threatData = { name = stats.name, hp = stats.hp, attack = stats.attack, maxHp = stats.hp }
    if not isBoss then
        threatData.cardGuid = targetObj.guid
        -- Chip damage from earlier fights carries over (gameState.threatDamage).
        local dmg = (gameState.threatDamage or {})[targetObj.guid] or 0
        threatData.hp = math.max(0, stats.hp - dmg)
        if dmg > 0 then
            broadcastEvent("proc", stats.name .. " is already wounded — " .. threatData.hp .. " HP left.")
        end
        local special = cardId and COMBAT_SPECIALS[cardId]
        if special then
            for k, v in pairs(special) do threatData[k] = v end
        end
    end

    if #participants > 1 then
        local names = {}
        for _, c in ipairs(participants) do names[#names + 1] = gameState.activeChars[c].name end
        broadcastEvent("proc", table.concat(names, " & ") .. " fight " .. stats.name .. " together!")
    end

    return beginCombat(participants, threatData)
end

-----------------------------------------------------------------------
-- FLEE (Design §12.4) — the Night escape valve. When a threat is at your
-- tile, you may flee instead of fighting: move 1 tile away, paying
-- 1 Sanity (running in the dark is terrifying, not tiring). Always
-- legal — even starving (Hunger < 3 blocks Fight, never Flee). The
-- threat stays where it was, and festers at Dawn.
-----------------------------------------------------------------------
function doFlee(color, targetLocation)
    local char = gameState.activeChars[color]
    if not char then return end
    if char.down then
        broadcastToColor("You are Down and cannot flee.", color, BROADCAST_COLORS.damage)
        return
    end

    local adjacent = false
    for _, n in ipairs(LOCATION_ADJACENCY[char.location] or {}) do
        if n == targetLocation then adjacent = true; break end
    end
    if not adjacent then
        broadcastToColor(targetLocation .. " is not adjacent to " .. (char.location or "?") ..
            ". Flee reaches 1 tile only.", color, BROADCAST_COLORS.damage)
        return
    end

    char.sanity = math.max(0, char.sanity - 1)
    char.location = targetLocation

    broadcastEvent("warn", char.name .. " flees to " .. targetLocation ..
        " (-1 Sanity). The threat remains behind — and festers at Dawn.")

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    safecall(function() checkWrongnessEntry(color) end, "Wrongness")
    checkDownState(color)
end

-----------------------------------------------------------------------
-- TRADE (free once/turn at same location, costs 1 action otherwise)
-----------------------------------------------------------------------
function doTrade(color, targetColor)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Check if target is at the same location
    local target = targetColor and gameState.activeChars[targetColor]
    local sameLocation = true
    if target then
        sameLocation = (char.location == target.location)
    end

    -- Track free trades per turn (1 free trade per turn at same location)
    gameState.tradesThisTurn = gameState.tradesThisTurn or {}
    local tradeCount = gameState.tradesThisTurn[color] or 0

    if not sameLocation then
        -- Different location: costs 1 action
        if not spendAction(color, "Trade (remote)") then return end
        broadcastEvent("proc", char.name .. " spends an action to trade with a player at a different location.")
    elseif tradeCount >= 1 then
        -- Same location but already used free trade: costs 1 action
        if not spendAction(color, "Trade (extra)") then return end
        broadcastEvent("proc", char.name .. " spends an action for an additional trade this turn.")
    else
        -- Free trade (first one this turn, same location)
        gameState.tradesThisTurn[color] = tradeCount + 1
        broadcastEvent("proc", char.name .. " trades for free (1 per turn at same location).")
    end

    broadcastEvent("proc", "Players at " .. (char.location or "?") ..
        " may exchange resources and items now.")
    safecall(function() Audio.playTradeChat() end, "Audio")
end

-----------------------------------------------------------------------
-- USE ENERGY DRINK (free action, James-specific)
-----------------------------------------------------------------------
function doEnergyDrink(color)
    local char = gameState.activeChars[color]
    if not char then return end

    if char.name ~= "James" then
        broadcastEvent("proc", char.name .. " uses an Energy Drink. +2 Sanity.")
    else
        broadcastEvent("proc", "James uses an Energy Drink. +2 Sanity. Addiction satisfied for today.")
        gameState.jamesEnergyDrinkUsed = true
    end

    char.sanity = math.min(char.maxSanity, char.sanity + 2)
    broadcastEvent("gain", char.name .. " gains +2 Sanity from Energy Drink. (Now " .. char.sanity .. ")")
end

-----------------------------------------------------------------------
-- EAT RAW FOOD (free action) — Design §8.4
-- +1 Hunger, -1 Sanity (mismatched currency)
-----------------------------------------------------------------------
function doEatRaw(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Particular Eater (§6.4): Ellie cannot eat raw food, ever.
    if char.name == "Ellie" then
        broadcastToColor("Ellie can't eat raw food (Particular Eater). Cook it first — Crockpot Master makes recipes cheaper.",
            color, BROADCAST_COLORS.damage)
        return
    end

    char.hunger = math.min(char.maxHunger, char.hunger + 1)
    char.sanity = math.max(0, char.sanity - 1)

    broadcastEvent("proc", char.name .. " eats raw food. +1 Hunger, -1 Sanity.")
    checkDownState(color)
end

-----------------------------------------------------------------------
-- PASS (end turn voluntarily)
-----------------------------------------------------------------------
function doPass(color)
    local char = gameState.activeChars[color]
    if not char then return end

    broadcastEvent("proc", char.name .. " passes. Turn over.")
    endPlayerTurn(color)
end

-----------------------------------------------------------------------
-- BARRICADE (1 action, costs 1 Wood) — Improvement: reduces night threats
-- Spend 1 Wood to barricade a location. That location draws -1 Threat tonight.
-- Barricade is consumed after one night.
-----------------------------------------------------------------------
function doBarricade(color)
    if not spendAction(color, "Barricade") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Auto-verify and pay the 1 Wood; refund the action if unaffordable.
    if not verifyAndPayResources(color, {Wood=1}, "the Barricade") then
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    local loc = char.location or ""

    -- Track barricades per location
    gameState.barricades = gameState.barricades or {}
    gameState.barricades[loc] = (gameState.barricades[loc] or 0) + 1

    broadcastEvent("gain", char.name .. " barricades " .. loc .. "! (-1 Threat draw tonight)")
end

-----------------------------------------------------------------------
-- DEFEND (Rayman special — 1 action)
-- Redirects all return damage to Rayman for one combat round
-----------------------------------------------------------------------
function doDefend(color)
    if not spendAction(color, "Defend") then return end

    local char = gameState.activeChars[color]
    if not char or char.name ~= "Rayman" then
        broadcastEvent("damage", "Only Rayman can Defend.")
        char.actionsLeft = char.actionsLeft + 1  -- refund
        return
    end

    gameState.raymanDefending = true
    broadcastEvent("gain", "Rayman DEFENDS (Backboard Block)! Counter-attack damage is redirected to him until his next turn.")
end

-----------------------------------------------------------------------
-- PATTERN RECOGNITION (James, free action, once per day) — Design §6.1
-- Peek at the top card of any deck; the name goes to James alone.
-----------------------------------------------------------------------
PEEK_DECKS = {
    Phase   = { label = "Dawn deck",  get = function() return getPhaseDeck(gameState.phase) end },
    Threat  = { label = "Threat deck",  get = getThreatDeck },
    Market  = { label = "Market deck",  get = getMarketDeck },
    Visitor = { label = "Visitor deck", get = getVisitorDeck },
}

function canPeek(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.name ~= "James" then return false, "Only James reads the patterns." end
    if char.down then return false, "You are Down." end
    if gameState.jamesPeekUsed then return false, "Pattern Recognition is spent for today." end
    return true, nil
end

function doPeek(color, deckKey)
    local ok, why = canPeek(color)
    if not ok then
        broadcastToColor(why or "Can't peek right now.", color, BROADCAST_COLORS.damage)
        return false
    end
    local entry = PEEK_DECKS[deckKey]
    local deck = entry and entry.get()
    if not deck or not deck.getObjects or (deck.getQuantity and deck.getQuantity() or 0) <= 0 then
        broadcastToColor("That deck is empty (or missing).", color, BROADCAST_COLORS.damage)
        return false
    end
    local top = deck.getObjects()[1]
    local name = top and ((top.nickname ~= "" and top.nickname) or top.name) or "???"
    gameState.jamesPeekUsed = true
    broadcastEvent("proc", "James studies the " .. entry.label .. "... Pattern Recognition (free action, once per day).")
    broadcastToColor("Top of the " .. entry.label .. ": " .. name .. ". Tell the team — or don't.",
        color, BROADCAST_COLORS.gain)
    return true
end

-----------------------------------------------------------------------
-- RALLY (Luca, free, once per turn) — Design §6.5
-- Give an ally at Luca's tile or an adjacent one a free non-movement
-- action: +1 to their action pool for this Day. (The "non-movement" part
-- is a table rule — the script can't earmark a specific future action.)
-----------------------------------------------------------------------
function canRally(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.name ~= "Luca" then return false, "Only Luca can Rally." end
    if char.down then return false, "You are Down." end
    if gameState.lucaRallyUsed then return false, "Rally is spent for this turn." end
    if #rallyTargets(color) == 0 then
        return false, "No ally nearby who can still act (same or adjacent tile, actions remaining)."
    end
    return true, nil
end

-- Allies eligible for Rally: standing, at Luca's tile or adjacent, with
-- actions still in their pool (a finished turn has 0 left — the gift
-- would evaporate).
function rallyTargets(color)
    local out = {}
    local char = gameState.activeChars[color]
    if not char then return out end
    local nearby = { [char.location or ""] = true }
    for _, n in ipairs(LOCATION_ADJACENCY[char.location] or {}) do nearby[n] = true end
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and nearby[ch2.location or ""]
            and (ch2.actionsLeft or 0) > 0 then
            table.insert(out, c2)
        end
    end
    return out
end

function doRally(lucaColor, targetColor)
    local ok, why = canRally(lucaColor)
    if not ok then
        broadcastToColor(why or "Can't Rally right now.", lucaColor, BROADCAST_COLORS.damage)
        return false
    end
    local target = gameState.activeChars[targetColor]
    local luca = gameState.activeChars[lucaColor]
    local valid = false
    for _, c in ipairs(rallyTargets(lucaColor)) do
        if c == targetColor then valid = true break end
    end
    if not target or not valid then
        broadcastToColor("That ally can't be rallied (must be at your tile or adjacent, standing, with actions left).",
            lucaColor, BROADCAST_COLORS.damage)
        return false
    end
    gameState.lucaRallyUsed = true
    target.actionsLeft = target.actionsLeft + 1
    broadcastEvent("gain", "Luca rallies " .. target.name .. " — a free action this Day! (Non-movement: spend it on Gather, Craft, Cook, Rest, Fight... not Move.)")
    return true
end

-----------------------------------------------------------------------
-- PRY (free action, requires a Pry tool) — Design §13.5, design_batch3.md §3
-- The one coded verb behind every sealed thing: sealed Threat cards and
-- the Sealed Basement (a fixed object placed at Ellie & Luca's House by
-- build_save.py). Guaranteed reward behind a tool gate — no dice.
-----------------------------------------------------------------------
PRY_TOOLS = {
    { id = "M_CROWBAR",  label = "Crowbar" },
    { id = "M_LOCKPICK", label = "Lockpick" },
    { id = "M_PRY_BAR",  label = "Pry Bar" },
}

-- Sealed-card rewards live in SEALED_REWARDS (lua/threat_types.lua,
-- AUTO-GENERATED from the `pry_reward` column of cards_threats.csv), so the
-- card face and the delivered reward can never drift apart. The Basement is
-- a placed object, not a card — its entry is authored here.
SEALED_REWARDS.BASEMENT = {
    market = 1, resources = { Food = 2, Wood = 1, Battery = 1 },
    line = "The basement cache, hoarded before the week began: a free Market Item plus 2 Food + 1 Wood + 1 Battery.",
}

local PRY_RADIUS = 7   -- same "at this tile" radius as festering / signatures

-- Which Pry tool (label) does this player hold? Hand + player-board area,
-- the same two places the night light check looks.
function playerPryTool(color)
    local char = gameState.activeChars[color]
    if not char then return nil end
    local candidates = {}
    local ok, handObjs = pcall(function() return Player[color].getHandObjects() end)
    if ok and handObjs then
        for _, o in ipairs(handObjs) do candidates[#candidates + 1] = o end
    end
    local board = getPlayerBoard(char.name)
    if board then
        local pos = board.getPosition()
        local b = board.getBoundsNormalized()
        local pad = 1.5
        for _, obj in ipairs(getAllObjects()) do
            local p = obj.getPosition()
            if p.x >= pos.x - b.size.x * 0.5 - pad and p.x <= pos.x + b.size.x * 0.5 + pad
                and p.z >= pos.z - b.size.z * 0.5 - pad and p.z <= pos.z + b.size.z * 0.5 + pad then
                candidates[#candidates + 1] = obj
            end
        end
    end
    for _, obj in ipairs(candidates) do
        for _, tool in ipairs(PRY_TOOLS) do
            if obj.hasTag and obj.hasTag(tool.id) then return tool.label end
            local nick = (obj.getNickname and obj.getNickname()) or ""
            if nick:lower():find(tool.label:lower(), 1, true) then return tool.label end
        end
    end
    return nil
end

-- Sealed things at this tile: { {obj, id}, ... }. id keys SEALED_REWARDS.
local function _sealedAtTile(locName)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    for _, obj in ipairs(getAllObjects()) do
        local sealedId = nil
        if obj.hasTag then
            if obj.hasTag("SealedBasement") and not gameState.basementOpened then
                sealedId = "BASEMENT"
            else
                for id in pairs(SEALED_REWARDS) do
                    if id ~= "BASEMENT" and obj.hasTag(id) then sealedId = id; break end
                end
            end
        end
        if sealedId then
            local p = obj.getPosition()
            local dx, dz = p.x - tp.x, p.z - tp.z
            if (dx * dx + dz * dz) <= (PRY_RADIUS * PRY_RADIUS) then
                table.insert(out, { obj = obj, id = sealedId })
            end
        end
    end
    return out
end

-- Precondition check; the reason doubles as the why-disabled tooltip.
function canPry(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if #_sealedAtTile(char.location) == 0 then
        return false, "Nothing sealed at " .. (char.location or "?") .. "."
    end
    local tool = playerPryTool(color)
    if not tool then
        return false, "You need a Crowbar, Lockpick, or Pry Bar (in hand or by your board)."
    end
    return true, tool
end

local function _deliverSealedReward(color, reward, locName)
    if reward.resources then
        local tile = getLocationTile(locName)
        local pos = tile and tile.getPosition()
        local i = 0
        for resType, qty in pairs(reward.resources) do
            local bag = getResourceBag(resType)
            for _ = 1, qty do
                i = i + 1
                if bag and pos then
                    safecall(function()
                        bag.takeObject({ position = { pos.x + (i % 3) * 1.2 - 1.2, pos.y + 3, pos.z + 2 },
                                         smooth = true })
                    end, "PryLoot")
                end
            end
        end
    end
    if reward.market and getMarketDeck() then
        local deck = getMarketDeck()
        if (deck.getQuantity and deck.getQuantity() or 0) > 0 then
            local hz = getHandZone(color)
            local tile = getLocationTile(locName)
            local dest = (hz and hz.getPosition()) or (tile and tile.getPosition()) or Vector(0, 2, 0)
            safecall(function()
                deck.takeObject({
                    position = dest + Vector(0, 2, 0),
                    rotation = {0, 180, 0},
                    smooth = true,
                    callback_function = function(c)
                        broadcastEvent("gain", "Sealed away all this time: " .. (c.getNickname() or "an Item") .. " — yours, free.")
                    end,
                })
            end, "PryMarket")
        end
    end
    if reward.line then broadcastEvent("gain", reward.line) end
end

function doPry(color)
    local ok, toolOrReason = canPry(color)
    if not ok then
        broadcastToColor(toolOrReason or "Nothing to pry.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    local target = _sealedAtTile(char.location)[1]
    local reward = SEALED_REWARDS[target.id]
    local name = (target.obj.getNickname and target.obj.getNickname() ~= "" and target.obj.getNickname())
        or "the sealed thing"

    broadcastEvent("proc", char.name .. " sets the " .. toolOrReason .. " against " .. name .. "... and it gives. (Pry is a free action.)")
    _deliverSealedReward(color, reward, char.location)

    if target.id == "BASEMENT" then
        gameState.basementOpened = true
    end
    pcall(function() target.obj.destruct() end)
    refreshPhaseBanner()
    return true
end

-----------------------------------------------------------------------
-- STABILIZE (1 action, requires Bandage) — Design §12.3
-----------------------------------------------------------------------
function doStabilize(color, targetColor)
    if not spendAction(color, "Stabilize") then return end

    local char = gameState.activeChars[color]
    local target = gameState.activeChars[targetColor]

    if not target or not target.down then
        broadcastEvent("proc", "Target is not Down.")
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    if char.location ~= target.location then
        broadcastEvent("damage", "Must be at the same location to stabilize.")
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    -- Requires Bandage item (manual check)
    broadcastEvent("proc", char.name .. " stabilizes " .. target.name .. " with a Bandage!")
    target.health = 1
    target.down = false
    broadcastEvent("gain", target.name .. " is stabilized at 1 Health. (Not a full revival.)")
end
