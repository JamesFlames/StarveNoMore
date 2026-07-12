-- tts_stub.lua — a headless stand-in for the Tabletop Simulator scripting API.
-- Loaded (by tests/test_lua_runtime.py, via lupa/Lua 5.2) BEFORE the game's
-- concatenated bundle so the bundle runs outside TTS.
--
-- Philosophy: globals are strict (an undefined global function is still an
-- error — that's a bug we want to catch), but fake *objects* are permissive
-- (TTS objects have a huge API; unknown methods become recorded no-ops).
--
-- ==========================================================================
-- DIVERGENCE LEDGER — known ways this stub does NOT behave like real TTS.
-- Read this before trusting a green test that leans on the physical layer.
--  * Wait.time ignores delays and repetition counts: TTS.flushWaits() runs
--    every queued callback immediately, in scheduling order, until quiescent.
--    Timing-dependent behavior (timeouts, delays between locations) is
--    untestable here.
--  * takeObject ignores `rotation` and `smooth`; only `position`, `guid`,
--    and `callback_function` are honored. Face-up/face-down state is not
--    modeled on taken cards.
--  * Container getObjects() entries carry `tags` copied from the contained
--    spec (real TTS also includes them in recent builds) — but entries for
--    specs without an explicit guid get an index-based one, which real TTS
--    never does. Give contained specs explicit guids when identity matters.
--  * Physics, snap points, collisions, and object bounds are fake:
--    getBoundsNormalized() always reports a 4x1x4 box at the object's
--    position, so radius/area checks pass more easily than on a real table.
--  * Player color/seat behavior is minimal: TTS.seated lists seated colors;
--    every player is admin; hands are plain lists set via TTS.setHand.
--  * UI.* records attributes/visibility but never lays anything out —
--    nothing can be asserted about on-screen geometry or wrapping.
--  * Audio (MusicPlayer) is a silent no-op recorder.
-- Fixed divergences (previously cost debugging time, now faithful):
--  * Object GUIDs come from a counter, NOT math.random — stubbed dice
--    sequences are never consumed by object creation.
--  * takeObject honors params.guid, matching real TTS.
-- ==========================================================================
--
-- The TTS table is the test-facing control surface:
--   TTS.addObject{tags={...}, position={x,y,z}, nickname=..., ...} -> obj
--   TTS.setHand(color, {obj, ...})
--   TTS.flushWaits()          -- run everything queued via Wait.time
--   TTS.broadcasts            -- every broadcast/print message, in order
--   TTS.ui                    -- recorded UI state (visible/attrs)
--   TTS.reset()               -- clear world/hands/broadcasts/UI/waits

TTS = {}

-- ---------------------------------------------------------------------------
-- Vector (supports the arithmetic the game uses: v + v, v - v)
-- ---------------------------------------------------------------------------
local VectorMT
local function newVector(x, y, z)
    if type(x) == "table" then
        x, y, z = x.x or x[1] or 0, x.y or x[2] or 0, x.z or x[3] or 0
    end
    return setmetatable({ x = x or 0, y = y or 0, z = z or 0 }, VectorMT)
end
VectorMT = {
    __add = function(a, b) return newVector(a.x + b.x, a.y + b.y, a.z + b.z) end,
    __sub = function(a, b) return newVector(a.x - b.x, a.y - b.y, a.z - b.z) end,
    __mul = function(a, k) return newVector(a.x * k, a.y * k, a.z * k) end,
    __tostring = function(v) return "(" .. v.x .. "," .. v.y .. "," .. v.z .. ")" end,
    __index = {
        copy = function(v) return newVector(v.x, v.y, v.z) end,
        setAt = function(v, k, val) v[k] = val; return v end,
    },
}
Vector = setmetatable({}, { __call = function(_, x, y, z) return newVector(x, y, z) end })
Vector.new = newVector

-- ---------------------------------------------------------------------------
-- Fake world objects
-- ---------------------------------------------------------------------------
local function makeObject(spec)
    spec = spec or {}
    local o = {}
    local tags = {}
    for _, t in ipairs(spec.tags or {}) do tags[t] = true end
    local state = {
        position = newVector(spec.position or { 0, 1, 0 }),
        rotation = newVector(spec.rotation or { 0, 0, 0 }),
        nickname = spec.nickname or "",
        description = spec.description or "",
        gmnotes = spec.gmnotes or "",
        name = spec.name or "Custom_Model",
        locked = false,
        value = spec.value or 0,
        contained = spec.contained or {},   -- for bags/decks: list of specs
        buttons = {},
        calls = {},                          -- method-call log for assertions
    }
    o.__state = state

    local function record(method, ...)
        table.insert(state.calls, { method = method, args = { ... } })
    end

    o.hasTag = function(t) return tags[t] == true end
    o.addTag = function(t) tags[t] = true; return true end
    o.removeTag = function(t) tags[t] = nil; return true end
    o.getTags = function()
        local out = {}
        for t in pairs(tags) do out[#out + 1] = t end
        return out
    end
    o.getPosition = function() return state.position:copy() end
    o.setPosition = function(p) state.position = newVector(p); record("setPosition", p); return true end
    o.setPositionSmooth = function(p) state.position = newVector(p); record("setPositionSmooth", p); return true end
    o.getRotation = function() return state.rotation:copy() end
    o.setRotation = function(r) state.rotation = newVector(r); record("setRotation", r); return true end
    o.setRotationSmooth = function(r) state.rotation = newVector(r); record("setRotationSmooth", r); return true end
    o.getNickname = function() return state.nickname end
    o.setNickname = function(n) state.nickname = n; return true end
    o.getDescription = function() return state.description end
    o.setDescription = function(d) state.description = d; return true end
    o.getGMNotes = function() return state.gmnotes end
    o.setGMNotes = function(n) state.gmnotes = n; return true end
    o.getName = function() return state.name end
    o.setName = function(n) state.name = n; return true end
    o.setLock = function(v) state.locked = v; return true end
    o.getLock = function() return state.locked end
    o.getValue = function() return state.value end
    o.setValue = function(v) state.value = v; return true end
    o.getQuantity = function() return #state.contained end
    o.getObjects = function()
        local out = {}
        for i, s in ipairs(state.contained) do
            local tagsCopy = {}
            for _, t in ipairs(s.tags or {}) do tagsCopy[#tagsCopy + 1] = t end
            out[i] = { name = s.nickname or "", nickname = s.nickname or "",
                       guid = s.guid or tostring(i), index = i - 1, tags = tagsCopy }
        end
        return out
    end
    o.takeObject = function(params)
        params = params or {}
        -- guid-aware, like real TTS: pull the named object if asked.
        local idx = 1
        if params.guid then
            for i, s in ipairs(state.contained) do
                if (s.guid or tostring(i)) == params.guid then idx = i; break end
            end
        end
        local spec2 = table.remove(state.contained, idx)
        local taken = makeObject(spec2 or {})
        if params.position then taken.setPosition(params.position) end
        table.insert(TTS.world, taken)
        if params.callback_function then params.callback_function(taken) end
        return taken
    end
    o.putObject = function(other)
        record("putObject", other)
        -- remove from world if present
        for i, w in ipairs(TTS.world) do
            if w == other then table.remove(TTS.world, i); break end
        end
        table.insert(state.contained, { nickname = other.getNickname() })
        return o
    end
    o.destruct = function()
        for i, w in ipairs(TTS.world) do
            if w == o then table.remove(TTS.world, i); break end
        end
        return true
    end
    o.createButton = function(params) table.insert(state.buttons, params); return true end
    o.editButton = function(params)
        local idx = (params.index or 0) + 1
        if state.buttons[idx] then
            for k, v in pairs(params) do state.buttons[idx][k] = v end
        end
        return true
    end
    o.clearButtons = function() state.buttons = {}; return true end
    o.getButtons = function() return state.buttons end
    o.getBoundsNormalized = function()
        return { center = state.position:copy(), size = newVector(4, 1, 4), offset = newVector(0, 0, 0) }
    end
    o.getSnapPoints = function() return spec.snapPoints or {} end
    o.positionToWorld = function(p) return newVector(p) end
    o.positionToLocal = function(p) return newVector(p) end
    o.highlightOn = function(...) record("highlightOn", ...); return true end
    o.highlightOff = function(...) record("highlightOff", ...); return true end
    o.flip = function() record("flip"); return true end
    o.shuffle = function() record("shuffle"); return true end
    o.deal = function(...) record("deal", ...); return true end
    o.randomize = function() record("randomize"); return true end
    o.setColorTint = function(...) record("setColorTint", ...); return true end
    o.setScale = function(...) record("setScale", ...); return true end
    o.getScale = function() return newVector(1, 1, 1) end
    o.setVar = function(...) record("setVar", ...); return true end
    o.getVar = function() return nil end
    o.call = function(...) record("call", ...); return nil end
    o.clone = function() return makeObject(spec) end
    -- Counter-based GUIDs: never consumes math.random (see divergence ledger).
    TTS.guidCounter = (TTS.guidCounter or 0) + 1
    o.guid = spec.guid or ("stub" .. TTS.guidCounter)
    o.type = spec.type or "Card"   -- TTS .type property ("Card", "Deck", ...)
    o.interactable = true
    o.UI = { setAttribute = function() return true end, show = function() return true end, hide = function() return true end }

    -- Permissive fallback: unknown methods become recorded no-ops.
    setmetatable(o, {
        __index = function(_, key)
            return function(...) record(key, ...); return nil end
        end,
    })
    return o
end

-- ---------------------------------------------------------------------------
-- World + global object API
-- ---------------------------------------------------------------------------
function TTS.reset()
    TTS.world = {}
    TTS.hands = {}
    TTS.broadcasts = {}
    TTS.ui = { visible = {}, attrs = {} }
    TTS.waits = {}
    TTS.waitId = 0
    TTS.seated = { "White" }
end
TTS.reset()

TTS.makeObject = makeObject

function TTS.addObject(spec)
    local o = makeObject(spec)
    table.insert(TTS.world, o)
    return o
end

function TTS.setHand(color, objs)
    TTS.hands[color] = objs
end

function getAllObjects()
    local out = {}
    for i, o in ipairs(TTS.world) do out[i] = o end
    return out
end

function getObjectsWithTag(tag)
    local out = {}
    for _, o in ipairs(TTS.world) do
        if o.hasTag(tag) then out[#out + 1] = o end
    end
    return out
end

function getObjectFromGUID(guid)
    for _, o in ipairs(TTS.world) do
        if o.guid == guid then return o end
    end
    return nil
end

function spawnObject(params)
    local o = makeObject({ name = params and params.type or "Spawned" })
    if params and params.position then o.setPosition(params.position) end
    table.insert(TTS.world, o)
    if params and params.callback_function then params.callback_function(o) end
    return o
end

function spawnObjectJSON(params)
    return spawnObject(params)
end

function destroyObject(o)
    if o and o.destruct then o.destruct() end
end

-- ---------------------------------------------------------------------------
-- Messaging
-- ---------------------------------------------------------------------------
local function note(kind, msg, target)
    table.insert(TTS.broadcasts, { kind = kind, message = tostring(msg), target = target })
end
function broadcastToAll(msg, _color) note("broadcastToAll", msg) end
function broadcastToColor(msg, color, _tint) note("broadcastToColor", msg, color) end
function printToAll(msg, _color) note("printToAll", msg) end
function printToColor(msg, color, _tint) note("printToColor", msg, color) end
function log(_msg, _label, _tags) end

-- ---------------------------------------------------------------------------
-- Wait (queued; tests drive time by calling TTS.flushWaits())
-- ---------------------------------------------------------------------------
Wait = {}
function Wait.time(fn, _delay, _repetitions)
    TTS.waitId = TTS.waitId + 1
    TTS.waits[TTS.waitId] = fn
    return TTS.waitId
end
Wait.frames = Wait.time
function Wait.condition(fn, _cond, _timeout, _timeoutFn)
    TTS.waitId = TTS.waitId + 1
    TTS.waits[TTS.waitId] = fn
    return TTS.waitId
end
function Wait.stop(id)
    TTS.waits[id] = nil
    return true
end

function TTS.flushWaits()
    -- Run rounds until quiescent (callbacks may schedule more), capped.
    -- Within a round, callbacks run in scheduling (id) order so chained
    -- sequences like the self-test behave FIFO; delays are ignored.
    for _round = 1, 100 do
        local ids = {}
        for id in pairs(TTS.waits) do ids[#ids + 1] = id end
        if #ids == 0 then return end
        table.sort(ids)
        for _, id in ipairs(ids) do
            local fn = TTS.waits[id]
            TTS.waits[id] = nil
            if fn then fn() end
        end
    end
end

-- ---------------------------------------------------------------------------
-- UI (records everything so tests can assert)
-- ---------------------------------------------------------------------------
UI = {}
function UI.show(id) TTS.ui.visible[id] = true; return true end
function UI.hide(id) TTS.ui.visible[id] = false; return true end
function UI.setAttribute(id, attr, value)
    TTS.ui.attrs[id] = TTS.ui.attrs[id] or {}
    TTS.ui.attrs[id][attr] = value
    return true
end
function UI.setAttributes(id, attrs)
    for k, v in pairs(attrs) do UI.setAttribute(id, k, v) end
    return true
end
function UI.getAttribute(id, attr)
    return TTS.ui.attrs[id] and TTS.ui.attrs[id][attr] or ""
end
function UI.setValue(id, v) return UI.setAttribute(id, "text", v) end
function UI.getValue(id) return UI.getAttribute(id, "text") end
function UI.setClass(id, v) return UI.setAttribute(id, "class", v) end
function UI.setXml(_xml) return true end
function UI.getXml() return "" end
function UI.setCustomAssets(assets) TTS.ui.customAssets = assets; return true end
function UI.getCustomAssets() return TTS.ui.customAssets or {} end

-- ---------------------------------------------------------------------------
-- Players
-- ---------------------------------------------------------------------------
local function makePlayer(color)
    local seated = false
    for _, c in ipairs(TTS.seated) do
        if c == color then seated = true end
    end
    return {
        color = color,
        seated = seated,
        steam_name = "Test_" .. color,
        admin = true,
        host = (color == "White"),
        getHandObjects = function() return TTS.hands[color] or {} end,
        lookAt = function(_params) return true end,
        pingTable = function(_pos) return true end,
        print = function(msg) note("printToColor", msg, color) end,
        broadcast = function(msg) note("broadcastToColor", msg, color) end,
        -- Reseat: swaps this seat's entry in TTS.seated, like the real
        -- Player.changeColor (fails if this player isn't seated). Hands
        -- are not migrated — the bundle only reseats before hands exist.
        changeColor = function(newColor)
            for i, c in ipairs(TTS.seated) do
                if c == color then
                    TTS.seated[i] = newColor
                    return true
                end
            end
            return false
        end,
    }
end

Player = setmetatable({
    getPlayers = function()
        local out = {}
        for _, c in ipairs(TTS.seated) do out[#out + 1] = makePlayer(c) end
        return out
    end,
    getAvailableColors = function() return { "White", "Red", "Yellow", "Green", "Blue" } end,
}, {
    __index = function(_, color)
        if type(color) == "string" then return makePlayer(color) end
        return nil
    end,
})

-- ---------------------------------------------------------------------------
-- Misc singletons the bundle touches
-- ---------------------------------------------------------------------------
Global = { UI = UI, setVar = function() return true end, getVar = function() return nil end, call = function() return nil end }
Turns = { enable = false, order = {}, turn_color = "" }
Notes = {
    setNotebookTabs = function(_tabs) return true end,
    getNotebookTabs = function() return {} end,
    setNotes = function(_s) return true end,
    getNotes = function() return "" end,
}
MusicPlayer = {
    setCurrentAudioclip = function(_clip) return true end,
    play = function() return true end,
    pause = function() return true end,
    skipForward = function() return true end,
    playlistIndex = -1,
}
Lighting = {
    LightIntensity = 0.54,
    AmbientIntensity = 1.3,
    AmbientSkyColor = { r = 0.5, g = 0.5, b = 0.5 },
    AmbientEquatorColor = { r = 0.5, g = 0.5, b = 0.5 },
    AmbientGroundColor = { r = 0.5, g = 0.5, b = 0.5 },
    apply = function() return true end,
    setAmbientSkyColor = function() return true end,
}
Physics = { cast = function() return {} end }

function startLuaCoroutine(_owner, name)
    local fn = _G[name]
    if fn then coroutine.wrap(fn)() end
    return true
end

-- JSON is injected from the Python side (tests/test_lua_runtime.py) using the
-- real json module, so encode/decode behave like TTS's implementation.
