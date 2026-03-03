from typing import Any, Optional, Set

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical, Grid
from textual.message import Message
from textual.widgets import Button, Checkbox, Static

from ..services import SOURCE_FULL


class SettingsView(Vertical):
    """Settings view for toggling active source books."""

    class SourcesChanged(Message):
        def __init__(self, active_sources: set) -> None:
            super().__init__()
            self.active_sources = active_sources

    class SourcesInstalled(Message):
        def __init__(self, installed_sources: set) -> None:
            super().__init__()
            self.installed_sources = installed_sources

    def __init__(self, installed_sources: Optional[Set[str]] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Only show sources that were actually downloaded
        self._installed_sources: Set[str] = installed_sources if installed_sources is not None else set(SOURCE_FULL.keys())

    def compose(self) -> ComposeResult:
        yield Static("[bold]Settings[/bold]", classes="title")
        yield Static("")
        yield Static("[bold yellow]Source Books[/bold yellow]")
        yield Static(
            "Toggle books to include across all tabs. Changes take effect immediately."
        )
        yield Static("")
        with Grid(id="source_list"):
            for code, title in SOURCE_FULL.items():
                if code not in self._installed_sources:
                    continue
                yield Checkbox(title, value=True, name=code)
        yield Static("")
        yield Button("Manage Sources", id="manage_sources", variant="primary")

    _COLS = 2  # must match grid-size in styles.css

    def on_key(self, event: events.Key) -> None:
        checkboxes = list(self.query(Checkbox))
        focused = self.app.focused
        if focused not in checkboxes:
            return

        idx = checkboxes.index(focused)
        n = len(checkboxes)
        new_idx = None

        if event.key == "tab":
            self.query_one("#manage_sources", Button).focus()
            self.query_one("#manage_sources", Button).scroll_visible()
            event.stop()
            return
        elif event.key == "shift+tab":
            self.app.query_one("Tabs").focus()
            event.stop()
            return

        if event.key == "down":
            candidate = idx + self._COLS
            new_idx = candidate if candidate < n else idx
        elif event.key == "up":
            candidate = idx - self._COLS
            new_idx = candidate if candidate >= 0 else idx
        elif event.key == "right":
            if idx % self._COLS < self._COLS - 1 and idx + 1 < n:
                new_idx = idx + 1
        elif event.key == "left":
            if idx % self._COLS > 0:
                new_idx = idx - 1

        if new_idx is not None and new_idx != idx:
            checkboxes[new_idx].focus()
            checkboxes[new_idx].scroll_visible()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "manage_sources":
            from .manage_sources import ManageSourcesScreen
            self.app.push_screen(
                ManageSourcesScreen(
                    installed_sources=set(self._installed_sources),
                    data_dir=self.app.data_dir,
                ),
                self._on_sources_managed,
            )

    def _on_sources_managed(self, new_installed: Optional[Set[str]]) -> None:
        if new_installed is None:
            return
        self._installed_sources = new_installed
        self._refresh_source_grid()
        self.post_message(self.SourcesInstalled(new_installed))

    def _refresh_source_grid(self) -> None:
        grid = self.query_one("#source_list", Grid)
        for cb in grid.query(Checkbox):
            cb.remove()
        for code, title in SOURCE_FULL.items():
            if code not in self._installed_sources:
                continue
            grid.mount(Checkbox(title, value=True, name=code))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        active = {cb.name for cb in self.query(Checkbox) if cb.value and cb.name}
        self.post_message(self.SourcesChanged(active))
