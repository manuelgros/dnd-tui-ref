import re
from typing import Any, List

from textual import events
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
            yield Static("[bold yellow]Condition[/bold yellow]")
            yield Static("")
            with ScrollableContainer():
                if c.entries:
                    for widget in self._render_entries(c.entries):
                        yield widget
                yield Static(f"\n[dim]Source: {SOURCE_FULL.get(c.source, c.source)}[/dim]")
            yield Button("Back", id="back")

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@variantrule ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@action ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@\w+ ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        return text.strip()

    def _render_entries(self, entries: List[Any]) -> List[Static]:
        """Yield Static widgets for each top-level entry block."""
        widgets: List[Static] = []
        for entry in entries:
            if isinstance(entry, str):
                text = self._strip_tags(entry)
                if text:
                    widgets.append(Static(text))
                    widgets.append(Static(""))
            elif isinstance(entry, dict):
                e_type = entry.get("type")
                if e_type == "list":
                    lines = "\n".join(f"  • {self._strip_tags(str(i))}" for i in entry.get("items", []))
                    widgets.append(Static(lines))
                    widgets.append(Static(""))
                elif e_type == "table":
                    widgets.append(Static(self._format_table(entry)))
                    widgets.append(Static(""))
                elif e_type in {"entries", "section"}:
                    # May be a wrapper containing named sub-sections or plain text
                    header = entry.get("name")
                    if header:
                        widgets.append(Static(f"[bold yellow]{header}[/bold yellow]"))
                    for sub in self._render_entries(entry.get("entries", [])):
                        widgets.append(sub)
                else:
                    # Fallback: inline render
                    text = self._inline_render(entry)
                    if text:
                        widgets.append(Static(text))
                        widgets.append(Static(""))
        return widgets

    def _inline_render(self, entry: Any) -> str:
        if isinstance(entry, str):
            return self._strip_tags(entry)
        if isinstance(entry, dict):
            e_type = entry.get("type")
            if e_type == "list":
                return "\n".join(f"  • {self._inline_render(i)}" for i in entry.get("items", []))
            if e_type in {"entries", "section"}:
                header = entry.get("name")
                body = "\n".join(self._inline_render(e) for e in entry.get("entries", []))
                return f"[bold yellow]{header}[/bold yellow]\n{body}" if header else body
            if "entries" in entry:
                return "\n".join(self._inline_render(e) for e in entry["entries"])
            return str(entry)
        if isinstance(entry, list):
            return "\n".join(self._inline_render(e) for e in entry)
        return str(entry)

    def _format_table(self, table: dict) -> str:
        col_labels = table.get("colLabels", [])
        rows = table.get("rows", [])
        lines = []
        if col_labels:
            lines.append("  ".join(f"[bold]{c}[/bold]" for c in col_labels))
            lines.append("─" * 40)
        for row in rows:
            lines.append("  ".join(str(cell) for cell in row))
        return "\n".join(lines)


    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
