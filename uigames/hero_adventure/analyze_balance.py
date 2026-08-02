"""
Analytics script for Hero Adventure.
Processes sim_summary.json and sim_events.jsonl to calculate win/death rates,
economy progression, monster lethality, and balance recommendations.
"""

import os
import json
from collections import defaultdict, Counter

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_logs")
JSONL_PATH = os.path.join(LOG_DIR, "sim_events.jsonl")
SUMMARY_PATH = os.path.join(LOG_DIR, "sim_summary.json")

def analyze_simulation_results():
    if not os.path.exists(SUMMARY_PATH) or not os.path.exists(JSONL_PATH):
        print("[ANALYTICS ERROR] Simulation log files not found! Run sim_runner.py first.")
        return

    with open(SUMMARY_PATH, "r") as f:
        summaries = json.load(f)

    total_runs = len(summaries)
    wins = [s for s in summaries if s["won"]]
    deaths = [s for s in summaries if not s["won"]]
    
    win_rate = (len(wins) / total_runs) * 100
    death_rate = (len(deaths) / total_runs) * 100

    # Class performance breakdown
    class_stats = defaultdict(lambda: {"total": 0, "wins": 0, "deaths": 0, "scores": [], "cash": []})
    for s in summaries:
        c = s["class"]
        class_stats[c]["total"] += 1
        if s["won"]:
            class_stats[c]["wins"] += 1
            class_stats[c]["scores"].append(s["score_info"]["score"])
            class_stats[c]["cash"].append(s["score_info"]["remaining_cash"])
        else:
            class_stats[c]["deaths"] += 1

    # House distribution
    houses_bought = Counter()
    for w in wins:
        h = w["score_info"]["house"]
        houses_bought[h] += 1

    # Relic distribution
    relics_found_counter = Counter()
    for s in summaries:
        for r in s["relics_found"]:
            relics_found_counter[r] += 1

    # Detailed event analysis from JSONL
    fight_wins = 0
    fight_losses = 0
    monster_deaths = Counter()
    
    with open(JSONL_PATH, "r") as f:
        for line in f:
            log = json.loads(line)
            l_type = log["type"]
            if l_type in ["FIGHT_WIN", "FIGHT_SUCCESS"]:
                fight_wins += 1
            elif l_type == "FIGHT_LOSS":
                fight_losses += 1
                monster_deaths[log["details"]["monster"]] += 1
            elif l_type == "DIED":
                monster_deaths[log["details"]["reason"]] += 1

    print("=================================================================")
    print("      🎮 HERO ADVENTURE - 1,000 RUN MONTE CARLO ANALYSIS          ")
    print("=================================================================")
    print(f"Total Simulation Runs: {total_runs}")
    print(f"Overall Victory Rate : {win_rate:.1f}% ({len(wins)} / {total_runs})")
    print(f"Overall Mortality Rate: {death_rate:.1f}% ({len(deaths)} / {total_runs})")
    print("-----------------------------------------------------------------")
    print("📊 PERFORMANCE BY HERO CLASS:")
    for c, data in class_stats.items():
        c_win_rate = (data["wins"] / data["total"]) * 100
        avg_score = (sum(data["scores"]) / len(data["scores"])) if data["scores"] else 0
        avg_cash = (sum(data["cash"]) / len(data["cash"])) if data["cash"] else 0
        print(f"  • {c:8s} | Runs: {data['total']} | Wins: {data['wins']} ({c_win_rate:.1f}%) | Avg Score: {avg_score:,.0f} | Avg Gold: {avg_cash:,.0f}")
    print("-----------------------------------------------------------------")
    print("🏠 CAPITAL HOUSES ACQUIRED AT RETIREMENT:")
    for house, count in houses_bought.most_common():
        pct = (count / max(1, len(wins))) * 100
        print(f"  • {house:10s}: {count} times ({pct:.1f}%)")
    print("-----------------------------------------------------------------")
    print("💀 TOP MOST LETHAL MONSTERS / DEATH REASONS:")
    for reason, count in monster_deaths.most_common(5):
        print(f"  • {reason}: {count} hero kills")
    print("-----------------------------------------------------------------")
    print("🔮 RELICS DISCOVERED FREQUENCY:")
    for relic, count in relics_found_counter.most_common():
        print(f"  • {relic:32s}: {count} times")
    print("=================================================================")

if __name__ == "__main__":
    analyze_simulation_results()
