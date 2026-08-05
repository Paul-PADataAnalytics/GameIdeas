"""
Game data tables and definitions for Hero Adventure.
Fully compliant with heroadventure.md design specification.
"""

CLASSES = {
    "Hitter": {"fighting": 20, "defending": 20, "camping": 20},
    "Blaster": {"magic": 20, "spotting": 20, "medical": 20},
    "Hider": {"stealth": 20, "salvaging": 20, "spotting": 20}
}

LEGS = [
    {
        "id": 1,
        "name": "Startersville to Forest Edge",
        "super_monster": "Angry Deer",
        "dungeons": [
            {
                "name": "The Goblin's Den",
                "boss": "Goblin King",
                "floors": ["Goblin Scavenger", "Goblin Sentry", "Goblin Bruiser", "Goblin Shaman", "Goblin Champion"]
            },
            {
                "name": "The Bandit's Hideout",
                "boss": "Bandit Lord",
                "floors": ["Bandit Recruit", "Bandit Thug", "Bandit Scout", "Bandit Enforcer", "Bandit Lieutenant"]
            }
        ]
    },
    {
        "id": 2,
        "name": "Forest Edge to Mountain Pass",
        "super_monster": "Giant Bear",
        "dungeons": [
            {
                "name": "The Spider's Lair",
                "boss": "Giant Spider",
                "floors": ["Spiderling", "Web Spinner", "Venomous Spider", "Cave Widow", "Brood Mother"]
            },
            {
                "name": "The Bandit's Camp",
                "boss": "Bandit Chief",
                "floors": ["Camp Lookout", "Camp Raider", "Camp Brute", "Camp Sergeant", "Camp Warlord"]
            }
        ]
    },
    {
        "id": 3,
        "name": "Mountain Pass to Desert Crossing",
        "super_monster": "Wyvern",
        "dungeons": [
            {
                "name": "The Sultans Tomb",
                "boss": "Mummy",
                "floors": ["Tomb Scarab", "Sand Mummy", "Cursed Guard", "Tomb Priest", "Royal Guardian"]
            },
            {
                "name": "The Ancient Ruins",
                "boss": "Lich",
                "floors": ["Ruin Wisp", "Stone Sentinel", "Arcane Construct", "Ruin Lichling", "Ancient Warden"]
            }
        ]
    },
    {
        "id": 4,
        "name": "Desert Crossing to Riverlands",
        "super_monster": "Chimera",
        "dungeons": [
            {
                "name": "The Vampire's Castle",
                "boss": "Vampire Lord",
                "floors": ["Castle Bat Swarm", "Castle Thrall", "Vampire Spawn", "Vampiric Knight", "Blood Countess"]
            },
            {
                "name": "The Dragon's Lair",
                "boss": "Ancient Dragon",
                "floors": ["Hatchling Drake", "Dragon Whelp", "Drake Sentinel", "Dragonkin Champion", "Elder Drake"]
            }
        ]
    },
    {
        "id": 5,
        "name": "Riverlands to Capital",
        "super_monster": "Dragon",
        "dungeons": [
            {
                "name": "The Dark Fortress",
                "boss": "Dark Knight",
                "floors": ["Shadow Acolyte", "Fortress Guard", "Dark Inquisitor", "Chaos Enforcer", "Doom Herald"]
            },
            {
                "name": "The Ancient Catacombs",
                "boss": "Lich King",
                "floors": ["Bone Servant", "Wailing Spirit", "Crypt Revenant", "Catacomb Oracle", "Death Knight"]
            }
        ]
    }
]

MONSTERS = {
    # Leg 1 (+10%): Startersville to Forest Edge
    "Giant Rat": {"fighting": 9, "defending": 5, "magic": 0, "cash_min": 5, "cash_max": 15, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Rabid Bat": {"fighting": 10, "defending": 5, "magic": 0, "cash_min": 5, "cash_max": 15, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin": {"fighting": 11, "defending": 6, "magic": 0, "cash_min": 10, "cash_max": 20, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Wild Wolf": {"fighting": 12, "defending": 7, "magic": 0, "cash_min": 10, "cash_max": 20, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Kobold": {"fighting": 13, "defending": 7, "magic": 0, "cash_min": 10, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Spider": {"fighting": 14, "defending": 8, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Shadow Bandit": {"fighting": 15, "defending": 9, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Witch": {"fighting": 11, "defending": 6, "magic": 7, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Woodland Stalker": {"fighting": 14, "defending": 8, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit": {"fighting": 17, "defending": 11, "magic": 0, "cash_min": 20, "cash_max": 30, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Angry Deer": {"fighting": 20, "defending": 13, "magic": 0, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 1},
    "Goblin King": {"fighting": 22, "defending": 13, "magic": 6, "cash_min": 50, "cash_max": 100, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 1},
    "Bandit Lord": {"fighting": 24, "defending": 17, "magic": 0, "cash_min": 60, "cash_max": 120, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 1},

    # Leg 2 (+5%): Forest Edge to Mountain Pass
    "Cave Goblin": {"fighting": 20, "defending": 15, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Giant Spider": {"fighting": 21, "defending": 16, "magic": 0, "cash_min": 30, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Timber Wolf": {"fighting": 23, "defending": 17, "magic": 0, "cash_min": 30, "cash_max": 45, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Harpy": {"fighting": 25, "defending": 18, "magic": 4, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Rock Elemental": {"fighting": 27, "defending": 22, "magic": 0, "cash_min": 40, "cash_max": 60, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Cliff Stalker": {"fighting": 22, "defending": 16, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Mountain Hexer": {"fighting": 20, "defending": 15, "magic": 8, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Peak Scout": {"fighting": 24, "defending": 17, "magic": 0, "cash_min": 30, "cash_max": 45, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Mountain Ogre": {"fighting": 28, "defending": 20, "magic": 0, "cash_min": 40, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Giant Bear": {"fighting": 29, "defending": 21, "magic": 0, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 2},
    "Bandit Chief": {"fighting": 32, "defending": 23, "magic": 0, "cash_min": 80, "cash_max": 150, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 2},

    # Leg 3 (-20%): Mountain Pass to Desert Crossing
    "Dust Elemental": {"fighting": 30, "defending": 24, "magic": 10, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Mummy": {"fighting": 31, "defending": 24, "magic": 8, "cash_min": 40, "cash_max": 50, "eq_min": 4, "eq_max": 5, "leg": 3},
    "Dune Shade": {"fighting": 29, "defending": 23, "magic": 10, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Hexer": {"fighting": 30, "defending": 24, "magic": 12, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Sand Stalker": {"fighting": 33, "defending": 25, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Skeleton": {"fighting": 32, "defending": 25, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Giant Scorpion": {"fighting": 33, "defending": 26, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Raider": {"fighting": 34, "defending": 26, "magic": 0, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Sand Serpent": {"fighting": 35, "defending": 27, "magic": 0, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Wyvern": {"fighting": 38, "defending": 28, "magic": 12, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 3},
    "Lich": {"fighting": 48, "defending": 44, "magic": 32, "cash_min": 80, "cash_max": 90, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 3},

    # Leg 4 (-20%): Desert Crossing to Riverlands
    "River Siren": {"fighting": 36, "defending": 30, "magic": 16, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Corpse Creeper": {"fighting": 37, "defending": 29, "magic": 4, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Marsh Witch": {"fighting": 35, "defending": 29, "magic": 18, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Grave Stalker": {"fighting": 38, "defending": 31, "magic": 0, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Moonlit Assassin": {"fighting": 40, "defending": 33, "magic": 0, "cash_min": 55, "cash_max": 70, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Swamp Hydra": {"fighting": 38, "defending": 32, "magic": 10, "cash_min": 55, "cash_max": 70, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Shadow Gargoyle": {"fighting": 39, "defending": 35, "magic": 8, "cash_min": 55, "cash_max": 70, "eq_min": 5, "eq_max": 6, "leg": 4},
    "Vampire": {"fighting": 40, "defending": 32, "magic": 16, "cash_min": 50, "cash_max": 60, "eq_min": 5, "eq_max": 6, "leg": 4},
    "Werewolf": {"fighting": 41, "defending": 34, "magic": 0, "cash_min": 60, "cash_max": 75, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Chimera": {"fighting": 40, "defending": 36, "magic": 24, "cash_min": 10000, "cash_max": 10000, "eq_min": 7, "eq_max": 8, "relic": True, "leg": 4},
    "Vampire Lord": {"fighting": 36, "defending": 28, "magic": 20, "cash_min": 120, "cash_max": 200, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 4},
    "Ancient Dragon": {"fighting": 44, "defending": 36, "magic": 24, "cash_min": 200, "cash_max": 300, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 4},

    # Leg 5 (-20%): Riverlands to Capital
    "Dread Warlock": {"fighting": 45, "defending": 38, "magic": 30, "cash_min": 60, "cash_max": 80, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Catacomb Wraith": {"fighting": 46, "defending": 42, "magic": 24, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Void Seer": {"fighting": 44, "defending": 40, "magic": 32, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Catacomb Assassin": {"fighting": 47, "defending": 41, "magic": 0, "cash_min": 70, "cash_max": 90, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Lich Acolyte": {"fighting": 45, "defending": 42, "magic": 28, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Infernal Fiend": {"fighting": 48, "defending": 40, "magic": 18, "cash_min": 70, "cash_max": 90, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Chaos Knight": {"fighting": 49, "defending": 43, "magic": 12, "cash_min": 75, "cash_max": 95, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Abyss Golem": {"fighting": 50, "defending": 45, "magic": 10, "cash_min": 80, "cash_max": 100, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Dragon": {"fighting": 51, "defending": 44, "magic": 25, "cash_min": 60, "cash_max": 70, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Dark Knight": {"fighting": 52, "defending": 44, "magic": 12, "cash_min": 250, "cash_max": 400, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 5},
    "Lich King": {"fighting": 60, "defending": 52, "magic": 40, "cash_min": 300, "cash_max": 500, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 5},

    # Dungeon Floor Encounters: The Goblin's Den (Leg 1)
    "Goblin Scavenger": {"fighting": 12, "defending": 8, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin Sentry": {"fighting": 14, "defending": 9, "magic": 0, "cash_min": 20, "cash_max": 30, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin Bruiser": {"fighting": 16, "defending": 10, "magic": 2, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Goblin Shaman": {"fighting": 17, "defending": 11, "magic": 5, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Goblin Champion": {"fighting": 20, "defending": 12, "magic": 3, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 1},

    # Dungeon Floor Encounters: The Bandit's Hideout (Leg 1)
    "Bandit Recruit": {"fighting": 13, "defending": 9, "magic": 0, "cash_min": 18, "cash_max": 28, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit Thug": {"fighting": 15, "defending": 10, "magic": 0, "cash_min": 22, "cash_max": 32, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit Scout": {"fighting": 17, "defending": 12, "magic": 0, "cash_min": 26, "cash_max": 36, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Bandit Enforcer": {"fighting": 19, "defending": 13, "magic": 0, "cash_min": 30, "cash_max": 42, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Bandit Lieutenant": {"fighting": 22, "defending": 15, "magic": 2, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 1},

    # Dungeon Floor Encounters: The Spider's Lair (Leg 2)
    "Spiderling": {"fighting": 15, "defending": 10, "magic": 0, "cash_min": 20, "cash_max": 28, "eq_min": 1, "eq_max": 2, "leg": 2},
    "Web Spinner": {"fighting": 17, "defending": 12, "magic": 0, "cash_min": 24, "cash_max": 32, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Venomous Spider": {"fighting": 19, "defending": 14, "magic": 0, "cash_min": 28, "cash_max": 36, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Cave Widow": {"fighting": 21, "defending": 15, "magic": 2, "cash_min": 32, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Brood Mother": {"fighting": 24, "defending": 17, "magic": 3, "cash_min": 36, "cash_max": 48, "eq_min": 3, "eq_max": 4, "leg": 2},

    # Dungeon Floor Encounters: The Bandit's Camp (Leg 2)
    "Camp Lookout": {"fighting": 18, "defending": 13, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Raider": {"fighting": 21, "defending": 15, "magic": 0, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Brute": {"fighting": 24, "defending": 17, "magic": 0, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Sergeant": {"fighting": 27, "defending": 19, "magic": 0, "cash_min": 42, "cash_max": 60, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Warlord": {"fighting": 30, "defending": 21, "magic": 2, "cash_min": 50, "cash_max": 70, "eq_min": 3, "eq_max": 4, "leg": 2},

    # Dungeon Floor Encounters: The Sultans Tomb (Leg 3)
    "Tomb Scarab": {"fighting": 22, "defending": 18, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 3},
    "Sand Mummy": {"fighting": 25, "defending": 20, "magic": 4, "cash_min": 30, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Cursed Guard": {"fighting": 28, "defending": 22, "magic": 6, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Priest": {"fighting": 30, "defending": 24, "magic": 10, "cash_min": 40, "cash_max": 50, "eq_min": 4, "eq_max": 5, "leg": 3},
    "Royal Guardian": {"fighting": 33, "defending": 26, "magic": 8, "cash_min": 45, "cash_max": 55, "eq_min": 4, "eq_max": 5, "leg": 3},

    # Dungeon Floor Encounters: The Ancient Ruins (Leg 3)
    "Ruin Wisp": {"fighting": 24, "defending": 20, "magic": 10, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 3},
    "Stone Sentinel": {"fighting": 28, "defending": 24, "magic": 6, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Arcane Construct": {"fighting": 32, "defending": 28, "magic": 14, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Ruin Lichling": {"fighting": 38, "defending": 34, "magic": 24, "cash_min": 50, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Ancient Warden": {"fighting": 44, "defending": 40, "magic": 28, "cash_min": 60, "cash_max": 75, "eq_min": 3, "eq_max": 4, "leg": 3},

    # Dungeon Floor Encounters: The Vampire's Castle (Leg 4)
    "Castle Bat Swarm": {"fighting": 28, "defending": 22, "magic": 8, "cash_min": 40, "cash_max": 55, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Castle Thrall": {"fighting": 30, "defending": 24, "magic": 10, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Vampire Spawn": {"fighting": 33, "defending": 26, "magic": 14, "cash_min": 55, "cash_max": 70, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Vampiric Knight": {"fighting": 35, "defending": 28, "magic": 16, "cash_min": 70, "cash_max": 85, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Blood Countess": {"fighting": 37, "defending": 30, "magic": 18, "cash_min": 85, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 4},

    # Dungeon Floor Encounters: The Dragon's Lair (Leg 4)
    "Hatchling Drake": {"fighting": 30, "defending": 24, "magic": 10, "cash_min": 50, "cash_max": 65, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Dragon Whelp": {"fighting": 33, "defending": 27, "magic": 12, "cash_min": 60, "cash_max": 75, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Drake Sentinel": {"fighting": 36, "defending": 30, "magic": 16, "cash_min": 70, "cash_max": 85, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Dragonkin Champion": {"fighting": 39, "defending": 33, "magic": 20, "cash_min": 85, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Elder Drake": {"fighting": 42, "defending": 35, "magic": 22, "cash_min": 100, "cash_max": 120, "eq_min": 3, "eq_max": 4, "leg": 4},

    # Dungeon Floor Encounters: The Dark Fortress (Leg 5)
    "Shadow Acolyte": {"fighting": 36, "defending": 30, "magic": 18, "cash_min": 60, "cash_max": 80, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Fortress Guard": {"fighting": 40, "defending": 34, "magic": 14, "cash_min": 75, "cash_max": 95, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Dark Inquisitor": {"fighting": 44, "defending": 38, "magic": 22, "cash_min": 90, "cash_max": 110, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Chaos Enforcer": {"fighting": 48, "defending": 42, "magic": 26, "cash_min": 110, "cash_max": 140, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Doom Herald": {"fighting": 50, "defending": 44, "magic": 30, "cash_min": 140, "cash_max": 170, "eq_min": 4, "eq_max": 5, "leg": 5},

    # Dungeon Floor Encounters: The Ancient Catacombs (Leg 5)
    "Bone Servant": {"fighting": 38, "defending": 32, "magic": 10, "cash_min": 70, "cash_max": 90, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Wailing Spirit": {"fighting": 42, "defending": 36, "magic": 20, "cash_min": 80, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Crypt Revenant": {"fighting": 46, "defending": 40, "magic": 26, "cash_min": 95, "cash_max": 120, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Catacomb Oracle": {"fighting": 50, "defending": 44, "magic": 32, "cash_min": 120, "cash_max": 150, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Death Knight": {"fighting": 55, "defending": 48, "magic": 36, "cash_min": 150, "cash_max": 190, "eq_min": 4, "eq_max": 5, "leg": 5}
}

ITEM_CATEGORIES = {
    "fighting": {"slot": "fighting_weapon", "names": ["Sword", "Axe", "Mace", "Spear"], "weight": 10},
    "defending": {"slot": "defending_armor", "names": ["Leather Armor", "Chainmail", "Shield"], "weight": 10},
    "magic": {"slot": "fighting_weapon", "names": ["Wand", "Staff", "Spellbook"], "weight": 3},
    "accessories": {"slot": "accessory", "names": ["Ring", "Amulet", "Bracelet", "Lockpicks", "Survival Knife"], "weight": 1},
    "stealth": {"slot": "defending_armor", "names": ["Cloak", "Boots", "Sneak Suit"], "weight": 5},
    "salvaging": {"slot": "salvaging_tool", "names": ["Crowbar", "Hammer", "Saw"], "weight": 5},
    "spotting": {"slot": "spotting_item", "names": ["Binoculars", "Telescope", "Magnifying Glass"], "weight": 5},
    "camping": {"slot": "camping_medical", "names": ["Tent", "Sleeping Bag", "Campfire Kit"], "weight": 5},
    "medical": {"slot": "camping_medical", "names": ["Bandages", "Potions", "Herbs"], "weight": 5}
}

QUALITY_TIERS = {
    "Common": {"code": "c", "color": "white", "skill_min": 5, "skill_max": 10, "cash_min": 10, "cash_max": 50, "med_uses": 1},
    "Uncommon": {"code": "u", "color": "green", "skill_min": 15, "skill_max": 25, "cash_min": 100, "cash_max": 500, "med_uses": 2},
    "Rare": {"code": "r", "color": "blue", "skill_min": 30, "skill_max": 40, "cash_min": 1000, "cash_max": 5000, "med_uses": 3},
    "Epic": {"code": "e", "color": "purple", "skill_min": 50, "skill_max": 60, "cash_min": 10000, "cash_max": 50000, "med_uses": 5}
}

RELICS = {
    "Pendant of Life": {"type": "accessory", "effect": "prevents_death_once", "skill": None, "bonus": 0},
    "Ring of Fortune": {"type": "accessory", "effect": "reroll_loot", "skill": None, "bonus": 0},
    "Sword of Power": {"type": "fighting_weapon", "effect": "reroll_fight_loss", "skill": "fighting", "bonus": 50},
    "Plate of Invincibility": {"type": "defending_armor", "effect": "invincible_combo", "skill": "defending", "bonus": 50},
    "Staff of Magic": {"type": "fighting_weapon", "effect": "reroll_magic_loss", "skill": "magic", "bonus": 50},
    "Boots of Stealth": {"type": "defending_armor", "effect": "reroll_stealth_loss", "skill": "stealth", "bonus": 50},
    "Eyeglass of the Master Pirate": {"type": "spotting_item", "effect": "guarantee_dungeon_7_14", "skill": "spotting", "bonus": 50},
    "Bandage of the tireless healer": {"type": "camping_medical", "effect": "infinite_medical_use", "skill": "medical", "bonus": 50},
    "Cloak of Invisibility": {"type": "defending_armor", "effect": "always_stealth_auto_win", "skill": "stealth", "bonus": 50},
    "Pharaoh's Ankh of Rebirth": {"type": "accessory", "effect": "heal_after_boss", "skill": "medical", "bonus": 50},
    "Alchemist's Philosopher Stone": {"type": "salvaging_tool", "effect": "better_trade_rates", "skill": "salvaging", "bonus": 50},
    "Crown of the Archmage": {"type": "fighting_weapon", "effect": "magic_replaces_defending", "skill": "magic", "bonus": 50},
    "Shadowstep Dagger": {"type": "fighting_weapon", "effect": "always_stealth_kill", "skill": "stealth", "bonus": 50},
    "Golden Horn of Plenty": {"type": "camping_medical", "effect": "full_camping_heal", "skill": "camping", "bonus": 50},
    "Mirror of Fate": {"type": "spotting_item", "effect": "flip_loss_once", "skill": "spotting", "bonus": 50},

    # New Slot-Diverse & Stat-Boosting Relics
    "Aegis Arm Guards": {"type": "accessory", "effect": None, "skill": "defending", "bonus": 50},
    "Dragon Scale Gauntlets": {"type": "accessory", "effect": None, "skill": "fighting", "bonus": 50},
    "Ring of Arcane Power": {"type": "accessory", "effect": None, "skill": "magic", "bonus": 50},
    "Slippers of the Wind": {"type": "accessory", "effect": None, "skill": "stealth", "bonus": 50},
    "Scavenger's Iron Claw": {"type": "salvaging_tool", "effect": "extra_loot_cash", "skill": "salvaging", "bonus": 50},
    "Eagle Eye Monocle": {"type": "spotting_item", "effect": "true_trade_value", "skill": "spotting", "bonus": 50},
    "Wand of the Void": {"type": "fighting_weapon", "effect": "always_win_magic_trap", "skill": "magic", "bonus": 50},
    "Behemoth Shield": {"type": "defending_armor", "effect": "half_damage_loss", "skill": "defending", "bonus": 50},
    "Elixir of Immortality": {"type": "camping_medical", "effect": "auto_cure_dungeon_injury", "skill": "medical", "bonus": 50},

    # Magic Slot-Diversity & Shielding Relics
    "Robe of the Archmage": {"type": "defending_armor", "effect": None, "skill": "magic", "bonus": 50},
    "Orb of Sorcery": {"type": "salvaging_tool", "effect": None, "skill": "magic", "bonus": 50},
    "Crystal Ball of Prescience": {"type": "spotting_item", "effect": None, "skill": "magic", "bonus": 50},
    "Tome of Ancient Runes": {"type": "camping_medical", "effect": None, "skill": "magic", "bonus": 50},
    "Amulet of Arcane Shielding": {"type": "accessory", "effect": "double_magical_ward", "skill": "magic", "bonus": 50}
}

HOUSES = [
    {"name": "Palace", "cost": 50000, "multiplier": 50},
    {"name": "Mansion", "cost": 20000, "multiplier": 20},
    {"name": "Castle", "cost": 10000, "multiplier": 10},
    {"name": "Villa", "cost": 5000, "multiplier": 5},
    {"name": "Cottage", "cost": 1000, "multiplier": 1}
]

PENSIONS = [
    {"min": 20000, "max": 49999, "pension": 5000},
    {"min": 10000, "max": 19999, "pension": 2000},
    {"min": 5000, "max": 9999, "pension": 1000},
    {"min": 1000, "max": 4999, "pension": 500},
    {"min": 0, "max": 999, "pension": 100}
]
