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

-- Re-assert every walkthrough panel's visibility from setupState.step
-- (step 0/4 = walkthrough over, so everything closes).
--
-- Why this exists: Player.changeColor — the reseat in onPickChar — rebuilds
-- that client's UI canvas, so a UI.show/UI.hide issued in the same handler
-- never lands for the player being reseated. They were left staring at a
-- frozen Step 2 panel (cards greyed mid-pick, someone else's name in the
-- title) while the rest of the table finished setup and started Day 1 —
-- and no code path could ever close it again. Re-run this a few frames
-- after a reseat, and again at finalize, to repair any client that missed
-- a show/hide.
local function syncSetupPanels()
    if not UI then return end
    local s = setupState.step
    local function set(id, on)
        if on then UI.show(id) else UI.hide(id) end
    end
    set("setupStep1", s == 1)
    set("setupStepVariants", s == 1.5)
    set("setupStep2", s == 2)
    set("charBriefing", s == 3)
end

-- A walkthrough click that arrives when setupState is NOT on that step came
-- off a ghost panel: a client that missed a hide (see syncSetupPanels), or a
-- window left open after the game moved on. Obeying it silently mutates
-- setupState/gameState from a dead UI — clicking Continue on a leftover
-- variants panel after the game ended really did re-apply a difficulty, and
-- with it a different Doom limit.
--
-- Step 2 learned this the hard way and grew the guard inline; every other
-- step is reachable the same way, so the guard lives here once and all of
-- them call it. tests/test_ui_handlers_smoke.py clicks every handler in every
-- phase, which is what surfaced the gap.
local function isGhostSetupClick(expectedStep, player)
    if setupState.step == expectedStep then return false end
    safecall(syncSetupPanels, "SetupSync")
    if gameState.started and player and player.color then
        broadcastToColor(
            "Setup already finished — closing that leftover setup window. " ..
            "Click 'Begin Day' to start Day 1.",
            player.color, BROADCAST_COLORS.warn)
    end
    return true
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
    setupState.briefingColor = nil
    syncSetupPanels()
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

    -- TTS's built-in Turns tracker stays off (same rule as onLoad and
    -- BeginDay — this mod runs its own turns). It matters most here: the
    -- walkthrough reseats people, and TTS re-announces "<player>'s turn."
    -- on every colour change, so one setup flooded the chat with a dozen
    -- identical turn messages.
    pcall(function() if Turns and Turns.enable then Turns.enable = false end end)

    setupState.inProgress = true
    setupState.step = 1
    setupState.hostColor = hostColor
    setupState.pickedPath = nil
    setupState.charPicks = {}
    setupState.pendingColors = {}
    setupState.duskSecret = false   -- §11.3 A/B variant, off by default
    setupState.solo = false         -- §20.3 → an official mode

    -- Defaults to STORY: the gentlest *full week*, not the short game. Each
    -- click steps up — Standard, Nightmare — and then offers Long Weekend as
    -- a length. See DIFFICULTY_CYCLE below for why the order matters.
    setupState.difficulty = "story"
    if UI then
        UI.setAttribute("toggleDifficulty", "text", DIFFICULTY_BLURBS.story)
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
    if isGhostSetupClick(1, player) then return end
    local variant
    if id == "pickCompact" then variant = "Compact"
    elseif id == "pickSprawl" then variant = "Sprawl"
    elseif id == "pickLinear" then variant = "Linear"
    elseif id == "pickRing" then variant = "Ring"
    elseif id == "pickStar" then variant = "Star"
    else return end

    setupState.pickedPath = variant
    -- Rebuilds the Move graph and repaints the board to match the choice.
    variant = applyPathVariant(variant)
    broadcastEvent("proc", "Path layout: " .. variant .. " (the lines printed on the board are the routes you can walk).")

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
    if isGhostSetupClick(1.5, player) then return end
    setupState.rotationTurns = not setupState.rotationTurns
    refreshVariantToggle("toggleRotation", setupState.rotationTurns,
        "Rotation turns: ON\n(take 1 action, then the next player goes — around the table 3 times)",
        "Rotation turns: OFF\n(standard turns — each player takes all 3 actions in one go)")
end

function onToggleScenario(player, value, id)
    if isGhostSetupClick(1.5, player) then return end
    setupState.randomScenario = not setupState.randomScenario
    refreshVariantToggle("toggleScenario", setupState.randomScenario,
        "Random Scenario: ON\n(a week-long twist like The Long Winter — revealed at setup)",
        "Random Scenario: OFF\n(a week-long twist like The Long Winter — recommended after your first game)")
end

-- Secret Dusk (§11.3 variant, A/B — §20.2 item 9). OFF by default, exactly
-- like Rotation turns: this cuts against §11.3's explicit intent (the public
-- declaration is celebrated there as "the table-talk moment where the group
-- argues geometry"), so it must earn the default with table data, not with an
-- argument. §20.1 records what to watch.
function onToggleDuskSecret(player, value, id)
    if isGhostSetupClick(1.5, player) then return end
    setupState.duskSecret = not setupState.duskSecret
    refreshVariantToggle("toggleDuskSecret", setupState.duskSecret,
        "Secret Dusk: ON\n(argue freely, then commit your night in secret — all revealed at once)",
        "Secret Dusk: OFF\n(standard — you declare where you sleep out loud, in turn order)")
end

-- Solo (§20.3 → an official mode). One player runs three characters. Every
-- anti-alpha mechanism is anti-SOLO by definition — private hands, the ghost
-- word-limit and Secret Dusk are all meaningless or merely annoying with one
-- brain — so the mode's actual content is suspending them.
function onToggleSolo(player, value, id)
    if isGhostSetupClick(1.5, player) then return end
    setupState.solo = not setupState.solo
    if setupState.solo then
        -- Secrecy against yourself is pure friction. Turning it off with the
        -- toggle (rather than silently ignoring it later) keeps the setup
        -- panel an honest description of the game about to be played.
        setupState.duskSecret = false
        refreshVariantToggle("toggleDuskSecret", false,
            "Secret Dusk: ON\n(argue freely, then commit your night in secret — all revealed at once)",
            "Secret Dusk: OFF\n(standard — you declare where you sleep out loud, in turn order)")
    end
    refreshVariantToggle("toggleSolo", setupState.solo,
        "Solo: ON\n(one player runs 3 characters — hands open, no ghost word-limit, no Dusk secrecy)",
        "Solo: OFF\n(a normal 3-5 player game)")
end

-- Mode selector (Design §17.2). Difficulty and length are separate dials:
-- STORY / STANDARD / NIGHTMARE are three difficulties on the same full
-- 7-day arc, and LONG WEEKEND is a *length* — a 3-day teaching format —
-- listed last because it is not "easy mode", it is "short mode".
--
-- Ordered easiest → hardest → short, so each click steps up in difficulty
-- and the length option sits at the end rather than masquerading as the
-- bottom of the difficulty ladder (which is exactly how the old
-- weekend/standard/nightmare cycle mis-taught it).
--
-- Default is Story: a first group gets the gentlest *full week*, so they
-- meet the Eye of Terror, fight the Source, and get to use a Signature at
-- the moment §6.7 tuned it for. The old default (Long Weekend) handed them
-- Phase 1 and half of Phase 2 and called it Easy.
--
-- Global (not local): startGuidedSetup resets the toggle label from these
-- before this point in the chunk is reached lexically.
DIFFICULTY_CYCLE = { "story", "standard", "nightmare", "weekend" }
DIFFICULTY_BLURBS = {
    story     = "Mode: STORY — the full week, gentler\n(7 days, Doom track to 35, a 6 HP Source. Recommended for your first game.)",
    standard  = "Mode: STANDARD\n(the full 7-day week, as tuned)",
    nightmare = "Mode: NIGHTMARE\n(7 days. Doom +1 in Phases 3-4, a 9 HP Source, and the week opens on Strange Days. Winnable — barely.)",
    weekend   = "Mode: LONG WEEKEND — short, not easy\n(3 days, Doom track to 15. A weeknight game or a teach; you won't meet the Eye or the Source.)",
}

function onToggleDifficulty(player, value, id)
    if isGhostSetupClick(1.5, player) then return end
    local current = setupState.difficulty or "story"
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
    if isGhostSetupClick(1.5, player) then return end
    UI.hide("setupStepVariants")
    gameState.turnStyle = setupState.rotationTurns and "rotate" or "full"
    if setupState.rotationTurns then
        broadcastEvent("proc", "Variant on — Rotation turns: each player takes 1 action at a time, going around the table until everyone has used all 3.")
    end
    gameState.duskSecret = setupState.duskSecret or false
    if gameState.duskSecret then
        broadcastEvent("proc", "Variant on — Secret Dusk: argue all you like, then commit your night privately. Everyone's move lands at once when the light goes.")
    end
    gameState.solo = setupState.solo or false
    if gameState.solo then
        broadcastEvent("proc", "SOLO MODE: one player, three characters. Play every hand face up, ignore the ghost's one-word limit, and skip Dusk secrecy — those rules exist to stop one player driving everyone, which is the whole point here.")
    end
    gameState.difficulty = setupState.difficulty or "standard"
    if gameState.difficulty ~= "standard" then
        local diff = getDifficulty()
        -- doomDelta is a flat number OR a per-phase table (§17.2), so it is
        -- described through describeDoomDelta rather than concatenated — the
        -- old `(diff.doomDelta or 0) > 0` threw "attempt to compare table with
        -- number" the moment Nightmare's surcharge became per-phase.
        broadcastEvent("proc", "Mode: " .. diff.label .. " — " .. diff.days ..
            " days, Doom track to " .. diff.doomLimit ..
            describeDoomDelta(diff) ..
            (diff.sourceHP and (", The Source at " .. diff.sourceHP .. " HP") or "") .. ".")
        -- Say out loud which dial was turned. A table that picks Long Weekend
        -- expecting "easy" and gets three days is the exact confusion the
        -- separated dials exist to prevent (§17.2).
        if (diff.days or 7) < 7 then
            broadcastEvent("warn", "Long Weekend is a SHORT game, not an easy one: 3 days means you won't meet the Eye of Terror or The Source. For a gentler full week, restart and pick Story.")
        end
    end
    -- The path variant was picked (and the board painted) in step 1, BEFORE
    -- the difficulty existed — so a Long Weekend game got the 30-cell board
    -- and the marker stopped halfway down a track labelled to 30. Repaint now
    -- that the Doom limit is known. applyPathVariant no-ops when the image is
    -- already the right one, so Standard costs nothing.
    safecall(function() applyPathVariant(gameState.pathVariant) end, "BoardForDifficulty")
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

-- Rebuild the pick queue from who is ACTUALLY seated right now.
--
-- The walkthrough moves people between seats while it runs (every pick
-- reseats the picker onto their character's colour, sometimes swapping two
-- players through a spare), and real tables also gain, lose and reshuffle
-- players mid-setup. Any of that can leave the queue holding a colour
-- nobody sits on, or a colour whose occupant has already picked — the
-- walkthrough then waits forever on a seat that can never answer, which is
-- what "Step 2 — <name> picks a character" that never advances actually
-- is. A seated player with no character is always added back, so nobody
-- can be locked out of their own setup either.
local function reconcilePendingColors()
    local queue, queued = {}, {}
    local function offer(c)
        if queued[c] or setupState.charPicks[c] then return end
        local seated = false
        pcall(function() seated = (Player[c] and Player[c].seated) or false end)
        if not seated then return end
        queued[c] = true
        queue[#queue + 1] = c
    end
    for _, c in ipairs(setupState.pendingColors) do offer(c) end
    for _, c in ipairs(getActivePlayerColors()) do offer(c) end
    setupState.pendingColors = queue
end

-- Console diagnostic (docs/debugging.md). The walkthrough's state is a
-- file-local table, so a stuck setup was invisible from outside the game —
-- this prints it, and logs it where the autosave keeps it.
function dumpSetupState()
    local function join(t, empty)
        return (#t > 0) and table.concat(t, ", ") or empty
    end
    local queue = {}
    for _, c in ipairs(setupState.pendingColors) do
        queue[#queue + 1] = c .. "=" .. _seatLabel(c)
    end
    local picks = {}
    for c, n in pairs(setupState.charPicks) do picks[#picks + 1] = c .. "=" .. n end
    local seats = {}
    for _, c in ipairs(getActivePlayerColors()) do seats[#seats + 1] = c .. "=" .. _seatLabel(c) end
    local msg = string.format(
        "[setup] step=%s running=%s host=%s | waiting: %s | picked: %s | seated: %s",
        tostring(setupState.step), tostring(setupState.inProgress),
        tostring(setupState.hostColor),
        join(queue, "nobody"), join(picks, "nobody"), join(seats, "nobody"))
    print(msg)
    if logMessage then pcall(function() logMessage("proc", msg) end) end
    return msg
end

function showCharPickForNextPlayer()
    reconcilePendingColors()
    -- Log-only (not a broadcast): players don't need the queue narrated,
    -- but a stuck table's autosave has to carry it.
    if logMessage then safecall(function() dumpSetupState() end, "SetupDump") end
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
    -- Swallowing a ghost-panel click silently is what made the original bug
    -- unescapable — the player clicked every card on a dead window while the
    -- game had already started. isGhostSetupClick closes it and says why.
    if isGhostSetupClick(2, player) then return end

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
    -- A seated player who hasn't got a character yet always picks for
    -- themself, even when the queue has lost track of their seat (they
    -- joined late, or moved while the walkthrough ran). The old code
    -- refused them outright — a dead end, because the queue was waiting on
    -- a seat they were no longer in, so nothing they clicked could ever
    -- register and nothing on screen said why.
    if not waiting and not setupState.charPicks[player.color] then
        local seatedNow = false
        pcall(function()
            seatedNow = (Player[player.color] and Player[player.color].seated) or false
        end)
        if seatedNow then
            color = player.color
            waiting = true
        end
    end
    if not waiting then
        color = setupState.pendingColors[1]
        if not color then return end
        if player.color ~= setupState.hostColor and not setupState.charPicks[player.color] then
            broadcastEvent("proc", tostring(player.steam_name or player.color) ..
                " clicked a character but is not seated in this game — sit at a colour, or ask the host to pick.")
            broadcastToColor("Sit down at a colour first (or ask the host to pick for you) — spectators can't pick a character.",
                player.color, BROADCAST_COLORS.damage)
            return
        end
        broadcastEvent("proc", tostring(player.steam_name or player.color) ..
            " picks " .. charName .. " for the " .. color .. " seat.")
    end

    for i, c in ipairs(setupState.pendingColors) do
        if c == color then table.remove(setupState.pendingColors, i) break end
    end

    -- Close the pick panel BEFORE the reseat: Player.changeColor rebuilds
    -- the moved player's UI canvas, and anything issued after it can miss
    -- that client entirely.
    UI.hide("setupStep2")

    local finalColor = color
    safecall(function() finalColor = reseatPlayerForCharacter(color, charName) end, "Reseat")
    setupState.charPicks[finalColor] = charName
    -- The picker can land on a colour that is itself still in the queue
    -- (their character's seat was empty but queued from an earlier swap).
    -- Left there, they became the head of their own queue — "<name> picks a
    -- character" forever, one more card greyed out on every click.
    for i = #setupState.pendingColors, 1, -1 do
        if setupState.pendingColors[i] == finalColor then
            table.remove(setupState.pendingColors, i)
        end
    end
    broadcastEvent("proc", charName .. " assigned to " .. finalColor .. ".")

    -- Show briefing for this player (Step 3 interleaved)
    showCharBriefing(finalColor, charName)

    -- ...then repair the reseated client once its rebuilt canvas exists.
    safecall(function()
        Wait.frames(function() safecall(syncSetupPanels, "SetupSync") end, 3)
    end, "SetupSync")
end

-----------------------------------------------------------------------
-- H.2 — Character Briefing Popup (Step 3, one per player)
-----------------------------------------------------------------------
-- CHAR_BRIEFINGS lives in lua/character_briefings.lua, AUTO-GENERATED from
-- content/help/character_briefings.md. Edit the markdown, not the table.

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
    if isGhostSetupClick(3, player) then return end
    UI.hide("charBriefing")
    if not setupState.inProgress then
        -- Ghost briefing on a client that missed a hide: returning a
        -- character "to the pool" after setup finished would drag the whole
        -- table back into the walkthrough mid-game.
        safecall(syncSetupPanels, "SetupSync")
        return
    end
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
    if isGhostSetupClick(3, player) then return end
    UI.hide("charBriefing")
    if not setupState.inProgress then
        -- Same ghost-click guard as onBriefBack, and the costlier one: this
        -- path ends in finalizeGuidedSetup, so a stray late click used to
        -- re-run setup — wiping the party and resetting the game to Day 1.
        safecall(syncSetupPanels, "SetupSync")
        return
    end

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
    setupState.pendingColors = {}
    setupState.briefingColor = nil
    pcall(function() if Turns and Turns.enable then Turns.enable = false end end)
    -- Close every walkthrough panel. Nothing below re-opens them, so a panel
    -- still on screen once the game starts is a dead end with no way back.
    safecall(syncSetupPanels, "SetupSync")

    -- Run the actual Setup logic with the picked characters
    broadcastEvent("phase", "Setting up Starve No More...")

    -- 1. Path variant already set (announced with the rest, below)

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
    gameState.resources = {}   -- fresh held-resource counts

    local seated = {}
    for color, _ in pairs(setupState.charPicks) do
        table.insert(seated, color)
    end
    gameState.playerCount = #seated
    gameState.turnOrder = seated
    gameState.turnIndex = 0

    local roster = {}   -- one "who is who" line instead of one broadcast each
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

        roster[#roster + 1] = charName .. " (" .. color .. ")"
    end

    -- Characters nobody picked leave the map for the bench.
    safecall(function() benchUnusedCharacters() end, "Bench")
    safecall(function() benchUnusedBoards() end, "BenchBoards")
    safecall(function() refreshQuickStartCard() end, "QuickStart")

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
    gameState.cluesFound = {}          -- Truth Run (§16.2)
    gameState.clueCount = 0
    gameState.cluesSurfaced = 0
    gameState.openingOffered = {}      -- guided opening (§15.9)
    gameState.duskPending = {}         -- secret Dusk commitments (§11.3)

    local counter = getDayCounter()
    if counter then counter.setValue(1) end
    moveDoomMarker(0)

    -- 7. Started
    gameState.started = true

    -- Staged, one idea at a time — see stageBroadcasts (global.lua). The
    -- guided path already named everyone as they picked, so the roster here
    -- is a single reminder line rather than one broadcast per seat.
    local queue = {
        {"proc", "Playing today: " .. table.concat(roster, ", ") .. "."},
        {"proc", "Path layout: " .. (gameState.pathVariant or "Compact") .. " (the lines printed on the board are the routes you can walk)."},
    }
    for _, m in ipairs(tableOrientationMessages()) do queue[#queue + 1] = m end
    queue[#queue + 1] = {"phase", "Setup complete! Day 1 begins. Click 'Begin Day' to reveal the first Dawn card."}
    stageBroadcasts(queue, 1.0)

    -- Refresh UI
    Wait.time(function()
        -- Second pass, after every reseat's canvas rebuild has settled:
        -- the last picker's client is the one that misses the first hide.
        safecall(syncSetupPanels, "SetupSync")
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
    -- panel too — new players need to re-read them after the fade. Staged,
    -- because five paragraphs arriving together is the very first thing a new
    -- table sees, and it reads as a wall rather than as an introduction. The
    -- content note (§18.19 item 5) still lands before characters are chosen —
    -- staging orders the messages, it does not defer them past the decision.
    stageBroadcasts({
        {"warn", "Welcome to Starve No More."},
        {"warn", "Sit at any colour for now — when you pick your character during Setup, your seat colour changes to match it (James=Blue, Coco=White, Rayman=Green, Ellie=Yellow, Luca=Red)."},
        {"proc", "Content note: cosmic horror. Darkness that hunts you, bodies that fail, and some grim writing when a character falls."},
        -- RULEBOOK is the leftmost tab but currentHelpTab defaults to "quick"
        -- (ui_help.lua), so '?' lands on Quick Start. Saying "its first tab is
        -- the rulebook" sent players looking at a page they weren't on.
        {"gain", "Press '?' anytime for help — it opens on QUICK START, and the RULEBOOK tab beside it is the complete player rulebook, page by page, so nobody has to go looking for rules outside the game. Press 'What now?' if you're stuck. The Message Log (bottom right) keeps everything said — nothing is lost when a broadcast fades."},
        {"warn", "Click 'Setup Game' on the Host Controls panel (top-left), or hover anything to see what it does."},
    })

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
