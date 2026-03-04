# Maps raw source codes → full book titles (used in filters and detail views)
SOURCE_FULL: dict = {
    # 2024 core
    "XPHB":  "Player's Handbook (2024)",
    "XDMG":  "Dungeon Master's Guide (2024)",
    "XMM":   "Monster Manual (2025)",
    # 2014 core
    "PHB":   "Player's Handbook (2014)",
    "DMG":   "Dungeon Master's Guide (2014)",
    "MM":    "Monster Manual (2014)",
    # Supplements
    "XGE":   "Xanathar's Guide to Everything",
    "TCE":   "Tasha's Cauldron of Everything",
    "VGM":   "Volo's Guide to Monsters",
    "MTF":   "Mordenkainen's Tome of Foes",
    "MPMM":  "Mordenkainen Presents: Monsters of the Multiverse",
    "FTD":   "Fizban's Treasury of Dragons",
    "BGG":   "Bigby Presents: Glory of the Giants",
    "VRGR":  "Van Richten's Guide to Ravenloft",
    "MOT":   "Mythic Odysseys of Theros",
    "GGR":   "Guildmasters' Guide to Ravnica",
    "ERLW":  "Eberron: Rising from the Last War",
    "EGW":   "Explorer's Guide to Wildemount",
    "SCC":   "Strixhaven: A Curriculum of Chaos",
    "BAM":   "Spelljammer: Boo's Astral Menagerie",
    "AI":    "Acquisitions Incorporated",
    "BMT":   "The Book of Many Things",
    # Forgotten Realms
    "FRHoF": "Forgotten Realms: Heroes of Faerun",
    "FRAiF": "Forgotten Realms: Adventures in Faerun",
    # Adventures (publication order)
    "HotDQ": "Hoard of the Dragon Queen",
    "RoT":   "Rise of Tiamat",
    "PotA":  "Princes of the Apocalypse",
    "OotA":  "Out of the Abyss",
    "CoS":   "Curse of Strahd",
    "SKT":   "Storm King's Thunder",
    "ToA":   "Tomb of Annihilation",
    "WDH":   "Waterdeep: Dragon Heist",
    "WDMM":  "Waterdeep: Dungeon of the Mad Mage",
    "BGDIA": "Baldur's Gate: Descent into Avernus",
    "IDRotF":"Icewind Dale: Rime of the Frostmaiden",
    "WBtW":  "The Wild Beyond the Witchlight",
}

# Maps raw source codes → short labels (used in list views)
SOURCE_SHORT: dict = {
    "XPHB":  "PHB'24",
    "XDMG":  "DMG'24",
    "XMM":   "MM'25",
    "PHB":   "PHB'14",
    "DMG":   "DMG'14",
    "MM":    "MM'14",
    "XGE":   "XGE",
    "TCE":   "TCE",
    "VGM":   "VGM",
    "MTF":   "MTF",
    "MPMM":  "MPMM",
    "FTD":   "FTD",
    "BGG":   "BGG",
    "VRGR":  "VGtR",
    "MOT":   "MOT",
    "GGR":   "GGR",
    "ERLW":  "ERLW",
    "EGW":   "EGW",
    "SCC":   "SCC",
    "BAM":   "BAM",
    "AI":    "AI",
    "BMT":   "BMT",
    "FRHoF": "FRHoF",
    "FRAiF": "FRAiF",
    "HotDQ": "HotDQ",
    "RoT":   "RoT",
    "PotA":  "PotA",
    "OotA":  "OotA",
    "CoS":   "CoS",
    "SKT":   "SKT",
    "ToA":   "ToA",
    "WDH":   "WDH",
    "WDMM":  "WDMM",
    "BGDIA": "BG:DiA",
    "IDRotF":"IDRotF",
    "WBtW":  "WBtW",
}

# Filter dropdown options — derived from SOURCE_FULL so it stays in sync automatically
SOURCE_OPTIONS: list = [("All Sources", None)] + [
    (title, code) for code, title in SOURCE_FULL.items()
]
