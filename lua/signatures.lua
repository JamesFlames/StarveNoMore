-- signatures.lua  (Design §6.7 — Signature Moves, design_batch2.md §2)
-- One named, once-per-game move per character, each paying a mismatched
-- currency (§8.4). This file owns the whole path: preconditions, the
-- doSignature dispatch, the Signature button handler, and the target-pick
-- UX for Coco (dialog) and Rayman (buttons on threat cards).

SIGNATURES = {
    James  = { name = "All-Nighter",
               desc = "Take 3 extra actions this turn.",
               cost = "The crash: -3 Sanity at the next Tick." },
    Coco   = { name = "Touch of Hope",
               desc = "Heal any character, anywhere on the map, by 4 Health.",
               cost = "Once per game." },
    Rayman = { name = "Posterize",
               desc = "Instantly defeat one non-boss threat at your tile. No roll, no counter.",
               cost = "The noise: +1 Threat draw at this tile tonight." },
    Ellie  = { name = "The Feast",
               desc = "Cook any number of recipes in a single action (ingredients still required).",
               cost = "Consumes ALL the Provisions beside your player board." },
    Luca   = { name = "The Speech",
               desc = "Every character, anywhere, gains +2 Sanity.",
               cost = "Only speakable while an ally is Down or below 3 Sanity." },
}

SIGNATURE_NARRATIONS = {
    James  = "James cracks his knuckles and opens every window at once. He does EVERYTHING. Tomorrow can bill him.",
    Coco   = "Coco closes her eyes and reaches across the whole neighborhood. Somewhere, someone stops bleeding.",
    Rayman = "Rayman rises, hangs in the air a full second, and DUNKS it into the pavement. The whole street heard that.",
    Ellie  = "Ellie empties the pantry into every pot she owns. Tonight, nobody goes hungry.",
    Luca   = "Luca stands up on a chair and starts talking — and for one impossible minute, everyone believes him.",
}

-----------------------------------------------------------------------
-- Helpers
-----------------------------------------------------------------------
local SIG_TILE_RADIUS = 7   -- same "at this tile" radius as festering

-- Loose (non-boss) threat cards sitting at a location tile.
local function threatsAtTile(locName)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        if obj.type == "Card" then
            local p = obj.getPosition()
            local dx, dz = p.x - tp.x, p.z - tp.z
            if (dx * dx + dz * dz) <= (SIG_TILE_RADIUS * SIG_TILE_RADIUS) then
                table.insert(out, obj)
            end
        end
    end
    return out
end

local function speechConditionMet(lucaColor)
    for c, ch in pairs(gameState.activeChars) do
        if c ~= lucaColor and (ch.down or ch.sanity < 3) then return true end
    end
    return false
end

-----------------------------------------------------------------------
-- Precondition check. Returns ok, reason — the reason doubles as the
-- refusal message and the why-disabled tooltip.
-----------------------------------------------------------------------
function canUseSignature(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    local sig = SIGNATURES[char.name]
    if not sig then return false, "No Signature for " .. char.name .. "." end
    if char.signatureUsed then
        return false, sig.name .. " is spent — one per game."
    end
    if char.name == "Rayman" then
        if #threatsAtTile(char.location) == 0 then
            return false, "No threat at " .. (char.location or "?") .. " to Posterize."
        end
    elseif char.name == "Ellie" then
        if char.location ~= "EllieLucaHouse" then
            return false, "The Feast needs the Crockpot — move to Ellie & Luca's House."
        end
        if char.actionsLeft <= 0 then
            return false, "The Feast costs 1 action — none left."
        end
    elseif char.name == "Luca" then
        if not speechConditionMet(color) then
            return false, "The Speech only comes when it matters — an ally must be Down or below 3 Sanity."
        end
    end
    return true
end

-----------------------------------------------------------------------
-- The move itself. arg: target seat color (Coco) or threat card object
-- (Rayman); unused otherwise.
-----------------------------------------------------------------------
function doSignature(color, arg)
    local ok, reason = canUseSignature(color)
    if not ok then
        broadcastToColor(reason or "Signature unavailable.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]

    if char.name == "James" then
        char.actionsLeft = char.actionsLeft + 3
        gameState.pendingSanityPenalty = gameState.pendingSanityPenalty or {}
        gameState.pendingSanityPenalty[color] = 3
        broadcastEvent("gain", "ALL-NIGHTER: James takes 3 extra actions this turn (" ..
            char.actionsLeft .. " remaining). The bill: -3 Sanity at Tick.")

    elseif char.name == "Coco" then
        local target = arg and gameState.activeChars[arg]
        if not target then
            broadcastToColor("Pick a character to heal.", color, BROADCAST_COLORS.damage)
            return false
        end
        if target.down then
            broadcastToColor("Touch of Hope can't reach the Down — they need a Telltale Heart.",
                color, BROADCAST_COLORS.damage)
            return false
        end
        target.health = math.min(target.maxHealth, target.health + 4)
        broadcastEvent("gain", "TOUCH OF HOPE: Coco heals " .. target.name ..
            " by 4 Health (now " .. target.health .. "), across any distance.")

    elseif char.name == "Rayman" then
        local threat = arg
        if not (threat and threat.hasTag and threat.hasTag("ThreatCard")) then
            broadcastToColor("Pick a threat card at your tile to Posterize.", color, BROADCAST_COLORS.damage)
            return false
        end
        local tName = threat.getNickname() or "the threat"
        broadcastEvent("gain", "POSTERIZE: " .. tName .. " is DEFEATED — no roll, no counter. Discarded.")
        safecall(function() recordKillInChronicle(tName, { color }) end, "Chronicle")
        gameState.loudSignature = gameState.loudSignature or {}
        gameState.loudSignature[char.location or ""] = true
        broadcastEvent("warn", "The dunk echoes — +1 Threat draw at " .. (char.location or "?") .. " tonight.")
        pcall(function() threat.destruct() end)

    elseif char.name == "Ellie" then
        if not spendAction(color, "The Feast") then return false end
        local food = (getPlayerResources(color) or {}).Provisions or 0
        if food > 0 then
            verifyAndPayResources(color, { Provisions = food }, "The Feast")
        end
        char.feastActive = true
        broadcastEvent("gain", "THE FEAST: Ellie empties the pantry (" .. food ..
            " Provisions consumed). Until her turn ends, cooking costs no actions — cook every recipe she has ingredients for.")

    elseif char.name == "Luca" then
        for _, ch in pairs(gameState.activeChars) do
            if not ch.down then
                ch.sanity = math.min(ch.maxSanity, ch.sanity + 2)
            end
        end
        broadcastEvent("gain", "THE SPEECH: every survivor, anywhere on the map, gains +2 Sanity.")
    end

    char.signatureUsed = true
    gameState.undoSnapshot = nil   -- a fired one-shot can't be undone
    safecall(function() recordBeat("signature", char.name) end, "Telemetry")
    if SIGNATURE_NARRATIONS[char.name] then
        broadcastEvent("phase", SIGNATURE_NARRATIONS[char.name])
    end
    safecall(function() refreshPhaseBanner() end, "Banner")
    return true
end

-----------------------------------------------------------------------
-- Posterize target buttons (mirrors the Move/Craft click-to-complete
-- pattern in ui_actionbar.lua, tracked separately so a destroyed card
-- never leaves a dangling reference in that file's list).
-----------------------------------------------------------------------
local _posterizeButtons = {}

function clearSignatureTargets()
    for _, obj in ipairs(_posterizeButtons) do
        if obj then pcall(function() obj.clearButtons() end) end
    end
    _posterizeButtons = {}
    local pa = gameState.pendingAction
    if pa and pa.type == "posterize" then gameState.pendingAction = nil end
end

function spawnPosterizeTargets(color)
    clearSignatureTargets()
    local char = gameState.activeChars[color]
    if not char then return end
    local threats = threatsAtTile(char.location)
    if #threats == 0 then
        broadcastToColor("No threat at your tile to Posterize.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.pendingAction = { type = "posterize", color = color }
    for _, tcard in ipairs(threats) do
        tcard.highlightOn("Red", 8)
        tcard.createButton({
            click_function = "onPosterizeTargetClick",
            function_owner  = Global,
            label           = "POSTERIZE",
            position        = { 0, 0.4, 0 },
            rotation        = { 0, 0, 0 },
            width           = 1200,
            height          = 420,
            font_size       = 180,
            color           = { 0.3, 0.08, 0.08, 0.95 },
            font_color      = { 1, 0.8, 0.8 },
            tooltip         = "Dunk " .. (tcard.getNickname() or "this threat") ..
                              " — instantly defeated. The noise draws +1 Threat here tonight.",
        })
        table.insert(_posterizeButtons, tcard)
    end
    broadcastToColor("Click POSTERIZE on a highlighted threat. Click your Signature button again to cancel.",
        color, BROADCAST_COLORS.proc)
end

function onPosterizeTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "posterize") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only Rayman's player may pick the target.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local color = pa.color
    local tName = obj.getNickname() or "this threat"
    showConfirm("Posterize — once per game",
        "Instantly defeat " .. tName .. ".\nThe noise: +1 Threat draw at this tile tonight.",
        function()
            clearSignatureTargets()
            safecall(function() doSignature(color, obj) end, "Signature")
            refreshPhaseBanner()
        end)
end

-----------------------------------------------------------------------
-- Touch of Hope target dialog (mirrors the Trade partner dialog)
-----------------------------------------------------------------------
local SIG_COLORS = { "White", "Red", "Yellow", "Green", "Blue" }

function showSignatureTargetDialog(color)
    local any = false
    for _, c in ipairs(SIG_COLORS) do
        local ch = gameState.activeChars[c]
        local btn = "sigTargetBtn_" .. c
        if ch and not ch.down then
            any = true
            UI.setAttribute(btn, "active", "true")
            setButtonLabel(btn, ch.name .. "  (Health " .. ch.health .. "/" .. ch.maxHealth .. ")")
        else
            UI.setAttribute(btn, "active", "false")
        end
    end
    if not any then
        broadcastToColor("No one standing to heal.", color, BROADCAST_COLORS.damage)
        return
    end
    gameState.pendingAction = { type = "signature_heal", color = color }
    UI.show("signatureTargetDialog")
end

function onSignatureTargetClick(player, value, id)
    UI.hide("signatureTargetDialog")
    local pa = gameState.pendingAction
    if not (pa and pa.type == "signature_heal" and pa.color == player.color) then return end
    gameState.pendingAction = nil
    local target = gameState.activeChars[value]
    if not target then return end
    showConfirm("Touch of Hope — once per game",
        "Heal " .. target.name .. " by 4 Health, across any distance.",
        function()
            safecall(function() doSignature(pa.color, value) end, "Signature")
            refreshPhaseBanner()
        end)
end

function onSignatureCancel(player, value, id)
    UI.hide("signatureTargetDialog")
    local pa = gameState.pendingAction
    if pa and pa.type == "signature_heal" then gameState.pendingAction = nil end
end

-----------------------------------------------------------------------
-- Action-bar Signature button (XML: actSignature)
-----------------------------------------------------------------------
function onActSignature(player, value, id)
    local color = player.color
    if not validateActivePlayer(color) then return end
    local char = gameState.activeChars[color]
    if not char then return end

    -- Clicking Signature again while Posterize targets are up cancels them.
    local pa = gameState.pendingAction
    if pa and pa.color == color and pa.type == "posterize" then
        clearSignatureTargets()
        broadcastToColor("Posterize cancelled — your Signature is still available.", color, BROADCAST_COLORS.proc)
        return
    end

    local ok, reason = canUseSignature(color)
    if not ok then
        broadcastToColor(reason or "Signature unavailable.", color, BROADCAST_COLORS.damage)
        return
    end

    local sig = SIGNATURES[char.name]
    if char.name == "Coco" then
        showSignatureTargetDialog(color)
    elseif char.name == "Rayman" then
        spawnPosterizeTargets(color)
    else
        showConfirm(sig.name .. " — once per game",
            sig.desc .. "\n" .. sig.cost,
            function()
                safecall(function() doSignature(color) end, "Signature")
                refreshPhaseBanner()
            end)
    end
end
