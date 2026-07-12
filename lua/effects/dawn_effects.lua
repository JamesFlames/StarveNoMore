-- dawn_effects.lua  (F.5 — Dawn-card effect dispatch table)
-- Each entry maps a card ID to { onReveal(card), onCleanup() }.
-- onReveal fires when the card is drawn; onCleanup fires at the next Dawn.

DAWN_EFFECTS = {}

-----------------------------------------------------------------------
-- Helper: apply stat change to all active (non-down) characters
-----------------------------------------------------------------------
local function allPlayersLose(stat, amount)
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char[stat] = math.max(0, char[stat] - amount)
            broadcastEvent("damage", char.name .. " loses " .. amount .. " " .. stat .. ".")
        end
    end
end

local function allPlayersGain(stat, amount)
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char[stat] = math.min(char["max" .. stat:sub(1,1):upper() .. stat:sub(2)], char[stat] + amount)
            broadcastEvent("gain", char.name .. " gains " .. amount .. " " .. stat .. ".")
        end
    end
end

local function lowestStatPlayer(stat)
    local lowest, lowestChar = 999, nil
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char[stat] < lowest then
            lowest = char[stat]
            lowestChar = char
        end
    end
    return lowestChar
end

-----------------------------------------------------------------------
-- Phase 1: Dusk of the Week
-----------------------------------------------------------------------
DAWN_EFFECTS["P1_QUIET_EVENING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A quiet evening. No effect.")
    end,
}

DAWN_EFFECTS["P1_LIGHTS_FLICKER"] = {
    -- Dare (design_batch3.md §2): the court floodlights are on all night.
    -- Opt in by sleeping at a court: +2 Threats there, 2 Market cards at Dawn
    -- for survivors (paid out beside Moonlit Salvage in BeginDay).
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.dareCourtGlow = true
        broadcastEvent("warn", "DARE: the court floodlights glow all night. Sleep at a sport court — it draws +2 extra Threats, but survivors claim 2 Market cards at Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.dareCourtGlow = nil
    end,
}

DAWN_EFFECTS["P1_PHONES_DEAD"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Phones are dead. All players discard 1 Battery (if held).")
        -- Resource discard is manual in this phase; broadcast the instruction
    end,
}

DAWN_EFFECTS["P1_SOMETHING_WATCHED"] = {
    onReveal = function(card)
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.max(0, target.sanity - 1)
            broadcastEvent("damage", target.name .. " (lowest Sanity) loses 1 more Sanity.")
        end
    end,
}

DAWN_EFFECTS["P1_FRESH_FOOD"] = {
    onReveal = function(card)
        broadcastEvent("gain", "2 Food added to Ellie & Luca's House resource bag.")
        -- Physical token spawn would be handled by a resource-bag helper in Phase G
    end,
}

DAWN_EFFECTS["P1_NEIGHBORHOOD_QUIET"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.noHouseThreats = true
        broadcastEvent("proc", "No threats spawn at house tiles tonight. Charlie checks ignore the Basketball Court until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.noHouseThreats = nil
    end,
}

DAWN_EFFECTS["P1_SCHOOL_CLOSED"] = {
    onReveal = function(card)
        broadcastEvent("proc", "School is closed! Move all standees at the Basketball Court to an adjacent tile.")
        -- Physical movement is manual; broadcast instruction
    end,
}

DAWN_EFFECTS["P1_OLD_FRIEND_VISIT"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An old friend calls. Choose one player — they gain +2 Sanity.")
        -- Player choice is manual
    end,
}

DAWN_EFFECTS["P1_BREEZE"] = {
    onReveal = function(card)
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local loc = char.location or ""
                if loc:find("Court") or loc:find("Badminton") or loc:find("Basketball") then
                    char.hunger = math.max(0, char.hunger - 1)
                    broadcastEvent("damage", char.name .. " at a sport court loses 1 Hunger from the breeze.")
                end
            end
        end
    end,
}

DAWN_EFFECTS["P1_STRAY_CAT"] = {
    onReveal = function(card)
        local highest, target = -1, nil
        for color, char in pairs(gameState.activeChars) do
            if not char.down and char.sanity > highest then
                highest = char.sanity
                target = char
            end
        end
        if target then
            gameState.ongoingDawnEffects.strayCat = target.name
            broadcastEvent("gain", "A stray cat follows " .. target.name .. " (+1 Sanity at Tick while it stays).")
            broadcastEvent("proc", "If " .. target.name .. " takes damage, the cat flees.")
        end
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.strayCat = nil
    end,
}

DAWN_EFFECTS["P1_BIKE_FOUND"] = {
    onReveal = function(card)
        broadcastEvent("gain", "Someone left a bicycle! One player at a sport court may take the Bicycle token (Move costs 0 Hunger).")
    end,
}

DAWN_EFFECTS["P1_GARDEN_GROWS"] = {
    onReveal = function(card)
        broadcastEvent("gain", "The garden still grows. Add 1 Food to every house tile's resource area.")
    end,
}

DAWN_EFFECTS["P1_STRANGE_RADIO"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A strange radio signal. All players roll d6.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 6)
                if roll == 6 then
                    broadcastEvent("gain", char.name .. " rolls 6 — peek at Market deck for a Clue card!")
                elseif roll == 1 then
                    char.sanity = math.max(0, char.sanity - 1)
                    broadcastEvent("damage", char.name .. " rolls 1 — loses 1 Sanity.")
                else
                    broadcastEvent("proc", char.name .. " rolls " .. roll .. " — no effect.")
                end
            end
        end
    end,
}

DAWN_EFFECTS["P1_PHOTO_FOUND"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An old photograph. Choose one player — they gain +1 Sanity and may peek at the top Threat card.")
    end,
}

DAWN_EFFECTS["P1_RUMOR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A rumor on the street. Reveal the next Dawn card, then place it back on top.")
        local phase = gameState.phase
        local deck = getPhaseDeck(phase)
        if deck and deck.getQuantity and deck.getQuantity() > 0 then
            deck.takeObject({
                position = deck.getPosition() + Vector(5, 2, 0),
                rotation = {0, 180, 0},
                smooth   = true,
                callback_function = function(peeked)
                    local name = peeked.getNickname() or "???"
                    broadcastEvent("proc", "Peeked: " .. name .. ". Returning to top of deck.")
                    Wait.time(function()
                        deck.putObject(peeked)
                    end, 3.0)
                end
            })
        end
    end,
}

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
        broadcastEvent("warn", "ONGOING: While Deerclops is on the map, all Sanity costs are doubled. It festers Doom +2 each Dawn it stands.")
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
        broadcastEvent("gain", "A box on the porch! Add 1 Metal and 1 Cloth to the nearest house tile.")
        broadcastEvent("warn", "Also draw 1 Threat at that house tile.")
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

-----------------------------------------------------------------------
-- Phase 3: Long Nights
-----------------------------------------------------------------------
DAWN_EFFECTS["P3_LONG_NIGHT"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 2)
        gameState.doom = gameState.doom + 1
        moveDoomMarker(gameState.doom)
        gameState.ongoingDawnEffects.reducedActions = true
        broadcastEvent("warn", "Doom +1. ONGOING: Day phase has only 2 actions per player.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.reducedActions = nil
    end,
}

DAWN_EFFECTS["P3_EYE_NEAR"] = {
    onReveal = function(card)
        broadcastEvent("warn", "WARNING: The Eye of Terror approaches! It arrives next Dawn at a random house tile.")
    end,
}

DAWN_EFFECTS["P3_EYE_ARRIVES"] = {
    -- No arrival Doom — festering (+2/Dawn) is the boss's bill.
    onReveal = function(card)
        broadcastEvent("warn", "THE EYE OF TERROR ARRIVES!")
        gameState.ongoingDawnEffects.eyeActive = true
        broadcastEvent("warn", "ONGOING: Each Dawn, draw 1 extra Threat at the Eye's location. It festers Doom +2 each Dawn it stands.")
        safecall(function() nudgeCameraToBoss("EyeOfTerror", "EllieLucaHouse") end, "CameraNudge")
        safecall(function() Audio.playBossLoop("eye_of_terror") end, "Audio")
    end,
    onCleanup = function()
        if gameState.ongoingDawnEffects.eyeDefeated then
            gameState.ongoingDawnEffects.eyeActive = nil
            gameState.ongoingDawnEffects.eyeDefeated = nil
            safecall(function() Audio.stopBossLoop("eye_of_terror") end, "Audio")
        end
    end,
}

DAWN_EFFECTS["P3_EYE_SPLITS"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The Eye of Terror SPLITS into 3 Terror Beaks at adjacent tiles!")
        gameState.ongoingDawnEffects.eyeActive = nil
        -- Terror Beaks are threat cards; manual placement
    end,
}

DAWN_EFFECTS["P3_HUNGER_PANG"] = {
    onReveal = function(card)
        allPlayersLose("hunger", 2)
    end,
}

DAWN_EFFECTS["P3_SCREAMS"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        local target = lowestStatPlayer("sanity")
        if target then
            target.sanity = math.max(0, target.sanity - 2)
            broadcastEvent("damage", target.name .. " (lowest Sanity) loses 2 more Sanity from screams.")
        end
    end,
}

DAWN_EFFECTS["P3_POWER_OUT"] = {
    onReveal = function(card)
        broadcastEvent("warn", "Power goes out! All Battery tokens returned to supply.")
        gameState.ongoingDawnEffects.charlieEverywhere = true
        broadcastEvent("warn", "ONGOING: Charlie checks affect every location tonight.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.charlieEverywhere = nil
    end,
}

DAWN_EFFECTS["P3_FRIEND_CHANGED"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Your friend looks wrong. The player to your left loses 2 Sanity and reveals one Item.")
        -- Manual resolution; the "left" direction depends on seating
    end,
}

DAWN_EFFECTS["P3_TRUTH_GLIMPSE"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A glimpse of the truth. Search the Market deck for a Clue card and reveal it face-up.")
        broadcastEvent("warn", "If found, the Clue cannot be claimed until Day 6.")
    end,
}

DAWN_EFFECTS["P3_LULL"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The calm before... No immediate effect.")
        gameState.ongoingDawnEffects.charliePaused = true
        broadcastEvent("gain", "ONGOING: All Charlie checks are paused until next Dawn. Gather while you can!")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.charliePaused = nil
    end,
}

DAWN_EFFECTS["P3_GRAVITY_WRONG"] = {
    onReveal = function(card)
        allPlayersLose("health", 1)
        gameState.ongoingDawnEffects.moveCostPlus1 = true
        gameState.ongoingDawnEffects.restNoHealth = true
        broadcastEvent("warn", "Gravity feels wrong. Movement costs +1 action this day.")
        broadcastEvent("warn", "ONGOING: Rest restores no Health until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.moveCostPlus1 = nil
        gameState.ongoingDawnEffects.restNoHealth = nil
    end,
}

DAWN_EFFECTS["P3_TIME_SKIP"] = {
    onReveal = function(card)
        gameState.day = math.min(getTotalDays(), gameState.day + 1)
        gameState.doom = gameState.doom + 1
        moveDoomMarker(gameState.doom)
        allPlayersLose("hunger", 1)
        broadcastEvent("warn", "You lost a day! Day counter advances by 1. Doom +1. All players lose 1 Hunger.")
    end,
}

DAWN_EFFECTS["P3_WALLS_CLOSE"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.reducedCapacity = true
        broadcastEvent("warn", "The walls are closer. Each house tile loses 1 character capacity (max 4).")
        broadcastEvent("proc", "Excess players must move at Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.reducedCapacity = nil
    end,
}

DAWN_EFFECTS["P3_ALLY_MISSING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "One of you was gone this morning. The player with the fewest items loses all items and reappears at a random tile.")
        gameState.ongoingDawnEffects.missingAllyBonus = true
        broadcastEvent("gain", "ONGOING: That player gets +1 action this day (adrenaline).")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.missingAllyBonus = nil
    end,
}

DAWN_EFFECTS["P3_OFFERING"] = {
    onReveal = function(card)
        broadcastEvent("proc", "An offering at the door. CHOOSE: Sacrifice 3 Food to reduce Doom by 2, OR ignore it and all players lose 1 Sanity.")
        -- Manual resolution — players decide together
    end,
}

-----------------------------------------------------------------------
-- Phase 4: Final Hours
-----------------------------------------------------------------------
DAWN_EFFECTS["P4_FINAL_HOURS"] = {
    -- (An earlier draft claimed "ONGOING: Doom rate is now +3 per day" but
    -- never implemented it, and a flat +3 would trample the per-player-count
    -- rates in Design §15.6. The card is now its immediate effect only.)
    onReveal = function(card)
        allPlayersLose("sanity", 2)
        gameState.doom = gameState.doom + 2
        moveDoomMarker(gameState.doom)
        broadcastEvent("warn", "The final hours begin. All players lose 2 Sanity. Doom +2.")
    end,
}

DAWN_EFFECTS["P4_SOURCE_NEAR"] = {
    onReveal = function(card)
        broadcastEvent("warn", "WARNING: Something worse approaches. The Source arrives next Dawn.")
    end,
}

DAWN_EFFECTS["P4_SOURCE_ARRIVES"] = {
    -- No arrival Doom — festering (+2/Dawn) is the boss's bill.
    onReveal = function(card)
        broadcastEvent("warn", "THE SOURCE ARRIVES at the center of the map!")
        gameState.ongoingDawnEffects.sourceActive = true
        -- Persistent boss HP (§12.6): the script tracks the Source's HP from
        -- here on — and at 5 HP it splits (checkSourcePhase, combat.lua).
        gameState.bossHP = gameState.bossHP or {}
        gameState.bossHP.source = SOURCE_MAX_HP or 8
        gameState.sourceSplit = false
        broadcastEvent("warn", "ONGOING: The Source is the final boss. It MUST be destroyed before Day 7 ends — while it stands, there is no victory.")
        broadcastEvent("proc", "The Source: HP " .. gameState.bossHP.source ..
            " (script-tracked). At 5 HP it will SPLIT — two Terror Beaks peel off to adjacent tiles.")
        safecall(function() nudgeCameraToBoss("TheSource", "EllieLucaHouse") end, "CameraNudge")
        -- No audio folder for "the_source" yet — Audio.playBossLoop no-ops
        -- when CREATURES[name] is missing, so ambient continues normally.
        safecall(function() Audio.playBossLoop("the_source") end, "Audio")
    end,
}

DAWN_EFFECTS["P4_DESPAIR"] = {
    onReveal = function(card)
        broadcastEvent("proc", "Despair. Each player rolls Sanity d8, loses half (round up).")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 8)
                local loss = math.ceil(roll / 2)
                char.sanity = math.max(0, char.sanity - loss)
                broadcastEvent("damage", char.name .. " rolls " .. roll .. " → loses " .. loss .. " Sanity.")
            end
        end
        gameState.ongoingDawnEffects.restNoSanity = true
        broadcastEvent("warn", "ONGOING: Rest restores no Sanity until next Dawn.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.restNoSanity = nil
    end,
}

DAWN_EFFECTS["P4_SACRIFICE_OPTION"] = {
    onReveal = function(card)
        broadcastEvent("proc", "A WAY OUT: Any one player may immediately become Down to reduce Doom by 5. (Optional.)")
        -- Manual resolution
    end,
}

DAWN_EFFECTS["P4_LAST_LIGHTS"] = {
    onReveal = function(card)
        allPlayersLose("sanity", 1)
        gameState.ongoingDawnEffects.onlyFireLight = true
        broadcastEvent("warn", "ONGOING: Only Fire is a light source until next Dawn. Batteries/Flashlights disabled.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.onlyFireLight = nil
    end,
}

DAWN_EFFECTS["P4_HOPE_REMAINS"] = {
    onReveal = function(card)
        allPlayersGain("sanity", 1)
        gameState.ongoingDawnEffects.doomReduced = true
        broadcastEvent("gain", "Hope remains. Doom advance reduced by 1 this Dawn only.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.doomReduced = nil
    end,
}

DAWN_EFFECTS["P4_THE_TRUTH"] = {
    onReveal = function(card)
        -- Check if the team has all 3 Clue cards
        local clueCount = gameState.clueCount or 0
        if clueCount >= 3 then
            broadcastEvent("gain", "The team has all 3 Clues! The Truth Trophy flips face-up on the trophy row.")
            local trophy = findOneByTag("TR_TRUTH")
            if trophy then
                trophy.setRotationSmooth({0, 180, 0}, false, true)  -- face up
                trophy.highlightOn("Yellow", 10)
            end
        else
            allPlayersLose("sanity", 2)
            broadcastEvent("damage", "The truth is worse than you imagined. Missing Clues — all lose 2 Sanity.")
        end
    end,
}

DAWN_EFFECTS["P4_ALL_TOGETHER"] = {
    onReveal = function(card)
        broadcastEvent("proc", "All Together. Move all standees to the same tile (player vote).")
        gameState.ongoingDawnEffects.togetherBonus = true
        broadcastEvent("gain", "ONGOING: All players gain +1 Sanity at Tick if sharing a tile with another player.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.togetherBonus = nil
    end,
}

DAWN_EFFECTS["P4_DAWN_BREAKS"] = {
    onReveal = function(card)
        broadcastEvent("gain", "Dawn breaks. Doom does NOT advance this Dawn.")
        gameState.ongoingDawnEffects.noDoomThisDawn = true
        if gameState.day == getTotalDays() then
            broadcastEvent("phase", "The final day — continue to the final Tick. Survival check!")
        end
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.noDoomThisDawn = nil
    end,
}

DAWN_EFFECTS["P4_GROUND_SPLITS"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The ground splits open! A random location tile is destroyed. Players there must flee. Resources there are lost.")
        -- Manual resolution: pick random tile, remove it, relocate players
    end,
}

DAWN_EFFECTS["P4_LAST_MEAL"] = {
    onReveal = function(card)
        broadcastEvent("warn", "The last meal. All Food at every location is destroyed.")
        gameState.ongoingDawnEffects.recipeBonusHunger = true
        broadcastEvent("gain", "Recipes cooked today restore +2 extra Hunger.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.recipeBonusHunger = nil
    end,
}

DAWN_EFFECTS["P4_VOICES_RETURN"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The voices come back. Every player rolls Sanity d8.")
        for color, char in pairs(gameState.activeChars) do
            if not char.down then
                local roll = gameRoll(1, 8)
                -- Check if an ally is at the same tile
                local hasAlly = false
                for c2, ch2 in pairs(gameState.activeChars) do
                    if c2 ~= color and not ch2.down and ch2.location == char.location then
                        hasAlly = true
                        break
                    end
                end
                local loss = roll
                if hasAlly then
                    loss = math.floor(roll / 2)
                    broadcastEvent("damage", char.name .. " rolls " .. roll .. " (halved with ally) -> loses " .. loss .. " Sanity.")
                else
                    broadcastEvent("damage", char.name .. " rolls " .. roll .. " -> loses " .. loss .. " Sanity.")
                end
                char.sanity = math.max(0, char.sanity - loss)
            end
        end
    end,
}

DAWN_EFFECTS["P4_BARGAIN"] = {
    onReveal = function(card)
        broadcastEvent("proc", "The Source offers a bargain. Choose one player to negotiate.")
        broadcastEvent("warn", "That player rolls d6: on 4+ Doom -3. On 1-3: that player goes Down immediately.")
        -- Manual resolution
    end,
}

DAWN_EFFECTS["P4_MEMORY_FLOOD"] = {
    onReveal = function(card)
        allPlayersGain("sanity", 2)
        allPlayersLose("health", 1)
        broadcastEvent("proc", "A flood of memories. +2 Sanity, -1 Health. The memories are sharp.")
        gameState.ongoingDawnEffects.homeSanityBonus = true
        broadcastEvent("gain", "ONGOING: Players at their own home gain +2 Sanity at sleep instead of +1.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.homeSanityBonus = nil
    end,
}

-----------------------------------------------------------------------
-- Anti-stacking Dawn cards: the thing outside notices crowds.
-----------------------------------------------------------------------
local function mostPopulatedLocations()
    local pops = {}
    local maxPop = 0
    for _, char in pairs(gameState.activeChars) do
        if not char.down and char.location then
            pops[char.location] = (pops[char.location] or 0) + 1
            if pops[char.location] > maxPop then maxPop = pops[char.location] end
        end
    end
    local locs = {}
    for loc, n in pairs(pops) do
        if n == maxPop and maxPop >= 2 then table.insert(locs, loc) end
    end
    return locs, maxPop
end

DAWN_EFFECTS["P2_DRAWN_TO_CROWDS"] = {
    onReveal = function(card)
        gameState.ongoingDawnEffects.crowdThreat = true
        broadcastEvent("warn", "ONGOING: Tonight, the most-populated location draws +1 Threat. It has learned where you gather.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.crowdThreat = nil
    end,
}

DAWN_EFFECTS["P3_HUNTS_THE_HERD"] = {
    onReveal = function(card)
        local locs = mostPopulatedLocations()
        if #locs == 0 then
            broadcastEvent("proc", "Everyone is scattered — it circles, finding no herd. No effect.")
        else
            for _, loc in ipairs(locs) do
                for _, char in pairs(gameState.activeChars) do
                    if not char.down and char.location == loc then
                        char.sanity = math.max(0, char.sanity - 1)
                        broadcastEvent("damage", char.name .. " feels watched at " .. loc .. " — loses 1 Sanity.")
                    end
                end
            end
        end
        gameState.ongoingDawnEffects.crowdThreat = true
        broadcastEvent("warn", "ONGOING: Tonight, the most-populated location draws +1 Threat.")
    end,
    onCleanup = function()
        gameState.ongoingDawnEffects.crowdThreat = nil
    end,
}

-----------------------------------------------------------------------
-- Manual steps per Dawn card — things the script cannot do for the
-- players (physical token moves, group choices, deck searches). These
-- feed the tickable Dawn checklist panel (ui_rules.lua) so instructions
-- don't just scroll away in chat. Cards absent here are fully scripted.
-----------------------------------------------------------------------
DAWN_MANUAL_STEPS = {
    P1_PHONES_DEAD      = { "Every player discards 1 Battery (if held)." },
    P1_FRESH_FOOD       = { "Add 2 Food to Ellie & Luca's House resource bag." },
    P1_SCHOOL_CLOSED    = { "Move every standee at the Basketball Court to an adjacent tile." },
    P1_OLD_FRIEND_VISIT = { "Choose one player: +2 Sanity (use their +S button)." },
    P1_BIKE_FOUND       = { "One player at a sport court may take the Bicycle token." },
    P1_GARDEN_GROWS     = { "Add 1 Food to every house tile's resource area." },
    P1_SOMETHING_WATCHED = { "Optional DARE: the watched player may lose 1 more Sanity (-S button) to peek at the top Threat card." },
    P1_STRANGE_RADIO    = { "Anyone who rolled a 6: peek at the Market deck for a Clue.",
                            "Optional DARE: spend 2 Battery to peek the next 3 Dawn cards (host: draw + show + return in order)." },
    P1_PHOTO_FOUND      = { "Choose one player: +1 Sanity and peek at the top Threat card." },
    P2_FOOD_SPOILS      = { "Every player discards 1 Food.",
                            "Optional DARE: eat it anyway — announce it: +2 Hunger and -1 Health instead of discarding." },
    P2_VISITOR          = { "Resolve the revealed Visitor card's instructions." },
    P2_SUPPLY_DROP      = { "Add 1 Metal + 1 Cloth to the nearest house tile.",
                            "Draw 1 Threat at that house tile." },
    P2_MIRROR_CRACK     = { "Every player discards 1 Battery (if held)." },
    P3_POWER_OUT        = { "Return all Battery tokens to the supply." },
    P3_FRIEND_CHANGED   = { "Player to your left: -2 Sanity and reveals one Item." },
    P3_TRUTH_GLIMPSE    = { "Search the Market deck for a Clue card; reveal it face-up (claimable Day 6+)." },
    P3_WALLS_CLOSE      = { "If a house holds more than its capacity, excess players move now." },
    P3_ALLY_MISSING     = { "Player with fewest items: discard all items, move their standee to a random tile." },
    P3_OFFERING         = { "Team choice: sacrifice 3 Food for Doom -2, OR everyone loses 1 Sanity." },
    P3_EYE_SPLITS       = { "Place 3 Terror Beak threat cards at tiles adjacent to the Eye." },
    P4_SACRIFICE_OPTION = { "Optional: one player may go Down to reduce Doom by 5." },
    P4_GROUND_SPLITS    = { "Destroy a random location tile; players there flee; its resources are lost." },
    P4_LAST_MEAL        = { "Remove all Food tokens from every location." },
    P4_ALL_TOGETHER     = { "Vote on a tile; move all standees there." },
    P4_BARGAIN          = { "Choose a negotiator: roll d6 — 4+: Doom -3; 1-3: they go Down." },
}

-----------------------------------------------------------------------
-- Dispatch entry point (called from day_loop.lua -> revealDawnCard)
-----------------------------------------------------------------------
function dispatchDawnEffect(card)
    -- Clean up previous Dawn's ongoing effects
    if gameState.activeDawn and gameState.activeDawn.prevId then
        local prev = DAWN_EFFECTS[gameState.activeDawn.prevId]
        if prev and prev.onCleanup then
            safecall(function() prev.onCleanup() end, "DawnCleanup:" .. gameState.activeDawn.prevId)
        end
    end

    -- Resolve the card's effect ID. Cards are tagged with their CSV id
    -- (e.g. "P1_QUIET_EVENING") by build_save.py; the nickname holds the
    -- display title, so check tags first and fall back to the nickname.
    local id = nil
    if card.getTags then
        for _, tag in ipairs(card.getTags()) do
            if DAWN_EFFECTS[tag] then id = tag; break end
        end
    end
    if not id then
        id = (card.getNickname() or ""):match("^%s*(.-)%s*$") or ""
    end

    local handler = DAWN_EFFECTS[id]
    if handler and handler.onReveal then
        safecall(function() handler.onReveal(card) end, "DawnEffect:" .. id)
    else
        broadcastEvent("proc", "No scripted effect for Dawn card: " .. id)
    end

    -- Populate the tickable manual-steps checklist (ui_rules.lua panel).
    gameState.dawnChecklist = {}
    for _, step in ipairs(DAWN_MANUAL_STEPS[id] or {}) do
        table.insert(gameState.dawnChecklist, { text = step, done = false })
    end
    if #gameState.dawnChecklist > 0 then
        broadcastEvent("warn", "This Dawn card needs " .. #gameState.dawnChecklist ..
            " manual step(s) — see the checklist panel (top right). Tick each when done.")
    end
    safecall(function() refreshDawnChecklist() end, "DawnChecklist")

    -- Track for next-dawn cleanup
    if gameState.activeDawn then
        gameState.activeDawn.prevId = id
    end
end
