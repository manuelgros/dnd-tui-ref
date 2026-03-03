from typing import Any, List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Checkbox, Input, Label, ListItem, ListView, Select, Static

from ..services import SearchService


MAX_DISPLAY = 100  # cap rendered list items; benchmark shows ~24ms for 100, ~162ms for 575


class BaseListView(Vertical):
    """Base class for all list views (Spells, Monsters, etc.)."""

    result_noun: str = "Results"

    items = reactive(list[Any]())
    filtered_items = reactive(list[Any]())

    def __init__(self, items: List[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.all_items: List[Any] = items
        self.items = items
        self.filtered_items = items
        self._search_timer: Optional[Timer] = None
        self._loaded: bool = False

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search...", id="search")
        yield self.render_filters()
        yield Static("", id="results_count")
        yield ListView(id="results")

    def on_show(self) -> None:
        """Populate the list the first time this tab becomes visible."""
        if not self._loaded:
            self._loaded = True
            self.update_results_list()

    def render_filters(self) -> Container:
        """Override in subclass to add specific filters."""
        return Container()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input with debounce to avoid re-rendering on every keystroke."""
        if event.input.id == "search":
            if self._search_timer is not None:
                self._search_timer.stop()
            self._search_timer = self.set_timer(0.15, lambda: self.perform_search(event.value))

    def perform_search(self, query: str) -> None:
        """Search and update results."""
        self.filtered_items = SearchService.search(self.items, query)
        self.update_results_list()

    def update_results_list(self) -> None:
        """Update the ListView with current filtered_items, capped at MAX_DISPLAY."""
        list_view = self.query_one("#results", ListView)
        list_view.clear()
        total_filtered = len(self.filtered_items)
        display = self.filtered_items[:MAX_DISPLAY]
        new_items = [self.create_list_item(item) for item in display]
        if new_items:
            list_view.mount(*new_items)
        shown = len(display)
        if shown < total_filtered:
            count_text = f"Showing first {shown} of {total_filtered} {self.result_noun} — type to filter"
        elif total_filtered < len(self.all_items):
            count_text = f"{total_filtered} {self.result_noun} found"
        else:
            count_text = f"{self.result_noun}: {total_filtered}"
        self.query_one("#results_count", Static).update(count_text)

    def create_list_item(self, item: Any) -> ListItem:
        """Override in subclass to create item representation."""
        return ListItem(Label(str(item)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection - delegate to subclass detail handler."""
        index = event.index
        if 0 <= index < len(self.filtered_items):
            item = self.filtered_items[index]
            self.show_detail(item)

    def on_key(self, event: events.Key) -> None:
        focused = self.app.focused

        if event.key in ("left", "right"):
            if not isinstance(focused, (Select, Checkbox)):
                return
            if getattr(focused, "_expanded", False):
                return
            filter_widgets = list(self.query("#filters Select, #filters Checkbox"))
            if focused not in filter_widgets:
                return
            idx = filter_widgets.index(focused)
            new_idx = idx + (1 if event.key == "right" else -1)
            if 0 <= new_idx < len(filter_widgets):
                filter_widgets[new_idx].focus()
                event.stop()

        elif event.key == "tab":
            filter_widgets = list(self.query("#filters Select, #filters Checkbox"))
            if isinstance(focused, (Select, Checkbox)) and focused in filter_widgets:
                self.query_one("#results", ListView).focus()
                event.stop()

        elif event.key == "shift+tab":
            filter_widgets = list(self.query("#filters Select, #filters Checkbox"))
            if isinstance(focused, (Select, Checkbox)) and focused in filter_widgets:
                self.query_one("#search", Input).focus()
                event.stop()
            elif isinstance(focused, ListView) and focused.id == "results":
                if filter_widgets:
                    filter_widgets[0].focus()
                    event.stop()

    def apply_filters(self) -> None:
        """Override in subclass to apply specific filters; default just refreshes."""
        self.filtered_items = self.items
        self.update_results_list()

    def reload(self, new_items: List[Any], active_sources: set) -> None:
        """Update the master item list when active sources change."""
        self.all_items = new_items
        self.items = new_items
        self.filtered_items = new_items
        if self._loaded:
            self.apply_filters()

    def show_detail(self, item: Any) -> None:
        """Override in subclass to push a detail screen."""
        return
