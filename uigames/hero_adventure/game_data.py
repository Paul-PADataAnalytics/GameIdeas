"""
Game data tables and definitions for Hero Adventure.
Fully compliant with heroadventure.md design specification.
"""

CLASSES = {
    "Hitter": {"fighting": 20, "defending": 20, "camping": 20},
    "Blaster": {"magic": 20, "spotting": 20, "medical": 20},
    # Small fighting/defending floor bump (5 -> 12) so a failed sneak/steal
    # doesn't dump a stealth build into a fight it has almost no stats for.
    "Hider": {"stealth": 20, "salvaging": 20, "spotting": 20, "fighting": 7, "defending": 7}
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
    "Giant Rat": {"fighting": 6, "defending": 6, "magic": 0, "cash_min": 5, "cash_max": 15, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Rabid Bat": {"fighting": 8, "defending": 6, "magic": 0, "cash_min": 5, "cash_max": 15, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin": {"fighting": 10, "defending": 9, "magic": 0, "cash_min": 10, "cash_max": 20, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Wild Wolf": {"fighting": 12, "defending": 13, "magic": 0, "cash_min": 10, "cash_max": 20, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Kobold": {"fighting": 14, "defending": 13, "magic": 0, "cash_min": 10, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Spider": {"fighting": 16, "defending": 16, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Shadow Bandit": {"fighting": 18, "defending": 19, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Forest Witch": {"fighting": 10, "defending": 9, "magic": 7, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Woodland Stalker": {"fighting": 16, "defending": 16, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit": {"fighting": 22, "defending": 26, "magic": 0, "cash_min": 20, "cash_max": 30, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Angry Deer": {"fighting": 20, "defending": 13, "magic": 0, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 1},
    "Goblin King": {"fighting": 22, "defending": 13, "magic": 6, "cash_min": 50, "cash_max": 100, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 1},
    "Bandit Lord": {"fighting": 24, "defending": 17, "magic": 0, "cash_min": 60, "cash_max": 120, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 1},

    # Leg 2 (+5%): Forest Edge to Mountain Pass
    "Cave Goblin": {"fighting": 19, "defending": 25, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Giant Spider": {"fighting": 22, "defending": 29, "magic": 0, "cash_min": 30, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Timber Wolf": {"fighting": 27, "defending": 33, "magic": 0, "cash_min": 30, "cash_max": 45, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Harpy": {"fighting": 32, "defending": 37, "magic": 4, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Rock Elemental": {"fighting": 38, "defending": 52, "magic": 0, "cash_min": 40, "cash_max": 60, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Cliff Stalker": {"fighting": 24, "defending": 29, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Mountain Hexer": {"fighting": 19, "defending": 25, "magic": 8, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Peak Scout": {"fighting": 30, "defending": 33, "magic": 0, "cash_min": 30, "cash_max": 45, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Mountain Ogre": {"fighting": 40, "defending": 45, "magic": 0, "cash_min": 40, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Giant Bear": {"fighting": 29, "defending": 21, "magic": 0, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 2},
    "Bandit Chief": {"fighting": 32, "defending": 23, "magic": 0, "cash_min": 80, "cash_max": 150, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 2},

    # Leg 3 (-20%): Mountain Pass to Desert Crossing
    "Dust Elemental": {"fighting": 25, "defending": 22, "magic": 10, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Mummy": {"fighting": 28, "defending": 22, "magic": 8, "cash_min": 40, "cash_max": 50, "eq_min": 4, "eq_max": 5, "leg": 3},
    "Dune Shade": {"fighting": 23, "defending": 20, "magic": 10, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Hexer": {"fighting": 25, "defending": 22, "magic": 12, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Sand Stalker": {"fighting": 33, "defending": 25, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Skeleton": {"fighting": 30, "defending": 25, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Giant Scorpion": {"fighting": 33, "defending": 28, "magic": 0, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Raider": {"fighting": 35, "defending": 28, "magic": 0, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Sand Serpent": {"fighting": 38, "defending": 31, "magic": 0, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Wyvern": {"fighting": 38, "defending": 28, "magic": 12, "cash_min": 10000, "cash_max": 10000, "eq_min": 1, "eq_max": 2, "relic": True, "leg": 3},
    "Lich": {"fighting": 48, "defending": 44, "magic": 32, "cash_min": 80, "cash_max": 90, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 3},

    # Leg 4 (-20%): Desert Crossing to Riverlands
    "River Siren": {"fighting": 48, "defending": 56, "magic": 16, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Corpse Creeper": {"fighting": 53, "defending": 50, "magic": 4, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Marsh Witch": {"fighting": 43, "defending": 50, "magic": 18, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Grave Stalker": {"fighting": 59, "defending": 63, "magic": 0, "cash_min": 50, "cash_max": 65, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Moonlit Assassin": {"fighting": 69, "defending": 75, "magic": 0, "cash_min": 55, "cash_max": 70, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Swamp Hydra": {"fighting": 59, "defending": 69, "magic": 10, "cash_min": 55, "cash_max": 70, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Shadow Gargoyle": {"fighting": 64, "defending": 88, "magic": 8, "cash_min": 55, "cash_max": 70, "eq_min": 5, "eq_max": 6, "leg": 4},
    "Vampire": {"fighting": 69, "defending": 69, "magic": 16, "cash_min": 50, "cash_max": 60, "eq_min": 5, "eq_max": 6, "leg": 4},
    "Werewolf": {"fighting": 75, "defending": 82, "magic": 0, "cash_min": 60, "cash_max": 75, "eq_min": 4, "eq_max": 5, "leg": 4},
    "Chimera": {"fighting": 40, "defending": 36, "magic": 24, "cash_min": 10000, "cash_max": 10000, "eq_min": 7, "eq_max": 8, "relic": True, "leg": 4},
    "Vampire Lord": {"fighting": 36, "defending": 28, "magic": 20, "cash_min": 120, "cash_max": 200, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 4},
    "Ancient Dragon": {"fighting": 44, "defending": 36, "magic": 24, "cash_min": 200, "cash_max": 300, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 4},

    # Leg 5 (-20%): Riverlands to Capital
    "Dread Warlock": {"fighting": 43, "defending": 44, "magic": 30, "cash_min": 60, "cash_max": 80, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Catacomb Wraith": {"fighting": 47, "defending": 64, "magic": 24, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Void Seer": {"fighting": 39, "defending": 54, "magic": 32, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Catacomb Assassin": {"fighting": 51, "defending": 59, "magic": 0, "cash_min": 70, "cash_max": 90, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Lich Acolyte": {"fighting": 43, "defending": 64, "magic": 28, "cash_min": 65, "cash_max": 85, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Infernal Fiend": {"fighting": 56, "defending": 54, "magic": 18, "cash_min": 70, "cash_max": 90, "eq_min": 5, "eq_max": 6, "leg": 5},
    "Chaos Knight": {"fighting": 60, "defending": 69, "magic": 12, "cash_min": 75, "cash_max": 95, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Abyss Golem": {"fighting": 64, "defending": 79, "magic": 10, "cash_min": 80, "cash_max": 100, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Dragon": {"fighting": 68, "defending": 74, "magic": 25, "cash_min": 60, "cash_max": 70, "eq_min": 6, "eq_max": 7, "leg": 5},
    "Dark Knight": {"fighting": 52, "defending": 44, "magic": 12, "cash_min": 250, "cash_max": 400, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 5},
    "Lich King": {"fighting": 60, "defending": 52, "magic": 40, "cash_min": 300, "cash_max": 500, "eq_min": 2, "eq_max": 3, "relic": True, "leg": 5},

    # Dungeon Floor Encounters: The Goblin's Den (Leg 1)
    "Goblin Scavenger": {"fighting": 12, "defending": 16, "magic": 0, "cash_min": 15, "cash_max": 25, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin Sentry": {"fighting": 16, "defending": 19, "magic": 0, "cash_min": 20, "cash_max": 30, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Goblin Bruiser": {"fighting": 20, "defending": 22, "magic": 2, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Goblin Shaman": {"fighting": 22, "defending": 26, "magic": 5, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Goblin Champion": {"fighting": 28, "defending": 29, "magic": 3, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 1},

    # Dungeon Floor Encounters: The Bandit's Hideout (Leg 1)
    "Bandit Recruit": {"fighting": 14, "defending": 19, "magic": 0, "cash_min": 18, "cash_max": 28, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit Thug": {"fighting": 18, "defending": 22, "magic": 0, "cash_min": 22, "cash_max": 32, "eq_min": 1, "eq_max": 2, "leg": 1},
    "Bandit Scout": {"fighting": 22, "defending": 29, "magic": 0, "cash_min": 26, "cash_max": 36, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Bandit Enforcer": {"fighting": 26, "defending": 32, "magic": 0, "cash_min": 30, "cash_max": 42, "eq_min": 2, "eq_max": 3, "leg": 1},
    "Bandit Lieutenant": {"fighting": 32, "defending": 39, "magic": 2, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 1},

    # Dungeon Floor Encounters: The Spider's Lair (Leg 2)
    "Spiderling": {"fighting": 6, "defending": 6, "magic": 0, "cash_min": 20, "cash_max": 28, "eq_min": 1, "eq_max": 2, "leg": 2},
    "Web Spinner": {"fighting": 11, "defending": 14, "magic": 0, "cash_min": 24, "cash_max": 32, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Venomous Spider": {"fighting": 16, "defending": 21, "magic": 0, "cash_min": 28, "cash_max": 36, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Cave Widow": {"fighting": 22, "defending": 25, "magic": 2, "cash_min": 32, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 2},
    "Brood Mother": {"fighting": 30, "defending": 33, "magic": 3, "cash_min": 36, "cash_max": 48, "eq_min": 3, "eq_max": 4, "leg": 2},

    # Dungeon Floor Encounters: The Bandit's Camp (Leg 2)
    "Camp Lookout": {"fighting": 14, "defending": 17, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Raider": {"fighting": 22, "defending": 25, "magic": 0, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Brute": {"fighting": 30, "defending": 33, "magic": 0, "cash_min": 35, "cash_max": 50, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Sergeant": {"fighting": 38, "defending": 41, "magic": 0, "cash_min": 42, "cash_max": 60, "eq_min": 2, "eq_max": 3, "leg": 2},
    "Camp Warlord": {"fighting": 46, "defending": 49, "magic": 2, "cash_min": 50, "cash_max": 70, "eq_min": 3, "eq_max": 4, "leg": 2},

    # Dungeon Floor Encounters: The Sultans Tomb (Leg 3)
    "Tomb Scarab": {"fighting": 6, "defending": 6, "magic": 0, "cash_min": 25, "cash_max": 35, "eq_min": 2, "eq_max": 3, "leg": 3},
    "Sand Mummy": {"fighting": 13, "defending": 11, "magic": 4, "cash_min": 30, "cash_max": 40, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Cursed Guard": {"fighting": 20, "defending": 17, "magic": 6, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Tomb Priest": {"fighting": 25, "defending": 22, "magic": 10, "cash_min": 40, "cash_max": 50, "eq_min": 4, "eq_max": 5, "leg": 3},
    "Royal Guardian": {"fighting": 33, "defending": 28, "magic": 8, "cash_min": 45, "cash_max": 55, "eq_min": 4, "eq_max": 5, "leg": 3},

    # Dungeon Floor Encounters: The Ancient Ruins (Leg 3)
    "Ruin Wisp": {"fighting": 10, "defending": 11, "magic": 10, "cash_min": 30, "cash_max": 40, "eq_min": 2, "eq_max": 3, "leg": 3},
    "Stone Sentinel": {"fighting": 20, "defending": 22, "magic": 6, "cash_min": 35, "cash_max": 45, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Arcane Construct": {"fighting": 30, "defending": 34, "magic": 14, "cash_min": 40, "cash_max": 50, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Ruin Lichling": {"fighting": 45, "defending": 51, "magic": 24, "cash_min": 50, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 3},
    "Ancient Warden": {"fighting": 60, "defending": 68, "magic": 28, "cash_min": 60, "cash_max": 75, "eq_min": 3, "eq_max": 4, "leg": 3},

    # Dungeon Floor Encounters: The Vampire's Castle (Leg 4)
    "Castle Bat Swarm": {"fighting": 5, "defending": 5, "magic": 8, "cash_min": 40, "cash_max": 55, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Castle Thrall": {"fighting": 16, "defending": 18, "magic": 10, "cash_min": 45, "cash_max": 60, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Vampire Spawn": {"fighting": 32, "defending": 31, "magic": 14, "cash_min": 55, "cash_max": 70, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Vampiric Knight": {"fighting": 43, "defending": 43, "magic": 16, "cash_min": 70, "cash_max": 85, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Blood Countess": {"fighting": 53, "defending": 56, "magic": 18, "cash_min": 85, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 4},

    # Dungeon Floor Encounters: The Dragon's Lair (Leg 4)
    "Hatchling Drake": {"fighting": 16, "defending": 18, "magic": 10, "cash_min": 50, "cash_max": 65, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Dragon Whelp": {"fighting": 32, "defending": 37, "magic": 12, "cash_min": 60, "cash_max": 75, "eq_min": 2, "eq_max": 3, "leg": 4},
    "Drake Sentinel": {"fighting": 48, "defending": 56, "magic": 16, "cash_min": 70, "cash_max": 85, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Dragonkin Champion": {"fighting": 64, "defending": 75, "magic": 20, "cash_min": 85, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 4},
    "Elder Drake": {"fighting": 80, "defending": 88, "magic": 22, "cash_min": 100, "cash_max": 120, "eq_min": 3, "eq_max": 4, "leg": 4},

    # Dungeon Floor Encounters: The Dark Fortress (Leg 5)
    "Shadow Acolyte": {"fighting": 5, "defending": 5, "magic": 18, "cash_min": 60, "cash_max": 80, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Fortress Guard": {"fighting": 22, "defending": 25, "magic": 14, "cash_min": 75, "cash_max": 95, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Dark Inquisitor": {"fighting": 39, "defending": 44, "magic": 22, "cash_min": 90, "cash_max": 110, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Chaos Enforcer": {"fighting": 56, "defending": 64, "magic": 26, "cash_min": 110, "cash_max": 140, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Doom Herald": {"fighting": 64, "defending": 74, "magic": 30, "cash_min": 140, "cash_max": 170, "eq_min": 4, "eq_max": 5, "leg": 5},

    # Dungeon Floor Encounters: The Ancient Catacombs (Leg 5)
    "Bone Servant": {"fighting": 13, "defending": 15, "magic": 10, "cash_min": 70, "cash_max": 90, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Wailing Spirit": {"fighting": 30, "defending": 34, "magic": 20, "cash_min": 80, "cash_max": 100, "eq_min": 3, "eq_max": 4, "leg": 5},
    "Crypt Revenant": {"fighting": 47, "defending": 54, "magic": 26, "cash_min": 95, "cash_max": 120, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Catacomb Oracle": {"fighting": 64, "defending": 74, "magic": 32, "cash_min": 120, "cash_max": 150, "eq_min": 4, "eq_max": 5, "leg": 5},
    "Death Knight": {"fighting": 85, "defending": 94, "magic": 36, "cash_min": 150, "cash_max": 190, "eq_min": 4, "eq_max": 5, "leg": 5}
}

ITEM_CATEGORIES = {
    "fighting": {"slot": "fighting_weapon", "names": ["Sword", "Axe", "Mace", "Spear"], "weight": 10},
    "defending": {"slot": "defending_armor", "names": ["Leather Armor", "Chainmail", "Shield"], "weight": 10},
    "magic": {"slot": "fighting_weapon", "names": ["Wand", "Staff", "Spellbook"], "weight": 3},
    "accessories": {"slot": "accessory", "names": ["Ring", "Amulet", "Bracelet", "Lockpicks", "Survival Knife"], "weight": 1},
    "stealth": {"slot": "defending_armor", "names": ["Cloak", "Boots", "Sneak Suit"], "weight": 5},
    "salvaging": {"slot": "salvaging_tool", "names": ["Crowbar", "Hammer", "Saw"], "weight": 5},
    "spotting": {"slot": "spotting_item", "names": ["Binoculars", "Telescope", "Magnifying Glass"], "weight": 5},
    "camping": {"slot": "camping_medical", "names": ["Tent", "Sleeping Bag", "Campfire Kit"], "weight": 5}
}

QUALITY_TIERS = {
    "Common": {"code": "c", "color": "white", "skill_min": 5, "skill_max": 10, "cash_min": 10, "cash_max": 50},
    "Uncommon": {"code": "u", "color": "green", "skill_min": 15, "skill_max": 25, "cash_min": 100, "cash_max": 500},
    "Rare": {"code": "r", "color": "blue", "skill_min": 30, "skill_max": 40, "cash_min": 1000, "cash_max": 5000},
    "Epic": {"code": "e", "color": "purple", "skill_min": 50, "skill_max": 60, "cash_min": 10000, "cash_max": 50000}
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
    "Crown of the Archmage": {"type": "accessory", "effect": "magic_replaces_defending", "skill": "magic", "bonus": 50},
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

# -- Aging / Town Recovery ---------------------------------------------------
# The hero starts at age 17. Every 10 HP of damage taken translates into one
# year spent recovering in town at the start of the next leg (journey-time
# healing has been removed entirely - see get_pension()/GameController's
# town recovery flow in hero_engine.py).
AGE_START = 17
DAMAGE_PER_TOWN_YEAR = 10
TOWN_JOB_OFFER_CHANCE = 0.05
FORCED_RETIREMENT_AGE = 50
PENSION_END_AGE_MIN = 60
PENSION_END_AGE_MAX = 90
# The flat PENSIONS table above is calibrated to fund roughly this many
# years of retirement; get_pension() scales it up/down based on how many
# years actually remain until the hero's randomly rolled end-of-life age.
PENSION_BASELINE_YEARS = 20

# Optional experimental toggle (off by default): when enabled, monsters
# flagged relic=True (dungeon bosses / super monsters) get their combat
# stats scaled up independently of regular per-leg trash-monster tuning.
RELIC_MONSTER_SCALE = 1.2

# Max non-equipped backpack items; above this the hero must sell/drop
# before continuing the journey.
INVENTORY_ITEM_CAP = 20

# Named Relics (the RELICS table) only drop on legs 4-5. On legs 1-3,
# dungeon bosses and super monsters (relic=True in MONSTERS) instead grant
# a bonus gear item at this tier, one step above the leg's normal ceiling,
# capped below Epic.
BOSS_BONUS_TIER_BY_LEG = {1: "Uncommon", 2: "Rare", 3: "Rare"}

# -- Karma (stealth-kill / steal penalties) -----------------------------------
# Karma starts at 0 and only ever goes down - a successful stealth kill costs
# KARMA_STEALTH_KILL_PENALTY, a successful steal costs KARMA_STEAL_PENALTY.
# Sneaking past a monster (no violence, no theft) carries no penalty.
KARMA_STEALTH_KILL_PENALTY = -5
KARMA_STEAL_PENALTY = -1
# During town recovery, a year spent with negative karma risks landing the
# hero in jail instead of healing. PRISON_CHANCE_CAP is the asymptotic upper
# bound (never reached) and PRISON_KARMA_SCALE controls how quickly the
# curve climbs toward it as karma gets more negative - see
# GameController._prison_chance() in hero_engine.py for the exact curve.
PRISON_CHANCE_CAP = 0.75
PRISON_KARMA_SCALE = 60

TOWN_PROFESSION_MODIFIERS = [
    "miniature", "wandering", "sleepy", "eccentric", "one-eyed", "left-handed",
    "suspiciously cheerful", "perpetually damp", "unlicensed", "semi-retired",
    "self-taught", "moderately famous", "extremely superstitious", "part-time",
    "notoriously slow", "surprisingly gentle", "off-duty", "freelance",
    "meticulous", "absent-minded", "overly cautious", "recklessly brave",
    "shenanigan-prone", "clumsy", "absurdly forgetful", "overly dramatic", "perpetually confused",
]

TOWN_PROFESSIONS = [
    "cobbler", "blacksmith's assistant", "goat herder", "town crier", "rat catcher",
    "candlestick maker", "well digger", "scribe", "tanner", "miller",
    "brewer", "thatcher", "gong farmer", "fishmonger", "bell ringer",
    "gravedigger", "stable hand", "chimney sweep", "weaver", "innkeeper",
    "alchemist", "apothecary", "barber", "carpenter", "cook", "doctor", 
    "farmer", "fletcher", "gardener", "herbalist", "toad wrangler",
    "frog wobbler", "newt trainer", "salamander tamer", "lizard herder",
    "snake charmer", "turtle caretaker", "dragon wrangler", "phoenix handler",
]

TOWN_INJURIES = [
    "splinter", "blister", "bruise", "sunburn", "cramp", "papercut",
    "stubbed toe", "pulled muscle", "rash", "sprain", "nasty pinch",
    "case of the hiccups", "black eye", "twisted ankle", "burn",
    "minor cut", "twisted wrist", "shin splint", "charley horse", "bum knee",
    "concussion", "broken rib", "dislocated shoulder", "fractured wrist", "twisted ankle",
    "bruised ego", "embarrassing wardrobe malfunction", "awkward social faux pas",
    "public humiliation", "lost dignity", "minor embarrassment", "hurt feelings",
]

TOWN_BODY_PARTS = [
    "left thumb", "right elbow", "big toe", "lower back", "eyebrow",
    "kneecap", "shoulder", "earlobe", "shin", "wrist", "chin", "heel",
    "forehead", "temple", "nose", "cheek", "upper back", "lower leg", "ankle",
    "foot", "toes", "fingers", "knuckles", "neck", "jaw", "hip", "thigh", "calf",
    "abdomen", "chest", "shoulder blade", "elbow", "knee", "heel", "instep", "palm",
    "back of the hand", "side of the torso", "side of the head", "cerebelum"
]

# -- Hero Backstory / Origin Story -------------------------------------------
# Rolled once at character creation and kept for the whole run - feeds both
# the opening origin-story narration and later in-journey reminiscence lines.
HERO_HOMETOWNS = [
    "Millbrook", "Oakhollow", "Suddenmarsh", "Thistlewick", "Grayford",
    "Pinehaven", "Cobbleton", "Ashford Vale", "Nettlebrook", "Farrow's End",
    "Reedmoor", "Copperfield",
]

HERO_FAMILY_MEMBERS = [
    "mother", "father", "older brother", "older sister", "younger brother",
    "younger sister", "grandmother", "grandfather", "uncle", "aunt",
]

HERO_FAMILY_TRAITS = [
    "always said adventurers come back either rich or not at all",
    "never once believed a monster story until it was standing in the doorway",
    "swore the only thing worse than debt was a boring life",
    "kept a lucky coin that was, on closer inspection, just a button",
    "insisted every scar was a story worth telling twice",
    "warned that the family had terrible luck with maps",
    "could never remember which of the five cities was which",
    "was convinced the world beyond the hills was mostly rumor",
    "still hasn't forgiven the goat for the incident",
    "always packed too much bread and not enough advice",
    "claimed to have fought a monster once, details unconfirmed",
    "thought the family name deserved to be shouted somewhere important",
]

HERO_ASPIRATIONS = [
    "prove the village elders wrong about how the story ends",
    "see the sea for the first time",
    "buy the family a roof that doesn't leak",
    "find out if any of the old stories were true",
    "come home with a name people actually remember",
    "outdo whatever cousin keeps getting mentioned at dinner",
    "settle a debt nobody else in the family will talk about",
    "simply see something bigger than the hills around home",
]

# Fixed closing beat appended to every generated origin story - a rules
# reminder (visit all 5 cities, retire on a fortune) wearing a narrative coat.
ORIGIN_STORY_CLOSERS = [
    "One thing is certain: this journey isn't over until all five great cities have been walked, and a fortune - and a place in the world - has been carved out along the way.",
    "There's no calling this journey done short of setting foot in all five great cities and retiring on a pile of hard-won cash and loot.",
    "The road ahead runs through all five great cities, and there's no version of this story that ends before a fortune is made and a place earned in the world.",
]

# =============================================================================
# Narrative / UI strings. Everything here is display text only - moving it
# out of hero_engine.py keeps all player-facing wording in one editable file.
# =============================================================================

EQUIPMENT_SLOT_LABELS = {
    "fighting_weapon": "Fighting Weapon",
    "defending_armor": "Defending Armor",
    "salvaging_tool": "Salvaging Tool",
    "spotting_item": "Spotting Item",
    "camping_medical": "Camping / Medical",
    "accessory_1": "Accessory 1",
    "accessory_2": "Accessory 2",
}

# Earned via good deeds (super monsters defeated + dungeons cleared), index
# 0-15. See GameController._character_title() in hero_engine.py.
HONORIFIC_TITLES = [
    {"text": "The unproven", "placement": "prefix"},
    {"text": "of the Open Road", "placement": "suffix"},
    {"text": "Road-Trodden", "placement": "prefix"},
    {"text": "of the Narrow Trail", "placement": "suffix"},
    {"text": "Trail-Bitten", "placement": "prefix"},
    {"text": "of the First Gates", "placement": "suffix"},
    {"text": "Monster-Hardened", "placement": "prefix"},
    {"text": "of the Deep Paths", "placement": "suffix"},
    {"text": "Relic-Scarred", "placement": "prefix"},
    {"text": "of the Long Journey", "placement": "suffix"},
    {"text": "Champion of Road and Wood", "placement": "prefix"},
    {"text": "of the Hard-Won Path", "placement": "suffix"},
    {"text": "Warden of Road and Wood", "placement": "prefix"},
    {"text": "of the Sealed Doors", "placement": "suffix"},
    {"text": "Conqueror of Roads and Ruins", "placement": "prefix"},
    {"text": "of Legend's End", "placement": "suffix"},
]

# Earned via bad deeds (negative karma magnitude / 5, capped at 15) and used
# instead of HONORIFIC_TITLES whenever karma is negative.
NEGATIVE_KARMA_TITLES = [
    {"text": "The Untrustworthy", "placement": "prefix"},
    {"text": "of Sticky Fingers", "placement": "suffix"},
    {"text": "The Backstabber", "placement": "prefix"},
    {"text": "of the Long Knife", "placement": "suffix"},
    {"text": "The Cutthroat", "placement": "prefix"},
    {"text": "of the Midnight Blade", "placement": "suffix"},
    {"text": "The Blackhearted", "placement": "prefix"},
    {"text": "of a Thousand Graves", "placement": "suffix"},
    {"text": "The Butcher", "placement": "prefix"},
    {"text": "of Blood and Shadow", "placement": "suffix"},
    {"text": "The Infamous", "placement": "prefix"},
    {"text": "of the Damned", "placement": "suffix"},
    {"text": "The Soulless", "placement": "prefix"},
    {"text": "of Endless Sin", "placement": "suffix"},
    {"text": "The Nightmare", "placement": "prefix"},
    {"text": "of Legend's Ruin", "placement": "suffix"},
]

# Combat-style descriptor parts used to build the non-honorific half of
# GameController._character_title().
CHARACTER_TITLE_PARTS = {
    "magic_high": "Master Sourcer",
    "magic_low": "Tower Mage",
    "stealth_high": "Night Assassin",
    "stealth_low": "Catburgular",
    "fight_high": "Hard Striking",
    "fight_low": "Light Striking",
    "balanced_attack": "Balanced",
    "defense_high": "Heavily Armoured",
    "defense_low": "Lightly Armoured",
    "balanced_adventurer": "Balanced Adventurer",
}

LEG_VIBES = {
    1: "the warm, dusty road out of Startersville",
    2: "the pine-shadowed trails near Forest Edge",
    3: "the steep wind-cut passes of the mountain road",
    4: "the blistering desert flats between settlements",
    5: "the wet, humming roads of the Riverlands",
}

EVENT_NARRATION_TEMPLATES = {
    "fight": [
        "While walking through {leg_vibe}, {hero_name} nearly stepped on a {monster_name}.",
        "On {leg_vibe}, {hero_name} heard a snort, turned around, and found a {monster_name}.",
        "Near {leg_vibe}, {hero_name} tried to look busy until a {monster_name} disagreed.",
        "While crossing {leg_vibe}, {hero_name} found a {monster_name} with awful timing.",
    ],
    "dungeon_found": [
        "While walking through {leg_vibe}, {hero_name} spotted a dungeon entrance half-hidden in the scenery.",
        "On {leg_vibe}, {hero_name} noticed suspiciously dramatic rocks that were absolutely a dungeon entrance.",
        "Near {leg_vibe}, {hero_name} found a hole in the ground that looked far too intentional.",
        "While crossing {leg_vibe}, {hero_name} saw a dungeon door pretending to be part of the landscape.",
    ],
    "town_recovery": [
        "{hero_name} spends the year working as a {modifier} {profession}, nursing a {injury} to the {body_part}.",
        "Back in town, {hero_name} takes up honest work as a {modifier} {profession} while a {injury} to the {body_part} heals up.",
        "{hero_name} settles into a year of quiet recovery, moonlighting as a {modifier} {profession} despite a {injury} to the {body_part}.",
        "While healing, {hero_name} picks up odd jobs as a {modifier} {profession}, favoring a sore {body_part} from a lingering {injury}.",
    ],
    "town_job_offer": [
        "While working as a {modifier} {profession}, {hero_name} is offered a permanent, steady post - the kind adventurers usually only dream about.",
        "{hero_name}'s work as a {modifier} {profession} has impressed the locals enough to offer a permanent position.",
        "A {modifier} local guild offers {hero_name} a permanent job as a {profession}, no more monsters required.",
    ],
    "town_prison": [
        "The sheriff finally catches up with {hero_name}, and the year is spent in a jail cell instead of recovering.",
        "{hero_name}'s reputation for sneaking and thieving earns a year behind bars in the town jail.",
        "Rumors of {hero_name}'s crimes reach the magistrate, and the year passes locked away in a cell.",
        "{hero_name} trades the sickbed for a jail cell this year, paying for past misdeeds.",
    ],
    "failed_adventurer": [
        "At {age}, {hero_name}'s joints finally outvote their ambitions. It's time to hang up the sword for good.",
        "{hero_name} is {age} now, and the road no longer agrees with the body. Adventuring days are over.",
        "After one too many years recovering in town, {age}-year-old {hero_name} is forced into retirement.",
    ],
    "wandering_trader": [
        "While crossing {leg_vibe}, {hero_name} met a wandering trader who was definitely not suspicious at all.",
        "On {leg_vibe}, {hero_name} found a trader polishing goods with the confidence of a stage magician.",
        "Near {leg_vibe}, {hero_name} was waved over by a wandering trader with a grin too wide to trust.",
        "While traveling {leg_vibe}, {hero_name} bumped into a trader who somehow had exactly what was needed.",
    ],
    "magic_shrine": [
        "While walking through {leg_vibe}, {hero_name} found a magic shrine humming like it paid rent.",
        "On {leg_vibe}, {hero_name} stumbled on a shrine that was glowing far too smugly.",
        "Near {leg_vibe}, {hero_name} discovered a shrine doing its best impression of a helpful miracle.",
        "While crossing {leg_vibe}, {hero_name} found a magic shrine and chose not to ask questions.",
    ],
    "super_monster": [
        "While crossing {leg_vibe}, {hero_name} spotted a super monster and immediately regretted the walk.",
        "On {leg_vibe}, {hero_name} saw a towering super monster and reconsidered every life choice.",
        "Near {leg_vibe}, {hero_name} found a super monster pacing like it owned the road.",
        "While traveling {leg_vibe}, {hero_name} came face to face with a super monster that looked deeply offended.",
    ],
    "wander_group": [
        "While traveling through {leg_vibe}, {hero_name} fell in with a wander group that knew a shortcut.",
        "On {leg_vibe}, {hero_name} joined a strange little band of travelers and let them take the lead.",
        "Near {leg_vibe}, {hero_name} was swept along by a helpful group with suspiciously good directions.",
        "While crossing {leg_vibe}, {hero_name} let a wander group hustle the journey forward.",
    ],
    "fairy_found": [
        "While moving through {leg_vibe}, {hero_name} noticed a tiny fairy fluttering around with trouble in its eyes.",
        "On {leg_vibe}, {hero_name} saw a fairy dart out of the grass like it had bad news.",
        "Near {leg_vibe}, {hero_name} spotted a fairy behaving as if it had been waiting for exactly this moment.",
        "While crossing {leg_vibe}, {hero_name} found a fairy and immediately understood this would be weird.",
    ],
    "dungeon_floor": [
        "Inside {dungeon_name} on {leg_vibe}, {hero_name} pushed toward floor {floor_number} and ran straight into a {monster_name}.",
        "While threading {leg_vibe}, {hero_name} advanced through {dungeon_name} to floor {floor_number}, where a {monster_name} was already waiting, unimpressed.",
        "On {leg_vibe}, {hero_name} marched through {dungeon_name}, and floor {floor_number} answered with a {monster_name}.",
        "Near {leg_vibe}, {hero_name} kept climbing inside {dungeon_name} until a {monster_name} blocked floor {floor_number}.",
    ],
    "dungeon_boss": [
        "Inside {dungeon_name} on {leg_vibe}, {hero_name} reached the boss chamber, where {monster_name} was clearly expecting company.",
        "While threading {leg_vibe}, {hero_name} reached the deepest hall of {dungeon_name} and found {monster_name} guarding it like a grudge.",
        "On {leg_vibe}, {hero_name} stepped into the final room of {dungeon_name}, and {monster_name} did not look like a warm welcome.",
        "Near {leg_vibe}, {hero_name} headed for the boss of {dungeon_name} and found {monster_name} already annoyed.",
    ],
}

# One-shot outcome/result lines built by GameController when an event
# resolves. Rendered in green on the journey screen (see journey.json).
OUTCOME_TEXT = {
    "sneak_success": "You slip past {monster} without a fight!",
    "throw_item_fallback": "You escape, but lose an item and any loot.",
    "throw_item_escape": "You hurl your {item_name} at {monster_name} and slip away in the confusion - the item and any loot are lost.",
    "fight_loss": "You were bested by {monster}{rounds_text}! You take {damage} damage.",
    "fight_win": "Victory! You defeat {monster}{rounds_text}.",
    "ignore_super_monster": "You avoid the super monster and continue on your way.",
    "ignore_dungeon": "You leave the dungeon entrance undisturbed.",
    "exit_dungeon": "You retreat from the dungeon.",
    "dungeon_victory": "You cleared the dungeon and found ${treasure} in treasure!",
    "leave_trader": "You part ways with the wandering trader.",
    "levelup_continue": "You finish training and set out for the next leg.",
    "run_away": "You run from {monster} and hurry back to the road.",
    "fairy_found": "You captured a fairy!",
    "wander_group": "The wander group helped you cover extra ground.",
    "magic_shrine": "The shrine granted you ${cash}{item_part}.",
    "magic_shrine_item_part": " and {count} item(s)",
    "retired_early": "Retired early as a {profession}",
    "bought_house": "Bought {house_name}",
    "failed_adventurer_suffix": " (Failed Adventurer)",
    "tavern": "Tavern",
}

DEATH_REASONS = {
    "slain_by": "slain by {monster_name}",
    "unknown": "unknown causes",
}

DUNGEON_EXIT_REASONS = {
    "default": "left",
    "voluntary": "exited voluntarily",
    "boss_defeated": "boss defeated",
    "combat_defeat": "defeated in combat",
    "floor_defeat": "defeated on floor",
    "fairy_rescue": "fairy rescue",
}

# Win-probability -> risk-band label lookup, checked in descending order of
# threshold. Shared by HeroAdventureEngine.estimate_fight_risk() and
# ._risk_band_for_probability().
RISK_BANDS = [
    (0.85, "Most Likely"),
    (0.70, "Good Chance"),
    (0.60, "Likely"),
    (0.45, "50:50"),
    (0.30, "Not Likely"),
    (0.15, "Poor Chance"),
    (0.00, "No Way"),
]

MAGIC_SPELL_NAME_PARTS = {
    "prefixes": [
        "Ackerman's Terrible", "Bridger's Snapping", "Merrick's Smoldering",
        "Harlow's Rude", "Pritchard's Violent", "Brennan's Sparkling",
        "Gorton's Unhelpful", "Vera's Ferocious", "Milo's Fussy", "Dorian's Spiteful",
    ],
    "spells": ["Firebolt", "Icicle", "Thunder Mote", "Moon Ray", "Arc Lash"],
}

MAGIC_SHIELD_NAME_PARTS = {
    "prefixes": [
        "Bridger's", "Marlow's", "Hendrix's", "Tilda's", "Rogan's",
        "Ember's", "Nora's", "Basil's", "Ivy's", "Quinn's",
    ],
    "shields": [
        "Shield of Tremendous Resistance", "Bulwark of Ridiculous Fortitude",
        "Wall of Argument-Ending Force", "Aegis of Mildly Heroic Endurance",
        "Barrier of Unreasonable Stubbornness",
    ],
}

# Randomized combat narration lines: each category is (start_phrases,
# end_phrases); _combat_line() picks one of each and joins them around the
# numeric value (damage, loot, etc).
COMBAT_LINE_POOLS = {
    "fight_win": (
        [
            "The hero decisively struck for",
            "With a brutal swing, the hero hammered out",
            "A clean opening appeared and the hero carved out",
            "The hero went in like a hurricane and dealt",
            "A heroic thump landed for",
            "The hero's blow cracked the air for",
            "With perfect timing, the hero delivered",
            "The hero leaned into the attack and produced",
            "A wildly enthusiastic hit sent out",
            "The hero smacked the monster with",
        ],
        [
            "damage and the {monster_name} recoiled in pain.",
            "damage while the {monster_name} stumbled backward.",
            "damage and the {monster_name} yelped like it regretted everything.",
            "damage, making the {monster_name} wobble dramatically.",
            "damage and the {monster_name} looked personally offended.",
        ],
    ),
    "fight_loss": (
        [
            "The {monster_name} landed a grim blow and the hero took",
            "A nasty hit from the {monster_name} forced the hero to absorb",
            "The {monster_name} crashed in like bad news and dealt",
            "The hero failed to dodge the {monster_name}, taking",
            "A foul strike from the {monster_name} rang out for",
            "The {monster_name} clipped the hero squarely, causing",
            "The {monster_name} made a rude point with",
            "The hero ate a careless hit from the {monster_name} for",
            "The {monster_name} answered with",
            "The hero got flattened by the {monster_name} for",
        ],
        [
            "damage and had to regain their footing.",
            "damage, sending the hero skidding back.",
            "damage while the hero reeled in disbelief.",
            "damage and the hero cursed the entire road.",
            "damage, enough to make the hero rethink bravado.",
        ],
    ),
    "magic_attack": (
        [
            "The hero unleashed {spell_name} for",
            "With a dramatic flourish, the hero cast {spell_name} for",
            "The air crackled as {spell_name} blasted out for",
            "The hero waved a hand and {spell_name} erupted for",
            "A dazzling {spell_name} struck true for",
            "The hero muttered {spell_name} and cooked the foe for",
            "With a pop of sparks, {spell_name} hit for",
            "The hero hurled {spell_name} straight into the monster for",
            "A ridiculous but effective {spell_name} fired for",
            "The hero shouted {spell_name} and launched",
        ],
        [
            "damage, leaving the {monster_name} smoking and confused",
            "damage and the {monster_name} staggered under the spell",
            "damage while the {monster_name} flailed at the arcane nonsense",
            "damage and the {monster_name} shrieked at the wizardry",
            "damage, which was apparently rude enough to count as a win",
        ],
    ),
    "magic_defense": (
        [
            "Using {shield_name}, the hero only took",
            "The hero invoked {shield_name} and limited the damage to",
            "With {shield_name} humming in protest, the hero suffered only",
            "The hero braced behind {shield_name} and absorbed just",
            "{shield_name} flared up and reduced the hit to",
            "The hero rode the blow through {shield_name}, taking only",
            "With a whispered charm from {shield_name}, the hero endured",
            "The hero hid behind {shield_name} and got clipped for only",
            "A glorious shimmer from {shield_name} softened the strike to",
            "The hero used {shield_name} and barely felt",
        ],
        [
            "damage instead of a full-body disaster.",
            "damage, which was somehow still insulting.",
            "damage and lived to complain about it.",
            "damage before the monster got bored.",
            "damage, proving magic could be a decent umbrella.",
        ],
    ),
    "steal": (
        [
            "Sneaking like a silent snake, the hero pickpocketed",
            "The hero moved like a street magician and stole",
            "With a wink and a pocketful of nonsense, the hero nabbed",
            "The hero slipped in like a rumor and swiped",
            "A cunning grab let the hero steal",
            "The hero's hands became unfairly slippery and lifted",
            "With impeccable timing, the hero liberated",
            "The hero bumped the monster and somehow stole",
            "A sly little trick let the hero pocket",
            "The hero vanished into the shadows and came back with",
        ],
        [
            "before anyone noticed.",
            "while the monster blinked in confusion.",
            "and left the monster muttering in outrage.",
            "with a triumphant little shrug.",
            "and not a single apology.",
        ],
    ),
    "stealth_kill": (
        [
            "Like a tiger, the hero snuck up and took out the monster with a silent strike for",
            "The hero moved like a ghost and ended the monster with",
            "A velvet-shadow ambush let the hero land",
            "The hero glided in and delivered a silent strike worth",
            "Like a thunderless shadow, the hero deleted the monster with",
            "The hero sprang from nowhere and drove home",
            "With one whisper-quiet motion, the hero dealt",
            "The hero became a rumor with a blade and landed",
            "A perfectly rude assassination produced",
            "The hero struck from the dark and scored",
        ],
        [
            "damage before the monster could even gasp.",
            "damage, and the monster simply ceased being confident.",
            "damage while the monster forgot how to stand.",
            "damage, which was the kind of silence that wins arguments.",
            "damage and the monster folded like bad origami.",
        ],
    ),
}
