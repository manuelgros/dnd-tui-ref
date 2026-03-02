import re
from typing import Any, List

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, Select, Static

from services import SearchService, SOURCE_FULL
from models import Rule
from .base import BaseListView


class RuleDetailScreen(Screen):
    """Detail screen for a single rule, condition, or disease."""

    def __init__(self, rule: Rule) -> None:
        super().__init__()
        self.rule = rule

    def compose(self) -> ComposeResult:
        r = self.rule
        with Vertical():
            yield Static(f"[bold]{r.name}[/bold]", classes="title")
            yield Static(f"[bold yellow]{r.type_display}[/bold yellow]")
            yield Static("")
            with ScrollableContainer():
                if r.entries:
                    for widget in self._render_entries(r.entries):
                        yield widget
                yield Static(f"\n[dim]Source: {SOURCE_FULL.get(r.source, r.source)}[/dim]")
            yield Button("Back", id="back")

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"\{@condition ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@variantrule ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@action ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        text = re.sub(r"\{@\w+ ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        return text.strip()

    def _render_entries(self, entries: List[Any]) -> List[Static]:
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
                    lines = "\n".join(
                        f"  • {self._strip_tags(str(i))}" for i in entry.get("items", [])
                    )
                    widgets.append(Static(lines))
                    widgets.append(Static(""))
                elif e_type == "table":
                    widgets.append(Static(self._format_table(entry)))
                    widgets.append(Static(""))
                elif e_type in {"entries", "section"}:
                    header = entry.get("name")
                    if header:
                        widgets.append(Static(f"[bold yellow]{header}[/bold yellow]"))
                    for sub in self._render_entries(entry.get("entries", [])):
                        widgets.append(sub)
                else:
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
                return "\n".join(
                    f"  • {self._inline_render(i)}" for i in entry.get("items", [])
                )
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


class RulesView(BaseListView):
    """Rules list with filter for Core Rules, Conditions, and Diseases."""

    result_noun = "Rules"

    def render_filters(self) -> Container:
        return Horizontal(
            Select(
                options=[
                    ("All", None),
                    ("Core Rules", "C"),
                    ("Conditions", "condition"),
                    ("Diseases", "disease"),
                ],
                id="type_filter",
                allow_blank=False,
                value=None,
            ),
            id="filters",
        )

    def create_list_item(self, rule: Rule) -> ListItem:
        return ListItem(Label(f"{rule.name} • {rule.type_display}"))

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered = self.all_items

        type_select = self.query_one("#type_filter", Select)
        if type_select.value is not None:
            filtered = [r for r in filtered if r.rule_type == type_select.value]

        self.items = filtered
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def show_detail(self, rule: Rule) -> None:
        self.app.push_screen(RuleDetailScreen(rule))
