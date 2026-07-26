-- actions_social.lua — the remaining action verbs: trade, energy drink,
-- eat-raw, pass, barricade, defend, peek, rally, pry, and stabilize.
-- Part of actions (see actions.lua for move/gather/rest + undo).

-----------------------------------------------------------------------
-- TRADE (free once/turn at same location, costs 1 action otherwise)
-----------------------------------------------------------------------
function doTrade(color, targetColor)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Check if target is at the same location
    local target = targetColor and gameState.activeChars[targetColor]
    local sameLocation = true
    if target then
        sameLocation = (char.location == target.location)
    end

    -- Track free trades per turn (1 free trade per turn at same location)
    gameState.tradesThisTurn = gameState.tradesThisTurn or {}
    local tradeCount = gameState.tradesThisTurn[color] or 0

    if not sameLocation then
        -- Different location: costs 1 action
        if not spendAction(color, "Trade (remote)") then return end
        broadcastEvent("proc", char.name .. " spends an action to trade with a player at a different location.")
    elseif tradeCount >= 1 then
        -- Same location but already used free trade: costs 1 action
        if not spendAction(color, "Trade (extra)") then return end
        broadcastEvent("proc", char.name .. " spends an action for an additional trade this turn.")
    else
        -- Free trade (first one this turn, same location)
        gameState.tradesThisTurn[color] = tradeCount + 1
        broadcastEvent("proc", char.name .. " trades for free (1 per turn at same location).")
    end

    broadcastEvent("proc", "Players at " .. (char.location or "?") ..
        " may exchange resources and items now.")
    safecall(function() Audio.playTradeChat() end, "Audio")
end

-----------------------------------------------------------------------
-- USE ENERGY DRINK (free action, James-specific)
-----------------------------------------------------------------------
function doEnergyDrink(color)
    local char = gameState.activeChars[color]
    if not char then return end

    if char.name ~= "James" then
        broadcastEvent("proc", char.name .. " uses an Energy Drink. +2 Sanity.")
    else
        broadcastEvent("proc", "James uses an Energy Drink. +2 Sanity. Addiction satisfied for today.")
        gameState.jamesEnergyDrinkUsed = true
    end

    char.sanity = math.min(char.maxSanity, char.sanity + 2)
    broadcastEvent("gain", char.name .. " gains +2 Sanity from Energy Drink. (Now " .. char.sanity .. ")")
end

-----------------------------------------------------------------------
-- EAT RAW FOOD (free action) — Design §8.4
-- +1 Hunger, -1 Sanity (mismatched currency)
-----------------------------------------------------------------------
function doEatRaw(color)
    local char = gameState.activeChars[color]
    if not char or char.down then return end

    -- Particular Eater (§6.4): Ellie cannot eat raw food, ever.
    if char.name == "Ellie" then
        broadcastToColor("Ellie can't eat raw food (Particular Eater). Cook it first — Crockpot Master makes recipes cheaper.",
            color, BROADCAST_COLORS.damage)
        return
    end

    char.hunger = math.min(char.maxHunger, char.hunger + 1)
    char.sanity = math.max(0, char.sanity - 1)

    broadcastEvent("proc", char.name .. " eats raw food. +1 Hunger, -1 Sanity.")
    checkDownState(color)
end

-----------------------------------------------------------------------
-- PASS (end turn voluntarily)
-----------------------------------------------------------------------
function doPass(color)
    local char = gameState.activeChars[color]
    if not char then return end

    broadcastEvent("proc", char.name .. " passes. Turn over.")
    endPlayerTurn(color)
end

-----------------------------------------------------------------------
-- BARRICADE (1 action, costs 1 Wood) — Improvement: reduces night threats
-- Spend 1 Wood to barricade a location. That location draws -1 Threat tonight.
-- Barricade is consumed after one night.
-----------------------------------------------------------------------
function doBarricade(color)
    if not spendAction(color, "Barricade") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Auto-verify and pay the 1 Wood; refund the action if unaffordable.
    if not verifyAndPayResources(color, {Wood=1}, "the Barricade") then
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    local loc = char.location or ""

    -- Track barricades per location
    gameState.barricades = gameState.barricades or {}
    gameState.barricades[loc] = (gameState.barricades[loc] or 0) + 1

    broadcastEvent("gain", char.name .. " barricades " .. loc .. "! (-1 Threat draw tonight)")
end

-----------------------------------------------------------------------
-- DEFEND (Rayman special — 1 action)
-- Redirects all return damage to Rayman for one combat round
-----------------------------------------------------------------------
function doDefend(color)
    if not spendAction(color, "Defend") then return end

    local char = gameState.activeChars[color]
    if not char or char.name ~= "Rayman" then
        broadcastEvent("damage", "Only Rayman can Defend.")
        char.actionsLeft = char.actionsLeft + 1  -- refund
        return
    end

    gameState.raymanDefending = true
    broadcastEvent("gain", "Rayman DEFENDS (Backboard Block)! Counter-attack damage is redirected to him until his next turn.")
end

-----------------------------------------------------------------------
-- PATTERN RECOGNITION (James, free action, once per day) — Design §6.1
-- Peek at the top card of any deck; the name goes to James alone.
-----------------------------------------------------------------------
PEEK_DECKS = {
    Phase   = { label = "Dawn deck",  get = function() return getPhaseDeck(gameState.phase) end },
    Threat  = { label = "Threat deck",  get = getThreatDeck },
    Market  = { label = "Market deck",  get = getMarketDeck },
    Visitor = { label = "Visitor deck", get = getVisitorDeck },
}

function canPeek(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.name ~= "James" then return false, "Only James reads the patterns." end
    if char.down then return false, "You are Down." end
    if gameState.jamesPeekUsed then return false, "Pattern Recognition is spent for today." end
    return true, nil
end

function doPeek(color, deckKey)
    local ok, why = canPeek(color)
    if not ok then
        broadcastToColor(why or "Can't peek right now.", color, BROADCAST_COLORS.damage)
        return false
    end
    local entry = PEEK_DECKS[deckKey]
    local deck = entry and entry.get()
    if not deck or not deck.getObjects or (deck.getQuantity and deck.getQuantity() or 0) <= 0 then
        broadcastToColor("That deck is empty (or missing).", color, BROADCAST_COLORS.damage)
        return false
    end
    local top = deck.getObjects()[1]
    local name = top and ((top.nickname ~= "" and top.nickname) or top.name) or "???"
    -- Show the card, not just its title: the description is the card's rules
    -- text, so the peeker actually learns what is coming.
    local text = (top and top.description) or ""
    gameState.jamesPeekUsed = true
    broadcastEvent("proc", "James studies the " .. entry.label .. "... Pattern Recognition (free action, once per day).")
    broadcastToColor("Top of the " .. entry.label .. ": " .. name
        .. (text ~= "" and ("\n" .. text) or "")
        .. "\nTell the team — or don't.", color, BROADCAST_COLORS.gain)
    return true
end

-----------------------------------------------------------------------
-- RALLY (Luca, free, once per turn) — Design §6.5
-- Give an ally at Luca's tile or an adjacent one a free non-movement
-- action: +1 to their action pool for this Day. (The "non-movement" part
-- is a table rule — the script can't earmark a specific future action.)
-----------------------------------------------------------------------
function canRally(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.name ~= "Luca" then return false, "Only Luca can Rally." end
    if char.down then return false, "You are Down." end
    if gameState.lucaRallyUsed then return false, "Rally is spent for this turn." end
    if #rallyTargets(color) == 0 then
        return false, "No ally nearby who can still act (same or adjacent tile, actions remaining)."
    end
    return true, nil
end

-- Allies eligible for Rally: standing, at Luca's tile or adjacent, with
-- actions still in their pool (a finished turn has 0 left — the gift
-- would evaporate).
function rallyTargets(color)
    local out = {}
    local char = gameState.activeChars[color]
    if not char then return out end
    local nearby = { [char.location or ""] = true }
    for _, n in ipairs(LOCATION_ADJACENCY[char.location] or {}) do nearby[n] = true end
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and nearby[ch2.location or ""]
            and (ch2.actionsLeft or 0) > 0 then
            table.insert(out, c2)
        end
    end
    return out
end

function doRally(lucaColor, targetColor)
    local ok, why = canRally(lucaColor)
    if not ok then
        broadcastToColor(why or "Can't Rally right now.", lucaColor, BROADCAST_COLORS.damage)
        return false
    end
    local target = gameState.activeChars[targetColor]
    local luca = gameState.activeChars[lucaColor]
    local valid = false
    for _, c in ipairs(rallyTargets(lucaColor)) do
        if c == targetColor then valid = true break end
    end
    if not target or not valid then
        broadcastToColor("That ally can't be rallied (must be at your tile or adjacent, standing, with actions left).",
            lucaColor, BROADCAST_COLORS.damage)
        return false
    end
    gameState.lucaRallyUsed = true
    target.actionsLeft = target.actionsLeft + 1
    broadcastEvent("gain", "Luca rallies " .. target.name .. " — a free action this Day! (Non-movement: spend it on Gather, Craft, Cook, Rest, Fight... not Move.)")
    return true
end

-----------------------------------------------------------------------
-- PRY (free action, requires a Pry tool) — Design §13.5, design_batch3.md §3
-- The one coded verb behind every sealed thing: sealed Threat cards and
-- the Sealed Basement (a fixed object placed at Ellie & Luca's House by
-- build_save.py). Guaranteed reward behind a tool gate — no dice.
-----------------------------------------------------------------------
PRY_TOOLS = {
    { id = "M_CROWBAR",  label = "Crowbar" },
    { id = "M_LOCKPICK", label = "Lockpick" },
    { id = "M_PRY_BAR",  label = "Pry Bar" },
}

-- Sealed-card rewards live in SEALED_REWARDS (lua/threat_types.lua,
-- AUTO-GENERATED from the `pry_reward` column of cards_threats.csv), so the
-- card face and the delivered reward can never drift apart. The Basement is
-- a placed object, not a card — its entry is authored here.
SEALED_REWARDS.BASEMENT = {
    market = 1, resources = { Food = 2, Wood = 1, Battery = 1 },
    line = "The basement cache, hoarded before the week began: a free Market Item plus 2 Food + 1 Wood + 1 Battery.",
}

local PRY_RADIUS = 7   -- same "at this tile" radius as festering / signatures

-- Which Pry tool (label) does this player hold? Hand + player-board area,
-- the same two places the night light check looks.
function playerPryTool(color)
    local char = gameState.activeChars[color]
    if not char then return nil end
    local candidates = {}
    local ok, handObjs = pcall(function() return Player[color].getHandObjects() end)
    if ok and handObjs then
        for _, o in ipairs(handObjs) do candidates[#candidates + 1] = o end
    end
    local board = getPlayerBoard(char.name)
    if board then
        local pos = board.getPosition()
        local b = board.getBoundsNormalized()
        local pad = 1.5
        for _, obj in ipairs(getAllObjects()) do
            local p = obj.getPosition()
            if p.x >= pos.x - b.size.x * 0.5 - pad and p.x <= pos.x + b.size.x * 0.5 + pad
                and p.z >= pos.z - b.size.z * 0.5 - pad and p.z <= pos.z + b.size.z * 0.5 + pad then
                candidates[#candidates + 1] = obj
            end
        end
    end
    for _, obj in ipairs(candidates) do
        -- pcall per object: this runs from refreshActionButtonStates every
        -- turn, and a candidate handle can be dead (a card just played from
        -- hand, a token mid-sweep) — touching hasTag/getNickname then throws
        -- "cannot access field getNickname of userdata<LuaObject>".
        local matched = nil
        pcall(function()
            for _, tool in ipairs(PRY_TOOLS) do
                if obj.hasTag and obj.hasTag(tool.id) then matched = tool.label; return end
                local nick = safeNickname(obj)
                if nick:lower():find(tool.label:lower(), 1, true) then matched = tool.label; return end
            end
        end)
        if matched then return matched end
    end
    return nil
end

-- Sealed things at this tile: { {obj, id}, ... }. id keys SEALED_REWARDS.
local function _sealedAtTile(locName)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    for _, obj in ipairs(getAllObjects()) do
        local sealedId = nil
        if obj.hasTag then
            if obj.hasTag("SealedBasement") and not gameState.basementOpened then
                sealedId = "BASEMENT"
            else
                for id in pairs(SEALED_REWARDS) do
                    if id ~= "BASEMENT" and obj.hasTag(id) then sealedId = id; break end
                end
            end
        end
        if sealedId then
            local p = obj.getPosition()
            local dx, dz = p.x - tp.x, p.z - tp.z
            if (dx * dx + dz * dz) <= (PRY_RADIUS * PRY_RADIUS) then
                table.insert(out, { obj = obj, id = sealedId })
            end
        end
    end
    return out
end

-- Precondition check; the reason doubles as the why-disabled tooltip.
function canPry(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    if #_sealedAtTile(char.location) == 0 then
        return false, "Nothing sealed at " .. (char.location or "?") .. "."
    end
    local tool = playerPryTool(color)
    if not tool then
        return false, "You need a Crowbar, Lockpick, or Pry Bar (in hand or by your board)."
    end
    return true, tool
end

local function _deliverSealedReward(color, reward, locName)
    if reward.resources then
        local tile = getLocationTile(locName)
        local pos = tile and tile.getPosition()
        local i = 0
        for resType, qty in pairs(reward.resources) do
            local bag = getResourceBag(resType)
            for _ = 1, qty do
                i = i + 1
                if bag and pos then
                    safecall(function()
                        bag.takeObject({ position = { pos.x + (i % 3) * 1.2 - 1.2, pos.y + 3, pos.z + 2 },
                                         smooth = true })
                    end, "PryLoot")
                end
            end
        end
    end
    if reward.market and getMarketDeck() then
        local deck = getMarketDeck()
        if (deck.getQuantity and deck.getQuantity() or 0) > 0 then
            local hz = getHandZone(color)
            local tile = getLocationTile(locName)
            local dest = (hz and hz.getPosition()) or (tile and tile.getPosition()) or Vector(0, 2, 0)
            safecall(function()
                deck.takeObject({
                    position = dest + Vector(0, 2, 0),
                    rotation = {0, 180, 0},
                    smooth = true,
                    callback_function = function(c)
                        -- pcall: the outer safecall wraps takeObject, not this
                        -- async callback; the drawn card's handle can be dead.
                        pcall(function()
                            broadcastEvent("gain", "Sealed away all this time: " .. (c.getNickname() or "an Item") .. " — yours, free.")
                        end)
                    end,
                })
            end, "PryMarket")
        end
    end
    if reward.line then broadcastEvent("gain", reward.line) end
end

function doPry(color)
    local ok, toolOrReason = canPry(color)
    if not ok then
        broadcastToColor(toolOrReason or "Nothing to pry.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    local target = _sealedAtTile(char.location)[1]
    local reward = SEALED_REWARDS[target.id]
    local name = (target.obj.getNickname and target.obj.getNickname() ~= "" and target.obj.getNickname())
        or "the sealed thing"

    broadcastEvent("proc", char.name .. " sets the " .. toolOrReason .. " against " .. name .. "... and it gives. (Pry is a free action.)")
    _deliverSealedReward(color, reward, char.location)

    if target.id == "BASEMENT" then
        gameState.basementOpened = true
    end
    pcall(function() target.obj.destruct() end)
    refreshPhaseBanner()
    return true
end

-----------------------------------------------------------------------
-- STABILIZE (1 action, requires Bandage) — Design §12.3
-----------------------------------------------------------------------
function doStabilize(color, targetColor)
    if not spendAction(color, "Stabilize") then return end

    local char = gameState.activeChars[color]
    local target = gameState.activeChars[targetColor]

    if not target or not target.down then
        broadcastEvent("proc", "Target is not Down.")
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    if char.location ~= target.location then
        broadcastEvent("damage", "Must be at the same location to stabilize.")
        char.actionsLeft = char.actionsLeft + 1
        return
    end

    -- Requires Bandage item (manual check)
    broadcastEvent("proc", char.name .. " stabilizes " .. target.name .. " with a Bandage!")
    target.health = 1
    target.down = false
    broadcastEvent("gain", target.name .. " is stabilized at 1 Health. (Not a full revival.)")
end
