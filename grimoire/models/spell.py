from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .base import BaseModel


@dataclass
class Spell(BaseModel):
    level: int
    school: str
    time: List[Dict[str, Any]]
    range: Dict[str, Any]
    components: Dict[str, Any]
    duration: List[Dict[str, Any]]
    entries: List[Any]
    classes: Dict[str, Any]

    concentration: bool = False
    ritual: bool = False
    higher_level: Optional[List[Any]] = None

    @property
    def level_text(self) -> str:
        return "Cantrip" if self.level == 0 else f"Level {self.level}"

    @property
    def school_full(self) -> str:
        schools = {
            "A": "Abjuration",
            "C": "Conjuration",
            "D": "Divination",
            "E": "Enchantment",
            "I": "Illusion",
            "N": "Necromancy",
            "T": "Transmutation",
            "V": "Evocation",
        }
        return schools.get(self.school, self.school)

    @property
    def classes_list(self) -> List[str]:
        return [c["name"] for c in self.classes.get("fromClassList", [])]
