-- ui_help_pages.lua — pagination for the Help panel, and the Rulebook tab.
--
-- Why this exists (docs/tts-interface.md; Design §18.17, §18.19 item 3):
--
-- A TTS `Text` element renders what fits and CLIPS the rest. No scrollbar, no
-- ellipsis, no warning, no error. The Quick Start notecard already taught this
-- lesson once (it cut off mid-word at "...the neighbo", which is why
-- QUICKSTART_CARD_BUDGET exists) — but the Help panel had the same bug at
-- larger scale and nobody had measured it: the Glossary is ~7,000 characters
-- against a body that holds roughly 2,000, so two thirds of the game's
-- reference material was invisible. The tab looked fine. It just stopped.
--
-- So every Help tab is paged. The pager splits on line boundaries, keeps a
-- heading with the text under it, and never splits mid-line.
--
-- The RULEBOOK tab is the point of the exercise: the whole player rulebook,
-- readable in the game. It is assembled from the same four sections and in the
-- same order as PlayerRules.md / PlayerRules.html
-- (scripts/generate_player_rules.py) — Quick Start, Full Rules, The
-- Characters, Glossary — out of the same content/ markdown, so the in-game
-- book and the browser book cannot drift.

-----------------------------------------------------------------------
-- Page geometry. helpBody is 498px tall at fontSize 12 inside a 430px
-- panel: ~34 rendered lines of ~64 characters. Budget is deliberately
-- under the true fit — a page that slightly underfills is invisible to
-- the player, and a page that overfills silently loses its last lines.
-----------------------------------------------------------------------
HELP_PAGE_LINES     = 31
HELP_PAGE_LINE_CHARS = 62

-- How many rendered lines a source line will wrap to.
local function wrappedLines(line)
    local n = string.len(line)
    if n == 0 then return 1 end
    return math.max(1, math.ceil(n / HELP_PAGE_LINE_CHARS))
end

-- An ALL-CAPS line is a heading: generate_notebook.py uppercases markdown
-- headings when it converts them to plain text. Starting a page on one reads
-- as a chapter break; ending a page on one orphans it from its content.
local function isHeading(line)
    local trimmed = line:match("^%s*(.-)%s*$")
    if trimmed == "" then return false end
    if string.len(trimmed) > 60 then return false end
    return trimmed == string.upper(trimmed) and trimmed:match("%a") ~= nil
end

-----------------------------------------------------------------------
-- Split text into a list of page strings.
-----------------------------------------------------------------------
function paginateHelpText(text, budget)
    budget = budget or HELP_PAGE_LINES
    local pages, current, used = {}, {}, 0

    local function flush()
        if #current > 0 then
            -- Trim trailing blanks so a page doesn't end in whitespace.
            while #current > 0 and current[#current]:match("^%s*$") do
                table.remove(current)
            end
            table.insert(pages, table.concat(current, "\n"))
            current, used = {}, 0
        end
    end

    for line in tostring(text or ""):gmatch("([^\n]*)\n?") do
        local cost = wrappedLines(line)
        -- Break BEFORE a heading that would otherwise land near the bottom of
        -- the page, so a section title is never orphaned from its first lines.
        -- The threshold is 0.8 rather than 0.5 deliberately: generate_notebook
        -- uppercases EVERY markdown heading, and the rulebook has dozens, so a
        -- half-full trigger broke pages so often the book ran to 23 pages of
        -- half-empty screen. Turning fewer, fuller pages is the better read.
        if isHeading(line) and used > budget * 0.8 then
            flush()
        elseif used + cost > budget then
            flush()
        end
        -- Never open a page with blank lines.
        if not (used == 0 and line:match("^%s*$")) then
            table.insert(current, line)
            used = used + cost
        end
    end
    flush()

    if #pages == 0 then pages = { "" } end
    return pages
end

-----------------------------------------------------------------------
-- The Rulebook tab body: the whole book, one string, paged by the caller.
--
-- Section order and titles MIRROR SECTIONS in
-- scripts/generate_player_rules.py — tests/test_cross_refs.py guards the
-- mirror, so the in-game rulebook and PlayerRules.html can't drift apart.
-- Quick Start comes from the difficulty-aware rewrite (§17.2): a Story or
-- Long Weekend table must not be handed Standard's numbers.
-----------------------------------------------------------------------
function rulebookText()
    local parts = {
        "STARVE NO MORE — PLAYER RULES",
        "",
        "The whole rulebook, in the game. Same text as PlayerRules.html.",
        "Use Back / More below to turn the pages.",
        "",
        "===== QUICK START =====",
        "",
        quickStartTextForVariant(),
        "",
        "===== FULL RULES =====",
        "",
        NOTEBOOK_FULL_RULES or "",
        "",
        "===== THE CHARACTERS =====",
        "",
        NOTEBOOK_CHARACTERS or "",
        "",
        "===== GLOSSARY =====",
        "",
        HELP_GLOSSARY or "",
    }
    return table.concat(parts, "\n")
end
