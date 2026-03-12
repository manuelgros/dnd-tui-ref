# Changelog Draft — v0.2.0

## Bug Fixes
- Fix magic item descriptions showing raw `{=bonusAc}` / `{=bonusWeapon}` placeholders instead of actual bonus values (+1, +2, +3) for armor, weapons, shields, and ammunition
- Fix feats and rules detail view subtitles staying yellow regardless of selected theme — now correctly follow the active theme's label color like spells, monsters, and items do
- Fix monster action entries showing raw `{@h}` tag before average damage values (e.g. `{@h}28 (3d12 + 9)` now renders as `28 (3d12 + 9)`)
- Fix custom sources disappearing from all content tabs after downloading additional official sources via Manage Sources
- Fix custom source content not appearing in source filter dropdowns after downloading additional official sources
- Fix app crash when filtering monsters by type (e.g. Undead) — some monsters use a structured tag format (`{"tag": "...", "prefix": "..."}`) that caused an `AttributeError` in the type filter logic
- Other small Bug Fixes to improve performance

## New Features
- **Custom source upload**: Import any 5etools-format JSON source book directly in the app (Settings → Upload Source) or via `grimoire --import /path/to/file.json`. Uploaded sources appear in all content tabs (monsters, items, spells, etc.) and in source filter dropdowns alongside official sources.
- **Remove custom sources**: Settings → Remove Custom lets you delete previously uploaded sources and their data files.
- **Non-blocking import**: Uploading a large source file no longer freezes the app — a loading indicator is shown while the file is being processed in the background.

## Changes
- Default theme changed from `textual-dark` to `5e-tools` for fresh installations
- Setup wizard now uses the `5e-tools` theme
- Monster list: replaced Size filter with Environment filter; only monsters that have environment tags are shown when filtering by environment (not all sourcebooks include this data)
- Keyboard navigation improvements across all menus: arrow keys (left/right) navigate between buttons, Tab jumps directly out of the button row instead of cycling through all buttons, and relevant menus auto-focus the first item on open
