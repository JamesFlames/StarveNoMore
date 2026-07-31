-- threat_hard.lua — the printed riders on Hard threat cards.
--
-- The third and last of the three threat kinds to get its card text read by
-- anything. Eighteen Hard cards carry a `special` line, and exactly ONE of
-- them was wired: `COMBAT_SPECIALS` in actions_combat.lua held a single row
-- (Your Roommate's Sanity cost) and nothing else. Seventeen printed rules —
-- Spider Thing's two counter dice, the Scarecrow taxing every Gather, the
-- Shadow Stalker's extra Sanity at Tick, the Black Dog that hunts in pairs —
-- were text on a card that no code had ever read.
--
-- One of them was not merely inert but actively harmful, and for the same
-- reason Soft threats were (threat_effects.lua) and the hp-less Persistents
-- were (threat_persistent.lua): **The Grue has hp 0**. Its card says "Cannot
-- be fought … Discard after", and `fightTargetsAt` duly filters it out — so
-- nothing could remove it, nothing discarded it, and `countFesteringThreats`
-- charged +1 Doom for it at every Dawn for the rest of the week while its
-- printed attack never landed. Three separate cards fell into that same hole.
-- This one closes it for the last of them.
--
-- HARD_THREAT_SPECIALS[id] — one declarative row per Hard card that prints a
-- special, in three flavours (a row may mix the first and the third):
--
--   scripted keys   the rule the hooks below enforce
--   manual = "..."  a step the table applies, announced so it is not missed
--   inert  = "..."  the rule is a no-op in this mod, with the reason why
--
-- tests/test_hard_threats.py fails on a Hard card with a printed special and
-- no row, on a row naming a non-Hard card, and on a row that is none of the
-- three (which would be a card silently doing nothing again).

-- Where a spent one-shot Hard card goes — the same discard as a resolved Soft
-- threat (threat_effects.lua). Only The Grue uses it: everything else here is
-- a real fight, and a real fight ends at the trophy pile.
local SPENT_DISCARD_POS = { -13.5, 1.5, 10.8 }

HARD_THREAT_SPECIALS = {
    -----------------------------------------------------------------
    -- Riders inside a fight (read by doFightTarget → beginCombat).
    -----------------------------------------------------------------
    T_ROOMMATE = {
        sanityPerAttackDie = 1,
        blurb = "Every attack die rolled against it costs 1 Sanity.",
    },
    T_CHILD_SHADOW = {
        -- "1 Sanity per attack", not per die: a flat toll on the decision to
        -- swing at it, which is a different (and cheaper) shape than the
        -- Roommate's per-die bill. Two keys, because one card charges for
        -- how hard you swing and the other for swinging at all.
        sanityPerFight = 1,
        blurb = "Attacking it costs 1 Sanity, however many dice you roll.",
    },
    T_SPIDER_THING = {
        counterDice = 2,
        blurb = "Multi-attack: it counters with 2 dice, not 1.",
    },
    T_DOPPELGANGER = {
        hesitationRoll = true,
        blurb = "It wears an ally's face: roll Sanity d8 before attacking — " ..
                "5+ and you can act, 1-4 and you hesitate for 1 Sanity.",
    },
    T_THING_IN_ATTIC = {
        houseTilesOnly = true,
        manual = "It retreats to the attic between attacks — spend 1 action to find it before each Fight.",
        blurb = "It can only be fought at a house tile.",
    },

    -----------------------------------------------------------------
    -- Riders that fire the moment the card is drawn.
    -----------------------------------------------------------------
    T_HOLLOW_SPECTATOR = {
        onDrawSanityHere = 1,
        blurb = "On entry, everyone at this tile loses 1 Sanity.",
    },
    T_WALL_CRAWLER = {
        onDrawDamageHere = 1,
        blurb = "Fast: it draws blood on arrival, before anyone can react, then fights normally.",
    },
    T_THE_GRUE = {
        -- The only Hard card that is not a fight at all. hp 0 means it can
        -- never be a Fight target, so without this it was a permanent Doom
        -- tax with a printed attack that never happened.
        charlieAttackHere = true, discardAfter = true,
        blurb = "It cannot be fought. It takes its bite and it goes.",
    },

    -----------------------------------------------------------------
    -- Riders that stand while the card does (per-tile, swept at Tick/Night).
    -----------------------------------------------------------------
    T_SHADOW_STALKER = {
        tickSanityAtTile = 1,
        blurb = "While it stands, everyone at its tile loses 1 extra Sanity at Tick.",
    },
    T_SCARECROW = {
        gatherSanityAtTile = 1,
        blurb = "While it stands, a Gather at its tile costs 1 Sanity.",
    },
    T_GLASS_CHILD = {
        nightSanityAtTile = 2,
        manual = "Weapons are no use on it. Calm it instead: spend 1 Comfort item, or 2 Sanity, to remove it.",
        blurb = "Until it is calmed, everyone at its tile loses 2 Sanity every Night.",
    },

    -----------------------------------------------------------------
    -- Riders that fire on its death.
    -----------------------------------------------------------------
    T_BLACK_DOG = {
        onDefeatDrawThreat = 1,
        blurb = "They hunt in pairs — killing it draws another Threat here.",
    },

    -----------------------------------------------------------------
    -- Table steps: the script has no basis to make these calls.
    -----------------------------------------------------------------
    T_MIMIC = {
        manual = "It was disguised as a resource token: it attacks whoever gathered at this tile most recently. Agree who that was.",
    },
    T_SWARM = {
        manual = "At 1 HP it splits: replace it with two 1-HP Crawling Hands at adjacent tiles (take them from the Threat deck).",
    },

    -----------------------------------------------------------------
    -- Declared inert: the rule has nothing to act on in this mod. Written
    -- down rather than left blank, so "no code" reads as a decision instead
    -- of an oversight — the distinction that made seventeen of these
    -- invisible in the first place.
    -----------------------------------------------------------------
    T_THE_NEIGHBOR = {
        inert = "'Cannot be attacked at range' — ranged combat is not a mechanic here " ..
                "(the Slingshot's adjacent-tile attack is declared unwired for the same reason, " ..
                "tests/test_market_wiring.py). Fight is same-tile only, so nothing can violate it.",
    },
    T_TERROR_BEAK = {
        inert = "'Spawned from the Eye of Terror split. Removed if the Eye is restored' — " ..
                "the split spawns it (dawn_effects_phase3), and a defeated Eye is defeated, " ..
                "not restored. There is no state in which the removal clause can fire.",
    },
    T_THE_DOOR = {
        inert = "Its Pry reward is delivered by doPry through SEALED_REWARDS (generated from " ..
                "the pry_reward column), so the card is wired — just not from this table.",
    },
    T_CRAWLING_HAND = {
        inert = "'Attacks the Down player first' — damage to a Down character does nothing " ..
                "in this engine (they are already at 0 and checkDownState early-returns), so " ..
                "spending counter hits on them would make the Hand strictly WEAKER than " ..
                "leaving the rule out. Implementing it literally would be a nerf wearing a " ..
                "bug fix's clothes.",
    },
}

-- The subset that hangs around a tile, for the sweeps below.
local function _standingAt(locName)
    return threatCardsAt(locName, HARD_THREAT_SPECIALS)
end

-- Sum one numeric key over the Hard threats at a tile. (total, names)
function hardSpecialTotal(locName, key)
    local total, names = 0, {}
    for _, t in ipairs(_standingAt(locName)) do
        local v = t.rule[key]
        if type(v) == "number" and v ~= 0 then
            total = total + v
            names[#names + 1] = t.name
        end
    end
    return total, names
end

-----------------------------------------------------------------------
-- On draw (drawThreatsAt, night.lua). Returns true if the card was spent
-- and discarded, so the caller knows not to also say "must be fought".
-----------------------------------------------------------------------
function resolveHardThreatDraw(id, location, name, card)
    local rule = HARD_THREAT_SPECIALS[id]
    if not rule then return false end
    local label = name or (THREAT_STATS[id] and THREAT_STATS[id].name) or "Something"

    if rule.blurb then broadcastEvent("proc", label .. ": " .. rule.blurb) end
    if rule.manual then
        broadcastEvent("warn", label .. " — TABLE STEP: " .. rule.manual)
    end

    if rule.onDrawSanityHere then
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == location then
                ch.sanity = math.max(0, ch.sanity - rule.onDrawSanityHere)
                broadcastEvent("damage", ch.name .. " loses " .. rule.onDrawSanityHere ..
                    " Sanity — " .. label .. " is simply there, watching.")
                checkDownState(color)
            end
        end
    end

    if rule.onDrawDamageHere then
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == location then
                ch.health = math.max(0, ch.health - rule.onDrawDamageHere)
                broadcastEvent("damage", ch.name .. " takes " .. rule.onDrawDamageHere ..
                    " damage before anyone can react — " .. label .. " was already moving.")
                checkDownState(color)
            end
        end
    end

    -- The Grue: its own numbers (1d8 Sanity, 1d6 Health), not Charlie's
    -- escalating streak — the card prints them, and it is a one-off visit
    -- rather than her nightly interest.
    if rule.charlieAttackHere then
        broadcastEvent("damage", "The dark at " .. (location or "this tile") ..
            " has teeth. " .. label .. " takes its bite.")
        for color, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == location then
                if ch.name == "Coco" then
                    broadcastEvent("proc", "Coco sees in the dark — the Grue passes her by (Night Vision).")
                else
                    local sLoss, hLoss = gameRoll(1, 8), gameRoll(1, 6)
                    ch.sanity = math.max(0, ch.sanity - sLoss)
                    ch.health = math.max(0, ch.health - hLoss)
                    broadcastEvent("damage", ch.name .. " is caught in the dark: -" .. sLoss ..
                        " Sanity, -" .. hLoss .. " Health. (Now S:" .. ch.sanity ..
                        " H:" .. ch.health .. ")")
                    checkDownState(color)
                end
            end
        end
    end

    if rule.discardAfter then
        if card then
            safecall(function()
                card.setPositionSmooth(Vector(SPENT_DISCARD_POS[1], SPENT_DISCARD_POS[2],
                                              SPENT_DISCARD_POS[3]), false, true)
                card.setRotationSmooth({0, 180, 0}, false, true)
            end, "HardDiscard")
        end
        broadcastEvent("proc", label .. " is gone as suddenly as it came — its card goes to the discard pile (NW corner).")
        return true
    end
    return false
end

-----------------------------------------------------------------------
-- Before the dice (doFightTarget, actions_combat.lua).
-- Returns (ok, reason): false stops the fight before an action is spent.
-----------------------------------------------------------------------
function hardThreatBlocksFight(cardId, color)
    local rule = cardId and HARD_THREAT_SPECIALS[cardId]
    if not rule then return true, nil end
    local char = gameState.activeChars[color]
    if rule.houseTilesOnly and char and isSportCourt(char.location or "") then
        return false, (THREAT_STATS[cardId] and THREAT_STATS[cardId].name or "It") ..
            " can only be fought indoors — it will not come out here."
    end
    return true, nil
end

-- The Doppelganger's hesitation (rolled once for the group, by the character
-- whose turn it is: they are the one who has to look at it).
-- Returns true if the attack goes ahead.
function hardThreatHesitation(cardId, color)
    local rule = cardId and HARD_THREAT_SPECIALS[cardId]
    if not (rule and rule.hesitationRoll) then return true end
    local char = gameState.activeChars[color]
    if not char then return true end
    -- Dice in the open can't be taken back — the same rule beginCombat
    -- applies. Without this, a hesitation is rolled *before* beginCombat
    -- clears the snapshot, so Undo would hand back the action and let the
    -- player reroll the nerve check until it passes.
    gameState.undoSnapshot = nil
    local roll = gameRoll(1, 8)
    if roll >= 5 then
        broadcastEvent("proc", char.name .. " rolls " .. roll ..
            " — they know it isn't really them. The attack lands as normal.")
        return true
    end
    char.sanity = math.max(0, char.sanity - 1)
    broadcastEvent("damage", char.name .. " rolls " .. roll ..
        " and hesitates — it is wearing a face they know. -1 Sanity, and the attack is not made.")
    checkDownState(color)
    return false
end

-----------------------------------------------------------------------
-- On its death (applyThreatDefeat, combat_resolve.lua).
-----------------------------------------------------------------------
function resolveHardThreatDefeat(cardId, location)
    local rule = cardId and HARD_THREAT_SPECIALS[cardId]
    if not (rule and rule.onDefeatDrawThreat) then return end
    broadcastEvent("warn", (THREAT_STATS[cardId] and THREAT_STATS[cardId].name or "It") ..
        " hunted in a pair — something answers from the dark. " ..
        rule.onDefeatDrawThreat .. " more Threat at " .. (location or "this tile") .. ".")
    safecall(function() drawThreatsAt(location, rule.onDefeatDrawThreat) end, "PairDraw")
end

-----------------------------------------------------------------------
-- Standing sweeps.
-----------------------------------------------------------------------

-- Gather (doGather, actions.lua): the Scarecrow's toll. (cost, name)
function hardThreatGatherSanity(locName)
    local total, names = hardSpecialTotal(locName, "gatherSanityAtTile")
    return total, names[1]
end

-- Tick (resolveTick, tick_victory.lua): extra Sanity per standing card at
-- that character's tile. Returns the per-character extra for `locName`.
function hardThreatTickSanity(locName, byTile)
    local list = byTile and byTile[locName] or _standingAt(locName)
    local extra = 0
    for _, t in ipairs(list) do extra = extra + (t.rule.tickSanityAtTile or 0) end
    return extra
end

-- Night (ResolveNight, night.lua): the Glass Child's nightly toll, swept
-- across the whole board in one pass.
function resolveHardThreatNight()
    for locName, list in pairs(threatCardsByTile(HARD_THREAT_SPECIALS)) do
        local loss, names = 0, {}
        for _, t in ipairs(list) do
            if t.rule.nightSanityAtTile then
                loss = loss + t.rule.nightSanityAtTile
                names[#names + 1] = t.name
            end
        end
        if loss > 0 then
            for color, ch in pairs(gameState.activeChars) do
                if not ch.down and ch.location == locName then
                    ch.sanity = math.max(0, ch.sanity - loss)
                    broadcastEvent("damage", ch.name .. " loses " .. loss .. " Sanity at " ..
                        locName .. " — " .. table.concat(names, ", ") .. " is still crying.")
                    checkDownState(color)
                end
            end
        end
    end
end
