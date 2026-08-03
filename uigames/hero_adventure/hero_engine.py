"""
Core Game Engine for Hero Adventure
Implements state machine, item inventory management, combat/stealth/steal checks,
weight penalties, dungeon management, and fast zero-delay simulation API.
"""

import random
from game_data import (
    CLASSES, LEGS, MONSTERS, ITEM_CATEGORIES, QUALITY_TIERS,
    RELICS, HOUSES, PENSIONS
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


class HeroAdventureEngine:
    def __init__(self, hero_name="Hero", hero_class="Hitter", fast_mode=True):
        self.fast_mode = fast_mode
        self.hero_name = hero_name
        self.hero_class = hero_class
        self.skip_journey_fights = False
        
        # Base Skills (all start at 5)
        self.base_skills = {
            "fighting": 5, "defending": 5, "magic": 5, "stealth": 5,
            "salvaging": 5, "spotting": 5, "camping": 5, "medical": 5
        }
        
        # Apply initial class boosts (+20 to 3 skills)
        if hero_class in CLASSES:
            for skill, boost in CLASSES[hero_class].items():
                self.base_skills[skill] += boost

        self.hp = 100
        self.max_hp = 100
        self.cash = 0
        
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
        self.last_journey_event_turn = {}
        self.in_dungeon = False
        self.dungeon_name = ""
        self.dungeon_event_count = 0  # 0 to 6 (1-5 floor fights, 6 boss)
        self.dungeon_boss = ""
        self.dungeon_floors = []
        
        # Relic tracking & state
        self.relics_found = []
        self.pendant_used = False
        self.game_over = False
        self.game_won = False
        self.death_reason = ""
        
        # Telemetry log
        self.event_logs = []

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
            "uses": q_data["med_uses"] if cat_key == "medical" else 1,
            "max_uses": q_data["med_uses"] if cat_key == "medical" else 1
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

    def resolve_fight(self, monster_name, choice="fight"):
        """Resolves combat (fight, sneak, steal, stealth_kill) via contested
        dice rolls instead of flat stat comparisons, so every encounter
        carries genuine risk - even a heavily favored hero can get unlucky,
        and a "fight" can end in a costly trade of blows rather than a
        clean win or loss."""
        m_stats = MONSTERS[monster_name]
        skills, _, _ = self.get_effective_skills()
        
        # Check Crown of Archmage (magic replaces defending in combat damage reduction)
        effective_def = skills["defending"]
        
        # Phase 8 Magic Boost: Amulet of Arcane Shielding doubles ward efficiency (100% Magic to DEF vs 50%)
        has_arcane_amulet = any(eq and eq.get("name") == "Amulet of Arcane Shielding" for eq in self.equipment.values())
        ward_mult = 1.0 if has_arcane_amulet else 0.5

        if skills["magic"] > skills["fighting"]:
            effective_def += int(skills["magic"] * ward_mult)

        for eq in self.equipment.values():
            if eq and eq.get("name") == "Crown of the Archmage":
                effective_def = max(effective_def, skills["magic"])
                break

        player_atk = max(skills["fighting"], skills["magic"])
        
        # Check Cloak of Invisibility
        for eq in self.equipment.values():
            if eq and eq.get("name") == "Cloak of Invisibility":
                if choice in ["sneak", "fight", "stealth_kill"]:
                    self.log("FIGHT_SUCCESS", {"monster": monster_name, "choice": choice, "relic": "Cloak of Invisibility"})
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
                self.log("STEAL_SUCCESS", {"monster": monster_name, "margin": margin})
                return self.grant_monster_loot(monster_name)
            else:
                choice = "fight"

        if choice == "stealth_kill":
            has_dagger = any(eq and eq.get("name") == "Shadowstep Dagger" for eq in self.equipment.values())
            has_cloak = any(eq and eq.get("name") == "Cloak of Invisibility" for eq in self.equipment.values())
            has_stone = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.equipment.values())
            
            # Shadow Assassin 2-Relic Synergy (Dagger + Cloak) & Master Thief 3-Relic Synergy (+Stone)
            is_shadow_assassin = (has_dagger and has_cloak)
            is_master_thief = (is_shadow_assassin and has_stone)

            # Surprise formula: (stealth * 2) vs (monster defending * 1.5), contested
            surprise_stealth = skills["stealth"] * 2
            surprise_def = int(m_stats["defending"] * 1.5)
            success, margin = self._opposed_roll(surprise_stealth, surprise_def)
            
            if is_shadow_assassin or success:
                self.log("STEALTH_KILL_SUCCESS", {"monster": monster_name, "stealth_score": surprise_stealth, "m_def_score": surprise_def, "margin": margin})
                cash_mult = 2.0 if is_master_thief else 1.0
                return self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
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
            if is_arcane_tempest or (has_sword and has_plate):
                # Guaranteed-win relic combos bypass the dice entirely and never wound the hero
                win, damage, margin = True, 0, 0
            else:
                # Single contested roll: each side's full combat power (offense + defense)
                # gets a d20 swing added on top. A bigger stat lead still matters a lot,
                # but a big enough roll can flip even a lopsided matchup.
                p_power = player_atk + effective_def + random.randint(1, 20)
                m_power = m_stats["fighting"] + m_stats["defending"] + random.randint(1, 20)
                win = p_power > m_power
                margin = abs(p_power - m_power)
                crit = margin >= 20  # a decisive roll - clearly one-sided exchange

                if win:
                    damage = 0
                else:
                    damage = max(5, m_stats["fighting"] - effective_def)

                # Sword of Power / Plate of Invincibility: 50% reroll of a loss when held alone
                if not win and (has_sword or has_plate):
                    if random.random() < 0.5:
                        win, damage = True, 0
                        self.log("RELIC_REROLL_PROC", {"monster": monster_name, "relic": "Sword of Power" if has_sword else "Plate of Invincibility"})

                # Mirror of Fate: flips a loss to an instant win once per game
                if not win:
                    for slot, eq in self.equipment.items():
                        if eq and eq.get("name") == "Mirror of Fate":
                            win, damage = True, 0
                            self.equipment[slot] = None  # consume relic
                            self.log("MIRROR_OF_FATE_PROC", {"monster": monster_name})
                            break

            if win:
                if m_stats.get("relic"):
                    if is_grand_archmage:
                        self.hp = 100
                        self.log("GRAND_ARCHMAGE_FULL_HEAL", {"hp": self.hp})
                    elif has_ankh:
                        self.hp = min(100, self.hp + 50)
                        self.log("ANKH_REBIRTH_HEAL", {"hp": self.hp})

                cash_mult = 1.5 if crit else 1.0
                self.log("FIGHT_WIN", {"monster": monster_name, "player_atk": player_atk, "m_def": m_stats["defending"], "margin": margin, "critical": crit})
                return self.grant_monster_loot(monster_name, cash_multiplier=cash_mult)
            else:
                has_shield = any(eq and eq.get("name") == "Behemoth Shield" for eq in self.equipment.values())
                if has_shield:
                    damage = max(1, damage // 2)
                self.log("FIGHT_LOSS", {"monster": monster_name, "hp_loss": damage, "critical": crit})
                self.take_damage(damage, f"slain by {monster_name}")
                return "LOSS_WINDOW"

    def take_damage(self, amount, reason="unknown causes"):
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
                    self.leave_dungeon("fairy rescue")
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
        
        # Check Relic drop
        relic_dropped = None
        if m_stats.get("relic") or random.random() < 0.05:
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
            return max(1, reduced)
        return max(0, reduced)

    # ------------------------------------------------------------------
    # Shared decision helpers - single source of truth for probabilities
    # and selection rules used by BOTH the fast auto-simulator
    # (step_next_event, below) and the interactive GameController.
    # ------------------------------------------------------------------
    def get_random_monster(self, leg_idx=None):
        """Picks a random regular monster appropriate for a leg (defaults to
        the hero's current leg)."""
        leg_idx = self.current_leg_idx if leg_idx is None else leg_idx
        leg_monsters = [
            m for m, data in MONSTERS.items()
            if data.get("leg") == leg_idx + 1 and m not in DUNGEON_MONSTER_NAMES
        ]
        return random.choice(leg_monsters) if leg_monsters else "Goblin"

    def roll_journey_event_type(self):
        """Rolls the next journey event with pacing constraints.
        Rules:
        - Mostly fights.
        - Rest events (tavern/camp) only in second half of a leg.
        - Rest events cannot occur within 3 events of another rest event.
        - Free-loot style events (magic shrine, wandering trader) cannot
          repeat within 3 events of themselves.
        - Super monster appears at most once per leg and also respects
          a 3-event self-cooldown.
        """
        # Weights are intentionally fight-heavy.
        if self.leg_event_count <= 10:
            weighted_events = [
                ("FIGHT", 78),
                ("SUPER_MONSTER", 8),
                ("MAGIC_SHRINE", 6),
                ("WANDERING_TRADER", 6),
                ("WANDER_GROUP", 4),
                ("FAIRY_FOUND", 2),
            ]
        else:
            weighted_events = [
                ("FIGHT", 70),
                ("SUPER_MONSTER", 8),
                ("MAGIC_SHRINE", 6),
                ("WANDERING_TRADER", 6),
                ("TAVERN", 4),
                ("CAMP", 4),
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
            elif event_type in ("TAVERN", "CAMP"):
                # Rest events are blocked in first-half legs by construction,
                # and share a mutual cooldown window.
                if within_three_events(self.last_journey_event_turn.get("REST")):
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
        elif chosen_event in ("TAVERN", "CAMP"):
            self.last_journey_event_turn["REST"] = self.leg_event_count
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

    def leave_dungeon(self, reason="left"):
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

    def apply_tavern_rest(self, cost=100):
        """Attempts to rest at a tavern. Returns the HP healed, or None if
        the hero cannot afford it."""
        if self.cash < cost:
            return None
        self.cash -= cost
        heal = 40 + random.randint(0, 20)
        self.hp = min(self.max_hp, self.hp + heal)
        self.log("TAVERN_REST", {"heal": heal, "hp": self.hp})
        return heal

    def apply_camp_rest(self):
        """Rests at a campsite. Heal = camping skill (doubled and the
        medical item consumed if one is equipped). Returns (heal, doubled)."""
        skills, _, _ = self.get_effective_skills()
        heal = skills["camping"]
        doubled = False
        med_item = self.equipment.get("camping_medical")
        if med_item and med_item.get("category") == "medical":
            heal *= 2
            doubled = True
            med_item["uses"] -= 1
            if med_item["uses"] <= 0:
                self.equipment["camping_medical"] = None
        self.hp = min(self.max_hp, self.hp + heal)
        self.log("CAMPING_REST", {"heal": heal, "hp": self.hp})
        return heal, doubled

    def resolve_magic_shrine(self):
        """Restores HP and grants loot with zero risk. Returns a summary dict."""
        self.hp = min(self.max_hp, self.hp + 20)
        self.log("MAGIC_SHRINE_RESTORE", {"hp": self.hp})
        before_cash = self.cash
        before_len = len(self.inventory)
        self.grant_monster_loot("Goblin")
        return {
            "cash_gained": self.cash - before_cash,
            "new_items": self.inventory[before_len:],
            "hp": self.hp,
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
        for p in PENSIONS:
            if p["min"] <= self.cash <= p["max"]:
                return p["pension"]
        return 5000 if self.cash >= 50000 else 100

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
                res = self.resolve_fight(monster, choice=choice)
                if res == "LOSS_WINDOW":
                    self.leave_dungeon("defeated on floor")
                return res
            else:
                # Dungeon boss fight
                res = self.resolve_fight(self.dungeon_boss, choice="fight")
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
        if event_type == "TAVERN":
            self.apply_tavern_rest()
            return "JOURNEY"
        elif event_type == "CAMP":
            self.apply_camp_rest()
            return "JOURNEY"
        elif event_type == "SUPER_MONSTER":
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

    def use_town_transport(self):
        """Hires transport back to last town to heal HP for a leg-scaled cash fee."""
        cost = 100 + (self.current_leg_idx * 50)
        if self.cash >= cost:
            self.cash -= cost
            self.hp = 100
            self.log("TOWN_TRANSPORT_USED", {"cost": cost, "leg": self.current_leg_idx + 1})
            return True
        return False

    def get_tactical_choice(self, monster_name):
        skills, _, _ = self.get_effective_skills()
        m_stats = MONSTERS[monster_name]
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
        elif skills["stealth"] > (m_def * 2) and self.hp < 40:
            return "sneak"
        else:
            return "fight"

    def calculate_score(self, chosen_house_name=None):
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
        return {
            "hero_name": self.hero_name,
            "house": bought_house["name"] if bought_house else "Tavern",
            "pension": pension_val,
            "remaining_cash": self.cash,
            "score": final_score
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

    def __init__(self):
        self.engine = None
        self.screen = "front_page"
        self.pending_name = ""
        self.pending_class = ""
        self.scores = []
        self.quit_requested = False
        self.ctx = {}
        self.previous_screen = "journey"
        self.dungeon_pending = None
        self.trader_offer = []
        self.levelup_chosen = []
        self.selected_item_letter = None

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
                "hp": e.hp, "max_hp": e.max_hp, "cash": e.cash,
                "leg": e.current_leg_idx + 1, "leg_name": leg_info["name"],
                "event": e.leg_event_count, "dungeons_found": e.dungeons_found_in_leg,
                "fighting": skills["fighting"], "defending": skills["defending"],
                "magic": skills["magic"], "stealth": skills["stealth"],
                "salvaging": skills["salvaging"], "spotting": skills["spotting"],
                "camping": skills["camping"], "medical": skills["medical"],
                "total_weight": total_weight, "max_weight": max_weight,
                "dungeon_name": e.dungeon_name, "dungeon_boss": e.dungeon_boss,
                "death_reason": e.death_reason or "unknown causes",
                "equipped_summary": equipped_summary,
            })

        ctx.update(self.ctx)
        ctx["pending_name"] = self.pending_name
        ctx["pending_class"] = self.pending_class or "(none)"
        ctx["levelup_count"] = len(self.levelup_chosen)

        if self.screen == "inventory":
            ctx["list_inventory"] = self._build_inventory_rows()
        elif self.screen == "item_detail":
            item, slot = self._find_letter_item(self.selected_item_letter)
            if item:
                stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
                ctx.update({
                    "item_name": item["name"], "item_tier": item.get("tier", ""),
                    "item_stat": stat, "item_value": item["value"], "item_weight": item["weight"],
                    "item_uses": item.get("uses"), "item_slot": item.get("slot", ""),
                    "can_equip": slot is None, "can_unequip": slot is not None,
                    "is_medical": item.get("category") == "medical",
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

        return ctx

    def _build_inventory_rows(self):
        rows = []
        for letter, item, slot in self._letter_items():
            tag = "Equipped" if slot else "Backpack"
            stat = f"+{item.get('skill_val', 0)} {item.get('skill', '')}" if item.get("skill") else "Relic"
            text = (f"{letter} - [{tag}] {item['name']} ({item.get('tier', '')}) "
                    f"{stat} | ${item['value']} | {item['weight']}wt")
            rows.append({"text": text, "action": f"select_item:{letter}", "enabled": True})
        if not rows:
            rows.append({"text": "Your inventory is empty.", "action": None, "enabled": False})
        return rows

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
        self.engine = None
        self.screen = "character_creation"

    def _action_select_class(self, class_name):
        if class_name in CLASSES:
            self.pending_class = class_name

    def _action_confirm_character(self):
        if not self.pending_name or not self.pending_class:
            return
        self.engine = HeroAdventureEngine(self.pending_name, self.pending_class)
        self.screen = "journey"

    def _action_quit(self):
        self.quit_requested = True

    # -- Inventory (openable from journey/combat, returns to prior screen) --
    def _action_open_inventory(self):
        self.previous_screen = self.screen
        self.screen = "inventory"

    def _action_close_inventory(self):
        self.screen = self.previous_screen or "journey"

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

    def _action_use_medical(self):
        letter = self.selected_item_letter
        item, slot = self._find_letter_item(letter)
        if item and item.get("category") == "medical":
            skills, _, _ = self.engine.get_effective_skills()
            heal = skills["camping"] + random.randint(0, max(1, skills["camping"]))
            item["uses"] -= 1
            self.engine.hp = min(self.engine.max_hp, self.engine.hp + heal)
            if item["uses"] <= 0:
                if slot is not None:
                    self.engine.equipment[slot] = None
                elif item in self.engine.inventory:
                    self.engine.inventory.remove(item)
            self.engine.log("MEDICAL_ITEM_USED", {"heal": heal, "hp": self.engine.hp})
        self.screen = "inventory"
        self.selected_item_letter = None

    # -- Journey ----------------------------------------------------------
    def _action_advance_event(self):
        e = self.engine
        e.leg_event_count += 1

        dungeon = e.try_spot_dungeon()
        if dungeon:
            self.dungeon_pending = dungeon
            self.ctx = {"dungeon_name": dungeon["name"], "dungeon_boss": dungeon["boss"]}
            self.screen = "dungeon_found"
            return

        transition = e.try_leg_transition()
        if transition == "LEVEL_UP":
            self.levelup_chosen = []
            self.ctx = {}
            self.screen = "level_up"
            return
        elif transition == "CAPITAL":
            e.sell_all_for_capital()
            self.ctx = {}
            self.screen = "capital"
            return

        event_type = e.roll_journey_event_type()
        if event_type == "TAVERN":
            self.ctx = {}
            self.screen = "tavern_event"
        elif event_type == "CAMP":
            self.ctx = {}
            self.screen = "camping_event"
        elif event_type == "SUPER_MONSTER":
            sm_name = LEGS[e.current_leg_idx]["super_monster"]
            m = MONSTERS[sm_name]
            self.ctx = {"monster_name": sm_name, "monster_fighting": m["fighting"],
                        "monster_defending": m["defending"], "monster_magic": m["magic"]}
            self.screen = "super_monster_preview"
        elif event_type == "MAGIC_SHRINE":
            result = e.resolve_magic_shrine()
            self.ctx = {"loot_cash": result["cash_gained"], "loot_items": result["new_items"],
                        "loot_lines": self._format_loot_lines(result["new_items"])}
            self.screen = "magic_shrine_event"
        elif event_type == "WANDERING_TRADER":
            self.trader_offer = e.generate_trader_offer()
            self.ctx = {}
            self.screen = "wandering_trader"
        elif event_type == "WANDER_GROUP":
            e.apply_wander_group_advance(5)
            transition = e.try_leg_transition()
            if transition == "LEVEL_UP":
                self.levelup_chosen = []
                self.ctx = {}
                self.screen = "level_up"
                return
            elif transition == "CAPITAL":
                e.sell_all_for_capital()
                self.ctx = {}
                self.screen = "capital"
                return
            self.ctx = {}
            self.screen = "journey"
        elif event_type == "FAIRY_FOUND":
            e.capture_fairy()
            self.ctx = {}
            self.screen = "journey"
        else:
            self._start_combat(e.get_random_monster(), "regular", allow_run=True)

    # -- Tavern / Camping ---------------------------------------------------
    def _action_rest_tavern(self):
        heal = self.engine.apply_tavern_rest()
        if heal is None:
            self.ctx["rest_text"] = "You don't have enough gold to rest here (needs $100)."
        else:
            self.ctx["rest_text"] = f"You rest and recover {heal} HP! (HP now {self.engine.hp}/{self.engine.max_hp})"
        self.ctx["resolved"] = True

    def _action_skip_tavern(self):
        self.ctx["rest_text"] = "You continue on your way."
        self.ctx["resolved"] = True

    def _action_rest_camp(self):
        heal, doubled = self.engine.apply_camp_rest()
        extra = " (medical supply consumed for double effect)" if doubled else ""
        self.ctx["rest_text"] = f"You make camp and recover {heal} HP{extra}! (HP now {self.engine.hp}/{self.engine.max_hp})"
        self.ctx["resolved"] = True

    def _action_skip_camp(self):
        self.ctx["rest_text"] = "You continue on your way."
        self.ctx["resolved"] = True

    def _action_continue_journey(self):
        self.ctx = {}
        self.screen = "journey"

    def _action_magic_shrine_continue(self):
        self.ctx = {}
        self.screen = "journey"

    # -- Super monster ------------------------------------------------------
    def _action_fight_super_monster(self):
        sm_name = self.ctx.get("monster_name")
        self._start_combat(sm_name, "super_monster", allow_run=False)

    def _action_ignore_super_monster(self):
        self.ctx = {}
        self.screen = "journey"

    # -- Dungeons -------------------------------------------------------
    def _action_enter_dungeon(self):
        self.engine.enter_dungeon(self.dungeon_pending)
        self.dungeon_pending = None
        self._enter_dungeon_floor_preview()

    def _action_ignore_dungeon(self):
        self.dungeon_pending = None
        self.ctx = {}
        self.screen = "journey"

    def _enter_dungeon_floor_preview(self):
        e = self.engine
        monster_name = e.get_dungeon_floor_monster()
        m = MONSTERS[monster_name]
        is_boss = e.dungeon_event_count >= 5
        self.ctx = {
            "floor_monster": monster_name, "floor_number": min(e.dungeon_event_count + 1, 5),
            "monster_fighting": m["fighting"], "monster_defending": m["defending"], "monster_magic": m["magic"],
            "is_boss": is_boss,
        }
        self.screen = "dungeon_boss_preview" if is_boss else "dungeon_floor_preview"

    def _action_engage_floor(self):
        is_boss = self.ctx.get("is_boss", False)
        monster = self.ctx.get("floor_monster")
        self._start_combat(monster, "dungeon_boss" if is_boss else "dungeon_floor", allow_run=False)

    def _action_exit_dungeon(self):
        self.engine.leave_dungeon("exited voluntarily")
        self.ctx = {}
        self.screen = "journey"

    def _dungeon_victory(self):
        e = self.engine
        treasure = random.randint(200, 500)
        e.cash += treasure
        e.leave_dungeon("boss defeated")
        self.ctx = {"treasure": treasure}
        self.screen = "dungeon_victory"

    def _action_dungeon_victory_continue(self):
        self.ctx = {}
        self.screen = "journey"

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
        self.ctx = {}
        self.screen = "journey"

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
        self.screen = "journey"

    # -- Combat -----------------------------------------------------------
    def _start_combat(self, monster_name, kind, allow_run=True):
        m = MONSTERS[monster_name]
        self.ctx = {
            "monster_name": monster_name,
            "monster_fighting": m["fighting"], "monster_defending": m["defending"], "monster_magic": m["magic"],
            "combat_kind": kind, "allow_run": allow_run,
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

    def _action_run_away(self):
        self.ctx = {}
        self.screen = "journey"

    def _resolve_combat_choice(self, choice):
        e = self.engine
        monster = self.ctx["monster_name"]
        kind = self.ctx.get("combat_kind", "regular")
        before_hp = e.hp
        before_cash = e.cash
        before_len = len(e.inventory)

        res = e.resolve_fight(monster, choice=choice)

        if res == "JOURNEY":
            self.ctx["result_text"] = f"You slip past {monster} without a fight!"
            self.ctx["result_won"] = True
            self.ctx["loot_items"] = []
        elif res == "LOSS_WINDOW":
            damage = before_hp - e.hp
            self.ctx["result_text"] = f"You were bested by {monster}! You take {damage} damage."
            self.ctx["result_won"] = False
            self.ctx["damage"] = damage
            if kind in ("dungeon_floor", "dungeon_boss"):
                e.leave_dungeon("defeated in combat")
        else:
            cash_gained = e.cash - before_cash
            new_items = e.inventory[before_len:]
            self.ctx["result_text"] = f"Victory! You defeat {monster}."
            self.ctx["result_won"] = True
            self.ctx["loot_cash"] = cash_gained
            self.ctx["loot_items"] = new_items
            self.ctx["loot_lines"] = self._format_loot_lines(new_items)

        self.screen = "death" if e.game_over else "combat_result"

    def _action_combat_continue(self):
        if not self.ctx.get("result_won"):
            self.ctx = {}
            self.screen = "journey"
            return
        if self.ctx.get("loot_items"):
            self.screen = "loot_screen"
        else:
            self._route_after_win()

    def _action_loot_continue(self):
        self._route_after_win()

    def _route_after_win(self):
        kind = self.ctx.get("combat_kind", "regular")
        if kind == "dungeon_floor":
            self.engine.advance_dungeon_floor()
            self._enter_dungeon_floor_preview()
        elif kind == "dungeon_boss":
            self._dungeon_victory()
        else:
            self.ctx = {}
            self.screen = "journey"

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
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": score,
                             "result": f"Bought {house['name']}"})
        self.ctx = {"final_house": house["name"], "final_score": score, "final_pension": pension}
        self.screen = "capital_result"

    def _action_keep_pension(self):
        e = self.engine
        pension = e.get_pension()
        self.scores.append({"name": e.hero_name, "class": e.hero_class, "score": pension, "result": "Tavern"})
        self.ctx = {"final_house": "Tavern", "final_score": pension, "final_pension": pension}
        self.screen = "capital_result"

    def _action_capital_continue(self):
        self.engine = None
        self.ctx = {}
        self.screen = "front_page"
