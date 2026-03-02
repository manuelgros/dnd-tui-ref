import re
from typing import Any, List

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from models import Item
from services import SOURCE_FULL


class ItemDetailScreen(Screen):
    """Detail screen for a single magic item."""

    def __init__(self, item: Item) -> None:
        super().__init__()
        self.item = item

    _RARITY_COLORS = {
        "Uncommon": "green", "Rare": "cyan",
        "Very Rare": "magenta", "Legendary": "gold1", "Artifact": "red",
    }

    def _rarity_colored(self, rarity: str) -> str:
        color = self._RARITY_COLORS.get(rarity)
        return f"[{color}]{rarity}[/{color}]" if color else rarity

    def compose(self) -> ComposeResult:
        it = self.item
        with Vertical():
            yield Static(f"[bold]{it.name}[/bold]", classes="title")
            yield Static(f"[bold]{it.type_display}[/bold]")
            if it.requires_str:
                yield Static(f"[bold]Applies to:[/bold] {it.requires_str}")
            yield Static(f"[bold]Rarity:[/bold] {self._rarity_colored(it.rarity_display)}")
            if it.requires_attunement:
                yield Static(f"[italic]{it.attunement_display}[/italic]")
            if it.weight is not None:
                yield Static(f"[bold]Weight:[/bold] {it.weight} lb.")
            if it.value is not None:
                yield Static(f"[bold]Value:[/bold] {self._format_value(it.value)}")
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
        # Generic fallback
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
