-- ui_setup.lua  (H.1 Setup walkthrough + H.2 Character briefing + H.6 Welcome)

-----------------------------------------------------------------------
-- H.1 — Guided Setup Walkthrough (4 steps)
-----------------------------------------------------------------------
-- State tracking for the walkthrough
local setupState = {
    step = 0,             -- 0=not started, 1=path pick, 1.5=variants, 2=char pick, 3=briefing, 4=done
    inProgress = false,   -- true from startGuidedSetup until finalize/cancel
    hostColor = nil,
    pickedPath = nil,
    rotationTurns = false, -- §11.2 rotation variant (1 action per visit)
    randomScenario = false, -- §17.3 optional Scenario (applied at finalize)
    charPicks = {},       -- { [color] = charName }
    pendingColors = {},   -- colors still needing to pick
}

-- Host Controls hide the Setup button while this is true (refreshHostControls).
function isGuidedSetupRunning()
    return setupState.inProgress == true
end

-- Re-open whatever step the walkthrough is on (used when someone clicks
-- Setup again mid-walkthrough — usually because they lost the window).
function reshowSetupStep()
    local s = setupState.step
    if s == 1 then UI.show("setupStep1")
    elseif s == 1.5 then UI.show("setupStepVariants")
    elseif s == 2 then showCharPickForNextPlayer()
    elseif s == 3 then UI.show("charBriefing")
    end
end

-- Abandon a half-finished walkthrough (called from Restart).
function cancelGuidedSetup()
    setupState.inProgress = false
    setupState.step = 0
    setupState.charPicks = {}
    setupState.pendingColors = {}
    if UI then
        UI.hide("setupStep1")
        UI.hide("setupStepVariants")
        UI.hide("setupStep2")
        UI.hide("charBriefing")
    end
end

function startGuidedSetup(hostColor)
    -- Re-entrant guard: a second "Setup Game" click used to silently restart
    -- the walkthrough (wiping picks mid-flow). Now it just re-opens the
    -- current step.
    if setupState.inProgress then
        broadcastEvent("proc", "Guided setup is already running — reopening the current step.")
        reshowSetupStep()
        return
    end

    setupState.inProgress = true
    setupState.step = 1
    setupState.hostColor = hostColor
    setupState.pickedPath = nil
    setupState.charPicks = {}
    setupState.pendingColors = {}

    -- Difficulty defaults to the teaching game (Long Weekend, easiest);
    -- each click on the toggle steps UP: Standard, then Nightmare.
    setupState.difficulty = "weekend"
    if UI then
        UI.setAttribute("toggleDifficulty", "text", DIFFICULTY_BLURBS.weekend)
        UI.setAttribute("toggleDifficulty", "color", "#CFE6C2FF")
        UI.setAttribute("toggleDifficulty", "textColor", "#1E5A1E")
    end

    -- Remove the board's 3D "Setup Game" button on every entry path (the
    -- XML Host Controls button skipped onSetupClick's clearButtons, so the
    -- button — and its "click to set up a new game" hover — used to linger
    -- through the whole game).
    local board = getMainBoard()
    if board then board.clearButtons() end

    -- Gather seated players
    local seated = getActivePlayerColors()
    for _, c in ipairs(seated) do
        table.insert(setupState.pendingColors, c)
    end

    broadcastEvent("phase", "Starting guided setup...")

    -- The XML Setup button hides itself while the walkthrough runs.
    safecall(function() refreshHostControls() end, "HostControls")

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
        "Rotation turns: ON\n(take 1 action, then the next player goes — around the table 3 times)",
        "Rotation turns: OFF\n(standard turns — each player takes all 3 actions in one go)")
end

function onToggleScenario(player, value, id)
    setupState.randomScenario = not setupState.randomScenario
    refreshVariantToggle("toggleScenario", setupState.randomScenario,
        "Random Scenario: ON\n(a week-long twist like The Long Winter — revealed at setup)",
        "Random Scenario: OFF\n(a week-long twist like The Long Winter — recommended after your first game)")
end

-- Difficulty selector (Design §17.2, batch 4 W3): cycles through the
-- DIFFICULTY_PARAMS modes, ordered easiest → hardest so each click steps
-- up in difficulty (wrapping from Nightmare back to the teaching game).
-- Long Weekend (easiest) unless changed — new tables learn on it.
-- Global (not local): startGuidedSetup resets the toggle label from these
-- before this point in the chunk is reached lexically.
DIFFICULTY_CYCLE = { "weekend", "standard", "nightmare" }
DIFFICULTY_BLURBS = {
    standard  = "Difficulty: STANDARD\n(the full 7-day week)",
    weekend   = "Difficulty: LONG WEEKEND\n(3 days, Doom track halved — recommended for your first game)",
    nightmare = "Difficulty: NIGHTMARE\n(Doom +1 every phase; the week starts on Strange Days)",
}

function onToggleDifficulty(player, value, id)
    local current = setupState.difficulty or "weekend"
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
        broadcastEvent("proc", "Variant on — Rotation turns: each player takes 1 action at a time, going around the table until everyone has used all 3.")
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
-- Hues follow each character's seat colour (CHARACTER_COLORS): James blue,
-- Coco white, Rayman green, Ellie yellow, Luca red.
local CHAR_CARD_STYLE = {
    James  = { bg = "#E2E8F5FF", name = "#24336B" },
    Coco   = { bg = "#F7F6F1FF", name = "#55524C" },
    Rayman = { bg = "#E2F0DCFF", name = "#1E5A1E" },
    Ellie  = { bg = "#F5F0D0FF", name = "#8A7414" },
    Luca   = { bg = "#F5E3E3FF", name = "#7A2727" },
}
local CARD_TAKEN_BG   = "#CFCBC2AA"
local CARD_TAKEN_NAME = "#8A857B"

-- The player's NAME when someone is seated there, else the seat colour.
-- Never lead with the colour: a player's colour is decided by the
-- character they pick, so naming their pre-pick seat colour ("Blue
-- picks...") reads as if the colour already mattered.
local function _seatLabel(color)
    local name
    pcall(function()
        local p = Player[color]
        if p and p.seated and p.steam_name and p.steam_name ~= "" then
            name = p.steam_name
        end
    end)
    return name or ("the " .. tostring(color) .. " seat")
end

function showCharPickForNextPlayer()
    if #setupState.pendingColors == 0 then
        -- All players picked — finalize setup
        finalizeGuidedSetup()
        return
    end

    -- Lead with WHO picks now (the head of the queue — the seat a host
    -- click picks for); the rest of the queue is listed underneath.
    local current = _seatLabel(setupState.pendingColors[1])
    local others = {}
    for i = 2, #setupState.pendingColors do
        table.insert(others, _seatLabel(setupState.pendingColors[i]))
    end
    UI.setAttribute("step2Title", "text",
        "Step 2 — " .. current .. " picks a character")
    local sub = "Click a card to choose — your seat colour changes to match your character. A host click also picks for " .. current .. "."
    if #others > 0 then
        sub = sub .. "\nUp next: " .. table.concat(others, ", ") ..
            " (anyone waiting may click their own card early)."
    end
    sub = sub .. "\nHover a card for the full briefing. HP = Health, HU = Hunger, SA = Sanity."
    UI.setAttribute("step2Subtitle", "text", sub)

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

-----------------------------------------------------------------------
-- A player's colour is determined by the character they pick
-- (CHARACTER_COLORS, global.lua): picking reseats the player onto the
-- character's colour so pointer, hand zone, standee holder and roster
-- all match. If another (not-yet-picked) player is parked on the target
-- seat, the two players SWAP seats through a spare — nobody is ever left
-- on a spare seat, because a player stranded off the five character
-- seats has no hand zone and TTS keeps prompting them to "Choose Color"
-- (the stray coloured circles that used to appear mid-game).
-----------------------------------------------------------------------
local SPARE_SEATS = { "Orange", "Purple", "Pink", "Teal", "Brown" }

local function _freeSpareSeat()
    for _, s in ipairs(SPARE_SEATS) do
        local seated = false
        pcall(function()
            local p = Player[s]
            seated = (p and p.seated) or false
        end)
        if not seated then return s end
    end
    return nil
end

local function reseatPlayerForCharacter(color, charName)
    local target = CHARACTER_COLORS and CHARACTER_COLORS[charName]
    if not target or target == color then return target or color end
    local mover = Player[color]
    if not (mover and mover.seated) then return color end

    local occupant = Player[target]
    if occupant and occupant.seated then
        -- Three-step swap through a spare seat (TTS can't swap directly).
        local spare = _freeSpareSeat()
        if not spare or not occupant.changeColor(spare) then
            return color   -- can't clear the seat; colours stay as they are
        end
        if not Player[color].changeColor(target) then
            pcall(function() Player[spare].changeColor(target) end)  -- undo
            return color
        end
        pcall(function() Player[spare].changeColor(color) end)
        -- Bookkeeping: the displaced player's waiting entry follows them
        -- onto the picker's old seat. (The picker's own entry was already
        -- removed by onPickChar; nobody who picked sits off their seat.)
        for i, c in ipairs(setupState.pendingColors) do
            if c == target then setupState.pendingColors[i] = color end
        end
        if setupState.hostColor == target then setupState.hostColor = color
        elseif setupState.hostColor == color then setupState.hostColor = target end
        broadcastEvent("proc", charName .. " plays as " .. target ..
            " — seats swapped so colours follow characters.")
        return target
    end

    if mover.changeColor(target) then
        if setupState.hostColor == color then setupState.hostColor = target end
        broadcastEvent("proc", charName .. " plays as " .. target ..
            " — your seat colour now matches your character.")
        return target
    end
    -- Reseat refused (engine edge): keep the old colour — the game works
    -- either way, the colours just won't match.
    return color
end

function onPickChar(player, value, id)
    local charName = CHAR_BUTTON_MAP[id]
    if not charName then return end
    if setupState.step ~= 2 then return end

    -- Verify this character isn't taken
    for _, name in pairs(setupState.charPicks) do
        if name == charName then
            broadcastToColor(charName .. " is already taken.", player.color, BROADCAST_COLORS.damage)
            return
        end
    end

    -- Whose pick is this? Any player still waiting picks for themself —
    -- no fixed order. A click from the host (or from a player who already
    -- picked) assigns the character to the next waiting seat instead:
    -- that's the hotseat path, where one person clicks through everyone.
    local color = player.color
    local waiting = false
    for _, c in ipairs(setupState.pendingColors) do
        if c == color then waiting = true break end
    end
    if not waiting then
        color = setupState.pendingColors[1]
        if not color then return end
        if player.color ~= setupState.hostColor and not setupState.charPicks[player.color] then
            broadcastToColor("You're not in this game's seat list — ask the host to pick for you.",
                player.color, BROADCAST_COLORS.damage)
            return
        end
        broadcastEvent("proc", tostring(player.steam_name or player.color) ..
            " picks " .. charName .. " for the " .. color .. " seat.")
    end

    for i, c in ipairs(setupState.pendingColors) do
        if c == color then table.remove(setupState.pendingColors, i) break end
    end

    local finalColor = color
    safecall(function() finalColor = reseatPlayerForCharacter(color, charName) end, "Reseat")
    setupState.charPicks[finalColor] = charName
    broadcastEvent("proc", charName .. " assigned to " .. finalColor .. ".")

    UI.hide("setupStep2")

    -- Show briefing for this player (Step 3 interleaved)
    showCharBriefing(finalColor, charName)
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

-- Rich-text pass for the briefing dialog only: section titles become bold
-- and slightly larger, colons dropped. CHAR_BRIEFINGS itself stays plain —
-- it doubles as the pick-card hover tooltip, where rich-text tags would
-- render literally.
local function formatBriefingBody(text)
    local out = text
    out = out:gsub("Strengths:", "<b><size=16>Strengths</size></b>")
    out = out:gsub("Constraints:", "<b><size=16>Constraints</size></b>")
    out = out:gsub("Constraint:", "<b><size=16>Constraint</size></b>")
    -- These two run inline into their item lists — break the line instead
    -- of just dropping the colon.
    out = out:gsub("Starting hand: ", "<b><size=16>Starting Hand</size></b>\n")
    out = out:gsub("First move: ", "<b><size=16>First Move</size></b>\n")
    return out
end

function showCharBriefing(color, charName)
    setupState.step = 3
    setupState.briefingColor = color

    local text = CHAR_BRIEFINGS[charName] or ("You are " .. charName .. ".")
    UI.setAttribute("briefTitle", "text", "You are " .. charName)
    UI.setAttribute("briefBody", "text", formatBriefingBody(text))
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
    setupState.inProgress = false

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
    -- PreDawn = "waiting for Begin Day" (banner + CTA point at the button).
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

    -- broadcastEvent (not broadcastToAll) so these land in the Message Log
    -- panel too — new players need to re-read them after the fade.
    broadcastEvent("warn", "Welcome to Starve No More.")
    broadcastEvent("warn", "Sit at any colour for now — when you pick your character during Setup, your seat colour changes to match it (James=Blue, Coco=White, Rayman=Green, Ellie=Yellow, Luca=Red).")
    broadcastEvent("warn", "Click 'Setup Game' on the Host Controls panel (top-left), or hover anything to see what it does.")
    broadcastEvent("gain", "Press '?' anytime for help. Press 'What now?' if you're stuck. The Message Log (bottom right) keeps everything said — nothing is lost when a broadcast fades.")

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
