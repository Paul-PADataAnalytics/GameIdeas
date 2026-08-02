#!/usr/bin/env python3
"""
Hero Adventure - Interactive GUI Game Launcher
A clickable GUI version of the Hero Adventure RPG game, built with CustomTkinter
for a modern, polished look (dark theme, rounded buttons, custom fonts).
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import sys
import os
import random
from typing import Optional, Dict, List, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hero_engine import HeroAdventureEngine
from game_data import CLASSES, LEGS, MONSTERS, ITEM_CATEGORIES, QUALITY_TIERS, HOUSES, PENSIONS, RELICS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class GameState:
    def __init__(self):
        self.engine: Optional[HeroAdventureEngine] = None
        self.player_name = ""
        self.player_class = ""
        self.scores: List[Dict] = []
        self.relics_found: Dict[str, bool] = {r: False for r in RELICS.keys()}


class HeroAdventureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hero Adventure - RPG Game")
        self.root.geometry("980x760")
        self.root.minsize(820, 620)

        # Modern dark fantasy palette
        self.colors = {
            'bg': '#12121f',
            'card': '#1d1d34',
            'card_alt': '#242444',
            'accent': '#ffd166',
            'primary': '#5865f2',
            'primary_hover': '#4752c4',
            'success': '#3ba55c',
            'success_hover': '#2d7d46',
            'danger': '#ed4245',
            'danger_hover': '#c53537',
            'warning': '#faa61a',
            'text': '#f2f3f5',
            'muted': '#9aa0ac',
        }
        self.root.configure(fg_color=self.colors['bg'])

        self.state = GameState()
        self.running = True
        self.in_dungeon = False
        self.in_combat = False

        self.show_front_page()

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------
    def clear_frame(self):
        """Clear all widgets from root"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def screen(self):
        """Create the standard scrollable screen container and return it"""
        frame = ctk.CTkScrollableFrame(self.root, fg_color=self.colors['bg'],
                                        scrollbar_button_color=self.colors['card_alt'],
                                        scrollbar_button_hover_color=self.colors['primary'])
        frame.pack(fill="both", expand=True, padx=15, pady=15)
        return frame

    def title_label(self, parent, text, **kwargs):
        return ctk.CTkLabel(parent, text=text,
                             font=ctk.CTkFont(size=28, weight="bold"),
                             text_color=self.colors['accent'], **kwargs)

    def header_label(self, parent, text, **kwargs):
        return ctk.CTkLabel(parent, text=text,
                             font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=self.colors['primary'], **kwargs)

    def body_label(self, parent, text, wraplength=700, justify="left", **kwargs):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13),
                             text_color=self.colors['text'], wraplength=wraplength,
                             justify=justify, **kwargs)

    def status_label(self, parent, text, **kwargs):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=self.colors['success'], **kwargs)

    def button(self, parent, text, command, kind="primary", **kwargs):
        palette = {
            "primary": (self.colors['primary'], self.colors['primary_hover']),
            "success": (self.colors['success'], self.colors['success_hover']),
            "danger": (self.colors['danger'], self.colors['danger_hover']),
            "muted": (self.colors['card_alt'], self.colors['card']),
        }
        fg, hover = palette.get(kind, palette["primary"])
        defaults = dict(font=ctk.CTkFont(size=13, weight="bold"), fg_color=fg,
                        hover_color=hover, corner_radius=10, height=42,
                        text_color="#ffffff")
        defaults.update(kwargs)
        return ctk.CTkButton(parent, text=text, command=command, **defaults)

    def card(self, parent, title):
        """A titled, non-scrolling card frame (LabelFrame equivalent)"""
        outer = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=14)
        self.header_label(outer, title).pack(anchor="w", padx=16, pady=(12, 4))
        return outer

    # ------------------------------------------------------------------
    # Front page / menu
    # ------------------------------------------------------------------
    def show_front_page(self):
        """Main front page"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "⚔️  HERO ADVENTURE  ⚔️").pack(pady=(30, 10))
        self.body_label(main_frame, "An epic journey awaits you across five treacherous lands",
                        wraplength=600, justify="center").pack(pady=10)

        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=40)
        buttons_frame.configure(width=400)

        self.button(buttons_frame, "🎮  Start New Game", self.start_new_game,
                    kind="success", width=340).pack(fill="x", pady=8)
        self.button(buttons_frame, "⭐  View High Scores", self.show_high_scores,
                    width=340).pack(fill="x", pady=8)
        self.button(buttons_frame, "📖  View Rules", self.show_rules,
                    width=340).pack(fill="x", pady=8)
        self.button(buttons_frame, "🏆  Credits", self.show_credits,
                    width=340).pack(fill="x", pady=8)
        self.button(buttons_frame, "❌  Quit", self.quit_game, kind="danger",
                    width=340).pack(fill="x", pady=8)

    # ------------------------------------------------------------------
    # Character creation
    # ------------------------------------------------------------------
    def start_new_game(self):
        """Start new game - character creation"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "Character Creation").pack(pady=(10, 20))

        name_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=5)
        self.header_label(name_frame, "Character Name:").pack(side="left")
        name_entry = ctk.CTkEntry(name_frame, font=ctk.CTkFont(size=13),
                                   placeholder_text="Enter your hero's name", height=36)
        name_entry.pack(side="left", padx=10, fill="x", expand=True)

        self.header_label(main_frame, "Choose Your Class:").pack(pady=(20, 10), anchor="w")

        selected_class = tk.StringVar(value="Hitter")

        for class_name, class_info in CLASSES.items():
            frame = self.card(main_frame, f"🎯 {class_name}")
            frame.pack(fill="x", pady=8)

            skills = ", ".join([f"{k}={v}" for k, v in class_info.items()])
            self.status_label(frame, f"Skills: {skills}").pack(anchor="w", padx=16, pady=(0, 4))

            ctk.CTkRadioButton(frame, text=f"Select {class_name}", variable=selected_class,
                               value=class_name, fg_color=self.colors['primary'],
                               hover_color=self.colors['primary_hover']).pack(anchor="w", padx=16, pady=(0, 12))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        def confirm_character():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a character name!")
                return
            self.state.player_name = name
            self.state.player_class = selected_class.get()
            self.create_game()

        self.button(button_frame, "Create Character", confirm_character,
                    kind="success", width=200).pack(side="left", padx=5)
        self.button(button_frame, "Back", self.show_front_page,
                    kind="muted", width=200).pack(side="left", padx=5)

    def create_game(self):
        """Initialize game engine and start journey"""
        self.state.engine = HeroAdventureEngine(self.state.player_name, self.state.player_class)
        self.dungeon_state = None
        self.levelup_state = None
        self.show_journey()

    # ------------------------------------------------------------------
    # Journey hub - shows progress (leg/event) and lets the player advance
    # one event at a time, matching the design doc ("shows the current leg
    # of the journey and the number of events completed" + a single
    # "continue the journey" button), rather than pre-rolling several
    # events and showing them all as buttons at once.
    # ------------------------------------------------------------------
    def show_journey(self):
        """Show journey progress hub - one event at a time"""
        self.clear_frame()
        main_frame = self.screen()

        engine = self.state.engine

        if engine.game_over:
            self.show_death_screen()
            return

        leg_idx = engine.current_leg_idx
        leg_data = LEGS[leg_idx]
        self.title_label(main_frame, f"Leg {leg_idx + 1}/5: {leg_data['name']}").pack(pady=(10, 15))

        status_card = self.card(main_frame, "Status")
        status_card.pack(fill="x", pady=10)
        status_text = (f"Name: {engine.hero_name} | Class: {engine.hero_class} | "
                       f"Health: {engine.hp}/{engine.max_hp} | Cash: ${engine.cash}")
        self.status_label(status_card, status_text).pack(anchor="w", padx=16, pady=(0, 4))
        progress_text = f"Event {engine.leg_event_count}/20  |  Dungeons found this leg: {engine.dungeons_found_in_leg}/2"
        self.body_label(status_card, progress_text).pack(anchor="w", padx=16, pady=(0, 12))

        self.body_label(main_frame,
                        "Press Continue Journey to advance to the next event, "
                        "or pause to check your inventory.").pack(pady=15)

        nav_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        nav_frame.pack(pady=15)

        self.button(nav_frame, "▶ Continue Journey", self.advance_event,
                    kind="success", width=220).pack(side="left", padx=5)
        self.button(nav_frame, "🎒 Inventory", self.show_inventory, width=180).pack(side="left", padx=5)
        self.button(nav_frame, "Menu", self.show_front_page, kind="muted", width=180).pack(side="left", padx=5)

    def show_death_screen(self):
        """Player has perished - game over"""
        self.clear_frame()
        main_frame = self.screen()
        engine = self.state.engine

        self.title_label(main_frame, "💀 You Have Perished").pack(pady=(20, 15))
        reason = getattr(engine, 'death_reason', None) or "unknown causes"
        self.body_label(main_frame, f"Your journey ends here, slain by {reason}.").pack(pady=10)
        self.button(main_frame, "Return to Menu", self.show_front_page,
                    kind="danger", width=220).pack(pady=20)

    def advance_event(self):
        """Advance the journey by exactly one event (design doc: 5 legs of
        20 events, an event happens on each 'continue' press)."""
        engine = self.state.engine

        # End of leg (20 events done) -> level up before moving on
        if engine.leg_event_count >= 20:
            self.show_level_up()
            return

        engine.leg_event_count += 1

        # Dungeon spotting chance - up to twice per leg, based on spotting skill
        if engine.dungeons_found_in_leg < 2:
            skills = engine.get_effective_skills()[0]
            roll = random.randint(0, 100)
            if skills.get('spotting', 5) >= roll:
                engine.dungeons_found_in_leg += 1
                leg_info = LEGS[engine.current_leg_idx]
                dungeon_idx = engine.dungeons_found_in_leg - 1
                dungeon = leg_info["dungeons"][dungeon_idx]
                self.show_dungeon_found(dungeon)
                return

        # Normal event roll (matches terminal play.py distribution):
        # 50% combat, 40% treasure, 5% tavern, 5% camping
        r = random.random()
        if r < 0.50:
            self.show_monster_event()
        elif r < 0.90:
            self.show_treasure_event()
        elif r < 0.95:
            self.show_tavern_event()
        else:
            self.show_camping_event()

    # ------------------------------------------------------------------
    # Individual event screens
    # ------------------------------------------------------------------
    def show_monster_event(self):
        """Regular monster encounter drawn from the current leg's pool"""
        engine = self.state.engine
        leg_monsters = [m for m, data in MONSTERS.items() if data.get('leg') == engine.current_leg_idx + 1]
        monster_name = random.choice(leg_monsters) if leg_monsters else "Goblin"
        self.show_monster_combat(monster_name)

    def show_monster_combat(self, monster_name, on_win_continue=None, on_loss_continue=None, allow_run=True):
        """Shared combat screen used by both regular journey encounters and
        dungeon floor/boss fights. on_win_continue/on_loss_continue let the
        caller decide what happens next (e.g. advance to the next dungeon
        floor on a win, but always exit to the journey hub on a loss)."""
        on_win_continue = on_win_continue or self.show_journey
        on_loss_continue = on_loss_continue or self.show_journey

        self.clear_frame()
        main_frame = self.screen()
        engine = self.state.engine
        monster = MONSTERS[monster_name]

        self.title_label(main_frame, f"⚔️ Battle: {monster_name}").pack(pady=(10, 15))

        stats = f"Stats: Fighting={monster['fighting']}, Defending={monster['defending']}, Magic={monster['magic']}"
        self.body_label(main_frame, stats).pack(pady=10)

        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.pack(pady=20, fill="x")

        def resolve(approach, choice):
            # engine.resolve_fight() already applies damage (take_damage) on loss
            # and already grants loot (grant_monster_loot) on win internally -
            # capture before/after state here for DISPLAY only, never re-invoke
            # those engine side effects afterwards (that would double them up).
            before_hp = engine.hp
            before_cash = engine.cash
            before_len = len(engine.inventory)
            before_equip = dict(engine.equipment)

            res = engine.resolve_fight(monster_name, choice=choice)

            if res == "JOURNEY":
                # Successful sneak - no combat occurred, no loot
                self.show_combat_result(monster_name, approach, True,
                                         "Sneaked past successfully!", no_loot=True,
                                         on_continue=on_win_continue)
            elif res == "LOSS_WINDOW":
                damage = before_hp - engine.hp
                self.show_combat_result(monster_name, approach, False,
                                         "You were bested in the encounter!", damage=damage,
                                         on_continue=on_loss_continue)
            else:
                # Any other return value indicates loot was already granted
                loot_data = self.compute_loot_diff(before_cash, before_len, before_equip)
                self.show_combat_result(monster_name, approach, True,
                                         "Victory! Loot acquired.", loot_data=loot_data,
                                         on_continue=on_win_continue)

        self.button(options_frame, "🗡️ Fight", lambda: resolve("Fight", "fight"), kind="danger").pack(fill="x", pady=5)
        self.button(options_frame, "👻 Sneak", lambda: resolve("Sneak", "sneak")).pack(fill="x", pady=5)
        self.button(options_frame, "🕵️ Steal", lambda: resolve("Steal", "steal")).pack(fill="x", pady=5)
        self.button(options_frame, "🔪 Stealth Kill", lambda: resolve("Stealth Kill", "stealth_kill")).pack(fill="x", pady=5)
        if allow_run:
            self.button(options_frame, "🏃 Run Away", on_loss_continue, kind="muted").pack(fill="x", pady=5)
        self.button(options_frame, "🎒 Inventory", self.show_inventory, kind="muted").pack(fill="x", pady=5)

    def show_treasure_event(self):
        self.clear_frame()
        main_frame = self.screen()
        engine = self.state.engine

        self.title_label(main_frame, "💰 Treasure Found!").pack(pady=(10, 15))

        reward = random.randint(20, 100)
        engine.cash += reward
        item = engine.generate_random_item(engine.current_leg_idx + 1)
        engine.inventory.append(item)

        desc_text = (f"You found ${reward} and a {item['name']} "
                    f"(value ${item['value']}, weight {item['weight']})!")
        self.body_label(main_frame, desc_text).pack(pady=10)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "Continue", self.show_journey, kind="success",
                    width=180).pack(side="left", padx=5)
        self.button(btn_frame, "🎒 Inventory", self.show_inventory, kind="muted",
                    width=180).pack(side="left", padx=5)

    def show_tavern_event(self):
        self.clear_frame()
        main_frame = self.screen()
        engine = self.state.engine

        self.title_label(main_frame, "🍺 Tavern Encountered!").pack(pady=(10, 15))
        self.body_label(main_frame, "You find a cozy tavern to rest and recover. Rest for 100g?").pack(pady=10)

        def rest_at_tavern():
            if engine.cash >= 100:
                engine.cash -= 100
                heal = random.randint(40, 60)
                engine.hp = min(engine.max_hp, engine.hp + heal)
                messagebox.showinfo("Rested", f"You rested at the tavern and recovered {heal} HP! HP: {engine.hp}/{engine.max_hp}")
            else:
                messagebox.showwarning("Not Enough Gold", "You need at least $100 to rest at the tavern.")
            self.show_journey()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "Rest ($100)", rest_at_tavern, kind="success",
                    width=180).pack(side="left", padx=5)
        self.button(btn_frame, "Continue On", self.show_journey, kind="muted",
                    width=180).pack(side="left", padx=5)

    def show_camping_event(self):
        self.clear_frame()
        main_frame = self.screen()
        engine = self.state.engine

        self.title_label(main_frame, "⛺ Camping Spot!").pack(pady=(10, 15))
        self.body_label(main_frame, "You find a good, safe place to set up camp.").pack(pady=10)

        def camp_and_rest():
            skills = engine.get_effective_skills()[0]
            heal = skills.get('camping', 5)
            med_item = engine.equipment.get("camping_medical")
            if med_item and med_item.get("category") == "medical":
                heal *= 2
                med_item["uses"] -= 1
                if med_item["uses"] <= 0:
                    engine.equipment["camping_medical"] = None
            engine.hp = min(engine.max_hp, engine.hp + heal)
            messagebox.showinfo("Rested", f"You set up camp and recovered {heal} HP! HP: {engine.hp}/{engine.max_hp}")
            self.show_journey()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "Camp & Rest", camp_and_rest, kind="success",
                    width=180).pack(side="left", padx=5)
        self.button(btn_frame, "Continue On", self.show_journey, kind="muted",
                    width=180).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # Dungeons - found twice per leg based on spotting skill. 5 floors then
    # a boss fight; the player can inspect the upcoming monster and choose
    # to Exit Dungeon safely before engaging, per the design doc.
    # ------------------------------------------------------------------
    def show_dungeon_found(self, dungeon):
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, f"🏰 Dungeon Found: {dungeon['name']}").pack(pady=(10, 15))
        self.body_label(main_frame,
                        f"You spot the entrance to {dungeon['name']}. Deep inside lurks "
                        f"{dungeon['boss']}, guarding a hoard of treasure. Enter at your own risk - "
                        "five chambers stand between you and the boss.").pack(pady=10)

        def enter():
            self.dungeon_state = {'dungeon': dungeon, 'floor': 1}
            self.show_dungeon_floor()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "⚔️ Enter Dungeon", enter, kind="success",
                    width=200).pack(side="left", padx=5)
        self.button(btn_frame, "🚪 Ignore & Continue", self.show_journey, kind="muted",
                    width=200).pack(side="left", padx=5)

    def show_dungeon_floor(self):
        """Preview screen for a dungeon floor - inspect the monster, then
        choose to engage or exit the dungeon safely."""
        engine = self.state.engine
        d_state = self.dungeon_state
        dungeon = d_state['dungeon']
        floor = d_state['floor']

        if floor > 5:
            self.show_dungeon_boss()
            return

        floor_idx = floor - 1
        floors = dungeon.get('floors', [])
        monster_name = floors[floor_idx] if floor_idx < len(floors) else "Goblin"
        monster = MONSTERS[monster_name]
        d_state['floor_monster'] = monster_name

        self.clear_frame()
        main_frame = self.screen()
        self.title_label(main_frame, f"🏰 {dungeon['name']} - Floor {floor}/5").pack(pady=(10, 15))
        stats = (f"You see {monster_name} ahead.\n"
                f"Stats: Fighting={monster['fighting']}, Defending={monster['defending']}, Magic={monster['magic']}")
        self.body_label(main_frame, stats).pack(pady=10)

        def engage():
            self.show_monster_combat(monster_name,
                                     on_win_continue=self.advance_dungeon_floor,
                                     on_loss_continue=self.exit_dungeon,
                                     allow_run=False)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "⚔️ Engage", engage, kind="danger",
                    width=200).pack(side="left", padx=5)
        self.button(btn_frame, "🚪 Exit Dungeon", self.exit_dungeon, kind="muted",
                    width=200).pack(side="left", padx=5)

    def advance_dungeon_floor(self):
        """Called after winning a dungeon floor fight - move to the next floor"""
        self.dungeon_state['floor'] += 1
        self.show_dungeon_floor()

    def exit_dungeon(self):
        """Leave the dungeon (safely before combat, or after a loss) and
        return to the main journey, per the design doc."""
        self.dungeon_state = None
        self.show_journey()

    def show_dungeon_boss(self):
        engine = self.state.engine
        dungeon = self.dungeon_state['dungeon']
        boss_name = dungeon['boss']
        monster = MONSTERS.get(boss_name)
        if monster is None:
            # Boss not defined in data - treat as dungeon cleared
            self.dungeon_victory()
            return

        self.clear_frame()
        main_frame = self.screen()
        self.title_label(main_frame, f"👑 Boss Chamber: {boss_name}").pack(pady=(10, 15))
        stats = f"Stats: Fighting={monster['fighting']}, Defending={monster['defending']}, Magic={monster['magic']}"
        self.body_label(main_frame, stats).pack(pady=10)

        def engage():
            self.show_monster_combat(boss_name,
                                     on_win_continue=self.dungeon_victory,
                                     on_loss_continue=self.exit_dungeon,
                                     allow_run=False)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.button(btn_frame, "⚔️ Engage Boss", engage, kind="danger",
                    width=200).pack(side="left", padx=5)
        self.button(btn_frame, "🚪 Exit Dungeon", self.exit_dungeon, kind="muted",
                    width=200).pack(side="left", padx=5)

    def dungeon_victory(self):
        """Boss defeated - award bonus treasure hoard cash and return to journey"""
        engine = self.state.engine
        treasure = random.randint(200, 500)
        engine.cash += treasure
        self.dungeon_state = None

        self.clear_frame()
        main_frame = self.screen()
        self.title_label(main_frame, "🏆 Dungeon Cleared!").pack(pady=(10, 15))
        self.status_label(main_frame, f"You claim ${treasure} from the treasure hoard!").pack(pady=10)
        self.button(main_frame, "Continue Journey", self.show_journey,
                    kind="success", width=220).pack(pady=20)

    # ------------------------------------------------------------------
    # Level up - at the end of each leg, choose 3 skills to increase by 5
    # ------------------------------------------------------------------
    def show_level_up(self):
        engine = self.state.engine
        if self.levelup_state is None:
            self.levelup_state = {'chosen': []}
        chosen = self.levelup_state['chosen']

        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "⭐ Level Up! ⭐").pack(pady=(10, 15))
        self.body_label(main_frame,
                        f"Leg {engine.current_leg_idx + 1} complete! Choose 3 skills to "
                        f"increase by 5 points each. ({len(chosen)}/3 chosen)").pack(pady=10)

        skills_card = self.card(main_frame, "Skills")
        skills_card.pack(fill="both", expand=True, pady=10)

        def pick(skill_name):
            engine.base_skills[skill_name] += 5
            chosen.append(skill_name)
            self.show_level_up()

        for skill_name, value in engine.base_skills.items():
            row = ctk.CTkFrame(skills_card, fg_color=self.colors['card_alt'], corner_radius=8)
            row.pack(fill="x", pady=4, padx=16)
            label_text = f"{skill_name.title()}: {value}" + (" ✓ increased" if skill_name in chosen else "")
            self.body_label(row, label_text).pack(side="left", padx=10, pady=8)
            if skill_name not in chosen and len(chosen) < 3:
                self.button(row, "+5", lambda s=skill_name: pick(s), kind="success",
                            width=70, height=32).pack(side="right", padx=10, pady=6)

        if len(chosen) >= 3:
            self.button(main_frame, "Continue", self.finish_leg,
                        kind="success", width=220).pack(pady=20)

    def finish_leg(self):
        """Advance to the next leg, or the Capital if the journey is complete"""
        engine = self.state.engine
        self.levelup_state = None
        engine.current_leg_idx += 1
        engine.leg_event_count = 0
        engine.dungeons_found_in_leg = 0

        if engine.current_leg_idx >= 5:
            self.show_capital()
        else:
            self.show_journey()

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    def show_inventory(self):
        """Show and manage inventory - equip or drop items"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "🎒 Inventory").pack(pady=(10, 15))

        engine = self.state.engine
        skills, total_weight, max_weight = engine.get_effective_skills()

        status_text = f"Carrying: {total_weight}/{max_weight} weight | Gold: ${engine.cash}"
        self.status_label(main_frame, status_text).pack(pady=5)

        # Equipped items
        equip_card = self.card(main_frame, "Equipped")
        equip_card.pack(fill="x", pady=10)

        has_equip = False
        for slot, item in engine.equipment.items():
            if item:
                has_equip = True
                self.body_label(equip_card, f"{slot}: {item['name']}").pack(anchor="w", padx=16, pady=2)
        if not has_equip:
            self.body_label(equip_card, "(None equipped)").pack(anchor="w", padx=16, pady=(0, 12))
        else:
            ctk.CTkFrame(equip_card, fg_color="transparent", height=8).pack()

        # Backpack items
        items_card = self.card(main_frame, "Backpack")
        items_card.pack(fill="both", expand=True, pady=10)

        if not engine.inventory:
            self.body_label(items_card, "Inventory is empty.").pack(anchor="w", padx=16, pady=(0, 12))
        else:
            for idx, item in enumerate(list(engine.inventory)):
                row = ctk.CTkFrame(items_card, fg_color=self.colors['card_alt'], corner_radius=8)
                row.pack(fill="x", pady=4, padx=16)

                item_text = f"{item['name']} ({item.get('code', '?')}) - ${item['value']} (w:{item['weight']})"
                self.body_label(row, item_text, wraplength=400).pack(side="left", padx=10, pady=8)

                def equip_item(i=idx):
                    if i >= len(engine.inventory):
                        return
                    it = engine.inventory[i]
                    engine.equipment[it['slot']] = it
                    self.show_inventory()

                def drop_item(i=idx):
                    if i >= len(engine.inventory):
                        return
                    engine.inventory.pop(i)
                    self.show_inventory()

                self.button(row, "Drop", drop_item, kind="danger", width=70,
                            height=32).pack(side="right", padx=(4, 10), pady=6)
                self.button(row, "Equip", equip_item, kind="success", width=70,
                            height=32).pack(side="right", padx=4, pady=6)

            ctk.CTkFrame(items_card, fg_color="transparent", height=8).pack()

        self.button(main_frame, "Back to Journey", self.show_journey, kind="muted",
                    width=220).pack(pady=15)

    # ------------------------------------------------------------------
    # Combat result / loot
    # ------------------------------------------------------------------
    def compute_loot_diff(self, before_cash, before_len, before_equip):
        """Build a display-only snapshot of loot already granted by the engine
        (e.g. inside resolve_fight -> grant_monster_loot). This must never call
        grant_monster_loot itself - that would grant the loot a second time."""
        engine = self.state.engine
        cash_gained = engine.cash - before_cash
        new_items = engine.inventory[before_len:]
        newly_equipped = [
            (slot, item) for slot, item in engine.equipment.items()
            if item and item in new_items and before_equip.get(slot) != item
        ]
        return {
            'cash_gained': cash_gained,
            'new_items': new_items,
            'newly_equipped': newly_equipped,
        }

    def show_combat_result(self, monster_name, approach, won, details, loot_data=None, damage=None,
                            no_loot=False, on_continue=None):
        """Show battle details screen after a combat choice is resolved.
        Damage and loot have already been applied by engine.resolve_fight() -
        this screen only displays the outcome, it does not apply any further
        engine side effects. on_continue lets the caller (journey vs dungeon
        floor/boss) decide what happens after the player clicks Continue."""
        on_continue = on_continue or self.show_journey

        self.clear_frame()
        main_frame = self.screen()

        engine = self.state.engine

        self.title_label(main_frame, "📋 Battle Details").pack(pady=(10, 15))
        self.header_label(main_frame, f"Approach: {approach}").pack(pady=5)

        details_card = self.card(main_frame, "Combat Roll")
        details_card.pack(fill="x", pady=10)
        self.body_label(details_card, details).pack(anchor="w", padx=16, pady=(0, 12))

        if won:
            if no_loot:
                msg = f"You evade {monster_name} successfully! (No loot - you avoided the fight)"
                self.status_label(main_frame, msg).pack(pady=10)
                self.button(main_frame, "Continue", on_continue, kind="success",
                            width=220).pack(pady=20)
            else:
                msg = f"Victory! You defeat {monster_name}!"
                self.status_label(main_frame, msg).pack(pady=10)
                self.button(main_frame, "🎁 View Loot",
                            lambda: self.show_loot_screen(loot_data or {}, on_continue=on_continue),
                            kind="success", width=220).pack(pady=20)
        else:
            msg = f"You were defeated! You take {damage} damage."
            self.body_label(main_frame, msg).pack(pady=10)

            hp_text = f"Health: {engine.hp}/{engine.max_hp}"
            self.status_label(main_frame, hp_text).pack(pady=5)

            if engine.hp <= 0 or engine.game_over:
                self.status_label(main_frame, "💀 You have perished on your journey...").pack(pady=10)
                self.button(main_frame, "Return to Menu", self.show_front_page, kind="danger",
                            width=220).pack(pady=20)
            else:
                self.button(main_frame, "Continue", on_continue, kind="muted",
                            width=220).pack(pady=20)

    def show_loot_screen(self, loot_data, on_continue=None):
        """Show detailed loot results after defeating a monster. loot_data is a
        precomputed snapshot from compute_loot_diff() - this screen only displays
        it, it never grants loot itself (that already happened in resolve_fight)."""
        on_continue = on_continue or self.show_journey

        self.clear_frame()
        main_frame = self.screen()

        cash_gained = loot_data.get('cash_gained', 0)
        new_items = loot_data.get('new_items', [])
        newly_equipped = loot_data.get('newly_equipped', [])

        self.title_label(main_frame, "🎁 Loot").pack(pady=(10, 15))
        self.status_label(main_frame, f"Gold gained: +${cash_gained}").pack(pady=5)

        items_card = self.card(main_frame, "Items Found")
        items_card.pack(fill="both", expand=True, pady=10)

        if not new_items:
            self.body_label(items_card, "No items found this time.").pack(anchor="w", padx=16, pady=(0, 12))
        else:
            for item in new_items:
                item_text = f"• {item['name']} ({item.get('code', '?')}) - ${item['value']} (w:{item['weight']})"
                self.body_label(items_card, item_text).pack(anchor="w", padx=16, pady=2)
            ctk.CTkFrame(items_card, fg_color="transparent", height=8).pack()

        if newly_equipped:
            equip_card = self.card(main_frame, "Auto-Equipped")
            equip_card.pack(fill="x", pady=10)
            for slot, item in newly_equipped:
                self.body_label(equip_card, f"{slot}: {item['name']}").pack(anchor="w", padx=16, pady=2)
            ctk.CTkFrame(equip_card, fg_color="transparent", height=8).pack()

        self.button(main_frame, "Continue", on_continue, kind="success",
                    width=220).pack(pady=20)

    # ------------------------------------------------------------------
    # Capital / endgame
    # ------------------------------------------------------------------
    def show_capital(self):
        """Show capital endgame"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "🏰 Capital - Journey's End").pack(pady=(10, 20))

        engine = self.state.engine

        stats_card = self.card(main_frame, "Final Stats")
        stats_card.pack(fill="x", pady=10)
        stats_text = f"Name: {engine.hero_name}\nClass: {engine.hero_class}\nCash: ${engine.cash}\nHealth: {engine.hp}/{engine.max_hp}"
        self.body_label(stats_card, stats_text).pack(anchor="w", padx=16, pady=(0, 12))

        houses_card = self.card(main_frame, "Purchase a House")
        houses_card.pack(fill="both", expand=True, pady=10)

        for house_info in HOUSES:
            house_name = house_info['name']
            frame = ctk.CTkFrame(houses_card, fg_color=self.colors['card_alt'], corner_radius=10)
            frame.pack(fill="x", pady=6, padx=16)

            cost = house_info['cost']
            multiplier = house_info['multiplier']

            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            self.header_label(info_frame, f"🏠 {house_name}").pack(anchor="w")
            desc_text = f"Cost: ${cost} | Score Multiplier: {multiplier}x"
            self.status_label(info_frame, desc_text).pack(anchor="w")

            def buy_house(h_cost=cost, h_mult=multiplier, h_name=house_name):
                if engine.cash >= h_cost:
                    final_score = (engine.cash - h_cost) * h_mult
                    self.state.scores.append({
                        'name': engine.hero_name,
                        'class': engine.hero_class,
                        'score': final_score,
                        'result': f'Purchased {h_name}'
                    })
                    messagebox.showinfo("Success!", f"Final Score: {final_score} pts")
                else:
                    messagebox.showerror("Error", "Not enough cash!")
                self.show_front_page()

            self.button(frame, f"Buy {house_name}", buy_house, kind="success",
                        width=160).pack(side="right", padx=10, pady=10)

        self.button(main_frame, "Don't Buy - Keep Pension", self.show_front_page,
                    kind="muted", width=260).pack(pady=15)

    # ------------------------------------------------------------------
    # Misc screens
    # ------------------------------------------------------------------
    def show_high_scores(self):
        """Display high scores"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "⭐ HALL OF FAME ⭐").pack(pady=(10, 20))

        scores_card = self.card(main_frame, "High Scores")
        scores_card.pack(fill="both", expand=True, pady=10)

        if not self.state.scores:
            self.body_label(scores_card, "No scores yet. Be the first to forge your legend!").pack(
                anchor="w", padx=16, pady=(0, 12))
        else:
            sorted_scores = sorted(self.state.scores, key=lambda x: x.get('score', 0), reverse=True)[:10]
            for i, score in enumerate(sorted_scores, 1):
                score_text = f"{i}. {score['name']} ({score['class']}) - {score['score']} pts ({score['result']})"
                self.body_label(scores_card, score_text).pack(anchor="w", padx=16, pady=3)
            ctk.CTkFrame(scores_card, fg_color="transparent", height=8).pack()

        self.button(main_frame, "Back", self.show_front_page, kind="muted",
                    width=200).pack(pady=20)

    def show_rules(self):
        """Show game rules"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "📖 Game Rules").pack(pady=(10, 20))

        rules_text = """HERO ADVENTURE - GAME RULES

OBJECTIVE:
Journey through 5 legendary lands, face enemies, collect treasures, and reach the capital to buy a house.

COMBAT:
- FIGHT: Use your fighting skill to defeat enemies directly
- SNEAK: Use stealth to avoid combat (requires higher stealth)
- STEAL: Use stealth + salvaging to pilfer from a monster
- STEALTH KILL: Use stealth x2 vs monster defending x1.5
- RUN: Escape without engaging in battle

RESOURCES:
- Health: Lost in combat, regenerates at taverns and campsites
- Cash: Earned from victories and treasures, needed to buy a house
- Inventory: Equip better gear to boost your skills

LEVELING:
After reaching the capital, purchase a house to increase your final score:
Final Score = (Cash - House Cost) x House Multiplier

SCORING:
Higher scores require balancing cash earnings with house purchases.
Each house has different costs and multipliers.

TIPS:
1. Choose fights you can win
2. Collect treasures when possible
3. Use stealth to avoid damage
4. Save cash for a good house"""

        textbox = ctk.CTkTextbox(main_frame, height=430, wrap="word",
                                  fg_color=self.colors['card'], text_color=self.colors['text'],
                                  font=ctk.CTkFont(size=13), corner_radius=14)
        textbox.pack(fill="both", expand=True, pady=10)
        textbox.insert("1.0", rules_text)
        textbox.configure(state="disabled")

        self.button(main_frame, "Back", self.show_front_page, kind="muted",
                    width=200).pack(pady=20)

    def show_credits(self):
        """Show credits"""
        self.clear_frame()
        main_frame = self.screen()

        self.title_label(main_frame, "🏆 Credits").pack(pady=(10, 20))

        credits_text = """HERO ADVENTURE - GAME CREDITS

Game Design: Hero Adventure Design Specification
Game Engine: HeroAdventureEngine (Python)
Game Data: Comprehensive data tables and balance system

GUI Version: Python + CustomTkinter Interface
Terminal Version: ANSI Terminal Interface

Created with Python 3
"An Epic Journey Awaits!"

Special Thanks:
- All brave adventurers who play this game
- The open-source community
- Everyone who contributes to making games awesome"""

        textbox = ctk.CTkTextbox(main_frame, height=380, wrap="word",
                                  fg_color=self.colors['card'], text_color=self.colors['text'],
                                  font=ctk.CTkFont(size=13), corner_radius=14)
        textbox.pack(fill="both", expand=True, pady=10)
        textbox.insert("1.0", credits_text)
        textbox.configure(state="disabled")

        self.button(main_frame, "Back", self.show_front_page, kind="muted",
                    width=200).pack(pady=20)

    def quit_game(self):
        """Quit the game"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.root.quit()


def main():
    root = ctk.CTk()
    app = HeroAdventureGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
