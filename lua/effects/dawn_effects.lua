-- dawn_effects.lua  (F.5 — Dawn-card effect dispatch table)
-- Each entry maps a card ID to { onReveal(card), onCleanup() }.
-- onReveal fires when the card is drawn; onCleanup fires at the next Dawn.

DAWN_EFFECTS = {}

-----------------------------------------------------------------------
-- Helper: apply stat change to all active (non-down) characters.
--
-- Calm Words (§6.5): when a scripted Sanity-loss event lands, Luca rolls
-- a d6 — on 4+ the whole group at HIS location ignores the loss.
-- Everyone elsewhere still pays. (Card texts that name a single victim
-- resolve inline in their own effects and stay a table roll.)
-----------------------------------------------------------------------
function allPlayersLose(stat, amount)
    local calmedLocation = nil
    if stat == "sanity" then
        for _, char in pairs(gameState.activeChars) do
            if char.name == "Luca" and not char.down then
                local roll = gameRoll(1, 6)
                if roll >= 4 then
                    calmedLocation = char.location
                    broadcastEvent("gain", "Calm Words: Luca rolls " .. roll ..
                        " — everyone at " .. (calmedLocation or "?") .. " ignores the Sanity loss.")
                else
                    broadcastEvent("proc", "Calm Words: Luca rolls " .. roll .. " — the words don't land this time.")
                end
                break
            end
        end
    end
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            if calmedLocation and char.location == calmedLocation then
                broadcastEvent("proc", char.name .. " is steadied by Luca — no " .. stat .. " loss.")
            else
                char[stat] = math.max(0, char[stat] - amount)
                broadcastEvent("damage", char.name .. " loses " .. amount .. " " .. stat .. ".")
            end
        end
    end
end

function allPlayersGain(stat, amount)
    for color, char in pairs(gameState.activeChars) do
        if not char.down then
            char[stat] = math.min(char["max" .. stat:sub(1,1):upper() .. stat:sub(2)], char[stat] + amount)
            broadcastEvent("gain", char.name .. " gains " .. amount .. " " .. stat .. ".")
        end
    end
end

function lowestStatPlayer(stat)
    local lowest, lowestChar = 999, nil
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char[stat] < lowest then
            lowest = char[stat]
            lowestChar = char
        end
    end
    return lowestChar
end

-----------------------------------------------------------------------
-- Boss arrivals place their own standee (the Boss Pool bag's stated
-- purpose). On the map it festers, blocks victory (the Source), and can
-- be fought; in the bag it is none of those things — so arrival cards
-- must never rely on players remembering to fish it out.
-----------------------------------------------------------------------
function placeBossStandee(bossName, locName)
    local tile = getLocationTile(locName)
    if not tile then return false end
    local target = tile.getPosition() + Vector(0, 2, 0.5)

    -- Already on the table (re-arrival after a reload)? Just move it.
    local standee = findOneByTag("Boss:" .. bossName)
    if standee then
        standee.setPositionSmooth(target)
        return true
    end

    local pool = getBossPool()
    if not pool then return false end
    local wanted = "Boss:" .. bossName
    for _, entry in ipairs(pool.getObjects()) do
        local match = false
        for _, t in ipairs(entry.tags or {}) do
            if t == wanted then match = true break end
        end
        if not match then
            -- Nickname fallback: "Eye of Terror" vs "EyeOfTerror" etc.
            local nick = ((entry.nickname ~= "" and entry.nickname) or entry.name or ""):gsub("%s", "")
            match = (nick:lower() == bossName:lower():gsub("%s", ""))
        end
        if match then
            pool.takeObject({ guid = entry.guid, position = target, smooth = true })
            return true
        end
    end
    return false
end

-- The defeated/departing boss goes back in the bag (stops festering).
function poolBossStandee(bossName)
    local standee = findOneByTag("Boss:" .. bossName)
    local pool = getBossPool()
    if standee and pool then
        pool.putObject(standee)
        return true
    end
    return false
end

