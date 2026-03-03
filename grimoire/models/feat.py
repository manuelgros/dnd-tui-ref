from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseModel


@dataclass
class Feat(BaseModel):
    entries: List[Any]
    prerequisite: Optional[List[Dict[str, Any]]] = None
    ability: Optional[List[Dict[str, Any]]] = None
    repeatable: Optional[bool] = False
    category: Optional[str] = None

    @property
    def has_prerequisite(self) -> bool:
        return self.prerequisite is not None and len(self.prerequisite) > 0
