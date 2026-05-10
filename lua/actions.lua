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

    -- Move standee back if location changed
    if char.location ~= snap.location then
        char.location = snap.location
        local standee = getCharacterStandee(char.name)
        local tile = getLocationTile(snap.location)
        if standee and tile then
            standee.setPositionSmooth(tile.getPosition() + Vector(0, 1.5, 0))
        end
    end

    moveDoomMarker(gameState.doom)
    gameState.undoSnapshot = nil  -- can only undo once

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
        standee.setPositionSmooth(tile.getPosition() + Vector(0, 1.5, 0))
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

    -- Rayman's perk: can move again for free (2 spaces per action)
    if char.name == "Rayman" then
        broadcastEvent("gain", "Rayman can move a second space for free (Court Master). Click Move again or pass.")
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

    char.hunger = math.max(0, char.hunger - 1)
    char.location = targetLocation

    broadcastEvent("proc", "Rayman moves again to " .. targetLocation .. ". (-1 Hunger)")

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(tile.getPosition() + Vector(0, 1.5, 0))
    end

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
-- GATHER (1 action) — Design §8.1
-- Draw 1 resource from the location's resource bag.
-----------------------------------------------------------------------
function doGather(color)
    if not spendAction(color, "Gather") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    local loc = char.location or ""
    broadcastEvent("proc", char.name .. " gathers at " .. loc .. ".")

    -- Determine which resource bags are available at this location
    -- Each location has tagged Infinite_Bag objects nearby
    -- For scripted mode, broadcast instruction; physical pickup is manual
    broadcastEvent("proc", "Draw 1 resource from " .. loc .. "'s resource bag.")

    -- Ellie's perk: "Knows the Pantry" — gathers 1 extra at Ellie & Luca's House
    if char.name == "Ellie" and loc == "EllieLucaHouse" then
        broadcastEvent("gain", "Ellie knows the pantry — gather 1 extra resource!")
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

    if choice == "hunger" then
        char.hunger = math.min(char.maxHunger, char.hunger + 1)
        broadcastEvent("gain", char.name .. " rests: +1 Hunger. (Now " .. char.hunger .. ")")
    else
        char.sanity = math.min(char.maxSanity, char.sanity + 2)
        broadcastEvent("gain", char.name .. " rests: +2 Sanity. (Now " .. char.sanity .. ")")
    end

    -- At own house: also +1 Health
    local home = CHARACTER_HOMES[char.name]
    if home and char.location == home then
        char.health = math.min(char.maxHealth, char.health + 1)
        broadcastEvent("gain", char.name .. " rests at home: +1 Health. (Now " .. char.health .. ")")
    end
end

-----------------------------------------------------------------------
-- FIGHT (1 action) — Design §11.2 / §12
-- Engage an enemy at the current location.
-----------------------------------------------------------------------
function doFight(color)
    if not spendAction(color, "Fight") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Low Hunger check: cannot fight if Hunger < 3
    if char.hunger < 3 then
        broadcastEvent("damage", char.name .. " is too hungry to fight (Hunger < 3)!")
        char.actionsLeft = char.actionsLeft + 1  -- refund
        return
    end

    broadcastEvent("proc", char.name .. " engages in combat at " .. (char.location or "?") .. "!")
    broadcastEvent("proc", "Select the Threat card to fight. Combat will resolve via the combat helper.")

    -- In a full implementation, this would prompt for target selection
    -- For now, broadcast the instruction for manual resolution
    -- Players can call resolveCombat() directly or use the combat helper button
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

    local loc = char.location or ""

    -- Track barricades per location
    gameState.barricades = gameState.barricades or {}
    gameState.barricades[loc] = (gameState.barricades[loc] or 0) + 1

    broadcastEvent("gain", char.name .. " barricades " .. loc .. "! (-1 Threat draw tonight). Costs 1 Wood.")
    broadcastEvent("proc", "Discard 1 Wood from your resources now.")
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
    broadcastEvent("gain", "Rayman DEFENDS! All return damage redirected to him this combat round.")
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
