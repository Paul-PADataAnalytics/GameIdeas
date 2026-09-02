# Hero Adventure

A short game with a point score at the end following a hero's adventure to glory or death.

## Character

The hero is the player character and we create them by picking a class and setting their attributes.

The classes are Hitter, Blaster, and Hider.  These classes set the skills and capabilities of the player character.  The choice of a class gives and initial boost to three of ten skills.

The hero always has a max HP of 100 and starts with 100 HP.  The hero can lose HP during events and if they reach 0 HP, they die and the game ends.  There is no way to heal during the journey itself - HP lost during a leg can only be recovered afterward, during the mandatory town recovery stay described in Aging & Town Recovery below.

The skills are:

- fighting
- defending
- magic
- stealth
- salvaging
- spotting
- camping
- medical

All players start at 5 in each skill.

The Hitter gets a +20 to fighting, defending, and camping.

The Blaster gets a +20 to magic, spotting, and medical.

The Hider gets a +20 to stealth, salvaging, and spotting.

The players max carry weight = (fighting + defending + (salvaging * 2))*2 skills, and if they are overburdened, they will be penalized in their skills by 10% for every 10 weight units over the limit.  All skills are reduced by 10% for every 20 weight units over the limit, with no effect taking place until the player is overburdened by over 20 weight units.


## Skills

The skills are used to determine the outcome of the game.  The events will have a function that calculates the two outcomes of success or failure, these are described in the event.

## Journey

The Hero is on a journey across the country to find fortune and will end in the Capital. If the hero has accumulated enough fortune (gold/cash), they will be able to buy a home and retire. If not, they will work in a tavern and live a life of obscurity. The end of the journey represents the end of the game character and the score is based on the life they ended up with. There are a selection of houses that can be purchased and the resulting cash is given up as a pension - the score is the two multiplied together. If the hero ends up in a tavern, the score is based only on the pension. The pension itself is also scaled by the hero's age at retirement - see Aging & Town Recovery.

The journey is made up of 5 legs of 20 events.  The journey is a series of events.  The events are randomly selected from a pool of events that are appropriate for the leg of the journey.  The events will have a function that calculates the two outcomes of success or failure, these are described in the event.  See the Dungeons section for details on dungeon discovery and exploration.

A player levels at the end of a leg of the journey, and can choose to increase three of their skills by 5 points.  The player can only level up at the end of the leg of the journey. Before leveling up, if the hero is not at full HP, they must first go through the town recovery sequence described in Aging & Town Recovery.

There are some specifics however: fights are the dominant event type in every leg. Free-loot style journey events (Magic Shrine and Wandering Trader) also have a per-type 3-event cooldown so they cannot chain too frequently.  The super monster can only occur once per leg of the journey, and is a special event that is more difficult than the regular monsters of the leg.  The super monster will always have a relic and 1-2 equipment items.

There are specific monsters that are assigned to each leg of the journey, and they are listed in the Monster Lookup Table.  The monsters have a chance to drop loot, and the loot is based on the leg of the journey.

## Aging & Town Recovery

There is no healing available during the journey itself - the only way to recover lost HP is to return to town, which happens automatically and mandatorily at the start of every new leg (right before the level-up screen). If the hero is already at full HP when a leg ends, the town recovery sequence is skipped entirely and the hero goes straight to leveling up.

If the hero is hurt, town recovery plays out one year at a time: each year heals 10 HP (or whatever is left to reach full HP, if less than 10 is needed) and ages the hero by 1 year, starting from an initial age of 17. Every year comes with a short, silly blurb about the odd job the hero took to make ends meet while recovering (a medieval profession, with a touch of injury-based humor). After each year, the player chooses to keep working and recovering for another year, or head back out on the road immediately at their current HP (ending the recovery sequence early, at less than full health).

Each year in town also carries a small (5%) chance that the hero is offered a permanent, steady job in town instead of another year of recovery. If offered, the player can choose to retire on the spot (ending the game, with a score based on their pension) or turn it down and keep adventuring.

If a hero's age reaches 50 during town recovery, they are forced into retirement immediately - too old to keep adventuring. This ends the game as "the failed adventurer": the hero still goes through the normal house-buying/pension choice, but the final score is reduced to 25% of what it would otherwise be.

The pension awarded at retirement (whether from reaching the Capital, an early job offer, or a forced age-50 retirement) is based on the hero's remaining cash, scaled by age: a random end-of-life age between 60 and 90 is rolled once per hero, and the fewer years remaining until that age, the further the same amount of cash goes. A younger hero therefore needs to accumulate more cash to retire as comfortably as an older one.

## Dungeons

Dungeons are optional side areas that the hero can discover and explore during the journey. There are exactly two dungeons per leg of the journey. Once the player has successfully spotted both dungeons in a leg, no more dungeons can be found for the remainder of that leg.

Each journey event has a chance to spot a dungeon entrance. This is based on a roll of 0 - 100; if the player's spotting skill is equal to or greater than the roll, a dungeon is found. When a dungeon is found the player can choose to enter it or ignore it and continue the journey. If they enter, they go to the Dungeon page; if they ignore it, they continue the journey.

A dungeon is a series of 5 floor fights of increasing difficulty followed by a final Dungeon Boss fight. On every dungeon floor — including right before facing the Dungeon Boss — the player can inspect the monster they are about to fight and has an explicit "Exit Dungeon" button to leave the dungeon safely at any time before initiating combat, returning to the journey where they left off.

If the hero defeats the boss, they are able to take the treasure and gain fortune. If they fail, they are injured and returned to the front door to continue the journey.

### Dungeon Floor Encounters

Each dungeon contains five themed floor monsters leading to its boss. Floor 1 is the weakest and Floor 5 is the strongest. The stats below are used by the engine.

#### The Goblin's Den

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Goblin Scavenger | Dungeon Floor | 12 | 8 | 0 | 15-25 | 1-2 | Picks through refuse in the entry tunnels |
| 2 | Goblin Sentry | Dungeon Floor | 14 | 9 | 0 | 20-30 | 1-2 | Watches the warren's twisting corridors |
| 3 | Goblin Bruiser | Dungeon Floor | 16 | 10 | 2 | 25-35 | 2-3 | Heavy fists and a worse temper |
| 4 | Goblin Shaman | Dungeon Floor | 17 | 11 | 5 | 30-40 | 2-3 | Channels crude magic for the tribe |
| 5 | Goblin Champion | Dungeon Floor | 20 | 12 | 3 | 35-50 | 2-3 | The king's chosen brute |

#### The Bandit's Hideout

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Bandit Recruit | Dungeon Floor | 13 | 9 | 0 | 18-28 | 1-2 | New blood guarding the outer camp |
| 2 | Bandit Thug | Dungeon Floor | 15 | 10 | 0 | 22-32 | 1-2 | Rough muscle keeping order |
| 3 | Bandit Scout | Dungeon Floor | 17 | 12 | 0 | 26-36 | 2-3 | Skirmisher who watches the roads |
| 4 | Bandit Enforcer | Dungeon Floor | 19 | 13 | 0 | 30-42 | 2-3 | Veteran who enforces the lord's will |
| 5 | Bandit Lieutenant | Dungeon Floor | 22 | 15 | 2 | 35-50 | 2-3 | Second-in-command of the hideout |

#### The Spider's Lair

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Spiderling | Dungeon Floor | 15 | 10 | 0 | 20-28 | 1-2 | Swarms of hatchlings in the webbing |
| 2 | Web Spinner | Dungeon Floor | 17 | 12 | 0 | 24-32 | 2-3 | Weaves sticky traps between stones |
| 3 | Venomous Spider | Dungeon Floor | 19 | 14 | 0 | 28-36 | 2-3 | Fat with poison and hunger |
| 4 | Cave Widow | Dungeon Floor | 21 | 15 | 2 | 32-40 | 3-4 | Older, cunning, and deadly patient |
| 5 | Brood Mother | Dungeon Floor | 24 | 17 | 3 | 36-48 | 3-4 | Guards the nest before the queen |

#### The Bandit's Camp

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Camp Lookout | Dungeon Floor | 18 | 13 | 0 | 25-35 | 2-3 | Spotter perched in the camp treeline |
| 2 | Camp Raider | Dungeon Floor | 21 | 15 | 0 | 30-40 | 2-3 | Fast rider who hits supply wagons |
| 3 | Camp Brute | Dungeon Floor | 24 | 17 | 0 | 35-50 | 2-3 | Hulking guard at the camp entrance |
| 4 | Camp Sergeant | Dungeon Floor | 27 | 19 | 0 | 42-60 | 2-3 | Drills the raiders and takes no excuses |
| 5 | Camp Warlord | Dungeon Floor | 30 | 21 | 2 | 50-70 | 3-4 | Rival leader vying for the chief's seat |

#### The Sultans Tomb

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Tomb Scarab | Dungeon Floor | 22 | 18 | 0 | 25-35 | 2-3 | Jewelled beetle that hungers for flesh |
| 2 | Sand Mummy | Dungeon Floor | 25 | 20 | 4 | 30-40 | 3-4 | Dried corpse roused by tomb robbers |
| 3 | Cursed Guard | Dungeon Floor | 28 | 22 | 6 | 35-45 | 3-4 | Animated statue of an ancient soldier |
| 4 | Tomb Priest | Dungeon Floor | 30 | 24 | 10 | 40-50 | 4-5 | Keeper of the sultan's death rites |
| 5 | Royal Guardian | Dungeon Floor | 33 | 26 | 8 | 45-55 | 4-5 | Elite protector of the burial chamber |

#### The Ancient Ruins

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Ruin Wisp | Dungeon Floor | 24 | 20 | 10 | 30-40 | 2-3 | Flickering spirit drawn to old magic |
| 2 | Stone Sentinel | Dungeon Floor | 28 | 24 | 6 | 35-45 | 3-4 | Crumbling construct still on patrol |
| 3 | Arcane Construct | Dungeon Floor | 32 | 28 | 14 | 40-50 | 3-4 | Relic-powered guardian of the halls |
| 4 | Ruin Lichling | Dungeon Floor | 38 | 34 | 24 | 50-60 | 3-4 | A lesser lich feeding on residual power |
| 5 | Ancient Warden | Dungeon Floor | 44 | 40 | 28 | 60-75 | 3-4 | Last defender before the master's vault |

#### The Vampire's Castle

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Castle Bat Swarm | Dungeon Floor | 28 | 22 | 8 | 40-55 | 2-3 | Living cloud of leathery wings |
| 2 | Castle Thrall | Dungeon Floor | 30 | 24 | 10 | 45-60 | 3-4 | Mindless servant of the court |
| 3 | Vampire Spawn | Dungeon Floor | 33 | 26 | 14 | 55-70 | 3-4 | Newly turned and ravenous |
| 4 | Vampiric Knight | Dungeon Floor | 35 | 28 | 16 | 70-85 | 3-4 | Undead champion in rusted plate |
| 5 | Blood Countess | Dungeon Floor | 37 | 30 | 18 | 85-100 | 3-4 | Ancient courtier guarding the lord's keep |

#### The Dragon's Lair

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Hatchling Drake | Dungeon Floor | 30 | 24 | 10 | 50-65 | 2-3 | Young fire-breather testing its teeth |
| 2 | Dragon Whelp | Dungeon Floor | 33 | 27 | 12 | 60-75 | 2-3 | Bigger, bolder, and already greedy |
| 3 | Drake Sentinel | Dungeon Floor | 36 | 30 | 16 | 70-85 | 3-4 | Watchful guardian of the hoard entrance |
| 4 | Dragonkin Champion | Dungeon Floor | 39 | 33 | 20 | 85-100 | 3-4 | Half-scaled warrior devoted to the wyrm |
| 5 | Elder Drake | Dungeon Floor | 42 | 35 | 22 | 100-120 | 3-4 | Ancient cousin too stubborn to leave |

#### The Dark Fortress

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Shadow Acolyte | Dungeon Floor | 36 | 30 | 18 | 60-80 | 3-4 | Cultist chanting in the lower halls |
| 2 | Fortress Guard | Dungeon Floor | 40 | 34 | 14 | 75-95 | 3-4 | Armored sentry at the inner gates |
| 3 | Dark Inquisitor | Dungeon Floor | 44 | 38 | 22 | 90-110 | 4-5 | Torturer who wields forbidden magic |
| 4 | Chaos Enforcer | Dungeon Floor | 48 | 42 | 26 | 110-140 | 4-5 | Twisted knight reshaped by dark power |
| 5 | Doom Herald | Dungeon Floor | 50 | 44 | 30 | 140-170 | 4-5 | Messenger of the fortress master's will |

#### The Ancient Catacombs

| Floor | Monster | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Description |
|---|---|---|---|---|---|---|---|---|
| 1 | Bone Servant | Dungeon Floor | 38 | 32 | 10 | 70-90 | 3-4 | Skeleton labourer still obeying old orders |
| 2 | Wailing Spirit | Dungeon Floor | 42 | 36 | 20 | 80-100 | 3-4 | Echo of a soul that refuses to rest |
| 3 | Crypt Revenant | Dungeon Floor | 46 | 40 | 26 | 95-120 | 4-5 | Revenant knight hunting the living |
| 4 | Catacomb Oracle | Dungeon Floor | 50 | 44 | 32 | 120-150 | 4-5 | Undead seer who reads death itself |
| 5 | Death Knight | Dungeon Floor | 55 | 48 | 36 | 150-190 | 4-5 | Fallen paladin who bars the inner sanctum |

### Dungeon Monsters

Dungeon monsters are specifically assigned to each dungeon such that they are specially set and can be learnt by the player. Dungeon monsters are always stronger than the regular monsters of the same leg and have a higher chance of dropping loot. Their stats are listed in the Monster Lookup Table under the Dungeon Boss type.

Dungeon Monsters only occur in dungeons, never in the wild on a leg.

### Dungeons by Leg

- **Startersville to Forest Edge**
  - The Goblin's Den — boss: Goblin King
  - The Bandit's Hideout — boss: Bandit Lord
- **Forest Edge to Mountain Pass**
  - The Spider's Lair — boss: Giant Spider
  - The Bandit's Camp — boss: Bandit Chief
- **Mountain Pass to Desert Crossing**
  - The Sultans Tomb — boss: Mummy
  - The Ancient Ruins — boss: Lich
- **Desert Crossing to Riverlands**
  - The Vampire's Castle — boss: Vampire Lord
  - The Dragon's Lair — boss: Ancient Dragon
- **Riverlands to Capital**
  - The Dark Fortress — boss: Dark Knight
  - The Ancient Catacombs — boss: Lich King

## Loot

During the journey the hero will find loot, and will be able to take loot after an event.  The loot will be based on the event and will be a random selection from a pool of loot that is appropriate for the event.  The loot will either be cash, equipment, or a special relic, or a mix of the three.  The loot will add to the users skill in an appropriate way, have a value, and weight.  The value is used in buying and selling at the legs of the game.  Buying is 120% of the value and selling is 80% of the value.  The weight is used to determine how much the hero can carry, and if they are overburdened, they will be penalized in their skills.  The hero's max carry weight is based on their fighting + defending + salvaging skills, and if they are overburdened, they will be penalized in their skills by 10% for every 10 weight units over the limit.

Medical items can be used directly from inventory.  On use, they heal for:
- `camping skill + random(0..camping skill)`
and consume one use.

At the end of the journey, the items are sold for 100% of their value and the cash is added to be used to buy a home in the Capital or added to their pension.

Some special loot has an effect on the outcome of events, such as a pendant that prevents death once, or a ring that allows to re-roll the received loot when an event awards loot.  The special loot will be described in the event and will have a limited number of uses.  Getting the loot will be a noted event and the player will be told that the loot is the result of success before they are given the option to take it.

Loot is tiered to the leg:

- Leg 1: Common only
- Leg 2: Common and Uncommon
- Leg 3: Common, Uncommon, and Rare
- Leg 4: Uncommon, Rare, and Epic
- Leg 5: Rare and Epic

Item drop volume is intentionally reduced across the board:
- Most leg-1 regular monsters drop 0 items.
- Non-boss monsters can drop no equipment even on a win.
- Boss/super encounters still drop fewer items than before, but remain the most reliable equipment source.

## Scoring

The following houses are available to purchase in the Capital:
- Cottage - 1000 gold (1x pension)
- Villa - 5000 gold (5x pension)
- Castle - 10000 gold (10x pension)
- Mansion - 20000 gold (20x pension)
- Palace - 50000 gold (50x pension)

The following thresholds are used to determine the pension:
- 0 - 999 gold - 100 gold yearly pension
- 1000 - 4999 gold - 500 gold yearly pension
- 5000 - 9999 gold - 1000 gold yearly pension
- 10000 - 19999 gold - 2000 gold yearly pension
- 20000 - 49999 gold - 5000 gold yearly pension

The score is described as the players name, house name and the pension band, with a points amount of the house value multiplied by the pension value.  If the hero does not buy a home, they end up in a tavern, the score is based only on the pension.

## Playing the Game

The game is a UI game made out of menus and buttons.  The ui is described as pages with controls, subpages may exist and will have an entry point and exit point which is another page.  The pages are described as follows:
- Character Creation - The player creates their character by selecting a class and setting their skill level, name, and class.
- Journey - The player progresses through the journey and can continue to the next event, open inventory, open the character sheet, or save the game. It shows current HP, cash, leg, events completed, and key effective stats.
- Dungeon - Like the journey but shows the progress through the dungeon with an option to pause or exit the dungeon. On every dungeon floor—including right before facing the Dungeon Boss—the player can inspect the monster they are about to fight and has an explicit "Exit Dungeon" button to leave the dungeon safely at any time before initiating combat, returning to the journey.  It's entry is from a "dungeon found" event in the journey and its exit is the journey where we left off.
- Capital - The player can buy a home and retire if they have enough fortune (cash).  There are options for each house, and the calculated score so you can choose the best option.  If you do not have enough fortune to buy a home, you can only choose tavern.  There is a button to end the adventure which secures the choice and takes to the end game.
- Event - There are the following major event types:
  - Magic event - Magic traps have been removed from the journey. Magic events now grant magical shrines that allow players to rest or roll for magic loot without taking damage. Players can only lose HP in combat fights.
  - Fight - The player is attacked by a monster and must fight it.  The outcome is a contested dice roll based on the fighting/defending skills of both the player and monster - a stat edge tilts the odds heavily but never guarantees the result.  Success results in the loot window (with a chance of a Critical win for bonus loot), failure results in a loss window with HP loss.
  - Dungeon Found - The player finds a dungeon and can choose to enter or ignore it.  If they enter, they go to the dungeon page, if they ignore it, they continue the journey.
  - Loot found - Shows the loot found window for random loot that is appropriate for the leg of the journey.
  - Friendly Encounter - The player meets a friendly NPC and can choose to talk or ignore them.  If they talk, they may be offered an item in trade, a chance to rest, or a guaranteed dungeon entrance (if they have some tries left), if they ignore them, they continue the journey.
  - Wandering Trader - The player meets a wandering trader and can choose to trade or ignore them.  If they trade, they can buy or sell items, if they ignore them, they continue the journey.  The player can sell items for 60% of their Value.  The trader will offer 5 items from the general loot table for the leg of the journey and the player can buy them for 140% of their value.  The player can only buy items if they have enough cash.
  - Wander Group - The player encounters a traveling group that helps move them forward safely. This event advances journey progress by 5 additional events on the current leg. It does not grant direct loot or combat, and it follows a 3-event self-cooldown.
  - Fairy Found - The player may find and capture a fairy. The fairy can be equipped in the camping/medical slot. If the equipped fairy would otherwise die in combat, it is consumed: the player is restored to full HP, moved back 5 journey events on the current leg, and loses up to 1000 cash (or all cash if below 1000).
  - Super monster - The player spots a super monster with a relic and can choose to fight or ignore it.  If they fight, they go to the fight event, if they ignore it, they continue the journey without taking damage or fighting.  If they win, they get a loot relic and 10000 Cash, if they lose, they get a loss window with a punishing loss of health.
  - Tavern - The player finds a tavern and can choose to rest or continue the journey.  If they rest, they gain a lot of their health back at the cost of 100 cash.  If they continue, they get no other benefit.  The amount of health is based on a random roll of 40 + random(0-20).  If the player has a healing item equipped, the healing item may be consumed and the amount of health gained will be doubled, the player will be informed of the amount healed before asking if they want to double it.  No skills are used when staying in a tavern.
  - Camping spot - The player finds a camping spot and can choose to rest or continue the journey.  If they rest, they gain some of their health back based on their camping score * 1.  This can be * 2 if they have a healing item equipped, the healing item will be consumed if they take this option.  If they continue, they get no other benefit.
- Fight screen - The fight screen shows enemy stats, player HP, a fight profile (attack, effective defense, per-round damage in/out), estimated rounds to win, estimated rounds before death, and risk bands for each action. The action buttons include success percentages in the label for Fight, Sneak, Steal, and Stealth Kill.
- Inventory - The player can view inventory and carry weight, inspect items, equip/unequip items, drop items, use medical items, and save the game.
- Character Sheet - The player can view all skills as Base vs Effective values and see equipped items by slot with each item's bonus/effect.
- Loss window - The loss window shows the player that they have lost the event and the reason for the loss, it shows an amount of hit points lost.  It also has an Ok button which takes us back to the journey page, if we were in a dungeon it says that "The hero left the dungeon."
- Loot Found - A loot window that shows the items found and the cash amount.  The player can choose to take the loot or leave it.  If they take it, it is added to their inventory and the weight is calculated.  If they leave it, they continue the journey/dungeon.
- Death window - The death window shows the player that they have died and the reason for the death.  It also has an Ok button which takes us to the end game page.  You get no entry to the score board if you die.
- End game - The end game tells a short story of the hero's life in the capital.  It says "The hero, [name], has retired to a [house] with a pension of [pension] and lived a [short/medium/long] life before dying to [death reason]."  It also has an Ok button which takes us to the score board.  The death reason is chosen from a random list I will write.  The short medium and long life is based on the pension, with a short life is based on how high the value is within the pension band.  < half way through the pension band is short, and the top 3/4 of the pension band is medium with long being an option if in the top 1/4 of the band.  The death reason is based on a random selection from a list of reasons I will write.
- Score board - The top 5 scores and an button to go to the front page
- Trade window -  option to sell, which shows only the players items, and an option to buy which shows only the traders items.  Cash and player stats are updated when any transaction occurs.
- Front page - The front page has Start New Game, Load Game, score board, rules, credits, and quit options.
- Rules - The rules page has a button to go back to the front page.  It also has a button to view the character creation rules, and a button to view the journey rules, and a button to view the scoring rules.  It has buttons for the sub sections of the rules, but each of those only returns to the rules page.  The character creation rules describe how to create a character, the journey rules describe how the journey works, and the scoring rules describe how the scoring works.
- Credits - The credits page has a button to go back to the front page.  It also has a list of the people who worked on the game and their roles.

## Journey

The jouney is made up of 5 legs of 20 events.

The player will have a chance to find a dungeon twice in each leg (see Dungeons).

The 5 legs are:
- Startersville to Forest Edge
    This is a low level leg of the journey, with low level monsters and events.  The loot is also low level and the player will not be able to buy a home at the end of this leg.  The super monster is an angry deer with a relic.  Fights are the dominant event; camping and tavern events are blocked in the first half of the leg and, when available later, still follow the 3-event rest cooldown.
- Forest Edge to Mountain Pass
    This is a mid level leg of the journey, with mid level monsters and events.  The loot is also mid level and the player may be able to buy a home at the end of this leg.  The super monster is a giant bear with a relic.
- Mountain Pass to Desert Crossing
    This is a high level leg of the journey, with high level monsters and events.  The loot is also high level and the player may be able to buy a home at the end of this leg.  The super monster is a wyvern with a relic.
- Desert Crossing to Riverlands
    This is a very high level leg of the journey, with very high level monsters and events.  The loot is also very high level and the player may be able to buy a home at the end of this leg.  The super monster is a chimera with a relic.
- Riverlands to Capital
    This is the final leg of the journey, with the toughest monsters and events.  The loot is the best and the player will be able to buy a home at the end of this leg.  The super monster is a dragon with a relic.

## Monsters

Monsters have no class, but have skills and loot. The skills are used to determine the outcome of the fight event. The loot is used to determine what the player can take after a successful fight. Monsters don't have salvaging, spotting, camping, or medical skills. Monsters only show up in specific legs of the journey matching their theme and level.

Monster stat tuning is now baseline-driven at three checkpoints per leg:
- **Leg Start baseline** (event 0)
- **Mid-Leg baseline** (event 10)
- **Leg End baseline** (event 20)

For each leg, we compute an average player combat profile from these checkpoints and set monster bands from that profile:
- **Weak monsters** target roughly **110% of the Leg Start average combat power**
- **Strong monsters** target roughly **110% of the Leg End average combat power**
- Mid-tier monsters are distributed between those two targets

This keeps each leg challenging even when players are not at top gear, while preserving progression.

Each leg now also includes extra regular monsters that lean more strongly into stealth or magic themes, so bandit-heavy roads feel more slippery and later legs lean harder into spellcasters and shadowy attackers.

Weak monsters always have 1-2 equipment, and strong monsters always have 2-3 equipment. The super monsters always have a relic and 1-2 equipment.

Super Monsters are a special event and should only occur once per leg.

Monsters have no HP, they are either defeated or not.

Dungeon monster rules and assignments are described in the Dungeons section.

### Monster Lookup Table

The table below is a thematic lookup (monster roster, loot bands, and progression intent). Final fighting/defending values are scaled at runtime by the baseline model above to keep encounter difficulty aligned to player progression within each leg.

| Leg | Monster Name | Type | Fighting | Defending | Magic | Cash Loot | Equipment | Relic Chance | Theme / Description | Super Monster |
|---|---|---|---|---|---|---|---|---|---|
| **Leg 1** | Giant Rat | Regular | 9 | 5 | 0 | 5-15 | 1-2 | 0% | Startersville sewers & cellar pest |
| **Leg 1** | Rabid Bat | Regular | 10 | 5 | 0 | 5-15 | 1-2 | 0% | Forest canopy pest |
| **Leg 1** | Goblin | Regular | 11 | 6 | 0 | 10-20 | 1-2 | 0% | Forest trail ambush predator |
| **Leg 1** | Wild Wolf | Regular | 12 | 7 | 0 | 10-20 | 1-2 | 0% | Woodland pack hunter |
| **Leg 1** | Forest Kobold | Regular | 13 | 7 | 0 | 10-25 | 1-2 | 0% | Woodland thief |
| **Leg 1** | Forest Spider | Regular | 14 | 8 | 0 | 15-25 | 1-2 | 0% | Lowland web weaver |
| **Leg 1** | Bandit | Regular | 17 | 11 | 0 | 20-30 | 2-3 | 0% | Highway highwayman |
| **Leg 1** | Angry Deer | Super Monster | 20 | 13 | 0 | 100 | 1-2 | 100% | Enraged woodland spirit |
| **Leg 1** | Goblin King | Dungeon Boss | 22 | 13 | 6 | 50-100 | 2-3 | 100% | Ruler of Goblin's Den |
| **Leg 1** | Bandit Lord | Dungeon Boss | 24 | 17 | 0 | 60-120 | 2-3 | 100% | Leader of Bandit's Hideout |
| **Leg 2** | Cave Goblin | Regular | 20 | 15 | 0 | 25-35 | 2-3 | 0% | Subterranean mountain dweller |
| **Leg 2** | Giant Spider | Regular | 21 | 16 | 0 | 30-40 | 3-4 | 0% | Foothill cavern weaver |
| **Leg 2** | Timber Wolf | Regular | 23 | 17 | 0 | 30-45 | 2-3 | 0% | Mountain pass pack hunter |
| **Leg 2** | Harpy | Regular | 25 | 18 | 4 | 35-50 | 2-3 | 0% | Cliffside winged terror |
| **Leg 2** | Rock Elemental | Regular | 27 | 22 | 0 | 40-60 | 2-3 | 0% | Living stone guardian |
| **Leg 2** | Mountain Ogre | Regular | 28 | 20 | 0 | 40-60 | 3-4 | 0% | High-pass brute |
| **Leg 2** | Giant Bear | Super Monster | 29 | 21 | 0 | 1000 | 1-2 | 100% | Apex forest/mountain beast |
| **Leg 2** | Bandit Chief | Dungeon Boss | 32 | 23 | 0 | 80-150 | 2-3 | 100% | Leader of Bandit's Camp |
| **Leg 3** | Dust Elemental | Regular | 30 | 24 | 10 | 35-45 | 3-4 | 0% | Desert storm incarnation |
| **Leg 3** | Tomb Skeleton | Regular | 32 | 25 | 0 | 40-50 | 3-4 | 0% | Undead ancient tomb guard |
| **Leg 3** | Giant Scorpion | Regular | 33 | 26 | 0 | 40-50 | 3-4 | 0% | Desert dune stalker |
| **Leg 3** | Tomb Raider | Regular | 34 | 26 | 0 | 45-60 | 3-4 | 0% | Hostile desert scavenger |
| **Leg 3** | Sand Serpent | Regular | 35 | 27 | 0 | 45-60 | 3-4 | 0% | Burrowing desert monster |
| **Leg 3** | Mummy | Regular | 31 | 24 | 8 | 40-50 | 4-5 | 0% | Preserved ancient ruler |
| **Leg 3** | Wyvern | Super Monster | 38 | 28 | 12 | 1000 | 1-2 | 100% | Desert canyon dragon-kin |
| **Leg 3** | Lich | Dungeon Boss | 48 | 44 | 32 | 80-90 | 2-3 | 100% | Master of Sultan's Tomb / Ancient Ruins |
| **Leg 4** | River Siren | Regular | 36 | 30 | 16 | 50-65 | 4-5 | 0% | Luring riverlands enchantress |
| **Leg 4** | Corpse Creeper | Regular | 37 | 29 | 4 | 50-65 | 4-5 | 0% | Swamp undead scavenger |
| **Leg 4** | Swamp Hydra | Regular | 38 | 32 | 10 | 55-70 | 4-5 | 0% | Multi-headed riverlands terror |
| **Leg 4** | Shadow Gargoyle | Regular | 39 | 35 | 8 | 55-70 | 5-6 | 0% | Castle rooftop stalker |
| **Leg 4** | Vampire | Regular | 40 | 32 | 16 | 50-60 | 5-6 | 0% | Bloodthirsty castle noble |
| **Leg 4** | Werewolf | Regular | 41 | 34 | 0 | 60-75 | 4-5 | 0% | Savage moonlit beast |
| **Leg 4** | Chimera | Super Monster | 40 | 36 | 24 | 5000 | 7-8 | 100% | Mythical multi-beast abomination |
| **Leg 4** | Vampire Lord | Dungeon Boss | 36 | 28 | 20 | 120-200 | 2-3 | 100% | Ruler of Vampire's Castle |
| **Leg 4** | Ancient Dragon | Dungeon Boss | 44 | 36 | 24 | 200-300 | 2-3 | 100% | Ruler of Dragon's Lair |
| **Leg 5** | Dread Warlock | Regular | 45 | 38 | 30 | 60-80 | 5-6 | 0% | Dark fortress spellcaster |
| **Leg 5** | Catacomb Wraith | Regular | 46 | 42 | 24 | 65-85 | 5-6 | 0% | Incorporeal catacomb terror |
| **Leg 5** | Infernal Fiend | Regular | 48 | 40 | 18 | 70-90 | 5-6 | 0% | Demon of the abyssal gates |
| **Leg 5** | Chaos Knight | Regular | 49 | 43 | 12 | 75-95 | 6-7 | 0% | Corrupted capital champion |
| **Leg 5** | Abyss Golem | Regular | 50 | 45 | 10 | 80-100 | 6-7 | 0% | Massive dark fortress construct |
| **Leg 5** | Dragon | Regular | 51 | 44 | 25 | 60-70 | 6-7 | 0% | Apex Capital approach terror |
| **Leg 5** | Dark Knight | Dungeon Boss | 52 | 44 | 12 | 250-400 | 2-3 | 100% | Master of Dark Fortress |
| **Leg 5** | Lich King | Dungeon Boss | 60 | 52 | 40 | 300-500 | 2-3 | 100% | Master of Ancient Catacombs |

## Fighting

All combat actions use contested rolls with a 1-20 random swing, but straight Fight is now resolved as a multi-round battle.

For Fight:
- Player attack uses `max(fighting, magic)`.
- If `magic > fighting`, a Magical Ward is added to defense (`+50% magic`, or `+100%` with Amulet of Arcane Shielding).
- Crown of the Archmage can raise effective defense up to magic.
- Monster HP is derived from monster stats, and combat runs round-by-round (capped to keep fights bounded).
- On a won round, monster HP is reduced by player round damage.
- On a lost round, player HP is reduced by monster round damage (Behemoth Shield halves this).
- If the player wins any round by a large margin, a Critical flag can apply bonus cash to the final victory loot.

Alternative actions:
- Sneak: contested `stealth` vs monster `defending`; failure falls through into Fight. Boots of Stealth can rescue failed sneaks.
- Steal: contested `(stealth + salvaging)` vs `(monster defending * 2)`; success grants loot directly, failure falls through into Fight.
- Stealth Kill: contested `(stealth * 2)` vs `(monster defending * 1.5)`; success grants loot directly, failure falls through into Fight.

Relics can materially change outcomes (guaranteed win combos, rerolls, one-time loss flip, damage mitigation, and class synergies), and are applied in the engine at fight resolution time.

## Loot table

There is a loot table for each leg of the journey and each dungeon.

Loot takes the form of fighting weapons, defending armor, magic items, stealth items, salvaging tools, spotting items, camping gear, and medical supplies. Each item has a value and weight associated with it and will change the associated skill by a certain amount.

Combat-skill gear is class-specific:
- **Hitter** is the only class that gains combat attack scaling from **fighting** gear
- **Blaster** is the only class that gains combat attack scaling from **magic** gear
- **Hider** is the only class that gains combat attack scaling from **stealth** gear

Utility gear (salvaging, spotting, camping, medical, accessories) remains available to all classes.

Equiped items have no weight.

The loot table is made up of the following items for each leg of the journey and each dungeon:

- Fighting weapons: sword, axe, mace, spear - 10 weight
- Defending armor: leather armor, chainmail, shield - 10 weight
- Magic items: wand, staff, spellbook - 3 weight
- Accessories: ring, amulet, bracelet, lockpicks, survival knife, anything weird and wonderful we can think of - 1 weight
- Stealth items: cloak, boots, sneak suit - 5 weight
- Salvaging tools: crowbar, hammer, saw - 5 weight
- Spotting items: binoculars, telescope, magnifying glass - 5 weight
- Camping gear: tent, sleeping bag, campfire kit - 5 weight
- Medical supplies: bandages, potions, herbs - 5 weight

Medical items have a use count based on their quality, with common having 1 use, uncommon having 2 uses, rare having 3 uses, and epic having 5 uses.  The use count is displayed in the inventory and is decremented when used.  When the use count reaches 0, the item is removed from the inventory.  The value is a ratio of the un-used count to the total count, so a common with 1 use left is worth 100% of its value, an uncommon with 1 use left is worth 50% of its value, and an epic with 2 uses left is worth 40% of its value.

Medical items can be used directly from inventory. Healing scales with camping skill plus a random component, and item uses are consumed.

Each item has a colour and a quality associated with it. The quality of the item will determine how much it will change the associated skill. The colours are:
- Common - white
- Uncommon - green
- Rare - blue
- Epic - purple

Equipment items receive stat boosts across quality tiers:
- Fighting weapons and Stealth items receive a +10 bonus to their skill boost across all quality tiers.
- Defending armor items receive a +20 bonus to their skill boost across all quality tiers.
- Common: Fighting/Stealth add 15-20 (Defending armor adds 25-30)
- Uncommon: Fighting/Stealth add 25-35 (Defending armor adds 35-45)
- Rare: Fighting/Stealth add 40-50 (Defending armor adds 50-60)
- Epic: Fighting/Stealth add 60-70 (Defending armor adds 70-80)
This is rolled at random within these bands.

### Town Transport Travel
Players can choose to hire transport to travel back to the last town/tavern to rest and recover HP. The cost scales by leg:
- Leg 1: 100 cash
- Leg 2: 150 cash
- Leg 3: 200 cash
- Leg 4: 250 cash
- Leg 5: 300 cash
Players can only use Town Transport if they have enough cash.

Commons are worth 10-50 cash, uncommons are worth 100-500 cash, rares are worth 1000-5000 cash, and epics are worth 10000-50000 cash.  The final value is based on the assocuiated skill amount that was rolled, a higher skill amount will result in a higher value with the maximum skill amount resulting in the maximum value.

Relics are always epic and have a special effect that is taken into account in certain events.

Relic acquisition is class-balanced:
- Each class has a class-specific relic pool with the **same number of relics**
- Relic pools are aligned to class identity (Hitter combat relics, Blaster magic relics, Hider stealth/utility relics)
- Neutral/non-stat relic effects are distributed to preserve parity rather than concentrating power in one class

The relics are:

- Pendant of Life - Accessory - prevents death once
- Ring of Fortune - Accessory - allows to re-roll the received loot when an event awards loot
- Sword of Power - Fighting Weapon - adds 50 to fighting and gives a chance to re-roll the fight outcome if the player loses
- Plate of Invincibility - Defending Armor - adds 50 to defending and gives a chance to re-roll the fight outcome if the player loses, in addition to the sword of power, if both are equipped, the player will always win the fight
- Staff of Magic - Fighting Weapon - adds 50 to magic and gives a chance to re-roll the outcome of a magic event if the player fails
- Boots of Stealth - Defending Armor - adds 50 to stealth and gives a chance to re-roll the outcome of a stealth event if the player fails
- Eyeglass of the Master Pirate - Spotting Item - adds 50 to spotting and always find a dungeon on the 7th and 14th events, if they have the dungeons left to discover, it can't find a dungeon if they have already found the two dungeons for that leg of the journey.
- Bandage of the tireless healer - Camping / Medical Item - adds 50 to medical and is never consumed when used.
- Cloak of Invisibility - Defending Armor - adds 50 to stealth and allows the player to avoid any combat encounters, and always succeeds in stealth events.
- Pharaoh's Ankh of Rebirth - Accessory - adds 50 to medical and restores 50% HP immediately after surviving any boss or super-monster battle.
- Alchemist's Philosopher Stone - Salvaging Tool - adds 50 to salvaging and changes all trades (including wandering traders) to 90% sell value and 110% buy cost.
- Crown of the Archmage - Fighting Weapon - adds 50 to magic and allows Magic skill to replace Defending in combat damage reduction.
- Shadowstep Dagger - Fighting Weapon - adds 50 to stealth and guarantees success on Stealth Kill actions.
- Golden Horn of Plenty - Camping / Medical Item - adds 50 to camping and makes resting at Camping Spots cost 0 medical supplies while restoring HP to 100%.
- Mirror of Fate - Spotting Item - adds 50 to spotting and flips a fight loss outcome to an instant win once per game.
- Aegis Arm Guards - Accessory - adds 50 to defending, allowing non-Hitter classes to boost physical defense via accessory slot.
- Dragon Scale Gauntlets - Accessory - adds 50 to fighting, boosting attack power in the accessory slot.
- Ring of Arcane Power - Accessory - adds 50 to magic, boosting spellcasting power in the accessory slot.
- Slippers of the Wind - Accessory - adds 50 to stealth, boosting evasion in the accessory slot.
- Scavenger's Iron Claw - Salvaging Tool - adds 50 to salvaging and grants 25% extra cash on every event loot roll.
- Eagle Eye Monocle - Spotting Item - adds 50 to spotting and reveals wandering trader inventory prices at 100% true value.
- Wand of the Void - Fighting Weapon - adds 50 to magic and grants 100% win rate on all Magic Trap events.
- Behemoth Shield - Defending Armor - adds 50 to defending and reduces monster hit damage by 50% in failed fight turns.
- Elixir of Immortality - Camping / Medical Item - adds 50 to medical and automatically cures all injury penalties after dungeon failures.
- Robe of the Archmage - Defending Armor - adds 50 to magic, boosting Blaster spellcasting and Magical Ward defense in the armor slot.
- Orb of Sorcery - Salvaging Tool - adds 50 to magic, granting Magic skill scaling in the salvaging tool slot.
- Crystal Ball of Prescience - Spotting Item - adds 50 to magic, granting Magic skill scaling in the spotting item slot.
- Tome of Ancient Runes - Camping / Medical Item - adds 50 to magic, granting Magic skill scaling in the camping/medical slot.
- Amulet of Arcane Shielding - Accessory - adds 50 to magic and increases Magical Ward defense bonus from 50% to 100% of Magic skill.

### Relic Synergies
- **Warrior's Supremacy (Hitter 2-Relic Synergy):** Equipping both `Sword of Power` and `Plate of Invincibility` guarantees 100% win rate in physical combat fights.
- **Arcane Tempest (Blaster 2-Relic Synergy):** Equipping both `Staff of Magic` and `Crown of the Archmage` converts all magic trap events into immediate loot and grants complete immunity to spell damage (reducing monster magic damage to 0).
- **Grand Archmage Synergy (Blaster 3-Relic Synergy):** Equipping `Staff of Magic`, `Crown of the Archmage`, and `Pharaoh's Ankh of Rebirth` grants complete spell immunity, 100% win rate on Magic Events, and fully restores HP to 100% after every boss battle.
- **Shadow Assassin (Hider 2-Relic Synergy):** Equipping both `Shadowstep Dagger` and `Cloak of Invisibility` guarantees 100% success on all Stealth Kills and Stealth Evasions, granting full monster loot without taking damage.
- **Master Thief Synergy (Hider 3-Relic Synergy):** Equipping `Shadowstep Dagger`, `Cloak of Invisibility`, and `Alchemist's Philosopher Stone` guarantees 100% Stealth Kills, grants double cash from all monster loot, and applies 100% sell value / 100% buy cost at traders.

Relics are unique and can only be found once in the game.  There are set relics of bosses of dungeons and Super monsters, and there are random relics that can be found in the loot table.  These can spawn on very strong monsters but only have a 5% chance of spawning.  A relic is unique to its spawn, so once spawned, it will not spawn again in the game, regardless of the outcome of the relic, sold/used/equipped, or dropped/ignored.

Relics found are noted in a gallery of relics that can be viewed from the main page, as a sort of trophy case.  The gallery will only show relics found.

## Equipment

Each character can have 1 fighting weapon or magic item, 1 defending armor or 1 stealth item, 1 salvaging tool, 1 spotting item, 1 camping gear or 1 medical item equipped at a time. The player can equip two accessories.

Class-specific combat scaling rules apply to equipment:
- **Hitter:** only fighting gear contributes to primary attack scaling
- **Blaster:** only magic gear contributes to primary attack scaling
- **Hider:** only stealth gear contributes to primary attack scaling

The player can change equipped items at any time during the journey or in the inventory page, but not during events.  The player can also have items in their inventory that are not equipped, but they will not add to the associated skill and will not be used in the events.  The equip sections are drop downs based on the items held in the inventory.  The player can choose to equip an item from the drop down and it will be equipped, or they can choose to unequip an item and it will be unequipped.  The player can also choose to drop an item from the inventory and it will be removed, the plays attributes are calculated every time the inventory is altered.  Items equipped have a * in front of their name to help identify what is equipped.  Inorder to not only rely on colour items have (c), (u), (r), (e) after their name to help identify the quality of the item.
