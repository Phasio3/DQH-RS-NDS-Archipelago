# items.py — Define every item that can appear in the multiworld item pool.
#
# Each item needs:
#   - a unique name (string, must be stable — never rename after release)
#   - a classification that tells the generator how important it is
#   - a numeric ID = BASE_ID + some offset
#
# Item classifications (from worlds.AutoWorld / BaseClasses):
#   ItemClassification.progression     → required to unlock locations; affects logic
#   ItemClassification.useful          → not required, but helpful to the player
#   ItemClassification.filler          → low-value padding item (used to fill empty slots)
#   ItemClassification.trap            → a trick item; hurts or hinders the player
#   ItemClassification.skip_balancing  → like filler but excluded from early-game balancing
#
# TODO: fill in real item names from your game research.
# TODO: decide the BASE_ID with a value that does not clash with other worlds.
#       Archipelago has a spreadsheet of registered ID ranges; pick a free block.

from BaseClasses import ItemClassification
from typing import NamedTuple


# ── ID range ──────────────────────────────────────────────────────────────────
# TODO: replace 0xDEAD_0000 with your real reserved base ID block.
BASE_ID: int = 0x02000000


# ── Item data structure ───────────────────────────────────────────────────────
# A NamedTuple keeps item definitions readable and immutable.
class DQHRSItemData(NamedTuple):
    classification: ItemClassification
    # offset added to BASE_ID to get the final numeric ID
    id_offset: int


# ── Item table ─────────────────────────────────────────────────────────────────
# Keys are the item names the generator and hint system will use.
# Values are DQHRSItemData instances.
#
# TODO: replace every placeholder entry with real in-game items.
# TODO: keep id_offset values dense and sequential so unused slots stay obvious.
ITEM_TABLE: dict[str, DQHRSItemData] = {
    # ── Progression items ─────────────────────────────────────────────────────
    # These unlock access to locations.  Put anything that can gate progress here.
    "Access_Tootinschleiman_Tomb": DQHRSItemData(ItemClassification.progression, 0x00),
    "Access_Mt_Krakatroda":        DQHRSItemData(ItemClassification.progression, 0x01),
    "Access_Backwoods":            DQHRSItemData(ItemClassification.progression, 0x02),
    "Access_Callmigh_Bluff":       DQHRSItemData(ItemClassification.progression, 0x03),
    "Access_Flucifer_Necropolis":  DQHRSItemData(ItemClassification.progression, 0x04),
    "Access_Flying_Clawtress":     DQHRSItemData(ItemClassification.progression, 0x05),


    # ── Useful items ──────────────────────────────────────────────────────────
    # Nice to have, but the game can be beaten without them.
    "Slime_1": DQHRSItemData(ItemClassification.useful, 0x10),
    "Slime_2": DQHRSItemData(ItemClassification.useful, 0x11),
    "Slime_3": DQHRSItemData(ItemClassification.useful, 0x12),
    "Slime_4": DQHRSItemData(ItemClassification.useful, 0x13),
    "Slime_5": DQHRSItemData(ItemClassification.useful, 0x14),
    "Slime_6": DQHRSItemData(ItemClassification.useful, 0x15),
    "Slime_7": DQHRSItemData(ItemClassification.useful, 0x16),
    "Slime_8": DQHRSItemData(ItemClassification.useful, 0x17),
    "Slime_9": DQHRSItemData(ItemClassification.useful, 0x18),
    "Slime_10": DQHRSItemData(ItemClassification.useful, 0x19),
    "Slime_11": DQHRSItemData(ItemClassification.useful, 0x1A),
    "Slime_12": DQHRSItemData(ItemClassification.useful, 0x1B),
    "Slime_13": DQHRSItemData(ItemClassification.useful, 0x1C),
    "Slime_14": DQHRSItemData(ItemClassification.useful, 0x1D),
    "Slime_15": DQHRSItemData(ItemClassification.useful, 0x1E),
    "Slime_16": DQHRSItemData(ItemClassification.useful, 0x1F),
    "Slime_17": DQHRSItemData(ItemClassification.useful, 0x20),
    "Slime_18": DQHRSItemData(ItemClassification.useful, 0x21),
    "Slime_19": DQHRSItemData(ItemClassification.useful, 0x22),
    "Slime_20": DQHRSItemData(ItemClassification.useful, 0x23),
    "Slime_21": DQHRSItemData(ItemClassification.useful, 0x24),
    "Slime_22": DQHRSItemData(ItemClassification.useful, 0x25),
    "Slime_23": DQHRSItemData(ItemClassification.useful, 0x26),
    "Slime_24": DQHRSItemData(ItemClassification.useful, 0x27),
    "Slime_25": DQHRSItemData(ItemClassification.useful, 0x28),
    "Slime_26": DQHRSItemData(ItemClassification.useful, 0x29),
    "Slime_27": DQHRSItemData(ItemClassification.useful, 0x2A),
    "Slime_28": DQHRSItemData(ItemClassification.useful, 0x2B),
    "Slime_29": DQHRSItemData(ItemClassification.useful, 0x2C),
    "Slime_30": DQHRSItemData(ItemClassification.useful, 0x2D),
    "Slime_31": DQHRSItemData(ItemClassification.useful, 0x2E),
    "Slime_32": DQHRSItemData(ItemClassification.useful, 0x2F),
    "Slime_33": DQHRSItemData(ItemClassification.useful, 0x30),
    "Slime_34": DQHRSItemData(ItemClassification.useful, 0x31),
    "Slime_35": DQHRSItemData(ItemClassification.useful, 0x32),
    "Slime_36": DQHRSItemData(ItemClassification.useful, 0x33),
    "Slime_37": DQHRSItemData(ItemClassification.useful, 0x34),
    "Slime_38": DQHRSItemData(ItemClassification.useful, 0x35),
    "Slime_39": DQHRSItemData(ItemClassification.useful, 0x36),
    "Slime_40": DQHRSItemData(ItemClassification.useful, 0x37),
    "Slime_41": DQHRSItemData(ItemClassification.useful, 0x38),
    "Slime_42": DQHRSItemData(ItemClassification.useful, 0x39),
    "Slime_43": DQHRSItemData(ItemClassification.useful, 0x3A),
    "Slime_44": DQHRSItemData(ItemClassification.useful, 0x3B),
    "Slime_45": DQHRSItemData(ItemClassification.useful, 0x3C),
    "Slime_46": DQHRSItemData(ItemClassification.useful, 0x3D),
    "Slime_47": DQHRSItemData(ItemClassification.useful, 0x3E),
    "Slime_48": DQHRSItemData(ItemClassification.useful, 0x3F),
    "Slime_49": DQHRSItemData(ItemClassification.useful, 0x40),
    "Slime_50": DQHRSItemData(ItemClassification.useful, 0x41),
    "Slime_51": DQHRSItemData(ItemClassification.useful, 0x42),
    "Slime_52": DQHRSItemData(ItemClassification.useful, 0x43),
    "Slime_53": DQHRSItemData(ItemClassification.useful, 0x44),
    "Slime_54": DQHRSItemData(ItemClassification.useful, 0x45),
    "Slime_55": DQHRSItemData(ItemClassification.useful, 0x46),
    "Slime_56": DQHRSItemData(ItemClassification.useful, 0x47),
    "Slime_57": DQHRSItemData(ItemClassification.useful, 0x48),
    "Slime_58": DQHRSItemData(ItemClassification.useful, 0x49),
    "Slime_59": DQHRSItemData(ItemClassification.useful, 0x4A),
    "Slime_60": DQHRSItemData(ItemClassification.useful, 0x4B),
    "Slime_61": DQHRSItemData(ItemClassification.useful, 0x4C),
    "Slime_62": DQHRSItemData(ItemClassification.useful, 0x4D),
    "Slime_63": DQHRSItemData(ItemClassification.useful, 0x4E),
    "Slime_64": DQHRSItemData(ItemClassification.useful, 0x4F),
    "Slime_65": DQHRSItemData(ItemClassification.useful, 0x50),
    "Slime_66": DQHRSItemData(ItemClassification.useful, 0x51),
    "Slime_67": DQHRSItemData(ItemClassification.useful, 0x52),
    "Slime_68": DQHRSItemData(ItemClassification.useful, 0x53),
    "Slime_69": DQHRSItemData(ItemClassification.useful, 0x54),
    "Slime_70": DQHRSItemData(ItemClassification.useful, 0x55),
    "Slime_71": DQHRSItemData(ItemClassification.useful, 0x56),
    "Slime_72": DQHRSItemData(ItemClassification.useful, 0x57),
    "Slime_73": DQHRSItemData(ItemClassification.useful, 0x58),
    "Slime_74": DQHRSItemData(ItemClassification.useful, 0x59),
    "Slime_75": DQHRSItemData(ItemClassification.useful, 0x5A),
    "Slime_76": DQHRSItemData(ItemClassification.useful, 0x5B),
    "Slime_77": DQHRSItemData(ItemClassification.useful, 0x5C),
    "Slime_78": DQHRSItemData(ItemClassification.useful, 0x5D),
    "Slime_79": DQHRSItemData(ItemClassification.useful, 0x5E),
    "Slime_80": DQHRSItemData(ItemClassification.useful, 0x5F),
    "Slime_81": DQHRSItemData(ItemClassification.useful, 0x60),
    "Slime_82": DQHRSItemData(ItemClassification.useful, 0x61),
    "Slime_83": DQHRSItemData(ItemClassification.useful, 0x62),
    "Slime_84": DQHRSItemData(ItemClassification.useful, 0x63),
    "Slime_85": DQHRSItemData(ItemClassification.useful, 0x64),
    "Slime_86": DQHRSItemData(ItemClassification.useful, 0x65),
    "Slime_87": DQHRSItemData(ItemClassification.useful, 0x66),
    "Slime_88": DQHRSItemData(ItemClassification.useful, 0x67),
    "Slime_89": DQHRSItemData(ItemClassification.useful, 0x68),
    "Slime_90": DQHRSItemData(ItemClassification.useful, 0x69),
    "Slime_91": DQHRSItemData(ItemClassification.useful, 0x6A),
    "Slime_92": DQHRSItemData(ItemClassification.useful, 0x6B),
    "Slime_93": DQHRSItemData(ItemClassification.useful, 0x6C),
    "Slime_94": DQHRSItemData(ItemClassification.useful, 0x6D),
    "Slime_95": DQHRSItemData(ItemClassification.useful, 0x6E),
    "Slime_96": DQHRSItemData(ItemClassification.useful, 0x6F),
    "Slime_97": DQHRSItemData(ItemClassification.useful, 0x70),
    "Slime_98": DQHRSItemData(ItemClassification.useful, 0x71),
    "Slime_99": DQHRSItemData(ItemClassification.useful, 0x72),
    "Slime_100": DQHRSItemData(ItemClassification.useful, 0x73),

    "Pompoms Unlocked": DQHRSItemData(ItemClassification.useful, 0x74), # addr : 0x0214180
    "Chests Unlocked": DQHRSItemData(ItemClassification.useful, 0x75), # addr : 0x0214180
    "Catnips Unlocked": DQHRSItemData(ItemClassification.useful, 0x76), # addr : 0x0214188
    "Rockbombs Unlocked": DQHRSItemData(ItemClassification.useful, 0x77), # addr : 0x021418C
    "Spooklear Bombs Unlocked": DQHRSItemData(ItemClassification.useful, 0x78), # addr : 0x0214190
    "Bombshells Unlocked": DQHRSItemData(ItemClassification.useful, 0x79), # addr : 0x0214194
    "Obelisks Unlocked": DQHRSItemData(ItemClassification.useful, 0x7A), # addr : 0x0214198
    "Wooden Arrows Unlocked": DQHRSItemData(ItemClassification.useful, 0x7B), # addr : 0x021419C
    "Iron Arrows Unlocked": DQHRSItemData(ItemClassification.useful, 0x7C), # addr : 0x02141A0
    "Golden Arrows Unlocked": DQHRSItemData(ItemClassification.useful, 0x7D), # addr : 0x02141A4
    "Boulders Unlocked": DQHRSItemData(ItemClassification.useful, 0x7E), # addr : 0x02141A8
    "Oaken Clubs Unlocked": DQHRSItemData(ItemClassification.useful, 0x7F), # addr : 0x02141AC
    "Irritaballs Unlocked": DQHRSItemData(ItemClassification.useful, 0x80), # addr : 0x02141B4
    "Destructiballs Unlocked": DQHRSItemData(ItemClassification.useful, 0x81), # addr : 0x02141B8
    "Girders Unlocked": DQHRSItemData(ItemClassification.useful, 0x82), # addr : 0x02141BC
    "Holy Waters Unlocked": DQHRSItemData(ItemClassification.useful, 0x83), # addr : 0x02141C0
    "Boomerangs Unlocked": DQHRSItemData(ItemClassification.useful, 0x84), # addr : 0x02141C4
    "Edged Boomerangs Unlocked": DQHRSItemData(ItemClassification.useful, 0x85), # addr : 0x02141C8
    "BS-1 Croozes Unlocked": DQHRSItemData(ItemClassification.useful, 0x86), # addr : 0x02141CC
    "BS-2 Blue Streaks Unlocked": DQHRSItemData(ItemClassification.useful, 0x87), # addr : 0x02141D0
    "BS-3 Slimahawks Unlocked": DQHRSItemData(ItemClassification.useful, 0x88), # addr : 0x02141D4
    "Fire Waters Unlocked": DQHRSItemData(ItemClassification.useful, 0x89), # addr : 0x02141D8
    "Thousandweights Unlocked": DQHRSItemData(ItemClassification.useful, 0x8A), # addr : 0x02141DC
    "Chimaera Wings Unlocked": DQHRSItemData(ItemClassification.useful, 0x8B), # addr : 0x02141E0
    "Shurikens Unlocked": DQHRSItemData(ItemClassification.useful, 0x8C), # addr : 0x02141E4
    "Slime Knights Unlocked": DQHRSItemData(ItemClassification.useful, 0x8D), # addr : 0x02141E8
    "Steel Broadswoards Unlocked": DQHRSItemData(ItemClassification.useful, 0x8E), # addr : 0x02141EC
    "Miracle Swords Unlocked": DQHRSItemData(ItemClassification.useful, 0x8F), # addr : 0x02141F0
    "Bastard Swords Unlocked": DQHRSItemData(ItemClassification.useful, 0x90), # addr : 0x02141F4
    "Metal King Swords Unlocked": DQHRSItemData(ItemClassification.useful, 0x91), # addr : 0x02141F8
    "Iron Shields Unlocked": DQHRSItemData(ItemClassification.useful, 0x92), # addr : 0x02141FC
    "Mirror Shields Unlocked": DQHRSItemData(ItemClassification.useful, 0x93), # addr : 0x0214200
    "Metal King Shields Unlocked": DQHRSItemData(ItemClassification.useful, 0x94), # addr : 0x0214204
    "Medicinal Herbs Unlocked": DQHRSItemData(ItemClassification.useful, 0x95), # addr : 0x0214208
    "Strong Medicines Unlocked": DQHRSItemData(ItemClassification.useful, 0x96), # addr : 0x021420C
    "Special Medicines Unlocked": DQHRSItemData(ItemClassification.useful, 0x97), # addr : 0x0214210
    "Goddess Statues Unlocked": DQHRSItemData(ItemClassification.useful, 0x98), # addr : 0x0214214
    "Vulcan Guns Unlocked": DQHRSItemData(ItemClassification.useful, 0x99), # addr : 0x0214218
    "Vulcan Pellets Unlocked": DQHRSItemData(ItemClassification.useful, 0x9A), # addr : 0x021421C
    "Vulcan Bullets Unlocked": DQHRSItemData(ItemClassification.useful, 0x9B), # addr : 0x0214220
    "Vulcan Shells Unlocked": DQHRSItemData(ItemClassification.useful, 0x9C), # addr : 0x0214224
    "Lightning Staves Unlocked": DQHRSItemData(ItemClassification.useful, 0x9D), # addr : 0x0214228
    "Hell Scythes Unlocked": DQHRSItemData(ItemClassification.useful, 0x9E), # addr : 0x021422C
    "Chilli Peppers Unlocked": DQHRSItemData(ItemClassification.useful, 0x9F), # addr : 0x0214230
    "Holy Crystals Unlocked": DQHRSItemData(ItemClassification.useful, 0xA0), # addr : 0x0214234
    "Devil's Tails Unlocked": DQHRSItemData(ItemClassification.useful, 0xA1), # addr : 0x0214238
    "Gold Bars Unlocked": DQHRSItemData(ItemClassification.useful, 0xA2), # addr : 0x021423C
    "Toy Slimes Unlocked": DQHRSItemData(ItemClassification.useful, 0xA3), # addr : 0x0214240
    "Clap Traps Unlocked": DQHRSItemData(ItemClassification.useful, 0xA4), # addr : 0x0214244
    "Cloaking Devices Unlocked": DQHRSItemData(ItemClassification.useful, 0xA5), # addr : 0x0214248
    "Kaboomamites Unlocked": DQHRSItemData(ItemClassification.useful, 0xA6), # addr : 0x021424C
    "Power Tablets Unlocked": DQHRSItemData(ItemClassification.useful, 0xA7), # addr : 0x0214250
    "Overdrive Tablets Unlocked": DQHRSItemData(ItemClassification.useful, 0xA8), # addr : 0x0214254
    "Weapon Tablets Unlocked": DQHRSItemData(ItemClassification.useful, 0xA9), # addr : 0x0214258
    "Orichalcums Unlocked": DQHRSItemData(ItemClassification.useful, 0xAA), # addr : 0x021425C
    "Orichalslimes Unlocked": DQHRSItemData(ItemClassification.useful, 0xAB), # addr : 0x0214260
    "Meteorites Unlocked": DQHRSItemData(ItemClassification.useful, 0xAC), # addr : 0x0214264
    "Kafrizzles Unlocked": DQHRSItemData(ItemClassification.useful, 0xAD), # addr : 0x0214268
    "Hero Swords Unlocked": DQHRSItemData(ItemClassification.useful, 0xAE), # addr : 0x021426C

    # ── Filler items ──────────────────────────────────────────────────────────
    # These pad the pool when the real items run out.
    # Usually consumables or currency.
    "100 Gold": DQHRSItemData(ItemClassification.filler, 0xAF),

    # ── Traps ─────────────────────────────────────────────────────────────────
    # Optional; only add these if the game supports receiving bad things.
    # "TODO_Trap_1": DQHRSItemData(ItemClassification.trap, 0x30),
}

# ── Helper: build name → id mapping ───────────────────────────────────────────
# This is what the World class will expose as item_name_to_id.
ITEM_NAME_TO_ID: dict[str, int] = {
    name: BASE_ID + data.id_offset
    for name, data in ITEM_TABLE.items()
}