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
from hero_engine import HeroAdventureEngine
from game_data import CLASSES, LEGS

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_logs")
JSONL_PATH = os.path.join(LOG_DIR, "sim_events.jsonl")
SUMMARY_PATH = os.path.join(LOG_DIR, "sim_summary.json")

class MonteCarloAgent:
    def __init__(self, run_id, chosen_class=None):
        self.run_id = run_id
        self.hero_class = chosen_class or random.choice(list(CLASSES.keys()))
        self.engine = HeroAdventureEngine(hero_name=f"Hero_{run_id}", hero_class=self.hero_class, fast_mode=True)

    def select_level_up_skills(self):
        """Pick 3 skill level-up choices (+5 each) tailored to class."""
        all_skills = list(self.engine.base_skills.keys())
        if self.hero_class == "Hitter":
            weights = [3, 3, 1, 1, 1, 1, 2, 1]
        elif self.hero_class == "Blaster":
            weights = [1, 1, 3, 1, 1, 3, 1, 2]
        else:
            weights = [1, 1, 1, 3, 3, 3, 1, 1]
            
        chosen = random.choices(all_skills, weights=weights, k=3)
        for sk in chosen:
            self.engine.base_skills[sk] += 5

    def choose_tactical_action(self, event_state, monster_name="Goblin"):
        skills, _, _ = self.engine.get_effective_skills()
        m_def = 25  # estimated monster defense
        
        # Check stealth kill vs steal vs sneak vs fight
        if skills["stealth"] > m_def:
            return "stealth_kill"
        elif (skills["stealth"] + skills["salvaging"]) > (m_def * 2):
            return "steal"
        elif skills["stealth"] > (m_def * 2) and self.engine.hp < 40:
            return "sneak"
        else:
            return "fight"

    def run_full_game(self):
        steps = 0
        max_steps = 300  # safety step cap
        
        while not self.engine.game_over and not self.engine.game_won and steps < max_steps:
            steps += 1
            
            # Phase 9: Use Town Transport if HP < 50 and cash is available
            cost = 10000 + (self.engine.current_leg_idx * 5000)
            if self.engine.hp < 50 and self.engine.cash >= cost:
                self.engine.use_town_transport()

            # Exit dungeon at any time (including boss floors) if HP < 50%
            if self.engine.in_dungeon and self.engine.hp < 50:
                self.engine.in_dungeon = False
                self.engine.log("DUNGEON_EXITED_SAFELY", {"hp": self.engine.hp})
                res = "JOURNEY"
            else:
                res = self.engine.step_next_event()
            
            if res == "LEVEL_UP":
                self.select_level_up_skills()
            elif res in ["DUNGEON_FOUND"]:
                # Enter dungeon only when above 50% HP
                if self.engine.hp > 50:
                    self.engine.in_dungeon = True
                else:
                    self.engine.log("DUNGEON_BYPASSED", {"hp": self.engine.hp})
            elif res == "SUPER_MONSTER":
                # Phase 8: Avoid Super Monster if HP < 60
                sm_name = LEGS[self.engine.current_leg_idx]["super_monster"]
                if self.engine.hp >= 60:
                    choice = self.choose_tactical_action(None, sm_name)
                    self.engine.resolve_fight(sm_name, choice=choice)
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

        # Handle final score if won
        score_info = None
        if self.engine.game_won:
            # Try to buy best house possible
            if self.engine.cash >= 50000:
                score_info = self.engine.calculate_score("Palace")
            elif self.engine.cash >= 20000:
                score_info = self.engine.calculate_score("Mansion")
            elif self.engine.cash >= 10000:
                score_info = self.engine.calculate_score("Castle")
            elif self.engine.cash >= 5000:
                score_info = self.engine.calculate_score("Villa")
            elif self.engine.cash >= 1000:
                score_info = self.engine.calculate_score("Cottage")
            else:
                score_info = self.engine.calculate_score(None)

        return {
            "run_id": self.run_id,
            "class": self.hero_class,
            "won": self.engine.game_won,
            "hp": self.engine.hp,
            "cash": self.engine.cash,
            "death_reason": self.engine.death_reason,
            "relics_found": self.engine.relics_found,
            "score_info": score_info,
            "total_events": len(self.engine.event_logs)
        }

def run_batch_simulation(total_runs=1000):
    os.makedirs(LOG_DIR, exist_ok=True)
    
    print(f"🚀 Starting {total_runs} batch Monte Carlo runs in zero-delay fast mode...")
    
    all_summaries = []
    
    with open(JSONL_PATH, "w") as jsonl_file:
        for i in range(1, total_runs + 1):
            agent = MonteCarloAgent(run_id=i)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hero Adventure Monte Carlo Batch Simulator")
    parser.add_argument("--runs", type=int, default=1000, help="Number of simulation runs (default: 1000)")
    args = parser.parse_args()
    
    run_batch_simulation(args.runs)
