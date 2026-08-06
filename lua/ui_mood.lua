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

-- Guard on the host's End Turn button (ui_controls.lua): it pushes the game
-- past whoever is up, and their unspent actions are gone. The list names
-- everyone still holding actions, because the useful question is not just
-- "are you sure" but "is the table actually finished?".
--
-- pairs() order is arbitrary, so the names are sorted — a confirm dialog
-- that reshuffles its list between openings reads as a different warning.
function confirmEndDayEarly(activeColor, onConfirm, sourceButtonId)
    local unspent, active = {}, nil
    for color, char in pairs(gameState.activeChars) do
        if not char.down and (char.actionsLeft or 0) > 0 then
            local entry = char.name .. " (" .. char.actionsLeft .. ")"
            table.insert(unspent, entry)
            if color == activeColor then active = char end
        end
    end
    table.sort(unspent)

    if not active then
        -- Whoever is up has nothing left to spend; nothing is being lost.
        onConfirm()
        return
    end

    showConfirm(
        "End " .. active.name .. "'s turn early?",
        active.name .. " still has " .. active.actionsLeft ..
        " action(s), and ending the turn forfeits them.\n\n" ..
        "Still holding actions: " .. table.concat(unspent, ", "),
        onConfirm, nil, sourceButtonId
    )
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
function confirmLastHeart(reviverName, targetName, onConfirm, sourceButtonId)
    local heartCount = gameState.heartCount or 0
    if heartCount <= 1 then
        showConfirm(
            "Use the last Telltale Heart?",
            reviverName .. " will revive " .. targetName .. ", but this is the LAST heart.\n"
            .. "If another character goes Down, there won't be a way to revive them.\n"
            .. "Cook another heart when you can (1 Cloth + 1 Battery + 1 Provisions + 2 HP).",
            onConfirm, nil, sourceButtonId
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

-- Focus on the Dawn card as it is revealed (day_loop._dawnCardRevealed).
-- The handle routinely arrives dead here — the card is mid-flight from the
-- deck and may already have merged — so this asks isLiveObject rather than
-- isDestroyed(), which would throw on exactly the handles it is screening.
function nudgeCameraToDawnCard(card)
    if isLiveObject(card) then
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
