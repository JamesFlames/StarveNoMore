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
-- Resource automation: the players never reach into a supply bag by hand.
-- giveResource pulls tokens from the shared supply and lays them out in a
-- player's board area (the same padded box getPlayerResources scans, so
-- they count immediately). spawnResourceAtTile drops them on a location
-- tile as a free pickup (dawn-card deliveries, Treeguard salvage). Both
-- are the counterpart to verifyAndPayResources, which puts tokens back.
-- Each returns the number of tokens actually delivered (0 if the bag or
-- destination is missing, so callers degrade gracefully in headless play).
-----------------------------------------------------------------------
local function _tagResource(tok, resType)
    if not tok then return end
    -- Infinite-bag tokens ship pre-tagged (build_save.py); re-tagging is a
    -- harmless no-op there but makes a token count in headless tests, where
    -- the stub bag hands back a blank object.
    pcall(function() tok.addTag("Resource") end)
    pcall(function() tok.addTag("Resource:" .. resType) end)
end

function giveResource(color, resType, qty)
    qty = qty or 1
    local charName = colorToCharacter(color)
    if not charName then return 0 end
    local board = getPlayerBoard(charName)
    local bag = getResourceBag(resType)
    if not board or not bag then return 0 end
    local base = board.getPosition()
    local given = 0
    for i = 1, qty do
        local ok = safecall(function()
            local tok = bag.takeObject({
                position = base + Vector(-2.6 + (i % 3) * 0.5, 0.8 + i * 0.4, -1.2),
                smooth   = true,
            })
            _tagResource(tok, resType)
        end, "GiveResource")
        if ok then given = given + 1 end
    end
    return given
end

function spawnResourceAtTile(locName, resType, qty)
    qty = qty or 1
    local tile = getLocationTile(locName)
    local bag = getResourceBag(resType)
    if not tile or not bag then return 0 end
    local base = tile.getPosition()
    local given = 0
    for i = 1, qty do
        local ok = safecall(function()
            local tok = bag.takeObject({
                position = base + Vector(-1.2 + (i % 3) * 1.2, 3, 2 + math.floor((i - 1) / 3) * 1.0),
                smooth   = true,
            })
            _tagResource(tok, resType)
        end, "SpawnResourceAtTile")
        if ok then given = given + 1 end
    end
    return given
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

-- Does another standing character share this character's tile? One
-- definition for every "alone" rule (Luca's Needs an Audience, Coco's
-- No Home warning, sleep bonuses), so "company" can't drift.
function charHasCompany(color)
    local char = gameState and gameState.activeChars and gameState.activeChars[color]
    if not char then return false end
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == char.location then
            return true
        end
    end
    return false
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

-- Map player color to character name. Mid-game the roster is authoritative
-- (a loaded old save may predate the colour scheme); otherwise fall back
-- to the character-colour scheme in CHARACTER_COLORS (global.lua).
function colorToCharacter(color)
    local char = gameState and gameState.activeChars and gameState.activeChars[color]
    if char then return char.name end
    for name, c in pairs(CHARACTER_COLORS) do
        if c == color then return name end
    end
    return nil
end

function characterToColor(name)
    for color, char in pairs((gameState and gameState.activeChars) or {}) do
        if char.name == name then return color end
    end
    return CHARACTER_COLORS[name]
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
