import json
from pathlib import Path
from typing import Callable, List, Optional

import httpx

from ..config import get_data_dir, load_config, save_config, get_sources_manifest


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
        files = self.files_for_sources(source_ids)
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
