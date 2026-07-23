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
-- Resource automation. THE COUNT IS AUTHORITATIVE IN gameState.resources
-- (per colour), NOT in physical token positions. Playtest 2026-07: the
-- old position-counting broke the moment a player board drifted (boards
-- spawned overlapping, physics flung them across the table, and a gathered
-- token 11 units from its board counted as zero). Physical tokens are now
-- pure decoration laid beside the board; giveResource / takeResourceFromPlayer
-- / verifyAndPayResources all read and write the gameState counts, so the
-- economy is correct no matter where a token or board ends up.
-----------------------------------------------------------------------
RESOURCE_TYPES_LIST = {"Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"}

-- The per-colour count table, created on first use (and after setup wipes).
function ensurePlayerResources(color)
    gameState.resources = gameState.resources or {}
    local r = gameState.resources[color]
    if not r then
        r = {}
        for _, t in ipairs(RESOURCE_TYPES_LIST) do r[t] = 0 end
        gameState.resources[color] = r
    end
    return r
end

local function _tagResource(tok, resType)
    if not tok then return end
    -- Infinite-bag tokens ship pre-tagged (build_save.py); re-tagging is a
    -- harmless no-op there but makes a token count in headless tests, where
    -- the stub bag hands back a blank object.
    pcall(function() tok.addTag("Resource") end)
    pcall(function() tok.addTag("Resource:" .. resType) end)
end

-- Lay `qty` decorative tokens beside the player's board (cosmetic only —
-- the authoritative count lives in gameState). Silent no-op headless / if
-- the board or bag is missing.
local function _spawnVisualTokens(charName, resType, qty)
    local board = getPlayerBoard(charName)
    local bag = getResourceBag(resType)
    if not board or not bag then return end
    local base = board.getPosition()
    for i = 1, qty do
        safecall(function()
            local tok = bag.takeObject({
                position = base + Vector(-2.6 + (i % 3) * 0.5, 0.8 + i * 0.4, -1.2),
                smooth   = true,
            })
            _tagResource(tok, resType)
        end, "GiveResource")
    end
end

-- Remove up to `qty` decorative tokens of resType from near a player's
-- board, back into the supply. Best-effort cosmetics — never affects the
-- count (that's already been adjusted in gameState by the caller).
local function _removeVisualTokens(color, resType, qty)
    local charName = colorToCharacter(color)
    local board = charName and getPlayerBoard(charName)
    if not board then return end
    local pos = board.getPosition()
    local b = board.getBoundsNormalized()
    local pad = 1.5
    local removed = 0
    for _, obj in ipairs(findAllByTag("Resource:" .. resType)) do
        if removed >= qty then break end
        local p = obj.getPosition()
        if p.x >= pos.x - b.size.x * 0.5 - pad and p.x <= pos.x + b.size.x * 0.5 + pad
            and p.z >= pos.z - b.size.z * 0.5 - pad and p.z <= pos.z + b.size.z * 0.5 + pad then
            local bag = getResourceBag(resType)
            local ok = pcall(function()
                if bag then bag.putObject(obj) else obj.destruct() end
            end)
            if ok then removed = removed + 1 end
        end
    end
end

-- Public wrapper so ui_actionbar_core's verifyAndPayResources can drop the
-- visual tokens after deducting the authoritative count.
function removeVisualTokens(color, resType, qty)
    safecall(function() _removeVisualTokens(color, resType, qty) end, "RemoveVisual")
end

function giveResource(color, resType, qty)
    qty = qty or 1
    local charName = colorToCharacter(color)
    if not charName then return 0 end
    local r = ensurePlayerResources(color)
    if r[resType] ~= nil then r[resType] = r[resType] + qty end
    _spawnVisualTokens(charName, resType, qty)
    return qty
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
-- Best-effort discard: remove up to qty of resType from a player's held
-- count (gameState), returning how many were actually taken — 0 is fine
-- (dawn cards say "discard 1 Battery IF HELD"). Also clears that many
-- decorative tokens. verifyAndPayResources (ui_actionbar_core.lua) is the
-- all-or-nothing variant for fixed costs.
-----------------------------------------------------------------------
function takeResourceFromPlayer(color, resType, qty)
    qty = qty or 1
    local r = ensurePlayerResources(color)
    local taken = math.min(qty, r[resType] or 0)
    if taken > 0 then
        r[resType] = r[resType] - taken
        removeVisualTokens(color, resType, taken)
    end
    return taken
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
    -- y is ABOVE the tile top (tiles sit on the ~1.55-high glass surface);
    -- the unlocked standee settles the last stretch itself.
    return tile.getPosition() + Vector(-1.8 + i * 0.9, 1.0, -1.7)
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

-- Characters that aren't in the current game wait on the under-table
-- library shelf (out of sight, like every inactive component) instead of
-- cluttering the map. A later placeCharacterAtTile (e.g. a Visitor
-- arrival) brings them back — smooth moves pass through the table.
BENCH_POSITION = { x = -23, y = -2.5, z = 8 }   -- slots run toward -z from here

function benchUnusedCharacters()
    local inPlay = {}
    for _, char in pairs(gameState.activeChars or {}) do
        if char and char.name then inPlay[char.name] = true end
    end
    for name, i in pairs(CHAR_SLOT_INDEX) do
        if not inPlay[name] then
            local standee = getCharacterStandee(name)
            if standee then
                standee.setPositionSmooth(Vector(BENCH_POSITION.x, BENCH_POSITION.y, BENCH_POSITION.z - i * 3))
            end
        end
    end
end

-- Player boards for characters nobody picked go under the table too, so a
-- 1- or 3-player game doesn't show four empty boards ("don't display
-- boards of players not in play"). Locked boards still move via setPosition.
-- x=-20, y=-2.5 mirrors the under-table library shelf (LIBRARY_Y).
function benchUnusedBoards()
    local inPlay = {}
    for _, char in pairs(gameState.activeChars or {}) do
        if char and char.name then inPlay[char.name] = true end
    end
    for name, i in pairs(CHAR_SLOT_INDEX) do
        if not inPlay[name] then
            local board = getPlayerBoard(name)
            if board then
                pcall(function()
                    board.setLock(false)
                    board.setPosition(Vector(-20, -2.5, 14 - i * 3))
                    board.setLock(true)
                end)
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
