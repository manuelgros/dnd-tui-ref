from dataclasses import dataclass
from typing import Any, List

from .base import BaseModel


@dataclass
class Rule(BaseModel):
    entries: List[Any]
    rule_type: str  # "C", "condition", "disease"

    @property
    def type_display(self) -> str:
        return {
            "C": "Core Rule",
            "O": "Optional Rule",
            "V": "Variant Rule",
            "VO": "Variant Optional",
            "condition": "Condition",
            "disease": "Disease",
        }.get(self.rule_type, self.rule_type)

    @property
    def is_condition(self) -> bool:
        return self.rule_type == "condition"

    @property
    def is_disease(self) -> bool:
        return self.rule_type == "disease"

    @property
    def is_core_rule(self) -> bool:
        return self.rule_type == "C"
