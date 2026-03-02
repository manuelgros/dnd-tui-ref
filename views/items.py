from textual.containers import Container, Horizontal
from textual.widgets import Checkbox, Input, Label, ListItem, Select

from services import SearchService, SOURCE_SHORT, SOURCE_OPTIONS as _SOURCE_OPTIONS

from models import Item
from .base import BaseListView
from .item_detail import ItemDetailScreen


TYPE_OPTIONS = [
    ("All Types", None),
    ("Weapon", "weapon"),
    ("Armor", "armor"),
    ("Shield", "shield"),
    ("Wondrous", "wondrous"),
    ("Potion", "potion"),
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

SOURCE_OPTIONS = _SOURCE_OPTIONS


class ItemsView(BaseListView):
    """Items list with filters."""

    result_noun = "Items"

    def render_filters(self) -> Container:
        return Horizontal(
            Select(options=TYPE_OPTIONS, id="type_filter", allow_blank=False, value=None),
            Select(options=RARITY_OPTIONS, id="rarity_filter", allow_blank=False, value=None),
            Select(options=SOURCE_OPTIONS, id="source_filter", allow_blank=False, value=None),
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

    def show_detail(self, item: Item) -> None:
        self.app.push_screen(ItemDetailScreen(item))
