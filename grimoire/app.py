from pathlib import Path
from typing import List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Input, TabbedContent, TabPane

from .services import DataLoader
from .views import SpellsView, MonstersView, ItemsView, FeatsView, RulesView, QuickSearchView, SettingsView
from .views.settings import DEFAULT_ACTIVE_SOURCES


class GrimoireApp(App):
    """Grimoire 5e — D&D 5th Edition Reference TUI."""

    TITLE = "Grimoire 5e"
    CSS_PATH = str(Path(__file__).parent / "styles.css")

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+1", "switch_tab('quick')", "Quick Search", show=False),
        Binding("ctrl+2", "switch_tab('spells')", "Spells", show=False),
        Binding("ctrl+3", "switch_tab('monsters')", "Monsters", show=False),
        Binding("ctrl+4", "switch_tab('items')", "Items", show=False),
        Binding("ctrl+5", "switch_tab('feats')", "Feats", show=False),
        Binding("ctrl+6", "switch_tab('rules')", "Rules", show=False),
        Binding("ctrl+7", "switch_tab('settings')", "Settings", show=False),
        Binding("/", "focus_search", "Search", show=True),
        Binding("escape", "quick_search", "Quick Search", show=False),
    ]

    def __init__(self, data_dir: Path) -> None:
        super().__init__()
        self.data_loader = DataLoader(data_dir)
        self.active_sources: set = set(DEFAULT_ACTIVE_SOURCES)

    def _filter(self, items: List) -> List:
        """Return only items whose source is currently active."""
        return [item for item in items if item.source in self.active_sources]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="quick"):
            with TabPane("Quick Search", id="quick"):
                yield QuickSearchView(
                    spells=self._filter(self.data_loader.spells),
                    monsters=self._filter(self.data_loader.monsters),
                    items=self._filter(self.data_loader.items),
                    feats=self._filter(self.data_loader.feats),
                    rules=self._filter(self.data_loader.rules),
                )
            with TabPane("Spells", id="spells"):
                yield SpellsView(self._filter(self.data_loader.spells))
            with TabPane("Monsters", id="monsters"):
                yield MonstersView(
                    self._filter(self.data_loader.monsters),
                    active_sources=self.active_sources,
                )
            with TabPane("Items", id="items"):
                yield ItemsView(
                    self._filter(self.data_loader.items),
                    active_sources=self.active_sources,
                )
            with TabPane("Feats", id="feats"):
                yield FeatsView(
                    self._filter(self.data_loader.feats),
                    active_sources=self.active_sources,
                )
            with TabPane("Rules", id="rules"):
                yield RulesView(self._filter(self.data_loader.rules))
            with TabPane("Settings", id="settings"):
                yield SettingsView()
        yield Footer()

    def on_settings_view_sources_changed(self, event: SettingsView.SourcesChanged) -> None:
        """Reload all views whenever the user toggles a source in Settings."""
        self.active_sources = event.active_sources

        spells = self._filter(self.data_loader.spells)
        monsters = self._filter(self.data_loader.monsters)
        items = self._filter(self.data_loader.items)
        feats = self._filter(self.data_loader.feats)
        rules = self._filter(self.data_loader.rules)

        self.query_one(SpellsView).reload(spells, self.active_sources)
        self.query_one(MonstersView).reload(monsters, self.active_sources)
        self.query_one(ItemsView).reload(items, self.active_sources)
        self.query_one(FeatsView).reload(feats, self.active_sources)
        self.query_one(RulesView).reload(rules, self.active_sources)
        self.query_one(QuickSearchView).reload({
            "spell": spells,
            "monster": monsters,
            "item": items,
            "feat": feats,
            "rule": rules,
        })

    def action_quick_search(self) -> None:
        """Switch to Quick Search and focus the search input."""
        self.query_one(TabbedContent).active = "quick"
        try:
            self.query_one(QuickSearchView).query_one("#search", Input).focus()
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to specified tab."""
        self.query_one(TabbedContent).active = tab_id

    def action_focus_search(self) -> None:
        """Focus the search input in current tab."""
        tabbed = self.query_one(TabbedContent)
        try:
            pane = tabbed.get_pane(tabbed.active)
            pane.query_one("#search", Input).focus()
        except Exception:
            pass
