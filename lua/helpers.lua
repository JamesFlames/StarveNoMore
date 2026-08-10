-- helpers.lua  (F.2 — Tag-based lookup helpers)
-- All object lookups use tags, never GUIDs, per TTS §13 pitfall 2.

-- These scan every object on the table, so they meet stale handles first:
-- one dead handle used to make EVERY tag lookup in the mod throw
-- "cannot access field hasTag of userdata<LuaObject>". They read through
-- safeHasTag (defined below; globals resolve at call time) so a dead
-- handle is simply skipped.
function findAllByTag(tag)
    local results = {}
    for _, obj in ipairs(getAllObjects()) do
        if safeHasTag(obj, tag) then
            table.insert(results, obj)
        end
    end
    return results
end

function findOneByTag(tag)
    for _, obj in ipairs(getAllObjects()) do
        if safeHasTag(obj, tag) then return obj end
    end
    return nil
end

-----------------------------------------------------------------------
-- Dead-handle-safe readers.
-- A handle can outlive its object (merged into a deck, destroyed by a
-- player); ANY field access then throws "cannot access field X of
-- userdata<LuaObject>" — the single most common crash in this mod
-- (pry, dawn reveal, threat reveal, gather). Read through these instead
-- of touching obj.* directly whenever the handle came from a callback,
-- a stored GUID, or a scan of the table. See docs/tts-interface.md.
-----------------------------------------------------------------------

function isLiveObject(obj)
    if not obj then return false end
    return (pcall(function() return obj.getPosition() end))
end

function safeNickname(obj)
    if not obj then return "" end
    local ok, name = pcall(function() return obj.getNickname() or "" end)
    if ok and type(name) == "string" then return name end
    return ""
end

-- A handle's GUID, or nil if it cannot be read. Exists because a nil GUID is
-- worse than a dead handle: `someTable[obj.getGUID()] = v` throws "table index
-- is nil" rather than the usual field-access error, and the callers that keep
-- a guid->something map all did exactly that inside a bare pcall — so the
-- throw was swallowed and reported as "there is nothing here" (the Craft
-- purchase reported "No cards in the Market display" with five cards on the
-- table). Returns nil so callers can skip the object instead of dying.
function safeGuid(obj)
    if not obj then return nil end
    local ok, guid = pcall(function() return obj.getGUID() end)
    if ok and type(guid) == "string" and guid ~= "" then return guid end
    return nil
end

function safeHasTag(obj, tag)
    if not obj then return false end
    local ok, has = pcall(function()
        return (obj.hasTag and obj.hasTag(tag)) or false
    end)
    return (ok and has) or false
end

-----------------------------------------------------------------------
-- Button labels.
-- UI.setAttribute(id, "text", ...) RESETS a Button's styling: the label
-- comes back near-black, which on our dark plates reads as unreadable or
-- disabled ("I'm settled" was dark-on-dark). Setting the colour in a
-- second call is a race — set text and colours in ONE setAttributes call
-- so the styling can never be lost in between. See docs/tts-interface.md.
-----------------------------------------------------------------------

-- Light plate + dark label. TTS dims a DISABLED button's text toward its
-- plate: on a dark plate the label disappears entirely (the action bar was
-- unreadable with 0 actions left), on a light one a dimmed dark label still
-- reads. House rule: light background => dark text.
BTN_DARK_PLATE = "#B9C9B4FF"   -- the standard button plate (light sage)
BTN_ON_DARK    = "#12180F"     -- readable label on that plate

-- The "yes, do it" green. ONE pair, because a second one that is merely close
-- does not read as the same control: the confirm mirrored onto an action-bar
-- button wore its own #AEFFAE, and a pale mint label on a dark plate in a bar
-- of bright sage buttons reads as GREYED OUT — "Take the Stash" looked
-- disabled while it was the live answer. Any button that means yes/committed
-- wears these, and they match confirmYes in xml/dialogs.xml (and "Got it" in
-- xml/msglog.xml) exactly; test_confirm_green_is_one_colour is the guard.
BTN_YES_TEXT  = "#88FF88"      -- bright green label + tick
BTN_YES_PLATE = "#1E501EE6"    -- the dark green plate it sits on

-- Face up and the right way round for a token. Two separate things:
--   rotZ=0  is the FACE. A token is a flat disc with no back image, so one
--           settling on rotZ=180 shows the same art from behind, i.e. mirrored.
--   rotY=180 is the TURN. Token art is authored upright and the object carries
--           the half turn flat art needs on the felt (build_save.TOKEN_ZOOM_ROT)
--           — done that way round so Alt-zoom, which TTS draws in the object's
--           LOCAL frame, magnifies the label upright instead of upside down.
-- Keep the 180 in step with TOKEN_ZOOM_ROT; test_cross_refs compares them.
-- Full rationale: docs/tts-runtime.md, "Rotations".
TOKEN_FACE_UP = { 0, 180, 0 }

function setButtonLabel(id, text, textColor, color)
    if not UI then return end
    UI.setAttributes(id, {
        text      = text,
        textColor = textColor or BTN_ON_DARK,
        color     = color or BTN_DARK_PLATE,
    })
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
RESOURCE_TYPES_LIST = {"Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"}

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
-- Each resource type gets its own little run of tokens beside the board, and
-- every new token is nudged along that run rather than dropped on the last
-- one: a stack of six identical discs is impossible to count at a glance, a
-- fanned row is not. The index continues across separate awards (the old code
-- restarted at 1 each call, so a second Gather landed on the first one).
RESOURCE_ROW_INDEX = {}

local function _spawnVisualTokens(charName, resType, qty)
    local board = getPlayerBoard(charName)
    local bag = getResourceBag(resType)
    if not board or not bag then return end
    local base = board.getPosition()

    -- One row per resource type, running along the board's edge.
    local slot = 0
    for i, t in ipairs(RESOURCE_TYPES_LIST) do
        if t == resType then slot = i - 1; break end
    end
    local key = charName .. ":" .. resType
    RESOURCE_ROW_INDEX[key] = RESOURCE_ROW_INDEX[key] or 0

    for _ = 1, qty do
        local n = RESOURCE_ROW_INDEX[key]
        RESOURCE_ROW_INDEX[key] = n + 1
        safecall(function()
            local tok = bag.takeObject({
                -- Step each token along the row; wrap to a second rank after
                -- six so a big pile stays beside the board instead of walking
                -- across the table.
                -- Y is absolute (spawnDropY, global.lua), not base.y + 0.8:
                -- gathered tokens land beside the board, right on the main
                -- board's rim, and a 0.85 drop was not enough to clear it.
                -- Six of them ended a live session sunk inside the tabletop.
                position = Vector(
                    base.x - 2.6 + (n % 6) * 0.42,
                    spawnDropY(base.y),
                    base.z - 1.2 - slot * 0.55 - math.floor(n / 6) * 0.30),
                -- TOKEN_FACE_UP, not "whatever the bag was holding". A token is
                -- a flat disc with the same art on both faces, so one that
                -- lands on its back shows the label MIRRORED — Metal, Cloth and
                -- Energy Drink were all reading backwards on one table. Spawned
                -- without a rotation they inherit the bag's and then settle
                -- whichever way the drop bounces them. The yaw in it matters
                -- just as much: it is what keeps the label upright.
                rotation = TOKEN_FACE_UP,
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
                rotation = TOKEN_FACE_UP,   -- see _spawnVisualTokens
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

-- A Down character's standee lies on the table; reviving stands it back up.
--
-- rotX, not rotZ: a standee is a flat plane facing the camera, so tipping it
-- about X turns the art face-up and the whole figure reads as lying down from
-- a seated camera. Rotating about Z would only spin the picture in its own
-- plane — the figure would still be standing, sideways.
--
-- The yaw is preserved, so a standee keeps whichever way it was facing. Move
-- and ghost drift only ever set position, so the posture survives both: a
-- ghost drifts around the map still lying down.
STANDEE_DOWN_PITCH = 90

-- ...and the colour drains out of them.
--
-- This is the automated version of "flip the standee to its ghost side", an
-- instruction the game printed for a long time and could never be followed:
-- THERE IS NO GHOST SIDE. Each standee's back is simply a rear view of the
-- living character — James from behind, Coco from behind, halo and wings
-- unchanged. Flipping shows a character standing with their back turned,
-- which reads as "facing away", not "dead".
--
-- TTS multiplies ColorDiffuse over the whole standee, so a near-black tint
-- greys the figure out where it lies. Down reads as down without needing art
-- nobody drew. Revive puts the seat colour back (CHARACTER_COLORS ->
-- stringToColorTint, the same source the hand-zone glow uses).
STANDEE_DOWN_TINT = { 0.28, 0.28, 0.32 }

function setStandeePosture(charName, isDown)
    local standee = getCharacterStandee(charName)
    if not standee then return false end
    local ok = safecall(function()
        local rot = standee.getRotation() or {}
        standee.setRotationSmooth({ isDown and STANDEE_DOWN_PITCH or 0,
                                    rot.y or 0, 0 }, false, true)
    end, "StandeePosture")
    safecall(function()
        local tint = STANDEE_DOWN_TINT
        if not isDown then
            tint = stringToColorTint(CHARACTER_COLORS[charName])
        end
        standee.setColorTint(tint)
    end, "StandeeTint")
    return ok
end

function placeCharacterAtTile(charName, locName)
    local standee = getCharacterStandee(charName)
    local tile = getLocationTile(locName)
    if standee and tile then
        -- Coming back up from the bench: sealUnderTableObjects (audit.lua)
        -- turned this standee's pointer interaction off while it was under
        -- the table. On the board it has to answer the mouse again.
        pcall(function() standee.interactable = true end)
        standee.setPositionSmooth(getCharSlotPosition(tile, charName))
        return true
    end
    return false
end

-- Characters that aren't in the current game wait on the under-table
-- library shelf (out of sight, like every inactive component) instead of
-- cluttering the map. A later placeCharacterAtTile (e.g. a Visitor
-- arrival) brings them back — smooth moves pass through the table.
-- Inside the board footprint (+/-12) so the board and the opaque table hide
-- them. Teleported, never smooth-moved: a smooth move to a spot under a solid
-- table collides on the way and leaves the standee hanging in mid-air
-- ("all the characters I am not playing are floating in the air").
BENCH_POSITION = { x = -9, y = -2.5, z = 8 }   -- slots run toward -z from here

function benchUnusedCharacters()
    local inPlay = {}
    for _, char in pairs(gameState.activeChars or {}) do
        if char and char.name then inPlay[char.name] = true end
    end
    -- Benched inside the board footprint (+/-12): parked at x=-20 they
    -- sat beyond the table edge and read as floating in mid-air.
    for name, i in pairs(CHAR_SLOT_INDEX) do
        if not inPlay[name] then
            local standee = getCharacterStandee(name)
            if standee then
                pcall(function()
                    standee.setLock(false)
                    standee.setPosition(Vector(BENCH_POSITION.x, BENCH_POSITION.y,
                                               BENCH_POSITION.z - i * 3))
                    standee.setLock(true)
                end)
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
                    board.setPosition(Vector(-9, -2.5, 9 - i * 4))
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
            -- A handle here can already be dead (a token merged into a stack
            -- as it landed); reading .getPosition() then throws and took the
            -- whole Gather action down with it.
            local ok, p = pcall(function() return obj.getPosition() end)
            if ok and p and p.x >= minX and p.x <= maxX and p.z >= minZ and p.z <= maxZ then
                out[#out + 1] = obj
            end
        end
    end
    return out
end

-- Does another standing character share this character's tile? One
-- definition for every "alone" rule (Luca's Needs an Audience, Coco's
-- No Home warning, sleep bonuses), so "company" can't drift.
-----------------------------------------------------------------------
-- Last Nerve (Design §10.1) — the INDIVIDUAL-level death-spiral valve.
--
-- §10.1's three threshold effects are all positive feedback pointed
-- downward: low Health costs you movement, so you reach food and allies
-- less; low Sanity makes you Haunted, so you fight alone and lose more
-- Sanity; Hunger 0 bleeds Health. The design's one catch-up mechanism,
-- Doom 25's Nothing Left to Lose (§15.2), is excellent — and it fires on
-- the TEAM's shared clock. A player can spiral into irrelevance on Day 4
-- while Doom sits at 12 and receive nothing at all: still at the table,
-- still nominally playing, out of meaningful decisions. That is the co-op
-- form of player elimination, and worse than in a competitive game
-- because there is no side left to root for.
--
-- Last Nerve is the individual mirror of Doom 25, using the same logic
-- the team-level version already validated: catch-up that arrives as the
-- third act, symmetric, and self-limiting — it switches off the moment
-- you recover, and it can only ever trigger on someone nearly dead, so
-- it cannot snowball. Thematically it is adrenaline: being cornered makes
-- you run better.
--
-- It targets one specific trap. Flee (§12.4) is the guaranteed-legal
-- escape, and it costs 1 Sanity — so the escape hatch is priced in the
-- currency most likely to be empty. A Sanity-2 character's only legal
-- move used to cost a third of what was left.
-----------------------------------------------------------------------
LAST_NERVE_THRESHOLD = 3

function hasLastNerve(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return false end
    local t = LAST_NERVE_THRESHOLD
    return char.health < t or char.hunger < t or char.sanity < t
end

-- Sport court vs. house. The two sport courts are the only non-house tiles,
-- and a dozen rules key off the distinction (threat rates, sleep regen, rain,
-- Coco's No Home). Every one of them used to open-code the same
-- `loc:find("Court") or loc:find("Badminton") or loc:find("Basketball")`
-- triple, which is three chances to mistype a rule into silence.
function isSportCourt(loc)
    return loc == "BasketballCourt" or loc == "BadmintonCourt"
end

-- The carried object matching a Market id (or its printed name), or nil.
-- Same two places every other carried-item rule looks — the hand and the
-- player-board area — via getPlayerCarriedObjects. Returns the OBJECT, so a
-- single-use item can be consumed rather than merely detected.
function findCarriedItem(color, marketId, label)
    local char = gameState.activeChars[color]
    if not char then return nil end
    local found = nil
    safecall(function()
        for _, obj in ipairs(getPlayerCarriedObjects(color, char.name)) do
            if safeHasTag(obj, marketId) then found = obj; return end
            if label and safeNickname(obj):lower():find(label:lower(), 1, true) then
                found = obj; return
            end
        end
    end, "CarriedItem")
    return found
end

-- Consume a single-use carried item. Best-effort: the rule has already been
-- paid for by the time the card is destroyed, and a dead handle must not
-- un-apply the effect (docs/tts-interface.md).
function consumeCarriedItem(obj)
    if not obj then return false end
    pcall(function() obj.destruct() end)
    return true
end

-- One step from `loc`, deduplicated, including any edge a scenario adds.
--
-- The single answer to "is that tile adjacent?" — Move, the Dusk scramble,
-- Flee and the drag-a-standee handler all route through here. LOCATION_ADJACENCY
-- itself is rebuilt per path variant by applyPathVariant (ui_actionbar_core);
-- this reads it at call time, never captures it.
function adjacentLocations(loc)
    local out, seen = {}, {}
    for _, n in ipairs((LOCATION_ADJACENCY or {})[loc] or {}) do
        if not seen[n] then seen[n] = true; out[#out + 1] = n end
    end
    -- SC_SHORTCUT's JamesHouse <-> BadmintonCourt edge. Ring (the default
    -- variant) and Sprawl already print that road, so adding it unguarded
    -- handed back the same neighbour twice — two overlapping MOVE HERE
    -- buttons on one tile, and an inflated count of legal targets.
    if (gameState.scenarioFlags or {}).shortcutPath then
        local extra = (loc == "JamesHouse" and "BadmintonCourt")
                   or (loc == "BadmintonCourt" and "JamesHouse")
        if extra and not seen[extra] then out[#out + 1] = extra end
    end
    return out
end

function isAdjacent(from, to)
    for _, n in ipairs(adjacentLocations(from or "")) do
        if n == to then return true end
    end
    return false
end

-- Where can a recipe be cooked? The kitchen at Ellie & Luca's House always,
-- and any tile where somebody standing there carries the Portable Crockpot
-- ("Persistent. Allows cooking at any tile (not just kitchen)" — the card was
-- craftable and did nothing). One definition, so the Cook button, the Cook
-- handler and a recipe's own requiresCrockpot flag can never disagree about
-- where the pot is.
CROCKPOT_HOME = "EllieLucaHouse"

function crockpotAt(loc)
    if not loc or loc == "" then return false end
    if loc == CROCKPOT_HOME then return true end
    for c, ch in pairs((gameState and gameState.activeChars) or {}) do
        if ch.location == loc then
            local carried = {}
            safecall(function() carried = getPlayerCarriedObjects(c, ch.name) end, "Crockpot")
            for _, obj in ipairs(carried) do
                if safeHasTag(obj, "M_PORTABLE_CROCKPOT") then return true end
                if safeNickname(obj):lower():find("portable crockpot", 1, true) then return true end
            end
        end
    end
    return false
end

-- P2_STRANGER_WAVES (sportCourtHungerCost): every step that touches a sport
-- court costs +1 Hunger until next Dawn. Shared by all four ways a character
-- changes tile — the ordinary Move, Rayman's free second step, the Dusk
-- scramble and the Secret-Dusk reveal — so the surcharge cannot be walked
-- around by picking a different verb.
function sportCourtSurcharge(from, to)
    if not gameState.ongoingDawnEffects.sportCourtHungerCost then return 0 end
    if not (isSportCourt(from or "") or isSportCourt(to or "")) then return 0 end
    broadcastEvent("warn", "The stranger's road: crossing to or from a sport court costs +1 Hunger.")
    return 1
end

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

-----------------------------------------------------------------------
-- MoonSharp-safe replacements for two standard Lua idioms.
--
-- These exist because of a structural blind spot, not a style preference.
-- The test suite runs the real bundle under real Lua 5.2 (lupa), and TTS runs
-- MoonSharp. Where the two disagree, the suite is green and the game throws —
-- so the ONLY defence is to not write the idiom. Both of these shipped, both
-- reached players, neither was catchable by any runtime test we could write.
-- Guard: tests/test_moonsharp_safety.py. Background: docs/tts-interface.md.
-----------------------------------------------------------------------

-- Trim. `s:match("^%s*(.-)%s*$")` is the standard Lua trim and MoonSharp
-- abandons it with "pattern too complex" once the subject passes a couple of
-- hundred characters. The rulebook has 400- and 600-character paragraphs, so
-- pressing '?' threw before a single help page rendered. find+sub is O(n) and
-- has no backtracking to give up on.
function trim(s)
    s = tostring(s or "")
    local first = s:find("%S")
    if not first then return "" end
    return s:sub(first, s:find("%s*$", first) - 1)
end

-- Distance between two positions, from their x/y/z instead of through the
-- engine's `Vector:distance()`.
--
-- Same rule as the two above: don't write an idiom whose behaviour differs
-- between the runtime the suite uses and the runtime the game uses. What
-- `Object.getPosition()` hands back is engine-provided, and whether it carries
-- Vector's methods is the engine's business — the three callers that matched
-- an object to a position (`doCraft`, `_spawnCraftButtons`, the Clue check)
-- all wrapped the call in a bare pcall, so if it ever came back as a plain
-- table the failure was invisible: `_spawnCraftButtons` reported "No cards in
-- the Market display" to a player looking at five of them.
--
-- Returns nil for anything that isn't two readable positions, so callers skip
-- rather than throw. Arithmetic on three numbers has no such ambiguity.
function objDistance(a, b)
    if type(a) ~= "table" and type(a) ~= "userdata" then return nil end
    if type(b) ~= "table" and type(b) ~= "userdata" then return nil end
    local ok, d = pcall(function()
        local dx = (a.x or 0) - (b.x or 0)
        local dy = (a.y or 0) - (b.y or 0)
        local dz = (a.z or 0) - (b.z or 0)
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    end)
    if ok and type(d) == "number" then return d end
    return nil
end

-- Take the first element of a list. `table.remove(t, 1)` throws in MoonSharp
-- when `t` is EMPTY ("bad argument #1 to 'remove' (position out of bounds)");
-- real Lua 5.2 just returns nil. That is not an edge case — every queue drain
-- reaches the empty case on its final pass, which is why the achievement toast
-- logged an error every single time one unlocked.
function popFirst(list)
    if not list or #list == 0 then return nil end
    return table.remove(list, 1)
end

-----------------------------------------------------------------------
-- Tell anyone still in the Grey seat why nothing they click works.
--
-- TTS refuses every interaction from Grey with its own message: "Grey
-- (Spectator) cannot interact. Click your name in the top right -> Change
-- Color, then click a colored circle." Accurate, and it reads as a bug —
-- because nobody joined AS a spectator. Grey is simply where TTS puts you
-- until you take a colour, so the player sees an error about a spectator that
-- does not exist, three refused clicks, and no way to connect the two. That
-- has now confused a real table twice.
--
-- Spectators are invisible to Player.getPlayers() (it returns seated players
-- only), which is also why every seat-counting loop in this mod cannot see
-- them and the guided setup will happily wait forever on a table of one.
-----------------------------------------------------------------------
function nudgeSpectatorsToSitDown()
    local watchers = {}
    pcall(function() watchers = Player.getSpectators() or {} end)
    for _, p in ipairs(watchers) do
        pcall(function()
            p.print(
                "You are not sitting down yet — Tabletop Simulator has you in the Grey " ..
                "seat, which it calls a spectator. A spectator cannot click anything on " ..
                "the table, pick a character, or take a turn, and every click you make " ..
                "will be refused.\n" ..
                "To join: click your name in the player list (top right), choose Change " ..
                "Color, then click any coloured circle. Which colour does not matter — " ..
                "picking a character sets your final colour during Setup.",
                {1, 0.85, 0.4})
        end)
    end
    return #watchers
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
