from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .base import BaseModel


def cr_to_float(cr_str: str) -> float:
    if "/" in cr_str:
        num, denom = cr_str.split("/")
        return float(num) / float(denom)
    return float(cr_str)


@dataclass
class Monster(BaseModel):
    size: List[str]
    type: Union[str, Dict[str, Any]]
    alignment: List[str]
    ac: List[Dict[str, Any]]
    hp: Dict[str, Any]
    speed: Dict[str, Any]
    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int
    cr: Union[str, Dict[str, Any]]

    save: Optional[Dict[str, str]] = None
    skill: Optional[Dict[str, str]] = None
    resist: Optional[List[Any]] = None
    immune: Optional[List[Any]] = None
    conditionImmune: Optional[List[Any]] = None
    senses: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    vulnerable: Optional[List[Any]] = None
    trait: Optional[List[Dict[str, Any]]] = None
    action: Optional[List[Dict[str, Any]]] = None
    bonus: Optional[List[Dict[str, Any]]] = None
    reaction: Optional[List[Dict[str, Any]]] = None
    legendary: Optional[List[Dict[str, Any]]] = None
    spellcasting: Optional[List[Dict[str, Any]]] = None

    @property
    def cr_display(self) -> str:
        if isinstance(self.cr, dict):
            return self.cr["cr"]
        return self.cr

    @property
    def type_display(self) -> str:
        if isinstance(self.type, dict):
            base = self.type["type"]
            tags = self.type.get("tags", [])
            if tags:
                return f"{base} ({', '.join(tags)})"
            return base
        return self.type

    @property
    def size_display(self) -> str:
        size_map = {
            "T": "Tiny",
            "S": "Small",
            "M": "Medium",
            "L": "Large",
            "H": "Huge",
            "G": "Gargantuan",
        }
        return "/".join([size_map.get(s, s) for s in self.size])

