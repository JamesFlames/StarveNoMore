-- actions_combat.lua — combat action verbs: threat/boss statlines
-- (BOSS_BASE_STATS, COMBAT_SPECIALS, threatStatsForCard, bossStatsFor),
-- fightTargetsAt / canFight / doFightTarget, and doFlee. Part of actions.

-----------------------------------------------------------------------
-- FIGHT (1 action) — Design §11.2 / §12
-- Click-to-complete like Move/Craft/Cook: onActFight (ui_actionbar.lua)
-- spawns a FIGHT button on every fightable thing at the tile; the click
-- lands here and resolves through beginCombat (combat.lua) with real
-- statlines — THREAT_STATS for cards, boss standlines for standees.
-----------------------------------------------------------------------
-- Global, not local: "at this tile" has to mean one distance everywhere, and
-- night.lua now needs it too — it lays each new threat card on its own spot and
-- must not put one down outside the radius that makes it fightable.
FIGHT_RADIUS = 7   -- same "at this tile" radius as festering / Pry

-- Phase-boss statlines, mirroring the standee descriptions baked by
-- build_save.py (bosses list) and the balance sim's BOSSES table. The
-- Treeguard resolves through TREEGUARD_STATS at call time (treeguard.lua
-- loads after this file).
--
-- The Source's HP is `hpFromDifficulty`, resolved in bossStatsFor by
-- getSourceMaxHP() at CALL time rather than baked in here at load time:
-- it is a difficulty knob now (§17.2 — Story fights a 6 HP Source), and a
-- load-time capture of SOURCE_MAX_HP would have frozen every mode at
-- Standard's 8.
BOSS_BASE_STATS = {
    ["Boss:Deerclops"]   = { name = "Deerclops",     hp = 6, attack = 3 },
    ["Boss:EyeOfTerror"] = { name = "Eye of Terror", hp = 8, attack = 3 },
    ["Boss:TheSource"]   = { name = "The Source",    hp = 8, attack = 3,
                             hpFromDifficulty = true },
}

-- Card-text combat riders the statline columns can't express live in
-- HARD_THREAT_SPECIALS (lua/threat_hard.lua) — one table for every printed
-- rider, in and out of combat, so a card cannot be half-wired. This used to
-- be a local COMBAT_SPECIALS holding exactly one row (the Roommate) while
-- seventeen other printed specials had no home at all.
--
-- The keys beginCombat/applyCounterAttack read off threatData:
local COMBAT_RIDER_KEYS = { "sanityPerAttackDie", "sanityPerFight", "counterDice" }

-- The Full Moon (softToHard): "all Soft threats become Hard (+2 HP, +1
-- attack)". Applied HERE rather than at the draw, because the statline is
-- what makes a card fightable at all: fightTargetsAt filters out hp 0, so a
-- Soft card left at hp 0 would still be unfightable — the scenario would have
-- turned every atmospheric card into an unkillable Doom tax instead of a
-- monster. THREAT_STATS rows are shared table references, so the promotion
-- returns a copy and never edits the generated data.
local function _fullMoonPromote(stats, id)
    if not stats then return stats end
    if not (gameState.scenarioFlags or {}).softToHard then return stats end
    if (THREAT_TYPE_BY_ID or {})[id or ""] ~= "Soft" then return stats end
    return { name = stats.name, hp = (stats.hp or 0) + 2, attack = (stats.attack or 0) + 1 }
end

function threatStatsForCard(card)
    if card.getTags then
        for _, tag in ipairs(card.getTags()) do
            if THREAT_STATS and THREAT_STATS[tag] then
                return _fullMoonPromote(THREAT_STATS[tag], tag), tag
            end
        end
    end
    local nick = (card.getNickname and card.getNickname()) or ""
    local s = THREAT_STATS_BY_NAME and THREAT_STATS_BY_NAME[nick]
    if s then
        for id, stats in pairs(THREAT_STATS) do
            if stats == s then return _fullMoonPromote(s, id), id end
        end
    end
    return nil, nil
end

function bossStatsFor(obj)
    for tag, s in pairs(BOSS_BASE_STATS) do
        if obj.hasTag and obj.hasTag(tag) then
            local hp = s.hp
            if s.hpFromDifficulty then hp = getSourceMaxHP() end
            return { name = s.name, hp = hp, attack = s.attack }
        end
    end
    if obj.hasTag and obj.hasTag("Boss:Treeguard") and TREEGUARD_STATS then
        return { name = TREEGUARD_STATS.name, hp = TREEGUARD_STATS.hp, attack = TREEGUARD_STATS.attack }
    end
    return nil   -- Charlie's standee (and anything unknown) can't be fought
end

-- Everything fightable at a tile: { {obj, stats, boss}, ... }
function fightTargetsAt(locName)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    local function near(obj)
        local p = obj.getPosition()
        local dx, dz = p.x - tp.x, p.z - tp.z
        return (dx * dx + dz * dz) <= (FIGHT_RADIUS * FIGHT_RADIUS)
    end
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        if obj.type == "Card" and near(obj) then
            local stats = threatStatsForCard(obj)
            if stats and stats.hp > 0 then
                table.insert(out, { obj = obj, stats = stats, boss = false })
            end
        end
    end
    for _, obj in ipairs(findAllByTag("Boss")) do
        if near(obj) then
            local stats = bossStatsFor(obj)
            if stats then table.insert(out, { obj = obj, stats = stats, boss = true }) end
        end
    end
    return out
end

-- Precondition check; the reason doubles as the why-disabled tooltip.
function canFight(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if (char.actionsLeft or 0) <= 0 then return false, "No actions left." end
    if char.hunger < 3 then
        return false, "Too hungry to fight (Hunger < 3). Flee is always legal: 1 tile, 1 Sanity."
    end
    if #fightTargetsAt(char.location) == 0 then
        return false, "Nothing to fight at " .. (char.location or "?") .. "."
    end
    return true, nil
end

-- The FIGHT / FIGHT TOGETHER button click lands here (ui_actionbar.lua).
-- together = true pulls in every standing, fed (Hunger >= 3) ally at the
-- tile: summed dice, shared counter-attacks (Design §12.2).
function doFightTarget(color, targetObj, together)
    local char = gameState.activeChars[color]
    if not char or char.down then return end
    if char.hunger < 3 then
        broadcastEvent("damage", char.name .. " is too hungry to fight (Hunger < 3)! You can still Flee: move 1 tile away, paying 1 Sanity.")
        return
    end

    local isBoss = targetObj.hasTag and targetObj.hasTag("Boss")
    local stats, cardId
    if isBoss then
        stats = bossStatsFor(targetObj)
    else
        stats, cardId = threatStatsForCard(targetObj)
    end
    if not stats or (stats.hp or 0) <= 0 then
        broadcastToColor("That can't be fought.", color, BROADCAST_COLORS.damage)
        return
    end

    -- Printed rules about WHERE it can be fought (the Thing in the Attic
    -- will not come out to a court). Refused before the action is spent —
    -- a rule that costs you a turn to discover is a worse rule.
    local mayFight, whyNot = hardThreatBlocksFight(cardId, color)
    if not mayFight then
        broadcastToColor(whyNot, color, BROADCAST_COLORS.damage)
        return
    end

    if not spendAction(color, "Fight") then return end

    -- The Doppelganger's hesitation roll: it happens AFTER the action is
    -- committed, because hesitating is what the action bought.
    if not hardThreatHesitation(cardId, color) then
        refreshPhaseBanner()
        return
    end

    local participants = { color }
    if together then
        for c2, ch2 in pairs(gameState.activeChars) do
            if c2 ~= color and not ch2.down and ch2.location == char.location then
                if ch2.hunger >= 3 then
                    table.insert(participants, c2)
                else
                    broadcastEvent("warn", ch2.name .. " is too hungry to join the fight (Hunger < 3).")
                end
            end
        end
    end

    local threatData = { name = stats.name, hp = stats.hp, attack = stats.attack, maxHp = stats.hp }
    if not isBoss then
        threatData.cardGuid = targetObj.guid
        threatData.cardId = cardId          -- applyThreatDefeat's on-death riders
        -- Chip damage from earlier fights carries over (gameState.threatDamage).
        local dmg = (gameState.threatDamage or {})[targetObj.guid] or 0
        threatData.hp = math.max(0, stats.hp - dmg)
        if dmg > 0 then
            broadcastEvent("proc", stats.name .. " is already wounded — " .. threatData.hp .. " HP left.")
        end
        local special = cardId and HARD_THREAT_SPECIALS[cardId]
        if special then
            for _, k in ipairs(COMBAT_RIDER_KEYS) do
                if special[k] ~= nil then threatData[k] = special[k] end
            end
        end
    end

    if #participants > 1 then
        local names = {}
        for _, c in ipairs(participants) do names[#names + 1] = gameState.activeChars[c].name end
        broadcastEvent("proc", table.concat(names, " & ") .. " fight " .. stats.name .. " together!")
    end

    return beginCombat(participants, threatData)
end

-----------------------------------------------------------------------
-- FLEE (Design §12.4) — the Night escape valve. When a threat is at your
-- tile, you may flee instead of fighting: move 1 tile away, paying
-- 1 Sanity (running in the dark is terrifying, not tiring). Always
-- legal — even starving (Hunger < 3 blocks Fight, never Flee). The
-- threat stays where it was, and festers at Dawn.
-----------------------------------------------------------------------
function doFlee(color, targetLocation)
    local char = gameState.activeChars[color]
    if not char then return end
    if char.down then
        broadcastToColor("You are Down and cannot flee.", color, BROADCAST_COLORS.damage)
        return
    end

    -- adjacentLocations(), not raw LOCATION_ADJACENCY: Flee used to be the one
    -- movement verb that didn't know about SC_SHORTCUT's extra road, so on a
    -- variant that doesn't print it you could walk the shortcut and scramble
    -- down it but not run down it — in the one direction the rule is for.
    if not isAdjacent(char.location, targetLocation) then
        broadcastToColor(targetLocation .. " is not adjacent to " .. (char.location or "?") ..
            ". Flee reaches 1 tile only.", color, BROADCAST_COLORS.damage)
        return
    end

    -- Last Nerve (§10.1): with any stat below 3, running is free. The escape
    -- hatch stops being priced in the currency most likely to be empty.
    local nerve = hasLastNerve(color)
    local cost = nerve and 0 or 1
    char.sanity = math.max(0, char.sanity - cost)
    char.location = targetLocation

    if nerve then
        broadcastEvent("warn", char.name .. " runs on their last nerve to " .. targetLocation ..
            " — no Sanity cost (Last Nerve). The threat remains behind, and festers at Dawn.")
    else
        broadcastEvent("warn", char.name .. " flees to " .. targetLocation ..
            " (-1 Sanity). The threat remains behind — and festers at Dawn.")
    end

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    safecall(function() checkWrongnessEntry(color) end, "Wrongness")
    checkDownState(color)
end

