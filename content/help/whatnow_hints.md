# What-Now Hints

Context-aware hint strings for the "What now?" button (Design §18.17). Each hint is keyed by sub-phase + character state. The Lua runtime substitutes placeholders at display time:

- `{name}` — active character name
- `{actionsLeft}` — remaining actions this turn
- `{location}` — current location name
- `{hunger}` — current Hunger value
- `{health}` — current Health value
- `{sanity}` — current Sanity value
- `{doom}` — current Doom value
- `{day}` — current day number
- `{nearestCrockpot}` — name of nearest location with a Crockpot
- `{nearestAlly}` — name of nearest other character

---

## Pre-Game

- **default:** "Click 'Setup Game' on the table to begin. Hover anything to see what it does. Press '?' for help anytime."

---

## Dawn

- **default:** "A new Dawn card has been revealed. Read the effect — it applies to everyone. When ready, the host clicks Begin Day."
- **ongoing_effect:** "Remember: the Dawn card '{dawnTitle}' is still active. Its ongoing effect lasts until next Dawn."

---

## Day (general)

- **default:** "It's your turn, {name}. You have {actionsLeft} action(s) left. Choose from your Action Bar: Move, Gather, Craft, Cook, Fight, Rest, or Cleanse."
- **no_actions:** "You've used all 3 actions. Click End Turn."
- **all_passed:** "All players have finished. The host should advance to Dusk."

---

## Day (character-specific situations)

### Low stats
- **low_hunger:** "{name}, your Hunger is at {hunger} — below 3 means you can't Fight (you can still Flee: 1 tile, 1 Sanity). Eat something, Rest, or ask an ally to trade you Food."
- **low_sanity:** "{name}, your Sanity is at {sanity} — below 3 you're Haunted: at Dawn you draw a personal Threat that allies can't help with. Use a Comfort item, Rest for +2 Sanity, or get near Coco or Luca."
- **low_health:** "{name}, your Health is at {health} — below 3 means movement costs +1 action. Use a Bandage, rest at your own house, or ask for help."
- **critical_any:** "{name}, one of your stats is dangerously low. Prioritize recovery this turn — Rest, eat, or use an item. Survival comes first."

### James-specific
- **james_no_energy_drink:** "James, you haven't consumed an Energy Drink today. If you don't by end of day, you'll lose 2 Sanity tonight. Check your hand — or gather at James's House: The Stash lets you take 2 Energy Drinks at once."
- **james_has_peek:** "James, you haven't used Pattern Recognition yet today. Peek at the top of any deck — the Threat deck is usually the best target."
- **signature_unused:** "James, your All-Nighter is still available (once per game): 3 extra actions this turn, -3 Sanity at the next Tick. The endgame push is what it's for."

### Coco-specific
- **coco_alone:** "Coco, you're alone at {location}. If you end Night alone at a non-house tile, you lose 3 Sanity. Move toward an ally or a house with company."
- **signature_unused:** "Coco, your Touch of Hope is still available (once per game): heal anyone, anywhere, +4 Health. Save it for a real emergency — someone near death."

### Rayman-specific
- **rayman_hungry:** "Rayman, your Hunger is at {hunger}. You lose 2 Hunger per Tick instead of 1. Get to the Kitchen or eat what you have."
- **rayman_at_court:** "Rayman, you're at the Basketball Court — your Court Master perk gives you +1 attack die here. If there's a Threat, now is the time to Fight."
- **signature_unused:** "Rayman, your Posterize is still available (once per game): instantly defeat one non-boss threat at your tile. The noise draws +1 Threat there tonight — dunk responsibly."

### Ellie-specific
- **ellie_at_kitchen:** "Ellie, you're at the Kitchen. You can Cook with 1 fewer ingredient than anyone else. Check your resources — a Hot Stew feeds everyone here."
- **ellie_no_food:** "Ellie, you have no Food. You can't eat raw food (Particular Eater). Gather at your own house (Knows the Pantry) or trade with an ally."
- **signature_unused:** "Ellie, The Feast is still available (once per game): at a Crockpot, cook any number of recipes in one action — it consumes ALL your Food. Fire it when the pantry is full and the team is empty."

### Luca-specific
- **luca_alone:** "Luca, you're alone. Your Sanity won't regenerate without company (Needs an Audience). Move toward an ally."
- **luca_rally_unused:** "Luca, you haven't used Rally yet this turn. Give a nearby ally a free non-movement action — it's one of the most powerful moves in the game."
- **signature_unused:** "Luca, The Speech is still available (once per game): +2 Sanity to everyone, anywhere — but only while an ally is Down or below 3 Sanity. When the moment comes, take it."

---

## Day (location-specific)

- **at_own_house:** "You're at your own house. Resting here gives +1 Health in addition to the normal Hunger/Sanity recovery."
- **at_kitchen_not_ellie:** "You're at the Kitchen. If Ellie is here too, her Comfort Food perk gives +1 Hunger and +1 Sanity on top of any cooked meal."
- **at_basketball_court:** "You're at the Basketball Court. Good for gathering Wood and Metal. Watch out — the Echoes here can cost Sanity on a bad roll."
- **at_badminton_court:** "You're at the Badminton Court. The Net gives +1 defense die in combat, but this location has the highest Threat draw rate at Night."

---

## Day (strategic)

- **doom_high:** "Doom is at {doom}. Consider spending an action on Cleanse (1 Wood + 1 Cloth + 1 Battery + 1 Energy Drink → Doom -2) if you have the resources. Clearing threats off the map also stops Doom festering at Dawn."
- **market_good_item:** "There's a useful item in the Market. Check if you can afford to Craft it — items are your long-term power."
- **ally_down:** "A teammate is Down. You need a Telltale Heart to revive them (cook 1 Cloth + 1 Battery + 1 Food + 2 Health at a Crockpot). Prioritize this — every Down character also fed the Doom track."
- **no_light_source:** "{name}, you don't have a light source. If Night comes without a Flashlight (Battery), Lantern, or Fire, Charlie will attack — and she hits harder every consecutive dark night. Get a light."
- **enemy_at_location:** "There's an active Threat at {location}. Fight it (1 action) or move away — but it'll still be here at Night, and every threat left on the map feeds Doom +1 at Dawn."

---

## Dusk

- **default:** "Last chance to move: each character may scramble 1 tile (costs 1 Hunger) using the Dusk panel, or stay put. You sleep where you stand. Remember — a house sleeps two comfortably; the third gets the floor."
- **alone_sport_court:** "You're about to sleep alone at a sport court. You'll draw an extra Threat and get no sleep regen — but survive the night and you salvage 2 resources at Dawn. Brave or foolish?"
- **coco_alone_warning:** "Coco, if you sleep alone at a non-house tile, you'll lose 3 Sanity. Scramble 1 tile to where an ally is sleeping."
- **no_light_warning:** "{name}, you have no light source. Charlie will attack tonight — 2 Sanity + 1 Health, and she hits harder each consecutive dark night. Acquire a light before committing."

---

## Night

- **default:** "Night is resolving. Threats are drawn at each occupied location, least-populated first. The host clicks Resolve Night to proceed."
- **combat_active:** "Combat is active at {location}. Roll your attack dice. Each 5-6 is a hit. Whiff completely with a 1 in the roll and you fumble (1 self-damage, max 1). Landed a hit? PRESS THE ATTACK: 1 Sanity per bonus die, until you miss — the enemy can't strike back while you press. Too hungry or outmatched? Flee: 1 tile away, 1 Sanity — the threat stays and festers."
- **charlie_incoming:** "{name} has no light source. Charlie attacks: 2 Sanity + 1 Health, +1 to each per consecutive night spent in darkness."
- **storytelling:** "Storytelling phase. Players together at a house can use Comfort items for shared Sanity gain. Luca's Storyteller perk gives +1 Sanity to everyone at his location."
- **sleep_phase:** "Sleep is resolving. Own house: +1 Sanity, +1 Hunger, +1 Health. Someone else's house with company: +1 Sanity. Houses sleep 2 comfortably — extra sleepers get the floor (no regen). Sport courts: nothing tonight, but survivors salvage 2 resources at Dawn."

---

## Tick

- **default:** "End-of-round Tick. Everyone loses 1 Hunger and 1 Sanity (Rayman loses 2 Hunger). Check your stats. The day advances."
- **someone_down:** "A character went Down during the Tick. They're now a ghost — they can't act but can drift 1 tile per round. The team needs a Telltale Heart to revive them."
- **between_days:** "Day {day} is ready to begin — the host clicks Begin Day. At Dawn: Doom advances (+1 per threat still on the map, +2 per boss), then a new Dawn card hits everyone. Use the pause to plan: who eats, who gets a light, who fights."

---

## Post-Game

- **victory:** "You survived {day} days with Doom at {doom}. Well done. Check for bonus achievements: Pristine (everyone in play still standing, nobody revived), Truth (3 Clue cards), Hero (all 3 phase bosses defeated)."
- **defeat_doom:** "Doom reached 30. The neighborhood is lost. Click Restart to try again — consider prioritizing Cleanse actions earlier next time."
- **defeat_all_down:** "All characters are Down at the same time. The team is lost. Click Restart — coordinate your positioning and keep at least one healer safe."
- **defeat_source:** "The Source was not stopped by end of Day 7. Click Restart — make sure you're ready for the final boss by Day 6."
