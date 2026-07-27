-- actions_haunted.lua  — the Haunted threshold effect's cooperative half.
--
-- Haunted itself (Design §10.1) is resolved at the table: BeginDay
-- (day_loop.lua) records who is Haunted in gameState.haunted and tells them
-- to draw a Threat at their tile. This file is the buy-in that stops the rule
-- from deleting the co-op layer for the one player who most needs it.

-----------------------------------------------------------------------
-- WITNESS (free, 1 Sanity) — Design §10.1, the Haunted buy-in.
--
-- "An ally at your location may pay 1 Sanity to see what you see, and may
-- then fight your Haunted threat alongside you."
--
-- Why it is priced in Sanity and not in an action: it is a textbook
-- mismatched-currency trade (§8.4) on the diagonal-AVOIDING side — you pay
-- Sanity to solve someone else's Sanity problem — and pricing it in actions
-- would have made it compete with Fight, which is the thing you are buying
-- the right to do. Free-but-costly keeps the decision about courage rather
-- than about the action economy.
--
-- Deliberately once per witness per haunting: this buys you into TODAY's
-- haunting, and tomorrow's Dawn draws a fresh one at a fresh price.
-----------------------------------------------------------------------
WITNESS_SANITY_COST = 1

-- Haunted allies at this character's tile whom they have not yet witnessed.
function witnessTargets(color)
    local out = {}
    local char = gameState.activeChars[color]
    if not char or char.down then return out end
    for hColor, rec in pairs(gameState.haunted or {}) do
        local hChar = gameState.activeChars[hColor]
        if hColor ~= color and hChar and not hChar.down
            and hChar.location == char.location
            and not (rec.witnesses or {})[color] then
            table.insert(out, hColor)
        end
    end
    return out
end

function canWitness(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    -- Paying your last point of Sanity to share someone's hallucination would
    -- put you Down to save them, which is a trade the rule shouldn't offer
    -- silently. Block it and say why.
    if char.sanity <= WITNESS_SANITY_COST then
        return false, "Not enough Sanity to spare — witnessing costs " ..
            WITNESS_SANITY_COST .. " and you have " .. char.sanity .. "."
    end
    if #witnessTargets(color) == 0 then
        return false, "Nobody at your tile is Haunted (or you already see what they see)."
    end
    return true, nil
end

function doWitness(color, hauntedColor)
    local ok, why = canWitness(color)
    if not ok then
        broadcastToColor(why or "Can't witness right now.", color, BROADCAST_COLORS.damage)
        return false
    end
    local valid = false
    for _, c in ipairs(witnessTargets(color)) do
        if c == hauntedColor then valid = true break end
    end
    local char   = gameState.activeChars[color]
    local target = gameState.activeChars[hauntedColor]
    if not valid or not target then
        broadcastToColor("That ally isn't Haunted at your tile.", color, BROADCAST_COLORS.damage)
        return false
    end

    char.sanity = math.max(0, char.sanity - WITNESS_SANITY_COST)
    local rec = gameState.haunted[hauntedColor]
    rec.witnesses = rec.witnesses or {}
    rec.witnesses[color] = true

    broadcastEvent("warn", char.name .. " looks where " .. target.name ..
        " is looking, and pays " .. WITNESS_SANITY_COST .. " Sanity to see it too. (Now " ..
        char.sanity .. ")")
    broadcastEvent("gain", char.name .. " can now fight " .. target.name ..
        "'s Haunted threat alongside them. " .. target.name .. " is not alone with it any more.")
    safecall(function() refreshRulesPanel() end, "Rules")
    checkDownState(color)
    return true
end
