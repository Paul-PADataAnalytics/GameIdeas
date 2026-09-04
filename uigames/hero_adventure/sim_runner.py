"""
Fast Automated Agent Simulator for Hero Adventure.
Executes batch Monte Carlo runs (default 1,000 runs) in zero-delay fast mode.
Makes tactical decisions based on character build while varying class & level-up choices.
Outputs detailed JSONL event log and summary analytics JSON.
"""

import os
import json
import argparse
import random
from game_engine import HeroAdventureEngine
from game_data import CLASSES, LEGS, DAMAGE_PER_TOWN_YEAR, TOWN_JOB_OFFER_CHANCE, FORCED_RETIREMENT_AGE

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_logs")
JSONL_PATH = os.path.join(LOG_DIR, "sim_events.jsonl")
SUMMARY_PATH = os.path.join(LOG_DIR, "sim_summary.json")

class MonteCarloAgent:
    def __init__(self, run_id, chosen_class=None, skip_journey_fights=False, relic_scaling_enabled=False,
                 stealth_atk_enabled=True, hider_stat_bonus_enabled=True, throw_item_enabled=True):
        self.run_id = run_id
        self.hero_class = chosen_class or random.choice(list(CLASSES.keys()))
        self.engine = HeroAdventureEngine(
            hero_name=f"Hero_{run_id}", hero_class=self.hero_class, fast_mode=True,
            relic_scaling_enabled=relic_scaling_enabled,
            stealth_atk_enabled=stealth_atk_enabled,
            hider_stat_bonus_enabled=hider_stat_bonus_enabled,
            throw_item_enabled=throw_item_enabled,
        )
        self.skip_journey_fights = skip_journey_fights
        self.engine.skip_journey_fights = skip_journey_fights
        self.town_years = 0
        self.forced_retirement = False

    def select_level_up_skills(self):
        """Pick 3 skill level-up choices (+5 each) tailored to class."""
        all_skills = list(self.engine.base_skills.keys())
        if self.hero_class == "Hitter":
            weights = [3, 3, 1, 1, 2, 1]
        elif self.hero_class == "Blaster":
            weights = [1, 3, 3, 3, 1, 1]
        else:
            weights = [1, 1, 3, 3, 3, 1]
            
        chosen = random.choices(all_skills, weights=weights, k=3)
        for sk in chosen:
            self.engine.base_skills[sk] += 5

    def choose_tactical_action(self, event_state, monster_name="Goblin"):
        # Delegates to the engine's shared tactical-choice logic (stealth_kill
        # / steal / sneak / throw_item / fight) so super monster fights use
        # the same up-to-date decision-making as regular journey fights.
        return self.engine.get_tactical_choice(monster_name)

    def equip_fairy_if_available(self):
        """Prioritize equipping a captured fairy into an accessory slot."""
        has_fairy_equipped = any(
            eq and eq.get("name") == "Captured Fairy" for eq in self.engine.equipment.values()
        )
        if has_fairy_equipped:
            return
        fairy_idx = next(
            (i for i, item in enumerate(self.engine.inventory) if item.get("name") == "Captured Fairy"),
            None,
        )
        if fairy_idx is None:
            return
        fairy = self.engine.inventory.pop(fairy_idx)
        target_slot = "accessory_1" if not self.engine.equipment.get("accessory_1") else "accessory_2"
        old = self.engine.equipment.get(target_slot)
        if old:
            self.engine.inventory.append(old)
        self.engine.equipment[target_slot] = fairy

    def town_recovery(self):
        """Headless equivalent of the interactive town-recovery loop: heals
        the hero fully, one year at a time, aging them along the way. Rolls
        the same 5% early-retirement job offer each year (always declined,
        since the agent's goal is to complete the journey) and the same
        forced retirement at FORCED_RETIREMENT_AGE. Returns True if the hero
        was forced into retirement, ending the run early."""
        while self.engine.hp < self.engine.max_hp:
            heal = min(DAMAGE_PER_TOWN_YEAR, self.engine.max_hp - self.engine.hp)
            self.engine.hp += heal
            self.engine.age += 1
            self.town_years += 1
            self.engine.log("TOWN_RECOVERY_YEAR", {"age": self.engine.age, "hp": self.engine.hp})
            if self.engine.age >= FORCED_RETIREMENT_AGE:
                self.forced_retirement = True
                self.engine.log("FORCED_RETIREMENT", {"age": self.engine.age})
                return True
            if random.random() < TOWN_JOB_OFFER_CHANCE:
                self.engine.log("TOWN_JOB_OFFER_DECLINED", {"age": self.engine.age})
        return False

    def run_full_game(self):
        steps = 0
        max_steps = 300  # safety step cap
        
        while not self.engine.game_over and not self.engine.game_won and steps < max_steps:
            steps += 1

            # Exit dungeon at any time (including boss floors) if HP < 50%
            if self.engine.in_dungeon and self.engine.hp < 50:
                self.engine.in_dungeon = False
                self.engine.log("DUNGEON_EXITED_SAFELY", {"hp": self.engine.hp})
                res = "JOURNEY"
            else:
                res = self.engine.step_next_event()
            
            if res == "LEVEL_UP":
                if self.town_recovery():
                    break
                self.select_level_up_skills()
            elif res in ["DUNGEON_FOUND"]:
                # In no-journey-fights mode, avoid dungeons entirely to model
                # near-guaranteed survivability from encounter skipping.
                if self.skip_journey_fights:
                    self.engine.log("DUNGEON_BYPASSED", {"reason": "skip_journey_fights_mode"})
                # Enter dungeon only when above 50% HP
                elif self.engine.hp > 50:
                    self.engine.in_dungeon = True
                else:
                    self.engine.log("DUNGEON_BYPASSED", {"hp": self.engine.hp})
            elif res == "FAIRY_FOUND":
                self.equip_fairy_if_available()
            elif res == "SUPER_MONSTER":
                sm_name = LEGS[self.engine.current_leg_idx]["super_monster"]
                # In no-journey-fights mode, always bypass.
                if self.skip_journey_fights:
                    self.engine.log("SUPER_MONSTER_BYPASSED", {"monster": sm_name, "reason": "skip_journey_fights_mode"})
                # Default behavior: avoid only when low HP.
                elif self.engine.hp >= 60:
                    choice = self.choose_tactical_action(None, sm_name)
                    self.engine.resolve_fight(sm_name, choice=choice, encounter_type="super_monster")
                else:
                    self.engine.log("SUPER_MONSTER_BYPASSED", {"monster": sm_name, "hp": self.engine.hp})
            elif res == "WANDERING_TRADER":
                # Check Philosopher's Stone for 1.1x buy rate instead of 1.4x
                has_p_stone = any(eq and eq.get("name") == "Alchemist's Philosopher Stone" for eq in self.engine.equipment.values())
                buy_mult = 1.10 if has_p_stone else 1.40
                
                item = self.engine.generate_random_item(leg_num=self.engine.current_leg_idx+1)
                cost = int(item["value"] * buy_mult)
                if self.engine.cash >= cost:
                    self.engine.cash -= cost
                    self.engine.inventory.append(item)
                    self.engine.auto_equip_best()

        # Handle final score if won or forced into retirement
        score_info = None
        if self.engine.game_won or self.forced_retirement:
            # Try to buy best house possible
            if self.engine.cash >= 50000:
                house_name = "Palace"
            elif self.engine.cash >= 20000:
                house_name = "Mansion"
            elif self.engine.cash >= 10000:
                house_name = "Castle"
            elif self.engine.cash >= 5000:
                house_name = "Villa"
            elif self.engine.cash >= 1000:
                house_name = "Cottage"
            else:
                house_name = None
            score_info = self.engine.calculate_score(house_name, failed_adventurer=self.forced_retirement)

        return {
            "run_id": self.run_id,
            "class": self.hero_class,
            "won": self.engine.game_won,
            "forced_retirement": self.forced_retirement,
            "hp": self.engine.hp,
            "cash": self.engine.cash,
            "death_reason": self.engine.death_reason,
            "relics_found": self.engine.relics_found,
            "score_info": score_info,
            "total_events": len(self.engine.event_logs),
            "town_years": self.town_years,
            "ending_age": self.engine.age
        }

def run_batch_simulation(total_runs=1000, skip_journey_fights=False, relic_scaling_enabled=False,
                          stealth_atk_enabled=True, hider_stat_bonus_enabled=True, throw_item_enabled=True):
    os.makedirs(LOG_DIR, exist_ok=True)
    
    print(f"🚀 Starting {total_runs} batch Monte Carlo runs in zero-delay fast mode...")
    
    all_summaries = []
    
    with open(JSONL_PATH, "w") as jsonl_file:
        for i in range(1, total_runs + 1):
            agent = MonteCarloAgent(
                run_id=i, skip_journey_fights=skip_journey_fights, relic_scaling_enabled=relic_scaling_enabled,
                stealth_atk_enabled=stealth_atk_enabled, hider_stat_bonus_enabled=hider_stat_bonus_enabled,
                throw_item_enabled=throw_item_enabled,
            )
            summary = agent.run_full_game()
            all_summaries.append(summary)
            
            # Write detailed logs to JSONL
            for log_entry in agent.engine.event_logs:
                log_entry["run_id"] = i
                log_entry["class"] = agent.hero_class
                jsonl_file.write(json.dumps(log_entry) + "\n")
                
            if i % 100 == 0:
                print(f"  Progress: {i}/{total_runs} runs completed...")

    # Write summary output
    with open(SUMMARY_PATH, "w") as sum_file:
        json.dump(all_summaries, sum_file, indent=2)

    print(f"✅ Simulation complete! Wrote full JSONL telemetry to {JSONL_PATH} and summary to {SUMMARY_PATH}")
    print_aging_stats(all_summaries)


def print_aging_stats(all_summaries):
    """Reports town-recovery (rest) and ending-age stats across the batch."""
    def avg(vals):
        vals = list(vals)
        return round(sum(vals) / len(vals), 1) if vals else 0

    total = len(all_summaries)
    wins = [s for s in all_summaries if s["won"]]
    forced = [s for s in all_summaries if s["forced_retirement"]]
    deaths = [s for s in all_summaries if not s["won"] and not s["forced_retirement"]]

    print("\n--- Aging & Town Recovery Stats ---")
    print(f"Runs: {total}  |  Wins: {len(wins)}  |  Forced retirements (age {FORCED_RETIREMENT_AGE}): {len(forced)}  |  Deaths: {len(deaths)}")
    print(f"Town years rested - avg: {avg(s['town_years'] for s in all_summaries)}  "
          f"(wins: {avg(s['town_years'] for s in wins)}, "
          f"forced: {avg(s['town_years'] for s in forced)}, "
          f"deaths: {avg(s['town_years'] for s in deaths)})")
    print(f"Ending age - avg: {avg(s['ending_age'] for s in all_summaries)}  "
          f"(wins: {avg(s['ending_age'] for s in wins)}, "
          f"forced: {avg(s['ending_age'] for s in forced)}, "
          f"deaths: {avg(s['ending_age'] for s in deaths)})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hero Adventure Monte Carlo Batch Simulator")
    parser.add_argument("--runs", type=int, default=1000, help="Number of simulation runs (default: 1000)")
    parser.add_argument("--skip-journey-fights", action="store_true",
                        help="Bypass all non-dungeon fights (regular and super monsters).")
    parser.add_argument("--relic-scaling", action="store_true",
                        help="Experimental: scale relic-flagged monsters (bosses/super monsters) up independently of regular per-leg monster stats.")
    parser.add_argument("--no-stealth-atk", action="store_true",
                        help="Disable counting stealth as a combat-attack stat (isolates that change for A/B testing).")
    parser.add_argument("--no-hider-bonus", action="store_true",
                        help="Disable Hider's fighting/defending stat floor bump (isolates that change for A/B testing).")
    parser.add_argument("--no-throw-item", action="store_true",
                        help="Disable the AI's use of the throw_item escape option (isolates that change for A/B testing).")
    args = parser.parse_args()
    
    run_batch_simulation(
        args.runs, skip_journey_fights=args.skip_journey_fights, relic_scaling_enabled=args.relic_scaling,
        stealth_atk_enabled=not args.no_stealth_atk, hider_stat_bonus_enabled=not args.no_hider_bonus,
        throw_item_enabled=not args.no_throw_item,
    )
