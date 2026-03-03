import json
from pathlib import Path
from typing import List, Optional

from ..models import Spell, Monster, Item, Feat, Rule, cr_to_float


ALLOWED_SOURCES = {"XPHB", "XDMG", "XMM", "XGE", "TCE", "BGG"}


class DataLoader:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self._spells: Optional[List[Spell]] = None
        self._monsters: Optional[List[Monster]] = None
        self._items: Optional[List[Item]] = None
        self._feats: Optional[List[Feat]] = None
        self._rules: Optional[List[Rule]] = None

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
    def rules(self) -> List[Rule]:
        if self._rules is None:
            self._rules = self._load_rules()
        return self._rules

    def _load_spells(self) -> List[Spell]:
        spells: List[Spell] = []
        sources = ["xphb", "xge", "tce"]

        for source in sources:
            file_path = self.data_dir / "spells" / f"spells-{source}.json"
            if not file_path.exists():
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for spell_data in data.get("spell", []):
                    concentration = False
                    for d in spell_data.get("duration", []):
                        if isinstance(d, dict) and d.get("concentration"):
                            concentration = True
                            break

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
        """Return a (name, source) → group dict from all bestiary files."""
        groups: dict = {}
        bestiary_dir = self.data_dir / "bestiary"
        lg_path = bestiary_dir / "legendarygroups.json"
        if lg_path.exists():
            with open(lg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for g in data.get("legendaryGroup", []):
                if "_copy" not in g:
                    groups[(g["name"], g["source"])] = g
        for file_path in sorted(bestiary_dir.glob("bestiary-*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for g in data.get("legendaryGroup", []):
                if "_copy" not in g:
                    groups[(g["name"], g["source"])] = g
        return groups

    def _resolve_legendary_group(self, ref, groups: dict):
        if not ref:
            return None
        return groups.get((ref["name"], ref["source"]))

    def _load_monsters(self) -> List[Monster]:
        monsters: List[Monster] = []
        bestiary_dir = self.data_dir / "bestiary"
        if not bestiary_dir.exists():
            return monsters
        legendary_groups = self._load_legendary_groups()

        for file_path in sorted(bestiary_dir.glob("bestiary-*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for monster_data in data.get("monster", []):
                    if monster_data.get("source") not in ALLOWED_SOURCES:
                        continue
                    # Skip copy/template stubs that don't have full stat blocks
                    if "_copy" in monster_data or "hp" not in monster_data:
                        continue

                    size = monster_data.get("size", [])
                    if isinstance(size, str):
                        size = [size]

                    monsters.append(
                        Monster(
                            name=monster_data["name"],
                            source=monster_data["source"],
                            size=size,
                            type=monster_data.get("type", "unknown"),
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
                            cr=monster_data.get("cr"),
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

        # ── Standard magic items ──────────────────────────────────────────────
        items_path = self.data_dir / "items.json"
        if items_path.exists():
            with open(items_path, "r", encoding="utf-8") as f:
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

        # ── Base / mundane items ──────────────────────────────────────────────
        base_path = self.data_dir / "items-base.json"
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item_data in data.get("baseitem", []):
                    if item_data.get("source") not in ALLOWED_SOURCES:
                        continue
                    items.append(
                        Item(
                            name=item_data["name"],
                            source=item_data["source"],
                            type=item_data.get("type", "G"),
                            rarity=item_data.get("rarity", "none"),
                            entries=item_data.get("entries", []),
                            weight=item_data.get("weight"),
                            value=item_data.get("value"),
                            weapon=item_data.get("weapon", False),
                            armor=item_data.get("armor", False),
                        )
                    )

        # ── Magic variants ────────────────────────────────────────────────────
        variants_path = self.data_dir / "magicvariants.json"
        if variants_path.exists():
            with open(variants_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for variant in data.get("magicvariant", []):
                    inh = variant.get("inherits", {})
                    if inh.get("source") not in ALLOWED_SOURCES:
                        continue
                    requires = variant.get("requires", [])
                    items.append(
                        Item(
                            name=variant["name"],
                            source=inh["source"],
                            type=self._requires_to_type(requires),
                            rarity=inh.get("rarity", "none"),
                            entries=inh.get("entries", []),
                            tier=inh.get("tier"),
                            reqAttune=inh.get("reqAttune"),
                            wondrous=inh.get("wondrous", False),
                            requires_str=self._requires_to_str(requires),
                        )
                    )

        return sorted(items, key=lambda i: i.name)

    def _requires_to_type(self, requires: list) -> str:
        """Derive a representative item type code from a magic variant's requires list."""
        all_flags = {k for req in requires for k in req.keys()}
        if "weapon" in all_flags or "weaponCategory" in all_flags or "sword" in all_flags:
            return "M"
        if "armor" in all_flags:
            return "HA"
        all_types = set()
        for req in requires:
            if "type" in req:
                all_types.add(req["type"].split("|")[0])
            if "name" in req:
                name = req["name"].lower()
                if any(w in name for w in [
                    "sword", "axe", "blade", "spear", "bow", "dagger",
                    "hammer", "mace", "glaive", "rapier", "scimitar",
                    "sickle", "flail", "lance", "pike", "trident",
                    "whip", "club", "quarterstaff", "maul", "halberd",
                ]):
                    all_types.add("M")
                elif any(w in name for w in ["armor", "mail", "plate", "chain shirt"]):
                    all_types.add("HA")
        armor_types = {"HA", "MA", "LA"}
        if all_types and all_types <= armor_types:
            return "HA"
        if "M" in all_types:
            return "M"
        if "R" in all_types:
            return "R"
        if "S" in all_types:
            return "S"
        return "G"

    def _requires_to_str(self, requires: list) -> str:
        """Convert a magic variant's requires list to a human-readable string."""
        if not requires:
            return ""
        all_flags = {k for req in requires for k in req.keys()}
        if "weapon" in all_flags:
            return "any weapon"
        if "sword" in all_flags:
            return "any sword"
        if "armor" in all_flags:
            return "any armor"
        if "weaponCategory" in all_flags:
            cats = sorted(set(
                req["weaponCategory"] for req in requires if "weaponCategory" in req
            ))
            return "any weapon" if set(cats) >= {"simple", "martial"} else f"any {' or '.join(cats)} weapon"
        names = [req["name"] for req in requires if "name" in req]
        if names:
            return ", ".join(names)
        type_map = {
            "M": "melee weapon", "R": "ranged weapon",
            "HA": "heavy armor", "MA": "medium armor", "LA": "light armor",
            "A": "ammunition", "AF": "ammunition", "S": "shield",
        }
        type_bases = list(dict.fromkeys(
            req["type"].split("|")[0] for req in requires if "type" in req
        ))
        readable = list(dict.fromkeys(type_map.get(t, t) for t in type_bases if t in type_map))
        armor_set = {"heavy armor", "medium armor", "light armor"}
        if set(readable) >= armor_set:
            return "any armor"
        if len(readable) == 1:
            return f"any {readable[0]}"
        if readable:
            return "any " + " or ".join(readable)
        return ""

    def _load_feats(self) -> List[Feat]:
        feats: List[Feat] = []
        file_path = self.data_dir / "feats.json"
        if not file_path.exists():
            return feats

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
                        category=feat_data.get("category"),
                    )
                )

        return sorted(feats, key=lambda f_: f_.name)

    def _load_rules(self) -> List[Rule]:
        rules: List[Rule] = []

        # Core rules from variantrules.json (XPHB only, ruleType "C")
        vr_path = self.data_dir / "variantrules.json"
        if vr_path.exists():
            with open(vr_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("variantrule", []):
                if entry.get("source") == "XPHB" and entry.get("ruleType") == "C":
                    rules.append(Rule(
                        name=entry["name"],
                        source=entry["source"],
                        entries=entry.get("entries", []),
                        rule_type="C",
                    ))

        # Conditions, status effects, and diseases from conditionsdiseases.json
        cd_path = self.data_dir / "conditionsdiseases.json"
        if cd_path.exists():
            with open(cd_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for cond in data.get("condition", []):
                if cond.get("source") == "XPHB":
                    rules.append(Rule(
                        name=cond["name"],
                        source=cond["source"],
                        entries=cond.get("entries", []),
                        rule_type="condition",
                    ))

            # Status effects (Bloodied, Concentration, Surprised) — treat as conditions
            for status in data.get("status", []):
                if status.get("source") == "XPHB":
                    rules.append(Rule(
                        name=status["name"],
                        source=status["source"],
                        entries=status.get("entries", []),
                        rule_type="condition",
                    ))

            # Diseases from ALLOWED_SOURCES
            for disease in data.get("disease", []):
                if disease.get("source") in ALLOWED_SOURCES:
                    rules.append(Rule(
                        name=disease["name"],
                        source=disease["source"],
                        entries=disease.get("entries", []),
                        rule_type="disease",
                    ))

        return sorted(rules, key=lambda r: r.name)
