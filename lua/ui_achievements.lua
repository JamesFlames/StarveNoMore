-- ui_achievements.lua — the Achievements panel and the unlock toast.
--
-- Layout lives in xml/achievements.xml (8 fixed rows, paged). This file fills
-- those rows from ACHIEVEMENT_ORDER / ACHIEVEMENTS (generated from
-- content/achievements.csv) and the vault in achievements.lua.
--
-- Paged rather than scrolled: a TTS Text clips silently, so a list longer
-- than the panel would simply lose its tail with no visual clue — the same
-- reason ui_help_pages.lua exists.

ACH_ROWS_PER_PAGE = 8

-- Current page of the panel (1-based) and whether it is open. Not gameState:
-- both are view state, and should not ride along in every save.
achievementsPage = 1
achievementsPanelOpen = false

function achievementsPageCount()
    local total = totalAchievementCount()
    return math.max(1, math.ceil(total / ACH_ROWS_PER_PAGE))
end

-- What a row should say. A hidden achievement keeps its secret until it is
-- earned: the roster still shows the slot (so the count adds up and nobody
-- wonders whether the panel is broken), but not what fills it.
function achievementRowText(id)
    local meta = ACHIEVEMENTS[id]
    if not meta then return "", "", "" end
    local unlocked = isAchievementUnlocked(id)
    if not unlocked and meta.hidden then
        return "??? (" .. meta.category .. ")",
               "A secret one. You will know it when it happens.",
               "Locked"
    end
    local status = "Locked"
    if unlocked then
        local rec = ensureAchievementVault().unlocked[id] or {}
        status = rec.day and ("Unlocked — Day " .. tostring(rec.day)) or "Unlocked"
    end
    return meta.name .. "  (" .. meta.category .. ")", meta.description, status
end

function refreshAchievementPanel()
    if not UI then return end

    local total = totalAchievementCount()
    local pages = achievementsPageCount()
    if achievementsPage > pages then achievementsPage = pages end
    if achievementsPage < 1 then achievementsPage = 1 end

    UI.setAttribute("achievementsProgress", "text",
        unlockedAchievementCount() .. " of " .. total .. " unlocked" ..
        "   |   games finished at this table: " .. (ensureAchievementVault().games or 0))
    UI.setAttribute("achPageLabel", "text", "Page " .. achievementsPage .. " of " .. pages)
    UI.setAttribute("achPrev", "active", achievementsPage > 1 and "true" or "false")
    UI.setAttribute("achNext", "active", achievementsPage < pages and "true" or "false")

    local first = (achievementsPage - 1) * ACH_ROWS_PER_PAGE
    for row = 1, ACH_ROWS_PER_PAGE do
        local id = ACHIEVEMENT_ORDER[first + row]
        if id then
            local name, desc, status = achievementRowText(id)
            local unlocked = isAchievementUnlocked(id)
            UI.setAttribute("achRow_" .. row, "active", "true")
            UI.setAttribute("achName_" .. row, "text", name)
            UI.setAttribute("achDesc_" .. row, "text", desc)
            UI.setAttribute("achStatus_" .. row, "text", status)
            UI.setAttribute("achName_" .. row, "color", unlocked and "#FFE0A0" or "#7A7268")
            UI.setAttribute("achStatus_" .. row, "color", unlocked and "#88DD88" or "#665C50")
            UI.setAttribute("achIcon_" .. row, "image", ACHIEVEMENTS[id].icon or "ach_locked")
            -- Locked icons are tinted down, not swapped for a grey copy: the
            -- silhouette of what you have not done yet stays on the wall.
            UI.setAttribute("achIcon_" .. row, "color",
                unlocked and "#FFFFFFFF" or "#4A4A4AFF")
        else
            UI.setAttribute("achRow_" .. row, "active", "false")
        end
    end
end

function onAchievementsClick(player, value, id)
    achievementsPanelOpen = not achievementsPanelOpen
    if achievementsPanelOpen then
        -- Opening is a natural checkpoint: anything earned since the last one
        -- should already be on the wall by the time the player looks at it.
        safecall(function() checkAchievements("panel") end, "Achievements")
        refreshAchievementPanel()
        UI.show("achievementsPanel")
    else
        UI.hide("achievementsPanel")
    end
end

function onAchievementsClose(player, value, id)
    achievementsPanelOpen = false
    UI.hide("achievementsPanel")
end

function onAchievementsPrev(player, value, id)
    achievementsPage = math.max(1, achievementsPage - 1)
    refreshAchievementPanel()
end

function onAchievementsNext(player, value, id)
    achievementsPage = math.min(achievementsPageCount(), achievementsPage + 1)
    refreshAchievementPanel()
end

-----------------------------------------------------------------------
-- Carrying the vault between tables.
--
-- Same trick the session-log export uses: the Notes panel holds arbitrary
-- text and survives chat scroll, so it is the one place in TTS a player can
-- reliably copy a long string out of.
-----------------------------------------------------------------------
function onAchievementsCopyCode(player, value, id)
    local code = nil
    safecall(function() code = exportAchievementCode() end, "Achievements")
    if not code then
        broadcastToColor("Could not build the achievement code.", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function() Notes.setNotes(code) end, "Achievements")
    broadcastEvent("proc", "Achievement code written to the Notes panel (top menu > Notes) — " ..
        unlockedAchievementCount() .. " unlock(s). Copy it out to carry them to another table.")
end

function onAchievementsImportCode(player, value, id)
    local imported, skipped, err = importAchievementCode(value)
    if err then
        broadcastToColor(err, player and player.color or "White", BROADCAST_COLORS.damage)
        return
    end
    UI.setAttribute("achCodeInput", "text", "")
    if imported > 0 then
        broadcastEvent("gain", "Achievement code accepted — " .. imported ..
            " unlock(s) restored" .. (skipped > 0 and (", " .. skipped .. " already held or unknown") or "") .. ".")
    else
        broadcastEvent("proc", "That code held nothing this table did not already have.")
    end
    refreshAchievementPanel()
end

-----------------------------------------------------------------------
-- The toast — one at a time, bottom right, the way Steam's does it.
-- A week can unlock several at once (game over fires most of them), so
-- they queue instead of overwriting each other.
-----------------------------------------------------------------------
achToastQueue = {}
achToastShowing = false
ACH_TOAST_SECONDS = 5

function showAchievementToast(id)
    if not ACHIEVEMENTS[id] then return end
    table.insert(achToastQueue, id)
    if not achToastShowing then popAchievementToast() end
end

function popAchievementToast()
    -- popFirst, not table.remove(q, 1): every toast schedules one more call of
    -- this function to clear itself, so the last of a run always lands here on
    -- an EMPTY queue — where table.remove throws in TTS but not in real Lua.
    -- That is why the game logged an error every time an achievement fired and
    -- the suite stayed green. See helpers.lua.
    local id = popFirst(achToastQueue)
    if not id then
        achToastShowing = false
        if UI then UI.hide("achToast") end
        return
    end
    local meta = ACHIEVEMENTS[id]
    achToastShowing = true
    -- Hide UI means hide UI: a toast must not reappear over the standard TTS
    -- controls somebody deliberately cleared the screen to reach. The unlock
    -- is already banked and already in the chat log either way.
    if UI and not customUIHidden then
        UI.setAttribute("achToastIcon", "image", meta.icon or "ach_locked")
        UI.setAttribute("achToastName", "text", meta.name)
        UI.setAttribute("achToastDesc", "text", meta.description)
        UI.show("achToast")
    end
    Wait.time(function()
        safecall(function() popAchievementToast() end, "AchToast")
    end, ACH_TOAST_SECONDS)
end
