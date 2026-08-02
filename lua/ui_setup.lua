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

    -- The intro is click-through now, so it can still be open when the host
    -- starts setup. Close it rather than stack a second modal on top of it.
    safecall(function() closeWelcomeSequence() end, "Welcome")

    setupState.inProgress = true
    setupState.step = 1
    setupState.hostColor = hostColor
    setupState.pickedPath = nil
    setupState.charPicks = {}
    setupState.pendingColors = {}
    setupState.confirmPickFor = nil -- pending "pick for another seat" confirm
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

    -- Shown ONLY to the seats that still have to pick, plus the host. It
    -- used to be table-wide, which is how a player who had already picked
    -- could click a second card and have it assigned to somebody else's
    -- seat. Restricted like this, an ordinary player's click can only ever
    -- be their own; the host keeps the panel because the hotseat path (one
    -- person driving several seats) runs through it, behind the confirm
    -- click in onPickChar.
    local seats = {}
    for _, c in ipairs(setupState.pendingColors) do seats[#seats + 1] = c end
    local hostWaiting = false
    for _, c in ipairs(seats) do
        if c == setupState.hostColor then hostWaiting = true break end
    end
    if setupState.hostColor and not hostWaiting then
        seats[#seats + 1] = setupState.hostColor
    end
    UI.setAttribute("setupStep2", "visibility", table.concat(seats, "|"))

    local others = {}
    for i = 2, #setupState.pendingColors do
        table.insert(others, _seatLabel(setupState.pendingColors[i]))
    end
    UI.setAttribute("step2Title", "text", "Step 2 — pick your character")
    local sub = "Click a card to choose. Your seat colour changes to match your character when setup finishes."
    if #others > 0 then
        sub = sub .. "\nStill choosing: " .. _seatLabel(setupState.pendingColors[1]) ..
            ", " .. table.concat(others, ", ") .. " — first click takes the card."
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
-- (CHARACTER_COLORS, global.lua), so everyone is reseated onto their
-- character's colour and pointer, hand zone, standee holder and roster
-- all match.
--
-- That reseat used to happen ON EACH PICK, inside the walkthrough, and it
-- was the wrong moment for it. Player.changeColor rebuilds the moved
-- client's UI canvas, so a swap fired three canvas rebuilds that raced the
-- panel show/hide of the *next* pick, and the live queue (pendingColors,
-- hostColor) had to be rewritten mid-flow to follow the players around.
-- A real table came out of it with the host holding two characters and one
-- player who never chose at all.
--
-- Now nothing moves until finalize: picks are recorded against whatever
-- seat the player is already sitting in, and the whole permutation is
-- applied once, after the walkthrough's panels are closed and the queue is
-- empty. There is no UI left to lose and no queue left to patch up.
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

local function _seatedAt(color)
    local seated = false
    pcall(function() seated = (Player[color] and Player[color].seated) or false end)
    return seated
end

local function _changeColor(from, to)
    -- Always index Player fresh: the handle held before a changeColor is
    -- stale afterwards (docs/tts-interface.md).
    local moved = false
    pcall(function() moved = Player[from].changeColor(to) and true or false end)
    return moved
end

-- Seat every picker on their character's colour. Returns the remap
-- { [seatTheyPickedFrom] = seatTheyEndedOn } for every player that moved.
--
-- Targets are distinct by construction (each character maps to its own
-- colour and is picked at most once), so this is a permutation: resolve it
-- by repeatedly moving anyone whose target is already free, and when only
-- a closed cycle is left, park one member on a spare seat to open a hole.
-- Nobody is left on a spare — a player stranded off the five character
-- seats has no hand zone and TTS keeps prompting them to "Choose Color".
local function applyCharacterSeating()
    local remap, pending, origin = {}, {}, {}
    for color, charName in pairs(setupState.charPicks) do
        local target = CHARACTER_COLORS and CHARACTER_COLORS[charName]
        if target and target ~= color and _seatedAt(color) then
            pending[color] = target
            origin[color] = color
        end
    end

    -- Evict anyone squatting a needed seat who picked nothing at all (a
    -- spectator sitting on a character colour). Players who DID pick sort
    -- themselves out through the permutation below.
    for _, target in pairs(pending) do
        if setupState.charPicks[target] == nil and _seatedAt(target) then
            local spare = _freeSpareSeat()
            if spare then _changeColor(target, spare) end
        end
    end

    local guard = 0
    while next(pending) and guard < 16 do
        guard = guard + 1
        local ready = {}
        for from, to in pairs(pending) do
            if not _seatedAt(to) then ready[#ready + 1] = from end
        end
        for _, from in ipairs(ready) do
            local to = pending[from]
            if _changeColor(from, to) then
                remap[origin[from]] = to
                pending[from], origin[from] = nil, nil
            else
                pending[from], origin[from] = nil, nil   -- engine refused; leave them put
            end
        end
        if #ready == 0 then
            -- Closed cycle: everyone left is blocked by someone who is also
            -- waiting to move. Park one on a spare to break it.
            local from = next(pending)
            local spare = _freeSpareSeat()
            if not (spare and _changeColor(from, spare)) then break end
            pending[spare], origin[spare] = pending[from], origin[from]
            pending[from], origin[from] = nil, nil
        end
    end
    return remap
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
        -- Picking FOR another seat is the hotseat path — one person at the
        -- keyboard driving several characters. It used to fire on the first
        -- click with no warning, which is how a host who had already picked
        -- his own character clicked a second card and had it assigned to the
        -- next seat in the queue. The log read as if that player had chosen
        -- it; they had never clicked anything, and the panel was still open
        -- in front of them.
        --
        -- The queue only ever holds SEATED colours (reconcilePendingColors),
        -- so "is somebody there?" cannot distinguish a hotseat from a real
        -- second player. Ask instead: the first click warns, a second click
        -- on the same card goes through. Hotseat still works, in two clicks
        -- rather than one; the accident does not.
        if _seatedAt(color) then
            local confirmKey = color .. ":" .. charName
            if setupState.confirmPickFor ~= confirmKey then
                setupState.confirmPickFor = confirmKey
                broadcastToColor(
                    _seatLabel(color) .. " is seated and hasn't picked yet — that choice is theirs. " ..
                    "If you're playing their seat too, click " .. charName ..
                    " again to pick it for them.",
                    player.color, BROADCAST_COLORS.warn)
                return
            end
        end
        setupState.confirmPickFor = nil
        broadcastEvent("proc", tostring(player.steam_name or player.color) ..
            " picks " .. charName .. " for the " .. color .. " seat.")
    end

    for i, c in ipairs(setupState.pendingColors) do
        if c == color then table.remove(setupState.pendingColors, i) break end
    end

    -- Recorded against the seat the player is sitting in RIGHT NOW. Nobody
    -- changes colour until finalize (applyCharacterSeating), so there is no
    -- canvas rebuild to race and no queue entry to chase around the table.
    setupState.charPicks[color] = charName
    setupState.confirmPickFor = nil
    broadcastEvent("proc", charName .. " goes to " .. _seatLabel(color) ..
        ". (Seat colours are set to match characters when setup finishes.)")

    -- Show briefing for this player (Step 3 interleaved)
    showCharBriefing(color, charName)
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

    UI.hide("setupStep2")
    local text = CHAR_BRIEFINGS[charName] or ("You are " .. charName .. ".")
    UI.setAttribute("briefTitle", "text", "You are " .. charName)
    UI.setAttribute("briefBody", "text", formatBriefingBody(text))
    -- Your character sheet, shown to you. Table-wide, everyone got a popup
    -- about somebody else's character and anyone could dismiss it — so the
    -- Continue that advanced the walkthrough was routinely clicked by a
    -- player who had not read a word of it.
    --
    -- The host keeps it too. Continue is what advances the walkthrough, and
    -- restricting it to one seat would put the whole table behind whoever
    -- just wandered off to make a coffee.
    if color then
        local seats = color
        if setupState.hostColor and setupState.hostColor ~= color then
            seats = seats .. "|" .. setupState.hostColor
        end
        UI.setAttribute("charBriefing", "visibility", seats)
    end
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
-- The body of finalize. Called under pcall by finalizeGuidedSetup so that a
-- throw in here can never strand the table (see the wrapper below).
local function runGuidedSetupFinalize()
    -- Run the actual Setup logic with the picked characters
    broadcastEvent("phase", "Setting up Starve No More...")

    -- 1. Path variant already set (announced with the rest, below)

    -- 2. Shuffle Phase decks
    safecall(function()
        for p = 1, 4 do
            local deck = getPhaseDeck(p)
            if deck then deck.shuffle() end
        end
    end, "PhaseDecks")

    -- 3. Market — deal the display row (empty slots only; re-setup safe)
    safecall(function() dealMarketDisplay() end, "Market")

    -- 4. Threat deck
    safecall(function()
        local threatDeck = getThreatDeck()
        if threatDeck then threatDeck.shuffle() end
    end, "ThreatDeck")

    -- 4.5. NOW everybody moves onto their character's colour — once, with
    -- the walkthrough closed and the queue empty. Re-key the picks onto the
    -- seats people actually ended up in, so everything below (activeChars,
    -- turn order, hand zones) is keyed by the final colour.
    local remap = {}
    safecall(function() remap = applyCharacterSeating() or {} end, "Reseat")
    if next(remap) then
        local reseated = {}
        for color, charName in pairs(setupState.charPicks) do
            reseated[remap[color] or color] = charName
        end
        setupState.charPicks = reseated
        setupState.hostColor = remap[setupState.hostColor] or setupState.hostColor
    end

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

        safecall(function() placeCharacterAtTile(charName, home) end, "PlaceChar")

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

    -- Both touch physical object handles, so both are safecall'd: an object
    -- that was deleted, merged into a deck or never spawned throws on the
    -- dead handle, and neither gadget is worth failing setup over.
    safecall(function()
        local counter = getDayCounter()
        if counter then counter.setValue(1) end
    end, "DayCounter")
    safecall(function() moveDoomMarker(0) end, "DoomMarker")

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
-- Finalize setup — the wrapper that cannot strand the table.
--
-- The body above touches a lot of physical objects, and one throw in the
-- middle of it used to be terminal: gameState.activeChars was already
-- written but `gameState.started = true` was not, so the game sat at
-- PreGame *with a full party*, Host Controls stayed hidden (they are
-- hidden on purpose while the walkthrough runs, and nothing re-ran
-- refreshHostControls), and the banner advised "Click Setup to begin"
-- beside no Setup button. The only way out was reloading the mod.
--
-- So: close the walkthrough FIRST (that part must happen either way), run
-- the body under pcall, and always end on a HUD refresh. Paired with the
-- zero-button escape in refreshHostControls (ui_controls.lua), a failed
-- setup is now a retryable error instead of a dead end.
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

    local ok, err = pcall(runGuidedSetupFinalize)
    if not ok then
        broadcastEvent("damage", "Setup stopped on an error: " .. tostring(err))
        broadcastEvent("warn", "Nothing is lost — Host Controls are back. Click Restart, then Setup Game to try again.")
    end

    -- Always, on both paths: the HUD is the only way back to a button.
    safecall(syncSetupPanels, "SetupSync")
    safecall(function() refreshPhaseBanner() end, "Banner")
end

-----------------------------------------------------------------------
-- H.6 — Welcome sequence on first load
-----------------------------------------------------------------------
-- The introduction, one page per click. These were five staged broadcasts;
-- a broadcast fades on a timer the reader did not choose, which is the wrong
-- control for the very first thing a new table ever sees. Same words, now
-- paced by the player (welcomePanel, dialogs.xml).
--   { category, title, body }   -- category feeds the Message Log colour
WELCOME_PAGES = {
    {"warn", "Welcome to Starve No More",
     "Five teenagers. Seven days. Something out there is hungry.\n\n" ..
     "You all win together or you all lose together — there is no solo victory in this game."},
    {"warn", "Take any seat",
     "Sit at any colour for now. When you pick your character during Setup, your seat colour changes to match them:\n\n" ..
     "James = Blue     Coco = White     Rayman = Green\nEllie = Yellow     Luca = Red"},
    {"proc", "Content note",
     "Cosmic horror. Darkness that hunts you, bodies that fail, and some grim writing when a character falls."},
    -- RULEBOOK is the leftmost tab but currentHelpTab defaults to "quick"
    -- (ui_help.lua), so '?' lands on Quick Start. Saying "its first tab is
    -- the rulebook" sent players looking at a page they weren't on.
    {"gain", "Where the help lives",
     "Press '?' anytime — it opens on QUICK START, and the RULEBOOK tab beside it is the complete player rulebook, page by page, so nobody has to go looking for rules outside the game.\n\n" ..
     "Press 'What now?' if you're stuck. The Message Log (bottom right) keeps everything said — including these pages."},
    {"warn", "Ready when you are",
     "Click 'Setup Game' on the Host Controls panel (top-left) to begin.\n\n" ..
     "Hover anything on the table to see what it does."},
}

local welcomePage = 0

local function renderWelcomePage()
    if not UI then return end
    local page = WELCOME_PAGES[welcomePage]
    if not page then return end
    UI.setAttribute("welcomeTitle", "text", page[2])
    UI.setAttribute("welcomeBody", "text", page[3])
    UI.setAttribute("welcomeStep", "text", welcomePage .. " of " .. #WELCOME_PAGES)
    UI.setAttribute("welcomeBack", "interactable", welcomePage > 1 and "true" or "false")
    -- setButtonLabel, not a bare text attribute: setting a Button's text on
    -- its own resets the styling to near-black (docs/tts-interface.md).
    if welcomePage >= #WELCOME_PAGES then
        setButtonLabel("welcomeNext", "Let's begin", "#12300F", "#CFE8CFF2")
    else
        setButtonLabel("welcomeNext", "Next ▸", "#12300F", "#CFE8CFF2")
    end
    UI.show("welcomePanel")
end

function closeWelcomeSequence()
    welcomePage = 0
    if UI then UI.hide("welcomePanel") end
end

function onWelcomeNext(player, value, id)
    -- A click on a ghost panel (a client that missed the hide) must close it,
    -- not walk a sequence that is already over.
    if welcomePage <= 0 or welcomePage >= #WELCOME_PAGES then
        closeWelcomeSequence()
        return
    end
    welcomePage = welcomePage + 1
    renderWelcomePage()
end

function onWelcomeBack(player, value, id)
    if welcomePage <= 1 then return end
    welcomePage = welcomePage - 1
    renderWelcomePage()
end

function onWelcomeSkip(player, value, id)
    closeWelcomeSequence()
end

function showWelcomeSequence()
    if gameState.started or gameState.welcomed then return end

    -- Every page also goes straight into the Message Log, so a player who
    -- skips (or joins late) can still read all of it. logMessage rather than
    -- broadcastEvent: a broadcast here would put the fading toast back.
    for _, page in ipairs(WELCOME_PAGES) do
        if logMessage then
            pcall(function() logMessage(page[1], page[2] .. " — " .. page[3]) end)
        end
    end

    welcomePage = 1
    renderWelcomePage()

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
