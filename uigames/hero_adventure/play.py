#!/usr/bin/env python3
"""Terminal renderer for the declarative UI + GameController."""

from __future__ import annotations

import json
import os
from pathlib import Path

from hero_engine import GameController


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class TerminalUI:
    def __init__(self):
        self.controller = GameController()
        self.screens = self._load_screens()

    def _load_screens(self):
        ui_dir = Path(__file__).resolve().parent / "ui"
        screens = {}
        for path in ui_dir.glob("*.json"):
            data = json.loads(path.read_text())
            screens[data["id"]] = data
        return screens

    def _fmt(self, text, ctx):
        return text.format_map(SafeDict(ctx))

    def _clear(self):
        os.system("clear")

    def _build_actions(self, screen_def, ctx):
        items = []
        idx = 1

        for list_def in screen_def.get("lists", []):
            list_rows = ctx.get(list_def["id"], [])
            if list_def.get("label"):
                print(f"\n{list_def['label']}:")
            for row in list_rows:
                text = self._fmt(row.get("text", ""), ctx)
                action = row.get("action")
                enabled = row.get("enabled", True)
                if action and enabled:
                    print(f"  {idx}. {text}")
                    items.append((str(idx), action))
                    idx += 1
                else:
                    print(f"   - {text}")

        if screen_def.get("buttons"):
            print()
        for button in screen_def.get("buttons", []):
            visible_if = button.get("visible_if")
            if visible_if and not ctx.get(visible_if):
                continue
            label = self._fmt(button["label"], ctx)
            action = button.get("action")
            if action:
                print(f"  {idx}. {label}")
                items.append((str(idx), action))
                idx += 1
            else:
                print(f"   - {label}")

        return items

    def _ensure_character_name(self):
        if self.controller.screen == "character_creation" and not self.controller.pending_name:
            name = input("\nEnter hero name: ").strip()
            self.controller.set_pending_name(name or "Hero")

    def run(self):
        while True:
            if self.controller.quit_requested:
                return

            screen_id = self.controller.screen
            screen = self.screens.get(screen_id)
            if not screen:
                # Defensive fallback for undefined screens.
                self.controller.screen = "front_page"
                continue

            self._ensure_character_name()
            ctx = self.controller.get_context()
            self._clear()

            print(f"\n=== {self._fmt(screen.get('title', screen_id), ctx)} ===\n")
            for line in screen.get("text", []):
                print(self._fmt(line, ctx))

            actions = self._build_actions(screen, ctx)
            action_map = dict(actions)

            if not action_map:
                input("\nPress Enter to continue...")
                self.controller.screen = "front_page"
                continue

            choice = input("\nChoose: ").strip()
            if choice not in action_map:
                continue
            self.controller.dispatch(action_map[choice])


def main():
    TerminalUI().run()


if __name__ == "__main__":
    main()
