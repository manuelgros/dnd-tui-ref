import re
from typing import Any, List

from textual import events
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from models import Feat
from services import SOURCE_FULL

CATEGORY_LABELS = {
    "G": "General",
    "O": "Origin",
    "FS": "Fighting Style",
    "FS:P": "Fighting Style (Paladin)",
    "FS:R": "Fighting Style (Ranger)",
    "EB": "Epic Boon",
}

ABILITY_MAP = {
    "str": "Strength", "dex": "Dexterity", "con": "Constitution",
    "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma",
}


class FeatDetailScreen(Screen):
    """Detail screen for a single feat."""

    def __init__(self, feat: Feat) -> None:
        super().__init__()
        self.feat = feat

    def compose(self) -> ComposeResult:
        ft = self.feat
        with Vertical():
            yield Static(f"[bold]{ft.name}[/bold]", classes="title")
            if ft.category:
                yield Static(f"[bold]{CATEGORY_LABELS.get(ft.category, ft.category)}[/bold]")
            if ft.repeatable:
                yield Static("[dim]Repeatable[/dim]")
            if ft.has_prerequisite:
                yield Static(f"[bold]Prerequisite:[/bold] {self._format_prereq(ft.prerequisite)}")
            if ft.ability:
                yield Static(f"[bold]Ability Score Increase:[/bold] {self._format_ability(ft.ability)}")
            yield Static("")

            with ScrollableContainer():
                if ft.entries:
                    yield Static(self._format_entries(ft.entries))
                yield Static(f"\n[dim]Source: {SOURCE_FULL.get(ft.source, ft.source)}[/dim]")

            yield Button("Back", id="back")

    def _format_prereq(self, prereqs: List) -> str:
        parts = []
        for prereq in prereqs:
            for key, val in prereq.items():
                if key == "level":
                    parts.append(f"Level {val}")
                elif key == "ability":
                    for ab in val:
                        for stat, score in ab.items():
                            parts.append(f"{ABILITY_MAP.get(stat, stat.title())} {score}")
                elif key == "race":
                    races = [r.get("name", str(r)) for r in val]
                    parts.append(" or ".join(races))
                elif key == "feature":
                    features = val if isinstance(val, list) else [val]
                    parts.append(", ".join(str(f_) for f_ in features))
                elif key in {"spellcasting", "spellcasting2020"}:
                    if val:
                        parts.append("Spellcasting ability")
                elif key == "feat":
                    feat_names = [f_.split("|")[0].title() for f_ in val]
                    parts.append(", ".join(feat_names) + " feat")
                elif key == "background":
                    bg_names = [b.get("name", str(b)) for b in val]
                    parts.append(" or ".join(bg_names) + " background")
                elif key == "class":
                    class_names = [c.get("name", str(c)) for c in val]
                    parts.append(" or ".join(class_names) + " class")
                elif key == "otherSummary":
                    entry = val.get("entry", str(val)) if isinstance(val, dict) else str(val)
                    parts.append(self._strip_tags(entry))
                elif key == "other":
                    parts.append(str(val))
        return ", ".join(parts) if parts else "None"

    def _format_ability(self, ability: List) -> str:
        parts = []
        for ab in ability:
            for stat, val in ab.items():
                if stat == "choose":
                    count = val.get("count", 1)
                    from_ = val.get("from", [])
                    names = [ABILITY_MAP.get(s, s.title()) for s in from_]
                    parts.append(f"choose {count} from {', '.join(names)}")
                else:
                    parts.append(f"{ABILITY_MAP.get(stat, stat.title())} +{val}")
        return " or ".join(parts)

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"\{@action ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@item ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@spell ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@creature ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@feat ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@skill ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
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
