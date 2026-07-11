-- helpers.lua  (F.2 — Tag-based lookup helpers)
-- All object lookups use tags, never GUIDs, per TTS §13 pitfall 2.

function findAllByTag(tag)
    local results = {}
    for _, obj in ipairs(getAllObjects()) do
        if obj.hasTag(tag) then
            table.insert(results, obj)
        end
    end
    return results
end

function findOneByTag(tag)
    for _, obj in ipairs(getAllObjects()) do
        if obj.hasTag(tag) then return obj end
    end
    return nil
end

function findOneByTags(tags)
    for _, obj in ipairs(getAllObjects()) do
        local match = true
        for _, t in ipairs(tags) do
            if not obj.hasTag(t) then match = false; break end
        end
        if match then return obj end
    end
    return nil
end

-- Typed convenience wrappers
function getMainBoard()        return findOneByTag("MainBoard") end
function getDoomMarker()       return findOneByTag("DoomMarker") end
function getDayCounter()       return findOneByTag("DayCounter") end
function getMarketDeck()       return findOneByTag("MarketCardDeck") end
function getThreatDeck()       return findOneByTag("ThreatCardDeck") end
function getVisitorDeck()      return findOneByTag("VisitorCardDeck") end
function getBossPool()         return findOneByTag("BossPool") end
function getHeartSupply()      return findOneByTag("TelltaleHeartSupply") end
function getSeverityLegend()   return findOneByTag("SeverityLegend") end

function getPhaseDeck(phase)
    return findOneByTag("PhaseCard:P" .. tostring(phase) .. "Deck")
        or findOneByTag("PhaseCardDeck")
end

function getLocationTile(name)
    return findOneByTag("Location:" .. name)
end

function getCharacterStandee(name)
    return findOneByTag("Character:" .. name)
end

function getPlayerBoard(name)
    return findOneByTag("PlayerBoard:" .. name)
end

function getHandZone(color)
    return findOneByTag("HandZone:" .. color)
end

function getMarketSlots()
    local slots = {}
    for i = 0, 4 do
        local s = findOneByTag("MarketSlot:" .. tostring(i))
        if s then table.insert(slots, s) end
    end
    return slots
end

function getPathVariantBag(variant)
    return findOneByTag("PathVariant:" .. variant)
end

function getResourceBag(resType)
    return findOneByTag("ResourceBag:" .. resType)
end

-----------------------------------------------------------------------
-- Standee placement: every character owns a fixed slot offset on every
-- tile so standees never stack on top of each other. The offsets mirror
-- the CharSlot row build_save.py bakes into each location tile (a row
-- across the tile's lower half, leaving the location name readable).
-----------------------------------------------------------------------
CHAR_SLOT_INDEX = { James = 0, Coco = 1, Rayman = 2, Ellie = 3, Luca = 4 }

function getCharSlotPosition(tile, charName)
    local i = CHAR_SLOT_INDEX[charName] or 0
    -- A row along the tile's near edge, clear of the printed name/yields.
    return tile.getPosition() + Vector(-1.8 + i * 0.9, 1.5, -1.7)
end

function placeCharacterAtTile(charName, locName)
    local standee = getCharacterStandee(charName)
    local tile = getLocationTile(locName)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, charName))
        return true
    end
    return false
end

-- Characters that aren't in the current game wait on a bench off the
-- board's right edge instead of cluttering the map.
BENCH_POSITION = { x = 18.5, z = 7 }   -- slots run toward -z from here

function benchUnusedCharacters()
    local inPlay = {}
    for _, char in pairs(gameState.activeChars or {}) do
        if char and char.name then inPlay[char.name] = true end
    end
    for name, i in pairs(CHAR_SLOT_INDEX) do
        if not inPlay[name] then
            local standee = getCharacterStandee(name)
            if standee then
                standee.setPositionSmooth(Vector(BENCH_POSITION.x, 1.5, BENCH_POSITION.z - i * 3))
            end
        end
    end
end

-----------------------------------------------------------------------
-- Objects a player "carries": cards in their hand plus anything laid
-- out around their player board (the same padded box getPlayerResources
-- uses). One definition shared by the night light check and the combat
-- weapon check, so "carried" can never mean two different things.
-----------------------------------------------------------------------
function getPlayerCarriedObjects(color, charName)
    local out = {}
    -- Cards in the player's hand
    local ok, handObjs = pcall(function() return Player[color].getHandObjects() end)
    if ok and handObjs then
        for _, o in ipairs(handObjs) do out[#out + 1] = o end
    end
    -- Objects laid out around the player board
    local board = getPlayerBoard(charName)
    if board then
        local pos = board.getPosition()
        local b = board.getBoundsNormalized()
        local pad = 1.5
        local minX = pos.x - b.size.x * 0.5 - pad
        local maxX = pos.x + b.size.x * 0.5 + pad
        local minZ = pos.z - b.size.z * 0.5 - pad
        local maxZ = pos.z + b.size.z * 0.5 + pad
        for _, obj in ipairs(getAllObjects()) do
            local p = obj.getPosition()
            if p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
                out[#out + 1] = obj
            end
        end
    end
    return out
end

-- Get all active (seated) player colors
function getActivePlayerColors()
    local colors = {}
    for _, p in ipairs(Player.getPlayers()) do
        if p.seated and p.color ~= "Grey" and p.color ~= "Black" then
            table.insert(colors, p.color)
        end
    end
    return colors
end

-- Map player color to character name
function colorToCharacter(color)
    local map = {White="James", Red="Coco", Yellow="Rayman", Green="Ellie", Blue="Luca"}
    return map[color]
end

function characterToColor(name)
    local map = {James="White", Coco="Red", Rayman="Yellow", Ellie="Green", Luca="Blue"}
    return map[name]
end

-----------------------------------------------------------------------
-- gameRoll — the RNG seam. ALL gameplay randomness (attack dice, dawn
-- card rolls, loot picks, lair/scenario draws) goes through this one
-- function, so tests can script outcomes by redefining gameRoll without
-- monkeypatching math.random (which the TTS stub and cosmetic systems
-- like the audio shuffle also use). Same signature as math.random.
-----------------------------------------------------------------------
function gameRoll(a, b)
    if b then return math.random(a, b) end
    return math.random(a)
end

-- Safe pcall wrapper (F.15)
function safecall(fn, context)
    local ok, err = pcall(fn)
    if not ok then
        broadcastEvent("proc", "(Edge case in " .. (context or "unknown") .. " — continuing.) " .. tostring(err))
        log(err, "ERROR", "safecall")
    end
    return ok
end
