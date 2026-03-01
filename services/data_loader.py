import json
from pathlib import Path
from typing import List, Optional

from models import Spell, Monster, Item, Feat, Condition, cr_to_float


ALLOWED_SOURCES = {"XPHB", "XDMG", "XMM", "XGE", "TCE", "BGG"}


class DataLoader:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self._spells: Optional[List[Spell]] = None
        self._monsters: Optional[List[Monster]] = None
        self._items: Optional[List[Item]] = None
        self._feats: Optional[List[Feat]] = None
        self._conditions: Optional[List[Condition]] = None

    @property
    def spells(self) -> List[Spell]:
        if self._spells is None:
            self._spells = self._load_spells()
        return self._spells

    @property
    def monsters(self) -> List[Monster]:
        if self._monsters is None:
            self._monsters = self._load_monsters()
        return self._monsters

    @property
    def items(self) -> List[Item]:
        if self._items is None:
            self._items = self._load_items()
        return self._items

    @property
    def feats(self) -> List[Feat]:
        if self._feats is None:
            self._feats = self._load_feats()
        return self._feats

    @property
    def conditions(self) -> List[Condition]:
        if self._conditions is None:
            self._conditions = self._load_conditions()
        return self._conditions

    def _load_spells(self) -> List[Spell]:
        spells: List[Spell] = []
        sources = ["xphb", "xge", "tce"]

        for source in sources:
            file_path = self.data_dir / "spells" / f"spells-{source}.json"
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for spell_data in data.get("spell", []):
                    # concentration is inside duration[0], not at top level
                    concentration = False
                    for d in spell_data.get("duration", []):
                        if isinstance(d, dict) and d.get("concentration"):
                            concentration = True
                            break

                    # ritual is inside meta, not at top level
                    meta = spell_data.get("meta") or {}
                    ritual = meta.get("ritual", False) if isinstance(meta, dict) else False

                    spells.append(
                        Spell(
                            name=spell_data["name"],
                            source=spell_data["source"],
                            level=spell_data["level"],
                            school=spell_data["school"],
                            time=spell_data["time"],
                            range=spell_data["range"],
                            components=spell_data["components"],
                            duration=spell_data["duration"],
                            entries=spell_data["entries"],
                            classes=spell_data.get("classes", {}),
                            concentration=concentration,
                            ritual=ritual,
                            higher_level=spell_data.get("entriesHigherLevel"),
                        )
                    )

        return sorted(spells, key=lambda s: (s.level, s.name))

    def _load_legendary_groups(self) -> dict:
        """Return a (name, source) → group dict from legendarygroups.json."""
        path = self.data_dir / "bestiary" / "legendarygroups.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            (g["name"], g["source"]): g
            for g in data.get("legendaryGroup", [])
            if "_copy" not in g
        }

    def _resolve_legendary_group(self, ref, groups: dict):
        if not ref:
            return None
        return groups.get((ref["name"], ref["source"]))

    def _load_monsters(self) -> List[Monster]:
        monsters: List[Monster] = []
        bestiary_dir = self.data_dir / "bestiary"
        legendary_groups = self._load_legendary_groups()

        for file_path in sorted(bestiary_dir.glob("bestiary-*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for monster_data in data.get("monster", []):
                    if monster_data.get("source") not in ALLOWED_SOURCES:
                        continue

                    size = monster_data.get("size", [])
                    if isinstance(size, str):
                        size = [size]

                    monsters.append(
                        Monster(
                            name=monster_data["name"],
                            source=monster_data["source"],
                            size=size,
                            type=monster_data["type"],
                            alignment=monster_data.get("alignment", []),
                            ac=monster_data.get("ac", []),
                            hp=monster_data["hp"],
                            speed=monster_data["speed"],
                            str=monster_data["str"],
                            dex=monster_data["dex"],
                            con=monster_data["con"],
                            int=monster_data["int"],
                            wis=monster_data["wis"],
                            cha=monster_data["cha"],
                            cr=monster_data["cr"],
                            save=monster_data.get("save"),
                            skill=monster_data.get("skill"),
                            vulnerable=monster_data.get("vulnerable"),
                            resist=monster_data.get("resist"),
                            immune=monster_data.get("immune"),
                            conditionImmune=monster_data.get("conditionImmune"),
                            senses=monster_data.get("senses"),
                            languages=monster_data.get("languages"),
                            trait=monster_data.get("trait"),
                            action=monster_data.get("action"),
                            bonus=monster_data.get("bonus"),
                            reaction=monster_data.get("reaction"),
                            legendary=monster_data.get("legendary"),
                            spellcasting=monster_data.get("spellcasting"),
                            legendary_group_data=self._resolve_legendary_group(
                                monster_data.get("legendaryGroup"), legendary_groups
                            ),
                        )
                    )

        return sorted(monsters, key=lambda m: m.name)

    def _load_items(self) -> List[Item]:
        items: List[Item] = []
        file_path = self.data_dir / "items.json"

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item_data in data.get("item", []):
                if item_data.get("source") not in ALLOWED_SOURCES:
                    continue

                items.append(
                    Item(
                        name=item_data["name"],
                        source=item_data["source"],
                        type=item_data.get("type", "G"),
                        rarity=item_data.get("rarity", "none"),
                        entries=item_data.get("entries", []),
                        tier=item_data.get("tier"),
                        reqAttune=item_data.get("reqAttune"),
                        weight=item_data.get("weight"),
                        value=item_data.get("value"),
                        weapon=item_data.get("weapon", False),
                        armor=item_data.get("armor", False),
                        wondrous=item_data.get("wondrous", False),
                        baseItem=item_data.get("baseItem"),
                    )
                )

        return sorted(items, key=lambda i: i.name)

    def _load_feats(self) -> List[Feat]:
        feats: List[Feat] = []
        file_path = self.data_dir / "feats.json"

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for feat_data in data.get("feat", []):
                if feat_data.get("source") not in ALLOWED_SOURCES:
                    continue

                feats.append(
                    Feat(
                        name=feat_data["name"],
                        source=feat_data["source"],
                        entries=feat_data.get("entries", []),
                        prerequisite=feat_data.get("prerequisite"),
                        ability=feat_data.get("ability"),
                        repeatable=feat_data.get("repeatable", False),
                    )
                )

        return sorted(feats, key=lambda f_: f_.name)

    def _load_conditions(self) -> List[Condition]:
        conditions: List[Condition] = []
        file_path = self.data_dir / "conditionsdiseases.json"

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for cond_data in data.get("condition", []):
                if cond_data.get("source") != "XPHB":
                    continue
                if cond_data.get("type") != "condition":
                    continue

                conditions.append(
                    Condition(
                        name=cond_data["name"],
                        source=cond_data["source"],
                        entries=cond_data.get("entries", []),
                    )
                )

        return sorted(conditions, key=lambda c: c.name)

