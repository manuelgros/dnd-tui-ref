import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

import httpx

from ..config import get_data_dir, load_config, save_config, get_sources_manifest
from .sources import SOURCE_FULL


class DataManager:
    """Downloads and manages 5etools data files."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or get_data_dir()
        self._manifest = get_sources_manifest()

    @property
    def base_url(self) -> str:
        return self._manifest["base_url"]

    @property
    def global_files(self) -> List[str]:
        return self._manifest["global_files"]

    @property
    def sources(self) -> List[dict]:
        return self._manifest["sources"]

    def get_source_by_id(self, source_id: str) -> Optional[dict]:
        for src in self.sources:
            if src["id"] == source_id:
                return src
        return None

    def get_installed_sources(self) -> List[str]:
        cfg = load_config()
        return cfg.get("installed_sources", [])

    def save_installed_sources(self, source_ids: List[str]) -> None:
        cfg = load_config()
        cfg["installed_sources"] = source_ids
        cfg["data_dir"] = str(self.data_dir)
        save_config(cfg)

    def files_for_sources(self, source_ids: List[str]) -> List[str]:
        """Return all file paths needed for the given source IDs (plus global files)."""
        files = list(self.global_files)
        for source_id in source_ids:
            src = self.get_source_by_id(source_id)
            if src:
                files.extend(src["files"])
        return files

    def download_sources(
        self,
        source_ids: List[str],
        progress_cb: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        """
        Download all files for the given source IDs plus global files.

        Args:
            source_ids: List of source ID strings (e.g. ["XPHB", "XGE"])
            progress_cb: Optional callback(file_path, current, total) for progress reporting
        """
        all_files = self.files_for_sources(source_ids)
        files = [f for f in all_files if not (self.data_dir / f).exists()]
        total = len(files)

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            for idx, file_path in enumerate(files):
                if progress_cb:
                    progress_cb(file_path, idx, total)

                url = f"{self.base_url}/{file_path}"
                dest = self.data_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)

                response = client.get(url)
                response.raise_for_status()
                dest.write_bytes(response.content)

        if progress_cb:
            progress_cb("", total, total)

        self.save_installed_sources(source_ids)

    def import_source(self, json_path: Path) -> Dict:
        """
        Parse a monolithic 5etools JSON file, split it into per-type files in data_dir,
        and return a summary dict with source metadata and content counts.

        Raises ValueError if the file is not a valid 5etools source JSON.
        """
        raw = json_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        meta = data.get("_meta", {})
        sources = meta.get("sources", [])
        if not sources:
            raise ValueError("No '_meta.sources' found — not a valid 5etools source file.")

        src_info = sources[0]
        src_code = src_info.get("json")
        src_name = src_info.get("full") or src_info.get("abbreviation") or src_code
        if not src_code:
            raise ValueError("Source code ('json' field) missing from _meta.sources[0].")

        if src_code in SOURCE_FULL:
            raise ValueError(
                f"'{src_code}' is an official source already built into Grimoire. "
                "Use Manage Sources to download it."
            )

        counts: Dict[str, int] = {}

        # Map of JSON key → (subdirectory or None, filename template, wrapper key for output)
        type_map = {
            "spell":        ("spells",   f"spells-{src_code}.json",          "spell"),
            "monster":      ("bestiary", f"bestiary-{src_code}.json",         "monster"),
            "legendaryGroup": ("bestiary", f"legendarygroups-{src_code}.json", "legendaryGroup"),
            "item":         (None,       f"items-{src_code}.json",            "item"),
            "magicvariant": (None,       f"magicvariants-{src_code}.json",    "magicvariant"),
            "feat":         (None,       f"feats-{src_code}.json",            "feat"),
        }

        for key, (subdir, filename, out_key) in type_map.items():
            entries = data.get(key, [])
            if not entries:
                continue
            dest_dir = (self.data_dir / subdir) if subdir else self.data_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / filename
            dest.write_text(
                json.dumps({out_key: entries}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            counts[key] = len(entries)

        # Conditions/diseases/status share one output file
        cd_entries: Dict[str, list] = {}
        for key in ("condition", "disease", "status"):
            entries = data.get(key, [])
            if entries:
                cd_entries[key] = entries
                counts[key] = len(entries)
        if cd_entries:
            dest = self.data_dir / f"conditionsdiseases-{src_code}.json"
            dest.write_text(
                json.dumps(cd_entries, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if not counts:
            raise ValueError("No supported content types found in this file.")

        return {"source": src_code, "name": src_name, "counts": counts}

    def remove_source_files(self, src_code: str) -> None:
        """Delete all split files created for a custom source."""
        candidates = [
            self.data_dir / "spells" / f"spells-{src_code}.json",
            self.data_dir / "bestiary" / f"bestiary-{src_code}.json",
            self.data_dir / "bestiary" / f"legendarygroups-{src_code}.json",
            self.data_dir / f"items-{src_code}.json",
            self.data_dir / f"magicvariants-{src_code}.json",
            self.data_dir / f"feats-{src_code}.json",
            self.data_dir / f"conditionsdiseases-{src_code}.json",
        ]
        for path in candidates:
            if path.exists():
                path.unlink()
