-- setup.lua  (F.3 — Setup flow, bare-bones without UX walkthrough)

function Setup(hostColor)
    broadcastEvent("phase", "Setting up Starve No More...")

    -- 1. Pick a random path-edge variant
    local variants = {"Compact", "Sprawl", "Linear"}
    local pick = variants[math.random(#variants)]
    gameState.pathVariant = pick
    broadcastEvent("proc", "Path layout: " .. pick)

    -- 2. Shuffle each Phase deck
    for p = 1, 4 do
        local deck = getPhaseDeck(p)
        if deck then deck.shuffle() end
    end

    -- 3. Shuffle and deal Market
    local marketDeck = getMarketDeck()
    if marketDeck then
        marketDeck.shuffle()
        -- Deal 5 face-up to the display (handled by the display slots)
        Wait.time(function()
            local slots = getMarketSlots()
            for i, slot in ipairs(slots) do
                if marketDeck and marketDeck.getQuantity() > 0 then
                    marketDeck.takeObject({
                        position = slot.getPosition() + Vector(0, 1, 0),
                        rotation = {0, 180, 0},  -- face-up
                        smooth   = true,
                    })
                end
            end
        end, 0.5)
    end

    -- 4. Shuffle Threat deck
    local threatDeck = getThreatDeck()
    if threatDeck then threatDeck.shuffle() end

    -- 5. Assign characters to seated players
    local seated = getActivePlayerColors()
    gameState.playerCount = #seated
    gameState.turnOrder = seated
    gameState.turnIndex = 0

    local defaultAssignment = {White="James", Red="Coco", Yellow="Rayman", Green="Ellie", Blue="Luca"}

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
            }

            -- Move standee to starting location
            local standee = getCharacterStandee(charName)
            local tile = getLocationTile(home)
            if standee and tile then
                local pos = tile.getPosition() + Vector(0, 1.5, 0)
                standee.setPositionSmooth(pos)
            end

            broadcastEvent("proc", charName .. " assigned to " .. color .. ".")
        end
    end

    -- 6. Set Day=1, Doom=0
    gameState.day = 1
    gameState.doom = 0
    gameState.phase = 1
    gameState.subPhase = "Dawn"
    gameState.dayLog = {}

    local counter = getDayCounter()
    if counter then counter.setValue(1) end

    moveDoomMarker(0)

    -- 7. Mark started
    gameState.started = true

    broadcastEvent("phase", "Setup complete! Day 1 begins. Click 'Begin Day' to reveal the first Dawn card.")
    createDayButton()

    -- G.1/G.7: Refresh UI and apply tooltips
    Wait.time(function()
        refreshPhaseBanner()
        updateActivePlayerIndicator()
        applyTooltips()
        refreshDynamicTooltips()
    end, 1.0)
end

function moveDoomMarker(targetStep)
    local marker = getDoomMarker()
    if not marker then return end
    local board = getMainBoard()
    if not board then return end

    -- Find the snap point for this doom step
    local snaps = board.getSnapPoints()
    for _, sp in ipairs(snaps) do
        for _, tag in ipairs(sp.tags or {}) do
            if tag == "Snap:Doom:" .. tostring(targetStep) then
                local worldPos = board.positionToWorld(sp.position) + Vector(0, 0.5, 0)
                marker.setPositionSmooth(worldPos)
                return
            end
        end
    end
end

function createDayButton()
    local board = getMainBoard()
    if not board then return end
    board.createButton({
        click_function = "onBeginDayClick",
        function_owner = Global,
        label          = "Begin Day",
        position       = {0, 0.5, -2},
        rotation       = {0, 0, 0},
        width          = 2000,
        height         = 500,
        font_size      = 260,
        color          = {0.1, 0.2, 0.3},
        font_color     = {0.5, 0.9, 1},
        tooltip        = "Advance to the next Dawn phase.",
    })
end

function onBeginDayClick(obj, playerColor, altClick)
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
    local pick = keys[math.random(#keys)]
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
