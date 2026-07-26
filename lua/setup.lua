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
    broadcastEvent("proc", "Path layout: " .. pick .. " (the lines printed on the board are the routes you can walk).")

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

            broadcastEvent("proc", charName .. " assigned to " .. color .. ".")
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

    local counter = getDayCounter()
    if counter then counter.setValue(1) end

    moveDoomMarker(0)

    -- 7. Mark started
    gameState.started = true

    broadcastEvent("phase", "Setup complete! Day 1 begins. Click 'Begin Day' on the Host Controls panel to reveal the first Dawn card.")

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
function dealStartingHands()
    for color, char in pairs(gameState.activeChars) do
        local deck = findOneByTag("StartingHand:" .. char.name)
        local board = getPlayerBoard(char.name)
        if deck and board then
            local n = deck.getQuantity and deck.getQuantity() or 0
            local base = board.getPosition()
            -- Lay them along the board's long edge, pushed OUTWARD (away from
            -- the map) so they never cover the board or the play area.
            local outward = Vector(base.x, 0, base.z)
            local len = math.sqrt(outward.x * outward.x + outward.z * outward.z)
            if len < 0.01 then outward = Vector(0, 0, -1); len = 1 end
            local ox, oz = outward.x / len, outward.z / len
            local px_, pz_ = -oz, ox          -- perpendicular: the row direction
            for i = 1, n do
                local offset = (i - 1) - (n - 1) / 2
                safecall(function()
                    deck.takeObject({
                        position = {
                            base.x + ox * 3.2 + px_ * offset * 1.3,
                            base.y + 0.6 + i * 0.05,
                            base.z + oz * 3.2 + pz_ * offset * 1.3,
                        },
                        rotation = {0, 180, 0},   -- face up
                        smooth   = false,
                    })
                end, "StartingItems")
            end
            broadcastToColor(char.name .. "'s starting items are face up beside your player board — hover each card to see what it does.",
                color, BROADCAST_COLORS.gain)
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
        -- Playtest: "who do these cards belong to?" — say it out loud.
        broadcastEvent("proc", "The 5 face-up cards west of the map are the shared MARKET — they belong to nobody until someone buys one with the Craft action. The card row south of the map is the RECIPE reference for the Cook action.")
    end, 0.5)
end

-- Rest height of the locked Doom marker on the board top (mirrors the
-- marker's spawn transform in build_save.py). The glass table's playing
-- surface is at ~y 1.55 — the old 1.2 left the marker inside the table.
-- Mirrors BOARD_PIECE_Y in scripts/build_save.py (the board's top surface is
-- ~1.79, well above the table's 1.55 — at 1.72 the marker sat inside the
-- board and was invisible). test_build_output.py guards the mirror.
local DOOM_MARKER_Y = 1.755

-- Printed Doom track geometry, mirroring board_geometry.py
-- (DOOM_STEP0_WORLD_X / DOOM_STEP30_WORLD_X / DOOM_TRACK_WORLD_Z).
-- tests/test_cross_refs.py guards the mirror.
DOOM_STEP0_X  = -10.9
DOOM_STEP30_X = 10.9
DOOM_TRACK_Z  = -11.5

-- World position of a Doom step's printed cell.
function doomStepWorld(step)
    step = math.max(0, math.min(30, step or 0))
    return {
        x = DOOM_STEP0_X + (DOOM_STEP30_X - DOOM_STEP0_X) * (step / 30),
        y = DOOM_MARKER_Y,
        z = DOOM_TRACK_Z,
    }
end

-- Last step the marker was sent to: refreshPhaseBanner calls
-- moveDoomMarker on every UI refresh so the marker can never lag the
-- doom value, and this guard makes the repeat calls free.
local _doomMarkerStep = nil

function moveDoomMarker(targetStep)
    -- The printed track has steps 0..30; pin overshoot to the last cell.
    targetStep = math.max(0, math.min(30, targetStep or 0))
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

-- The 3D board "Begin Day" button is gone — Host Controls > Begin Day
-- (btnBeginDay, shown between days) drives it, and the banner pulses that
-- button as the next step. onBeginDayClick remains as its handler / for tests.
function onBeginDayClick(obj, playerColor, altClick)
    -- Begin Day is only valid between days — mid-day it would re-run the
    -- whole Dawn (double Doom, second Dawn card).
    if gameState.subPhase ~= "PreDawn" then
        broadcastToColor("Begin Day is only available between days (currently: " ..
            tostring(gameState.subPhase) .. ").", playerColor, BROADCAST_COLORS.damage)
        return
    end
    safecall(function() BeginDay() end, "BeginDay")
end

-----------------------------------------------------------------------
-- SCENARIO SYSTEM — drawn at setup, modifies the entire game
-----------------------------------------------------------------------
SCENARIOS = {
    SC_WINTER = {
        name = "The Long Winter",
        description = "Hunger decay doubled. Food gathering yields -1. Houses give +1 Sanity at sleep.",
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
        description = "1 Food spoils per location at Dawn. Recipes yield +1 Hunger. Cloth is easier to find.",
        onApply = function()
            gameState.scenario = "SC_AUTUMN"
            gameState.scenarioFlags = { foodSpoilsAtDawn = true, recipeBonus = true, clothBonus = true }
            broadcastEvent("warn", "SCENARIO: The Rotting Autumn. Food rots fast — cook it before you lose it.")
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
