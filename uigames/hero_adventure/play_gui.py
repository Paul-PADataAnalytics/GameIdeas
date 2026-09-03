#!/usr/bin/env python3
"""CustomTkinter renderer for the four-frame declarative UI."""

from __future__ import annotations

import json
from pathlib import Path

import customtkinter as ctk

from hero_engine import GameController


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class DeclarativeGUI:
    FRAME_ORDER = ("status", "scene", "context", "actions")
    FRAME_WEIGHTS = {
        "status": 15,
        "scene": 50,
        "context": 20,
        "actions": 15,
    }
    ACTION_COLUMNS = 5
    FRAME_COLORS = {
        "status": "#3f6f9f",
        "scene": "#4f8a5b",
        "context": "#8a6a3f",
        "actions": "#8a4f4f",
    }
    BAR_COLORS = {
        "health": "#35c759",
        "capacity": "#f0ad4e",
        "backpack": "#f0ad4e",
        "journey": "#4ea1ff",
        "dungeon": "#b07cff",
        "levelup": "#ffd166",
        "honor": "#ff9f43",
        "odds": "#69d2a0",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Hero Adventure")
        self.root.geometry("980x760")
        self.controller = GameController()
        self.screens = self._load_screens()
        self.name_var = ctk.StringVar(value="")
        self.frame = None
        self._action_index = 0
        self._status_identity = None
        self._status_bars = None
        self._scene_frame = None
        self._context_frame = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.render()

    def _load_screens(self):
        ui_dir = Path(__file__).resolve().parent / "ui"
        screens = {}
        for path in ui_dir.glob("*.json"):
            data = json.loads(path.read_text())
            screens[data["id"]] = data
        return screens

    def _fmt(self, value, ctx):
        return str(value).format_map(SafeDict(ctx))

    def _resolve_number(self, value, ctx, control_id, field):
        rendered = self._fmt(value, ctx)
        try:
            return float(rendered)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid progressbar {field} for {control_id}: {rendered!r}"
            ) from exc

    def _dispatch(self, action):
        if not action:
            return
        if self.controller.screen == "character_creation":
            self.controller.set_pending_name(self.name_var.get().strip())
        self.controller.dispatch(action)
        if self.controller.quit_requested:
            self.root.destroy()
            return
        self.render()

    def _frame_definitions(self, screen):
        if len(screen["frames"]) != len(self.FRAME_ORDER):
            raise ValueError(f"Screen {screen['id']} must declare exactly four frames")
        definitions = {frame["id"]: frame for frame in screen["frames"]}
        missing = set(self.FRAME_ORDER) - definitions.keys()
        if missing:
            raise ValueError(f"Screen {screen['id']} is missing frames: {sorted(missing)}")
        ratio_total = sum(float(definitions[frame_id]["ratio"]) for frame_id in self.FRAME_ORDER)
        if abs(ratio_total - 1.0) > 0.001:
            raise ValueError(f"Screen {screen['id']} frame ratios must total 1.0")
        for frame_id in self.FRAME_ORDER:
            frame = definitions[frame_id]
            expected_ratio = self.FRAME_WEIGHTS[frame_id] / 100
            if frame.get("role") != frame_id or abs(float(frame["ratio"]) - expected_ratio) > 0.001:
                raise ValueError(f"Screen {screen['id']} has invalid {frame_id} frame metadata")
        return definitions

    def _frame_containers(self, screen):
        self.frame = ctk.CTkFrame(self.root)
        self.frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.frame.grid_columnconfigure(0, weight=1)

        definitions = self._frame_definitions(screen)
        controls_by_frame = {frame_id: [] for frame_id in self.FRAME_ORDER}
        for control in screen["controls"]:
            frame_id = control["frame"]
            if frame_id not in controls_by_frame:
                raise ValueError(
                    f"Control {control.get('id', control.get('type'))} uses unknown frame "
                    f"{frame_id!r}"
                )
            controls_by_frame[frame_id].append(control)

        self.frame.grid_rowconfigure(0, weight=15)
        self.frame.grid_rowconfigure(1, weight=70)
        self.frame.grid_rowconfigure(2, weight=15)

        middle = ctk.CTkFrame(self.frame, fg_color="transparent")
        middle.grid(row=1, column=0, sticky="nsew", padx=4, pady=3)

        containers = {}
        context_controls = controls_by_frame["context"]
        context_visible = bool(context_controls)
        context_dense = (
            len(context_controls) >= 4
            or sum(control["type"] == "list" for control in context_controls) >= 2
            or sum(control["type"] == "progressbar" for control in context_controls) >= 4
        )
        for frame_id, parent, row, column in (
            ("status", self.frame, 0, 0),
            ("scene", middle, 0, 0),
            ("context", middle, 0, 1),
            ("actions", self.frame, 2, 0),
        ):
            frame = ctk.CTkFrame(
                parent,
                border_width=2,
                border_color=self.FRAME_COLORS[frame_id],
            )
            if frame_id == "scene":
                self._scene_frame = frame
            elif frame_id == "context":
                self._context_frame = frame
            else:
                frame.grid(row=row, column=column, sticky="nsew", padx=4, pady=3)
            frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                frame,
                text=frame_id.upper(),
                text_color=self.FRAME_COLORS[frame_id],
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(3, 0))

            if frame_id in ("scene", "context"):
                content = ctk.CTkScrollableFrame(frame, fg_color="transparent")
                content.pack(fill="both", expand=True, padx=6, pady=4)
            elif frame_id == "actions":
                content = ctk.CTkFrame(frame, fg_color="transparent")
                content.pack(fill="both", expand=True, padx=6, pady=4)
                for column_index in range(self.ACTION_COLUMNS):
                    content.grid_columnconfigure(column_index, weight=1)
            else:
                content = ctk.CTkFrame(frame, fg_color="transparent")
                content.pack(fill="both", expand=True, padx=6, pady=4)
                content.grid_columnconfigure(0, weight=25)
                content.grid_columnconfigure(1, weight=75)
                self._status_identity = ctk.CTkFrame(content, fg_color="transparent")
                self._status_identity.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
                self._status_bars = ctk.CTkFrame(content, fg_color="transparent")
                self._status_bars.grid(row=0, column=1, sticky="nsew")
                for bar_column in range(3):
                    self._status_bars.grid_columnconfigure(bar_column, weight=1)
            containers[frame_id] = content

        self._set_middle_geometry(context_visible, context_dense)
        self._action_index = 0
        return containers, controls_by_frame, definitions

    def _set_middle_geometry(self, context_visible, context_dense):
        if context_visible:
            scene_width = 0.65 if context_dense else 0.7143
            context_width = 1 - scene_width
            self._scene_frame.place(
                relx=0,
                rely=0,
                relwidth=scene_width,
                relheight=1,
            )
            self._context_frame.place(
                relx=scene_width,
                rely=0,
                relwidth=context_width,
                relheight=1,
            )
        else:
            self._context_frame.place_forget()
            self._scene_frame.place(
                relx=0,
                rely=0,
                relwidth=1,
                relheight=1,
            )

    def _add_text(self, parent, control, ctx, title=False):
        text = self._fmt(control.get("value", ""), ctx)
        if not text and not control.get("show_empty", False):
            return
        font = ctk.CTkFont(size=24 if title else 14, weight="bold" if title else "normal")
        ctk.CTkLabel(
            parent,
            text=text,
            font=font,
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", pady=(4, 8) if title else (2, 4))

    def _add_input(self, parent, control, ctx):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        label = control.get("label")
        if label:
            ctk.CTkLabel(row, text=self._fmt(label, ctx), width=90).pack(side="left")
        if control.get("id") == "name_input":
            self.name_var.set(self.controller.pending_name)
            ctk.CTkEntry(
                row,
                textvariable=self.name_var,
                placeholder_text=control.get("placeholder", ""),
            ).pack(side="left", fill="x", expand=True)
        else:
            entry = ctk.CTkEntry(
                row,
                placeholder_text=control.get("placeholder", ""),
            )
            entry.insert(0, self._fmt(control.get("value", ""), ctx))
            entry.pack(side="left", fill="x", expand=True)

    def _add_progressbar(self, parent, control, ctx, compact=False):
        control_id = control["id"]
        value = self._resolve_number(control["value"], ctx, control_id, "value")
        maximum = self._resolve_number(control["max"], ctx, control_id, "max")
        if maximum <= 0:
            raise ValueError(f"Progressbar {control_id} must have a positive max")

        ratio = value / maximum
        display_ratio = min(1.0, max(0.0, ratio))
        kind = control.get("kind", "neutral")
        color = self.BAR_COLORS.get(kind, "#4ea1ff")
        thresholds = control.get("thresholds", {})
        if kind == "health":
            if ratio <= thresholds.get("critical", 0.15):
                color = "#ff4d4d"
            elif ratio <= thresholds.get("warning", 0.35):
                color = "#f0ad4e"
        elif kind == "capacity":
            if ratio >= thresholds.get("critical", 1.0):
                color = "#ff4d4d"
            elif ratio >= thresholds.get("warning", 0.8):
                color = "#f0ad4e"
        elif kind == "backpack":
            if ratio >= thresholds.get("critical", 1.0):
                color = "#ff4d4d"
            elif ratio >= thresholds.get("warning", 0.8):
                color = "#f0ad4e"

        label = self._fmt(control.get("label", control_id), ctx)
        text = f"{label}: {value:g}/{maximum:g}" if control.get("show_text", True) else label
        if compact:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            if parent is self._status_bars:
                row.grid(row=0, column=self._status_bar_index, sticky="nsew", padx=3)
                self._status_bar_index += 1
            else:
                row.pack(side="left", fill="both", expand=True, padx=3)
            ctk.CTkLabel(row, text=text, anchor="w").pack(fill="x")
            bar = ctk.CTkProgressBar(row, progress_color=color, height=10)
            bar.set(display_ratio)
            bar.pack(fill="x", pady=(4, 0))
            return

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=text, width=150, anchor="w").pack(side="left")
        bar = ctk.CTkProgressBar(row, progress_color=color)
        bar.set(display_ratio)
        bar.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _add_list(self, parent, control, ctx):
        list_id = control["id"]
        label = control.get("label")
        rows = ctx.get(list_id, [])
        if label:
            ctk.CTkLabel(
                parent,
                text=self._fmt(label, ctx),
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w",
            ).pack(anchor="w", pady=(6, 4))

        max_rows = control.get("max_rows")
        visible_rows = rows[:max_rows] if max_rows else rows
        for row in visible_rows:
            text = self._fmt(row.get("text", ""), ctx)
            action = row.get("action")
            enabled = row.get("enabled", True)
            if action and enabled:
                highlight = row.get("highlight")
                text_color = {
                    "better": "#9be59b",
                    "worse": "#e08283",
                }.get(highlight)
                kwargs = {"text_color": text_color} if text_color else {}
                ctk.CTkButton(
                    parent,
                    text=text,
                    command=lambda a=action: self._dispatch(a),
                    anchor="w",
                    height=32,
                    **kwargs,
                ).pack(fill="x", pady=2)
            else:
                outcome = row.get("outcome")
                if outcome:
                    row_frame = ctk.CTkFrame(
                        parent,
                        fg_color="#1d2a1f" if outcome == "hit" else "#2a241d",
                        corner_radius=4,
                    )
                    row_frame.pack(fill="x", pady=2)
                    ctk.CTkLabel(
                        row_frame,
                        text=text,
                        anchor="w",
                        justify="left",
                        wraplength=900,
                        text_color="#9be59b" if outcome == "hit" else "#f0c674",
                    ).pack(fill="x", padx=8, pady=4)
                else:
                    ctk.CTkLabel(
                        parent,
                        text=text,
                        anchor="w",
                        justify="left",
                        wraplength=900,
                    ).pack(fill="x", pady=2)

        if max_rows and len(rows) > max_rows:
            ctk.CTkLabel(
                parent,
                text=f"Showing {max_rows} of {len(rows)} entries; open detail to continue.",
                text_color="#aaaaaa",
                anchor="w",
            ).pack(fill="x", pady=4)

    def _add_button(self, parent, control, ctx):
        visible_if = control.get("visible_if")
        if visible_if and not ctx.get(visible_if):
            return
        label = self._fmt(control.get("label", ""), ctx)
        action = control.get("action")
        ctk.CTkButton(
            parent,
            text=label,
            command=(lambda a=action: self._dispatch(a)) if action else None,
            height=30,
        ).grid(
            row=self._action_index // self.ACTION_COLUMNS,
            column=self._action_index % self.ACTION_COLUMNS,
            sticky="ew",
            padx=3,
            pady=2,
        )
        self._action_index += 1

    def _render_control(self, parent, control, ctx, screen_id, compact=False):
        control_type = control["type"]
        if control_type == "text":
            self._add_text(parent, control, ctx, title=control.get("variant") == "title")
        elif control_type == "input":
            self._add_input(parent, control, ctx)
        elif control_type == "progressbar":
            self._add_progressbar(parent, control, ctx, compact=compact)
        elif control_type == "list":
            self._add_list(parent, control, ctx)
        elif control_type == "button":
            self._add_button(parent, control, ctx)
        else:
            raise ValueError(
                f"Unsupported control type {control_type!r} on screen {screen_id}"
            )

    def render(self):
        if self.frame is not None:
            self.frame.destroy()

        screen_id = self.controller.screen
        screen = self.screens.get(screen_id)
        if not screen:
            self.controller.screen = "front_page"
            screen = self.screens["front_page"]

        ctx = self.controller.get_context()
        containers, controls_by_frame, _definitions = self._frame_containers(screen)
        self._status_bar_index = 0
        for frame_id in self.FRAME_ORDER:
            parent = containers[frame_id]
            controls = controls_by_frame[frame_id]
            if frame_id == "context":
                index = 0
                while index < len(controls):
                    control = controls[index]
                    if control["type"] == "progressbar" and control.get("compact"):
                        row = ctk.CTkFrame(parent, fg_color="transparent")
                        row.pack(fill="x", pady=2)
                        for _ in range(2):
                            if index >= len(controls):
                                break
                            candidate = controls[index]
                            if candidate["type"] != "progressbar" or not candidate.get("compact"):
                                break
                            self._render_control(
                                row,
                                candidate,
                                ctx,
                                screen_id,
                                compact=True,
                            )
                            index += 1
                        continue
                    self._render_control(parent, control, ctx, screen_id)
                    index += 1
                continue
            for control in controls:
                if frame_id == "status":
                    target = (
                        self._status_bars
                        if control["type"] == "progressbar"
                        else self._status_identity
                    )
                    self._render_control(
                        target,
                        control,
                        ctx,
                        screen_id,
                        compact=control["type"] == "progressbar",
                    )
                else:
                    self._render_control(parent, control, ctx, screen_id)


def main():
    root = ctk.CTk()
    DeclarativeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
