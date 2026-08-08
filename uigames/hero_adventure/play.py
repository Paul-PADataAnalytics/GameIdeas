#!/usr/bin/env python3
"""Textual terminal renderer for the four-frame declarative UI."""

from __future__ import annotations

import json
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual import events
from textual.widgets import Button, Footer, Header, Input, Label, Static

from hero_engine import GameController


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class HeroAdventureTUI(App):
    TITLE = "Hero Adventure"
    FRAME_ORDER = ("status", "scene", "context", "actions")
    FRAME_WEIGHTS = {
        "status": 15,
        "scene": 50,
        "context": 20,
        "actions": 15,
    }
    BAR_COLORS = {
        "health": "green",
        "capacity": "yellow",
        "journey": "cyan",
        "dungeon": "magenta",
        "levelup": "yellow",
        "honor": "dark_orange",
        "odds": "green",
    }
    CSS = """
    Screen {
        layout: vertical;
    }

    Header {
        height: 1;
    }

    Footer {
        height: 1;
    }

    #layout {
        height: 1fr;
        width: 1fr;
    }

    #middle {
        height: 70%;
        width: 1fr;
        layout: horizontal;
    }

    .frame {
        padding: 0 1;
        border: round $accent;
    }

    #frame_status {
        width: 1fr;
        height: 15%;
    }

    #frame_scene {
        width: 71%;
        height: 1fr;
    }

    #frame_context {
        width: 29%;
        height: 1fr;
    }

    #frame_actions {
        width: 1fr;
        height: 15%;
    }

    .frame_content {
        width: 1fr;
        height: 1fr;
    }

    #scene_content,
    #context_content {
        overflow-y: auto;
    }

    #actions_content {
        overflow: hidden;
    }

    .line {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }

    .progress_line {
        width: 1fr;
        height: 1;
        padding: 0 1;
    }

    .compact_row {
        width: 1fr;
        height: 1;
    }

    .compact_progress {
        width: 1fr;
    }

    #status_content {
        layout: horizontal;
    }

    .status_identity {
        width: 25%;
        height: 1fr;
    }

    .status_identity_line {
        width: 1fr;
        height: 1;
        overflow-x: hidden;
        padding: 0 1;
    }

    .status_bars {
        width: 75%;
        height: 1fr;
        layout: horizontal;
    }

    .status_bar {
        width: 1fr;
        height: 1fr;
    }

    .list_label {
        width: 1fr;
        height: 1;
        text-style: bold;
        padding: 0 1;
    }

    .disabled_line {
        width: 1fr;
        height: auto;
        color: $text-muted;
        padding: 0 1;
    }

    .combat_round {
        border-bottom: solid $panel;
        padding: 0 1;
    }

    .combat_round_hit {
        color: $success;
    }

    .combat_round_loss {
        color: $warning;
    }

    .combat_round_attrition {
        color: $error;
    }

    .input_row {
        width: 1fr;
        height: 3;
    }

    .input_label {
        width: 12;
        padding: 1 0;
    }

    .action_row {
        width: 1fr;
        height: 2;
    }

    .action_button {
        width: 1fr;
        height: 2;
        margin: 0 1;
        padding: 0 1;
        border: none;
    }

    .narrow_action {
        height: 1;
        border: none;
        padding: 0;
    }

    """

    def __init__(self):
        super().__init__()
        self.controller = GameController()
        self.screens = self._load_screens()
        self.ctx = {}
        self._button_actions = {}
        self._button_seq = 0
        self._context_visible = False
        self._context_dense = False
        self._action_rows = 1

    def _load_screens(self):
        ui_dir = Path(__file__).resolve().parent / "ui"
        screens = {}
        for path in ui_dir.glob("*.json"):
            data = json.loads(path.read_text())
            screens[data["id"]] = data
        return screens

    def _fmt(self, value):
        return str(value).format_map(SafeDict(self.ctx))

    def _resolve_number(self, value, control_id, field):
        rendered = self._fmt(value)
        try:
            return float(rendered)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid progressbar {field} for {control_id}: {rendered!r}"
            ) from exc

    def _frame_definitions(self, screen):
        if len(screen["frames"]) != len(self.FRAME_ORDER):
            raise ValueError(f"Screen {screen['id']} must declare exactly four frames")
        definitions = {frame["id"]: frame for frame in screen["frames"]}
        if set(definitions) != set(self.FRAME_ORDER):
            raise ValueError(f"Screen {screen['id']} has invalid frame IDs")
        ratio_total = sum(float(definitions[frame_id]["ratio"]) for frame_id in self.FRAME_ORDER)
        if abs(ratio_total - 1.0) > 0.001:
            raise ValueError(f"Screen {screen['id']} frame ratios must total 1.0")
        for frame_id in self.FRAME_ORDER:
            frame = definitions[frame_id]
            expected_ratio = self.FRAME_WEIGHTS[frame_id] / 100
            if frame.get("role") != frame_id or abs(float(frame["ratio"]) - expected_ratio) > 0.001:
                raise ValueError(f"Screen {screen['id']} has invalid {frame_id} frame metadata")
        return definitions

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="layout"):
            with Horizontal(id="frame_status", classes="frame"):
                yield Horizontal(id="status_content", classes="frame_content")
            with Horizontal(id="middle"):
                with Vertical(id="frame_scene", classes="frame"):
                    yield VerticalScroll(id="scene_content", classes="frame_content")
                with Vertical(id="frame_context", classes="frame"):
                    yield VerticalScroll(id="context_content", classes="frame_content")
            with Vertical(id="frame_actions", classes="frame"):
                yield Vertical(id="actions_content", classes="frame_content")
        yield Footer()

    async def on_mount(self):
        for frame_id in self.FRAME_ORDER:
            self.query_one(f"#frame_{frame_id}").border_title = frame_id.upper()
        await self.refresh_screen()

    def on_resize(self, event: events.Resize):
        self._apply_action_geometry(event.size.width)
        self._apply_middle_geometry(event.size.width)

    def _action_columns(self, width=None):
        width = self.size.width if width is None else width
        return 4 if width >= 100 else 3 if width >= 80 else 2

    def _apply_action_geometry(self, width=None):
        width = self.size.width if width is None else width
        action_percent = (
            15
            if width >= 100 or self._action_rows <= 2
            else min(30, 15 + (self._action_rows - 2) * 5)
        )
        self.query_one("#frame_actions").styles.height = f"{action_percent}%"
        self.query_one("#middle").styles.height = f"{100 - 15 - action_percent}%"

    def _apply_middle_geometry(self, width):
        middle = self.query_one("#middle", Horizontal)
        scene = self.query_one("#frame_scene")
        context = self.query_one("#frame_context")
        if width < 100:
            middle.styles.layout = "vertical"
            scene.styles.width = "1fr"
            scene.styles.height = "70%" if self._context_visible else "1fr"
            context.styles.width = "1fr"
            context.styles.height = "30%" if self._context_visible else "0"
        else:
            middle.styles.layout = "horizontal"
            scene.styles.width = (
                "65%" if self._context_dense else "71%"
            ) if self._context_visible else "1fr"
            scene.styles.height = "1fr"
            context.styles.width = (
                "35%" if self._context_dense else "29%"
            ) if self._context_visible else "0"
            context.styles.height = "1fr"

    def _button_id(self, action):
        button_id = f"act_{self._button_seq}"
        self._button_seq += 1
        self._button_actions[button_id] = action
        return button_id

    def _progressbar_text(self, control, compact=False, dense=False):
        control_id = control["id"]
        value = self._resolve_number(control["value"], control_id, "value")
        maximum = self._resolve_number(control["max"], control_id, "max")
        if maximum <= 0:
            raise ValueError(f"Progressbar {control_id} must have a positive max")

        ratio = value / maximum
        display_ratio = min(1.0, max(0.0, ratio))
        kind = control.get("kind", "journey")
        color = self.BAR_COLORS.get(kind, "cyan")
        thresholds = control.get("thresholds", {})
        if kind == "health":
            if ratio <= thresholds.get("critical", 0.15):
                color = "red"
            elif ratio <= thresholds.get("warning", 0.35):
                color = "yellow"
        elif kind == "capacity":
            if ratio >= thresholds.get("critical", 1.0):
                color = "red"
            elif ratio >= thresholds.get("warning", 0.8):
                color = "yellow"

        if dense:
            width = 4
        elif compact:
            width = 5 if self.size.width < 100 else 8
        else:
            width = max(12, min(28, (self.size.width - 34) // 2))
        filled = round(display_ratio * width)
        bar = "#" * filled + "-" * (width - filled)
        label = self._fmt(control.get("label", control_id))
        if dense:
            label = {
                "health": "HP",
                "capacity": "Carry",
                "journey": "Prog",
                "dungeon": "Dng",
                "levelup": "Lvl",
                "honor": "Hon",
                "stealth_kill": "Kill",
            }.get(kind, label)[:4]
        elif compact:
            label = {
                "health": "HP",
                "capacity": "Carry",
                "journey": "Prog",
                "dungeon": "Dng",
                "levelup": "Lvl",
                "honor": "Honor",
            }.get(kind, label)[:5]
        text = Text()
        text.append(
            f"{label:<4} "
            if dense
            else f"{label:<5} "
            if compact
            else f"{label:<12} "
        )
        text.append(f"[{bar}]", style=color)
        if control.get("show_text", True):
            if dense and kind == "odds" and maximum == 100:
                text.append(f" {value:g}%")
            else:
                text.append(f" {value:g}/{maximum:g}")
        return text

    async def _mount_text(self, parent, control, title=False):
        value = self._fmt(control.get("value", ""))
        if not value and not control.get("show_empty", False):
            return
        if title:
            value = Text(value, style="bold cyan")
        classes = (
            "status_identity_line"
            if "status_identity" in parent.classes
            else "line"
        )
        await parent.mount(Static(value, classes=classes))

    async def _mount_input(self, parent, control):
        row = Horizontal(classes="input_row")
        await parent.mount(row)
        await row.mount(Label(self._fmt(control.get("label", "")), classes="input_label"))
        name_input = Input(
            placeholder=control.get("placeholder", ""),
            id=control.get("id"),
        )
        name_input.value = self.controller.pending_name
        await row.mount(name_input)

    async def _mount_list(self, parent, control):
        list_id = control["id"]
        label = control.get("label")
        rows = self.ctx.get(list_id, [])
        if label:
            await parent.mount(Static(self._fmt(label), classes="list_label"))

        max_rows = control.get("max_rows")
        visible_rows = rows[:max_rows] if max_rows else rows
        for row in visible_rows:
            text = self._fmt(row.get("text", ""))
            action = row.get("action")
            enabled = row.get("enabled", True)
            if action and enabled:
                button_id = self._button_id(action)
                await parent.mount(Button(text, classes="action_button", id=button_id))
            else:
                classes = "disabled_line"
                if row.get("outcome"):
                    classes = f"combat_round combat_round_{row['outcome']}"
                await parent.mount(Static(f"- {text}", classes=classes))

        if max_rows and len(rows) > max_rows:
            await parent.mount(Static(
                f"Showing {max_rows} of {len(rows)} entries; scroll for more.",
                classes="disabled_line",
            ))

    async def _mount_button(self, parent, control):
        visible_if = control.get("visible_if")
        if visible_if and not self.ctx.get(visible_if):
            return None
        label = self._fmt(control.get("label", ""))
        action = control.get("action")
        if not action:
            return Static(f"- {label}", classes="disabled_line")
        button_id = self._button_id(action)
        return Button(label, classes="action_button", id=button_id)

    async def _mount_regular_control(self, parent, control):
        control_type = control["type"]
        if control_type == "text":
            await self._mount_text(parent, control, title=control.get("variant") == "title")
        elif control_type == "input":
            await self._mount_input(parent, control)
        elif control_type == "progressbar":
            await parent.mount(Static(
                self._progressbar_text(control),
                classes="progress_line",
            ))
        elif control_type == "list":
            await self._mount_list(parent, control)
        else:
            raise ValueError(f"Unsupported control type {control_type!r}")

    async def _mount_frame_controls(self, frame_id, parent, controls):
        if frame_id == "status":
            identity = Vertical(classes="status_identity")
            bars = Horizontal(classes="status_bars")
            await parent.mount(identity)
            await parent.mount(bars)
            for control in controls:
                target = bars if control["type"] == "progressbar" else identity
                if control["type"] == "progressbar":
                    await target.mount(Static(
                        self._progressbar_text(control, compact=True),
                        classes="compact_progress status_bar",
                    ))
                else:
                    await self._mount_regular_control(target, control)
            return

        if frame_id == "actions":
            buttons = []
            for control in controls:
                if control["type"] != "button":
                    await self._mount_regular_control(parent, control)
                    continue
                button = await self._mount_button(parent, control)
                if button is not None:
                    if self.size.width < 100:
                        button.add_class("narrow_action")
                    buttons.append(button)
            columns = self._action_columns()
            for offset in range(0, len(buttons), columns):
                row = Horizontal(classes="action_row")
                if self.size.width < 100:
                    row.add_class("narrow_action")
                await parent.mount(row)
                for button in buttons[offset:offset + columns]:
                    await row.mount(button)
            return

        if frame_id == "context":
            index = 0
            while index < len(controls):
                control = controls[index]
                if control["type"] == "progressbar" and control.get("compact"):
                    compact = []
                    while index < len(controls):
                        candidate = controls[index]
                        if candidate["type"] != "progressbar" or not candidate.get("compact"):
                            break
                        compact.append(candidate)
                        index += 1
                    for offset in range(0, len(compact), 2):
                        row = Horizontal(classes="compact_row")
                        await parent.mount(row)
                        for candidate in compact[offset:offset + 2]:
                            await row.mount(Static(
                                self._progressbar_text(
                                    candidate,
                                    compact=True,
                                    dense=True,
                                ),
                                classes="compact_progress",
                            ))
                    continue
                await self._mount_regular_control(parent, control)
                index += 1
            return

        index = 0
        while index < len(controls):
            control = controls[index]
            if control["type"] == "progressbar" and control.get("compact"):
                compact = []
                while index < len(controls):
                    candidate = controls[index]
                    if candidate["type"] != "progressbar" or not candidate.get("compact"):
                        break
                    compact.append(candidate)
                    index += 1
                row = Horizontal(classes="compact_row")
                await parent.mount(row)
                for candidate in compact:
                    await row.mount(Static(
                        self._progressbar_text(candidate, compact=True),
                        classes="compact_progress",
                    ))
                continue
            await self._mount_regular_control(parent, control)
            index += 1

    async def refresh_screen(self):
        if self.controller.quit_requested:
            self.exit()
            return

        screen_id = self.controller.screen
        screen = self.screens.get(screen_id)
        if not screen:
            self.controller.screen = "front_page"
            screen = self.screens["front_page"]
            screen_id = "front_page"

        self._frame_definitions(screen)
        self.ctx = self.controller.get_context()
        self._button_actions = {}
        self._button_seq = 0

        controls_by_frame = {frame_id: [] for frame_id in self.FRAME_ORDER}
        for control in screen["controls"]:
            frame_id = control["frame"]
            if frame_id not in controls_by_frame:
                raise ValueError(f"Control uses unknown frame {frame_id!r}")
            controls_by_frame[frame_id].append(control)

        context_controls = controls_by_frame["context"]
        self._context_visible = bool(context_controls)
        self._context_dense = (
            len(context_controls) >= 4
            or sum(control["type"] == "list" for control in context_controls) >= 2
            or sum(control["type"] == "progressbar" for control in context_controls) >= 4
        )
        visible_actions = []
        for control in controls_by_frame["actions"]:
            if control["type"] != "button":
                continue
            visible_if = control.get("visible_if")
            if visible_if and not self.ctx.get(visible_if):
                continue
            visible_actions.append(control)
        columns = self._action_columns()
        self._action_rows = max(1, (len(visible_actions) + columns - 1) // columns)
        self._apply_action_geometry(self.size.width)
        self.query_one("#frame_context").display = self._context_visible
        self._apply_middle_geometry(self.size.width)

        for frame_id in self.FRAME_ORDER:
            frame = self.query_one(f"#frame_{frame_id}")
            frame.display = frame_id != "context" or self._context_visible
            content = self.query_one(
                f"#{frame_id}_content",
                (Horizontal, Vertical, VerticalScroll),
            )
            await content.remove_children()
            await self._mount_frame_controls(
                frame_id,
                content,
                controls_by_frame[frame_id],
            )

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "name_input":
            self.controller.set_pending_name(event.value.strip())
            await self.refresh_screen()

    async def on_button_pressed(self, event: Button.Pressed):
        action = self._button_actions.get(event.button.id or "")
        if not action:
            return
        if self.controller.screen == "character_creation":
            name = self.query_one("#name_input", Input).value.strip()
            self.controller.set_pending_name(name)
        self.controller.dispatch(action)
        await self.refresh_screen()


def main():
    HeroAdventureTUI().run()


if __name__ == "__main__":
    main()
