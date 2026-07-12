-- audit.lua  (J.1 Object count + J.5 Permission lockdown + J.7 Tooltip audit + J.8 Hint audit + J.10 First-load check)

-----------------------------------------------------------------------
-- J.1 — Object count audit (< 500 mid-game)
-- Call from TTS console: auditObjectCount()
-----------------------------------------------------------------------
function auditObjectCount()
    local count = #getAllObjects()
    local msg = "Object count: " .. count .. " / 500 limit"
    if count >= 500 then
        broadcastEvent("warn", msg .. " [OVER LIMIT — consolidate tokens into bags]")
    elseif count >= 400 then
        broadcastEvent("warn", msg .. " [approaching limit]")
    else
        broadcastEvent("gain", msg .. " [OK]")
    end
    return count
end

-----------------------------------------------------------------------
-- J.5 — Permission lockdown on critical objects
-- Locks board, tiles, counters, legends to prevent accidental deletion.
-- Called at end of Setup.
-----------------------------------------------------------------------
function lockdownCriticalObjects()
    local criticalTags = {
        "MainBoard",
        "DayCounter",
        "SeverityLegend",
        "Location:JamesHouse",
        "Location:RaymanHouse",
        "Location:EllieLucaHouse",
        "Location:BasketballCourt",
        "Location:BadmintonCourt",
    }

    local locked = 0
    for _, tag in ipairs(criticalTags) do
        local obj = findOneByTag(tag)
        if obj then
            obj.setLock(true)
            locked = locked + 1
        end
    end

    -- The Day Counter is script-driven only: block its +/- buttons so
    -- players can't adjust the day by hand (setValue still works).
    local counter = getDayCounter()
    if counter then counter.interactable = false end

    -- Lock all resource infinite bags
    for _, obj in ipairs(getAllObjects()) do
        if obj.hasTag("ResourceBag") then
            obj.setLock(true)
            locked = locked + 1
        end
    end

    broadcastEvent("proc", "Locked " .. locked .. " critical objects against accidental movement.")
end

-----------------------------------------------------------------------
-- J.7 — Tooltip coverage audit
-- Call from TTS console: auditTooltips()
-- Flags any interactable object with an empty or missing description.
-----------------------------------------------------------------------
function auditTooltips()
    local missing = {}
    local total = 0
    local covered = 0

    for _, obj in ipairs(getAllObjects()) do
        -- Skip hidden/contained objects
        if obj.getPosition().y > -5 then
            total = total + 1
            local desc = obj.getDescription() or ""
            local nick = obj.getNickname() or ""

            if desc == "" and nick ~= "" then
                table.insert(missing, nick .. " (" .. obj.getName() .. ")")
            elseif desc ~= "" then
                covered = covered + 1
            end
        end
    end

    broadcastEvent("proc", "Tooltip audit: " .. covered .. "/" .. total .. " objects have descriptions.")
    if #missing > 0 then
        local preview = {}
        for i = 1, math.min(10, #missing) do
            table.insert(preview, "- " .. missing[i])
        end
        broadcastEvent("warn", "Missing tooltips (" .. #missing .. "):\n" .. table.concat(preview, "\n"))
        if #missing > 10 then
            broadcastEvent("proc", "... and " .. (#missing - 10) .. " more.")
        end
    else
        broadcastEvent("gain", "All named objects have tooltip descriptions!")
    end

    return missing
end

-----------------------------------------------------------------------
-- J.8 — What-now hint coverage audit
-- Call from TTS console: auditHintCoverage()
-- Walks through every sub-phase and verifies a hint exists.
-----------------------------------------------------------------------
function auditHintCoverage()
    -- WHATNOW_HINTS is auto-generated from content/help/whatnow_hints.md.
    -- Group keys: PreGame, Dawn, Day, Dusk, Night, Tick, PostGame,
    --             Stats, James, Coco, Rayman, Ellie, Luca,
    --             Location, Strategic.
    local missing = {}
    local covered = 0

    local subPhaseGroups = {"PreGame", "Dawn", "Day", "Dusk", "Night", "Tick", "PostGame"}
    for _, g in ipairs(subPhaseGroups) do
        local hints = WHATNOW_HINTS[g]
        if hints and hints.default and hints.default ~= "" then
            covered = covered + 1
        else
            table.insert(missing, "Sub-phase: " .. g)
        end
    end

    local chars = {"James", "Coco", "Rayman", "Ellie", "Luca"}
    for _, name in ipairs(chars) do
        local h = WHATNOW_HINTS[name]
        if h and next(h) then
            covered = covered + 1
        else
            table.insert(missing, "Character group: " .. name)
        end
    end

    local statKeys = {"low_hunger", "low_sanity", "low_health"}
    local stats = WHATNOW_HINTS.Stats or {}
    for _, key in ipairs(statKeys) do
        if stats[key] and stats[key] ~= "" then
            covered = covered + 1
        else
            table.insert(missing, "Stat: " .. key)
        end
    end

    local stratKeys = {"doom_high", "ally_down", "no_light_source"}
    local strat = WHATNOW_HINTS.Strategic or {}
    for _, key in ipairs(stratKeys) do
        if strat[key] and strat[key] ~= "" then
            covered = covered + 1
        else
            table.insert(missing, "Strategic: " .. key)
        end
    end

    local locKeys = {"at_own_house", "at_kitchen_not_ellie", "at_basketball_court", "at_badminton_court"}
    local locs = WHATNOW_HINTS.Location or {}
    for _, key in ipairs(locKeys) do
        if locs[key] and locs[key] ~= "" then
            covered = covered + 1
        else
            table.insert(missing, "Location: " .. key)
        end
    end

    broadcastEvent("proc", "Hint coverage audit: " .. covered .. " covered, " .. #missing .. " missing.")
    if #missing > 0 then
        broadcastEvent("warn", "Missing hints: " .. table.concat(missing, ", "))
    else
        broadcastEvent("gain", "All hint slots populated!")
    end

    return missing
end

-----------------------------------------------------------------------
-- J.10 — First-time-load checklist (run automatically or from console)
-- Call from TTS console: auditFirstLoad()
-----------------------------------------------------------------------
function auditFirstLoad()
    local checks = {}
    local pass = 0
    local fail = 0

    -- 1. Main board exists
    if getMainBoard() then
        pass = pass + 1
        table.insert(checks, "[OK] Main board present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Main board missing")
    end

    -- 2. All 5 location tiles
    local locs = {"JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"}
    for _, loc in ipairs(locs) do
        if getLocationTile(loc) then
            pass = pass + 1
        else
            fail = fail + 1
            table.insert(checks, "[FAIL] Location tile missing: " .. loc)
        end
    end

    -- 3. Doom marker
    if getDoomMarker() then
        pass = pass + 1
        table.insert(checks, "[OK] Doom marker present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Doom marker missing")
    end

    -- 4. Day counter
    if getDayCounter() then
        pass = pass + 1
        table.insert(checks, "[OK] Day counter present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Day counter missing")
    end

    -- 5. All 5 character standees
    local charNames = {"James", "Coco", "Rayman", "Ellie", "Luca"}
    for _, name in ipairs(charNames) do
        if getCharacterStandee(name) then
            pass = pass + 1
        else
            fail = fail + 1
            table.insert(checks, "[FAIL] Standee missing: " .. name)
        end
    end

    -- 6. Severity legend
    if getSeverityLegend() then
        pass = pass + 1
        table.insert(checks, "[OK] Severity legend present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Severity legend missing")
    end

    -- 7. Resource bags (6)
    local resources = {"Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"}
    for _, res in ipairs(resources) do
        if getResourceBag(res) then
            pass = pass + 1
        else
            fail = fail + 1
            table.insert(checks, "[FAIL] Resource bag missing: " .. res)
        end
    end

    -- 8. Heart supply
    if getHeartSupply() then
        pass = pass + 1
        table.insert(checks, "[OK] Telltale Heart supply present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Telltale Heart supply missing")
    end

    -- 9. Boss pool
    if getBossPool() then
        pass = pass + 1
        table.insert(checks, "[OK] Boss pool present")
    else
        fail = fail + 1
        table.insert(checks, "[FAIL] Boss pool missing")
    end

    -- Summary
    broadcastEvent("proc", "First-load audit: " .. pass .. " pass, " .. fail .. " fail.")
    if fail > 0 then
        for _, c in ipairs(checks) do
            if c:find("FAIL") then
                broadcastEvent("warn", c)
            end
        end
    else
        broadcastEvent("gain", "First-load checklist passed! All components present.")
    end

    return fail == 0
end
