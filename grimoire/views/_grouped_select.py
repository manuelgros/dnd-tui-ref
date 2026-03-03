"""GroupedSelect: a Select subclass that renders labelled group headers."""

from __future__ import annotations

from textual import on
from textual.widgets import Select
from textual.widgets._select import NULL, SelectCurrent, SelectOverlay
from textual.widgets._option_list import Option
from rich.text import Text


class GroupedSelect(Select):
    """A Select that shows disabled group-header entries between option groups.

    Args:
        groups: list of (group_label, [(display, value), ...]) tuples.
                The flat option list passed to Select is derived from these;
                the group labels are rendered as disabled, unselectable entries.
    """

    def __init__(self, groups: list[tuple[str, list[tuple]]], **kwargs) -> None:
        flat = [(display, value) for _, opts in groups for display, value in opts]
        super().__init__(flat, **kwargs)
        self._groups = groups
        # Populated by _setup_options_renderables:
        self._overlay_to_flat: dict[int, int] = {}  # overlay idx → self._options idx
        self._flat_to_overlay: dict[int, int] = {}  # self._options idx → overlay idx

    # ------------------------------------------------------------------
    # Build the OptionList with group headers injected
    # ------------------------------------------------------------------

    def _setup_options_renderables(self) -> None:
        options: list[Option] = []
        self._overlay_to_flat = {}
        self._flat_to_overlay = {}
        ov_idx = 0
        flat_idx = 0

        # Blank option (only present when allow_blank=True)
        if self._allow_blank:
            options.append(Option(Text(self.prompt, style="dim")))
            self._overlay_to_flat[ov_idx] = flat_idx
            self._flat_to_overlay[flat_idx] = ov_idx
            ov_idx += 1
            flat_idx += 1

        for group_label, group_opts in self._groups:
            # Disabled, unselectable group header
            header = Text()
            header.append(f" {group_label} ", style="bold dim")
            options.append(Option(header, disabled=True))
            ov_idx += 1  # no flat mapping — this entry cannot be selected

            for display, _value in group_opts:
                options.append(Option(display))
                self._overlay_to_flat[ov_idx] = flat_idx
                self._flat_to_overlay[flat_idx] = ov_idx
                ov_idx += 1
                flat_idx += 1

        overlay = self.query_one(SelectOverlay)
        overlay.clear_options()
        overlay.add_options(options)

    # ------------------------------------------------------------------
    # Patch event.option_index before the parent's _update_selection runs.
    # The parent uses self._options[event.option_index] which assumes no
    # headers in the OptionList. We remap overlay idx → flat idx here.
    # Our @on handler fires first (MRO order: most-derived → least-derived).
    # ------------------------------------------------------------------

    @on(SelectOverlay.UpdateSelection)
    def _remap_option_index(self, event: SelectOverlay.UpdateSelection) -> None:
        flat_idx = self._overlay_to_flat.get(event.option_index)
        if flat_idx is not None:
            event.option_index = flat_idx

    # ------------------------------------------------------------------
    # Override reactive watchers to use flat→overlay index mapping
    # ------------------------------------------------------------------

    def _watch_value(self, value) -> None:
        """Mirror parent, but map flat idx → overlay idx for highlighting."""
        self._value = value
        try:
            select_current = self.query_one(SelectCurrent)
        except Exception:
            return
        if value == NULL:
            select_current.update(NULL)
        else:
            for flat_idx, (prompt, _value) in enumerate(self._options):
                if _value == value:
                    ov_idx = self._flat_to_overlay.get(flat_idx)
                    if ov_idx is not None:
                        try:
                            self.query_one(SelectOverlay).highlighted = ov_idx
                        except Exception:
                            pass
                    select_current.update(prompt)
                    break
        self.post_message(self.Changed(self, value))

    def _watch_expanded(self, expanded: bool) -> None:
        """Mirror parent, but map flat idx → overlay idx for overlay.select()."""
        try:
            overlay = self.query_one(SelectOverlay)
        except Exception:
            return
        self.set_class(expanded, "-expanded")
        if expanded:
            overlay.focus(scroll_visible=False)
            if self.value is NULL:
                overlay.select(None)
                self.query_one(SelectCurrent).has_value = False
            else:
                value = self.value
                for flat_idx, (_prompt, prompt_value) in enumerate(self._options):
                    if value == prompt_value:
                        ov_idx = self._flat_to_overlay.get(flat_idx)
                        if ov_idx is not None:
                            overlay.select(ov_idx)
                        break
                self.query_one(SelectCurrent).has_value = True
