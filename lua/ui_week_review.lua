-- ui_week_review.lua — the campaign chronicle and the Week in Review panel.
--
-- Split out of ui_controls.lua when it passed the ~500-line budget. It is a
-- coherent subsystem: small hooks at sites that already fire (cook, kill,
-- Charlie, Down, revive, day-end) accumulate a record that outlives dayLog,
-- and showWeekInReview narrates it back at game end.
--
-- Design §16.5. The Review is not a report — it is the replayability engine.
-- The Closing Notes define this design's success test as a group that loses on
-- Day 6, immediately resets, and starts over. This panel is the exact moment
-- that either happens or doesn't, which is why it ends on the MARGIN (how
-- close it was) and a HOOK (one concrete thing to try next), not on statistics.

-----------------------------------------------------------------------
-- Week in Review chronicle (design_batch1.md §3)
-- A persistent record across the whole campaign — dayLog is wiped each
-- Dawn, the chronicle is not. Accumulated by small hooks at sites that
-- already fire (cook, kill, Charlie, Down, revive, day-end), narrated
-- back at game end by showWeekInReview().
-----------------------------------------------------------------------
function ensureChronicle()
    -- Lazy init: saves from before the chronicle existed load cleanly.
    if not gameState.chronicle then
        gameState.chronicle = {
            days = {}, meals = {}, kills = {},
            peakDoom = { value = 0, day = 0 },
            maxCharlieStreak = { value = 0, name = "" },
            downs = 0, revives = 0,
            setup = {}, turns = {}, usage = {},
            beats = { pressKills = 0, signaturesUsed = {}, sourceSplit = false, daresTaken = 0 },
        }
    end
    return gameState.chronicle
end

local BOSS_NAME_PATTERNS = { "deerclops", "eye of terror", "eyeofterror", "source", "treeguard" }

function recordKillInChronicle(threatName, colors)
    local ch = ensureChronicle()
    local who = {}
    for _, color in ipairs(colors or {}) do
        local c = gameState.activeChars[color]
        if c then table.insert(who, c.name) end
    end
    local lower = string.lower(threatName or "")
    local isBoss = false
    for _, p in ipairs(BOSS_NAME_PATTERNS) do
        if string.find(lower, p, 1, true) then isBoss = true break end
    end
    table.insert(ch.kills, { who = table.concat(who, " & "), threat = threatName or "?",
                             day = gameState.day, boss = isBoss })
end

function recordMealInChronicle(cookName)
    local ch = ensureChronicle()
    ch.meals[cookName] = (ch.meals[cookName] or 0) + 1
end

function recordCharlieInChronicle(charName, streak)
    local ch = ensureChronicle()
    if streak > ch.maxCharlieStreak.value then
        ch.maxCharlieStreak.value = streak
        ch.maxCharlieStreak.name = charName
    end
end

-- Called at day end (from showEndOfDaySummary), while the day's dayLog is
-- still intact — BeginDay wipes it at the next Dawn.
function recordDayInChronicle()
    local ch = ensureChronicle()
    local day = gameState.day

    local damageCount = 0
    local headline = nil
    for _, e in ipairs(gameState.dayLog or {}) do
        if e.category == "damage" then
            damageCount = damageCount + 1
            -- Headline precedence 1: somebody fell tonight.
            if not headline and (e.message:find("is DOWN") or e.message:find("is LOST")) then
                headline = e.message
            end
        end
    end
    -- Precedence 2: a boss fell today.
    if not headline then
        for _, k in ipairs(ch.kills) do
            if k.day == day and k.boss then
                headline = "The " .. k.threat .. " fell to " .. k.who .. "."
                break
            end
        end
    end
    -- Precedence 3: a bruising day / a quiet one.
    if not headline then
        if damageCount >= 4 then headline = "A bruising day — the neighborhood bit back " .. damageCount .. " times."
        elseif damageCount > 0 then headline = "The team took some knocks and kept moving."
        else headline = "A quiet day. Nobody trusted it." end
    end

    ch.days[day] = { headline = headline, damageTonight = damageCount }
    if gameState.doom > ch.peakDoom.value then
        ch.peakDoom.value = gameState.doom
        ch.peakDoom.day = day
    end
end

-----------------------------------------------------------------------
-- THE MARGIN (§16.5) — how close it was, in one line.
--
-- [PrinciplesOfGoodBoardGames.md §25]: near-misses drive replay far more
-- strongly than comfortable wins, and "a results ritual that reveals how
-- near the margin was converts a loss into a rematch." The Review narrated
-- the week beautifully and then stopped. The Closing Notes define this
-- design's success test as a group that "loses on Day 6 to the Eye of
-- Terror, immediately resets, and starts over" — the Review is the exact
-- moment that either happens or doesn't.
--
-- Every number here is already tracked. Nothing new is recorded at the
-- table, which is the §16.5 constraint.
-----------------------------------------------------------------------
function weekMarginLines()
    local out = {}
    local limit = getDoomLimit()
    local doomGap = limit - (gameState.doom or 0)
    local cause = gameState.gameOverCause

    if cause == "defeat_doom" then
        local ch = ensureChronicle()
        table.insert(out, "THE MARGIN: the Doom track ran out on Day " ..
            (gameState.day or "?") .. ". You had " .. (#ch.kills) ..
            " kill(s) behind you and " .. (ch.revives or 0) .. " revival(s).")
    elseif cause == "defeat_all_down" then
        table.insert(out, "THE MARGIN: everyone fell at once on Day " .. (gameState.day or "?") ..
            " — with Doom still " .. doomGap .. " short of the end. The clock wasn't what beat you.")
    elseif cause == "defeat_source" then
        local hp = (gameState.bossHP or {}).source
        if hp and hp > 0 and hp < getSourceMaxHP() then
            table.insert(out, "THE MARGIN: The Source had " .. hp ..
                " HP left. " .. hp .. " more damage and the week was yours.")
        else
            table.insert(out, "THE MARGIN: The Source was never brought down. It ended the week standing.")
        end
    else  -- victory
        table.insert(out, "THE MARGIN: you finished " .. doomGap ..
            " Doom from the end of the track.")
        if doomGap <= 3 then
            table.insert(out, "That is as close as it gets. Nobody at that table breathed on Day 7.")
        end
    end

    -- How close the OTHER failure was, whichever one didn't get you.
    local standing, total = 0, 0
    for _, char in pairs(gameState.activeChars) do
        total = total + 1
        if not char.down then standing = standing + 1 end
    end
    if total > 0 and cause ~= "defeat_all_down" then
        if standing == 1 then
            table.insert(out, "One of you was still on their feet. Exactly one.")
        elseif standing > 0 then
            table.insert(out, standing .. " of " .. total .. " still standing at the end.")
        end
    end
    return out
end

-----------------------------------------------------------------------
-- THE HOOK (§16.5) — one concrete suggestion for the next game, drawn
-- from what actually went wrong this one. Ordered by how badly each
-- failure bit, so the table is handed the biggest lever, not a list.
-----------------------------------------------------------------------
function weekReviewHook()
    local ch = ensureChronicle()
    local cause = gameState.gameOverCause
    local roster = {}
    for _, char in pairs(gameState.activeChars) do roster[char.name] = true end

    -- Lost nights to the dark? Charlie is the most fixable death in the game.
    if (ch.maxCharlieStreak.value or 0) >= 2 then
        if not roster.Coco then
            return "NEXT TIME: you lost " .. ch.maxCharlieStreak.value ..
                " nights running to the dark. Try Coco — she never triggers Charlie — or make a Flashlight and a spare Battery the first thing you craft."
        end
        return "NEXT TIME: " .. ch.maxCharlieStreak.name .. " spent " ..
            ch.maxCharlieStreak.value ..
            " nights running in the dark, and Charlie hits harder every one of them. Light is a week-long plan, not a nightly decision."
    end

    if cause == "defeat_source" then
        return "NEXT TIME: the Source is not optional and it arrives on Day 6. Bank Sanity for Press the Attack, and be standing on its tile the morning it lands."
    end

    if cause == "defeat_doom" then
        return "NEXT TIME: most of the Doom you took was for messes left standing overnight. Finish fights, and spend an action on Cleanse before the track reaches 20 rather than after."
    end

    if (ch.downs or 0) >= 2 then
        return "NEXT TIME: " .. ch.downs .. " of you went down. A Telltale Heart costs the cook 2 Health and is the team's only insurance — cook one early, while somebody can spare the Health."
    end

    -- Won comfortably: hand them a harder question rather than a fix.
    if cause == "victory" then
        local diff = getDifficulty()
        if (diff.label or "") == "Story" then
            return "NEXT TIME: you held it together. Try Standard — same seven days, a tighter Doom track and a Source with more in it."
        end
        if (diff.label or "") == "Long Weekend" then
            return "NEXT TIME: that was the short game. Play the full week — the Eye of Terror and The Source are the parts you haven't met."
        end
        return "NEXT TIME: try a Scenario, or a different three at the table. The week plays differently when nobody can cook."
    end

    return "NEXT TIME: swap one character. The week is a different problem with a different five at the table."
end

function showWeekInReview()
    -- The game can end before the day-end summary fires (victory/defeat are
    -- checked first in resolveTick) — chronicle the final day now. Safe to
    -- call twice: it overwrites the same day's entry.
    safecall(function() recordDayInChronicle() end, "Chronicle")

    local ch = ensureChronicle()
    local lines = {}

    for day = 1, 7 do
        local d = ch.days[day]
        if d then table.insert(lines, "Day " .. day .. " — " .. d.headline) end
    end
    if #lines > 0 then table.insert(lines, "") end

    -- The darkest night: most damage entries in one day.
    local worstDay, worstDmg = nil, 0
    for day, d in pairs(ch.days) do
        if d.damageTonight > worstDmg then worstDay, worstDmg = day, d.damageTonight end
    end
    if worstDay then
        table.insert(lines, "Darkest night: Day " .. worstDay .. " (" .. worstDmg .. " wounds and frights)")
    end

    -- Best kill: prefer a boss, else the last kill.
    local best = nil
    for _, k in ipairs(ch.kills) do
        if k.boss then best = k break end
    end
    if not best and #ch.kills > 0 then best = ch.kills[#ch.kills] end
    if best then
        table.insert(lines, "Best kill: " .. best.threat .. " — " .. best.who .. " (Day " .. best.day .. ")")
    end
    table.insert(lines, "Threats defeated: " .. #ch.kills)

    -- Camp mother: most meals cooked.
    local cook, meals = nil, 0
    for name, n in pairs(ch.meals) do
        if n > meals then cook, meals = name, n end
    end
    if cook then table.insert(lines, "Kept everyone fed: " .. cook .. " (" .. meals .. " meals)") end

    if ch.maxCharlieStreak.value > 0 then
        table.insert(lines, "Held the line in the dark: " .. ch.maxCharlieStreak.name ..
            " (" .. ch.maxCharlieStreak.value .. " night(s) of Charlie)")
    end
    table.insert(lines, "Doom high-water mark: " .. ch.peakDoom.value .. " / " .. getDoomLimit() .. " (Day " .. ch.peakDoom.day .. ")")
    if ch.downs > 0 then
        table.insert(lines, "The fallen: " .. ch.downs .. " down" .. (ch.revives > 0 and (" — " .. ch.revives .. " brought back") or ""))
    else
        table.insert(lines, "Nobody fell. Not once.")
    end

    -- The margin and the hook (§16.5). Everything above narrates the week;
    -- these two lines are what turn a loss into a rematch. Both are computed
    -- from data already tracked — nothing new is recorded at the table.
    table.insert(lines, "")
    for _, l in ipairs(weekMarginLines()) do table.insert(lines, l) end
    local hook = weekReviewHook()
    if hook then
        table.insert(lines, "")
        table.insert(lines, hook)
    end

    local title = (gameState.gameOverCause == "victory") and "THE WEEK YOU SURVIVED" or "THE WEEK THAT TOOK YOU"
    local body = table.concat(lines, "\n")
    broadcastEvent("phase", "=== WEEK IN REVIEW ===")
    for _, l in ipairs(lines) do
        if l ~= "" then broadcastEvent("proc", l) end
    end

    if UI then
        UI.setAttribute("weekReviewTitle", "text", title)
        UI.setAttribute("weekReviewBody", "text", body)
        UI.show("weekReviewPanel")
    end
end

function onWeekReviewClose(player, value, id)
    UI.hide("weekReviewPanel")
end
