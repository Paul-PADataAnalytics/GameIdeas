# Hero Adventure - Game Launcher

A complete, playable text-based RPG adventure game for the terminal!

## Quick Start

To launch the game, run:

```bash
python3 play.py
```

## Game Features

### ⚔️ Character Creation
- Choose from **3 unique classes**: Hitter, Blaster, or Hider
- Each class starts with different skill bonuses
- Begin your adventure with 100 HP and 0 gold

### 🗺️ Five-Leg Journey
Travel through five regions, each with 20 events:
1. **Startersville to Forest Edge** - Low-level challenges
2. **Forest Edge to Mountain Pass** - Mid-level threats
3. **Mountain Pass to Desert Crossing** - High-level dangers
4. **Desert Crossing to Riverlands** - Very challenging
5. **Riverlands to Capital** - Final, toughest leg

### ⚔️ Dynamic Combat System
Face monsters with multiple action options:
- **Fight**: Direct combat using your fighting/defending skills
- **Sneak**: Evade past enemies using stealth
- **Steal**: Attempt to rob monsters for loot
- **Stealth Kill**: Achieve surprise victory if skilled enough

### 🏰 Dungeon Exploration
- Discover up to 2 dungeons per leg based on your spotting skill
- Explore 5 floors with enemies and challenges
- Face a powerful boss for legendary treasure
- Choose to enter or ignore dungeons as you wish

### 💰 Loot & Equipment
- Find weapons, armor, magical items, and tools
- Equip gear to boost your skills
- Manage inventory weight and carry capacity
- Sell items at journey's end for final gold total

### 📈 Leveling System
At the end of each leg, choose 3 skills to increase by 5 points:
- Customize your hero's progression
- Adapt to challenges ahead
- Build towards your desired playstyle

### 🏘️ Capital & Retirement
Arrive at the Capital with your accumulated wealth:
- **Buy a house** if you have enough gold (Cottage → Palace)
- **Work in a tavern** if wealth is insufficient
- Your score = remaining gold × house multiplier
- Relive your hero's retirement story

## Game Pages

### Main Menu
- **Start New Game** - Begin your adventure
- **View High Scores** - See the top 5 heroes
- **View Rules** - Learn game mechanics
- **Credits** - Meet the team
- **Quit** - Exit the game

### Journey Screen
Displays:
- Current leg and event progress
- HP and gold
- Inventory management (pause during non-event)
- Skills and equipment status

### Inventory
- View all items you're carrying
- Check weight and capacity
- Equip/unequip gear
- Drop items to reduce weight

## Tips for Success

1. **Balance your skills** - Don't rely on one approach
2. **Manage weight** - Overburdened heroes suffer skill penalties
3. **Explore dungeons** - Bosses carry legendary treasure
4. **Rest wisely** - Taverns and camping restore health
5. **Equip strategically** - Good gear makes a big difference
6. **Save money** - Expensive houses multiply your pension significantly

## Scoring System

**Final Score = Remaining Gold × House Multiplier**

### House Values
- **Palace**: 50,000 gold cost, 50× multiplier
- **Mansion**: 20,000 gold cost, 20× multiplier
- **Castle**: 10,000 gold cost, 10× multiplier
- **Villa**: 5,000 gold cost, 5× multiplier
- **Cottage**: 1,000 gold cost, 1× multiplier
- **Tavern**: No cost, modest pension (fallback)

### Example Scoring
- Arrive with 10,000 gold
- Buy a Villa for 5,000 gold → 5,000 remaining
- Score = 5,000 × 5 = **25,000 points**

## Character Classes

### 🛡️ Hitter
- **Bonuses**: +20 Fighting, +20 Defending, +20 Camping
- **Playstyle**: Tank and deal physical damage
- **Best for**: Direct combat approach

### 🔮 Blaster
- **Bonuses**: +20 Magic, +20 Spotting, +20 Medical
- **Playstyle**: Ranged magic and support
- **Best for**: Exploration and tactical play

### 👟 Hider
- **Bonuses**: +20 Stealth, +20 Salvaging, +20 Spotting
- **Playstyle**: Sneaky and resourceful
- **Best for**: Avoidance and thievery

## Skills Explained

- **Fighting** - Attack power in combat
- **Defending** - Defense and armor effectiveness
- **Magic** - Magical ability and spellcasting
- **Stealth** - Sneaking and evasion
- **Salvaging** - Finding and stealing items
- **Spotting** - Detecting dungeons and hazards
- **Camping** - Survival skills and field healing
- **Medical** - Using healing items effectively

## Files Included

- `play.py` - Main game launcher (this is what you run!)
- `hero_engine.py` - Core game engine (don't modify)
- `game_data.py` - Game data tables (don't modify)
- `heroadventure.md` - Design specification
- `ui/` - UI layouts (reference)
- `sim_runner.py` - Simulation mode (original)

## Game Flow

```
Front Page
    ↓
Character Creation
    ↓
Leg 1 Journey (20 events)
    → Level Up
    ↓
Leg 2 Journey (20 events)
    → Level Up
    ↓
Leg 3 Journey (20 events)
    → Level Up
    ↓
Leg 4 Journey (20 events)
    → Level Up
    ↓
Leg 5 Journey (20 events)
    → Level Up
    ↓
Capital (Buy House or Work)
    ↓
Score Screen
    ↓
Hall of Fame
```

## Notes

- This launcher preserves all original game files
- High scores are stored in memory during your session
- Each adventure takes 30-60 minutes to complete
- Different classes and strategies yield different scores
- Try multiple playthroughs to master the game!

---

**Enjoy your adventure, brave hero!** 🗡️⚔️🛡️
