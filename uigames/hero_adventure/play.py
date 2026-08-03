#!/usr/bin/env python3
"""Textual terminal renderer for the declarative UI + GameController."""

from __future__ import annotations

import json
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Static

from hero_engine import GameController


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


class HeroAdventureTUI(App):
    TITLE = "Hero Adventure"
    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        padding: 1 2;
    }

    #title {
        height: auto;
        margin-bottom: 1;
    }

    #name_row {
        height: auto;
        margin-bottom: 1;
    }

    #content {
        height: 1fr;
    }

    .line {
        height: auto;
    }

    .list_label {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
    }

    .action_button {
        margin-bottom: 1;
        width: 100%;
    }

    .disabled_line {
        color: gray;
        margin-bottom: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.controller = GameController()
        self.screens = self._load_screens()
        self.ctx = {}
        self._button_actions = {}
        self._button_seq = 0

    def _load_screens(self):
        ui_dir = Path(__file__).resolve().parent / "ui"
        screens = {}
        for path in ui_dir.glob("*.json"):
            data = json.loads(path.read_text())
            screens[data["id"]] = data
        return screens

    def _fmt(self, text: str) -> str:
        return text.format_map(SafeDict(self.ctx))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="main"):
            yield Static(id="title")
            with Horizontal(id="name_row"):
                yield Label("Hero Name:")
                yield Input(placeholder="Enter hero name", id="name_input")
            yield VerticalScroll(id="content")
        yield Footer()

    async def on_mount(self):
        await self.refresh_screen()

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

        self.ctx = self.controller.get_context()
        self._button_actions = {}

        title_widget = self.query_one("#title", Static)
        title_widget.update(Panel(Text(self._fmt(screen.get("title", screen_id)), style="bold cyan")))

        name_row = self.query_one("#name_row", Horizontal)
        name_input = self.query_one("#name_input", Input)
        if screen_id == "character_creation":
            name_row.display = True
            name_input.value = self.controller.pending_name
            name_input.focus()
        else:
            name_row.display = False

        content = self.query_one("#content", VerticalScroll)
        await content.remove_children()

        for line in screen.get("text", []):
            content.mount(Static(self._fmt(line), classes="line"))

        for list_def in screen.get("lists", []):
            label = list_def.get("label")
            if label:
                content.mount(Static(label, classes="list_label"))
            for row in self.ctx.get(list_def["id"], []):
                text = self._fmt(row.get("text", ""))
                action = row.get("action")
                enabled = row.get("enabled", True)
                if action and enabled:
                    button_id = f"act_{self._button_seq}"
                    self._button_seq += 1
                    self._button_actions[button_id] = action
                    content.mount(Button(text, classes="action_button", id=button_id))
                else:
                    content.mount(Static(f"• {text}", classes="disabled_line"))

        for button in screen.get("buttons", []):
            visible_if = button.get("visible_if")
            if visible_if and not self.ctx.get(visible_if):
                continue
            label = self._fmt(button.get("label", ""))
            action = button.get("action")
            if action:
                button_id = f"act_{self._button_seq}"
                self._button_seq += 1
                self._button_actions[button_id] = action
                content.mount(Button(label, classes="action_button", id=button_id))
            else:
                content.mount(Static(f"• {label}", classes="disabled_line"))

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
