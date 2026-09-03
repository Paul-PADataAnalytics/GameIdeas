Smart fixes applied
-------------------

This file tracks each complaint from [dumb.md](dumb.md) with the reasoning behind the
fix and where it landed in the code. Items are processed as soon as they appear
complete in dumb.md (a paragraph that isn't mid-sentence/cut off).

## 1. Inventory and character sheet were split across two screens

**Answer:** They're now one screen. `inventory` is the single source of truth: the
backpack list lives in `scene` (left, dominant reading area) and character stats +
equipment + title/honor sit in `context` (right), per your explicit ask (this is an
intentional exception to the general scene/context guidance in
[UI_FRAME_PORTING_GUIDE.md](uigames/hero_adventure/UI_FRAME_PORTING_GUIDE.md)).

- Deleted `ui/character_sheet.json`; merged its controls into
  [ui/inventory.json](uigames/hero_adventure/ui/inventory.json).
- Removed the separate `open_character_sheet`/`close_character_sheet` actions in
  [hero_engine.py](uigames/hero_adventure/hero_engine.py); `open_inventory` now opens the merged screen.
- Combat and journey screens' duplicate "Character" button was removed; the remaining
  button is labelled "🧑 Character & Inventory".

## 2. Choosing a class required a separate "Confirm & Begin Journey" button

**Answer:** Tapping a class button (Hitter/Blaster/Hider) now directly starts the
journey (calls the same logic `confirm_character` used), as long as a hero name has
been entered. The standalone confirm button was removed from
[ui/character_creation.json](uigames/hero_adventure/ui/character_creation.json).

## 3. No way to keep/discard loot after a fight

**Answer:** The loot screen now lets you toggle each drop between ✅ KEEP and
❌ DISCARD before continuing (tap the row to flip it; default is keep). On
"Confirm & Continue", discarded items are actually removed from the backpack.
Implemented via `_build_combat_loot_rows`, `_action_toggle_loot_item`, and the
updated `_action_loot_continue` in hero_engine.py. Covers regular fights, dungeon
floors/bosses, and super monsters (all route through the same loot screen).

## 4. Inventory didn't show what's currently equipped

**Answer:** This was already tagged in code (`[Equipped]`/`[Backpack]`), but the
labels were easy to miss. Made them louder: rows now show "✅ Equipped" vs
"🎒 Backpack" so equipped gear is unambiguous before you tap an item.

## 5. Inventory should highlight better (green) / worse (red) items

**Answer:** Added `_item_highlight()`: for each backpack item with a skill effect, it
compares against whatever is currently equipped in that same slot, but only when the
equipped item shares the same skill (matches your "limited to the type of effect
they currently have" rule). An empty slot always counts as an improvement (green).
Relics aren't compared (no meaningful stat to diff). Wired into both renderers:
- Terminal ([play.py](uigames/hero_adventure/play.py)): `inv_better`/`inv_worse` CSS classes (green/red).
- GUI ([play_gui.py](uigames/hero_adventure/play_gui.py)): button `text_color` set per highlight.

## 6. "Load Game" gave no info and only supported one save

**Answer:** Rebuilt as a real multi-slot save system. Each hero now gets its own save
file under `uigames/hero_adventure/saves/<hero_name>.json`. "Load Game" now lists every
save as `Leg {leg} - Event {event} - Hero: {name}` (e.g. "Leg 3 - Event 12 - Hero:
Arin") and picking a row loads that specific run. See the new
[ui/load_game.json](uigames/hero_adventure/ui/load_game.json) and
`_list_save_slots`/`_action_load_slot` in hero_engine.py.

## 7. Could create a new hero with a name that already has a save

**Answer:** `_action_confirm_character` (now also triggered by class selection, see
#2) checks `_save_name_exists()` before creating the engine. If a save already exists
for that name, it blocks creation and shows a message on the character-creation
screen instead ("A save already exists for '<name>'. Choose a different name or load
that save instead.").

## 8. Winning didn't clean up the save; Save + Quit were two separate buttons

**Answer:**
- `_action_capital_continue` (reached after buying a house or keeping the pension at
  the end of a successful run) now deletes that hero's save file — a finished run
  shouldn't leave a stale continuable save behind.
- Journey's separate "💾 Save Game" and "Quit to Menu" buttons are merged into one
  "💾 Save & Quit" button (`_action_save_and_quit`): it always saves first, then
  returns to the front page.

## 9. Journey screen showed a generic "Journey events include..." line

**Answer:** Removed that filler text from
[ui/journey.json](uigames/hero_adventure/ui/journey.json) entirely. The screen already
renders `{event_narration}` above it, i.e. the actual thing that just happened, so
the generic blurb was pure noise.

---

## 10. Aging mechanic + forced town healing + retirement paths

**Answer:** This was a large, ambiguous design change, so I asked clarifying
questions before implementing (see chat history) and built the feature based on
your answers:

- **All journey-time healing removed.** The TAVERN and CAMP journey events are
  gone entirely (their event-pool weight rolled into FIGHT in
  [hero_engine.py](uigames/hero_adventure/hero_engine.py)'s `roll_journey_event_type()`),
  `apply_tavern_rest`/`apply_camp_rest` were deleted, and Magic Shrine
  (`resolve_magic_shrine`) no longer heals (loot only) — since the goal was
  removing *all* journey-time healing, not just tavern/camp. Medical items
  (Bandages/Potions/Herbs) are removed from the loot tables entirely (the
  `medical` entry in `ITEM_CATEGORIES` in `game_data.py`) rather than just
  disabling their "Use" button — since they can no longer be used to heal,
  they'd otherwise still be findable as pointless dead-weight loot.
- **Age tracking:** `HeroAdventureEngine.age` starts at 17 (`AGE_START` in
  `game_data.py`) and is displayed in the status bar on the Character/Inventory,
  Capital, Capital Result, and Town Recovery screens.
- **Mandatory town recovery:** hooked into the existing leg-transition point
  (`try_leg_transition() == "LEVEL_UP"`), right before the level-up screen. If
  the hero is already at full HP the whole sequence is skipped. Otherwise it
  plays out year-by-year (new `town_recovery` screen/state machine in
  `GameController`): each year heals up to 10 HP (partial on the last year,
  e.g. 35 missing HP = 4 years) and ages the hero by 1, with a silly
  procedurally-generated blurb (medieval profession + tone modifier + injury +
  body part, new lists in `game_data.py`). Each year the player chooses
  "Work and recover for another year" or "Go back to adventuring" (stop early
  at current HP).
- **5% profitable job offer:** each town year has a 5% chance of instead
  offering permanent retirement as the year's profession (`town_retire`
  action), ending the game immediately with a pension-based score.
- **Forced retirement at 50:** if a town year pushes age to 50, the hero is
  immediately routed to "the failed adventurer" ending — still gets the normal
  house/pension choice on the Capital screen, but the final score is cut to
  25% (`_action_buy_house`/`_action_keep_pension` now check
  `self.failed_adventurer`).
- **Age-scaled pension:** `get_pension()` now rolls a random end-of-life age
  (60-90, once per hero) and scales the old flat cash-based pension by
  `20 / years_remaining` (clamped 0.2x-3x) — a younger hero needs more cash to
  match an older hero's pension, since their cash has to last longer.
- **Docs:** added a new "Aging & Town Recovery" section to
  [heroadventure.md](uigames/hero_adventure/heroadventure.md) and updated the
  Character/Journey sections to remove references to tavern/camp/medical
  healing.
- **`sim_runner.py` now models aging too.** Its headless path
  (`MonteCarloAgent.town_recovery()`) replicates the interactive town-recovery
  loop: heals 10 HP/year, ages the hero, rolls the same 5% job-offer chance
  each year (always declined, since the agent's goal is to finish the
  journey) and the same forced retirement at age 50 (ending the run with the
  usual 25% score penalty via `calculate_score(..., failed_adventurer=True)`).
  Each run's summary now includes `town_years` and `ending_age`, and
  `run_batch_simulation()` prints an aggregate rest/age breakdown
  (wins/forced-retirements/deaths) after each batch.

## 11. Class balance pass (Hider was nearly unplayable, Hitter/Blaster couldn't escape bad odds)

**Answer:** You asked why balancing felt like whack-a-mole (fixing early game
broke late game and vice versa). A 2000-run Monte Carlo diagnostic showed the
real problem wasn't per-leg monster tuning at all — it was per-*class*:
Hitter won 39%, Blaster 11%, Hider just **1%**, and 90%+ of Hider deaths
happened in leg 1 alone (a stealth build with no combat stats gets dumped
into a fight it can't win the moment a sneak/steal fails). Implemented and
A/B-tested four fixes in [hero_engine.py](uigames/hero_adventure/hero_engine.py)/
[game_data.py](uigames/hero_adventure/game_data.py)/[sim_runner.py](uigames/hero_adventure/sim_runner.py):

- **#1 - Stealth counts as attack power.** `_fight_core_stats()`'s
  `player_atk` is now `max(fighting, magic, stealth * 0.5)` instead of just
  `max(fighting, magic)`, so a failed sneak/steal isn't a guaranteed weak
  fight for stealth builds. *Alone, this barely moved the needle* (Hider
  1.6% -> 1.9%) — stealth wasn't a big enough number to matter on its own.
- **#2 - Hider stat floor.** `CLASSES["Hider"]` in `game_data.py` now also
  grants `+7 fighting`/`+7 defending` (5 -> 12 base), just enough to survive
  a forced early fight. *This was the real fix for leg 1* — combined with #1,
  Hider's win rate jumped to 24% and leg-1 deaths collapsed from ~600 to 6
  (out of 2000 runs).
- **#3 - "Throw Item" escape.** New `throw_item` tactical choice
  (`resolve_fight`/`get_tactical_choice` in `hero_engine.py`) usable by any
  class, in any encounter (including dungeons/super monsters, which never
  had a "Run Away" option): consumes one spare inventory item and guarantees
  escape with no damage, at the cost of that item and the encounter's loot.
  Added as a real "Throw Item" button in
  [combat.json](uigames/hero_adventure/ui/combat.json) (`visible_if
  has_throwable_item`), not just a sim heuristic. The AI picks it over a
  blind sneak when below 50% HP and stealth looks unlikely to succeed. This
  had the single biggest effect of all four: overall win rate 25% -> 38%,
  Hitter 38% -> 54%, Blaster 12% -> 28% — confirming Hitter/Blaster's
  mid/late-game deaths were really about having zero escape options across
  ~100 mandatory full-risk fights per run, not raw stat shortfalls.
- **#4 - Relic-monster scaling (tried, not adopted).** Added an opt-in
  `relic_scaling_enabled` toggle (`HeroAdventureEngine.__init__`,
  `_get_monster_stats()`) that scales dungeon-boss/super-monster stats by
  `RELIC_MONSTER_SCALE` (1.2x) independently of regular per-leg monsters —
  `sim_runner.py --relic-scaling` to test it. Result: it made things *worse*
  across the board (overall 38% -> 21%), and specifically undid the leg-1
  fix (Hider crashed back to 1.7%, leg-1 deaths jumped back to 728) because
  it blindly toughens every relic monster regardless of how early a
  low-level hero might run into one (leg-1 dungeon bosses/the leg-1 super
  monster included). **Left disabled by default** — the multiplier would
  need to scale by leg/player progress rather than flatly, if revisited.
- All four changes are individually toggle-able for testing:
  `sim_runner.py --no-stealth-atk` / `--no-hider-bonus` / `--no-throw-item` /
  `--relic-scaling` (all default to the shipped/adopted state: #1-#3 on,
  #4 off).
- Cumulative 2000-run results: initial 15.3% -> +1 14.8% -> +1+2 25.0% ->
  **+1+2+3 37.8% (shipped)** -> +1+2+3+4 20.8% (rejected).

## 12. Fight round text could repeat within one fight; no closing "kill" line

**Answer:** `_combat_line()` in [hero_engine.py](uigames/hero_adventure/hero_engine.py)
now takes an optional `used_lines` set - `resolve_fight()` creates one fresh set per
encounter and threads it through every `_combat_action_line()` call in that fight, so
the same (category, opening-line, closing-line) template combo is never picked twice
in a row across rounds (falls back to allowing repeats only if every combo in a
category has genuinely been exhausted, which 50 combos vs. an 8-round cap makes
essentially impossible). Also added `KILL_PHRASES` (10 lines, including your
"...and then they goofed the whole pooch") and a `_kill_phrase()` helper - appended to
the round text at every point a monster actually dies mid-narration: the killing blow
of a multi-round fight, an instant relic-combo win, and a successful stealth kill.
(Steal/sneak/run/throw-item don't get one - the monster isn't dead in those cases.)

## 13. Repeated monster encounters felt identical - no acknowledgement it's the "same" monster type

**Answer:** Added `HeroAdventureEngine.monster_encounter_counts` (a `{monster_name:
count}` dict, part of the normal engine state so it saves/loads for free via the
existing `engine.__dict__` payload). Each regular journey fight
(`_action_advance_event`'s fallthrough case) increments the count for that monster
name and passes it to `_set_narration`, which now has a `REPEAT_ENCOUNTER_TEMPLATES`
table keyed by encounter number: distinct 2nd- and 3rd-encounter phrasing (e.g. "ran
into another Cave Spider - maybe it's the first one's brother", "encountered yet
another Cave Spider, this one seems particularly vengeful" - both close to your exact
examples), then a "many" tier for the 4th+ that uses an ordinal ("braced for the 5th
Cave Spider of the trip") so it keeps scaling without needing one template per count.
Scoped to regular journey monsters only (not dungeon/boss/super monsters, which
already have distinct one-off narration and are far less repetitive by design).

## 14. Journey needed more flavor/reminiscence text tied to actual events (not per-item lore)

**Answer:** This was flagged as possibly "hideously expensive", so we talked
through the design in chat before building anything, and deliberately dropped
the most expensive sub-idea (per-loot-item backstory, e.g. reminiscing about
a monster's mace needing repair) - there's no item-lore data to hang that on
and inventing it for every item wasn't worth it. What shipped instead reuses
data the engine already tracks or now tracks cheaply:

- **`HeroAdventureEngine.special_moments`** - a FIFO log capped at the most
  recent 10 entries *shared across all types*, via a new `_log_special_moment()`
  helper. Logged at: a relic drop (`grant_monster_loot`), a dungeon boss beaten
  (all three `resolve_fight` win paths - fight/steal/stealth_kill), and the
  *first* time a regular monster's encounter count reaches 3 (in
  `_action_advance_event`, reusing item #13's `monster_encounter_counts` - not
  re-logged for every kill after that, since the live count can always be
  re-read at recall time). Left generic enough that future special events
  (camping/shrine/trader/tavern) can log into the same pool later.
- **`HeroAdventureEngine.town_history`** - every town-recovery year
  (`_generate_town_blurb`) now appends its rolled
  profession/modifier/injury/body_part to a list, also capped at the most
  recent 10, instead of being thrown away after one blurb.
- **Reminiscence templates** (`GameController.REMINISCENCE_TEMPLATES`,
  `_maybe_add_reminiscence()`): after building normal journey-event narration
  (fight/dungeon/trader/shrine/super monster/wander group/fairy - not
  town-recovery itself), there's an 18% chance (`REMINISCENCE_CHANCE`) of one
  extra sentence pulled from whichever of these the hero actually has: a past
  town job, a monster faced 3+ times, a logged special moment, or their fixed
  backstory (see #15) - e.g. "Rin thought back to the year spent as a sleepy
  candlestick maker, and how a blister to the heel never quite faded." All
  data is stored structured (not pre-rendered), so wording can change later
  without losing old memories, and it costs nothing extra to carry in saves
  (goes along for free in the existing `engine.__dict__` dump).
- **Design decisions made in chat, in order:** FIFO eviction across all
  special-moment types (not per-type quotas); same-monster memory triggers
  once at the 3rd encounter, not re-logged on every later kill; cap of 10 is
  a starting guess, tunable later. A "tiered/toggle" idea (disable narrative
  flavor on low-power ports) was raised and then explicitly dropped - this
  Python version is the reference implementation ("the bible") other
  ports/languages are carved from, so it always has the full feature; lower-
  powered ports decide what to drop when they're built, not this one. A
  "export the whole playthrough as a chapter-per-leg story" idea was raised
  and intentionally **not** built yet - parked as a future item once the
  reminiscence line pool has been tuned (see instrumentation below) and
  proven readable over a full run.
- **Instrumentation** (new
  [narrative_instrument.py](uigames/hero_adventure/narrative_instrument.py)):
  since "does this feel repetitive" isn't eyeball-able, this drives full
  headless playthroughs through `GameController.dispatch()` (not the fast-sim
  engine API, since narration only exists at the controller layer) and counts
  how many times each template (`category:index`, via the new
  `_choose_template()` helper used everywhere `random.choice(templates)` used
  to be) gets picked in a single run, flagging anything reused more than 3
  times (your stated target). A 100-run pass found the two new reminiscence
  categories only occasionally exceed target (a couple of runs out of 100),
  which is expected/acceptable at 3 templates each - but it also surfaced
  that several *pre-existing* pools (`event_fight`, `event_dungeon_floor`,
  `event_town_recovery`, `repeat_encounter_2`, all only 3-4 templates against
  very high per-run frequency) exceed the target far more often (used in
  25-40% of runs). Those pools predate this change and weren't touched here -
  flagging for your review since the instrumentation was built specifically
  to catch this.

## 15. Add an introductory backstory before the first journey event

**Answer:** New `origin_story` screen, shown once right after character
creation (`_action_confirm_character`) and before the first journey event.
`GameController._generate_backstory()` rolls a hometown, family member +
one-line quirky trait, and a personal aspiration (new `HERO_HOMETOWNS` /
`HERO_FAMILY_MEMBERS` / `HERO_FAMILY_TRAITS` / `HERO_ASPIRATIONS` lists in
`game_data.py`), stored on `HeroAdventureEngine.backstory` for the whole run
(persists via the existing save mechanism, and is the data source for #14's
backstory-flavored reminiscence lines). `_build_origin_story()` combines a
random `ORIGIN_STORY_TEMPLATES` paragraph with a fixed-variance
`ORIGIN_STORY_CLOSERS` line that always restates the actual win condition
(visit all 5 major cities, retire on a fortune) - a rules reminder wearing a
narrative coat, per your explicit ask. New
[ui/origin_story.json](uigames/hero_adventure/ui/origin_story.json) renders it
with a single "Begin the Journey" button (`origin_continue` action). Fixed an
a/an grammar bug along the way (`family_article`, computed once at generation
time from the chosen family member, e.g. "an older sister" vs. "a mother").

