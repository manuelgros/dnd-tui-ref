import re
from typing import Any, List

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from ..models import Item
from ..services import SOURCE_FULL

_LABEL_COLOR = "#5f87ff"

_RARITY_COLORS = {
    "Uncommon":  "#55cc55",
    "Rare":      "#55cccc",
    "Very Rare": "#cc55cc",
    "Legendary": "#ffd700",
    "Artifact":  "#cc5555",
}


class ItemDetailScreen(Screen):
    """Detail screen for a single magic item."""

    def __init__(self, item: Item) -> None:
        super().__init__()
        self.item = item

    def _stat(self, label: str, value: str) -> Static:
        t = Text()
        t.append(label, style=f"bold {_LABEL_COLOR}")
        t.append(f" {value}")
        return Static(t)

    def _rarity_stat(self, rarity: str) -> Static:
        t = Text()
        t.append("Rarity:", style=f"bold {_LABEL_COLOR}")
        t.append(" ")
        color = _RARITY_COLORS.get(rarity)
        t.append(rarity, style=color if color else "")
        return Static(t)

    def compose(self) -> ComposeResult:
        it = self.item
        with Vertical():
            yield Static(f"[bold]{it.name}[/bold]", classes="title")
            yield Static(f"[bold]{it.type_display}[/bold]")
            if it.requires_str:
                yield self._stat("Applies to:", it.requires_str)
            yield self._rarity_stat(it.rarity_display)
            if it.requires_attunement:
                t = Text(it.attunement_display, style="italic")
                yield Static(t)
            if it.weight is not None:
                yield self._stat("Weight:", f"{it.weight} lb.")
            if it.value is not None:
                yield self._stat("Value:", self._format_value(it.value))
            yield Static("")

            with ScrollableContainer():
                if it.entries:
                    yield Static(self._format_entries(it.entries))
                yield Static(f"\n[dim]Source: {SOURCE_FULL.get(it.source, it.source)}[/dim]")

            yield Button("Back", id="back")

    def _format_value(self, value: int) -> str:
        if value >= 100:
            return f"{value // 100} gp"
        if value >= 10:
            return f"{value // 10} sp"
        return f"{value} cp"

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"\{@action ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@item ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@spell ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@creature ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@damage ([^}]+)\}", r"\1", text)
        text = re.sub(r"\{@dice ([^}]+)\}", r"\1", text)
        text = re.sub(r"\{@dc ([^}]+)\}", r"DC \1", text)
        text = re.sub(r"\{@hit ([^}]+)\}", r"+\1", text)
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
                if e_type == "item":
                    name = entry.get("name", "")
                    if "entries" in entry:
                        body = "\n".join(render(e) for e in entry["entries"])
                    else:
                        raw = entry.get("entry", "")
                        body = self._strip_tags(raw) if isinstance(raw, str) else render(raw)
                    return f"[bold]{name}.[/bold] {body}" if name else body
                if e_type in {"entries", "section"}:
                    header = entry.get("name")
                    body = "\n".join(render(e) for e in entry.get("entries", []))
                    return f"[bold]{header}[/bold]\n{body}" if header else body
                if "entries" in entry:
                    return "\n".join(render(e) for e in entry["entries"])
                if "entry" in entry:
                    raw = entry["entry"]
                    return self._strip_tags(raw) if isinstance(raw, str) else render(raw)
                return str(entry)
            if isinstance(entry, list):
                return "\n".join(render(e) for e in entry)
            return str(entry)

        return "\n\n".join(render(e) for e in entries)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
