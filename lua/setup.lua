-- setup.lua  (F.3 — Setup flow, bare-bones without UX walkthrough)

function Setup(hostColor)
    -- Guard: a second Setup on a running game would re-deal the Market and
    -- overwrite the picked party with the default seat assignment.
    if gameState.started then
        broadcastEvent("damage", "Game already started. Click Restart first.")
        return
    end

    broadcastEvent("phase", "Setting up Starve No More...")

    -- 1. Pick a random path variant. applyPathVariant rebuilds the Move
    -- graph AND repaints the board, so the printed lines match the routes.
    local variants = {}
    for name, _ in pairs(PATH_LAYOUTS) do table.insert(variants, name) end
    table.sort(variants)   -- gameRoll must index a stable list
    local pick = applyPathVariant(variants[gameRoll(#variants)])

    -- 2. Shuffle each Phase deck
    for p = 1, 4 do
        local deck = getPhaseDeck(p)
        if deck then deck.shuffle() end
    end

    -- 3. Shuffle and deal Market display (empty slots only)
    dealMarketDisplay()

    -- 4. Shuffle Threat deck
    local threatDeck = getThreatDeck()
    if threatDeck then threatDeck.shuffle() end

    -- 5. Assign characters to seated players. Wipe the previous party
    -- first so a re-setup can never leave stale characters around.
    gameState.activeChars = {}
    gameState.dailyAlerts = {}
    gameState.resources = {}   -- fresh held-resource counts

    local seated = getActivePlayerColors()
    gameState.playerCount = #seated
    gameState.turnOrder = seated
    gameState.turnIndex = 0

    -- Seat colour ↔ character follows CHARACTER_COLORS (a player's colour
    -- is determined by their character; the guided setup reseats players
    -- to enforce it — the bare path simply assigns by seat).
    local defaultAssignment = {}
    for name, c in pairs(CHARACTER_COLORS) do defaultAssignment[c] = name end

    local roster = {}   -- one "who is who" line instead of one broadcast each
    for _, color in ipairs(seated) do
        local charName = defaultAssignment[color]
        if charName then
            local stats = CHARACTER_STATS[charName]
            local home = CHARACTER_HOMES[charName] or "EllieLucaHouse"
            gameState.activeChars[color] = {
                name       = charName,
                health     = stats.health,
                maxHealth  = stats.health,
                hunger     = stats.hunger,
                maxHunger  = stats.hunger,
                sanity     = stats.sanity,
                maxSanity  = stats.sanity,
                actionsLeft = ACTIONS_PER_TURN,
                down       = false,
                briefed    = false,
                location   = home,
                signatureUsed = false,   -- Signature Move (§6.7): one per game
            }

            -- Move standee to its per-character slot at the home tile
            placeCharacterAtTile(charName, home)

            roster[#roster + 1] = charName .. " (" .. color .. ")"
        end
    end

    -- Characters nobody is playing leave the map for the bench.
    safecall(function() benchUnusedCharacters() end, "Bench")
    safecall(function() benchUnusedBoards() end, "BenchBoards")
    safecall(function() refreshQuickStartCard() end, "QuickStart")

    -- Starting hands: each character's personal items into their hand.
    safecall(function() dealStartingHands() end, "StartingHands")

    -- 6. Set Day=1, Doom=0
    gameState.day = 1
    gameState.doom = 0
    gameState.difficulty = gameState.difficulty or "standard"
    gameState.phase = getPhaseForDay(1)
    -- PreDawn = "waiting for Begin Day": the banner and CTA point the host
    -- at the Begin Day button instead of implying a Dawn is resolving.
    gameState.subPhase = "PreDawn"
    gameState.dayLog = {}
    gameState.chronicle = nil          -- fresh Week in Review record
    safecall(function() ensureChronicle() end, "Chronicle")
    safecall(function() recordSetupInChronicle() end, "Telemetry")
    gameState.combatContext = nil
    gameState.gameOverCause = nil
    gameState.bossHP = {}
    gameState.threatDamage = {}
    gameState.eyeLocation = nil
    gameState.sourceSplit = nil
    gameState.pendingSanityPenalty = {}
    gameState.loudSignature = {}
    gameState.wrongness = nil
    gameState.basementOpened = nil
    gameState.cluesFound = {}          -- Truth Run (§16.2)
    gameState.clueCount = 0
    gameState.cluesSurfaced = 0
    gameState.openingOffered = {}      -- guided opening (§15.9)
    gameState.duskPending = {}         -- secret Dusk commitments (§11.3)

    local counter = getDayCounter()
    if counter then counter.setValue(1) end

    moveDoomMarker(0)

    -- 7. Mark started
    gameState.started = true

    -- One idea at a time. Everything below used to fire inside this frame,
    -- on top of the market blurb and one line per seated character; the table
    -- got a dozen overlapping broadcasts before anyone had touched a card.
    local queue = {
        {"proc", "Playing today: " .. table.concat(roster, ", ") .. "."},
        {"proc", "Path layout: " .. pick .. " (the lines printed on the board are the routes you can walk)."},
    }
    for _, m in ipairs(tableOrientationMessages()) do queue[#queue + 1] = m end
    queue[#queue + 1] = {"phase", "Setup complete! Day 1 begins. Click 'Begin Day' on the Host Controls panel to reveal the first Dawn card."}
    stageBroadcasts(queue, 1.0)

    -- G.1/G.7: Refresh UI and apply tooltips
    Wait.time(function()
        refreshPhaseBanner()
        updateActivePlayerIndicator()
        applyTooltips()
        refreshDynamicTooltips()
    end, 1.0)
end

-----------------------------------------------------------------------
-- Starting hands (design §6): each character's personal item deck is
-- dealt into their player's hand. James's two Energy Drinks are resource
-- tokens (his Wired economy runs on tokens), placed beside his board.
-- Re-setup safe: a consumed deck simply no longer exists to deal.
-----------------------------------------------------------------------
-- A "starting hand" is the two-to-five personal item cards a character begins
-- with (content/cards_starting.csv) — Ellie's Cooking Knife, James's
-- Flashlight, and so on.
--
-- They used to be dealt into the TTS hand zone, where they stacked vertically
-- in mid-air (measured at y 9.5 to 24.4, tumbling) and showed only their
-- "STARTING" backs. They are now laid FACE UP in a neat row just outside the
-- player's own board, where they read at a glance and cannot float away.
--
-- Only the items whose `arrives` day is 1 come up face up — three per
-- character. The rest lie FACE DOWN in a second row behind them and turn over
-- at Dawn on their day (revealScheduledStartingItems). Five unique rules texts
-- per player, all landing before anyone has taken a single action, was the
-- biggest source of turn-one overload at the table, and the held-back cards
-- are the conditional single-use ones whose text means nothing until you know
-- the rule it hooks into (Pantry Key, Whistle, Toolbox, Spare Battery). Same
-- total power over the week, a third of the reading up front.
STARTING_ROW_DIST     = 3.2   -- distance out from the board: today's items
STARTING_RESERVE_DIST = 4.6   -- ...and the face-down "not yet" row behind them

-- One slot in a row laid along the board's long edge, pushed OUTWARD (away
-- from the map) so the cards never cover the board or the play area.
local function _startingRowSpot(base, ox, oz, dist, idx, count)
    local px_, pz_ = -oz, ox          -- perpendicular: the row direction
    local offset = (idx - 1) - (count - 1) / 2
    return {
        base.x + ox * dist + px_ * offset * 1.3,
        base.y + 0.6 + idx * 0.05,
        base.z + oz * dist + pz_ * offset * 1.3,
    }
end

-- "Day 2" / "Day 2 and Day 3" — for the message that tells a player the
-- face-down row is not something they have to read yet.
local function _dayPhrase(days)
    table.sort(days)
    local out = {}
    for _, d in ipairs(days) do out[#out + 1] = "Day " .. tostring(d) end
    if #out <= 1 then return out[1] or "" end
    return table.concat(out, " and ", 1, #out - 1) .. " and " .. out[#out]
end

function dealStartingHands()
    for color, char in pairs(gameState.activeChars) do
        local deck = findOneByTag("StartingHand:" .. char.name)
        local board = getPlayerBoard(char.name)
        if deck and board then
            local base = board.getPosition()
            local outward = Vector(base.x, 0, base.z)
            local len = math.sqrt(outward.x * outward.x + outward.z * outward.z)
            if len < 0.01 then outward = Vector(0, 0, -1); len = 1 end
            local ox, oz = outward.x / len, outward.z / len

            -- Snapshot the whole deal off the deck handle while it is known
            -- good (docs/tts-interface.md Rule 2), then take by guid. Sorted
            -- so today's items are taken FIRST: if the final take ever loses
            -- its handle to the deck collapsing, what strands is a card
            -- nobody needed yet rather than a weapon.
            local plan = {}
            for i, entry in ipairs(deck.getObjects() or {}) do
                local nick = entry.nickname or entry.name or ""
                plan[#plan + 1] = {
                    guid  = entry.guid,
                    day   = (STARTING_ARRIVAL or {})[nick] or 1,
                    order = i,
                }
            end
            table.sort(plan, function(a, b)
                if a.day ~= b.day then return a.day < b.day end
                return a.order < b.order
            end)

            local today, later, laterDays = 0, 0, {}
            for _, p in ipairs(plan) do
                if p.day <= 1 then
                    today = today + 1
                else
                    later = later + 1
                    laterDays[p.day] = true
                end
            end

            local ti, li = 0, 0
            for _, p in ipairs(plan) do
                local faceUp = (p.day <= 1)
                local spot, reserveTag
                if faceUp then
                    ti = ti + 1
                    spot = _startingRowSpot(base, ox, oz, STARTING_ROW_DIST, ti, today)
                else
                    li = li + 1
                    spot = _startingRowSpot(base, ox, oz, STARTING_RESERVE_DIST, li, later)
                    reserveTag = "StartingReserve:" .. color .. ":" .. tostring(p.day)
                end
                safecall(function()
                    if not isLiveObject(deck) then return end
                    deck.takeObject({
                        guid     = p.guid,
                        position = spot,
                        -- rz 0 = face up, 180 = face down. These cards carry
                        -- HideWhenFaceDown, so a reserve card shows nothing
                        -- but its "STARTING" back until its day comes.
                        rotation = {0, 180, faceUp and 0 or 180},
                        smooth   = false,
                        callback_function = function(c)
                            -- pcall: the outer safecall wraps takeObject, not
                            -- this callback, whose handle can already be dead.
                            if reserveTag then
                                pcall(function() c.addTag(reserveTag) end)
                            end
                        end,
                    })
                end, "StartingItems")
            end

            local msg = char.name .. "'s starting items are face up beside your player board — hover each card to see what it does."
            if later > 0 then
                local days = {}
                for d in pairs(laterDays) do days[#days + 1] = d end
                msg = msg .. " The " .. later .. " face-down cards behind them are the rest of your kit; they turn over on " ..
                    _dayPhrase(days) .. ". Nothing to read there yet."
            end
            broadcastToColor(msg, color, BROADCAST_COLORS.gain)
        end
        if char.name == "James" then
            -- Through giveResource so the authoritative count is set, not
            -- just the physical tokens (his Wired economy reads the count).
            giveResource(color, "EnergyDrink", 2)
            broadcastToColor("James starts with 2 Energy Drinks by his player board — Wired burns one per day.",
                color, BROADCAST_COLORS.warn)
        end
    end
end

-----------------------------------------------------------------------
-- Turn over the starting items Setup held back. Called from BeginDay once the
-- day number has advanced, so a card marked `arrives = 2` is face up before
-- that day's first action. A no-op on Day 1 (nothing is ever tagged for it)
-- and on any day a character has nothing left in reserve.
-----------------------------------------------------------------------
function revealScheduledStartingItems(day)
    for color, char in pairs(gameState.activeChars or {}) do
        local tag = "StartingReserve:" .. color .. ":" .. tostring(day)
        local names = {}
        for _, card in ipairs(findAllByTag(tag)) do
            names[#names + 1] = safeNickname(card)
            safecall(function()
                card.setRotationSmooth({0, 180, 0}, false, true)   -- face up
                -- Untag as we go: the reveal is then idempotent if a day ever
                -- begins twice (a reloaded save, a re-run BeginDay).
                pcall(function() card.removeTag(tag) end)
            end, "StartingReveal")
        end
        if #names > 0 then
            broadcastToColor("The rest of " .. char.name .. "'s kit is face up now: " ..
                table.concat(names, ", ") .. ". Hover each card to see what it does.",
                color, BROADCAST_COLORS.gain)
        end
    end
end

-----------------------------------------------------------------------
-- Market display: deal a card to every EMPTY display slot. Safe to call
-- on a re-setup — occupied slots are skipped, so cards never double-deal
-- and pile up (they used to scatter across the day counter).
-----------------------------------------------------------------------
local function _slotOccupied(slotPos)
    for _, card in ipairs(findAllByTag("MarketCard")) do
        if card.type == "Card" then
            local p = card.getPosition()
            local dx, dz = p.x - slotPos.x, p.z - slotPos.z
            if (dx * dx + dz * dz) < 4 then return true end
        end
    end
    return false
end

function dealMarketDisplay()
    local marketDeck = getMarketDeck()
    if not marketDeck then return end
    marketDeck.shuffle()
    Wait.time(function()
        local deck = getMarketDeck()
        if not deck then return end
        for _, slot in ipairs(getMarketSlots()) do
            local slotPos = slot.getPosition()
            if not _slotOccupied(slotPos) and deck.getQuantity() > 0 then
                deck.takeObject({
                    position = slotPos + Vector(0, 1, 0),
                    rotation = {0, 180, 0},  -- face-up
                    smooth   = true,
                    -- The slot markers no longer print the "what is this?"
                    -- paragraph beside them; it hangs off the card's own
                    -- tooltip instead (addMarketHelp, lua/crafting.lua).
                    callback_function = function(c) addMarketHelp(c) end,
                })
            end
        end
    end, 0.5)
end

-----------------------------------------------------------------------
-- The orientation a new table needs, one idea per message, for whichever
-- Setup path ran. Both callers hand these to stageBroadcasts rather than
-- firing them here, because dealing the market is not the moment to talk.
--
-- Playtest: "who do these cards belong to?" — so say it out loud. Only
-- describe things that are ON the table: this used to point at "the card row
-- south of the map" for recipes, and that row moved into the hidden library
-- when the board was decluttered, so players went looking for a row that
-- isn't there ("I don't see any card row"). It was also one three-clause
-- paragraph, which is how the ownership answer kept getting missed — it was
-- in clause two, on screen for four seconds, under a stack of other
-- broadcasts.
-----------------------------------------------------------------------
function tableOrientationMessages()
    return {
        {"proc", "The 5 face-up cards west of the map are the shared MARKET. They belong to nobody until someone buys one with the Craft action — hover one to see what it does."},
        {"proc", "Recipes for the Cook action are listed in the action itself, in the Notebook, and in the ? panel. Nothing to memorise."},
    }
end

-- Rest height of the locked Doom marker on the board top (mirrors the
-- marker's spawn transform in build_save.py). The glass table's playing
-- surface is at ~y 1.55 — the old 1.2 left the marker inside the table.
-- Mirrors BOARD_PIECE_Y in scripts/build_save.py (the board's top surface is
-- ~1.79, well above the table's 1.55 — at 1.72 the marker sat inside the
-- board and was invisible). test_build_output.py guards the mirror.
local DOOM_MARKER_Y = 1.572

-- Printed Doom track geometry, mirroring board_geometry.py
-- (DOOM_STEP0_WORLD_X / DOOM_STEP30_WORLD_X / DOOM_TRACK_WORLD_Z).
-- tests/test_cross_refs.py guards the mirror.
DOOM_STEP0_X  = -10.9
DOOM_STEP30_X = 10.9
DOOM_TRACK_Z  = -11.5

-- World position of a Doom step's printed cell.
-- The printed track always occupies the same strip of board; the DIFFICULTY
-- decides how many cells that strip is cut into (Long Weekend prints 16 and
-- loses at 15). So the marker's position is a fraction of the Doom LIMIT, not
-- of a hardcoded 30 — with 30 baked in here, a Long Weekend game ended with
-- the marker sitting halfway down the track, which is what "the doom track is
-- halved but it still goes up to 30" looked like from the seat.
function doomStepWorld(step)
    local limit = getDoomLimit()
    step = math.max(0, math.min(limit, step or 0))
    return {
        x = DOOM_STEP0_X + (DOOM_STEP30_X - DOOM_STEP0_X) * (step / limit),
        y = DOOM_MARKER_Y,
        z = DOOM_TRACK_Z,
    }
end

-- Last step the marker was sent to: refreshPhaseBanner calls
-- moveDoomMarker on every UI refresh so the marker can never lag the
-- doom value, and this guard makes the repeat calls free.
local _doomMarkerStep = nil

function moveDoomMarker(targetStep)
    -- The printed track runs 0..getDoomLimit(); pin overshoot to the last cell.
    targetStep = math.max(0, math.min(getDoomLimit(), targetStep or 0))
    if _doomMarkerStep == targetStep then return end
    local marker = getDoomMarker()
    if not marker then return end
    local board = getMainBoard()
    if not board then return end

    -- World position computed DIRECTLY, not via board.positionToWorld(snap).
    -- Going through the board made the marker's position depend on the
    -- board's Transform scale and on surviving a board reload (the path
    -- variant swap reloads it) — the marker ended up at (-14.2, -15.7),
    -- out on the felt beyond the board's corner.
    local worldPos = doomStepWorld(targetStep)
    _doomMarkerStep = targetStep

    -- The marker stays locked so players can't drag it; only this function
    -- moves it. Unlock for the smooth slide (locked objects don't smooth-
    -- move reliably), then pin it exactly on the step and re-lock.
    marker.setLock(false)
    marker.setPositionSmooth(worldPos, false, true)
    Wait.time(function()
        local m = getDoomMarker()
        if m then
            m.setPosition(worldPos)
            m.setRotation({0, 0, 0})
            m.setLock(true)
        end
    end, 1.0)
end

-----------------------------------------------------------------------
-- SCENARIO SYSTEM — drawn at setup, modifies the entire game
-----------------------------------------------------------------------
SCENARIOS = {
    SC_WINTER = {
        name = "The Long Winter",
        description = "Hunger decay doubled. Provisions gathering yields -1. Houses give +1 Sanity at sleep.",
        onApply = function()
            gameState.scenario = "SC_WINTER"
            gameState.scenarioFlags = { hungerDecayX2 = true, foodGatherPenalty = true, housesSanityBonus = true }
            broadcastEvent("warn", "SCENARIO: The Long Winter. Hunger is brutal. Stay fed or perish.")
        end,
    },
    SC_SUMMER = {
        name = "The Scorching Summer",
        description = "All players start -2 max Hunger. Energy Drinks restore +1 extra Sanity. Sport courts yield +1 resource.",
        onApply = function()
            gameState.scenario = "SC_SUMMER"
            gameState.scenarioFlags = { energyDrinkBonus = true, courtGatherBonus = true }
            for _, char in pairs(gameState.activeChars) do
                char.maxHunger = char.maxHunger - 2
                char.hunger = math.min(char.hunger, char.maxHunger)
            end
            broadcastEvent("warn", "SCENARIO: The Scorching Summer. Smaller stomachs, but Energy Drinks hit harder.")
        end,
    },
    SC_AUTUMN = {
        name = "The Rotting Autumn",
        description = "1 Provisions token spoils per location at Dawn. Recipes yield +1 Hunger. Cloth is easier to find.",
        onApply = function()
            gameState.scenario = "SC_AUTUMN"
            gameState.scenarioFlags = { foodSpoilsAtDawn = true, recipeBonus = true, clothBonus = true }
            broadcastEvent("warn", "SCENARIO: The Rotting Autumn. Provisions rot fast — cook them before you lose them.")
        end,
    },
    SC_SPRING = {
        name = "The False Spring",
        description = "Days 1-3: no Charlie. Day 4+: Charlie attacks everywhere every night.",
        onApply = function()
            gameState.scenario = "SC_SPRING"
            gameState.scenarioFlags = { falseSpring = true }
            broadcastEvent("warn", "SCENARIO: The False Spring. Enjoy the calm while it lasts...")
        end,
    },
    SC_BLACKOUT = {
        name = "Total Blackout",
        description = "All Battery items removed. Flashlights can't be crafted. Only Fire provides light.",
        onApply = function()
            gameState.scenario = "SC_BLACKOUT"
            gameState.scenarioFlags = { noBatteries = true, onlyFireLight = true }
            gameState.ongoingDawnEffects.onlyFireLight = true
            broadcastEvent("warn", "SCENARIO: Total Blackout. Fire is your only friend against Charlie.")
        end,
    },
    SC_RATIONING = {
        name = "Strict Rationing",
        description = "Market restocks 1 card every 2 days. Recipes cost -1 ingredient (min 1).",
        onApply = function()
            gameState.scenario = "SC_RATIONING"
            gameState.scenarioFlags = { slowMarket = true, cheapRecipes = true }
            broadcastEvent("warn", "SCENARIO: Strict Rationing. Supplies are scarce — make every craft count.")
        end,
    },
    SC_FULL_MOON = {
        name = "The Full Moon",
        description = "Charlie never attacks. All Soft threats become Hard (gain 2 HP, 1 attack).",
        onApply = function()
            gameState.scenario = "SC_FULL_MOON"
            gameState.scenarioFlags = { noCharlie = true, softToHard = true }
            gameState.ongoingDawnEffects.charliePaused = true
            broadcastEvent("warn", "SCENARIO: The Full Moon. No Charlie — but the things in the moonlight are much worse.")
        end,
    },
    SC_SHORTCUT = {
        name = "The Shortcut",
        description = "Path between JamesHouse and BadmintonCourt costs 0 Hunger. But +1 Threat at both at night.",
        onApply = function()
            gameState.scenario = "SC_SHORTCUT"
            gameState.scenarioFlags = { shortcutPath = true, shortcutThreatBonus = true }
            broadcastEvent("warn", "SCENARIO: The Shortcut. A hole in the fence... but something uses it too.")
        end,
    },
}

function applyRandomScenario()
    local keys = {}
    for k, _ in pairs(SCENARIOS) do table.insert(keys, k) end
    local pick = keys[gameRoll(#keys)]
    local scenario = SCENARIOS[pick]
    broadcastEvent("phase", "Drawing Scenario Card: " .. scenario.name)
    broadcastEvent("proc", scenario.description)
    scenario.onApply()
end

-- Force a named scenario, e.g. applyScenario("SC_WINTER") — a console-only
-- playtest tool (tests/test_lua_reachability.py::CONSOLE_ENTRY_POINTS). Setup
-- always draws at random via applyRandomScenario, so this is the only way to
-- play the same scenario twice on purpose, which is what testing one needs.
function applyScenario(scenarioId)
    local scenario = SCENARIOS[scenarioId]
    if not scenario then
        broadcastEvent("damage", "Unknown scenario: " .. tostring(scenarioId))
        return
    end
    broadcastEvent("phase", "Scenario: " .. scenario.name)
    broadcastEvent("proc", scenario.description)
    scenario.onApply()
end
