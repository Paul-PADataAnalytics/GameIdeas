"""
One-off rebalance tool: reconfigures every non-relic monster's `fighting`
(or `magic`, whichever is that monster's dominant/attack stat) and
`defending` values so they sit inside the per-leg "leveling window" from
leveling_window.py. Relative rank within each leg's monster pool is
preserved via linear rescaling.

A per-leg "gear curve" is layered on top of the base 15%-below-max /
5%-above-min margins, to account for players not yet having best-in-slot
gear for the leg they're currently in. The curve starts at 20% (leg 1) and
drops 5 points per leg, added to the max margin and used directly as the
min margin:
  leg 1: max -35%, min +20%
  leg 2: max -30%, min +15%
  leg 3: max -25%, min +10%
  leg 4: max -20%, min +5%
  leg 5: max -15%, min +0%

Relic-flagged monsters (dungeon bosses / super monsters) are intentionally
left untouched - they are meant to sit above the normal player power curve
and are already scaled separately via RELIC_MONSTER_SCALE.

Run once; it rewrites game_data.py in place.
"""

import re
from game_data import CLASSES, MONSTERS
from leveling_window import compute_window, LEG_TIERS

GAME_DATA_PATH = "game_data.py"

BASE_MAX_MARGIN = 0.15
BASE_MIN_MARGIN = 0.0
CURVE_START = 0.20
CURVE_STEP = 0.05


def curve_for_leg(leg):
    return max(0.0, CURVE_START - CURVE_STEP * (leg - 1))


def combined_window(stat):
    """Per leg: (min, max) combined across all 3 classes."""
    out = {}
    for leg in LEG_TIERS:
        mins = [compute_window(c, leg, stat)["min"] for c in CLASSES]
        maxs = [compute_window(c, leg, stat)["max"] for c in CLASSES]
        out[leg] = (min(mins), max(maxs))
    return out


def target_bounds(leg, window_min, window_max):
    curve = curve_for_leg(leg)
    max_margin = BASE_MAX_MARGIN + curve
    min_margin = BASE_MIN_MARGIN + curve
    return window_min * (1 + min_margin), window_max * (1 - max_margin)


def rescale(value, old_min, old_max, new_low, new_high):
    if old_max == old_min:
        return round((new_low + new_high) / 2)
    ratio = (value - old_min) / (old_max - old_min)
    return round(new_low + ratio * (new_high - new_low))


def main():
    fighting_windows = combined_window("fighting")
    defending_windows = combined_window("defending")
    magic_windows = combined_window("magic")

    new_values = {}  # name -> (new_fighting, new_defending, new_magic_or_None)

    for leg in sorted(LEG_TIERS):
        leg_monsters = {n: m for n, m in MONSTERS.items() if m.get("leg") == leg and not m.get("relic")}
        if not leg_monsters:
            continue

        fight_names = [n for n, m in leg_monsters.items() if m["magic"] <= m["fighting"]]
        magic_names = [n for n, m in leg_monsters.items() if m["magic"] > m["fighting"]]

        f_lo, f_hi = target_bounds(leg, *fighting_windows[leg])
        d_lo, d_hi = target_bounds(leg, *defending_windows[leg])
        m_lo, m_hi = target_bounds(leg, *magic_windows[leg])

        # -- attack stat (fighting-dominant monsters) --
        if fight_names:
            f_vals = [leg_monsters[n]["fighting"] for n in fight_names]
            f_old_min, f_old_max = min(f_vals), max(f_vals)
            for n in fight_names:
                new_f = rescale(leg_monsters[n]["fighting"], f_old_min, f_old_max, f_lo, f_hi)
                new_values.setdefault(n, {})["fighting"] = new_f

        # -- attack stat (magic-dominant monsters, none currently exist but handled) --
        if magic_names:
            m_vals = [leg_monsters[n]["magic"] for n in magic_names]
            m_old_min, m_old_max = min(m_vals), max(m_vals)
            for n in magic_names:
                new_m = rescale(leg_monsters[n]["magic"], m_old_min, m_old_max, m_lo, m_hi)
                new_values.setdefault(n, {})["magic"] = new_m

        # -- defending (always, for every non-relic monster in the leg) --
        d_vals = [m["defending"] for m in leg_monsters.values()]
        d_old_min, d_old_max = min(d_vals), max(d_vals)
        for n in leg_monsters:
            new_d = rescale(leg_monsters[n]["defending"], d_old_min, d_old_max, d_lo, d_hi)
            new_values.setdefault(n, {})["defending"] = new_d

    # Apply to game_data.py source text, one monster line at a time.
    with open(GAME_DATA_PATH, "r") as f:
        lines = f.readlines()

    name_re = re.compile(r'^\s*"([^"]+)":\s*\{')
    changed = 0
    for i, line in enumerate(lines):
        match = name_re.match(line)
        if not match:
            continue
        name = match.group(1)
        if name not in new_values:
            continue
        updates = new_values[name]
        new_line = line
        if "fighting" in updates:
            new_line = re.sub(r'"fighting":\s*\d+', f'"fighting": {updates["fighting"]}', new_line)
        if "defending" in updates:
            new_line = re.sub(r'"defending":\s*\d+', f'"defending": {updates["defending"]}', new_line)
        if "magic" in updates:
            new_line = re.sub(r'"magic":\s*\d+', f'"magic": {updates["magic"]}', new_line)
        if new_line != line:
            lines[i] = new_line
            changed += 1

    with open(GAME_DATA_PATH, "w") as f:
        f.writelines(lines)

    print(f"Updated {changed} monster entries.")
    for leg in sorted(LEG_TIERS):
        print(f"Leg {leg}: fighting window [{fighting_windows[leg][0]}, {fighting_windows[leg][1]}] "
              f"-> target [{target_bounds(leg, *fighting_windows[leg])[0]:.1f}, {target_bounds(leg, *fighting_windows[leg])[1]:.1f}]  "
              f"defending window [{defending_windows[leg][0]}, {defending_windows[leg][1]}] "
              f"-> target [{target_bounds(leg, *defending_windows[leg])[0]:.1f}, {target_bounds(leg, *defending_windows[leg])[1]:.1f}]")


if __name__ == "__main__":
    main()
