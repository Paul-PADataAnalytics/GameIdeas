"""
Core Game Engine for Hero Adventure
Implements state machine, item inventory management, combat/stealth/steal checks,
weight penalties, dungeon management, and fast zero-delay simulation API.
"""

import json
import math
import random
from pathlib import Path
from game_data import (
    CLASSES, LEGS, MONSTERS, ITEM_CATEGORIES, QUALITY_TIERS,
    RELICS, HOUSES, PENSIONS,
    AGE_START, DAMAGE_PER_TOWN_YEAR, TOWN_JOB_OFFER_CHANCE, FORCED_RETIREMENT_AGE,
    PENSION_END_AGE_MIN, PENSION_END_AGE_MAX, PENSION_BASELINE_YEARS,
    TOWN_PROFESSIONS, TOWN_PROFESSION_MODIFIERS, TOWN_INJURIES, TOWN_BODY_PARTS,
    RELIC_MONSTER_SCALE,
    HERO_HOMETOWNS, HERO_FAMILY_MEMBERS, HERO_FAMILY_TRAITS, HERO_ASPIRATIONS,
    ORIGIN_STORY_CLOSERS,
    KARMA_STEALTH_KILL_PENALTY, KARMA_STEAL_PENALTY,
    PRISON_CHANCE_CAP, PRISON_KARMA_SCALE,
    EQUIPMENT_SLOT_LABELS, HONORIFIC_TITLES, NEGATIVE_KARMA_TITLES,
    CHARACTER_TITLE_PARTS, LEG_VIBES, EVENT_NARRATION_TEMPLATES,
    OUTCOME_TEXT, DEATH_REASONS, DUNGEON_EXIT_REASONS, RISK_BANDS,
    MAGIC_SPELL_NAME_PARTS, MAGIC_SHIELD_NAME_PARTS, COMBAT_LINE_POOLS,
    INVENTORY_ITEM_CAP, BOSS_BONUS_TIER_BY_LEG,
)


def _build_dungeon_monster_name_set():
    names = set()
    for leg in LEGS:
        for dungeon in leg.get("dungeons", []):
            boss = dungeon.get("boss")
            if boss:
                names.add(boss)
            for floor_monster in dungeon.get("floors", []):
                names.add(floor_monster)
    return names


DUNGEON_MONSTER_NAMES = _build_dungeon_monster_name_set()
SUPER_MONSTER_NAMES = {leg["super_monster"] for leg in LEGS if leg.get("super_monster")}


class HeroAdventureEngine:
    def __init__(self, hero_name="Hero", hero_class="Hitter", fast_mode=True, relic_scaling_enabled=False,
                 stealth_atk_enabled=True, hider_stat_bonus_enabled=True, throw_item_enabled=True):
        self.fast_mode = fast_mode
        self.hero_name = hero_name
        self.hero_class = hero_class
        self.skip_journey_fights = False
        # Experimental toggle: scale relic-flagged monsters (bosses/super
        # monsters) independently of regular per-leg monster tuning.
        self.relic_scaling_enabled = relic_scaling_enabled
        # Balance-experiment toggles (all default on; kept togglable purely
        # so sim_runner.py can A/B-test each change in isolation).
        self.stealth_atk_enabled = stealth_atk_enabled
        self.throw_item_enabled = throw_item_enabled
        
        # Base Skills (all start at 5)
        self.base_skills = {
            "fighting": 5, "defending": 5, "magic": 5, "stealth": 5,
            "salvaging": 5, "spotting": 5, "camping": 5, "medical": 5
        }
        
        # Apply initial class boosts (+20 to 3 skills)
        if hero_class in CLASSES:
            for skill, boost in CLASSES[hero_class].items():
                self.base_skills[skill] += boost
        # Hider's small fighting/defending floor bump (see CLASSES in
        # game_data.py) can be disabled in isolation for balance testing.
        if hero_class == "Hider" and not hider_stat_bonus_enabled:
            self.base_skills["fighting"] -= 7
            self.base_skills["defending"] -= 7

        self.hp = 100
        self.max_hp = 100
        self.cash = 0
        self.age = AGE_START
        self.end_age = None  # rolled once (lazily, in get_pension) between 60-90
        # Reputation tracker: starts neutral, only ever decreases (see
        # resolve_fight's stealth_kill/steal branches). Negative karma
        # swaps the hero's title for a villainous one and risks a year in
        # jail during town recovery (see GameController._prison_chance()).
        self.karma = 0
        
        # Inventory & Equipment
        self.inventory = []  # items held in backpack
        self.equipment = {
            "fighting_weapon": None,
            "defending_armor": None,
            "salvaging_tool": None,
            "spotting_item": None,
            "camping_medical": None,
            "accessory_1": None,
            "accessory_2": None
        }
        
        # Journey tracking
        self.current_leg_idx = 0  # 0 to 4
        self.leg_event_count = 0  # 0 to 20
        self.dungeons_found_in_leg = 0 # max 2
        self.super_monster_seen_in_leg = False
        self.super_monsters_defeated = 0
        self.dungeons_cleared = 0
        self.last_journey_event_turn = {}
        self.in_dungeon = False
        self.dungeon_name = ""
        self.dungeon_event_count = 0  # 0 to 6 (1-5 floor fights, 6 boss)
        self.dungeon_boss = ""
        self.dungeon_floors = []
        # How many times each regular monster has been encountered on the
        # journey this run - used to give repeat encounters a callback
        # ("...ran into another Cave Spider, maybe it's the first one's
        # brother.") instead of the same generic first-encounter text.
        self.monster_encounter_counts = {}
        # Rolled once at character creation (see GameController._generate_backstory)
        # and kept for the whole run - feeds the opening origin story and
        # later in-journey reminiscence lines.
        self.backstory = {}
        # Past town-recovery years (profession/modifier/injury/body_part), most
        # recent 10 kept - reminiscence material for "remember that year..." lines.
        self.town_history = []
        # Rare/notable run events (relic finds, dungeon bosses beaten, a
        # monster faced 3+ times) kept as a FIFO of the most recent 10 across
        # all types - reminiscence material, deliberately not exhaustive.
        self.special_moments = []
        
        # Relic tracking & state
        self.relics_found = []
        self.pendant_used = False
        self.game_over = False
        self.game_won = False
        self.death_reason = ""
        
        # Telemetry log
        self.event_logs = []
        self.last_combat_summary = {}

    def _log_special_moment(self, moment_type, **detail):
        """Records a rare/notable event (relic found, dungeon boss beaten, a
        monster faced 3+ times) for later reminiscence callbacks. Keeps only
        the most recent 10 (FIFO) shared across all moment types - deliberately
        not exhaustive, so only the genuinely memorable stuff survives."""
        self.special_moments.append({"type": moment_type, "leg": self.current_leg_idx + 1, **detail})
        self.special_moments = self.special_moments[-10:]

    def log(self, event_type, details):
        entry = {
            "leg": self.current_leg_idx + 1,
            "event_num": self.leg_event_count if not self.in_dungeon else self.dungeon_event_count,
            "in_dungeon": self.in_dungeon,
            "type": event_type,
            "hp": self.hp,
            "cash": self.cash,
            "details": details
        }
        self.event_logs.append(entry)

    def get_effective_skills(self):
        """Calculates skills with equipment bonuses and overburdened penalties applied."""
        effective = dict(self.base_skills)
        
        # 1. Add equipment bonuses
        for slot, item in self.equipment.items():
            if item:
                skill = item.get("skill")
                if skill and skill in effective:
                    effective[skill] += item.get("skill_val", 0)

        # 2. Calculate weight & penalty
        total_weight = sum(item["weight"] for item in self.inventory)
        max_weight = (effective["fighting"] + effective["defending"] + (effective["salvaging"] * 2)) * 2
        
        overburdened = total_weight - max_weight
        if overburdened > 20:
            penalty_units = (overburdened - 20) // 10 + 1
            penalty_pct = min(0.9, penalty_units * 0.10)
            for skill in effective:
                effective[skill] = int(effective[skill] * (1.0 - penalty_pct))
                
        return effective, total_weight, max_weight

    def generate_random_item(self, leg_num=1, quality_bias=None):
        cat_key = random.choice(list(ITEM_CATEGORIES.keys()))
        cat_data = ITEM_CATEGORIES[cat_key]
        
        if not quality_bias:
            r = random.random()
            if leg_num == 1:
                # Design tiering: leg 1 is Common only.
                tier = "Common"
            elif leg_num == 2:
                tier = "Common" if r < 0.70 else "Uncommon"
            elif leg_num == 3:
                tier = "Common" if r < 0.40 else ("Uncommon" if r < 0.80 else "Rare")
            elif leg_num == 4:
                tier = "Uncommon" if r < 0.35 else ("Rare" if r < 0.80 else "Epic")
            else:
                tier = "Rare" if r < 0.65 else "Epic"
        else:
            tier = quality_bias
            
        q_data = QUALITY_TIERS[tier]
        name = f"{tier} {random.choice(cat_data['names'])}"
        
        # Quality bonuses: Defending +20, Fighting/Stealth +10
        bonus = 0
        if cat_data["slot"] == "defending_armor":
            bonus = 20
        elif cat_key in ["fighting", "stealth"]:
            bonus = 10
            
        skill_val = random.randint(q_data["skill_min"], q_data["skill_max"]) + bonus
        
        val_ratio = (skill_val - q_data["skill_min"]) / max(1, (q_data["skill_max"] - q_data["skill_min"]))
        cash_val = int(q_data["cash_min"] + val_ratio * (q_data["cash_max"] - q_data["cash_min"]))
        
        item = {
            "name": name,
            "category": cat_key,
            "slot": cat_data["slot"],
            "tier": tier,
            "code": q_data["code"],
            "skill": cat_key if cat_key != "accessories" else random.choice(list(self.base_skills.keys())),
            "skill_val": skill_val,
            "weight": cat_data["weight"],
            "value": cash_val,
            "uses": 1,
            "max_uses": 1
        }
        return item

    def auto_equip_best(self):
        """Helper to equip highest stat items from inventory."""
        for item in list(self.inventory):
            slot = item["slot"]
            if slot == "accessory":
                if not self.equipment["accessory_1"]:
                    self.equipment["accessory_1"] = item
                    self.inventory.remove(item)
                elif not self.equipment["accessory_2"]:
                    self.equipment["accessory_2"] = item
                    self.inventory.remove(item)
                else:
                    min_acc = min([self.equipment["accessory_1"], self.equipment["accessory_2"]], key=lambda x: x.get("skill_val", 0))
                    if item.get("skill_val", 0) > min_acc.get("skill_val", 0):
                        if min_acc == self.equipment["accessory_1"]:
                            self.inventory.append(self.equipment["accessory_1"])
                            self.equipment["accessory_1"] = item
                        else:
                            self.inventory.append(self.equipment["accessory_2"])
                            self.equipment["accessory_2"] = item
                        self.inventory.remove(item)
            else:
                curr = self.equipment.get(slot)
                if not curr:
                    self.equipment[slot] = item
                    self.inventory.remove(item)
                elif item.get("skill_val", 0) > curr.get("skill_val", 0):
                    self.inventory.append(curr)
                    self.equipment[slot] = item
                    self.inventory.remove(item)

    def _opposed_roll(self, attacker_stat, defender_stat, die=20):
        """Contested check: both sides add a random 1-die swing to their stat
        and the higher total wins. A bigger stat gap makes winning likely but
        never certain - a lucky (or unlucky) roll can still flip the result.
        Returns (attacker_wins: bool, margin: int) where margin is how much
        the winning roll beat the losing one by (used to gauge crits)."""
        atk_roll = attacker_stat + random.randint(1, die)
        def_roll = defender_stat + random.randint(1, die)
        return atk_roll > def_roll, abs(atk_roll - def_roll)

    KILL_PHRASES = [
        "and then they goofed the whole pooch.",
        "and that was the last mistake it ever made.",
        "and promptly forgot how to be a threat.",
        "and folded like a lawn chair in a hurricane.",
        "and simply gave up on the concept of continuing to exist.",
        "and went down clutching its own bad decisions.",
        "and that, as they say, was that.",
        "and the universe quietly filed it under 'no longer a problem'.",
        "and became a cautionary tale for future monsters.",
        "and exited the story rather abruptly.",
    ]

    def _kill_phrase(self):
        return random.choice(self.KILL_PHRASES)

    def _combat_line(self, category, used_lines=None, **kwargs):
        """Builds a silly combat narration line from a 50+ line generated pool.

        `used_lines`, if given, is a set shared across a single fight; the
        (category, start_idx, end_idx) template combo is tracked so the same
        flavour text is never repeated across rounds of the same encounter."""
        start, end = COMBAT_LINE_POOLS[category]
        if used_lines is not None:
            combos = [(s, e) for s in range(len(start)) for e in range(len(end))
                      if (category, s, e) not in used_lines]
            if not combos:
                combos = [(s, e) for s in range(len(start)) for e in range(len(end))]
            s_idx, e_idx = random.choice(combos)
            used_lines.add((category, s_idx, e_idx))
        else:
            s_idx = random.randrange(len(start))
            e_idx = random.randrange(len(end))
        start_text = start[s_idx].format(**kwargs)
        end_text = end[e_idx].format(**kwargs)
        line = f"{start_text} {kwargs.get('value', '')} {end_text}".strip()
        return " ".join(line.split())

    def _combat_action_line(self, action, used_lines=None, **kwargs):
        if action == "fight_win":
            return self._combat_line("fight_win", used_lines, **kwargs)
        if action == "fight_loss":
            return self._combat_line("fight_loss", used_lines, **kwargs)
        if action == "magic_attack":
            return self._combat_line("magic_attack", used_lines, **kwargs)
        if action == "magic_defense":
            return self._combat_line("magic_defense", used_lines, **kwargs)
        if action == "steal":
            return self._combat_line("steal", used_lines, **kwargs)
        if action == "stealth_kill":
            return self._combat_line("stealth_kill", used_lines, **kwargs)
        return ""

    def _combat_round_detail(
        self,
        number,
        outcome,
        text,
        damage_dealt=0,
        damage_taken=0,
        hero_hp=None,
        monster_hp=None,
    ):
        return {
            "round": number,
            "outcome": outcome,
            "text": text,
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,
            "hero_hp": self.hp if hero_hp is None else hero_hp,
            "monster_hp": monster_hp,
        }

    def _magic_spell_name(self):
        return f"{random.choice(MAGIC_SPELL_NAME_PARTS['prefixes'])} {random.choice(MAGIC_SPELL_NAME_PARTS['spells'])}"

    def _magic_shield_name(self):
        return f"{random.choice(MAGIC_SHIELD_NAME_PARTS['prefixes'])} {random.choice(MAGIC_SHIELD_NAME_PARTS['shields'])}"

    def _fight_core_stats(self):
        skills, _, _ = self.get_effective_skills()
        effective_def = skills["defending"]

        has_arcane_amulet = any(eq and eq.get("name") == "Amulet of Arcane Shielding" for eq in self.equipment.values())
        ward_mult = 1.0 if has_arcane_amulet else 0.5
        if skills["magic"] > skills["fighting"]:
            effective_def += int(skills["magic"] * ward_mult)

        for eq in self.equipment.values():
            if eq and eq.get("name") == "Crown of the Archmage":
                effective_def = max(effective_def, skills["magic"])
                break

        # Stealth counts as a viable (if weaker) combat stat too, so a
        # stealth-built hero isn't defenseless whenever a sneak/steal fails
        # and they're dumped into a straight fight.
        stealth_component = int(skills["stealth"] * 0.5) if self.stealth_atk_enabled else 0
        player_atk = max(skills["fighting"], skills["magic"], stealth_component)
        return skills, player_atk, effective_def

    def _get_monster_stats(self, monster_name):
        """Returns monster combat stats, optionally scaled up for
        relic-flagged monsters (dungeon bosses/super monsters) when
        relic_scaling_enabled is set - a way to tune late-game/boss
        difficulty independently of regular per-leg monster stats."""
        m_stats = MONSTERS[monster_name]
        if self.relic_scaling_enabled and m_stats.get("relic"):
            scaled = dict(m_stats)
            for stat in ("fighting", "defending", "magic"):
                if stat in scaled:
                    scaled[stat] = int(scaled[stat] * RELIC_MONSTER_SCALE)
            return scaled
        return m_stats

    def _pick_throwable_item(self):
        """Returns the cheapest non-relic inventory item usable as a
        distraction to throw at a monster, or None if nothing's available."""
        candidates = [it for it in self.inventory if it.get("category") != "relic"]
        if not candidates:
            return None
        return min(candidates, key=lambda it: it.get("value", 0))

    def estimate_fight_risk(self, monster_name):
        m_stats = self._get_monster_stats(monster_name)
        skills, player_atk, effective_def = self._fight_core_stats()

        has_cloak = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        has_staff = any(eq and eq.get("name") == "Staff of Magic" for eq in self.equipment.values())
        has_crown = any(eq and eq.get("name") == "Crown of the Archmage" for eq in self.equipment.values())
        has_sword = any(eq and eq.get("name") == "Sword of Power" for eq in self.equipment.values())
        has_plate = any(eq and eq.get("name") == "Plate of Invincibility" for eq in self.equipment.values())
        has_shield = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())
        has_mirror = any(eq and eq.get("name") == "Mirror of Fate" for eq in self.equipment.values())

        guaranteed = has_cloak or (has_staff and has_crown) or (has_sword and has_plate)
        player_round_damage = max(5, player_atk - m_stats["defending"])
        monster_round_damage = max(5, m_stats["fighting"] - effective_def)
        if has_shield:
            monster_round_damage = max(1, monster_round_damage // 2)

        monster_hp = max(20, (m_stats["fighting"] + m_stats["defending"]) * 2)
        rounds_to_kill = max(1, math.ceil(monster_hp / player_round_damage))
        rounds_to_die = max(1, math.ceil(max(1, self.hp) / max(1, monster_round_damage)))
        round_cap = 8

        if guaranteed:
            win_prob = 1.0
        else:
            # Exact chance to win a single contested round.
            wins = 0
            for p_die in range(1, 21):
                for m_die in range(1, 21):
                    p_power = player_atk + effective_def + p_die
                    m_power = m_stats["fighting"] + m_stats["defending"] + m_die
                    if p_power > m_power:
                        wins += 1
            p_round = wins / 400.0
            q_round = 1.0 - p_round

            # DP race model: probability player reaches required wins before
            # accumulating enough losses to drop to 0 HP, within round cap.
            states = {(0, 0): 1.0}  # (wins, losses) -> probability
            win_prob = 0.0
            for _ in range(round_cap):
                next_states = {}
                for (w, l), prob in states.items():
                    if prob <= 0:
                        continue

                    # Round win
                    w2 = w + 1
                    pw = prob * p_round
                    if w2 >= rounds_to_kill:
                        win_prob += pw
                    else:
                        next_states[(w2, l)] = next_states.get((w2, l), 0.0) + pw

                    # Round loss
                    l2 = l + 1
                    pl = prob * q_round
                    if l2 < rounds_to_die:
                        next_states[(w, l2)] = next_states.get((w, l2), 0.0) + pl
                states = next_states

            # Relic safety nets that can flip losses.
            if has_sword or has_plate:
                win_prob = win_prob + (1.0 - win_prob) * 0.50
            if has_mirror:
                win_prob = win_prob + (1.0 - win_prob) * 0.35

        band = self._risk_band_for_probability(win_prob)

        return {
            "band": band,
            "win_pct": int(round(win_prob * 100)),
            "player_attack": player_atk,
            "player_effective_defense": effective_def,
            "player_round_damage": player_round_damage,
            "monster_round_damage": monster_round_damage,
            "monster_hp": monster_hp,
            "rounds_to_kill": rounds_to_kill,
            "rounds_to_die": rounds_to_die,
            "fighting": skills["fighting"],
            "magic": skills["magic"],
            "defending": skills["defending"],
        }

    def _opposed_win_probability(self, attacker_stat, defender_stat, die=20):
        wins = 0
        total = die * die
        for atk_die in range(1, die + 1):
            for def_die in range(1, die + 1):
                if attacker_stat + atk_die > defender_stat + def_die:
                    wins += 1
        return wins / float(total)

    def _risk_band_for_probability(self, prob):
        for threshold, label in RISK_BANDS:
            if prob >= threshold:
                return label
        return RISK_BANDS[-1][1]

    def estimate_combat_action_risks(self, monster_name):
        m_stats = self._get_monster_stats(monster_name)
        fight = self.estimate_fight_risk(monster_name)
        skills, _, _ = self._fight_core_stats()

        has_cloak = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        has_boots = any(eq and eq.get("name") == "Boots of Stealth" for eq in self.equipment.values())
        has_dagger = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())

        if has_cloak:
            sneak_prob = 1.0
        else:
            sneak_prob = self._opposed_win_probability(skills["stealth"], m_stats["defending"])
            if has_boots:
                sneak_prob = sneak_prob + (1.0 - sneak_prob) * 0.50

        steal_prob = self._opposed_win_probability(
            skills["stealth"] + skills["salvaging"],
            m_stats["defending"] * 2
        )

        if has_cloak or (has_dagger and has_cloak):
            stealth_kill_prob = 1.0
        else:
            stealth_kill_prob = self._opposed_win_probability(
                skills["stealth"] * 2,
                int(m_stats["defending"] * 1.5)
            )

        return {
            "fight": {"prob": fight["win_pct"] / 100.0, "pct": fight["win_pct"], "band": fight["band"]},
            "sneak": {"prob": sneak_prob, "pct": int(round(sneak_prob * 100)), "band": self._risk_band_for_probability(sneak_prob)},
            "steal": {"prob": steal_prob, "pct": int(round(steal_prob * 100)), "band": self._risk_band_for_probability(steal_prob)},
            "stealth_kill": {"prob": stealth_kill_prob, "pct": int(round(stealth_kill_prob * 100)), "band": self._risk_band_for_probability(stealth_kill_prob)},
            "fight_profile": fight,
        }

    def resolve_fight(self, monster_name, choice="fight", encounter_type="fight"):
        """Resolves combat (fight, sneak, steal, stealth_kill) via contested
        dice rolls instead of flat stat comparisons, so every encounter
        carries genuine risk - even a heavily favored hero can get unlucky,
        and a "fight" can end in a costly trade of blows rather than a
        clean win or loss."""
        m_stats = self._get_monster_stats(monster_name)
        self.last_combat_summary = {}
        skills, player_atk, effective_def = self._fight_core_stats()
        # Tracks (category, start_idx, end_idx) template combos already used
        # this fight so no two rounds of the same encounter reuse the same
        # flavour text.
        used_lines = set()

        # Check Cloak of Invisibility
        for eq in self.equipment.values():
            if eq and eq.get("name") == "Cloak of Invisibility":
                if choice in ["sneak", "fight", "stealth_kill"]:
                    self.log("FIGHT_SUCCESS", {"monster": monster_name, "choice": choice, "relic": "Cloak of Invisibility"})
                    round_text = self._combat_action_line(
                        "fight_win",
                        used_lines,
                        value="a flawless strike",
                        monster_name=monster_name,
                    )
                    round_text = f"{round_text} {self._kill_phrase()}"
                    self.last_combat_summary = {
                        "rounds": 1,
                        "round_texts": [round_text],
                        "round_details": [
                            self._combat_round_detail(
                                1,
                                "hit",
                                round_text,
                                monster_hp=0,
                            )
                        ],
                        "mode": choice,
                        "monster_name": monster_name,
                    }
                    return self.grant_monster_loot(monster_name)

        has_boots = any(eq and eq.get("name") == "Boots of Stealth" for eq in self.equipment.values())

        if choice == "sneak":
            success, margin = self._opposed_roll(skills["stealth"], m_stats["defending"])
            if not success and has_boots and random.random() < 0.5:
                success = True
                self.log("BOOTS_OF_STEALTH_PROC", {"monster": monster_name})
            if success:
                self.log("SNEAK_SUCCESS", {"monster": monster_name, "stealth": skills["stealth"], "margin": margin})
                return "JOURNEY"
            else:
                choice = "fight"

        if choice == "steal":
            success, margin = self._opposed_roll(skills["stealth"] + skills["salvaging"], m_stats["defending"] * 2)
            if success:
                self.karma += KARMA_STEAL_PENALTY
                self.log("STEAL_SUCCESS", {"monster": monster_name, "margin": margin, "karma": self.karma})
                loot = self.grant_monster_loot(monster_name)
                if encounter_type == "super_monster":
                    self.super_monsters_defeated = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared = min(10, self.dungeons_cleared + 1)
                    self._log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                round_text = self._combat_action_line("steal", value="a pouch of loot")
                self.last_combat_summary = {
                    "rounds": 1,
                    "round_texts": [round_text],
                    "round_details": [
                        self._combat_round_detail(1, "hit", round_text, monster_hp=0)
                    ],
                    "mode": "steal",
                    "monster_name": monster_name,
                }
                return loot
            else:
                choice = "fight"

        if choice == "stealth_kill":
            has_dagger = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())
            has_cloak = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
            has_stone = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.equipment.values())
            player_round_damage = max(5, player_atk - m_stats["defending"])
            
            # Shadow Assassin 2-Relic Synergy (Dagger + Cloak) & Master Thief 3-Relic Synergy (+Stone)
            is_shadow_assassin = (has_dagger and has_cloak)
            is_master_thief = (is_shadow_assassin and has_stone)

            # Surprise formula: (stealth * 2) vs (monster defending * 1.5), contested
            surprise_stealth = skills["stealth"] * 2
            surprise_def = int(m_stats["defending"] * 1.5)
            success, margin = self._opposed_roll(surprise_stealth, surprise_def)
            
            if is_shadow_assassin or success:
                self.karma += KARMA_STEALTH_KILL_PENALTY
                self.log("STEALTH_KILL_SUCCESS", {"monster": monster_name, "stealth_score": surprise_stealth, "m_def_score": surprise_def, "margin": margin, "karma": self.karma})
                cash_mult = 2.0 if is_master_thief else 1.0
                loot = self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
                if encounter_type == "super_monster":
                    self.super_monsters_defeated = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared = min(10, self.dungeons_cleared + 1)
                    self._log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                round_text = self._combat_action_line(
                    "stealth_kill",
                    used_lines,
                    value=f"{player_round_damage} damage",
                )
                round_text = f"{round_text} {self._kill_phrase()}"
                self.last_combat_summary = {
                    "rounds": 1,
                    "round_texts": [round_text],
                    "round_details": [
                        self._combat_round_detail(
                            1,
                            "hit",
                            round_text,
                            damage_dealt=player_round_damage,
                            monster_hp=0,
                        )
                    ],
                    "mode": "stealth_kill",
                    "monster_name": monster_name,
                }
                return loot
            else:
                choice = "fight"

        if choice == "throw_item":
            item = self._pick_throwable_item()
            if item:
                self.inventory.remove(item)
                self.log("THROW_ITEM_ESCAPE", {"monster": monster_name, "item": item["name"]})
                round_text = f"You hurl your {item['name']} at {monster_name} and slip away in the confusion - the item and any loot are lost."
                self.last_combat_summary = {
                    "rounds": 1,
                    "round_texts": [round_text],
                    "round_details": [
                        self._combat_round_detail(1, "escape", round_text, monster_hp=None)
                    ],
                    "mode": "throw_item",
                    "monster_name": monster_name,
                }
                return "JOURNEY"
            else:
                choice = "fight"

        if choice == "fight":
            # Check Arcane Tempest (Staff + Crown) & Grand Archmage (Staff + Crown + Ankh)
            has_staff = any(eq and eq.get("name") == "Staff of Magic" for eq in self.equipment.values())
            has_crown = any(eq and eq.get("name") == "Crown of the Archmage" for eq in self.equipment.values())
            has_ankh = any(eq and eq.get("name") == "Pharaoh's Ankh of Rebirth" for eq in self.equipment.values())
            
            is_arcane_tempest = (has_staff and has_crown)
            is_grand_archmage = (is_arcane_tempest and has_ankh)

            has_sword = any(eq and eq.get("name") == "Sword of Power" for eq in self.equipment.values())
            has_plate = any(eq and eq.get("name") == "Plate of Invincibility" for eq in self.equipment.values())

            crit = False
            rounds_fought = 0
            player_hp_before = self.hp
            monster_max_hp = max(20, (m_stats["fighting"] + m_stats["defending"]) * 2)
            monster_hp = monster_max_hp
            round_texts = []
            round_details = []
            magic_attack_mode = skills["magic"] > skills["fighting"]
            spell_name = self._magic_spell_name()
            shield_name = self._magic_shield_name()
            player_round_damage = max(5, player_atk - m_stats["defending"])
            base_monster_damage = max(5, m_stats["fighting"] - effective_def)
            has_shield = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())

            if is_arcane_tempest or (has_sword and has_plate):
                # Guaranteed-win relic combos bypass the dice entirely and never wound the hero
                win, damage, margin = True, 0, 0
                rounds_fought = 1
                monster_hp = 0
                round_texts.append(
                    self._combat_action_line(
                        "magic_attack" if magic_attack_mode else "fight_win",
                        used_lines,
                        value=player_round_damage,
                        monster_name=monster_name,
                        spell_name=spell_name,
                        weapon_name=spell_name,
                    ) + f" {self._kill_phrase()}"
                )
                round_details.append(
                    self._combat_round_detail(
                        1,
                        "hit",
                        round_texts[-1],
                        damage_dealt=player_round_damage,
                        monster_hp=monster_hp,
                    )
                )
            else:
                # Multi-round combat: each round winner deals direct damage.
                # Round cap prevents very long exchanges while still allowing
                # multiple swings per encounter.
                max_rounds = 8
                margin = 0
                win = False

                for r in range(1, max_rounds + 1):
                    rounds_fought = r
                    p_power = player_atk + effective_def + random.randint(1, 20)
                    m_power = m_stats["fighting"] + m_stats["defending"] + random.randint(1, 20)
                    margin = abs(p_power - m_power)
                    player_wins_round = p_power > m_power
                    crit = crit or (player_wins_round and margin >= 20)

                    if player_wins_round:
                        monster_hp = max(0, monster_hp - player_round_damage)
                        line = self._combat_action_line(
                            "magic_attack" if magic_attack_mode else "fight_win",
                            used_lines,
                            value=player_round_damage,
                            monster_name=monster_name,
                            spell_name=spell_name,
                            weapon_name=spell_name,
                        )
                        if monster_hp <= 0:
                            line = f"{line} {self._kill_phrase()}"
                        round_texts.append(line)
                        round_details.append(
                            self._combat_round_detail(
                                r,
                                "hit",
                                round_texts[-1],
                                damage_dealt=player_round_damage,
                                hero_hp=self.hp,
                                monster_hp=monster_hp,
                            )
                        )
                        if monster_hp <= 0:
                            win = True
                            break
                    else:
                        damage = base_monster_damage
                        if has_shield:
                            damage = max(1, damage // 2)
                        round_texts.append(
                            self._combat_action_line(
                                "magic_defense" if magic_attack_mode else "fight_loss",
                                used_lines,
                                value=damage,
                                monster_name=monster_name,
                                shield_name=shield_name,
                            )
                        )
                        self.take_damage(damage, DEATH_REASONS["slain_by"].format(monster_name=monster_name))
                        round_details.append(
                            self._combat_round_detail(
                                r,
                                "loss",
                                round_texts[-1],
                                damage_taken=damage,
                                hero_hp=self.hp,
                                monster_hp=monster_hp,
                            )
                        )
                        if self.game_over:
                            break

                # If combat timed out on round cap, treat as loss pressure.
                if not win and not self.game_over and monster_hp <= 0:
                    win = True

                # Sword of Power / Plate of Invincibility: 50% reroll of a loss when held alone.
                if not win and (has_sword or has_plate):
                    if random.random() < 0.5:
                        win = True
                        monster_hp = 0
                        self.log("RELIC_REROLL_PROC", {"monster": monster_name, "relic": "Sword of Power" if has_sword else "Plate of Invincibility"})

                # Mirror of Fate: flips a loss to an instant win once per game.
                if not win:
                    for slot, eq in self.equipment.items():
                        if eq and eq.get("name") == "Mirror of Fate":
                            win = True
                            monster_hp = 0
                            self.equipment[slot] = None  # consume relic
                            self.log("MIRROR_OF_FATE_PROC", {"monster": monster_name})
                            break

                damage = max(0, player_hp_before - self.hp)

            self.last_combat_summary = {
                "rounds": rounds_fought,
                "monster_max_hp": monster_max_hp,
                "monster_hp_left": max(0, monster_hp),
                "player_hp_before": player_hp_before,
                "player_hp_after": self.hp,
                "hp_lost": max(0, player_hp_before - self.hp),
                "round_texts": round_texts,
                "round_details": round_details,
                "mode": "fight",
            }

            if win:
                if encounter_type == "super_monster":
                    self.super_monsters_defeated = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared = min(10, self.dungeons_cleared + 1)
                    self._log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                if m_stats.get("relic"):
                    if is_grand_archmage:
                        self.hp = 100
                        self.log("GRAND_ARCHMAGE_FULL_HEAL", {"hp": self.hp})
                    elif has_ankh:
                        self.hp = min(100, self.hp + 50)
                        self.log("ANKH_REBIRTH_HEAL", {"hp": self.hp})

                cash_mult = 1.5 if crit else 1.0
                self.log("FIGHT_WIN", {"monster": monster_name, "player_atk": player_atk, "m_def": m_stats["defending"], "margin": margin, "critical": crit, "rounds": rounds_fought})
                return self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
            else:
                # If rounds ended without lethal player damage, apply a final attrition hit.
                if not self.game_over:
                    timeout_damage = max(5, m_stats["fighting"] - effective_def)
                    has_shield = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())
                    if has_shield:
                        timeout_damage = max(1, timeout_damage // 2)
                    self.take_damage(timeout_damage, DEATH_REASONS["slain_by"].format(monster_name=monster_name))
                    timeout_text = self._combat_action_line(
                        "fight_loss",
                        used_lines,
                        value=timeout_damage,
                        monster_name=monster_name,
                    )
                    round_texts.append(timeout_text)
                    round_details.append(
                        self._combat_round_detail(
                            rounds_fought + 1,
                            "attrition",
                            timeout_text,
                            damage_taken=timeout_damage,
                            hero_hp=self.hp,
                            monster_hp=monster_hp,
                        )
                    )
                    self.last_combat_summary["rounds"] = len(round_details)
                    self.last_combat_summary["round_texts"] = round_texts
                    self.last_combat_summary["round_details"] = round_details
                    self.last_combat_summary["player_hp_after"] = self.hp
                    self.last_combat_summary["hp_lost"] = max(
                        0,
                        player_hp_before - self.hp,
                    )
                self.log("FIGHT_LOSS", {"monster": monster_name, "hp_loss": max(0, player_hp_before - self.hp), "critical": crit, "rounds": rounds_fought})
                return "LOSS_WINDOW"

    def take_damage(self, amount, reason=None):
        reason = reason or DEATH_REASONS["unknown"]
        self.hp -= amount
        if self.hp <= 0:
            fairy_item = self.equipment.get("camping_medical")
            if fairy_item and fairy_item.get("name") == "Captured Fairy":
                rewind_events = min(5, self.leg_event_count)
                self.leg_event_count = max(0, self.leg_event_count - 5)
                cash_taken = min(1000, self.cash)
                self.cash -= cash_taken
                self.hp = self.max_hp
                self.equipment["camping_medical"] = None
                if self.in_dungeon:
                    self.leave_dungeon(DUNGEON_EXIT_REASONS["fairy_rescue"])
                self.log("FAIRY_SAVED_LIFE", {
                    "reason": reason,
                    "events_rewound": rewind_events,
                    "cash_taken": cash_taken,
                    "hp": self.hp
                })
                return
            # Check Pendant of Life
            has_pendant = False
            for slot, eq in self.equipment.items():
                if eq and eq.get("name") == "Pendant of Life":
                    has_pendant = True
                    self.equipment[slot] = None
                    break
            if has_pendant:
                self.hp = 20
                self.log("PENDANT_SAVED_LIFE", {"reason": reason})
            else:
                self.hp = 0
                self.game_over = True
                self.death_reason = reason
                self.log("DIED", {"reason": reason})

    def grant_monster_loot(self, monster_name, cash_multiplier=1.0):
        m_stats = MONSTERS[monster_name]
        earned_cash = int(random.randint(m_stats["cash_min"], m_stats["cash_max"]) * cash_multiplier)
        self.cash += earned_cash
        
        num_eq = self._roll_loot_item_count(monster_name, m_stats)
        items_found = [self.generate_random_item(leg_num=self.current_leg_idx+1) for _ in range(num_eq)]
        
        # Named Relics only drop on legs 4-5. On legs 1-3, dungeon
        # bosses/super monsters get a bonus item at an upgraded tier instead.
        leg_num = self.current_leg_idx + 1
        is_relic_monster = bool(m_stats.get("relic"))
        relic_dropped = None
        if leg_num >= 4:
            if is_relic_monster or random.random() < 0.05:
                avail_relics = [r for r in RELICS.keys() if r not in self.relics_found]
                if avail_relics:
                    relic_name = random.choice(avail_relics)
                    r_info = RELICS[relic_name]
                    relic_item = {
                        "name": relic_name,
                        "category": "relic",
                        "slot": r_info["type"],
                        "tier": "Epic",
                        "code": "e",
                        "skill": r_info["skill"],
                        "skill_val": r_info["bonus"],
                        "weight": 1,
                        "value": 25000,
                        "uses": 1
                    }
                    items_found.append(relic_item)
                    self.relics_found.append(relic_name)
                    relic_dropped = relic_name
                    self._log_special_moment("relic_found", relic_name=relic_name, monster_name=monster_name)
        elif is_relic_monster:
            bonus_tier = BOSS_BONUS_TIER_BY_LEG.get(leg_num, "Rare")
            items_found.append(self.generate_random_item(leg_num=leg_num, quality_bias=bonus_tier))

        self.inventory.extend(items_found)
        
        self.log("LOOT_GAINED", {"cash": earned_cash, "items_count": len(items_found), "relic": relic_dropped})
        return "LOOT_FOUND"

    def _roll_loot_item_count(self, monster_name, m_stats):
        """Roll item drops with reduced global drop rates and very sparse low-level drops."""
        base_count = random.randint(m_stats["eq_min"], m_stats["eq_max"])
        leg_num = m_stats.get("leg", self.current_leg_idx + 1)
        is_super_or_boss = bool(m_stats.get("relic"))
        is_early_regular = (leg_num == 1 and not is_super_or_boss)

        # Leg 1 regular monsters should drop 0 items most of the time.
        if is_early_regular:
            if random.random() < 0.70:
                return 0
            return 1 if random.random() < 0.80 else 2

        # Global reduction across the board.
        keep_scale = 0.55 if not is_super_or_boss else 0.70
        reduced = int(round(base_count * keep_scale))

        # Non-boss enemies can still drop nothing sometimes.
        if not is_super_or_boss and random.random() < 0.25:
            return 0

        # Keep at least one item for boss/super encounters when they drop loot.
        if is_super_or_boss:
            reduced = max(1, reduced)
        else:
            reduced = max(0, reduced)

        # Additional global reduction pass: remove at most one item.
        return max(0, reduced - random.randint(0, 1))

    # ------------------------------------------------------------------
    # Shared decision helpers - single source of truth for probabilities
    # and selection rules used by BOTH the fast auto-simulator
    # (step_next_event, below) and the interactive GameController.
    # ------------------------------------------------------------------
    def get_random_monster(self, leg_idx=None):
        """Picks a random regular monster appropriate for a leg (defaults to
        the hero's current leg). Excludes dungeon and super monster names so
        those stay unique to their own dedicated encounters."""
        leg_idx = self.current_leg_idx if leg_idx is None else leg_idx
        leg_monsters = [
            m for m, data in MONSTERS.items()
            if data.get("leg") == leg_idx + 1
            and m not in DUNGEON_MONSTER_NAMES
            and m not in SUPER_MONSTER_NAMES
        ]
        return random.choice(leg_monsters) if leg_monsters else "Goblin"

    def roll_journey_event_type(self):
        """Rolls the next journey event with pacing constraints.
        Rules:
        - Mostly fights.
        - There is no in-journey healing/rest event anymore (see the town
          recovery mechanic, triggered at leg transitions instead).
        - Free-loot style events (magic shrine, wandering trader) cannot
          repeat within 3 events of themselves.
        - Super monster appears at most once per leg and also respects
          a 3-event self-cooldown.
        """
        # Weights are intentionally fight-heavy.
        weighted_events = [
            ("FIGHT", 78),
            ("SUPER_MONSTER", 8),
            ("MAGIC_SHRINE", 6),
            ("WANDERING_TRADER", 6),
            ("WANDER_GROUP", 4),
            ("FAIRY_FOUND", 2),
        ]

        def within_three_events(last_turn):
            return last_turn is not None and (self.leg_event_count - last_turn) <= 3

        allowed = []
        for event_type, weight in weighted_events:
            if event_type == "SUPER_MONSTER":
                if self.super_monster_seen_in_leg:
                    continue
                if within_three_events(self.last_journey_event_turn.get("SUPER_MONSTER")):
                    continue
            elif event_type in ("MAGIC_SHRINE", "WANDERING_TRADER"):
                if within_three_events(self.last_journey_event_turn.get(event_type)):
                    continue
            elif event_type == "WANDER_GROUP":
                if within_three_events(self.last_journey_event_turn.get("WANDER_GROUP")):
                    continue
            elif event_type == "FAIRY_FOUND":
                if within_three_events(self.last_journey_event_turn.get("FAIRY_FOUND")):
                    continue
            allowed.append((event_type, weight))

        # If all non-fight options are blocked, force a fight.
        if not allowed:
            return "FIGHT"

        total_weight = sum(weight for _, weight in allowed)
        roll = random.uniform(0, total_weight)
        upto = 0
        chosen_event = "FIGHT"
        for event_type, weight in allowed:
            upto += weight
            if roll <= upto:
                chosen_event = event_type
                break

        # Record event occurrence for cooldown tracking.
        if chosen_event == "SUPER_MONSTER":
            self.super_monster_seen_in_leg = True
            self.last_journey_event_turn["SUPER_MONSTER"] = self.leg_event_count
        elif chosen_event in ("MAGIC_SHRINE", "WANDERING_TRADER"):
            self.last_journey_event_turn[chosen_event] = self.leg_event_count
        elif chosen_event == "WANDER_GROUP":
            self.last_journey_event_turn["WANDER_GROUP"] = self.leg_event_count
        elif chosen_event == "FAIRY_FOUND":
            self.last_journey_event_turn["FAIRY_FOUND"] = self.leg_event_count

        return chosen_event

    def try_spot_dungeon(self):
        """Checks the dungeon-spotting roll (max 2 per leg). If found, records
        the dungeon's name/boss/floors (but does NOT enter it - the caller
        decides whether to enter_dungeon() or ignore it) and returns the
        dungeon info dict, else None."""
        if self.dungeons_found_in_leg >= 2:
            return None
        skills, _, _ = self.get_effective_skills()
        roll = random.randint(0, 100)
        if skills["spotting"] < roll:
            return None
        self.dungeons_found_in_leg += 1
        leg_info = LEGS[self.current_leg_idx]
        dung_info = leg_info["dungeons"][self.dungeons_found_in_leg - 1]
        self.dungeon_name = dung_info["name"]
        self.dungeon_boss = dung_info["boss"]
        self.dungeon_floors = dung_info.get("floors", [])
        self.dungeon_event_count = 0
        self.log("DUNGEON_FOUND", {"name": dung_info["name"], "boss": dung_info["boss"]})
        return dung_info

    def try_leg_transition(self):
        """Checks whether the current leg's 20 events are complete. Returns
        'LEVEL_UP', 'CAPITAL', or None. Mutates leg state accordingly."""
        if self.leg_event_count <= 20:
            return None
        if self.current_leg_idx < 4:
            self.current_leg_idx += 1
            self.leg_event_count = 0
            self.dungeons_found_in_leg = 0
            self.super_monster_seen_in_leg = False
            self.last_journey_event_turn = {}
            self.log("LEG_COMPLETED", {"new_leg": self.current_leg_idx + 1})
            return "LEVEL_UP"
        else:
            self.game_won = True
            self.log("ARRIVED_CAPITAL", {"cash": self.cash})
            return "CAPITAL"

    def enter_dungeon(self, dungeon=None):
        """Begins exploring a dungeon found via try_spot_dungeon(). `dungeon`
        is optional if try_spot_dungeon() already populated dungeon_name/boss/floors."""
        if dungeon:
            self.dungeon_name = dungeon["name"]
            self.dungeon_boss = dungeon["boss"]
            self.dungeon_floors = dungeon.get("floors", [])
            self.dungeon_event_count = 0
        self.in_dungeon = True

    def leave_dungeon(self, reason=None):
        reason = reason or DUNGEON_EXIT_REASONS["default"]
        self.in_dungeon = False
        self.log("DUNGEON_LEFT", {"reason": reason})

    def get_dungeon_floor_monster(self):
        """Previews the monster for the *next* dungeon floor/boss without
        advancing any state (dungeon_event_count is only bumped by
        advance_dungeon_floor() after a floor is won)."""
        idx = self.dungeon_event_count
        if idx < 5:
            return self.dungeon_floors[idx] if idx < len(self.dungeon_floors) else "Goblin"
        return self.dungeon_boss

    def advance_dungeon_floor(self):
        """Call after winning a dungeon floor fight to move to the next floor."""
        self.dungeon_event_count += 1

    def resolve_magic_shrine(self):
        """Grants loot with zero risk. Journey-time healing has been removed
        entirely (see the town recovery mechanic), so this no longer restores
        HP - it is purely a free-loot event. Returns a summary dict."""
        self.log("MAGIC_SHRINE_LOOT", {})
        before_cash = self.cash
        before_len = len(self.inventory)
        self.grant_monster_loot("Goblin")
        return {
            "cash_gained": self.cash - before_cash,
            "new_items": self.inventory[before_len:],
        }

    def capture_fairy(self):
        """Adds a captured fairy item to inventory."""
        fairy_item = {
            "name": "Captured Fairy",
            "category": "fairy",
            "slot": "camping_medical",
            "tier": "Epic",
            "code": "e",
            "skill": None,
            "skill_val": 0,
            "weight": 1,
            "value": 1000,
            "uses": 1,
            "max_uses": 1,
        }
        self.inventory.append(fairy_item)
        self.log("FAIRY_CAPTURED", {"item": fairy_item["name"]})
        return fairy_item

    def apply_wander_group_advance(self, step_count=5):
        """Moves the hero forward on the current leg by additional events."""
        self.leg_event_count += step_count
        self.log("WANDER_GROUP_ADVANCE", {"events_advanced": step_count, "leg_event_count": self.leg_event_count})

    def trader_buy_multiplier(self):
        has_stone = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.equipment.values())
        return 1.10 if has_stone else 1.40

    def trader_sell_multiplier(self):
        has_stone = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.equipment.values())
        return 0.90 if has_stone else 0.60

    def generate_trader_offer(self, count=5):
        """Generates the wandering trader's for-sale inventory."""
        return [self.generate_random_item(self.current_leg_idx + 1) for _ in range(count)]

    def trader_buy(self, item):
        """Player buys `item` from the trader. Returns True if successful."""
        cost = int(item["value"] * self.trader_buy_multiplier())
        if self.cash < cost:
            return False
        self.cash -= cost
        self.inventory.append(item)
        self.log("TRADER_BUY", {"item": item["name"], "cost": cost})
        return True

    def trader_sell(self, item):
        """Player sells `item` (must be in inventory) to the trader."""
        if item not in self.inventory:
            return False
        price = int(item["value"] * self.trader_sell_multiplier())
        self.cash += price
        self.inventory.remove(item)
        self.log("TRADER_SELL", {"item": item["name"], "price": price})
        return True

    def apply_level_up(self, skill):
        if skill in self.base_skills:
            self.base_skills[skill] += 5
            return True
        return False

    def advance_to_next_leg(self):
        self.current_leg_idx += 1
        self.leg_event_count = 0
        self.dungeons_found_in_leg = 0
        self.super_monster_seen_in_leg = False
        self.last_journey_event_turn = {}

    def sell_all_for_capital(self):
        """Auto-sells all inventory & equipment at 100% value, as happens
        when the hero arrives at the Capital."""
        for item in self.inventory:
            self.cash += item["value"]
        self.inventory.clear()
        for slot, item in list(self.equipment.items()):
            if item:
                self.cash += item["value"]
                self.equipment[slot] = None

    def get_pension(self):
        """Pension = flat cash-based lookup, scaled by how many years the
        pension needs to last. A random end-of-life age (60-90) is rolled
        once per hero and reused for every pension calculation that run, so
        a younger hero (more years left to fund) gets a smaller multiplier
        for the same cash than an older one - i.e. the younger hero needs
        more cash to retire equally comfortably."""
        base = None
        for p in PENSIONS:
            if p["min"] <= self.cash <= p["max"]:
                base = p["pension"]
                break
        if base is None:
            base = 5000 if self.cash >= 50000 else 100
        if self.end_age is None:
            self.end_age = random.randint(PENSION_END_AGE_MIN, PENSION_END_AGE_MAX)
        years_remaining = max(1, self.end_age - self.age)
        multiplier = max(0.2, min(PENSION_BASELINE_YEARS / years_remaining, 3.0))
        return round(base * multiplier)

    def get_house_options(self):
        """Returns (options, pension) for the Capital screen. Score preview
        follows the design spec: multiplier x pension (not remaining cash)."""
        pension = self.get_pension()
        options = []
        for h in HOUSES:
            affordable = self.cash >= h["cost"]
            score = h["multiplier"] * pension if affordable else None
            options.append({
                "name": h["name"], "cost": h["cost"], "multiplier": h["multiplier"],
                "affordable": affordable, "score": score
            })
        return options, pension

    def step_next_event(self):
        """Advances the game state by one event step (10 sec equivalent in fast mode)."""
        if self.game_over:
            return "GAME_OVER"

        # Dungeon logic: 5 themed floor fights, then the boss
        if self.in_dungeon:
            self.dungeon_event_count += 1
            if self.dungeon_event_count <= 5:
                floor_idx = self.dungeon_event_count - 1
                monster = self.dungeon_floors[floor_idx] if floor_idx < len(self.dungeon_floors) else "Goblin"
                choice = self.get_tactical_choice(monster)
                res = self.resolve_fight(monster, choice=choice, encounter_type="dungeon_floor")
                if res == "LOSS_WINDOW":
                    self.leave_dungeon(DUNGEON_EXIT_REASONS["floor_defeat"])
                return res
            else:
                # Dungeon boss fight
                res = self.resolve_fight(self.dungeon_boss, choice="fight", encounter_type="dungeon_boss")
                self.in_dungeon = False
                return res

        # Main Journey events
        self.leg_event_count += 1

        dungeon = self.try_spot_dungeon()
        if dungeon:
            return "DUNGEON_FOUND"

        transition = self.try_leg_transition()
        if transition:
            return transition

        event_type = self.roll_journey_event_type()
        if event_type == "SUPER_MONSTER":
            return "SUPER_MONSTER"
        elif event_type == "MAGIC_SHRINE":
            self.resolve_magic_shrine()
            return "MAGIC_SHRINE"
        elif event_type == "WANDERING_TRADER":
            return "WANDERING_TRADER"
        elif event_type == "WANDER_GROUP":
            self.apply_wander_group_advance(5)
            transition = self.try_leg_transition()
            if transition:
                return transition
            return "WANDER_GROUP"
        elif event_type == "FAIRY_FOUND":
            self.capture_fairy()
            return "FAIRY_FOUND"
        else:
            if self.skip_journey_fights:
                m_name = self.get_random_monster()
                self.log("JOURNEY_FIGHT_BYPASSED", {"monster": m_name})
                return "JOURNEY"
            m_name = self.get_random_monster()
            choice = self.get_tactical_choice(m_name)
            return self.resolve_fight(m_name, choice=choice)

    def get_tactical_choice(self, monster_name):
        skills, _, _ = self.get_effective_skills()
        m_stats = self._get_monster_stats(monster_name)
        m_def = m_stats["defending"]
        
        has_dagger = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())
        has_cloak = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        is_shadow_assassin = (has_dagger and has_cloak)

        # Phase 3 Surprise Formula: (stealth * 2) vs (m_def * 1.5)
        surprise_stealth = skills["stealth"] * 2
        surprise_def = int(m_def * 1.5)
        
        if is_shadow_assassin or surprise_stealth > surprise_def:
            return "stealth_kill"
        elif (skills["stealth"] + skills["salvaging"]) > (m_def * 2):
            return "steal"
        elif self.hp < self.max_hp * 0.5:
            # Below half HP: a low-stealth build (e.g. Hitter) is unlikely to
            # sneak away, so prefer a guaranteed escape by throwing a spare
            # item if one's available. Otherwise fall back to the free
            # sneak attempt - a failed sneak just becomes a normal fight,
            # so there's no downside to trying it.
            if self.throw_item_enabled and skills["stealth"] < m_def and self._pick_throwable_item():
                return "throw_item"
            return "sneak"
        else:
            return "fight"

    def calculate_score(self, chosen_house_name=None, failed_adventurer=False):
        self.sell_all_for_capital()

        bought_house = None
        house_mult = 0
        if chosen_house_name:
            for h in HOUSES:
                if h["name"] == chosen_house_name and self.cash >= h["cost"]:
                    bought_house = h
                    self.cash -= h["cost"]
                    house_mult = h["multiplier"]
                    break

        pension_val = self.get_pension()
        final_score = (house_mult * pension_val) if bought_house else pension_val
        if failed_adventurer:
            final_score = round(final_score * 0.25)
        return {
            "hero_name": self.hero_name,
            "house": bought_house["name"] if bought_house else "Tavern",
            "pension": pension_val,
            "remaining_cash": self.cash,
            "score": final_score,
            "failed_adventurer": failed_adventurer
        }


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
    EQUIPMENT_SLOT_LABELS = {
        "fighting_weapon": "Fighting Weapon",
        "defending_armor": "Defending Armor",
        "salvaging_tool": "Salvaging Tool",
        "spotting_item": "Spotting Item",
        "camping_medical": "Camping / Medical",
        "accessory_1": "Accessory 1",
        "accessory_2": "Accessory 2",
    }
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
    # Repeat-encounter callbacks for regular journey monsters, keyed by how
    # many times this monster has been faced this run (2nd, 3rd, 4th+).
    REPEAT_ENCOUNTER_TEMPLATES = {
        2: [
            "While walking through {leg_vibe}, {hero_name} ran into another {monster_name} - maybe it's the first one's brother.",
            "On {leg_vibe}, {hero_name} spotted a second {monster_name}, oddly familiar around the eyes.",
            "Near {leg_vibe}, {hero_name} crossed paths with another {monster_name}, which felt like too much of a coincidence.",
            "While crossing {leg_vibe}, {hero_name} found a second {monster_name} - small world, apparently.",
        ],
        3: [
            "While crossing {leg_vibe}, {hero_name} encountered yet another {monster_name} - this one seemed particularly vengeful.",
            "On {leg_vibe}, {hero_name} found a third {monster_name} and started to suspect a conspiracy.",
            "Near {leg_vibe}, {hero_name} met another {monster_name}, who looked personally aggrieved on behalf of the others.",
            "While walking through {leg_vibe}, {hero_name} sighed at yet another {monster_name} blocking the way.",
        ],
        "many": [
            "While walking through {leg_vibe}, {hero_name} braced for the {ordinal} {monster_name} of the trip.",
            "On {leg_vibe}, {hero_name} has now met so many {monster_name_plural} that this one got a nickname.",
            "Near {leg_vibe}, {hero_name} rolled their eyes at the {ordinal} {monster_name} - at this point it's basically a rivalry.",
            "While crossing {leg_vibe}, {hero_name} wondered if the {monster_name_plural} were breeding on purpose just to annoy them.",
        ],
    }
    # Opening backstory paragraph, shown once after character creation.
    ORIGIN_STORY_TEMPLATES = [
        "{hero_name} grew up in {hometown}, raised in no small part by {family_article} {family_member} who {family_trait}. When the day finally came to leave, the only thing louder than the goodbyes was the hope of getting to {aspiration}.",
        "Home was {hometown}, and for {hero_name} it meant {family_article} {family_member} who {family_trait}. Leaving wasn't easy, but the pull to {aspiration} won out in the end.",
        "Before any of this, {hero_name} was just someone from {hometown} - the kind of place where {family_article} {family_member} {family_trait}. All {hero_name} ever wanted was to {aspiration}.",
        "{hero_name}'s story starts in {hometown}, where {family_article} {family_member} {family_trait} and never let anyone forget it. The road out began with one simple hope: to {aspiration}.",
    ]
    # Occasional extra sentence appended to journey narration, pulling from
    # backstory / town job history / special moments / monster tallies - see
    # _maybe_add_reminiscence(). Keyed by source, not by screen/event.
    REMINISCENCE_TEMPLATES = {
        "town_job": [
            "For a moment, {hero_name} thought back to the year spent as a {modifier} {profession}, and how a {injury} to the {body_part} never quite faded.",
            "{hero_name} remembered the year as a {modifier} {profession} - that old {injury} to the {body_part} still aches sometimes.",
            "A stray thought drifted back to the year working as a {modifier} {profession}, {body_part} still recalling that old {injury}.",
        ],
        "monster_tally": [
            "{hero_name} thought about all the {monster_name_plural} faced so far, and wondered, not for the first time, whether they have families.",
            "Somewhere around the {ordinal} {monster_name}, {hero_name} started keeping an unofficial tally, whether they meant to or not.",
            "{hero_name} couldn't help but notice how many {monster_name_plural} this road had produced by now.",
        ],
        "relic_found": [
            "{hero_name} thought back to finding the {relic_name} - still one of the stranger days of this whole trip.",
            "For a moment {hero_name} remembered the day the {relic_name} turned up, and how little sense it made at the time.",
        ],
        "dungeon_boss_beaten": [
            "{hero_name} remembered clearing {dungeon_name} and the fight with {boss_name} - a good day, all things considered.",
            "A memory surfaced of {dungeon_name} and the fight against {boss_name}, still vivid after all this time.",
        ],
        "repeat_monster": [
            "{hero_name} remembered the run of {monster_name_plural} that kept turning up around the {ordinal} encounter - hard to forget that stretch.",
        ],
        "backstory_family": [
            "For a moment, {hero_name} thought of home in {hometown}, and {family_article} {family_member} who {family_trait}.",
            "{hero_name} pictured {hometown} for a moment, and the {family_member} who {family_trait}.",
            "A flicker of home crossed {hero_name}'s mind - {hometown}, and {family_article} {family_member} who {family_trait}.",
        ],
        "backstory_aspiration": [
            "{hero_name} remembered, as always, the whole reason for this journey: to {aspiration}.",
            "It came back around again, as it always did - {hero_name} was out here to {aspiration}.",
            "For a moment, {hero_name} remembered exactly why this road was worth it: to {aspiration}.",
        ],
    }
    REMINISCENCE_CHANCE = 0.18
    REMINISCENCE_ELIGIBLE_EVENTS = {
        "fight", "dungeon_found", "wandering_trader", "magic_shrine",
        "super_monster", "wander_group", "fairy_found", "dungeon_floor", "dungeon_boss",
    }
    NARRATION_EVENT_SCREENS = {
        "journey", "dungeon_found", "town_recovery", "wandering_trader",
        "magic_shrine_event", "super_monster_preview", "combat", "dungeon_floor_preview",
        "dungeon_boss_preview", "origin_story",
    }
    SAVE_VERSION = 1
    SAVE_DIR = Path(__file__).resolve().parent / "saves"

    def __init__(self):
        self.engine = None
        self.screen = "front_page"
        self.pending_name = ""
        self.pending_class = ""
        self.creation_message = ""
        self.scores = []
        self.quit_requested = False
        self.ctx = {}
        self.previous_screen = "journey"
        self.inventory_return_screen = "journey"
        self.dungeon_pending = None
        self.trader_offer = []
        self.town_shop_offer = []
        self._save_slot_paths = []
        self.levelup_chosen = []
        self.selected_item_letter = None
        self.current_narration = ""
        self.loot_discarded_indices = set()
        self.failed_adventurer = False
        # Instrumentation only (not persisted in saves): counts how many
        # times each narration template (category:index) has been chosen
        # this playthrough, so we can measure repetition - see
        # narrative_instrument.py.
        self.line_usage_counts = {}

    def _save_payload(self):
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

    def _restore_payload(self, payload):
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

    def _set_menu_message(self, text):
        if self.screen == "front_page":
            self.ctx["menu_message"] = text

    def _set_save_message(self, text):
        if self.screen in ("journey", "inventory"):
            self.ctx["save_message"] = text

    def _build_leg_vibe(self):
        if not self.engine:
            return "the road"
        return self.LEG_VIBES.get(
            self.engine.current_leg_idx + 1,
            LEGS[self.engine.current_leg_idx]["name"].lower(),
        )

    @staticmethod
    def _ordinal(n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def _choose_template(self, category, templates):
        """Picks a random template and records (category:index) usage for
        the line-reuse instrumentation (see narrative_instrument.py)."""
        idx = random.randrange(len(templates))
        key = f"{category}:{idx}"
        self.line_usage_counts[key] = self.line_usage_counts.get(key, 0) + 1
        return templates[idx]

    def _set_narration(self, event_type, **kwargs):
        encounter_count = kwargs.pop("encounter_count", None)
        if event_type == "fight" and encounter_count and encounter_count > 1:
            tier = encounter_count if encounter_count in (2, 3) else "many"
            templates = self.REPEAT_ENCOUNTER_TEMPLATES[tier]
            data = {
                "hero_name": self.engine.hero_name if self.engine else "the Hero",
                "leg_vibe": self._build_leg_vibe(),
                "ordinal": self._ordinal(encounter_count),
                "monster_name_plural": f"{kwargs.get('monster_name', '')}s",
            }
            data.update(kwargs)
            self.current_narration = self._choose_template(f"repeat_encounter_{tier}", templates).format(**data)
            return self.current_narration
        templates = self.EVENT_NARRATION_TEMPLATES.get(event_type, [])
        if not templates:
            self.current_narration = ""
            return ""
        data = {
            "hero_name": self.engine.hero_name if self.engine else "the Hero",
            "leg_vibe": self._build_leg_vibe(),
        }
        data.update(kwargs)
        self.current_narration = self._choose_template(f"event_{event_type}", templates).format(**data)
        self._maybe_add_reminiscence(event_type)
        return self.current_narration

    def _maybe_add_reminiscence(self, event_type):
        """With low probability, appends one extra sentence of "remember
        when..." flavor to the just-built narration, pulled from whichever
        of these the hero actually has: past town jobs, monsters faced 3+
        times, logged special moments, or their fixed backstory. Cheap by
        design - all sources are data already being tracked for other
        reasons, nothing new is generated here."""
        e = self.engine
        if not e or event_type not in self.REMINISCENCE_ELIGIBLE_EVENTS:
            return
        if random.random() >= self.REMINISCENCE_CHANCE:
            return
        sources = []
        if e.town_history:
            sources.append("town_job")
        tallied = [m for m, c in e.monster_encounter_counts.items() if c >= 3]
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
        data = {"hero_name": e.hero_name}
        if source == "town_job":
            data.update(random.choice(e.town_history))
            text = self._choose_template("reminiscence_town_job", self.REMINISCENCE_TEMPLATES["town_job"]).format(**data)
        elif source == "monster_tally":
            monster = random.choice(tallied)
            data.update({
                "monster_name": monster,
                "monster_name_plural": f"{monster}s",
                "ordinal": self._ordinal(e.monster_encounter_counts[monster]),
            })
            text = self._choose_template("reminiscence_monster_tally", self.REMINISCENCE_TEMPLATES["monster_tally"]).format(**data)
        elif source == "special_moment":
            moment = random.choice(e.special_moments)
            moment_type = moment["type"]
            templates = self.REMINISCENCE_TEMPLATES.get(moment_type)
            if not templates:
                return
            data.update({k: v for k, v in moment.items() if k not in ("type", "leg")})
            if moment_type == "repeat_monster":
                data["monster_name_plural"] = f"{moment.get('monster_name', '')}s"
                data["ordinal"] = self._ordinal(moment.get("count", 3))
            text = self._choose_template(f"reminiscence_{moment_type}", templates).format(**data)
        else:
            data.update(e.backstory)
            text = self._choose_template(f"reminiscence_{source}", self.REMINISCENCE_TEMPLATES[source]).format(**data)
        self.current_narration = f"{self.current_narration} {text}".strip()

    def _generate_backstory(self):
        family_member = random.choice(HERO_FAMILY_MEMBERS)
        return {
            "hometown": random.choice(HERO_HOMETOWNS),
            "family_member": family_member,
            "family_article": "an" if family_member[:1].lower() in "aeiou" else "a",
            "family_trait": random.choice(HERO_FAMILY_TRAITS),
            "aspiration": random.choice(HERO_ASPIRATIONS),
        }

    def _build_origin_story(self):
        e = self.engine
        data = {"hero_name": e.hero_name}
        data.update(e.backstory)
        paragraph = self._choose_template("origin_story", self.ORIGIN_STORY_TEMPLATES).format(**data)
        closer = self._choose_template("origin_story_closer", ORIGIN_STORY_CLOSERS)
        return f"{paragraph} {closer}"

    # ------------------------------------------------------------------
    # Item letter helpers (DCSS-style lettered inventory, shared by the
    # inventory, item detail, and wandering trader "sell" screens)
    # ------------------------------------------------------------------
    def _letter_items(self):
        """Returns an ordered list of (letter, item, equipped_slot_or_None)."""
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
        e = self.engine
        if e:
            skills, total_weight, max_weight = e.get_effective_skills()
            leg_info = LEGS[e.current_leg_idx]
            equipped_summary = ", ".join(item["name"] for item in e.equipment.values() if item) or "(none)"
            ctx.update({
                "hero_name": e.hero_name, "hero_class": e.hero_class,
                "hp": e.hp, "max_hp": e.max_hp, "cash": e.cash, "age": e.age,
                "leg": e.current_leg_idx + 1, "leg_name": leg_info["name"],
                "event": e.leg_event_count, "dungeons_found": e.dungeons_found_in_leg,
                "fighting": skills["fighting"], "defending": skills["defending"],
                "magic": skills["magic"], "stealth": skills["stealth"],
                "salvaging": skills["salvaging"], "spotting": skills["spotting"],
                "camping": skills["camping"], "medical": skills["medical"],
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
        ctx["event_narration"] = self.current_narration if self.screen in self.NARRATION_EVENT_SCREENS else ""
        ctx["pending_name"] = self.pending_name
        ctx["pending_class"] = self.pending_class or "(none)"
        ctx["creation_message"] = self.creation_message
        ctx["levelup_count"] = len(self.levelup_chosen)
        ctx["load_available"] = self.SAVE_DIR.exists() and any(self.SAVE_DIR.glob("*.json"))
        ctx["failed_adventurer"] = self.failed_adventurer

        if self.screen == "inventory":
            ctx["list_inventory"] = self._build_inventory_rows()
            ctx["character_title"] = self._character_title()
            ctx["honor_mark"] = min(15, self.engine.super_monsters_defeated + self.engine.dungeons_cleared)
            ctx["karma"] = self.engine.karma
            ctx["list_character_stats"] = self._build_character_stats_rows()
            ctx["list_character_equipment"] = self._build_character_equipment_rows()
        elif self.screen == "loot_screen":
            ctx["loot_lines"] = self._build_combat_loot_rows()
        elif self.screen == "item_detail":
            item, slot = self._find_letter_item(self.selected_item_letter)
            if item:
                stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
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

    def _item_highlight(self, item):
        """Returns 'better', 'worse', or None for a backpack item, comparing it
        only against the equipped item in the same slot that shares its skill
        effect (an empty slot always counts as 'better')."""
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
        equipped = self.engine.equipment.get(target_slot)
        if not equipped:
            return "better"
        if equipped.get("skill") != skill:
            return None
        return "better" if item.get("skill_val", 0) > equipped.get("skill_val", 0) else "worse"

    # Grouping order/labels for the inventory list - items are broken into
    # slot sections (with a plain header row) so a full backpack is still
    # easy to scan while scrolling.
    INVENTORY_SLOT_GROUPS = [
        ("fighting_weapon", "Weapons"),
        ("defending_armor", "Armor"),
        ("salvaging_tool", "Salvaging Tools"),
        ("spotting_item", "Spotting Items"),
        ("camping_medical", "Camping / Medical Items"),
        ("accessory", "Accessories"),
    ]

    def _build_inventory_rows(self):
        groups = {slot: [] for slot, _label in self.INVENTORY_SLOT_GROUPS}
        other = []
        for letter, item, slot in self._letter_items():
            tag = "\u2705 Equipped" if slot else "\U0001f392 Backpack"
            stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            text = (f"{letter} - [{tag}] {item['name']} ({item.get('tier', '')}) "
                    f"{stat} | ${item['value']} | {item['weight']}wt")
            highlight = None if slot else self._item_highlight(item)
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
            stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            tag = "\u274c DISCARD" if idx in self.loot_discarded_indices else "\u2705 KEEP"
            text = (f"[{tag}] {item['name']} ({item.get('tier', '')}) {stat} | "
                    f"${item['value']} | {item['weight']}wt")
            rows.append({"text": text, "action": f"toggle_loot_item:{idx}", "enabled": True})
        return rows

    def _build_character_stats_rows(self):
        skills, _, _ = self.engine.get_effective_skills()
        rows = []
        for skill in ("fighting", "defending", "magic", "stealth", "spotting", "salvaging", "camping", "medical"):
            base = self.engine.base_skills.get(skill, 0)
            effective = skills.get(skill, base)
            delta = effective - base
            delta_text = f"+{delta}" if delta >= 0 else str(delta)
            rows.append({
                "text": f"{skill.title():<10}  Base: {base:<3}  Effective: {effective:<3}  Net: {delta_text}",
                "action": None,
                "enabled": False,
            })
        return rows

    def _build_character_equipment_rows(self):
        rows = []
        for slot, item in self.engine.equipment.items():
            label = self.EQUIPMENT_SLOT_LABELS.get(slot, slot)
            if not item:
                rows.append({"text": f"{label}: (empty)", "action": None, "enabled": False})
                continue
            if item.get("skill"):
                bonus = f"+{item.get('skill_val', 0)} {item.get('skill', '')}"
            else:
                bonus = "Relic effect"
            rows.append({
                "text": f"{label}: {item['name']} ({item.get('tier', '')}) {bonus} | {item['weight']}wt",
                "action": None,
                "enabled": False,
            })
        return rows

    def _leg_monster_cap(self, stat_name):
        leg = self.engine.current_leg_idx + 1
        values = [data.get(stat_name, 0) for data in MONSTERS.values() if data.get("leg") == leg]
        return max(values) if values else 0

    def _band_for_title(self, value, cap):
        if cap <= 0:
            return "neutral"
        if value >= cap * 0.75:
            return "high"
        if value <= cap * 0.25:
            return "low"
        return "neutral"

    def _character_title(self):
        if not self.engine:
            return ""

        skills, _, _ = self.engine.get_effective_skills()
        fight_band = self._band_for_title(skills["fighting"], self._leg_monster_cap("fighting"))
        def_band = self._band_for_title(skills["defending"], self._leg_monster_cap("defending"))
        magic_band = self._band_for_title(skills["magic"], self._leg_monster_cap("magic"))
        sneak_band = self._band_for_title(skills["stealth"], self._leg_monster_cap("defending"))

        if magic_band == "high":
            attack_title = CHARACTER_TITLE_PARTS["magic_high"]
        elif magic_band == "low":
            attack_title = CHARACTER_TITLE_PARTS["magic_low"]
        elif sneak_band == "high":
            attack_title = CHARACTER_TITLE_PARTS["stealth_high"]
        elif sneak_band == "low":
            attack_title = CHARACTER_TITLE_PARTS["stealth_low"]
        elif fight_band == "high":
            attack_title = CHARACTER_TITLE_PARTS["fight_high"]
        elif fight_band == "low":
            attack_title = CHARACTER_TITLE_PARTS["fight_low"]
        else:
            attack_title = CHARACTER_TITLE_PARTS["balanced_attack"]

        defense_title = ""
        if def_band == "high":
            defense_title = CHARACTER_TITLE_PARTS["defense_high"]
        elif def_band == "low":
            defense_title = CHARACTER_TITLE_PARTS["defense_low"]

        core_parts = []
        if attack_title != CHARACTER_TITLE_PARTS["balanced_attack"]:
            core_parts.append(attack_title)
        if defense_title:
            core_parts.append(defense_title)
        if not core_parts:
            core_parts.append(CHARACTER_TITLE_PARTS["balanced_adventurer"])
        core_title = ", ".join(core_parts)

        honor_mark = min(15, self.engine.super_monsters_defeated + self.engine.dungeons_cleared)
        karma = self.engine.karma
        if karma < 0:
            karma_mark = min(15, (-karma) // 5)
            honor = self.NEGATIVE_KARMA_TITLES[karma_mark]
        else:
            honor = self.HONORIFIC_TITLES[honor_mark]
        if honor["placement"] == "prefix":
            if honor["text"] == "The unproven":
                return f"{honor['text']} {core_title}"
            return f"{honor['text']}, {core_title}"
        return f"{core_title}, {honor['text']}"

    def _build_levelup_rows(self):
        rows = []
        for skill, val in self.engine.base_skills.items():
            chosen = skill in self.levelup_chosen
            can_pick = not chosen and len(self.levelup_chosen) < 3
            text = f"{skill.title()}: {val}" + (" [chosen]" if chosen else "")
            rows.append({"text": text, "action": f"pick_levelup_skill:{skill}" if can_pick else None,
                         "enabled": can_pick})
        return rows

    def _build_house_rows(self):
        options, _pension = self.engine.get_house_options()
        rows = []
        for h in options:
            text = f"{h['name']} - ${h['cost']} (x{h['multiplier']})"
            if h["affordable"]:
                text += f" -> Score: {h['score']}"
            else:
                text += " (can't afford)"
            rows.append({"text": text, "action": f"buy_house:{h['name']}" if h["affordable"] else None,
                         "enabled": h["affordable"]})
        return rows

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
        mult = self.engine.trader_buy_multiplier()
        rows = []
        for idx, item in enumerate(self.trader_offer):
            cost = int(item["value"] * mult)
            affordable = self.engine.cash >= cost
            text = f"{item['name']} ({item.get('tier', '')}) - ${cost}" + ("" if affordable else " (can't afford)")
            rows.append({"text": text, "action": f"trader_buy:{idx}" if affordable else None, "enabled": affordable})
        if not rows:
            rows.append({"text": "(Sold out)", "action": None, "enabled": False})
        return rows

    def _build_trader_sell_rows(self):
        mult = self.engine.trader_sell_multiplier()
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
        mult = self.engine.trader_buy_multiplier()
        rows = []
        for idx, item in enumerate(self.town_shop_offer):
            cost = int(item["value"] * mult)
            affordable = self.engine.cash >= cost
            text = f"{item['name']} ({item.get('tier', '')}) - ${cost}" + ("" if affordable else " (can't afford)")
            rows.append({"text": text, "action": f"town_buy:{idx}" if affordable else None, "enabled": affordable})
        if not rows:
            rows.append({"text": "(Sold out)", "action": None, "enabled": False})
        return rows

    def _build_town_sell_rows(self):
        mult = self.engine.trader_sell_multiplier()
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
            stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            text = f"{item['name']} ({item.get('tier', '')}) {stat} | ${item['value']} | {item['weight']}wt"
            lines.append({"text": text, "action": None, "enabled": False})
        if not lines:
            lines.append({"text": "No items dropped.", "action": None, "enabled": False})
        return lines

    def _format_combat_rounds(self, round_details, fallback_lines):
        rows = []
        outcome_labels = {
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
            facts_text = f" ({'; '.join(facts)})" if facts else ""
            label = outcome_labels.get(detail.get("outcome"), "EVENT")
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
    def dispatch(self, action):
        if not action:
            return
        if ":" in action:
            verb, arg = action.split(":", 1)
        else:
            verb, arg = action, None

        if verb == "goto":
            self.screen = arg
            return

        handler = getattr(self, f"_action_{verb}", None)
        if handler is None:
            return  # unknown action - ignore defensively rather than crash
        if arg is not None:
            handler(arg)
        else:
            handler()

    def set_pending_name(self, name):
        self.pending_name = (name or "").strip()

    # -- Front page / character creation --------------------------------
    def _action_new_game(self):
        self.pending_name = ""
        self.pending_class = ""
        self.creation_message = ""
        self.engine = None
        self.ctx = {}
        self.current_narration = ""
        self.screen = "character_creation"

    def _action_select_class(self, class_name):
        if class_name not in CLASSES:
            return
        self.pending_class = class_name
        self._action_confirm_character()

    def _action_confirm_character(self):
        if not self.pending_name or not self.pending_class:
            return
        if self._save_name_exists(self.pending_name):
            self.creation_message = (
                f"A save already exists for '{self.pending_name}'. "
                "Choose a different name or load that save instead."
            )
            return
        self.creation_message = ""
        self.engine = HeroAdventureEngine(self.pending_name, self.pending_class)
        self.engine.backstory = self._generate_backstory()
        self.line_usage_counts = {}
        self.current_narration = self._build_origin_story()
        self.screen = "origin_story"

    def _action_origin_continue(self):
        self.ctx = {}
        self.current_narration = ""
        self.screen = "journey"

    def _action_quit(self):
        self.quit_requested = True

    @staticmethod
    def _slot_filename(hero_name):
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in hero_name.strip())
        return safe or "hero"

    def _save_slot_path(self, hero_name):
        return self.SAVE_DIR / f"{self._slot_filename(hero_name)}.json"

    def _save_name_exists(self, hero_name):
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

    def _action_view_load_game(self):
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

    def _action_load_slot(self, idx_str):
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

    def _action_save_game(self):
        if not self.engine:
            self._set_menu_message("Start or load a game before saving.")
            return
        try:
            self.SAVE_DIR.mkdir(exist_ok=True)
            payload = self._save_payload()
            path = self._save_slot_path(self.engine.hero_name)
            tmp_path = path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, separators=(",", ":")))
            tmp_path.replace(path)
            self._set_save_message(f"Game saved to {path.name}.")
        except OSError:
            self._set_save_message("Failed to save game.")

    def _action_save_and_quit(self):
        self._action_save_game()
        self.ctx = {}
        self.screen = "front_page"

    # -- Inventory (openable from journey/combat, returns to prior screen) --
    def _action_open_inventory(self):
        origin = self.screen if self.screen != "inventory" else (self.inventory_return_screen or "journey")
        self.previous_screen = origin
        self.inventory_return_screen = origin
        self.screen = "inventory"

    def _action_close_inventory(self):
        target = self.inventory_return_screen or self.previous_screen or "journey"
        if target == "inventory":
            target = "journey"
        self.screen = target

    def _action_select_item(self, letter):
        self.selected_item_letter = letter
        self.screen = "item_detail"

    def _action_item_back(self):
        self.selected_item_letter = None
        self.screen = "inventory"

    def _action_equip_item(self):
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
        old = self.engine.equipment.get(target_slot)
        if old:
            self.engine.inventory.append(old)
        self.engine.equipment[target_slot] = item
        self.screen = "inventory"
        self.selected_item_letter = None

    def _action_unequip_item(self):
        letter = self.selected_item_letter
        item, slot = self._find_letter_item(letter)
        if item and slot is not None:
            self.engine.equipment[slot] = None
            self.engine.inventory.append(item)
        self.screen = "inventory"
        self.selected_item_letter = None

    def _action_drop_item(self):
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
    def _action_advance_event(self):
        e = self.engine
        if len(e.inventory) > INVENTORY_ITEM_CAP:
            self.ctx["inventory_full_message"] = (
                f"Your pack is overflowing ({len(e.inventory)}/{INVENTORY_ITEM_CAP}). "
                "Sell or drop items before continuing."
            )
            return
        e.leg_event_count += 1

        dungeon = e.try_spot_dungeon()
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

        transition = e.try_leg_transition()
        if transition == "LEVEL_UP":
            self._enter_town_recovery()
            return
        elif transition == "CAPITAL":
            e.sell_all_for_capital()
            self.failed_adventurer = False
            self.ctx = {}
            self.screen = "capital"
            return

        event_type = e.roll_journey_event_type()
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
            transition = e.try_leg_transition()
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
            monster = e.get_random_monster()
            e.monster_encounter_counts[monster] = e.monster_encounter_counts.get(monster, 0) + 1
            count = e.monster_encounter_counts[monster]
            if count == 3:
                e._log_special_moment("repeat_monster", monster_name=monster, count=count)
            self._set_narration("fight", monster_name=monster, encounter_count=count)
            self._start_combat(monster, "regular", allow_run=True)

    # -- Town Recovery (aging) ------------------------------------------
    def _generate_town_blurb(self, job_offer=False):
        profession = random.choice(TOWN_PROFESSIONS)
        modifier = random.choice(TOWN_PROFESSION_MODIFIERS)
        injury = random.choice(TOWN_INJURIES)
        body_part = random.choice(TOWN_BODY_PARTS)
        event_type = "town_job_offer" if job_offer else "town_recovery"
        blurb = self._set_narration(
            event_type, profession=profession, modifier=modifier,
            injury=injury, body_part=body_part,
        )
        self.engine.town_history.append({
            "profession": profession, "modifier": modifier,
            "injury": injury, "body_part": body_part, "age": self.engine.age,
        })
        self.engine.town_history = self.engine.town_history[-10:]
        return blurb, profession

    def _enter_town_recovery(self):
        """Mandatory town stop at the start of a new leg. Skipped entirely
        if the hero is already at full HP; otherwise plays out one year at
        a time (10 HP healed per year, hero ages by 1), with a per-year
        5% chance of a permanent job offer and a forced failed-adventurer
        ending if age 50 is reached."""
        if self.engine.hp >= self.engine.max_hp:
            self._enter_level_up()
            return
        self.town_shop_offer = self.engine.generate_trader_offer()
        self._prepare_town_year()

    def _enter_level_up(self):
        self.levelup_chosen = []
        self.ctx = {}
        self.screen = "level_up"

    def _prison_chance(self):
        """Odds of a town-recovery year being spent in jail instead of
        working, curved on negative karma: 0 while karma is neutral/positive,
        then climbing steeply and asymptotically toward (never reaching)
        PRISON_CHANCE_CAP as karma gets more negative."""
        karma = self.engine.karma if self.engine else 0
        if karma >= 0:
            return 0.0
        magnitude = -karma
        return PRISON_CHANCE_CAP * (1 - math.exp(-magnitude / PRISON_KARMA_SCALE))

    def _prepare_town_year(self):
        e = self.engine
        if random.random() < self._prison_chance():
            blurb = self._set_narration("town_prison")
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
        heal = min(DAMAGE_PER_TOWN_YEAR, e.max_hp - e.hp)
        e.hp = min(e.max_hp, e.hp + heal)
        e.age += 1
        e.log("TOWN_RECOVERY_YEAR", {"age": e.age, "heal": heal, "hp": e.hp})
        if e.age >= FORCED_RETIREMENT_AGE:
            self._enter_failed_adventurer(blurb)
            return
        self.ctx = {"town_job_offer": False, "town_fully_healed": e.hp >= e.max_hp,
                     "event_narration": blurb}
        self.screen = "town_recovery"

    def _enter_failed_adventurer(self, blurb):
        e = self.engine
        e.sell_all_for_capital()
        self.failed_adventurer = True
        self.ctx = {"failed_adventurer_text": blurb}
        self.screen = "capital"

    def _action_town_work(self):
        if self.ctx.get("town_job_offer"):
            return
        self._prepare_town_year()

    def _action_town_buy(self, idx_str):
        idx = int(idx_str)
        if 0 <= idx < len(self.town_shop_offer):
            item = self.town_shop_offer[idx]
            if self.engine.trader_buy(item):
                self.town_shop_offer.pop(idx)

    def _action_town_sell(self, letter):
        item, slot = self._find_letter_item(letter)
        if item and slot is None:
            self.engine.trader_sell(item)

    def _action_town_leave(self):
        self.town_shop_offer = []
        self.ctx = {}
        self._enter_level_up()

    def _action_town_retire(self):
        e = self.engine
        profession = self.ctx.get("town_profession", "adventurer")
        e.sell_all_for_capital()
        pension = e.get_pension()
        result = f"Retired early as a {profession}"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": pension, "result": result})
        self.town_shop_offer = []
        self.ctx = {"final_house": result, "final_score": pension, "final_pension": pension}
        self.screen = "capital_result"

    def _go_to_journey(self, outcome_text=""):
        """Returns to the journey screen carrying a one-shot outcome summary
        (rendered in green) so completing an event doesn't look identical
        to a brand-new one. The next _action_advance_event() call replaces
        self.ctx wholesale, so this text naturally disappears."""
        self.ctx = {"last_outcome_text": outcome_text}
        self.screen = "journey"
        # Force-save after every completed event so progress is never lost.
        self._action_save_game()

    def _action_continue_journey(self):
        self._go_to_journey()

    def _action_magic_shrine_continue(self):
        cash = self.ctx.get("loot_cash", 0)
        items = self.ctx.get("loot_items") or []
        item_part = f" and {len(items)} item(s)" if items else ""
        self._go_to_journey(f"The shrine granted you ${cash}{item_part}.")

    # -- Super monster ------------------------------------------------------
    def _action_fight_super_monster(self):
        sm_name = self.ctx.get("monster_name")
        if sm_name:
            self._set_narration("super_monster", monster_name=sm_name)
        self._start_combat(sm_name, "super_monster", allow_run=False)

    def _action_ignore_super_monster(self):
        self._go_to_journey("You avoid the super monster and continue on your way.")

    # -- Dungeons -------------------------------------------------------
    def _action_enter_dungeon(self):
        self.engine.enter_dungeon(self.dungeon_pending)
        self.dungeon_pending = None
        self._enter_dungeon_floor_preview()

    def _action_ignore_dungeon(self):
        self.dungeon_pending = None
        self._go_to_journey("You leave the dungeon entrance undisturbed.")

    def _enter_dungeon_floor_preview(self):
        e = self.engine
        monster_name = e.get_dungeon_floor_monster()
        m = MONSTERS[monster_name]
        is_boss = e.dungeon_event_count >= 5
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
        self.screen = "dungeon_boss_preview" if is_boss else "dungeon_floor_preview"

    def _action_engage_floor(self):
        is_boss = self.ctx.get("is_boss", False)
        monster = self.ctx.get("floor_monster")
        self._start_combat(monster, "dungeon_boss" if is_boss else "dungeon_floor", allow_run=False)

    def _action_exit_dungeon(self):
        self.engine.leave_dungeon(DUNGEON_EXIT_REASONS["voluntary"])
        self._go_to_journey("You retreat from the dungeon.")

    def _dungeon_victory(self):
        e = self.engine
        treasure = random.randint(200, 500)
        e.cash += treasure
        e.leave_dungeon(DUNGEON_EXIT_REASONS["boss_defeated"])
        self.ctx = {"treasure": treasure}
        self.screen = "dungeon_victory"

    def _action_dungeon_victory_continue(self):
        treasure = self.ctx.get("treasure", 0)
        self._go_to_journey(f"You cleared the dungeon and found ${treasure} in treasure!")

    # -- Wandering trader -----------------------------------------------
    def _action_trader_buy(self, idx_str):
        idx = int(idx_str)
        if 0 <= idx < len(self.trader_offer):
            item = self.trader_offer[idx]
            if self.engine.trader_buy(item):
                self.trader_offer.pop(idx)

    def _action_trader_sell(self, letter):
        item, slot = self._find_letter_item(letter)
        if item and slot is None:
            self.engine.trader_sell(item)

    def _action_leave_trader(self):
        self.trader_offer = []
        self._go_to_journey("You part ways with the wandering trader.")

    # -- Level up ---------------------------------------------------------
    def _action_pick_levelup_skill(self, skill):
        e = self.engine
        if skill in e.base_skills and skill not in self.levelup_chosen and len(self.levelup_chosen) < 3:
            e.apply_level_up(skill)
            self.levelup_chosen.append(skill)

    def _action_levelup_continue(self):
        if len(self.levelup_chosen) < 3:
            return
        self.engine.advance_to_next_leg()
        self.levelup_chosen = []
        self._go_to_journey("You finish training and set out for the next leg.")

    # -- Combat -----------------------------------------------------------
    def _start_combat(self, monster_name, kind, allow_run=True):
        m = MONSTERS[monster_name]
        if not self.current_narration:
            event_type = "dungeon_boss" if kind == "dungeon_boss" else "dungeon_floor" if kind == "dungeon_floor" else "fight"
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
            "has_throwable_item": bool(self.engine._pick_throwable_item()),
            "event_narration": self.current_narration,
        }
        self.screen = "combat"

    def _action_fight(self):
        self._resolve_combat_choice("fight")

    def _action_sneak(self):
        self._resolve_combat_choice("sneak")

    def _action_steal(self):
        self._resolve_combat_choice("steal")

    def _action_stealth_kill(self):
        self._resolve_combat_choice("stealth_kill")

    def _action_throw_item(self):
        self._resolve_combat_choice("throw_item")

    def _action_run_away(self):
        monster = self.ctx.get("monster_name", "the monster")
        self._go_to_journey(f"You run from {monster} and hurry back to the road.")

    def _resolve_combat_choice(self, choice):
        e = self.engine
        monster = self.ctx["monster_name"]
        kind = self.ctx.get("combat_kind", "regular")
        before_hp = e.hp
        before_cash = e.cash
        before_len = len(e.inventory)

        res = e.resolve_fight(monster, choice=choice, encounter_type=kind)
        combat_summary = e.last_combat_summary if isinstance(e.last_combat_summary, dict) else {}
        rounds_text = ""
        if combat_summary.get("rounds"):
            rounds_text = f" ({combat_summary['rounds']} rounds)"
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
            damage = before_hp - e.hp
            self.ctx["result_text"] = f"You were bested by {monster}{rounds_text}! You take {damage} damage."
            self.ctx["result_won"] = False
            self.ctx["damage"] = damage
            if kind in ("dungeon_floor", "dungeon_boss"):
                e.leave_dungeon(DUNGEON_EXIT_REASONS["combat_defeat"])
        else:
            cash_gained = e.cash - before_cash
            new_items = e.inventory[before_len:]
            self.ctx["result_text"] = f"Victory! You defeat {monster}{rounds_text}."
            self.ctx["result_won"] = True
            self.ctx["loot_cash"] = cash_gained
            self.ctx["loot_items"] = new_items
            self.ctx["loot_lines"] = self._format_loot_lines(new_items)

        self.ctx["combat_rounds"] = combat_rounds

        self.screen = "death" if e.game_over else "combat_result"

    def _action_combat_continue(self):
        if not self.ctx.get("result_won"):
            self._go_to_journey(self.ctx.get("result_text", ""))
            return
        if self.ctx.get("loot_items"):
            self.loot_discarded_indices = set()
            self.screen = "loot_screen"
        else:
            self._route_after_win()

    def _action_toggle_loot_item(self, idx_str):
        try:
            idx = int(idx_str)
        except (TypeError, ValueError):
            return
        if idx in self.loot_discarded_indices:
            self.loot_discarded_indices.discard(idx)
        else:
            self.loot_discarded_indices.add(idx)

    def _action_loot_continue(self):
        items = self.ctx.get("loot_items") or []
        discarded = [item for idx, item in enumerate(items) if idx in self.loot_discarded_indices]
        if discarded:
            self.engine.inventory = [it for it in self.engine.inventory if not any(it is d for d in discarded)]
        self.loot_discarded_indices = set()
        self._route_after_win()

    def _route_after_win(self):
        kind = self.ctx.get("combat_kind", "regular")
        if kind == "dungeon_floor":
            self.engine.advance_dungeon_floor()
            self._enter_dungeon_floor_preview()
        elif kind == "dungeon_boss":
            self._dungeon_victory()
        else:
            self._go_to_journey(self.ctx.get("result_text", ""))

    # -- Death / Capital ----------------------------------------------------
    def _action_death_continue(self):
        self.engine = None
        self.ctx = {}
        self.screen = "front_page"

    def _action_buy_house(self, house_name):
        e = self.engine
        house = next((h for h in HOUSES if h["name"] == house_name), None)
        if not house or e.cash < house["cost"]:
            return
        pension = e.get_pension()
        e.cash -= house["cost"]
        score = house["multiplier"] * pension
        result = f"Bought {house['name']}"
        if self.failed_adventurer:
            score = round(score * 0.25)
            result += " (Failed Adventurer)"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": score,
                             "result": result})
        self.ctx = {"final_house": house["name"], "final_score": score, "final_pension": pension}
        self.failed_adventurer = False
        self.screen = "capital_result"

    def _action_keep_pension(self):
        e = self.engine
        pension = e.get_pension()
        score = pension
        result = "Tavern"
        if self.failed_adventurer:
            score = round(score * 0.25)
            result += " (Failed Adventurer)"
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": score, "result": result})
        self.ctx = {"final_house": "Tavern", "final_score": score, "final_pension": pension}
        self.failed_adventurer = False
        self.screen = "capital_result"

    def _action_capital_continue(self):
        if self.engine:
            path = self._save_slot_path(self.engine.hero_name)
            if path.exists():
                path.unlink()
        self.engine = None
        self.ctx = {}
        self.screen = "front_page"
