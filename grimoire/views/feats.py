from typing import Any, List, Set

from textual.containers import Container, Horizontal
from textual.widgets import Input, Label, ListItem, Select

from ..services import SearchService, SOURCE_SHORT
from ..models import Feat
from .base import BaseListView
from .feat_detail import FeatDetailScreen


CATEGORY_OPTIONS = [
    ("All Categories", None),
    ("General", "G"),
    ("Origin", "O"),
    ("Fighting Style", "FS"),
    ("Epic Boon", "EB"),
    ("No Category", "none"),
]

# All possible feat sources (without the "All" header)
_FEAT_SOURCE_OPTIONS: List[tuple] = [
    ("Player's Handbook (2024)", "XPHB"),
    ("Xanathar's Guide to Everything", "XGE"),
    ("Tasha's Cauldron of Everything", "TCE"),
    ("Bigby Presents: Glory of the Giants", "BGG"),
]


def _build_source_opts(active_sources: Set[str]) -> list:
    return [("All Sources", None)] + [
        (label, code) for label, code in _FEAT_SOURCE_OPTIONS
        if code in active_sources
    ]


class FeatsView(BaseListView):
    """Feats list with filters."""

    result_noun = "Feats"

    def __init__(self, items: List[Any], active_sources: Set[str] = frozenset(), **kwargs: Any) -> None:
        super().__init__(items, **kwargs)
        self._active_sources = set(active_sources)

    def render_filters(self) -> Container:
        return Horizontal(
            Select(options=CATEGORY_OPTIONS, id="category_filter", allow_blank=False, value=None),
            Select(
                options=_build_source_opts(self._active_sources),
                id="source_filter",
                allow_blank=False,
                value=None,
            ),
            id="filters",
        )

    def create_list_item(self, feat: Feat) -> ListItem:
        cat = feat.category or "-"
        source = SOURCE_SHORT.get(feat.source, feat.source)
        return ListItem(Label(f"{feat.name} • {cat} • {source}"))

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def apply_filters(self) -> None:
        filtered = self.all_items

        source_select = self.query_one("#source_filter", Select)
        if source_select.value is not None:
            filtered = [f for f in filtered if f.source == source_select.value]

        cat_select = self.query_one("#category_filter", Select)
        if cat_select.value is not None:
            val = cat_select.value
            if val == "FS":
                filtered = [f for f in filtered if f.category and f.category.startswith("FS")]
            elif val == "none":
                filtered = [f for f in filtered if not f.category]
            else:
                filtered = [f for f in filtered if f.category == val]

        self.items = filtered
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def reload(self, new_items: List[Any], active_sources: Set[str]) -> None:
        self._active_sources = set(active_sources)
        self.all_items = new_items
        self.items = new_items
        self.filtered_items = new_items
        opts = _build_source_opts(active_sources)
        source_select = self.query_one("#source_filter", Select)
        source_select.set_options(opts)
        if source_select.value not in active_sources:
            source_select.value = None
        if self._loaded:
            self.apply_filters()

    def show_detail(self, feat: Feat) -> None:
        self.app.push_screen(FeatDetailScreen(feat))
