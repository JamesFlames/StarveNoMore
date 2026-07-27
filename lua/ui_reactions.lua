-- ui_reactions.lua — the Reactions panel: free things a player can do on
-- SOMEBODY ELSE'S turn.
--
-- Why this file exists (Design §11.2 downtime, §10.1 Haunted, §6.5 Rally):
--
-- [PrinciplesOfGoodBoardGames.md §11] lists four cures for downtime, and the
-- design was A/B-testing the two most disruptive (shorter turns, more of
-- them — the Rotation variant) while never trying the cheapest: DECISIONS
-- THAT OCCUR ON OTHER PLAYERS' TURNS. It already had exactly one, free
-- Trade (§8.2), and that one works.
--
-- The Action Bar cannot host these. It is a single shared XML panel: a
-- button's enabled state is global rather than per-seat, and every handler
-- runs through validateActivePlayer, so a non-active player's click is
-- rejected by construction. This panel is the off-turn home instead.
--
-- The pattern that makes a shared panel safe: every row NAMES its actor
-- ("Rayman: see what Coco sees"), and onReactionClick checks that the
-- clicking player IS that actor. A shared panel therefore never lets one
-- player spend another player's Sanity — which matters more here than
-- usual, because these reactions cost the actor a stat.
--
-- Two reactions live here:
--   * WITNESS (§10.1) — pay 1 Sanity to see an ally's Haunted threat, then
--     fight it alongside them. The buy-in that stops Haunted from deleting
--     the co-op layer for the player who most needs it.
--   * RALLY (§6.5, §11.2) — Luca's free gift of an action, now firable on
--     the RECIPIENT's turn rather than only on his own. That makes Luca a
--     player who is always partly engaged and turns the Rally into a real
--     interruption-shaped decision instead of a pre-allocation. It also
--     sharpens his identity (§1.4 #4): the orator acts THROUGH other people.

REACTION_SLOTS = 3

-- Rebuilt on every refresh; onReactionClick indexes into it. Kept in a Lua
-- local rather than gameState: it is derived state, cheap to recompute, and
-- persisting it would let a stale row survive a reload and fire an action
-- whose preconditions have since evaporated.
local reactionRows = {}

-----------------------------------------------------------------------
-- Row collection. Each row: { color, label, run }.
--   color — the ONE seat allowed to click it
--   label — names the actor, so the table can see whose call it is
--   run   — the effect, re-validated inside the action itself
-----------------------------------------------------------------------
-- Iterating gameState.activeChars with pairs() gives an arbitrary order, so
-- row 1 could be a different reaction on every refresh — and onReactionClick
-- indexes by row number, which means a player could click "Rayman: witness"
-- and fire "Luca: rally". Rows are therefore collected against a FIXED colour
-- order and then sorted by label, so the same board state always produces the
-- same panel.
local REACTION_SEAT_ORDER = {"White", "Red", "Yellow", "Green", "Blue"}

local function collectReactionRows()
    local rows = {}
    if not gameState.started then return rows end
    local sp = gameState.subPhase
    -- Reactions belong to the Day phase: Dawn/Dusk/Night/Tick are resolved
    -- by the host in sequence, and offering an off-turn stat spend in the
    -- middle of night resolution invites double-resolution bugs.
    if sp ~= "Day" then return rows end

    for _, color in ipairs(REACTION_SEAT_ORDER) do
        local char = gameState.activeChars[color]
        if char and not char.down then
            -- WITNESS: one row per Haunted ally at this character's tile.
            if canWitness and (canWitness(color)) then
                -- witnessTargets also iterates a map, so sort its output for
                -- the same reason the seat loop is ordered.
                local targets = witnessTargets(color)
                table.sort(targets)
                for _, hColor in ipairs(targets) do
                    local hChar = gameState.activeChars[hColor]
                    if hChar then
                        rows[#rows + 1] = {
                            color = color,
                            label = char.name .. ": see what " .. hChar.name ..
                                    " sees  (pay " .. WITNESS_SANITY_COST .. " Sanity)",
                            run = function() doWitness(color, hColor) end,
                        }
                    end
                end
            end

            -- RALLY off-turn (§6.5): only offered while it is NOT Luca's own
            -- turn — on his turn the Action Bar's Rally button is the right
            -- affordance, and showing both would read as two different rules.
            if char.name == "Luca" and color ~= gameState.activeColor
                and canRally and canRally(color) then
                local active = gameState.activeColor
                    and gameState.activeChars[gameState.activeColor]
                -- Rally the player whose turn it is when they are eligible:
                -- that is the whole point of firing it off-turn — the gift
                -- arrives while they can still spend it.
                if active then
                    for _, c in ipairs(rallyTargets(color)) do
                        if c == gameState.activeColor then
                            rows[#rows + 1] = {
                                color = color,
                                label = "Luca: rally " .. active.name ..
                                        " now  (free — +1 action on their turn)",
                                run = function() doRally(color, c) end,
                            }
                            break
                        end
                    end
                end
            end
        end
    end
    -- Final tiebreak: identical board states must render identically, so a
    -- player learns "my row is the second one" and stays right.
    table.sort(rows, function(a, b) return a.label < b.label end)
    return rows
end

-----------------------------------------------------------------------
-- Panel refresh. Hidden entirely when nothing is available — an empty
-- panel parked over the table is clutter, and §18.10 principle 2 says the
-- screen should tell you what to do, not what you can't.
-----------------------------------------------------------------------
function refreshReactionsPanel()
    if not UI then return end
    if customUIHidden then
        UI.hide("reactionsPanel")
        return
    end

    reactionRows = {}
    safecall(function() reactionRows = collectReactionRows() end, "Reactions")

    local shown = 0
    for i = 1, REACTION_SLOTS do
        local row = reactionRows[i]
        local id = "reactBtn_" .. i
        if row then
            UI.setAttribute(id, "active", "true")
            setButtonLabel(id, row.label)
            shown = shown + 1
        else
            UI.setAttribute(id, "active", "false")
        end
    end

    if shown > 0 then
        UI.show("reactionsPanel")
    else
        UI.hide("reactionsPanel")
    end
end

function onReactionClick(player, value, id)
    local idx = tonumber(value)
    local row = idx and reactionRows[idx]
    if not row then
        -- The row list was rebuilt between render and click (somebody's stats
        -- moved). Say so rather than firing whatever now sits at that index.
        broadcastToColor("That option just expired — the board changed. Check the panel again.",
                         player.color, BROADCAST_COLORS.warn)
        refreshReactionsPanel()
        return
    end
    if player.color ~= row.color then
        broadcastToColor("That one is " .. (gameState.activeChars[row.color]
                             and gameState.activeChars[row.color].name or row.color) ..
                         "'s call, not yours.", player.color, BROADCAST_COLORS.damage)
        return
    end
    safecall(function() row.run() end, "Reaction")
    refreshReactionsPanel()
    refreshPhaseBanner()
    safecall(function() refreshActionBar() end, "ActionBar")
end
