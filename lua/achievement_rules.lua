-- achievement_rules.lua — one predicate per achievement id.
--
-- ACHIEVEMENT_RULES[id]() -> truthy when the achievement is earned RIGHT NOW.
-- checkAchievements (achievements.lua) re-tests the whole table at every
-- checkpoint, so a predicate must be a pure read of gameState / the chronicle:
-- no side effects, no broadcasts, no object handles.
--
-- Every id in content/achievements.csv needs an entry here and vice versa —
-- tests/test_lua_achievements.py fails on either gap, so the roster and the
-- rules cannot drift the way a hand-maintained pair of lists always does.
--
-- Nothing here records anything new at the table: every number these rules
-- read was already being tracked for the Week in Review (§16.5) or the
-- session telemetry (§20.2). That is the constraint the Review works under
-- and achievements inherit it.

-----------------------------------------------------------------------
-- Shared readers
-----------------------------------------------------------------------
function achChronicle()
    if ensureChronicle then return ensureChronicle() end
    return gameState.chronicle or {}
end

function achWon()
    return gameState.gameOverCause == "victory"
end

-- Characters still on their feet, and how many are in play at all.
function achStanding()
    local standing, total = 0, 0
    for _, char in pairs(gameState.activeChars or {}) do
        total = total + 1
        if not char.down then standing = standing + 1 end
    end
    return standing, total
end

-- Total of one telemetry usage bucket ("crafted", "cooked", "actions", ...).
function achUsageTotal(kind)
    local n = 0
    for _, count in pairs((achChronicle().usage or {})[kind] or {}) do
        n = n + (count or 0)
    end
    return n
end

-- Did a boss with this name in it ever fall? Used for the Treeguard, which is
-- a mini-boss (§14.2) and so has no gameState.bossesDefeated key of its own —
-- its kill lands in the chronicle like any other.
function achKilledNamed(needle)
    for _, k in ipairs(achChronicle().kills or {}) do
        if string.find(string.lower(k.threat or ""), needle, 1, true) then return true end
    end
    return false
end

-- The three phase bosses. bossesDefeated is authoritative; the ongoing-effect
-- flags are checked too so a mid-campaign save from before it existed still
-- scores (the same pairing checkBonusVictories uses).
function achBossDown(key)
    local bd = gameState.bossesDefeated or {}
    local e = gameState.ongoingDawnEffects or {}
    if key == "deerclops" then return bd.deerclops or e.deerclopsDefeated end
    if key == "eye"       then return bd.eye       or e.eyeDefeated end
    if key == "source"    then return bd.source    or e.sourceDefeated end
    return false
end

-- "Survived to the end of day N": the chronicle gets a headline for a day
-- only once that day is over (recordDayInChronicle, at the day-end summary),
-- which is exactly the fact these want and is immune to where `gameState.day`
-- happens to be mid-Tick.
function achDayCompleted(day)
    return (achChronicle().days or {})[day] ~= nil
end

function achMealsCooked()
    local n = 0
    for _, count in pairs(achChronicle().meals or {}) do n = n + (count or 0) end
    return n
end

function achBeats()
    return achChronicle().beats or {}
end

-----------------------------------------------------------------------
-- The rules
-----------------------------------------------------------------------
ACHIEVEMENT_RULES = {}

-- ---- Progress ----
ACHIEVEMENT_RULES.A_FIRST_NIGHT = function()
    return achDayCompleted(1)
end

ACHIEVEMENT_RULES.A_MIDWEEK = function()
    return achDayCompleted(4)
end

ACHIEVEMENT_RULES.A_SURVIVOR = function()
    return achWon()
end

-- ---- Mastery ----
-- Mirrors checkBonusVictories' Pristine Run (§16.2): every character IN PLAY
-- on their feet, and nobody brought back.
ACHIEVEMENT_RULES.A_PRISTINE = function()
    if not achWon() then return false end
    local standing, total = achStanding()
    return total > 0 and standing == total and (achChronicle().revives or 0) == 0
end

ACHIEVEMENT_RULES.A_HERO = function()
    return achBossDown("deerclops") and achBossDown("eye") and achBossDown("source")
end

ACHIEVEMENT_RULES.A_TRUTH = function()
    return (gameState.clueCount or 0) >= 3
end

ACHIEVEMENT_RULES.A_NIGHTMARE = function()
    return achWon() and gameState.difficulty == "nightmare"
end

ACHIEVEMENT_RULES.A_WEEKEND = function()
    return achWon() and gameState.difficulty == "weekend"
end

ACHIEVEMENT_RULES.A_SOLO = function()
    return achWon() and gameState.solo == true
end

ACHIEVEMENT_RULES.A_WIRE = function()
    return achWon() and (getDoomLimit() - (gameState.doom or 0)) <= 2
end

-- ---- Bosses ----
ACHIEVEMENT_RULES.A_DEERCLOPS = function() return achBossDown("deerclops") end
ACHIEVEMENT_RULES.A_EYE       = function() return achBossDown("eye") end
ACHIEVEMENT_RULES.A_SOURCE    = function() return achBossDown("source") end
ACHIEVEMENT_RULES.A_TREEGUARD = function() return achKilledNamed("treeguard") end

-- ---- Habits ----
ACHIEVEMENT_RULES.A_CAMP_MOTHER = function()
    return achMealsCooked() >= 10
end

ACHIEVEMENT_RULES.A_HANDY = function()
    return achUsageTotal("crafted") >= 8
end

ACHIEVEMENT_RULES.A_WATCH = function()
    return #(achChronicle().kills or {}) >= 15
end

ACHIEVEMENT_RULES.A_PRESS = function()
    return (achBeats().pressKills or 0) >= 3
end

-- Every character at the table spent the one move that is theirs alone. A
-- roster of nobody must not satisfy it, hence the count check.
ACHIEVEMENT_RULES.A_ALL_HANDS = function()
    local count = 0
    for _, char in pairs(gameState.activeChars or {}) do
        if not char.signatureUsed then return false end
        count = count + 1
    end
    return count > 0
end

ACHIEVEMENT_RULES.A_DARE = function()
    return (achBeats().daresTaken or 0) >= 5
end

ACHIEVEMENT_RULES.A_HEART = function()
    return (achChronicle().revives or 0) >= 1
end

-- ---- Secret ----
ACHIEVEMENT_RULES.A_SPLIT = function()
    return achBeats().sourceSplit == true
end

ACHIEVEMENT_RULES.A_CHARLIE = function()
    return ((achChronicle().maxCharlieStreak or {}).value or 0) >= 3
end

ACHIEVEMENT_RULES.A_LAST_ONE = function()
    if not achWon() then return false end
    local standing = achStanding()
    return standing == 1
end
