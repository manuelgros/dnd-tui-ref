import threading
from pathlib import Path
from typing import List

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.widgets import Button, Checkbox, Footer, Header, ProgressBar, Static


class SetupWizardApp(App):
    """First-run setup wizard for downloading 5etools data."""

    TITLE = "Grimoire 5e — Setup"
    CSS_PATH = str(Path(__file__).parent.parent / "styles.css")

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, manage_only: bool = False) -> None:
        super().__init__()
        self._manage_only = manage_only
        self._downloading = False

        from ..services.data_manager import DataManager
        self._manager = DataManager()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wizard"):
            yield Static("[bold]Grimoire 5e — Setup[/bold]", classes="title")
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
                installed = set(self._manager.get_installed_sources())
                for src in self._manager.sources:
                    default = src.get("default", False) or src["id"] in installed
                    yield Checkbox(
                        src["name"],
                        value=default,
                        name=src["id"],
                        id=f"src_{src['id']}",
                    )

            yield Static("")
            yield Static("", id="status")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            yield Static("")
            installed = set(self._manager.get_installed_sources())
            any_selected = any(
                src.get("default", False) or src["id"] in installed
                for src in self._manager.sources
            )
            yield Button("Download & Launch", id="download", variant="primary", disabled=not any_selected)

        yield Footer()

    _COLS = 2  # must match grid-size in styles.css

    def on_key(self, event: events.Key) -> None:
        checkboxes = list(self.query(Checkbox))
        focused = self.focused
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
            self.query_one("#download", Button).focus()
            event.stop()
            return

        if new_idx is not None and new_idx != idx:
            checkboxes[new_idx].focus()
            event.stop()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if not self._downloading:
            any_selected = any(cb.value for cb in self.query(Checkbox))
            self.query_one("#download", Button).disabled = not any_selected

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "download" and not self._downloading:
            self._start_download()

    def _selected_sources(self) -> List[str]:
        return [
            cb.name for cb in self.query(Checkbox)
            if cb.value and cb.name
        ]

    def _start_download(self) -> None:
        self._downloading = True
        self.query_one("#download", Button).disabled = True
        sources = self._selected_sources()

        total_files = len(self._manager.files_for_sources(sources))

        def progress_cb(file_path: str, current: int, total: int) -> None:
            pct = int(current / total * 100) if total > 0 else 0
            label = file_path or "Complete"
            self.call_from_thread(self._update_progress, label, pct, current, total)

        def run() -> None:
            try:
                self._manager.download_sources(sources, progress_cb=progress_cb)
                self.call_from_thread(self._on_complete, sources)
            except Exception as e:
                self.call_from_thread(self._on_error, str(e))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _update_progress(self, label: str, pct: int, current: int, total: int) -> None:
        self.query_one("#status", Static).update(
            f"Downloading ({current}/{total}): {label}"
        )
        self.query_one("#progress", ProgressBar).update(progress=pct)

    def _on_complete(self, sources: List[str]) -> None:
        self.query_one("#status", Static).update(
            f"[green]Download complete! {len(sources)} source(s) installed.[/green]"
        )
        self.query_one("#progress", ProgressBar).update(progress=100)

        # Exit the wizard, passing the selected sources as the return value.
        # cli.py will receive this from run() and launch GrimoireApp afterwards.
        self.exit(set(sources))

    def _on_error(self, message: str) -> None:
        self._downloading = False
        self.query_one("#download", Button).disabled = False
        self.query_one("#status", Static).update(
            f"[red]Error: {message}[/red]\n[dim]Check your internet connection and try again.[/dim]"
        )
        self.query_one("#progress", ProgressBar).update(progress=0)
