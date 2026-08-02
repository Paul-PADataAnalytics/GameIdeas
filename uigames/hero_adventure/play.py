#!/usr/bin/env python3
"""
Hero Adventure - Interactive Terminal Game Launcher
A complete text-based RPG adventure game following the design specification
"""

import sys
import os
import time
import random
import json
from typing import Optional, Dict, List, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hero_engine import HeroAdventureEngine
from game_data import CLASSES, LEGS, MONSTERS, ITEM_CATEGORIES, QUALITY_TIERS, HOUSES, PENSIONS, RELICS

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GOLD = "\033[1;33m"
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    CYAN = "\033[1;36m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[1;34m"
    MAGENTA = "\033[1;35m"
    WHITE = "\033[1;37m"

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def c(text, color="RESET"):
    return f"{getattr(Colors, color, '')}{text}{Colors.RESET}"

def header(text):
    print(f"\n{c('═'*70, 'GOLD')}")
    print(f"{c(text.center(70), 'GOLD')}")
    print(f"{c('═'*70, 'GOLD')}\n")

def section(text):
    print(f"\n{c(text, 'CYAN')}")
    print(c("─" * 50, 'CYAN'))

def success(text):
    print(c(f"✓ {text}", 'GREEN'))

def error(text):
    print(c(f"✗ {text}", 'RED'))

RELIC_DESCRIPTIONS = {
    "Pendant of Life": "Prevents death once when HP reaches 0.",
    "Ring of Fortune": "Allows re-rolling the received loot when an event awards loot.",
    "Sword of Power": "Adds +50 Fighting and gives a chance to re-roll fight outcome on loss (Guarantees victory when paired with Plate of Invincibility).",
    "Plate of Invincibility": "Adds +50 Defending and gives a chance to re-roll fight outcome on loss (Guarantees victory when paired with Sword of Power).",
    "Staff of Magic": "Adds +50 Magic and gives a chance to re-roll outcome of a failed magic event (Grants Arcane Tempest / Grand Archmage synergies).",
    "Boots of Stealth": "Adds +50 Stealth and gives a chance to re-roll outcome of a failed stealth event.",
    "Eyeglass of the Master Pirate": "Adds +50 Spotting and always discovers a dungeon on 7th and 14th leg events.",
    "Bandage of the tireless healer": "Adds +50 Medical and is never consumed when used.",
    "Cloak of Invisibility": "Adds +50 Stealth, allows bypassing combat encounters, and guarantees stealth success.",
    "Pharaoh's Ankh of Rebirth": "Adds +50 Medical and restores 50% HP immediately after surviving boss or super-monster battles.",
    "Alchemist's Philosopher Stone": "Adds +50 Salvaging and changes trader rates to 90% sell value and 110% buy cost.",
    "Crown of the Archmage": "Adds +50 Magic and allows Magic skill to replace Defending in combat damage reduction.",
    "Shadowstep Dagger": "Adds +50 Stealth and guarantees 100% success on Stealth Kills.",
    "Golden Horn of Plenty": "Adds +50 Camping and makes camping cost 0 supplies while restoring HP to 100%.",
    "Mirror of Fate": "Adds +50 Spotting and flips a fight loss outcome into an instant victory once per game.",
    "Aegis Arm Guards": "Adds +50 Defending in the accessory slot.",
    "Dragon Scale Gauntlets": "Adds +50 Fighting in the accessory slot.",
    "Ring of Arcane Power": "Adds +50 Magic in the accessory slot.",
    "Slippers of the Wind": "Adds +50 Stealth in the accessory slot.",
    "Scavenger's Iron Claw": "Adds +50 Salvaging and grants 25% extra cash on event loot rolls.",
    "Eagle Eye Monocle": "Adds +50 Spotting and reveals wandering trader inventory prices at 100% true value.",
    "Wand of the Void": "Adds +50 Magic and grants 100% win rate on all Magic Trap events.",
    "Behemoth Shield": "Adds +50 Defending and reduces monster hit damage by 50% on failed fight turns.",
    "Elixir of Immortality": "Adds +50 Medical and automatically cures all injury penalties after dungeon failures.",
    "Robe of the Archmage": "Adds +50 Magic in the armor slot, boosting Blaster spellcasting and Magical Ward defense.",
    "Orb of Sorcery": "Adds +50 Magic in the salvaging tool slot.",
    "Crystal Ball of Prescience": "Adds +50 Magic in the spotting item slot.",
    "Tome of Ancient Runes": "Adds +50 Magic in the camping/medical slot.",
    "Amulet of Arcane Shielding": "Adds +50 Magic in the accessory slot and increases Magical Ward defense bonus from 50% to 100% of Magic skill."
}

def warning(text):
    print(c(f"⚠ {text}", 'YELLOW'))

def box(title: str, lines: List[str], color="CYAN", width=62):
    title_str = f" {title} "
    pad = max(0, width - 2 - len(title_str))
    left_pad = pad // 2
    right_pad = pad - left_pad
    top = f"┌{'─' * left_pad}{title_str}{'─' * right_pad}┐"
    bot = f"└{'─' * (width - 2)}┘"
    print(c(top, color))
    for line in lines:
        print(f"{c('│', color)} {line} {c('│', color)}")
    print(c(bot, color))

def item_str(item: Dict) -> str:
    quality = item.get("quality", "Common")
    code = item.get("code", "c")
    color = "WHITE"
    if quality == "Uncommon": color = "GREEN"
    elif quality == "Rare": color = "BLUE"
    elif quality == "Epic": color = "MAGENTA"
    return c(f"{item['name']} ({code})", color)

class GameState:
    def __init__(self):
        self.engine: Optional[HeroAdventureEngine] = None
        self.player_name = ""
        self.player_class = ""
        self.scores: List[Dict] = []
        self.relics_found: Dict[str, bool] = {r: False for r in RELICS.keys()}

class HeroAdventureGame:
    def __init__(self):
        self.state = GameState()
        self.running = True
        self.in_dungeon = False
        self.in_combat = False

    def front_page(self):
        """Main front page"""
        clear()
        header("⚔️ HERO ADVENTURE ⚔️")
        print("Welcome, brave adventurer!")
        print("An epic journey awaits you across five treacherous lands.\n")
        
        options = ["1. Start New Game", "2. View High Scores", "3. View Rules", "4. Credits", "5. Quit"]
        for opt in options:
            print(opt)
        
        while True:
            choice = input(f"\n{c('Choose:', 'CYAN')} ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            error("Invalid choice!")

    def show_high_scores(self):
        """Display high scores"""
        clear()
        header("⭐ HALL OF FAME ⭐")
        
        if not self.state.scores:
            print("No scores yet. Be the first to forge your legend!\n")
        else:
            sorted_scores = sorted(self.state.scores, key=lambda x: x.get('score', 0), reverse=True)[:5]
            for i, score in enumerate(sorted_scores, 1):
                score_text = c(f"{score['score']} pts", 'GOLD')
                print(f"{i}. {score['name']} ({score['class']}) - {score_text} ({score['result']})")
        
        input(f"\n{c('Press Enter to continue...', 'DIM')}")

    def show_rules(self):
        """Display game rules"""
        clear()
        header("📜 GAME RULES 📜")
        
        print("""
CHARACTER CREATION:
• Choose from Hitter (fighting/defending/camping), Blaster (magic/spotting/medical), or Hider (stealth/salvaging/spotting)
• Start with 5 points in each skill, +20 bonus in your class skills
• Begin with 100 HP and 0 gold

THE JOURNEY:
• Travel through 5 legs of the realm, each with 20 events
• Find monsters, treasures, dungeons, traders, taverns, and more
• Gain equipment to boost your skills and survive
• Level up at the end of each leg to improve 3 skills

COMBAT:
• Every action below is a contested dice roll (stat + d20) vs the monster's stat + d20 - a big edge favors you but never guarantees the outcome
• Fight: Your fighting/magic + defending vs monster's fighting + defending (a big enough margin scores a Critical - bonus loot on a win, extra damage on a loss)
• Sneak: Your stealth vs monster defending (fails become a Fight; Boots of Stealth grant a reroll chance)
• Steal: Your stealth + salvaging vs monster defending × 2 (fails become a Fight)
• Stealth Kill: Your stealth × 2 vs monster defending × 1.5 (fails become a Fight)

DUNGEONS:
• Spot dungeons through the journey (based on spotting skill)
• Up to 2 dungeons per leg with 5 mini-encounters and a boss
• Defeat the boss to claim treasure; flee to return to journey

ENDING:
• Accumulate wealth to buy a house in the Capital
• Higher wealth = better house = higher pension multiplier
• Score = house value × pension amount
• If you die or lack wealth, work in a tavern for smaller score
""")
        
        input(f"\n{c('Press Enter to continue...', 'DIM')}")

    def show_credits(self):
        """Display credits"""
        clear()
        header("🎭 CREDITS 🎭")
        print("""
HERO ADVENTURE
A Text-Based RPG Experience

GAME DESIGN
Original Vision

DEVELOPMENT
Game Engine & Systems

PLAYTESTING
Brave Adventurers

Special thanks to all who venture forth!
""")
        input(f"\n{c('Press Enter to continue...', 'DIM')}")

    def character_creation(self) -> bool:
        """Create hero - returns True if successful"""
        clear()
        header("⚔️ CHARACTER CREATION ⚔️")
        
        # Get name
        while not self.state.player_name:
            self.state.player_name = input(f"{c('Hero name:', 'CYAN')} ").strip()
            if not self.state.player_name:
                error("Please enter a name!")
        
        # Show class info
        print(f"\n{c('Choose your class:', 'CYAN')}")
        classes_list = list(CLASSES.keys())
        for i, cls in enumerate(classes_list, 1):
            skills = CLASSES[cls]
            skills_str = ", ".join([f"+{v} {k.title()}" for k, v in skills.items()])
            print(f"{i}. {cls} ({skills_str})")
        
        print(f"\n{c('Skill Descriptions:', 'DIM')}")
        print("  Fighting: Combat attack power | Defending: Defense & armor")
        print("  Magic: Magical ability | Stealth: Sneaking & evasion")
        print("  Salvaging: Item gathering | Spotting: Detection & perception")
        print("  Camping: Survival & rest | Medical: Healing ability")
        
        # Choose class
        while not self.state.player_class:
            try:
                choice = int(input(f"\n{c('Enter class (1-3):', 'CYAN')} ").strip())
                if 1 <= choice <= len(classes_list):
                    self.state.player_class = classes_list[choice - 1]
                else:
                    error(f"Enter 1-{len(classes_list)}")
            except ValueError:
                error("Enter a number!")
        
        # Confirm
        clear()
        header("📋 CHARACTER SUMMARY 📋")
        print(f"Name: {c(self.state.player_name, 'YELLOW')}")
        print(f"Class: {c(self.state.player_class, 'BLUE')}\n")
        
        engine_test = HeroAdventureEngine(self.state.player_name, self.state.player_class)
        print(f"{c('Starting Stats:', 'CYAN')}")
        for skill, value in engine_test.base_skills.items():
            bonus = value - 5
            bonus_str = f" {c(f'+{bonus}', 'GREEN')}" if bonus > 0 else ""
            print(f"  {skill.title():15} {value}{bonus_str}")
        
        print(f"\nHP: {c('100/100', 'RED')}\nGold: {c('0g', 'YELLOW')}")
        
        confirm = input(f"\n{c('Proceed? (y/n):', 'CYAN')} ").strip().lower()
        
        if confirm == 'y':
            self.state.engine = HeroAdventureEngine(self.state.player_name, self.state.player_class)
            return True
        else:
            self.state.player_name = ""
            self.state.player_class = ""
            return False

    def show_status(self):
        """Display hero status HUD"""
        engine = self.state.engine
        skills = engine.base_skills
        effective, total_weight, max_weight = engine.get_effective_skills()
        leg_info = LEGS[engine.current_leg_idx]
        
        hp_pct = max(0, min(1.0, engine.hp / engine.max_hp))
        bar = "█" * int(hp_pct * 15) + "░" * (15 - int(hp_pct * 15))
        hp_color = 'RED' if engine.hp < 30 else 'YELLOW' if engine.hp < 70 else 'GREEN'
        weight_color = 'RED' if total_weight > max_weight else 'GREEN'

        equip_summary = ", ".join([item_str(item) for item in engine.equipment.values() if item]) or "(None)"

        lines = [
            f"Hero: {c(engine.hero_name, 'YELLOW')} ({c(engine.hero_class, 'CYAN')}) | Gold: {c(f'{engine.cash}g', 'GOLD')}",
            f"Location: {c(leg_info['name'], 'BLUE')} (Leg {engine.current_leg_idx + 1}/5 - Event {engine.leg_event_count}/20)",
            f"HP: [{c(bar, hp_color)}] {engine.hp}/{engine.max_hp} | Carry Weight: {c(f'{total_weight}/{max_weight}', weight_color)}",
            "──────────────────────────────────────────────────────────",
            f"Fight: {effective.get('fighting', 5):2d}  Def: {effective.get('defending', 5):2d}  Magic: {effective.get('magic', 5):2d}  Stealth: {effective.get('stealth', 5):2d}",
            f"Spot:  {effective.get('spotting', 5):2d}  Salv: {effective.get('salvaging', 5):2d}  Camp:  {effective.get('camping', 5):2d}  Med:     {effective.get('medical', 5):2d}",
            "──────────────────────────────────────────────────────────",
            f"Equipped: {equip_summary}"
        ]
        box("HERO STATUS HUD", lines, color="CYAN", width=62)

    def handle_item_action(self, letter: str, item: Dict, status: str, slot_key: Optional[str]):
        """Interactive action menu for a specific item (DCSS style)"""
        engine = self.state.engine
        
        while True:
            clear()
            header(f"📦 ITEM INSPECTION: {item['name']}")
            
            is_equipped = slot_key is not None
            stat_str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get('skill') else "Relic"
            target_slot = item.get('slot', 'general')
            
            lines = [
                f"Letter Slot   : {c(letter, 'YELLOW')}",
                f"Item Name     : {item_str(item)}",
                f"Equip Slot    : {c(target_slot, 'MAGENTA')} ({item.get('category', 'gear')})",
                f"Skill Bonus   : {c(stat_str, 'GREEN')}",
                f"Value / Weight: ${item['value']}  |  {item['weight']} wt",
                f"Status        : {c(status, 'GREEN' if is_equipped else 'DIM')}"
            ]
            
            relic_desc = RELIC_DESCRIPTIONS.get(item['name'])
            if relic_desc or item.get('category') == 'relic':
                effect_text = relic_desc or "Unique relic item with passive or active legendary powers."
                lines.append("──────────────────────────────────────────────────────────")
                lines.append(f"✨ Relic Effect : {c(effect_text, 'GOLD')}")

            if item.get('uses'):
                lines.append(f"Uses Remaining : {item['uses']}")

            box("ITEM DETAILS", lines, color="CYAN", width=68)
            
            print(f"\n{c('Actions available for this item:', 'CYAN')}")
            if is_equipped:
                print("  [u] Unequip item (move to backpack)")
            else:
                print("  [e] Equip / Wield item")
            print("  [d] Drop item")
            if item.get("category") == "medical":
                print("  [r] Rest / Use medical item")
            print("  [b] Back to inventory list (or press 0/Enter)")
            
            choice = input(f"\n{c('Choose action (e/u/d/r/b):', 'CYAN')} ").strip().lower()
            
            if choice == 'e' and not is_equipped:
                slot = item.get("slot")
                if not slot:
                    error("This item cannot be equipped.")
                    time.sleep(1)
                    return
                
                # Handle accessory slot target
                if slot == "accessory":
                    if not engine.equipment["accessory_1"]:
                        slot = "accessory_1"
                    elif not engine.equipment["accessory_2"]:
                        slot = "accessory_2"
                    else:
                        acc_choice = input(f"{c('Replace Accessory 1 [1] or Accessory 2 [2]?:', 'CYAN')} ").strip()
                        slot = "accessory_2" if acc_choice == '2' else "accessory_1"
                
                # Remove from inventory
                if item in engine.inventory:
                    engine.inventory.remove(item)
                
                # Unequip existing item in target slot if present
                old_eq = engine.equipment.get(slot)
                if old_eq:
                    engine.inventory.append(old_eq)
                    success(f"Unequipped {old_eq['name']} to backpack.")
                
                engine.equipment[slot] = item
                success(f"Equipped {item['name']} into {slot}!")
                time.sleep(1.2)
                return
            
            elif choice == 'u' and is_equipped:
                engine.equipment[slot_key] = None
                engine.inventory.append(item)
                success(f"Unequipped {item['name']} to backpack!")
                time.sleep(1.2)
                return
            
            elif choice == 'd':
                if is_equipped:
                    engine.equipment[slot_key] = None
                elif item in engine.inventory:
                    engine.inventory.remove(item)
                warning(f"Dropped {item['name']}.")
                time.sleep(1.2)
                return

            elif choice == 'r' and item.get("category") == "medical":
                heal = 30
                item["uses"] -= 1
                engine.hp = min(engine.max_hp, engine.hp + heal)
                success(f"Used {item['name']}! Recovered {heal} HP (HP: {engine.hp}/{engine.max_hp}).")
                if item["uses"] <= 0:
                    if is_equipped:
                        engine.equipment[slot_key] = None
                    elif item in engine.inventory:
                        engine.inventory.remove(item)
                    warning(f"{item['name']} fully consumed.")
                time.sleep(1.5)
                return

            elif choice == 'b' or choice == '':
                return

    def show_inventory(self):
        """Dungeon Crawl Stone Soup (DCSS) style letter-based inventory manager"""
        engine = self.state.engine
        
        while True:
            clear()
            header("🎒 INVENTORY & EQUIPMENT (DCSS STYLE) 🎒")
            
            skills, total_weight, max_weight = engine.get_effective_skills()
            weight_color = 'RED' if total_weight > max_weight else 'GREEN'
            
            hud = [
                f"Gold: {c(f'${engine.cash}', 'GOLD')}  |  Carry Weight: {c(f'{total_weight}/{max_weight}', weight_color)}",
                f"HP: {c(f'{engine.hp}/{engine.max_hp}', 'GREEN' if engine.hp > 50 else 'RED')}"
            ]
            box("HERO SUMMARY", hud, color="CYAN", width=68)

            letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            all_items = []  # (letter, item, status_tag, slot_key)
            
            idx = 0
            # 1. Equipped items
            for slot, eq_item in engine.equipment.items():
                if eq_item and idx < len(letters):
                    slot_tag = {
                        "fighting_weapon": "[Wielded]",
                        "defending_armor": "[Worn Armor]",
                        "salvaging_tool": "[Salvage Tool]",
                        "spotting_item": "[Spotting]",
                        "camping_medical": "[Camp/Med]",
                        "accessory_1": "[Accessory 1]",
                        "accessory_2": "[Accessory 2]"
                    }.get(slot, "[Equipped]")
                    all_items.append((letters[idx], eq_item, slot_tag, slot))
                    idx += 1

            # 2. Backpack items
            for item in engine.inventory:
                if idx < len(letters):
                    all_items.append((letters[idx], item, "[In Backpack]", None))
                    idx += 1

            if not all_items:
                print(f"\n{c('Your inventory is completely empty.', 'DIM')}")
                input(f"\n{c('Press Enter to return...', 'DIM')}")
                return

            print(f"\n{c('ITEMS IN POSSESSION:', 'CYAN')}")
            item_map = {}
            for let, item, status, slot_key in all_items:
                item_map[let] = (item, status, slot_key)
                tag_color = "GREEN" if slot_key else "DIM"
                stat_str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get('skill') else "Relic"
                target_slot = item.get('slot', 'general')
                uses_str = f" ({item['uses']} uses)" if item.get('uses') else ""
                relic_star = " ✨" if (item['name'] in RELIC_DESCRIPTIONS or item.get('category') == 'relic') else ""
                print(f"  {c(let, 'YELLOW')} - {c(status, tag_color):14} : {item_str(item):25}{relic_star} | Slot: {c(target_slot, 'MAGENTA'):18} | {stat_str:12}{uses_str} | ${item['value']:<5} | {item['weight']} wt")

            print(f"\n{c('Select an item letter [a-z] to manage that item, or option:', 'CYAN')}")
            print("  [0] Back to game (or press Enter)")
            
            inp = input(f"\n{c('Choose item letter or 0 to exit:', 'CYAN')} ").strip()
            
            # Check item letter match FIRST to avoid key collision with option shortcuts
            if inp in item_map:
                item, status, slot_key = item_map[inp]
                self.handle_item_action(inp, item, status, slot_key)
            elif inp in ['0', 'x', 'X', 'q', 'Q', 'exit'] or inp == '':
                return

    def handle_combat(self, monster_name: str) -> bool:
        """Combat encounter - returns True if won"""
        engine = self.state.engine
        leg_monsters = [m for m, data in MONSTERS.items() if data.get('leg') == engine.current_leg_idx + 1]
        monster = MONSTERS.get(monster_name) if monster_name in MONSTERS else (MONSTERS[random.choice(leg_monsters)] if leg_monsters else MONSTERS["Goblin"])
        
        clear()
        
        m_info = [
            f"Enemy: {c(monster_name, 'RED')} (Leg {engine.current_leg_idx + 1})",
            f"Fighting: {c(str(monster.get('fighting', 10)), 'RED')}  Defending: {c(str(monster.get('defending', 5)), 'BLUE')}  Magic: {c(str(monster.get('magic', 0)), 'MAGENTA')}",
            f"Loot Cash: {monster.get('cash_min', 10)}-{monster.get('cash_max', 20)}g  |  Equipment: {monster.get('eq_min', 1)}-{monster.get('eq_max', 2)} items"
        ]
        box("⚔️ MONSTER ENCOUNTER", m_info, color="RED", width=62)
        
        your_skills, _, _ = engine.get_effective_skills()
        p_atk = max(your_skills["fighting"], your_skills["magic"])
        atk_type = "Magic" if your_skills["magic"] > your_skills["fighting"] else "Fighting"
        ward_val = int(your_skills["magic"] * 0.5) if your_skills["magic"] > your_skills["fighting"] else 0
        p_def = your_skills["defending"] + ward_val
        
        p_info = [
            f"Hero: {c(engine.hero_name, 'YELLOW')} ({engine.hero_class})  |  HP: {c(f'{engine.hp}/{engine.max_hp}', 'GREEN' if engine.hp > 50 else 'RED')}",
            f"Attack ({atk_type}): {c(str(p_atk), 'GREEN')}  |  Effective Defending: {c(str(p_def), 'CYAN')}" + (f" (+{ward_val} Ward)" if ward_val else ""),
            f"Stealth: {c(str(your_skills['stealth']), 'YELLOW')}  |  Salvaging: {c(str(your_skills['salvaging']), 'YELLOW')}"
        ]
        box("🛡️ YOUR COMBAT STATS", p_info, color="CYAN", width=62)
        
        print(f"\n{c('Your options:', 'CYAN')}")
        print("1. Fight        (use fighting/magic skill)")
        print("2. Sneak        (use stealth skill)")
        print("3. Steal        (use stealth + salvaging)")
        print("4. Stealth Kill (use stealth × 2)")
        
        while True:
            choice = input(f"\n{c('Choose:', 'CYAN')} ").strip()
            if choice in ['1', '2', '3', '4']:
                break
            error("Invalid choice!")
        
        choice_map = {'1': 'fight', '2': 'sneak', '3': 'steal', '4': 'stealth_kill'}
        action_key = choice_map.get(choice, 'fight')
        
        # engine.resolve_fight() already applies damage (take_damage) on loss
        # and already grants loot (grant_monster_loot) on win internally -
        # capture before/after state here for DISPLAY only, and never re-invoke
        # those engine side effects afterwards (that would double them up).
        hp_before = engine.hp
        before_cash = engine.cash
        before_len = len(engine.inventory)
        before_equip = dict(engine.equipment)

        res = engine.resolve_fight(monster_name, choice=action_key)
        hp_after = engine.hp

        section("📋 BATTLE DETAILS")
        if res == "LOSS_WINDOW":
            damage = hp_before - hp_after
            error(f"\nFailed action against {monster_name}!")
            print(f"You take {c(f'{damage}', 'RED')} damage (HP remaining: {c(str(engine.hp), 'RED')})")
            input(f"\n{c('Press Enter to continue...', 'DIM')}")
            return False
        elif res == "JOURNEY":
            success(f"\nYou sneak past {monster_name} safely! (No damage taken)")
            input(f"\n{c('Press Enter to continue...', 'DIM')}")
            return True
        else:
            # Loot was already granted inside resolve_fight (e.g. via a
            # successful fight/steal/stealth-kill, or a fallback fight after a
            # failed sneak/steal/stealth-kill attempt) - just display it.
            self.show_loot_screen(before_cash, before_len, before_equip)
            return True

    def show_loot_screen(self, before_cash: int, before_len: int, before_equip: dict):
        """Show detailed loot results already granted by resolve_fight(), with
        equip/armoury options. Does NOT grant loot itself - engine.resolve_fight()
        already applied it; this only displays the before/after diff."""
        engine = self.state.engine

        cash_gained = engine.cash - before_cash
        new_items = engine.inventory[before_len:]
        
        clear()
        header("🎁 VICTORY LOOT 🎁")
        
        print(f"Cash Earned: {c(f'+${cash_gained}', 'GOLD')}")
        print(f"Total Cash: {c(f'${engine.cash}', 'GOLD')}\n")
        
        if new_items:
            print(f"{c('Items Found:', 'CYAN')}")
            for item in new_items:
                bonus_str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get('skill') else ""
                print(f"  • {item_str(item)} | {bonus_str} | Val: ${item['value']} | Wt: {item['weight']}")
        else:
            print(f"{c('No items dropped.', 'DIM')}")
        
        print(f"\n{c('1. Open Inventory & Equip Gear (DCSS Style)', 'CYAN')}")
        print(f"{c('2. Continue Journey', 'CYAN')}")
        
        choice = input(f"\n{c('Choose option (1-2):', 'CYAN')} ").strip()
        if choice == '1':
            self.show_inventory()


    def process_event(self):
        """Process a random journey event"""
        engine = self.state.engine
        roll = random.random()
        
        if roll < 0.5:  # Combat
            leg_monsters = [m for m, data in MONSTERS.items() if data.get('leg') == engine.current_leg_idx + 1]
            monster_name = random.choice(leg_monsters) if leg_monsters else "Goblin"
            self.handle_combat(monster_name)
        
        elif roll < 0.9:  # Find loot
            section("💰 TREASURE FOUND!")
            item = engine.generate_random_item(engine.current_leg_idx + 1)
            
            val_str = item["value"]
            wt_str = item["weight"]
            loot_lines = [
                f"Found Item: {item_str(item)}",
                f"Value: {c(f'${val_str}', 'GOLD')}  |  Weight: {c(str(wt_str), 'CYAN')}"
            ]
            box("TREASURE CHEST", loot_lines, color="GOLD", width=62)
            
            take = input(f"\n{c('Take it? (y/n):', 'CYAN')} ").strip().lower()
            if take == 'y':
                engine.inventory.append(item)
                success("Added to inventory")
        
        elif roll < 0.95:  # Tavern (infrequent ~5%)
            section("🍺 TAVERN ENCOUNTERED!")
            print("\nYou find a tavern along the road to rest and recover.")
            
            rest = input(f"{c('Rest for 100g? (y/n):', 'CYAN')} ").strip().lower()
            if rest == 'y' and engine.cash >= 100:
                engine.cash -= 100
                heal = random.randint(40, 60)
                engine.hp = min(engine.max_hp, engine.hp + heal)
                success(f"Rested and recovered {heal} HP")
            else:
                warning("You continue on...")
        
        else:  # Camping (infrequent ~5%)
            section("⛺ CAMPING SPOT!")
            print("\nYou find a safe spot to set up camp.")
            
            camp = input(f"{c('Camp and rest? (y/n):', 'CYAN')} ").strip().lower()
            if camp == 'y':
                heal = random.randint(20, 40)
                engine.hp = min(engine.max_hp, engine.hp + heal)
                success(f"Rested and recovered {heal} HP")
        
        # Check for dungeon (20% chance, max 2 per leg)
        if (engine.dungeons_found_in_leg < 2 and
            random.random() < 0.2 and
            engine.get_effective_skills()[0]["spotting"] > random.randint(30, 100)):
            
            dungeon = random.choice(LEGS[engine.current_leg_idx]["dungeons"])
            warning(f"\nYou spot a dungeon entrance: {dungeon['name']}")
            
            enter = input(f"{c('Enter dungeon? (y/n):', 'CYAN')} ").strip().lower()
            if enter == 'y':
                self.process_dungeon(dungeon)
            
            engine.dungeons_found_in_leg += 1

    def process_dungeon(self, dungeon: Dict):
        """Explore a dungeon"""
        engine = self.state.engine
        
        clear()
        header(f"🏰 DUNGEON: {dungeon['name']} 🏰")
        
        # 5 floor encounters
        floors = dungeon.get('floors', [])
        for floor in range(1, 6):
            if engine.hp <= 0:
                break
            
            print(f"\n{c(f'Floor {floor}/5', 'CYAN')}")
            
            floor_idx = floor - 1
            monster_name = floors[floor_idx] if floor_idx < len(floors) else "Goblin"
            if not self.handle_combat(monster_name):
                warning("You flee the dungeon!")
                return
            
            time.sleep(0.5)
        
        if engine.hp <= 0:
            warning("You were defeated and fled the dungeon!")
            return
        
        # Boss fight
        print("\n" + c("="*50, 'RED'))
        print(c(f"BOSS: {dungeon['boss']}", 'RED'))
        print(c("="*50, 'RED'))
        
        if self.handle_combat(dungeon['boss']):
            treasure = random.randint(200, 500)
            engine.cash += treasure
            success(f"You claim {treasure}g from the treasure hoard!")
        else:
            warning("You flee the dungeon, defeated but alive!")

    def level_up(self):
        """Level up at end of leg"""
        engine = self.state.engine
        
        clear()
        header("⭐ LEVEL UP! ⭐")
        
        print("Choose 3 skills to increase by 5 points each:\n")
        
        skills = list(engine.base_skills.keys())
        chosen = []
        
        for attempt in range(3):
            print(f"\n{c(f'Selection {attempt + 1}/3:', 'CYAN')}")
            for i, skill in enumerate(skills, 1):
                val = engine.base_skills[skill]
                mark = " ✓" if skill in chosen else ""
                print(f"  {i}. {skill.title():15} (now {val}){mark}")
            
            while True:
                try:
                    choice = int(input(f"\n{c('Choose (1-8):', 'CYAN')} ").strip())
                    if 1 <= choice <= len(skills):
                        skill = skills[choice - 1]
                        if skill not in chosen:
                            engine.base_skills[skill] += 5
                            chosen.append(skill)
                            success(f"Increased {skill} to {engine.base_skills[skill]}")
                            break
                        else:
                            error("Already increased this skill!")
                    else:
                        error(f"Enter 1-{len(skills)}")
                except ValueError:
                    error("Enter a number!")
        
        input(f"\n{c('Press Enter to continue...', 'DIM')}")

    def process_leg(self):
        """Process one leg of the journey"""
        engine = self.state.engine
        leg_num = engine.current_leg_idx + 1
        leg_info = LEGS[engine.current_leg_idx]
        
        clear()
        header(f"LEG {leg_num}/5: {leg_info['name']}")
        print(f"Starting with {c(f'{engine.cash}g', 'YELLOW')} and {c(f'{engine.hp}', 'RED')} HP\n")
        
        input(f"{c('Press Enter to begin...', 'DIM')}")
        
        # Process 20 events
        for event_num in range(1, 21):
            if engine.hp <= 0:
                error("You have been defeated!")
                engine.game_over = True
                return
            
            engine.leg_event_count = event_num

            while True:
                clear()
                print(f"\n{c(f'Leg {leg_num}/5 ─ Event {event_num}/20', 'CYAN')}")
                self.show_status()
                
                cmd = input(f"\n{c('Press Enter for next event, or (i) Inventory:', 'DIM')} ").strip().lower()
                if cmd == 'i':
                    self.show_inventory()
                    continue
                break
            
            self.process_event()
            
            if engine.hp <= 0:
                break
        
        # Level up
        if engine.hp > 0:
            self.level_up()
        
        engine.current_leg_idx += 1
        engine.leg_event_count = 0
        engine.dungeons_found_in_leg = 0

    def capital_screen(self):
        """Buy house or go to tavern"""
        engine = self.state.engine
        
        clear()
        header("🏰 THE CAPITAL 🏰")
        
        # Sell all inventory
        inventory_value = sum(item['value'] for item in engine.inventory)
        engine.cash += inventory_value
        
        print(f"{c(engine.hero_name, 'YELLOW')} arrives at the Capital!")
        print(f"Final Gold: {c(f'{engine.cash}g', 'GOLD')}\n")
        
        # Determine pension bracket
        pension_tier = None
        for tier in PENSIONS:
            if tier['min'] <= engine.cash <= tier['max']:
                pension_tier = tier
                break
        
        if not pension_tier:
            pension_tier = PENSIONS[-1]  # Fallback to lowest
        
        print(f"{c('Available Houses:', 'CYAN')}")
        
        affordable = [h for h in HOUSES if h['cost'] <= engine.cash]
        
        for i, house in enumerate(affordable, 1):
            remaining = engine.cash - house['cost']
            score = remaining * house['multiplier']
            print(f"{i}. {house['name']:15} - ${house['cost']:6} (multiplier: {house['multiplier']}x, score: {c(f'{score}', 'YELLOW')})")
        
        print(f"{len(affordable) + 1}. Tavern (fallback)")
        
        if not affordable:
            print("\nNo affordable houses. You must work at a tavern.")
            score = pension_tier['pension']
            print(f"\nTavern Pension: {c(f'{score}g/year', 'YELLOW')}")
        else:
            while True:
                try:
                    choice = int(input(f"\n{c('Choose house (1-9):', 'CYAN')} ").strip()) - 1
                    if choice == len(affordable):
                        score = pension_tier['pension']
                        print(f"\nYou work at a tavern. Pension: {c(f'{score}g/year', 'YELLOW')}")
                        break
                    elif 0 <= choice < len(affordable):
                        house = affordable[choice]
                        remaining = engine.cash - house['cost']
                        score = remaining * house['multiplier']
                        print(f"\n{c(engine.hero_name, 'YELLOW')} buys {house['name']}")
                        print(f"Cost: {house['cost']}g")
                        print(f"Remaining: {remaining}g")
                        print(f"Score: {c(f'{score} pts', 'GOLD')}")
                        break
                except (ValueError, IndexError):
                    error("Invalid choice!")
        
        # Record score
        self.state.scores.append({
            'name': engine.hero_name,
            'class': engine.hero_class,
            'score': score,
            'result': f"{engine.cash}g"
        })
        
        input(f"\n{c('Press Enter to continue...', 'DIM')}")

    def run(self):
        """Main game loop"""
        while self.running:
            choice = self.front_page()
            
            if choice == '1':
                if self.character_creation():
                    # Run all 5 legs
                    for leg in range(5):
                        if self.state.engine.hp > 0:
                            self.process_leg()
                        else:
                            break
                    
                    # End game
                    if self.state.engine.hp > 0:
                        self.capital_screen()
                    else:
                        clear()
                        header("💀 GAME OVER 💀")
                        error(f"{self.state.player_name} has fallen...")
                    
                    input(f"\n{c('Press Enter to return to main menu...', 'DIM')}")
                    self.state.player_name = ""
                    self.state.player_class = ""
                    self.state.engine = None
            
            elif choice == '2':
                self.show_high_scores()
            elif choice == '3':
                self.show_rules()
            elif choice == '4':
                self.show_credits()
            elif choice == '5':
                clear()
                print("\nThanks for playing Hero Adventure!")
                print("May your next adventure be legendary.\n")
                self.running = False

if __name__ == "__main__":
    game = HeroAdventureGame()
    game.run()
