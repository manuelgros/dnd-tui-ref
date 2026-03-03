from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass
class SearchResult:
    item: Any
    score: float


class SearchService:
    """Handles search with optional tag prefixes and fuzzy matching."""

    @staticmethod
    def parse_query(query: str) -> Tuple[Optional[str], str]:
        """
        Parse search query for tag prefix.
        Returns: (tag, search_term)
        """
        if ":" not in query:
            return None, query

        tag, term = query.split(":", 1)
        tag = tag.lower().strip()
        term = term.strip()

        tag_map = {
            "s": "spell",
            "m": "monster",
            "i": "item",
            "f": "feat",
            "r": "rule",
        }

        return tag_map.get(tag, tag), term

    @staticmethod
    def tiered_match(query: str, text: str) -> float:
        """
        Tiered matching against word boundaries. Returns score 0.0-1.0.

        Tier 1 (1.0): full name starts with query      — "ring" → "Ring of Protection"
        Tier 2 (0.9): any word in name starts with query — "tongue" → "Flame Tongue"
        Tier 3 (0.7): query is a substring of the name  — "lame" → "Flame Tongue"
        Tier 0 (0.0): no match
        """
        if not query:
            return 1.0
        q = query.lower()
        t = text.lower()
        if t.startswith(q):
            return 1.0
        words = t.split()
        if any(w.startswith(q) for w in words):
            return 0.9
        if q in t:
            return 0.7
        return 0.0

    @staticmethod
    def search(items: List[Any], query: str, name_attr: str = "name") -> List[Any]:
        """
        Search items by name using tiered word-boundary matching.
        Returns items sorted by match tier, then alphabetically within each tier.
        """
        _, term = SearchService.parse_query(query)
        if not term:
            return items

        results: List[SearchResult] = []
        for item in items:
            name = getattr(item, name_attr, "")
            score = SearchService.tiered_match(term, name)
            if score > 0.0:
                results.append(SearchResult(item=item, score=score))

        results.sort(key=lambda r: (-r.score, getattr(r.item, name_attr, "").lower()))
        return [r.item for r in results]
