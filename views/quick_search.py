from typing import Any, List, Optional, Tuple

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.timer import Timer
from textual.widgets import Input, Label, ListItem, ListView, Static

from models import Rule, Feat, Item, Monster, Spell
from services import SearchService, SOURCE_SHORT

from .spell_detail import SpellDetailScreen
from .monster_detail import MonsterDetailScreen
from .item_detail import ItemDetailScreen
from .feat_detail import FeatDetailScreen
from .rules import RuleDetailScreen


SHORTCUT_LEGEND = "m: Monsters  •  i: Items  •  s: Spells  •  f: Feats  •  r: Rules"

_PREFIX_MAP = {"m": "monster", "i": "item", "s": "spell", "f": "feat", "r": "rule"}

_CATEGORY_ORDER = ["spell", "monster", "item", "feat", "rule"]

_SCHOOLS = {
    "A": "Abjuration", "C": "Conjuration", "D": "Divination", "E": "Enchantment",
    "V": "Evocation", "I": "Illusion", "N": "Necromancy", "T": "Transmutation",
}


class QuickSearchView(Vertical):
    """Cross-category search with optional type prefix (m:, i:, s:, f:, c:)."""

    def __init__(
        self,
        spells: List[Spell],
        monsters: List[Monster],
        items: List[Item],
        feats: List[Feat],
        rules: List[Rule],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._collections = {
            "spell": spells,
            "monster": monsters,
            "item": items,
            "feat": feats,
            "rule": rules,
        }
        self._results: List[Tuple[str, Any]] = []
        self._search_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Search all… or prefix with  m:  i:  s:  f:  r:",
            id="search",
        )
        yield Static(SHORTCUT_LEGEND, id="shortcuts")
        yield ListView(id="results")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            if self._search_timer is not None:
                self._search_timer.stop()
            self._search_timer = self.set_timer(0.15, lambda: self._perform_search(event.value))

    def _parse_query(self, query: str) -> Tuple[str, str]:
        """Return (category_key, search_term). category_key is '' for all."""
        if ":" in query:
            prefix, _, term = query.partition(":")
            prefix = prefix.strip().lower()
            if prefix in _PREFIX_MAP:
                return _PREFIX_MAP[prefix], term.strip()
        return "", query.strip()

    def _perform_search(self, query: str) -> None:
        category, term = self._parse_query(query)

        if not term:
            self._results = []
            self._update_list()
            return

        targets = {category: self._collections[category]} if category else self._collections

        results: List[Tuple[str, Any]] = []
        for type_key, collection in targets.items():
            for item in SearchService.search(collection, term):
                results.append((type_key, item))

        if not category:
            results.sort(
                key=lambda r: (
                    _CATEGORY_ORDER.index(r[0]) if r[0] in _CATEGORY_ORDER else 99,
                    r[1].name.lower(),
                )
            )

        self._results = results
        self._update_list()

    def _make_label(self, type_key: str, item: Any) -> str:
        src = SOURCE_SHORT.get(item.source, item.source)
        if type_key == "monster":
            return f"[M] {item.name}  •  {item.size_display} {item.type_display}  •  CR {item.cr_display}  •  {src}"
        if type_key == "item":
            return f"[I] {item.name}  •  {item.type_display}  •  {item.rarity_display}  •  {src}"
        if type_key == "spell":
            level = "Cantrip" if item.level == 0 else f"Level {item.level}"
            school = _SCHOOLS.get(item.school, item.school)
            return f"[S] {item.name}  •  {level} {school}  •  {src}"
        if type_key == "feat":
            cat = item.category or "-"
            return f"[F] {item.name}  •  {cat}  •  {src}"
        if type_key == "rule":
            return f"[R] {item.name}  •  {item.type_display}  •  {src}"
        return item.name

    def _update_list(self) -> None:
        from .base import MAX_DISPLAY
        lv = self.query_one("#results", ListView)
        lv.clear()
        display = self._results[:MAX_DISPLAY]
        new_items = [ListItem(Label(self._make_label(type_key, item))) for type_key, item in display]
        if new_items:
            lv.mount(*new_items)

    def reload(self, collections: dict) -> None:
        """Update all data collections when active sources change."""
        self._collections = collections
        self._results = []
        self._update_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.index
        if not (0 <= idx < len(self._results)):
            return
        type_key, item = self._results[idx]
        detail_map = {
            "spell": SpellDetailScreen,
            "monster": MonsterDetailScreen,
            "item": ItemDetailScreen,
            "feat": FeatDetailScreen,
            "rule": RuleDetailScreen,
        }
        if type_key in detail_map:
            self.app.push_screen(detail_map[type_key](item))
