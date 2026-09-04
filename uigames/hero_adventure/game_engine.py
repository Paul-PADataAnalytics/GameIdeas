"""
Core simulation/rules engine for Hero Adventure: HeroAdventureEngine.

Implements the state machine, item inventory management, combat/stealth/steal
checks, weight penalties, dungeon management, and the fast zero-delay
simulation API (step_next_event). Entirely UI-agnostic - see
game_controller.py (GameController) for screen flow and player-facing text,
and sim_runner.py for a headless batch-simulation consumer of this class.
"""

import math
import random
from typing import cast
from game_data import (
    CLASSES, LEGS, MONSTERS, ITEM_CATEGORIES, QUALITY_TIERS,
    RELICS, HOUSES, PENSIONS, DUNGEON_FIND_CHANCE,
    AGE_START, PENSION_END_AGE_MIN, PENSION_END_AGE_MAX, PENSION_BASELINE_YEARS,
    RELIC_MONSTER_SCALE,
    KARMA_STEALTH_KILL_PENALTY, KARMA_STEAL_PENALTY,
    DEATH_REASONS, DUNGEON_EXIT_REASONS, RISK_BANDS,
    MAGIC_SPELL_NAME_PARTS, MAGIC_SHIELD_NAME_PARTS, COMBAT_LINE_POOLS,
    BOSS_BONUS_TIER_BY_LEG, KILL_PHRASES,
    Dungeon, House, Item, ItemCategoryEntry, Leg, Monster, QualityTier, RelicDef,
)


def _build_dungeon_monster_name_set() -> set[str]:
    names: set[str] = set()
    for leg in LEGS:
        for dungeon in leg.get("dungeons", []):
            boss: str | None = dungeon.get("boss")
            if boss:
                names.add(boss)
            for floor_monster in dungeon.get("floors", []):
                names.add(floor_monster)
    return names


DUNGEON_MONSTER_NAMES = _build_dungeon_monster_name_set()
SUPER_MONSTER_NAMES: set[str] = {leg["super_monster"] for leg in LEGS if leg.get("super_monster")}


class HeroAdventureEngine:
    def __init__(self, hero_name: str = "Hero", hero_class: str = "Hitter", fast_mode: bool = True,
                 relic_scaling_enabled: bool = False, stealth_atk_enabled: bool = True,
                 hider_stat_bonus_enabled: bool = True, throw_item_enabled: bool = True) -> None:
        self.fast_mode: bool = fast_mode
        self.hero_name: str = hero_name
        self.hero_class: str = hero_class
        self.skip_journey_fights: bool = False
        # Experimental toggle: scale relic-flagged monsters (bosses/super
        # monsters) independently of regular per-leg monster tuning.
        self.relic_scaling_enabled: bool = relic_scaling_enabled
        # Balance-experiment toggles (all default on; kept togglable purely
        # so sim_runner.py can A/B-test each change in isolation).
        self.stealth_atk_enabled: bool = stealth_atk_enabled
        self.throw_item_enabled: bool = throw_item_enabled
        
        # Base Skills (all start at 5, except speech which starts at 0 and
        # is only ever raised via level-ups/equipment - see trader_buy_multiplier).
        self.base_skills: dict[str, int] = {
            "fighting": 5, "defending": 5, "magic": 5, "stealth": 5,
            "salvaging": 5, "speech": 0
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

        self.hp: int = 100
        self.max_hp: int = 100
        self.cash: int = 0
        self.age: int = AGE_START
        self.end_age: int | None = None  # rolled once (lazily, in get_pension) between 60-90
        # Reputation tracker: starts neutral, only ever decreases (see
        # resolve_fight's stealth_kill/steal branches). Negative karma
        # swaps the hero's title for a villainous one and risks a year in
        # jail during town recovery (see GameController._prison_chance()).
        self.karma: int = 0
        
        # Inventory & Equipment
        self.inventory: list[Item] = []  # items held in backpack
        self.equipment: dict[str, Item | None] = {
            "fighting_weapon": None,
            "defending_armor": None,
            "salvaging_tool": None,
            "accessory_1": None,
            "accessory_2": None
        }
        
        # Journey tracking
        self.current_leg_idx: int = 0  # 0 to 4
        self.leg_event_count: int = 0  # 0 to 20
        self.dungeons_found_in_leg: int = 0  # max 2
        self.super_monster_seen_in_leg: bool = False
        self.super_monsters_defeated: int = 0
        self.dungeons_cleared: int = 0
        self.last_journey_event_turn: dict[str, int] = {}
        self.in_dungeon: bool = False
        self.dungeon_name: str = ""
        self.dungeon_event_count: int = 0  # 0 to 6 (1-5 floor fights, 6 boss)
        self.dungeon_boss: str = ""
        self.dungeon_floors: list[str] = []
        # How many times each regular monster has been encountered on the
        # journey this run - used to give repeat encounters a callback
        # ("...ran into another Cave Spider, maybe it's the first one's
        # brother.") instead of the same generic first-encounter text.
        self.monster_encounter_counts: dict[str, int] = {}
        # Rolled once at character creation (see GameController._generate_backstory)
        # and kept for the whole run - feeds the opening origin story and
        # later in-journey reminiscence lines.
        self.backstory: dict[str, str] = {}
        # Past town-recovery years (profession/modifier/injury/body_part), most
        # recent 10 kept - reminiscence material for "remember that year..." lines.
        self.town_history: list[dict[str, str]] = []
        # Rare/notable run events (relic finds, dungeon bosses beaten, a
        # monster faced 3+ times) kept as a FIFO of the most recent 10 across
        # all types - reminiscence material, deliberately not exhaustive.
        self.special_moments: list[dict] = []
        
        # Relic tracking & state
        self.relics_found: list[str] = []
        self.pendant_used: bool = False
        self.game_over: bool = False
        self.game_won: bool = False
        self.death_reason: str = ""
        
        # Telemetry log
        self.event_logs: list[dict] = []
        self.last_combat_summary: dict = {}

    def log_special_moment(self, moment_type: str, **detail: object) -> None:
        """Records a rare/notable event (relic found, dungeon boss beaten, a
        monster faced 3+ times) for later reminiscence callbacks. Keeps only
        the most recent 10 (FIFO) shared across all moment types - deliberately
        not exhaustive, so only the genuinely memorable stuff survives."""
        self.special_moments.append({"type": moment_type, "leg": self.current_leg_idx + 1, **detail})
        self.special_moments = self.special_moments[-10:]

    def log(self, event_type: str, details: dict) -> None:
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

    def get_effective_skills(self) -> tuple[dict[str, int], int, int]:
        """Calculates skills with equipment bonuses and overburdened penalties applied."""
        effective: dict[str, int] = dict(self.base_skills)
        
        # 1. Add equipment bonuses
        for item in self.equipment.values():
            if item:
                skill: str | None = item.get("skill")
                if skill and skill in effective:
                    effective[skill] += item.get("skill_val", 0)

        # 2. Calculate weight & penalty
        total_weight: int = sum(item["weight"] for item in self.inventory)
        max_weight: int = (effective["fighting"] + effective["defending"] + (effective["salvaging"] * 2)) * 2
        
        overburdened: int = total_weight - max_weight
        if overburdened > 20:
            penalty_units: int = (overburdened - 20) // 10 + 1
            penalty_pct: float = min(0.9, penalty_units * 0.10)
            for skill in effective:
                effective[skill] = int(effective[skill] * (1.0 - penalty_pct))
                
        return effective, total_weight, max_weight

    def generate_random_item(self, leg_num: int = 1, quality_bias: str | None = None) -> Item:
        cat_key: str = random.choice(list(ITEM_CATEGORIES.keys()))
        cat_data: ItemCategoryEntry = ITEM_CATEGORIES[cat_key]
        
        if not quality_bias:
            r: float = random.random()
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
            
        q_data: QualityTier = QUALITY_TIERS[tier]
        name: str = f"{tier} {random.choice(cat_data['names'])}"
        
        # Quality bonuses: Defending +20, Fighting/Stealth +10
        bonus = 0
        if cat_data["slot"] == "defending_armor":
            bonus = 20
        elif cat_key in ["fighting", "stealth"]:
            bonus = 10
            
        skill_val: int = random.randint(q_data["skill_min"], q_data["skill_max"]) + bonus
        
        val_ratio: float = (skill_val - q_data["skill_min"]) / max(1, (q_data["skill_max"] - q_data["skill_min"]))
        cash_val: int = int(q_data["cash_min"] + val_ratio * (q_data["cash_max"] - q_data["cash_min"]))
        
        item: Item = {
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

    def auto_equip_best(self) -> None:
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

    def _opposed_roll(self, attacker_stat: int, defender_stat: int, die: int = 20) -> tuple[bool, int]:
        """Contested check: both sides add a random 1-die swing to their stat
        and the higher total wins. A bigger stat gap makes winning likely but
        never certain - a lucky (or unlucky) roll can still flip the result.
        Returns (attacker_wins: bool, margin: int) where margin is how much
        the winning roll beat the losing one by (used to gauge crits)."""
        atk_roll = attacker_stat + random.randint(1, die)
        def_roll = defender_stat + random.randint(1, die)
        return atk_roll > def_roll, abs(atk_roll - def_roll)

    def _kill_phrase(self) -> str:
        return random.choice(KILL_PHRASES)

    def _combat_line(self, category: str, used_lines: set[tuple[str, int, int]] | None = None, **kwargs: object) -> str:
        """Builds a silly combat narration line from a 50+ line generated pool.

        `used_lines`, if given, is a set shared across a single fight; the
        (category, start_idx, end_idx) template combo is tracked so the same
        flavour text is never repeated across rounds of the same encounter."""
        start, end = COMBAT_LINE_POOLS[category]
        if used_lines is not None:
            combos: list[tuple[int, int]] = [(s, e) for s in range(len(start)) for e in range(len(end))
                      if (category, s, e) not in used_lines]
            if not combos:
                combos = [(s, e) for s in range(len(start)) for e in range(len(end))]
            s_idx, e_idx = random.choice(combos)
            used_lines.add((category, s_idx, e_idx))
        else:
            s_idx = random.randrange(len(start))
            e_idx = random.randrange(len(end))
        start_text: str = start[s_idx].format(**kwargs)
        end_text: str = end[e_idx].format(**kwargs)
        line: str = f"{start_text} {kwargs.get('value', '')} {end_text}".strip()
        return " ".join(line.split())

    def _combat_action_line(self, action: str, used_lines: set[tuple[str, int, int]] | None = None, **kwargs: object) -> str:
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
        number: int,
        outcome: str,
        text: str,
        damage_dealt: int = 0,
        damage_taken: int = 0,
        hero_hp: int | None = None,
        monster_hp: int | None = None,
    ) -> dict:
        return {
            "round": number,
            "outcome": outcome,
            "text": text,
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,
            "hero_hp": self.hp if hero_hp is None else hero_hp,
            "monster_hp": monster_hp,
        }

    def _magic_spell_name(self) -> str:
        return f"{random.choice(MAGIC_SPELL_NAME_PARTS['prefixes'])} {random.choice(MAGIC_SPELL_NAME_PARTS['spells'])}"

    def _magic_shield_name(self) -> str:
        return f"{random.choice(MAGIC_SHIELD_NAME_PARTS['prefixes'])} {random.choice(MAGIC_SHIELD_NAME_PARTS['shields'])}"

    def _fight_core_stats(self) -> tuple[dict[str, int], int, int]:
        skills, _, _ = self.get_effective_skills()
        effective_def: int = skills["defending"]

        has_arcane_amulet: bool = any(eq and eq.get("name") == "Amulet of Arcane Shielding" for eq in self.equipment.values())
        ward_mult: float = 1.0 if has_arcane_amulet else 0.5
        if skills["magic"] > skills["fighting"]:
            effective_def += int(skills["magic"] * ward_mult)

        for eq in self.equipment.values():
            if eq and eq.get("name") == "Crown of the Archmage":
                effective_def: int = max(effective_def, skills["magic"])
                break

        # Stealth counts as a viable (if weaker) combat stat too, so a
        # stealth-built hero isn't defenseless whenever a sneak/steal fails
        # and they're dumped into a straight fight.
        stealth_component: int = int(skills["stealth"] * 0.5) if self.stealth_atk_enabled else 0
        player_atk: int = max(skills["fighting"], skills["magic"], stealth_component)
        return skills, player_atk, effective_def

    def _get_monster_stats(self, monster_name: str) -> Monster:
        """Returns monster combat stats, optionally scaled up for
        relic-flagged monsters (dungeon bosses/super monsters) when
        relic_scaling_enabled is set - a way to tune late-game/boss
        difficulty independently of regular per-leg monster stats."""
        m_stats: Monster = MONSTERS[monster_name]
        if self.relic_scaling_enabled and m_stats.get("relic"):
            scaled: Monster = cast(Monster, dict(m_stats))
            for stat in ("fighting", "defending", "magic"):
                if stat in scaled:
                    scaled[stat] = int(scaled[stat] * RELIC_MONSTER_SCALE)
            return scaled
        return m_stats

    def pick_throwable_item(self) -> Item | None:
        """Returns the cheapest non-relic inventory item usable as a
        distraction to throw at a monster, or None if nothing's available."""
        candidates = [it for it in self.inventory if it.get("category") != "relic"]
        if not candidates:
            return None
        return min(candidates, key=lambda it: it.get("value", 0))

    def estimate_fight_risk(self, monster_name: str) -> dict:
        m_stats: Monster = self._get_monster_stats(monster_name)
        skills, player_atk, effective_def = self._fight_core_stats()

        has_cloak: bool = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        has_staff: bool = any(eq and eq.get("name") == "Staff of Magic" for eq in self.equipment.values())
        has_crown: bool = any(eq and eq.get("name") == "Crown of the Archmage" for eq in self.equipment.values())
        has_sword: bool = any(eq and eq.get("name") == "Sword of Power" for eq in self.equipment.values())
        has_plate: bool = any(eq and eq.get("name") == "Plate of Invincibility" for eq in self.equipment.values())
        has_shield: bool = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())
        has_mirror: bool = any(eq and eq.get("name") == "Mirror of Fate" for eq in self.equipment.values())

        guaranteed: bool = has_cloak or (has_staff and has_crown) or (has_sword and has_plate)
        player_round_damage = max(5, player_atk - m_stats["defending"])
        monster_round_damage = max(5, m_stats["fighting"] - effective_def)
        if has_shield:
            monster_round_damage = max(1, monster_round_damage // 2)

        monster_hp = max(20, (m_stats["fighting"] + m_stats["defending"]) * 2)
        rounds_to_kill: int = max(1, math.ceil(monster_hp / player_round_damage))
        rounds_to_die: int = max(1, math.ceil(max(1, self.hp) / max(1, monster_round_damage)))
        round_cap = 8

        if guaranteed:
            win_prob = 1.0
        else:
            # Exact chance to win a single contested round.
            wins = 0
            for p_die in range(1, 21):
                for m_die in range(1, 21):
                    p_power: int = player_atk + effective_def + p_die
                    m_power = m_stats["fighting"] + m_stats["defending"] + m_die
                    if p_power > m_power:
                        wins += 1
            p_round: float = wins / 400.0
            q_round: float = 1.0 - p_round

            # DP race model: probability player reaches required wins before
            # accumulating enough losses to drop to 0 HP, within round cap.
            states: dict[tuple[int, int], float] = {(0, 0): 1.0}  # (wins, losses) -> probability
            win_prob = 0.0
            for _ in range(round_cap):
                next_states = {}
                for (w, l), prob in states.items():
                    if prob <= 0:
                        continue

                    # Round win
                    w2: int = w + 1
                    pw: float = prob * p_round
                    if w2 >= rounds_to_kill:
                        win_prob += pw
                    else:
                        next_states[(w2, l)] = next_states.get((w2, l), 0.0) + pw

                    # Round loss
                    l2: int = l + 1
                    pl: float = prob * q_round
                    if l2 < rounds_to_die:
                        next_states[(w, l2)] = next_states.get((w, l2), 0.0) + pl
                states = next_states

            # Relic safety nets that can flip losses.
            if has_sword or has_plate:
                win_prob: float = win_prob + (1.0 - win_prob) * 0.50
            if has_mirror:
                win_prob: float = win_prob + (1.0 - win_prob) * 0.35

        band: str = self._risk_band_for_probability(win_prob)

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

    def _opposed_win_probability(self, attacker_stat: int, defender_stat: int, die: int = 20) -> float:
        wins = 0
        total: int = die * die
        for atk_die in range(1, die + 1):
            for def_die in range(1, die + 1):
                if attacker_stat + atk_die > defender_stat + def_die:
                    wins += 1
        return wins / float(total)

    def _risk_band_for_probability(self, prob: float) -> str:
        for threshold, label in RISK_BANDS:
            if prob >= threshold:
                return label
        return RISK_BANDS[-1][1]

    def estimate_combat_action_risks(self, monster_name: str) -> dict:
        m_stats: Monster = self._get_monster_stats(monster_name)
        fight = self.estimate_fight_risk(monster_name)
        skills, _, _ = self._fight_core_stats()

        has_cloak: bool = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        has_boots: bool = any(eq and eq.get("name") == "Boots of Stealth" for eq in self.equipment.values())
        has_dagger: bool = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())

        if has_cloak:
            sneak_prob = 1.0
        else:
            sneak_prob: float = self._opposed_win_probability(skills["stealth"], m_stats["defending"])
            if has_boots:
                sneak_prob: float = sneak_prob + (1.0 - sneak_prob) * 0.50

        steal_prob: float = self._opposed_win_probability(
            skills["stealth"] + skills["salvaging"],
            m_stats["defending"] * 2
        )

        if has_cloak or (has_dagger and has_cloak):
            stealth_kill_prob = 1.0
        else:
            stealth_kill_prob: float = self._opposed_win_probability(
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

    def resolve_fight(self, monster_name: str, choice: str = "fight", encounter_type: str = "fight") -> str | None:
        """Resolves combat (fight, sneak, steal, stealth_kill) via contested
        dice rolls instead of flat stat comparisons, so every encounter
        carries genuine risk - even a heavily favored hero can get unlucky,
        and a "fight" can end in a costly trade of blows rather than a
        clean win or loss."""
        m_stats: Monster = self._get_monster_stats(monster_name)
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
                    round_text: str = self._combat_action_line(
                        "fight_win",
                        used_lines,
                        value="a flawless strike",
                        monster_name=monster_name,
                    )
                    round_text: str = f"{round_text} {self._kill_phrase()}"
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

        has_boots: bool = any(eq and eq.get("name") == "Boots of Stealth" for eq in self.equipment.values())

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
                loot: str = self.grant_monster_loot(monster_name)
                if encounter_type == "super_monster":
                    self.super_monsters_defeated: int = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared: int = min(10, self.dungeons_cleared + 1)
                    self.log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                round_text: str = self._combat_action_line("steal", value="a pouch of loot")
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
            has_dagger: bool = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())
            has_cloak: bool = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
            has_stone: bool = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.equipment.values())
            player_round_damage = max(5, player_atk - m_stats["defending"])
            
            # Shadow Assassin 2-Relic Synergy (Dagger + Cloak) & Master Thief 3-Relic Synergy (+Stone)
            is_shadow_assassin: bool = (has_dagger and has_cloak)
            is_master_thief: bool = (is_shadow_assassin and has_stone)

            # Surprise formula: (stealth * 2) vs (monster defending * 1.5), contested
            surprise_stealth: int = skills["stealth"] * 2
            surprise_def = int(m_stats["defending"] * 1.5)
            success, margin = self._opposed_roll(surprise_stealth, surprise_def)
            
            if is_shadow_assassin or success:
                self.karma += KARMA_STEALTH_KILL_PENALTY
                self.log("STEALTH_KILL_SUCCESS", {"monster": monster_name, "stealth_score": surprise_stealth, "m_def_score": surprise_def, "margin": margin, "karma": self.karma})
                cash_mult: float = 2.0 if is_master_thief else 1.0
                loot: str = self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
                if encounter_type == "super_monster":
                    self.super_monsters_defeated: int = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared: int = min(10, self.dungeons_cleared + 1)
                    self.log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                round_text: str = self._combat_action_line(
                    "stealth_kill",
                    used_lines,
                    value=f"{player_round_damage} damage",
                )
                round_text: str = f"{round_text} {self._kill_phrase()}"
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
            item = self.pick_throwable_item()
            if item:
                self.inventory.remove(item)
                self.log("THROW_ITEM_ESCAPE", {"monster": monster_name, "item": item["name"]})
                round_text: str = f"You hurl your {item['name']} at {monster_name} and slip away in the confusion - the item and any loot are lost."
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
            has_staff: bool = any(eq and eq.get("name") == "Staff of Magic" for eq in self.equipment.values())
            has_crown: bool = any(eq and eq.get("name") == "Crown of the Archmage" for eq in self.equipment.values())
            has_ankh: bool = any(eq and eq.get("name") == "Pharaoh's Ankh of Rebirth" for eq in self.equipment.values())
            
            is_arcane_tempest: bool = (has_staff and has_crown)
            is_grand_archmage: bool = (is_arcane_tempest and has_ankh)

            has_sword: bool = any(eq and eq.get("name") == "Sword of Power" for eq in self.equipment.values())
            has_plate: bool = any(eq and eq.get("name") == "Plate of Invincibility" for eq in self.equipment.values())

            crit = False
            rounds_fought = 0
            player_hp_before = self.hp
            monster_max_hp = max(20, (m_stats["fighting"] + m_stats["defending"]) * 2)
            monster_hp = monster_max_hp
            round_texts = []
            round_details = []
            magic_attack_mode: bool = skills["magic"] > skills["fighting"]
            spell_name: str = self._magic_spell_name()
            shield_name: str = self._magic_shield_name()
            player_round_damage = max(5, player_atk - m_stats["defending"])
            base_monster_damage = max(5, m_stats["fighting"] - effective_def)
            has_shield: bool = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())

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
                    rounds_fought: int = r
                    p_power: int = player_atk + effective_def + random.randint(1, 20)
                    m_power = m_stats["fighting"] + m_stats["defending"] + random.randint(1, 20)
                    margin: int = abs(p_power - m_power)
                    player_wins_round = p_power > m_power
                    crit = crit or (player_wins_round and margin >= 20)

                    if player_wins_round:
                        monster_hp = max(0, monster_hp - player_round_damage)
                        line: str = self._combat_action_line(
                            "magic_attack" if magic_attack_mode else "fight_win",
                            used_lines,
                            value=player_round_damage,
                            monster_name=monster_name,
                            spell_name=spell_name,
                            weapon_name=spell_name,
                        )
                        if monster_hp <= 0:
                            line: str = f"{line} {self._kill_phrase()}"
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
                    self.super_monsters_defeated: int = min(5, self.super_monsters_defeated + 1)
                elif encounter_type == "dungeon_boss":
                    self.dungeons_cleared: int = min(10, self.dungeons_cleared + 1)
                    self.log_special_moment("dungeon_boss_beaten", dungeon_name=self.dungeon_name, boss_name=monster_name)
                if m_stats.get("relic"):
                    if is_grand_archmage:
                        self.hp = 100
                        self.log("GRAND_ARCHMAGE_FULL_HEAL", {"hp": self.hp})
                    elif has_ankh:
                        self.hp = min(100, self.hp + 50)
                        self.log("ANKH_REBIRTH_HEAL", {"hp": self.hp})

                cash_mult: float = 1.5 if crit else 1.0
                self.log("FIGHT_WIN", {"monster": monster_name, "player_atk": player_atk, "m_def": m_stats["defending"], "margin": margin, "critical": crit, "rounds": rounds_fought})
                return self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
            else:
                # If rounds ended without lethal player damage, apply a final attrition hit.
                if not self.game_over:
                    timeout_damage = max(5, m_stats["fighting"] - effective_def)
                    has_shield: bool = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())
                    if has_shield:
                        timeout_damage = max(1, timeout_damage // 2)
                    self.take_damage(timeout_damage, DEATH_REASONS["slain_by"].format(monster_name=monster_name))
                    timeout_text: str = self._combat_action_line(
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

    def take_damage(self, amount: int, reason: str | None = None) -> None:
        reason = reason or DEATH_REASONS["unknown"]
        self.hp -= amount
        if self.hp <= 0:
            fairy_slot: str | None = next(
                (slot for slot, eq in self.equipment.items() if eq and eq.get("name") == "Captured Fairy"),
                None,
            )
            if fairy_slot:
                rewind_events: int = min(5, self.leg_event_count)
                self.leg_event_count: int = max(0, self.leg_event_count - 5)
                cash_taken = min(1000, self.cash)
                self.cash -= cash_taken
                self.hp: int = self.max_hp
                self.equipment[fairy_slot] = None
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

    def grant_monster_loot(self, monster_name: str, cash_multiplier: float = 1.0) -> str:
        m_stats: Monster = MONSTERS[monster_name]
        earned_cash = int(random.randint(m_stats["cash_min"], m_stats["cash_max"]) * cash_multiplier)
        self.cash += earned_cash
        
        num_eq: int = self._roll_loot_item_count(monster_name, m_stats)
        items_found = [self.generate_random_item(leg_num=self.current_leg_idx+1) for _ in range(num_eq)]
        
        # Named Relics only drop on legs 4-5. On legs 1-3, dungeon
        # bosses/super monsters get a bonus item at an upgraded tier instead.
        leg_num: int = self.current_leg_idx + 1
        is_relic_monster = bool(m_stats.get("relic"))
        relic_dropped: str | None = None
        if leg_num >= 4:
            if is_relic_monster or random.random() < 0.05:
                avail_relics: list[str] = [r for r in RELICS.keys() if r not in self.relics_found]
                if avail_relics:
                    relic_name: str = random.choice(avail_relics)
                    r_info: RelicDef = RELICS[relic_name]
                    relic_item: Item = {
                        "name": relic_name,
                        "category": "relic",
                        "slot": r_info["type"],
                        "tier": "Epic",
                        "code": "e",
                        "skill": r_info["skill"],
                        "skill_val": r_info["bonus"],
                        "weight": 1,
                        "value": 25000,
                        "uses": 1,
                        "max_uses": 1
                    }
                    items_found.append(relic_item)
                    self.relics_found.append(relic_name)
                    relic_dropped = relic_name
                    self.log_special_moment("relic_found", relic_name=relic_name, monster_name=monster_name)
        elif is_relic_monster:
            bonus_tier: str = BOSS_BONUS_TIER_BY_LEG.get(leg_num, "Rare")
            items_found.append(self.generate_random_item(leg_num=leg_num, quality_bias=bonus_tier))

        self.inventory.extend(items_found)
        
        self.log("LOOT_GAINED", {"cash": earned_cash, "items_count": len(items_found), "relic": relic_dropped})
        return "LOOT_FOUND"

    def _roll_loot_item_count(self, monster_name: str, m_stats: Monster) -> int:
        """Roll item drops with reduced global drop rates and very sparse low-level drops."""
        base_count: int = random.randint(m_stats["eq_min"], m_stats["eq_max"])
        leg_num = m_stats.get("leg", self.current_leg_idx + 1)
        is_super_or_boss = bool(m_stats.get("relic"))
        is_early_regular = (leg_num == 1 and not is_super_or_boss)

        # Leg 1 regular monsters should drop 0 items most of the time.
        if is_early_regular:
            if random.random() < 0.70:
                return 0
            return 1 if random.random() < 0.80 else 2

        # Global reduction across the board.
        keep_scale: float = 0.55 if not is_super_or_boss else 0.70
        reduced = int(round(base_count * keep_scale))

        # Non-boss enemies can still drop nothing sometimes.
        if not is_super_or_boss and random.random() < 0.25:
            return 0

        # Keep at least one item for boss/super encounters when they drop loot.
        if is_super_or_boss:
            reduced: int = max(1, reduced)
        else:
            reduced: int = max(0, reduced)

        # Additional global reduction pass: remove at most one item.
        return max(0, reduced - random.randint(0, 1))

    # ------------------------------------------------------------------
    # Shared decision helpers - single source of truth for probabilities
    # and selection rules used by BOTH the fast auto-simulator
    # (step_next_event, below) and the interactive GameController.
    # ------------------------------------------------------------------
    def get_random_monster(self, leg_idx: int | None = None) -> str:
        """Picks a random regular monster appropriate for a leg (defaults to
        the hero's current leg). Excludes dungeon and super monster names so
        those stay unique to their own dedicated encounters."""
        leg_idx = self.current_leg_idx if leg_idx is None else leg_idx
        leg_monsters: list[str] = [
            m for m, data in MONSTERS.items()
            if data.get("leg") == leg_idx + 1
            and m not in DUNGEON_MONSTER_NAMES
            and m not in SUPER_MONSTER_NAMES
        ]
        return random.choice(leg_monsters) if leg_monsters else "Goblin"

    def roll_journey_event_type(self) -> str:
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
        weighted_events: list[tuple[str, int]] = [
            ("FIGHT", 78),
            ("SUPER_MONSTER", 8),
            ("MAGIC_SHRINE", 6),
            ("WANDERING_TRADER", 6),
            ("WANDER_GROUP", 4),
            ("FAIRY_FOUND", 2),
        ]

        def within_three_events(last_turn: int | None) -> bool:
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

        total_weight: int = sum(weight for _, weight in allowed)
        roll: float = random.uniform(0, total_weight)
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

    def try_spot_dungeon(self) -> None | Dungeon:
        """Rolls a flat chance to stumble on a dungeon entrance (max 2 per
        leg). If found, records the dungeon's name/boss/floors (but does NOT
        enter it - the caller decides whether to enter_dungeon() or ignore
        it) and returns the dungeon info dict, else None."""
        if self.dungeons_found_in_leg >= 2:
            return None
        if random.random() > DUNGEON_FIND_CHANCE:
            return None
        self.dungeons_found_in_leg += 1
        leg_info: Leg = LEGS[self.current_leg_idx]
        dung_info: Dungeon = leg_info["dungeons"][self.dungeons_found_in_leg - 1]
        self.dungeon_name: str = dung_info["name"]
        self.dungeon_boss: str = dung_info["boss"]
        self.dungeon_floors: list[str] = dung_info.get("floors", [])
        self.dungeon_event_count = 0
        self.log("DUNGEON_FOUND", {"name": dung_info["name"], "boss": dung_info["boss"]})
        return dung_info

    def try_leg_transition(self) -> None | str:
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

    def enter_dungeon(self, dungeon: Dungeon | None = None) -> None:
        """Begins exploring a dungeon found via try_spot_dungeon(). `dungeon`
        is optional if try_spot_dungeon() already populated dungeon_name/boss/floors."""
        if dungeon:
            self.dungeon_name = dungeon["name"]
            self.dungeon_boss = dungeon["boss"]
            self.dungeon_floors = dungeon.get("floors", [])
            self.dungeon_event_count = 0
        self.in_dungeon = True

    def leave_dungeon(self, reason: str | None = None) -> None:
        reason = reason or DUNGEON_EXIT_REASONS["default"]
        self.in_dungeon = False
        self.log("DUNGEON_LEFT", {"reason": reason})

    def get_dungeon_floor_monster(self) -> str:
        """Previews the monster for the *next* dungeon floor/boss without
        advancing any state (dungeon_event_count is only bumped by
        advance_dungeon_floor() after a floor is won)."""
        idx: int = self.dungeon_event_count
        if idx < 5:
            return self.dungeon_floors[idx] if idx < len(self.dungeon_floors) else "Goblin"
        return self.dungeon_boss

    def advance_dungeon_floor(self) -> None:
        """Call after winning a dungeon floor fight to move to the next floor."""
        self.dungeon_event_count += 1

    def resolve_magic_shrine(self) -> dict:
        """Grants loot with zero risk. Journey-time healing has been removed
        entirely (see the town recovery mechanic), so this no longer restores
        HP - it is purely a free-loot event. Returns a summary dict."""
        self.log("MAGIC_SHRINE_LOOT", {})
        before_cash = self.cash
        before_len: int = len(self.inventory)
        self.grant_monster_loot("Goblin")
        return {
            "cash_gained": self.cash - before_cash,
            "new_items": self.inventory[before_len:],
        }

    def capture_fairy(self) -> Item:
        """Adds a captured fairy item to inventory."""
        fairy_item: Item = {
            "name": "Captured Fairy",
            "category": "fairy",
            "slot": "accessory",
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

    def apply_wander_group_advance(self, step_count: int = 5) -> None:
        """Moves the hero forward on the current leg by additional events."""
        self.leg_event_count += step_count
        self.log("WANDER_GROUP_ADVANCE", {"events_advanced": step_count, "leg_event_count": self.leg_event_count})

    def trader_buy_multiplier(self) -> float:
        # Speech skill curves buy/sell rates: 0 speech = 10% worse than
        # value, 100 speech = exact value, clamped beyond that range.
        skills, _, _ = self.get_effective_skills()
        speech: int = max(0, min(200, skills.get("speech", 0)))
        return 1.0 + (100 - speech) / 1000

    def trader_sell_multiplier(self) -> float:
        skills, _, _ = self.get_effective_skills()
        speech: int = max(0, min(200, skills.get("speech", 0)))
        return 1.0 - (100 - speech) / 1000

    def generate_trader_offer(self, count: int = 5) -> list[Item]:
        """Generates the wandering trader's for-sale inventory."""
        return [self.generate_random_item(self.current_leg_idx + 1) for _ in range(count)]

    def trader_buy(self, item: Item) -> bool:
        """Player buys `item` from the trader. Returns True if successful."""
        cost = int(item["value"] * self.trader_buy_multiplier())
        if self.cash < cost:
            return False
        self.cash -= cost
        self.inventory.append(item)
        self.log("TRADER_BUY", {"item": item["name"], "cost": cost})
        return True

    def trader_sell(self, item: Item) -> bool:
        """Player sells `item` (must be in inventory) to the trader."""
        if item not in self.inventory:
            return False
        price = int(item["value"] * self.trader_sell_multiplier())
        self.cash += price
        self.inventory.remove(item)
        self.log("TRADER_SELL", {"item": item["name"], "price": price})
        return True

    def apply_level_up(self, skill: str) -> bool:
        if skill in self.base_skills:
            self.base_skills[skill] += 5
            return True
        return False

    def advance_to_next_leg(self) -> None:
        self.current_leg_idx += 1
        self.leg_event_count = 0
        self.dungeons_found_in_leg = 0
        self.super_monster_seen_in_leg = False
        self.last_journey_event_turn = {}

    def sell_all_for_capital(self) -> None:
        """Auto-sells all inventory & equipment at 100% value, as happens
        when the hero arrives at the Capital."""
        for item in self.inventory:
            self.cash += item["value"]
        self.inventory.clear()
        for slot, item in list(self.equipment.items()):
            if item:
                self.cash += item["value"]
                self.equipment[slot] = None

    def get_pension(self) -> int:
        """Pension = flat cash-based lookup, scaled by how many years the
        pension needs to last. A random end-of-life age (60-90) is rolled
        once per hero and reused for every pension calculation that run, so
        a younger hero (more years left to fund) gets a smaller multiplier
        for the same cash than an older one - i.e. the younger hero needs
        more cash to retire equally comfortably."""
        base: int | None = None
        for p in PENSIONS:
            if p["min"] <= self.cash <= p["max"]:
                base = p["pension"]
                break
        if base is None:
            base = 5000 if self.cash >= 50000 else 100
        if self.end_age is None:
            self.end_age = random.randint(PENSION_END_AGE_MIN, PENSION_END_AGE_MAX)
        years_remaining: int = max(1, self.end_age - self.age)
        multiplier: float = max(0.2, min(PENSION_BASELINE_YEARS / years_remaining, 3.0))
        return round(base * multiplier)

    def get_house_options(self) -> tuple[list[dict], int]:
        """Returns (options, pension) for the Capital screen. Score preview
        follows the design spec: multiplier x pension (not remaining cash)."""
        pension: int = self.get_pension()
        options = []
        for h in HOUSES:
            affordable = self.cash >= h["cost"]
            score: int | None = h["multiplier"] * pension if affordable else None
            options.append({
                "name": h["name"], "cost": h["cost"], "multiplier": h["multiplier"],
                "affordable": affordable, "score": score
            })
        return options, pension

    def step_next_event(self) -> str | None:
        """Advances the game state by one event step (10 sec equivalent in fast mode)."""
        if self.game_over:
            return "GAME_OVER"

        # Dungeon logic: 5 themed floor fights, then the boss
        if self.in_dungeon:
            self.dungeon_event_count += 1
            if self.dungeon_event_count <= 5:
                floor_idx: int = self.dungeon_event_count - 1
                monster = self.dungeon_floors[floor_idx] if floor_idx < len(self.dungeon_floors) else "Goblin"
                choice: str = self.get_tactical_choice(monster)
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

        dungeon: None | Dungeon = self.try_spot_dungeon()
        if dungeon:
            return "DUNGEON_FOUND"

        transition: None | str = self.try_leg_transition()
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
            transition: None | str = self.try_leg_transition()
            if transition:
                return transition
            return "WANDER_GROUP"
        elif event_type == "FAIRY_FOUND":
            self.capture_fairy()
            return "FAIRY_FOUND"
        else:
            if self.skip_journey_fights:
                m_name: str = self.get_random_monster()
                self.log("JOURNEY_FIGHT_BYPASSED", {"monster": m_name})
                return "JOURNEY"
            m_name: str = self.get_random_monster()
            choice: str = self.get_tactical_choice(m_name)
            return self.resolve_fight(m_name, choice=choice)

    def get_tactical_choice(self, monster_name: str) -> str:
        skills, _, _ = self.get_effective_skills()
        m_stats: Monster = self._get_monster_stats(monster_name)
        m_def: object | int = m_stats["defending"]
        
        has_dagger: bool = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())
        has_cloak: bool = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
        is_shadow_assassin: bool = (has_dagger and has_cloak)

        # Phase 3 Surprise Formula: (stealth * 2) vs (m_def * 1.5)
        surprise_stealth: int = skills["stealth"] * 2
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
            if self.throw_item_enabled and skills["stealth"] < m_def and self.pick_throwable_item():
                return "throw_item"
            return "sneak"
        else:
            return "fight"

    def calculate_score(self, chosen_house_name: str | None = None, failed_adventurer: bool = False) -> dict:
        self.sell_all_for_capital()

        bought_house: House | None = None
        house_mult = 0
        if chosen_house_name:
            for h in HOUSES:
                if h["name"] == chosen_house_name and self.cash >= h["cost"]:
                    bought_house = h
                    self.cash -= h["cost"]
                    house_mult: int = h["multiplier"]
                    break

        pension_val: int = self.get_pension()
        final_score: int = (house_mult * pension_val) if bought_house else pension_val
        if failed_adventurer:
            final_score: int = round(final_score * 0.25)
        return {
            "hero_name": self.hero_name,
            "house": bought_house["name"] if bought_house else "Tavern",
            "pension": pension_val,
            "remaining_cash": self.cash,
            "score": final_score,
            "failed_adventurer": failed_adventurer
        }


