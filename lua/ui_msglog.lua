-- ui_msglog.lua — persistent on-screen Message Log.
--
-- TTS broadcast text fades after a few seconds and renders top-centre,
-- straight behind the Phase Banner — playtest: "messages disappear before
-- I can read them". Every public broadcastEvent is therefore also kept in
-- gameState.messageLog (persists through save/load) and rendered in the
-- msgLog panel, which stays until the player clears or hides it.
-- The "Log" button on the Phase Banner reopens it.

MSGLOG_MAX = 40          -- entries kept in gameState.messageLog
MSGLOG_SHOW_LINES = 9    -- newest entries rendered in the panel

-- Panel line colours per broadcastEvent category (readable-on-black
-- versions of BROADCAST_COLORS).
local MSGLOG_COLORS = {
    damage = "#FF9999",
    warn   = "#FFDD88",
    gain   = "#99FF99",
    phase  = "#88DDFF",
    proc   = "#BBBBBB",
}

-- Called from broadcastEvent (global.lua) for every public message.
function logMessage(category, message)
    if not gameState then return end
    gameState.messageLog = gameState.messageLog or {}
    table.insert(gameState.messageLog, {
        c = category,
        m = tostring(message),
        day = gameState.day,
    })
    -- popFirst rather than table.remove(log, 1). The `while` above already
    -- guarantees a non-empty list, so this one was never going to throw — but
    -- the rule is absolute on purpose. "table.remove(t, 1) is fine here
    -- because of the surrounding loop" is a judgement call re-made at every
    -- call site, and it is the one that got the achievement toast wrong.
    while #gameState.messageLog > MSGLOG_MAX do
        popFirst(gameState.messageLog)
    end
    refreshMsgLog()
end

function refreshMsgLog()
    if not UI then return end
    if customUIHidden then return end
    local log = (gameState and gameState.messageLog) or {}
    local lines = {}
    for i = math.max(1, #log - MSGLOG_SHOW_LINES + 1), #log do
        local e = log[i]
        local col = MSGLOG_COLORS[e.c] or "#CCCCCC"
        lines[#lines + 1] = "<color=" .. col .. ">" .. e.m .. "</color>"
    end
    UI.setAttribute("msgLogBody", "text", table.concat(lines, "\n"))
    -- New content reopens the panel unless the player explicitly hid it.
    if not gameState.msgLogHidden and #log > 0 then
        UI.show("msgLog")
    end
end

function onMsgLogToggle(player, value, id)
    gameState.msgLogHidden = not gameState.msgLogHidden
    if gameState.msgLogHidden then
        UI.hide("msgLog")
    else
        refreshMsgLog()
        UI.show("msgLog")
    end
end

function onMsgLogClear(player, value, id)
    gameState.messageLog = {}
    if UI then UI.setAttribute("msgLogBody", "text", "") end
end

function onMsgLogHide(player, value, id)
    gameState.msgLogHidden = true
    UI.hide("msgLog")
end
