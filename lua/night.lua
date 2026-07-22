-- night.lua  (F.9 — Night-phase resolver)
-- Design §11.4: For each location with players (least populated first):
--   1. Threat draw
--   2. Resolve threats (combat)
--   3. Charlie check (no light = 2 Sanity + 1 Health, escalating per consecutive dark night)
--   4. Storytelling (Comfort/Music items for Sanity)
--   5. Sleep regen (houses sleep 2 comfortably — extra sleepers get the floor)

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
-- Rayman's Loud, with the 3-player relief (§20.1, batch 4 W2): at 3
-- players the noise needs 3+ tiles moved today — a short errand stays
-- quiet. At 4-5 players any movement is Loud, as before.
-----------------------------------------------------------------------
function raymanLoudTonight()
    if not gameState.raymanMovedToday then return false end
    if gameState.playerCount == 3 and (gameState.raymanTilesMovedToday or 0) < 3 then
        return false
    end
    return true
end

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
-- Draw N threat cards onto a location tile. Shared by the Night
-- resolver below and the Eye of Terror's each-Dawn stare (day_loop.lua).
-----------------------------------------------------------------------
function drawThreatsAt(location, count)
    local threatDeck = getThreatDeck()
    if not threatDeck then return end
    for t = 1, count do
        local qty = threatDeck.getQuantity and threatDeck.getQuantity() or 0
        if qty > 0 then
            local tile = getLocationTile(location)
            local targetPos = tile and (tile.getPosition() + Vector(2, 1, t * 0.3)) or Vector(0, 2, 0)
            threatDeck.takeObject({
                position = targetPos,
                rotation = {0, 180, 0},
                smooth   = true,
                callback_function = function(threatCard)
                    -- pcall: the handle is dead if the card merged with
                    -- another threat on the tile mid-flight — touching any
                    -- field then throws "cannot access field of userdata".
                    local ok = pcall(function()
                        local tName = threatCard.getNickname() or "Unknown Threat"
                        local tDesc = threatCard.getDescription() or ""
                        broadcastEvent("warn", "THREAT at " .. location .. ": " .. tName)
                        broadcastEvent("proc", tDesc)

                        -- Auto-resolve soft threats (HP = 0)
                        local tType = identifyThreatType(threatCard)
                        if tType == "Soft" then
                            broadcastEvent("proc", tName .. " is a soft threat — resolves and discards.")
                        else
                            broadcastEvent("warn", tName .. " must be fought or fled! Flee: move 1 tile away, pay 1 Sanity (always legal, even starving). A fled threat stays here and festers at Dawn.")
                        end
                    end)
                    if not ok then
                        broadcastEvent("warn", "A Threat appears at " .. location .. " — its card stacked with another there; check the tile.")
                    end
                end
            })
        else
            broadcastEvent("proc", "Threat deck is empty.")
            break
        end
    end
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

    -- Crowd-drawn threats (Dawn cards): +1 threat at the most-populated location(s)
    if gameState.ongoingDawnEffects.crowdThreat then
        local maxPop = 0
        local popHere = #colors
        for _, ch in pairs(gameState.activeChars) do
            if not ch.down then
                local n = 0
                for _, ch2 in pairs(gameState.activeChars) do
                    if not ch2.down and ch2.location == ch.location then n = n + 1 end
                end
                if n > maxPop then maxPop = n end
            end
        end
        if popHere >= maxPop and popHere >= 2 then
            baseRate = baseRate + 1
            broadcastEvent("warn", "It is drawn to the gathering at " .. location .. " — +1 Threat.")
        end
    end

    -- Alone at a sport court: +1 extra threat
    if #colors == 1 and (location:find("Court") or location:find("Badminton") or location:find("Basketball")) then
        baseRate = baseRate + 1
        broadcastEvent("warn", charNames[1] .. " is alone at " .. location .. "! Extra threat drawn.")
    end

    -- Rayman's Loud constraint: if he moved at all today, the location where
    -- he spends the Night draws +1 Threat — the noise follows him home.
    if raymanLoudTonight() then
        for _, c in ipairs(colors) do
            local ch = gameState.activeChars[c]
            if ch and ch.name == "Rayman" then
                baseRate = baseRate + 1
                broadcastEvent("warn", "Rayman was Loud today — +1 Threat at " .. location .. ".")
                break
            end
        end
    end

    -- Dare — the court floodlights (P1_LIGHTS_FLICKER): the glow draws the
    -- dark. The reward half pays out at Dawn beside Moonlit Salvage.
    if gameState.ongoingDawnEffects.dareCourtGlow
        and (location:find("Court") or location:find("Badminton") or location:find("Basketball")) then
        baseRate = baseRate + 2
        broadcastEvent("warn", "The floodlights hum over " .. location .. " — the dare's price: +2 Threats.")
    end

    -- Posterize (Signature, §6.7): the dunk echoed here all afternoon.
    if (gameState.loudSignature or {})[location] then
        baseRate = baseRate + 1
        broadcastEvent("warn", "The echo of the dunk draws attention — +1 Threat at " .. location .. ".")
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
        drawThreatsAt(location, baseRate)
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
                    -- checkPlayerHasLight announces the protecting item itself
                    if not checkPlayerHasLight(c) then
                        resolveCharlieAttack(c)
                    end
                end
            end
        end
    else
        broadcastEvent("gain", "Charlie checks paused tonight (The Calm Before).")
    end
end

-----------------------------------------------------------------------
-- Light-source check: scans the player's hand and the area around
-- their player board for personal lights, and their current tile for
-- a shared Campfire. On fire-only nights (P2_PORCH_LIGHT /
-- P4_LAST_LIGHTS) the Flashlight is ignored.
--
-- Cards are matched by their Market id tag (build_save.py tags each
-- card with its CSV id) with a nickname fallback for hand-placed items.
-----------------------------------------------------------------------
LIGHT_SOURCES = {
    { id = "M_FLASHLIGHT", label = "Flashlight",       fire = false },
    { id = "M_LANTERN",    label = "Lantern",          fire = true  },
    { id = "M_FIRE_KIT",   label = "Fire Starter Kit", fire = true  },
}

local CAMPFIRE_RADIUS = 7  -- matches the fester radius: "at this tile"

local function _matchesLight(obj, src)
    if obj.hasTag and obj.hasTag(src.id) then return true end
    local nick = (obj.getNickname and obj.getNickname()) or ""
    return nick:lower():find(src.label:lower(), 1, true) ~= nil
end

-- The hand + player-board-area scan lives in helpers.lua now
-- (getPlayerCarriedObjects), shared with the combat weapon check so
-- "carried" can never mean two different things.

function checkPlayerHasLight(color)
    local char = gameState.activeChars[color]
    if not char then return false end
    local fireOnly = gameState.ongoingDawnEffects.flashlightsDisabled
                  or gameState.ongoingDawnEffects.onlyFireLight

    -- Shared fire: a Campfire at this character's tile covers everyone there.
    local tile = getLocationTile(char.location or "")
    if tile then
        local tp = tile.getPosition()
        for _, obj in ipairs(getAllObjects()) do
            local isCampfire = (obj.hasTag and obj.hasTag("M_CAMPFIRE"))
            if not isCampfire then
                local nick = (obj.getNickname and obj.getNickname()) or ""
                isCampfire = nick:lower():find("campfire", 1, true) ~= nil
            end
            if isCampfire then
                local p = obj.getPosition()
                local dx, dz = p.x - tp.x, p.z - tp.z
                if (dx * dx + dz * dz) <= (CAMPFIRE_RADIUS * CAMPFIRE_RADIUS) then
                    broadcastEvent("proc", char.name .. " is lit by the Campfire at " .. (char.location or "?") .. " — Charlie stays away.")
                    return true
                end
            end
        end
    end

    -- Personal lights: hand + player-board area.
    local foundDisabled = nil
    for _, obj in ipairs(getPlayerCarriedObjects(color, char.name)) do
        for _, src in ipairs(LIGHT_SOURCES) do
            if _matchesLight(obj, src) then
                if src.fire or not fireOnly then
                    local note = (src.id == "M_FIRE_KIT") and " (spend 1 Wood for tonight's fire)" or ""
                    broadcastEvent("proc", char.name .. "'s " .. src.label .. " keeps the dark out" .. note .. " — Charlie stays away.")
                    return true
                end
                foundDisabled = src.label
            end
        end
    end

    if foundDisabled then
        broadcastEvent("warn", char.name .. "'s " .. foundDisabled .. " is useless tonight — only Fire counts as light.")
    else
        broadcastEvent("proc", char.name .. " has no light: no Flashlight/Lantern/Fire Kit in hand or by their player board, no Campfire at their tile.")
    end
    return false
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

    -- Luca's perk: storytelling gives +1 Sanity to all at his location.
    -- Needs an Audience (§6.5): alone, there's nobody to tell — and his
    -- own Sanity doesn't regenerate without company.
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char.name == "Luca" then
            if not charHasCompany(color) then
                broadcastEvent("proc", "Luca has no one to tell stories to tonight (Needs an Audience — no Sanity regen alone).")
            else
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
end

-----------------------------------------------------------------------
-- Sleep regeneration (Design §11.4 step 5)
-----------------------------------------------------------------------
function resolveSleep()
    broadcastEvent("phase", "--- SLEEP ---")

    -- Crowded floor (Design §11.4): a house sleeps two comfortably. Each
    -- character beyond the second at the same house gets the floor — no
    -- sleep regeneration. Beds go to owners first, then to the guests who
    -- need them most (lowest Sanity).
    local BEDS_PER_HOUSE = 2
    local floorSleepers = {}   -- [color] = true
    local sleepersByLoc = {}   -- [loc] = { {color=, char=}, ... }
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local loc = char.location or ""
            local isHouse = not (loc:find("Court") or loc:find("Badminton") or loc:find("Basketball"))
            if isHouse then
                sleepersByLoc[loc] = sleepersByLoc[loc] or {}
                table.insert(sleepersByLoc[loc], { color = color, char = char })
            end
        end
    end
    for loc, sleepers in pairs(sleepersByLoc) do
        if #sleepers > BEDS_PER_HOUSE then
            -- Owners keep their own beds; remaining beds go to lowest-Sanity guests.
            table.sort(sleepers, function(a, b)
                local aOwn = (CHARACTER_HOMES[a.char.name] == loc)
                local bOwn = (CHARACTER_HOMES[b.char.name] == loc)
                if aOwn ~= bOwn then return aOwn end
                return a.char.sanity < b.char.sanity
            end)
            for i = BEDS_PER_HOUSE + 1, #sleepers do
                floorSleepers[sleepers[i].color] = true
                broadcastEvent("warn", sleepers[i].char.name .. " gets the floor at " .. loc ..
                    " — a house sleeps two comfortably. No sleep regen.")
            end
        end
    end

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

            -- Crowded-floor sleepers get no regen (broadcast already sent
            -- above); everyone else settles according to where they slept.
            if not floorSleepers[color] then
                if isOwnHome then
                    -- Own house: +1 Sanity, +1 Hunger, +1 Health.
                    -- Needs an Audience (§6.5): Luca alone regains no Sanity —
                    -- the body rests, the mind doesn't.
                    local sanityGain = 1 + (winterBonus and 1 or 0)
                    if char.name == "Luca" and othersHere == 0 then
                        sanityGain = 0
                    end
                    char.sanity = math.min(char.maxSanity, char.sanity + sanityGain)
                    char.hunger = math.min(char.maxHunger, char.hunger + 1)
                    char.health = math.min(char.maxHealth, char.health + 1)
                    local winterNote = winterBonus and " (+1 Winter huddle)" or ""
                    if sanityGain == 0 then
                        broadcastEvent("gain", char.name .. " sleeps at home alone: +1 Health, +1 Hunger — but no Sanity (Needs an Audience).")
                    else
                        broadcastEvent("gain", char.name .. " sleeps at home: +1 Health, +1 Hunger, +" .. sanityGain .. " Sanity." .. winterNote)
                    end
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
            end

            -- Coco's No Home constraint: if sleeping alone at a non-house, -3 Sanity
            if char.name == "Coco" and not isHouse and othersHere == 0 then
                char.sanity = math.max(0, char.sanity - 3)
                broadcastEvent("damage", "Coco sleeps alone outside a house — loses 3 Sanity (No Home).")
            end
        end
    end
end
