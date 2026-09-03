"""
Sneak/steal/stealth-kill odds analysis: same before/after comparison as
combat_odds.py, but for the stealth-based avoidance actions instead of
straight fighting. Uses the exact single-roll opposed-check formula from
HeroEngine._opposed_win_probability (same math as _opposed_roll, just
computed exactly instead of sampled).

Note: "running away" itself has no success roll in this game - the
interactive controller's run-away action (_action_run_away) is a free,
always-successful bail-out with no stat check, so there's no probability
to compare there. Sneak/steal/stealth_kill are the actual stat-gated
avoidance mechanics, all keyed off the monster's `defending` stat.
"""

from combat_odds import load_module_from_file, STATS

SNEAK_ACTIONS = ["sneak", "steal", "stealth_kill"]


def opposed_win_probability(attacker_stat, defender_stat, die=20):
    wins = 0
    for a in range(1, die + 1):
        for d in range(1, die + 1):
            if attacker_stat + a > defender_stat + d:
                wins += 1
    return wins / float(die * die)


def action_probs(stealth, salvaging, m_defending):
    return {
        "sneak": opposed_win_probability(stealth, m_defending),
        "steal": opposed_win_probability(stealth + salvaging, m_defending * 2),
        "stealth_kill": opposed_win_probability(stealth * 2, int(m_defending * 1.5)),
    }


def analyze(game_data_path, leveling_window_path, label):
    game_data_mod = load_module_from_file(game_data_path, f"game_data_{label}")
    leveling_mod = load_module_from_file(leveling_window_path, f"leveling_window_{label}")
    leveling_mod.CLASSES = game_data_mod.CLASSES
    leveling_mod.ITEM_CATEGORIES = game_data_mod.ITEM_CATEGORIES
    leveling_mod.QUALITY_TIERS = game_data_mod.QUALITY_TIERS

    results = {}  # (class, leg) -> list of (monster_name, {action: pct})
    for class_name in game_data_mod.CLASSES:
        for leg in range(1, 6):
            stealth_med = leveling_mod.compute_window(class_name, leg, "stealth")["median"]
            salvaging_med = leveling_mod.compute_window(class_name, leg, "salvaging")["median"]
            monsters = {n: m for n, m in game_data_mod.MONSTERS.items() if m.get("leg") == leg and not m.get("relic")}
            rows = []
            for name, m in monsters.items():
                probs = action_probs(stealth_med, salvaging_med, m["defending"])
                rows.append((name, {k: round(v * 100) for k, v in probs.items()}))
            results[(class_name, leg)] = rows
    return results


def summarize(results, label):
    print(f"\n=== {label} ===")
    print(f"{'Class':10s} {'Leg':>3s} | {'#Monsters':>9s} | "
          f"{'Sneak avg%':>10s} {'#100%':>6s} {'#0%':>4s} | "
          f"{'Steal avg%':>10s} {'#100%':>6s} {'#0%':>4s} | "
          f"{'SKill avg%':>10s} {'#100%':>6s} {'#0%':>4s}")
    for (class_name, leg), rows in sorted(results.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = len(rows)
        line = f"{class_name:10s} {leg:3d} | {total:9d} |"
        for action in SNEAK_ACTIONS:
            vals = [r[1][action] for r in rows]
            avg = sum(vals) / total if total else 0
            hundred = sum(1 for v in vals if v >= 100)
            zero = sum(1 for v in vals if v <= 0)
            line += f" {avg:10.1f} {hundred:6d} {zero:4d} |"
        print(line)


if __name__ == "__main__":
    before = analyze("game_data.py.bak", "leveling_window.py", "before")
    after = analyze("game_data.py", "leveling_window.py", "after")
    summarize(before, "BEFORE (original monster stats)")
    summarize(after, "AFTER (curved rebalance)")
