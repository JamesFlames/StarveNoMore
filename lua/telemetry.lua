-- telemetry.lua  (design_batch4.md W0 — session instrumentation)
--
-- Playtests need data, not anecdote. This file turns the Week in Review
-- chronicle (batch 1) into a full session record and exports it at game
-- end as a copyable JSON blob. No server, no external calls.
--
-- What gets recorded (all rides gameState.chronicle, so it persists):
--   setup   — player count, roster, path variant, scenario, turn style,
--             difficulty (written by Setup / finalizeGuidedSetup).
--   turns[] — per-turn duration in seconds (the §20.2 turn-structure A/B
--             lives or dies on this; hooked in day_loop.lua).
--   beats   — which batch-1/2/3 moments fired: presses that killed,
--             Signatures used, the Source split, dares taken.

-----------------------------------------------------------------------
-- Beat recording — called from combat.lua / signatures.lua / the dare
-- sites via safecall (a telemetry failure must never break the game).
-----------------------------------------------------------------------
-----------------------------------------------------------------------
-- OPTION UTILIZATION (Design §20.2 item 8) — which of the game's options
-- does anyone actually use?
--
-- [PrinciplesOfGoodBoardGames.md §26] calls this "the single most
-- actionable report a simulator or session log produces", and notes it is
-- the metric most often skipped. This repo was unusually well placed to
-- collect it — a simulator, a session log and a one-click export all
-- already existed — and collected none of it.
--
-- It matters because the design ships 49 Market items, ~20 recipes, 51
-- threat cards, 8 scenarios and 4 trophies, and §19.6 item 3 has the
-- Visitor deck sitting open as a judgement call awaiting playtests when it
-- is substantially a MEASUREMENT question: if Visitors are drawn in 90% of
-- 3-player games and change the outcome, they stay; if they are drawn and
-- ignored, they go. Anything near zero here is a cut candidate under §3's
-- complexity-budget audit.
--
-- Counts, not booleans: "crafted 4 Flashlights" and "crafted 1" are
-- different facts about the same card.
-----------------------------------------------------------------------
function recordUsage(kind, name)
    if not name or name == "" then return end
    local ch = ensureChronicle()
    ch.usage = ch.usage or {}
    ch.usage[kind] = ch.usage[kind] or {}
    ch.usage[kind][tostring(name)] = (ch.usage[kind][tostring(name)] or 0) + 1
end

function recordBeat(kind, value)
    local ch = ensureChronicle()
    ch.beats = ch.beats or { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 }
    local b = ch.beats
    if kind == "pressKill" then
        b.pressKills = (b.pressKills or 0) + 1
    elseif kind == "signature" then
        b.signaturesUsed = b.signaturesUsed or {}
        table.insert(b.signaturesUsed, tostring(value))
    elseif kind == "sourceSplit" then
        b.sourceSplit = true
    elseif kind == "dare" then
        b.daresTaken = (b.daresTaken or 0) + 1
    end
end

-- Setup facts, written once when a game starts (both setup paths call this).
function recordSetupInChronicle()
    local ch = ensureChronicle()
    local roster = {}
    for _, color in ipairs(gameState.turnOrder or {}) do
        local c = gameState.activeChars[color]
        if c then table.insert(roster, c.name) end
    end
    ch.setup = {
        playerCount = gameState.playerCount,
        roster      = roster,
        pathVariant = gameState.pathVariant,
        scenario    = gameState.scenario,
        turnStyle   = gameState.turnStyle,
        difficulty  = gameState.difficulty or "standard",
    }
end

-- Turn-duration bookkeeping (hooked from day_loop.lua).
function markTurnStart()
    gameState.turnStartedAt = os.time()
end

function recordTurnEnd(color)
    local started = gameState.turnStartedAt
    gameState.turnStartedAt = nil
    if not started then return end
    local char = gameState.activeChars[color]
    local ch = ensureChronicle()
    ch.turns = ch.turns or {}
    table.insert(ch.turns, {
        day     = gameState.day,
        name    = char and char.name or tostring(color),
        seconds = math.max(0, os.time() - started),
    })
end

-----------------------------------------------------------------------
-- The session log: chronicle + outcome as one plain, JSON-safe table.
-----------------------------------------------------------------------
function buildSessionLog()
    local ch = ensureChronicle()
    local chars = {}
    for color, c in pairs(gameState.activeChars or {}) do
        table.insert(chars, {
            color = color, name = c.name,
            health = c.health, hunger = c.hunger, sanity = c.sanity,
            down = c.down or false,
            signatureUsed = c.signatureUsed or false,
        })
    end
    table.sort(chars, function(a, b) return (a.name or "") < (b.name or "") end)
    return {
        -- schema 2 adds `usage` (option-utilization, §20.2 item 8).
        -- analyze_sessions.py accepts 1 and 2; a schema-1 log simply has no
        -- utilization data rather than being rejected.
        schema  = 2,
        setup   = ch.setup or {},
        outcome = {
            cause = gameState.gameOverCause,
            day   = gameState.day,
            doom  = gameState.doom,
        },
        finalCharacters = chars,
        days   = ch.days or {},
        kills  = ch.kills or {},
        meals  = ch.meals or {},
        turns  = ch.turns or {},
        beats  = ch.beats or {},
        usage  = ch.usage or {},
        peakDoom = ch.peakDoom,
        downs = ch.downs or 0,
        revives = ch.revives or 0,
    }
end

function exportSessionLog()
    return JSON.encode(buildSessionLog())
end

-- Week in Review button: dump the log somewhere copyable. The Notes panel
-- holds arbitrary text and survives chat scroll; chat gets a short pointer.
function onCopySessionLog(player, value, id)
    local json = nil
    safecall(function() json = exportSessionLog() end, "Telemetry")
    if not json then
        broadcastToColor("Could not build the session log.", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function() Notes.setNotes(json) end, "Telemetry")
    broadcastEvent("proc", "Session log written to the Notes panel (top menu > Notes). Copy it into the playtest tracker.")
end
