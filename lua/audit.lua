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
-- J.11 — Board geometry probe
-- Call from the TTS console:  auditBoardGeometry()
--
-- Every object position and every snap point is authored inside a
-- BOARD_WORLD_SIZE square (scripts/board_geometry.py), which assumes the
-- Custom_Board mesh spans board-local -1..+1 so Transform scale 12 paints
-- the art across exactly that square. If the real mesh half-extent is not
-- 1.0 the printed art is stretched over a LARGER world area than the
-- pieces occupy: every piece then sits in a heap in the middle of the
-- board while the printed rings / DAY COUNTER frame / Doom track sit
-- outside them. This prints the real numbers so the scale gets fixed from
-- a measurement instead of a guess.
-----------------------------------------------------------------------
BOARD_WORLD_SIZE = 24   -- world units the board art is authored across (+/-12)

-- quiet=true (the onLoad call) logs the measurement and stays silent unless
-- the geometry is actually wrong, so a healthy board adds no table chatter.
-- `label` tags which sample this is: the board's bounds read SMALLER while
-- its custom image is still downloading, so an early sample and a late one
-- disagree (9.14 vs 12.79 mesh half-extent across two sessions). Always
-- take BOARD_MESH_HALF from the late sample.
function auditBoardGeometry(quiet, label)
    label = label and (" [" .. label .. "]") or ""
    local board = getMainBoard()
    if not board then
        broadcastEvent("warn", "Board geometry: main board not found.")
        return nil
    end

    local b = board.getBoundsNormalized()
    local scale = board.getScale()
    local worldW, worldD = b.size.x, b.size.z
    local factor = worldW / BOARD_WORLD_SIZE
    -- Local half-extent of the Custom_Board mesh: 1.0 is what the build
    -- assumes. Anything else is the whole bug.
    local meshHalf = (scale.x ~= 0) and (worldW / (2 * scale.x)) or 0

    -- Also to the in-game console. (Not to Unity's Player.log -- that file
    -- only carries engine output; the Message Log below is what reaches disk,
    -- via the autosave. See docs/debugging.md.)
    print(string.format(
        "[BoardGeometry]%s world=%.4f x %.4f scale=%.4f meshHalf=%.4f factor=%.4f correctScale=%.4f",
        label, worldW, worldD, scale.x, meshHalf, factor,
        (factor ~= 0) and (scale.x / factor) or 0))

    if not quiet then
        broadcastEvent("proc", string.format(
            "Board renders %.2f x %.2f world units (Transform scale %.2f, mesh half-extent %.3f).",
            worldW, worldD, scale.x, meshHalf))
    end

    if math.abs(factor - 1) <= 0.05 then
        if not quiet then
            broadcastEvent("gain", string.format(
                "Matches the %d-unit square the art is authored for - pieces and printed art line up.",
                BOARD_WORLD_SIZE))
        end
    else
        broadcastEvent("warn", string.format(
            "Board geometry%s: art is authored for %d units but the board renders %.2fx that, "
            .. "so pieces sit inside the printed rings/track instead of on them. Correct "
            .. "Custom_Board Transform scale = %.4f (currently %.4f); mesh half-extent %.3f.",
            label, BOARD_WORLD_SIZE, factor, scale.x / factor, scale.x, meshHalf))
    end

    return { worldWidth = worldW, worldDepth = worldD, scale = scale.x,
             meshHalf = meshHalf, factor = factor, correctScale = scale.x / factor }
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

-----------------------------------------------------------------------
-- J.12 — Object footprint probe.
-- Reports each key object's real world size and how far its visual centre
-- sits from its transform origin. Sizes were guessed for years against a
-- board that rendered nine times too big; this measures them instead.
-- MEASURE_FOOTPRINTS stays true only while sizes are being tuned — the
-- numbers land in the Message Log, which the autosave persists, so they
-- can be read off disk with scripts/inspect_save.py --live.
-----------------------------------------------------------------------

MEASURE_FOOTPRINTS = true

function auditObjectFootprints()
    if not MEASURE_FOOTPRINTS then return end

    local probes = {
        -- The board first: bounds centre vs transform origin. The DAY COUNTER
        -- frame is printed at world (-10, 8) and the counter object sits at
        -- (-10, 8), yet they render apart -- which can only mean the image is
        -- not centred on the mesh.
        {tag = "MainBoard",    label = "Board"},
        {tag = "DayCounter",   label = "DayCounter",  anchorX = -10,  anchorZ = 8},
        {tag = "DoomMarker",   label = "DoomMarker"},
        {tag = "Location:JamesHouse", label = "Tile"},
        {tag = "Resource:EnergyDrink", label = "EnergyTok"},
    }

    local parts = {}
    for _, p in ipairs(probes) do
        local obj = findOneByTag(p.tag)
        if obj then
            local ok, line = pcall(function()
                local b = obj.getBoundsNormalized()
                local pos = obj.getPosition()
                local s = string.format("%s size %.2fx%.2f", p.label, b.size.x, b.size.z)
                -- VERTICAL facts. Everything on the board once hung in the
                -- air because a Custom_Tile's Thickness is scaled by scaleY,
                -- not by the XZ transform scale, and build_save assumed the
                -- latter — so the computed "board top" was 0.13 too high and
                -- nothing standing on it could be flush. Report the real top
                -- and bottom so the next person reads the number instead of
                -- inferring it from a screenshot.
                local bottom, top = b.center.y - b.size.y / 2, b.center.y + b.size.y / 2
                s = s .. string.format(" thick %.3f bottom %.3f top %.3f",
                                       b.size.y, bottom, top)
                local board = findOneByTag("MainBoard")
                if board and p.tag ~= "MainBoard" then
                    local okb, bb = pcall(function() return board.getBoundsNormalized() end)
                    if okb and bb then
                        s = s .. string.format(" gapOverBoard %+.3f",
                            bottom - (bb.center.y + bb.size.y / 2))
                    end
                end
                -- Offset of the rendered centre from the transform origin:
                -- a non-zero value means the gadget does not sit where it is
                -- placed (the Day Counter looks off its printed frame).
                local dx, dz = b.center.x - pos.x, b.center.z - pos.z
                if math.abs(dx) > 0.05 or math.abs(dz) > 0.05 then
                    s = s .. string.format(" centreOff %+.2f,%+.2f", dx, dz)
                end
                if p.anchorX then
                    s = s .. string.format(" vsAnchor %+.2f,%+.2f",
                        b.center.x - p.anchorX, b.center.z - p.anchorZ)
                end
                return s
            end)
            table.insert(parts, ok and line or (p.label .. " ?"))
        end
    end

    if #parts > 0 then
        broadcastEvent("proc", "[footprints] " .. table.concat(parts, " | "))
    end
end
