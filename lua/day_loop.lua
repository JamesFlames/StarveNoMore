-- day_loop.lua  (F.4 — Day lifecycle: Dawn advance, Dusk, Night trigger.
-- The turn engine — beginDayPhase/advanceToNextPlayer/endPlayerTurn/
-- spendAction and the idle nudge — lives in turns.lua.)

function BeginDay()
    -- TTS's built-in Turns system stays off — this mod runs its own turns.
    pcall(function() if Turns then Turns.enable = false end end)
    -- Phase 1: Dawn
    gameState.subPhase = "Dawn"
    gameState.dayLog = {}
    gameState.dailyAlerts = {}  -- reset one-per-day urgent-hint flags
    gameState.raymanMovedToday = false  -- Loud constraint resets each day
    gameState.raymanTilesMovedToday = 0 -- 3p Big Appetite relief reads this (§20.1)
    gameState.raymanFoughtToday = false
    gameState.raymanDefending = false   -- Backboard Block never outlives the night
    gameState.jamesPeekUsed = false     -- Pattern Recognition: once per day (§6.1)
    gameState.lucaRallyUsed = false     -- Rally: once per ROUND, any turn (§6.5)
    gameState.driftedThisRound = {}     -- Ghost drift: one tile per round (§16.4)
    gameState.loudSignature = {}        -- Posterize echo lasts one night only
    safecall(function() setNightOmen(false) end, "NightOmen")  -- last night's moon sets
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

    -- The Rotting Autumn (foodSpoilsAtDawn): "1 Provisions token spoils per location at
    -- Dawn." Held Provisions are per-player, so "per location" resolves to the
    -- fullest larder at each occupied tile — one spoiled ration per place,
    -- not per person, and taken from whoever can most afford it.
    if (gameState.scenarioFlags or {}).foodSpoilsAtDawn then
        for _, locName in ipairs(LOCATION_ORDER) do
            local bestColor, bestFood = nil, 0
            for color, ch in pairs(gameState.activeChars) do
                if not ch.down and ch.location == locName then
                    local held = (getPlayerResources(color) or {}).Provisions or 0
                    if held > bestFood then bestColor, bestFood = color, held end
                end
            end
            if bestColor then
                takeResourceFromPlayer(bestColor, "Provisions", 1)
                broadcastEvent("damage", gameState.activeChars[bestColor].name ..
                    " loses 1 Provisions at " .. locName .. " — it turned overnight (The Rotting Autumn).")
            end
        end
    end

    -- Moonlit Salvage (Design §7.4/§7.5): anyone who spent the night at a
    -- sport court and is still standing gathers 2 resources at Dawn.
    for color, char in pairs(gameState.activeChars) do
        if not char.down and (char.location == "BasketballCourt" or char.location == "BadmintonCourt") then
            broadcastEvent("gain", char.name .. " survived the night at " .. char.location ..
                " — Moonlit Salvage: 2 resources delivered to your board.")
            safecall(function() gatherRandomResources(color, char.location, 2) end, "MoonlitSalvage")
            -- Dare — the court floodlights (P1_LIGHTS_FLICKER): survivors
            -- claim the prize. (The flag is cleaned up by revealDawnCard's
            -- dispatch below, so it is still readable here.)
            if gameState.ongoingDawnEffects.dareCourtGlow then
                broadcastEvent("gain", char.name .. " braved the glowing court — the dare pays: 2 Market cards, dealt to their hand.")
                safecall(function()
                    local mdeck = getMarketDeck()
                    if mdeck and (mdeck.getQuantity and mdeck.getQuantity() or 0) >= 2 then
                        mdeck.deal(2, color)
                    end
                end, "DareClaim")
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
    -- their tile at Dawn. It is real to them. Discard it once resolved; it's
    -- not real, so it never festers.
    --
    -- Allies can now BUY IN (§10.1, 2026-07): one at the haunted character's
    -- tile may pay 1 Sanity to see what they see and fight it alongside them.
    -- As pure isolation the rule was the harshest in the game — it stripped
    -- the cooperative layer from the player who most needed it, at the worst
    -- moment, compounding daily, converting a struggling player into a solo
    -- player inside a co-op. The buy-in keeps every good part (help is
    -- neither free nor automatic, and the helper takes on the madness to
    -- reach you) and moves the decision to the table, where "who goes in
    -- after them" is the storied-collaboration beat §1.4 ranks third.
    --
    -- gameState.haunted is the record the buy-in reads; rebuilt each Dawn so
    -- yesterday's witnesses don't carry over.
    gameState.haunted = {}
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char.sanity > 0 and char.sanity < 3 then
            gameState.haunted[color] = { location = char.location, witnesses = {} }
            broadcastEvent("warn", char.name .. " is Haunted (Sanity < 3): draw 1 Threat card at " ..
                (char.location or "?") .. ". Only " .. char.name ..
                " may fight or flee it. Discard it when resolved; it never festers.")
            broadcastEvent("proc", "An ally standing with " .. char.name ..
                " may pay 1 Sanity to SEE what they see — and then fight it with them (the Witness button).")
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
        broadcastEvent("gain", "DOOM " .. T.anyPhaseBosses .. " — Nothing Left to Lose. +1 attack die for everyone; Rest heals +1 Health anywhere. Go down swinging.")
    end
end

-----------------------------------------------------------------------
-- The Last Dawn (Design §15.7, design_batch2.md §3): Day 7's Dawn is
-- fixed, not drawn — scheduled by the clock like the Treeguard, so every
-- campaign lands on the same held breath. Pure tone, no penalty: the
-- first Dawn all week that isn't a threat.
-----------------------------------------------------------------------
-- Where the drawn Dawn card is displayed and where yesterday's card is
-- stacked when the next one is drawn. Both are FIXED board positions —
-- the phase decks live in the under-table library, so nothing can be
-- placed relative to them. Cards dropped on the discard spot pile into a
-- face-up deck, so nobody ever has to tidy Dawn cards by hand.
-- MIRRORS DAWN_REVEAL_WORLD / DAWN_DISCARD_WORLD in scripts/board_geometry.py,
-- which is also where generate_assets prints the "DAWN EVENTS" box and its two
-- captioned slots. At the old (-7.5, 9.5) a 2.3x3.2 card lay across the Day
-- Counter's printed frame and the board title, so the day's event read as a
-- stray card. tests/test_cross_refs.py guards the mirror.
local DAWN_REVEAL_POS    = {x = 6.3, y = 1.9, z = 4.9}
local DAWN_DISCARD_POS   = {x = 9.3, y = 1.9, z = 4.9}

local function discardActiveDawnCard()
    local guid = gameState.activeDawn and gameState.activeDawn.cardGuid
    if not guid then return end
    local card = getObjectFromGUID(guid)
    if card then
        -- Instant, not smooth: while the old card glided away, the new
        -- card could land on it mid-flight and merge into a deck — which
        -- destroyed the new card's handle and killed the reveal callback.
        card.setPosition({DAWN_DISCARD_POS.x, DAWN_DISCARD_POS.y + 1, DAWN_DISCARD_POS.z})
        card.setRotation({0, 180, 0})  -- face up on the pile
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

-----------------------------------------------------------------------
-- The First Dawn (Design §15.9) — the guided opening.
--
-- Day 1's Dawn is fixed, like Day 7's. First turns are structurally the
-- hardest in most games ([PrinciplesOfGoodBoardGames.md §9]) — widest
-- options, least context — and here turn one asks a brand-new player to
-- choose among 8 action types across a 5-tile map with a 3-action budget,
-- a private hand of 5 cards, a perk set, a constraint and a Signature,
-- immediately after a 12-step setup. §22 identifies the guided opening as
-- the highest-value, lowest-cost onboarding intervention available.
--
-- It uses the precedent the design already set twice: the Last Dawn
-- (§15.7) and the Treeguard (§14.2) are both scheduled rather than drawn,
-- on the stated logic that predictable structure with unpredictable
-- details is the DST seasons principle. Applying it to the opening costs
-- the same thing it cost at the other end of the week — Day 1 stops being
-- a surprise — and buys a first turn nobody has to guess their way
-- through. It also means the Phase 1 deck only ever has to cover Day 2.
--
-- Severity ●○○○○, no penalty. Tone and a nudge, nothing else.
-----------------------------------------------------------------------
function revealFirstDawn()
    broadcastEvent("phase", "DAWN: THE FIRST MORNING")
    broadcastEvent("proc", "The street looks exactly as it always has, which is somehow worse. Gather what you can. The dark is eight hours away.")

    gameState.activeDawn = {
        id = "FIRST_DAWN",
        title = "The First Morning",
        description = "No penalty today — the world hasn't started yet. Gather what you can. The dark is eight hours away.",
    }
    gameState.dawnChecklist = {}
    safecall(function() refreshDawnChecklist() end, "DawnChecklist")
end

function revealDawnCard()
    -- The first day never draws either — the opening is scripted so that a
    -- brand-new table's hardest turn isn't also a surprise (§15.9).
    if gameState.day <= 1 then
        revealFirstDawn()
        return
    end
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

    -- Assigned immediately below, read by the callback once the card lands.
    local preflight = nil

    local taken = deck.takeObject({
        position = {DAWN_REVEAL_POS.x, DAWN_REVEAL_POS.y, DAWN_REVEAL_POS.z},
        rotation = {0, 180, 0},  -- face up
        smooth   = true,
        callback_function = function(card)
            safecall(function() _dawnCardRevealed(card, preflight) end, "DawnReveal")
        end
    })

    -- takeObject's handle is alive the instant it returns. By the time the
    -- callback fires the card may have merged into a deck at the reveal spot,
    -- killing the handle — and then re-finding it fails too, because what is
    -- sitting there is a deck, not a card. Snapshot the identity now, while
    -- the handle is guaranteed good, so the Dawn card is still announced and
    -- still resolves even if every handle dies in flight.
    preflight = _cardSnapshot(taken)
end

-- Identity snapshot of a card handle, or nil if the handle is already dead.
-- Any field access on a destroyed object throws "cannot access field
-- getNickname of userdata<LuaObject>" (docs/tts-interface.md), so every read
-- goes through one pcall.
function _cardSnapshot(obj)
    if not obj then return nil end
    local ok, info = pcall(function()
        local tags = {}
        if obj.getTags then tags = obj.getTags() or {} end
        return {
            name = obj.getNickname() or "",
            desc = obj.getDescription() or "",
            guid = (obj.getGUID and obj.getGUID()) or obj.guid,
            tags = tags,
        }
    end)
    if ok and info and info.name ~= "" then return info end
    return nil
end

function _findCardAtDawnRevealSpot()
    for _, obj in ipairs(findAllByTag("PhaseCard")) do
        if obj.type == "Card" then
            local p = obj.getPosition()
            local dx, dz = p.x - DAWN_REVEAL_POS.x, p.z - DAWN_REVEAL_POS.z
            if (dx * dx + dz * dz) < 4 then return obj end
        end
    end
    return nil
end

function _dawnCardRevealed(card, preflight)
    -- Prefer the handle we were handed; if it died in flight fall back to the
    -- pre-flight snapshot for the text and re-find a live card on the reveal
    -- spot for the effect. Either source alone is enough to run the Dawn.
    local live = card
    local data = _cardSnapshot(card)
    if not data then
        live = _findCardAtDawnRevealSpot()
        data = preflight or _cardSnapshot(live)
    end
    if not data then
        broadcastEvent("proc", "The Dawn card landed oddly — check the reveal spot by the Dawn discard pile.")
        return
    end

    broadcastEvent("phase", "DAWN: " .. data.name)
    if data.desc ~= "" then broadcastEvent("proc", data.desc) end

    gameState.activeDawn = {
        id = data.name,
        title = data.name,
        description = data.desc,
        cardGuid = data.guid,
    }

    -- Point every camera at the card before its effect fires (I.11): the
    -- Dawn reveal is the day's headline, and a table looking at five
    -- different corners misses it. No-ops on a dead handle.
    safecall(function() nudgeCameraToDawnCard(live) end, "CameraNudge")

    -- Dispatch dawn effect. `live` may be nil if the card merged away — the
    -- effect is resolved from the snapshot, and handlers are safecall-wrapped.
    dispatchDawnEffect(live, data)
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

    -- The Watching Jar (Eye of Terror trophy): the team reads the top of the
    -- Threat deck now, while the scramble window is open and the information
    -- can still change where people stand.
    safecall(function() resolveWatchingJar() end, "WatchingJar")

    gameState.duskPending = {}
    refreshPhaseBanner()
    if gameState.duskSecret then
        broadcastEvent("phase", "DUSK — SECRET COMMITMENT. Argue it out, then choose: your scramble is banked and nobody sees it until the light goes. You sleep where you stand.")
        broadcastEvent("proc", "Talk all you like. Nobody can check that you did what you said.")
    else
        broadcastEvent("phase", "DUSK — Last chance to move: each character may scramble 1 tile (costs 1 Hunger). You sleep where you stand.")
    end

    -- Night Sounds (Design §15.8): if the top of the Threat deck is a Hard
    -- threat, a distant growl crosses the table. Pure ambient information —
    -- no rule text, no broadcast, deliberately unexplained.
    --
    -- Double-coded since 2026-07 (§18.19 item 2): the growl now always ships
    -- with a moon glyph in the Phase Banner, because "the next threat is
    -- Hard" IS a gameable bit and audio-only meant deaf, hard-of-hearing and
    -- muted players simply didn't get it. Both channels are computed from the
    -- same boolean below, so they can never disagree, and the visual is set
    -- OUTSIDE the audio safecall — a missing sound file must not cost a
    -- player the only channel they can perceive.
    local hardNext = false
    safecall(function()
        local deck = getThreatDeck()
        local top = deck and deck.getObjects and deck.getObjects()[1]
        local topName = top and (top.nickname ~= "" and top.nickname or top.name)
        hardNext = topName and THREAT_TYPE_BY_NAME
            and THREAT_TYPE_BY_NAME[topName] == "Hard" or false
    end, "NightSoundsPeek")
    safecall(function() setNightOmen(hardNext) end, "NightOmen")
    if hardNext then
        safecall(function() Audio.playGrowl() end, "NightSounds")
    end

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
    --
    -- Under secret commitment these describe where you stand RIGHT NOW, which
    -- is the honest thing to warn about — where you (or anyone) will end up is
    -- precisely what nobody is allowed to know yet.
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
    if UI and not customUIHidden then UI.show("duskPanel") end
    broadcastEvent("proc", "Scramble now if you must (Dusk panel, 1 tile, 1 Hunger each). Click 'Ready for Night' when settled — Night begins when everyone has. (Host's Resolve Night also works.)")
end

-----------------------------------------------------------------------
-- Night trigger (F.9 lives in night.lua)
-----------------------------------------------------------------------
function beginNight()
    gameState.subPhase = "Night"
    if UI then UI.hide("duskPanel") end
    -- Secret Dusk commitment (§11.3 variant): every banked scramble lands now,
    -- simultaneously, before anything else reads a position.
    safecall(function() revealDuskCommitments() end, "DuskReveal")
    safecall(function() setPhaseMood("Night") end, "Mood")
    safecall(function() Audio.startNightAmbience() end, "Audio")
    refreshPhaseBanner()
    broadcastEvent("phase", "NIGHT — Resolving threats and sleep.")
    safecall(function() ResolveNight() end, "Night")
end
