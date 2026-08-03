#!/usr/bin/env python3
"""CustomTkinter renderer for declarative UI + GameController."""

from __future__ import annotations

import json
from pathlib import Path

import customtkinter as ctk

from hero_engine import GameController


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class DeclarativeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hero Adventure")
        self.root.geometry("980x760")
        self.controller = GameController()
        self.screens = self._load_screens()
        self.name_var = ctk.StringVar(value="")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.frame = None
        self.render()

    def _load_screens(self):
        ui_dir = Path(__file__).resolve().parent / "ui"
        screens = {}
        for path in ui_dir.glob("*.json"):
            data = json.loads(path.read_text())
            screens[data["id"]] = data
        return screens

    def _fmt(self, text, ctx):
        return text.format_map(SafeDict(ctx))

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

    def _add_list(self, parent, list_id, label, ctx):
        rows = ctx.get(list_id, [])
        if label:
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(10, 4))
        for row in rows:
            text = self._fmt(row.get("text", ""), ctx)
            action = row.get("action")
            enabled = row.get("enabled", True)
            if action and enabled:
                ctk.CTkButton(
                    parent, text=text, command=lambda a=action: self._dispatch(a),
                    anchor="w", height=34
                ).pack(fill="x", pady=2)
            else:
                ctk.CTkLabel(parent, text=text, anchor="w", justify="left").pack(fill="x", pady=2)

    def render(self):
        if self.frame is not None:
            self.frame.destroy()

        screen_id = self.controller.screen
        screen = self.screens.get(screen_id)
        if not screen:
            self.controller.screen = "front_page"
            screen = self.screens["front_page"]

        ctx = self.controller.get_context()
        self.frame = ctk.CTkScrollableFrame(self.root)
        self.frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            self.frame,
            text=self._fmt(screen.get("title", screen_id), ctx),
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(anchor="w", pady=(6, 12))

        if screen_id == "character_creation":
            row = ctk.CTkFrame(self.frame, fg_color="transparent")
            row.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(row, text="Hero Name:", width=90).pack(side="left")
            self.name_var.set(self.controller.pending_name)
            ctk.CTkEntry(row, textvariable=self.name_var).pack(side="left", fill="x", expand=True)

        for line in screen.get("text", []):
            ctk.CTkLabel(
                self.frame,
                text=self._fmt(line, ctx),
                anchor="w",
                justify="left",
                wraplength=900
            ).pack(fill="x", pady=1)

        for list_def in screen.get("lists", []):
            self._add_list(self.frame, list_def["id"], list_def.get("label"), ctx)

        if screen.get("buttons"):
            btn_wrap = ctk.CTkFrame(self.frame, fg_color="transparent")
            btn_wrap.pack(fill="x", pady=(14, 4))
            for button in screen["buttons"]:
                visible_if = button.get("visible_if")
                if visible_if and not ctx.get(visible_if):
                    continue
                label = self._fmt(button["label"], ctx)
                action = button.get("action")
                ctk.CTkButton(
                    btn_wrap,
                    text=label,
                    command=(lambda a=action: self._dispatch(a)) if action else None,
                    height=38
                ).pack(fill="x", pady=3)


def main():
    root = ctk.CTk()
    DeclarativeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
