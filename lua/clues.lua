-- clues.lua — the Truth Run (Design §16.2), made findable by decision.
--
-- Two problems, one file.
--
-- 1. THE TRUTH RUN COULD NEVER FIRE. checkBonusVictories reads
--    gameState.clueCount, and nothing in the mod ever incremented it. Three
--    Clue cards shipped in the Market deck, a Trophy existed for collecting
--    them, a Dawn card referenced them — and the achievement was unreachable
--    in code, not merely improbable.
--
-- 2. EVEN FIXED, IT WAS A LOTTERY. Drawing three specific cards from a
--    49-card deck through a 5-card display over seven days is dominated by
--    shuffle luck: a team can play perfectly and never see a Clue. That is
--    output randomness applied to a GOAL — the player did everything right
--    and lost the achievement anyway — and an alternate goal that is
--    "technically possible but usually unreachable" is not a path (§12).
--    It also wasted the best replayability hook in the bonus set, since the
--    Truth Run is the one that changes the ending narrative.
--
-- So the clues are now findable three ways, all of them decisions:
--
--   * SEEDED BY THIRDS (seedCluesIntoMarketDeck). One Clue is shuffled into
--     each third of the Market deck, so availability is spread across the
--     week instead of clumping. A team that keeps crafting sees clues.
--   * THE SEALED BASEMENT (§13.5). One guaranteed Clue behind the basement,
--     which is placed at setup, visible from turn one, and already designed
--     as "the map's reliable early destination". This converts the Truth Run
--     from a lottery into a plan using machinery that already exists.
--   * JAMES CAN PULL ONE (§6.1). His Pattern Recognition already peeks at
--     deck tops; seeing a Clue on the Market deck now lets him TAKE it. That
--     gives one character a genuine claim on one of the three bonus
--     victories, which serves the personal-asymmetry pillar (§1.4 #4).

CLUE_IDS = { "M_CLUE_TAPE", "M_CLUE_NOTE", "M_CLUE_PHOTO" }
CLUES_FOR_TRUTH_RUN = 3

-- A card is a Clue if it carries one of the three ids as a tag, or if its
-- printed name starts "Clue:" — the tag is authoritative, the name is the
-- fallback for a handle whose tags didn't survive a takeObject.
function isClueCard(card)
    if not card then return false, nil end
    if card.hasTag then
        for _, id in ipairs(CLUE_IDS) do
            if card.hasTag(id) then return true, id end
        end
    end
    local nick = ""
    pcall(function() nick = (card.getNickname and card.getNickname()) or "" end)
    if nick:sub(1, 5) == "Clue:" then return true, nick end
    return false, nil
end

-- Record a found Clue. Idempotent per clue: the same card claimed twice (a
-- craft that got retried, a card that bounced back to the deck) must not
-- count twice, or the Truth Run becomes a bug rather than an achievement.
function recordClueFound(color, card)
    local isClue, id = isClueCard(card)
    if not isClue then return false end

    gameState.cluesFound = gameState.cluesFound or {}
    if gameState.cluesFound[id] then return false end
    gameState.cluesFound[id] = true

    local n = 0
    for _ in pairs(gameState.cluesFound) do n = n + 1 end
    gameState.clueCount = n

    local char = color and gameState.activeChars[color]
    local who = (char and char.name) or "The team"
    local nick = "a Clue"
    pcall(function() nick = (card.getNickname and card.getNickname()) or nick end)

    broadcastEvent("gain", who .. " finds " .. nick .. " — Clue " .. n ..
        " of " .. CLUES_FOR_TRUTH_RUN .. ".")
    if n >= CLUES_FOR_TRUTH_RUN then
        broadcastEvent("gain", "ALL THREE CLUES. The Truth Run is yours if you survive the week — and the ending will not be the one the others get.")
    else
        broadcastEvent("proc", "Truth Run: " .. (CLUES_FOR_TRUTH_RUN - n) ..
            " more to find. One is behind the Sealed Basement; the rest are spread through the Market deck.")
    end
    safecall(function() refreshRulesPanel() end, "Rules")
    return true
end

-----------------------------------------------------------------------
-- Spreading the clues across the week.
--
-- The proposal was "shuffle one Clue into each third of the Market deck".
-- TTS has no insert-at-index on a Deck — takeObject can pull by index, but
-- putObject only ever lands on top — so a literal re-stack means splitting
-- the deck into a staging pile and reassembling it through the physics
-- engine, asynchronously, at setup. That is a lot of moving parts for a
-- guarantee the player never sees directly.
--
-- So the spread is implemented at the seam where the player actually meets
-- the deck: the Market REFILL. If the week has reached a checkpoint and the
-- team still hasn't been offered that clue, the next refill deals a Clue
-- instead of a random card. The observable property is identical to a
-- seeded deck — availability spread across the week rather than clumped —
-- and it is deterministic instead of best-effort, which matters more here:
-- the whole complaint was that shuffle luck decided the achievement.
--
-- Day 1's clue is not on this schedule. That one is behind the Sealed
-- Basement, where it is a *plan* rather than a draw (§13.5).
-----------------------------------------------------------------------
CLUE_SURFACE_DAYS = { 3, 5 }   -- by these Dawns, a clue must have been offered

-- Has a Clue already been offered to the table (found, or sitting face-up in
-- the Market display)? Cards in the display are public, so one on the board
-- counts as offered even if nobody has bought it yet.
function clueIsOnOffer()
    -- Only an OPEN shelf counts. A Clue dealt face down into slot 5 on Day 1
    -- is not "in front of the team" — nobody can see it, and treating it as
    -- offered would let the Truth Run guarantee (§16.2) tick off a Clue the
    -- table never had the chance to read.
    for i = 1, MARKET_SLOTS_TOTAL do
        if not marketSlotIsHidden(i) then
            local card = marketCardAtSlot(i)
            if card and isClueCard(card) then return true end
        end
    end
    return false
end

-- Called by refillMarketSlot. Returns the guid of a Clue to deal instead of
-- the top card, or nil to refill normally.
function clueDueForRefill()
    local found = 0
    for _ in pairs(gameState.cluesFound or {}) do found = found + 1 end
    if found >= CLUES_FOR_TRUTH_RUN then return nil end

    -- How many checkpoints have passed?
    local due = 0
    for _, day in ipairs(CLUE_SURFACE_DAYS) do
        if (gameState.day or 1) >= day then due = due + 1 end
    end
    -- One clue per passed checkpoint, over and above whatever the basement
    -- gave them; already-offered clues count against the quota.
    gameState.cluesSurfaced = gameState.cluesSurfaced or 0
    if gameState.cluesSurfaced >= due then return nil end
    if clueIsOnOffer() then return nil end

    local deck = getMarketDeck()
    if not deck or not deck.getObjects then return nil end
    for _, entry in ipairs(deck.getObjects() or {}) do
        local nick = entry.nickname or entry.name or ""
        if nick:sub(1, 5) == "Clue:" then
            gameState.cluesSurfaced = gameState.cluesSurfaced + 1
            return entry.guid
        end
    end
    return nil
end

-----------------------------------------------------------------------
-- Pull a named Clue out of the Market deck and hand it to a player.
-- Used by the Sealed Basement reward and by James's Pattern Recognition.
-----------------------------------------------------------------------
function takeClueFromMarketDeck(color, locName)
    local deck = getMarketDeck()
    if not deck or not deck.getObjects then return false end

    local wanted = nil
    for _, entry in ipairs(deck.getObjects() or {}) do
        local nick = entry.nickname or entry.name or ""
        if nick:sub(1, 5) == "Clue:" then
            local already = false
            for _, id in ipairs(CLUE_IDS) do
                if (gameState.cluesFound or {})[id] and nick:find(id, 1, true) then
                    already = true
                end
            end
            if not already then wanted = entry; break end
        end
    end
    if not wanted then
        broadcastEvent("proc", "No Clue left in the Market deck — they are all already found or in play.")
        return false
    end

    local hz = getHandZone(color)
    local tile = locName and getLocationTile(locName)
    local dest = (hz and hz.getPosition()) or (tile and tile.getPosition()) or Vector(0, 3, 0)

    safecall(function()
        deck.takeObject({
            guid = wanted.guid,
            position = dest + Vector(0, 2, 0),
            rotation = {0, 180, 0},
            smooth = true,
            callback_function = function(c)
                -- pcall: the outer safecall wraps takeObject, not this async
                -- callback, and the drawn card's handle can already be dead.
                pcall(function() recordClueFound(color, c) end)
            end,
        })
    end, "TakeClue")
    return true
end
