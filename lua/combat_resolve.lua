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
    safecall(function() markBossDefeated(threatName, colors) end, "BossFlags")
    safecall(function() recordKillInChronicle(threatName, colors) end, "Chronicle")
    local bossKey = Audio and Audio.threatNameToBossKey and Audio.threatNameToBossKey(threatName)
    if bossKey then safecall(function() Audio.stopBossLoop(bossKey) end, "Audio") end
    if bossKey == "treeguard" then safecall(function() treeguardDefeated(colors) end, "Treeguard") end
    -- A kill is the moment its achievement should land, not the end of the
    -- week — and both flags and the chronicle are up to date by here.
    safecall(function() checkAchievements("kill") end, "Achievements")
    -- Printed on-death riders (the Black Dog's mate answering from the dark).
    -- Last, so the card that killed it has already been cleared away and the
    -- new draw lands on a tidy tile — and after the achievement, so "defeat
    -- fifteen threats" cannot be gamed by the reinforcement it summons.
    local killedId = ctx and ctx.threat and ctx.threat.cardId
    if killedId then
        local where = colors[1] and gameState.activeChars[colors[1]]
            and gameState.activeChars[colors[1]].location
        safecall(function() resolveHardThreatDefeat(killedId, where) end, "DefeatRider")
    end
    -- Last, so the popup carries every line above it too — the kill, the
    -- Sanity gain, boss loot/narration if any, the death rider.
    safecall(function() showFightResultDialog(ctx and ctx.logMark) end, "FightResultPopup")
end

-- Enemy counter-attack against the live combat, then leave HP as-is.
function applyCounterAttack()
    local ctx = gameState.combatContext
    if not ctx or ctx.threatHP <= 0 then return end
    local threatAtk = ctx.threat.attack or 0
    -- Multi-attack (the Spider Thing): the card rolls more dice than its
    -- printed Attack column, so the rider overrides rather than adds.
    if ctx.threat.counterDice then threatAtk = ctx.threat.counterDice end

    -- Where the fight is decides how well you can cover (Design §7.1-7.5).
    -- A negative defence is extra dice for the threat — being caught on an
    -- open court is the same rule pointed the other way — so it is folded in
    -- before the "does it even swing" check.
    local here = ctx.colors[1] and gameState.activeChars[ctx.colors[1]]
        and gameState.activeChars[ctx.colors[1]].location
    local defence = LOCATION_DEFENSE[here or ""] or 0
    if defence < 0 and threatAtk > 0 then
        threatAtk = threatAtk - defence
        broadcastEvent("warn", "No cover at " .. here .. " — it swings " ..
            (-defence) .. " extra time(s).")
    end

    if threatAtk <= 0 then return end
    local tName = ctx.threat.name or "Threat"
    broadcastEvent("proc", tName .. " counter-attacks with " .. threatAtk .. " dice...")
    local defResult = rollAttackDice(threatAtk)
    broadcastEvent("proc", "Enemy: " .. formatRolls(defResult.rolls))

    -- The Net (§7.5): the team rolls its defence dice and each 5-6 turns one
    -- incoming hit aside. Rolled only when something actually landed, so a
    -- missed counter doesn't spend the table's attention on a pointless roll.
    local blockedAll = false
    if defence > 0 and defResult.hits > 0 then
        local block = rollAttackDice(defence)
        broadcastEvent("proc", "Defending at " .. here .. ": " .. formatRolls(block.rolls))
        local blocked = math.min(block.hits, defResult.hits)
        if blocked > 0 then
            defResult.hits = defResult.hits - blocked
            blockedAll = (defResult.hits == 0)
            broadcastEvent("gain", "The cover at " .. here .. " turns " .. blocked ..
                " hit(s) aside.")
        end
    end

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
        local struck, struckOrder = {}, {}
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
                if not struck[c.name] then
                    struck[c.name] = true
                    table.insert(struckOrder, c.name)
                end
                if color == defenderColor then checkDownState(color) end
            end
        end
        -- One cue for the whole volley, one shake per person hit. Three hits
        -- on one character is one thud and one shake, not three of each: the
        -- single MusicPlayer would only restart the clip anyway, and the log
        -- lines above already carry the count.
        --
        -- Deliberately BEFORE the checkDownState sweep. Going Down plays its
        -- own sound, and taking the last point of Health should end on that,
        -- not on the generic hit thud.
        if #struckOrder > 0 then
            safecall(function() Audio.playHitTaken() end, "HitSFX")
            for _, name in ipairs(struckOrder) do
                safecall(function() jiggleCharacterHit(name) end, "HitJiggle")
            end
        end
        for _, color in ipairs(ctx.colors) do checkDownState(color) end
    elseif blockedAll then
        -- It connected and the cover ate it — saying "misses" here would
        -- credit the dice with what the Net actually did.
        broadcastEvent("gain", tName .. " gets through nothing — every hit turned aside.")
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

    -- Where THIS fight's own narration starts in gameState.dayLog — every
    -- broadcastEvent from here to whichever exit ends the fight is the
    -- fight, verbatim. showFightResultDialog (below) slices this range
    -- rather than re-summarizing it by hand, so the popup can never say
    -- something different from what was actually broadcast.
    local logMark = #(gameState.dayLog or {})

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

    -- Per-fighter dice are kept, not just the sum: the Roommate bills Sanity
    -- per die and must not re-call getAttackDice (it broadcasts the Court
    -- Master and weapon lines as a side effect, so a second call prints them
    -- twice).
    local totalDice, diceByColor = 0, {}
    for _, color in ipairs(participants) do
        diceByColor[color] = getAttackDice(color)
        totalDice = totalDice + diceByColor[color]
    end

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
        safecall(function() Audio.playHitLand() end, "HitSFX")
        safecall(function() jiggleThreat(threatData) end, "HitJiggle")
    end

    -- Fumble: only on a complete whiff (no hits at all), max 1, to the healthiest.
    if atkResult.fumbles > 0 and atkResult.hits == 0 then
        local tank = _healthiestColor(participants)
        local c = gameState.activeChars[tank]
        c.health = math.max(0, c.health - 1)
        broadcastEvent("damage", c.name .. " whiffs completely and fumbles! Takes 1 self-damage. Health: " .. c.health)
        -- A fumble is damage taken, not damage dealt: same cue as being hit.
        safecall(function() Audio.playHitTaken() end, "HitSFX")
        safecall(function() jiggleCharacterHit(c.name) end, "HitJiggle")
        checkDownState(tank)
    elseif atkResult.fumbles > 0 then
        broadcastEvent("proc", "A 1 was rolled, but a hit landed — no fumble damage.")
    end

    -- Sanity-on-attack specials (threat_hard.lua). Two shapes, because two
    -- cards charge differently: Your Roommate bills per attack DIE rolled,
    -- A Child's Shadow bills a flat 1 per attacker for swinging at all.
    --
    -- Both are charged to EVERY participant, each on their own dice. The
    -- per-die rule used to be skipped entirely unless `#participants == 1`,
    -- which made Fight Together a way to dodge the Roommate's whole printed
    -- cost — the one card in the deck whose point is that hitting it hurts,
    -- turned off by the button next to it.
    if threatData.sanityPerAttackDie or threatData.sanityPerFight then
        for _, pColor in ipairs(participants) do
            local c = gameState.activeChars[pColor]
            if c then
                local sLoss = 0
                if threatData.sanityPerAttackDie then
                    sLoss = sLoss + threatData.sanityPerAttackDie * (diceByColor[pColor] or 1)
                end
                if threatData.sanityPerFight then
                    sLoss = sLoss + threatData.sanityPerFight
                end
                if sLoss > 0 then
                    c.sanity = math.max(0, c.sanity - sLoss)
                    broadcastEvent("damage", c.name .. " loses " .. sLoss ..
                        " Sanity from attacking " .. threatName .. ".")
                    checkDownState(pColor)
                end
            end
        end
    end

    gameState.combatContext = { colors = participants, threat = threatData,
                                threatHP = threatHP, hits = atkResult.hits, open = false,
                                logMark = logMark }

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

    -- Complete whiff: no press, the enemy counters now. Routed through
    -- finishCombat rather than calling applyCounterAttack + clearing the
    -- context here directly, so this exit shows the result popup exactly
    -- like every other way a fight can end.
    finishCombat()
    return { defeated = false, remainingHP = threatHP }
end

-- Single-fighter shorthand for beginCombat, which takes a colour LIST.
--
-- Game code does not call this and should not: the real fight path
-- (doFight, actions_combat.lua) checks canFight, resolves the threat's
-- statline, applies carried chip damage and assembles the participant list
-- before it calls beginCombat. Reaching the resolver directly skips every
-- one of those rules. It exists for the combat tests, which want to drive
-- the resolver without the targeting UI in the way.
--
-- There is deliberately no resolveGroupCombat: for several fighters the
-- signature is already beginCombat(colors, threatData), so a wrapper would
-- be an alias that only makes the two look like different mechanisms.
function resolveCombat(color, threatData)
    return beginCombat({ color }, threatData)
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
        safecall(function() Audio.playHitLand() end, "HitSFX")
        safecall(function() jiggleThreat(ctx.threat) end, "HitJiggle")
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
-- Also the shared exit for "no press, whiff, counter now" (beginCombat) and
-- "turn ended with a press window still open" (turns.lua endPlayerTurn) —
-- every non-defeat way a fight can end passes through here once.
function finishCombat()
    local ctx = gameState.combatContext
    if not ctx then return end
    if ctx.threatHP > 0 then applyCounterAttack() end
    gameState.combatContext = nil
    safecall(function() refreshCombatPanel() end, "CombatPanel")
    safecall(function() showFightResultDialog(ctx.logMark) end, "FightResultPopup")
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
    -- Charlie has no piece on the table to shake — she is the dark itself —
    -- so the feedback lands entirely on her victim.
    safecall(function() Audio.playHitTaken() end, "HitSFX")
    safecall(function() jiggleCharacterHit(char.name) end, "HitJiggle")
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

