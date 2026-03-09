"""Grimoire 5e — application configuration and paths."""

import json
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "grimoire"
APP_AUTHOR = "grimoire5e"


def get_user_data_dir() -> Path:
    """Return the platform-appropriate user data directory for grimoire."""
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_data_dir() -> Path:
    """Return the directory where downloaded 5etools data is stored."""
    return get_user_data_dir() / "data"


def get_config_path() -> Path:
    return get_user_data_dir() / "config.json"


def load_config() -> dict:
    p = get_config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(config: dict) -> None:
    p = get_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_sources_manifest() -> dict:
    """Load the bundled sources.json manifest."""
    manifest_path = Path(__file__).parent / "sources.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def is_data_installed() -> bool:
    """Return True if data has been downloaded and config records installed sources."""
    cfg = load_config()
    if not cfg.get("installed_sources"):
        return False
    data_dir = Path(cfg.get("data_dir", str(get_data_dir())))
    return data_dir.exists()


def get_custom_sources() -> dict:
    """Return the custom_sources dict from config: {source_code: display_name}."""
    return load_config().get("custom_sources", {})


def register_custom_source(code: str, name: str) -> None:
    """Add a custom source to config and mark it as installed."""
    cfg = load_config()
    cfg.setdefault("custom_sources", {})[code] = name
    installed = set(cfg.get("installed_sources", []))
    installed.add(code)
    cfg["installed_sources"] = list(installed)
    save_config(cfg)


def remove_custom_source(code: str) -> None:
    """Remove a custom source from config and installed_sources."""
    cfg = load_config()
    cfg.get("custom_sources", {}).pop(code, None)
    installed = set(cfg.get("installed_sources", []))
    installed.discard(code)
    cfg["installed_sources"] = list(installed)
    save_config(cfg)
