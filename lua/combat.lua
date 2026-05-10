-- combat.lua  (F.7 — Combat dice rolling and resolution)
-- Design §12: fast dice-based combat. 5-6 = hit, 1 = fumble.

-----------------------------------------------------------------------
-- Roll attack dice and return { hits, fumbles, rolls[] }
-----------------------------------------------------------------------
function rollAttackDice(numDice)
    local result = { hits = 0, fumbles = 0, rolls = {} }
    for i = 1, numDice do
        local roll = math.random(1, 6)
        table.insert(result.rolls, roll)
        if roll >= 5 then
            result.hits = result.hits + 1
        elseif roll == 1 then
            result.fumbles = result.fumbles + 1
        end
    end
    return result
end

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

    -- Rayman gets +1 base attack
    if char.name == "Rayman" then dice = dice + 1 end

    -- Equipment bonuses would be checked via hand zone / item tags
    -- For now, broadcast a reminder
    return dice
end

-----------------------------------------------------------------------
-- Resolve a player attacking a threat
-- threatData = { name, hp, attack, special }
-----------------------------------------------------------------------
function resolveCombat(color, threatData)
    local char = gameState.activeChars[color]
    if not char then return end

    local attackerName = char.name
    local threatName = threatData.name or "Unknown Threat"
    local threatHP = threatData.hp or 0
    local threatAtk = threatData.attack or 0

    broadcastEvent("proc", "--- COMBAT: " .. attackerName .. " vs " .. threatName .. " ---")

    -- Player attacks
    local numDice = getAttackDice(color)
    broadcastEvent("proc", attackerName .. " rolls " .. numDice .. " attack dice...")

    local atkResult = rollAttackDice(numDice)
    broadcastEvent("proc", "Attack: " .. formatRolls(atkResult.rolls))

    -- Apply hits to threat
    threatHP = threatHP - atkResult.hits
    if atkResult.hits > 0 then
        broadcastEvent("gain", atkResult.hits .. " hit(s)! " .. threatName .. " HP: " .. math.max(0, threatHP))
    end

    -- Apply fumbles to attacker
    if atkResult.fumbles > 0 then
        char.health = math.max(0, char.health - atkResult.fumbles)
        broadcastEvent("damage", attackerName .. " fumbles " .. atkResult.fumbles .. " time(s)! Takes " .. atkResult.fumbles .. " self-damage. Health: " .. char.health)
    end

    -- Sanity cost if the threat has a sanity-on-attack special (e.g. Child Shadow)
    if threatData.sanityCostPerAttack then
        local sLoss = threatData.sanityCostPerAttack * numDice
        char.sanity = math.max(0, char.sanity - sLoss)
        broadcastEvent("damage", attackerName .. " loses " .. sLoss .. " Sanity from attacking " .. threatName .. ".")
    end

    -- Check threat defeated
    if threatHP <= 0 then
        broadcastEvent("gain", threatName .. " is DEFEATED!")
        -- Defeat reward: +1 Sanity to attacker (Design §12)
        char.sanity = math.min(char.maxSanity, char.sanity + 1)
        broadcastEvent("gain", attackerName .. " gains +1 Sanity from victory.")
        checkDownState(color)
        return { defeated = true, remainingHP = 0 }
    end

    -- Enemy counter-attack
    if threatAtk > 0 then
        broadcastEvent("proc", threatName .. " counter-attacks with " .. threatAtk .. " dice...")
        local defResult = rollAttackDice(threatAtk)
        broadcastEvent("proc", "Enemy: " .. formatRolls(defResult.rolls))

        if defResult.hits > 0 then
            char.health = math.max(0, char.health - defResult.hits)
            broadcastEvent("damage", attackerName .. " takes " .. defResult.hits .. " damage! Health: " .. char.health)
        else
            broadcastEvent("proc", threatName .. " misses!")
        end
    end

    checkDownState(color)
    return { defeated = false, remainingHP = threatHP }
end

-----------------------------------------------------------------------
-- Roll the Charlie attack dice (Design §15.4)
-- d8 Sanity damage + d6 Health damage
-----------------------------------------------------------------------
function resolveCharlieAttack(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Coco is immune to Charlie
    if char.name == "Coco" then
        broadcastEvent("proc", char.name .. " is immune to Charlie (Night Vision).")
        return
    end

    broadcastEvent("damage", "CHARLIE attacks " .. char.name .. " in the darkness!")

    local sanityRoll = math.random(1, 8)
    local healthRoll = math.random(1, 6)

    char.sanity = math.max(0, char.sanity - sanityRoll)
    char.health = math.max(0, char.health - healthRoll)

    broadcastEvent("damage", char.name .. " suffers Charlie: d8=" .. sanityRoll .. " Sanity, d6=" .. healthRoll .. " Health lost.")
    broadcastEvent("damage", char.name .. " now at Health " .. char.health .. ", Sanity " .. char.sanity .. ".")

    checkDownState(color)
end

-----------------------------------------------------------------------
-- Group combat (simplified: sum all co-located attackers' dice)
-----------------------------------------------------------------------
function resolveGroupCombat(colors, threatData)
    local threatName = threatData.name or "Unknown Threat"
    local threatHP = threatData.hp or 0
    local threatAtk = threatData.attack or 0

    broadcastEvent("proc", "--- GROUP COMBAT vs " .. threatName .. " ---")

    -- All attackers roll together
    local totalDice = 0
    local participants = {}
    for _, color in ipairs(colors) do
        local char = gameState.activeChars[color]
        if char and not char.down then
            local d = getAttackDice(color)
            totalDice = totalDice + d
            table.insert(participants, { color = color, char = char, dice = d })
        end
    end

    local atkResult = rollAttackDice(totalDice)
    broadcastEvent("proc", "Group rolls " .. totalDice .. " dice: " .. formatRolls(atkResult.rolls))

    -- Hits
    threatHP = threatHP - atkResult.hits
    if atkResult.hits > 0 then
        broadcastEvent("gain", atkResult.hits .. " hit(s)! " .. threatName .. " HP: " .. math.max(0, threatHP))
    end

    -- Fumbles: distribute round-robin starting with highest-health
    if atkResult.fumbles > 0 then
        table.sort(participants, function(a, b) return a.char.health > b.char.health end)
        for i = 1, atkResult.fumbles do
            local p = participants[((i - 1) % #participants) + 1]
            p.char.health = math.max(0, p.char.health - 1)
            broadcastEvent("damage", p.char.name .. " takes 1 fumble damage. Health: " .. p.char.health)
        end
    end

    if threatHP <= 0 then
        broadcastEvent("gain", threatName .. " is DEFEATED!")
        for _, p in ipairs(participants) do
            p.char.sanity = math.min(p.char.maxSanity, p.char.sanity + 1)
            broadcastEvent("gain", p.char.name .. " gains +1 Sanity from victory.")
            checkDownState(p.color)
        end
        return { defeated = true, remainingHP = 0 }
    end

    -- Counter-attack: distribute hits round-robin (highest health first)
    if threatAtk > 0 then
        broadcastEvent("proc", threatName .. " counter-attacks with " .. threatAtk .. " dice...")
        local defResult = rollAttackDice(threatAtk)
        broadcastEvent("proc", "Enemy: " .. formatRolls(defResult.rolls))

        if defResult.hits > 0 then
            for i = 1, defResult.hits do
                local p = participants[((i - 1) % #participants) + 1]
                p.char.health = math.max(0, p.char.health - 1)
                broadcastEvent("damage", p.char.name .. " takes 1 counter-attack damage. Health: " .. p.char.health)
            end
        end
    end

    for _, p in ipairs(participants) do
        checkDownState(p.color)
    end

    return { defeated = false, remainingHP = threatHP }
end
