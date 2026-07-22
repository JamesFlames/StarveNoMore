-- ui_mood.lua  (I.3 Phase lighting + I.6 Safety-net confirms + I.11 Camera nudges)

-----------------------------------------------------------------------
-- I.3 — Phase-specific lighting transitions
-- Design §18.18: subtle environment shifts per sub-phase.
-----------------------------------------------------------------------

-- Per-phase lighting (overrides the save's baseline Lighting block once
-- play starts). Lifted ~45% from the original dim values so the character
-- standees read clearly against the night-suburb board, while keeping the
-- Day > Dusk > Night gradient so the mood still darkens toward night.
-- Mirror of the raise in build_save.py's Lighting block.
LIGHTING_PRESETS = {
    Dawn = {
        LightIntensity = 0.85,
        AmbientIntensity = 1.30,
        AmbientSkyColor = {r=0.52, g=0.54, b=0.66},
    },
    Day = {
        LightIntensity = 0.80,
        AmbientIntensity = 1.30,
        AmbientSkyColor = {r=0.50, g=0.54, b=0.66},
    },
    Dusk = {
        LightIntensity = 0.68,
        AmbientIntensity = 1.15,
        AmbientSkyColor = {r=0.42, g=0.44, b=0.60},
    },
    Night = {
        LightIntensity = 0.55,
        AmbientIntensity = 1.05,
        AmbientSkyColor = {r=0.32, g=0.34, b=0.52},
    },
    Tick = {
        LightIntensity = 0.62,
        AmbientIntensity = 1.10,
        AmbientSkyColor = {r=0.38, g=0.40, b=0.56},
    },
}

-- Transition lighting to match the current sub-phase.
-- NOTE: the runtime Lighting API uses snake_case properties + setters +
-- apply() — the PascalCase names (LightIntensity etc.) exist only in the
-- save JSON and throw "cannot access field" at runtime.
function setPhaseMood(subPhase)
    if not Lighting then return end
    local preset = LIGHTING_PRESETS[subPhase] or LIGHTING_PRESETS["Day"]

    local function applyPreset(intensity)
        Lighting.light_intensity = intensity
        Lighting.ambient_intensity = preset.AmbientIntensity
        local c = preset.AmbientSkyColor
        Lighting.setAmbientSkyColor({r = c.r, g = c.g, b = c.b})
        Lighting.apply()
    end

    -- Dawn gets a brief intensity flash before settling
    if subPhase == "Dawn" then
        applyPreset(0.95)
        Wait.time(function() applyPreset(preset.LightIntensity) end, 0.5)
    else
        applyPreset(preset.LightIntensity)
    end
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
