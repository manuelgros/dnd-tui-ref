import re
from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from models import Spell
from services import SOURCE_FULL


class SpellDetailScreen(Screen):
    """Detail screen for a single spell."""

    def __init__(self, spell: Spell) -> None:
        super().__init__()
        self.spell = spell

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"[bold]{self.spell.name}[/bold]", classes="title")
            yield Static(f"[bold]{self.spell.level_text} {self.spell.school_full}[/bold]")
            yield Static(f"[bold]Casting Time:[/bold] {self.format_time(self.spell.time)}")
            yield Static(f"[bold]Range:[/bold] {self.format_range(self.spell.range)}")
            yield Static(f"[bold]Components:[/bold] {self.format_components(self.spell.components)}")
            yield Static(f"[bold]Duration:[/bold] {self.format_duration(self.spell.duration)}")

            with ScrollableContainer():
                yield Static(self.format_entries(self.spell.entries))

                if self.spell.higher_level:
                    yield Static(self.format_entries(self.spell.higher_level))

                yield Static(
                    f"\n[dim]Classes: {', '.join(self.spell.classes_list)}[/dim]"
                )
                yield Static(f"[dim]Source: {SOURCE_FULL.get(self.spell.source, self.spell.source)}[/dim]")

            yield Button("Back", id="back")

    def format_time(self, time_list: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for t in time_list:
            number = t.get("number", 1)
            unit = t.get("unit", "")
            text = f"{number} {unit}".strip()
            condition = t.get("condition")
            if condition:
                text = f"{text} ({condition})"
            parts.append(text)
        return ", ".join(parts) if parts else "—"

    def format_range(self, range_data: Dict[str, Any]) -> str:
        r_type = range_data.get("type", "point")
        distance = range_data.get("distance", {})
        if isinstance(distance, dict):
            amount = distance.get("amount")
            d_type = distance.get("type", "")
            if amount is not None:
                dist_text = f"{amount} {d_type}".strip()
            else:
                dist_text = d_type
        else:
            dist_text = str(distance)

        if r_type == "self":
            return "Self"
        if r_type == "touch":
            return "Touch"
        if r_type == "sight":
            return "Sight"
        if r_type == "unlimited":
            return "Unlimited"
        if dist_text:
            return dist_text
        return r_type.title()

    def format_components(self, components: Dict[str, Any]) -> str:
        parts: List[str] = []
        if components.get("v"):
            parts.append("V")
        if components.get("s"):
            parts.append("S")

        material = components.get("m")
        if material:
            if isinstance(material, dict):
                mat_text = material.get("text") or ""
            else:
                mat_text = str(material)
            parts.append(f"M ({mat_text})")

        return ", ".join(parts) if parts else "—"

    def format_duration(self, duration_list: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for d in duration_list:
            d_type = d.get("type")
            if d_type == "instant":
                parts.append("Instantaneous")
            elif d_type == "permanent":
                parts.append("Permanent")
            elif d_type == "timed":
                info = d.get("duration", {})
                amount = info.get("amount")
                unit = info.get("type", "")
                text = f"{amount} {unit}".strip() if amount is not None else unit
                if d.get("concentration"):
                    text = f"Concentration, up to {text}"
                parts.append(text)
            else:
                parts.append(d_type or "—")
        return ", ".join(parts) if parts else "—"

    def _strip_tags(self, text: str) -> str:
        # scaledamage: {@scaledamage 2d8|1-9|1d8} → 2d8
        text = re.sub(r"\{@scaledamage ([^|]+)\|[^}]*\}", r"\1", text)
        text = re.sub(r"\{@damage ([^}]+)\}", r"\1", text)
        text = re.sub(r"\{@dice ([^}]+)\}", r"\1", text)
        text = re.sub(r"\{@hit ([^}]+)\}", r"+\1", text)
        text = re.sub(r"\{@dc ([^}]+)\}", r"DC \1", text)
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@spell ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@creature ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@item ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@action ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@skill ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@feat ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@b ([^}]+)\}", r"\1", text)
        text = re.sub(r"\{@i ([^}]+)\}", r"\1", text)
        # Generic fallback
        text = re.sub(r"\{@\w+ ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        return text

    def format_entries(self, entries: List[Any]) -> str:
        """Convert entry objects to formatted text."""

        def render_entry(entry: Any) -> str:
            if isinstance(entry, str):
                return self._strip_tags(entry)
            if isinstance(entry, dict):
                e_type = entry.get("type")
                if e_type == "list":
                    return "\n".join(f"- {render_entry(e)}" for e in entry.get("items", []))
                if e_type in {"entries", "section"}:
                    header = entry.get("name")
                    body = "\n".join(render_entry(e) for e in entry.get("entries", []))
                    if header:
                        return f"[bold]{header}[/bold]\n{body}"
                    return body
                if "entries" in entry:
                    return "\n".join(render_entry(e) for e in entry["entries"])
                return str(entry)
            if isinstance(entry, list):
                return "\n".join(render_entry(e) for e in entry)
            return str(entry)

        return "\n\n".join(render_entry(e) for e in entries)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

