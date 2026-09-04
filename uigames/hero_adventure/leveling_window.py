"""
Leveling Window balance tool for Hero Adventure.

For each class and each leg, computes the full permutation space of a
single stat's value from:
  - this leg's level-up choice (the stat is one of the 3 chosen for +5, or not)
  - the equipment obtainable as loot during this leg (excluding relics /
    super-monster "super loot"), at every quality tier that can actually
    drop in that leg

and reports min, median, and max across that permutation set, plus the
permutation count. This is a per-leg snapshot (base class stat + this
leg's choices only), not a cumulative carry-over across legs.

Source of truth: CLASSES, ITEM_CATEGORIES, QUALITY_TIERS in game_data.py.
Tier-per-leg availability and slot-bonus rules mirror
HeroAdventureEngine.generate_random_item in game_engine.py.
"""

import statistics
from game_data import CLASSES, ITEM_CATEGORIES, QUALITY_TIERS

STATS = ["fighting", "defending", "magic", "stealth", "salvaging", "speech"]

# Quality tiers that can actually drop in each leg (probability > 0),
# per the r-based branches in HeroEngine.generate_random_item. Relics
# ("super loot") are excluded entirely - they are handled separately.
LEG_TIERS = {
    1: ["Common"],
    2: ["Common", "Uncommon"],
    3: ["Common", "Uncommon", "Rare"],
    4: ["Uncommon", "Rare", "Epic"],
    5: ["Rare", "Epic"],
}

# A stat's directly-matching loot category (the item always rolls that
# stat's skill). "speech" has no direct category in ITEM_CATEGORIES -
# it can only be boosted by a lucky "accessories" roll.
STAT_TO_CATEGORY = {
    "fighting": "fighting",
    "defending": "defending",
    "magic": "magic",
    "stealth": "stealth",
    "salvaging": "salvaging",
    "speech": None,
}


def item_bonus(cat_key):
    """Reproduces the slot-bonus rule from generate_random_item."""
    cat_data = ITEM_CATEGORIES[cat_key]
    if cat_data["slot"] == "defending_armor":
        return 20
    elif cat_key in ["fighting", "stealth"]:
        return 10
    return 0


def base_stats_for_class(class_name):
    stats = {s: 5 for s in STATS}
    for skill, boost in CLASSES[class_name].items():
        stats[skill] += boost
    return stats


def equipment_options(stat, leg):
    """All discrete equipment contributions obtainable for `stat` in `leg`,
    including 0 (no drop). Combines the stat's direct category (if any)
    with the always-possible "accessories" wildcard roll."""
    options = {0}
    tiers = LEG_TIERS[leg]

    direct_cat = STAT_TO_CATEGORY[stat]
    if direct_cat is not None:
        bonus = item_bonus(direct_cat)
        for tier in tiers:
            q = QUALITY_TIERS[tier]
            options.add(q["skill_min"] + bonus)
            options.add(q["skill_max"] + bonus)

    # "accessories" can randomly roll ANY stat (speech's only source), bonus is always 0
    acc_bonus = item_bonus("accessories")
    for tier in tiers:
        q = QUALITY_TIERS[tier]
        options.add(q["skill_min"] + acc_bonus)
        options.add(q["skill_max"] + acc_bonus)

    return sorted(options)


def compute_window(class_name, leg, stat):
    base = base_stats_for_class(class_name)[stat]
    level_up_options = [0, 5]
    eq_options = equipment_options(stat, leg)

    perms = [base + lvl + eq for lvl in level_up_options for eq in eq_options]
    return {
        "base": base,
        "min": min(perms),
        "median": statistics.median(perms),
        "max": max(perms),
        "permutations": len(perms),
    }


def render_markdown():
    lines = []
    lines.append("# Hero Adventure — Leveling Window Report")
    lines.append("")
    lines.append("Per-leg permutation window for each stat: base class stat, plus this leg's")
    lines.append("level-up choice (+5 or +0), plus this leg's obtainable loot (every quality")
    lines.append("tier that can drop that leg, best and worst roll, on the stat's matching")
    lines.append("item category and the wildcard \"accessories\" slot). Relics / super-monster")
    lines.append("loot are excluded. Each leg is an independent snapshot, not a carry-over")
    lines.append("from previous legs.")
    lines.append("")
    lines.append("Note: `speech` has no dedicated loot category - its only equipment source")
    lines.append("is a lucky \"accessories\" roll (bonus +0).")
    lines.append("")

    for class_name in CLASSES:
        lines.append(f"## {class_name}")
        lines.append("")
        for leg in sorted(LEG_TIERS):
            tiers = ", ".join(LEG_TIERS[leg])
            lines.append(f"### Leg {leg} (available tiers: {tiers})")
            lines.append("")
            lines.append("| Stat | Base | Min | Median | Max | Permutations |")
            lines.append("|------|-----:|----:|-------:|----:|-------------:|")
            for stat in STATS:
                w = compute_window(class_name, leg, stat)
                lines.append(
                    f"| {stat} | {w['base']} | {w['min']} | {w['median']:g} | {w['max']} | {w['permutations']} |"
                )
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    report = render_markdown()
    print(report)
