-- crafting.lua  (F.8 — Crafting from Market + Cooking at Crockpot)
-- Design §13: Crafting claims a Market card; Cooking uses a Recipe at a Crockpot.

-----------------------------------------------------------------------
-- Crafting (the Market)  — Design §13.1
-----------------------------------------------------------------------
-- In TTS, the player manually spends resource tokens and claims a card
-- from the 5-card Market display. This function handles the bookkeeping
-- and market refill.

-- The Market slot markers used to be big notecards printing this paragraph
-- beside every slot. A notecard is much wider than a card, so the column lay
-- across the printed map and hid it ("the market slots are covering the board
-- up"). The paragraph now rides on the CARD itself, where the player is
-- already hovering to read the cost — and is stripped again the moment the
-- card is bought, because "use the Craft action to buy it" is a lie once the
-- card is in your hand.
--
-- The separator doubles as the marker for "already tagged" and as the cut
-- point for the strip, so the two can never disagree.
MARKET_HELP_SEP  = "\n\n— MARKET —\n"
MARKET_HELP_BODY = "One of the 5 shared cards for sale — it belongs to nobody "
                .. "yet. Use the Craft action to buy it; its resource cost is "
                .. "paid automatically and a fresh card is dealt onto the empty "
                .. "slot to take its place."

-- pcall throughout: a freshly dealt card can merge with the one already on
-- the slot and leave a dead handle (docs/tts-interface.md), and a tooltip is
-- never worth aborting a deal over.
function addMarketHelp(card)
    if not card then return end
    pcall(function()
        local d = card.getDescription() or ""
        if d:find(MARKET_HELP_SEP, 1, true) then return end
        card.setDescription(d .. MARKET_HELP_SEP .. MARKET_HELP_BODY)
    end)
end

function stripMarketHelp(card)
    if not card then return end
    pcall(function()
        local d = card.getDescription() or ""
        local at = d:find(MARKET_HELP_SEP, 1, true)
        if at then card.setDescription(d:sub(1, at - 1)) end
    end)
end

function doCraft(color, marketSlotIndex)
    if not spendAction(color, "Craft") then return end

    local char = gameState.activeChars[color]
    if not char then return end

    local slots = getMarketSlots()
    local slot = slots[marketSlotIndex]
    if not slot then
        broadcastEvent("damage", "Invalid market slot.")
        return
    end

    -- Find the card sitting on this slot (within ~2 units above it)
    local slotPos = slot.getPosition()
    local card = nil
    for _, obj in ipairs(getAllObjects()) do
        if obj.type == "Card" and obj.hasTag("MarketCard") then
            local d = obj.getPosition():distance(slotPos)
            if d < 2 then
                card = obj
                break
            end
        end
    end

    if not card then
        broadcastEvent("damage", "No card at market slot " .. marketSlotIndex .. ".")
        return
    end

    local itemName = card.getNickname() or "Unknown Item"

    -- Cost is paid automatically from the held count (resources are virtual
    -- now — no dropping tokens on a tray). Build the cost, add the Scarcity
    -- surcharge if Doom ≥ 15, then verify+pay; refund the action if short.
    local cardId = _cardIdFromTags(card)

    -- Total Blackout (noBatteries): "No Batteries in the game; Flashlights
    -- uncraftable." Refused before the action is charged, and derived from
    -- the cost table rather than a hardcoded card id — anything that needs a
    -- Battery is unbuildable in a world with no Batteries, which is the rule
    -- the scenario is actually stating.
    if (gameState.scenarioFlags or {}).noBatteries
        and ((cardId and MARKET_COSTS[cardId]) or {}).Battery then
        broadcastToColor(itemName .. " needs a Battery, and there are none left in the " ..
            "world (Total Blackout). Fire is the only light this week.",
            color, BROADCAST_COLORS.damage)
        char.actionsLeft = char.actionsLeft + 1   -- refund the Craft action
        return
    end

    local cost = {}
    for r, q in pairs((cardId and MARKET_COSTS[cardId]) or {}) do cost[r] = q end
    if gameState.ongoingDawnEffects.doom15 then
        local extra = _pickScarcityResource(color, cost)
        if extra then
            cost[extra] = (cost[extra] or 0) + 1
            broadcastEvent("warn", "Scarcity (Doom ≥ 15): +1 " .. _resLabel(extra) .. " added to the cost.")
        end
    end
    if next(cost) ~= nil then
        if not verifyAndPayResources(color, cost, itemName) then
            char.actionsLeft = char.actionsLeft + 1   -- refund the Craft action
            return
        end
    end
    broadcastEvent("gain", char.name .. " crafts " .. itemName .. " — dealt to your hand.")

    -- Truth Run (§16.2): claiming a Clue is what "finds and reads" it. This
    -- is the only place an ordinary craft can advance the achievement, and
    -- until it existed gameState.clueCount was never incremented by anything,
    -- so the Truth Run was unreachable in code rather than merely unlikely.
    safecall(function() recordClueFound(color, card) end, "Clue")
    -- Option utilization (§20.2 item 8): which of the 49 Market items does
    -- anyone ever actually craft?
    safecall(function() recordUsage("crafted", itemName) end, "Usage")

    -- Move card to the player's hand zone
    stripMarketHelp(card)
    local handZone = getHandZone(color)
    if handZone then
        card.setPositionSmooth(handZone.getPosition() + Vector(0, 1, 0))
    end

    -- Refill market slot from the deck
    refillMarketSlot(slot)
end

-- Scarcity surcharge picks the resource the player holds most of (that
-- isn't already zero after the base cost), so the +1 "any type you hold"
-- is spent automatically without a prompt.
function _pickScarcityResource(color, baseCost)
    local held = getPlayerResources(color)
    local best, bestN = nil, 0
    for _, r in ipairs({"Wood", "Metal", "Cloth", "Food", "EnergyDrink", "Battery"}) do
        local spare = (held[r] or 0) - (baseCost[r] or 0)
        if spare > bestN then best, bestN = r, spare end
    end
    return best
end

function refillMarketSlot(slot)
    local marketDeck = getMarketDeck()
    if not marketDeck then return end

    -- Strict Rationing (slowMarket): "Market restocks 1 card per 2 days."
    -- One card enters the market every second day, whoever bought and
    -- whenever — so an empty slot stays empty and the shelf really is bare.
    if (gameState.scenarioFlags or {}).slowMarket then
        local last = gameState.lastMarketRefillDay
        if last and (gameState.day - last) < 2 then
            broadcastEvent("warn", "Strict Rationing: the shelf stays empty — " ..
                "the market restocks one card every two days (last on Day " .. last .. ").")
            return
        end
        gameState.lastMarketRefillDay = gameState.day
    end

    local qty = marketDeck.getQuantity and marketDeck.getQuantity() or 0
    if qty <= 0 then
        broadcastEvent("proc", "Market deck is empty — no refill.")
        return
    end

    -- (Doom 15 no longer slows the refill — it adds +1 to craft costs
    -- instead. Scarcity should pressure, not bore: players still see
    -- tempting cards they can't quite afford.)

    -- Truth Run (§16.2, clues.lua): if the week has passed a checkpoint and
    -- no Clue has been put in front of the team, this refill is a Clue. This
    -- is the "spread the clues through the deck" guarantee, applied where the
    -- player actually meets the deck — so finding all three is a plan rather
    -- than a shuffle.
    local clueGuid = nil
    safecall(function() clueGuid = clueDueForRefill() end, "ClueRefill")

    marketDeck.takeObject({
        guid     = clueGuid,   -- nil ⇒ normal top-of-deck draw
        position = slot.getPosition() + Vector(0, 1, 0),
        rotation = {0, 180, 0},  -- face up
        smooth   = true,
        callback_function = function(newCard)
            addMarketHelp(newCard)
            -- pcall: the refilled card can merge with the placeholder/next
            -- card on the slot, leaving a dead handle (see docs/tts-interface.md).
            pcall(function()
                broadcastEvent("proc", "Market refilled: " .. (newCard.getNickname() or "?"))
            end)
        end
    })
end

-----------------------------------------------------------------------
-- Cooking (the Crockpot)  — Design §13.2
-----------------------------------------------------------------------
-- RECIPE_DATA (lua/recipe_data.lua, AUTO-GENERATED from the `script`
-- column of content/cards_recipes.csv) is the lookup table for scripted
-- recipe resolution. Ingredients are validated manually by the player
-- (resource tokens); the script resolves the stat effects.

-- The Resource cost to cook this recipe, after Ellie's Crockpot Master
-- perk (§6.4: "recipes need 1 fewer ingredient, min 1") — one unit is
-- shaved off the largest ingredient, never below 1 ingredient total.
-- Take one unit off the largest line of a cost, but never take the last one:
-- a recipe that costs nothing is a different card. Shared by Ellie's Crockpot
-- Master perk and Strict Rationing, which are the same discount from two
-- different directions and were not going to stay in step written twice.
local function _discountOne(cost)
    local total = 0
    for _, q in pairs(cost) do total = total + q end
    if total <= 1 then return end
    local best, bestQ = nil, 0
    for r, q in pairs(cost) do if q > bestQ then best, bestQ = r, q end end
    if best then
        cost[best] = cost[best] - 1
        if cost[best] <= 0 then cost[best] = nil end
    end
end

function recipeIngredientCost(color, recipe)
    local cost = {}
    for r, q in pairs(recipe.ingredients or {}) do cost[r] = q end
    local char = gameState.activeChars[color]
    if char and char.name == "Ellie" then
        _discountOne(cost)
    end
    -- Strict Rationing (cheapRecipes): "recipes cost 1 fewer ingredient".
    -- Applied after Ellie's, so the two stack the way two discounts should —
    -- and `_discountOne` refuses to take the last ingredient either time.
    if (gameState.scenarioFlags or {}).cheapRecipes then
        _discountOne(cost)
    end
    return cost
end

function doCook(color, recipeId)
    local recipe = RECIPE_DATA[recipeId]
    if not recipe then
        broadcastEvent("damage", "Unknown recipe: " .. tostring(recipeId))
        return
    end

    local char = gameState.activeChars[color]
    if not char then return end

    -- Night-only restriction: none here. Midnight Snack (canCookAtNight)
    -- may be cooked during the Day too, so this cook is never gated by phase.

    -- Every reason this cook CAN'T happen is checked before anything is
    -- spent, so a refused cook never costs an action, ingredients or a cook
    -- penalty. (The Telltale Heart used to fail on a full supply *after*
    -- charging its 2 Health — the one recipe whose penalty is paid up front.)
    if recipe.oncePerGame then
        gameState.usedRecipes = gameState.usedRecipes or {}
        if gameState.usedRecipes[recipeId] then
            broadcastEvent("damage", recipe.name .. " can only be cooked once per game.")
            return
        end
    end
    if recipe.special == "heart" and (gameState.heartCount or 0) >= HEART_SUPPLY_MAX then
        broadcastEvent("damage", "Telltale Heart supply is exhausted (max " ..
            HEART_SUPPLY_MAX .. ").")
        return
    end
    -- Gumbo and friends need the pot, not just the ingredients.
    if recipe.requiresCrockpot and not crockpotAt(char.location) then
        broadcastToColor(recipe.name .. " needs a Crockpot at your tile. There isn't one at " ..
            (char.location or "?") .. ".", color, BROADCAST_COLORS.damage)
        return
    end

    -- Action cost. The Feast (Ellie's Signature, §6.7) covers every cook
    -- for the rest of her turn in its single action.
    local actionCost = recipe.actionCost or 1
    if char.feastActive then
        actionCost = 0
        broadcastEvent("proc", "The Feast: " .. recipe.name .. " costs no action.")
    end
    -- Multi-action recipes are all-or-nothing: the Birthday Cake costs 2, and
    -- starting it with 1 action left used to burn that action on nothing.
    if char.actionsLeft < actionCost then
        broadcastToColor(recipe.name .. " takes " .. actionCost .. " actions — you have " ..
            char.actionsLeft .. ".", color, BROADCAST_COLORS.damage)
        return
    end
    for i = 1, actionCost do
        if not spendAction(color, "Cook (" .. recipe.name .. ")") then
            -- Refund whatever this cook already took (rotation turns can
            -- refuse the second action even when the budget allowed it).
            for _ = 1, i - 1 do char.actionsLeft = char.actionsLeft + 1 end
            return
        end
    end

    -- Ingredients are paid automatically from the held count (no dropping
    -- tokens). The Feast already consumed all Food up front, so cooking is
    -- ingredient-free during it. Refund the action(s) if the cook is short.
    if not char.feastActive then
        local cost = recipeIngredientCost(color, recipe)
        if next(cost) ~= nil then
            if not verifyAndPayResources(color, cost, recipe.name) then
                for _ = 1, actionCost do char.actionsLeft = char.actionsLeft + 1 end
                return
            end
        end
    end

    if recipe.oncePerGame then gameState.usedRecipes[recipeId] = true end

    broadcastEvent("proc", char.name .. " cooks " .. recipe.name .. "!")
    safecall(function() recordMealInChronicle(char.name) end, "Chronicle")
    safecall(function() recordUsage("cooked", recipe.name or recipeId) end, "Usage")

    -- Cook penalty (e.g., Battery Acid Soup costs health, Telltale Heart costs 2 health)
    if recipe.cookPenalty then
        for stat, amount in pairs(recipe.cookPenalty) do
            char[stat] = math.max(0, char[stat] - amount)
            broadcastEvent("damage", char.name .. " pays " .. amount .. " " .. stat .. " to cook.")
        end
    end

    -- Special recipes
    if recipe.special == "heart" then
        cookTelltaleHeart(color)
        return
    end

    if recipe.special == "trailmix" then
        broadcastEvent("gain", char.name .. " makes Trail Mix! 2 Energy Bar items placed in hand.")
        return
    end

    -- Ellie's Comfort Food perk: +1 hunger and +1 sanity to each ally she shares food with
    local ellieBonus = (char.name == "Ellie") and true or false
    -- P4_LAST_MEAL (recipeBonusHunger): the last of the food goes further —
    -- every Hunger a recipe restores today is worth 2 more. Applied per eater,
    -- once, to the Hunger term only.
    local mealBonus = gameState.ongoingDawnEffects.recipeBonusHunger and 2 or 0
    -- The Rotting Autumn (recipeBonus): "recipes yield +1 Hunger". Stacks
    -- with the Dawn card above — one is a season, the other is a day.
    if (gameState.scenarioFlags or {}).recipeBonus then mealBonus = mealBonus + 1 end

    -- Apply a recipe's stat table to one character, returning the "+N Stat"
    -- fragments actually granted. `extra` is the Comfort Food ally bonus.
    local function _applyStats(ch, tbl, extra)
        local gains = {}
        for stat, amount in pairs(tbl) do
            local maxKey = "max" .. stat:sub(1,1):upper() .. stat:sub(2)
            local total = amount + extra + ((stat == "hunger") and mealBonus or 0)
            ch[stat] = math.min(ch[maxKey], ch[stat] + total)
            gains[#gains + 1] = "+" .. total .. " " .. stat
        end
        return gains
    end

    -- Apply effects to all at the same tile
    if recipe.allAtTile then
        local loc = char.location
        for c, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == loc then
                local extra = (ellieBonus and c ~= color) and 1 or 0
                local gains = _applyStats(ch, recipe.allAtTile, extra)
                broadcastEvent("gain", ch.name .. " gains " .. table.concat(gains, ", ") .. " from " .. recipe.name .. ".")
            end
        end
    end

    -- Apply cook-only effects
    if recipe.cookOnly then
        local gains = _applyStats(char, recipe.cookOnly, 0)
        broadcastEvent("gain", char.name .. " (cook) gains " .. table.concat(gains, ", ") .. ".")
    end

    -- Adjacent allies (Iced Tea): the tile next door gets a share. Printed on
    -- the card and generated into RECIPE_DATA since the CSV had it, but no
    -- code had ever read the field — the recipe's second line simply never
    -- happened. Down characters are skipped, as everywhere else.
    if recipe.adjacentAllies then
        local neighbours = {}
        for _, n in ipairs(adjacentLocations(char.location or "")) do neighbours[n] = true end
        for c, ch in pairs(gameState.activeChars) do
            if not ch.down and c ~= color and neighbours[ch.location or ""] then
                local gains = _applyStats(ch, recipe.adjacentAllies, 0)
                broadcastEvent("gain", ch.name .. " catches the smell from " .. (char.location or "?") ..
                    " — " .. table.concat(gains, ", ") .. " from " .. recipe.name .. ".")
            end
        end
    end

    -- Apply one-ally bonus (e.g., Grilled Cheese)
    if recipe.oneAlly then
        broadcastEvent("proc", "Choose one ally at this tile to receive bonus: " ..
            (recipe.oneAlly.hunger and ("+" .. recipe.oneAlly.hunger .. " Hunger") or "") ..
            (recipe.oneAlly.sanity and (" +" .. recipe.oneAlly.sanity .. " Sanity") or ""))
    end

    checkDownState(color)
end

-----------------------------------------------------------------------
-- Telltale Heart special recipe  — Design §13.4 / F.12
-----------------------------------------------------------------------
function cookTelltaleHeart(color)
    local char = gameState.activeChars[color]
    if not char then return end

    -- Backstop: doCook checks the same ceiling BEFORE charging the 2 Health
    -- cook penalty, so this only fires for a direct call.
    gameState.heartCount = gameState.heartCount or 0
    if gameState.heartCount >= HEART_SUPPLY_MAX then
        broadcastEvent("damage", "Telltale Heart supply is exhausted (max " ..
            HEART_SUPPLY_MAX .. ").")
        return
    end

    gameState.heartCount = gameState.heartCount + 1
    broadcastEvent("gain", char.name .. " creates a Telltale Heart! (" .. gameState.heartCount .. "/5 in existence)")
    broadcastEvent("proc", "The Telltale Heart is placed at " .. char.name .. "'s location.")

    -- Physical token placement handled via the TTS supply bag
    local supply = getHeartSupply()
    if supply and supply.getQuantity and supply.getQuantity() > 0 then
        local tile = getLocationTile(char.location)
        if tile then
            supply.takeObject({
                position = tile.getPosition() + Vector(0, 1.5, 1),
                smooth = true,
            })
        end
    end
end
