-- crafting.lua  (F.8 — Crafting from Market + Cooking at Crockpot)
-- Design §13: Crafting claims a Market card; Cooking uses a Recipe at a Crockpot.

-----------------------------------------------------------------------
-- Crafting (the Market)  — Design §13.1
-----------------------------------------------------------------------
-- In TTS, the player manually spends resource tokens and claims a card
-- from the 5-card Market display. This function handles the bookkeeping
-- and market refill.

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

    -- Move card to the player's hand zone
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

    local qty = marketDeck.getQuantity and marketDeck.getQuantity() or 0
    if qty <= 0 then
        broadcastEvent("proc", "Market deck is empty — no refill.")
        return
    end

    -- (Doom 15 no longer slows the refill — it adds +1 to craft costs
    -- instead. Scarcity should pressure, not bore: players still see
    -- tempting cards they can't quite afford.)
    marketDeck.takeObject({
        position = slot.getPosition() + Vector(0, 1, 0),
        rotation = {0, 180, 0},  -- face up
        smooth   = true,
        callback_function = function(newCard)
            local name = newCard.getNickname() or "?"
            broadcastEvent("proc", "Market refilled: " .. name)
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
function recipeIngredientCost(color, recipe)
    local cost = {}
    for r, q in pairs(recipe.ingredients or {}) do cost[r] = q end
    local char = gameState.activeChars[color]
    if char and char.name == "Ellie" then
        local total = 0
        for _, q in pairs(cost) do total = total + q end
        if total > 1 then
            local best, bestQ = nil, 0
            for r, q in pairs(cost) do if q > bestQ then best, bestQ = r, q end end
            if best then
                cost[best] = cost[best] - 1
                if cost[best] <= 0 then cost[best] = nil end
            end
        end
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

    -- Once-per-game check FIRST (before spending anything), so a repeat
    -- attempt doesn't cost an action or ingredients.
    if recipe.oncePerGame then
        gameState.usedRecipes = gameState.usedRecipes or {}
        if gameState.usedRecipes[recipeId] then
            broadcastEvent("damage", recipe.name .. " can only be cooked once per game.")
            return
        end
    end

    -- Action cost. The Feast (Ellie's Signature, §6.7) covers every cook
    -- for the rest of her turn in its single action.
    local actionCost = recipe.actionCost or 1
    if char.feastActive then
        actionCost = 0
        broadcastEvent("proc", "The Feast: " .. recipe.name .. " costs no action.")
    end
    for i = 1, actionCost do
        if not spendAction(color, "Cook (" .. recipe.name .. ")") then return end
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

    -- Apply effects to all at the same tile
    if recipe.allAtTile then
        local loc = char.location
        for c, ch in pairs(gameState.activeChars) do
            if not ch.down and ch.location == loc then
                for stat, amount in pairs(recipe.allAtTile) do
                    local maxKey = "max" .. stat:sub(1,1):upper() .. stat:sub(2)
                    local bonus = 0
                    if ellieBonus and c ~= color then bonus = 1 end
                    ch[stat] = math.min(ch[maxKey], ch[stat] + amount + bonus)
                end
                local gains = {}
                for stat, amount in pairs(recipe.allAtTile) do
                    table.insert(gains, "+" .. amount .. " " .. stat)
                end
                broadcastEvent("gain", ch.name .. " gains " .. table.concat(gains, ", ") .. " from " .. recipe.name .. ".")
            end
        end
    end

    -- Apply cook-only effects
    if recipe.cookOnly then
        for stat, amount in pairs(recipe.cookOnly) do
            local maxKey = "max" .. stat:sub(1,1):upper() .. stat:sub(2)
            char[stat] = math.min(char[maxKey], char[stat] + amount)
        end
        local gains = {}
        for stat, amount in pairs(recipe.cookOnly) do
            table.insert(gains, "+" .. amount .. " " .. stat)
        end
        broadcastEvent("gain", char.name .. " (cook) gains " .. table.concat(gains, ", ") .. ".")
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

    -- Check supply (max 5 in the game)
    gameState.heartCount = gameState.heartCount or 0
    if gameState.heartCount >= 5 then
        broadcastEvent("damage", "Telltale Heart supply is exhausted (max 5).")
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
