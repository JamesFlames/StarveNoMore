-- ui_rules.lua  ("Rules in effect" panel + day-cycle strip)
--
-- Design §18.10 extension: broadcasts scroll away and Help tabs must be
-- opened, so every rule that is CURRENTLY modifying play is mirrored into
-- one persistent, auto-refreshing panel. Refreshed from refreshPhaseBanner()
-- on every state change — no manual bookkeeping anywhere else.

-----------------------------------------------------------------------
-- What happens in the current sub-phase (always the first line)
-----------------------------------------------------------------------
SUBPHASE_RULES = {
    PreGame  = "Pre-game. Click Setup Game to begin.",
    Dawn     = "DAWN: Doom advances (+1 per threat left on the map), then the Dawn card applies to everyone.",
    Day      = "DAY: 3 actions each — Move, Gather, Craft, Cook, Fight, Rest, Cleanse. Trade is free at your tile.",
    Dusk     = "DUSK: optional scramble 1 tile (1 Hunger). You sleep where you stand. A house sleeps 2 comfortably; extras get no sleep regen.",
    Night    = "NIGHT: threats drawn at occupied tiles. No light source = Charlie attack. Then sleep.",
    Tick     = "TICK: everyone loses 1 Hunger + 1 Sanity (Rayman: 2 Hunger). Hunger 0 = lose 1 Health.",
    PreDawn  = "Between days. Host clicks Begin Day to start the next day.",
    GameOver = "Game over. Click Restart to play again.",
}

-----------------------------------------------------------------------
-- Doom threshold effects (flags set in checkDoomThresholds)
-----------------------------------------------------------------------
DOOM_THRESHOLD_RULES = {
    { "doom10", "Doom 10+: Night threat draws +1 at all locations." },
    { "doom15", "Doom 15+ (Scarcity): every craft costs +1 extra resource." },
    { "doom20", "Doom 20+: everyone loses +1 extra Sanity at Tick." },
    { "doom25", "Doom 25+ (Nothing Left to Lose): +1 attack die for everyone; Rest heals +1 Health anywhere." },
}

-----------------------------------------------------------------------
-- Ongoing Dawn-card effect flags → player-readable rule text.
-- Bookkeeping-only flags (doom10..25, *Defeated) are handled elsewhere
-- or deliberately absent.
-----------------------------------------------------------------------
EFFECT_RULES = {
    noHouseThreats      = "Quiet night: no threats spawn at house tiles tonight.",
    flashlightsDisabled = "Flashlights are dead — only Fire counts as light tonight.",
    onlyFireLight       = "Only Fire counts as light — flashlights and batteries do nothing.",
    restNoHunger        = "Rest restores no Hunger today.",
    restNoSanity        = "Rest restores no Sanity today.",
    restNoHealth        = "Rest restores no Health today.",
    bloodMoon           = "Blood Moon: threat draws +1 at every location tonight.",
    sportCourtHungerCost = "Moving to or from a sport court costs +1 Hunger.",
    rainSanityCost      = "Rain: Gather at sport courts costs +1 Sanity.",
    rainFireDisabled    = "Rain: Fire gives no light at sport courts.",
    fireDisabled        = "Every flame is out — Fire counts as no light tonight.",
    reducedActions      = "Only 2 actions per player today.",
    charlieEverywhere   = "Charlie hunts everywhere tonight — light check at every location.",
    charliePaused       = "Charlie is paused tonight — no darkness attacks.",
    moveCostPlus1       = "Move costs +1 action today.",
    reducedCapacity     = "Every house sleeps 1 fewer character.",
    missingAllyBonus    = "The player who vanished this morning gets +1 action today.",
    doomReduced         = "Doom advance is reduced by 1 this Dawn.",
    noDoomThisDawn      = "Doom does not advance this Dawn.",
    togetherBonus       = "All Together: +1 Sanity at Tick if you share a tile with an ally.",
    recipeBonusHunger   = "Recipes cooked today restore +2 extra Hunger.",
    homeSanityBonus     = "Sleeping at your own home gives +2 Sanity instead of +1.",
    crowdThreat         = "The most-populated location draws +1 threat tonight.",
    dareCourtGlow       = "DARE — court floodlights: sleep at a sport court for +2 Threats there tonight; survivors claim 2 Market cards at Dawn.",
    darePorchLight      = "DARE — porch light: the first Gather at a house today may take 3 resources instead of 1, for 2 Sanity.",
    deerclopsActive     = "DEERCLOPS is loose: everyone loses double Sanity at Tick. Festers Doom +2 each Dawn.",
    eyeActive           = "EYE OF TERROR is loose: +1 extra threat at its tile each Dawn. Festers Doom +2 each Dawn.",
    sourceActive        = "THE SOURCE is here: destroy it before Day 7 ends — while it stands, there is no victory. Festers Doom +2 each Dawn.",
}

-- Stable display order so the panel doesn't reshuffle every refresh.
EFFECT_RULE_ORDER = {
    "deerclopsActive", "eyeActive", "sourceActive",
    "bloodMoon", "charlieEverywhere", "charliePaused",
    "flashlightsDisabled", "onlyFireLight",
    "reducedActions", "moveCostPlus1",
    "restNoHunger", "restNoSanity", "restNoHealth",
    "sportCourtHungerCost", "rainSanityCost", "rainFireDisabled", "fireDisabled",
    "reducedCapacity", "crowdThreat", "noHouseThreats",
    "dareCourtGlow", "darePorchLight",
    "doomReduced", "noDoomThisDawn",
    "togetherBonus", "recipeBonusHunger", "homeSanityBonus",
    "missingAllyBonus",
}

-----------------------------------------------------------------------
-- Collect every rule currently in force into a list of lines
-----------------------------------------------------------------------
local function collectActiveRules()
    local lines = {}
    local effects = gameState.ongoingDawnEffects or {}

    -- 0) Outstanding manual steps from the current Dawn card
    for _, step in ipairs(gameState.dawnChecklist or {}) do
        if not step.done then
            table.insert(lines, "DAWN CARD TO-DO: " .. step.text)
        end
    end

    -- 0.3) Table variants chosen at setup
    if gameState.turnStyle == "rotate" then
        table.insert(lines, "VARIANT — Rotation turns: take 1 action, then the next player goes; play circles the table until everyone has used all 3. Pass after acting = keep your remaining actions for your next go; pass without acting = forfeit them.")
    end

    -- 0.4) The two A/B variants (§11.3 / §20.3)
    if gameState.duskSecret then
        table.insert(lines, "VARIANT — Secret Dusk: talk it through, then commit your scramble privately. Every move lands at once when Night begins. Nobody can check that you did what you said.")
    end
    if gameState.solo then
        table.insert(lines, "SOLO MODE: hands open, no ghost word-limit, no Dusk secrecy — the anti-alpha rules are off because there is only one of you.")
    end
    -- 0.6) Active Scenario (§17.3): its rules apply all game
    if gameState.scenario and SCENARIOS and SCENARIOS[gameState.scenario] then
        local sc = SCENARIOS[gameState.scenario]
        table.insert(lines, "SCENARIO — " .. sc.name .. ": " .. sc.description)
    end

    -- 1) Doom thresholds crossed
    for _, entry in ipairs(DOOM_THRESHOLD_RULES) do
        if effects[entry[1]] then table.insert(lines, entry[2]) end
    end

    -- 2) Ongoing Dawn-card effects
    for _, key in ipairs(EFFECT_RULE_ORDER) do
        if effects[key] then table.insert(lines, EFFECT_RULES[key]) end
    end
    if effects.strayCat then
        table.insert(lines, "A stray cat follows " .. tostring(effects.strayCat) ..
            ": +1 Sanity at Tick (flees if they take damage).")
    end
    -- The Source's live HP + its announced phase beat (§12.6)
    if effects.sourceActive and gameState.bossHP and gameState.bossHP.source then
        if gameState.sourceSplit then
            table.insert(lines, "The Source stands at " .. gameState.bossHP.source ..
                " HP. It has already split — finish it.")
        else
            table.insert(lines, "The Source stands at " .. gameState.bossHP.source ..
                " HP. At " .. getSourceSplitHP() ..
                " HP it SPLITS: two Terror Beaks peel off to adjacent tiles.")
        end
    end

    -- 2.2) Truth Run progress (§16.2). Stated as a live rule, not left to be
    -- reconstructed at game end: a bonus victory nobody is tracking is one
    -- nobody plays toward, which was half of what made it dead content.
    local clues = gameState.clueCount or 0
    if clues > 0 and clues < (CLUES_FOR_TRUTH_RUN or 3) then
        table.insert(lines, "TRUTH RUN: " .. clues .. " of " .. (CLUES_FOR_TRUTH_RUN or 3) ..
            " Clues found. The Sealed Basement holds one; the rest surface in the Market.")
    elseif clues >= (CLUES_FOR_TRUTH_RUN or 3) then
        table.insert(lines, "TRUTH RUN secured — all 3 Clues found. Survive the week and the ending changes.")
    end

    -- 2.5) The Wrongness (design_batch3.md §4): a deferred face-down threat
    if gameState.wrongness then
        table.insert(lines, "SOMETHING IS WRONG at " .. (gameState.wrongness.location or "?") ..
            ": an unresolved threat sits face-down. Go look — or it resolves at the next Dawn, where it stands.")
    end

    -- 2.7) Persistent threats standing on tiles (lua/threat_persistent.lua).
    -- These change what an action does at a tile for as long as the card is
    -- there, which is precisely what this panel is for — and the rule is
    -- otherwise only visible on a card face somebody has to walk over and
    -- read. Each line ends in the one verb that removes it.
    local persistents = persistentThreatsEverywhere()
    for _, locName in ipairs(LOCATION_ORDER) do
        for _, p in ipairs(persistents[locName] or {}) do
            local how
            if p.rule.fought then
                how = "Fight it."
            elseif p.rule.sealed then
                how = "Pry it open (free action + tool)."
            else
                how = "Clear it: " .. CLEAR_PERSISTENT_ACTIONS .. " actions + " ..
                      CLEAR_PERSISTENT_WOOD .. " Wood."
            end
            table.insert(lines, p.name .. " at " .. locName .. ": " ..
                (p.rule.blurb or "It stays until cleared.") ..
                " Festers Doom +1 each Dawn. " .. how)
        end
    end

    -- 2.8) Hard threats whose printed rider keeps applying while they stand
    -- (the Shadow Stalker's Tick tax, the Scarecrow's Gather tax, the Glass
    -- Child's nightly one). Only the standing kind: a rider that fires inside
    -- a fight is announced by the fight.
    local hardStanding = threatCardsByTile(HARD_THREAT_SPECIALS)
    for _, locName in ipairs(LOCATION_ORDER) do
        for _, t in ipairs(hardStanding[locName] or {}) do
            if t.rule.tickSanityAtTile or t.rule.gatherSanityAtTile or t.rule.nightSanityAtTile then
                table.insert(lines, t.name .. " at " .. locName .. ": " ..
                    (t.rule.blurb or "It is still here.") .. " Kill it to stop it.")
            end
        end
    end

    -- 2.9) Trophy powers the team has actually earned (lua/trophies.lua).
    -- The kill broadcast says "its power is live" and then scrolls away; a
    -- build-around reward nobody can see the terms of is one nobody builds
    -- around.
    for _, line in ipairs(activeTrophyRules()) do table.insert(lines, line) end

    -- 3) Treeguard mini-boss (lua/treeguard.lua)
    local tg = gameState.treeguard
    if tg and tg.active then
        table.insert(lines, "TREEGUARD at " .. (tg.location or "?") ..
            ": no Gathering there. Festers Doom +1 each Dawn. Fight it, or appease with 2 Wood at its tile.")
    end

    -- 4) Per-character statuses that change what that player may do
    for color, char in pairs(gameState.activeChars or {}) do
        if char.down then
            table.insert(lines, char.name .. " is DOWN: ghost — drifts 1 tile/round, 1 word/round. Revive with a Telltale Heart at their tile.")
        else
            if char.sanity > 0 and char.sanity < 3 then
                local rec = (gameState.haunted or {})[color]
                local seers = {}
                for wColor in pairs((rec or {}).witnesses or {}) do
                    local w = gameState.activeChars[wColor]
                    if w then table.insert(seers, w.name) end
                end
                if #seers > 0 then
                    table.insert(lines, char.name .. " is Haunted (Sanity < 3) — but " ..
                        table.concat(seers, " & ") .. " can see it too, and may fight it with them.")
                else
                    table.insert(lines, char.name .. " is Haunted (Sanity < 3): a personal threat only they can fight. An ally at their tile may pay 1 Sanity to Witness it and join the fight.")
                end
            end
            if char.hunger == 0 then
                table.insert(lines, char.name .. " is starving (Hunger 0): loses 1 Health every Tick.")
            elseif char.hunger < 3 then
                table.insert(lines, char.name .. " can't Fight (Hunger < 3). Flee is still allowed (1 tile, and free right now — Last Nerve).")
            end
            if char.health > 0 and char.health < 3 then
                table.insert(lines, char.name .. " is critically injured (Health < 3): Move costs +1 action.")
            end
            -- Last Nerve (§10.1.1): the individual death-spiral valve. Stated
            -- as a rule in effect, not left for the player to discover from a
            -- broadcast — a catch-up mechanism nobody knows about is one that
            -- never changes a decision.
            if hasLastNerve(color) then
                table.insert(lines, char.name .. " is on their LAST NERVE (a stat below 3): Flee costs no Sanity, and Rest restores 1 extra. It ends when they recover.")
            end
            if (char.charlieStreak or 0) >= 1 then
                table.insert(lines, char.name .. ": Charlie streak " .. char.charlieStreak ..
                    " — her next dark-night attack hits +" .. char.charlieStreak .. " harder.")
            end
            local sp = gameState.subPhase
            if char.name == "James" and not gameState.jamesEnergyDrinkUsed
                and (sp == "Day" or sp == "Dusk" or sp == "Night") then
                table.insert(lines, "James (Wired): needs an Energy Drink today or loses 2 Sanity at Tick.")
            end
            if char.name == "Rayman" and raymanLoudTonight()
                and (sp == "Day" or sp == "Dusk" or sp == "Night") then
                table.insert(lines, "Rayman moved today (Loud): his Night location draws +1 threat.")
            end
            local pendingSanity = (gameState.pendingSanityPenalty or {})[color]
            if pendingSanity then
                table.insert(lines, char.name .. " (All-Nighter): crashes for -" .. pendingSanity .. " Sanity at Tick.")
            end
            if char.feastActive then
                table.insert(lines, char.name .. " (The Feast): cooking costs no actions until her turn ends.")
            end
        end
    end

    return lines
end

-----------------------------------------------------------------------
-- Panel refresh (called from refreshPhaseBanner on every state change)
-----------------------------------------------------------------------
local _rulesCollapsed = false

-- Panel is 230 px wide with 16 px padding at fontSize 11 → ~36 chars/line.
local function estimateWrappedLines(text)
    return math.max(1, math.ceil(string.len(text) / 36))
end

function refreshRulesPanel()
    if not UI then return end
    if customUIHidden then return end
    if not gameState.started then
        UI.setAttribute("rulesPanel", "active", "false")
        return
    end
    local sp = gameState.subPhase or "PreGame"
    local header = SUBPHASE_RULES[sp] or ""
    local rules = collectActiveRules()

    -- Nothing special in force → no panel at all. The sub-phase header
    -- alone is already covered by the day-cycle strip and the banner.
    if #rules == 0 then
        UI.setAttribute("rulesPanel", "active", "false")
        return
    end
    UI.setAttribute("rulesPanel", "active", "true")

    local body = header
    for _, line in ipairs(rules) do
        body = body .. "\n\n• " .. line
    end

    UI.setAttribute("rulesBody", "text", body)

    if _rulesCollapsed then
        UI.setAttribute("rulesBody", "active", "false")
        UI.setAttribute("rulesPanel", "height", "36")
        UI.setAttribute("rulesToggle", "text", "+")
    else
        -- Size the panel to its content (estimate; clamped so a wild day
        -- can't cover the whole screen).
        local wrapped = estimateWrappedLines(header)
        for _, line in ipairs(rules) do
            wrapped = wrapped + estimateWrappedLines(line)
        end
        if #rules == 0 then wrapped = wrapped + 1 end
        local gaps = math.max(1, #rules)                -- blank separator lines
        local bodyHeight = wrapped * 15 + gaps * 8
        -- LowerLeft-anchored: grows upward. Clamped so a wild day can't
        -- reach the statDisplay panel in the middle of the left edge.
        local panelHeight = math.min(420, 44 + bodyHeight)
        UI.setAttribute("rulesBody", "active", "true")
        UI.setAttribute("rulesBody", "preferredHeight", tostring(bodyHeight))
        UI.setAttribute("rulesPanel", "height", tostring(panelHeight))
        UI.setAttribute("rulesToggle", "text", "–")
    end
end

function onRulesToggle(player, value, id)
    _rulesCollapsed = not _rulesCollapsed
    refreshRulesPanel()
end

-----------------------------------------------------------------------
-- Dawn-card manual-steps checklist. Populated by dispatchDawnEffect
-- (effects/dawn_effects.lua, DAWN_MANUAL_STEPS). Any player ticks a
-- step off; the panel hides itself once every step is done. Outstanding
-- steps also appear in the Rules panel (collectActiveRules above).
-----------------------------------------------------------------------
local DAWN_CHECK_MAX_ROWS = 4

function refreshDawnChecklist()
    if not UI then return end
    if customUIHidden then return end
    local list = gameState.dawnChecklist or {}
    local remaining = 0

    for i = 1, DAWN_CHECK_MAX_ROWS do
        local id = "dawnStep_" .. i
        local step = list[i]
        if step then
            UI.setAttribute(id, "active", "true")
            if step.done then
                UI.setAttribute(id, "text", "[done] " .. step.text)
                UI.setAttribute(id, "textColor", "#557755")
            else
                UI.setAttribute(id, "text", "[   ] " .. step.text)
                UI.setAttribute(id, "textColor", "#EEDDBB")
                remaining = remaining + 1
            end
        else
            UI.setAttribute(id, "active", "false")
        end
    end

    if #list == 0 or remaining == 0 then
        UI.setAttribute("dawnChecklist", "active", "false")
    else
        UI.setAttribute("dawnChecklist", "active", "true")
        local rows = math.min(DAWN_CHECK_MAX_ROWS, #list)
        UI.setAttribute("dawnChecklist", "height", tostring(50 + rows * 42))
    end

end

function onDawnStepClick(player, value, id)
    local i = tonumber(value)
    local list = gameState.dawnChecklist or {}
    local step = i and list[i]
    if not step then return end
    step.done = not step.done
    if step.done then
        broadcastEvent("proc", "Dawn step done (" .. (player.steam_name or player.color) .. "): " .. step.text)
    end
    refreshDawnChecklist()
    refreshRulesPanel()  -- keep the DAWN CARD TO-DO lines in sync
end

-----------------------------------------------------------------------
-- Day-cycle strip: Dawn ▸ Day ▸ Dusk ▸ Night ▸ Tick with the current
-- step lit, so players always see where they are in the loop.
-----------------------------------------------------------------------
local CYCLE_STEPS = { "Dawn", "Day", "Dusk", "Night", "Tick" }

local CYCLE_DIM  = "#66788A"
local CYCLE_LIT  = "#FFDD66"

function refreshCycleStrip()
    if not UI then return end
    if customUIHidden then return end
    local sp = gameState.subPhase or "PreGame"
    if not gameState.started or sp == "PreGame" or sp == "GameOver" then
        UI.setAttribute("cycleStrip", "active", "false")
        return
    end
    UI.setAttribute("cycleStrip", "active", "true")

    local parts = {}
    for _, step in ipairs(CYCLE_STEPS) do
        if step == sp then
            table.insert(parts, "<color=" .. CYCLE_LIT .. "><b>" .. string.upper(step) .. "</b></color>")
        else
            table.insert(parts, "<color=" .. CYCLE_DIM .. ">" .. step .. "</color>")
        end
    end
    local strip = table.concat(parts, " <color=" .. CYCLE_DIM .. ">▸</color> ")

    if sp == "PreDawn" then
        strip = strip .. "  <color=#88DDFF>(day done — next: Dawn)</color>"
    end

    UI.setAttribute("cycleText", "text", strip)
end
