# Hero Adventure

A short game with a point score at the end following a hero's adventure to glory or death.

## Character

The hero is the player character and we create them by picking a class and setting their attributes.

The classes are Hitter, Blaster, and Hider.  These classes set the skills and capabilities of the player character.  The choice of a class gives and initial boost to three of ten skills.

The hero always has a max HP of 100 and starts with 100 HP.  The hero can lose HP during events and if they reach 0 HP, they die and the game ends.  The hero can regain HP by resting at a tavern or camping spot, or by using medical supplies.

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

The Hero is on a journey across the country to find fortune and will end in the Capital. If the hero has accumulated enough fortune (gold/cash), they will be able to buy a home and retire. If not, they will work in a tavern and live a life of obscurity. The end of the journey represents the end of the game character and the score is based on the life they ended up with. There are a selection of houses that can be purchased and the resulting cash is given up as a pension - the score is the two multiplied together. If the hero ends up in a tavern, the score is based only on the pension.

The journey is made up of 5 legs of 20 events.  An event occurs every 10 seconds, unless the user has paused the game to adjust something.  The events are randomly selected from a pool of events that are appropriate for the leg of the journey.  The events will have a function that calculates the two outcomes of success or failure, these are described in the event.  There is a chance, twice per leg to find a dungeon, this is based on the spotting skill.  The dungeon is a series of 10 second events that will have a final boss at the end.  If the hero defeats the boss, they will be able to take the treasure and gain fortune.  If they fail, they will be injured and returned to the front door to continue the journey.  The dungeon is a series of 10 events that are randomly selected from a pool of events that are appropriate for the dungeon.  The events will have a function that calculates the two outcomes of success or failure, these are described in the event.

Each event has a chance to spot a dungeon entrance, this is based on a roll of 0 - 100 where the players spotting skill being equal or greater than the roll will result in a dungeon being found. There are exactly two dungeons per leg of the journey; once the player has successfully spotted both dungeons in a leg, no more dungeons can be found for the remainder of that leg. The player can choose to enter the dungeon or ignore it and continue the journey.  If they enter, they will go to the dungeon page, if they ignore it, they will continue the journey.

A player levels at the end of a leg of the journey, and can choose to increase three of their skills by 5 points.  The player can only level up at the end of the leg of the journey.

## Loot

During the journey the hero will find loot, and will be able to take loot after an event.  The loot will be based on the event and will be a random selection from a pool of loot that is appropriate for the event.  The loot will either be cash, equipment, or a special relic, or a mix of the three.  The loot will add to the users skill in an appropriate way, have a value, and weight.  The value is used in buying and selling at the legs of the game.  Buying is 120% of the value and selling is 80% of the value.  The weight is used to determine how much the hero can carry, and if they are overburdened, they will be penalized in their skills.  The hero's max carry weight is based on their fighting + defending + salvaging skills, and if they are overburdened, they will be penalized in their skills by 10% for every 10 weight units over the limit.

At the end of the journey, the items are sold for 100% of their value and the cash is added to be used to buy a home in the Capital or added to their pension.

Some special loot has an effect on the outcome of events, such as a pendant that prevents death once, or a ring that allows to re-roll the received loot when an event awards loot.  The special loot will be described in the event and will have a limited number of uses.  Getting the loot will be a noted event and the player will be told that the loot is the result of success before they are given the option to take it.

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
- Journey - The player progresses through the journey showing their progress, a pause button to pause and look at their inventory, and a button to continue the journey.  It shows how long till the next event, and the current gold/cash of the player.  It also shows the current leg of the journey and the number of events completed.
- Dungeon - Like the journey but shows the progress through the dungeon with an option to pause or exit the dungeon.  It's entry is from a "dungeon found" event in the journey and its exit is the journey where we left off.
- Capital - The player can buy a home and retire if they have enough fortune (cash).  There are options for each house, and the calculated score so you can choose the best option.  If you do not have enough fortune to buy a home, you can only choose tavern.  There is a button to end the adventure which secures the choice and takes to the end game.
- Event - There are the following major event types:
  - Magic event - The player has found themselves in a magic trap with a name from the magic traps list. The outcome is based on the players magic skill (roll 0-100 vs magic). Non-magical characters can attempt to escape using the highest of their fighting, defending, or stealth skills (roll 0-100 vs highest of fighting, defending, stealth). Success results in the loot window, failure results in a loss window.
  - Fight - The player is attacked by a monster and must fight it.  The outcome is based on the fighting and defending skills or both the player and monster.  Success results in the loot window, failure results in a loss window.
  - Dungeon Found - The player finds a dungeon and can choose to enter or ignore it.  If they enter, they go to the dungeon page, if they ignore it, they continue the journey.
  - Loot found - Shows the loot found window for random loot that is appropriate for the leg of the journey.
  - Friendly Encounter - The player meets a friendly NPC and can choose to talk or ignore them.  If they talk, they may be offered an item in trade, a chance to rest, or a guaranteed dungeon entrance (if they have some tries left), if they ignore them, they continue the journey.
  - Wandering Trader - The player meets a wandering trader and can choose to trade or ignore them.  If they trade, they can buy or sell items, if they ignore them, they continue the journey.  The player can sell items for 60% of their Value.  The trader will offer 5 items from the general loot table for the leg of the journey and the player can buy them for 140% of their value.  The player can only buy items if they have enough cash.
  - Super monster - The player spots a super monster with a relic and can choose to fight or ignore it.  If they fight, they go to the fight event, if they ignore it, they continue the journey.  If they win, they get a loot relic and 10000 Cash, if they lose, they get a loss window with a punishing loss of health.
  - Tavern - The player finds a tavern and can choose to rest or continue the journey.  If they rest, they gain a lot of their health back at the cost of 100 cash.  If they continue, they get no other benefit.  The amount of health is based on a random roll of 40 + random(0-20).  If the player has a healing item equipped, the healing item may be consumed and the amount of health gained will be doubled, the player will be informed of the amount healed before asking if they want to double it.  No skills are used when staying in a tavern.
  - Camping spot - The player finds a camping spot and can choose to rest or continue the journey.  If they rest, they gain some of their health back based on their camping score * 1.  This can be * 2 if they have a healing item equipped, the healing item will be consumed if they take this option.  If they continue, they get no other benefit.
- Fight screen - The fight screen shows the player the monster they are fighting and their skills, and the monsters skills.  It also has a button to fight, a button to sneak past, a button to steal their loot, and a button for a stealth kill. There may be an option to run away if the event grants it, or by a relic.  The outcome of the fight based on the players and monsters skills.  If the player wins, they go to the loot window, if they lose, they go to the loss window.  If they chose steal, it is based on their stealth and salvaging skills added together vs the monsters defending skill * 2.  If they win, they go to the loot window, if they lose, they go to the loss window.  If they chose sneak past, it is based on their stealth skill vs the monsters defending skill * 2.  If they win, they continue the journey, if they lose, they go to the loss window. If they chose stealth kill, it is based on the players stealth skill vs the monsters defending skill. If the players stealth is higher than the monsters defending, the player wins and gets loot, if it is lower, the player is caught and must fight.
- Inventory - The player can view their inventory and the weight of the items they are carrying.  They can choose to drop items to reduce their weight, or use items that have a use effect.  The inventory shows the items in a list with their name, value, weight, and use effect if any.
- Loss window - The loss window shows the player that they have lost the event and the reason for the loss, it shows an amount of hit points lost.  It also has an Ok button which takes us back to the journey page, if we were in a dungeon it says that "The hero left the dungeon."
- Loot Found - A loot window that shows the items found and the cash amount.  The player can choose to take the loot or leave it.  If they take it, it is added to their inventory and the weight is calculated.  If they leave it, they continue the journey/dungeon.
- Death window - The death window shows the player that they have died and the reason for the death.  It also has an Ok button which takes us to the end game page.  You get no entry to the score board if you die.
- End game - The end game tells a short story of the hero's life in the capital.  It says "The hero, [name], has retired to a [house] with a pension of [pension] and lived a [short/medium/long] life before dying to [death reason]."  It also has an Ok button which takes us to the score board.  The death reason is chosen from a random list I will write.  The short medium and long life is based on the pension, with a short life is based on how high the value is within the pension band.  < half way through the pension band is short, and the top 3/4 of the pension band is medium with long being an option if in the top 1/4 of the band.  The death reason is based on a random selection from a list of reasons I will write.
- Score board - The top 5 scores and an button to go to the front page
- Trade window -  option to sell, which shows only the players items, and an option to buy which shows only the traders items.  Cash and player stats are updated when any transaction occurs.
- Front page - The front page has a button to start a new game, and a button to view the score board.  It also has a button to view the rules of the game.
- Rules - The rules page has a button to go back to the front page.  It also has a button to view the character creation rules, and a button to view the journey rules, and a button to view the scoring rules.  It has buttons for the sub sections of the rules, but each of those only returns to the rules page.  The character creation rules describe how to create a character, the journey rules describe how the journey works, and the scoring rules describe how the scoring works.
- Credits - The credits page has a button to go back to the front page.  It also has a list of the people who worked on the game and their roles.

## Journey

The jouney is made up of 5 legs of 20 events.

The player will have a chance to find a dungeon twice in each leg.

The 5 legs are:
- Startersville to Forest Edge
    This is a low level leg of the journey, with low level monsters and events.  The loot is also low level and the player will not be able to buy a home at the end of this leg.  The super monster is an angry deer with a relic.  There is 20% chance of camping/taven events, with the remaining 80% being the other events.  The two dungeons are named "The Goblin's Den" and "The Bandit's Hideout" and have a super monster at the end of each dungeon.  The goblin's den has a goblin king with a relic, and the bandit's hideout has a bandit lord with a relic.
- Forest Edge to Mountain Pass
    This is a mid level leg of the journey, with mid level monsters and events.  The loot is also mid level and the player may be able to buy a home at the end of this leg.  The super monster is a giant bear with a relic.  The two dungeons are named "The Spider's Lair" and "The Bandit's Camp" and have a super monster at the end of each dungeon.  The spider's lair has a giant spider with a relic, and the bandit's camp has a bandit chief with a relic.
- Mountain Pass to Desert Crossing
    This is a high level leg of the journey, with high level monsters and events.  The loot is also high level and the player may be able to buy a home at the end of this leg.  The super monster is a wyvern with a relic.  The dungeons are named "The Sultans Tomb" and "The Ancient Ruins" and have a super monster at the end of each dungeon.  The sultans tomb has a mummy with a relic, and the ancient ruins has a lich with a relic.
- Desert Crossing to Riverlands
    This is a very high level leg of the journey, with very high level monsters and events.  The loot is also very high level and the player may be able to buy a home at the end of this leg.  The super monster is a chimera with a relic.  The dungeons are named "The Vampire's Castle" and "The Dragon's Lair" and have a super monster at the end of each dungeon.  The vampire's castle has a vampire lord with a relic, and the dragon's lair has an ancient dragon with a relic.
- Riverlands to Capital
    This is the final leg of the journey, with the toughest monsters and events.  The loot is the best and the player will be able to buy a home at the end of this leg.  The super monster is a dragon with a relic.  The dungeons are named "The Dark Fortress" and "The Ancient Catacombs" and have a super monster at the end of each dungeon.  The dark fortress has a dark knight with a relic, and the ancient catacombs has a lich king with a relic.

## Monsters

Monsters have no class, but have skills and loot.  The skills are used to determine the outcome of the fight event.  The loot is used to determine what the player can take after a successful fight.  Monsters don't have salvaging, spotting, camping, or medical skills.  Monsters only show up in specific legs of the journey and may show up on specific floors of the dungeons in that leg.

Weak monsters always have 1-2 equipment, and strong monsters always have 2-3 equipment.  The super monsters always have a relic and 1-2 equipment.

Monsters have no HP, they are either defeated or not.

There are the following monsters with their skills and loot:
- Goblin - fighting 11, defending 6, magic 0, Loot: cash 10-20, equipment 1-2, relic 0. (Leg 1, +10%)
- Bandit - fighting 17, defending 11, magic 0, Loot: cash 20-30, equipment 2-3, relic 0. (Leg 1, +10%)
- Angry Deer - fighting 20, defending 13, magic 0, Loot: cash 10000, equipment 1-2, relic 1. (Leg 1 Super Monster, +10%)
- Goblin King - fighting 22, defending 13, magic 6, Loot: cash 50-100, equipment 2-3, relic 1. (Leg 1 Boss, +10%)
- Bandit Lord - fighting 24, defending 17, magic 0, Loot: cash 60-120, equipment 2-3, relic 1. (Leg 1 Boss, +10%)

- Giant Spider - fighting 21, defending 16, magic 0, Loot: cash 30-40, equipment 3-4, relic 0. (Leg 2, +5%)
- Giant Bear - fighting 29, defending 21, magic 0, Loot: cash 10000, equipment 1-2, relic 1. (Leg 2 Super Monster, +5%)
- Bandit Chief - fighting 32, defending 23, magic 0, Loot: cash 80-150, equipment 2-3, relic 1. (Leg 2 Boss, +5%)

- Mummy - fighting 20, defending 16, magic 4, Loot: cash 40-50, equipment 4-5, relic 0. (Leg 3, -20%)
- Wyvern - fighting 30, defending 22, magic 8, Loot: cash 10000, equipment 1-2, relic 1. (Leg 3 Super Monster, -20%)
- Lich - fighting 48, defending 44, magic 32, Loot: cash 80-90, equipment 2-3, relic 0. (Leg 3 Boss, -20%)

- Vampire - fighting 24, defending 20, magic 8, Loot: cash 50-60, equipment 5-6, relic 0. (Leg 4, -20%)
- Vampire Lord - fighting 36, defending 28, magic 20, Loot: cash 120-200, equipment 2-3, relic 1. (Leg 4 Boss, -20%)
- Ancient Dragon - fighting 44, defending 36, magic 24, Loot: cash 200-300, equipment 2-3, relic 1. (Leg 4 Boss, -20%)
- Chimera - fighting 40, defending 36, magic 24, Loot: cash 10000, equipment 7-8, relic 1. (Leg 4 Super Monster, -20%)

- Dragon - fighting 32, defending 28, magic 16, Loot: cash 60-70, equipment 6-7, relic 0. (Leg 5, -20%)
- Dark Knight - fighting 52, defending 44, magic 12, Loot: cash 250-400, equipment 2-3, relic 1. (Leg 5 Boss, -20%)
- Lich King - fighting 60, defending 52, magic 40, Loot: cash 300-500, equipment 2-3, relic 1. (Leg 5 Boss, -20%)

## Fighting

A fight is between the monster and the player.  If a players magic skill is higher than their fighting skill, we always use the higher value.  We take the fighting of the player and match it against the defending monster.  If the fighting is higher than the defending, the player hits, if it is lower, the player did not hit.  The players defending, or magic, if higher is compared to the monsters fighting to see if monster makes a hit.  If the player hits, we compare the two hits and if the players hit is higher than the monsters hit, the player wins, if it is lower, the monster wins.  If they are equal, the player wins, relics may effect this.

The player can choose to sneak past the monster, steal from the monster, or execute a Stealth Kill.  Sneaking past is based on the players stealth vs the monsters defending.  If the players stealth is higher than the monsters defending, the player sneaks past, if it is lower, the player is caught and must fight.  Sneaking past never rewards loot, but never hurts the player either.  Relics may effect this.

The player can try to Steal from the monster. If the players stealth + salvaging is higher than the monsters defending * 2, the player steals from the monster, if it is lower, the player is caught and must fight.  Succesful stealing rewards the player with loot and never hurts the player.  Relics may effect this.

The player can attempt a Stealth Kill. To simulate the advantage of surprise, a Stealth Kill is calculated as (players stealth * 2) vs (monsters defending * 1.5). If (stealth * 2) is higher than (monsters defending * 1.5), the player instantly defeats the monster and gains full loot without taking damage. If it is lower, the player is caught and must fight. Relics may effect this.

On a defeat, the player loses hp based on the monsters hit.  Which is the diference between the monsters fighting and the players defending.  Relics may effect this.  The player never loses cash or items on a defeat.

Relics may cause a re-roll, or materially effect the outcome of any of these actions.  The relic itself will detail it's effect and how it is used.  The relics are described in the Relics section.

## Loot table

There is a loot table for each leg of the journey and each dungeon.

Loot takes the form of fighting weapons, defending armor, magic items, stealth items, salvaging tools, spotting items, camping gear, and medical supplies. Each item has a value and weight associated with it and will change the associated skill by a certain amount.

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

Medical items can only be used in resting events.

Each item has a colour and a quality associated with it. The quality of the item will determine how much it will change the associated skill. The colours are:
- Common - white
- Uncommon - green
- Rare - blue
- Epic - purple

Defending armor items receive a +20 bonus to their skill boost across all quality tiers to bolster player physical defense:
- Common add 5-10 to the associated skill (Defending armor adds 25-30)
- Uncommon add 15-25 to the associated skill (Defending armor adds 35-45)
- Rare add 30-40 to the associated skill (Defending armor adds 50-60)
- Epic add 50-60 to the associated skill (Defending armor adds 70-80)
This is rolled at random within these bands.

Commons are worth 10-50 cash, uncommons are worth 100-500 cash, rares are worth 1000-5000 cash, and epics are worth 10000-50000 cash.  The final value is based on the assocuiated skill amount that was rolled, a higher skill amount will result in a higher value with the maximum skill amount resulting in the maximum value.

Relics are always epic and have a special effect that is taken into account in certain events.  The relics are:

- Pendant of Life - Accessory - prevents death once
- Ring of Fortune - Accessory - allows to re-roll the received loot when an event awards loot
- Sword of Power - Weapon - adds 50 to fighting and gives a chance to re-roll the fight outcome if the player loses
- Plate of Invincibility - Armor - adds 50 to defending and gives a chance to re-roll the fight outcome if the player loses, in addition to the sword of power, if both are equipped, the player will always win the fight
- Staff of Magic - Weapon - adds 50 to magic and gives a chance to re-roll the outcome of a magic event if the player fails
- Boots of Stealth - Armor - adds 50 to stealth and gives a chance to re-roll the outcome of a stealth event if the player fails
- Eyeglass of the Master Pirate - Accessory - adds 50 to spotting and always find a dungeon on the 7th and 14th events, if they have the dungeons left to discover, it can't find a dungeon if they have already found the two dungeons for that leg of the journey.
- Bandage of the tireless healer - Accessory - adds 50 to medical and is never consumed when used.
- Cloak of Invisibility - Armor - adds 50 to stealth and allows the player to avoid any combat encounters, and always succeeds in stealth events.
- Pharaoh's Ankh of Rebirth - Accessory - adds 50 to medical and restores 50% HP immediately after surviving any boss or super-monster battle.
- Alchemist's Philosopher Stone - Accessory - adds 50 to salvaging and changes all trades (including wandering traders) to 90% sell value and 110% buy cost.
- Crown of the Archmage - Weapon - adds 50 to magic and allows Magic skill to replace Defending in combat damage reduction.
- Shadowstep Dagger - Weapon - adds 50 to stealth and guarantees success on Stealth Kill actions.
- Golden Horn of Plenty - Accessory - adds 50 to camping and makes resting at Camping Spots cost 0 medical supplies while restoring HP to 100%.
- Mirror of Fate - Accessory - adds 50 to spotting and flips a fight loss outcome to an instant win once per game.

### Relic Synergies
- **Warrior's Supremacy (Hitter 2-Relic Synergy):** Equipping both `Sword of Power` and `Plate of Invincibility` guarantees 100% win rate in physical combat fights.
- **Arcane Tempest (Blaster 2-Relic Synergy):** Equipping both `Staff of Magic` and `Crown of the Archmage` converts all magic trap events into immediate loot and grants complete immunity to spell damage (reducing monster magic damage to 0).
- **Grand Archmage Synergy (Blaster 3-Relic Synergy):** Equipping `Staff of Magic`, `Crown of the Archmage`, and `Pharaoh's Ankh of Rebirth` grants complete spell immunity, 100% win rate on Magic Events, and fully restores HP to 100% after every boss battle.
- **Shadow Assassin (Hider 2-Relic Synergy):** Equipping both `Shadowstep Dagger` and `Cloak of Invisibility` guarantees 100% success on all Stealth Kills and Stealth Evasions, granting full monster loot without taking damage.
- **Master Thief Synergy (Hider 3-Relic Synergy):** Equipping `Shadowstep Dagger`, `Cloak of Invisibility`, and `Alchemist's Philosopher Stone` guarantees 100% Stealth Kills, grants double cash from all monster loot, and applies 100% sell value / 100% buy cost at traders.

Relics are unique and can only be found once in the game.  There are set relics of bosses of dungeons and Super monsters, and there are random relics that can be found in the loot table.  These can spawn on very strong monsters but only have a 5% chance of spawning.  A relic is unique to its spawn, so once spawned, it will not spawn again in the game, regardless of the outcome of the relic, sold/used/equipped, or dropped/ignored.

Relics found are noted in a gallery of relics that can be viewed from the main page, as a sort of trophy case.  The gallery will only show relics found.

## Equipment

Each character can have 1 fighting weapon or magic item, 1 defending armor or 1 stealth item, 1 salvaging tool, 1 spotting item, 1 camping gear or 1 medical item equipped at a time. The player can equip two accessories. The equipped items will add to the associated skill and will be used in the events. The player can change their equipped items at any time during the journey or in the inventory page, but not during events.  The player can also have items in their inventory that are not equipped, but they will not add to the associated skill and will not be used in the events.  The equip sections are drop downs based on the items held in the inventory.  The player can choose to equip an item from the drop down and it will be equipped, or they can choose to unequip an item and it will be unequipped.  The player can also choose to drop an item from the inventory and it will be removed, the plays attributes are calculated every time the inventory is altered.  Items equipped have a * in front of their name to help identify what is equipped.  Inorder to not only rely on colour items have (c), (u), (r), (e) after their name to help identify the quality of the item.
