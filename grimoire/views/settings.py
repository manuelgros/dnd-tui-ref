from typing import Any, Optional, Set

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.message import Message
from textual.widgets import Button, Checkbox, Select, Static

from ..config import get_custom_sources, register_custom_source
from ..services import SOURCE_FULL
from ..themes import GRIMOIRE_THEMES
from ._grouped_select import GroupedSelect


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

    class ThemeChanged(Message):
        def __init__(self, theme: str) -> None:
            super().__init__()
            self.theme = theme

    def __init__(
        self,
        installed_sources: Optional[Set[str]] = None,
        current_theme: str = "textual-dark",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._installed_sources: Set[str] = installed_sources if installed_sources is not None else set(SOURCE_FULL.keys())
        self._current_theme = current_theme

    def compose(self) -> ComposeResult:
        yield Static("[bold]Settings[/bold]", classes="title")
        yield Static("")
        yield Static("[bold yellow]Appearance[/bold yellow]")
        grimoire_names = {t.name for t in GRIMOIRE_THEMES}
        grimoire_group = [
            (t.name.replace("-", " ").title(), t.name)
            for t in GRIMOIRE_THEMES
            if t.name in self.app.available_themes
        ]
        textual_group = [
            (name.replace("-", " ").title(), name)
            for name in sorted(self.app.available_themes.keys())
            if name not in grimoire_names
        ]
        yield GroupedSelect(
            groups=[("Grimoire Themes", grimoire_group), ("Textual Themes", textual_group)],
            id="theme_select",
            allow_blank=False,
            value=self._current_theme,
        )
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
            # Custom sources shown after official ones
            for code, name in get_custom_sources().items():
                if code not in self._installed_sources:
                    continue
                yield Checkbox(f"{name} [dim](custom)[/dim]", value=True, name=code)
        yield Static("")
        with Horizontal(id="source_buttons"):
            yield Button("Manage Sources", id="manage_sources", variant="primary")
            yield Button("Upload Source", id="upload_source", variant="default")
            custom = get_custom_sources()
            if custom:
                yield Button("Remove Custom", id="remove_custom", variant="warning")

    _COLS = 2  # must match grid-size in styles.css

    def on_key(self, event: events.Key) -> None:
        focused = self.app.focused
        checkboxes = list(self.query(Checkbox))
        buttons = list(self.query("#source_buttons Button"))
        theme_select = self.query_one("#theme_select", GroupedSelect)

        # ── Theme select layer ───────────────────────────────────────────────
        if focused is theme_select:
            if event.key == "shift+tab":
                self.app.query_one("Tabs").focus()
                event.stop()
            # Tab: let Textual move focus naturally into checkboxes
            return

        # ── Button row layer ─────────────────────────────────────────────────
        if focused in buttons:
            idx = buttons.index(focused)
            if event.key == "right":
                if idx + 1 < len(buttons):
                    buttons[idx + 1].focus()
                event.stop()
            elif event.key == "left":
                if idx > 0:
                    buttons[idx - 1].focus()
                event.stop()
            elif event.key == "shift+tab":
                if checkboxes:
                    checkboxes[-1].focus()
                    checkboxes[-1].scroll_visible()
                else:
                    theme_select.focus()
                event.stop()
            return

        # ── Checkbox grid layer ──────────────────────────────────────────────
        if focused not in checkboxes:
            return

        idx = checkboxes.index(focused)
        n = len(checkboxes)
        new_idx = None

        if event.key == "tab":
            if buttons:
                buttons[0].focus()
                buttons[0].scroll_visible()
            event.stop()
            return
        elif event.key == "shift+tab":
            theme_select.focus()
            theme_select.scroll_visible()
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
        elif event.button.id == "upload_source":
            from .upload_source import UploadSourceScreen
            self.app.push_screen(
                UploadSourceScreen(data_dir=self.app.data_dir),
                self._on_upload_closed,
            )
        elif event.button.id == "remove_custom":
            from .remove_custom_sources import RemoveCustomSourcesScreen
            self.app.push_screen(
                RemoveCustomSourcesScreen(
                    custom_sources=get_custom_sources(),
                    data_dir=self.app.data_dir,
                ),
                self._on_remove_closed,
            )

    def _on_sources_managed(self, new_installed: Optional[Set[str]]) -> None:
        if new_installed is None:
            return
        self._installed_sources = new_installed
        self._refresh_source_grid()
        self.post_message(self.SourcesInstalled(new_installed))

    def _on_upload_closed(self, _result: Any = None) -> None:
        # Re-read config to pick up any newly registered custom source
        custom = get_custom_sources()
        for code in custom:
            self._installed_sources.add(code)
        self._refresh_source_grid()
        self._refresh_remove_button()
        if custom:
            self.post_message(self.SourcesInstalled(set(self._installed_sources)))

    def _on_remove_closed(self, removed_codes: Optional[Set[str]] = None) -> None:
        if not removed_codes:
            return
        # Re-read installed sources from config after removal
        from ..config import load_config
        cfg_installed = set(load_config().get("installed_sources", []))
        self._installed_sources = cfg_installed
        self._refresh_source_grid()
        self._refresh_remove_button()
        self.post_message(self.SourcesInstalled(self._installed_sources))

    def _refresh_source_grid(self) -> None:
        grid = self.query_one("#source_list", Grid)
        for cb in grid.query(Checkbox):
            cb.remove()
        for code, title in SOURCE_FULL.items():
            if code not in self._installed_sources:
                continue
            grid.mount(Checkbox(title, value=True, name=code))
        for code, name in get_custom_sources().items():
            if code not in self._installed_sources:
                continue
            grid.mount(Checkbox(f"{name} [dim](custom)[/dim]", value=True, name=code))

    def _refresh_remove_button(self) -> None:
        custom = get_custom_sources()
        buttons = self.query_one("#source_buttons", Horizontal)
        existing = self.query("#remove_custom")
        if custom and not existing:
            buttons.mount(Button("Remove Custom", id="remove_custom", variant="warning"))
        elif not custom and existing:
            for btn in existing:
                btn.remove()

    def on_select_changed(self, event: Select.Changed) -> None:
        if isinstance(event.select, GroupedSelect) and event.select.id == "theme_select" and isinstance(event.value, str):
            self.post_message(self.ThemeChanged(event.value))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        active = {cb.name for cb in self.query(Checkbox) if cb.value and cb.name}
        self.post_message(self.SourcesChanged(active))
