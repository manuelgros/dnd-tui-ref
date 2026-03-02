import re
from typing import Any, Dict, Generator, List, Tuple

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from models import Monster
from services import SOURCE_FULL

_STAT_COLOR = "#5f87ff"  # medium blue for stat block property labels

_ATK_MAP = {
    "m":     "Melee Attack",
    "mw":    "Melee Weapon Attack",
    "rw":    "Ranged Weapon Attack",
    "ms":    "Melee Spell Attack",
    "rs":    "Ranged Spell Attack",
    "mp":    "Melee Power Attack",
    "rp":    "Ranged Power Attack",
    "mw,rw": "Melee or Ranged Weapon Attack",
    "ms,rs": "Melee or Ranged Spell Attack",
    "mp,rp": "Melee or Ranged Power Attack",
}

_ATKR_MAP = {
    "m":   "Melee Attack Roll",
    "r":   "Ranged Attack Roll",
    "m,r": "Melee or Ranged Attack Roll",
}

# Section display order and labels
_SECTIONS: List[Tuple[str, str]] = [
    ("trait",     "Traits"),
    ("action",    "Actions"),
    ("bonus",     "Bonus Actions"),
    ("reaction",  "Reactions"),
    ("legendary", "Legendary Actions"),
]


class MonsterDetailScreen(Screen):
    """Detail screen for a single monster stat block."""

    def __init__(self, monster: Monster) -> None:
        super().__init__()
        self.monster = monster

    def _stat(self, label: str, value: str) -> Static:
        """A property row with a colored bold label and plain value."""
        t = Text()
        t.append(label, style=f"bold {_STAT_COLOR}")
        t.append(f" {value}")
        return Static(t)

    def compose(self) -> ComposeResult:
        m = self.monster
        with Vertical():
            yield Static(f"[bold]{m.name}[/bold]", classes="title")
            yield Static(
                f"{m.size_display} {m.type_display}, {self._format_alignment(m.alignment)}"
            )
            yield Static("")
            yield self._stat("Armor Class", self._format_ac(m.ac))
            yield self._stat("Hit Points", self._format_hp(m.hp))
            yield self._stat("Speed", self._format_speed(m.speed))
            yield Static("")
            yield Static(self._format_ability_scores(m))
            yield Static("")

            with ScrollableContainer():
                if m.save:
                    yield self._stat("Saving Throws", self._format_kv(m.save))
                if m.skill:
                    yield self._stat("Skills", self._format_kv(m.skill))
                if m.vulnerable:
                    yield self._stat("Damage Vulnerabilities", self._format_resist_immune(m.vulnerable))
                if m.resist:
                    yield self._stat("Damage Resistances", self._format_resist_immune(m.resist))
                if m.immune:
                    yield self._stat("Damage Immunities", self._format_resist_immune(m.immune))
                if m.conditionImmune:
                    yield self._stat("Condition Immunities", self._format_resist_immune(m.conditionImmune))
                if m.senses:
                    yield self._stat("Senses", ", ".join(m.senses))
                if m.languages:
                    yield self._stat("Languages", ", ".join(m.languages))
                yield self._stat("Challenge", m.cr_display)
                yield Static("")

                for section_label, items in self._build_sections(m):
                    yield Static(f"[bold yellow]{section_label}[/bold yellow]")
                    for text in items:
                        yield Static(text)
                        yield Static("")

                grp = m.legendary_group_data or {}
                for grp_key, grp_label in [
                    ("lairActions",    "Lair Actions"),
                    ("regionalEffects", "Regional Effects"),
                ]:
                    entries = grp.get(grp_key)
                    if entries:
                        yield Static(f"[bold yellow]{grp_label}[/bold yellow]")
                        yield Static(self._format_entries(entries))
                        yield Static("")

                yield Static(f"[dim]Source: {SOURCE_FULL.get(m.source, m.source)}[/dim]")

            yield Button("Back", id="back")

    # ── Section builder ────────────────────────────────────────────────────────

    def _build_sections(
        self, m: Monster
    ) -> Generator[Tuple[str, List[str]], None, None]:
        """Yield (label, [rendered_text]) for each populated section."""
        buckets: Dict[str, List[str]] = {key: [] for key, _ in _SECTIONS}

        # Spellcasting entries slot into whichever section their displayAs names
        for sc in m.spellcasting or []:
            display_as = sc.get("displayAs", "action")
            if display_as in buckets:
                buckets[display_as].append(self._format_spellcasting(sc))

        # Regular feature lists
        for feat in m.trait or []:
            buckets["trait"].append(self._format_feature(feat))
        for feat in m.action or []:
            buckets["action"].append(self._format_feature(feat))
        for feat in m.bonus or []:
            buckets["bonus"].append(self._format_feature(feat))
        for feat in m.reaction or []:
            buckets["reaction"].append(self._format_feature(feat))
        for feat in m.legendary or []:
            buckets["legendary"].append(self._format_feature(feat))

        for key, label in _SECTIONS:
            if buckets[key]:
                yield label, buckets[key]

    # ── Formatters ─────────────────────────────────────────────────────────────

    def _strip_tags(self, text: str) -> str:
        """Convert 5etools inline tags to readable text."""
        text = re.sub(r"\{@actTrigger\}", "Trigger:", text)
        text = re.sub(r"\{@actResponse(?:\s+\w+)?\}", "Response:", text)
        text = re.sub(r"\{@actSave\s+\w+\}", "", text)
        text = re.sub(r"\{@actSaveFail\}", "On a failed save:", text)
        text = re.sub(r"\{@actSaveSuccess\}", "On a successful save:", text)
        text = re.sub(
            r"\{@recharge\s*(\d+)?\}",
            lambda m: f"(Recharge {m.group(1)}-6)" if m.group(1) else "(Recharge 6)",
            text,
        )
        text = re.sub(
            r"\{@atk ([^}]+)\}",
            lambda m: _ATK_MAP.get(m.group(1).strip(), m.group(1)),
            text,
        )
        text = re.sub(
            r"\{@atkr ([^}]+)\}",
            lambda m: _ATKR_MAP.get(m.group(1).strip(), m.group(1)),
            text,
        )
        text = re.sub(r"\{@hit ([^}]+)\}", r"+\1", text)
        text = re.sub(r"\{@dc ([^}]+)\}", r"DC \1", text)
        text = re.sub(r"\{@(?:damage|dice) ([^}]+)\}", r"\1", text)
        # Generic fallback: {@tag display text|optional source} → display text
        text = re.sub(r"\{@\w+ ([^|}]+)(?:\|[^}]*)?\}", r"\1", text)
        return text.strip()

    def _format_alignment(self, alignment: List[str]) -> str:
        align_map = {
            "L": "Lawful", "N": "Neutral", "C": "Chaotic",
            "G": "Good", "E": "Evil", "U": "Unaligned", "A": "Any",
        }
        return " ".join(align_map.get(a, a) for a in alignment)

    def _format_ac(self, ac: List[Any]) -> str:
        parts = []
        for entry in ac:
            if isinstance(entry, int):
                parts.append(str(entry))
            elif isinstance(entry, dict):
                value = str(entry.get("ac", "?"))
                armor = entry.get("armor") or entry.get("from", [])
                if armor:
                    value += f" ({', '.join(str(a) for a in armor)})"
                condition = entry.get("condition")
                if condition:
                    value += f" {condition}"
                parts.append(value)
        return ", ".join(parts) if parts else "—"

    def _format_hp(self, hp: Dict[str, Any]) -> str:
        if "special" in hp:
            return str(hp["special"])
        avg = hp.get("average", "?")
        formula = hp.get("formula")
        return f"{avg} ({formula})" if formula else str(avg)

    def _format_speed(self, speed: Dict[str, Any]) -> str:
        parts = []
        for mode, label in [
            ("walk", ""), ("fly", "fly"), ("swim", "swim"),
            ("burrow", "burrow"), ("climb", "climb"),
        ]:
            val = speed.get(mode)
            if val is None:
                continue
            dist = val if isinstance(val, int) else val.get("number", val)
            text = f"{dist} ft."
            if label:
                text = f"{label} {text}"
            parts.append(text)
        return ", ".join(parts) if parts else "—"

    def _format_ability_scores(self, m: Monster) -> str:
        def mod(score: int) -> str:
            v = (score - 10) // 2
            return f"+{v}" if v >= 0 else str(v)

        scores = [
            ("STR", m.str), ("DEX", m.dex), ("CON", m.con),
            ("INT", m.int), ("WIS", m.wis), ("CHA", m.cha),
        ]
        return "  ".join(
            f"[bold]{name}[/bold] {val} ({mod(val)})" for name, val in scores
        )

    def _format_kv(self, d: Dict[str, str]) -> str:
        return ", ".join(f"{k.upper()} {v}" for k, v in d.items())

    def _format_resist_immune(self, items: List[Any]) -> str:
        parts = []
        for item in items:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                inner = item.get("immune") or item.get("resist") or item.get("special", [])
                text = ", ".join(str(x) for x in inner) if isinstance(inner, list) else str(inner)
                note = item.get("note")
                if note:
                    text += f" ({note})"
                parts.append(text)
        return ", ".join(parts) if parts else "—"

    def _format_feature(self, feature: Dict[str, Any]) -> str:
        name = self._strip_tags(feature.get("name", ""))
        body = self._format_entries(feature.get("entries", []))
        return f"[bold]{name}.[/bold] {body}" if name else body

    def _format_spellcasting(self, sc: Dict[str, Any]) -> str:
        name = self._strip_tags(sc.get("name", "Spellcasting"))
        header_parts = [self._strip_tags(e) for e in sc.get("headerEntries", [])]
        header = " ".join(header_parts)

        lines: List[str] = []
        lines.append(f"[bold]{name}.[/bold] {header}" if header else f"[bold]{name}[/bold]")

        if "will" in sc:
            spells = ", ".join(self._strip_tags(s) for s in sc["will"])
            lines.append(f"  At will: {spells}")

        for freq_key, freq_suffix in [
            ("daily",   "/day"),
            ("restLong", "/long rest"),
            ("legendary", " legendary action"),
        ]:
            freq_dict = sc.get(freq_key, {})
            for count, spells in sorted(freq_dict.items()):
                spell_str = ", ".join(self._strip_tags(s) for s in spells)
                suffix = f"{count}{freq_suffix} each" if len(spells) > 1 else f"{count}{freq_suffix}"
                lines.append(f"  {suffix}: {spell_str}")

        if "recharge" in sc:
            for roll, spells in sc["recharge"].items():
                spell_str = ", ".join(self._strip_tags(s) for s in spells)
                lines.append(f"  Recharge {roll}-6: {spell_str}")

        return "\n".join(lines)

    def _format_entries(self, entries: List[Any]) -> str:
        def render(entry: Any) -> str:
            if isinstance(entry, str):
                return self._strip_tags(entry)
            if isinstance(entry, dict):
                e_type = entry.get("type")
                if e_type == "list":
                    return "\n".join(f"- {render(e)}" for e in entry.get("items", []))
                if e_type == "item":
                    # Named item: {"type":"item","name":"...","entry":"..."} or "entries":[...]
                    name = entry.get("name", "")
                    if "entries" in entry:
                        body = "\n".join(render(e) for e in entry["entries"])
                    else:
                        raw = entry.get("entry", "")
                        body = self._strip_tags(raw) if isinstance(raw, str) else render(raw)
                    return f"[bold]{name}.[/bold] {body}" if name else body
                if e_type in {"entries", "section"}:
                    header = entry.get("name")
                    body = "\n".join(render(e) for e in entry.get("entries", []))
                    return f"[bold]{header}[/bold]\n{body}" if header else body
                if "entries" in entry:
                    return "\n".join(render(e) for e in entry["entries"])
                if "entry" in entry:
                    raw = entry["entry"]
                    return self._strip_tags(raw) if isinstance(raw, str) else render(raw)
                return str(entry)
            if isinstance(entry, list):
                return "\n".join(render(e) for e in entry)
            return str(entry)

        return "\n\n".join(render(e) for e in entries)


    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
