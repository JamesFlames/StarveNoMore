-- ui_setup.lua  (H.1 Setup walkthrough + H.2 Character briefing + H.6 Welcome)

-----------------------------------------------------------------------
-- H.1 — Guided Setup Walkthrough (4 steps)
-----------------------------------------------------------------------
-- State tracking for the walkthrough
local setupState = {
    step = 0,             -- 0=not started, 1=path pick, 1.5=variants, 2=char pick, 3=briefing, 4=done
    hostColor = nil,
    pickedPath = nil,
    rotationTurns = false, -- §11.2 rotation variant (1 action per visit)
    randomScenario = false, -- §17.3 optional Scenario (applied at finalize)
    charPicks = {},       -- { [color] = charName }
    pendingColors = {},   -- colors still needing to pick
}

function startGuidedSetup(hostColor)
    setupState.step = 1
    setupState.hostColor = hostColor
    setupState.pickedPath = nil
    setupState.charPicks = {}
    setupState.pendingColors = {}

    -- Gather seated players
    local seated = getActivePlayerColors()
    for _, c in ipairs(seated) do
        table.insert(setupState.pendingColors, c)
    end

    broadcastEvent("phase", "Starting guided setup...")

    -- Step 1: Show path pick to host
    UI.show("setupStep1")
end

-----------------------------------------------------------------------
-- Step 1: Path graph pick
-----------------------------------------------------------------------
function onPickPath(player, value, id)
    local variant
    if id == "pickCompact" then variant = "Compact"
    elseif id == "pickSprawl" then variant = "Sprawl"
    elseif id == "pickLinear" then variant = "Linear"
    elseif id == "pickRing" then variant = "Ring"
    elseif id == "pickStar" then variant = "Star"
    else return end

    setupState.pickedPath = variant
    gameState.pathVariant = variant
    broadcastEvent("proc", "Path layout: " .. variant)

    UI.hide("setupStep1")

    -- Advance to step 1.5: optional variants (host chooses; defaults = standard game)
    setupState.step = 1.5
    UI.show("setupStepVariants")
end

-----------------------------------------------------------------------
-- Step 1.5: Optional variants (rotation turns §11.2, Scenario §17.3)
-----------------------------------------------------------------------
local function refreshVariantToggle(id, on, labelOn, labelOff)
    UI.setAttribute(id, "text", on and labelOn or labelOff)
    -- Light "rulebook page" theme (matches xml/setup.xml): green = ON.
    UI.setAttribute(id, "color", on and "#CFE6C2FF" or "#ECE6D8FF")
    UI.setAttribute(id, "textColor", on and "#1E5A1E" or "#3A362E")
end

function onToggleRotation(player, value, id)
    setupState.rotationTurns = not setupState.rotationTurns
    refreshVariantToggle("toggleRotation", setupState.rotationTurns,
        "Rotation turns: ON\n(take 1 action per visit, cycling — shorter waits at 4-5 players)",
        "Rotation turns: OFF\n(take 1 action per visit, cycling — shorter waits at 4-5 players)")
end

function onToggleScenario(player, value, id)
    setupState.randomScenario = not setupState.randomScenario
    refreshVariantToggle("toggleScenario", setupState.randomScenario,
        "Random Scenario: ON\n(a week-long twist like The Long Winter — revealed at setup)",
        "Random Scenario: OFF\n(a week-long twist like The Long Winter — recommended after your first game)")
end

-- Difficulty selector (Design §17.2, batch 4 W3): cycles through the
-- DIFFICULTY_PARAMS modes. Standard unless changed.
local DIFFICULTY_CYCLE = { "standard", "weekend", "nightmare" }
local DIFFICULTY_BLURBS = {
    standard  = "Difficulty: STANDARD\n(the full 7-day week)",
    weekend   = "Difficulty: LONG WEEKEND\n(3 days, Doom track halved — good for teaching)",
    nightmare = "Difficulty: NIGHTMARE\n(Doom +1 every phase; the week starts on Strange Days)",
}

function onToggleDifficulty(player, value, id)
    local current = setupState.difficulty or "standard"
    local idx = 1
    for i, d in ipairs(DIFFICULTY_CYCLE) do
        if d == current then idx = i break end
    end
    setupState.difficulty = DIFFICULTY_CYCLE[(idx % #DIFFICULTY_CYCLE) + 1]
    refreshVariantToggle("toggleDifficulty", setupState.difficulty ~= "standard",
        DIFFICULTY_BLURBS[setupState.difficulty],
        DIFFICULTY_BLURBS[setupState.difficulty])
end

function onVariantsContinue(player, value, id)
    UI.hide("setupStepVariants")
    gameState.turnStyle = setupState.rotationTurns and "rotate" or "full"
    if setupState.rotationTurns then
        broadcastEvent("proc", "Variant on — Rotation turns: 1 action per visit, cycling until all are spent.")
    end
    gameState.difficulty = setupState.difficulty or "standard"
    if gameState.difficulty ~= "standard" then
        local diff = getDifficulty()
        broadcastEvent("proc", "Difficulty: " .. diff.label .. " — " .. diff.days ..
            " days, Doom track to " .. diff.doomLimit ..
            ((diff.doomDelta or 0) > 0 and (", Doom rate +" .. diff.doomDelta .. " per phase") or "") .. ".")
    end
    -- The Scenario (if any) is applied in finalizeGuidedSetup, after the
    -- characters exist (some scenarios modify character stats).

    setupState.step = 2
    showCharPickForNextPlayer()
end

-----------------------------------------------------------------------
-- Step 2: Character pick (one player at a time)
-----------------------------------------------------------------------
local CHAR_BUTTON_MAP = {
    pickJames  = "James",
    pickCoco   = "Coco",
    pickRayman = "Rayman",
    pickEllie  = "Ellie",
    pickLuca   = "Luca",
}

-- Step 2 card styling (light "rulebook page" theme; matches xml/setup.xml).
local CHAR_CARD_STYLE = {
    James  = { bg = "#E9E9F2FF", name = "#2B2B52" },
    Coco   = { bg = "#F5E3E3FF", name = "#7A2727" },
    Rayman = { bg = "#F0EDD8FF", name = "#5C5214" },
    Ellie  = { bg = "#E2F0DCFF", name = "#1E5A1E" },
    Luca   = { bg = "#E2E6F5FF", name = "#24336B" },
}
local CARD_TAKEN_BG   = "#CFCBC2AA"
local CARD_TAKEN_NAME = "#8A857B"

function showCharPickForNextPlayer()
    if #setupState.pendingColors == 0 then
        -- All players picked — finalize setup
        finalizeGuidedSetup()
        return
    end

    local color = setupState.pendingColors[1]
    UI.setAttribute("step2Title", "text", "Step 2 — " .. color .. " Player: Pick Your Character")
    UI.setAttribute("step2Subtitle", "text",
        "Click a card to choose — taken characters are greyed out. Hover a card for the full briefing. HP = Health, HU = Hunger, SA = Sanity.")

    -- Grey out already-picked characters
    local taken = {}
    for _, name in pairs(setupState.charPicks) do
        taken[name] = true
    end

    for btnId, charName in pairs(CHAR_BUTTON_MAP) do
        local style = CHAR_CARD_STYLE[charName]
        if taken[charName] then
            UI.setAttribute(btnId, "interactable", "false")
            UI.setAttribute(btnId, "tooltip", charName .. " is already taken.")
            UI.setAttribute("card" .. charName, "color", CARD_TAKEN_BG)
            UI.setAttribute("charName_" .. charName, "color", CARD_TAKEN_NAME)
        else
            UI.setAttribute(btnId, "interactable", "true")
            -- Hovering anywhere on the card shows the full briefing — every
            -- detail the post-pick page would tell you about this character.
            UI.setAttribute(btnId, "tooltip", CHAR_BRIEFINGS[charName] or charName)
            UI.setAttribute("card" .. charName, "color", style.bg)
            UI.setAttribute("charName_" .. charName, "color", style.name)
        end
    end

    UI.show("setupStep2")
end

function onPickChar(player, value, id)
    local charName = CHAR_BUTTON_MAP[id]
    if not charName then return end

    -- Verify this character isn't taken
    for _, name in pairs(setupState.charPicks) do
        if name == charName then
            broadcastToColor(charName .. " is already taken.", player.color, BROADCAST_COLORS.damage)
            return
        end
    end

    local color = setupState.pendingColors[1]

    -- Allow the correct player OR the host to pick
    if player.color ~= color and player.color ~= setupState.hostColor then
        broadcastToColor("It's " .. color .. "'s turn to pick.", player.color, BROADCAST_COLORS.damage)
        return
    end

    setupState.charPicks[color] = charName
    table.remove(setupState.pendingColors, 1)
    broadcastEvent("proc", charName .. " assigned to " .. color .. ".")

    UI.hide("setupStep2")

    -- Show briefing for this player (Step 3 interleaved)
    showCharBriefing(color, charName)
end

-----------------------------------------------------------------------
-- H.2 — Character Briefing Popup (Step 3, one per player)
-----------------------------------------------------------------------
CHAR_BRIEFINGS = {
    James = "You are James, the Gamer.\n\nYou know patterns. You see things before they happen.\n\nStrengths:\n- Gaming Reflexes: once per turn, reroll one die.\n- Pattern Recognition: once per day, peek any deck top.\n\nConstraint:\n- Wired: consume 1 Energy Drink per day or lose 2 Sanity at night.\n\nStarting hand: Energy Drink x2, Pocketknife, Flashlight, Headphones.\n\nFirst move: Gather at home — The Stash lets you take 2 Energy Drinks at once. Stock up, then use Pattern Recognition to peek at the Phase deck.",
    Coco = "You are Coco, the Angel.\n\nYou are calm when the world isn't. You're visiting — no house of your own.\n\nStrengths:\n- Calming Presence: allies at your tile lose 1 less Sanity at Tick.\n- Touch of Hope (once per game): heal any character +4 Health.\n- Light in the Dark: never triggers Charlie attacks.\n- Wanderer's Gift: gain +1 Sanity each time you move to a new location.\n\nConstraint:\n- No Home: alone at a non-house tile at night = -3 Sanity.\n\nStarting hand: First Aid Kit, Comfort Blanket, Hopeful Tea, Spare Phone Battery, Friendship Bracelet.\n\nFirst move: Keep moving — your Gift rewards travel. Stick with allies at night.",
    Rayman = "You are Rayman, the Basketball Player.\n\nFastest and toughest. You hit hard. You also eat a lot.\n\nStrengths:\n- Speed: Move 2 tiles per Move action.\n- Court Master: +1 attack die at the Basketball Court.\n- Backboard Block: Defend action shields adjacent allies.\n\nConstraints:\n- Big Appetite: lose 2 Hunger per Tick (others lose 1).\n- Loud: if you moved at all today, wherever you spend the Night draws +1 Threat. A quiet day keeps the dark away.\n\nStarting hand: Basketball, Sports Drink x2, Athletic Tape, Whistle.\n\nFirst move: Head to the Basketball Court for Wood. Watch your Hunger.",
    Ellie = "You are Ellie, the Cook.\n\nThe kitchen is your domain. You feed the team.\n\nStrengths:\n- Crockpot Master: recipes need 1 fewer ingredient (min 1).\n- Comfort Food: shared meals give +1 extra Hunger and Sanity.\n- Knows the Pantry: at your house, pick a specific resource.\n\nConstraint:\n- Particular Eater: cannot eat raw food. Must cook first.\n\nStarting hand: Crockpot, Soup Recipe, Cooking Knife, Pantry Key, Apron.\n\nFirst move: Gather Food with Knows the Pantry, then cook Hot Stew for the team.",
    Luca = "You are Luca, the Orator.\n\nYour words hold Sanity together when everything else falls apart.\n\nStrengths:\n- Rally: once per turn, give an adjacent ally a free action.\n- Calm Words: on Sanity-loss events at your tile, d6 — 4+ negates it.\n- Storyteller: allies at your tile gain +1 Sanity at Night.\n\nConstraint:\n- Needs an Audience: Sanity doesn't regen when alone.\n\nStarting hand: Notebook, Loud Whistle, Pep Talk, Reading Lamp, Toolbox.\n\nFirst move: Use Rally to give Ellie a free action. Stay with allies.",
}

function showCharBriefing(color, charName)
    setupState.step = 3
    setupState.briefingColor = color

    local text = CHAR_BRIEFINGS[charName] or ("You are " .. charName .. ".")
    UI.setAttribute("briefTitle", "text", "You are " .. charName)
    UI.setAttribute("briefBody", "text", text)
    UI.show("charBriefing")
end

-- Go Back: return the just-picked character to the pool and reopen the
-- Step 2 pick for the same player.
function onBriefBack(player, value, id)
    UI.hide("charBriefing")
    local color = setupState.briefingColor
    if color and setupState.charPicks[color] then
        broadcastEvent("proc", setupState.charPicks[color] .. " returned to the pool — " ..
            color .. " is picking again.")
        setupState.charPicks[color] = nil
        table.insert(setupState.pendingColors, 1, color)
    end
    setupState.step = 2
    showCharPickForNextPlayer()
end

function onBriefDismiss(player, value, id)
    UI.hide("charBriefing")

    -- Mark as briefed
    local color = setupState.briefingColor
    if color and gameState.activeChars[color] then
        gameState.activeChars[color].briefed = true
    end

    -- Continue to next player's character pick or finalize
    if #setupState.pendingColors > 0 then
        setupState.step = 2
        showCharPickForNextPlayer()
    else
        finalizeGuidedSetup()
    end
end

-----------------------------------------------------------------------
-- Finalize setup after all players have picked and been briefed
-----------------------------------------------------------------------
function finalizeGuidedSetup()
    setupState.step = 4

    -- Run the actual Setup logic with the picked characters
    broadcastEvent("phase", "Setting up Starve No More...")

    -- 1. Path variant already set
    broadcastEvent("proc", "Path layout: " .. (gameState.pathVariant or "Compact"))

    -- 2. Shuffle Phase decks
    for p = 1, 4 do
        local deck = getPhaseDeck(p)
        if deck then deck.shuffle() end
    end

    -- 3. Market — deal the display row (empty slots only; re-setup safe)
    dealMarketDisplay()

    -- 4. Threat deck
    local threatDeck = getThreatDeck()
    if threatDeck then threatDeck.shuffle() end

    -- 5. Assign characters per picks. Wipe the previous party first so a
    -- re-setup can never leave stale characters in the roster.
    gameState.activeChars = {}
    gameState.dailyAlerts = {}

    local seated = {}
    for color, _ in pairs(setupState.charPicks) do
        table.insert(seated, color)
    end
    gameState.playerCount = #seated
    gameState.turnOrder = seated
    gameState.turnIndex = 0

    for color, charName in pairs(setupState.charPicks) do
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
            briefed    = true,
            location   = home,
            signatureUsed = false,   -- Signature Move (§6.7): one per game
        }

        placeCharacterAtTile(charName, home)

        broadcastEvent("proc", charName .. " assigned to " .. color .. ".")
    end

    -- Characters nobody picked leave the map for the bench.
    safecall(function() benchUnusedCharacters() end, "Bench")

    -- Starting hands: each character's personal items into their hand.
    safecall(function() dealStartingHands() end, "StartingHands")

    -- 5.5. Optional Scenario (§17.3) — applied now that the characters
    -- exist, because some scenarios modify character stats (e.g. Summer's
    -- -2 max Hunger).
    if setupState.randomScenario then
        safecall(function() applyRandomScenario() end, "Scenario")
    end

    -- 6. Day=1, Doom=0
    gameState.day = 1
    gameState.doom = 0
    gameState.difficulty = gameState.difficulty or "standard"
    gameState.phase = getPhaseForDay(1)   -- Nightmare starts on Strange Days
    gameState.subPhase = "Dawn"
    gameState.dayLog = {}
    gameState.chronicle = nil          -- fresh Week in Review record
    safecall(function() ensureChronicle() end, "Chronicle")
    safecall(function() recordSetupInChronicle() end, "Telemetry")
    gameState.combatContext = nil
    gameState.gameOverCause = nil
    gameState.bossHP = {}
    gameState.sourceSplit = nil
    gameState.pendingSanityPenalty = {}
    gameState.loudSignature = {}
    gameState.wrongness = nil
    gameState.basementOpened = nil

    local counter = getDayCounter()
    if counter then counter.setValue(1) end
    moveDoomMarker(0)

    -- 7. Started
    gameState.started = true

    broadcastEvent("phase", "Setup complete! Day 1 begins. Click 'Begin Day' to reveal the first Dawn card.")

    -- Refresh UI
    Wait.time(function()
        refreshPhaseBanner()
        updateActivePlayerIndicator()
        applyTooltips()
        refreshDynamicTooltips()
        safecall(function() lockdownCriticalObjects() end, "Lockdown")
    end, 1.0)
end

-----------------------------------------------------------------------
-- H.6 — Welcome sequence on first load
-----------------------------------------------------------------------
function showWelcomeSequence()
    if gameState.started or gameState.welcomed then return end

    broadcastToAll("Welcome to Starve No More.", {0.9, 0.7, 0.3})
    broadcastToAll("Click 'Setup Game' on the Host Controls panel (top-left), or hover anything to see what it does.", {0.9, 0.7, 0.3})
    broadcastToAll("Press '?' anytime for help. Press 'What now?' if you're stuck.", {0.7, 0.8, 0.6})

    -- Camera tween to the main board for all players
    local board = getMainBoard()
    if board then
        local pos = board.getPosition()
        for _, p in ipairs(Player.getPlayers()) do
            if p.seated then
                p.lookAt({
                    position = pos,
                    distance = 30,
                    pitch    = 60,
                })
            end
        end
    end

    gameState.welcomed = true
end

-----------------------------------------------------------------------
-- Override the host Setup button to use guided flow
-----------------------------------------------------------------------
-- This replaces the onHostSetup from ui_controls.lua
-- The original is kept as a fallback; this version is called from XML
function onHostSetupGuided(player, value, id)
    if gameState.started then
        broadcastToColor("Game already started. Click Restart first.", player.color, BROADCAST_COLORS.damage)
        return
    end
    startGuidedSetup(player.color)
end
