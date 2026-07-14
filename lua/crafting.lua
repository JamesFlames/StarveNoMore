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
    broadcastEvent("proc", char.name .. " crafts " .. itemName .. "!")

    -- Doom threshold 15 (Scarcity): every craft costs +1 extra resource
    if gameState.ongoingDawnEffects.doom15 then
        broadcastEvent("warn", "Scarcity (Doom ≥ 15): also discard 1 extra resource of any type you hold.")
    end

    -- Move card to the player's hand zone
    local handZone = getHandZone(color)
    if handZone then
        card.setPositionSmooth(handZone.getPosition() + Vector(0, 1, 0))
    end

    -- Refill market slot from the deck
    refillMarketSlot(slot)
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

    -- Once-per-game check
    if recipe.oncePerGame then
        gameState.usedRecipes = gameState.usedRecipes or {}
        if gameState.usedRecipes[recipeId] then
            broadcastEvent("damage", recipe.name .. " can only be cooked once per game.")
            return
        end
        gameState.usedRecipes[recipeId] = true
    end

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
