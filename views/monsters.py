from textual.containers import Container, Horizontal
from textual.widgets import Input, Label, ListItem, Select

from services import SearchService, SOURCE_SHORT

from models import Monster
from .base import BaseListView
from .monster_detail import MonsterDetailScreen

CR_OPTIONS = [
    ("All CRs", None),
    ("0", "0"), ("1/8", "1/8"), ("1/4", "1/4"), ("1/2", "1/2"),
    ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"),
    ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"), ("10", "10"),
    ("11", "11"), ("12", "12"), ("13", "13"), ("14", "14"), ("15", "15"),
    ("16", "16"), ("17", "17"), ("18", "18"), ("19", "19"), ("20", "20"),
    ("21", "21"), ("22", "22"), ("23", "23"), ("24", "24"), ("25", "25"),
    ("26", "26"), ("27", "27"), ("28", "28"), ("29", "29"), ("30", "30"),
]

TYPE_OPTIONS = [
    ("All Types", None),
    ("Aberration", "aberration"),
    ("Beast", "beast"),
    ("Celestial", "celestial"),
    ("Construct", "construct"),
    ("Dragon", "dragon"),
    ("Elemental", "elemental"),
    ("Fey", "fey"),
    ("Fiend", "fiend"),
    ("Giant", "giant"),
    ("Humanoid", "humanoid"),
    ("Monstrosity", "monstrosity"),
    ("Ooze", "ooze"),
    ("Plant", "plant"),
    ("Undead", "undead"),
]

SIZE_OPTIONS = [
    ("All Sizes", None),
    ("Tiny", "T"),
    ("Small", "S"),
    ("Medium", "M"),
    ("Large", "L"),
    ("Huge", "H"),
    ("Gargantuan", "G"),
]

SOURCE_OPTIONS = [
    ("All Sources", None),
    ("Monster Manual (2025)", "XMM"),
    ("Bigby Presents: Glory of the Giants", "BGG"),
]


class MonstersView(BaseListView):
    """Monsters list with filters."""

    def render_filters(self) -> Container:
        return Horizontal(
            Select(options=CR_OPTIONS, id="cr_filter", allow_blank=False, value=None),
            Select(options=TYPE_OPTIONS, id="type_filter", allow_blank=False, value=None),
            Select(options=SIZE_OPTIONS, id="size_filter", allow_blank=False, value=None),
            Select(options=SOURCE_OPTIONS, id="source_filter", allow_blank=False, value=None),
            id="filters",
        )

    def create_list_item(self, monster: Monster) -> ListItem:
        ac = self._get_ac(monster)
        hp = monster.hp.get("average", "?")
        source_label = SOURCE_SHORT.get(monster.source, monster.source)
        label = (
            f"{monster.name} • {monster.size_display} {monster.type_display}"
            f" • CR {monster.cr_display} • AC {ac} HP {hp} • {source_label}"
        )
        return ListItem(Label(label))

    def _get_ac(self, monster: Monster) -> str:
        for entry in monster.ac:
            if isinstance(entry, int):
                return str(entry)
            if isinstance(entry, dict):
                return str(entry.get("ac", "?"))
        return "?"

    def _base_types(self, monster: Monster) -> list:
        """Return a list of lowercase type strings for filter matching.

        Handles plain strings, dicts with a 'type' key (string or choose-dict).
        e.g. Empyrean: {"type": {"choose": ["celestial","fiend"]}} → ["celestial","fiend"]
        """
        t = monster.type
        if isinstance(t, str):
            return [t.lower()]
        if isinstance(t, dict):
            inner = t.get("type", "")
            if isinstance(inner, str):
                return [inner.lower()]
            if isinstance(inner, dict):
                return [c.lower() for c in inner.get("choose", [])]
        return []

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered = self.all_items

        source_select = self.query_one("#source_filter", Select)
        if source_select.value is not None and isinstance(source_select.value, str):
            filtered = [m for m in filtered if m.source == source_select.value]

        cr_select = self.query_one("#cr_filter", Select)
        if cr_select.value is not None:
            filtered = [m for m in filtered if m.cr_display == cr_select.value]

        type_select = self.query_one("#type_filter", Select)
        if type_select.value is not None and isinstance(type_select.value, str):
            selected = type_select.value
            filtered = [m for m in filtered if selected in self._base_types(m)]

        size_select = self.query_one("#size_filter", Select)
        if size_select.value is not None:
            filtered = [m for m in filtered if size_select.value in m.size]

        self.items = filtered
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def show_detail(self, monster: Monster) -> None:
        self.app.push_screen(MonsterDetailScreen(monster))
