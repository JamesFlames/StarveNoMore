-- threat_persistent.lua — Persistent threats: the ones that stay (Design
-- §11.4 / docs/design/04-decks.md: "a few are persistent — stays on the
-- location until cleared").
--
-- Thirteen cards, and until now not one of them did anything. The printed
-- rule ("Move actions out of this tile cost 1 extra Hunger", "No Food can be
-- gathered at this tile", "each Tick eats 1 Food at this tile") was text on a
-- card face that no code read. Worse, seven of them have hp 0, so
-- `fightTargetsAt` filters them out — unfightable — and only four of those
-- seven are Sealed, i.e. removable by Pry. The remaining six had NO removal
-- path at any price, while `countFesteringThreats` counted them every Dawn:
-- +1 Doom per card per day, for the rest of the week, with no counterplay.
-- That is the same pathology threat_effects.lua was written to fix for Soft
-- cards, and it is worse here, because a Persistent card is *supposed* to sit
-- on the tile — nothing else was ever going to take it off.
--
-- Two halves, then:
--
--   1. the printed effects actually apply, through PERSISTENT_THREAT_RULES —
--      one declarative row per card, read by hooks in doMove / doGather /
--      doRest / doTrade / doBarricade / resolveNightAtLocation / resolveTick;
--   2. every Persistent card has a way off the tile:
--        * hp > 0                     → Fight it (Lurker, Hungry Dog)
--        * Sealed (a pry_reward)      → Pry it (doPry, actions_social.lua)
--        * everything else            → CLEAR it (doClearPersistent, below)
--      tests/test_persistent_threats.py fails if a Persistent card has none
--      of the three.
--
-- The state is the table itself: which persistents are at a tile is derived
-- from the cards physically near it, exactly as fightTargetsAt and _sealedAtTile
-- do. Nothing is cached in gameState, so a card that is fought, pried, cleared
-- or simply dragged away stops applying the moment it moves — and a reload
-- cannot resurrect an effect whose card is gone.

-- Same "at this tile" radius as festering / Fight / Pry.
local PERSIST_RADIUS = 7

-- Where a Cleared persistent goes: the same discard as a spent Soft threat
-- (threat_effects.lua), west of the trophy pile — these were not kills.
local CLEARED_DISCARD_POS = { -13.5, 1.5, 10.8 }

-- The Clear action's price. The one Persistent card whose removal cost is
-- PRINTED is The Nest ("Destroy with 2 actions + 1 Wood (burn it)"), so that
-- is the cost every Clear pays: generalising the game's own number rather
-- than inventing a second one. Two actions is most of a turn — clearing is a
-- real decision against the +1 Doom/Dawn the card would otherwise charge.
CLEAR_PERSISTENT_ACTIONS = 2
CLEAR_PERSISTENT_WOOD    = 1

-----------------------------------------------------------------------
-- The rules table. One row per Persistent card in content/cards_threats.csv;
-- tests/test_persistent_threats.py enforces the roster in both directions.
--
--   fought    = true   hp > 0: Fight is the removal path, no Clear button
--   sealed    = true   has a pry_reward: Pry is the removal path
--   (neither)          Clear is the removal path
--
-- Effect keys are read by the hooks named beside them. `manual` is the
-- MANUAL_SOFT equivalent — a rule the table applies itself, announced so it
-- does not read as flavour.
-----------------------------------------------------------------------
PERSISTENT_THREAT_RULES = {
    -- Fightable: their printed rule IS "stays until cleared", and hp is the clear.
    T_LURKER = {
        fought = true,
        blurb  = "It stays at this tile until something kills it.",
    },
    T_HUNGRY_DOG = {
        fought = true,
        eatsFoodAtTick = 1,
        blurb = "Each Tick it eats 1 Food from someone at this tile.",
    },

    -- Terrain. No hp, no seal — these are what the Clear action exists for.
    T_CRACKED_FLOOR = {
        moveOutHunger = 1,
        blurb = "Moving OUT of this tile costs 1 extra Hunger.",
    },
    T_FOG_BANK = {
        moveActionCost = 1,
        blurb = "Moving out of this tile costs 1 extra action. Visibility zero.",
    },
    T_NEST = {
        nightThreats = 1,
        blurb = "Every Night this tile draws 1 extra Threat.",
    },
    T_CONTAMINATED = {
        noFoodGather = true, rawFoodSanity = 2,
        blurb = "No Food can be gathered here, and eating raw here costs 2 Sanity.",
    },
    T_ROOTS = {
        noBarricade = true, restRestoresNothing = true,
        blurb = "This tile cannot be barricaded, and Rest restores nothing here.",
    },
    T_WATCHER = {
        noTrade = true,
        blurb = "Nobody at this tile can trade. It watches. It remembers.",
    },
    T_SPIRAL = {
        -- A player-initiated gamble with a physical card draw on the win
        -- side; the table runs it, the script makes sure it is offered.
        manual = "Anyone here may take the Risk: roll Sanity d8 — 6+ take a Clue, 1-5 lose 2 Sanity.",
        blurb  = "Players here may take a Risk action for a Clue.",
    },

    -- Sealed: doPry (actions_social.lua) opens them and destroys the card.
    T_LOCKED_ROOM = {
        sealed = true,
        blurb = "An Item is locked inside. Pry it open (free, needs a tool) or it is lost.",
    },
    T_SEALED_SHED   = { sealed = true, blurb = "Pry it open (free, needs a tool): 3 Wood." },
    T_SEALED_LOCKER = { sealed = true, blurb = "Pry it open (free, needs a tool): 2 Battery + 1 Cloth." },
    T_SEALED_CAR    = { sealed = true, blurb = "Pry it open (free, needs a tool): 2 Energy Drinks + 1 Metal." },
}

-----------------------------------------------------------------------
-- Shared tile scanner. `ruleTable` is keyed by CSV id
-- (PERSISTENT_THREAT_RULES here, HARD_THREAT_SPECIALS in threat_hard.lua);
-- a card counts when it carries a key of that table as a tag and lies within
-- PERSIST_RADIUS of the tile. Entries are
-- { obj = card, id = "T_...", rule = {...}, name = "..." }.
--
-- One implementation for both tables: the Persistent rules and the Hard
-- specials ask the same question ("what is standing at this tile, and what
-- does its row say"), and two copies of a getAllObjects scan is how the
-- radius constants drift apart.
-----------------------------------------------------------------------
local function _ruleFor(obj, ruleTable)
    for _, tag in ipairs(obj.getTags() or {}) do
        if ruleTable[tag] then return ruleTable[tag], tag end
    end
    return nil, nil
end

function threatCardsAt(locName, ruleTable)
    local out = {}
    local tile = locName and getLocationTile(locName)
    if not tile then return out end
    local tp = tile.getPosition()
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        -- pcall per card: a scan of the table meets stale handles (a card
        -- merged into a deck mid-flight), and touching getPosition throws.
        local hit = nil
        pcall(function()
            if obj.type ~= "Card" then return end
            local p = obj.getPosition()
            local dx, dz = p.x - tp.x, p.z - tp.z
            if (dx * dx + dz * dz) > (PERSIST_RADIUS * PERSIST_RADIUS) then return end
            local rule, id = _ruleFor(obj, ruleTable)
            if rule then
                hit = { obj = obj, id = id, rule = rule,
                        name = (THREAT_STATS[id] and THREAT_STATS[id].name)
                               or safeNickname(obj) }
            end
        end)
        if hit then out[#out + 1] = hit end
    end
    return out
end

-- Every matching card on the board at once, bucketed by tile:
-- { JamesHouse = { entry, ... }, ... }, only for tiles that have one.
--
-- threatCardsAt scans the whole table per call (findAllByTag does), and the
-- callers that want ALL five tiles — the Rules panel, which refreshes on
-- every state change, plus the Tick and Night sweeps — would otherwise pay
-- for five scans each. This pays for one.
function threatCardsByTile(ruleTable)
    local buckets = {}
    for _, locName in ipairs(LOCATION_ORDER) do
        local tile = getLocationTile(locName)
        if tile then buckets[locName] = { tile = tile.getPosition(), list = {} } end
    end
    for _, obj in ipairs(findAllByTag("ThreatCard")) do
        pcall(function()
            if obj.type ~= "Card" then return end
            local rule, id = _ruleFor(obj, ruleTable)
            if not rule then return end
            local p = obj.getPosition()
            for _, bucket in pairs(buckets) do
                local dx, dz = p.x - bucket.tile.x, p.z - bucket.tile.z
                if (dx * dx + dz * dz) <= (PERSIST_RADIUS * PERSIST_RADIUS) then
                    bucket.list[#bucket.list + 1] = {
                        obj = obj, id = id, rule = rule,
                        name = (THREAT_STATS[id] and THREAT_STATS[id].name) or safeNickname(obj),
                    }
                    return
                end
            end
        end)
    end
    local byLoc = {}
    for locName, bucket in pairs(buckets) do
        if #bucket.list > 0 then byLoc[locName] = bucket.list end
    end
    return byLoc
end

-- Which persistents are standing at a tile, right now.
function persistentThreatsAt(locName)
    return threatCardsAt(locName, PERSISTENT_THREAT_RULES)
end

function persistentThreatsEverywhere()
    return threatCardsByTile(PERSISTENT_THREAT_RULES)
end

-- Sum one numeric rule key over every persistent at a tile, collecting the
-- card names that contributed. Returns (total, { "Fog Bank", ... }).
function persistentRuleTotal(locName, key)
    local total, names = 0, {}
    for _, p in ipairs(persistentThreatsAt(locName)) do
        local v = p.rule[key]
        if type(v) == "number" and v ~= 0 then
            total = total + v
            names[#names + 1] = p.name
        end
    end
    return total, names
end

-- The first persistent at a tile whose rule sets a boolean key, or nil.
-- Callers use its name in the refusal, so the player is told WHAT stopped them.
function persistentRuleHolder(locName, key)
    for _, p in ipairs(persistentThreatsAt(locName)) do
        if p.rule[key] then return p end
    end
    return nil
end

-----------------------------------------------------------------------
-- Announcement when a Persistent card lands (drawThreatsAt, night.lua).
-- Says what it does and — the part that was missing entirely — how to be
-- rid of it. "Must be fought or fled" was a lie for the eleven that cannot
-- be fought.
-----------------------------------------------------------------------
function announcePersistentThreat(id, name, location)
    local rule = PERSISTENT_THREAT_RULES[id]
    local label = name or (THREAT_STATS[id] and THREAT_STATS[id].name) or "Something"
    if not rule then
        -- A Persistent card with no rule row: still say the true thing.
        broadcastEvent("warn", label .. " settles in at " .. (location or "this tile") ..
            " and stays. Every Dawn it stands costs +1 Doom.")
        return
    end

    broadcastEvent("warn", label .. " settles in at " .. (location or "this tile") ..
        " — PERSISTENT. " .. (rule.blurb or "It stays until it is cleared."))
    if rule.manual then
        broadcastEvent("proc", label .. " — TABLE STEP: " .. rule.manual)
    end

    local how
    if rule.fought then
        how = "Fight it to be rid of it (it can also be fled — it stays and festers)."
    elseif rule.sealed then
        how = "Pry it open (free action + Crowbar/Lockpick/Pry Bar) to take it off the tile."
    else
        how = "CLEAR it: " .. CLEAR_PERSISTENT_ACTIONS .. " actions + " ..
              CLEAR_PERSISTENT_WOOD .. " Wood, at this tile."
    end
    broadcastEvent("proc", how .. " Left standing, it festers +1 Doom every Dawn.")
end

-----------------------------------------------------------------------
-- Effect hooks. Each is called from the verb that owns the rule; keeping
-- them here means the card's whole behaviour reads in one place.
-----------------------------------------------------------------------

-- Move (doMove, actions.lua). Keyed on the tile being LEFT — both printed
-- rules are about getting out. Returns four values, actions and hunger kept
-- apart so each surcharge is blamed on the card that actually charged it:
--   extraActions, actionNames, extraHunger, hungerNames
function persistentMoveSurcharge(fromLoc)
    local acts, actNames = persistentRuleTotal(fromLoc, "moveActionCost")
    local hunger, hungerNames = persistentRuleTotal(fromLoc, "moveOutHunger")
    return acts, actNames, hunger, hungerNames
end

-- Gather (gatherRandomResources, actions.lua): Contaminated Water takes Food
-- off this tile's yield table. If Food is ALL the tile yields the gather
-- fails rather than silently handing out something else.
function persistentFilterYields(locName, yields)
    local holder = persistentRuleHolder(locName, "noFoodGather")
    if not holder then return yields, nil end
    local kept = {}
    for _, r in ipairs(yields) do
        if r ~= "Food" then kept[#kept + 1] = r end
    end
    if #kept == 0 then return nil, holder.name end
    return kept, holder.name
end

-- Eat Raw (doEatRaw, actions_social.lua): Contaminated Water makes it worse.
function persistentRawFoodSanityCost(locName)
    local holder = persistentRuleHolder(locName, "rawFoodSanity")
    if not holder then return 1, nil end
    return holder.rule.rawFoodSanity or 1, holder.name
end

-- Rest (doRest, actions.lua) and Barricade (canBarricade/doBarricade,
-- actions_social.lua): the two things Roots Through the Floor forbids.
function persistentBlocksRest(locName)
    local holder = persistentRuleHolder(locName, "restRestoresNothing")
    return holder and holder.name or nil
end

function persistentBlocksBarricade(locName)
    local holder = persistentRuleHolder(locName, "noBarricade")
    return holder and holder.name or nil
end

function persistentBlocksTrade(locName)
    local holder = persistentRuleHolder(locName, "noTrade")
    return holder and holder.name or nil
end

-- Night draw (resolveNightAtLocation, night.lua): The Nest.
function persistentNightThreatBonus(locName)
    return persistentRuleTotal(locName, "nightThreats")
end

-- Tick (resolveTick, tick_victory.lua): the Hungry Dog eats. It takes from
-- whoever at its tile has the most Food, so the loss is real rather than
-- landing on whichever colour pairs() happened to hand back first.
function resolvePersistentTick()
    for locName, list in pairs(persistentThreatsEverywhere()) do
        local eaten = 0
        for _, p in ipairs(list) do eaten = eaten + (p.rule.eatsFoodAtTick or 0) end
        for _ = 1, eaten do
            local bestColor, bestFood = nil, 0
            for color, ch in pairs(gameState.activeChars) do
                if not ch.down and ch.location == locName then
                    local held = (getPlayerResources(color) or {}).Food or 0
                    if held > bestFood then bestColor, bestFood = color, held end
                end
            end
            if bestColor then
                takeResourceFromPlayer(bestColor, "Food", 1)
                broadcastEvent("damage", gameState.activeChars[bestColor].name ..
                    " loses 1 Food at " .. locName .. " — something is eating at this tile.")
            end
        end
    end
end

-----------------------------------------------------------------------
-- CLEAR (2 actions + 1 Wood) — the removal path for the persistents that
-- are neither fightable nor sealed. Without it those six cards were a
-- permanent, un-payable +1 Doom per Dawn each.
-----------------------------------------------------------------------

-- The clearable persistents at this tile (not fought, not sealed).
function clearablePersistentsAt(locName)
    local out = {}
    for _, p in ipairs(persistentThreatsAt(locName)) do
        if not p.rule.fought and not p.rule.sealed then out[#out + 1] = p end
    end
    return out
end

-- Precondition check; the reason doubles as the why-disabled tooltip.
function canClearPersistent(color)
    local char = gameState.activeChars[color]
    if not char then return false, "No character." end
    if char.down then return false, "You are Down." end
    local targets = clearablePersistentsAt(char.location)
    if #targets == 0 then
        return false, "Nothing to clear at " .. (char.location or "?") .. "."
    end
    if (char.actionsLeft or 0) < CLEAR_PERSISTENT_ACTIONS then
        return false, "Clearing " .. targets[1].name .. " takes " ..
            CLEAR_PERSISTENT_ACTIONS .. " actions; you have " .. (char.actionsLeft or 0) .. "."
    end
    if ((getPlayerResources(color) or {}).Wood or 0) < CLEAR_PERSISTENT_WOOD then
        return false, "Clearing " .. targets[1].name .. " needs " ..
            CLEAR_PERSISTENT_WOOD .. " Wood."
    end
    return true, targets[1].name
end

function doClearPersistent(color)
    local ok, why = canClearPersistent(color)
    if not ok then
        broadcastToColor(why or "Nothing to clear.", color, BROADCAST_COLORS.damage)
        return false
    end
    local char = gameState.activeChars[color]
    local target = clearablePersistentsAt(char.location)[1]

    -- Actions first, then the Wood — and refund the actions if the Wood is
    -- not really there (verifyAndPayResources rescans the board), the same
    -- shape as doBarricade.
    if not spendAction(color, "Clear") then return false end
    char.actionsLeft = char.actionsLeft - (CLEAR_PERSISTENT_ACTIONS - 1)
    if not verifyAndPayResources(color, { Wood = CLEAR_PERSISTENT_WOOD }, "clearing " .. target.name) then
        char.actionsLeft = char.actionsLeft + CLEAR_PERSISTENT_ACTIONS
        return false
    end

    safecall(function()
        target.obj.setPositionSmooth(Vector(CLEARED_DISCARD_POS[1], CLEARED_DISCARD_POS[2],
                                            CLEARED_DISCARD_POS[3]), false, true)
        target.obj.setRotationSmooth({0, 180, 0}, false, true)
    end, "ClearPersistent")

    broadcastEvent("gain", char.name .. " clears " .. target.name .. " from " ..
        (char.location or "the tile") .. " — " .. CLEAR_PERSISTENT_ACTIONS ..
        " actions and " .. CLEAR_PERSISTENT_WOOD ..
        " Wood, and it stops festering at Dawn.")
    refreshPhaseBanner()
    return true
end
