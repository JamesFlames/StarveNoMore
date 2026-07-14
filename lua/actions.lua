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

