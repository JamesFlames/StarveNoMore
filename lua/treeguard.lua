-- treeguard.lua  (Phase 2.5 mini-boss — Design §14.2)
-- The Treeguard wakes at Dusk of Day 4, lairing at a random sport court.
-- While awake: Gather at its court is blocked (it guards the timber), and
-- it festers Doom +1 at each Dawn (mini-boss rate; phase bosses fester +2).
-- Two outs: fight it (HP 5, Atk 2; defeat = +1 Sanity each + 3 Wood), or
-- appease it (spend 2 Wood at its tile to plant saplings — it returns to
-- sleep, no reward). Pure DST: the trees only want their pound of bark.

TREEGUARD_STATS = { name = "Treeguard", hp = 5, attack = 2 }

function getTreeguardStandee()
    return findOneByTag("Boss:Treeguard")
end

function wakeTreeguard()
    if gameState.treeguard then return end  -- already woke this game

    local courts = { "BasketballCourt", "BadmintonCourt" }
    local lair = courts[gameRoll(#courts)]
    gameState.treeguard = { active = true, location = lair, hp = TREEGUARD_STATS.hp }

    broadcastEvent("phase", "THE GROVE WAKES — a TREEGUARD unfolds itself at " .. lair .. "!")
    broadcastEvent("warn", "Treeguard (HP " .. TREEGUARD_STATS.hp .. ", Atk " .. TREEGUARD_STATS.attack ..
        "). While it stands: no Gathering at " .. lair .. ", and it festers Doom +1 each Dawn.")
    broadcastEvent("proc", "Fight it — or Appease it: spend 2 Wood at its tile to plant saplings and send it back to sleep.")

    -- Place the standee from the Boss Pool onto the lair tile.
    local tile = getLocationTile(lair)
    local pool = getBossPool()
    if pool and tile then
        for _, entry in ipairs(pool.getObjects()) do
            if entry.name == "Treeguard" or (entry.nickname or "") == "Treeguard" then
                pool.takeObject({
                    guid = entry.guid,
                    position = tile.getPosition() + Vector(0, 2, 0.5),
                    smooth = true,
                })
                break
            end
        end
    else
        -- Standee already on the table (or pool missing): just move it.
        local standee = getTreeguardStandee()
        if standee and tile then
            standee.setPositionSmooth(tile.getPosition() + Vector(0, 2, 0.5))
        end
    end

    safecall(function() nudgeCameraToBoss("Treeguard", lair) end, "CameraNudge")
    safecall(function() Audio.playBossLoop("treeguard") end, "Audio")
end

-- Return the standee to the Boss Pool (shared by defeat and appeasement).
local function _sleepStandee()
    local standee = getTreeguardStandee()
    local pool = getBossPool()
    if standee and pool then
        pool.putObject(standee)
    end
end

-- Called from combat_resolve.lua's applyThreatDefeat when a threat named
-- "Treeguard" hits 0 HP. `colors` is the fighter list applyThreatDefeat
-- already has on hand — the same shape dropBossLoot (combat.lua) takes.
--
-- Used to spawn 3 Wood tokens loose at the tile and call it salvaged: the
-- exact bug dropBossLoot's own comment documents for the phase bosses
-- ("nobody received them... physical tokens are decoration, the economy is
-- gameState.resources"). The Treeguard is a mini-boss on its own code path
-- and got missed when that fix landed. lootRecipients + giveResource is the
-- same fix, reused rather than re-solved.
function treeguardDefeated(colors)
    if not (gameState.treeguard and gameState.treeguard.active) then return end
    gameState.treeguard.active = false

    local winners = lootRecipients(colors)
    if #winners == 0 then
        broadcastEvent("warn", "The TREEGUARD splinters and falls — 3 Wood spill out with nobody standing to take it.")
    else
        local haul = {}
        for i = 1, 3 do
            local color = winners[((i - 1) % #winners) + 1]
            safecall(function() giveResource(color, "Wood", 1) end, "TreeguardSalvage")
            local ch = gameState.activeChars[color]
            local who = (ch and ch.name) or color
            haul[who] = (haul[who] or 0) + 1
        end
        local parts = {}
        for who, n in pairs(haul) do table.insert(parts, who .. ": " .. n .. " Wood") end
        table.sort(parts)   -- pairs() order would reshuffle the line every kill
        broadcastEvent("gain", "The TREEGUARD splinters and falls — 3 Wood salvaged: " ..
            table.concat(parts, "  ·  ") .. ".")
    end

    _sleepStandee()
    -- combat.lua already stops the boss audio loop via threatNameToBossKey.
end

-- Appease: at the Treeguard's tile, spend 2 Wood to send it back to sleep.
-- No action cost gate here beyond the wood — planting is quick, calming work.
function doAppeaseTreeguard(color)
    local tg = gameState.treeguard
    if not (tg and tg.active) then
        broadcastToColor("There is no Treeguard to appease.", color, BROADCAST_COLORS.proc)
        return
    end

    local char = gameState.activeChars[color]
    if not char or char.down then return end
    if char.location ~= tg.location then
        broadcastToColor("You must be at " .. tg.location .. " to appease the Treeguard.", color, BROADCAST_COLORS.damage)
        return
    end

    if not spendAction(color, "Appease Treeguard") then return end

    -- Auto-verify and pay the 2 Wood; refund the action if unaffordable.
    if not verifyAndPayResources(color, {Wood=2}, "appeasing the Treeguard") then
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    tg.active = false
    broadcastEvent("gain", char.name .. " kneels and plants saplings. The Treeguard watches... then folds back into stillness.")
    broadcastEvent("proc", "The Treeguard returns to sleep. No reward — but no fight, and no more festering.")

    _sleepStandee()
    safecall(function() Audio.stopBossLoop("treeguard") end, "Audio")
end
