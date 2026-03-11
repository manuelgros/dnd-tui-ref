from pathlib import Path
from dataclasses import dataclass

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Input, LoadingIndicator, Static
from textual.worker import Worker, WorkerState


class UploadSourceScreen(Screen):
    """Screen for importing a custom 5etools JSON source file."""

    @dataclass
    class Uploaded(Message):
        source_code: str
        source_name: str

    def __init__(self, data_dir: Path) -> None:
        super().__init__()
        self._data_dir = data_dir
        self._pending_result: dict | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="upload_container"):
            yield Static("[bold]Upload Custom Source[/bold]", classes="title")

            # ── Phase 1: input ────────────────────────────────────────────
            with Vertical(id="phase_input"):
                yield Static(
                    "Import a custom D&D 5e source book in 5etools JSON format.\n"
                    "The file will be split and stored alongside your downloaded sources."
                )
                yield Static("")
                yield Static("[bold]File Path[/bold]")
                yield Input(placeholder="Enter full path to .json file...", id="file_path")
                yield Static("", id="error_msg")
                yield Static("")
                with Horizontal():
                    yield Button("Validate", id="validate", variant="primary")
                    yield Button("Cancel", id="cancel_input", variant="error")

            # ── Phase 2: loading ──────────────────────────────────────────
            with Vertical(id="phase_loading"):
                yield LoadingIndicator()
                yield Static("Reading and splitting source file…", id="loading_status")

            # ── Phase 3: summary / confirmation ───────────────────────────
            with Vertical(id="phase_summary"):
                yield Static("", id="summary_text")
                yield Static("")
                with Horizontal():
                    yield Button("Confirm Import", id="confirm", variant="primary")
                    yield Button("Cancel", id="cancel_summary", variant="error")

            # ── Phase 4: result ───────────────────────────────────────────
            with Vertical(id="phase_result"):
                yield Static("", id="result_text")
                yield Static("")
                with Horizontal():
                    yield Button("Close", id="close", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#phase_loading").display = False
        self.query_one("#phase_summary").display = False
        self.query_one("#phase_result").display = False

    # ── Button handling ───────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid in ("cancel_input", "cancel_summary"):
            self.dismiss(None)
        elif bid == "validate":
            self._start_validate()
        elif bid == "confirm":
            self._do_import()
        elif bid == "close":
            self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return

        focused = self.app.focused

        if event.key == "enter":
            if hasattr(focused, "id") and focused.id == "file_path":
                self._start_validate()
            return

        # Determine which phase's buttons are currently visible
        visible_phase = next(
            (pid for pid in ("phase_input", "phase_summary", "phase_result")
             if self.query_one(f"#{pid}").display),
            None,
        )
        if visible_phase is None:
            return

        buttons = list(self.query(f"#{visible_phase} Button"))
        if focused not in buttons:
            return

        idx = buttons.index(focused)
        if event.key in ("left", "right"):
            new_idx = idx + (1 if event.key == "right" else -1)
            if 0 <= new_idx < len(buttons):
                buttons[new_idx].focus()
            event.stop()
        elif event.key == "tab":
            # Tab from any button → back to file path input (input phase only)
            if visible_phase == "phase_input":
                self.query_one("#file_path", Input).focus()
                event.stop()

    # ── Phase transitions ─────────────────────────────────────────────────

    def _show_phase(self, phase_id: str) -> None:
        for pid in ("phase_input", "phase_loading", "phase_summary", "phase_result"):
            self.query_one(f"#{pid}").display = pid == phase_id

    def _set_error(self, msg: str) -> None:
        self.query_one("#error_msg", Static).update(f"[bold red]{msg}[/bold red]")

    # ── Logic ─────────────────────────────────────────────────────────────

    def _start_validate(self) -> None:
        path_str = self.query_one("#file_path", Input).value.strip()
        if not path_str:
            self._set_error("Please enter a file path.")
            return

        json_path = Path(path_str)
        if not json_path.exists():
            self._set_error(f"File not found: {path_str}")
            return
        if json_path.suffix.lower() != ".json":
            self._set_error("File must be a .json file.")
            return

        self._show_phase("phase_loading")
        self._run_import(json_path)

    @work(thread=True)
    def _run_import(self, json_path: Path) -> dict:
        from ..services.data_manager import DataManager
        return DataManager(self._data_dir).import_source(json_path)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != "_run_import":
            return
        if event.state == WorkerState.SUCCESS:
            result = event.worker.result
            self._pending_result = result
            counts = result["counts"]
            parts = [f"{v} {k}s" for k, v in counts.items() if v > 0]
            self.query_one("#summary_text", Static).update(
                f"[bold]Found in '{result['name']}' ({result['source']}):[/bold]\n"
                f"{', '.join(parts)}\n\n"
                "Import this source?"
            )
            self._show_phase("phase_summary")
        elif event.state == WorkerState.ERROR:
            self._set_error(str(event.worker.error))
            self._show_phase("phase_input")

    def _do_import(self) -> None:
        if self._pending_result is None:
            return
        result = self._pending_result
        from ..config import register_custom_source
        register_custom_source(result["source"], result["name"])
        self.query_one("#result_text", Static).update(
            f"[bold green]'{result['name']}' imported successfully![/bold green]\n\n"
            "The source has been added to your library."
        )
        self._show_phase("phase_result")
        self.post_message(self.Uploaded(
            source_code=result["source"],
            source_name=result["name"],
        ))
