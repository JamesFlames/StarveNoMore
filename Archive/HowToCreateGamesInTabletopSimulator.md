# How To Create Games In Tabletop Simulator

> A reference manual for an AI agent whose job is to design, build, and ship playable mods for **Tabletop Simulator** (Berserk Games — Steam app `286160`). This document assumes the agent will produce JSON save files, Lua scripts, XML UI definitions, and Steam Workshop-ready assets. Treat it as both a design playbook and an API quick-reference.

---

## 0. Quick Glossary

| Term | Meaning |
|------|---------|
| **TTS** | Tabletop Simulator. |
| **Mod** | A user-made game/scenario, distributed as a save file plus referenced assets. |
| **Save** | A `.json` file describing the entire game state (objects, transforms, scripts, UI). |
| **Object** | Anything physical in the world — cards, dice, tokens, boards, figurines, custom models, zones, hands, containers. |
| **Bag / Deck / Infinite Bag** | Container objects that hold other objects. |
| **GUID** | Per-object 6-character hex ID auto-assigned by TTS; used as the primary handle for scripting. |
| **Global script** | The single top-level Lua script attached to the world. |
| **Object script** | Per-object Lua script that runs in that object's local scope. |
| **Scripting Zone / Trigger Zone** | Invisible volumes that detect objects entering/leaving. |
| **Hand Zone** | Per-player private area; cards inside are hidden from other players. |
| **Snap Point** | Magnetic position objects gravitate to when dropped nearby. |
| **State** | Stack of alternate looks/behaviors on a single object (e.g., a card with multiple faces). |
| **Workshop** | Steam Workshop, where mods are uploaded for distribution. |

---

## 1. What Tabletop Simulator Actually Is

TTS is a **physics sandbox** with a Lua scripting layer on top. It does *not* enforce rules — it gives you the table, the pieces, and the camera, then trusts the players (or your scripts) to play the game correctly. Anything you can model with rigid bodies, decals, and Lua callbacks is fair game; anything that needs continuous animation, complex AI, or non-tabletop interactions is the wrong tool.

Strengths to lean into:
- Physical handling: gravity, collisions, friction, throwing dice, flicking pieces.
- Multiplayer presence: voice, pointers, hand zones, hidden info per player.
- Component fidelity: high-res card faces, custom 3D models, audio cues.
- Rapid iteration: Lua hot-reload, JSON-editable saves.

Weaknesses to design around:
- Not a game engine — no animations beyond physics, no built-in AI opponents.
- Network sync is authoritative on the host; latency-sensitive logic is brittle.
- Lua sandbox lacks file I/O and most OS APIs (use `WebRequest` for net access).
- Performance ceiling on object count: keep working scenes well under ~2000 active objects.

---

## 2. Design Pipeline (Top-Down)

Before producing a single asset, the agent should answer these in order. Save the answers as a design brief inside the mod folder.

1. **Format.** Card game? Hex wargame? Roll-and-write? RPG map? This dictates which built-in primitives to lean on (Custom Deck vs. Custom Board vs. Tilemap of tiles).
2. **Player count and seating.** Maps to which `Player.Color` slots are active and where hand zones sit.
3. **Information model.** What is public, what is private (hand zones), what is hidden-but-known (face-down decks), what is hidden-and-unknown (bags, fog).
4. **Turn structure.** Free-form, scripted turn order, real-time? If turn-based, plan the Turns API up front.
5. **Win/lose triggers.** Are these enforced by script, or judged by players? If scripted, identify which zones / counters / states are observed.
6. **Components inventory.** Numbered list of every physical piece, with quantity and asset source.
7. **UI overlays.** What needs custom XML panels (score trackers, phase indicators, action buttons)?
8. **Setup automation.** Which steps the host must do manually vs. a `Setup()` button that deals/shuffles/places everything.

Only then start building.

---

## 3. Mod Anatomy on Disk

Tabletop Simulator stores per-user data under:

- **Windows:** `%USERPROFILE%\Documents\My Games\Tabletop Simulator\`
- **macOS:** `~/Library/Tabletop Simulator/`
- **Linux (Proton):** under the Steam compatdata prefix.

Key subfolders:

```
Tabletop Simulator/
├── Saves/                        # Saves you make from inside TTS (and Workshop subscriptions cache).
│   ├── TS_Save_*.json            # The save file itself.
│   └── TS_Save_*.png             # Thumbnail.
├── Mods/
│   ├── Models/                   # Cached .obj custom models keyed by URL hash.
│   ├── Images/                   # Cached textures / card sheets / table images.
│   ├── Audio/                    # Cached audio assets.
│   ├── PDF/
│   ├── Assetbundles/
│   └── Workshop/                 # Workshop subscriptions live here.
└── Screenshots/
```

**Important rule:** TTS does not bundle assets into the save by default. The save references each asset by URL (or local path, see below). If you ship a save file alone, TTS will re-download every URL on load. For distribution, either:
- Host every asset on a permanent CDN (Steam Cloud, imgur direct links, your own server with permissive CORS), **or**
- Use the in-game **Save & Load → Backup** which packages assets, **or**
- Publish via Steam Workshop, which uploads referenced assets automatically.

Local-only development is fine with `file:///C:/path/to/asset.png` URLs, but those break the moment anyone else loads the save.

---

## 4. The Save File (JSON Schema, Practical Subset)

A TTS save is a single JSON document. The agent should be comfortable producing and patching these directly. Top-level shape (most-used fields only):

```json
{
  "SaveName": "My Game",
  "GameMode": "My Game",
  "Date": "",
  "VersionNumber": "v13.x",
  "GameType": "",
  "GameComplexity": "",
  "Tags": [],
  "Gravity": 0.5,
  "PlayArea": 1.0,
  "Table": "Table_Hexagon",
  "Sky": "Sky_Museum",
  "Note": "",
  "TabStates": {},
  "LuaScript": "",
  "LuaScriptState": "",
  "XmlUI": "",
  "Grid":   { "Type": 0, "Lines": false, "Color": {"r":0,"g":0,"b":0}, "Offset": false, "BothSnapping": false, "xSize": 2, "ySize": 2 },
  "Lighting": { "LightIntensity": 0.54, "LightColor": {"r":1,"g":1,"b":1}, "AmbientIntensity": 1.3, "AmbientType": 1, "AmbientSkyColor": {...}, "AmbientEquatorColor": {...}, "AmbientGroundColor": {...}, "ReflectionIntensity": 1.0, "LutIndex": 0, "LutContribution": 1.0 },
  "Hands": { "Enable": true, "DisableUnused": false, "Hiding": 0 },
  "Turns":  { "Enable": false, "Type": 0, "TurnOrder": [], "Reverse": false, "SkipEmpty": false, "DisableInteractions": false, "PassTurns": true, "TurnColor": "" },
  "ObjectStates": [ /* array of Object entries — see §5 */ ],
  "DecalPallet": [],
  "MusicPlayer": {...},
  "ComponentTags": {...}
}
```

### 4.1 Object entry schema (subset)

Every entity in `ObjectStates` follows the same envelope. Type-specific fields are added on top.

```json
{
  "Name": "Custom_Model",
  "Transform": {
    "posX": 0.0, "posY": 1.0, "posZ": 0.0,
    "rotX": 0.0, "rotY": 180.0, "rotZ": 0.0,
    "scaleX": 1.0, "scaleY": 1.0, "scaleZ": 1.0
  },
  "Nickname": "Crown of Thorns",
  "Description": "",
  "GMNotes": "",
  "ColorDiffuse": { "r": 1.0, "g": 1.0, "b": 1.0 },
  "Tags": [],
  "LayoutGroupSortIndex": 0,
  "Value": 0,
  "Locked": false,
  "Grid": true,
  "Snap": true,
  "IgnoreFoW": false,
  "MeasureMovement": false,
  "DragSelectable": true,
  "Autoraise": true,
  "Sticky": true,
  "Tooltip": true,
  "GridProjection": false,
  "HideWhenFaceDown": false,
  "Hands": false,
  "CustomMesh": { /* model-specific, see §6.4 */ },
  "LuaScript": "",
  "LuaScriptState": "",
  "XmlUI": "",
  "GUID": "abc123",
  "States": { "2": { /* a full object entry for state index 2 */ } },
  "ContainedObjects": [ /* nested object entries for bags/decks */ ],
  "AttachedSnapPoints": [ {"Position": {"x":0,"y":0.1,"z":0}, "Rotation": {...}, "Tags": []} ]
}
```

### 4.2 Common `Name` values and what they mean

| `Name` | Object kind | Required extra fields |
|--------|-------------|------------------------|
| `Card`            | A single card. Generally lives inside a `Deck`. | `CardID`, `CustomDeck` lookup |
| `Deck` / `DeckCustom` | Stack of 2+ cards. | `DeckIDs`, `CustomDeck`, `ContainedObjects` |
| `Custom_Model`    | User-supplied 3D model. | `CustomMesh` |
| `Custom_Token`    | Flat shaped token from an image. | `CustomImage` with `CustomToken` |
| `Custom_Tile`     | Hex / square / circle / rounded tile. | `CustomImage` with `CustomTile` |
| `Custom_Dice`     | Custom-faced die. | `CustomImage` with `CustomDice` |
| `Custom_Board`    | Flat board image. | `CustomImage` |
| `Custom_PDF`      | In-game PDF viewer. | `CustomPDF` |
| `Custom_Assetbundle` | Imported Unity assetbundle. | `CustomAssetbundle` |
| `Bag` / `Custom_Model_Bag` / `Infinite_Bag` | Container. | `ContainedObjects` |
| `Notecard` / `Tablet` | Text / web-content props. | — |
| `Figurine_Custom` | Stand-up cardboard figure. | `CustomImage` with `CustomFigurine` |
| `Dice` (`Die_4` … `Die_20`)         | Standard polyhedral. | — |
| `HandTrigger`     | Hand zone. | `FogColor` |
| `ScriptingTrigger`| Invisible scripting zone. | — |
| `FogOfWarTrigger` / `FogOfWar` | Hidden-info volumes. | — |
| `Counter`         | Numeric counter widget. | — |
| `go_game_piece_white` etc. | Built-in chess/Go pieces. | — |

---

## 5. Object Categories — When To Use Which

### 5.1 Cards and Decks

A `Deck` is a stack of `Card` objects backed by a **Custom Deck Sheet**: a single image atlas where each card occupies one tile in a `width × height` grid, plus a separate back image (or a single hidden back tile).

- Atlas dimensions cap at **10 × 7 = 70 cards per sheet**. Larger decks are split across multiple `CustomDeck` entries inside the same deck object.
- `CardID` is `<deckId><index>`, e.g. deck `100` index `0` ⇒ `100`, index `1` ⇒ `101`, index `13` ⇒ `113`. Index runs left-to-right, top-to-bottom.
- For bleed-free results, render each card cell at the same pixel size; common sizes are 408×585 (poker) or 367×529 (bridge). Power-of-two atlas dimensions render slightly faster.

```json
"CustomDeck": {
  "100": {
    "FaceURL":   "https://cdn.example.com/deck_faces.png",
    "BackURL":   "https://cdn.example.com/deck_back.png",
    "NumWidth":  10,
    "NumHeight": 7,
    "BackIsHidden": true,
    "UniqueBack":  false,
    "Type": 0
  }
}
```

### 5.2 Custom Models

Use for any 3D piece (miniatures, terrain, custom dice with non-standard mesh). Required URLs:

```json
"CustomMesh": {
  "MeshURL":     "https://cdn.example.com/dragon.obj",
  "DiffuseURL":  "https://cdn.example.com/dragon_diffuse.png",
  "NormalURL":   "",
  "ColliderURL": "",
  "Convex": true,
  "MaterialIndex": 3,
  "TypeIndex": 0,
  "CustomShader": { "SpecularColor": {...}, "SpecularIntensity": 0.1, "SpecularSharpness": 2, "FresnelStrength": 0.1 },
  "CastShadows": true
}
```

- `MaterialIndex`: 0 plastic, 1 wood, 2 metal, 3 cardboard, 4 glass.
- `TypeIndex`: 0 generic, 1 figurine, 2 dice, 3 coin, 4 board, 5 chip, 6 bag, 7 infinite bag.
- Provide a separate convex `ColliderURL` for complex meshes — the visual mesh is a poor collider above ~5k tris.
- `.obj` is the only mesh format (with `.mtl` ignored — TTS uses the explicit URL fields). Keep models under ~50k tris for performance.

### 5.3 Tokens vs. Tiles vs. Figurines

- **Custom Token** — flat cutout following the alpha of an image, configurable thickness. Best for non-rectangular game pieces.
- **Custom Tile** — solid prism (square / hex / circle / rounded), image on top. Best for terrain hexes, location boards.
- **Custom Figurine** — stand-up cardboard standee, two-sided.
- **Custom Board** — flat oversized tile, no thickness, locked-by-default. Use for the play area.

### 5.4 Dice

- For **standard polyhedral**, use `Die_4`, `Die_6`, `Die_8`, `Die_10`, `Die_12`, `Die_20`.
- For **custom faces**, use `Custom_Dice` with a face atlas:
  - d4: 1×4, d6: 3×2, d8: 4×2, d10: 5×2, d12: 4×3, d20: 5×4.
- Rolling is `obj.roll()`. Read result with `obj.getValue()` once `obj.resting` is true.

### 5.5 Containers

- **Bag** — opaque, you can see how many items are inside but not what they are.
- **Custom Model Bag** — a bag whose mesh you supply (treasure chest, deck box).
- **Infinite Bag** — endless supply of identical items; great for resource cubes.
- **Deck** — implicitly a container of cards.

Containers preserve their `ContainedObjects` in JSON, which is the easiest way to script-generate complex starting setups: build the bag's contents in code, drop them in, then save.

### 5.6 Zones

- **Hand Zone (`HandTrigger`)** — assigned to a player color; objects inside are private to that player. Always create one per seated player.
- **Scripting Zone (`ScriptingTrigger`)** — invisible, dispatches `onObjectEnterScriptingZone` / `onObjectLeaveScriptingZone`. Use for "is this card in the discard pile?" checks.
- **Snap Point** — not a zone; an attractor coordinate on a parent object. Use these for grids of card slots, miniature bases, etc.
- **Fog of War Zone** — hides everything inside from non-GM players. Pair with `IgnoreFoW = true` on board pieces.

---

## 6. Lua Scripting — The Core API

TTS runs **MoonSharp Lua 5.2** with Berserk-specific bindings. Every save has one **Global** script and any number of **Object** scripts; they share no scope by default — communicate via `getObjectFromGUID(...).call("FunctionName", argsTable)` or `Global.call(...)`.

### 6.1 Lifecycle callbacks

Implement these as global functions in any script. They fire automatically.

| Callback | When it fires | Notes |
|----------|---------------|-------|
| `onLoad(saved_state)` | Save loaded, scene ready. | Receives the previously saved Lua state string. |
| `onSave()` → `string` | Game is being saved. Return the state to persist. | Stringify state with `JSON.encode(t)`. |
| `onUpdate()` | Every frame. | Avoid heavy logic — prefer event-driven callbacks. |
| `onFixedUpdate()` | Physics tick. | |
| `onPlayerTurn(player, previous)` | Turns API advances. | Only fires when Turns are enabled. |
| `onPlayerChangeColor(color)` | Seat reassigned. | |
| `onPlayerConnect(player)` / `onPlayerDisconnect(player)` | Player joins/leaves. | |
| `onChat(message, player)` → `bool` | Chat message. Return `false` to suppress. | |
| `onObjectDrop(player_color, obj)` | Object released by a player. | |
| `onObjectPickUp(player_color, obj)` | Object grabbed by a player. | |
| `onObjectEnterContainer(container, obj)` | Anything dropped into a bag/deck. | |
| `onObjectLeaveContainer(container, obj)` | Anything pulled out. | |
| `onObjectEnterScriptingZone(zone, obj)` / `Leave` | Scripting zone events. | |
| `onObjectSpawn(obj)` / `onObjectDestroy(obj)` | Lifecycle. | `obj` may be partially initialized in `Spawn`. |
| `onObjectRandomize(obj, color)` | Player pressed `R` to shuffle/roll. | |
| `onObjectStateChange(obj, old_obj_state)` | State swap on a multi-state object. | |

There are **per-object** versions of most (e.g. `onPickUp(player_color)`, `onDrop(player_color)`, `onCollisionEnter(info)`). Define those inside the object's own Lua script — they receive `self` implicitly.

### 6.2 Global helpers

| Function | Purpose |
|---|---|
| `getObjectFromGUID(guid)` | Look up by GUID. Returns `nil` if missing. |
| `getAllObjects()` | All world objects (excludes things inside containers). |
| `getObjects()` | Synonym; varies by version. |
| `getSeatedPlayers()` | Array of color strings for seats currently occupied. |
| `Player[color]` | The Player object for a color. |
| `Player.getPlayers()` | All connected Player objects. |
| `spawnObject(params)` | Spawn a built-in object by name. |
| `spawnObjectJSON{ json = "...", position = {...}, callback_function = function(o) end }` | Spawn from a JSON blob (powerful — paste any object-shaped JSON). |
| `spawnObjectData{ data = table, position = ... }` | Same but with a Lua table. |
| `WebRequest.get(url, callback)` / `WebRequest.put` / `WebRequest.post` | HTTP. |
| `JSON.encode(t)` / `JSON.decode(s)` | Built-in JSON. |
| `Wait.frames(fn, n)` / `Wait.time(fn, seconds)` / `Wait.condition(fn, predicate, timeout?, on_timeout?)` | Scheduling without busy-loops. |
| `Timer.create{ identifier, function_name, parameters, delay, repetitions }` | Legacy timers — prefer `Wait`. |
| `printToAll(msg, color)` / `printToColor(msg, color, color)` / `broadcastToAll` / `broadcastToColor` | Chat output. |
| `UI.setXml(xml)` / `UI.setAttribute` / `UI.show` / `UI.hide` | Top-level UI. |
| `Notes.setNotebookTabs(tbl)` / `Notes.getNotebookTabs()` | Player notebook. |
| `Turns.enable`, `Turns.order`, `Turns.turn_color` | Turn manager. |
| `Hands.enable`, `Hands.disable_unused` | Hand zone toggles. |
| `Lighting.light_color`, `Lighting.ambient_intensity` | Mood control. |
| `setLuaScript(guid, str)` | Hot-replace a script (rare; usually edit in the editor). |

### 6.3 Object methods (called via `obj:method()` or `obj.method`)

A non-exhaustive but representative list:

**Identity / metadata**
- `getGUID()`, `getName()`, `getDescription()`, `setDescription(s)`
- `getGMNotes()`, `setGMNotes(s)` — invisible to non-GM players, perfect for storing per-object data.
- `getNickname()`, `setNickname(s)`
- `getValue()`, `setValue(v)` — die value, card value, counter value, depending on type.
- `getCustomObject()`, `setCustomObject(t)` — read/write the `CustomMesh`/`CustomImage` table.

**Transform**
- `getPosition()`, `setPosition(v)`, `setPositionSmooth(v, collide?, fast?)`
- `getRotation()`, `setRotation(v)`, `setRotationSmooth(v, collide?, fast?)`
- `getScale()`, `setScale(v)`
- `translate(v)`, `rotate(v)`, `scale(v)` — relative.
- `getBounds()` — `{center, size, offset}` AABB.

**Physics / interaction state**
- `isSmoothMoving()`, `resting`, `held_by_color`, `interactable`
- `setLock(b)`, `getLock()` — physics frozen.
- `addForce(v, type)`, `addTorque(v, type)` — `type`: 1 force, 2 acceleration, 3 impulse, 4 velocity-change.

**Cards / Decks**
- `flip()`, `is_face_down`
- `takeObject{ position, rotation, smooth, top, callback_function, ... }` — pull a card off a deck or item out of a bag.
- `putObject(other)` — combine into a deck/bag.
- `shuffle()`, `randomize()`
- `deal(n, color, slot?)`
- `getObjects()` (on a deck) — list contained card data.
- `remainder` is exposed via `take_callback` when a deck is reduced to one card.

**Containers**
- `getObjects()` — list contents (bags only return summary entries).
- `reset()` — restore Infinite Bag.
- `clearButtons()` etc. for UI on the bag itself.

**States**
- `setState(index)` — switch to alt state; current object is replaced (returns the new object).
- `getStates()` — list state metadata.

**Custom UI per object**
- `createButton(params)`, `editButton(params)`, `removeButton(index)`, `getButtons()`
- `createInput(params)`, `editInput`, `removeInput`, `getInputs()`
- `UI` per-object proxy supporting all the same XML methods as global UI.

**Tags**
- `addTag(s)`, `removeTag(s)`, `getTags()`, `hasTag(s)`, `setTags(t)` — used for filtering in scripting zones, Search, and snap-point matching.

**Inter-object calls**
- `call(funcName, paramsTable?)` — invoke a function defined in this object's script.
- `setLuaScript(s)`, `getLuaScript()`
- `setVar(name, value)`, `getVar(name)` — read/write top-level globals in another object's script scope.
- `setTable(name, t)`, `getTable(name)`
- `script_state` — string the object should restore on load (set inside `onSave`).

### 6.4 Player object (`Player[color]`)

- `color`, `steam_name`, `steam_id`, `host`, `seated`, `admin`, `promoted`, `team`
- `getHandObjects(index?)`, `getHandCount()`, `getHandTransform()`
- `getHoldingObjects()`, `getSelectedObjects()`
- `lookAt{ position, pitch?, yaw?, distance? }`
- `setHandCount(n)`, `changeColor(c)`, `kick(), ban()`
- `pingTable(v)` — visible ping at world position.
- `attachCameraToObject{ object, offset? }`

### 6.5 Scheduling, randomness, math helpers

- `math.random()` is seeded per-host on load. Sync sensitive shuffles via the host or call `obj.shuffle()` (server-authoritative).
- Use `Wait.condition(fn, predicate)` to wait for `obj.resting == true` before reading dice values.
- Avoid blocking loops; `coroutine` works but the conventional pattern in TTS is chained `Wait` callbacks.

### 6.6 Coroutine pattern (canonical)

```lua
function startCoroutine(name)
  function coroutine_step()
    -- step 1
    coroutine.yield(0)
    -- step 2 ... etc.
    return 1
  end
  startLuaCoroutine(self, "coroutine_step")
end
```

`startLuaCoroutine(host, fn_name)` runs `fn_name` as a Lua coroutine on `host`. Yields are delayed to the next frame; return `1` to end. Useful for staged setup that needs intermediate physics settling.

---

## 7. UI Scripting (XML)

Each object (and the world) can carry an XML UI tree, edited from the **UI** tab next to the Lua script in the in-game editor.

### 7.1 Sample XML

```xml
<Defaults>
  <Button color="#222" textColor="#FFF" fontSize="22" />
  <Text color="#FFF" fontSize="24" />
</Defaults>

<Panel id="scorePanel" position="0 -300 -10" width="600" height="80" color="#0008" active="true">
  <HorizontalLayout childForceExpandWidth="true" spacing="20" padding="10 10 5 5">
    <Text id="redScore">Red: 0</Text>
    <Text id="blueScore">Blue: 0</Text>
    <Button id="endTurnBtn" onClick="endTurn">End Turn</Button>
  </HorizontalLayout>
</Panel>
```

### 7.2 Common elements

`Panel`, `HorizontalLayout`, `VerticalLayout`, `GridLayout`, `Text`, `Button`, `InputField`, `Image`, `Toggle`, `Dropdown`, `Slider`, `ProgressBar`, `Mask`, `Cell`, `Row`, `Defaults`.

### 7.3 Driving UI from Lua

```lua
function onLoad()
  UI.setAttribute("redScore", "text", "Red: 0")
end

function endTurn(player, value, id)
  -- player is the Player object that clicked, value/id are element-bound.
  Turns.turn_color = nextColor(player.color)
end
```

Useful UI methods (`UI` global or `obj.UI`):
- `setXml(xml)`, `getXml()`
- `setAttribute(id, key, value)`, `setAttributes(id, t)`
- `getAttribute(id, key)`, `getAttributes(id)`
- `show(id)`, `hide(id)`
- `setValue(id, value)` — for inputs/toggles/sliders.

Per-player visibility is the `visibility` attribute, which takes a pipe-separated color list (`Red|Blue`) or an `!` prefix (`!Red`) to negate.

### 7.4 In-world buttons (3D, no XML)

Quicker for quick affordances on a single object:

```lua
self.createButton({
  click_function = "incScore",
  function_owner = self,
  label          = "Score: 0",
  position       = {0, 0.2, 0},
  rotation       = {0, 180, 0},
  width          = 800, height = 300,
  font_size      = 240,
  color          = {0.1, 0.1, 0.1},
  font_color     = {1, 1, 1},
  tooltip        = "Click to add a point",
})

function incScore(obj, color, alt_click)
  score = (score or 0) + 1
  self.editButton({ index = 0, label = "Score: " .. score })
end
```

`createInput` is the textbox cousin and supports `validation`, `alignment`, `tab`, `onValueChanged` patterns.

---

## 8. Common Patterns / Recipes

### 8.1 Setup button that deals starting hands

```lua
DECK_GUID = "abcdef"
PLAYERS   = { "Red", "Blue", "Green", "Yellow" }

function onLoad()
  self.createButton({
    click_function="doSetup", function_owner=self,
    label="Start Game", position={0,0.2,0}, width=900, height=300, font_size=180
  })
end

function doSetup()
  local deck = getObjectFromGUID(DECK_GUID)
  if not deck then broadcastToAll("Deck missing", {1,0,0}) return end
  deck.shuffle()
  Wait.time(function()
    for _, color in ipairs(PLAYERS) do
      if Player[color].seated then deck.deal(5, color) end
    end
  end, 1.0)
end
```

### 8.2 Discard pile via Scripting Zone

```lua
DISCARD_ZONE_GUID = "111222"

function onObjectEnterScriptingZone(zone, obj)
  if zone.getGUID() ~= DISCARD_ZONE_GUID then return end
  if obj.tag ~= "Card" then return end
  obj.flip()  -- ensure face up
end
```

### 8.3 Score counter synced to UI

```lua
score = { Red = 0, Blue = 0 }

function addScore(params)  -- callable via Global.call
  score[params.color] = score[params.color] + (params.delta or 1)
  UI.setAttribute(params.color:lower().."Score", "text", params.color..": "..score[params.color])
end
```

Any object can do `Global.call("addScore", {color="Red", delta=2})`.

### 8.4 Persisting state across save/load

```lua
function onSave()
  return JSON.encode({ score = score, round = round })
end

function onLoad(savedState)
  if savedState and savedState ~= "" then
    local t = JSON.decode(savedState)
    score = t.score or { Red=0, Blue=0 }
    round = t.round or 1
  else
    score = { Red=0, Blue=0 }; round = 1
  end
end
```

### 8.5 Spawning a custom card programmatically

```lua
spawnObjectJSON({
  json = JSON.encode({
    Name = "Card",
    Transform = { posX=0, posY=2, posZ=0, rotX=0, rotY=180, rotZ=0, scaleX=1, scaleY=1, scaleZ=1 },
    Nickname = "Goblin Scout",
    CardID = 100,
    CustomDeck = {
      ["1"] = { FaceURL="https://.../faces.png", BackURL="https://.../back.png", NumWidth=1, NumHeight=1, BackIsHidden=true, UniqueBack=false, Type=0 }
    }
  }),
  callback_function = function(o) o.setLock(false) end
})
```

### 8.6 Detecting stable dice

```lua
function rollAndRead(die, onResult)
  die.roll()
  Wait.condition(function() onResult(die.getValue()) end,
                 function() return die.resting end,
                 5.0,
                 function() onResult(nil) end)
end
```

---

## 9. Building the Mod — End-to-End Workflow

The agent should follow this loop when constructing a new mod from scratch.

1. **Scaffold a save.** Start in TTS from *Create → Single Player → Classic* (or load an existing template). Save immediately under a unique name; the JSON now exists on disk.
2. **Stage assets.** Upload card sheets, model files, and textures to a stable HTTPS host. Confirm each URL returns the asset directly with `Content-Type` matching the kind (PNG/JPG/OBJ/MP3/OGG/WAV).
3. **Place components.** Either:
   - Import via the in-game `Objects → Components → Custom` panels (recommended for first pass), **or**
   - Hand-edit the saved JSON to splice in object entries (for bulk placement of dozens of identical pieces).
4. **Snap & lock.** Lock the table-side board, set snap points (Gizmo tool), and confirm hand zones are correct.
5. **Wire scripting.** Open the Scripting window (`</>` icon), paste Global Lua, paste per-object Lua, save (Ctrl+S inside the editor) — TTS hot-applies. Use `print(...)` and `log(t)` for debug.
6. **Test multiplayer behavior.** Use `Host` mode and `Spectate as another color` (or join with a second account/instance) to verify hidden info and turn flow.
7. **Iterate on save/load.** Save, reload from disk — anything not persisted via `onSave` must be reconstructed in `onLoad`.
8. **Polish UX.**
   - Tooltips on every interactable.
   - GM Notes for hidden setup data.
   - Tags so Search and zones behave.
   - Notebook entries for rules summary, per-player crib sheets.
9. **Workshop publish.** *Games → Save & Load → Steam Workshop → Upload*. Provide title, description, tags (`Card Games`, `Strategy`, etc.), and a 512×512 thumbnail. Mark `Mod Caching` on so subscribers don't redownload assets.
10. **Ship a "Setup" save and a "Mid-game" save.** Players appreciate a clean pristine starting save plus a worked example.

---

## 10. Multiplayer, Permissions, and Hidden Information

- **Host authority.** All physics and state are simulated on the host; clients receive snapshots. Scripts run on the host. Don't try to script on clients.
- **Player colors and seats.** Active seats: `White`, `Brown`, `Red`, `Orange`, `Yellow`, `Green`, `Teal`, `Blue`, `Purple`, `Pink`. Plus `Black` (GM) and `Grey` (spectator). `Player.getPlayers()` excludes `Grey`/`Black` unless explicitly seated.
- **Hand zones** are assigned a color via the in-game gizmo. Anything inside is hidden from other colors and from spectators — except `Grey` who never sees hands, and `Black` (GM/Promoted) who sees everything.
- **Hidden Zones** (curtain zones) hide *all* objects inside, not just cards.
- **Blindfold** hides the entire screen for a player; useful for "leave the room" deduction games.
- **Promote** — host can promote a player to share GM-level view. Useful for co-DMs.
- **Permissions panel** (`Options → Permissions`) toggles flip / draw / spawn / etc. per player color. Account for restrictive settings — don't assume every seat can spawn objects.

---

## 11. Performance & Limits — Things An AI Author Should Not Forget

- **Object count.** Aim for < 1500 active world objects. Use bags / decks to consolidate.
- **Texture memory.** Card atlases + board + tokens easily hit GBs. Cap each texture at 4096×4096; prefer 2048 where legible.
- **Mesh polycount.** Visual mesh < 50k tris; collider mesh < 5k. Provide a separate convex collider for anything larger.
- **Network bandwidth.** Newly spawned objects are streamed to clients — avoid spawning 1000 tokens in one frame; stagger via `Wait.frames`.
- **Scripts.** `onUpdate` is a footgun. Replace with `Wait.condition` or event-driven callbacks.
- **Asset URLs.** If a host goes down, the mod is bricked. Mirror critical assets to Steam Cloud via the Workshop upload, or to imgur direct links (`i.imgur.com/xxxx.png`).
- **Save size.** Save files balloon if every card has its own `CustomDeck` entry. Consolidate cards onto shared atlases and reference the same `CustomDeck` ID across cards.

---

## 12. Debugging Toolkit

- `print(x)` — chat-window log.
- `log(table_or_value, label?, tag?)` — pretty-print to the system console (the `~` console). Crucial for inspecting tables.
- `logStyle(tag, color, prefix?)` — colorize tagged logs.
- **System Console** (`~`) — primary debug stream; shows asset load failures, script errors, network errors.
- **Lua Cheat Sheet** in-game lists current API surface.
- **External editor: Atom + tts-tools / VS Code + vscode-tabletopsimulator-lua** — open every script and XML in your save in one workspace, with live save-to-game on Ctrl+S.
- **Save diff** — keep saves under git; the JSON is text and diffs cleanly. Pretty-printing them once (`jq . save.json > save.pretty.json`) makes diffs vastly more readable.

---

## 13. Known Pitfalls (Paste This Into Every Author's Pre-Flight Checklist)

1. **`onSave` not implemented.** All script state is lost on reload. Always implement it once you keep any non-trivial state.
2. **GUID drift.** When you duplicate an object, it gets a new GUID. Hard-coded GUIDs in Lua break. Prefer **lookup by tag, name, or zone**; fall back to GUIDs only after a setup step writes them into Global state.
3. **Spawn race conditions.** `spawnObject` is async; the returned object may not be fully initialized. Always use `callback_function` before calling methods on it.
4. **Decks of size 1.** A `Deck` collapses to a `Card` automatically when reduced to one item. Code that assumes `getObjectFromGUID(deckGUID).takeObject(...)` will throw once it's a `Card`. Re-resolve from a Scripting Zone instead.
5. **Hand visibility.** Anything dropped into a hand zone is hidden — even tokens. Don't put non-card resources in a hand zone unless that's the intent.
6. **Locked objects ignore physics.** They also ignore `setPositionSmooth(...)` collision checks. Unlock briefly, move, relock.
7. **`takeObject` rotation.** Default rotation is the deck's rotation; pass `rotation` explicitly for face-up/down dealing.
8. **Hot-reload wipes script-driven UI.** Re-create dynamic UI in `onLoad`, not at file-load time.
9. **`UI.setXml` clobbers everything.** Use `setAttribute` for incremental updates.
10. **`onChat` returning `false` silently swallows the message.** Useful for command parsing (`/draw 3`), dangerous if you forget to return `true` for non-commands.
11. **Custom Models load slower than images.** Tell players the first-load delay is normal; consider a "Loading…" banner via UI until critical objects fire `onObjectSpawn`.
12. **Workshop URL rewrites.** When you publish, asset URLs are sometimes rewritten to Steam-cached copies. If you re-host an asset later, you may need to re-upload the mod for the cache to refresh.

---

## 14. Recipes For Common Game Genres

### 14.1 Trick-taking card game

- One `Deck` of 52+ cards on the table, face-down.
- Hand zones for each seat.
- Scripting Zone in the center as the trick area.
- Global script: track current trick (4 cards in zone), determine winner, distribute "trick" tokens, advance lead.
- UI panel showing current contract / trump / score.

### 14.2 Hex wargame

- Single large `Custom_Board` with a hex grid texture.
- A grid of snap points at hex centers (hand-placed once, then save).
- `Custom_Token` units with `Description` = stats; `Tags` = faction.
- Movement is free; combat is resolved by selecting a defender, picking attackers, and pressing a UI "Resolve" button that rolls attached `Custom_Dice`.
- Fog of War zone over the map for hidden movement.

### 14.3 Deckbuilder

- Multiple Decks: market, supply piles, trash, per-player draw + discard.
- Per-player **Custom Bag** as discard, automation pulls "shuffle into deck" when draw is empty.
- Notebook tab per player listing their played cards this turn (script-managed).

### 14.4 RPG sandbox

- Custom_Board as map; multiple states for different scenes.
- Figurines for PCs/NPCs.
- Custom dice tray per player.
- Hidden Zone for the GM's screen, holding NPC stats and hidden tokens.
- Notepad and music player heavily used.

### 14.5 Real-time / dexterity

- Disable Turns; lean on physics.
- Use `addForce` from buttons rather than scripted teleporting to keep the feel.
- Provide a host "Reset" button that re-spawns from the saved JSON layout.

---

## 15. Reference: Minimum Viable Save (Copy-Paste Skeleton)

A complete loadable save with one custom board, one deck of 4 cards, and one hand zone:

```json
{
  "SaveName": "Skeleton",
  "GameMode": "Skeleton",
  "VersionNumber": "v13.x",
  "Gravity": 0.5,
  "PlayArea": 1.0,
  "Table": "Table_Hexagon",
  "Sky": "Sky_Museum",
  "Note": "",
  "LuaScript": "function onLoad() printToAll('Skeleton loaded.', {1,1,1}) end",
  "LuaScriptState": "",
  "XmlUI": "",
  "Hands": { "Enable": true, "DisableUnused": false, "Hiding": 0 },
  "Turns": { "Enable": false, "Type": 0, "TurnOrder": [], "Reverse": false, "SkipEmpty": false, "DisableInteractions": false, "PassTurns": true, "TurnColor": "" },
  "ObjectStates": [
    {
      "Name": "Custom_Board",
      "Transform": { "posX": 0, "posY": 0.96, "posZ": 0, "rotX": 0, "rotY": 0, "rotZ": 0, "scaleX": 12, "scaleY": 1, "scaleZ": 12 },
      "Nickname": "Main Board",
      "Locked": true,
      "CustomImage": { "ImageURL": "https://example.com/board.png", "WidthScale": 0 },
      "GUID": "board1"
    },
    {
      "Name": "DeckCustom",
      "Transform": { "posX": -3, "posY": 1.2, "posZ": 0, "rotX": 0, "rotY": 180, "rotZ": 180, "scaleX": 1, "scaleY": 1, "scaleZ": 1 },
      "Nickname": "Main Deck",
      "DeckIDs": [ 100, 101, 102, 103 ],
      "CustomDeck": {
        "1": {
          "FaceURL": "https://example.com/cards.png",
          "BackURL": "https://example.com/back.png",
          "NumWidth": 2,
          "NumHeight": 2,
          "BackIsHidden": true,
          "UniqueBack": false,
          "Type": 0
        }
      },
      "ContainedObjects": [
        { "Name": "Card", "CardID": 100, "Nickname": "Card 1", "Transform": { "posX":0,"posY":0,"posZ":0,"rotX":0,"rotY":180,"rotZ":180,"scaleX":1,"scaleY":1,"scaleZ":1 }, "GUID": "c1", "CustomDeck": { "1": { "FaceURL":"https://example.com/cards.png","BackURL":"https://example.com/back.png","NumWidth":2,"NumHeight":2,"BackIsHidden":true,"UniqueBack":false,"Type":0 } } },
        { "Name": "Card", "CardID": 101, "Nickname": "Card 2", "Transform": { "posX":0,"posY":0,"posZ":0,"rotX":0,"rotY":180,"rotZ":180,"scaleX":1,"scaleY":1,"scaleZ":1 }, "GUID": "c2", "CustomDeck": { "1": { "FaceURL":"https://example.com/cards.png","BackURL":"https://example.com/back.png","NumWidth":2,"NumHeight":2,"BackIsHidden":true,"UniqueBack":false,"Type":0 } } },
        { "Name": "Card", "CardID": 102, "Nickname": "Card 3", "Transform": { "posX":0,"posY":0,"posZ":0,"rotX":0,"rotY":180,"rotZ":180,"scaleX":1,"scaleY":1,"scaleZ":1 }, "GUID": "c3", "CustomDeck": { "1": { "FaceURL":"https://example.com/cards.png","BackURL":"https://example.com/back.png","NumWidth":2,"NumHeight":2,"BackIsHidden":true,"UniqueBack":false,"Type":0 } } },
        { "Name": "Card", "CardID": 103, "Nickname": "Card 4", "Transform": { "posX":0,"posY":0,"posZ":0,"rotX":0,"rotY":180,"rotZ":180,"scaleX":1,"scaleY":1,"scaleZ":1 }, "GUID": "c4", "CustomDeck": { "1": { "FaceURL":"https://example.com/cards.png","BackURL":"https://example.com/back.png","NumWidth":2,"NumHeight":2,"BackIsHidden":true,"UniqueBack":false,"Type":0 } } }
      ]
    },
    {
      "Name": "HandTrigger",
      "Transform": { "posX": 0, "posY": 5, "posZ": -20, "rotX": 0, "rotY": 0, "rotZ": 0, "scaleX": 12, "scaleY": 6, "scaleZ": 6 },
      "Nickname": "White Hand",
      "FogColor": "White",
      "GUID": "h1"
    }
  ]
}
```

---

## 16. AI Authoring Heuristics (Process Notes For The Next Run)

When building a mod from a user requirement, the agent should:

1. **Normalize the brief.** Convert the user's prose into the §2 design brief. Surface ambiguity early — turn structure and hidden-info rules are the cheapest to misinterpret and the most expensive to fix later.
2. **Pick the smallest primitive that fits.** Custom Tile beats Custom Model unless you genuinely need 3D. Built-in dice beat custom dice unless faces differ. A `Counter` object beats a Lua-driven UI for a single number.
3. **Author content first, scripts last.** Get the deck shuffled and dealt by hand before scripting `Setup`. It's easier to script a working table than to debug a broken one.
4. **Write Lua against tags, not GUIDs.** Tag `Card`, `Resource`, `EnemyToken`, etc. The save survives duplication, deletion, and re-spawn far better.
5. **Keep `onSave` honest.** Every `gameState`-touching mutation is followed by a thought: "would this survive a reload right now?"
6. **Bake setup into a Setup button.** Players will reset constantly. A 1-click reseed is the difference between "one-and-done" and "we played this six times."
7. **Two-pass UX polish.** First pass: tooltips on every clickable. Second pass: a Notebook tab titled "Rules" plus a "Quick Start" tab.
8. **Explicit failure modes.** If a script depends on a GUID, check it on `onLoad` and `broadcastToAll` a clear error if missing — silent failures are the worst player experience.
9. **Ship the JSON pretty-printed.** Easier to diff, easier for users to bug-report.
10. **Record what you didn't build.** A `GMNotes` on a "Roadmap" notecard is the canonical place to leave TODOs for future iterations.

---

## 17. Authoritative Sources (Update Targets When Refreshing This Document)

When this document needs updating, consult, in order:

1. The official **Knowledge Base / API**: `api.tabletopsimulator.com` — Object, Player, UI, Wait, JSON, WebRequest references.
2. The **Berserk Games Forums** and Discord — community patches and undocumented flags.
3. The **Steam Workshop** top-rated mods — read their saves for real-world JSON shapes.
4. The **VS Code TTS extension** documentation — the most current set of editor-supported entry points.
5. Patch notes inside the TTS launcher — version-specific changes (especially anything around Lua sandbox, UI, and asset caching).

A new TTS major version (`v14`, etc.) tends to add fields, not break old ones, but always re-validate the §4 JSON schema against a fresh "empty save" exported from the current build.

---

*End of reference. Treat this file as the contract between the design brief the user gives you and the JSON / Lua / XML you produce. When in doubt, build the smallest playable version, hand it to the user, and iterate.*
