# Hero Adventure Developer Guide

This guide explains how the codebase is organized, how the game flow works, and how to add new content or modify core systems without breaking the architecture.

It is meant to be read alongside the architecture document and the actual source files:

- ARCHITECTURE.md
- game_data.py
- game_engine.py
- game_controller.py
- ui/*.json

## 1. Mental model of the codebase

The game is intentionally separated into three layers:

- game_data.py
  - Static tables only.
  - Character classes, monsters, relics, towns, loot tiers, narration text, houses, pensions, etc.
  - No game logic.

- game_engine.py
  - Core rules and simulation.
  - Combat, item generation, dungeon flow, journey events, relic effects, town recovery, aging, retirement math.
  - No UI.

- game_controller.py
  - Screen flow and interaction layer.
  - Owns the state machine, action dispatch, narration, save/load, and all context building for the UI.
  - Does not contain core combat math; it delegates to HeroAdventureEngine.

- ui/*.json
  - Declarative UI definitions for each screen.
  - Each screen is rendered from JSON and a context dict built by GameController.get_context().

- play.py / play_gui.py / web/
  - Renderer front-ends only.
  - They display what GameController says and send button actions back into dispatch().

The most important architectural rule is this:

- If it changes the world state, put it in game_engine.py or game_data.py.
- If it changes screen flow or player interaction, put it in game_controller.py and ui/*.json.

This separation is the key to safely adding content.

## 2. Program flow: how a single turn works

The game uses a screen state machine. The most important runtime variable is:

- `self.screen` in GameController

It is a string like:

- "front_page"
- "character_creation"
- "journey"
- "combat"
- "town_recovery"
- "capital"
- "level_up"
- etc.

Each screen name corresponds to a file in `ui/`.

A typical interaction loop is:

1. UI loads `ui/{screen}.json`
2. UI asks `GameController.get_context()` for the variables needed by that screen
3. The JSON is rendered with those values substituted in
4. The user clicks a button
5. The UI sends a string like `advance_event` or `trader_buy:2`
6. `GameController.dispatch(action)` splits it into verb + optional arg
7. It looks for `_action_<verb>` and calls it
8. The handler mutates engine state, sets `self.screen`, and updates `self.ctx`
9. The UI re-renders

The relevant methods are:

- `GameController.dispatch()`
- `GameController.get_context()`
- `_action_*` methods in GameController

The engine is used by controller actions for simulation logic, not by renderers.

## 3. Where to add common changes

### 3.1 Add a new screen

The pattern is:

- create a new JSON file in `ui/`
- add a command/action in GameController
- optionally update `get_context()`
- optionally add narration templates or data values

Example: a new screen called `genie_relic_offer`.

Create a file like:

- `ui/genie_relic_offer.json`

Minimal structure:

```json
{
  "id": "genie_relic_offer",
  "title": "The Genie Offers a Gift",
  "frames": [
    { "id": "status", "role": "status", "ratio": 0.15, "overflow": "collapse" },
    { "id": "scene", "role": "scene", "ratio": 0.6, "overflow": "truncate" },
    { "id": "context", "role": "context", "ratio": 0.15, "overflow": "page" },
    { "id": "actions", "role": "actions", "ratio": 0.10, "overflow": "collapse" }
  ],
  "controls": [
    { "type": "text", "frame": "scene", "value": "{event_narration}" },
    { "type": "text", "frame": "context", "value": "Choose a relic" },
    { "type": "button", "frame": "actions", "label": "{relic_a_name}", "action": "accept_genie:{relic_a_name}" },
    { "type": "button", "frame": "actions", "label": "{relic_b_name}", "action": "accept_genie:{relic_b_name}" },
    { "type": "button", "frame": "actions", "label": "{relic_c_name}", "action": "accept_genie:{relic_c_name}" },
    { "type": "button", "frame": "actions", "label": "Decline", "action": "decline_genie" }
  ]
}
```

Then add the controller side:

```python
def _start_genie_offer(self) -> None:
    e = self.engine
    assert e is not None

    choices = [name for name in RELICS if name not in e.relics_found]
    if len(choices) < 3:
        self._go_to_journey("The genie found you already had everything it could offer.")
        return

    options = random.sample(choices, 3)
    self._set_narration("genie_relic", relics=", ".join(options))
    self.ctx = {
        "relic_a_name": options[0],
        "relic_b_name": options[1],
        "relic_c_name": options[2],
        "event_narration": self.current_narration,
    }
    self.screen = "genie_relic_offer"
```

And handlers:

```python
def _action_accept_genie(self, relic_name: str) -> None:
    e = self.engine
    assert e is not None
    if relic_name not in RELICS:
        return

    info = RELICS[relic_name]
    item = {
        "name": relic_name,
        "category": "relic",
        "slot": info["type"],
        "tier": "Epic",
        "code": "e",
        "skill": info["skill"],
        "skill_val": info["bonus"],
        "weight": 1,
        "value": 25000,
        "uses": 1,
        "max_uses": 1,
    }
    e.inventory.append(item)
    e.relics_found.append(relic_name)
    self._go_to_journey(f"The genie granted you {relic_name}.")


def _action_decline_genie(self) -> None:
    self._go_to_journey("You turn away from the genie and continue down the road.")
```

This is the standard pattern for a new screen.

### 3.2 Add a new event with a probability

Your request mentions a genie that offers one of three special relics the hero does not have, at a 0.1% chance.

The correct place is the journey event selection logic in HeroAdventureEngine.roll_journey_event_type().

Add something like:

```python
if random.random() < 0.001:
    return "GENIE_RELIC"
```

Then in GameController._action_advance_event(), branch on it:

```python
elif event_type == "GENIE_RELIC":
    self._start_genie_offer()
```

This is the cleanest pattern. The engine decides “what kind of event occurs,” and the controller decides “what screen shows and what actions are available.”

### 3.3 Insert a new screen in the journey start, before the first event

This is the “journey start injection” problem.

The first actual journey progression begins here:

```python
def _action_origin_continue(self) -> None:
    self.ctx = {}
    self.current_narration = ""
    self.screen = "journey"
```

If you want a screen inserted before the first normal event:

```python
def _action_origin_continue(self) -> None:
    self.ctx = {}
    self.current_narration = ""
    self.screen = "genie_intro"
```

Then create `ui/genie_intro.json` and add:

```python
def _action_genie_intro_continue(self) -> None:
    self.ctx = {}
    self.screen = "journey"
```

This makes the intro happen before any journey event has resolved.

If the intro should only show once, add a flag in the engine or controller, e.g.:

```python
self.engine.intro_seen = True
```

and guard it on future loads.

## 4. Adding a new class

A class is split between data and logic.

### 4.1 Add class data

In `game_data.py`, add a new entry to `CLASSES`:

```python
CLASSES: dict[str, dict[str, int]] = {
    "Hitter": {"fighting": 20, "defending": 20},
    "Blaster": {"magic": 20, "defending": 20, "stealth": 20},
    "Hider": {"stealth": 20, "magic": 20, "fighting": 7, "defending": 7},
    "Oracle": {"magic": 25, "speech": 15, "defending": 10},
}
```

This gives the class starting bonuses.

### 4.2 Add special behavior if needed

If the class has custom abilities, add logic in the engine.

Example: a class with a town-heal bonus:

```python
if hero_class == "Oracle":
    self.max_hp += 20
    self.hp += 20
```

Or in the controller, when starting town recovery:

```python
if self.engine.hero_class == "Oracle":
    self.engine.hp = min(self.engine.max_hp, self.engine.hp + 10)
```

If the class changes combat style, add it to:

- `HeroAdventureEngine._fight_core_stats()`
- `HeroAdventureEngine.estimate_fight_risk()`
- `HeroAdventureEngine.estimate_combat_action_risks()`
- `GameController._character_title()` if you want the title to reflect it

### 4.3 Add it to the UI for selection

The character creation flow uses `CLASSES` and UI-generated buttons. The game already builds class choices from the data; if you add a new class there, it often appears automatically in the character selection screen depending on how the screen is wired.

If the UI is hardcoded, modify the relevant `character_creation` JSON or screen-generation code.

## 5. Adding a new relic with a non-trivial effect

This is the pattern for relational rules content.

### 5.1 Add the relic definition

In `game_data.py`:

```python
RELICS: dict[str, RelicDef] = {
    "Townkeeper's Charm": {
        "type": "accessory",
        "effect": "heal_on_town_enter",
        "skill": None,
        "bonus": 0,
    },
    ...
}
```

This is the data side. The `effect` field is a nominal identifier the engine checks by name.

### 5.2 Add the logic in the engine

The cleanest pattern is a helper method on `HeroAdventureEngine`:

```python
def apply_relic_effect(self, effect_name: str, **context) -> None:
    if effect_name == "heal_on_town_enter":
        if any(eq and eq.get("name") == "Townkeeper's Charm" for eq in self.equipment.values()):
            heal_amount = 10
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.log("RELIC_TOWN_HEAL", {"amount": heal_amount, "hp": self.hp})
```

Then call it from the controller when the player enters town recovery:

```python
def _prepare_town_year(self) -> None:
    e = self.engine
    assert e is not None

    e.apply_relic_effect("heal_on_town_enter")
    ...
```

This matches the architecture: the controller triggers the moment, the engine applies the effect.

### 5.3 Example: recover 10 HP on entering a town

This is exactly the sort of effect to add as a passive accessory relic.

Implementation outline:

- Add to `RELICS` with `effect: "heal_on_town_enter"`
- Add branch to `apply_relic_effect` or a dedicated method
- Invoke it at the beginning of `GameController._prepare_town_year()` or `_enter_town_recovery()`

Example code:

```python
def _enter_town_recovery(self) -> None:
    assert self.engine is not None
    self.engine.apply_relic_effect("heal_on_town_enter")
    if self.engine.hp >= self.engine.max_hp:
        self._enter_level_up()
        return
    self.town_shop_offer = self.engine.generate_trader_offer()
    self._prepare_town_year()
```

This means the hero enters town and regains 10 HP automatically when the relic is equipped.

### 5.4 New relic effect categories that fit the codebase

These are all good candidate patterns:

- passive stat bonus
- one-time heal on entering town
- extra gold on winning a fight
- reroll one failed stealth attempt
- auto-heal after a boss fight
- half-damage taken when below 25% HP
- create a guaranteed escape once per dungeon
- reduce karmic penalty for stealing

The game already uses a few named effects like:

- `prevents_death_once`
- `reroll_loot`
- `reroll_fight_loss`
- `invincible_combo`
- `heal_after_boss`
- `magic_replaces_defending`
- `always_stealth_auto_win`
- `always_stealth_kill`
- `always_win_magic_trap`
- `half_damage_loss`
- `double_magical_ward`

They live in the engine as effect checks, not as a generic script engine.

## 6. Adding a new item or loot type

The pattern is:

- add to `ITEM_CATEGORIES` if it is a standard generated item
- or add a one-off item by manually appending an item dict
- use `slot`, `skill`, `skill_val`, `weight`, `value`, `tier`

Example:

```python
item = {
    "name": "Crimson Flask",
    "category": "magic",
    "slot": "fighting_weapon",
    "tier": "Rare",
    "code": "r",
    "skill": "magic",
    "skill_val": 30,
    "weight": 3,
    "value": 500,
    "uses": 1,
    "max_uses": 1,
}
```

If you want a particular loot to also affect a combat or town action, add the check in the engine and the trigger in the controller.

## 7. How to add a new event or narrative line

The narration system is mostly table-based.

Relevant files:

- `game_data.py`
  - `EVENT_NARRATION_TEMPLATES`
  - `REPEAT_ENCOUNTER_TEMPLATES`
  - `REMINISCENCE_TEMPLATES`
  - `NARRATION_EVENT_SCREENS`

The controller uses:

```python
self._set_narration("event_type", **data)
```

This pulls from:

```python
EVENT_NARRATION_TEMPLATES.get(event_type, [])
```

So adding a new event is usually:

1. add a new `event_type` string in the engine
2. add a narrative template entry in `EVENT_NARRATION_TEMPLATES`
3. add a screen to show it if needed
4. ensure the screen is in `NARRATION_EVENT_SCREENS` if you want `event_narration` to display

## 8. How to debug the game

This project is very debug-friendly if you know the right places to stop.

### 8.1 Best breakpoints in the code

#### GameController.dispatch

This is the main entry point for all player actions.

Add a breakpoint here to see every action string the UI sends:

```python
def dispatch(self, action: str) -> None:
    if not action:
        return
    print("DISPATCH:", action)
    breakpoint()
```

This is the best place to answer:

- Why didn’t my button fire?
- Did the action string match the handler name?
- Did the UI send the wrong argument?

#### GameController._action_advance_event

This is the core journey event trigger.

Break here to inspect:

- current leg
- event count
- current screen
- engine state
- event selected

This is the perfect place to debug new event additions.

#### GameController._action_origin_continue

Break here when adding intro screens or altering the opening journey flow.

#### GameController._prepare_town_year

Break here to debug:

- healing amounts
- age progression
- job offers
- prison checks
- forced retirement

#### GameController._resolve_combat_choice

Break here to debug player choices and their outcome.

Inspect:

- choice
- monster name
- engine hp before/after
- `self.ctx`
- `res`

#### HeroAdventureEngine.resolve_fight

This is the single most important function for combat debugging.

Break here and inspect:

- `monster_name`
- `choice`
- `encounter_type`
- `self.hp`
- `self.inventory`
- `self.equipment`
- `self.last_combat_summary`

This function decides outcomes for fight/sneak/steal/stealth_kill/throw_item, so it is the core debugging hub for game balance and bug fixing.

#### HeroAdventureEngine.take_damage

This is the best place to debug:

- death conditions
- fairy rescue behavior
- pendant saves
- death reasons

#### HeroAdventureEngine.grant_monster_loot

Break here to debug:

- cash gains
- item drops
- relic drops
- refused/discarded loot flow

#### HeroAdventureEngine.get_effective_skills

Break here to debug:

- skill totals after equipment bonuses
- carry penalties
- weight calculations
- why a character suddenly feels weaker or stronger

### 8.2 Running the game in debug mode

Use Python’s built-in debugger:

```bash
python3 -m pdb play.py
```

or:

```bash
python3 -m pdb play_gui.py
```

Then add `breakpoint()` where needed.

### 8.3 Useful state to inspect at breakpoints

When paused, inspect:

- `self.screen`
- `self.ctx`
- `self.engine`
- `self.engine.hp`
- `self.engine.max_hp`
- `self.engine.cash`
- `self.engine.current_leg_idx`
- `self.engine.dungeon_name`
- `self.engine.inventory`
- `self.engine.equipment`
- `self.engine.relics_found`
- `self.engine.karma`

For combat debugging, also inspect:

- `monster_name`
- `choice`
- `res`
- `self.last_combat_summary`

### 8.4 Debugging with the headless simulator

This repository includes `sim_runner.py` specifically for logic validation without UI noise.

Run:

```bash
python3 sim_runner.py
```

It writes logs to:

- `sim_logs/sim_events.jsonl`
- `sim_logs/sim_summary.json`

This is especially useful when:

- a bug is in the engine and not the UI
- you want to test new combat math or event selection
- you want to validate a new relic effect or class balance
- you want to inspect event flow without clicking through screens

The engine logs are already structured with `HeroAdventureEngine.log()` and `log_special_moment()`, which means you can make logic changes and inspect exactly what happened.

### 8.5 Good debug log patterns

Add logs like:

```python
self.log("GENIE_RELIC_EVENT", {"relics": options})
```

or:

```python
self.log_special_moment("genie_relic", relics=options)
```

These integrate with the simulation logs and are easy to inspect later.

## 9. How to add a new screen in the exact architecture style

The intended pattern is always:

- engine decides world state
- controller decides route and context
- JSON screen describes layout and controls
- renderers only display

So for any new feature, ask:

1. Is this a world rule or just a UI bit?
2. Does this belong in `game_data.py` (static content) or `game_engine.py` (behavior)?
3. Does this create a new state in the app? If yes, it belongs in `GameController` and likely `ui/`.
4. Does it need a new screen? Then add to `ui/*.json` and handle it in `_action_*`.
5. Does it need a new item or relic effect? Then add data and engine logic.

## 10. Common modifications and where they belong

### Add a new monster

- `game_data.py`: `MONSTERS`
- optionally adjust `roll_journey_event_type()` or encounter selection
- optionally add special narration if needed

### Add a new dungeon

- `game_data.py`: `LEGS` list and the dungeon metadata
- `game_engine.py`: dungeon advancement code may already work generically
- `ui/*.json`: if you want a custom dungeon screen or summary screen

### Add a new town recovery mechanic

- `game_controller.py`: `_prepare_town_year()` and related flow
- `game_data.py`: their descriptions/tables
- `game_engine.py`: underlying state effects

### Add a new relic effect

- `game_data.py`: `RELICS`
- `game_engine.py`: effect logic and checks
- `game_controller.py`: call the effect at the right moment

### Add a new UI action

- `game_controller.py`: new `_action_<verb>`
- `ui/*.json`: button with matching `action` string

### Add a new score condition

- `game_engine.py`: `calculate_score()` or related retirement code
- `game_controller.py`: screen for display

## 10. Additional concrete use cases

These are the kinds of changes people usually want to make after the first few features. They follow the same architecture patterns, but they are slightly more involved.

### 10.1 Add a new status effect like "blinded", "poisoned", or "frenzied"

This is a common request when expanding combat depth.

Use a pattern like:

```python
# in HeroAdventureEngine.__init__
self.status_effects: dict[str, int] = {}
```

Then create methods like:

```python
def apply_status(self, name: str, duration: int = 1) -> None:
    self.status_effects[name] = max(self.status_effects.get(name, 0), duration)


def tick_statuses(self) -> None:
    for name in list(self.status_effects):
        self.status_effects[name] -= 1
        if self.status_effects[name] <= 0:
            del self.status_effects[name]
```

When a status affects combat, add checks in `resolve_fight()` or `_fight_core_stats()`:

```python
if "poisoned" in self.status_effects:
    self.hp = max(0, self.hp - 5)
```

Then surface it in the UI with a new context field in `get_context()`:

```python
ctx["status_effects"] = ", ".join(self.engine.status_effects.keys()) or "None"
```

And add a display line in a relevant screen JSON, such as the journey or combat screen.

This is a good pattern because status effects are engine-owned game state, while the UI only displays them.

### 10.2 Add a new town action like "visit the shrine", "consult an oracle", or "bet in the arena"

Most town actions should be implemented as a new action branch in the controller and a corresponding screen JSON.

Example flow:

1. Add a new UI button to `ui/town_recovery.json` or a new town-specific screen
2. Add a controller method:

```python
def _action_town_visit_oracle(self) -> None:
    e = self.engine
    assert e is not None
    if e.cash < 100:
        self.ctx = {"town_message": "The oracle refuses to speak without a fee."}
        return

    e.cash -= 100
    e.base_skills["magic"] += 5
    self._go_to_journey("The oracle whispers a blessing into your mind.")
```

3. Add a matching action string to the JSON

```json
{ "type": "button", "label": "Consult the Oracle", "action": "town_visit_oracle" }
```

This should feel exactly like the rest of the game: the controller triggers the interaction, the engine mutates state, and the UI re-renders.

### 10.3 Add a new leg or journey route

This is a larger but straightforward expansion.

The game is built around 5 legs, each with a `LEGS` array in `game_data.py`.

Example:

```python
LEGS.append({
    "id": 6,
    "name": "The Shattered Coast",
    "super_monster": "Sea Wyrm",
    "dungeons": [
        {
            "name": "The Sunken Vault",
            "boss": "Deep Drowned King",
            "floors": ["Barnacle Fiend", "Reef Hunter", "Tide Stalker", "Drowned Knight", "Coral Tyrant"]
        }
    ]
})
```

Then modify any system that assumes there are exactly 5 legs:

- `advance_to_next_leg()` in the engine
- `GameController._enter_level_up()` flow
- any capital/retirement logic that bakes 5 leg behavior into narration or end-state behavior
- any UI text that says “Leg {leg}/5” or assumes level progression ends at 5

Important detail: this project is not deeply parameterized by leg count. It assumes 5 is the maximum. So if you add a 6th leg, you may need to update UI strings and some end-of-leg calculations.

### 10.4 Add a new inventory interaction or list-based screen

The inventory and list screens are generated by row builders in `GameController`.

For example, if you want a new list screen like `alchemy_table`:

1. Add a new screen in `ui/alchemy_table.json`
2. Add a row builder:

```python
def _build_alchemy_rows(self):
    assert self.engine is not None
    rows = []
    for idx, item in enumerate(self.engine.inventory):
        rows.append({
            "text": f"{idx + 1}. {item['name']}",
            "action": f"alchemy_mix:{idx}",
            "enabled": True,
        })
    return rows
```

3. In `get_context()`:

```python
elif self.screen == "alchemy_table":
    ctx["list_alchemy"] = self._build_alchemy_rows()
```

4. Add action handlers:

```python
def _action_alchemy_mix(self, idx_str) -> None:
    idx = int(idx_str)
    if 0 <= idx < len(self.engine.inventory):
        item = self.engine.inventory.pop(idx)
        self.engine.cash += 50
        self._go_to_journey(f"You refine {item['name']} into a little extra coin.")
```

This is the same mechanism used for the trader and town buy/sell screens.

### 10.5 Add a new save-version migration

The game stores save payloads in `GameController._save_payload()` and restores them in `_restore_payload()`.

This means save compatibility matters when changing state shape.

A common pattern is:

```python
SAVE_VERSION = 2
```

Then in `_restore_payload()`:

```python
if payload.get("version") != self.SAVE_VERSION:
    # migrate old version to new version here
    if payload.get("version") == 1:
        payload = self._migrate_v1_to_v2(payload)
```

And implement a migration helper:

```python
def _migrate_v1_to_v2(self, payload):
    engine_data = payload.get("engine", {})
    if "status_effects" not in engine_data:
        engine_data["status_effects"] = {}
    payload["version"] = 2
    return payload
```

This is important if you add a new engine field, a new item type, or a new relic flag that must survive reloads.

If you do not migrate correctly, the save may silently fail or create broken runtime state.

### 10.6 Add an entirely new combat action

This is a bit more involved than a new event, but the pattern is consistent.

For example, imagine adding a new action called `focus` that temporarily boosts the next attack by +10.

1. Add a controller action:

```python
def _action_focus(self) -> None:
    e = self.engine
    assert e is not None
    e.apply_status("focused", 1)
    self._go_to_journey("You steady yourself and focus your breath.")
```

2. Adjust `resolve_fight()` to support the new choice:

```python
if choice == "focus":
    self.apply_status("focused", 1)
    return "JOURNEY"
```

3. Add UI handling in `combat.json` with a button like:

```json
{ "type": "button", "label": "Focus", "action": "focus" }
```

4. Update risk estimation if desired:

```python
if choice == "focus":
    # add a custom risk profile or a temporary stat boost in the estimate
```

The important part: the logic belongs in the engine, while the button + screen belongs in the controller/UI layer.

### 10.7 Add a custom item use or consumable

Consumables are often easier than raw stat items.

Add a custom item like `Potion of Mending` in the generated items list or data tables, then handle it in a method like:

```python
def _action_use_potion(self, letter: str) -> None:
    item, slot = self._find_letter_item(letter)
    if not item or item.get("name") != "Potion of Mending":
        return

    self.engine.hp = min(self.engine.max_hp, self.engine.hp + 25)
    self.engine.inventory.remove(item)
    self.screen = "inventory"
```

This is a great example of how a “special item” is implemented without disturbing the core engine.

The broader rule is: item behavior is engine- or controller-logic depending on whether it is free-form game logic or direct player-action flow.

### 10.8 Add a new narrative hook for a custom event chain

Suppose you want a new event that generates a short “special moment” for reminiscence later.

In the engine, create a record like:

```python
self.log_special_moment("oracle_blessing", blessing="the voice of the glass sea")
```

Then in `GameController._maybe_add_reminiscence()`, include a branch for the new type:

```python
elif source == "oracle_blessing":
    text = self._choose_template(
        "reminiscence_oracle_blessing",
        REMINISCENCE_TEMPLATES["oracle_blessing"],
    ).format(**data)
```

And add template text in `game_data.py`:

```python
REMINISCENCE_TEMPLATES["oracle_blessing"] = [
    "For a moment, {hero_name} remembered the whisper from the oracle, and the glow of the sea still shone in the mind.",
]
```

This is how the game keeps narrative flavor attached to important events without hardcoding them in the UI.

### 10.9 Add a custom local panel or widget without changing the front-end renderer

This project’s renderers already accept a JSON control schema. That means you can often add new widgets without touching code.

Example widget types already used in this repo include:

- `text`
- `progressbar`
- `button`
- `list`
- `input`

If you add a new type of control, you may need to update the front-end renderer (terminal or GUI) to handle it. But if you stick to existing controls, the “JSON-only” route is usually enough.

Example: add a list of quest status entries:

```json
{
  "type": "list",
  "frame": "context",
  "id": "quest_list",
  "value": "{list_quest_lines}"
}
```

In `get_context()`:

```python
ctx["list_quest_lines"] = [
    {"text": "Find the shrine in the Green Pass", "action": None, "enabled": False},
    {"text": "Win a duel at the arena", "action": None, "enabled": False},
]
```

This pattern is ideal when a feature is mostly display-only but still needs to be dynamic.

### 10.10 Add a new endgame condition or alternate victory path

Suppose you want a victory condition like “collect five relics” or “become the master of all guilds.”

The normal place for this is the engine’s victory logic and the controller’s route after event resolution.

Add a check like:

```python
if self.relics_found and len(self.relics_found) >= 5:
    self.game_won = True
```

or a branch that triggers on `leg_event_count` or `dungeons_cleared`.

Then update the relevant screen after the game is won.

This is often a matter of:

- adding a new condition in `HeroAdventureEngine`
- making `GameController._action_advance_event()` route to a new screen when that condition is met
- updating the end-of-game score or capital flow

### 10.11 Add a debug-only feature toggle

This codebase already has feature toggles in `HeroAdventureEngine.__init__` such as:

- `relic_scaling_enabled`
- `stealth_atk_enabled`
- `hider_stat_bonus_enabled`
- `throw_item_enabled`

This is a good pattern for experimenting without permanently changing rules.

Example:

```python
class HeroAdventureEngine:
    def __init__(..., new_town_bonus_enabled: bool = True):
        self.new_town_bonus_enabled = new_town_bonus_enabled
```

Then in the logic:

```python
if self.new_town_bonus_enabled:
    self.hp = min(self.max_hp, self.hp + 10)
```

This makes it easy to test a feature in `sim_runner.py` and compare outcomes quickly.

## 12. Copy-paste templates

These are small boilerplate blocks you can adapt directly when adding new features.

### 12.1 Template: new screen + action flow

`ui/my_new_screen.json`:

```json
{
  "id": "my_new_screen",
  "title": "My New Screen",
  "frames": [
    { "id": "status", "role": "status", "ratio": 0.15, "overflow": "collapse" },
    { "id": "scene", "role": "scene", "ratio": 0.6, "overflow": "truncate" },
    { "id": "context", "role": "context", "ratio": 0.15, "overflow": "page" },
    { "id": "actions", "role": "actions", "ratio": 0.10, "overflow": "collapse" }
  ],
  "controls": [
    { "type": "text", "frame": "scene", "value": "{event_narration}" },
    { "type": "text", "frame": "context", "value": "{my_message}" },
    { "type": "button", "frame": "actions", "label": "Confirm", "action": "confirm_my_screen" },
    { "type": "button", "frame": "actions", "label": "Cancel", "action": "goto:journey" }
  ]
}
```

Controller:

```python
def _start_my_screen(self) -> None:
    e = self.engine
    assert e is not None
    self._set_narration("my_event")
    self.ctx = {
        "my_message": "Something interesting happened.",
        "event_narration": self.current_narration,
    }
    self.screen = "my_new_screen"


def _action_confirm_my_screen(self) -> None:
    self._go_to_journey("You resolved the event and continue on your way.")
```

And add narration templates in `game_data.py`:

```python
EVENT_NARRATION_TEMPLATES["my_event"] = [
    "While following the road, {hero_name} encountered something strange and very likely important.",
]
```

### 12.2 Template: new class

`game_data.py`:

```python
CLASSES: dict[str, dict[str, int]] = {
    "Hitter": {"fighting": 20, "defending": 20},
    "Blaster": {"magic": 20, "defending": 20, "stealth": 20},
    "Hider": {"stealth": 20, "magic": 20, "fighting": 7, "defending": 7},
    "Oracle": {"magic": 25, "speech": 15, "defending": 10},
}
```

`game_engine.py`:

```python
def __init__(self, hero_name: str = "Hero", hero_class: str = "Hitter", ...):
    self.hero_class = hero_class
    self.base_skills = {
        "fighting": 5, "defending": 5, "magic": 5, "stealth": 5, "speech": 0
    }

    if hero_class in CLASSES:
        for skill, boost in CLASSES[hero_class].items():
            self.base_skills[skill] += boost

    if hero_class == "Oracle":
        self.max_hp += 10
        self.hp += 10
```

If the class also has a combat specialty, add it to `_fight_core_stats()` or `resolve_fight()`.

### 12.3 Template: new relic with a new effect

`game_data.py`:

```python
RELICS: dict[str, RelicDef] = {
    "Townkeeper's Charm": {
        "type": "accessory",
        "effect": "heal_on_town_enter",
        "skill": None,
        "bonus": 0,
    },
}
```

`game_engine.py`:

```python
def apply_relic_effect(self, effect_name: str, **context) -> None:
    if effect_name == "heal_on_town_enter":
        if any(eq and eq.get("name") == "Townkeeper's Charm" for eq in self.equipment.values()):
            heal_amount = 10
            self.hp = min(self.max_hp, self.hp + heal_amount)
            self.log("RELIC_TOWN_HEAL", {"amount": heal_amount, "hp": self.hp})
```

Controller trigger:

```python
def _enter_town_recovery(self) -> None:
    assert self.engine is not None
    self.engine.apply_relic_effect("heal_on_town_enter")
    if self.engine.hp >= self.engine.max_hp:
        self._enter_level_up()
        return
    self.town_shop_offer = self.engine.generate_trader_offer()
    self._prepare_town_year()
```

### 12.4 Template: new random event in the journey loop

Engine side:

```python
def roll_journey_event_type(self) -> str:
    if random.random() < 0.001:
        return "GENIE_RELIC"

    # existing logic below
    if random.random() < 0.12:
        return "SUPER_MONSTER"
    if random.random() < 0.18:
        return "MAGIC_SHRINE"
    if random.random() < 0.12:
        return "WANDERING_TRADER"
    return "FIGHT"
```

Controller side:

```python
def _action_advance_event(self) -> None:
    e = self.engine
    assert e is not None

    event_type = e.roll_journey_event_type()
    if event_type == "GENIE_RELIC":
        self._start_genie_offer()
    elif event_type == "MAGIC_SHRINE":
        ...
```

### 12.5 Template: new town action

Controller:

```python
def _action_town_visit_oracle(self) -> None:
    e = self.engine
    assert e is not None

    if e.cash < 100:
        self.ctx["town_message"] = "The oracle refuses to speak without a fee."
        return

    e.cash -= 100
    e.base_skills["magic"] += 5
    self._go_to_journey("The oracle whispers a blessing into your mind.")
```

UI button:

```json
{ "type": "button", "frame": "actions", "label": "Consult the Oracle", "action": "town_visit_oracle" }
```

### 12.6 Template: new item use / consumable

Controller:

```python
def _action_use_item(self, letter: str) -> None:
    e = self.engine
    assert e is not None

    item, slot = self._find_letter_item(letter)
    if not item or item.get("name") != "Potion of Mending":
        return

    e.hp = min(e.max_hp, e.hp + 25)
    if item in e.inventory:
        e.inventory.remove(item)
    self.screen = "inventory"
```

This is the pattern for any special-use item with a one-off effect.

### 12.7 Template: save migration

If you add a new engine field and want backward compatibility:

```python
SAVE_VERSION = 2


def _restore_payload(self, payload: object) -> bool:
    if not isinstance(payload, dict):
        return False

    version = payload.get("version")
    if version == 1:
        payload = self._migrate_v1_to_v2(payload)
    if version != self.SAVE_VERSION:
        return False

    ...


def _migrate_v1_to_v2(self, payload: dict) -> dict:
    engine_data = payload.get("engine", {})
    if not isinstance(engine_data, dict):
        return payload
    if "status_effects" not in engine_data:
        engine_data["status_effects"] = {}
    payload["version"] = 2
    return payload
```

### 12.8 Template: debug-only feature toggle

Engine:

```python
class HeroAdventureEngine:
    def __init__(self, ..., new_town_bonus_enabled: bool = True):
        self.new_town_bonus_enabled = new_town_bonus_enabled
```

Usage:

```python
if self.new_town_bonus_enabled:
    self.hp = min(self.max_hp, self.hp + 10)
```

This makes it easy to test a new rule in `sim_runner.py` without permanently changing the balance.

### 12.9 Common gotchas to watch for

- Do not put UI code in `game_engine.py`
- Do not put combat math in `game_controller.py`
- If a new effect is data-driven, keep it in `RELICS` and handle by name in the engine
- If a new screen needs new data, add it in `get_context()`
- If the screen is only display-only, the JSON and `ctx` values may be enough
- If it is a world state change, it almost always belongs in the engine
- If it is a route change or action branch, it almost always belongs in the controller
- If you change save/load structure, bump `SAVE_VERSION` and migrate old saves
- If you add a new leg, check any assumptions like “exactly 5 legs” in narration and UI text

## 13. Recap: the golden rules

- Keep data in `game_data.py`
- Keep rules in `game_engine.py`
- Keep app flow in `game_controller.py`
- Keep rendering in `ui/*.json` and front-end renderers
- Add a screen by editing UI + controller, not the renderers
- Use the engine for behavior, the controller for state transitions
- Debug by breaking in dispatch, advance_event, resolve_fight, and take_damage
- For new features, start with: data → engine → controller → UI → debug

This architecture is intentionally designed to let the game grow without rewriting the front-ends or breaking the rules layer.

One more thing worth adding to every feature plan: write a one-sentence conceptual test before coding. Example:

- “The genie event occurs only 0.1% of journey events and offers exactly three unique relics not currently owned by the hero.”
- “Entering town with the Townkeeper’s Charm restores 10 HP before town recovery resolves.”
- “The Oracle class gains +10 max HP and +5 magic at character creation.”

That single sentence keeps scope clear and prevents feature drift.

## 14. Full worked example: adding the genie relic event

This section walks through the exact architecture pattern for the example feature you described: a rare genie event that offers one of three relics the hero does not already have, with a 0.1% chance while journeying.

The goal is to implement it in the same style as the rest of the project: engine picks the event, controller displays the screen, UI renders the buttons, and the engine mutates the save state when the player chooses.

### 14.1 Feature spec in one sentence

“The genie event occurs with a 0.1% chance on a journey step, shows three unique relic choices the hero does not own, and the chosen relic is added to the hero’s inventory when accepted.”

This is exactly the kind of feature sentence worth writing before touching code.

### 14.2 Data changes

No new monster or leg data is required. This is a new journey event, so most of the content is in narration templates and the event string.

Add a new template to `EVENT_NARRATION_TEMPLATES` in `game_data.py`:

```python
"genie_relic": [
    "While traveling through {leg_vibe}, {hero_name} noticed a tiny lantern bobbing in the dust, and a genie stepped out of the smoke with a grin.",
    "On {leg_vibe}, {hero_name} was approached by a genie carrying three impossible gifts and a suspiciously calm expression.",
    "Near {leg_vibe}, a genie appeared from nowhere and offered a choice between a few items that seemed far too valuable to be legal.",
],
```

If you want the event to participate in reminiscence later, add a corresponding template in `REMINISCENCE_TEMPLATES`:

```python
"genie_relic": [
    "For a moment, {hero_name} remembered the genie who had offered three impossible relics and then vanished before the bargain was settled.",
],
```

And add it to the eligible event set if you want it to show up in the reminiscence engine:

```python
REMINISCENCE_ELIGIBLE_EVENTS = {
    "fight", "dungeon_found", "wandering_trader", "magic_shrine",
    "super_monster", "wander_group", "fairy_found", "dungeon_floor",
    "dungeon_boss", "genie_relic",
}
```

### 14.3 Engine change: trigger the event

Add the probability in `HeroAdventureEngine.roll_journey_event_type()`.

```python
def roll_journey_event_type(self) -> str:
    # Rare special event: we want a 0.1% chance on each journey step.
    if random.random() < 0.001:
        return "GENIE_RELIC"

    # ... existing logic continues here ...
```

This makes the event rare but not impossible, which is usually the right balance for a special relic offer.

### 14.4 Controller change: start the screen

Add a helper in `GameController`:

```python
def _start_genie_offer(self) -> None:
    e = self.engine
    assert e is not None

    available = [name for name in RELICS if name not in e.relics_found]
    if len(available) < 3:
        self._go_to_journey("The genie sighs: there are no more relics worth offering.")
        return

    chosen = random.sample(available, 3)
    self._set_narration("genie_relic")
    self.ctx = {
        "relic_a_name": chosen[0],
        "relic_b_name": chosen[1],
        "relic_c_name": chosen[2],
        "event_narration": self.current_narration,
    }
    self.screen = "genie_relic_offer"
```

Then add the event hook in `_action_advance_event()`:

```python
elif event_type == "GENIE_RELIC":
    self._start_genie_offer()
```

This is the key part: the controller owns the screen route, while the engine tells it which event type occurred.

### 14.5 UI screen

Create a file:

- `ui/genie_relic_offer.json`

Example:

```json
{
  "id": "genie_relic_offer",
  "title": "A Genie Offers Three Relics",
  "frames": [
    { "id": "status", "role": "status", "ratio": 0.15, "overflow": "collapse" },
    { "id": "scene", "role": "scene", "ratio": 0.6, "overflow": "truncate" },
    { "id": "context", "role": "context", "ratio": 0.15, "overflow": "page" },
    { "id": "actions", "role": "actions", "ratio": 0.10, "overflow": "collapse" }
  ],
  "controls": [
    { "type": "text", "frame": "scene", "value": "{event_narration}" },
    { "type": "text", "frame": "context", "value": "Choose a relic." },
    { "type": "button", "frame": "actions", "label": "{relic_a_name}", "action": "accept_genie:{relic_a_name}" },
    { "type": "button", "frame": "actions", "label": "{relic_b_name}", "action": "accept_genie:{relic_b_name}" },
    { "type": "button", "frame": "actions", "label": "{relic_c_name}", "action": "accept_genie:{relic_c_name}" },
    { "type": "button", "frame": "actions", "label": "Decline", "action": "decline_genie" }
  ]
}
```

This relies on the existing rendering contract: `GameController.get_context()` populates the values and the front-end just renders them.

### 14.6 Controller actions for accepting/declining

Add handlers:

```python
def _action_accept_genie(self, relic_name: str) -> None:
    e = self.engine
    assert e is not None

    if relic_name not in RELICS:
        return

    info = RELICS[relic_name]
    item = {
        "name": relic_name,
        "category": "relic",
        "slot": info["type"],
        "tier": "Epic",
        "code": "e",
        "skill": info["skill"],
        "skill_val": info["bonus"],
        "weight": 1,
        "value": 25000,
        "uses": 1,
        "max_uses": 1,
    }
    e.inventory.append(item)
    e.relics_found.append(relic_name)
    self._go_to_journey(f"The genie presents {relic_name} and vanishes into the dust.")


def _action_decline_genie(self) -> None:
    self._go_to_journey("You politely refuse the genie and continue on your way.")
```

This is the exact “UI action → controller → engine mutation” flow the project expects.

### 14.7 Save behavior and state consistency

Because this new relic is an inventory item and a found relic record, it should already persist through saves because:

- `HeroAdventureEngine.__dict__` is stored in the save payload
- if the item is added to `inventory` and the relic is appended to `relics_found`, it is automatically saved

This is an important benefit of the architecture: you do not need to manually wire the relic into a save-specific format unless the structure itself changes.

### 14.8 Optional: log it for debug and narrative analysis

Add a log entry in the engine when the offer is accepted or created:

```python
def _start_genie_offer(self) -> None:
    e = self.engine
    assert e is not None
    ...
    e.log("GENIE_RELIC_OFFERED", {"relics": chosen})
```

When accepted:

```python
def _action_accept_genie(self, relic_name: str) -> None:
    ...
    e.log("GENIE_RELIC_ACCEPTED", {"relic": relic_name})
```

This makes analyzing the event easier in `sim_logs` or debugging output.

### 14.9 Optional: place it in the journey flow with a little extra flavor

If you want a custom intro or victory path, add a small screen before the journey begins or after the relic is accepted:

```python
def _action_genie_intro_continue(self) -> None:
    self.ctx = {}
    self.screen = "journey"
```

This is exactly the same pattern used by the origin story flow and is the cleanest place for a custom pre-event “story beat.”

### 14.10 Why this example fits the architecture

This is the ideal feature for the project because:

- the event is selected by the engine
- the UI doesn’t know any rules
- the controller owns the screen transitions
- the new item is an inventory mutation in the engine
- the new narration is table-driven in `game_data.py`
- the screen is declarative JSON

That means the logic is isolated exactly where the architecture expects it.

## 15. A short “feature implementation checklist”

Before writing code, ask:

- Does this change world state or only presentation?
- Is it static data, runtime rules, or controller flow?
- Does it need a new screen?
- Does it need a new event or a new branch in an existing event?
- Does it need to be saved or migrated?
- Does it need a debug log or a simulation hook?
- Is the change purely additive, or does it alter existing assumptions like “there are exactly five legs”?

If you can answer those quickly, new work usually lands in the correct place on the first pass.

## 16. Final advice

The codebase is designed for small, clean additions. The best changes are the ones that follow the same pattern everywhere:

- add static config to `game_data.py`
- add behavior to `game_engine.py`
- trigger it from `GameController`
- render it via `ui/*.json`
- validate using the simulator or a breakpoint

That discipline is the reason the code remains modular even as the feature set grows.

- Keep data in `game_data.py`
- Keep rules in `game_engine.py`
- Keep app flow in `game_controller.py`
- Keep rendering in `ui/*.json` and front-end renderers
- Add a screen by editing UI + controller, not the renderers
- Use the engine for behavior, the controller for state transitions
- Debug by breaking in dispatch, advance_event, resolve_fight, and take_damage

This architecture is intentionally designed to let the game grow without rewriting the front-ends or breaking the rules layer.

If you want, I can also produce a second document focused specifically on “exact code edits for feature X,” such as:

- adding the genie relic event as a real patch,
- adding a new class and relic effect,
- creating your own new screen with UI JSON and controller hooks.
