-- audio.lua
-- Game audio for Starve No More.
--
-- Behaviour:
--   - Day starts with a randomly-selected suburban ambient track.
--   - When that track finishes, varied ambient tracks play one after another.
--   - Night stops ambience entirely.
--   - When a boss appears, ambient is suspended and a random sound from that
--     boss's folder plays. After the sound + 10s, if the boss is still alive,
--     another random sound plays. Loops until Audio.stopBossLoop() is called.
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
        mode         = "idle",       -- "idle" | "ambient" | "boss"
        ambientPhase = "suburban",   -- "suburban" (first track of day) | "varied"
        bossName     = nil,          -- key into AUDIO.CREATURES when mode=="boss"
        nextHandle   = nil,          -- Wait.time handle for next scheduled clip
    },
}

-- ---------------- internal helpers ----------------

local function _cancel()
    if Audio.state.nextHandle then
        Wait.stop(Audio.state.nextHandle)
        Audio.state.nextHandle = nil
    end
end

local function _pickRandom(list)
    if not list or #list == 0 then return nil end
    return list[math.random(1, #list)]
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

-- Schedule the function `fn` to run after `delay` seconds. Replaces any
-- pending scheduled callback.
local function _scheduleNext(fn, delay)
    _cancel()
    Audio.state.nextHandle = Wait.time(fn, delay)
end

-- Play one varied ambient track and schedule the one after.
local function _playNextVaried()
    if Audio.state.mode ~= "ambient" then return end
    Audio.state.ambientPhase = "varied"
    local clip = _pickRandom(AUDIO.AMBIENT_VARIED)
    if not clip then return end
    _playClip(clip)
    _scheduleNext(_playNextVaried, clip.duration or 180)
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
end

-- Resume ambient at the right phase (used after chime / boss-defeat).
local function _resumeAmbient()
    Audio.state.mode = "ambient"
    Audio.state.bossName = nil
    if Audio.state.ambientPhase == "suburban" then
        local clip = _pickRandom(AUDIO.AMBIENT_SUBURBAN)
        if clip then
            _playClip(clip)
            Audio.state.ambientPhase = "varied"  -- next track will be varied
            _scheduleNext(_playNextVaried, clip.duration or 180)
        end
    else
        _playNextVaried()
    end
end

-- ---------------- public API ----------------

-- Called at the start of a new in-game day (Dawn).
function Audio.startDayAmbience()
    Audio.state.ambientPhase = "suburban"  -- fresh day -> start with suburban
    _resumeAmbient()
end

-- Called at Night start. Stops music entirely.
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

-- Called when a boss is defeated. Resumes day ambience.
function Audio.stopBossLoop(boss_name)
    -- If a different boss is currently active, ignore.
    if boss_name and Audio.state.bossName ~= boss_name then return end
    _cancel()
    _resumeAmbient()
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
        elseif resumeMode == "boss" and resumeBoss then
            Audio.state.mode = "boss"
            Audio.state.bossName = resumeBoss
            _bossStep()
        end
    end, d)
end

-- Convenience names for the project's specific SFX events.
function Audio.playChime()       Audio.playSFX("tick_chime")          end
function Audio.playWalk()        Audio.playSFX("character_walk")      end
function Audio.playTradeChat()   Audio.playSFX("character_talktrade") end
function Audio.playMeet()        Audio.playSFX("character_meet")      end
function Audio.playDeath()       Audio.playSFX("character_death")     end
