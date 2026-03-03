from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .base import BaseModel

_CATEGORY_MAP: Dict[str, str] = {
    "M": "weapon", "R": "weapon",
    "HA": "armor", "MA": "armor", "LA": "armor",
    "S": "shield",
    "P": "potion",
    "SC": "scroll",
    "RD": "rod",
    "RG": "ring",
    "WD": "wand",
    "SCF": "focus",
    "INS": "instrument",
    "G": "gear",
}

_CATEGORY_LABELS: Dict[str, str] = {
    "weapon": "Weapon",
    "armor": "Armor",
    "shield": "Shield",
    "wondrous": "Wondrous Item",
    "potion": "Potion",
    "scroll": "Scroll",
    "rod": "Rod",
    "ring": "Ring",
    "wand": "Wand",
    "focus": "Spellcasting Focus",
    "instrument": "Instrument",
    "gear": "Adventuring Gear",
    "other": "Other",
}


@dataclass
class Item(BaseModel):
    type: str
    rarity: str
    entries: List[Any]

    tier: Optional[str] = None
    reqAttune: Optional[Union[bool, str]] = None
    weight: Optional[float] = None
    value: Optional[int] = None
    weapon: Optional[bool] = False
    armor: Optional[bool] = False
    wondrous: Optional[bool] = False
    baseItem: Optional[str] = None
    requires_str: Optional[str] = None  # Human-readable "applies to" for magic variants

    @property
    def rarity_display(self) -> str:
        rarity_map = {
            "none": "Common Item",
            "common": "Common",
            "uncommon": "Uncommon",
            "rare": "Rare",
            "very rare": "Very Rare",
            "legendary": "Legendary",
            "artifact": "Artifact",
            "varies": "Varies",
        }
        return rarity_map.get(self.rarity, self.rarity.title())

    @property
    def requires_attunement(self) -> bool:
        return self.reqAttune is not None

    @property
    def attunement_display(self) -> str:
        if not self.requires_attunement:
            return ""
        if isinstance(self.reqAttune, str):
            return f"Requires Attunement ({self.reqAttune})"
        return "Requires Attunement"

    @property
    def category(self) -> str:
        base = (self.type or "").split("|")[0]
        cat = _CATEGORY_MAP.get(base)
        if cat:
            return cat
        if self.wondrous:
            return "wondrous"
        return "other"

    @property
    def type_display(self) -> str:
        label = _CATEGORY_LABELS.get(self.category, "Other")
        if self.baseItem:
            subtype = self.baseItem.split("|")[0].title()
            if subtype.lower() != label.lower():
                return f"{label} ({subtype})"
        return label
