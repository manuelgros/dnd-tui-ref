from typing import Any, List, Set

from textual.containers import Container, Horizontal
from textual.widgets import Checkbox, Input, Label, ListItem, Select

from ..services import SearchService, SOURCE_FULL, SOURCE_SHORT
from ..models import Item
from .base import BaseListView
from .item_detail import ItemDetailScreen


TYPE_OPTIONS = [
    ("All Types", None),
    ("Weapon", "weapon"),
    ("Armor", "armor"),
    ("Shield", "shield"),
    ("Wondrous", "wondrous"),
    ("Potion", "potion"),
    ("Poison", "poison"),
    ("Scroll", "scroll"),
    ("Rod", "rod"),
    ("Ring", "ring"),
    ("Wand", "wand"),
    ("Spellcasting Focus", "focus"),
    ("Instrument", "instrument"),
    ("Adventuring Gear", "gear"),
]

RARITY_OPTIONS = [
    ("All Rarities", None),
    ("Common", "common"),
    ("Uncommon", "uncommon"),
    ("Rare", "rare"),
    ("Very Rare", "very rare"),
    ("Legendary", "legendary"),
    ("Artifact", "artifact"),
]

def _build_source_opts(items: List[Any], active_sources: Set[str]) -> list:
    from ..config import get_custom_sources
    present = {i.source for i in items}
    all_sources = {**SOURCE_FULL, **get_custom_sources()}
    return [("All Sources", None)] + [
        (title, code)
        for code, title in all_sources.items()
        if code in active_sources and code in present
    ]


class ItemsView(BaseListView):
    """Items list with filters."""

    result_noun = "Items"

    def __init__(self, items: List[Any], active_sources: Set[str] = frozenset(), **kwargs: Any) -> None:
        super().__init__(items, **kwargs)
        self._active_sources = set(active_sources)

    def render_filters(self) -> Container:
        return Horizontal(
            Select(options=TYPE_OPTIONS, id="type_filter", allow_blank=False, value=None),
            Select(options=RARITY_OPTIONS, id="rarity_filter", allow_blank=False, value=None),
            Select(
                options=_build_source_opts(self.all_items, self._active_sources),
                id="source_filter",
                allow_blank=False,
                value=None,
            ),
            Checkbox("Attunement", id="attune_filter"),
            id="filters",
        )

    def create_list_item(self, item: Item) -> ListItem:
        parts = [item.name, item.type_display, item.rarity_display]
        if item.requires_attunement:
            parts.append("Requires Attunement")
        parts.append(SOURCE_SHORT.get(item.source, item.source))
        return ListItem(Label(" • ".join(parts)))

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered = self.all_items

        type_select = self.query_one("#type_filter", Select)
        if type_select.value is not None:
            filtered = [i for i in filtered if i.category == type_select.value]

        rarity_select = self.query_one("#rarity_filter", Select)
        if rarity_select.value is not None:
            filtered = [i for i in filtered if i.rarity == rarity_select.value]

        source_select = self.query_one("#source_filter", Select)
        if source_select.value is not None:
            filtered = [i for i in filtered if i.source == source_select.value]

        attune_check = self.query_one("#attune_filter", Checkbox)
        if attune_check.value:
            filtered = [i for i in filtered if i.requires_attunement]

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

    def show_detail(self, item: Item) -> None:
        self.app.push_screen(ItemDetailScreen(item))
