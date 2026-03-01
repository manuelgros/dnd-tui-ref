from typing import Any, List

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Checkbox, Input, Label, ListItem, ListView, Select

from services import SearchService


class BaseListView(Vertical):
    """Base class for all list views (Spells, Monsters, etc.)."""

    items = reactive(list[Any]())
    filtered_items = reactive(list[Any]())

    def __init__(self, items: List[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.all_items: List[Any] = items
        self.items = items
        self.filtered_items = items

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search...", id="search")
        yield self.render_filters()
        yield ListView(id="results")

    def on_mount(self) -> None:
        """Populate the list when the view is shown."""
        self.update_results_list()

    def render_filters(self) -> Container:
        """Override in subclass to add specific filters."""
        return Container()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input."""
        if event.input.id == "search":
            self.perform_search(event.value)

    def perform_search(self, query: str) -> None:
        """Search and update results."""
        self.filtered_items = SearchService.search(self.items, query)
        self.update_results_list()

    def update_results_list(self) -> None:
        """Update the ListView with current filtered_items."""
        list_view = self.query_one("#results", ListView)
        list_view.clear()
        for item in self.filtered_items:
            list_view.append(self.create_list_item(item))

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
        """Navigate between filter Selects with left/right arrow keys."""
        if event.key not in ("left", "right"):
            return
        focused = self.app.focused
        if not isinstance(focused, (Select, Checkbox)):
            return
        if getattr(focused, "_expanded", False):
            return  # let the open dropdown handle its own arrow keys
        filter_widgets = list(self.query("#filters Select, #filters Checkbox"))
        if focused not in filter_widgets:
            return
        idx = filter_widgets.index(focused)
        new_idx = idx + (1 if event.key == "right" else -1)
        if 0 <= new_idx < len(filter_widgets):
            filter_widgets[new_idx].focus()
            event.stop()

    def show_detail(self, item: Any) -> None:
        """Override in subclass to push a detail screen."""
        # Default implementation does nothing.
        return

