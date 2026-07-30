-- combat.lua  (F.7 — Combat dice rolling and resolution)
-- Design §12: fast dice-based combat. 5-6 = hit.
-- Fumble: a natural 1 deals 1 self-damage ONLY if the roll contains no
-- hits, and never more than 1 per roll — big dice pools aren't punished
-- for being big; whiffing completely is what hurts.

-----------------------------------------------------------------------
-- Roll attack dice and return { hits, fumbles, rolls[] }
-----------------------------------------------------------------------
function rollAttackDice(numDice)
    local result = { hits = 0, fumbles = 0, rolls = {} }
    for i = 1, numDice do
        local roll = gameRoll(1, 6)
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
-- Boss rewards (Design §14.1, improvements.md item 1 / design_batch1.md §2)
--
-- A phase-boss kill should visibly rescue the week, not just remove a
-- penalty. On top of recording the kill (bossesDefeated + the *Defeated
-- flags the Dawn onCleanup handlers watch), a defeat now:
--   * pushes Doom back (Deerclops -2, Eye -3; the Source ends the game),
--   * showers resources at the fight's tile + points at the Trophy (the
--     unique build-around card — the standalone loot deck from the spec
--     was folded into the Trophy to avoid a parallel atlas pipeline),
--   * lands a boss-specific kill line and a lighting flash.
-----------------------------------------------------------------------
BOSS_KILL_NARRATIONS = {
    deerclops = "The Deerclops shudders, and the cold goes out of it like a last breath. The court is only a court again.",
    eye       = "The Eye of Terror bursts. For one second you all see what it saw — then, mercifully, nothing.",
    source    = "The Source comes apart without a sound. Whatever it was, it isn't anymore.",
}
local BOSS_STANDEE_TAG = { deerclops = "Boss:Deerclops", eye = "Boss:EyeOfTerror", source = "Boss:TheSource" }

-- Boss key → the Trophy it awards. MIRRORS the `boss` column of
-- content/cards_trophies.csv (which holds the trophy NAMES, despite the
-- column heading); tests/test_cross_refs.py guards the mirror.
TROPHY_BY_BOSS = {
    deerclops = "The Antler Sled",
    eye       = "The Watching Jar",
    source    = "The Source Defeated",
}
local BOSS_LOOT_RESOURCES = { "Wood", "Metal", "Cloth", "Food" }

-- Resource shower + a nod to the Trophy at the fallen boss's tile.
function dropBossLoot(bossKey)
    local standee = findOneByTag(BOSS_STANDEE_TAG[bossKey] or "")
    local pos = standee and standee.getPosition()
    if not pos then return end
    for i = 1, 3 do
        local resType = BOSS_LOOT_RESOURCES[gameRoll(#BOSS_LOOT_RESOURCES)]
        local bag = getResourceBag and getResourceBag(resType)
        if bag then
            safecall(function()
                bag.takeObject({ position = { pos.x + (i - 2) * 1.2, pos.y + 3, pos.z + 1.5 }, smooth = true })
            end, "BossLoot")
        end
    end
    broadcastEvent("gain", "Spoils spill across the tile — 3 resources salvaged from the wreckage.")
end

-- Brief victory flash so a boss kill reads as an event, not a line of chat.
function flashVictoryLighting()
    if not Lighting then return end
    local base = Lighting.light_intensity or 0.6
    -- Runtime API: assign light_intensity then apply() (there is no
    -- setLightIntensity function).
    Lighting.light_intensity = math.min(1.2, base + 0.4)
    Lighting.apply()
    Wait.time(function() safecall(function()
        Lighting.light_intensity = base
        Lighting.apply()
    end, "Light") end, 0.6)
end

-----------------------------------------------------------------------
-- Source phases (Design §12.6, design_batch2.md §3)
--
-- The one new subsystem: persistent boss HP. Combat is otherwise
-- stateless about enemy HP (the card tracks it); the Source's phase
-- trigger needs the engine to know its real HP, so gameState.bossHP
-- mirrors every point of damage and survives saves mid-fight.
--
-- The phase beat: the FIRST time the Source drops to 5 HP or below, it
-- splits — two Terror Beaks peel off to adjacent tiles. Deterministic
-- and announced (§1.4 legible losses); fires exactly once.
-----------------------------------------------------------------------
-- HP retuned 10 → 8 in the batch-4 W3 calibration pass: the §20.1-sanctioned
-- first knob, which put the sim's best line in the 40-50% win band.
SOURCE_MAX_HP   = 8
SOURCE_SPLIT_HP = 5

local function isSourceName(name)
    return string.find(string.lower(name or ""), "source", 1, true) ~= nil
end

-- Boss name → persistent-HP key. The Treeguard keeps its HP on
-- gameState.treeguard (its own subsystem); the phase bosses live in
-- gameState.bossHP, seeded by their arrival Dawn effects.
function bossKeyForName(name)
    local lower = string.lower(name or "")
    if string.find(lower, "deerclops", 1, true) then return "deerclops" end
    if string.find(lower, "eye of terror", 1, true) or string.find(lower, "eyeofterror", 1, true) then return "eye" end
    if isSourceName(lower) then return "source" end
    if string.find(lower, "treeguard", 1, true) then return "treeguard" end
    return nil
end

-- Mirror applied damage onto the persistent record + check the phase beat.
function syncSourceHP(threatName, hp)
    if not isSourceName(threatName) then return end
    if not (gameState.bossHP and gameState.bossHP.source) then return end
    gameState.bossHP.source = math.max(0, hp)
    checkSourcePhase(hp)
end

-- Persist every point of boss damage — no honor-system counting on any
-- boss. Source keeps its phase-beat check; the Treeguard's HP lives on
-- its own record.
function syncBossHP(threatName, hp)
    local key = bossKeyForName(threatName)
    if not key then return end
    if key == "source" then
        syncSourceHP(threatName, hp)
    elseif key == "treeguard" then
        if gameState.treeguard then gameState.treeguard.hp = math.max(0, hp) end
    else
        gameState.bossHP = gameState.bossHP or {}
        gameState.bossHP[key] = math.max(0, hp)
    end
end

-- Threat-card damage that survives between Fight actions (and saves):
-- a 4 HP Shadow Stalker chipped for 2 today is a 2 HP fight tomorrow.
-- Keyed by card GUID; cleared when the card dies.
function syncThreatHP(threat, hp)
    if threat.cardGuid and threat.maxHp then
        gameState.threatDamage = gameState.threatDamage or {}
        gameState.threatDamage[threat.cardGuid] = math.max(0, threat.maxHp - math.max(0, hp))
    end
    syncBossHP(threat.name, hp)
end

function checkSourcePhase(hp)
    -- getSourceSplitHP(), not the constant: the threshold scales with the
    -- difficulty's HP pool (§17.2) so the beat keeps a "before" phase.
    if hp > 0 and hp <= getSourceSplitHP() and not gameState.sourceSplit then
        gameState.sourceSplit = true
        safecall(function() recordBeat("sourceSplit") end, "Telemetry")
        safecall(function() sourceSplitIntoBeaks() end, "SourceSplit")
    end
end

-- A dark mirror of flashVictoryLighting: the room dims for a beat.
function flashSplitLighting()
    if not Lighting then return end
    local base = Lighting.light_intensity or 0.6
    Lighting.light_intensity = math.max(0.05, base - 0.4)
    Lighting.apply()
    Wait.time(function() safecall(function()
        Lighting.light_intensity = base
        Lighting.apply()
    end, "Light") end, 0.8)
end

local SPLIT_LOCATIONS = {"JamesHouse", "RaymanHouse", "EllieLucaHouse", "BasketballCourt", "BadmintonCourt"}

function sourceSplitIntoBeaks()
    broadcastEvent("warn", "THE SOURCE SHUDDERS — AND SPLITS. Two TERROR BEAKS peel off it toward the neighboring tiles!")
    broadcastEvent("proc", "Burst it down before the Beaks land — or someone has to turn and deal with them.")
    safecall(function() flashSplitLighting() end, "Light")

    -- Find the Source's tile (nearest location to its standee).
    local standee = findOneByTag("Boss:TheSource")
    local sourceLoc, bestD
    if standee then
        local p = standee.getPosition()
        for _, locName in ipairs(SPLIT_LOCATIONS) do
            local tile = getLocationTile(locName)
            if tile then
                local tp = tile.getPosition()
                local d = (p.x - tp.x) ^ 2 + (p.z - tp.z) ^ 2
                if not bestD or d < bestD then bestD, sourceLoc = d, locName end
            end
        end
    end
    sourceLoc = sourceLoc or "EllieLucaHouse"

    local adjacent = adjacentLocations(sourceLoc)
    if #adjacent == 0 then adjacent = { sourceLoc } end

    -- Pull Terror Beak cards out of the threat deck onto the adjacent tiles;
    -- whatever the deck can't supply becomes a manual placement instruction.
    local placed = 0
    local deck = getThreatDeck()
    if deck and deck.getObjects then
        for _, entry in ipairs(deck.getObjects()) do
            if placed >= 2 then break end
            local nick = string.lower(entry.nickname or entry.name or "")
            if string.find(nick, "terror beak", 1, true) then
                local locName = adjacent[(placed % #adjacent) + 1]
                local tile = getLocationTile(locName)
                if tile then
                    placed = placed + 1
                    deck.takeObject({
                        guid = entry.guid,
                        position = tile.getPosition() + Vector(2, 1.5, -1 + placed),
                        rotation = {0, 180, 0},
                        smooth = true,
                    })
                    broadcastEvent("warn", "A TERROR BEAK lands at " .. locName ..
                        " — an ordinary threat: fight it, flee it, or let it fester.")
                end
            end
        end
    end
    if placed < 2 then
        broadcastEvent("warn", "Place " .. (2 - placed) .. " Terror Beak threat card(s) at tiles adjacent to " ..
            sourceLoc .. " (the deck/discard is out of Beaks — grab them from the discard).")
    end
end

function markBossDefeated(threatName)
    local lower = string.lower(threatName or "")
    gameState.bossesDefeated = gameState.bossesDefeated or {}
    local e = gameState.ongoingDawnEffects
    local key = nil

    -- Trophies are awarded with the boss kill, so the kill is where the
    -- utilization report learns whether anyone ever earned one (§20.2 item 8).
    -- Record the TROPHY's printed name, not the boss's: the report scores
    -- against the `boss` column of content/cards_trophies.csv, which holds the
    -- trophy names, and "Deerclops" would never match "The Antler Sled".
    safecall(function()
        recordUsage("trophies", TROPHY_BY_BOSS[bossKeyForName(threatName) or ""] or threatName)
    end, "Usage")

    if string.find(lower, "deerclops", 1, true) then
        key = "deerclops"
        gameState.bossesDefeated.deerclops = true
        e.deerclopsDefeated = true
        gameState.doom = math.max(0, gameState.doom - 2)
        safecall(function() moveDoomMarker(gameState.doom) end, "Doom")
        broadcastEvent("gain", "The Deerclops falls! Sanity costs return to normal — and the pressure eases: Doom -2 (now "
            .. gameState.doom .. "). Its Trophy flips face-up on the trophy row — its power is live.")
    elseif string.find(lower, "eye of terror", 1, true) or string.find(lower, "eyeofterror", 1, true) then
        key = "eye"
        gameState.bossesDefeated.eye = true
        e.eyeDefeated = true
        gameState.doom = math.max(0, gameState.doom - 3)
        safecall(function() moveDoomMarker(gameState.doom) end, "Doom")
        broadcastEvent("gain", "The Eye of Terror is destroyed! The sky stops watching: Doom -3 (now "
            .. gameState.doom .. "). Its Trophy flips face-up on the trophy row — its power is live.")
    elseif string.find(lower, "source", 1, true) then
        key = "source"
        gameState.bossesDefeated.source = true
        e.sourceDefeated = true
        e.sourceActive = nil
        if gameState.bossHP then gameState.bossHP.source = 0 end
        broadcastEvent("gain", "THE SOURCE IS DESTROYED. Its Trophy flips face-up — you have won the week.")
    end

    if key then
        if BOSS_KILL_NARRATIONS[key] then broadcastEvent("phase", BOSS_KILL_NARRATIONS[key]) end
        safecall(function() flashVictoryLighting() end, "Light")
        safecall(function() dropBossLoot(key) end, "BossLoot")
        safecall(function() revealTrophy(key) end, "Trophy")
        -- The fallen boss leaves the map (loot dropped first — it needs the
        -- standee's position). Back in the pool it stops festering and the
        -- Source stops blocking victory.
        safecall(function()
            local standee = findOneByTag(BOSS_STANDEE_TAG[key] or "")
            local pool = getBossPool()
            if standee and pool then pool.putObject(standee) end
        end, "BossStandee")
    end
end

-- Trophies sit face-down on the trophy row; a boss kill flips its own
-- trophy face-up automatically — no card handling by the players.
local TROPHY_TAG_BY_BOSS = {
    deerclops = "TR_DEERCLOPS",
    eye       = "TR_EYE_OF_TERROR",
    source    = "TR_SOURCE",
}

function revealTrophy(key)
    local tag = TROPHY_TAG_BY_BOSS[key]
    if not tag then return end
    local trophy = findOneByTag(tag)
    if not trophy then return end
    trophy.setRotationSmooth({0, 180, 0}, false, true)  -- face up
    trophy.highlightOn("Yellow", 10)
end

