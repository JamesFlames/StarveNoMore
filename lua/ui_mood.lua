-- ui_mood.lua  (I.3 Phase lighting + I.6 Safety-net confirms + I.11 Camera nudges)

-----------------------------------------------------------------------
-- I.3 — Phase-specific lighting transitions
-- Design §18.18: subtle environment shifts per sub-phase.
-----------------------------------------------------------------------

-- Baseline lighting set in D.3
LIGHTING_PRESETS = {
    Dawn = {
        LightIntensity = 0.60,
        AmbientIntensity = 1.0,
        AmbientSkyColor = {r=0.40, g=0.42, b=0.55},
    },
    Day = {
        LightIntensity = 0.55,
        AmbientIntensity = 1.0,
        AmbientSkyColor = {r=0.35, g=0.40, b=0.55},
    },
    Dusk = {
        LightIntensity = 0.50,
        AmbientIntensity = 0.95,
        AmbientSkyColor = {r=0.30, g=0.32, b=0.50},
    },
    Night = {
        LightIntensity = 0.38,
        AmbientIntensity = 0.85,
        AmbientSkyColor = {r=0.18, g=0.20, b=0.40},
    },
    Tick = {
        LightIntensity = 0.45,
        AmbientIntensity = 0.90,
        AmbientSkyColor = {r=0.25, g=0.28, b=0.45},
    },
}

-- Smoothly transition lighting to match the current sub-phase
function setPhaseMood(subPhase)
    local preset = LIGHTING_PRESETS[subPhase] or LIGHTING_PRESETS["Day"]

    -- Dawn gets a brief intensity flash before settling
    if subPhase == "Dawn" then
        Lighting.LightIntensity = 0.70
        Wait.time(function()
            Lighting.LightIntensity = preset.LightIntensity
        end, 0.5)
    else
        Lighting.LightIntensity = preset.LightIntensity
    end

    Lighting.AmbientIntensity = preset.AmbientIntensity
    Lighting.AmbientSkyColor = Color(preset.AmbientSkyColor.r, preset.AmbientSkyColor.g, preset.AmbientSkyColor.b)
end

-----------------------------------------------------------------------
-- I.6 — Safety-net confirmations on risky actions
-----------------------------------------------------------------------

-- Check if any players have unspent actions before ending Day
function confirmEndDayEarly(player, onConfirm)
    local unspent = {}
    for color, char in pairs(gameState.activeChars) do
        if not char.down and char.actionsLeft > 0 then
            table.insert(unspent, char.name .. " (" .. char.actionsLeft .. ")")
        end
    end

    if #unspent > 0 then
        showConfirm(
            "End Day phase early?",
            "These players still have actions:\n" .. table.concat(unspent, ", ") .. "\n\nUnused actions will be forfeited.",
            onConfirm
        )
    else
        onConfirm()
    end
end

-- Warn when sleeping alone at a sport court
function confirmSleepAloneAtCourt(color, location, onConfirm)
    local char = gameState.activeChars[color]
    if not char then
        if onConfirm then onConfirm() end
        return
    end

    local isCourt = location:find("Court") or location:find("Badminton") or location:find("Basketball")
    if not isCourt then
        if onConfirm then onConfirm() end
        return
    end

    -- Check if alone
    local othersHere = 0
    for c2, ch2 in pairs(gameState.activeChars) do
        if c2 ~= color and not ch2.down and ch2.location == location then
            othersHere = othersHere + 1
        end
    end

    if othersHere == 0 then
        showConfirm(
            "Sleep alone at " .. location .. "?",
            char.name .. " will draw +1 extra Threat and get no sleep regen.\n"
            .. "Charlie will likely attack (no house = no shelter).\n"
            .. "But survive the night and you salvage 2 resources at Dawn.",
            onConfirm
        )
    else
        onConfirm()
    end
end

-- Warn when spending the last Telltale Heart
function confirmLastHeart(reviverName, targetName, onConfirm)
    local heartCount = gameState.heartCount or 0
    if heartCount <= 1 then
        showConfirm(
            "Use the last Telltale Heart?",
            reviverName .. " will revive " .. targetName .. ", but this is the LAST heart.\n"
            .. "If another character goes Down, there won't be a way to revive them.\n"
            .. "Cook another heart when you can (1 Cloth + 1 Battery + 1 Food + 2 HP).",
            onConfirm
        )
    else
        onConfirm()
    end
end

-- Warn when moving an injured character to a high-threat location
function confirmMoveInjuredToThreat(color, targetLocation, onConfirm)
    local char = gameState.activeChars[color]
    if not char then
        if onConfirm then onConfirm() end
        return
    end

    local isCourt = targetLocation:find("Court") or targetLocation:find("Badminton") or targetLocation:find("Basketball")
    local isLowHealth = char.health < 3

    if isCourt and isLowHealth then
        showConfirm(
            "Move " .. char.name .. " to " .. targetLocation .. "?",
            char.name .. " has only " .. char.health .. " Health.\n"
            .. targetLocation .. " draws threat cards at night.\n"
            .. "This could be fatal. Proceed?",
            onConfirm
        )
    else
        onConfirm()
    end
end

-----------------------------------------------------------------------
-- I.11 — Camera nudges at major moments
-----------------------------------------------------------------------

-- Focus all players on a specific position briefly
function nudgeCameraAll(position, distance, duration)
    distance = distance or 20
    duration = duration or 2.0

    for _, p in ipairs(Player.getPlayers()) do
        if p.seated then
            p.lookAt({
                position = position,
                distance = distance,
                pitch    = 55,
            })
        end
    end
    -- Note: TTS doesn't have a built-in "return camera" API.
    -- Players can right-click to reset their view. The nudge is brief by nature.
end

-- Focus on a boss arrival at a location tile
function nudgeCameraToBoss(bossName, location)
    local tile = getLocationTile(location)
    if tile then
        nudgeCameraAll(tile.getPosition(), 18, 2.0)
        broadcastEvent("phase", "All eyes on " .. location .. "!")
    end
end

-- Focus on a high-severity Dawn card reveal
function nudgeCameraToDawnCard(card)
    if card and not card.isDestroyed() then
        nudgeCameraAll(card.getPosition(), 15, 2.0)
    end
end

-- Focus on the Doom marker when crossing a threshold
function nudgeCameraToDoom()
    local marker = getDoomMarker()
    if marker then
        nudgeCameraAll(marker.getPosition(), 20, 1.5)
    end
end
