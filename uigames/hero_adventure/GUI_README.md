# Hero Adventure - GUI Version

## Quick Start

Choose your preferred way to play:

### Option 1: Unified Launcher (Recommended)
```bash
./play_launcher
```
This interactive menu lets you choose between GUI and Terminal versions.

### Option 2: Direct GUI Launch
```bash
python3 play_gui.py
```
Opens the clickable graphical interface immediately.

### Option 3: Terminal Version (Original)
```bash
python3 play.py
```
Or use the original launcher:
```bash
./launch
```

---

## GUI Features

### ✨ What's New
- **Clickable Interface**: Point-and-click gameplay instead of typing
- **Visual Layout**: Dark theme with gold accents and color-coded elements
- **Button-Based Navigation**: All actions are one click away
- **Live Status Display**: See your character stats in real-time
- **Window-Based Interface**: Runs in a dedicated window (900x700)

### 🎮 Game Flow

#### 1. **Main Menu**
- Start New Game
- View High Scores
- View Rules
- Credits
- Quit

#### 2. **Character Creation**
- Enter your character name
- Select your class:
  - **Hitter**: High fighting skill (melee combat)
  - **Blaster**: High salvaging skill (ranged/magic)
  - **Hider**: High stealth skill (sneaking/evasion)

#### 3. **Journey (5 Legs)**
- Each leg presents multiple events:
  - ⚔️ **Monster Battles**: Fight, Sneak, or Run
  - 💰 **Treasure**: Collect gold
  - 🎲 **Challenges**: Roll dice for rewards
- Status bar shows: Name, Class, Level, Health, Cash

#### 4. **Battle System**
When encountering a monster, choose your approach:
- **🗡️ Fight**: Use fighting skill for direct combat
- **👻 Sneak**: Use stealth to avoid combat
- **🏃 Run Away**: Escape the encounter

#### 5. **Capital Endgame**
- View your final stats
- Purchase a house to multiply your score
- Or keep your pension

### 📊 Scoring
```
Final Score = (Cash - House Cost) × House Multiplier
```

Each house has different cost/multiplier ratios:
- Budget house: Low cost, lower multiplier
- Standard house: Medium cost, standard multiplier
- Luxury house: High cost, high multiplier

---

## Technical Details

### File Structure
```
hero_adventure/
├── play_gui.py          ← NEW: GUI version (Tkinter)
├── play.py              ← UNCHANGED: Terminal version
├── play_launcher        ← NEW: Interactive launcher menu
├── hero_engine.py       ← Core game engine (unchanged)
├── game_data.py         ← Game data tables (unchanged)
├── heroadventure.md     ← Design specification (unchanged)
└── UI files (preserved for reference)
```

### Requirements
- Python 3.x (with Tkinter - usually included)
- Same game engine and data files as terminal version

### Tkinter on Different Systems

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**macOS:**
Tkinter is included with Python from python.org

**Windows:**
Tkinter is included with Python from python.org

### Colors & Styling
- **Background**: Dark theme (#1a1a2e)
- **Text**: Cyan (#00d4ff)
- **Accents**: Gold (#ffd700)
- **Success**: Green (#00ff41)
- **Error**: Red (#ff3333)
- **Warnings**: Yellow (#ffaa00)

---

## Comparison: GUI vs Terminal

| Feature | GUI | Terminal |
|---------|-----|----------|
| Interface Type | Buttons & Windows | Text Input |
| Visual Style | Dark theme with colors | ANSI colors |
| Input Method | Click | Type |
| Accessibility | Point-and-click | Keyboard only |
| Window Size | 900x700 pixels | Full terminal |
| Speed | Fast UI rendering | Instant text |
| Portability | Requires Tkinter | Works everywhere |

---

## Tips for Playing

1. **Character Choice Matters**
   - Hitter: Best for direct combat
   - Blaster: Good for stealing treasures
   - Hider: Best for avoiding damage through stealth

2. **Combat Strategy**
   - Click the approach that matches your class strengths
   - Successful sneaks give you partial rewards without damage
   - Running away is always safe but nets no rewards

3. **Cash Management**
   - Each victory gives different rewards
   - Treasures give 20-100 gold
   - Save enough for the house you want

4. **House Selection**
   - Multipliers range from 1.5x to 3.0x
   - Higher multipliers require more cash upfront
   - Strategic choice can double or triple your final score

---

## Troubleshooting

### "No module named 'tkinter'"
Install Tkinter:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- macOS: Download Python from python.org (includes Tkinter)

### Window doesn't appear
- Make sure your display server is running
- Try running from the game directory
- Check that X11/Wayland is properly configured (Linux)

### Game runs slow
- This is normal on first launch (Python bytecode generation)
- Subsequent runs will be faster
- Ensure your system has adequate resources

### Button text is truncated
- This is just display formatting
- All functionality works correctly
- Try resizing the window

---

## Both Versions Available

You now have **two ways to play**:

1. **GUI Version** (`play_gui.py`): Clickable, visual, modern
2. **Terminal Version** (`play.py`): Classic, text-based, lightweight

Switch between them using the launcher:
```bash
./play_launcher
```

**Enjoy your adventure!** ⚔️
