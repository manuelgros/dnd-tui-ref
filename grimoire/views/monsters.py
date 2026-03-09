from typing import Any, List, Set

from textual.containers import Container, Horizontal
from textual.widgets import Input, Label, ListItem, Select

from ..services import SearchService, SOURCE_FULL, SOURCE_SHORT
from ..models import Monster, cr_to_float
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

ENVIRONMENT_OPTIONS = [
    ("All Environments", None),
    ("Any", "any"),
    ("Arctic", "arctic"),
    ("Coastal", "coastal"),
    ("Desert", "desert"),
    ("Forest", "forest"),
    ("Grassland", "grassland"),
    ("Hill", "hill"),
    ("Mountain", "mountain"),
    ("Swamp", "swamp"),
    ("Underdark", "underdark"),
    ("Underwater", "underwater"),
    ("Urban", "urban"),
    ("Planar: Abyss", "planar, abyss"),
    ("Planar: Acheron", "planar, acheron"),
    ("Planar: Air", "planar, air"),
    ("Planar: Astral", "planar, astral"),
    ("Planar: Earth", "planar, earth"),
    ("Planar: Elemental", "planar, elemental"),
    ("Planar: Feywild", "planar, feywild"),
    ("Planar: Fire", "planar, fire"),
    ("Planar: Limbo", "planar, limbo"),
    ("Planar: Lower", "planar, lower"),
    ("Planar: Nine Hells", "planar, nine hells"),
    ("Planar: Shadowfell", "planar, shadowfell"),
    ("Planar: Upper", "planar, upper"),
]

def _build_source_opts(items: List[Any], active_sources: Set[str]) -> list:
    from ..config import get_custom_sources
    present = {m.source for m in items}
    all_sources = {**SOURCE_FULL, **get_custom_sources()}
    return [("All Sources", None)] + [
        (title, code)
        for code, title in all_sources.items()
        if code in active_sources and code in present
    ]


class MonstersView(BaseListView):
    """Monsters list with filters."""

    result_noun = "Monsters"

    def __init__(self, items: List[Any], active_sources: Set[str] = frozenset(), **kwargs: Any) -> None:
        super().__init__(items, **kwargs)
        self._active_sources = set(active_sources)

    def render_filters(self) -> Container:
        return Horizontal(
            Select(options=CR_OPTIONS, id="cr_filter", allow_blank=False, value=None),
            Select(options=TYPE_OPTIONS, id="type_filter", allow_blank=False, value=None),
            Select(options=ENVIRONMENT_OPTIONS, id="env_filter", allow_blank=False, value=None),
            Select(
                options=_build_source_opts(self.all_items, self._active_sources),
                id="source_filter",
                allow_blank=False,
                value=None,
            ),
            Select(
                options=[
                    ("Sort: Name", "name"),
                    ("Sort: CR", "cr"),
                    ("Sort: Type", "type"),
                    ("Sort: Source", "source"),
                ],
                id="sort_filter",
                allow_blank=False,
                value="name",
            ),
            id="filters",
        )

    def create_list_item(self, monster: Monster) -> ListItem:
        ac = self._get_ac(monster)
        special = monster.hp.get("special")
        if special is not None:
            hp = special if str(special).isdigit() else "?"
        else:
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
        t = monster.type
        if isinstance(t, str):
            return [t.lower()]
        if isinstance(t, dict):
            inner = t.get("type", "")
            if isinstance(inner, str):
                types = [inner.lower()]
            elif isinstance(inner, dict):
                types = [c.lower() for c in inner.get("choose", [])]
            else:
                types = []
            tags = [tag.lower() for tag in t.get("tags", [])]
            return types + tags
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

        env_select = self.query_one("#env_filter", Select)
        if env_select.value is not None and isinstance(env_select.value, str):
            selected_env = env_select.value
            filtered = [m for m in filtered if m.environment and selected_env in m.environment]

        sort_select = self.query_one("#sort_filter", Select)
        sort_key = sort_select.value or "name"
        if sort_key == "cr":
            def _cr_key(m: Monster):
                cr = m.cr_display
                try:
                    return (cr_to_float(cr), m.name.lower())
                except (ValueError, ZeroDivisionError):
                    return (float("inf"), m.name.lower())
            filtered = sorted(filtered, key=_cr_key)
        elif sort_key == "type":
            filtered = sorted(filtered, key=lambda m: (m.type_display.lower(), m.name.lower()))
        elif sort_key == "source":
            filtered = sorted(filtered, key=lambda m: (m.source.lower(), m.name.lower()))
        else:
            filtered = sorted(filtered, key=lambda m: m.name.lower())

        self.items = filtered
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def reload(self, new_items: List[Any], active_sources: Set[str]) -> None:
        self._active_sources = set(active_sources)
        self.all_items = new_items
        self.items = new_items
        self.filtered_items = new_items
        opts = _build_source_opts(new_items, active_sources)
        source_select = self.query_one("#source_filter", Select)
        source_select.set_options(opts)
        if source_select.value not in active_sources:
            source_select.value = None
        if self._loaded:
            self.apply_filters()

    def show_detail(self, monster: Monster) -> None:
        self.app.push_screen(MonsterDetailScreen(monster))
