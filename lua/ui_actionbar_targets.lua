-- ui_actionbar_targets.lua — click-to-complete action targets: the 3D
-- target-button plumbing (_spawnTargetButton / clearActionTargets), the
-- per-action spawn helpers (move/craft/cook/fight), their click handlers,
-- and the highlight helpers. Part of ui_actionbar (see ui_actionbar_core).


-----------------------------------------------------------------------
-- Click-to-complete action targets (Move / Craft / Cook).
--
-- Selecting one of these actions spawns a clickable 3D button on every
-- legal target object (tile / market card / recipe card). Clicking the
-- button consumes gameState.pendingAction and calls the matching do*
-- handler. Buttons are cleared when the action completes, is cancelled
-- (click the same action again), the turn ends, or after a timeout.
--
-- Rayman's Speed perk is a chained flow: his Move spawns a second round
-- of FREE MOVE buttons around his new tile (doRaymanBonusMove).
-----------------------------------------------------------------------
local _targetButtonObjs  = {}   -- objects we added buttons to
local _craftSlotByGuid   = {}   -- market card guid -> slot index for doCraft
local _recipeIdByGuid    = {}   -- recipe card guid -> recipe id for doCook
local _targetClearHandle = nil
local TARGET_TIMEOUT = 30       -- seconds before stale target buttons vanish

local function _clearTargetButtons()
    if _targetClearHandle then Wait.stop(_targetClearHandle); _targetClearHandle = nil end
    for _, obj in ipairs(_targetButtonObjs) do
        -- These are tiles and cards a player may have moved, merged or
        -- deleted since the buttons went on. isDestroyed() throws on the
        -- dead handle it is asked about; isLiveObject asks safely.
        if isLiveObject(obj) then
            pcall(function() obj.clearButtons() end)
        end
    end
    _targetButtonObjs = {}
    _craftSlotByGuid  = {}
    _recipeIdByGuid   = {}
end

-- Global: also cancels a pending targeted action. Called from turn-end
-- (day_loop.lua) and from every action-button handler.
-- pendingAction types that are "pick a target on the table": their prompt is
-- the 3D buttons _clearTargetButtons removes, so clearing the buttons has to
-- clear the intent too, or a cancelled action stays half-armed.
--
-- A set rather than a chain of ors, because it was a chain of ors and "flee"
-- and "drift" had been left out of it — Flee's click-again-to-cancel could not
-- cancel, and a ghost's pending drift outlived the turn that armed it. The
-- dialog-driven types (revive, stabilize, posterize) are deliberately absent:
-- their prompt is a UI panel with its own dismissal, not a tile button.
local TILE_TARGET_ACTIONS = {
    move = true, bonusmove = true, drift = true, flee = true,
    craft = true, cook = true, trade = true, fight = true,
    rally = true, signature_heal = true,
}

function clearActionTargets()
    local pa = gameState.pendingAction
    if pa and TILE_TARGET_ACTIONS[pa.type] then
        gameState.pendingAction = nil
    end
    _clearTargetButtons()
    -- Posterize target buttons live in signatures.lua (clears its own list
    -- and the "posterize" pendingAction).
    if clearSignatureTargets then
        safecall(function() clearSignatureTargets() end, "SigTargets")
    end
    if UI then
        UI.hide("tradeDialog"); UI.hide("signatureTargetDialog")
        UI.hide("peekDialog"); UI.hide("rallyDialog")
    end
end

function _armTargetTimeout()
    if _targetClearHandle then Wait.stop(_targetClearHandle) end
    _targetClearHandle = Wait.time(function()
        _targetClearHandle = nil
        clearActionTargets()
    end, TARGET_TIMEOUT)
end

-- createButton's `rotation` is in the object's LOCAL frame, so a button at
-- {0,0,0} inherits whatever yaw its object has. Threat cards are dealt face
-- up at rotY=180 (that is what "face up" is for a Card in this mod), so FIGHT
-- and TOGETHER came out mirrored — printed backwards across the card, which
-- is how a player reported them. Location tiles sit at rotY=0, which is why
-- MOVE HERE always looked fine and this went unnoticed.
--
-- Cancelling the object's own yaw makes every target button read the same way
-- up, whatever it is stuck to.
local function _uprightYaw(obj)
    local yaw = 0
    pcall(function() yaw = (obj.getRotation() or {}).y or 0 end)
    return (360 - (yaw % 360)) % 360
end

local function _spawnTargetButton(obj, label, fnName, tooltip, wide, pos)
    obj.createButton({
        click_function = fnName,
        function_owner  = Global,
        label           = label,
        position        = pos or {0, 0.4, 0},
        rotation        = {0, _uprightYaw(obj), 0},
        width           = wide and 2000 or 1200,
        height          = wide and 560 or 420,
        font_size       = wide and 240 or 180,
        -- Bright, fully opaque, white text: these must read as "click me"
        -- from table height, not blend into the tile art.
        color           = {0.10, 0.55, 0.20, 1.0},
        font_color      = {1, 1, 1},
        tooltip         = tooltip,
    })
    table.insert(_targetButtonObjs, obj)
end

-- Move targets are always 1-step neighbours; Rayman's 2-tile Speed is
-- delivered as a chained free second hop, so his buttons are 1-step too.
-- mode: "move" | "bonusmove" (Rayman's Speed) | "drift" (a ghost, §16.4)
--     | "flee" (§12.4).
-- Drift and Flee reuse this because they pick a destination exactly the way
-- the living walking do — one adjacent tile — and duplicating the tile-button
-- machinery per case is how the four drift apart.
local MOVE_BUTTON_LABEL = {
    bonusmove = "FREE MOVE", drift = "DRIFT HERE", flee = "FLEE HERE",
}
local MOVE_BUTTON_NOTE = {
    bonusmove = " (free second step)",
    drift     = " (ghost drift — free, once per round)",
    flee      = " (flee — 1 Sanity, no action; the threat stays behind)",
    move      = " (1 action, 1 Hunger)",
}

function _spawnMoveButtons(color, mode)
    local char = gameState.activeChars[color]
    if not char or not char.location then return 0 end
    local label = MOVE_BUTTON_LABEL[mode] or "MOVE HERE"
    local n = 0
    local names = {}
    for _, locName in ipairs(adjacentLocations(char.location)) do
        local tile = getLocationTile(locName)
        if tile then
            tile.highlightOn("Green", HIGHLIGHT_DURATION)
            -- Front edge of the tile, floated well above it: the tile
            -- centre is busy (standee slots, threat cards) and a button
            -- there disappears into the clutter.
            _spawnTargetButton(tile, label, "onMoveTargetClick",
                "Move " .. char.name .. " to " .. locName ..
                (MOVE_BUTTON_NOTE[mode] or MOVE_BUTTON_NOTE.move),
                true, {0, 0.7, -0.85})
            n = n + 1
            names[#names + 1] = locName
        end
    end
    -- Orient the mover: say where they ARE and where the buttons went —
    -- otherwise a lone green button reads as "move to where I stand".
    if n > 0 then
        broadcastToColor(char.name .. " is at " .. char.location ..
            ". Reachable now (green): " .. table.concat(names, ", ") ..
            " — click a " .. label .. " button, or just drag your standee onto the destination circle.",
            color, BROADCAST_COLORS.gain)
    end
    return n
end

-----------------------------------------------------------------------
-- Drag-to-move: players instinctively pick up their standee and drop it
-- where they want to go — long before they find the Move button. Treat
-- a standee drop as a Move request; anything illegal snaps the standee
-- back to where the game says it stands, with the reason.
-----------------------------------------------------------------------
local LOCATION_NAMES = {"JamesHouse", "RaymanHouse", "EllieLucaHouse",
                        "BasketballCourt", "BadmintonCourt"}

local function _nearestLocationTo(pos)
    local best, bestD = nil, math.huge
    for _, locName in ipairs(LOCATION_NAMES) do
        local tile = getLocationTile(locName)
        if tile then
            local p = tile.getPosition()
            local dx, dz = pos.x - p.x, pos.z - p.z
            local d = math.sqrt(dx * dx + dz * dz)
            if d < bestD then best, bestD = locName, d end
        end
    end
    return best, bestD
end

function onObjectDrop(dropColor, obj)
    if not (obj and obj.hasTag and obj.hasTag("Character")) then return end
    local charName = nil
    for _, tag in ipairs(obj.getTags()) do
        charName = tag:match("^Character:(.+)$") or charName
    end
    if not charName then return end
    safecall(function() _handleStandeeDrop(dropColor, obj, charName) end, "DragMove")
end

function _handleStandeeDrop(dropColor, obj, charName)
    -- Which seat plays this character?
    local color = nil
    for c, ch in pairs(gameState.activeChars or {}) do
        if ch.name == charName then color = c break end
    end
    local char = color and gameState.activeChars[color]

    local function snapBack(msg)
        if msg then broadcastToColor(msg, dropColor, BROADCAST_COLORS.warn) end
        if char and char.location then
            placeCharacterAtTile(charName, char.location)
        else
            -- Not in this game: back to the under-table bench.
            local i = CHAR_SLOT_INDEX[charName] or 0
            obj.setPositionSmooth(Vector(BENCH_POSITION.x, BENCH_POSITION.y, BENCH_POSITION.z - i * 3))
        end
    end

    if not char then
        snapBack(charName .. " isn't in this game — back to the bench.")
        return
    end

    local dest, dist = _nearestLocationTo(obj.getPosition())
    if not dest or dist > 6 then
        snapBack("Drop " .. charName .. " on a location circle to move. Back to " .. (char.location or "?") .. ".")
        return
    end
    if dest == char.location then
        placeCharacterAtTile(charName, dest)   -- tidy into the standee slot
        return
    end

    -- Dusk: a drag is the scramble move (doDuskMove validates everything).
    if gameState.subPhase == "Dusk" then
        doDuskMove(color, dest)
        if gameState.activeChars[color].location ~= dest then snapBack(nil) end
        return
    end
    if gameState.subPhase ~= "Day" then
        snapBack("Characters move during the Day (or scramble at Dusk). " .. charName .. " returns to " .. (char.location or "?") .. ".")
        return
    end
    if color ~= gameState.activeColor then
        snapBack("It's not " .. charName .. "'s turn — drag your standee (or use Move) on your own turn.")
        return
    end
    local adjacent = false
    for _, n in ipairs(adjacentLocations(char.location or "")) do
        if n == dest then adjacent = true break end
    end
    if not adjacent then
        snapBack(dest .. " isn't adjacent to " .. (char.location or "?") .. " — move 1 tile at a time.")
        return
    end

    -- Legal move request: consume any pending Move targeting and go.
    local pa = gameState.pendingAction
    if pa and (pa.type == "move" or pa.type == "bonusmove") then
        gameState.pendingAction = nil
    end
    _clearTargetButtons()

    if gameState.raymanBonusMove then
        safecall(function() doRaymanBonusMove(color, dest) end, "BonusMove")
    else
        safecall(function() doMove(color, dest) end, "Move")
        if gameState.raymanBonusMove then
            gameState.pendingAction = { type = "bonusmove", color = color }
            _spawnMoveButtons(color, "bonusmove")
            _armTargetTimeout()
        end
    end
    -- doMove refuses (no actions / injured refund) without moving the
    -- character — put the standee back where the rules say it is.
    if gameState.activeChars[color].location ~= dest then snapBack(nil) end
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

-- Why the last _spawnCraftButtons call produced nothing. Read by onActCraft so
-- a failure names itself instead of being reported as an empty market — the
-- old bare pcall turned EVERY error in this loop into "No cards in the Market
-- display", printed to a player looking straight at five market cards.
_craftScanProblem = nil

function _spawnCraftButtons()
    -- Iterate the CARDS (not the slots) and attach each to its nearest
    -- market slot. Robust to a card that drifted off its slot, and every
    -- handle access is guarded (a card merged/destroyed mid-deal would
    -- otherwise throw and abort the whole scan).
    _craftScanProblem = nil
    local slots = getMarketSlots()
    if #slots == 0 then
        _craftScanProblem = "the five Market slots are not on the table"
        return 0
    end
    local n, seen, failed, hidden = 0, 0, 0, 0
    for _, card in ipairs(findAllByTag("MarketCard")) do
        local ok = safecall(function()
            if card.type ~= "Card" then return end   -- skip the deck itself
            seen = seen + 1
            -- A guid that cannot be read is a card that cannot be bought:
            -- doCraft is handed the slot index through this map, so an entry
            -- keyed on nil is not a degraded button, it is a throw.
            local guid = safeGuid(card)
            if not guid then return end
            local cp = card.getPosition()
            local bestSlot, bestD = nil, math.huge
            for i, slot in ipairs(slots) do
                local d = objDistance(cp, slot.getPosition())
                if d and d < bestD then bestSlot, bestD = i, d end
            end
            -- Generous radius: cards settle up to ~1.5u off their slot.
            if bestSlot and bestD < 4 then
                -- A shelf that has not opened yet gets no button: the card is
                -- face down, so offering to buy it would be offering a choice
                -- the player cannot make (marketOpenSlots, global.lua).
                if marketSlotIsHidden(bestSlot) then
                    hidden = hidden + 1
                    return
                end
                _craftSlotByGuid[guid] = bestSlot
                _spawnTargetButton(card, "CRAFT", "onCraftTargetClick",
                    "Craft " .. safeNickname(card) .. " (1 action + resources)",
                    false)
                n = n + 1
            end
        end, "CraftButton")
        if not ok then failed = failed + 1 end
    end
    if n == 0 then
        if seen == 0 then
            _craftScanProblem = "no Market cards are dealt — the display is empty"
        elseif hidden > 0 and hidden == seen then
            _craftScanProblem = "every Market card is still face down — the shelves open " ..
                "one per day (" .. marketOpenSlots() .. " of " .. MARKET_SLOTS_TOTAL .. " so far)"
        elseif failed > 0 then
            _craftScanProblem = failed .. " of " .. seen ..
                " Market card(s) could not be read (see the TTS log for the error)"
        else
            _craftScanProblem = seen .. " Market card(s) are on the table but none is " ..
                "near a Market slot — drag them back onto their slots"
        end
    end
    return n
end

-- "2 Provisions + 1 Wood" from a { Provisions = 2, Wood = 1 } cost table (for tooltips).
--
-- Global, not local, because ui_actionbar_handlers.lua uses it too. It worked
-- as a file-local only because the bundle is one concatenated chunk and this
-- file happens to load first — i.e. it was relying on load order for *scope*,
-- which is invisible to luacheck (it lints per file) and would break silently
-- if the manifest order ever changed. Cross-file sharing here goes through
-- globals; there is no require().
function formatIngredientCost(cost)
    local parts = {}
    for _, r in ipairs({"Wood", "Metal", "Cloth", "Provisions", "EnergyDrink", "Battery"}) do
        if (cost[r] or 0) > 0 then
            parts[#parts + 1] = cost[r] .. " " .. (r == "EnergyDrink" and "Energy Drink" or r)
        end
    end
    return #parts > 0 and table.concat(parts, " + ") or "no ingredients"
end

-- Fight targets: everything fightable at the active player's tile gets a
-- FIGHT button — plus a FIGHT TOGETHER button when standing, fed allies
-- share the tile (group combat, Design §12.2).
local _fightTargetByGuid = {}

local function _alliesCanJoinFight(color)
    local char = gameState.activeChars[color]
    if not char then return false end
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == char.location
            and ch2.hunger >= 3 then
            return true
        end
    end
    return false
end

function _spawnFightButtons(color)
    _fightTargetByGuid = {}
    local char = gameState.activeChars[color]
    if not char then return 0 end
    local group = _alliesCanJoinFight(color)
    local n = 0
    for _, target in ipairs(fightTargetsAt(char.location)) do
        local obj = target.obj
        _fightTargetByGuid[obj.guid] = obj
        obj.highlightOn("Red", HIGHLIGHT_DURATION)
        local hpNote = target.stats.hp
        if not target.boss then
            local dmg = (gameState.threatDamage or {})[obj.guid] or 0
            hpNote = math.max(0, target.stats.hp - dmg)
        end
        _spawnTargetButton(obj, "FIGHT", "onFightTargetClick",
            "Fight " .. target.stats.name .. " (HP " .. hpNote .. ", Atk " .. target.stats.attack ..
            ") — 1 action, you alone.", false, {0, 0.4, -0.6})
        if group then
            _spawnTargetButton(obj, "TOGETHER", "onFightTogetherClick",
                "Fight " .. target.stats.name .. " as a group — every standing ally here with Hunger 3+ joins: summed dice, shared counter-attacks.",
                false, {0, 0.4, 0.6})
        end
        n = n + 1
    end
    return n
end

-----------------------------------------------------------------------
-- Target-button click handlers (createButton click_functions)
-----------------------------------------------------------------------
function onMoveTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and (pa.type == "move" or pa.type == "bonusmove"
                    or pa.type == "drift" or pa.type == "flee")) then
        return
    end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the moving player may choose the destination.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local loc = nil
    for _, tag in ipairs(obj.getTags()) do
        loc = tag:match("^Location:(.+)")
        if loc then break end
    end
    if not loc then return end

    local mode, color = pa.type, pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()

    if mode == "drift" then
        -- One tile per round, free, and it never touches the action budget:
        -- the ghost is not the active player and never will be.
        gameState.driftedThisRound = gameState.driftedThisRound or {}
        gameState.driftedThisRound[color] = true
        safecall(function() ghostDrift(color, loc) end, "GhostDrift")
        safecall(function() refreshReactionsPanel() end, "Reactions")
    elseif mode == "flee" then
        -- No action cost and no Hunger: running is priced in Sanity (§12.4),
        -- and doFlee owns the Last Nerve discount and the adjacency re-check.
        safecall(function() doFlee(color, loc) end, "Flee")
        refreshPhaseBanner()
        updateActivePlayerIndicator()
    elseif mode == "move" then
        -- Safety net (I.6): walking a character below 3 Health onto a tile
        -- that draws Threat cards at night is how a Down happens by accident.
        -- Passes straight through when the character is healthy or the
        -- destination is a house.
        --
        -- Everything downstream of doMove lives inside the callback: the move
        -- may not happen until the player answers, and Rayman's Speed reads
        -- gameState.raymanBonusMove, which doMove is what sets.
        safecall(function()
            confirmMoveInjuredToThreat(color, loc, function()
                safecall(function() doMove(color, loc) end, "Move")
                -- Rayman's Speed: doMove grants a free second 1-tile step.
                if gameState.raymanBonusMove then
                    gameState.pendingAction = { type = "bonusmove", color = color }
                    _spawnMoveButtons(color, "bonusmove")
                    _armTargetTimeout()
                    broadcastToColor("Speed: click FREE MOVE on a green tile for your second step — or take another action to skip it.",
                        color, BROADCAST_COLORS.gain)
                end
                refreshPhaseBanner()
                updateActivePlayerIndicator()
            end)
        end, "MoveConfirm")
    else
        safecall(function() doRaymanBonusMove(color, loc) end, "BonusMove")
    end
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onCraftTargetClick(obj, clickerColor, altClick)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "craft") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the crafting player may pick the card.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local slotIndex = _craftSlotByGuid[obj.getGUID()]
    if not slotIndex then return end
    local color = pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()
    safecall(function() doCraft(color, slotIndex) end, "Craft")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

local function _resolveFightClick(obj, clickerColor, together)
    local pa = gameState.pendingAction
    if not (pa and pa.type == "fight") then return end
    if clickerColor ~= pa.color then
        broadcastToColor("Only the fighting player may pick the target.", clickerColor, BROADCAST_COLORS.damage)
        return
    end
    local target = _fightTargetByGuid[obj.guid]
    if not target then return end
    local color = pa.color
    gameState.pendingAction = nil
    _clearTargetButtons()
    safecall(function() doFightTarget(color, target, together) end, "Fight")
    refreshPhaseBanner()
    updateActivePlayerIndicator()
end

function onFightTargetClick(obj, clickerColor, altClick)
    _resolveFightClick(obj, clickerColor, false)
end

function onFightTogetherClick(obj, clickerColor, altClick)
    _resolveFightClick(obj, clickerColor, true)
end

function _highlightCraftTargets(color)
    local deck = getMarketDeck()
    if deck then deck.highlightOn("Yellow", HIGHLIGHT_DURATION) end
    -- Empty market slots — neutral hint that this is where cards go
    for _, slot in ipairs(getMarketSlots()) do
        slot.highlightOn("Yellow", HIGHLIGHT_DURATION)
    end
    -- Per-card affordability: each individual MarketCard (those that have
    -- been dealt out of the deck) gets Green if the active player can
    -- afford it, Yellow otherwise.
    local affordableCount = 0
    for _, card in ipairs(findAllByTag("MarketCard")) do
        if card.type == "Card" then
            local cardId = _cardIdFromTags(card)
            if color and cardId and canAfford(color, cardId) then
                card.highlightOn("Green", HIGHLIGHT_DURATION)
                affordableCount = affordableCount + 1
            else
                card.highlightOn("Yellow", HIGHLIGHT_DURATION)
            end
        end
    end
    if color then
        local res = getPlayerResources(color)
        local resStr = string.format("Wood %d / Metal %d / Cloth %d / Provisions %d / Energy %d / Battery %d",
            res.Wood or 0, res.Metal or 0, res.Cloth or 0, res.Provisions or 0,
            res.EnergyDrink or 0, res.Battery or 0)
        printToColor("Affordable Market cards highlighted Green (" .. affordableCount .. "). Your bag: " .. resStr,
                     color, {0.7, 1.0, 0.7})
    end
end

-- Cook highlights only the Crockpot tile. It also used to highlight every
-- "RecipeCard", which drew an orange outline on cards parked UNDER the board
-- once the recipe rack moved into the hidden library.
function _highlightCookTargets()
    local tile = getLocationTile("EllieLucaHouse")
    if tile then tile.highlightOn("Orange", HIGHLIGHT_DURATION) end
end

function _highlightCleanseTargets()
    -- Cleanse cost bundle (CLEANSE_COST, global.lua).
    for resType in pairs(CLEANSE_COST) do
        local bag = getResourceBag(resType)
        if bag then bag.highlightOn("White", HIGHLIGHT_DURATION) end
    end
end

