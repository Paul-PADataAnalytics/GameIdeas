# Hero Adventure — Static Balance Analysis Report

> **STALE:** This report predates the removal of the camping/medical/spotting
> skills and equipment slots and the addition of the speech skill (see
> CLASSES/ITEM_CATEGORIES in game_data.py). The per-stat numbers below no
> longer reflect the current 6-skill, 5-slot design and should be
> regenerated (e.g. via leveling_window.py / combat_odds.py) before reuse.

**Purpose:** Establish expected hero stats at two key checkpoints — **Leg Start** and **Event 10** — for each class and leg. Use as baseline targets before simulation-driven monster balancing.

---

## Methodology

- **Leg Start** = base class stats + best equipment carried over from the *previous* leg's quality tier
- **Event 10** = base class stats + current leg's quality tier equipment assumed filling all 7 slots (historical; now 5 slots)
- All estimates use the **midpoint** of each quality tier's skill range + slot bonus
- **No relics included** (each adds +50 to one stat — covered separately)
- **No weight penalties** assumed (inventory well-managed)
- Equipment slot bonuses: `defending_armor` +20, `fighting_weapon` / `stealth armor` +10, others +0

---

## Base Stats (No Equipment)

| Stat       | Hitter | Blaster | Hider |
|------------|--------|---------|-------|
| fighting   | **25** | 5       | 5     |
| defending  | **25** | 5       | 5     |
| magic      | 5      | **25**  | 5     |
| stealth    | 5      | 5       | **25**|
| salvaging  | 5      | 5       | **25**|
| spotting   | 5      | **25**  | **25**|
| camping    | **25** | 5       | 5     |
| medical    | 5      | **25**  | 5     |

All base skills start at 5; each class receives +20 to 3 skills.

---

## Equipment Quality Tier Probabilities & Average Item Bonus

| Leg | Common | Uncommon | Rare | Epic | Avg Item Bonus (raw) |
|-----|--------|----------|------|------|----------------------|
| 1   | 70%    | 25%      | 5%   | 0%   | ~16                  |
| 2   | 40%    | 45%      | 15%  | 0%   | ~22                  |
| 3   | 0%     | 50%      | 40%  | 10%  | ~34                  |
| 4   | 0%     | 0%       | 60%  | 40%  | ~47                  |
| 5   | 0%     | 0%       | 60%  | 40%  | ~47 (same as leg 4)  |

Legs 4 and 5 share the same loot tier — the gear ceiling is reached at leg 4.

---

## Full Stat Projections Per Leg

### Leg 1 — Startersville to Forest Edge

| Stat       | Hitter Start | Hitter Ev10 | Blaster Start | Blaster Ev10 | Hider Start | Hider Ev10 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| fighting   | 25  | 37  | 5   | 17  | 5   | 17  |
| defending  | 25  | 46  | 5   | 26  | 5   | 26  |
| magic      | 5   | 17  | 25  | 37  | 5   | 17  |
| stealth    | 5   | 19  | 5   | 19  | 25  | 39  |
| salvaging  | 5   | 18  | 5   | 18  | 25  | 38  |
| spotting   | 5   | 18  | 25  | 38  | 25  | 38  |
| camping    | 25  | 32  | 5   | 12  | 5   | 12  |
| medical    | 5   | 12  | 25  | 32  | 5   | 12  |

### Leg 2 — Forest Edge to Mountain Pass

| Stat       | Hitter Start | Hitter Ev10 | Blaster Start | Blaster Ev10 | Hider Start | Hider Ev10 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| fighting   | 37  | 40  | 17  | 20  | 17  | 20  |
| defending  | 46  | 49  | 26  | 29  | 26  | 29  |
| magic      | 17  | 20  | 37  | 40  | 17  | 20  |
| stealth    | 19  | 22  | 19  | 22  | 39  | 42  |
| salvaging  | 18  | 24  | 18  | 24  | 38  | 44  |
| spotting   | 18  | 24  | 38  | 44  | 38  | 44  |
| camping    | 32  | 35  | 12  | 15  | 12  | 15  |
| medical    | 12  | 15  | 32  | 35  | 12  | 15  |

### Leg 3 — Mountain Pass to Desert Crossing

| Stat       | Hitter Start | Hitter Ev10 | Blaster Start | Blaster Ev10 | Hider Start | Hider Ev10 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| fighting   | 40  | 47  | 20  | 27  | 20  | 27  |
| defending  | 49  | 57  | 29  | 37  | 29  | 37  |
| magic      | 20  | 27  | 40  | 47  | 20  | 27  |
| stealth    | 22  | 27  | 22  | 27  | 42  | 47  |
| salvaging  | 24  | 37  | 24  | 37  | 44  | 57  |
| spotting   | 24  | 37  | 44  | 57  | 44  | 57  |
| camping    | 35  | 42  | 15  | 22  | 15  | 22  |
| medical    | 15  | 22  | 35  | 42  | 15  | 22  |

### Leg 4 — Desert Crossing to Riverlands

| Stat       | Hitter Start | Hitter Ev10 | Blaster Start | Blaster Ev10 | Hider Start | Hider Ev10 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| fighting   | 47  | 55  | 27  | 35  | 27  | 35  |
| defending  | 57  | 66  | 37  | 46  | 37  | 46  |
| magic      | 27  | 35  | 47  | 55  | 27  | 35  |
| stealth    | 27  | 34  | 27  | 34  | 47  | 54  |
| salvaging  | 37  | 51  | 37  | 51  | 57  | 71  |
| spotting   | 37  | 51  | 57  | 71  | 57  | 71  |
| camping    | 42  | 50  | 22  | 30  | 22  | 30  |
| medical    | 22  | 30  | 42  | 50  | 22  | 30  |

### Leg 5 — Riverlands to Capital

| Stat       | Hitter Start | Hitter Ev10 | Blaster Start | Blaster Ev10 | Hider Start | Hider Ev10 |
|------------|:---:|:---:|:---:|:---:|:---:|:---:|
| fighting   | 55  | 55  | 35  | 35  | 35  | 35  |
| defending  | 66  | 66  | 46  | 46  | 46  | 46  |
| magic      | 35  | 35  | 55  | 55  | 35  | 35  |
| stealth    | 34  | 34  | 34  | 34  | 54  | 54  |
| salvaging  | 51  | 51  | 51  | 51  | 71  | 71  |
| spotting   | 51  | 51  | 71  | 71  | 71  | 71  |
| camping    | 50  | 50  | 30  | 30  | 30  | 30  |
| medical    | 30  | 30  | 50  | 50  | 30  | 30  |

> **Note:** Leg 5 Start = Leg 5 Event 10 because loot quality doesn't improve between legs 4 and 5 — the gear ceiling is already reached.

---

## Key Combat Stats Summary (Primary Attack + Defense, No Relics)

| Leg | Point    | Hitter Fight | Hitter Def | Blaster Magic | Blaster Def | Hider Stealth | Hider Def |
|-----|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1   | Start    | 25  | 25  | 25  | 5   | 25  | 5   |
| 1   | Event 10 | 47  | 57  | 47  | 37  | 57  | 37  |
| 2   | Start    | 47  | 57  | 47  | 37  | 57  | 37  |
| 2   | Event 10 | 52  | 62  | 52  | 42  | 62  | 42  |
| 3   | Start    | 52  | 62  | 52  | 42  | 62  | 42  |
| 3   | Event 10 | 64  | 74  | 64  | 54  | 74  | 54  |
| 4   | Start    | 64  | 74  | 64  | 54  | 74  | 54  |
| 4   | Event 10 | 78  | 88  | 78  | 68  | 88  | 68  |
| 5   | Start    | 78  | 88  | 78  | 68  | 88  | 68  |
| 5   | Event 10 | 78  | 88  | 78  | 68  | 88  | 68  |

> All three classes reach equivalent **primary attack** scores per leg because the weapon slot generates the same expected bonus regardless of class. Class differences show up in *secondary* stats and non-combat utility.

---

## Combat Resolution Reminder

```
Win if: (player_atk > monster_defending) AND (p_score >= m_score)
  p_score = player_atk - monster_defending
  m_score = monster_fighting - player_defending

HP loss on defeat = max(5, monster_fighting - player_defending)
```

Blaster: `player_atk = max(fighting, magic)` — so magic items directly feed attack.  
Hider: stealth enables `sneak` / `steal` / `stealth_kill` bypasses — defence stat less critical.

---

## Relic Impact

Each relic adds **+50** to one stat. Key relics per class:

| Class   | Key Relic(s)                         | Stat Boosted    | Combat Effect                          |
|---------|--------------------------------------|-----------------|----------------------------------------|
| Hitter  | Sword of Power, Plate of Invincibility | fighting +50, defending +50 | Re-roll a fight loss 50% of time; both = always win |
| Blaster | Staff of Magic, Crown of Archmage    | magic +50       | Re-roll magic loss; magic fully replaces defending  |
| Hider   | Cloak of Invisibility, Shadowstep Dagger | stealth +50 | Always win stealth; always stealth kill |

A single relic pushes the relevant combat stat from ~**55–88** to ~**105–138** — representing a massive power spike. Monster tuning should assume **0–1 relics** for legs 1–2, **1–2 relics** for legs 3–4, and **2–3 relics** for leg 5.

---

## Observations & Flags for Simulation

1. **Leg 1 is rough at the start** — non-class stats are only 5, meaning Blaster/Hider defending = 5 vs leg-1 monster fighting values of 9–17. Early deaths likely for non-optimal builds.

2. **Gear ceiling hits at Leg 4** — Leg 5 adds no new tier; heroes plateau. Monster stats must escalate without gear support.

3. **Blaster/Hider defending is consistently ~20 lower than Hitter** through all legs — expect higher HP loss rates for these classes.

4. **Stealth classes (Hider) converge on fighting classes** in primary attack by mid-game via sneak/kill paths; not reflected in raw fight stat.

5. **The Lich (Leg 3 dungeon)** has fighting=48, defending=44 — the static analysis suggests only a player with `fighting/magic ≈ 47–64` at Event 10 of Leg 3. This is borderline and likely to cause deaths without relic support.

---

*Next step: run simulations to validate these projections against actual HP survival rates and cash accumulation per class per leg.*

---

## ✅ Corrected Combat Stats — Class Mechanics Properly Applied

The initial summary treated all classes identically. The engine already implements two important mechanics that significantly change the picture:

### Blaster: Magic Contributes to Effective Defence
```python
# In resolve_fight():
if skills["magic"] > skills["fighting"]:   # always true for Blaster
    effective_def += int(skills["magic"] * 0.5)
```
Blaster's **effective defence = defending + (magic × 0.5)**. With the Arcane Amulet relic this becomes magic × 1.0 (full conversion).

### Hider: Stealth Kill Uses stealth × 2 as Attack
```python
# stealth_kill formula:
surprise_stealth = skills["stealth"] * 2   # Hider's true attack score
surprise_def     = monster_defending * 1.5  # what they must beat
```
The Hider's **effective attack = stealth × 2**, not the raw stealth value shown earlier.

---

### Corrected Key Combat Stats

| Leg | Point    | Hitter Atk | Hitter Def | Blaster Atk | Blaster EffDef | Hider StkAtk | Hider Def |
|-----|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1   | Start    | 25  | 25  | 25  | 18  | **50**  | 5   |
| 1   | Event 10 | 47  | 57  | 47  | **60**  | **114** | 37  |
| 2   | Start    | 47  | 57  | 47  | 60  | 114 | 37  |
| 2   | Event 10 | 52  | 62  | 52  | **68**  | **124** | 42  |
| 3   | Start    | 52  | 62  | 52  | 68  | 124 | 42  |
| 3   | Event 10 | 64  | 74  | 64  | **87**  | **149** | 54  |
| 4   | Start    | 64  | 74  | 64  | 87  | 149 | 54  |
| 4   | Event 10 | 78  | 88  | 78  | **107** | **176** | 68  |
| 5   | Start    | 78  | 88  | 78  | 107 | 176 | 68  |
| 5   | Event 10 | 78  | 88  | 78  | 107 | 176 | 68  |

### Stealth Kill Threshold Check (Hider vs monsters per leg)

| Leg | Monster def×1.5 range | Avg threshold | Hider StkAtk Start | Hider StkAtk Ev10 | Result |
|-----|----------------------|:---:|:---:|:---:|---|
| 1   | 8 – 26               | 15  | 50  | 114 | ✅ Hider **dominates** all leg-1 monsters from the start |
| 2   | 15 – 34              | 25  | 114 | 124 | ✅ Well above threshold |
| 3   | 27 – 66              | 40  | 124 | 149 | ✅ Comfortable, top-end monsters still manageable |
| 4   | 33 – 54              | 45  | 149 | 176 | ✅ Clearly ahead |
| 5   | 45 – 78              | 61  | 176 | 176 | ✅ Stays ahead but the gap narrows |

---

## Revised Balance Observations

1. **Hider is the strongest combat class throughout** — `stealth × 2` consistently doubles the raw stealth stat, massively outpacing the monster `defending × 1.5` threshold at every leg. The Hider also gains loot on stealth kills, so they lose no income compared to straight fights.

2. **Blaster defence is actually comparable to Hitter** by Event 10 of Leg 1 (eff_def 60 vs Hitter's 57), and pulls further ahead at every subsequent leg (Leg 5: 107 vs 88). The Blaster is arguably the tankiest class in the late game.

3. **Hitter is the weakest class** — the original "balanced" class now looks like it falls behind on both offence (vs Hider's stealth doubling) and defence (vs Blaster's magic stacking).

4. **⚠️ Hider's Leg 1 start** is still fragile — defence = 5 with no gear, and stealth_kill only kicks in when `stealth*2 > monster_defending*1.5`. Since stealth starts at 25, threshold is met (50 > 8–26), but a fallback to regular fight still exposes Hider's raw defending of 5.

5. **Monster tuning target**: Hider stealth_atk should be the **ceiling** for what monsters can survive — if you balance around Hitter fight (47–78), Hider will trivialise every encounter via stealth kill. Consider whether the `stealth × 2` multiplier should be reduced, or whether Hider's gear should steer toward non-weapon slots to limit raw stealth growth.


---

## Non-Deterministic Combat — Material Impact Assessment

### The Change
The combat system was updated from **flat stat comparisons** to **contested d20 rolls**:

```
# New formula
p_power = player_atk + effective_def + d20
m_power = monster_fighting + monster_defending + d20
win = p_power > m_power
```

The d20 adds a random swing of 1–20 to each side, meaning the maximum it can flip an outcome is a **gap of ±19**.

---

### Finding: No Material Impact on Equipped Heroes

| Leg | Scenario | Stat Gap | Outcome |
|-----|----------|:---:|---|
| 1   | Hitter (equipped) vs any leg-1 monster | +67 | 100% — dice irrelevant |
| 2   | Hitter (equipped) vs Camp Warlord      | +53 | 100% — dice irrelevant |
| 3   | Hitter (equipped) vs Ancient Warden    | +30 | 100% — dice irrelevant |
| 4   | Hitter (equipped) vs Elder Drake       | +62 | 100% — dice irrelevant |
| 5   | Hitter (equipped) vs Death Knight      | +63 | 100% — dice irrelevant |

Once a hero has even one leg's worth of equipment, their combined `atk + def` exceeds the monster's combined `fight + def` by **30–89 points** — far outside the ±19 d20 range. **The change has zero effect on a normally-progressing hero.**

---

### Where the d20 *Does* Matter

The dice only affect outcomes when the stat gap is **< 19** — which only occurs with **completely unequipped heroes** fighting mid-to-high monsters:

| Scenario (no equipment) | Stat Gap | Old Win% | New Win% | Δ |
|---|:---:|:---:|:---:|:---:|
| Leg 1 Blaster vs Bandit   | +14 | 100% | **94.8%** | -5.2% |
| Leg 1 Hider vs Bandit     | -18 | 0%   | **0.3%**  | +0.3% |
| Leg 2 Blaster vs Mountain Ogre | -6 | 0% | **22.8%** | +22.8% |
| Leg 3+ anything           | < -19 | 0% | 0% | no change |

The biggest difference is a **naked Blaster vs Mountain Ogre** going from 0% to 23% — but this is an extreme edge case that can't occur in normal play (the hero would have found items many events before reaching Leg 2 monsters).

---

### Verdict

> **The non-deterministic change is cosmetically meaningful but structurally inert.**

- For any equipped hero it changes nothing — stat gaps are 2–5× larger than the d20 range
- It adds variance in the **amount of HP lost** on a defeat (via crit multiplier), which creates slightly more interesting moment-to-moment play
- The fundamental balance problem remains: **monsters are far too weak relative to equipped heroes**, so the outcome of most fights is predetermined regardless of the roll system

**Recommendation:** Before further tuning the randomness mechanics, address the core stat gap — monster stats need to be significantly higher, or equipment bonuses need to be lower, to make the d20 roll meaningful in normal play.


---

## Class-Restricted Gear — Impact Analysis

**Proposal:** Each class can only receive meaningful stat bonuses from gear matching their primary skills.
- **Hitter**: weapon slot → fighting only; armour slot → defending only
- **Blaster**: weapon slot → magic only; armour slot → defending only (magic still feeds eff_def)
- **Hider**: armour slot → stealth only; weapon slot → irrelevant (stealth_kill doesn't use it)

### Combat Stat Changes vs Current (Unrestricted)

All gains/losses are vs the current unrestricted model where weapon slots split 50/50 between fighting/magic and armour slots split 60/40 between defending/stealth.

| Leg | Point    | Hitter Atk Δ | Hitter Def Δ | Blaster Atk Δ | Blaster EffDef Δ | Hider StkAtk Δ | Hider Def Δ |
|-----|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1   | Start    | +0  | +0  | +0  | +0  | +0  | +0  |
| 1   | Event 10 | +11 | +13 | +11 | +18 | +38 | **-19** |
| 2   | Start    | +11 | +13 | +11 | +18 | +38 | **-19** |
| 3   | Event 10 | +20 | +20 | +20 | +30 | +59 | **-30** |
| 4   | Event 10 | +26 | +25 | +26 | +38 | +76 | **-38** |
| 5   | Start    | +26 | +25 | +26 | +38 | +76 | **-38** |

### What This Does

**✅ Good effects:**
- Strengthens class identity — each class is clearly better at their own combat style
- Hitter and Blaster both get meaningful primary stat boosts (~+11–+26 attack, +13–+38 effective defence)
- Gear drops feel purposeful — finding a Magic Wand as a Hitter is correctly flavourless

**⚠️ Problems it creates:**

1. **Hider becomes even more dominant.** Stealth_attack (already 2–3× the monster threshold) gains another +38–+76 by end-game. This pushes the Hider further out of reach of any challenge.

2. **Hider defence collapses to 5 permanently.** The armour slot currently gives the Hider some defending (~24–43 at legs 1–4). Under restriction, ALL armour bonus goes to stealth, so Hider defending stays at 5 base from Leg 1 onwards. Any fight they *fall into* (failed stealth kill) becomes lethal.

3. **Relic pool imbalance gets worse.** The Blaster already has 9 magic relics vs Hitter's 7 and Hider's 11. Applied to relics, this concentrates more power on already-stronger classes.

### Relic Pool Under Restriction

| Class  | Primary skills | Available relics | Notes |
|--------|---------------|:---:|---|
| Hitter  | fighting, defending | **7** | Smallest pool — Sword, Dragon Gauntlets, Plate, Aegis, Behemoth Shield + 2 neutral |
| Blaster | magic | **11** | 9 magic relics + 2 neutral — large, powerful pool |
| Hider   | stealth, salvaging, spotting | **11** | Broad pool but includes utility relics (not all combat) |

### Verdict

> **Class-restricted gear is a sound identity mechanic but will worsen the existing balance problem without also increasing monster stats.**

The right order of operations is:
1. **First** raise monster stats to close the stat gap (see above findings)
2. **Then** apply class restriction to sharpen identity once the baseline is set
3. Consider giving **Hider a separate defence relic/slot** so their armour-for-stealth trade-off doesn't leave them one-shot vulnerable

