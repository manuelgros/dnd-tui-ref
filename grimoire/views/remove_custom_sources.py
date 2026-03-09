from dataclasses import dataclass
from pathlib import Path
from typing import Set

from textual import events
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Static


_COLS = 2


class RemoveCustomSourcesScreen(Screen):
    """Screen for removing previously uploaded custom source files."""

    @dataclass
    class Removed(Message):
        removed_codes: Set[str]

    def __init__(self, custom_sources: dict, data_dir: Path) -> None:
        """
        Args:
            custom_sources: dict of {source_code: display_name}
            data_dir: Path to the data directory (for file deletion)
        """
        super().__init__()
        self._custom_sources = dict(custom_sources)
        self._data_dir = data_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[bold]Remove Custom Sources[/bold]", classes="title")
            yield Static("")
            if not self._custom_sources:
                yield Static("[dim]No custom sources installed.[/dim]")
                yield Static("")
                yield Button("Close", id="cancel", variant="primary")
                return

            yield Static("Select the sources you want to remove:")
            yield Static("")
            grid = Grid(id="source_list")
            yield grid
            yield Static("")
            yield Static("", id="status")
            yield Static("")
            with Horizontal(id="buttons"):
                yield Button("Remove Selected", id="remove", variant="error")
                yield Button("Cancel", id="cancel", variant="default")

    def on_mount(self) -> None:
        if not self._custom_sources:
            return
        grid = self.query_one("#source_list")
        for code, name in self._custom_sources.items():
            grid.mount(Checkbox(f"{name} ({code})", id=f"src_{code}", value=False))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "remove":
            self._do_remove()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)

        elif event.key in ("up", "down", "left", "right"):
            focused = self.app.focused
            checkboxes = list(self.query("#source_list Checkbox"))
            if not checkboxes or focused not in checkboxes:
                return
            if getattr(focused, "_expanded", False):
                return
            idx = checkboxes.index(focused)
            if event.key == "down":
                new_idx = idx + _COLS
            elif event.key == "up":
                new_idx = idx - _COLS
            elif event.key == "right":
                new_idx = idx + 1
            else:
                new_idx = idx - 1
            if 0 <= new_idx < len(checkboxes):
                checkboxes[new_idx].focus()
            event.stop()

    def _do_remove(self) -> None:
        from ..config import remove_custom_source
        from ..services.data_manager import DataManager

        selected: Set[str] = set()
        for code in self._custom_sources:
            cb = self.query_one(f"#src_{code}", Checkbox)
            if cb.value:
                selected.add(code)

        if not selected:
            self.query_one("#status", Static).update("[yellow]No sources selected.[/yellow]")
            return

        manager = DataManager(self._data_dir)
        for code in selected:
            manager.remove_source_files(code)
            remove_custom_source(code)

        self.dismiss(selected)
