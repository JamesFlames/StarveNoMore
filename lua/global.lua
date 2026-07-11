-- global.lua  (F.1 — Global script skeleton + F.14 save/load + F.15 broadcast)

-----------------------------------------------------------------------
-- Game State (the single source of truth, persisted via onSave)
-----------------------------------------------------------------------
gameState = {
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

CHARACTER_HOMES = {
    James  = "JamesHouse",
    Rayman = "RaymanHouse",
    Ellie  = "EllieLucaHouse",
    Luca   = "EllieLucaHouse",
    Coco   = nil,
}

ACTIONS_PER_TURN = 3

-----------------------------------------------------------------------
-- Difficulty modes (Design §17.2, batch 4 W3). gameState.difficulty is
-- "standard" unless the host picks otherwise in the setup Variants step.
--   weekend   — 3 days (Phase 1 + half of Phase 2), Doom track halved
--               (defeat at 15). Good for teaching.
--   standard  — the full 7-day week.
--   nightmare — Doom rate +1 in every phase; no Phase 1 (the week starts
--               on Strange Days).
-- Long Weekend and Nightmare are derived offsets from the tuned Standard,
-- not separately balanced.
-----------------------------------------------------------------------
DIFFICULTY_PARAMS = {
    weekend   = { label = "Long Weekend", days = 3, doomLimit = 15, doomDelta = 0,
                  phaseForDay = {1, 1, 2} },
    standard  = { label = "Standard",     days = 7, doomLimit = 30, doomDelta = 0 },
    nightmare = { label = "Nightmare",    days = 7, doomLimit = 30, doomDelta = 1,
                  minPhase = 2 },
}

function getDifficulty()
    return DIFFICULTY_PARAMS[gameState.difficulty or "standard"] or DIFFICULTY_PARAMS.standard
end

function getTotalDays() return getDifficulty().days end
function getDoomLimit() return getDifficulty().doomLimit end

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
end

-----------------------------------------------------------------------
-- Lifecycle (F.1 + F.14)
-----------------------------------------------------------------------
function onLoad(savedState)
    if savedState and savedState ~= "" then
        local decoded = JSON.decode(savedState)
        if decoded then
            gameState = decoded
        end
    end

    if not gameState.started and not gameState.welcomed then
        safecall(function() showWelcomeSequence() end, "Welcome")
        createSetupButton()
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
        end
        -- J.10: Run first-load component audit
        safecall(function() auditFirstLoad() end, "FirstLoadAudit")
    end, 1.0)
end

function onSave()
    return JSON.encode(gameState)
end

-----------------------------------------------------------------------
-- Setup button (temporary, replaced by guided walkthrough in Phase H)
-----------------------------------------------------------------------
function createSetupButton()
    local board = getMainBoard()
    if not board then
        broadcastToAll("ERROR: Main Board not found. Cannot create Setup button.", {1, 0, 0})
        return
    end
    board.createButton({
        click_function = "onSetupClick",
        function_owner = Global,
        label          = "Setup Game",
        position       = {0, 0.5, 0},
        rotation       = {0, 0, 0},
        width          = 2400,
        height         = 600,
        font_size      = 300,
        color          = {0.15, 0.15, 0.15},
        font_color     = {0.9, 0.7, 0.3},
        tooltip        = "Click to set up a new game of Starve No More.",
    })
end

function onSetupClick(obj, playerColor, altClick)
    obj.clearButtons()
    safecall(function() Setup(playerColor) end, "Setup")
end
