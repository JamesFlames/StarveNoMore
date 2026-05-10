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

-- Phase→day mapping: which phase deck is active on which day
function getPhaseForDay(day)
    if day <= 2 then return 1
    elseif day <= 4 then return 2
    elseif day <= 5 then return 3
    else return 4 end
end

-- Doom rate per phase, scaled by player count (Design §15.6)
DOOM_RATES = {
    [3] = {1, 1, 1, 2},
    [4] = {1, 1, 2, 3},
    [5] = {1, 2, 2, 3},
}

function getDoomRate()
    local pc = math.max(3, math.min(5, gameState.playerCount))
    local rates = DOOM_RATES[pc] or DOOM_RATES[4]
    return rates[gameState.phase] or 1
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
