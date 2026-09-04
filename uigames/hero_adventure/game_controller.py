"""
UI-agnostic screen-flow controller for Hero Adventure: GameController.

See game_engine.py (HeroAdventureEngine) for the actual simulation/rules
layer that this class drives. This module owns: screen state machine
navigation, save/load, narration/backstory text assembly, and building the
context dict each ui/*.json screen renders against.
"""

import json
import math
import random
from pathlib import Path
from typing import Any
from game_data import (
    DAMAGE_PER_TOWN_YEAR, TOWN_JOB_OFFER_CHANCE, FORCED_RETIREMENT_AGE,
    TOWN_PROFESSIONS, TOWN_PROFESSION_MODIFIERS, TOWN_INJURIES, TOWN_BODY_PARTS,
    HERO_HOMETOWNS, HERO_FAMILY_MEMBERS, HERO_FAMILY_TRAITS, HERO_ASPIRATIONS,
    ORIGIN_STORY_CLOSERS,
    PRISON_CHANCE_CAP, PRISON_KARMA_SCALE,
    EQUIPMENT_SLOT_LABELS, HONORIFIC_TITLES, NEGATIVE_KARMA_TITLES,
    CHARACTER_TITLE_PARTS, LEG_VIBES, EVENT_NARRATION_TEMPLATES,
    RETIREMENT_DEATH_REASONS, HOUSES, PENSIONS,
    INVENTORY_ITEM_CAP,
    REPEAT_ENCOUNTER_TEMPLATES, ORIGIN_STORY_TEMPLATES, REMINISCENCE_TEMPLATES,
    REMINISCENCE_CHANCE, REMINISCENCE_ELIGIBLE_EVENTS, NARRATION_EVENT_SCREENS,
    LEGS, MONSTERS, CLASSES, DEATH_REASONS, DUNGEON_EXIT_REASONS,
    Dungeon, HonorificTitle, House, Item, Pension,
)
from game_engine import HeroAdventureEngine


class GameController:
    """UI-agnostic game flow controller - the single "brain" that drives
    screen-to-screen navigation and all interactive game logic.

    Both front-ends (the terminal `play.py` and the GUI `play_gui.py`) are
    thin renderers: they load the JSON screen definition named by
    `self.screen` from ui/, bind its text/lists against `get_context()`, and
    call `dispatch(action)` whenever the player picks an option. No game
    rules live in the front-ends - only presentation.
    """

    LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    SAVE_VERSION = 1
    SAVE_DIR: Path = Path(__file__).resolve().parent / "saves"

    def __init__(self) -> None:
        self.engine: HeroAdventureEngine | None = None
        self.screen: str = "front_page"
        self.pending_name: str = ""
        self.pending_class: str = ""
        self.creation_message: str = ""
        self.scores: list[dict] = []
        self.quit_requested: bool = False
        self.ctx: dict = {}
        self.previous_screen: str = "journey"
        self.inventory_return_screen: str = "journey"
        self.dungeon_pending: Dungeon | None = None
        self.trader_offer: list[Item] = []
        self.town_shop_offer: list[Item] = []
        self._save_slot_paths: list[Path] = []
        self.levelup_chosen: list[str] = []
        self.selected_item_letter: str | None = None
        self.current_narration: str = ""
        self.loot_discarded_indices: set[int] = set()
        self.failed_adventurer: bool = False
        # Instrumentation only (not persisted in saves): counts how many
        # times each narration template (category:index) has been chosen
        # this playthrough, so we can measure repetition - see
        # narrative_instrument.py.
        self.line_usage_counts: dict[str, int] = {}

    def _save_payload(self) -> dict:
        return {
            "version": self.SAVE_VERSION,
            "controller": {
                "screen": self.screen,
                "previous_screen": self.previous_screen,
                "ctx": self.ctx,
                "pending_name": self.pending_name,
                "pending_class": self.pending_class,
                "dungeon_pending": self.dungeon_pending,
                "trader_offer": self.trader_offer,
                "town_shop_offer": self.town_shop_offer,
                "levelup_chosen": self.levelup_chosen,
                "selected_item_letter": self.selected_item_letter,
                "current_narration": self.current_narration,
                "scores": self.scores,
                "failed_adventurer": self.failed_adventurer,
            },
            "engine": self.engine.__dict__ if self.engine else None,
        }

    def _restore_payload(self, payload: object) -> bool:
        if not isinstance(payload, dict):
            return False
        if payload.get("version") != self.SAVE_VERSION:
            return False
        engine_data = payload.get("engine")
        if not isinstance(engine_data, dict):
            return False

        hero_name = engine_data.get("hero_name", "Hero")
        hero_class = engine_data.get("hero_class", "Hitter")
        fast_mode = engine_data.get("fast_mode", True)
        engine = HeroAdventureEngine(hero_name, hero_class, fast_mode=fast_mode)
        for key, val in engine_data.items():
            setattr(engine, key, val)
        self.engine = engine

        controller_data = payload.get("controller", {})
        self.screen = controller_data.get("screen", "journey")
        self.previous_screen = controller_data.get("previous_screen", "journey")
        self.ctx = controller_data.get("ctx", {}) or {}
        self.pending_name = controller_data.get("pending_name", "")
        self.pending_class = controller_data.get("pending_class", "")
        self.dungeon_pending = controller_data.get("dungeon_pending")
        self.trader_offer = controller_data.get("trader_offer", []) or []
        self.town_shop_offer = controller_data.get("town_shop_offer", []) or []
        self.levelup_chosen = controller_data.get("levelup_chosen", []) or []
        self.selected_item_letter = controller_data.get("selected_item_letter")
        self.current_narration = controller_data.get("current_narration", "")
        self.scores = controller_data.get("scores", []) or []
        self.failed_adventurer = controller_data.get("failed_adventurer", False)

        if not self.screen:
            self.screen = "journey"
        if self.screen == "front_page":
            self.screen = "journey"
        return True

    def _set_menu_message(self, text) -> None:
        if self.screen == "front_page":
            self.ctx["menu_message"] = text

    def _set_save_message(self, text) -> None:
        if self.screen in ("journey", "inventory"):
            self.ctx["save_message"] = text

    def _build_leg_vibe(self) -> str | None:
        if not self.engine:
            return "the road"
        return LEG_VIBES.get(
            self.engine.current_leg_idx + 1,
            LEGS[self.engine.current_leg_idx]["name"].lower(),
        )

    @staticmethod
    def _ordinal(n) -> str:
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix: str = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def _choose_template(self, category, templates):
        """Picks a random template and records (category:index) usage for
        the line-reuse instrumentation (see narrative_instrument.py)."""
        idx: int = random.randrange(len(templates))
        key: str = f"{category}:{idx}"
        self.line_usage_counts[key] = self.line_usage_counts.get(key, 0) + 1
        return templates[idx]

    def _set_narration(self, event_type, **kwargs) -> str:
        encounter_count = kwargs.pop("encounter_count", None)
        if event_type == "fight" and encounter_count and encounter_count > 1:
            tier: int | str = encounter_count if encounter_count in (2, 3) else "many"
            templates: list[str] = REPEAT_ENCOUNTER_TEMPLATES[tier]
            data = {
                "hero_name": self.engine.hero_name if self.engine else "the Hero",
                "leg_vibe": self._build_leg_vibe(),
                "ordinal": self._ordinal(encounter_count),
                "monster_name_plural": f"{kwargs.get('monster_name', '')}s",
            }
            data.update(kwargs)
            self.current_narration: str = self._choose_template(f"repeat_encounter_{tier}", templates).format(**data)
            return self.current_narration
        templates: list[str] = EVENT_NARRATION_TEMPLATES.get(event_type, [])
        if not templates:
            self.current_narration: str = ""
            return ""
        data = {
            "hero_name": self.engine.hero_name if self.engine else "the Hero",
            "leg_vibe": self._build_leg_vibe(),
        }
        data.update(kwargs)
        self.current_narration: str = self._choose_template(f"event_{event_type}", templates).format(**data)
        self._maybe_add_reminiscence(event_type)
        return self.current_narration

    def _maybe_add_reminiscence(self, event_type) -> None:
        """With low probability, appends one extra sentence of "remember
        when..." flavor to the just-built narration, pulled from whichever
        of these the hero actually has: past town jobs, monsters faced 3+
        times, logged special moments, or their fixed backstory. Cheap by
        design - all sources are data already being tracked for other
        reasons, nothing new is generated here."""
        e: None | HeroAdventureEngine = self.engine
        if not e or event_type not in REMINISCENCE_ELIGIBLE_EVENTS:
            return
        if random.random() >= REMINISCENCE_CHANCE:
            return
        sources = []
        if e.town_history:
            sources.append("town_job")
        tallied: list[str] = [m for m, c in e.monster_encounter_counts.items() if c >= 3]
        if tallied:
            sources.append("monster_tally")
        if e.special_moments:
            sources.append("special_moment")
        if e.backstory:
            sources.append("backstory_family")
            sources.append("backstory_aspiration")
        if not sources:
            return
        source = random.choice(sources)
        data: dict[str, str] = {"hero_name": e.hero_name}
        if source == "town_job":
            data.update(random.choice(e.town_history))
            text: str = self._choose_template("reminiscence_town_job", REMINISCENCE_TEMPLATES["town_job"]).format(**data)
        elif source == "monster_tally":
            monster: str = random.choice(tallied)
            data.update({
                "monster_name": monster,
                "monster_name_plural": f"{monster}s",
                "ordinal": self._ordinal(e.monster_encounter_counts[monster]),
            })
            text: str = self._choose_template("reminiscence_monster_tally", REMINISCENCE_TEMPLATES["monster_tally"]).format(**data)
        elif source == "special_moment":
            moment = random.choice(e.special_moments)
            moment_type = moment["type"]
            templates: list[str] | None = REMINISCENCE_TEMPLATES.get(moment_type)
            if not templates:
                return
            data.update({k: v for k, v in moment.items() if k not in ("type", "leg")})
            if moment_type == "repeat_monster":
                data["monster_name_plural"] = f"{moment.get('monster_name', '')}s"
                data["ordinal"] = self._ordinal(moment.get("count", 3))
            text: str = self._choose_template(f"reminiscence_{moment_type}", templates).format(**data)
        else:
            data.update(e.backstory)
            text: str = self._choose_template(f"reminiscence_{source}", REMINISCENCE_TEMPLATES[source]).format(**data)
        self.current_narration: str = f"{self.current_narration} {text}".strip()

    def _generate_backstory(self) -> dict[str, str]:
        family_member: str = random.choice(HERO_FAMILY_MEMBERS)
        return {
            "hometown": random.choice(HERO_HOMETOWNS),
            "family_member": family_member,
            "family_article": "an" if family_member[:1].lower() in "aeiou" else "a",
            "family_trait": random.choice(HERO_FAMILY_TRAITS),
            "aspiration": random.choice(HERO_ASPIRATIONS),
        }

    def _build_origin_story(self) -> str:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        data: dict[str, str] = {"hero_name": e.hero_name}
        data.update(e.backstory)
        paragraph: str = self._choose_template("origin_story", ORIGIN_STORY_TEMPLATES).format(**data)
        closer: str = self._choose_template("origin_story_closer", ORIGIN_STORY_CLOSERS)
        return f"{paragraph} {closer}"

    # ------------------------------------------------------------------
    # Item letter helpers (DCSS-style lettered inventory, shared by the
    # inventory, item detail, and wandering trader "sell" screens)
    # ------------------------------------------------------------------
    def _letter_items(self):
        """Returns an ordered list of (letter, item, equipped_slot_or_None)."""
        assert self.engine is not None
        items = []
        idx = 0
        for slot, item in self.engine.equipment.items():
            if item and idx < len(self.LETTERS):
                items.append((self.LETTERS[idx], item, slot))
                idx += 1
        for item in self.engine.inventory:
            if idx < len(self.LETTERS):
                items.append((self.LETTERS[idx], item, None))
                idx += 1
        return items

    def _find_letter_item(self, letter):
        for let, item, slot in self._letter_items():
            if let == letter:
                return item, slot
        return None, None

    # ------------------------------------------------------------------
    # Context building - one dict of template variables + dynamic list rows
    # per screen, consumed by the JSON-driven renderers.
    # ------------------------------------------------------------------
    def get_context(self):
        ctx = {}
        e: None | HeroAdventureEngine = self.engine
        if e:
            skills, total_weight, max_weight = e.get_effective_skills()
            leg_info = LEGS[e.current_leg_idx]
            equipped_summary: str = ", ".join(item["name"] for item in e.equipment.values() if item) or "(none)"
            ctx.update({
                "hero_name": e.hero_name, "hero_class": e.hero_class,
                "hp": e.hp, "max_hp": e.max_hp, "cash": e.cash, "age": e.age,
                "leg": e.current_leg_idx + 1, "leg_name": leg_info["name"],
                "event": e.leg_event_count, "dungeons_found": e.dungeons_found_in_leg,
                "fighting": skills["fighting"], "defending": skills["defending"],
                "magic": skills["magic"], "stealth": skills["stealth"],
                "salvaging": skills["salvaging"], "speech": skills["speech"],
                "total_weight": total_weight, "max_weight": max_weight,
                "dungeon_name": e.dungeon_name, "dungeon_boss": e.dungeon_boss,
                "dungeon_event": e.dungeon_event_count, "dungeon_max": 6,
                "death_reason": e.death_reason or DEATH_REASONS["unknown"],
                "equipped_summary": equipped_summary,
                "inventory_count": len(e.inventory),
            })

        ctx.update(self.ctx)
        ctx["menu_message"] = ctx.get("menu_message", "")
        ctx["save_message"] = ctx.get("save_message", "")
        ctx["inventory_full_message"] = ctx.get("inventory_full_message", "")
        ctx["event_narration"] = self.current_narration if self.screen in NARRATION_EVENT_SCREENS else ""
        ctx["pending_name"] = self.pending_name
        ctx["pending_class"] = self.pending_class or "(none)"
        ctx["creation_message"] = self.creation_message
        ctx["levelup_count"] = len(self.levelup_chosen)
        ctx["load_available"] = self.SAVE_DIR.exists() and any(self.SAVE_DIR.glob("*.json"))
        ctx["failed_adventurer"] = self.failed_adventurer

        if self.screen == "inventory":
            assert e is not None
            ctx["list_inventory"] = self._build_inventory_rows()
            ctx["character_title"] = self._character_title()
            ctx["honor_mark"] = min(15, e.super_monsters_defeated + e.dungeons_cleared)
            ctx["karma"] = e.karma
            ctx["list_character_stats"] = self._build_character_stats_rows()
            ctx["list_character_equipment"] = self._build_character_equipment_rows()
        elif self.screen == "loot_screen":
            ctx["loot_lines"] = self._build_combat_loot_rows()
        elif self.screen == "item_detail":
            item, slot = self._find_letter_item(self.selected_item_letter)
            if item:
                stat: str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
                ctx.update({
                    "item_name": item["name"], "item_tier": item.get("tier", ""),
                    "item_stat": stat, "item_value": item["value"], "item_weight": item["weight"],
                    "item_uses": item.get("uses"), "item_slot": item.get("slot", ""),
                    "can_equip": slot is None, "can_unequip": slot is not None,
                })
        elif self.screen == "level_up":
            ctx["list_levelup_skills"] = self._build_levelup_rows()
            ctx["levelup_done"] = len(self.levelup_chosen) >= 3
        elif self.screen == "capital":
            ctx["list_houses"] = self._build_house_rows()
        elif self.screen == "high_scores":
            ctx["list_scores"] = self._build_score_rows()
        elif self.screen == "wandering_trader":
            ctx["list_trader_buy"] = self._build_trader_buy_rows()
            ctx["list_trader_sell"] = self._build_trader_sell_rows()
        elif self.screen == "town_recovery":
            ctx["list_town_buy"] = self._build_town_buy_rows()
            ctx["list_town_sell"] = self._build_town_sell_rows()
        elif self.screen == "combat_result":
            ctx["list_rounds"] = self.ctx.get("combat_rounds", [])
        elif self.screen == "combat" and e and ctx.get("monster_name"):
            action_risks = e.estimate_combat_action_risks(ctx["monster_name"])
            risk = action_risks["fight_profile"]
            ctx.update({
                "fight_risk_band": action_risks["fight"]["band"],
                "sneak_risk_band": action_risks["sneak"]["band"],
                "steal_risk_band": action_risks["steal"]["band"],
                "stealth_kill_risk_band": action_risks["stealth_kill"]["band"],
                "fight_win_pct": action_risks["fight"]["pct"],
                "sneak_win_pct": action_risks["sneak"]["pct"],
                "steal_win_pct": action_risks["steal"]["pct"],
                "stealth_kill_win_pct": action_risks["stealth_kill"]["pct"],
                "combat_attack": risk["player_attack"],
                "combat_effective_defense": risk["player_effective_defense"],
                "combat_round_damage": risk["player_round_damage"],
                "combat_incoming_damage": risk["monster_round_damage"],
                "combat_rounds_to_kill": risk["rounds_to_kill"],
                "combat_rounds_to_die": risk["rounds_to_die"],
            })

        return ctx

    def _item_highlight(self, item) -> None | str:
        """Returns 'better', 'worse', or None for a backpack item, comparing it
        only against the equipped item in the same slot that shares its skill
        effect (an empty slot always counts as 'better')."""
        assert self.engine is not None
        skill = item.get("skill")
        if not skill:
            return None
        target_slot = item.get("slot")
        if target_slot == "accessory":
            if not self.engine.equipment.get("accessory_1"):
                target_slot = "accessory_1"
            elif not self.engine.equipment.get("accessory_2"):
                target_slot = "accessory_2"
            else:
                target_slot = "accessory_1"
        equipped: Item | None = self.engine.equipment.get(target_slot)
        if not equipped:
            return "better"
        if equipped.get("skill") != skill:
            return None
        return "better" if item.get("skill_val", 0) > equipped.get("skill_val", 0) else "worse"

    # Grouping order/labels for the inventory list - items are broken into
    # slot sections (with a plain header row) so a full backpack is still
    # easy to scan while scrolling.
    INVENTORY_SLOT_GROUPS: list[tuple[str, str]] = [
        ("fighting_weapon", "Weapons"),
        ("defending_armor", "Armor"),
        ("salvaging_tool", "Salvaging Tools"),
        ("accessory", "Accessories"),
    ]

    def _build_inventory_rows(self):
        groups = {slot: [] for slot, _label in self.INVENTORY_SLOT_GROUPS}
        other = []
        for letter, item, slot in self._letter_items():
            tag: str = "\u2705 Equipped" if slot else "\U0001f392 Backpack"
            stat: str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            text: str = (f"{letter} - [{tag}] {item['name']} ({item.get('tier', '')}) "
                    f"{stat} | ${item['value']} | {item['weight']}wt")
            highlight: None | str = None if slot else self._item_highlight(item)
            row = {"text": text, "action": f"select_item:{letter}", "enabled": True, "highlight": highlight}
            groups.get(item.get("slot"), other).append(row)

        rows = []
        for slot, label in self.INVENTORY_SLOT_GROUPS:
            group_rows = groups[slot]
            if not group_rows:
                continue
            rows.append({"text": f"\u2500\u2500 {label} \u2500\u2500", "action": None, "enabled": False})
            rows.extend(group_rows)
        if other:
            rows.append({"text": "\u2500\u2500 Other \u2500\u2500", "action": None, "enabled": False})
            rows.extend(other)
        if not rows:
            rows.append({"text": "Your inventory is empty.", "action": None, "enabled": False})
        return rows

    def _build_combat_loot_rows(self):
        """Rows for the post-fight loot screen, letting the player toggle
        each drop between kept and discarded before it lands in the backpack."""
        items = self.ctx.get("loot_items") or []
        if not items:
            return [{"text": "No items dropped.", "action": None, "enabled": False}]
        rows = []
        for idx, item in enumerate(items):
            stat: str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            tag: str = "\u274c DISCARD" if idx in self.loot_discarded_indices else "\u2705 KEEP"
            text: str = (f"[{tag}] {item['name']} ({item.get('tier', '')}) {stat} | "
                    f"${item['value']} | {item['weight']}wt")
            rows.append({"text": text, "action": f"toggle_loot_item:{idx}", "enabled": True})
        return rows

    def _build_character_stats_rows(self):
        assert self.engine is not None
        skills, _, _ = self.engine.get_effective_skills()
        rows = []
        for skill in ("fighting", "defending", "magic", "stealth", "salvaging", "speech"):
            base: int = self.engine.base_skills.get(skill, 0)
            effective: int = skills.get(skill, base)
            delta: int = effective - base
            delta_text: str = f"+{delta}" if delta >= 0 else str(delta)
            rows.append({
                "text": f"{skill.title():<10}  Base: {base:<3}  Effective: {effective:<3}  Net: {delta_text}",
                "action": None,
                "enabled": False,
            })
        return rows

    def _build_character_equipment_rows(self):
        assert self.engine is not None
        rows = []
        for slot, item in self.engine.equipment.items():
            label: str = EQUIPMENT_SLOT_LABELS.get(slot, slot)
            if not item:
                rows.append({"text": f"{label}: (empty)", "action": None, "enabled": False})
                continue
            if item.get("skill"):
                bonus: str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}"
            else:
                bonus = "Relic effect"
            rows.append({
                "text": f"{label}: {item['name']} ({item.get('tier', '')}) {bonus} | {item['weight']}wt",
                "action": None,
                "enabled": False,
            })
        return rows

    def _leg_monster_cap(self, stat_name):
        assert self.engine is not None
        leg: int = self.engine.current_leg_idx + 1
        values = [data.get(stat_name, 0) for data in MONSTERS.values() if data.get("leg") == leg]
        return max(values) if values else 0

    def _band_for_title(self, value, cap) -> str:
        if cap <= 0:
            return "neutral"
        if value >= cap * 0.75:
            return "high"
        if value <= cap * 0.25:
            return "low"
        return "neutral"

    def _character_title(self) -> str:
        if not self.engine:
            return ""

        skills, _, _ = self.engine.get_effective_skills()
        fight_band: str = self._band_for_title(skills["fighting"], self._leg_monster_cap("fighting"))
        def_band: str = self._band_for_title(skills["defending"], self._leg_monster_cap("defending"))
        magic_band: str = self._band_for_title(skills["magic"], self._leg_monster_cap("magic"))
        sneak_band: str = self._band_for_title(skills["stealth"], self._leg_monster_cap("defending"))

        if magic_band == "high":
            attack_title: str = CHARACTER_TITLE_PARTS["magic_high"]
        elif magic_band == "low":
            attack_title: str = CHARACTER_TITLE_PARTS["magic_low"]
        elif sneak_band == "high":
            attack_title: str = CHARACTER_TITLE_PARTS["stealth_high"]
        elif sneak_band == "low":
            attack_title: str = CHARACTER_TITLE_PARTS["stealth_low"]
        elif fight_band == "high":
            attack_title: str = CHARACTER_TITLE_PARTS["fight_high"]
        elif fight_band == "low":
            attack_title: str = CHARACTER_TITLE_PARTS["fight_low"]
        else:
            attack_title: str = CHARACTER_TITLE_PARTS["balanced_attack"]

        defense_title: str = ""
        if def_band == "high":
            defense_title: str = CHARACTER_TITLE_PARTS["defense_high"]
        elif def_band == "low":
            defense_title: str = CHARACTER_TITLE_PARTS["defense_low"]

        core_parts = []
        if attack_title != CHARACTER_TITLE_PARTS["balanced_attack"]:
            core_parts.append(attack_title)
        if defense_title:
            core_parts.append(defense_title)
        if not core_parts:
            core_parts.append(CHARACTER_TITLE_PARTS["balanced_adventurer"])
        core_title: str = ", ".join(core_parts)

        honor_mark: int = min(15, self.engine.super_monsters_defeated + self.engine.dungeons_cleared)
        karma: int = self.engine.karma
        if karma < 0:
            karma_mark: int = min(15, (-karma) // 5)
            honor: HonorificTitle = NEGATIVE_KARMA_TITLES[karma_mark]
        else:
            honor: HonorificTitle = HONORIFIC_TITLES[honor_mark]
        if honor["placement"] == "prefix":
            if honor["text"] == "The unproven":
                return f"{honor['text']} {core_title}"
            return f"{honor['text']}, {core_title}"
        return f"{core_title}, {honor['text']}"

    def _build_levelup_rows(self):
        assert self.engine is not None
        rows = []
        for skill, val in self.engine.base_skills.items():
            chosen: bool = skill in self.levelup_chosen
            can_pick: bool = not chosen and len(self.levelup_chosen) < 3
            text: str = f"{skill.title()}: {val}" + (" [chosen]" if chosen else "")
            rows.append({"text": text, "action": f"pick_levelup_skill:{skill}" if can_pick else None,
                         "enabled": can_pick})
        return rows

    def _build_house_rows(self):
        assert self.engine is not None
        options, _pension = self.engine.get_house_options()
        rows = []
        for h in options:
            text: str = f"{h['name']} - ${h['cost']} (x{h['multiplier']})"
            if h["affordable"]:
                text += f" -> Score: {h['score']}"
            else:
                text += " (can't afford)"
            rows.append({"text": text, "action": f"buy_house:{h['name']}" if h["affordable"] else None,
                         "enabled": h["affordable"]})
        return rows

    @staticmethod
    def _life_span_band(cash) -> str:
        """Buckets retirement cash into short/medium/long based on where it
        falls within its matching PENSIONS band (bottom half = short, next
        quarter = medium, top quarter = long); cash above the top band is
        always long."""
        band: Pension | None = next((p for p in PENSIONS if p["min"] <= cash <= p["max"]), None)
        if band is None:
            return "long"
        span: int = band["max"] - band["min"]
        position = (cash - band["min"]) / span if span > 0 else 1.0
        if position < 0.5:
            return "short"
        if position < 0.75:
            return "medium"
        return "long"

    def _build_life_story(self, settled_phrase, pension, cash) -> str:
        """Epilogue sentence for the capital_result screen - a flash-forward
        past the game's ending, unrelated to in-journey combat deaths (see
        DEATH_REASONS). `settled_phrase` completes "The hero, {name}, ..."
        (e.g. "retired to a Palace", "retired early as a blacksmith")."""
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        span: str = self._life_span_band(cash)
        reason: str = random.choice(RETIREMENT_DEATH_REASONS)
        return (f"The hero, {e.hero_name}, {settled_phrase} with a pension of "
                f"${pension} and lived a {span} life before dying to {reason}.")

    def _build_score_rows(self):
        rows = []
        top = sorted(self.scores, key=lambda s: s.get("score", 0), reverse=True)[:10]
        for i, s in enumerate(top, 1):
            rows.append({"text": f"{i}. {s['name']} ({s['class']}) - {s['score']} pts ({s['result']})",
                         "action": None, "enabled": False})
        if not rows:
            rows.append({"text": "No scores yet. Be the first to forge your legend!", "action": None, "enabled": False})
        return rows


    def _build_trader_buy_rows(self):
        assert self.engine is not None
        mult: float = self.engine.trader_buy_multiplier()
        rows = []
        for idx, item in enumerate(self.trader_offer):
            cost = int(item["value"] * mult)
            affordable: bool = self.engine.cash >= cost
            text: str = f"{item['name']} ({item.get('tier', '')}) - ${cost}" + ("" if affordable else " (can't afford)")
            rows.append({"text": text, "action": f"trader_buy:{idx}" if affordable else None, "enabled": affordable})
        if not rows:
            rows.append({"text": "(Sold out)", "action": None, "enabled": False})
        return rows

    def _build_trader_sell_rows(self):
        assert self.engine is not None
        mult: float = self.engine.trader_sell_multiplier()
        rows = []
        for letter, item, slot in self._letter_items():
            if slot is None:
                price = int(item["value"] * mult)
                rows.append({"text": f"{letter} - {item['name']} - sell for ${price}",
                             "action": f"trader_sell:{letter}", "enabled": True})
        if not rows:
            rows.append({"text": "(Nothing in your backpack to sell)", "action": None, "enabled": False})
        return rows

    def _build_town_buy_rows(self):
        assert self.engine is not None
        mult: float = self.engine.trader_buy_multiplier()
        rows = []
        for idx, item in enumerate(self.town_shop_offer):
            cost = int(item["value"] * mult)
            affordable: bool = self.engine.cash >= cost
            text: str = f"{item['name']} ({item.get('tier', '')}) - ${cost}" + ("" if affordable else " (can't afford)")
            rows.append({"text": text, "action": f"town_buy:{idx}" if affordable else None, "enabled": affordable})
        if not rows:
            rows.append({"text": "(Sold out)", "action": None, "enabled": False})
        return rows

    def _build_town_sell_rows(self):
        assert self.engine is not None
        mult: float = self.engine.trader_sell_multiplier()
        rows = []
        for letter, item, slot in self._letter_items():
            if slot is None:
                price = int(item["value"] * mult)
                rows.append({"text": f"{letter} - {item['name']} - sell for ${price}",
                             "action": f"town_sell:{letter}", "enabled": True})
        if not rows:
            rows.append({"text": "(Nothing in your backpack to sell)", "action": None, "enabled": False})
        return rows

    def _format_loot_lines(self, items):
        """Formats a list of raw item dicts (already granted by the engine)
        into display-only row dicts for the loot / magic shrine screens."""
        lines = []
        for item in items:
            stat: str = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            text: str = f"{item['name']} ({item.get('tier', '')}) {stat} | ${item['value']} | {item['weight']}wt"
            lines.append({"text": text, "action": None, "enabled": False})
        if not lines:
            lines.append({"text": "No items dropped.", "action": None, "enabled": False})
        return lines

    def _format_combat_rounds(self, round_details, fallback_lines):
        rows = []
        outcome_labels: dict[str, str] = {
            "hit": "HIT",
            "loss": "LOSS",
            "attrition": "ATTRITION",
            "escape": "ESCAPE",
        }
        for detail in round_details:
            facts = []
            if detail.get("damage_dealt"):
                facts.append(f"dealt {detail['damage_dealt']}")
            if detail.get("damage_taken"):
                facts.append(f"took {detail['damage_taken']}")
            if detail.get("hero_hp") is not None:
                facts.append(f"hero HP {detail['hero_hp']}")
            if detail.get("monster_hp") is not None:
                facts.append(f"enemy HP {detail['monster_hp']}")
            facts_text: str = f" ({'; '.join(facts)})" if facts else ""
            label: str = outcome_labels.get(detail.get("outcome"), "EVENT")
            rows.append({
                "text": (
                    f"R{detail['round']} {label}: "
                    f"{detail.get('text', '')}{facts_text}"
                ),
                "action": None,
                "enabled": False,
                "outcome": detail.get("outcome"),
            })
        if rows:
            return rows
        return [
            {
                "text": f"R{index}: {line}",
                "action": None,
                "enabled": False,
            }
            for index, line in enumerate(fallback_lines, start=1)
        ]

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------
    def dispatch(self, action: str) -> None:
        if not action:
            return
        verb: str
        arg: str | None
        if ":" in action:
            verb, arg = action.split(":", 1)
        else:
            verb, arg = action, None

        if verb == "goto" and arg is not None:
            self.screen = arg
            return

        handler: Any | None = getattr(self, f"_action_{verb}", None)
        if handler is None:
            return  # unknown action - ignore defensively rather than crash
        if arg is not None:
            handler(arg)
        else:
            handler()

    def set_pending_name(self, name: str) -> None:
        self.pending_name = (name or "").strip()

    # -- Front page / character creation --------------------------------
    def _action_new_game(self) -> None:
        self.pending_name: str = ""
        self.pending_class: str = ""
        self.creation_message: str = ""
        self.engine = None
        self.ctx = {}
        self.current_narration: str = ""
        self.screen = "character_creation"

    def _action_select_class(self, class_name) -> None:
        if class_name not in CLASSES:
            return
        self.pending_class = class_name
        self._action_confirm_character()

    def _action_confirm_character(self) -> None:
        if not self.pending_name or not self.pending_class:
            return
        if self._save_name_exists(self.pending_name):
            self.creation_message: str = (
                f"A save already exists for '{self.pending_name}'. "
                "Choose a different name or load that save instead."
            )
            return
        self.creation_message: str = ""
        self.engine = HeroAdventureEngine(self.pending_name, self.pending_class)
        self.engine.backstory = self._generate_backstory()
        self.line_usage_counts = {}
        self.current_narration: str = self._build_origin_story()
        self.screen = "origin_story"

    def _action_origin_continue(self) -> None:
        self.ctx = {}
        self.current_narration: str = ""
        self.screen = "journey"

    def _action_quit(self) -> None:
        self.quit_requested = True

    @staticmethod
    def _slot_filename(hero_name) -> str:
        safe: str = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in hero_name.strip())
        return safe or "hero"

    def _save_slot_path(self, hero_name) -> Path:
        return self.SAVE_DIR / f"{self._slot_filename(hero_name)}.json"

    def _save_name_exists(self, hero_name) -> bool:
        return self._save_slot_path(hero_name).exists()

    def _save_summary(self, payload):
        if not isinstance(payload, dict) or payload.get("version") != self.SAVE_VERSION:
            return None
        engine_data = payload.get("engine")
        if not engine_data:
            return None
        return {
            "hero_name": engine_data.get("hero_name", "Unknown"),
            "hero_class": engine_data.get("hero_class", "Unknown"),
            "leg": engine_data.get("current_leg_idx", 0) + 1,
            "event": engine_data.get("leg_event_count", 0),
        }

    def _list_save_slots(self):
        """Returns ordered (path, summary) pairs for every valid save file."""
        slots = []
        if not self.SAVE_DIR.exists():
            return slots
        for path in sorted(self.SAVE_DIR.glob("*.json")):
            try:
                payload = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            summary = self._save_summary(payload)
            if summary:
                slots.append((path, summary))
        return slots

    def _action_view_load_game(self) -> None:
        slots = self._list_save_slots()
        if not slots:
            self._set_menu_message("No valid save file was found.")
            return
        self._save_slot_paths = [path for path, _ in slots]
        rows = [
            {
                "text": f"Leg {summary['leg']} - Event {summary['event']} - Hero: {summary['hero_name']}",
                "action": f"load_slot:{idx}",
                "enabled": True,
            }
            for idx, (_, summary) in enumerate(slots)
        ]
        self.ctx = {"list_save_slots": rows}
        self.screen = "load_game"

    def _action_load_slot(self, idx_str) -> None:
        try:
            idx = int(idx_str)
        except (TypeError, ValueError):
            return
        if not (0 <= idx < len(self._save_slot_paths)):
            return
        try:
            payload = json.loads(self._save_slot_paths[idx].read_text())
        except (OSError, json.JSONDecodeError):
            self.ctx = {"menu_message": "Save file is invalid or incompatible."}
            self.screen = "front_page"
            return

        if self._restore_payload(payload):
            self._set_save_message("Game loaded.")
        else:
            self.engine = None
            self.screen = "front_page"
            self.ctx = {"menu_message": "Save file is invalid or incompatible."}

    def _action_save_game(self) -> None:
        if not self.engine:
            self._set_menu_message("Start or load a game before saving.")
            return
        try:
            self.SAVE_DIR.mkdir(exist_ok=True)
            payload = self._save_payload()
            path: Path = self._save_slot_path(self.engine.hero_name)
            tmp_path: Path = path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, separators=(",", ":")))
            tmp_path.replace(path)
            self._set_save_message(f"Game saved to {path.name}.")
        except OSError:
            self._set_save_message("Failed to save game.")

    def _action_save_and_quit(self) -> None:
        self._action_save_game()
        self.ctx = {}
        self.screen = "front_page"

    # -- Inventory (openable from journey/combat, returns to prior screen) --
    def _action_open_inventory(self) -> None:
        origin = self.screen if self.screen != "inventory" else (self.inventory_return_screen or "journey")
        self.previous_screen = origin
        self.inventory_return_screen = origin
        self.screen = "inventory"

    def _action_close_inventory(self) -> None:
        target = self.inventory_return_screen or self.previous_screen or "journey"
        if target == "inventory":
            target = "journey"
        self.screen = target

    def _action_select_item(self, letter) -> None:
        self.selected_item_letter = letter
        self.screen = "item_detail"

    def _action_item_back(self) -> None:
        self.selected_item_letter = None
        self.screen = "inventory"

    def _action_equip_item(self) -> None:
        assert self.engine is not None
        letter = self.selected_item_letter
        item, slot = self._find_letter_item(letter)
        if not item or slot is not None:
            return
        target_slot = item.get("slot")
        if target_slot == "accessory":
            if not self.engine.equipment["accessory_1"]:
                target_slot = "accessory_1"
            elif not self.engine.equipment["accessory_2"]:
                target_slot = "accessory_2"
            else:
                target_slot = "accessory_1"
        if item in self.engine.inventory:
            self.engine.inventory.remove(item)
        old: Item | None = self.engine.equipment.get(target_slot)
        if old:
            self.engine.inventory.append(old)
        self.engine.equipment[target_slot] = item
        self.screen = "inventory"
        self.selected_item_letter = None

    def _action_unequip_item(self) -> None:
        assert self.engine is not None
        letter = self.selected_item_letter
        item, slot = self._find_letter_item(letter)
        if item and slot is not None:
            self.engine.equipment[slot] = None
            self.engine.inventory.append(item)
        self.screen = "inventory"
        self.selected_item_letter = None

    def _action_drop_item(self) -> None:
        assert self.engine is not None
        letter = self.selected_item_letter
        item, slot = self._find_letter_item(letter)
        if item:
            if slot is not None:
                self.engine.equipment[slot] = None
            elif item in self.engine.inventory:
                self.engine.inventory.remove(item)
        self.screen = "inventory"
        self.selected_item_letter = None

    # -- Journey ----------------------------------------------------------
    def _action_advance_event(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        if len(e.inventory) > INVENTORY_ITEM_CAP:
            self.ctx["inventory_full_message"] = (
                f"Your pack is overflowing ({len(e.inventory)}/{INVENTORY_ITEM_CAP}). "
                "Sell or drop items before continuing."
            )
            return
        e.leg_event_count += 1

        dungeon: None | Dungeon = e.try_spot_dungeon()
        if dungeon:
            self.dungeon_pending = dungeon
            self._set_narration("dungeon_found", dungeon_name=dungeon["name"])
            self.ctx = {
                "dungeon_name": dungeon["name"],
                "dungeon_boss": dungeon["boss"],
                "event_narration": self.current_narration,
            }
            self.screen = "dungeon_found"
            return

        transition: None | str = e.try_leg_transition()
        if transition == "LEVEL_UP":
            self._enter_town_recovery()
            return
        elif transition == "CAPITAL":
            e.sell_all_for_capital()
            self.failed_adventurer = False
            self.ctx = {}
            self.screen = "capital"
            return

        event_type: str = e.roll_journey_event_type()
        if event_type == "SUPER_MONSTER":
            sm_name = LEGS[e.current_leg_idx]["super_monster"]
            m = MONSTERS[sm_name]
            self._set_narration("super_monster")
            self.ctx = {"monster_name": sm_name, "monster_fighting": m["fighting"],
                        "monster_defending": m["defending"], "monster_magic": m["magic"],
                        "event_narration": self.current_narration}
            self.screen = "super_monster_preview"
        elif event_type == "MAGIC_SHRINE":
            result = e.resolve_magic_shrine()
            self._set_narration("magic_shrine")
            self.ctx = {"loot_cash": result["cash_gained"], "loot_items": result["new_items"],
                        "loot_lines": self._format_loot_lines(result["new_items"]),
                        "event_narration": self.current_narration}
            self.screen = "magic_shrine_event"
        elif event_type == "WANDERING_TRADER":
            self.trader_offer = e.generate_trader_offer()
            self._set_narration("wandering_trader")
            self.ctx = {"event_narration": self.current_narration}
            self.screen = "wandering_trader"
        elif event_type == "WANDER_GROUP":
            self._set_narration("wander_group")
            e.apply_wander_group_advance(5)
            transition: None | str = e.try_leg_transition()
            if transition == "LEVEL_UP":
                self._enter_town_recovery()
                return
            elif transition == "CAPITAL":
                e.sell_all_for_capital()
                self.failed_adventurer = False
                self.ctx = {}
                self.screen = "capital"
                return
            self._go_to_journey("The wander group helped you cover extra ground.")
        elif event_type == "FAIRY_FOUND":
            self._set_narration("fairy_found")
            e.capture_fairy()
            self._go_to_journey("You captured a fairy!")
        else:
            monster: str = e.get_random_monster()
            e.monster_encounter_counts[monster] = e.monster_encounter_counts.get(monster, 0) + 1
            count: int = e.monster_encounter_counts[monster]
            if count == 3:
                e.log_special_moment("repeat_monster", monster_name=monster, count=count)
            self._set_narration("fight", monster_name=monster, encounter_count=count)
            self._start_combat(monster, "regular", allow_run=True)

    # -- Town Recovery (aging) ------------------------------------------
    def _generate_town_blurb(self, job_offer=False) -> tuple[str, str]:
        assert self.engine is not None
        profession: str = random.choice(TOWN_PROFESSIONS)
        modifier: str = random.choice(TOWN_PROFESSION_MODIFIERS)
        injury: str = random.choice(TOWN_INJURIES)
        body_part: str = random.choice(TOWN_BODY_PARTS)
        event_type: str = "town_job_offer" if job_offer else "town_recovery"
        blurb: str = self._set_narration(
            event_type, profession=profession, modifier=modifier,
            injury=injury, body_part=body_part,
        )
        self.engine.town_history.append({
            "profession": profession, "modifier": modifier,
            "injury": injury, "body_part": body_part, "age": self.engine.age,
        })
        self.engine.town_history = self.engine.town_history[-10:]
        return blurb, profession

    def _enter_town_recovery(self) -> None:
        """Mandatory town stop at the start of a new leg. Skipped entirely
        if the hero is already at full HP; otherwise plays out one year at
        a time (10 HP healed per year, hero ages by 1), with a per-year
        5% chance of a permanent job offer and a forced failed-adventurer
        ending if age 50 is reached."""
        assert self.engine is not None
        if self.engine.hp >= self.engine.max_hp:
            self._enter_level_up()
            return
        self.town_shop_offer = self.engine.generate_trader_offer()
        self._prepare_town_year()

    def _enter_level_up(self) -> None:
        self.levelup_chosen = []
        self.ctx = {}
        self.screen = "level_up"

    def _prison_chance(self) -> float:
        """Odds of a town-recovery year being spent in jail instead of
        working, curved on negative karma: 0 while karma is neutral/positive,
        then climbing steeply and asymptotically toward (never reaching)
        PRISON_CHANCE_CAP as karma gets more negative."""
        karma: int = self.engine.karma if self.engine else 0
        if karma >= 0:
            return 0.0
        magnitude: int = -karma
        return PRISON_CHANCE_CAP * (1 - math.exp(-magnitude / PRISON_KARMA_SCALE))

    def _prepare_town_year(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        if random.random() < self._prison_chance():
            blurb: str = self._set_narration("town_prison")
            e.age += 1
            e.log("TOWN_PRISON_YEAR", {"age": e.age, "karma": e.karma})
            if e.age >= FORCED_RETIREMENT_AGE:
                self._enter_failed_adventurer(blurb)
                return
            self.ctx = {"town_job_offer": False, "town_prison": True,
                        "town_fully_healed": False, "event_narration": blurb}
            self.screen = "town_recovery"
            return

        if random.random() < TOWN_JOB_OFFER_CHANCE:
            blurb, profession = self._generate_town_blurb(job_offer=True)
            self.ctx = {"town_job_offer": True, "town_profession": profession,
                        "event_narration": blurb}
            self.screen = "town_recovery"
            return

        blurb, _ = self._generate_town_blurb(job_offer=False)
        heal: int = min(DAMAGE_PER_TOWN_YEAR, e.max_hp - e.hp)
        e.hp = min(e.max_hp, e.hp + heal)
        e.age += 1
        e.log("TOWN_RECOVERY_YEAR", {"age": e.age, "heal": heal, "hp": e.hp})
        if e.age >= FORCED_RETIREMENT_AGE:
            self._enter_failed_adventurer(blurb)
            return
        self.ctx = {"town_job_offer": False, "town_fully_healed": e.hp >= e.max_hp,
                     "event_narration": blurb}
        self.screen = "town_recovery"

    def _enter_failed_adventurer(self, blurb) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        e.sell_all_for_capital()
        self.failed_adventurer = True
        self.ctx = {"failed_adventurer_text": blurb}
        self.screen = "capital"

    def _action_town_work(self) -> None:
        if self.ctx.get("town_job_offer"):
            return
        self._prepare_town_year()

    def _action_town_buy(self, idx_str) -> None:
        assert self.engine is not None
        idx = int(idx_str)
        if 0 <= idx < len(self.town_shop_offer):
            item = self.town_shop_offer[idx]
            if self.engine.trader_buy(item):
                self.town_shop_offer.pop(idx)

    def _action_town_sell(self, letter) -> None:
        assert self.engine is not None
        item, slot = self._find_letter_item(letter)
        if item and slot is None:
            self.engine.trader_sell(item)

    def _action_town_leave(self) -> None:
        self.town_shop_offer = []
        self.ctx = {}
        self._enter_level_up()

    def _action_town_retire(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        profession = self.ctx.get("town_profession", "adventurer")
        e.sell_all_for_capital()
        pension: int = e.get_pension()
        result: str = f"Retired early as a {profession}"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": pension, "result": result})
        self.town_shop_offer = []
        self.ctx = {"final_house": result, "final_score": pension, "final_pension": pension,
                    "life_story": self._build_life_story(f"retired early as a {profession}", pension, e.cash)}
        self.screen = "capital_result"

    def _go_to_journey(self, outcome_text="") -> None:
        """Returns to the journey screen carrying a one-shot outcome summary
        (rendered in green) so completing an event doesn't look identical
        to a brand-new one. The next _action_advance_event() call replaces
        self.ctx wholesale, so this text naturally disappears."""
        self.ctx = {"last_outcome_text": outcome_text}
        self.screen = "journey"
        # Force-save after every completed event so progress is never lost.
        self._action_save_game()

    def _action_continue_journey(self) -> None:
        self._go_to_journey()

    def _action_magic_shrine_continue(self) -> None:
        cash = self.ctx.get("loot_cash", 0)
        items = self.ctx.get("loot_items") or []
        item_part: str = f" and {len(items)} item(s)" if items else ""
        self._go_to_journey(f"The shrine granted you ${cash}{item_part}.")

    # -- Super monster ------------------------------------------------------
    def _action_fight_super_monster(self) -> None:
        sm_name = self.ctx.get("monster_name")
        if sm_name:
            self._set_narration("super_monster", monster_name=sm_name)
        self._start_combat(sm_name, "super_monster", allow_run=False)

    def _action_ignore_super_monster(self) -> None:
        self._go_to_journey("You avoid the super monster and continue on your way.")

    # -- Dungeons -------------------------------------------------------
    def _action_enter_dungeon(self) -> None:
        assert self.engine is not None
        self.engine.enter_dungeon(self.dungeon_pending)
        self.dungeon_pending = None
        self._enter_dungeon_floor_preview()

    def _action_ignore_dungeon(self) -> None:
        self.dungeon_pending = None
        self._go_to_journey("You leave the dungeon entrance undisturbed.")

    def _enter_dungeon_floor_preview(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        monster_name: str = e.get_dungeon_floor_monster()
        m = MONSTERS[monster_name]
        is_boss: bool = e.dungeon_event_count >= 5
        self._set_narration(
            "dungeon_boss" if is_boss else "dungeon_floor",
            dungeon_name=e.dungeon_name,
            floor_number=min(e.dungeon_event_count + 1, 5),
            monster_name=monster_name,
        )
        self.ctx = {
            "floor_monster": monster_name, "floor_number": min(e.dungeon_event_count + 1, 5),
            "monster_fighting": m["fighting"], "monster_defending": m["defending"], "monster_magic": m["magic"],
            "is_boss": is_boss,
            "event_narration": self.current_narration,
        }
        self.screen: str = "dungeon_boss_preview" if is_boss else "dungeon_floor_preview"

    def _action_engage_floor(self) -> None:
        is_boss = self.ctx.get("is_boss", False)
        monster = self.ctx.get("floor_monster")
        self._start_combat(monster, "dungeon_boss" if is_boss else "dungeon_floor", allow_run=False)

    def _action_exit_dungeon(self) -> None:
        assert self.engine is not None
        self.engine.leave_dungeon(DUNGEON_EXIT_REASONS["voluntary"])
        self._go_to_journey("You retreat from the dungeon.")

    def _dungeon_victory(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        treasure: int = random.randint(200, 500)
        e.cash += treasure
        e.leave_dungeon(DUNGEON_EXIT_REASONS["boss_defeated"])
        self.ctx = {"treasure": treasure}
        self.screen = "dungeon_victory"

    def _action_dungeon_victory_continue(self) -> None:
        treasure = self.ctx.get("treasure", 0)
        self._go_to_journey(f"You cleared the dungeon and found ${treasure} in treasure!")

    # -- Wandering trader -----------------------------------------------
    def _action_trader_buy(self, idx_str) -> None:
        assert self.engine is not None
        idx = int(idx_str)
        if 0 <= idx < len(self.trader_offer):
            item = self.trader_offer[idx]
            if self.engine.trader_buy(item):
                self.trader_offer.pop(idx)

    def _action_trader_sell(self, letter) -> None:
        assert self.engine is not None
        item, slot = self._find_letter_item(letter)
        if item and slot is None:
            self.engine.trader_sell(item)

    def _action_leave_trader(self) -> None:
        self.trader_offer = []
        self._go_to_journey("You part ways with the wandering trader.")

    # -- Level up ---------------------------------------------------------
    def _action_pick_levelup_skill(self, skill) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        if skill in e.base_skills and skill not in self.levelup_chosen and len(self.levelup_chosen) < 3:
            e.apply_level_up(skill)
            self.levelup_chosen.append(skill)

    def _action_levelup_continue(self) -> None:
        assert self.engine is not None
        if len(self.levelup_chosen) < 3:
            return
        self.engine.advance_to_next_leg()
        self.levelup_chosen = []
        self._go_to_journey("You finish training and set out for the next leg.")

    # -- Combat -----------------------------------------------------------
    def _start_combat(self, monster_name, kind, allow_run=True) -> None:
        assert self.engine is not None
        m = MONSTERS[monster_name]
        if not self.current_narration:
            event_type: str = "dungeon_boss" if kind == "dungeon_boss" else "dungeon_floor" if kind == "dungeon_floor" else "fight"
            self._set_narration(
                event_type,
                monster_name=monster_name,
                dungeon_name=self.engine.dungeon_name if self.engine else "",
                floor_number=(self.engine.dungeon_event_count + 1) if self.engine else "",
            )
        self.ctx = {
            "monster_name": monster_name,
            "monster_fighting": m["fighting"], "monster_defending": m["defending"], "monster_magic": m["magic"],
            "combat_kind": kind, "allow_run": allow_run,
            "has_throwable_item": bool(self.engine.pick_throwable_item()),
            "event_narration": self.current_narration,
        }
        self.screen = "combat"

    def _action_fight(self) -> None:
        self._resolve_combat_choice("fight")

    def _action_sneak(self) -> None:
        self._resolve_combat_choice("sneak")

    def _action_steal(self) -> None:
        self._resolve_combat_choice("steal")

    def _action_stealth_kill(self) -> None:
        self._resolve_combat_choice("stealth_kill")

    def _action_throw_item(self) -> None:
        self._resolve_combat_choice("throw_item")

    def _action_run_away(self) -> None:
        monster = self.ctx.get("monster_name", "the monster")
        self._go_to_journey(f"You run from {monster} and hurry back to the road.")

    def _resolve_combat_choice(self, choice) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        monster = self.ctx["monster_name"]
        kind = self.ctx.get("combat_kind", "regular")
        before_hp: int = e.hp
        before_cash: int = e.cash
        before_len: int = len(e.inventory)

        res: str | None = e.resolve_fight(monster, choice=choice, encounter_type=kind)
        combat_summary = e.last_combat_summary
        rounds_text: str = ""
        if combat_summary.get("rounds"):
            rounds_text: str = f" ({combat_summary['rounds']} rounds)"
        combat_lines = combat_summary.get("round_texts", [])
        combat_rounds = self._format_combat_rounds(
            combat_summary.get("round_details", []),
            combat_lines,
        )

        if res == "JOURNEY":
            if combat_summary.get("mode") == "throw_item":
                self.ctx["result_text"] = f"{combat_lines[0] if combat_lines else 'You escape, but lose an item and any loot.'}"
            else:
                self.ctx["result_text"] = f"You slip past {monster} without a fight!"
            self.ctx["result_won"] = True
            self.ctx["loot_items"] = []
        elif res == "LOSS_WINDOW":
            damage: int = before_hp - e.hp
            self.ctx["result_text"] = f"You were bested by {monster}{rounds_text}! You take {damage} damage."
            self.ctx["result_won"] = False
            self.ctx["damage"] = damage
            if kind in ("dungeon_floor", "dungeon_boss"):
                e.leave_dungeon(DUNGEON_EXIT_REASONS["combat_defeat"])
        else:
            cash_gained: int = e.cash - before_cash
            new_items: list[Item] = e.inventory[before_len:]
            self.ctx["result_text"] = f"Victory! You defeat {monster}{rounds_text}."
            self.ctx["result_won"] = True
            self.ctx["loot_cash"] = cash_gained
            self.ctx["loot_items"] = new_items
            self.ctx["loot_lines"] = self._format_loot_lines(new_items)

        self.ctx["combat_rounds"] = combat_rounds

        self.screen: str = "death" if e.game_over else "combat_result"

    def _action_combat_continue(self) -> None:
        if not self.ctx.get("result_won"):
            self._go_to_journey(self.ctx.get("result_text", ""))
            return
        if self.ctx.get("loot_items"):
            self.loot_discarded_indices = set()
            self.screen = "loot_screen"
        else:
            self._route_after_win()

    def _action_toggle_loot_item(self, idx_str) -> None:
        try:
            idx = int(idx_str)
        except (TypeError, ValueError):
            return
        if idx in self.loot_discarded_indices:
            self.loot_discarded_indices.discard(idx)
        else:
            self.loot_discarded_indices.add(idx)

    def _action_loot_continue(self) -> None:
        assert self.engine is not None
        items = self.ctx.get("loot_items") or []
        discarded = [item for idx, item in enumerate(items) if idx in self.loot_discarded_indices]
        if discarded:
            self.engine.inventory = [it for it in self.engine.inventory if not any(it is d for d in discarded)]
        self.loot_discarded_indices = set()
        self._route_after_win()

    def _route_after_win(self) -> None:
        assert self.engine is not None
        kind = self.ctx.get("combat_kind", "regular")
        if kind == "dungeon_floor":
            self.engine.advance_dungeon_floor()
            self._enter_dungeon_floor_preview()
        elif kind == "dungeon_boss":
            self._dungeon_victory()
        else:
            self._go_to_journey(self.ctx.get("result_text", ""))

    # -- Death / Capital ----------------------------------------------------
    def _action_death_continue(self) -> None:
        self.engine = None
        self.ctx = {}
        self.screen = "front_page"

    def _action_buy_house(self, house_name) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        house: House | None = next((h for h in HOUSES if h["name"] == house_name), None)
        if not house or e.cash < house["cost"]:
            return
        pension: int = e.get_pension()
        e.cash -= house["cost"]
        score: int = house["multiplier"] * pension
        result: str = f"Bought {house['name']}"
        if self.failed_adventurer:
            score: int = round(score * 0.25)
            result += " (Failed Adventurer)"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": score,
                             "result": result})
        self.ctx = {"final_house": house["name"], "final_score": score, "final_pension": pension,
                    "life_story": self._build_life_story(f"retired to a {house['name']}", pension, e.cash + house["cost"])}
        self.failed_adventurer = False
        self.screen = "capital_result"

    def _action_keep_pension(self) -> None:
        e: None | HeroAdventureEngine = self.engine
        assert e is not None
        pension: int = e.get_pension()
        score: int = pension
        result = "Tavern"
        if self.failed_adventurer:
            score: int = round(score * 0.25)
            result += " (Failed Adventurer)"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": score, "result": result})
        self.ctx = {"final_house": "Tavern", "final_score": score, "final_pension": pension,
                    "life_story": self._build_life_story("retired to a room at the Tavern", pension, e.cash)}
        self.failed_adventurer = False
        self.screen = "capital_result"

    def _action_capital_continue(self) -> None:
        if self.engine:
            path: Path = self._save_slot_path(self.engine.hero_name)
            if path.exists():
                path.unlink()
        self.engine = None
        self.ctx = {}
        self.screen = "front_page"
