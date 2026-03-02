import re
from typing import Any, List

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from models import Condition
from services import SOURCE_FULL


class ConditionDetailScreen(Screen):
    """Detail screen for a single condition."""

    def __init__(self, condition: Condition) -> None:
        super().__init__()
        self.condition = condition

    def compose(self) -> ComposeResult:
        c = self.condition
        with Vertical():
            yield Static(f"[bold]{c.name}[/bold]", classes="title")
            yield Static("[bold]Condition[/bold]")
            yield Static("")
            with ScrollableContainer():
                if c.entries:
                    yield Static(self._format_entries(c.entries))
                yield Static(f"\n[dim]Source: {SOURCE_FULL.get(c.source, c.source)}[/dim]")
            yield Button("Back", id="back")

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@\w+ ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        return text.strip()

    def _format_entries(self, entries: List[Any]) -> str:
        def render(entry: Any) -> str:
            if isinstance(entry, str):
                return self._strip_tags(entry)
            if isinstance(entry, dict):
                e_type = entry.get("type")
                if e_type == "list":
                    return "\n".join(f"- {render(e)}" for e in entry.get("items", []))
                if e_type in {"entries", "section"}:
                    header = entry.get("name")
                    body = "\n".join(render(e) for e in entry.get("entries", []))
                    return f"[bold]{header}[/bold]\n{body}" if header else body
                if "entries" in entry:
                    return "\n".join(render(e) for e in entry["entries"])
                return str(entry)
            if isinstance(entry, list):
                return "\n".join(render(e) for e in entry)
            return str(entry)

        return "\n\n".join(render(e) for e in entries)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
