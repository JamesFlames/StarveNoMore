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
        broadcastEvent("gain", "Rayman can move a second space for free (Court Master). Click Move again or pass.")
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
-- Engage an enemy at the current location.
-----------------------------------------------------------------------
function doFight(color)
    if not spendAction(color, "Fight") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Low Hunger check: cannot fight if Hunger < 3 (Flee is always legal)
    if char.hunger < 3 then
        broadcastEvent("damage", char.name .. " is too hungry to fight (Hunger < 3)! You can still Flee: move 1 tile away, paying 1 Sanity.")
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
    broadcastEvent("gain", "Rayman DEFENDS! All return damage redirected to him this combat round.")
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
