from textual.containers import Container, Horizontal
from textual.widgets import Checkbox, Input, Label, ListItem, Select

from services import SearchService

from models import Spell
from .base import BaseListView
from .spell_detail import SpellDetailScreen


class SpellsView(BaseListView):
    """Spells list with filters."""

    result_noun = "Spells"
    def render_filters(self) -> Container:
        # Only show class filter if spell data includes class info
        has_class_data = any(s.classes_list for s in self.all_items)

        filters: list = [
            Select(
                options=[("All Levels", None)]
                + [(f"Level {i}", i) for i in range(10)],
                id="level_filter",
                allow_blank=False,
                value=None,
            ),
            Select(
                options=[
                    ("All Schools", None),
                    ("Abjuration", "A"),
                    ("Conjuration", "C"),
                    ("Divination", "D"),
                    ("Enchantment", "E"),
                    ("Evocation", "V"),
                    ("Illusion", "I"),
                    ("Necromancy", "N"),
                    ("Transmutation", "T"),
                ],
                id="school_filter",
                allow_blank=False,
                value=None,
            ),
            Checkbox("Concentration", id="concentration_filter"),
            Checkbox("Ritual", id="ritual_filter"),
        ]
        if has_class_data:
            filters.insert(
                2,
                Select(
                    options=[
                        ("All Classes", None),
                        ("Bard", "Bard"),
                        ("Cleric", "Cleric"),
                        ("Druid", "Druid"),
                        ("Paladin", "Paladin"),
                        ("Ranger", "Ranger"),
                        ("Sorcerer", "Sorcerer"),
                        ("Warlock", "Warlock"),
                        ("Wizard", "Wizard"),
                    ],
                    id="class_filter",
                    allow_blank=False,
                    value=None,
                ),
            )
        return Horizontal(*filters, id="filters")

    def create_list_item(self, spell: Spell) -> ListItem:
        """Create spell list item with formatted display."""
        tags = []
        if spell.concentration:
            tags.append("C")
        if spell.ritual:
            tags.append("R")
        tag_str = f" [{','.join(tags)}]" if tags else ""

        label = f"{spell.name} • {spell.level_text} {spell.school_full}{tag_str}"
        return ListItem(Label(label))

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter changes."""
        self.apply_filters()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox filter changes."""
        self.apply_filters()

    def _has_level_filter(self, value) -> bool:
        """True if value is a concrete level choice (0-9), not 'All Levels'."""
        return value is not None and isinstance(value, int)

    def _has_school_filter(self, value) -> bool:
        """True if value is a school code, not 'All Schools'."""
        return value is not None and isinstance(value, str)

    def _has_class_filter(self, value) -> bool:
        """True if value is a class name, not 'All Classes'."""
        return value is not None and isinstance(value, str)

    def apply_filters(self) -> None:
        """Apply all active filters."""
        filtered = self.all_items

        level_select = self.query_one("#level_filter", Select)
        if self._has_level_filter(level_select.value):
            filtered = [s for s in filtered if s.level == level_select.value]

        school_select = self.query_one("#school_filter", Select)
        if self._has_school_filter(school_select.value):
            filtered = [s for s in filtered if s.school == school_select.value]

        try:
            class_select = self.query_one("#class_filter", Select)
            if self._has_class_filter(class_select.value):
                filtered = [
                    s for s in filtered if class_select.value in s.classes_list
                ]
        except Exception:
            pass  # Class filter not rendered when data has no class info

        conc_check = self.query_one("#concentration_filter", Checkbox)
        if conc_check.value:
            filtered = [s for s in filtered if s.concentration]

        ritual_check = self.query_one("#ritual_filter", Checkbox)
        if ritual_check.value:
            filtered = [s for s in filtered if s.ritual]

        self.items = filtered
        # Apply current search on the filtered list so list shows filter + search
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def show_detail(self, item: Spell) -> None:
        """Open the spell detail screen."""
        self.app.push_screen(SpellDetailScreen(item))

