# locations.py — Define every location where an item can be placed.
#
# A "location" is any spot in the game where an item could logically exist.
#
# Each location needs:
#   - a unique name (display-only; can be renamed freely during development,
#     since it's just a label — see slime_id below for what actually matters)
#   - a numeric ID = BASE_ID + id_offset (NEVER change this once a seed has
#     been generated and shared — this is what AP actually tracks)
#   - a region name (must match a Region created in __init__.py)
#   - the real in-game slime_id rescued at that spot, as read from
#     SAVED_SLIME_ADDR in client.py. This is what ties the memory table to
#     the location, independently of how the location is named.
#   - for "X unlocked" (bestiary) locations only: monster_id, the 0-based
#     INDEX of that monster's 4-byte entry in the table read from
#     MONSTER_ID_ADDR_BEGIN in client.py (entry 0 = bytes 0-3, entry 1 =
#     bytes 4-7, etc). Defaults to -1 for every non-bestiary location.
#
# Workflow while researching the game:
#   Every entry starts with a placeholder name ("Chest_N") and slime_id = N
#   as a guess. As you actually rescue each slime in-game and observe its
#   real ID (e.g. via RAM Watch), rename the entry and fix its slime_id to
#   match reality. Nothing else needs to change — id_offset stays put, and
#   client.py never needs to be touched again for this. Bestiary entries
#   follow the exact same logic with monster_id instead of slime_id: the
#   values below were inferred from an observed save (see CHECKLIST.md §2),
#   confirm each one in-game before relying on it for real generation.

from typing import NamedTuple
from .items import BASE_ID


# ── Location data structure ───────────────────────────────────────────────────
class DQHRSLocationData(NamedTuple):
    id_offset: int
    region_name: str
    slime_id: int
    monster_id: int = -1  # index (0-based) in the bestiary table; -1 = not a bestiary location
    tank_id: int = -1   # ID brut du combat (1-36 / 0x01-0x24) ; -1 = non concerné


# ── Location table ────────────────────────────────────────────────────────────
# TODO: as you confirm each real slime_id in-game, rename the entry and fix
#       its slime_id value. id_offset must stay exactly as-is.
LOCATION_TABLE: dict[str, DQHRSLocationData] = {
    # ────────────────────────────── SLIMES ────────────────────────────────────
    # ── Region: Forewood Forest ───────────────────────────────────────────────
    # part 1: the first half of the forest, where you start the game
    "Swotsy saved": DQHRSLocationData(0x104, "Forewood_Forest_part1", 4),
    "His Wobbliness saved":    DQHRSLocationData(0x105, "Forewood_Forest_part1", 5),
    "Mother Glooperior saved":    DQHRSLocationData(0x108, "Forewood_Forest_part1", 8),
    "Stony saved":   DQHRSLocationData(0x10F, "Forewood_Forest_part1", 15),
    "Baron Blubba saved":   DQHRSLocationData(0x110, "Forewood_Forest_part1", 16),
    "Peewee saved":   DQHRSLocationData(0x114, "Forewood_Forest_part1", 20),
    "Bubbilly saved":   DQHRSLocationData(0x112, "Forewood_Forest_part1", 18),

    # part 2: the second half of the forest, where you can go after rescuing the first 8 slimes
    "Big Daddy saved": DQHRSLocationData(0x100, "Forewood_Forest", 0),
    "Mama Mia saved":    DQHRSLocationData(0x101, "Forewood_Forest", 1),
    "Bo saved":    DQHRSLocationData(0x102, "Forewood_Forest", 2),
    "Hooly saved":    DQHRSLocationData(0x103, "Forewood_Forest", 3),
    "Her Wobbliness saved":    DQHRSLocationData(0x106, "Forewood_Forest", 6),
    "Gluttonella saved":    DQHRSLocationData(0x107, "Forewood_Forest", 7),
    "Curate Rollo saved":    DQHRSLocationData(0x109, "Forewood_Forest", 9),
    "Flancisco saved":   DQHRSLocationData(0x10A, "Forewood_Forest", 10),
    "Goosashi saved":   DQHRSLocationData(0x10B, "Forewood_Forest", 11),
    "Gooshido saved":   DQHRSLocationData(0x10C, "Forewood_Forest", 12),
    "Tokyo Tom saved":   DQHRSLocationData(0x10D, "Forewood_Forest", 13),
    "Flanpa saved":   DQHRSLocationData(0x10E, "Forewood_Forest", 14),

    # ── Region: Tootinschleiman's Tomb ────────────────────────────────────────
    "Perry saved":   DQHRSLocationData(0x111, "Tootinschleimans_Tomb", 17),
    "Jumpy saved":   DQHRSLocationData(0x113, "Tootinschleimans_Tomb", 19),
    "George saved":   DQHRSLocationData(0x115, "Tootinschleimans_Tomb", 21),
    "Dragory saved":   DQHRSLocationData(0x116, "Tootinschleimans_Tomb", 22),
    "Gootrude saved":   DQHRSLocationData(0x117, "Tootinschleimans_Tomb", 23),
    "Goodith saved":   DQHRSLocationData(0x118, "Tootinschleimans_Tomb", 24),
    "Goolia saved":   DQHRSLocationData(0x119, "Tootinschleimans_Tomb", 25),
    "Goozanna saved":   DQHRSLocationData(0x11A, "Tootinschleimans_Tomb", 26),
    "Merc saved":   DQHRSLocationData(0x11B, "Tootinschleimans_Tomb", 27),
    "Splodgy Dave saved":   DQHRSLocationData(0x11C, "Tootinschleimans_Tomb", 28),
    "Splatrick saved":   DQHRSLocationData(0x11D, "Tootinschleimans_Tomb", 29),
    "Curator saved":   DQHRSLocationData(0x11E, "Tootinschleimans_Tomb", 30),
    "Curedon Bleu saved":   DQHRSLocationData(0x11F, "Tootinschleimans_Tomb", 31),
    "Swellington saved":   DQHRSLocationData(0x120, "Tootinschleimans_Tomb", 32),
    "Goopid saved":   DQHRSLocationData(0x121, "Tootinschleimans_Tomb", 33),
    "Goobrielle saved":   DQHRSLocationData(0x122, "Tootinschleimans_Tomb", 34),
    "Namby saved":   DQHRSLocationData(0x123, "Tootinschleimans_Tomb", 35),

    # ── Region: Mt Krakatroda ─────────────────────────────────────────────────
    "Pamby saved":   DQHRSLocationData(0x124, "Mt_Krakatroda", 36),
    "Kworry saved":   DQHRSLocationData(0x125, "Mt_Krakatroda", 37),
    "Rocky saved":   DQHRSLocationData(0x126, "Mt_Krakatroda", 38),
    "Bud saved":   DQHRSLocationData(0x127, "Mt_Krakatroda", 39),
    "Rustle Sprout saved":   DQHRSLocationData(0x128, "Mt_Krakatroda", 40),
    "Flantenna saved":   DQHRSLocationData(0x129, "Mt_Krakatroda", 41),
    "Shelby saved":   DQHRSLocationData(0x12A, "Mt_Krakatroda", 42),
    "Plopstar saved":   DQHRSLocationData(0x12B, "Mt_Krakatroda", 43),
    "Stathur saved":   DQHRSLocationData(0x12C, "Mt_Krakatroda", 44),
    "Dragoola saved":   DQHRSLocationData(0x12D, "Mt_Krakatroda", 45),
    "Spot saved":   DQHRSLocationData(0x12E, "Mt_Krakatroda", 46),
    "Patch saved":   DQHRSLocationData(0x12F, "Mt_Krakatroda", 47),
    "Startist saved":   DQHRSLocationData(0x130, "Mt_Krakatroda", 48),
    "Drake saved":   DQHRSLocationData(0x131, "Mt_Krakatroda", 49),
    "Mag Max saved":   DQHRSLocationData(0x132, "Mt_Krakatroda", 50),
    "Poxie saved":   DQHRSLocationData(0x133, "Mt_Krakatroda", 51),
    "Soapia saved":   DQHRSLocationData(0x134, "Mt_Krakatroda", 52),

    # ── Region: Backwoods ─────────────────────────────────────────────────────
    "Sliminator saved":   DQHRSLocationData(0x135, "Backwoods", 53),
    "Speckles saved":   DQHRSLocationData(0x136, "Backwoods", 54),
    "Sheala saved":   DQHRSLocationData(0x137, "Backwoods", 55),
    "Tickled Pink saved":   DQHRSLocationData(0x138, "Backwoods", 56),
    "Luminum saved":   DQHRSLocationData(0x139, "Backwoods", 57),
    "Early Burly saved":   DQHRSLocationData(0x13A, "Backwoods", 58),

    # ── Region: Callmigh Bluff ────────────────────────────────────────────────
    "Anjello saved":   DQHRSLocationData(0x13B, "Callmigh_Bluff", 59),
    "Cheruboing saved":   DQHRSLocationData(0x13C, "Callmigh_Bluff", 60),
    "Winkles saved":   DQHRSLocationData(0x13D, "Callmigh_Bluff", 61),
    "Michelle saved":   DQHRSLocationData(0x13E, "Callmigh_Bluff", 62),
    "Diablob saved":   DQHRSLocationData(0x13F, "Callmigh_Bluff", 63),
    "Frankenslime saved":   DQHRSLocationData(0x140, "Callmigh_Bluff", 64),
    "Dummy saved":   DQHRSLocationData(0x141, "Callmigh_Bluff", 65),
    "Tickles saved":   DQHRSLocationData(0x142, "Callmigh_Bluff", 66),
    "Pebbles saved":   DQHRSLocationData(0x143, "Callmigh_Bluff", 67),
    "Bouncer saved":   DQHRSLocationData(0x144, "Callmigh_Bluff", 68),
    "Goochie saved":   DQHRSLocationData(0x145, "Callmigh_Bluff", 69),
    "Flopsy saved":   DQHRSLocationData(0x146, "Callmigh_Bluff", 70),
    "Itsy saved":   DQHRSLocationData(0x147, "Callmigh_Bluff", 71),
    "Bitsy saved":   DQHRSLocationData(0x148, "Callmigh_Bluff", 72),
    "Teeny saved":   DQHRSLocationData(0x149, "Callmigh_Bluff", 73),

    # ── Region: Flucifer's Necropolis ─────────────────────────────────────────
    "Weeny saved":   DQHRSLocationData(0x14A, "Flucifers_Necropolis", 74),
    "Fangummy Bob saved":   DQHRSLocationData(0x14B, "Flucifers_Necropolis", 75),
    "Wild Fang saved":   DQHRSLocationData(0x14C, "Flucifers_Necropolis", 76),
    "Clawdia saved":   DQHRSLocationData(0x14D, "Flucifers_Necropolis", 77),
    "Clawrence saved":   DQHRSLocationData(0x14E, "Flucifers_Necropolis", 78),
    "Pigummy saved":   DQHRSLocationData(0x14F, "Flucifers_Necropolis", 79),
    "Lady Poly saved":   DQHRSLocationData(0x150, "Flucifers_Necropolis", 80),
    "Lord Roly saved":   DQHRSLocationData(0x151, "Flucifers_Necropolis", 81),
    "Count Calories saved":   DQHRSLocationData(0x152, "Flucifers_Necropolis", 82),
    "Sir Sudsy saved":   DQHRSLocationData(0x153, "Flucifers_Necropolis", 83),
    "Lord Lard saved":   DQHRSLocationData(0x154, "Flucifers_Necropolis", 84),
    "Viscous saved":   DQHRSLocationData(0x155, "Flucifers_Necropolis", 85),
    "Jewelian saved":   DQHRSLocationData(0x156, "Flucifers_Necropolis", 86),
    "Chronicler saved":   DQHRSLocationData(0x157, "Flucifers_Necropolis", 87),
    "Blingaling saved":   DQHRSLocationData(0x158, "Flucifers_Necropolis", 88),
    "Flan Spinel saved":   DQHRSLocationData(0x159, "Flucifers_Necropolis", 89),
    "Mrs. Hooly saved":   DQHRSLocationData(0x15A, "Flucifers_Necropolis", 90),

    # ── Region: Flying Clawtress ──────────────────────────────────────────────
    "Mr. Hooly saved":   DQHRSLocationData(0x15B, "Flying_Clawtress", 91),
    "Gregg saved":   DQHRSLocationData(0x15C, "Flying_Clawtress", 92),
    "Eggbard saved":   DQHRSLocationData(0x15D, "Flying_Clawtress", 93),
    "Meggan saved":   DQHRSLocationData(0x15E, "Flying_Clawtress", 94),
    "Bunny saved":   DQHRSLocationData(0x15F, "Flying_Clawtress", 95),
    "Morrie-Morrie saved":   DQHRSLocationData(0x160, "Flying_Clawtress", 96),
    "Slimechanic saved":   DQHRSLocationData(0x161, "Flying_Clawtress", 97),
    "Sliborg saved":   DQHRSLocationData(0x162, "Flying_Clawtress", 98),
    "Roboglop saved":   DQHRSLocationData(0x163, "Flying_Clawtress", 99),

    
    # ─────────────────────────────── BOSS ─────────────────────────────────────
    # ── Bough Beater ──────────────────────────────────────────────────────────
    "Bough Beater defeated": DQHRSLocationData(0x164, "Forewood_Forest_part1", 100),

    # ── Pot Belly ─────────────────────────────────────────────────────────────
    "Pot Belly defeated": DQHRSLocationData(0x165, "Mt_Krakatroda", 100),

    # ── Harvest Loon ──────────────────────────────────────────────────────────
    "Harvest Loon defeated": DQHRSLocationData(0x166, "Callmigh_Bluff", 100),

    # ── Don Clawleone ─────────────────────────────────────────────────────────
    "Don Clawleone defeated": DQHRSLocationData(0x167, "Flying_Clawtress", 100),

    # ── Lickity Spit ──────────────────────────────────────────────────────────
    "Lickity Spit defeated": DQHRSLocationData(0x168, "Flucifers_Necropolis", 100),

    # ───────────────────────────── MONSTERS ───────────────────────────────────
    "Platypunk unlocked": DQHRSLocationData(0x169, "Forewood_Forest_part1", 100, monster_id=0),
    "Jailcat unlocked": DQHRSLocationData(0x16A, "Forewood_Forest_part1", 100, monster_id=1),
    "Dracky unlocked": DQHRSLocationData(0x16B, "Forewood_Forest_part1", 100, monster_id=2),
    "Mischievous Mole unlocked": DQHRSLocationData(0x16C, "Forewood_Forest_part1", 100, monster_id=3),
    "Bunicorn unlocked": DQHRSLocationData(0x16D, "Forewood_Forest", 100, monster_id=4),
    "Picksy unlocked": DQHRSLocationData(0x16E, "Tootinschleimans_Tomb", 100, monster_id=5),
    "Hammerhood unlocked": DQHRSLocationData(0x16F, "Tootinschleimans_Tomb", 100, monster_id=6),
    "Goodybag unlocked": DQHRSLocationData(0x170, "Tootinschleimans_Tomb", 100, monster_id=7),
    "Mimic unlocked": DQHRSLocationData(0x171, "Tootinschleimans_Tomb", 100, monster_id=8),
    "Cactiball unlocked": DQHRSLocationData(0x172, "Tootinschleimans_Tomb", 100, monster_id=9),
    "Ghost unlocked": DQHRSLocationData(0x173, "Mt_Krakatroda", 100, monster_id=10),
    "Imp unlocked": DQHRSLocationData(0x174, "Mt_Krakatroda", 100, monster_id=11),
    "Wyrtle unlocked": DQHRSLocationData(0x175, "Mt_Krakatroda", 100, monster_id=12),
    "Living statue unlocked": DQHRSLocationData(0x176, "Mt_Krakatroda", 100, monster_id=13),
    "Walking Corpse unlocked": DQHRSLocationData(0x177, "Mt_Krakatroda", 100, monster_id=14),
    "Dancing Flame unlocked": DQHRSLocationData(0x178, "Flucifers_Necropolis", 100, monster_id=15),
    "Jinkster unlocked": DQHRSLocationData(0x179, "Flucifers_Necropolis", 100, monster_id=16),
    "Restless Armor unlocked": DQHRSLocationData(0x17A, "Flying_Clawtress", 100, monster_id=17),
    "Killing Machine unlocked": DQHRSLocationData(0x17B, "Flying_Clawtress", 100, monster_id=18),
    "Golem unlocked": DQHRSLocationData(0x17C, "Flying_Clawtress", 100, monster_id=19),

    # ────────────────────────────── TANKS ────────────────────────────────────
        # ─────────────────────────── COMBATS DE TANK ──────────────────────────────
    # 36 combats, tank_id de 1 (0x01) à 36 (0x24), lus à TANK_BATTLE_ID_ADDR.
    # TODO: renommer chaque "TODO_Tank_Battle_XX" avec le vrai nom du combat une
    # fois identifié en jeu, et corriger la région si besoin (mise à "Boingburg"
    # par défaut car on ne sait pas encore où chaque combat a lieu).
    "Websy tank battle won": DQHRSLocationData(0x17D, "Boingburg", 100, tank_id=0x01),
    "TODO_Tank_Battle_02 defeated": DQHRSLocationData(0x17E, "Boingburg", 100, tank_id=0x02),
    "TODO_Tank_Battle_03 defeated": DQHRSLocationData(0x17F, "Boingburg", 100, tank_id=0x03),
    "Pyjamas tank battle won": DQHRSLocationData(0x180, "Boingburg", 100, tank_id=0x04),
    "TODO_Tank_Battle_05 defeated": DQHRSLocationData(0x181, "Boingburg", 100, tank_id=0x05),
    "TODO_Tank_Battle_06 defeated": DQHRSLocationData(0x182, "Boingburg", 100, tank_id=0x06),
    "TODO_Tank_Battle_07 defeated": DQHRSLocationData(0x183, "Boingburg", 100, tank_id=0x07),
    "TODO_Tank_Battle_08 defeated": DQHRSLocationData(0x184, "Boingburg", 100, tank_id=0x08),
    "Guaca Moly tank battle won": DQHRSLocationData(0x185, "Boingburg", 100, tank_id=0x09),
    "TODO_Tank_Battle_0A defeated": DQHRSLocationData(0x186, "Boingburg", 100, tank_id=0x0A),
    "TODO_Tank_Battle_0B defeated": DQHRSLocationData(0x187, "Boingburg", 100, tank_id=0x0B),
    "Slival first tank battle won": DQHRSLocationData(0x188, "Boingburg", 100, tank_id=0x0C),
    "TODO_Tank_Battle_0D defeated": DQHRSLocationData(0x189, "Boingburg", 100, tank_id=0x0D),
    "TODO_Tank_Battle_0E defeated": DQHRSLocationData(0x18A, "Boingburg", 100, tank_id=0x0E),
    "TODO_Tank_Battle_0F defeated": DQHRSLocationData(0x18B, "Boingburg", 100, tank_id=0x0F),
    "Bugsy tank battle won": DQHRSLocationData(0x18C, "Boingburg", 100, tank_id=0x10),
    "Dracky Dan tank battle won": DQHRSLocationData(0x18D, "Boingburg", 100, tank_id=0x11),
    "Molone tank battle won": DQHRSLocationData(0x18E, "Boingburg", 100, tank_id=0x12),
    "Slival second tank battle won": DQHRSLocationData(0x18F, "Boingburg", 100, tank_id=0x13),
    "TODO_Tank_Battle_14 defeated": DQHRSLocationData(0x190, "Boingburg", 100, tank_id=0x14),
    "TODO_Tank_Battle_15 defeated": DQHRSLocationData(0x191, "Boingburg", 100, tank_id=0x15),
    "TODO_Tank_Battle_16 defeated": DQHRSLocationData(0x192, "Boingburg", 100, tank_id=0x16),
    "TODO_Tank_Battle_17 defeated": DQHRSLocationData(0x193, "Boingburg", 100, tank_id=0x17),
    "TODO_Tank_Battle_18 defeated": DQHRSLocationData(0x194, "Boingburg", 100, tank_id=0x18),
    "TODO_Tank_Battle_19 defeated": DQHRSLocationData(0x195, "Boingburg", 100, tank_id=0x19),
    "TODO_Tank_Battle_1A defeated": DQHRSLocationData(0x196, "Boingburg", 100, tank_id=0x1A),
    "TODO_Tank_Battle_1B defeated": DQHRSLocationData(0x197, "Boingburg", 100, tank_id=0x1B),
    "TODO_Tank_Battle_1C defeated": DQHRSLocationData(0x198, "Boingburg", 100, tank_id=0x1C),
    "Slival third tank battle won": DQHRSLocationData(0x199, "Boingburg", 100, tank_id=0x1D),
    "TODO_Tank_Battle_1E defeated": DQHRSLocationData(0x19A, "Boingburg", 100, tank_id=0x1E),
    "Rusty tank battle won": DQHRSLocationData(0x19B, "Boingburg", 100, tank_id=0x1F),
    "TODO_Tank_Battle_20 defeated": DQHRSLocationData(0x19C, "Boingburg", 100, tank_id=0x20),
    "Hollow Kitty tank battle won": DQHRSLocationData(0x19D, "Boingburg", 100, tank_id=0x21),
    "TODO_Tank_Battle_22 defeated": DQHRSLocationData(0x19E, "Boingburg", 100, tank_id=0x22),
    "TODO_Tank_Battle_23 defeated": DQHRSLocationData(0x19F, "Boingburg", 100, tank_id=0x23),
    "TODO_Tank_Battle_24 defeated": DQHRSLocationData(0x1A0, "Boingburg", 100, tank_id=0x24),
}

# ── Helper: build name → id mapping ───────────────────────────────────────────
# Used by the World class (item_name_to_id / location_name_to_id) and by the
# webhost / hints to display a human-readable name for each location.
LOCATION_NAME_TO_ID: dict[str, int] = {
    name: BASE_ID + data.id_offset
    for name, data in LOCATION_TABLE.items()
}

# ── Goals ─────────────────────────────────────────────────────────────────────
FINAL_BOSS_LOCATION_ID: int = LOCATION_NAME_TO_ID["Don Clawleone defeated"]

# Les boss et monstres ont slime_id = 100 : on filtre donc sur < 100.
SLIME_LOCATION_IDS: frozenset[int] = frozenset(
    BASE_ID + data.id_offset for data in LOCATION_TABLE.values() if data.slime_id < 100
)

# ── Helper: build slime_id → AP location id mapping ───────────────────────────
# This is what client.py actually uses. It never needs to change when you
# rename a location — only when a slime_id value turns out to be wrong.
SLIME_ID_TO_LOCATION_ID: dict[int, int] = {
    data.slime_id: BASE_ID + data.id_offset
    for data in LOCATION_TABLE.values()
}
# ATTENTION : tous les boss ET tous les monstres du bestiaire partagent le
# même slime_id=100 (copié-collé lors de leur création). Le dict ci-dessus
# n'en garde donc qu'UN SEUL par clé — client.py ne s'en sert heureusement
# pas pour les boss (recherche par nom) ni pour le bestiaire (voir
# MONSTER_ID_TO_LOCATION_ID ci-dessous), mais à corriger si un jour un autre
# bout de code veut chercher une location "boss" ou "unlocked" par cette voie.

# ── Helper: build monster_id → AP location id mapping ─────────────────────────
# Miroir de SLIME_ID_TO_LOCATION_ID, mais pour le bestiaire. monster_id == -1
# est le défaut pour toute location qui n'est pas un déblocage de monstre :
# on l'exclut explicitement pour ne jamais associer -1 à une vraie location.
MONSTER_ID_TO_LOCATION_ID: dict[int, int] = {
    data.monster_id: BASE_ID + data.id_offset
    for data in LOCATION_TABLE.values()
    if data.monster_id != -1
}

# ─────────────────────────── COMBATS DE TANK ──────────────────────────────
TANK_ID_TO_LOCATION_ID: dict[int, int] = {
    data.tank_id: BASE_ID + data.id_offset
    for data in LOCATION_TABLE.values()
    if data.tank_id != -1
}

# ── Convenience: list all region names used ───────────────────────────────────
ALL_REGIONS: set[str] = {
    "Menu",
    "Boingburg",
    "Forewood_Forest_part1",
    "Forewood_Forest",
    "Tootinschleimans_Tomb",
    "Mt_Krakatroda",
    "Backwoods",
    "Callmigh_Bluff",
    "Flucifers_Necropolis",
    "Flying_Clawtress",
}