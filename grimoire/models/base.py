from dataclasses import dataclass
from typing import List


@dataclass
class BaseModel:
    name: str
    source: str

    def matches_source(self, sources: List[str]) -> bool:
        """Check if item is from one of the specified sources."""
        return self.source in sources
