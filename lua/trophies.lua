-- trophies.lua — the powers printed on the boss Trophy cards.
--
-- Killing a phase boss flips its Trophy face-up and the kill broadcast says,
-- twice, "its Trophy flips face-up on the trophy row — **its power is live**".
-- Neither power existed. `revealTrophy` (combat.lua) turned a card over and
-- highlighted it; that was the entire implementation. The Trophy is the whole
-- reward for the hardest content in the game — §14.1's "a boss kill should
-- visibly rescue the week, not just remove a penalty" — and it was a picture.
--
--   TR_DEERCLOPS  The Antler Sled   "Once per turn a character may bring one
--                                    co-located ally along on a Move — both
--                                    move together (both pay 1 Hunger)."
--   TR_EYE_OF_TERROR  The Watching Jar  "At each Dusk the team looks at the
--                                    top 2 Threat cards and returns them in
--                                    any order."
--   TR_SOURCE / TR_TRUTH             end-game markers, not powers (the Source
--                                    ends the week; the Truth Trophy is the
--                                    Clue achievement). Nothing to run.
--
-- Both live powers key off gameState.bossesDefeated, which markBossDefeated
-- already maintains — a trophy is earned exactly when its boss is dead, so
-- there is no second record to drift.

TROPHY_POWERS = {
    deerclops = {
        trophy = "The Antler Sled",
        blurb  = "Once per turn, one character may bring a co-located ally " ..
                 "along on their Move. Both pay 1 Hunger.",
    },
    eye = {
        trophy = "The Watching Jar",
        blurb  = "At each Dusk the team sees the top 2 Threat cards before " ..
                 "choosing where to stand.",
    },
}

-- Has the team earned this trophy? (markBossDefeated, combat.lua.)
function teamHasTrophy(key)
    return ((gameState.bossesDefeated or {})[key] == true)
end

-----------------------------------------------------------------------
-- The Antler Sled (TR_DEERCLOPS).
--
-- The pick happens AFTER the mover has arrived, so the destination is
-- already settled and the table only has one decision left: who comes too.
-- One dialog instead of two, and it reuses the Revive/Stabilize panel.
-----------------------------------------------------------------------

-- Standing allies who were at `fromLoc` when the mover left it.
function sledCandidates(color, fromLoc)
    local out = {}
    for c, ch in pairs(gameState.activeChars) do
        if c ~= color and not ch.down and ch.location == fromLoc then out[#out + 1] = c end
    end
    table.sort(out)   -- pairs() order is arbitrary; the dialog must be stable
    return out
end

-- Called from doMove once the move has landed. Returns true if the offer was
-- put to the table (the caller does nothing else with it — the dialog owns
-- the rest of the interaction).
function offerAntlerSled(color, fromLoc, toLoc)
    if not teamHasTrophy("deerclops") then return false end
    if (gameState.sledUsedThisTurn or {})[color] then return false end
    local candidates = sledCandidates(color, fromLoc)
    if #candidates == 0 then return false end

    local char = gameState.activeChars[color]
    showSledTargets(color, toLoc, candidates,
        "The Antler Sled — bring whom to " .. toLoc .. "?",
        (char and char.name or "You") .. " can pull one ally along. They pay 1 Hunger. Once per turn.")
    return true
end

-- Resolve the pick: the ally is dragged along to where the mover went.
function bringAllyOnSled(color, allyColor, toLoc)
    local ally = gameState.activeChars[allyColor]
    if not ally or ally.down then return false end

    gameState.sledUsedThisTurn = gameState.sledUsedThisTurn or {}
    gameState.sledUsedThisTurn[color] = true

    ally.hunger = math.max(0, ally.hunger - 1)
    ally.location = toLoc

    local mover = gameState.activeChars[color]
    broadcastEvent("gain", (mover and mover.name or "?") .. " pulls " .. ally.name ..
        " along on the Antler Sled to " .. toLoc .. ". (-1 Hunger, no action.)")

    safecall(function()
        local standee = getCharacterStandee(ally.name)
        local tile = getLocationTile(toLoc)
        if standee and tile then
            standee.setPositionSmooth(getCharSlotPosition(tile, ally.name))
        end
    end, "SledStandee")

    -- Arriving anywhere is arriving: the same hooks a Move fires.
    safecall(function() checkWrongnessEntry(allyColor) end, "Wrongness")
    checkDownState(allyColor)
    return true
end

-----------------------------------------------------------------------
-- The Watching Jar (TR_EYE_OF_TERROR).
--
-- Read at Dusk, which is exactly when it is worth something: the scramble
-- window is open, so knowing what tonight holds changes where people stand.
-- The names go to everyone — this is a team trophy, not a peek.
--
-- The reorder is announced rather than scripted: the Threat deck is a real
-- deck on the table and reordering it through the API is the kind of
-- take-then-put dance docs/tts-interface.md warns about. Seeing the two
-- cards is the half that changes a decision; swapping them is one drag.
-----------------------------------------------------------------------
function resolveWatchingJar()
    if not teamHasTrophy("eye") then return false end
    local deck = getThreatDeck()
    if not deck then return false end

    local names = {}
    safecall(function()
        for i, entry in ipairs(deck.getObjects() or {}) do
            if i > 2 then break end
            names[#names + 1] = entry.nickname or "an unnamed card"
        end
    end, "WatchingJar")

    if #names == 0 then
        broadcastEvent("proc", "The Watching Jar clouds over — the Threat deck is empty.")
        return false
    end

    broadcastEvent("gain", "THE WATCHING JAR opens its eye. Tonight's deck begins: " ..
        table.concat(names, ", then ") .. ".")
    if #names > 1 then
        broadcastEvent("proc", "You may return them in either order — swap the top two cards " ..
            "of the Threat deck now if you would rather have " .. names[2] .. " first.")
    end
    return true
end

-----------------------------------------------------------------------
-- Rules-panel lines for the trophies the team is actually holding.
-- collectActiveRules (ui_rules.lua) appends these.
-----------------------------------------------------------------------
function activeTrophyRules()
    local lines = {}
    for key, t in pairs(TROPHY_POWERS) do
        if teamHasTrophy(key) then
            lines[#lines + 1] = "TROPHY — " .. t.trophy .. ": " .. t.blurb
        end
    end
    table.sort(lines)   -- pairs() order is arbitrary; the panel must be stable
    return lines
end
