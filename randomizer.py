from __future__ import annotations

import logging
import random

import worlds._bizhawk as bizhawk

logger = logging.getLogger("Client")


# BizHawk memory domain we read from / write to.
RAM_DOMAIN = "Main RAM"

TANK_BATTLE_FLAG_ADDR = 0x0013B487

# Inventory entries use four bytes: unlocked flag, then owned count.
INVENTORY_START_ADDR = 0x00214180
INVENTORY_LAST_ADDR = 0x0021426D
INVENTORY_STRIDE = 4
INVENTORY_SLOT_COUNT = (INVENTORY_LAST_ADDR - INVENTORY_START_ADDR) // INVENTORY_STRIDE + 1
INVENTORY_SIZE = INVENTORY_SLOT_COUNT * INVENTORY_STRIDE

AMMO_START_ADDR = 0x0013B40E
AMMO_END_ADDR = 0x0013B42B
AMMO_SLOT_COUNT = AMMO_END_ADDR - AMMO_START_ADDR + 1

# Loaded ammo is separate from the inventory and must be included in the source pool.
LOADED_AMMO_START_ADDR = 0x0013B189
LOADED_AMMO_END_ADDR = 0x0013B1A6
LOADED_AMMO_SLOT_COUNT = LOADED_AMMO_END_ADDR - LOADED_AMMO_START_ADDR + 1

# Pebble ID used to pad empty ammo slots.
PEBBLE_ID = 0x65

# Validate fixed-size memory ranges at import time.
assert AMMO_SLOT_COUNT == 30, "The ammo range must be exactly 30 bytes"
assert LOADED_AMMO_SLOT_COUNT == 30, "The loaded ammo range must be exactly 30 bytes"


# Inventory slot → in-game ammo ID overrides.
ITEM_ID_BY_SLOT: dict[int, int] = {
    0: 0x29, # Pompoms
    1: 0x25, # Chest
    2: 0x1A, # Catnip
    3: 0x05, # Rockbomb
    4: 0x89, # Spooklear Bomb
    5: 0x0D, # Bombshell
    6: 0x21, # Obelisk
    7: 0x26, # Wooden Arrow
    8: 0x6A, # Iron Arrow
    9: 0x6B, # Golden Arrow
    10: 0x65, # Boulder
    11: 0x48, # Oaken Club
    12: 0x22, # Iron ball
    13: 0x6F, # Irritaball
    14: 0x70, # Destructiball
    15: 0x27, # Girder
    16: 0x5F, # Holy Water
    17: 0x49, # Boomerang
    18: 0x85, # Edged Boomerang
    19: 0x67, # BS-1 Crooze
    20: 0x68, # BS-2 Blue Streak
    21: 0x69, # BS-3 Slimahawk
    22: 0x16, # Fire Water
    23: 0x33, # Thousandweight
    24: 0x30, # Chimaera Wing
    25: 0x72, # Shuriken
    26: 0x07, # Slime Knight
    27: 0x6E, # Steel Broadwoard
    28: 0x87, # Miracle Sword
    29: 0x86, # Bastard Sword
    30: 0x88, # Metal King Sword
    31: 0x3C, # Iron Shield
    32: 0x10, # Mirror Shield
    33: 0x64, # Metal King Shield
    34: 0x7F, # Medicinal Herb
    35: 0x80, # Strong Medicine
    36: 0x81, # Special Medicine
    37: 0x5E, # Goddess Statues
    38: 0x12, # Vulcan Gun
    39: 0x13, # Vulcan Pellets
    40: 0x6C, # Vulcan Bullets
    41: 0x6D, # Vulcan Shells
    42: 0x8B, # Lightning Staff
    43: 0x8A, # Hell Scythe
    44: 0x15, # Chilli Pepper
    45: 0x61, # Holy Crystal
    46: 0x60, # Devil's Tail
    47: 0x5D, # Gold Bar
    48: 0x14, # Toy Slime
    49: 0x93, # Clap Trap
    50: 0x92, # Cloaking Device
    51: 0x84, # Kaboomamite
    52: 0x8F, # Power Tablet
    53: 0x90, # Overdrive Tablet
    54: 0x91, # Weapon Tablet
    55: 0x8E, # Orichalcum
    56: 0x8D, # Orichalslime
    57: 0x06, # Meteorite
    58: 0x0A, # Kafrizzle
    59: 0x8C,  # Hero Sword
}


def item_id_for_slot(slot: int) -> int:
    """Convert an inventory slot number into the item ID the ammo list expects."""
    return ITEM_ID_BY_SLOT.get(slot, slot)


# Known IDs used to filter invalid loaded-ammo bytes.
VALID_ITEM_IDS: frozenset[int] = frozenset(ITEM_ID_BY_SLOT.values())


def parse_inventory(block: bytes) -> list[int]:
    """Turn the raw inventory bytes into a list with one entry per owned item copy.

    Example: 3 Pompoms and 2 of item slot 5 -> [id0, id0, id0, id5, id5]
    """
    owned: list[int] = []
    for slot in range(INVENTORY_SLOT_COUNT):
        unlocked = block[slot * INVENTORY_STRIDE]
        count = block[slot * INVENTORY_STRIDE + 1]
        if unlocked == 1 and count > 0:
            owned.extend([item_id_for_slot(slot)] * count)
    return owned


def parse_loaded_ammo(block: bytes) -> list[int]:
    """Return the item IDs of the ammo currently loaded in the tank.

    Pebbles (0x65) are skipped on purpose, and so is any byte that is not a known item ID
    (for example an empty slot), so that only real items are added to the owned list.
    """
    return [item_id for item_id in block if item_id != PEBBLE_ID and item_id in VALID_ITEM_IDS]


def build_ammo(owned: list[int], rng: random.Random | None = None) -> list[int]:
    """Pick 30 random ammo IDs from the owned items, padding with pebbles if needed."""
    rng = rng if rng is not None else random.Random()

    if len(owned) >= AMMO_SLOT_COUNT:
        return rng.sample(owned, AMMO_SLOT_COUNT)

    ammo = owned.copy()
    ammo += [PEBBLE_ID] * (AMMO_SLOT_COUNT - len(ammo))
    rng.shuffle(ammo)
    print(f"Ammo randomized {ammo} from owned {owned}, padded with {PEBBLE_ID:02X}")
    return ammo


class TankAmmoRandomizer:
    """Watches the tank battle flag and randomizes the ammo when a battle starts."""

    def __init__(self) -> None:
        self._was_in_battle: bool | None = None
        self._pending: bool = False

    async def update(self, bizhawk_ctx: bizhawk.BizHawkContext) -> None:
        """Call this once per game_watcher tick."""
        try:
            flag = (await bizhawk.read(bizhawk_ctx, [
                (TANK_BATTLE_FLAG_ADDR, 1, RAM_DOMAIN),
            ]))[0]
        except bizhawk.RequestFailedError:
            return

        in_battle = flag[0] == 1

        if self._was_in_battle is None:
            # Do not modify ammo if the client connects during an active battle.
            self._was_in_battle = in_battle
            return

        if in_battle and not self._was_in_battle:
            self._pending = True  # rising edge: 00 -> 01
        if not in_battle:
            self._pending = False
        self._was_in_battle = in_battle

        if self._pending and await self._randomize(bizhawk_ctx):
            self._pending = False

    async def _randomize(self, bizhawk_ctx: bizhawk.BizHawkContext) -> bool:
        """Read the inventory, build the new ammo list, write it. Returns True on success."""
        try:
            # Read both areas together so they come from the same frame.
            inventory_block, loaded_block = await bizhawk.read(bizhawk_ctx, [
                (INVENTORY_START_ADDR, INVENTORY_SIZE, RAM_DOMAIN),
                (LOADED_AMMO_START_ADDR, LOADED_AMMO_SLOT_COUNT, RAM_DOMAIN),
            ])
            owned = parse_inventory(inventory_block) + parse_loaded_ammo(loaded_block)
            ammo = build_ammo(owned)
            await bizhawk.write(bizhawk_ctx, [
                (AMMO_START_ADDR, bytes(ammo), RAM_DOMAIN),
            ])
        except bizhawk.RequestFailedError:
            return False

        logger.info("Tank ammo randomized: %s", " ".join(f"{item_id:02X}" for item_id in ammo))
        return True