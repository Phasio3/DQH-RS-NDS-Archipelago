# client.py — BizHawk connector for DQH-RS.
#
# This file runs on the player's PC while they play.
# It bridges the Archipelago server and the emulator.

from __future__ import annotations

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

from NetUtils import ClientStatus

from .locations import SLIME_ID_TO_LOCATION_ID
from .locations import MONSTER_ID_TO_LOCATION_ID
from .locations import ITEM_ID_TO_LOCATION_ID
from .locations import LOCATION_TABLE
from .locations import FINAL_BOSS_LOCATION_ID, SLIME_LOCATION_IDS
from .locations import TANK_ID_TO_LOCATION_ID
from .locations import TANK_UPGRADE_ID_TO_LOCATION_ID
from .items import BASE_ID
from .randomizer import TankAmmoRandomizer
from .options import Goal

# ── Constants still pending real research (see CHECKLIST.md §6) ────────────────
AP_ITEM_INDEX_ADDR = 0x00001890
RECV_ITEM_COUNT_ADDR = 0x00001C00
ITEM_INBOX_ADDR = 0x00001EB0
ITEM_INBOX_STRIDE = 2
GOAL_FLAG_ADDR = 0x0013B469
ROOM_ID_ADDR = 0x0013B068
MONSTER_ID_ADDR_BEGIN = 0x00214270
MONSTER_ID_ADDR_END = 0x002142BF
TANK_BATTLE_FLAG_ADDR = 0x0013B487
PLAYER_HP_ADDR = 0x00143BD8


# ── tank battle ──────────────────────────────────────────────────────────
TANK_BATTLE_ID_ADDR = 0x0013AED8        # 01-24 (hex) depending on the battle; never goes back to 00
TANK_EXPLOSION_ANIM_ADDR = 0x0013B5B4   # goes to 02 at the end of the enemy tank explosion
TANK_EXPLOSION_DONE_VALUE = 0x02

# ── tank upgrades ──────────────────────────────────────────────────────────
# Contiguous byte table, 1 byte per upgrade:
#   0x00 = locked, 0x01 = unlocked
# The range goes from TANK_UPGRADE_ID_ADDR_BEGIN to TANK_UPGRADE_ID_ADDR_END included.
TANK_UPGRADE_ID_ADDR_BEGIN = 0x002143e7
TANK_UPGRADE_ID_ADDR_END = 0x002143fa
TANK_UPGRADE_ENTRY_SIZE = 1
TANK_UPGRADE_COUNT = (TANK_UPGRADE_ID_ADDR_END - TANK_UPGRADE_ID_ADDR_BEGIN + 1) // TANK_UPGRADE_ENTRY_SIZE
TANK_UPGRADE_STATUS_LOCKED = 0x00  # kept to document the locked value
TANK_UPGRADE_ID_BASE = 0x25  # tank_id of the first byte of the range

# ── item found ──────────────────────────────────────────────────────────
ITEM_ENTRY_SIZE = 4
ITEM_COUNT = 59
ITEM_STATUS_LOCKED = 0x00

# ── Bestiary table ──────────────────────────────────────────────────────────
# Each monster occupies a 4-byte contiguous entry:
#   byte 0 : status -> 0x00 = locked, 0x01 = unlocked, 0x11 = unlocked
#             + golden version (these two cases both count as "unlocked"
#             for the location)
#   byte 1 : number of specimens captured by the player
#   bytes 2-3 : unused (always 00 00 observed so far)
# The entry index (0, 1, 2...) is the "monster_id" used in
# locations.py — see MONSTER_ID_TO_LOCATION_ID below.
MONSTER_ENTRY_SIZE = 4
MONSTER_COUNT = 20
MONSTER_STATUS_LOCKED = 0x00

# ── Hot Patch: neutralize the call that writes 01 to 0x02214444 ─────────────
HOTPATCH_ADDR = 0x0207ECF4 - 0x02000000      # = 0x7ECF4, relative to the "Main RAM" domain
BL_ORIGINAL   = bytes([0xF6, 0xD8, 0x01, 0xEB])   # bl FUN_020f50d4
NOP           = bytes([0x00, 0x00, 0xA0, 0xE1])   # mov r0, r0

# ── Map unlock system ────────────────────────────────────────────────────
# The map reveal animation is driven by 3 fields in a fixed global structure
# (never reallocated, always at 0x022106C0):
#   0x02214444  mode  : 0x01 = nothing to do, 0x02 = "reveal this map"
#   0x02214445  id    : which map to reveal (consumed when the map opens)
#   0x02214442  timer : internal animation countdown; returns to 0x00
#                        and stays there once the animation is truly finished
#
# Forcing the mode to 0x01 permanently prevents the game from triggering its
# own story-based map unlocks. We switch to 0x02 ourselves, one map at a time,
# whenever a received "Access_*" item has not yet been applied.
MAP_UNLOCK_MODE_ADDR  = 0x00214444
MAP_UNLOCK_ID_ADDR    = 0x00214445
MAP_UNLOCK_TIMER_ADDR = 0x00214442
MODE_IDLE   = 0x01
MODE_REVEAL = 0x02

# Mini-map guide animation counter (observed behavior):
#   - in the mini-map      : counts in a loop MAX -> ... -> 00 -> MAX -> ...
#   - outside the mini-map : remains FROZEN on its highest value (MAX varies:
#                             03, 05, 0A... so we cannot rely on a precise
#                             value, only on whether it is moving)
#   - during the map unlock animation : 0xFF (and ONLY then)
MAP_ANIM_ADDR  = 0x0021442C   # relative to "Main RAM" (absolute: 0x0221442C)
ANIM_UNLOCKING = 0xFF

# Number of ticks without any change in the counter before considering
# that the player is no longer on the selection screen (~1 s at 8 ticks/s).
MINIMAP_ACTIVITY_TICKS = 8

# Number of game_watcher ticks (~125 ms each, NOT frames) during which the timer
# must remain at 0x00 (after already being non-zero) before we consider the
# animation complete. This is the SLOW safety net: it avoids confusing the true
# end with the internal pause between phases 2 and 3 of the animation.
UNLOCK_STABILITY_FRAMES = 1

# Number of ticks used instead when BOTH signals agree: 0xFF was seen (the
# animation really ran), the guide counter returned to a normal value, and the
# timer is 0x00. Completion is detected in ~250 ms instead of ~1 s, so the bit
# can be written before the player can reopen the map.
UNLOCK_FAST_END_TICKS = 2

# Set to True to print a log of map-unlock state changes.
DEBUG_MAP_UNLOCK = False

# Relative offset to "Main RAM" (0x0012E040 -> absolute 0x0212E040), so valid:
# the DS Main RAM is 4 MB, and offsets range from 0x000000 to 0x3FFFFF.
UNLOCKED_MAPS_BITFIELD_ADDR   = 0x0012E040
UNLOCKED_MAPS_BITFIELD_DOMAIN = "Main RAM"

MAP_ITEM_TO_GAME_ID: dict[str, int] = {
    "Access_Tootinschleiman_Tomb": 0x02,
    "Access_Mt_Krakatroda":        0x03,
    "Access_Backwoods":            0x04,
    "Access_Callmigh_Bluff":       0x05,
    "Access_Flucifer_Necropolis":  0x06,
    "Access_Flying_Clawtress":     0x07,
}

def _map_bit(game_id: int) -> int:
    """Position of the bit for a given map ID (0x02-0x07 -> bit 0-5)."""
    return 1 << (game_id - 2)

# ── Saved-slime table ────────────────────────────────────────────────────────
# 100 bytes. Each byte is either EMPTY_SLOT (nothing saved in that slot yet)
# or the in-game ID (1-100) of the slime rescued into that slot.
# The game can fill several slots within the same frame (multi-rescue).
SAVED_SLIME_ADDR = 0x0214345
SAVED_SLIME_SIZE = 100
EMPTY_SLOT = 0xFF
TOTAL_NUMBER_OF_SLIME_ADDR = 0x02143A9

# ── Items ────────────────────────────────────────────────────────
GOLD_COUNTER_ADDR = 0x0013B0C0 # 32 bits

# ── BOSS ────────────────────────────────────────────────────────
BOSS_NAMES = ["Bough Beater", "Pot Belly", "Harvest Loon", "Don Clawleone", "Lickity Spit"]
BOSS_ROOM_VALUES = [b"\x4A", b"\x7F", b"\xA5", b"\xDB", b"\xB3"]
BOUGH_BEATER_HEALTH_ADDR = 0x01444B8
POT_BELLY_HEALTH_ADDR = 0x0145F58
HARVEST_LOON_HEALTH_ADDR = 0x01446F0
DON_CLAWLEONE_HEALTH_ADDR = 0x01444B8
LICKITY_SPIT_HEALTH_ADDR = 0x0147350

# ── Unlocked Items Addresses ──────────────────────────────────────────────────
UNLOCKED_ITEMS_ADDRS = {
    "Pompoms Unlocked": 0x0214180,
    "Chests Unlocked": 0x0214184,
    "Catnips Unlocked": 0x0214188,
    "Rockbombs Unlocked": 0x021418C,
    "Spooklear Bombs Unlocked": 0x0214190,
    "Bombshells Unlocked": 0x0214194,
    "Obelisks Unlocked": 0x0214198,
    "Wooden Arrows Unlocked": 0x021419C,
    "Iron Arrows Unlocked": 0x02141A0,
    "Golden Arrows Unlocked": 0x02141A4,
    "Boulders Unlocked": 0x02141A8,
    "Oaken Clubs Unlocked": 0x02141AC,
    "Irritaballs Unlocked": 0x02141B4,
    "Destructiballs Unlocked": 0x02141B8,
    "Girders Unlocked": 0x02141BC,
    "Holy Waters Unlocked": 0x02141C0,
    "Boomerangs Unlocked": 0x02141C4,
    "Edged Boomerangs Unlocked": 0x02141C8,
    "BS-1 Croozes Unlocked": 0x02141CC,
    "BS-2 Blue Streaks Unlocked": 0x02141D0,
    "BS-3 Slimahawks Unlocked": 0x02141D4,
    "Fire Waters Unlocked": 0x02141D8,
    "Thousandweights Unlocked": 0x02141DC,
    "Chimaera Wings Unlocked": 0x02141E0,
    "Shurikens Unlocked": 0x02141E4,
    "Slime Knights Unlocked": 0x02141E8,
    "Steel Broadswoards Unlocked": 0x02141EC,
    "Miracle Swords Unlocked": 0x02141F0,
    "Bastard Swords Unlocked": 0x02141F4,
    "Metal King Swords Unlocked": 0x02141F8,
    "Iron Shields Unlocked": 0x02141FC,
    "Mirror Shields Unlocked": 0x0214200,
    "Metal King Shields Unlocked": 0x0214204,
    "Medicinal Herbs Unlocked": 0x0214208,
    "Strong Medicines Unlocked": 0x021420C,
    "Special Medicines Unlocked": 0x0214210,
    "Goddess Statues Unlocked": 0x0214214,
    "Vulcan Guns Unlocked": 0x0214218,
    "Vulcan Pellets Unlocked": 0x021421C,
    "Vulcan Bullets Unlocked": 0x0214220,
    "Vulcan Shells Unlocked": 0x0214224,
    "Lightning Staves Unlocked": 0x0214228,
    "Hell Scythes Unlocked": 0x021422C,
    "Chilli Peppers Unlocked": 0x0214230,
    "Holy Crystals Unlocked": 0x0214234,
    "Devil's Tails Unlocked": 0x0214238,
    "Gold Bars Unlocked": 0x021423C,
    "Toy Slimes Unlocked": 0x0214240,
    "Clap Traps Unlocked": 0x0214244,
    "Cloaking Devices Unlocked": 0x0214248,
    "Kaboomamites Unlocked": 0x021424C,
    "Power Tablets Unlocked": 0x0214250,
    "Overdrive Tablets Unlocked": 0x0214254,
    "Weapon Tablets Unlocked": 0x0214258,
    "Orichalcums Unlocked": 0x021425C,
    "Orichalslimes Unlocked": 0x0214260,
    "Meteorites Unlocked": 0x0214264,
    "Kafrizzles Unlocked": 0x0214268,
    "Hero Swords Unlocked": 0x021426C,
}


class DQHRSClient(BizHawkClient):
    """BizHawk client for DQH-RS."""

    game = "dqh_rs"
    system = "NDS"

    def __init__(self) -> None:
        self.num_items_received = 0
        self.total_slimes = 0
        self.boss_health_hist = []
        self.unlocked_items_received = set()
        self._unlock_in_progress = False   # is a reveal currently in progress?
        self._unlock_timer_started = False # has the timer already been seen non-zero?
        self._unlock_zero_streak = 0       # consecutive frames at 0x00 since
        self._pending_game_id: int | None = None
        self._saw_unlocking_anim = False   # anim == 0xFF seen during this reveal?
        self._unlock_end_streak = 0        # consecutive ticks where the 2 end signals agree
        self._last_snapshot = None         # for the debug log
        self._last_anim: int | None = None
        self._ticks_since_anim_change = MINIMAP_ACTIVITY_TICKS  # "inactive" at startup
        self.tank_ammo = TankAmmoRandomizer()
        self._prev_tank_explosion_anim = 0x00
        self._prev_item_counts: dict[int, int] = {}
        # Global lock: while False, no "tank upgrade" check should be sent to the AP server,
        # even if the byte in memory changes to 01.
        self.begin_apworld = False
        pass

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        """Return True only if the correct, already-patched ROM is loaded."""
        if await bizhawk.get_system(ctx.bizhawk_ctx) != "NDS":
            return False

        try:
            title_bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(0x027FFA80, 12, "ROM")]))[0]
        except bizhawk.RequestFailedError:
            return False

        if title_bytes != b"SURAMORI2\x00\x00\x00":
            return False

        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        return True

    async def apply_hotpatch(self, ctx: BizHawkClientContext) -> None:
        """Replaces the bl instruction with a NOP only if the original instruction is present."""
        try:
            await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                [(HOTPATCH_ADDR, NOP, "Main RAM")],          # what we write
                [(HOTPATCH_ADDR, BL_ORIGINAL, "Main RAM")],  # guard: write only if it matches exactly
            )
            #print("Hotpatch applied: bl replaced with NOP.")
        except bizhawk.RequestFailedError:
            #print("Hotpatch failed: could not read/write memory. Is the game running?")
            pass

    def _player_in_minimap(self, anim: int) -> bool:
        """True if the guide animation counter is moving (= selection screen).

        Outside the minimap, the counter stays frozen on its highest value
        (variable value): we therefore detect a MOVEMENT over a window of
        MINIMAP_ACTIVITY_TICKS ticks, never a precise value.

        Must be called on EVERY tick to keep the history up to date.
        """
        if anim == ANIM_UNLOCKING:
            # Unlock animation: this is not the selection screen.
            self._last_anim = anim
            self._ticks_since_anim_change = MINIMAP_ACTIVITY_TICKS
            return False

        if self._last_anim is not None and anim != self._last_anim:
            self._ticks_since_anim_change = 0   # the counter moved
        else:
            self._ticks_since_anim_change += 1  # same value as the previous tick

        self._last_anim = anim
        return self._ticks_since_anim_change < MINIMAP_ACTIVITY_TICKS

    async def _handle_map_unlocks(self, ctx: "BizHawkClientContext") -> None:
        """Delivers access items for maps one by one through the game's animation,
        while preventing any native story-based map unlocking from occurring."""

        try:
            bitfield_byte, mode_byte, timer_byte, anim_byte = await bizhawk.read(ctx.bizhawk_ctx, [
                (UNLOCKED_MAPS_BITFIELD_ADDR, 1, UNLOCKED_MAPS_BITFIELD_DOMAIN),
                (MAP_UNLOCK_MODE_ADDR, 1, "Main RAM"),
                (MAP_UNLOCK_TIMER_ADDR, 1, "Main RAM"),
                (MAP_ANIM_ADDR, 1, "Main RAM"),
            ])
        except bizhawk.RequestFailedError:
            return

        bitfield, current_mode, timer = bitfield_byte[0], mode_byte[0], timer_byte[0]
        anim = anim_byte[0]
        in_minimap = self._player_in_minimap(anim)   # call on every tick, before any return
        #print(f"DEBUG: _handle_map_unlocks: bitfield={bitfield:08b} mode={current_mode:02X} timer={timer:02X} anim={anim:02X} in_minimap={in_minimap}")

        if DEBUG_MAP_UNLOCK:
            snapshot = (bitfield, current_mode, timer, self._unlock_in_progress,
                        in_minimap, anim == ANIM_UNLOCKING)
            if snapshot != self._last_snapshot:
                print(f"[unlock] bitfield={bitfield:08b} mode={current_mode:02X} timer={timer:02X} "
                      f"anim={anim:02X} ff={anim == ANIM_UNLOCKING} "
                      f"in_progress={self._unlock_in_progress} in_minimap={in_minimap}")
                self._last_snapshot = snapshot

        if self._unlock_in_progress:
            # Keep the ID of the map currently being unlocked at all times.
            await bizhawk.write(ctx.bizhawk_ctx, [
                (MAP_UNLOCK_ID_ADDR, bytes([self._pending_game_id]), "Main RAM"),
            ])

            # End-of-animation tracking does NOT depend on in_minimap: if the player leaves
            # the map just after the animation, the counter stays frozen and in_minimap eventually
            # falls back to False, which must not delay writing the bit.

            # Signal A: 0xFF only appears during the unlock animation (outside the minimap,
            # the counter stays on the normal high value). Seeing it therefore proves the
            # game played the animation.
            #print(f"DEBUG: _handle_map_unlocks: anim={anim:02X}, timer={timer:02X}, in_minimap={in_minimap}, ff={anim == ANIM_UNLOCKING}")
            if anim == ANIM_UNLOCKING:
                self._saw_unlocking_anim = True

            # Signal B: the internal animation timer (slow safety net).
            if timer != 0:
                self._unlock_timer_started = True
                self._unlock_zero_streak = 0
            elif self._unlock_timer_started:
                self._unlock_zero_streak += 1

            # FAST END: FF seen, counter back to a normal value (loop OR frozen on its high
            # value, both are != FF) and timer at 0 for 2 ticks in a row.
            if self._saw_unlocking_anim and anim != ANIM_UNLOCKING and timer == 0:
                self._unlock_end_streak += 1
            else:
                self._unlock_end_streak = 0

            fast_end = self._unlock_end_streak >= UNLOCK_FAST_END_TICKS
            slow_end = self._unlock_timer_started and self._unlock_zero_streak >= UNLOCK_STABILITY_FRAMES

            if fast_end or slow_end:
                # Finished: write the bit and return the mode to idle.
                new_bitfield = bitfield | _map_bit(self._pending_game_id)
                try:
                    written = await bizhawk.guarded_write(
                        ctx.bizhawk_ctx,
                        [(UNLOCKED_MAPS_BITFIELD_ADDR, bytes([new_bitfield]), UNLOCKED_MAPS_BITFIELD_DOMAIN),
                         (MAP_UNLOCK_MODE_ADDR, bytes([MODE_IDLE]), "Main RAM")],
                        [(UNLOCKED_MAPS_BITFIELD_ADDR, bytes([bitfield]), UNLOCKED_MAPS_BITFIELD_DOMAIN)],
                    )
                    #print(f"DEBUG: _handle_map_unlocks: wrote new bitfield {new_bitfield:08b} (was {bitfield:08b})")
                except bizhawk.RequestFailedError:
                    return
                if not written:
                    return  # guarded write failed: nothing was written, we remain "in progress" and retry
                self._unlock_in_progress = False
                self._unlock_timer_started = False
                self._unlock_zero_streak = 0
                self._saw_unlocking_anim = False
                self._unlock_end_streak = 0
                return

            # Maintain the mode: never 02 while the player is in the selection screen.
            wanted = MODE_IDLE if in_minimap else MODE_REVEAL
            if current_mode != wanted:
                #print(f"DEBUG: _handle_map_unlocks: changing mode from {current_mode:02X} to {wanted:02X}")
                await bizhawk.write(ctx.bizhawk_ctx, [(MAP_UNLOCK_MODE_ADDR, bytes([wanted]), "Main RAM")])
            return

        # Nothing in progress: prevent the game from triggering its own unlock.
        if current_mode != MODE_IDLE:
            #print(f"DEBUG: _handle_map_unlocks: forcing mode to IDLE (was {current_mode:02X})")
            await bizhawk.write(ctx.bizhawk_ctx, [(MAP_UNLOCK_MODE_ADDR, bytes([MODE_IDLE]), "Main RAM")])
            #print("Forcing map unlock mode to IDLE to prevent native unlocks.")

        # The player is choosing a map: keep the mode at 01 and retry on the next tick.
        if in_minimap:
            #print("Player is in the minimap, waiting for them to leave before applying new unlocks.")
            #print(f"DEBUG: _handle_map_unlocks: player is in minimap")
            return

        # Look for the next received "Access_*" item that has not yet been applied.
        for network_item in ctx.items_received:

            item_name = ctx.item_names.lookup_in_game(network_item.item)
            game_id = MAP_ITEM_TO_GAME_ID.get(item_name)
            if game_id is None or (bitfield & _map_bit(game_id)):
                continue  # Not a map item, or already applied.
            print(f"Checking received item: {game_id:02X} {item_name} (bitfield={bitfield:08b})")

            self._pending_game_id = game_id
            self._unlock_in_progress = True
            self._unlock_timer_started = False
            self._unlock_zero_streak = 0
            self._saw_unlocking_anim = False
            self._unlock_end_streak = 0
            await bizhawk.write(ctx.bizhawk_ctx, [
                (MAP_UNLOCK_ID_ADDR, bytes([game_id]), "Main RAM"),
                (MAP_UNLOCK_MODE_ADDR, bytes([MODE_REVEAL]), "Main RAM"),
            ])
            break

    async def _handle_item_checks(self, ctx: "BizHawkClientContext") -> set[int]:
        """Detects rising edges 00 -> 01 on item counters.

        Each entry in UNLOCKED_ITEMS_ADDRS points to the item status.
        The quantity counter sits at address + 0x01.

        An AP check is generated only when a counter actually changes
        from 0x00 to 0x01, and only after the AP run has started.
        """
        if not self.begin_apworld:
            return set()

        try:
            item_counts = await bizhawk.read(
                ctx.bizhawk_ctx,
                [
                    (addr + 0x01, 1, "Main RAM")
                    for addr in UNLOCKED_ITEMS_ADDRS.values()
                ],
            )
        except bizhawk.RequestFailedError:
            return set()

        new_checks: set[int] = set()

        for item_id, (count_byte,) in zip(ITEM_ID_TO_LOCATION_ID, item_counts):
            current_count = count_byte

            previous_count = self._prev_item_counts.get(item_id, 0)

            # Always record the current value.
            self._prev_item_counts[item_id] = current_count

            # Rising edge 00 -> 0X.
            if previous_count != 0x00 or current_count == 0x00:
                continue

            location_ap_id = ITEM_ID_TO_LOCATION_ID.get(item_id)

            if location_ap_id is not None and location_ap_id not in ctx.checked_locations:
                new_checks.add(location_ap_id)

        return new_checks

    async def _check_goal(self, ctx: BizHawkClientContext, new_checks: set[int]) -> None:
        """Sends CLIENT_GOAL to the server when the selected objective is completed."""
        if ctx.finished_game:
            return
        goal = (ctx.slot_data or {}).get("goal")   # sent by fill_slot_data
        if goal is None:
            return

        done = ctx.checked_locations | new_checks  # already checked + those from the current tick
        if goal == Goal.option_defeat_final_boss:
            reached = FINAL_BOSS_LOCATION_ID in done
        elif goal == Goal.option_save_all_slimes:
            reached = SLIME_LOCATION_IDS <= done   # "<=" : subset
        else:
            return

        if reached:
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.finished_game = True

    async def apply_low_hp_trap(self, ctx: BizHawkClientContext) -> None:
        await bizhawk.write(ctx.bizhawk_ctx, [(PLAYER_HP_ADDR, bytes([0x01]), "Main RAM")])

    async def _handle_tank_battle_checks(self, ctx: "BizHawkClientContext") -> set[int]:
        """Detects the end of a tank battle via the rising edge (00 -> 02) of the
        explosion animation, then returns the corresponding AP location ID.

        We react only to a VALUE CHANGE, never to the value alone: otherwise, the
        same battle would trigger a check on every tick while the anim stays at 02.
        """
        try:
            anim_byte, tank_id_byte = await bizhawk.read(ctx.bizhawk_ctx, [
                (TANK_EXPLOSION_ANIM_ADDR, 1, "Main RAM"),
                (TANK_BATTLE_ID_ADDR, 1, "Main RAM"),
            ])
        except bizhawk.RequestFailedError:
            return set()

        anim = anim_byte[0]
        tank_id = tank_id_byte[0]

        rising_edge = (self._prev_tank_explosion_anim == 0x00 and anim == TANK_EXPLOSION_DONE_VALUE)
        self._prev_tank_explosion_anim = anim  # always update, even without a rising edge

        #print(f"DEBUG: _handle_tank_battle_checks: tank_id={tank_id} anim={anim:02X} rising_edge={rising_edge}")

        if not rising_edge:
            return set()

        location_ap_id = TANK_ID_TO_LOCATION_ID.get(tank_id)
        if location_ap_id is None or location_ap_id in ctx.checked_locations:
            return set()
        
        #print(f"DEBUG: Tank battle finished, sending check for tank_id={tank_id} location_ap_id={location_ap_id}")

        return {location_ap_id}

    async def _handle_tank_upgrade_checks(self, ctx: "BizHawkClientContext") -> set[int]:
        """One check per unlocked tank upgrade (byte == 0x01), but only if
        self.begin_apworld is True. While it is False, we do not even read the
        table: this avoids sending free checks before the player has actually
        started the randomized run.
        """
        if not self.begin_apworld:
            return set()

        try:
            tank_upgrades = (await bizhawk.read(ctx.bizhawk_ctx,
                [(TANK_UPGRADE_ID_ADDR_BEGIN,
                  TANK_UPGRADE_ID_ADDR_END - TANK_UPGRADE_ID_ADDR_BEGIN + 1,
                  "Main RAM")]
            ))[0]
        except bizhawk.RequestFailedError:
            return set()  # connector didn't respond, will retry next loop

        new_checks: set[int] = set()
        for i in range(TANK_UPGRADE_COUNT):
            status = tank_upgrades[i * TANK_UPGRADE_ENTRY_SIZE]
            if status != 0x01:
                continue  # only 0x01 explicitly means "unlocked"

            tank_id = TANK_UPGRADE_ID_BASE + i
            location_ap_id = TANK_UPGRADE_ID_TO_LOCATION_ID.get(tank_id)
            if location_ap_id is not None and location_ap_id not in ctx.checked_locations:
                new_checks.add(location_ap_id)

        return new_checks

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.server is None or ctx.slot is None:
            return  # not connected to the AP server/slot yet

        # From the first tick where the client is actually connected to an AP slot,
        # the items and upgrades tables can generate checks.
        self.begin_apworld = True

        await self.apply_hotpatch(ctx)

        await self.tank_ammo.update(ctx.bizhawk_ctx)

        await self._handle_map_unlocks(ctx)

        # ── 1. Read the whole saved-slime table in a single call ───────────────
        try:
            slime_table = (await bizhawk.read(ctx.bizhawk_ctx, [
                (SAVED_SLIME_ADDR, SAVED_SLIME_SIZE, "Main RAM"),
            ]))[0]
        except bizhawk.RequestFailedError:
            return  # connector didn't respond, will retry next loop

        # ── 2. Turn every filled slot into a location check ────────────────────
        # Direct lookup: raw slime_id -> AP location id. No name is built here,
        # so renaming a location in locations.py never affects this code.
        new_checks: set[int] = set()
        for slime_id in slime_table:
            if slime_id == EMPTY_SLOT:
                continue  # slot not used yet

            location_ap_id = SLIME_ID_TO_LOCATION_ID.get(slime_id)
            if location_ap_id is not None and location_ap_id not in ctx.checked_locations:
                new_checks.add(location_ap_id)
                await bizhawk.write(ctx.bizhawk_ctx, [(TOTAL_NUMBER_OF_SLIME_ADDR, bytes([self.total_slimes]), "Main RAM")])

        try:
            boss_list = (await bizhawk.read(ctx.bizhawk_ctx,
                [(BOUGH_BEATER_HEALTH_ADDR, 1, "Main RAM"),
                (POT_BELLY_HEALTH_ADDR, 1, "Main RAM"),
                (HARVEST_LOON_HEALTH_ADDR, 1, "Main RAM"),
                (DON_CLAWLEONE_HEALTH_ADDR, 1, "Main RAM"),
                (LICKITY_SPIT_HEALTH_ADDR, 1, "Main RAM"),
            ]))
        except bizhawk.RequestFailedError:
            return  # connector didn't respond, will retry next loop
        
        try:
            room_id = (await bizhawk.read(ctx.bizhawk_ctx,
                [(ROOM_ID_ADDR, 1, "Main RAM")]
            ))[0]
        except bizhawk.RequestFailedError:
            return  # connector didn't respond, will retry next loop
        
        try:
            tank_battle_flag = (await bizhawk.read(ctx.bizhawk_ctx,
                [(TANK_BATTLE_FLAG_ADDR, 1, "Main RAM")]
            ))[0]
        except bizhawk.RequestFailedError:
            return  # connector didn't respond, will retry next loop

        if room_id in BOSS_ROOM_VALUES and tank_battle_flag != b"\x01":
            for i in range(len(BOSS_NAMES)):
                if room_id == BOSS_ROOM_VALUES[i]:
                    if boss_list[i] == b"\x00":
                        if not boss_list[i] in self.boss_health_hist:
                            location_ap_id = BASE_ID + LOCATION_TABLE[f"{BOSS_NAMES[i]} defeated"].id_offset
                            new_checks.add(location_ap_id)  
                    self.boss_health_hist.append(boss_list[i])
                    if len(self.boss_health_hist) > 2:
                        self.boss_health_hist = self.boss_health_hist[1:]
            
        try:
            unlocked_monsters = (await bizhawk.read(ctx.bizhawk_ctx,
                [(MONSTER_ID_ADDR_BEGIN, MONSTER_ID_ADDR_END - MONSTER_ID_ADDR_BEGIN + 1, "Main RAM")]
            ))[0]
        except bizhawk.RequestFailedError:
            return  # connector didn't respond, will retry next loop

        # ── Tank Battle ─────────────────────────────────────────────────
        new_checks |= await self._handle_tank_battle_checks(ctx)

        # ── Tank Upgrades ────────────────────────────────────────────────
        new_checks |= await self._handle_tank_upgrade_checks(ctx)

        # ── Bestiary: one check per monster whose status is no longer 0x00 ──
        for monster_id in range(MONSTER_COUNT):
            status = unlocked_monsters[monster_id * MONSTER_ENTRY_SIZE]
            if status == MONSTER_STATUS_LOCKED:
                continue
            print(f"status monster_id = {status} | for monster_id = {monster_id}\nunlocked_monsters\n")

            location_ap_id = MONSTER_ID_TO_LOCATION_ID.get(monster_id)
            if location_ap_id is not None and location_ap_id not in ctx.checked_locations:
                new_checks.add(location_ap_id)

        # ── Item ─────────────────────────────────────────────────────────
        new_checks |= await self._handle_item_checks(ctx)

        # Send ALL checks detected during this tick.
        if new_checks:
            await ctx.send_msgs([
                {"cmd": "LocationChecks", "locations": list(new_checks)}
            ])

        await self._check_goal(ctx, new_checks)

        # ── 3. Item delivery + goal detection ───────────────────────────────────

        if len(ctx.items_received) > self.num_items_received:
            item = ctx.items_received[self.num_items_received]
            item_name = ctx.item_names.lookup_in_game(item.item)

            # Handle Slime items
            if item_name.startswith("Slime_"):
                self.total_slimes += 1
                await bizhawk.write(ctx.bizhawk_ctx, [(TOTAL_NUMBER_OF_SLIME_ADDR, bytes([self.total_slimes]), "Main RAM")])

            # Handle filler "100 Gold"
            elif item_name == "100 Gold":
                # Read the current gold (4 bytes = 32 bits)
                gold_data = (await bizhawk.read(ctx.bizhawk_ctx, [(GOLD_COUNTER_ADDR, 4, "Main RAM")]))[0]
                current_gold = int.from_bytes(gold_data, byteorder="little")

                # Calculate and write the new gold value
                new_gold = current_gold + 100
                await bizhawk.write(ctx.bizhawk_ctx, [(GOLD_COUNTER_ADDR, new_gold.to_bytes(4, byteorder="little"), "Main RAM")])

            elif item_name == "Low HP Trap":
                await self.apply_low_hp_trap(ctx)

            # Track unlocked items
            if item_name in UNLOCKED_ITEMS_ADDRS:
                self.unlocked_items_received.add(item_name)

            self.num_items_received += 1

        # ── 4. Enforce Unlocked Items states ────────────────────────────────────
        unlocked_writes = []
        for name, addr in UNLOCKED_ITEMS_ADDRS.items():
            if name in self.unlocked_items_received:
                unlocked_writes.append((addr, b"\x01", "Main RAM"))
            else:
                unlocked_writes.append((addr, b"\x00", "Main RAM"))
        
        if unlocked_writes:
            try:
                await bizhawk.write(ctx.bizhawk_ctx, unlocked_writes)
            except bizhawk.RequestFailedError:
                pass