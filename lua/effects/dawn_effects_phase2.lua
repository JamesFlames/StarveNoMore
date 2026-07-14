-- dawn_effects_phase2.lua — Phase 2 (Strange Days) Dawn card effects, plus
-- the Wrongness resolver/entry check. Part of dawn_effects (see core).

-----------------------------------------------------------------------
-- Phase 2: Strange Days
-----------------------------------------------------------------------
DAWN_EFFECTS["P2_PORCH_LIGHT"] = {
    -- Dare (design_batch3.md §2): the first Gather at a house today may take
    -- 3 resources instead of 1 — and pay 2 Sanity for what's seen through
    -- the window. Offered via a confirm in doGather (actions.lua).
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.flashlightsDisabled = true
        broadcastEvent("warn", "ONGOING: Flashlights disabled tonight — only Fire counts as light.")
        gameState.ongoingDawnEffects.darePorchLight = true
        broadcastEvent("warn", "DARE: the first player to Gather at a house today may take 3 resources instead of 1 — and lose 2 Sanity from what they see through the window.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.flashlightsDisabled = nil
        gameState.ongoingDawnEffects.darePorchLight = nil
    end,
}

DAWN_EFFECTS["P2_SHADOWS_MOVE"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Shadows move. Each player rolls Sanity d8, loses half (round up).")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 8)
                local loss = math.ceil(roll / 2)
                char.sanity = math.max(0, char.sanity - loss)
                broadcastEvent("damage", char.name .. " rolls " .. roll .. " → loses " .. loss .. " Sanity.")
            end
        end
    end,
}

DAWN_EFFECTS["P2_FOOD_SPOILS"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Food goes bad. Each player discards 1 Food.")
        -- Resource discard is manual
    end,
}

DAWN_EFFECTS["P2_BASKETBALL_BOUNCE"] = {
    -- The Wrongness token (design_batch3.md §4): a deferred, face-down
    -- threat at the School. It does NOT resolve now — it resolves when a
    -- character enters the tile (checkWrongnessEntry) or at the next Dawn
    -- (BeginDay timeout), whichever comes first. Until then it just sits
    -- there, and the table argues about who goes to look.
    onReveal = function(card)
        broadcastEvent("warn", "A basketball bounces in the dark. Something is wrong at the School.")
        local deck = getThreatDeck()
        local qty = deck and (deck.getQuantity and deck.getQuantity() or 0) or 0
        if qty <= 0 then
            broadcastEvent("proc", "The threat deck is empty — the bouncing stops. Nothing comes of it.")
            return
        end
        local tile = getLocationTile("BasketballCourt")
        local pos = tile and (tile.getPosition() + Vector(2, 1.5, -2)) or Vector(0, 2, 0)
        deck.takeObject({
            position = pos,
            rotation = {0, 180, 180},   -- face-down: unresolved
            smooth = true,
            callback_function = function(tcard)
                gameState.wrongness = { location = "BasketballCourt", guid = tcard.guid,
                                        placedDay = gameState.day }
                broadcastEvent("warn", "An unresolved threat lies FACE-DOWN at the Basketball Court. Someone can go look — or it resolves at the next Dawn, where it stands.")
            end,
        })
    end,
}

-----------------------------------------------------------------------
-- The Wrongness (design_batch3.md §4) — shared resolver + entry check.
-- While pending, the face-down card does not fester (countFesteringThreats
-- skips its guid) — it is unresolved, not fled-from.
-----------------------------------------------------------------------
function resolveWrongness(trigger)
    local w = gameState.wrongness
    if not w then return end
    gameState.wrongness = nil
    local card = w.guid and getObjectFromGUID(w.guid)
    if not card then
        broadcastEvent("proc", "The wrongness at " .. (w.location or "?") .. " is gone — nothing was there after all.")
        return
    end
    safecall(function() card.setRotationSmooth({0, 180, 0}) end, "Wrongness")   -- flip face-up
    local tName = card.getNickname() or "Unknown Threat"
    if trigger == "entered" then
        broadcastEvent("warn", "You went to look. The wrongness at " .. (w.location or "?") .. " is: " .. tName .. "!")
    else
        broadcastEvent("warn", "Nobody went to look. At Dawn, the wrongness at " .. (w.location or "?") .. " reveals itself: " .. tName .. "!")
    end
    broadcastEvent("proc", card.getDescription() or "")
    local tType = identifyThreatType(card)
    if tType == "Soft" then
        broadcastEvent("proc", tName .. " is a soft threat — resolve it and discard.")
    else
        broadcastEvent("warn", tName .. " must be fought or fled. Left standing, it festers at Dawn.")
    end
end

-- Called after any location change (Move, bonus move, Dusk scramble, Flee).
function checkWrongnessEntry(color)
    local w = gameState.wrongness
    if not w then return end
    local char = gameState.activeChars[color]
    if char and not char.down and char.location == w.location then
        resolveWrongness("entered")
    end
end

DAWN_EFFECTS["P2_HUNGRY"] = {
    onReveal = function(card)
        allPlayersLose("hunger", 1)
        gameState.ongoingDawnEffects.restNoHunger = true
        broadcastEvent("warn", "ONGOING: Rest restores no Hunger until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.restNoHunger = nil
    end,
}

DAWN_EFFECTS["P2_DEERCLOPS_NEAR"] = {
    onReveal = function(card)
        broadcastEvent("warn", "WARNING: The Deerclops approaches! It arrives next Dawn at the Basketball Court.")
    end,
}

DAWN_EFFECTS["P2_DEERCLOPS_ARRIVES"] = {
    -- No arrival Doom: a boss charges the track by STAYING (+2 fester per
    -- Dawn, §15.1), not by showing up.
    onReveal = function(card)
        broadcastEvent("warn", "THE DEERCLOPS ARRIVES at the Basketball Court!")
        gameState.ongoingDawnEffects.deerclopsActive = true
        gameState.bossHP = gameState.bossHP or {}
        gameState.bossHP.deerclops = BOSS_BASE_STATS["Boss:Deerclops"].hp
        safecall(function() placeBossStandee("Deerclops", "BasketballCourt") end, "BossPlace")
        broadcastEvent("warn", "ONGOING: While Deerclops is on the map, all Sanity costs are doubled. It festers Doom +2 each Dawn it stands.")
        broadcastEvent("proc", "Deerclops: HP " .. gameState.bossHP.deerclops .. ", Atk " ..
            BOSS_BASE_STATS["Boss:Deerclops"].attack .. " — Fight it at its tile; the script tracks its HP.")
        safecall(function() nudgeCameraToBoss("Deerclops", "BasketballCourt") end, "CameraNudge")
        safecall(function() Audio.playBossLoop("deerclops") end, "Audio")
    end,
    onCleanup = function()
        -- Deerclops stays until defeated; cleanup only removes if defeated flag set
        if gameState.ongoingDawnEffects.deerclopsDefeated then
            gameState.ongoingDawnEffects.deerclopsActive = nil
            gameState.ongoingDawnEffects.deerclopsDefeated = nil
            safecall(function() Audio.stopBossLoop("deerclops") end, "Audio")
        end
    end,
}

DAWN_EFFECTS["P2_DOOR_OPENS"] = {
    onReveal = function(card)
        for color, char in pairs(gameState.activeChars) do
            if not char.down and char.location == "EllieLucaHouse" then
                char.sanity = math.max(0, char.sanity - 2)
                broadcastEvent("damage", char.name .. " at Ellie & Luca's House loses 2 Sanity — a door opened by itself.")
            end
        end
    end,
}

DAWN_EFFECTS["P2_VISITOR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An old friend drops by. Resolve the top Visitor card.")
        local vDeck = getVisitorDeck()
        if vDeck and vDeck.getQuantity and vDeck.getQuantity() > 0 then
            vDeck.takeObject({
                position = vDeck.getPosition() + Vector(3, 1, 0),
                rotation = {0, 180, 0},
                smooth   = true,
                callback_function = function(vCard)
                    local vName = vCard.getNickname() or "Visitor"
                    broadcastEvent("proc", "VISITOR: " .. vName .. " — read the card for instructions.")
                end
            })
        else
            broadcastEvent("proc", "No visitor cards remaining.")
        end
    end,
}

DAWN_EFFECTS["P2_BLOOD_MOON"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.bloodMoon = true
        broadcastEvent("warn", "ONGOING: Blood Moon — threat draws +1 at all locations tonight.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.bloodMoon = nil
    end,
}

DAWN_EFFECTS["P2_WALLS_BLEED"] = {
    onReveal = function(card)
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local loc = char.location or ""
                if loc:find("House") then
                    char.sanity = math.max(0, char.sanity - 2)
                    broadcastEvent("damage", char.name .. " at a house tile loses 2 Sanity — the walls are bleeding.")
                end
            end
        end
    end,
}

DAWN_EFFECTS["P2_SUPPLY_DROP"] = {
    onReveal = function(card)
        -- The box lands on the neighbourhood's central porch: Ellie & Luca's
        -- House. 1 Metal + 1 Cloth spill out, and the noise draws 1 Threat.
        broadcastEvent("gain", "A box on Ellie & Luca's porch! 1 Metal + 1 Cloth appear there.")
        safecall(function()
            spawnResourceAtTile("EllieLucaHouse", "Metal", 1)
            spawnResourceAtTile("EllieLucaHouse", "Cloth", 1)
        end, "SupplyDrop")
        broadcastEvent("warn", "The clatter draws 1 Threat to Ellie & Luca's House.")
        safecall(function() drawThreatsAt("EllieLucaHouse", 1) end, "SupplyDropThreat")
    end,
}

DAWN_EFFECTS["P2_MIRROR_CRACK"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Every mirror cracked. All players discard 1 Battery (if held).")
        -- Find player with most items for the Sanity loss
        local most, target = -1, nil
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local count = char.itemCount or 0
                if count > most then
                    most = count
                    target = char
                end
            end
        end
        if target then
            target.sanity = math.max(0, target.sanity - 1)
            broadcastEvent("damage", target.name .. " (most items) loses 1 Sanity.")
        end
    end,
}

DAWN_EFFECTS["P2_STRANGER_WAVES"] = {
    onReveal = function(card)
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local loc = char.location or ""
                if loc:find("Court") or loc:find("Badminton") or loc:find("Basketball") then
                    char.sanity = math.max(0, char.sanity - 2)
                    broadcastEvent("damage", char.name .. " at a sport court loses 2 Sanity.")
                end
            end
        end
        gameState.ongoingDawnEffects.sportCourtHungerCost = true
        broadcastEvent("warn", "ONGOING: Movement to or from sport courts costs +1 Hunger until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.sportCourtHungerCost = nil
    end,
}

DAWN_EFFECTS["P2_RAIN_STARTS"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.rainSanityCost = true
        gameState.ongoingDawnEffects.rainFireDisabled = true
        broadcastEvent("warn", "The rain starts. Gather at sport courts costs +1 Sanity this day.")
        broadcastEvent("warn", "ONGOING: Fire light sources extinguished at sport courts until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.rainSanityCost = nil
        gameState.ongoingDawnEffects.rainFireDisabled = nil
    end,
}

