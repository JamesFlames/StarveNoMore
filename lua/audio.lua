-- audio.lua
-- Game audio for Starve No More.
--
-- Behaviour:
--   - Each Dawn picks ONE ambient track (suburban pool, varied pool as a
--     fallback) and loops it until the day ends. Playtest: a mid-day track
--     change read as "did something just happen?" — repetition is the
--     cozy baseline, and a new day gets a new track.
--   - Night picks ONE low drone (sounds/ambient/night/) and loops it the
--     same way. Cozy dread needs a heartbeat, not silence.
--   - When a boss appears, ambient is suspended and a random sound from that
--     boss's folder plays. After the sound + 10s, if the boss is still alive,
--     another random sound plays. Loops until Audio.stopBossLoop() is called.
--     A live boss loop owns the soundscape through Night and Dawn.
--   - Tick fires a brief soft chime (sounds/sfx/tick_chime.wav).
--
-- Constraints:
--   TTS has only one global MusicPlayer, so chimes and boss roars briefly
--   take it over from the ambient track. After a one-shot, ambient resumes
--   from the appropriate phase (suburban or varied).
--
-- Depends on `AUDIO` table from audio_manifest.lua (auto-generated).

Audio = {
    state = {
        mode         = "idle",       -- "idle" | "ambient" | "night" | "boss"
        dayClip      = nil,          -- the ONE ambient clip looped all day
        nightClip    = nil,          -- the ONE drone looped all night
        bossName     = nil,          -- key into AUDIO.CREATURES when mode=="boss"
        nextHandle   = nil,          -- Wait.time handle for next scheduled clip
        watchHandle  = nil,          -- Wait.time handle for the load watchdog
    },
}

-- Clips whose URL failed to load this session ("Error: AudioClip could not
-- be loaded"). Blacklisted so a bad file costs one skip, not a silent
-- track-length hole in the soundscape every time it comes up.
local _failedUrls = {}

-- ---------------- internal helpers ----------------

local function _cancel()
    if Audio.state.nextHandle then
        Wait.stop(Audio.state.nextHandle)
        Audio.state.nextHandle = nil
    end
    if Audio.state.watchHandle then
        Wait.stop(Audio.state.watchHandle)
        Audio.state.watchHandle = nil
    end
end

-- Random pick that skips clips already known to fail.
local function _pickRandom(list)
    local playable = {}
    for _, c in ipairs(list or {}) do
        if c.url and not _failedUrls[c.url] then playable[#playable + 1] = c end
    end
    if #playable == 0 then return nil end
    return playable[math.random(1, #playable)]
end

local function _playClip(clip)
    if not clip or not clip.url then return end
    MusicPlayer.setCurrentAudioclip({
        url    = clip.url,
        title  = clip.name or "",
        artist = "Starve No More",
    })
    MusicPlayer.play()
end

-- Load watchdog: a few seconds after starting a clip, a MusicPlayer left in
-- "Stop" means the URL failed to load. Blacklist it and move on immediately
-- instead of sitting in silence until the scheduled track change. Only a
-- literal "Stop" counts — unknown/absent status (older TTS, headless stub)
-- is left alone.
local function _watchClip(clip, retryFn)
    if Audio.state.watchHandle then Wait.stop(Audio.state.watchHandle) end
    Audio.state.watchHandle = Wait.time(function()
        Audio.state.watchHandle = nil
        local status = nil
        pcall(function() status = MusicPlayer and MusicPlayer.player_status end)
        if status == "Stop" and clip and clip.url then
            _failedUrls[clip.url] = true
            log("Audio clip failed to load, skipping from now on: " .. tostring(clip.url),
                "WARN", "Audio")
            if retryFn then retryFn() end
        end
    end, 6)
end

-- Schedule the function `fn` to run after `delay` seconds. Replaces any
-- pending scheduled callback.
local function _scheduleNext(fn, delay)
    _cancel()
    Audio.state.nextHandle = Wait.time(fn, delay)
end

-- Day-ambience pool: suburban tracks, or the varied pool if none exist.
local function _dayPool()
    local pool = {}
    for _, c in ipairs(AUDIO.AMBIENT_SUBURBAN or {}) do pool[#pool + 1] = c end
    if #pool == 0 then
        for _, c in ipairs(AUDIO.AMBIENT_VARIED or {}) do pool[#pool + 1] = c end
    end
    return pool
end

-- Loop the day's single ambient clip (repick only if it failed to load).
local function _playNextDay()
    if Audio.state.mode ~= "ambient" then return end
    local clip = Audio.state.dayClip
    if not clip or not clip.url or _failedUrls[clip.url] then
        clip = _pickRandom(_dayPool())
        Audio.state.dayClip = clip
    end
    if not clip then return end
    _playClip(clip)
    _scheduleNext(_playNextDay, clip.duration or 180)
    _watchClip(clip, _playNextDay)
end

-- Loop the night's single drone while mode=="night".
local function _playNextNight()
    if Audio.state.mode ~= "night" then return end
    local clip = Audio.state.nightClip
    if not clip or not clip.url or _failedUrls[clip.url] then
        clip = _pickRandom(AUDIO.AMBIENT_NIGHT)
        Audio.state.nightClip = clip
    end
    if not clip then return end
    _playClip(clip)
    _scheduleNext(_playNextNight, clip.duration or 72)
    _watchClip(clip, _playNextNight)
end

-- Boss loop: random roar, wait roar+10s, repeat while mode=="boss".
local function _bossStep()
    if Audio.state.mode ~= "boss" then return end
    local boss = Audio.state.bossName
    if not boss then return end
    local list = (AUDIO.CREATURES or {})[boss]
    local clip = _pickRandom(list)
    if not clip then return end
    _playClip(clip)
    _scheduleNext(_bossStep, (clip.duration or 4) + 10.0)
    _watchClip(clip, _bossStep)
end

-- Resume the day's looped ambient (used after chime / boss-defeat).
local function _resumeAmbient()
    Audio.state.mode = "ambient"
    Audio.state.bossName = nil
    _playNextDay()
end

-- ---------------- public API ----------------

-- Called at the start of a new in-game day (Dawn). A fresh day picks a
-- fresh track — then loops it until nightfall. A live boss loop keeps
-- the soundscape — the roars don't stop for sunrise.
function Audio.startDayAmbience()
    if Audio.state.mode == "boss" then return end
    _cancel()
    Audio.state.dayClip = _pickRandom(_dayPool())
    Audio.state.nightClip = nil
    _resumeAmbient()
end

-- Called at Night start. Picks one low drone and loops it; a live boss
-- loop keeps priority (the thing outside is louder than the wind).
function Audio.startNightAmbience()
    if Audio.state.mode == "boss" then return end
    _cancel()
    Audio.state.mode = "night"
    Audio.state.nightClip = _pickRandom(AUDIO.AMBIENT_NIGHT)
    _playNextNight()
end

-- Hard stop (kept for edge cases / manual host control).
function Audio.stopAmbience()
    _cancel()
    Audio.state.mode = "idle"
    Audio.state.bossName = nil
    if MusicPlayer and MusicPlayer.pause then
        MusicPlayer.pause()
    end
end

-- Map a threat/card name to a boss key in AUDIO.CREATURES, or nil if there's
-- no audio for it. Used by combat.lua so we can stop the boss loop when its
-- HP hits zero without combat needing to know about audio internals.
function Audio.threatNameToBossKey(name)
    if not name then return nil end
    local lower = string.lower(name)
    if string.find(lower, "deerclops")  then return "deerclops" end
    if string.find(lower, "eye of terror") or string.find(lower, "eye_of_terror") then return "eye_of_terror" end
    if string.find(lower, "bearger")   then return "bearger" end
    if string.find(lower, "treeguard") then return "treeguard" end
    return nil
end

-- Called when a boss appears. boss_name must match a key in AUDIO.CREATURES
-- (e.g. "bearger", "deerclops", "eye_of_terror", "treeguard"). If the boss
-- has no audio (e.g. "the_source"), this is a no-op so ambient continues.
function Audio.playBossLoop(boss_name)
    if not boss_name then return end
    local list = (AUDIO.CREATURES or {})[boss_name]
    if not list or #list == 0 then return end
    Audio.state.mode = "boss"
    Audio.state.bossName = boss_name
    _bossStep()
end

-- Called when a boss is defeated. Resumes whatever ambience fits the hour.
function Audio.stopBossLoop(boss_name)
    -- If a different boss is currently active, ignore.
    if boss_name and Audio.state.bossName ~= boss_name then return end
    _cancel()
    Audio.state.bossName = nil
    if gameState and gameState.subPhase == "Night" then
        Audio.state.mode = "night"
        _playNextNight()
    else
        _resumeAmbient()
    end
end

-- Play a one-shot SFX by key (any clip in AUDIO.SFX). Briefly interrupts
-- the ambient or boss track and restores it when the SFX ends.
function Audio.playSFX(key)
    local clip = AUDIO.SFX and AUDIO.SFX[key]
    if not clip then return end
    local resumeMode = Audio.state.mode
    local resumeBoss = Audio.state.bossName
    _cancel()
    _playClip(clip)
    local d = (clip.duration or 1.5) + 0.2
    Audio.state.nextHandle = Wait.time(function()
        if resumeMode == "ambient" then
            _resumeAmbient()
        elseif resumeMode == "night" then
            Audio.state.mode = "night"
            _playNextNight()
        elseif resumeMode == "boss" and resumeBoss then
            Audio.state.mode = "boss"
            Audio.state.bossName = resumeBoss
            _bossStep()
        end
    end, d)
end

-- Convenience names for the project's specific SFX events.
function Audio.playChime()       Audio.playSFX("tick_chime")          end
function Audio.playTurnPing()    Audio.playSFX("turn_ping")           end
function Audio.playWalk()        Audio.playSFX("character_walk")      end
function Audio.playTradeChat()   Audio.playSFX("character_talktrade") end
function Audio.playMeet()        Audio.playSFX("character_meet")      end
function Audio.playDeath()       Audio.playSFX("character_death")     end
function Audio.playGrowl()       Audio.playSFX("night_growl")         end
