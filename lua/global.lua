-- global.lua  (F.1 — Global script skeleton + F.14 save/load + F.15 broadcast)

-----------------------------------------------------------------------
-- Game State (the single source of truth, persisted via onSave)
-----------------------------------------------------------------------
-- Bump when gameState gains fields a restored save must have; the actual
-- defaults live in ONE place: migrateGameState() below.
SCHEMA_VERSION = 3

gameState = {
    schemaVersion = SCHEMA_VERSION,
    day          = 1,
    phase        = 1,         -- 1..4 (Dusk of Week / Strange Days / Long Nights / Final Hours)
    doom         = 0,
    started      = false,
    welcomed     = false,
    subPhase     = "PreGame",  -- PreGame / Dawn / Day / Dusk / Night / Tick
    activeColor  = nil,        -- whose turn during Day
    turnOrder    = {},         -- ordered list of seated colors
    turnIndex    = 0,
    playerCount  = 0,
    pathVariant  = nil,
    turnStyle    = "full",     -- "full" (3 actions per turn) | "rotate" (1 action per visit — §11.2 variant)
    actedThisVisit = false,    -- rotation variant: has the active player acted since gaining priority?
    combatContext = nil,       -- transient live-combat state for Press the Attack (§12.5); nil when no fight is open
    scenario     = nil,        -- active Scenario id (SC_*, optional variant — §17.3) or nil
    scenarioFlags = {},        -- rule flags set by the active Scenario
    dayLog       = {},
    activeDawn   = nil,        -- {id, title, immediate, ongoing, severity}
    ongoingDawnEffects = {},   -- keyed by effect name

    activeChars = {
        -- Populated at setup: [color] = {name, health, maxHealth, hunger, maxHunger,
        --   sanity, maxSanity, actionsLeft, down, briefed, location}
    },

    -- Authoritative held resources per seat colour (ensurePlayerResources,
    -- helpers.lua). Physical tokens are decoration; THIS is the count the
    -- economy reads. [color] = {Wood, Metal, Cloth, Provisions, EnergyDrink, Battery}
    resources = {},

    -- One-fire-per-day flags so urgent auto-broadcasts (Down, stat-below-3,
    -- James-no-Energy-Drink) don't spam the chat. Cleared in BeginDay() at Dawn.
    dailyAlerts = {
        -- [color] = { downHint = true, low_hunger = true, ... }
    },

    -- Idle-detection nudge state (see day_loop.lua).
    lastInteractionAt    = 0,
    idleNudgedThisTurn   = false,

    -- chronicle: the Week in Review record (design_batch1.md §3) — a
    -- persistent history across all 7 days (NOT wiped with dayLog each Dawn),
    -- narrated at game end. Deliberately NOT declared here: it is built on
    -- first use by ensureChronicle() (ui_week_review.lua), which is the one
    -- constructor for its shape. Both setup paths null it for a new game, so
    -- a literal here would only be a second copy of that shape waiting to
    -- drift. Every read guards with ensureChronicle() or `or {}`.
}

-----------------------------------------------------------------------
-- Character base stats
-----------------------------------------------------------------------
CHARACTER_STATS = {
    James  = {health=8,  hunger=6,  sanity=10},
    Coco   = {health=6,  hunger=8,  sanity=12},
    Rayman = {health=12, hunger=10, sanity=6},
    Ellie  = {health=8,  hunger=10, sanity=8},
    Luca   = {health=7,  hunger=8,  sanity=10},
}

-- A player's seat colour is determined by the character they pick: the
-- guided setup reseats each player onto their character's colour
-- (reseatPlayerForCharacter, ui_setup.lua), and the bare Setup() assigns
-- characters by the same scheme. Standee holders, roster names and hand
-- zones all match these colours. Mirrored by STANDEE_COLORS in
-- scripts/build_save.py.
CHARACTER_COLORS = {
    James  = "Blue",
    Coco   = "White",
    Rayman = "Green",
    Ellie  = "Yellow",
    Luca   = "Red",
}

CHARACTER_HOMES = {
    James  = "JamesHouse",
    Rayman = "RaymanHouse",
    Ellie  = "EllieLucaHouse",
    Luca   = "EllieLucaHouse",
    Coco   = nil,
}

-----------------------------------------------------------------------
-- Gather yields per location (Design §7-8). A Gather draws one resource
-- picked uniformly from this list, so Provisions come up twice as often at
-- Ellie & Luca's House. These are the six canonical resource types
-- (the token/bag tags), so giveResource can pull straight from a bag.
-- Mirrors scripts/simulate_balance.py's YIELDS (lower-cased there);
-- tests/test_sim.py::test_location_yields_match guards the two.
-----------------------------------------------------------------------
-- The five tiles in a fixed order, for the passes that must visit every
-- location (LOCATION_YIELDS is a hash, so it has none). Iterating it instead
-- of pairs() keeps the Rules panel from reshuffling between refreshes.
LOCATION_ORDER = {
    "JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt",
}

LOCATION_YIELDS = {
    JamesHouse      = {"EnergyDrink", "Battery", "Provisions"},
    RaymanHouse     = {"Metal", "Battery", "Provisions"},
    EllieLucaHouse  = {"Provisions", "Provisions", "Cloth"},
    BasketballCourt = {"Wood", "Metal", "Cloth"},
    BadmintonCourt  = {"Cloth", "Wood", "Metal"},
}

-----------------------------------------------------------------------
-- Per-location defence, Design §7.1-7.5 ("Defense: +1 (the nets help)",
-- "-1 (open court, exposed)"). MIRRORS the `defense` column of
-- content/locations.csv; tests/test_cross_refs.py guards the mirror.
--
-- Read by applyCounterAttack (combat_resolve.lua): a positive value is that
-- many dice the defenders roll to block incoming counter hits (The Net's
-- "+1 die when defending"), a negative one is that many EXTRA dice the
-- threat rolls, because being caught in the open is the same rule pointed
-- the other way. Two UI strings — the Badminton Court's board tooltip and
-- its What-now hint — have promised this since before it existed.
-----------------------------------------------------------------------
LOCATION_DEFENSE = {
    JamesHouse      = 0,
    RaymanHouse     = 1,   -- the Garage: lots of cover
    EllieLucaHouse  = 0,
    BasketballCourt = -1,  -- open court, exposed
    BadmintonCourt  = 1,   -- The Net: the nets entangle attackers
}

ACTIONS_PER_TURN = 3

-----------------------------------------------------------------------
-- Doom thresholds (Design §15.2). checkDoomThresholds (day_loop.lua) and
-- getNextDoomThreshold (ui_banner.lua) read this table; the balance sim
-- mirrors it and tests/test_sim.py enforces the mirror.
-----------------------------------------------------------------------
DOOM_THRESHOLDS = {
    night          = 10,   -- night threat draws +1 everywhere
    scarcity       = 15,   -- crafts cost +1 extra resource
    tick           = 20,   -- everyone -1 extra Sanity at Tick
    anyPhaseBosses = 25,   -- Nothing Left to Lose (the name is historical:
                           -- the "bosses in any phase" half described a
                           -- mechanic the mod never had — one un-phased Threat
                           -- deck, bosses placed by scripted Dawn cards — and
                           -- was cut from the player-facing text in 2026-07)
}

-----------------------------------------------------------------------
-- Cleanse (Design §15.3): the communal ritual. doCleanse (tick_victory.lua)
-- and the cleanse highlight (ui_actionbar.lua) read these; sim-mirrored.
-----------------------------------------------------------------------
CLEANSE_COST = { Wood = 1, Cloth = 1, Battery = 1, EnergyDrink = 1 }
CLEANSE_REDUCTION = 2

-- Revival (Design §16.4): the reviver pays this much Health on top of the
-- Telltale Heart. Read by reviveCharacter (tick_victory.lua) and by the
-- Revive button's precondition + tooltip (ui_actionbar_situational.lua) —
-- the number is quoted to the player before they commit, so it lives here
-- rather than inline in the one that happens to charge it.
REVIVE_HEALTH_COST = 2

-- How many Telltale Hearts can exist at once (Design §13.4). Checked by
-- doCook before it charges the recipe's 2 Health, and again by
-- cookTelltaleHeart itself.
HEART_SUPPLY_MAX = 5

-----------------------------------------------------------------------
-- Difficulty and length are SEPARATE DIALS (Design §17.2).
--
-- They used to be the same one: "Easy" *was* "Long Weekend" — 3 days
-- instead of 7 with the Doom track halved. That conflation is costly here
-- in a way it isn't in most games, because the arc IS the design: §14
-- maps seven days onto Jo-Ha-Kyu with four phases, three bosses and a
-- scripted Last Dawn; §14.1 tunes boss rewards to "rescue the week"; §6.7
-- tunes all five Signatures for Days 5-7. A group on the old Easy got
-- Phase 1 and half of Phase 2 — they never met the Eye of Terror, never
-- fought the Source, never reached Doom 25's Nothing Left to Lose, and
-- never used a Signature at the moment it was designed for. The easy mode
-- omitted everything the design is proudest of.
--
-- So there are now two independent axes:
--   * LENGTH — `days` (+ phaseForDay). Long Weekend is a SHORT mode: the
--     teaching format and the weeknight option, not a difficulty setting.
--   * DIFFICULTY — doomLimit / doomDelta / sourceHP / minPhase, all on the
--     full 7-day arc, so every difficulty delivers the whole week.
--
--   story     — the full arc, gentler: Doom track to 35, Source at 6 HP.
--               This is the easy mode a first group should meet.
--   standard  — the tuned 7-day week (§20.1 calibration).
--   nightmare — Doom rate +1 in every phase; no Phase 1 (starts on
--               Strange Days).
--   weekend   — 3 days. A length, offered alongside the difficulties
--               because the setup UI has one selector; still gets the
--               Last Dawn on its final day.
--
-- Story, Nightmare and Long Weekend are derived offsets from the tuned
-- Standard, not separately balanced — the simulator brackets the ordering
-- and the table settles the magnitude (§26).
-----------------------------------------------------------------------
DIFFICULTY_PARAMS = {
    story     = { label = "Story",        days = 7, doomLimit = 35, doomDelta = 0,
                  sourceHP = 6, sourceSplitHP = 4 },
    standard  = { label = "Standard",     days = 7, doomLimit = 30, doomDelta = 0 },
    -- Nightmare's Doom surcharge is PER PHASE, not flat. A flat +1 measured at
    -- 0-6% for the best lines — not "hard", unwinnable — because it compounds
    -- from Day 1 against an already-responsive clock (§15.1). Loading it onto
    -- Phases 3-4 keeps the early week merely tense and makes the back half the
    -- part that kills you, which is where §14's arc wants the pressure anyway.
    -- The tougher Source is the second half of the knob; see §17.2 for the
    -- measured ladder.
    nightmare = { label = "Nightmare",    days = 7, doomLimit = 30,
                  doomDelta = {0, 0, 1, 1}, sourceHP = 9,
                  minPhase = 2 },
    weekend   = { label = "Long Weekend", days = 3, doomLimit = 15, doomDelta = 0,
                  phaseForDay = {1, 1, 2} },
}

function getDifficulty()
    return DIFFICULTY_PARAMS[gameState.difficulty or "standard"] or DIFFICULTY_PARAMS.standard
end

function getTotalDays() return getDifficulty().days end
function getDoomLimit() return getDifficulty().doomLimit end

-- The Source's HP is a difficulty knob (§20.1's first sanctioned one), so it
-- must be read through here and never off the SOURCE_MAX_HP constant — that
-- constant is Standard's value and the base the others offset from.
function getSourceMaxHP()
    return getDifficulty().sourceHP or SOURCE_MAX_HP or 8
end

-- The split threshold (§12.6) moves with the HP pool, or the beat loses its
-- "before" phase: a 6 HP Source against a fixed threshold of 5 would split on
-- the first point of damage, which reads as an opening rather than a climax.
-- Story scales it to 4 so there are still two damaging turns before the adds.
function getSourceSplitHP()
    return getDifficulty().sourceSplitHP or SOURCE_SPLIT_HP or 5
end

-- Phase→day mapping: which phase deck is active on which day
function getPhaseForDay(day)
    local diff = getDifficulty()
    if diff.phaseForDay then
        return diff.phaseForDay[math.min(day, #diff.phaseForDay)]
    end
    local phase
    if day <= 2 then phase = 1
    elseif day <= 4 then phase = 2
    elseif day <= 5 then phase = 3
    else phase = 4 end
    if diff.minPhase then phase = math.max(diff.minPhase, phase) end
    return phase
end

-- Doom rate per phase, scaled by player count (Design §15.6).
-- Retuned 2026-07 alongside uncapped boss festering and the removal of
-- boss arrival Doom: the fixed clock is gentler because far more of the
-- pressure is now responsive (festering bosses, threats, Downs).
-- Phase 4 at the 4-player baseline raised 2 -> 3 in the batch-5 calibration
-- (§20.1's third ordered knob): the Last Nerve valve had put the best lines
-- at 50-52%, above §20.2's 40-50% band, and this is the smallest sanctioned
-- change that lands them back in it. Phase 3 as well overshoots to ~22%.
DOOM_RATES = {
    [3] = {1, 1, 1, 1},
    [4] = {1, 1, 1, 3},
    [5] = {1, 1, 2, 2},
}

-- A difficulty's doomDelta is EITHER a flat number (Story/Standard/Long
-- Weekend: 0) OR a per-phase table (Nightmare: {0,0,1,1}). Per-phase exists
-- because a flat surcharge is the wrong shape for a difficulty setting — it
-- taxes the exploratory half of the week that §14 wants calm, and compounds
-- into an unwinnable clock long before the arc reaches its climax.
function getDoomDelta(phase)
    local d = getDifficulty().doomDelta
    if type(d) == "table" then return d[phase] or 0 end
    return d or 0
end

function getDoomRate()
    local pc = math.max(3, math.min(5, gameState.playerCount))
    local rates = DOOM_RATES[pc] or DOOM_RATES[4]
    local phase = gameState.phase
    return (rates[phase] or 1) + getDoomDelta(phase)
end

-- Human-readable Doom surcharge for a difficulty, for the setup announcement
-- and the Rules panel. Exists because doomDelta has two shapes and every
-- caller that assumed "number" was a latent crash.
function describeDoomDelta(diff)
    local d = (diff or getDifficulty()).doomDelta
    if type(d) == "table" then
        local hit = {}
        for phase = 1, 4 do
            if (d[phase] or 0) > 0 then
                table.insert(hit, "Phase " .. phase .. " +" .. d[phase])
            end
        end
        if #hit == 0 then return "" end
        return ", Doom rate " .. table.concat(hit, " / ")
    end
    if (d or 0) > 0 then return ", Doom rate +" .. d .. " every phase" end
    return ""
end

-----------------------------------------------------------------------
-- Broadcast helpers (F.15 + G.8 prep)
-----------------------------------------------------------------------
BROADCAST_COLORS = {
    damage = {1, 0.4, 0.4},
    warn   = {1, 0.85, 0.4},
    gain   = {0.5, 1, 0.5},
    phase  = {0.5, 0.9, 1},
    proc   = {0.7, 0.7, 0.7},
}

function broadcastEvent(category, message)
    local color = BROADCAST_COLORS[category] or {1, 1, 1}
    broadcastToAll(message, color)
    table.insert(gameState.dayLog, {category=category, message=message})
    -- Every public message also lands in the persistent Message Log panel
    -- (ui_msglog.lua) — broadcasts fade too fast to read.
    if logMessage then pcall(function() logMessage(category, message) end) end
end

-----------------------------------------------------------------------
-- Lifecycle (F.1 + F.14)
-----------------------------------------------------------------------
-----------------------------------------------------------------------
-- Save migration: every field a restored save might be missing gets its
-- default HERE, in one place, instead of `or {}` scattered per read site.
-- An old mid-campaign save must load and play through a full day.
-----------------------------------------------------------------------
function migrateGameState()
    local gs = gameState
    -- Scalars first. These used to exist only in the literal above, which
    -- meant the Restart path (ui_controls.lua) had to hand-copy them and an
    -- old save missing one would read nil. `x = x or default` is safe for
    -- every field here: none has a meaningful `false`/`nil` value that a
    -- default would wrongly overwrite (the booleans below use the explicit
    -- nil test for exactly that reason).
    gs.day                  = gs.day or 1
    gs.phase                = gs.phase or 1        -- 1..4 (Dusk of Week … Final Hours)
    gs.doom                 = gs.doom or 0
    gs.subPhase             = gs.subPhase or "PreGame"  -- PreGame/Dawn/Day/Dusk/Night/Tick
    gs.turnIndex            = gs.turnIndex or 0
    gs.playerCount          = gs.playerCount or 0
    gs.lastInteractionAt    = gs.lastInteractionAt or 0
    if gs.started == nil then gs.started = false end
    if gs.welcomed == nil then gs.welcomed = false end
    if gs.actedThisVisit == nil then gs.actedThisVisit = false end
    if gs.idleNudgedThisTurn == nil then gs.idleNudgedThisTurn = false end
    -- Deliberately absent (nil IS the default, so declaring them would only
    -- create keys with no meaning): activeColor, pathVariant, combatContext,
    -- scenario, activeDawn, chronicle.
    gs.ongoingDawnEffects   = gs.ongoingDawnEffects or {}
    gs.activeChars          = gs.activeChars or {}
    gs.dailyAlerts          = gs.dailyAlerts or {}
    gs.turnOrder            = gs.turnOrder or {}
    gs.dayLog               = gs.dayLog or {}
    gs.scenarioFlags        = gs.scenarioFlags or {}
    gs.bossHP               = gs.bossHP or {}               -- batch 2
    gs.pendingSanityPenalty = gs.pendingSanityPenalty or {} -- batch 2
    gs.loudSignature        = gs.loudSignature or {}        -- batch 2
    gs.turnStyle            = gs.turnStyle or "full"
    gs.difficulty           = gs.difficulty or "standard"   -- batch 4
    gs.raymanTilesMovedToday = gs.raymanTilesMovedToday or 0 -- batch 4
    gs.threatDamage         = gs.threatDamage or {}          -- schema 3: chip damage on threat cards
    gs.messageLog           = gs.messageLog or {}            -- Message Log panel (ui_msglog.lua)
    gs.resources            = gs.resources or {}             -- authoritative held resources per colour
    gs.haunted              = gs.haunted or {}               -- who is Haunted today + who witnessed it (§10.1)
    gs.cluesFound           = gs.cluesFound or {}            -- Truth Run (§16.2): which of the 3 Clues are in hand
    gs.clueCount            = gs.clueCount or 0
    gs.cluesSurfaced        = gs.cluesSurfaced or 0          -- how many the refill seam has put on offer
    gs.openingOffered       = gs.openingOffered or {}        -- Day-1 opening suggestion, once per player (§15.9)
    gs.duskPending          = gs.duskPending or {}           -- banked secret Dusk moves (§11.3 variant)
    gs.driftedThisRound     = gs.driftedThisRound or {}      -- ghost drift, once per round (§16.4)
    gs.sledUsedThisTurn     = gs.sledUsedThisTurn or {}      -- Antler Sled trophy, once per turn (trophies.lua)
    -- Deliberately absent: lastMarketRefillDay. nil means "never restocked",
    -- which is exactly what Strict Rationing's first refill needs to see.
    gs.missingAlly          = gs.missingAlly or nil          -- P3_ALLY_MISSING: who gets today's +1 action
    if gs.duskSecret == nil then gs.duskSecret = false end   -- §11.3 A/B variant
    if gs.solo == nil then gs.solo = false end               -- §20.3 solo mode
    -- The achievement vault (achievements.lua). It spans games rather than
    -- belonging to one, which is why Restart preserves it — but it still
    -- rides gameState, because onSave/onLoad is the only store a TTS mod has.
    gs.achievements         = gs.achievements or {}
    gs.achievements.unlocked = gs.achievements.unlocked or {}
    gs.achievements.games   = gs.achievements.games or 0
    for _, char in pairs(gs.activeChars) do
        if char.signatureUsed == nil then char.signatureUsed = false end -- batch 2
    end
    -- Chronicle: lazily created; older chronicles gain the telemetry fields.
    if gs.chronicle then
        gs.chronicle.setup = gs.chronicle.setup or {}
        gs.chronicle.turns = gs.chronicle.turns or {}
        gs.chronicle.beats = gs.chronicle.beats or
            { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 }
        gs.chronicle.usage = gs.chronicle.usage or {}   -- option utilization (§20.2 item 8)
    end
    gs.schemaVersion = SCHEMA_VERSION
end

function onLoad(savedState)
    if savedState and savedState ~= "" then
        -- pcall: a corrupt saved state must not kill the whole mod script —
        -- fall back to a fresh game and say so.
        local ok, decoded = pcall(function() return JSON.decode(savedState) end)
        if ok and decoded then
            gameState = decoded
            migrateGameState()
        else
            broadcastToAll("Could not read the saved game state — starting fresh.", {1, 0.6, 0.4})
        end
    end

    if not gameState.started and not gameState.welcomed then
        safecall(function() showWelcomeSequence() end, "Welcome")
        -- No 3D board Setup button: setup is driven from Host Controls
        -- (btnSetup). The board plate rendered upside down and duplicated
        -- the panel button.
    elseif gameState.started then
        broadcastToAll("Starve No More — game restored. Day " .. gameState.day .. ", Doom " .. gameState.doom .. ".", {0.5, 0.9, 1})
    end

    -- G.1: Refresh UI after a short delay to let XML load
    Wait.time(function()
        refreshPhaseBanner()
        safecall(function() populateNotebook() end, "Notebook")
        if gameState.started then
            updateActivePlayerIndicator()
            applyTooltips()
            refreshDynamicTooltips()
            safecall(function() lockdownCriticalObjects() end, "Lockdown")
        end
        -- TTS's built-in Turns system stays OFF: this mod tracks turns
        -- itself (banner + action bar), and the built-in turn plate just
        -- sat behind the phase banner confusing everyone.
        pcall(function()
            if Turns and Turns.enable then
                Turns.enable = false
                broadcastToAll("Tabletop Simulator's built-in turn tracker is off — this game runs its own turns (see the top banner).", {0.7, 0.7, 0.7})
            end
        end)
        -- (No Discard Tray sweep any more — resources are virtual, so no
        -- tokens are ever dropped for it to reclaim.)
        -- J.10: Run first-load component audit
        safecall(function() auditFirstLoad() end, "FirstLoadAudit")
        -- J.11: Measure the board against the world square its art is drawn
        -- for. Silent when they match; shouts (and logs) when they don't --
        -- that mismatch is what heaps every piece in the middle of the board.
        safecall(function() auditBoardGeometry(true, "early") end, "BoardGeometry")
    end, 1.0)

    -- Second geometry sample once the custom images have loaded. The board's
    -- bounds are smaller while its image is still downloading, so the early
    -- reading understates the mesh — measure again before trusting a number.
    Wait.time(function()
        safecall(function() auditBoardGeometry(true, "late") end, "BoardGeometry")
        safecall(function() auditObjectFootprints() end, "Footprints")
    end, 12.0)
end

function onSave()
    return JSON.encode(gameState)
end

-----------------------------------------------------------------------
-- Setup entry point: onHostSetupGuided (ui_setup.lua), wired to the Host
-- Controls > Setup Game button.
--
-- There used to be a second one here, onSetupClick, for a physical 3D board
-- button. That button was removed (it rendered upside down and duplicated
-- Host Controls), and the comment left behind claimed onSetupClick "remains
-- as the handler for that panel button" — which was never true: the panel
-- button has always called onHostSetupGuided. What was left was a strict
-- duplicate of it, plus a clearButtons() call on an object that no longer
-- exists, kept alive in the reachability scan by the one test that called
-- it. Deleted, the way resolveGroupCombat was.
-----------------------------------------------------------------------
