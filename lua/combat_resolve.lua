-- combat_resolve.lua — combat resolution flow: dice formatting, getAttackDice,
-- threat-defeat application, counter-attacks, James reroll, beginCombat /
-- resolveCombat / pressAttack / finishCombat, and resolveCharlieAttack.
-- Part of combat (see combat.lua for dice roll + boss/Source lifecycle + rewards).

-----------------------------------------------------------------------
-- Format dice result for broadcast
-----------------------------------------------------------------------
local function formatRolls(rolls)
    local parts = {}
    for _, r in ipairs(rolls) do
        if r >= 5 then
            table.insert(parts, "[" .. r .. " HIT]")
        elseif r == 1 then
            table.insert(parts, "[" .. r .. " FUMBLE]")
        else
            table.insert(parts, "[" .. r .. "]")
        end
    end
    return table.concat(parts, " ")
end

-----------------------------------------------------------------------
-- Count a character's total attack dice
-----------------------------------------------------------------------
function getAttackDice(color)
    local char = gameState.activeChars[color]
    if not char then return 1 end

    local dice = 1  -- base attack

    -- Rayman gets +1 base attack; Court Master (§6.3) adds another +1
    -- when the fight is on his home court.
    if char.name == "Rayman" then
        dice = dice + 1
        if char.location == "BasketballCourt" then
            dice = dice + 1
            broadcastEvent("proc", "Court Master: Rayman fights on his own court — +1 attack die.")
        end
    end

    -- Nothing Left to Lose (Design §15.2): at Doom 25 the survivors stop
    -- being afraid — +1 attack die for everyone, all combat.
    if gameState.ongoingDawnEffects.doom25 then dice = dice + 1 end

    -- Weapons: cards print "+N Attack die"; WEAPON_DICE (auto-generated
    -- from the card CSVs by generate_market_data.py) lets the script roll
    -- them. Only the best single carried weapon counts — no stacking.
    local bonus, weaponName = 0, nil
    safecall(function()
        for _, obj in ipairs(getPlayerCarriedObjects(color, char.name)) do
            for id, n in pairs(WEAPON_DICE or {}) do
                if safeHasTag(obj, id) and n > bonus then
                    bonus = n
                    weaponName = safeNickname(obj)
                    if weaponName == "" then weaponName = id end
                end
            end
        end
    end, "WeaponDice")
    if bonus > 0 then
        dice = dice + bonus
        broadcastEvent("proc", char.name .. "'s " .. (weaponName or "weapon") ..
            " adds +" .. bonus .. " attack " .. (bonus == 1 and "die" or "dice") .. ".")
    end

    return dice
end

-----------------------------------------------------------------------
-- Combat (Design §12 + §12.5 Press the Attack)
--
-- Combat is a small state machine so the Press the Attack window can open
-- between the attack and the enemy's counter:
--   beginCombat  → roll attack, apply hits/fumble. Defeated? reward, done.
--                  Landed a hit and it survives? open the press window
--                  (DON'T counter yet). Whiffed? counter immediately.
--   pressAttack  → pay 1 Sanity, roll 1 bonus die (never fumbles). 5-6 =
--                  another point of damage and the window stays open; 1-4 =
--                  the streak ends and the enemy strikes back.
--   finishCombat → the player stops pressing: enemy counters, window closes.
--
-- gameState.combatContext holds the live fight. It is transient (combat
-- never spans a save); it is cleared on any phase change and defensively
-- re-closed if a new combat begins while one is dangling.
-----------------------------------------------------------------------

local function _healthiestColor(colors)
    local best, bestHP
    for _, color in ipairs(colors) do
        local c = gameState.activeChars[color]
        if c and (not bestHP or c.health > bestHP) then best, bestHP = color, c.health end
    end
    return best
end

-- Shared defeat tail: reward, boss hooks, chronicle, audio, Treeguard.
function applyThreatDefeat(threatName, colors)
    broadcastEvent("gain", threatName .. " is DEFEATED!")
    for _, color in ipairs(colors) do
        local c = gameState.activeChars[color]
        if c then
            c.sanity = math.min(c.maxSanity, c.sanity + 1)   -- Design §12 victory Sanity
            broadcastEvent("gain", c.name .. " gains +1 Sanity from victory.")
            checkDownState(color)
        end
    end
    -- A defeated threat CARD discards itself beside the Threat deck (the
    -- fight flow put its guid on the combat context); its chip damage is
    -- forgotten with it. Boss standees are pooled by markBossDefeated.
    local ctx = gameState.combatContext
    local guid = ctx and ctx.threat and ctx.threat.cardGuid
    if guid then
        if gameState.threatDamage then gameState.threatDamage[guid] = nil end
        safecall(function()
            local card = getObjectFromGUID(guid)
            if card then
                -- Fixed spot NW of the board (the Threat deck itself lives
                -- in the under-table library) — defeated threats pile up
                -- face-up where everyone can see the kill count.
                card.setPositionSmooth(Vector(-10.5, 1.5, 10.8), false, true)
                card.setRotationSmooth({0, 180, 0}, false, true)
                broadcastEvent("proc", threatName .. " discards itself to the trophy pile (NW corner).")
            end
        end, "ThreatDiscard")
    end
    safecall(function() markBossDefeated(threatName) end, "BossFlags")
    safecall(function() recordKillInChronicle(threatName, colors) end, "Chronicle")
    local bossKey = Audio and Audio.threatNameToBossKey and Audio.threatNameToBossKey(threatName)
    if bossKey then safecall(function() Audio.stopBossLoop(bossKey) end, "Audio") end
    if bossKey == "treeguard" then safecall(function() treeguardDefeated() end, "Treeguard") end
end

-- Enemy counter-attack against the live combat, then leave HP as-is.
function applyCounterAttack()
    local ctx = gameState.combatContext
    if not ctx or ctx.threatHP <= 0 then return end
    local threatAtk = ctx.threat.attack or 0
    if threatAtk <= 0 then return end
    local tName = ctx.threat.name or "Threat"
    broadcastEvent("proc", tName .. " counter-attacks with " .. threatAtk .. " dice...")
    local defResult = rollAttackDice(threatAtk)
    broadcastEvent("proc", "Enemy: " .. formatRolls(defResult.rolls))
    if defResult.hits > 0 then
        -- Backboard Block (§6.3): while Rayman Defends, every counter hit
        -- lands on him instead of whoever it targeted — as long as he is
        -- still standing in (or adjacent to) the fight.
        local defenderColor = nil
        if gameState.raymanDefending then
            for color, c in pairs(gameState.activeChars) do
                if c.name == "Rayman" and not c.down then defenderColor = color break end
            end
        end
        for i = 1, defResult.hits do
            local color = ctx.colors[((i - 1) % #ctx.colors) + 1]
            if defenderColor then
                local ray = gameState.activeChars[defenderColor]
                if ray and not ray.down then
                    color = defenderColor
                    broadcastEvent("proc", "Backboard Block: Rayman takes the hit instead.")
                else
                    defenderColor = nil  -- Rayman fell mid-counter; the rest land normally
                end
            end
            local c = gameState.activeChars[color]
            if c then
                c.health = math.max(0, c.health - 1)
                broadcastEvent("damage", c.name .. " takes 1 counter-attack damage. Health: " .. c.health)
                if color == defenderColor then checkDownState(color) end
            end
        end
        for _, color in ipairs(ctx.colors) do checkDownState(color) end
    else
        broadcastEvent("proc", tName .. " misses!")
    end
end

-----------------------------------------------------------------------
-- Gaming Reflexes (§6.1): once per turn, James may reroll one of his own
-- dice. Auto-applied on his turn to the lowest non-hit die — a reroll can
-- only help (a stray 1 rerolled can clear the fumble; a miss can become a
-- hit; the worst case is the same miss again).
-----------------------------------------------------------------------
function maybeJamesReroll(participants, atkResult)
    if gameState.jamesRerollUsed then return end
    local active = gameState.activeColor
    local activeChar = active and gameState.activeChars[active]
    if not (activeChar and activeChar.name == "James" and not activeChar.down) then return end
    local isParticipant = false
    for _, color in ipairs(participants) do
        if color == active then isParticipant = true break end
    end
    if not isParticipant then return end
    local worstIdx = nil
    for i, r in ipairs(atkResult.rolls) do
        if r < 5 and (not worstIdx or r < atkResult.rolls[worstIdx]) then worstIdx = i end
    end
    if not worstIdx then return end   -- every die hit; nothing worth fixing
    gameState.jamesRerollUsed = true
    local old = atkResult.rolls[worstIdx]
    local new = gameRoll(1, 6)
    atkResult.rolls[worstIdx] = new
    atkResult.hits, atkResult.fumbles = 0, 0
    for _, r in ipairs(atkResult.rolls) do
        if r >= 5 then atkResult.hits = atkResult.hits + 1
        elseif r == 1 then atkResult.fumbles = atkResult.fumbles + 1 end
    end
    broadcastEvent(new >= 5 and "gain" or "proc",
        "Gaming Reflexes: James rerolls a " .. old .. " → " .. new ..
        (new >= 5 and " — a HIT!" or ". No better.") .. " (once per turn)")
end

-- Unified combat entry. colors = list of participating seat colors.
function beginCombat(colors, threatData)
    finishCombat()   -- close any dangling fight first (safety)

    local participants = {}
    for _, color in ipairs(colors) do
        local c = gameState.activeChars[color]
        if c and not c.down then
            table.insert(participants, color)
            -- 3p Big Appetite relief (§20.1) reads whether Rayman fought today.
            if c.name == "Rayman" then gameState.raymanFoughtToday = true end
        end
    end
    if #participants == 0 then return { defeated = false } end

    local threatName = threatData.name or "Unknown Threat"
    local threatHP = threatData.hp or 0

    -- Persistent boss HP (§12.6): the engine, not the players' memory,
    -- knows a boss's real HP — mid-fight, across actions, across saves.
    local bossKey = bossKeyForName(threatName)
    if bossKey == "source" and gameState.bossHP and gameState.bossHP.source then
        threatHP = gameState.bossHP.source
        broadcastEvent("proc", "The Source stands at " .. threatHP .. " HP (tracked).")
    elseif bossKey == "treeguard" and gameState.treeguard and gameState.treeguard.hp then
        threatHP = gameState.treeguard.hp
    elseif bossKey and gameState.bossHP and gameState.bossHP[bossKey] then
        threatHP = gameState.bossHP[bossKey]
        broadcastEvent("proc", threatName .. " stands at " .. threatHP .. " HP (tracked).")
    end

    -- Dice were rolled in the open: a fight can't be taken back.
    gameState.undoSnapshot = nil

    local totalDice = 0
    for _, color in ipairs(participants) do totalDice = totalDice + getAttackDice(color) end

    broadcastEvent("proc", "--- COMBAT vs " .. threatName .. " ---")
    local atkResult = rollAttackDice(totalDice)
    broadcastEvent("proc", (#participants > 1 and "Group rolls " or "Attack: ")
        .. (#participants > 1 and (totalDice .. " dice: ") or "") .. formatRolls(atkResult.rolls))

    -- Gaming Reflexes (§6.1): on James's turn, his once-per-turn reroll
    -- auto-fixes the lowest non-hit die.
    safecall(function() maybeJamesReroll(participants, atkResult) end, "Reroll")

    threatHP = threatHP - atkResult.hits
    if atkResult.hits > 0 then
        broadcastEvent("gain", atkResult.hits .. " hit(s)! " .. threatName .. " HP: " .. math.max(0, threatHP))
        syncThreatHP(threatData, threatHP)
    end

    -- Fumble: only on a complete whiff (no hits at all), max 1, to the healthiest.
    if atkResult.fumbles > 0 and atkResult.hits == 0 then
        local tank = _healthiestColor(participants)
        local c = gameState.activeChars[tank]
        c.health = math.max(0, c.health - 1)
        broadcastEvent("damage", c.name .. " whiffs completely and fumbles! Takes 1 self-damage. Health: " .. c.health)
        checkDownState(tank)
    elseif atkResult.fumbles > 0 then
        broadcastEvent("proc", "A 1 was rolled, but a hit landed — no fumble damage.")
    end

    -- Sanity-on-attack special (single attacker only, e.g. Your Roommate).
    if threatData.sanityCostPerAttack and #participants == 1 then
        local c = gameState.activeChars[participants[1]]
        local sLoss = threatData.sanityCostPerAttack * totalDice
        c.sanity = math.max(0, c.sanity - sLoss)
        broadcastEvent("damage", c.name .. " loses " .. sLoss .. " Sanity from attacking " .. threatName .. ".")
        checkDownState(participants[1])
    end

    gameState.combatContext = { colors = participants, threat = threatData,
                                threatHP = threatHP, hits = atkResult.hits, open = false }

    if threatHP <= 0 then
        applyThreatDefeat(threatName, participants)
        gameState.combatContext = nil
        return { defeated = true, remainingHP = 0 }
    end

    if atkResult.hits > 0 then
        -- You landed a hit: PRESS THE ATTACK is available. The enemy does not
        -- strike back until you stop pressing (miss or click Finish).
        gameState.combatContext.open = true
        broadcastEvent("proc", "Landed a hit — PRESS THE ATTACK (−1 Sanity for one more die) or FINISH to let it strike back.")
        safecall(function() refreshCombatPanel() end, "CombatPanel")
        return { defeated = false, remainingHP = threatHP, pressWindow = true }
    end

    -- Complete whiff: no press, the enemy counters now.
    applyCounterAttack()
    gameState.combatContext = nil
    return { defeated = false, remainingHP = threatHP }
end

-- Backwards-compatible entry points.
function resolveCombat(color, threatData)
    return beginCombat({ color }, threatData)
end

function resolveGroupCombat(colors, threatData)
    local list = {}
    for _, c in ipairs(colors) do table.insert(list, c) end
    return beginCombat(list, threatData)
end

-----------------------------------------------------------------------
-- Press the Attack (Design §12.5). Pay 1 Sanity, roll one bonus die.
-- 5-6 = one more damage, window stays open. 1-4 = the streak ends and the
-- enemy counters. Press dice never fumble. Pressing may zero your Sanity
-- and put you Down — that risky press requires an explicit confirm.
-----------------------------------------------------------------------
function pressAttack(color, confirmed)
    local ctx = gameState.combatContext
    if not ctx or not ctx.open then
        broadcastToColor("No attack to press right now.", color, BROADCAST_COLORS.damage)
        return false
    end
    local isParticipant = false
    for _, c in ipairs(ctx.colors) do if c == color then isParticipant = true break end end
    if not isParticipant then
        broadcastToColor("Only a fighter in this combat may press.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    if not char or char.down then return false end
    if char.sanity < 1 then
        broadcastToColor("No Sanity left to press.", color, BROADCAST_COLORS.damage)
        return false
    end
    -- A press that would zero Sanity drops the presser to Lost — confirm first.
    if char.sanity == 1 and not confirmed then
        broadcastToColor("Press again? This drops you to 0 Sanity — you will go Lost. Click Press once more to confirm.",
            color, BROADCAST_COLORS.warn)
        return false
    end

    char.sanity = char.sanity - 1
    local roll = rollAttackDice(1)
    broadcastEvent("proc", char.name .. " presses the attack (−1 Sanity): " .. formatRolls(roll.rolls))

    if roll.hits > 0 then
        ctx.threatHP = ctx.threatHP - 1
        ctx.hits = ctx.hits + 1
        broadcastEvent("gain", "Press lands! " .. (ctx.threat.name or "Threat") .. " HP: " .. math.max(0, ctx.threatHP))
        syncThreatHP(ctx.threat, ctx.threatHP)
        checkDownState(color)   -- pressing to 0 Sanity goes Down mid-fight
        if ctx.threatHP <= 0 then
            safecall(function() recordBeat("pressKill") end, "Telemetry")
            applyThreatDefeat(ctx.threat.name or "Threat", ctx.colors)
            gameState.combatContext = nil
        end
        safecall(function() refreshCombatPanel() end, "CombatPanel")
        return true
    end

    -- Press dice do not fumble; a 1-4 simply ends the streak.
    broadcastEvent("proc", char.name .. "'s press fizzles — the streak ends.")
    checkDownState(color)
    finishCombat()
    return true
end

-- The player stops pressing: the enemy counters and the window closes.
function finishCombat()
    local ctx = gameState.combatContext
    if not ctx then return end
    if ctx.threatHP > 0 then applyCounterAttack() end
    gameState.combatContext = nil
    safecall(function() refreshCombatPanel() end, "CombatPanel")
end

-----------------------------------------------------------------------
-- Charlie attack (Design §15.4)
-- Deterministic and escalating: first dark night costs 2 Sanity + 1 Health.
-- Each consecutive night in darkness, Charlie grows bolder: +1 to both.
-- A night with light (or no attack) resets her interest — see resolveTick.
-----------------------------------------------------------------------
function resolveCharlieAttack(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Coco is immune to Charlie
    if char.name == "Coco" then
        broadcastEvent("proc", char.name .. " is immune to Charlie (Night Vision).")
        return
    end

    local streak = char.charlieStreak or 0
    local sanityLoss = 2 + streak
    local healthLoss = 1 + streak

    broadcastEvent("damage", "CHARLIE attacks " .. char.name .. " in the darkness!")

    char.sanity = math.max(0, char.sanity - sanityLoss)
    char.health = math.max(0, char.health - healthLoss)
    char.charlieStreak = streak + 1
    char.charlieHitTonight = true
    safecall(function() recordCharlieInChronicle(char.name, char.charlieStreak) end, "Chronicle")

    if streak > 0 then
        broadcastEvent("damage", char.name .. " suffers Charlie: -" .. sanityLoss .. " Sanity, -" .. healthLoss ..
            " Health. (" .. (streak + 1) .. " nights in darkness — she grows bolder.)")
    else
        broadcastEvent("damage", char.name .. " suffers Charlie: -" .. sanityLoss .. " Sanity, -" .. healthLoss .. " Health.")
    end
    broadcastEvent("damage", char.name .. " now at Health " .. char.health .. ", Sanity " .. char.sanity .. ".")

    checkDownState(color)
end

