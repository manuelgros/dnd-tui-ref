# Maps raw source codes → full book titles (used in filters and detail views)
SOURCE_FULL: dict = {
    "XPHB": "Player's Handbook (2024)",
    "XDMG": "Dungeon Master's Guide (2024)",
    "XMM": "Monster Manual (2025)",
    "XGE": "Xanathar's Guide to Everything",
    "TCE": "Tasha's Cauldron of Everything",
    "BGG": "Bigby Presents: Glory of the Giants",
}

# Maps raw source codes → short labels (used in list views)
SOURCE_SHORT: dict = {
    "XPHB": "PHB'24",
    "XDMG": "DMG'24",
    "XMM":  "MM'25",
    "XGE":  "XGE",
    "TCE":  "TCE",
    "BGG":  "BGG",
}

# Filter dropdown options — display full title, value is the raw source code
SOURCE_OPTIONS: list = [
    ("All Sources", None),
    ("Player's Handbook (2024)", "XPHB"),
    ("Dungeon Master's Guide (2024)", "XDMG"),
    ("Monster Manual (2025)", "XMM"),
    ("Xanathar's Guide to Everything", "XGE"),
    ("Tasha's Cauldron of Everything", "TCE"),
    ("Bigby Presents: Glory of the Giants", "BGG"),
]
