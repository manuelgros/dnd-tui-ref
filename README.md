# Grimoire 5e

A terminal UI for D&D 5th Edition reference material — spells, monsters, items, feats, and rules — all searchable and filterable without leaving your keyboard.

![PyPI](https://img.shields.io/pypi/v/grimoire5e)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Features

- **Quick Search** across all content types with `s:`, `m:`, `i:`, `f:`, `r:` prefixes
- **Spells** — filter by level, school, class, source; sort by name / level / school
- **Monsters** — filter by CR, type, size, source; sort by name / CR / type
- **Items** — filter by type (weapon, armor, wondrous, potion, poison…), rarity, attunement
- **Feats** — filter by source
- **Rules** — conditions, status effects, diseases, and core rules from XPHB
- **Themes** — Classic D&D, 5e Tools, Arcane, Parchment, Gelatinous Cube (+ Textual built-ins)
- **Manage Sources** in-app — download new books or toggle active ones without restarting
- Supports **30+ official sourcebooks** including adventures and Forgotten Realms titles

## Requirements

- Python 3.11 or newer
- Internet connection for first-run data download
- **Windows only:** [Windows Terminal](https://aka.ms/terminal) (the default CMD/PowerShell console does not support the required ANSI colours)

## Installation

### Recommended (pipx)

[pipx](https://pipx.pypa.io) installs Python CLI tools in isolated environments and puts them on your PATH — no virtual environment management needed.

```bash
# macOS
brew install pipx && pipx install grimoire5e

# Linux (Debian/Ubuntu)
apt install pipx && pipx install grimoire5e

# Windows (in Windows Terminal, using winget)
winget install Python.Launcher
pip install pipx
pipx install grimoire5e
```

### Alternative (pip)

```bash
pip install grimoire5e
```

### From source (for development)

```bash
git clone https://github.com/manuelgros/grimoire5e.git
cd grimoire5e
pip install -e .
```

## First Run

On first launch, Grimoire opens a setup wizard where you select which source books to download. Only books you legally own should be selected.

```bash
grimoire
```

Data is downloaded from the public [5etools mirror](https://github.com/5etools-mirror-3/5etools-src) and stored in your platform's user data directory:

| Platform | Path |
|----------|------|
| macOS    | `~/Library/Application Support/grimoire/` |
| Linux    | `~/.local/share/grimoire/` |
| Windows  | `%APPDATA%\grimoire5e\grimoire\` |

## Usage

```
grimoire                    # launch app (setup wizard on first run)
grimoire --manage-sources   # open source manager to add/remove books
```

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate between filters |
| `↑` / `↓` | Move through the list |
| `Enter` | Open detail view |
| `/` | Focus search |
| `Esc` | Return to Quick Search |
| `Ctrl+1–7` | Jump to tab |
| `q` | Quit |

## Supported Sources

**Core (2024)**
XPHB · XDMG · XMM

**Core (2014)**
PHB · DMG · MM

**Supplements**
XGE · TCE · VGM · MTF · MPMM · FTD · BGG · VRGR · MOT · GGR · EGW · SCC · AI · BMT · PHB

**Adventures**
HotDQ · RoT · PotA · OotA · CoS · SKT · ToA · WDH · WDMM · BGDIA · IDRotF · WBtW · FRAiF

**Forgotten Realms**
FRHoF

## Legal

This tool downloads data from the [5etools-mirror-3](https://github.com/5etools-mirror-3/5etools-src) repository for personal use only. Grimoire 5e does not bundle any game content — all data is fetched at runtime from publicly available mirrors of D&D 5e material published under the [Creative Commons Attribution 4.0 license](https://creativecommons.org/licenses/by/4.0/) (for XPHB/2024 content) or used under fair use for personal reference.

**Only download content you legally own.**

## License

[MIT](LICENSE)
