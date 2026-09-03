"""
Combat-odds analysis: for a "typical" (median-stat, per leveling_window.py)
hero of each class entering each leg, computes the exact win probability
against every non-relic monster in that leg, using the same round-based
race model as HeroEngine.estimate_fight_risk (no relic procs/items).

Used to check how many monster matchups are effectively "guaranteed wins"
(win_pct == 100) before vs after a monster-stat rebalance, since the goal
of the balance pass is to reduce the count of those certain-win fights.
"""

import math
import sys

STATS = ["fighting", "defending", "magic", "stealth", "salvaging", "spotting", "camping", "medical"]


def load_module_from_file(path, modname):
    """Loads a game_data.py-shaped file into its own fresh module namespace,
    so we can compare two versions (e.g. original vs rebalanced) side by side
    without Python's module cache getting in the way."""
    import importlib.util
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader(modname, path)
    spec = importlib.util.spec_from_loader(modname, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def win_probability(player_atk, effective_def, m_fighting, m_defending, player_hp=100):
    monster_hp = max(20, (m_fighting + m_defending) * 2)
    player_round_damage = max(5, player_atk - m_defending)
    monster_round_damage = max(5, m_fighting - effective_def)
    rounds_to_kill = max(1, math.ceil(monster_hp / player_round_damage))
    rounds_to_die = max(1, math.ceil(player_hp / monster_round_damage))
    round_cap = 8

    wins = 0
    for p_die in range(1, 21):
        for m_die in range(1, 21):
            p_power = player_atk + effective_def + p_die
            m_power = m_fighting + m_defending + m_die
            if p_power > m_power:
                wins += 1
    p_round = wins / 400.0
    q_round = 1.0 - p_round

    states = {(0, 0): 1.0}
    win_prob = 0.0
    for _ in range(round_cap):
        next_states = {}
        for (w, l), prob in states.items():
            if prob <= 0:
                continue
            w2 = w + 1
            pw = prob * p_round
            if w2 >= rounds_to_kill:
                win_prob += pw
            else:
                next_states[(w2, l)] = next_states.get((w2, l), 0.0) + pw
            l2 = l + 1
            pl = prob * q_round
            if l2 < rounds_to_die:
                next_states[(w, l2)] = next_states.get((w, l2), 0.0) + pl
        states = next_states
    return win_prob


def typical_player_stats(leveling_mod, game_data_mod, class_name, leg):
    """Median stat block for a 'typical' hero of `class_name` at `leg`,
    per leveling_window.py's per-leg permutation model."""
    medians = {s: leveling_mod.compute_window(class_name, leg, s)["median"] for s in STATS}
    effective_def = medians["defending"]
    if medians["magic"] > medians["fighting"]:
        effective_def += medians["magic"] * 0.5
    player_atk = max(medians["fighting"], medians["magic"], medians["stealth"] * 0.5)
    return player_atk, effective_def


def analyze(game_data_path, leveling_window_path, label):
    game_data_mod = load_module_from_file(game_data_path, f"game_data_{label}")
    leveling_mod = load_module_from_file(leveling_window_path, f"leveling_window_{label}")
    # leveling_window.py imports game_data at module scope, so swap in the right version.
    leveling_mod.CLASSES = game_data_mod.CLASSES
    leveling_mod.ITEM_CATEGORIES = game_data_mod.ITEM_CATEGORIES
    leveling_mod.QUALITY_TIERS = game_data_mod.QUALITY_TIERS

    results = {}  # (class, leg) -> list of (monster_name, win_pct)
    for class_name in game_data_mod.CLASSES:
        for leg in range(1, 6):
            player_atk, effective_def = typical_player_stats(leveling_mod, game_data_mod, class_name, leg)
            monsters = {n: m for n, m in game_data_mod.MONSTERS.items() if m.get("leg") == leg and not m.get("relic")}
            rows = []
            for name, m in monsters.items():
                wp = win_probability(player_atk, effective_def, m["fighting"], m["defending"])
                rows.append((name, round(wp * 100)))
            results[(class_name, leg)] = rows
    return results


def summarize(results, label):
    print(f"\n=== {label} ===")
    print(f"{'Class':10s} {'Leg':>3s} | {'#Monsters':>9s} | {'#100% wins':>10s} | {'#0% wins':>8s} | {'Avg win%':>8s}")
    for (class_name, leg), rows in sorted(results.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = len(rows)
        certain = sum(1 for _, wp in rows if wp >= 100)
        hopeless = sum(1 for _, wp in rows if wp <= 0)
        avg = sum(wp for _, wp in rows) / total if total else 0
        print(f"{class_name:10s} {leg:3d} | {total:9d} | {certain:10d} | {hopeless:8d} | {avg:8.1f}")


if __name__ == "__main__":
    before = analyze("game_data.py.bak", "leveling_window.py", "before")
    after = analyze("game_data.py", "leveling_window.py", "after")
    summarize(before, "BEFORE (original monster stats)")
    summarize(after, "AFTER (curved rebalance)")
