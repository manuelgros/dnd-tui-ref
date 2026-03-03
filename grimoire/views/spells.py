from textual.containers import Container, Horizontal
from textual.widgets import Checkbox, Input, Label, ListItem, Select

from ..services import SearchService
from ..models import Spell
from .base import BaseListView
from .spell_detail import SpellDetailScreen


class SpellsView(BaseListView):
    """Spells list with filters."""

    result_noun = "Spells"

    def render_filters(self) -> Container:
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
            Select(
                options=[
                    ("Sort: Name", "name"),
                    ("Sort: Level", "level"),
                    ("Sort: School", "school"),
                    ("Sort: Source", "source"),
                ],
                id="sort_filter",
                allow_blank=False,
                value="name",
            ),
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
        tags = []
        if spell.concentration:
            tags.append("C")
        if spell.ritual:
            tags.append("R")
        tag_str = f" [{','.join(tags)}]" if tags else ""
        label = f"{spell.name} • {spell.level_text} {spell.school_full}{tag_str}"
        return ListItem(Label(label))

    def on_select_changed(self, event: Select.Changed) -> None:
        self.apply_filters()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.apply_filters()

    def _has_level_filter(self, value) -> bool:
        return value is not None and isinstance(value, int)

    def _has_school_filter(self, value) -> bool:
        return value is not None and isinstance(value, str)

    def _has_class_filter(self, value) -> bool:
        return value is not None and isinstance(value, str)

    def apply_filters(self) -> None:
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
            pass

        conc_check = self.query_one("#concentration_filter", Checkbox)
        if conc_check.value:
            filtered = [s for s in filtered if s.concentration]

        ritual_check = self.query_one("#ritual_filter", Checkbox)
        if ritual_check.value:
            filtered = [s for s in filtered if s.ritual]

        sort_select = self.query_one("#sort_filter", Select)
        sort_key = sort_select.value or "name"
        if sort_key == "level":
            filtered = sorted(filtered, key=lambda s: (s.level, s.name.lower()))
        elif sort_key == "school":
            filtered = sorted(filtered, key=lambda s: (s.school_full.lower(), s.name.lower()))
        elif sort_key == "source":
            filtered = sorted(filtered, key=lambda s: (s.source.lower(), s.name.lower()))
        else:
            filtered = sorted(filtered, key=lambda s: s.name.lower())

        self.items = filtered
        search_input = self.query_one("#search", Input)
        self.filtered_items = SearchService.search(self.items, search_input.value)
        self.update_results_list()

    def show_detail(self, item: Spell) -> None:
        self.app.push_screen(SpellDetailScreen(item))
