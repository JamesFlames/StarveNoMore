-- day_loop.lua  (F.4 — Day Advance / BeginDay + turn management)

-----------------------------------------------------------------------
-- Idle-detection nudge: if the active player hasn't taken an action in
-- IDLE_THRESHOLD seconds, surface a "click What now?" prompt once per
-- turn. Watcher only runs during Day sub-phase.
-----------------------------------------------------------------------
local IDLE_THRESHOLD = 45  -- seconds
local _idleWatcher = nil

function noteInteraction()
    gameState.lastInteractionAt = os.time()
end

function _checkIdle()
    if gameState.subPhase ~= "Day" then return end
    local active = gameState.activeColor
    if not active then return end
    if gameState.idleNudgedThisTurn then return end
    local last = gameState.lastInteractionAt or 0
    local elapsed = os.time() - last
    if elapsed >= IDLE_THRESHOLD then
        gameState.idleNudgedThisTurn = true
        printToColor("Idle for " .. elapsed .. "s. Click '?' or 'What now?' on the Phase Banner for a context hint.",
                     active, {1, 0.85, 0.4})
    end
end

function startIdleWatcher()
    if _idleWatcher then Wait.stop(_idleWatcher) end
    _idleWatcher = Wait.time(_checkIdle, 10, -1)
end

function stopIdleWatcher()
    if _idleWatcher then Wait.stop(_idleWatcher); _idleWatcher = nil end
end

function BeginDay()
    -- Phase 1: Dawn
    gameState.subPhase = "Dawn"
    gameState.dayLog = {}
    gameState.dailyAlerts = {}  -- reset one-per-day urgent-hint flags
    gameState.raymanMovedToday = false  -- Loud constraint resets each day
    gameState.raymanTilesMovedToday = 0 -- 3p Big Appetite relief reads this (§20.1)
    gameState.raymanFoughtToday = false
    gameState.raymanDefending = false   -- Backboard Block never outlives the night
    gameState.jamesPeekUsed = false     -- Pattern Recognition: once per day (§6.1)
    gameState.loudSignature = {}        -- Posterize echo lasts one night only
    safecall(function() setPhaseMood("Dawn") end, "Mood")
    safecall(function() Audio.startDayAmbience() end, "Audio")

    -- QoL: Snapshot start-of-day stats for end-of-day comparison
    gameState.dayStartStats = {}
    for color, char in pairs(gameState.activeChars) do
        gameState.dayStartStats[color] = {
            health = char.health,
            hunger = char.hunger,
            sanity = char.sanity,
        }
    end

    -- Advance Day Counter
    local counter = getDayCounter()
    if counter then counter.setValue(gameState.day) end

    -- Determine which phase deck we're in
    gameState.phase = getPhaseForDay(gameState.day)

    broadcastEvent("phase", "--- Day " .. gameState.day .. " of " .. getTotalDays() .. " --- Phase " .. gameState.phase .. " ---")

    -- Phase 2.5 foreshadow: the Treeguard wakes at Dusk tonight (Design §14.2).
    if gameState.day == 4 and not gameState.treeguard then
        broadcastEvent("warn", "The trees remember every plank you took. Something in the courts is breathing slower than the wind...")
    end

    -- Advance Doom by phase rate
    local rate = getDoomRate()
    gameState.doom = gameState.doom + rate
    moveDoomMarker(gameState.doom)
    broadcastEvent("warn", "Doom advances +" .. rate .. " to " .. gameState.doom .. " / " .. getDoomLimit() .. ".")

    -- Festering (Design §15.1): every mess left on the map at Dawn feeds the
    -- Doom track. Ordinary threats +1 each (max +3); bosses are uncapped —
    -- +2 per phase boss, +1 for the Treeguard.
    local threatFester, bossFester = countFesteringThreats()
    if threatFester > 0 then
        gameState.doom = gameState.doom + threatFester
        broadcastEvent("warn", "Uncleared threats fester: Doom +" .. threatFester ..
            " (now " .. gameState.doom .. " / " .. getDoomLimit() .. "). Clear the map to stop the bleed.")
    end
    if bossFester > 0 then
        gameState.doom = gameState.doom + bossFester
        broadcastEvent("warn", "A boss looms over the neighborhood: Doom +" .. bossFester ..
            " (now " .. gameState.doom .. " / " .. getDoomLimit() .. "). Bosses fester every Dawn they stand — no cap.")
    end
    if threatFester > 0 or bossFester > 0 then
        moveDoomMarker(gameState.doom)
    end

    -- Check doom thresholds
    checkDoomThresholds()

    -- Check defeat
    if checkDefeat() then return end

    -- The Wrongness (design_batch3.md §4): if nobody went to look, it
    -- resolves in place now — it comes to them. (Runs after festering: the
    -- face-down card was unresolved, not fled-from, so this Dawn is free.)
    if gameState.wrongness and (gameState.wrongness.placedDay or 0) < gameState.day then
        safecall(function() resolveWrongness("dawn") end, "Wrongness")
    end

    -- Moonlit Salvage (Design §7.4/§7.5): anyone who spent the night at a
    -- sport court and is still standing gathers 2 resources at Dawn.
    for color, char in pairs(gameState.activeChars) do
        if not char.down and (char.location == "BasketballCourt" or char.location == "BadmintonCourt") then
            broadcastEvent("gain", char.name .. " survived the night at " .. char.location ..
                " — Moonlit Salvage: draw 2 resources from this court's bag now.")
            -- Dare — the court floodlights (P1_LIGHTS_FLICKER): survivors
            -- claim the prize. (The flag is cleaned up by revealDawnCard's
            -- dispatch below, so it is still readable here.)
            if gameState.ongoingDawnEffects.dareCourtGlow then
                broadcastEvent("gain", char.name .. " braved the glowing court — the dare pays: draw 2 Market cards now.")
                safecall(function() recordBeat("dare") end, "Telemetry")
            end
        end
    end

    -- The Eye of Terror's stare (P3_EYE_ARRIVES): each Dawn it stands, its
    -- tile draws 1 extra Threat.
    if gameState.ongoingDawnEffects.eyeActive and gameState.eyeLocation
        and isBossOnMap("Boss:EyeOfTerror") then
        broadcastEvent("warn", "The Eye of Terror stares down " .. gameState.eyeLocation ..
            " — 1 extra Threat appears there.")
        safecall(function() drawThreatsAt(gameState.eyeLocation, 1) end, "EyeThreat")
    end

    -- Haunted (Design §10.1): a character below 3 Sanity draws 1 Threat at
    -- their tile at Dawn. Only they can fight or flee it — allies can't
    -- help with what they can't see. Discard it once resolved; it's not
    -- real, so it never festers.
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char.sanity > 0 and char.sanity < 3 then
            broadcastEvent("warn", char.name .. " is Haunted (Sanity < 3): draw 1 Threat card at " ..
                (char.location or "?") .. ". Only " .. char.name ..
                " may fight or flee it — allies can't help. Discard it when resolved; it never festers.")
        end
    end

    -- Draw and reveal top Dawn card
    revealDawnCard()

    -- After dawn resolves, transition to Day phase
    Wait.time(function()
        beginDayPhase()
    end, 2.0)
end

-----------------------------------------------------------------------
-- Festering (Design §15.1): count loose Threat cards and Boss standees
-- sitting on/near a location tile at Dawn.
--   * Ordinary threats: +1 Doom each, capped at +3 so a bad night can't
--     cascade into an instant loss.
--   * Bosses are NOT capped: each phase boss festers +2, the Treeguard
--     mini-boss +1. Leaving THE monster alive is never the cheap option.
-----------------------------------------------------------------------
local FESTER_RADIUS     = 7    -- x/z distance from a tile that counts as "on the map"
local FESTER_THREAT_CAP = 3
local BOSS_FESTER = {          -- Doom per Dawn while on the map (uncapped)
    ["Boss:Treeguard"] = 1,    -- mini-boss (Design §14.2)
}
local BOSS_FESTER_DEFAULT = 2  -- Deerclops, Eye of Terror, The Source

local function locationTilePositions()
    local tiles = {}
    for _, locName in ipairs({"JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"}) do
        local tile = getLocationTile(locName)
        if tile then table.insert(tiles, tile.getPosition()) end
    end
    return tiles
end

local function nearATile(obj, tiles)
    local p = obj.getPosition()
    for _, tp in ipairs(tiles) do
        local dx, dz = p.x - tp.x, p.z - tp.z
        if (dx * dx + dz * dz) <= (FESTER_RADIUS * FESTER_RADIUS) then return true end
    end
    return false
end

-- Is this boss standee out of the Boss Pool and standing on the map?
-- (Bagged objects are invisible to getAllObjects, so a defeated/appeased
-- boss returned to the pool is never "on the map".)
function isBossOnMap(bossTag)
    local standee = findOneByTag(bossTag)
    if not standee then return false end
    return nearATile(standee, locationTilePositions())
end

-- Returns two values: capped ordinary-threat fester and uncapped boss fester.
function countFesteringThreats()
    local tiles = locationTilePositions()
    if #tiles == 0 then return 0, 0 end

    -- Loose (drawn) threat cards on the map. Cards still in the deck don't
    -- count — and neither does a pending face-down Wrongness card (§ batch 3:
    -- it is unresolved, not fled-from; it starts festering once revealed).
    local pendingWrongGuid = gameState.wrongness and gameState.wrongness.guid
    local threatCount = 0
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        if obj.type == "Card" and obj.guid ~= pendingWrongGuid and nearATile(obj, tiles) then
            threatCount = threatCount + 1
        end
    end

    -- Active boss standees on the map.
    local bossDoom = 0
    for _, obj in ipairs(findAllByTag("Boss")) do
        if nearATile(obj, tiles) then
            local rate = BOSS_FESTER_DEFAULT
            for tag, r in pairs(BOSS_FESTER) do
                if obj.hasTag(tag) then rate = r break end
            end
            bossDoom = bossDoom + rate
        end
    end

    return math.min(FESTER_THREAT_CAP, threatCount), bossDoom
end

function checkDoomThresholds()
    local d = gameState.doom
    local T = DOOM_THRESHOLDS
    if d >= T.night and not gameState.ongoingDawnEffects.doom10 then
        gameState.ongoingDawnEffects.doom10 = true
        broadcastEvent("warn", "DOOM THRESHOLD " .. T.night .. ": Night threat draws +1 at all locations.")
        safecall(function() nudgeCameraToDoom() end, "CameraNudge")
    end
    if d >= T.scarcity and not gameState.ongoingDawnEffects.doom15 then
        gameState.ongoingDawnEffects.doom15 = true
        broadcastEvent("warn", "DOOM THRESHOLD " .. T.scarcity .. ": Scarcity — every Market craft costs +1 extra resource (any type you hold, your choice).")
    end
    if d >= T.tick and not gameState.ongoingDawnEffects.doom20 then
        gameState.ongoingDawnEffects.doom20 = true
        broadcastEvent("warn", "DOOM THRESHOLD " .. T.tick .. ": All characters lose +1 Sanity at Tick.")
    end
    if d >= T.anyPhaseBosses and not gameState.ongoingDawnEffects.doom25 then
        gameState.ongoingDawnEffects.doom25 = true
        broadcastEvent("warn", "DOOM THRESHOLD " .. T.anyPhaseBosses .. ": Boss-level threats can appear in any phase.")
        broadcastEvent("gain", "DOOM " .. T.anyPhaseBosses .. " — Nothing Left to Lose. +1 attack die for everyone; Rest heals +1 Health anywhere. Go down swinging.")
    end
end

-----------------------------------------------------------------------
-- The Last Dawn (Design §15.7, design_batch2.md §3): Day 7's Dawn is
-- fixed, not drawn — scheduled by the clock like the Treeguard, so every
-- campaign lands on the same held breath. Pure tone, no penalty: the
-- first Dawn all week that isn't a threat.
-----------------------------------------------------------------------
-- Where the drawn Dawn card is displayed (in front of the phase decks) and
-- where yesterday's card is stacked when the next one is drawn. Cards
-- dropped on the same spot pile into a face-up discard deck, so nobody
-- ever has to tidy Dawn cards by hand.
local DAWN_REVEAL_OFFSET = Vector(0, 1, -2.5)   -- relative to the phase deck
local DAWN_DISCARD_POS   = {x = -4.5, y = 1.5, z = 9.5}

local function discardActiveDawnCard()
    local guid = gameState.activeDawn and gameState.activeDawn.cardGuid
    if not guid then return end
    local card = getObjectFromGUID(guid)
    if card then
        card.setPositionSmooth({DAWN_DISCARD_POS.x, DAWN_DISCARD_POS.y + 1, DAWN_DISCARD_POS.z}, false, true)
        card.setRotationSmooth({0, 180, 0}, false, true)  -- face up on the pile
    end
end

function revealLastDawn()
    -- dispatchDawnEffect normally cleans up the previous Dawn's ongoing
    -- effects; the Last Dawn bypasses the deck, so do it here.
    if gameState.activeDawn and gameState.activeDawn.prevId then
        local prev = DAWN_EFFECTS[gameState.activeDawn.prevId]
        if prev and prev.onCleanup then
            safecall(function() prev.onCleanup() end, "DawnCleanup:" .. gameState.activeDawn.prevId)
        end
    end
    safecall(discardActiveDawnCard, "DawnDiscard")

    broadcastEvent("phase", "DAWN: THE LAST DAWN")
    broadcastEvent("proc", "The sky is trying to lighten. Survive until it's over.")

    gameState.activeDawn = {
        id = "LAST_DAWN",
        title = "The Last Dawn",
        description = "The sky is trying to lighten. Survive until it's over.",
    }
    gameState.dawnChecklist = {}
    safecall(function() refreshDawnChecklist() end, "DawnChecklist")
end

function revealDawnCard()
    -- The final day never draws from the phase deck — the finale is scripted.
    if gameState.day >= getTotalDays() then
        revealLastDawn()
        return
    end

    local phase = gameState.phase
    local deck = getPhaseDeck(phase)

    if not deck then
        broadcastEvent("proc", "No Phase " .. phase .. " deck found — skipping Dawn card.")
        gameState.activeDawn = nil
        return
    end

    -- Take the top card
    local qty = deck.getQuantity and deck.getQuantity() or 1
    if qty <= 0 then
        broadcastEvent("proc", "Phase " .. phase .. " deck is empty — no Dawn card.")
        gameState.activeDawn = nil
        return
    end

    -- Yesterday's card moves itself to the discard pile first.
    safecall(discardActiveDawnCard, "DawnDiscard")

    deck.takeObject({
        -- In front of the deck row — the old +x offset dropped the card
        -- on top of the Threat deck.
        position = deck.getPosition() + DAWN_REVEAL_OFFSET,
        rotation = {0, 180, 0},  -- face up
        smooth   = true,
        callback_function = function(card)
            local name = card.getNickname() or "Unknown Dawn"
            local desc = card.getDescription() or ""
            broadcastEvent("phase", "DAWN: " .. name)
            broadcastEvent("proc", desc)

            gameState.activeDawn = {
                id = name,
                title = name,
                description = desc,
                cardGuid = card.getGUID and card.getGUID() or card.guid,
            }

            -- Dispatch dawn effect
            dispatchDawnEffect(card)
        end
    })
end

function beginDayPhase()
    gameState.subPhase = "Day"
    gameState.turnIndex = 1
    safecall(function() setPhaseMood("Day") end, "Mood")
    noteInteraction()
    startIdleWatcher()

    -- Reset all players' actions and trade counters
    gameState.combatContext = nil   -- no fight carries across into a new Day
    gameState.tradesThisTurn = {}
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char.actionsLeft = ACTIONS_PER_TURN
        else
            char.actionsLeft = 0
        end
    end

    if gameState.turnStyle == "rotate" then
        broadcastEvent("proc", "Rotation turns: take 1 action, then the next player goes — around the table until everyone has used all "
            .. ACTIONS_PER_TURN .. ". Passing without acting forfeits your remaining actions.")
    end

    -- Start the first player's turn
    advanceToNextPlayer()
end

function advanceToNextPlayer()
    -- New turn: reset idle tracking
    gameState.idleNudgedThisTurn = false
    noteInteraction()
    gameState.actedThisVisit = false

    -- Find the next standing player with actions left. Full-turn default
    -- marches once down the turn order; the rotation variant (§11.2) wraps
    -- around the table until every action is spent.
    local n = #gameState.turnOrder
    local rotate = (gameState.turnStyle == "rotate")
    local tries = 0
    while n > 0 and ((rotate and tries < n) or (not rotate and gameState.turnIndex <= n)) do
        if rotate then
            gameState.turnIndex = ((gameState.turnIndex - 1) % n) + 1
        end
        local color = gameState.turnOrder[gameState.turnIndex]
        local char = gameState.activeChars[color]
        if char and not char.down and char.actionsLeft > 0 then
            gameState.activeColor = color
            -- Per-turn perk windows reset with each new turn (§6.1 / §6.5).
            gameState.jamesRerollUsed = false
            gameState.lucaRallyUsed = false
            -- Backboard Block (§6.3) holds "until Rayman's next turn".
            if char.name == "Rayman" and gameState.raymanDefending then
                gameState.raymanDefending = false
                broadcastEvent("proc", "Rayman's Backboard Block ends — he steps out of the defensive stance.")
            end
            safecall(function() markTurnStart() end, "Telemetry")
            broadcastEvent("proc", char.name .. "'s turn. " .. char.actionsLeft .. " action(s) remaining.")
            -- G.2: Update UI for new active player
            refreshPhaseBanner()
            updateActivePlayerIndicator()
            pulseHandZone(color)
            -- Audible turn-start cue for players watching the board, not the banner
            safecall(function() Audio.playTurnPing() end, "Audio")
            return
        end
        gameState.turnIndex = gameState.turnIndex + 1
        tries = tries + 1
    end

    -- All players done — advance to Dusk
    gameState.activeColor = nil
    stopIdleWatcher()
    broadcastEvent("phase", "All players have finished. Advancing to Dusk.")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
    beginDusk()
end

function endPlayerTurn(color)
    safecall(function() recordTurnEnd(color) end, "Telemetry")
    local char = gameState.activeChars[color]
    if char then
        char.feastActive = nil   -- The Feast's free cooking ends with her turn
        if gameState.turnStyle == "rotate" and gameState.actedThisVisit and char.actionsLeft > 0 then
            -- Rotation variant: acted this visit — remaining actions stay
            -- banked and priority passes around the table.
            broadcastEvent("proc", char.name .. " passes. (" .. char.actionsLeft .. " action(s) banked)")
        else
            if gameState.turnStyle == "rotate" and not gameState.actedThisVisit and char.actionsLeft > 0 then
                broadcastEvent("proc", char.name .. " passes without acting — remaining actions forfeited.")
            end
            char.actionsLeft = 0
        end
    end
    -- Drop any half-finished targeted action (MOVE HERE / CRAFT / COOK buttons)
    safecall(function() clearActionTargets() end, "ClearTargets")
    safecall(function() finishCombat() end, "FinishCombat")  -- an open press window resolves before priority passes
    gameState.undoSnapshot = nil  -- undo can't cross a turn boundary
    gameState.turnIndex = gameState.turnIndex + 1
    advanceToNextPlayer()
end

function spendAction(color, actionName)
    local char = gameState.activeChars[color]
    if not char then
        broadcastEvent("damage", "Error: no character for " .. color)
        return false
    end
    if char.down then
        broadcastToColor("You are Down and cannot act.", color, BROADCAST_COLORS.damage)
        return false
    end
    if char.actionsLeft <= 0 then
        broadcastToColor("No actions remaining. Click Pass to end your turn.", color, BROADCAST_COLORS.damage)
        return false
    end
    if gameState.turnStyle == "rotate" and gameState.actedThisVisit then
        broadcastToColor("Rotation turns: that was your 1 action for this go-around. Click Pass — your remaining actions are kept for your next go.",
            color, BROADCAST_COLORS.damage)
        return false
    end
    -- QoL: Snapshot before spending so undo is possible
    safecall(function() snapshotForUndo(color) end, "Undo")
    char.actionsLeft = char.actionsLeft - 1
    gameState.actedThisVisit = true
    broadcastEvent("proc", char.name .. " uses " .. actionName .. ". (" .. char.actionsLeft .. " left)")
    return true
end

-----------------------------------------------------------------------
-- Dusk
-----------------------------------------------------------------------
function beginDusk()
    gameState.subPhase = "Dusk"
    gameState.duskMoves = {}   -- one scramble move per character
    gameState.duskReady = {}   -- per-player ready-check for Night
    safecall(function() clearActionTargets() end, "ClearTargets")
    safecall(function() setPhaseMood("Dusk") end, "Mood")
    safecall(function() refreshDuskReadyLabel() end, "DuskReady")

    -- Phase 2.5: the Treeguard wakes at Dusk of Day 4 (Design §14.2).
    if gameState.day == 4 then
        safecall(function() wakeTreeguard() end, "Treeguard")
    end

    refreshPhaseBanner()
    broadcastEvent("phase", "DUSK — Last chance to move: each character may scramble 1 tile (costs 1 Hunger). You sleep where you stand.")

    -- Night Sounds (design_batch3.md §1): if the top of the Threat deck is a
    -- Hard threat, a distant growl crosses the table. Pure ambient
    -- information — no rule text, no broadcast, deliberately unexplained.
    safecall(function()
        local deck = getThreatDeck()
        local top = deck and deck.getObjects and deck.getObjects()[1]
        local topName = top and (top.nickname ~= "" and top.nickname or top.name)
        if topName and THREAT_TYPE_BY_NAME and THREAT_TYPE_BY_NAME[topName] == "Hard" then
            Audio.playGrowl()
        end
    end, "NightSounds")

    -- QoL: Threat preview — show threat level per location before sleep
    broadcastEvent("proc", "--- THREAT PREVIEW ---")
    for _, locName in ipairs({"JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"}) do
        local baseRate = LOCATION_THREAT_RATE[locName] or 0
        if gameState.ongoingDawnEffects.doom10 then baseRate = baseRate + 1 end
        if gameState.ongoingDawnEffects.bloodMoon then baseRate = baseRate + 1 end
        if (gameState.loudSignature or {})[locName] then baseRate = baseRate + 1 end
        local barricades = (gameState.barricades or {})[locName] or 0
        baseRate = math.max(0, baseRate - barricades)

        -- Count players here
        local playersHere = {}
        for color, char in pairs(gameState.activeChars) do
            if not char.down and char.location == locName then
                table.insert(playersHere, char.name)
            end
        end

        if #playersHere > 0 then
            local risk = "safe"
            if baseRate >= 3 then risk = "DANGEROUS"
            elseif baseRate >= 2 then risk = "risky"
            elseif baseRate >= 1 then risk = "moderate" end
            local barricadeNote = barricades > 0 and " [barricaded]" or ""
            broadcastEvent("proc", "  " .. locName .. ": " .. table.concat(playersHere, ", ") ..
                " | Threat draws: " .. baseRate .. " (" .. risk .. ")" .. barricadeNote)
        end
    end

    -- James end-of-Day reminder: if his Energy Drink is still unconsumed,
    -- the Wired constraint will hit him at Tick. Surface this once per day.
    do
        local jamesColor, jamesChar = nil, nil
        for c, ch in pairs(gameState.activeChars) do
            if ch.name == "James" and not ch.down then jamesColor, jamesChar = c, ch; break end
        end
        if jamesChar and not gameState.jamesEnergyDrinkUsed then
            gameState.dailyAlerts = gameState.dailyAlerts or {}
            gameState.dailyAlerts[jamesColor] = gameState.dailyAlerts[jamesColor] or {}
            if not gameState.dailyAlerts[jamesColor].jamesEnergy then
                gameState.dailyAlerts[jamesColor].jamesEnergy = true
                printToColor("Reminder: you haven't drunk an Energy Drink today. Wired triggers at Tick: −2 Sanity tonight unless one is consumed first.",
                             jamesColor, {1, 0.85, 0.4})
            end
        end
    end

    -- Per-player Dusk warnings: advisory printToColor messages. Each player
    -- may still scramble 1 tile (1 Hunger) via the Dusk panel before Night.
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            local loc = char.location
            local othersHere = 0
            for c2, ch2 in pairs(gameState.activeChars) do
                if c2 ~= color and not ch2.down and ch2.location == loc then
                    othersHere = othersHere + 1
                end
            end

            -- Alone at a sport court
            if (loc == "BasketballCourt" or loc == "BadmintonCourt") and othersHere == 0 then
                printToColor("Warning: alone at " .. loc .. " — +1 Threat draw and no sleep regen tonight. " ..
                             "Survive it, though, and you salvage 2 resources at Dawn.",
                             color, {1, 0.85, 0.4})
            end

            -- Coco alone at non-house tile
            if char.name == "Coco" and othersHere == 0 then
                local isHouse = (loc == "JamesHouse" or loc == "RaymanHouse" or loc == "EllieLucaHouse")
                if not isHouse then
                    printToColor("Warning: Coco alone at non-house tile — −3 Sanity (No Home constraint).",
                                 color, {1, 0.85, 0.4})
                end
            end
        end
    end

    -- Public no-light reminder (item tracking is private to each hand zone,
    -- so we broadcast a generic prompt rather than naming who lacks a light).
    broadcastEvent("warn", "Reminder: anyone without a Flashlight (Battery), Lantern, or Fire suffers a Charlie attack tonight (2 Sanity + 1 Health, +1 each per consecutive dark night). Coco is immune.")

    -- Open the Dusk scramble window. Night begins when the host clicks
    -- Resolve Night (the banner CTA pulses it) — no auto-advance, so the
    -- table has time to argue about who sleeps where.
    if UI then UI.show("duskPanel") end
    broadcastEvent("proc", "Scramble now if you must (Dusk panel, 1 tile, 1 Hunger each). Click 'Ready for Night' when settled — Night begins when everyone has. (Host's Resolve Night also works.)")
end

-----------------------------------------------------------------------
-- Dusk ready-check: each seated player with a living character clicks
-- Ready; when everyone eligible is ready, Night begins automatically.
-- The host's Resolve Night button remains as a manual override (and
-- the only path when no eligible player is seated, e.g. hotseat).
-----------------------------------------------------------------------
function countDuskReady()
    local ready, total = 0, 0
    for color, ch in pairs(gameState.activeChars) do
        if not ch.down then
            local seated = false
            pcall(function()
                local p = Player[color]
                seated = (p and p.seated) or false
            end)
            if seated then
                total = total + 1
                if (gameState.duskReady or {})[color] then ready = ready + 1 end
            end
        end
    end
    return ready, total
end

function refreshDuskReadyLabel()
    if not UI then return end
    local ready, total = countDuskReady()
    if total > 0 then
        UI.setAttribute("duskReadyBtn", "text",
            "I'm settled — Ready for Night  (" .. ready .. "/" .. total .. ")")
    else
        UI.setAttribute("duskReadyBtn", "text", "Host: click Resolve Night when settled")
    end
end

function toggleDuskReady(color)
    if gameState.subPhase ~= "Dusk" then return end
    local char = gameState.activeChars[color]
    if not char then
        broadcastToColor("You have no character in this game.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.duskReady = gameState.duskReady or {}
    gameState.duskReady[color] = not gameState.duskReady[color] or nil

    local ready, total = countDuskReady()
    if gameState.duskReady[color] then
        broadcastEvent("proc", char.name .. " is settled for the night. (" .. ready .. "/" .. total .. " ready)")
    else
        broadcastEvent("proc", char.name .. " is up again. (" .. ready .. "/" .. total .. " ready)")
    end
    refreshDuskReadyLabel()

    if total > 0 and ready >= total then
        broadcastEvent("phase", "Everyone is settled — night falls.")
        Wait.time(function()
            if gameState.subPhase == "Dusk" then beginNight() end
        end, 1.5)
    end
end

-----------------------------------------------------------------------
-- Night trigger (F.9 lives in night.lua)
-----------------------------------------------------------------------
function beginNight()
    gameState.subPhase = "Night"
    if UI then UI.hide("duskPanel") end
    safecall(function() setPhaseMood("Night") end, "Mood")
    safecall(function() Audio.startNightAmbience() end, "Audio")
    refreshPhaseBanner()
    broadcastEvent("phase", "NIGHT — Resolving threats and sleep.")
    safecall(function() ResolveNight() end, "Night")
end
