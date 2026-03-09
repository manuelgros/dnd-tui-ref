import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="grimoire",
        description="Grimoire 5e — D&D 5th Edition reference TUI.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        metavar="PATH",
        help="Use a local 5etools-compatible data directory instead of downloaded data.",
    )
    parser.add_argument(
        "--manage-sources",
        action="store_true",
        help="Open the source management screen to add or remove downloaded sources.",
    )
    parser.add_argument(
        "--import",
        dest="import_source",
        type=Path,
        metavar="FILE",
        help="Import a custom 5etools-format JSON source file and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="grimoire5e 0.1.0",
    )
    args = parser.parse_args()

    if args.import_source:
        _import_source(args.import_source.resolve())
    elif args.data_dir:
        _run_app(data_dir=args.data_dir.resolve())
    elif args.manage_sources:
        _run_setup_wizard(manage_only=True)
    else:
        from .config import is_data_installed, get_data_dir, load_config
        if not is_data_installed():
            _run_setup_wizard()
        else:
            cfg = load_config()
            installed = set(cfg.get("installed_sources", []))
            _run_app(data_dir=get_data_dir(), installed_sources=installed)


def _import_source(json_path: Path) -> None:
    from .config import is_data_installed, get_data_dir, load_config, register_custom_source
    from .services.data_manager import DataManager

    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        raise SystemExit(1)

    if not is_data_installed():
        print("Error: No data directory found. Run 'grimoire' first to set up your data.")
        raise SystemExit(1)

    cfg = load_config()
    data_dir = Path(cfg.get("data_dir", str(get_data_dir())))

    try:
        result = DataManager(data_dir).import_source(json_path)
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    register_custom_source(result["source"], result["name"])

    counts = result["counts"]
    parts = [f"{v} {k}s" for k, v in counts.items()]
    print(f"Imported {', '.join(parts)} from '{result['name']}' ({result['source']}).")
    print(f"Run 'grimoire' to browse the new content.")


def _run_app(data_dir: Path, installed_sources=None) -> None:
    from .app import GrimoireApp
    GrimoireApp(data_dir=data_dir, installed_sources=installed_sources).run()


def _run_setup_wizard(manage_only: bool = False) -> None:
    from .views.setup_wizard import SetupWizardApp
    from .config import get_data_dir
    installed = SetupWizardApp(manage_only=manage_only).run()
    # run() returns whatever was passed to self.exit() — the set of installed source IDs.
    # Launch the main app only if the wizard completed a download (not if user quit early).
    if installed:
        _run_app(data_dir=get_data_dir(), installed_sources=installed)
