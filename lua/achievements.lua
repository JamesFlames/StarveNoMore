-- achievements.lua — the unlock engine and the cross-game vault.
--
-- The roster (names, descriptions, categories, icons) is AUTO-GENERATED into
-- lua/achievement_data.lua from content/achievements.csv. The unlock
-- CONDITIONS are hand-written predicates in lua/achievement_rules.lua. This
-- file is the machinery between them: when to evaluate, what to remember, and
-- how a player carries a vault from one table to the next.
--
-- WHY A VAULT AND NOT STEAM: a Tabletop Simulator Workshop mod runs inside
-- someone else's Steam app. It has no appid of its own and no Steamworks
-- surface, so it cannot set a real Steam achievement, and it cannot write a
-- file to disk. The two stores it DOES have are the mod's own saved script
-- state (onSave/onLoad in global.lua — survives Save & Play and every
-- autosave) and the clipboard. So: the vault lives in gameState.achievements,
-- it is deliberately NOT cleared by Restart, and exportAchievementCode gives
-- the player a paste-able string that reconstitutes it anywhere.
-- content/achievements.csv is simultaneously the Steamworks manifest source
-- (steam/achievements.json) for the day this ships as its own app —
-- docs/achievements.md has the whole story.

-----------------------------------------------------------------------
-- The vault
-----------------------------------------------------------------------
-- gameState.achievements = {
--   unlocked = { [id] = { day = <game day>, at = <os.time>, game = <n> } },
--   games    = <how many games this table has finished>,
-- }
-- Lazily created so a save from before achievements existed loads clean.
function ensureAchievementVault()
    local gs = gameState
    gs.achievements = gs.achievements or {}
    gs.achievements.unlocked = gs.achievements.unlocked or {}
    gs.achievements.games = gs.achievements.games or 0
    return gs.achievements
end

function isAchievementUnlocked(id)
    return ensureAchievementVault().unlocked[id] ~= nil
end

function unlockedAchievementCount()
    local n = 0
    for _ in pairs(ensureAchievementVault().unlocked) do n = n + 1 end
    return n
end

function totalAchievementCount()
    return #ACHIEVEMENT_ORDER
end

-----------------------------------------------------------------------
-- Unlocking
-----------------------------------------------------------------------
-- `silent` is for import/restore, which must not fire 20 toasts at once.
function unlockAchievement(id, silent)
    local meta = ACHIEVEMENTS[id]
    if not meta then return false end
    local vault = ensureAchievementVault()
    if vault.unlocked[id] then return false end

    vault.unlocked[id] = {
        day  = gameState.day,
        at   = os.time(),
        game = vault.games,
    }

    if not silent then
        broadcastEvent("gain", "ACHIEVEMENT UNLOCKED — " .. meta.name .. ": " .. meta.description)
        safecall(function() Audio.playChime() end, "Audio")
        safecall(function() showAchievementToast(id) end, "AchToast")
        safecall(function() refreshAchievementPanel() end, "AchPanel")
    end
    return true
end

-----------------------------------------------------------------------
-- Evaluation
--
-- Every predicate reads gameState and the chronicle, so there is nothing to
-- hook per-achievement: the whole roster is re-tested at a handful of
-- checkpoints (end of a player's turn, end of day, a boss kill, game over).
-- 24 table reads is cheaper than 24 call sites to keep in sync, and it means
-- a new achievement needs a CSV row and a predicate — nothing else.
--
-- A predicate that throws must never break the game it is watching, hence the
-- pcall: a broken rule costs its own achievement and nothing more.
-----------------------------------------------------------------------
function checkAchievements(reason)
    if not ACHIEVEMENT_ORDER then return 0 end
    local vault = ensureAchievementVault()
    local unlocked = 0
    for _, id in ipairs(ACHIEVEMENT_ORDER) do
        if not vault.unlocked[id] then
            local rule = ACHIEVEMENT_RULES[id]
            if rule then
                local ok, earned = pcall(rule)
                if ok and earned then
                    if unlockAchievement(id) then unlocked = unlocked + 1 end
                end
            end
        end
    end
    return unlocked
end

-- Called once per finished game (win or lose), from showWeekInReview. That
-- can fire more than once for the same game — checkDefeat runs from both
-- checkDownState and resolveTick, and a wipe satisfies it twice — so the
-- count is gated on a per-game flag rather than on the call site.
function recordGameFinished()
    if gameState.gameCounted then return false end
    gameState.gameCounted = true
    local vault = ensureAchievementVault()
    vault.games = (vault.games or 0) + 1
    return true
end

-----------------------------------------------------------------------
-- Carrying the vault between tables
--
-- Format: "SNM-ACH-1:<id>,<id>,..." — ids, not a bitfield, so a code stays
-- readable and keeps working when the roster is reordered. Long, but it is
-- pasted once and never typed.
-----------------------------------------------------------------------
ACHIEVEMENT_CODE_PREFIX = "SNM-ACH-1:"

function exportAchievementCode()
    local ids = {}
    for _, id in ipairs(ACHIEVEMENT_ORDER) do
        if isAchievementUnlocked(id) then table.insert(ids, id) end
    end
    return ACHIEVEMENT_CODE_PREFIX .. table.concat(ids, ",")
end

-- Returns imported, skipped, error-message.
function importAchievementCode(code)
    code = tostring(code or ""):gsub("%s", "")
    if code == "" then return 0, 0, "Paste a code first." end
    if code:sub(1, #ACHIEVEMENT_CODE_PREFIX) ~= ACHIEVEMENT_CODE_PREFIX then
        return 0, 0, "That is not a Starve No More achievement code (it should start with " ..
            ACHIEVEMENT_CODE_PREFIX .. ")."
    end

    local body = code:sub(#ACHIEVEMENT_CODE_PREFIX + 1)
    local imported, skipped = 0, 0
    for id in body:gmatch("[^,]+") do
        if ACHIEVEMENTS[id] then
            if unlockAchievement(id, true) then imported = imported + 1 else skipped = skipped + 1 end
        else
            skipped = skipped + 1
        end
    end
    safecall(function() refreshAchievementPanel() end, "AchPanel")
    return imported, skipped, nil
end
