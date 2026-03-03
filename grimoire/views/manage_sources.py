import threading
from pathlib import Path
from typing import List, Optional, Set

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, ProgressBar, Static


class ManageSourcesScreen(Screen):
    """Modal screen for adding or removing downloaded source books."""

    TITLE = "Grimoire 5e — Manage Sources"
    CSS_PATH = str(Path(__file__).parent.parent / "styles.css")

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, installed_sources: Set[str], data_dir: Optional[Path] = None) -> None:
        super().__init__()
        self._installed_sources = installed_sources
        self._downloading = False

        from ..services.data_manager import DataManager
        self._manager = DataManager(data_dir=data_dir)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wizard"):
            yield Static("[bold]Manage Sources[/bold]", classes="title")
            yield Static("")
            yield Static(
                "[bold yellow]Important:[/bold yellow] Only download content you legally own. "
                "This tool downloads data from 5etools for personal use."
            )
            yield Static("")
            yield Static("[bold]Always included (global files):[/bold]")
            yield Static("  • Conditions & Diseases")
            yield Static("  • Variant Rules")
            yield Static("  • Feats")
            yield Static("  • Magic Items & Variants")
            yield Static("  • Legendary Groups")
            yield Static("")
            yield Static("[bold]Select source books to include:[/bold]")

            with Grid(id="source_list"):
                for src in self._manager.sources:
                    checked = src["id"] in self._installed_sources
                    yield Checkbox(
                        src["name"],
                        value=checked,
                        name=src["id"],
                        id=f"src_{src['id']}",
                    )

            yield Static("")
            yield Static("", id="status")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            yield Static("")
            any_selected = any(src["id"] in self._installed_sources for src in self._manager.sources)
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel", variant="error")
                yield Button("Apply Changes", id="apply", variant="primary", disabled=not any_selected)

        yield Footer()

    _COLS = 2

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        cancel_btn = self.query_one("#cancel", Button)
        apply_btn = self.query_one("#apply", Button)

        # Left/Right navigate between the two action buttons
        if focused is cancel_btn:
            if event.key == "right":
                apply_btn.focus()
                event.stop()
            return
        if focused is apply_btn:
            if event.key == "left":
                cancel_btn.focus()
                event.stop()
            return

        # Arrow-key navigation within the checkbox grid
        checkboxes = list(self.query(Checkbox))
        if focused not in checkboxes:
            return

        idx = checkboxes.index(focused)
        n = len(checkboxes)
        new_idx = None

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
        elif event.key == "tab":
            cancel_btn.focus()
            cancel_btn.scroll_visible()
            event.stop()
            return

        if new_idx is not None and new_idx != idx:
            checkboxes[new_idx].focus()
            event.stop()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if not self._downloading:
            any_selected = any(cb.value for cb in self.query(Checkbox))
            self.query_one("#apply", Button).disabled = not any_selected

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply" and not self._downloading:
            self._start_apply()
        elif event.button.id == "cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _selected_sources(self) -> List[str]:
        return [cb.name for cb in self.query(Checkbox) if cb.value and cb.name]

    def _start_apply(self) -> None:
        self._downloading = True
        self.query_one("#apply", Button).disabled = True
        self.query_one("#cancel", Button).disabled = True
        sources = self._selected_sources()

        def progress_cb(file_path: str, current: int, total: int) -> None:
            pct = int(current / total * 100) if total > 0 else 0
            label = file_path or "Complete"
            self.app.call_from_thread(self._update_progress, label, pct, current, total)

        def run() -> None:
            try:
                self._manager.download_sources(sources, progress_cb=progress_cb)
                self.app.call_from_thread(self._on_complete, sources)
            except Exception as e:
                self.app.call_from_thread(self._on_error, str(e))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _update_progress(self, label: str, pct: int, current: int, total: int) -> None:
        if total == 0:
            self.query_one("#status", Static).update("Updating configuration…")
        else:
            self.query_one("#status", Static).update(
                f"Downloading ({current}/{total}): {label}"
            )
        self.query_one("#progress", ProgressBar).update(progress=pct)

    def _on_complete(self, sources: List[str]) -> None:
        self.query_one("#status", Static).update(
            f"[green]Done! {len(sources)} source(s) configured.[/green]"
        )
        self.query_one("#progress", ProgressBar).update(progress=100)
        self.dismiss(set(sources))

    def _on_error(self, message: str) -> None:
        self._downloading = False
        self.query_one("#apply", Button).disabled = False
        self.query_one("#cancel", Button).disabled = False
        self.query_one("#status", Static).update(
            f"[red]Error: {message}[/red]\n[dim]Check your internet connection and try again.[/dim]"
        )
        self.query_one("#progress", ProgressBar).update(progress=0)
