-- night.lua  (F.9 — Night-phase resolver)
-- Design §11.4: For each location with players (least populated first):
--   1. Threat draw
--   2. Resolve threats (combat)
--   3. Charlie check (no light = d8 Sanity + d6 Health)
--   4. Storytelling (Comfort/Music items for Sanity)
--   5. Sleep regen

-----------------------------------------------------------------------
-- Location threat rates
-----------------------------------------------------------------------
LOCATION_THREAT_RATE = {
    JamesHouse       = 0,
    RaymanHouse      = 0,
    EllieLucaHouse   = 0,
    BasketballCourt  = 1,
    BadmintonCourt   = 1,
}

-----------------------------------------------------------------------
-- Main Night resolver (called from day_loop.lua → beginNight)
-----------------------------------------------------------------------
function ResolveNight()
    broadcastEvent("phase", "--- NIGHT PHASE ---")

    -- Build a list of occupied locations sorted by population (ascending)
    local locPop = {}  -- { location = { colors... } }
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local loc = char.location or "Unknown"
            locPop[loc] = locPop[loc] or {}
            table.insert(locPop[loc], color)
        end
    end

    -- Sort locations by population count ascending
    local sortedLocs = {}
    for loc, colors in pairs(locPop) do
        table.insert(sortedLocs, { location = loc, colors = colors, count = #colors })
    end
    table.sort(sortedLocs, function(a, b) return a.count < b.count end)

    -- Process each location sequentially with delays
    local delay = 0
    for i, entry in ipairs(sortedLocs) do
        Wait.time(function()
            resolveNightAtLocation(entry.location, entry.colors)
        end, delay)
        delay = delay + 4.0  -- 4 seconds between locations
    end

    -- After all locations resolved, proceed to storytelling + sleep + tick
    Wait.time(function()
        resolveStorytelling()
    end, delay + 1.0)

    Wait.time(function()
        resolveSleep()
    end, delay + 3.0)

    Wait.time(function()
        -- Clear barricades (single-use per night)
        gameState.barricades = {}
        resolveTick()
    end, delay + 5.0)
end

-----------------------------------------------------------------------
-- Resolve threats at one location
-----------------------------------------------------------------------
function resolveNightAtLocation(location, colors)
    local charNames = {}
    for _, c in ipairs(colors) do
        local ch = gameState.activeChars[c]
        if ch then table.insert(charNames, ch.name) end
    end

    broadcastEvent("phase", "Night at " .. location .. " (" .. table.concat(charNames, ", ") .. ")")

    -- 1. Threat draw
    local baseRate = LOCATION_THREAT_RATE[location] or 0

    -- Doom 10 threshold: +1 threat at all locations
    if gameState.ongoingDawnEffects.doom10 then
        baseRate = baseRate + 1
    end

    -- Blood Moon: +1 threat at all locations
    if gameState.ongoingDawnEffects.bloodMoon then
        baseRate = baseRate + 1
    end

    -- Alone at a sport court: +1 extra threat
    if #colors == 1 and (location:find("Court") or location:find("Badminton") or location:find("Basketball")) then
        baseRate = baseRate + 1
        broadcastEvent("warn", charNames[1] .. " is alone at " .. location .. "! Extra threat drawn.")
    end

    -- Barricade reduces threat draws
    local barricades = (gameState.barricades or {})[location] or 0
    if barricades > 0 then
        baseRate = math.max(0, baseRate - barricades)
        broadcastEvent("gain", "Barricade at " .. location .. " absorbs " .. barricades .. " threat draw(s)!")
    end

    -- Shortcut scenario: +1 threat at connected locations
    local flags = gameState.scenarioFlags or {}
    if flags.shortcutThreatBonus and (location == "JamesHouse" or location == "BadmintonCourt") then
        baseRate = baseRate + 1
        broadcastEvent("warn", "The Shortcut draws attention — +1 Threat at " .. location .. ".")
    end

    -- No house threats (P1_NEIGHBORHOOD_QUIET)
    if gameState.ongoingDawnEffects.noHouseThreats then
        if not (location:find("Court") or location:find("Badminton") or location:find("Basketball")) then
            baseRate = 0
            broadcastEvent("proc", "No threats at " .. location .. " tonight (Neighborhood quiet).")
        end
    end

    if baseRate > 0 then
        broadcastEvent("proc", "Drawing " .. baseRate .. " threat(s) at " .. location .. "...")
        local threatDeck = getThreatDeck()
        if threatDeck then
            for t = 1, baseRate do
                local qty = threatDeck.getQuantity and threatDeck.getQuantity() or 0
                if qty > 0 then
                    local tile = getLocationTile(location)
                    local targetPos = tile and (tile.getPosition() + Vector(2, 1, t * 0.3)) or Vector(0, 2, 0)
                    threatDeck.takeObject({
                        position = targetPos,
                        rotation = {0, 180, 0},
                        smooth   = true,
                        callback_function = function(threatCard)
                            local tName = threatCard.getNickname() or "Unknown Threat"
                            local tDesc = threatCard.getDescription() or ""
                            broadcastEvent("warn", "THREAT at " .. location .. ": " .. tName)
                            broadcastEvent("proc", tDesc)

                            -- Auto-resolve soft threats (HP = 0)
                            local tType = identifyThreatType(threatCard)
                            if tType == "Soft" then
                                broadcastEvent("proc", tName .. " is a soft threat — resolves and discards.")
                            else
                                broadcastEvent("warn", tName .. " must be fought or fled! Players at " .. location .. " must deal with it.")
                            end
                        end
                    })
                else
                    broadcastEvent("proc", "Threat deck is empty.")
                    break
                end
            end
        end
    else
        broadcastEvent("proc", "No threats drawn at " .. location .. ".")
    end

    -- 3. Charlie check
    -- Spring scenario: no Charlie days 1-3, Charlie everywhere day 4+
    local flags = gameState.scenarioFlags or {}
    if flags.falseSpring then
        if gameState.day <= 3 then
            gameState.ongoingDawnEffects.charliePaused = true
        else
            gameState.ongoingDawnEffects.charliePaused = false
            gameState.ongoingDawnEffects.charlieEverywhere = true
        end
    end

    if not gameState.ongoingDawnEffects.charliePaused then
        local charlieApplies = gameState.ongoingDawnEffects.charlieEverywhere or
            (location:find("Court") or location:find("Badminton") or location:find("Basketball"))

        -- At house tiles, Charlie only hits if there's no light source
        -- For now, we broadcast the check and let players confirm light sources
        if charlieApplies or baseRate > 0 then
            for _, c in ipairs(colors) do
                local ch = gameState.activeChars[c]
                if ch and not ch.down then
                    -- Check for light sources: player must have Flashlight, Lantern, Fire, etc.
                    -- In scripted mode, we check if flashlights are disabled
                    local hasLight = checkPlayerHasLight(c)
                    if not hasLight then
                        resolveCharlieAttack(c)
                    else
                        broadcastEvent("proc", ch.name .. " has a light source — Charlie avoids them.")
                    end
                end
            end
        end
    else
        broadcastEvent("gain", "Charlie checks paused tonight (The Calm Before).")
    end
end

-----------------------------------------------------------------------
-- Check if a player has a light source
-----------------------------------------------------------------------
function checkPlayerHasLight(color)
    -- In a full implementation, scan the player's hand zone for light-source items
    -- For now, check if flashlights are disabled and return a heuristic
    if gameState.ongoingDawnEffects.flashlightsDisabled or gameState.ongoingDawnEffects.onlyFireLight then
        -- Only Fire counts; broadcast a manual check
        broadcastEvent("proc", "Light check for " .. color .. ": only Fire sources count tonight. Confirm manually.")
        return false  -- conservative: assume no fire unless confirmed
    end

    -- Default: broadcast and assume the player will handle it
    broadcastEvent("proc", "Light check for " .. color .. ": do you have a Flashlight, Lantern, or Fire? (Confirm manually.)")
    return false  -- conservative default; Phase G/H will add proper item scanning
end

-----------------------------------------------------------------------
-- Identify threat type from card tags or GM notes
-----------------------------------------------------------------------
function identifyThreatType(card)
    if card.hasTag and card.hasTag("ThreatType:Soft") then return "Soft" end
    if card.hasTag and card.hasTag("ThreatType:Hard") then return "Hard" end
    if card.hasTag and card.hasTag("ThreatType:Persistent") then return "Persistent" end

    -- Fallback: check GMNotes
    local gm = card.getGMNotes and card.getGMNotes() or ""
    if gm:find("Soft") then return "Soft" end
    if gm:find("Persistent") then return "Persistent" end
    return "Hard"
end

-----------------------------------------------------------------------
-- Storytelling (Design §11.4 step 4)
-----------------------------------------------------------------------
function resolveStorytelling()
    broadcastEvent("phase", "--- STORYTELLING ---")
    broadcastEvent("proc", "Players at house tiles with Comfort/Music/Photo items may use them now for Sanity gains.")

    -- Luca's perk: storytelling gives +1 Sanity to all at his location
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char.name == "Luca" then
            local loc = char.location
            for c2, ch2 in pairs(gameState.activeChars) do
                if not ch2.down and ch2.location == loc then
                    ch2.sanity = math.min(ch2.maxSanity, ch2.sanity + 1)
                    broadcastEvent("gain", ch2.name .. " gains +1 Sanity from Luca's storytelling.")
                end
            end
        end
    end
end

-----------------------------------------------------------------------
-- Sleep regeneration (Design §11.4 step 5)
-----------------------------------------------------------------------
function resolveSleep()
    broadcastEvent("phase", "--- SLEEP ---")

    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local loc = char.location or ""
            local home = CHARACTER_HOMES[char.name]
            local isOwnHome = (home and loc == home)
            local isHouse = not (loc:find("Court") or loc:find("Badminton") or loc:find("Basketball"))

            -- Count others at same location
            local othersHere = 0
            for c2, ch2 in pairs(gameState.activeChars) do
                if c2 ~= color and not ch2.down and ch2.location == loc then
                    othersHere = othersHere + 1
                end
            end

            -- Winter scenario: houses give +1 Sanity bonus at sleep
            local winterBonus = (gameState.scenarioFlags or {}).housesSanityBonus and isHouse

            if isOwnHome then
                -- Own house: +1 Sanity, +1 Hunger, +1 Health
                local sanityGain = 1 + (winterBonus and 1 or 0)
                char.sanity = math.min(char.maxSanity, char.sanity + sanityGain)
                char.hunger = math.min(char.maxHunger, char.hunger + 1)
                char.health = math.min(char.maxHealth, char.health + 1)
                local winterNote = winterBonus and " (+1 Winter huddle)" or ""
                broadcastEvent("gain", char.name .. " sleeps at home: +1 Health, +1 Hunger, +" .. sanityGain .. " Sanity." .. winterNote)
            elseif isHouse and othersHere > 0 then
                -- Someone else's house, with company: +1 Sanity
                local sanityGain = 1 + (winterBonus and 1 or 0)
                char.sanity = math.min(char.maxSanity, char.sanity + sanityGain)
                local winterNote = winterBonus and " (+1 Winter huddle)" or ""
                broadcastEvent("gain", char.name .. " sleeps at a friend's house with company: +" .. sanityGain .. " Sanity." .. winterNote)
            elseif isHouse and othersHere == 0 then
                -- Someone else's house, alone: nothing
                broadcastEvent("proc", char.name .. " sleeps alone at someone else's house. No rest bonus.")
            else
                -- Sport court: nothing
                broadcastEvent("proc", char.name .. " sleeps at " .. loc .. ". No rest bonus (not a safe space).")
            end

            -- Coco's No Home constraint: if sleeping alone at a non-house, -3 Sanity
            if char.name == "Coco" and not isHouse and othersHere == 0 then
                char.sanity = math.max(0, char.sanity - 3)
                broadcastEvent("damage", "Coco sleeps alone outside a house — loses 3 Sanity (No Home).")
            end
        end
    end
end
