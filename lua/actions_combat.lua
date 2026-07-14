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
local FIGHT_RADIUS = 7   -- same "at this tile" radius as festering / Pry

-- Phase-boss statlines, mirroring the standee descriptions baked by
-- build_save.py (bosses list) and the balance sim's BOSSES table. The
-- Source reads SOURCE_MAX_HP (combat.lua, loaded earlier) so the batch-4
-- calibration knob stays single-sourced; the Treeguard resolves through
-- TREEGUARD_STATS at call time (treeguard.lua loads after this file).
BOSS_BASE_STATS = {
    ["Boss:Deerclops"]   = { name = "Deerclops",     hp = 6,             attack = 3 },
    ["Boss:EyeOfTerror"] = { name = "Eye of Terror", hp = 8,             attack = 3 },
    ["Boss:TheSource"]   = { name = "The Source",    hp = SOURCE_MAX_HP, attack = 3 },
}

-- Card-text combat riders the statline columns can't express.
COMBAT_SPECIALS = {
    T_ROOMMATE = { sanityCostPerAttack = 1 },   -- "1 Sanity per attack die rolled"
}

function threatStatsForCard(card)
    if card.getTags then
        for _, tag in ipairs(card.getTags()) do
            if THREAT_STATS and THREAT_STATS[tag] then return THREAT_STATS[tag], tag end
        end
    end
    local nick = (card.getNickname and card.getNickname()) or ""
    local s = THREAT_STATS_BY_NAME and THREAT_STATS_BY_NAME[nick]
    if s then
        for id, stats in pairs(THREAT_STATS) do
            if stats == s then return s, id end
        end
    end
    return nil, nil
end

function bossStatsFor(obj)
    for tag, s in pairs(BOSS_BASE_STATS) do
        if obj.hasTag and obj.hasTag(tag) then
            return { name = s.name, hp = s.hp, attack = s.attack }
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

    if not spendAction(color, "Fight") then return end

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
        -- Chip damage from earlier fights carries over (gameState.threatDamage).
        local dmg = (gameState.threatDamage or {})[targetObj.guid] or 0
        threatData.hp = math.max(0, stats.hp - dmg)
        if dmg > 0 then
            broadcastEvent("proc", stats.name .. " is already wounded — " .. threatData.hp .. " HP left.")
        end
        local special = cardId and COMBAT_SPECIALS[cardId]
        if special then
            for k, v in pairs(special) do threatData[k] = v end
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

    local adjacent = false
    for _, n in ipairs(LOCATION_ADJACENCY[char.location] or {}) do
        if n == targetLocation then adjacent = true; break end
    end
    if not adjacent then
        broadcastToColor(targetLocation .. " is not adjacent to " .. (char.location or "?") ..
            ". Flee reaches 1 tile only.", color, BROADCAST_COLORS.damage)
        return
    end

    char.sanity = math.max(0, char.sanity - 1)
    char.location = targetLocation

    broadcastEvent("warn", char.name .. " flees to " .. targetLocation ..
        " (-1 Sanity). The threat remains behind — and festers at Dawn.")

    local standee = getCharacterStandee(char.name)
    local tile = getLocationTile(targetLocation)
    if standee and tile then
        standee.setPositionSmooth(getCharSlotPosition(tile, char.name))
    end

    safecall(function() checkWrongnessEntry(color) end, "Wrongness")
    checkDownState(color)
end

