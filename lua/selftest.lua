-- selftest.lua  (J.11 — In-TTS scripted smoke test)
--
-- Run from the TTS console:  runSelfTest()
--
-- Plays a scripted mini-game against the real components: component audit →
-- Setup → Begin Day → a Gather action → Pass → Dusk → Night → Tick, asserting
-- gameState after every step, then reports PASS/FAIL lines and a summary.
--
-- WARNING: this resets the current game state and moves real cards/tokens
-- (decks are shuffled, a Dawn card is drawn). Run it on a fresh load, then
-- reload the save before playing for real.
--
-- Steps are spaced with Wait.time because the real flow is asynchronous
-- (BeginDay -> beginDayPhase after 2s, ResolveNight chains up to ~7s).
-- The same file runs headlessly under tests/tts_stub.lua, where the harness
-- flushes the waits instantly — keep steps free of TTS-only assumptions
-- unless guarded.

SELFTEST = { results = {}, done = false, passed = 0, failed = 0 }

local function check(cond, label)
    if cond then
        SELFTEST.passed = SELFTEST.passed + 1
        table.insert(SELFTEST.results, "[OK] " .. label)
    else
        SELFTEST.failed = SELFTEST.failed + 1
        table.insert(SELFTEST.results, "[FAIL] " .. label)
        broadcastEvent("damage", "SELFTEST FAIL: " .. label)
    end
    return cond
end

local function finishSelfTest()
    SELFTEST.done = true
    broadcastEvent("phase", "=== SELF-TEST COMPLETE: " .. SELFTEST.passed .. " passed, "
        .. SELFTEST.failed .. " failed ===")
    for _, line in ipairs(SELFTEST.results) do
        if line:find("FAIL") then broadcastEvent("warn", line) end
    end
    if SELFTEST.failed == 0 then
        broadcastEvent("gain", "All self-test steps passed. Reload the save before playing for real.")
    else
        broadcastEvent("damage", "Self-test found problems — see FAIL lines above (full list in SELFTEST.results).")
    end
end

-- Each step: { name, wait (seconds before the NEXT step), fn }.
-- fn runs inside pcall; a hard error is recorded as a FAIL and the run continues.
local function selfTestSteps()
    return {

        { name = "component audit", wait = 0.5, fn = function()
            check(auditFirstLoad(), "auditFirstLoad: all physical components present")
        end },

        { name = "setup", wait = 1.5, fn = function()
            Setup("White")
            check(gameState.started == true, "Setup marks game started")
            check(gameState.day == 1 and gameState.doom == 0, "Setup: Day 1, Doom 0")
            check(gameState.subPhase == "Dawn", "Setup leaves subPhase Dawn")
            local n = 0
            for _ in pairs(gameState.activeChars) do n = n + 1 end
            check(n == gameState.playerCount and n >= 1,
                "Setup assigned a character per seated player (" .. n .. ")")
        end },

        -- BeginDay draws a Dawn card and schedules beginDayPhase after 2s.
        { name = "begin day", wait = 3.5, fn = function()
            BeginDay()
            check(gameState.doom >= 1, "Dawn advanced Doom (now " .. gameState.doom .. ")")
        end },

        { name = "day phase started", wait = 0.5, fn = function()
            check(gameState.subPhase == "Day", "subPhase is Day after Dawn resolves")
            check(gameState.activeColor ~= nil, "a player has the turn")
            local char = gameState.activeChars[gameState.activeColor or ""]
            check(char ~= nil and char.actionsLeft == ACTIONS_PER_TURN,
                "active player has " .. ACTIONS_PER_TURN .. " actions")
        end },

        { name = "gather action", wait = 0.5, fn = function()
            local color = gameState.activeColor
            if not check(color ~= nil, "active player exists for Gather") then return end
            local before = gameState.activeChars[color].actionsLeft
            doGather(color)
            check(gameState.activeChars[color].actionsLeft == before - 1,
                "Gather consumed exactly 1 action")
        end },

        { name = "undo", wait = 0.5, fn = function()
            local color = gameState.activeColor
            if not check(color ~= nil, "active player exists for Undo") then return end
            local before = gameState.activeChars[color].actionsLeft
            doUndo(color)
            check(gameState.activeChars[color].actionsLeft == before + 1,
                "Undo refunded the Gather action")
        end },

        -- Everyone passes; with all actions spent the loop advances to Dusk.
        { name = "pass to dusk", wait = 1.0, fn = function()
            local guard = 0
            while gameState.subPhase == "Day" and gameState.activeColor and guard < 12 do
                doPass(gameState.activeColor)
                guard = guard + 1
            end
            check(gameState.subPhase == "Dusk", "all players passed -> subPhase Dusk")
        end },

        -- Host-override path into Night. ResolveNight chains threats ->
        -- storytelling -> sleep -> tick over ~7s of Wait.time.
        { name = "night", wait = 9.0, fn = function()
            beginNight()
            check(gameState.subPhase == "Night", "beginNight sets subPhase Night")
        end },

        { name = "tick completed", wait = 0.5, fn = function()
            check(gameState.subPhase == "PreDawn" or gameState.subPhase == "GameOver",
                "Night chain reached Tick (subPhase now " .. tostring(gameState.subPhase) .. ")")
            check(gameState.day == 2 or gameState.subPhase == "GameOver",
                "Tick advanced to Day 2")
            for color, char in pairs(gameState.activeChars) do
                check(char.health >= 0 and char.health <= char.maxHealth
                    and char.hunger >= 0 and char.hunger <= char.maxHunger
                    and char.sanity >= 0 and char.sanity <= char.maxSanity,
                    char.name .. " stats within bounds after Tick")
            end
        end },

        { name = "save/load round-trip", wait = 0.5, fn = function()
            local saved = onSave()
            check(type(saved) == "string" and #saved > 2, "onSave returns JSON")
            local decoded = JSON.decode(saved)
            check(decoded ~= nil and decoded.day == gameState.day,
                "saved state decodes and preserves day")
        end },
    }
end

function runSelfTest()
    SELFTEST = { results = {}, done = false, passed = 0, failed = 0 }
    broadcastEvent("phase", "=== SELF-TEST STARTING — this resets game state; reload the save afterwards ===")

    -- start from a clean slate, same shape as global.lua's initial gameState
    gameState.started = false
    gameState.welcomed = true
    gameState.day = 1
    gameState.phase = 1
    gameState.doom = 0
    gameState.subPhase = "PreGame"
    gameState.activeColor = nil
    gameState.turnOrder = {}
    gameState.turnIndex = 0
    gameState.activeChars = {}
    gameState.ongoingDawnEffects = {}
    gameState.dailyAlerts = {}
    gameState.dayLog = {}
    gameState.activeDawn = nil
    gameState.scenarioFlags = {}
    gameState.treeguard = nil
    gameState.jamesEnergyDrinkUsed = false

    local steps = selfTestSteps()
    local function runStep(i)
        local s = steps[i]
        if not s then
            finishSelfTest()
            return
        end
        local ok, err = pcall(s.fn)
        if not ok then
            SELFTEST.failed = SELFTEST.failed + 1
            table.insert(SELFTEST.results, "[FAIL] step '" .. s.name .. "' errored: " .. tostring(err))
            broadcastEvent("damage", "SELFTEST step '" .. s.name .. "' errored: " .. tostring(err))
        end
        Wait.time(function() runStep(i + 1) end, s.wait or 0.5)
    end
    runStep(1)
end
