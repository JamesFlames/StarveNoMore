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
        -- Both halves of the Loud bookkeeping, or neither: the tile COUNT
        -- feeds two thresholds of its own (the 3p Loud relief at <3, night.lua,
        -- and the 3p Big Appetite relief at <2, tick_victory.lua). Snapshotting
        -- only the boolean left an undone move still counted against both.
        raymanTilesMovedToday = gameState.raymanTilesMovedToday,
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
    gameState.raymanTilesMovedToday = snap.raymanTilesMovedToday or 0
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

    -- Surcharges in actions: low Health (§10.1) and P3_GRAVITY_WRONG's
    -- moveCostPlus1 each add one, and they stack — both are "this step is
    -- harder than it should be", from different directions.
    local extraActions, why = 0, {}
    if char.health < 3 and char.health > 0 then
        extraActions = extraActions + 1
        why[#why + 1] = "Health < 3"
    end
    if gameState.ongoingDawnEffects.moveCostPlus1 then
        extraActions = extraActions + 1
        why[#why + 1] = "gravity feels wrong"
    end
    if extraActions > 0 then
        if char.actionsLeft < extraActions then
            broadcastEvent("damage", char.name .. " can't afford this move — it needs " ..
                extraActions .. " extra action(s) (" .. table.concat(why, ", ") .. ") they don't have.")
            -- Refund the action spendAction just took
            char.actionsLeft = char.actionsLeft + 1
            return
        end
        char.actionsLeft = char.actionsLeft - extraActions
        broadcastEvent("warn", char.name .. " spends " .. extraActions ..
            " extra action(s) to move (" .. table.concat(why, ", ") .. ").")
    end

    -- Movement costs 1 Hunger
    local hungerCost = 1

    local from = char.location or ""
    hungerCost = hungerCost + sportCourtSurcharge(from, targetLocation)

    -- Shortcut scenario: free movement between JamesHouse and BadmintonCourt
    local sFlags = gameState.scenarioFlags or {}
    if sFlags.shortcutPath then
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

    local hungerCost = 1 + sportCourtSurcharge(char.location, targetLocation)
    char.hunger = math.max(0, char.hunger - hungerCost)
    char.location = targetLocation

    broadcastEvent("proc", "Rayman moves again to " .. targetLocation .. ". (-" .. hungerCost .. " Hunger)")

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

    -- Secret Dusk commitment (§11.3 variant, off by default). The table still
    -- argues; it just can't watch you comply. The move is banked here and
    -- applied for everyone at once by revealDuskCommitments (turns.lua), so
    -- nobody can react to anybody else's declaration.
    if gameState.duskSecret then
        gameState.duskPending = gameState.duskPending or {}
        gameState.duskPending[color] = targetLocation
        printToColor("Committed: you'll slip to " .. targetLocation ..
                     " when the light goes. Nobody else can see it yet. (-1 Hunger on reveal)",
                     color, BROADCAST_COLORS.warn)
        broadcastEvent("proc", char.name .. " has committed their night. Where, they aren't saying.")
        safecall(function() refreshDuskReadyLabel() end, "DuskReady")
        return
    end

    local hungerCost = 1 + sportCourtSurcharge(char.location, targetLocation)
    char.hunger = math.max(0, char.hunger - hungerCost)
    char.location = targetLocation
    if char.name == "Rayman" then
        gameState.raymanMovedToday = true
        gameState.raymanTilesMovedToday = (gameState.raymanTilesMovedToday or 0) + 1
    end

    broadcastEvent("warn", char.name .. " scrambles to " .. targetLocation ..
        " as the light fades. (-" .. hungerCost .. " Hunger)")

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
-- Draw resources from the location's supply and lay them by the player's
-- board automatically — nobody reaches into a bag. Special cases: James's
-- House Stash (2 Energy Drinks), Ellie's pantry pick, the Backpack (+1),
-- and the porch-light dare (+2 for -2 Sanity).
-----------------------------------------------------------------------
local RES_LABELS = { EnergyDrink = "Energy Drink" }
local function _resLabel(r) return RES_LABELS[r] or r end

-- One line summarising a gather: { Food = 2, Wood = 1 } -> "2 Food + 1 Wood".
local function _describeHaul(got)
    local parts = {}
    for r, n in pairs(got) do parts[#parts + 1] = n .. " " .. _resLabel(r) end
    return table.concat(parts, " + ")
end

-- After tokens land, whisper the player's full stock so "what do I have
-- now?" never needs counting tokens by eye. Delayed so the smooth-moving
-- tokens are actually beside the board when getPlayerResources scans.
function announceInventory(color)
    Wait.time(function()
        safecall(function()
            local res = getPlayerResources(color)
            printToColor(string.format(
                "You now hold: Wood %d · Metal %d · Cloth %d · Food %d · Energy Drink %d · Battery %d  (tokens sit beside your player board; the panel on the left tracks them live).",
                res.Wood or 0, res.Metal or 0, res.Cloth or 0, res.Food or 0,
                res.EnergyDrink or 0, res.Battery or 0), color, {0.7, 1.0, 0.7})
            refreshStatDisplay()
        end, "InvSummary")
    end, 1.6)
end

-- Does this player carry a Backpack (Persistent tool: gather +1)?
function playerHasBackpack(color)
    local charName = colorToCharacter(color)
    if not charName then return false end
    for _, obj in ipairs(getPlayerCarriedObjects(color, charName)) do
        if safeHasTag(obj, "M_BACKPACK") then return true end
        if safeNickname(obj):lower():find("backpack", 1, true) then return true end
    end
    return false
end

-- Draw `n` random resources from `loc`'s yield table straight to `color`'s
-- board area, then announce the haul.
function gatherRandomResources(color, loc, n)
    local char = gameState.activeChars[color]
    if not char then return end
    local yields = LOCATION_YIELDS[loc] or {"Food"}
    local got = {}
    for _ = 1, (n or 1) do
        local resType = yields[gameRoll(#yields)]
        giveResource(color, resType, 1)
        got[resType] = (got[resType] or 0) + 1
    end
    broadcastEvent("gain", char.name .. " gathers " .. _describeHaul(got) .. " at " .. loc ..
        " (tokens delivered to your board automatically).")
    announceInventory(color)
end

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

    -- P2_RAIN_STARTS (rainSanityCost): searching a sport court in the rain
    -- costs 1 Sanity. Charged before the haul so a Gather that puts the
    -- character Down still delivers what they found.
    if gameState.ongoingDawnEffects.rainSanityCost and isSportCourt(loc) then
        char.sanity = math.max(0, char.sanity - 1)
        broadcastEvent("damage", char.name .. " searches " .. loc ..
            " in the rain — 1 Sanity. (Now " .. char.sanity .. ")")
        checkDownState(color)
    end

    local extra = playerHasBackpack(color) and 1 or 0   -- Backpack: gather +1
    if extra > 0 then
        broadcastToColor("Your Backpack gathers 1 extra resource.", color, BROADCAST_COLORS.gain)
    end

    -- Ellie's perk: "Knows the Pantry" (§6.4) — at her own house she picks
    -- exactly what she needs (no random draw), and takes 1 extra.
    if char.name == "Ellie" and loc == "EllieLucaHouse" then
        showResourcePicker(color, 2 + extra, "Ellie knows the pantry — take any resources you want:")
        return
    end

    local isHouse = (loc == "JamesHouse" or loc == "RaymanHouse" or loc == "EllieLucaHouse")

    -- Dare — the porch light (P2_PORCH_LIGHT, design_batch3.md §2): the base
    -- draw lands now; the dare offers +2 more for 2 Sanity. Rare, so it — not
    -- the Stash — owns the confirm dialog on the turn it fires.
    if gameState.ongoingDawnEffects.darePorchLight and isHouse then
        gatherRandomResources(color, loc, 1 + extra)
        showConfirm("Dare — the porch light",
            "Draw 2 extra resources — and lose 2 Sanity from what you see through the window?",
            function()
                if not gameState.ongoingDawnEffects.darePorchLight then return end  -- someone beat you to it
                gameState.ongoingDawnEffects.darePorchLight = nil
                local ch = gameState.activeChars[color]
                if not ch or ch.down then return end
                safecall(function() recordBeat("dare") end, "Telemetry")
                ch.sanity = math.max(0, ch.sanity - 2)
                gatherRandomResources(color, loc, 2)
                broadcastEvent("gain", ch.name .. " takes the dare — 2 extra resources from " .. loc .. ".")
                broadcastEvent("damage", ch.name .. " loses 2 Sanity from what they see through the window. (Now " .. ch.sanity .. ")")
                checkDownState(color)
                refreshPhaseBanner()
            end)
        return
    end

    -- The Stash (Design §7.1): a Gather at James's House may take 2 Energy
    -- Drinks instead of the random draw. Confirm = the Stash, Cancel = draw.
    if loc == "JamesHouse" then
        showConfirm("The Stash",
            "Take 2 Energy Drinks (The Stash)?\nConfirm = 2 Energy Drinks.  Cancel = 1 random resource.",
            function()
                giveResource(color, "EnergyDrink", 2)
                broadcastEvent("gain", char.name .. " raids the Stash: 2 Energy Drinks (delivered to your board).")
                announceInventory(color)
            end,
            function()
                gatherRandomResources(color, loc, 1 + extra)
            end)
        return
    end

    -- Everyone else, everywhere else: an automatic random draw.
    gatherRandomResources(color, loc, 1 + extra)
end

-----------------------------------------------------------------------
-- REST (1 action) — Design §11.2
-- Recover 1 Hunger OR 2 Sanity (player's choice). At own house: also +1 Health.
-----------------------------------------------------------------------
function doRest(color, choice)
    if not spendAction(color, "Rest") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Ongoing restrictions and Luca's Needs an Audience (§6.5) can each
    -- redirect the choice, and a redirect can land on the OTHER banned
    -- half — so the two bans are re-checked after every redirect rather
    -- than once each, in order. (Luca alone under P2_HUNGRY used to be
    -- redirected sanity -> hunger *past* restNoHunger, and rested for the
    -- Hunger the Dawn card had just forbidden.)
    local noHunger = gameState.ongoingDawnEffects.restNoHunger
    local noSanity = gameState.ongoingDawnEffects.restNoSanity
    local lucaAlone = (char.name == "Luca") and not charHasCompany(color)

    if choice == "hunger" and noHunger then
        if noSanity then
            broadcastEvent("warn", "Rest can restore neither Hunger nor Sanity today — " ..
                char.name .. " rests for nothing.")
            return
        end
        broadcastEvent("warn", "Rest cannot restore Hunger (ongoing Dawn effect).")
        choice = "sanity"
    end
    if choice == "sanity" and (noSanity or lucaAlone) then
        if noHunger then
            broadcastEvent("warn", (noSanity
                and "Rest can restore neither Hunger nor Sanity today — "
                or  "Needs an Audience, and Rest restores no Hunger today — ") ..
                char.name .. " rests for nothing.")
            return
        end
        if noSanity then
            broadcastEvent("warn", "Rest cannot restore Sanity (ongoing Dawn effect).")
        else
            broadcastEvent("warn", "Needs an Audience: Luca is alone — his Sanity won't regenerate. He rests for Hunger instead.")
        end
        choice = "hunger"
    end

    -- Last Nerve (§10.1): with any stat below 3, Rest restores 1 extra.
    -- Sampled BEFORE the restoration — the point is to reward the state you
    -- were in when you chose to rest, not to check whether the rest worked.
    local nerve = hasLastNerve(color)
    local bonus = nerve and 1 or 0
    local nerveNote = nerve and " (+1 Last Nerve)" or ""

    if choice == "hunger" then
        char.hunger = math.min(char.maxHunger, char.hunger + 1 + bonus)
        broadcastEvent("gain", char.name .. " rests: +" .. (1 + bonus) .. " Hunger" ..
            nerveNote .. ". (Now " .. char.hunger .. ")")
    else
        char.sanity = math.min(char.maxSanity, char.sanity + 2 + bonus)
        broadcastEvent("gain", char.name .. " rests: +" .. (2 + bonus) .. " Sanity" ..
            nerveNote .. ". (Now " .. char.sanity .. ")")
    end

    -- At own house: also +1 Health. Nothing Left to Lose (Design §15.2):
    -- at Doom 25, Rest heals +1 Health anywhere — non-stacking with the
    -- home bonus (one +1 Health either way). P3_GRAVITY_WRONG suspends
    -- the Health half of Rest entirely for the day.
    if gameState.ongoingDawnEffects.restNoHealth then
        broadcastEvent("warn", "Rest restores no Health today (gravity feels wrong).")
        return
    end
    local home = CHARACTER_HOMES[char.name]
    if home and char.location == home then
        char.health = math.min(char.maxHealth, char.health + 1)
        broadcastEvent("gain", char.name .. " rests at home: +1 Health. (Now " .. char.health .. ")")
    elseif gameState.ongoingDawnEffects.doom25 then
        char.health = math.min(char.maxHealth, char.health + 1)
        broadcastEvent("gain", char.name .. " rests: +1 Health (Nothing Left to Lose). (Now " .. char.health .. ")")
    end
end

