# UI Frame and Porting Guide

Hero Adventure screens use a shared semantic frame contract. The contract describes
what belongs together; each platform decides how those regions look and how much space
they receive.

## Four frames

Every screen declares these four frame IDs, even when one has no controls:

| Frame | Default share | Priority | Responsibility |
| --- | ---: | --- | --- |
| `status` | 15% | P0 | Persistent orientation: identity, health, money, capacity, and progress |
| `scene` | 50% | P0 | The current situation: narration, encounter, result, loot, or decision |
| `context` | 20% | P1 | One supporting detail mode: odds, inventory, trader, dungeon, scores, or messages |
| `actions` | 15% | P0 | Legal choices, grouped as primary, utility, and navigation |

These are content-importance weights, not terminal columns or GUI coordinates. The
default physical shell is:

```text
STATUS: full width, 15% height
SCENE:  71% of the middle width | CONTEXT: 29% of the middle width, 70% height
ACTIONS: full width, 15% height
```

The middle split is the original `scene:context` weight of `50:20`, normalized to
approximately `71:29`. The four frames must be visibly bounded and labelled; assigning
`frame` metadata while rendering one vertical document does not satisfy the contract.
When space is limited, retain `actions`, `scene`, and `status` first. Collapse or reflow
`context` first without mixing it into `status`.

The four questions are:

- `status`: How am I doing?
- `scene`: What is happening?
- `context`: What supporting detail do I need?
- `actions`: What can I do?

Do not put a choice in `scene`, a long log in `status`, or all available detail in
`context`. Each frame should have one job.

## Usage audit and retention decisions

The current 28 screens contain 279 controls:

| Area | Usage | What it contains | Decision |
| --- | ---: | --- | --- |
| `status` | 20 screens / 80 controls | The same identity text and HP, carry, and journey bars | Keep as a fixed HUD strip; split identity and bars inside the strip rather than adding a fifth frame. |
| `scene` | 28 screens / 109 controls | Titles, narration, event outcomes, result history, loot, rules, and the one character-name input | Keep as the dominant reading area; compact routine lines and allow bounded scrolling for rules and outcome lists. |
| `context` | 11 screens / 28 controls | Event-related stats, forecasts, inventory, character detail, dungeon facts, and trader data | Keep as an optional detail pane; hide it when empty and use dense two-column rows when it is information-heavy. |
| `actions` | 28 screens / 62 controls | Available buttons only | Keep as a fixed horizontal footer; use wider columns before adding another row. |

`status` is the only high-frequency area with genuinely fixed information. It does not
justify a new permanent frame because its four controls are already a compact,
repeated HUD. `context` is the area most likely to become unreadable: it is uncommon
but dense, so its width expands from the normal 29% middle split to 35% when a screen
contains multiple lists or four or more supporting controls. An empty context pane is
collapsed so it cannot steal reading space from `scene`.

## JSON screen shape

The old top-level `text`, `lists`, and `buttons` arrays are not part of the new format.
Each screen has `frames` and one ordered `controls` collection:

```json
{
  "id": "journey",
  "title": "Leg {leg}/5: {leg_name}",
  "frames": [
    {"id": "status", "role": "status", "ratio": 0.15, "priority": "P0"},
    {"id": "scene", "role": "scene", "ratio": 0.50, "priority": "P0"},
    {"id": "context", "role": "context", "ratio": 0.20, "priority": "P1"},
    {"id": "actions", "role": "actions", "ratio": 0.15, "priority": "P0"}
  ],
  "controls": [
    {
      "type": "progressbar",
      "id": "hp_bar",
      "frame": "status",
      "label": "HP",
      "value": "{hp}",
      "max": "{max_hp}",
      "kind": "health",
      "thresholds": {"warning": 0.35, "critical": 0.15},
      "show_text": true
    },
    {
      "type": "text",
      "frame": "scene",
      "value": "{event_narration}"
    },
    {
      "type": "button",
      "frame": "actions",
      "label": "Continue",
      "action": "advance_event"
    }
  ]
}
```

`frame` is required on every control. The order of controls is the order within its
frame. The frame declaration is the contract; the renderer owns the geometry.

Controls may also declare `compact: true` when a renderer can safely place several
small controls on one line. The terminal uses this for the persistent status bars and
combat odds; a GUI may ignore the hint and give each control its own row.

## Control types

### `text`

Displays a formatted value in its frame.

```json
{"type": "text", "frame": "scene", "value": "You found a dungeon."}
```

Use `variant: "title"` only for the screen heading. Keep headings in `scene` so menu
and event screens have the same title treatment.

### `input`

Provides editable input. The GUI currently reserves `id: "name_input"` for character
creation and binds it to the controller's pending hero name.

```json
{
  "type": "input",
  "id": "name_input",
  "frame": "scene",
  "label": "Hero Name:",
  "value": "{pending_name}",
  "placeholder": "Enter hero name"
}
```

### `list`

Renders rows from a controller context list. Lists that communicate the outcome of
the current event belong in `scene` (for example loot or combat round history).
Reference, inventory, and selectable data belong in `context`. Use `max_rows` for a
first-page budget and `overflow: "page"` when the platform supports a detail or
paging interaction.

```json
{
  "type": "list",
  "id": "list_inventory",
  "frame": "context",
  "label": "Inventory",
  "max_rows": 12,
  "overflow": "page"
}
```

Rows may contain `text`, `action`, and `enabled`. A row with an action is interactive;
a disabled row is informational.

### `button`

Represents an available action and belongs in `actions`.

```json
{
  "type": "button",
  "frame": "actions",
  "label": "Fight ({fight_win_pct}%)",
  "action": "fight",
  "visible_if": "allow_run"
}
```

Renderers should preserve the JSON order and separate primary choices from utility
and navigation choices when their platform supports grouping. Do not create a button
for an unavailable action.

### `progressbar`

A progressbar communicates an amount relative to a known maximum. It is not a
scrollbar and must never be used to represent document overflow.

Required fields are `id`, `frame`, `label`, `value`, `max`, and `kind`. `value` and
`max` may be formatted controller bindings or numeric literals. Keep the numeric
text visible even when the platform also shows a visual bar.

Supported kinds currently used by the GUI are:

- `health`: lower values become warning/critical.
- `capacity`: higher values become warning/critical and values above max remain
  visibly full with a warning color.
- `journey`, `dungeon`, `levelup`, and `honor`: neutral progression.
- `odds`: comparative action likelihood in combat context.

Renderers clamp only the visual fill to 0-1; they must not alter the displayed values.
Reject a zero or negative maximum as invalid screen data.

### Combat round history

The `combat_result` screen keeps the resolved fight and `list_rounds` in `scene`.
Each row includes a round number,
an outcome (`HIT`, `LOSS`, or `ATTRITION`), the existing flavour text, and available damage and
remaining-HP facts, for example:

```text
R1 HIT: The hero struck first. (dealt 12; hero HP 95; enemy HP 18)
```

Round history is shown after the fight resolves; it does not pause synchronous
combat between rounds. Rows are informational, never action buttons, and may scroll
inside `scene` when a fight produces more rows than fit. The final result remains
next to the history in `scene` and `Continue` remains in `actions`.

## GUI implementation notes

`play_gui.py` creates a three-row shell: a 15% status header, a 70% middle row with
scene/context placed at the normalized 71:29 split (65:35 for dense context), and a
15% actions footer. The status header uses approximately 25% identity, 45% resource
bars, and 30% journey/dungeon progress. The actions footer uses horizontal columns
rather than a vertical button stack. Context is omitted from the physical shell when
a screen has no context controls, allowing the scene to use the full middle width.

`play.py` uses the same shell at normal width. At 120 columns, scene and context are
side-by-side, dense context expands to 35% of the middle row, and actions use four
compact columns. Below 100 columns, the middle row reflows to scene above context
while preserving their borders and labels. An empty context frame collapses. Scene and
context are bounded scrollable regions; status and actions are fixed and must not
overflow their frame.

The status frame should contain only compact orientation: one identity line plus HP,
carry, and journey/dungeon bars. Do not place narration, event outcomes, combat odds,
inventory rows, full skills, or action controls in status. Scene is the event feed:
put narration, results, loot, round history, and other consequences there. Context is
mode-specific supporting data: combat shows odds and enemy facts, inventory shows
capacity and item rows, dungeon shows depth, and capital shows affordability or score.
In dense context, compact progressbars are rendered as two columns so each label, fill,
and numeric amount remains readable.

When a control does not fit:

1. Preserve P0 frames and their primary controls.
2. Collapse or page the P1 context.
3. Shorten or wrap content inside its frame.
4. Add a detail action rather than expanding the whole screen.

Do not solve overflow by adding another permanent frame or by moving controls into
an unrelated frame.

## Porting checklist

1. Load each screen and validate all four frame IDs, ratios, priorities, and control
   frame references.
2. Allocate platform space using the ratios as defaults, then define responsive
   reflow for narrow and wide displays.
3. Render controls by type; keep action dispatch and controller bindings unchanged.
4. Give `scene` and `context` bounded overflow behavior appropriate to the platform.
5. Preserve progressbar labels, numeric values, maxima, kinds, and threshold meaning.
6. Keep actions keyboard-addressable in terminal ports and clickable in GUI ports.
7. Test the longest narration, combat context, inventory, trader lists, level-up,
   and capital screens at 80x24 and 120x40 or the platform's equivalent normal sizes.
8. Record platform-specific geometry in the renderer or platform guide, not in the
   shared JSON.
