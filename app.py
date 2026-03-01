from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Input, Static, TabbedContent, TabPane

from services import DataLoader
from views import SpellsView, MonstersView, ItemsView


class DnDReferenceApp(App):
    """D&D 5E Reference TUI."""

    TITLE = "D&D 5E Reference"
    CSS_PATH = "styles.css"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+1", "switch_tab('spells')", "Spells", show=False),
        Binding("ctrl+2", "switch_tab('monsters')", "Monsters", show=False),
        Binding("ctrl+3", "switch_tab('items')", "Items", show=False),
        Binding("ctrl+4", "switch_tab('feats')", "Feats", show=False),
        Binding("ctrl+5", "switch_tab('conditions')", "Conditions", show=False),
        Binding("/", "focus_search", "Search", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.data_loader = DataLoader(Path("data"))

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="spells"):
            with TabPane("Spells", id="spells"):
                yield SpellsView(self.data_loader.spells)
            with TabPane("Monsters", id="monsters"):
                yield MonstersView(self.data_loader.monsters)
            with TabPane("Items", id="items"):
                yield ItemsView(self.data_loader.items)
            with TabPane("Feats", id="feats"):
                yield Static("Feats View Coming Soon")
            with TabPane("Conditions", id="conditions"):
                yield Static("Conditions View Coming Soon")
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to specified tab."""
        self.query_one(TabbedContent).active = tab_id

    def action_focus_search(self) -> None:
        """Focus the search input in current tab (currently spells only)."""
        tabbed = self.query_one(TabbedContent)
        if tabbed.active == "spells":
            pane = tabbed.get_pane("spells")
            try:
                search = pane.query_one("#search", Input)
            except Exception:
                return
            search.focus()


