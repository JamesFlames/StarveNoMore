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
    -- economy reads. [color] = {Wood, Metal, Cloth, Food, EnergyDrink, Battery}
    resources = {},

    -- One-fire-per-day flags so urgent auto-broadcasts (Down, stat-below-3,
    -- James-no-Energy-Drink) don't spam the chat. Cleared in BeginDay() at Dawn.
    dailyAlerts = {
        -- [color] = { downHint = true, low_hunger = true, ... }
    },

    -- Idle-detection nudge state (see day_loop.lua).
    lastInteractionAt    = 0,
    idleNudgedThisTurn   = false,

    -- Week in Review chronicle (design_batch1.md §3). A persistent record
    -- across all 7 days (NOT wiped with dayLog each Dawn), narrated at game
    -- end. Reset at setup; auto-persists with gameState.
    chronicle = {
        days = {},                              -- [day] = {headline, damageTonight}
        meals = {},                             -- [charName] = count
        kills = {},                             -- { {who, threat, day}, ... }
        peakDoom = { value = 0, day = 0 },
        maxCharlieStreak = { value = 0, name = "" },
        downs = 0, revives = 0,
        -- Session telemetry (design_batch4.md W0, lua/telemetry.lua):
        setup = {},                             -- player count / roster / variants / difficulty
        turns = {},                             -- { {day, name, seconds}, ... } per player turn
        beats = { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 },
    },
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
-- picked uniformly from this list, so Food comes up twice as often at
-- Ellie & Luca's House. These are the six canonical resource types
-- (the token/bag tags), so giveResource can pull straight from a bag.
-- Mirrors scripts/simulate_balance.py's YIELDS (lower-cased there);
-- tests/test_sim.py::test_location_yields_match guards the two.
-----------------------------------------------------------------------
LOCATION_YIELDS = {
    JamesHouse      = {"EnergyDrink", "Battery", "Food"},
    RaymanHouse     = {"Metal", "Battery", "Food"},
    EllieLucaHouse  = {"Food", "Food", "Cloth"},
    BasketballCourt = {"Wood", "Metal", "Cloth"},
    BadmintonCourt  = {"Cloth", "Wood", "Metal"},
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
    anyPhaseBosses = 25,   -- bosses any phase + Nothing Left to Lose
}

-----------------------------------------------------------------------
-- Cleanse (Design §15.3): the communal ritual. doCleanse (tick_victory.lua)
-- and the cleanse highlight (ui_actionbar.lua) read these; sim-mirrored.
-----------------------------------------------------------------------
CLEANSE_COST = { Wood = 1, Cloth = 1, Battery = 1, EnergyDrink = 1 }
CLEANSE_REDUCTION = 2

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
    nightmare = { label = "Nightmare",    days = 7, doomLimit = 30, doomDelta = 1,
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
DOOM_RATES = {
    [3] = {1, 1, 1, 1},
    [4] = {1, 1, 1, 2},
    [5] = {1, 1, 2, 2},
}

function getDoomRate()
    local pc = math.max(3, math.min(5, gameState.playerCount))
    local rates = DOOM_RATES[pc] or DOOM_RATES[4]
    return (rates[gameState.phase] or 1) + (getDifficulty().doomDelta or 0)
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
    for _, char in pairs(gs.activeChars) do
        if char.signatureUsed == nil then char.signatureUsed = false end -- batch 2
    end
    -- Chronicle: lazily created; older chronicles gain the telemetry fields.
    if gs.chronicle then
        gs.chronicle.setup = gs.chronicle.setup or {}
        gs.chronicle.turns = gs.chronicle.turns or {}
        gs.chronicle.beats = gs.chronicle.beats or
            { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 }
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
-- Setup entry point. The physical 3D board button is gone (it rendered
-- upside down and duplicated Host Controls > Setup Game); onSetupClick
-- remains as the handler for that panel button and for tests.
-----------------------------------------------------------------------
function onSetupClick(obj, playerColor, altClick)
    -- Route through the guided walkthrough — the bare Setup() would assign
    -- characters by seat color and ignore the players' picks.
    if gameState.started then
        broadcastToColor("Game already started. Click Restart first.", playerColor, BROADCAST_COLORS.damage)
        return
    end
    obj.clearButtons()
    safecall(function() startGuidedSetup(playerColor) end, "Setup")
end
