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
