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

from .locations import SLIME_ID_TO_LOCATION_ID
from .locations import MONSTER_ID_TO_LOCATION_ID
from .locations import LOCATION_TABLE
from .items import BASE_ID
from .randomizer import TankAmmoRandomizer

# ── Constants still pending real research (see CHECKLIST.md §6) ────────────────
AP_ITEM_INDEX_ADDR = 0x00001890    
RECV_ITEM_COUNT_ADDR = 0x00001C00  
ITEM_INBOX_ADDR = 0x00001EB0       
ITEM_INBOX_STRIDE = 2
GOAL_FLAG_ADDR = 0x0013B469        
ROOM_ID_ADDR = 0x0013B068
MONSTER_ID_ADDR_BEGIN = 0x00214260
MONSTER_ID_ADDR_END = 0x002142BF
TANK_BATTLE_FLAG_ADDR = 0x0013B487

# ── Bestiary table ──────────────────────────────────────────────────────────
# Chaque monstre occupe une entrée de 4 octets consécutifs :
#   octet 0 : statut  -> 0x00 = pas débloqué, 0x01 = débloqué, 0x11 = débloqué
#             + version dorée (ces deux derniers cas comptent tous les deux
#             comme "débloqué" pour la location)
#   octet 1 : nombre de spécimens capturés par le joueur
#   octets 2-3 : inutilisés (toujours 00 00 observé pour l'instant)
# L'index de l'entrée (0, 1, 2...) est le "monster_id" utilisé dans
# locations.py — voir MONSTER_ID_TO_LOCATION_ID ci-dessous.
MONSTER_ENTRY_SIZE = 4
MONSTER_COUNT = 20
MONSTER_STATUS_LOCKED = 0x00

# ── Hot Patch : neutralise l'appel qui écrit 01 dans 0x02214444 ────────────
HOTPATCH_ADDR = 0x0207ECF4 - 0x02000000      # = 0x7ECF4, relatif au domaine "Main RAM"
BL_ORIGINAL   = bytes([0xF6, 0xD8, 0x01, 0xEB])   # bl FUN_020f50d4
NOP           = bytes([0x00, 0x00, 0xA0, 0xE1])   # mov r0, r0

# ── Map unlock system ────────────────────────────────────────────────────
# L'animation de révélation de map est pilotée par 3 champs d'une structure
# globale fixe (jamais réallouée, toujours à 0x022106C0) :
#   0x02214444  mode  : 0x01 = rien à faire, 0x02 = "révèle cette map"
#   0x02214445  id    : quelle map révéler (consommé à l'ouverture de la carte)
#   0x02214442  timer : décompte interne de l'animation ; retombe à 0x00
#                        et y reste une fois l'animation vraiment terminée
#
# Forcer le mode à 0x01 en permanence empêche tout déblocage scénaristique
# du jeu de se produire. On ne passe à 0x02 que nous-mêmes, une map à la
# fois, quand un item "Access_*" reçu n'a pas encore été appliqué.
MAP_UNLOCK_MODE_ADDR  = 0x00214444
MAP_UNLOCK_ID_ADDR    = 0x00214445
MAP_UNLOCK_TIMER_ADDR = 0x00214442
MODE_IDLE   = 0x01
MODE_REVEAL = 0x02

# Compteur d'animation du petit guide (comportement observé) :
#   - dans la mini-map      : décompte en boucle  MAX -> ... -> 00 -> MAX -> ...
#   - hors de la mini-map   : reste FIGÉ sur sa valeur la plus haute (MAX varie :
#                             03, 05, 0A... on ne peut donc pas s'appuyer sur une
#                             valeur précise, seulement sur "est-ce que ça bouge ?")
#   - pendant l'animation de déblocage d'une map : 0xFF (et UNIQUEMENT à ce moment)
MAP_ANIM_ADDR  = 0x0021442C   # relatif à "Main RAM" (absolu : 0x0221442C)
ANIM_UNLOCKING = 0xFF

# Nombre de ticks sans aucun changement du compteur avant de considérer
# que le joueur n'est plus dans l'écran de sélection (~1 s à 8 ticks/s).
MINIMAP_ACTIVITY_TICKS = 8

# Nombre de TICKS de game_watcher (~125 ms chacun, PAS des frames) où le timer doit
# rester à 0x00 (après avoir déjà été non-nul) avant qu'on considère l'animation
# terminée. C'est le filet de sécurité LENT : il sert à ne pas confondre la vraie
# fin avec la pause interne entre les phases 2 et 3 de l'animation.
UNLOCK_STABILITY_FRAMES = 1

# Nombre de ticks utilisé à la place quand les DEUX signaux concordent : 0xFF a été
# vu (l'animation a vraiment tourné), le compteur du guide est revenu à une valeur
# normale, et le timer est à 0x00. Fin détectée en ~250 ms au lieu de ~1 s, pour
# écrire le bit dans le bitfield avant que le joueur ne puisse rouvrir la carte.
UNLOCK_FAST_END_TICKS = 2

# Mettre à True pour afficher un journal des changements d'état du déblocage.
DEBUG_MAP_UNLOCK = False

# Offset relatif à "Main RAM" (0x0012E040 -> absolu 0x0212E040), donc valide :
# la Main RAM du DS fait 4 Mo, les offsets vont de 0x000000 à 0x3FFFFF.
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
    """Position du bit pour un ID de map donné (0x02-0x07 -> bit 0-5)."""
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
GOLD_COUNTER_ADDR = 0x0213B0C0 # 32 bits

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
    "Chests Unlocked": 0x0214186,
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
        self._unlock_in_progress = False   # une révélation est-elle en cours ?
        self._unlock_timer_started = False # le timer a-t-il déjà été vu non-nul ?
        self._unlock_zero_streak = 0       # frames consécutives à 0x00 depuis
        self._pending_game_id: int | None = None
        self._saw_unlocking_anim = False   # anim == 0xFF vu pendant cette révélation ?
        self._unlock_end_streak = 0        # ticks consécutifs où les 2 signaux de fin concordent
        self._last_snapshot = None         # pour le journal de debug
        self._last_anim: int | None = None
        self._ticks_since_anim_change = MINIMAP_ACTIVITY_TICKS  # "inactif" au départ
        self.tank_ammo = TankAmmoRandomizer()
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
        """Remplace le bl par un NOP, uniquement si l'instruction d'origine est bien là."""
        try:
            await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                [(HOTPATCH_ADDR, NOP, "Main RAM")],          # ce qu'on écrit
                [(HOTPATCH_ADDR, BL_ORIGINAL, "Main RAM")],  # garde : on n'écrit que si c'est identique
            )
            #print("Hotpatch applied: bl replaced with NOP.")
        except bizhawk.RequestFailedError:
            #print("Hotpatch failed: could not read/write memory. Is the game running?")
            pass

    def _player_in_minimap(self, anim: int) -> bool:
        """True si le compteur d'animation du guide bouge (= écran de sélection).

        Hors de la mini-map le compteur reste figé sur sa valeur la plus haute
        (valeur variable) : on détecte donc un MOUVEMENT sur une fenêtre de
        MINIMAP_ACTIVITY_TICKS ticks, jamais une valeur précise.

        Doit être appelée à CHAQUE tick pour garder l'historique à jour.
        """
        if anim == ANIM_UNLOCKING:
            # Animation de déblocage : ce n'est pas la sélection.
            self._last_anim = anim
            self._ticks_since_anim_change = MINIMAP_ACTIVITY_TICKS
            return False

        if self._last_anim is not None and anim != self._last_anim:
            self._ticks_since_anim_change = 0   # le compteur a bougé
        else:
            self._ticks_since_anim_change += 1  # même valeur qu'au tick précédent

        self._last_anim = anim
        return self._ticks_since_anim_change < MINIMAP_ACTIVITY_TICKS

    async def _handle_map_unlocks(self, ctx: "BizHawkClientContext") -> None:
        """Livre les items d'accès aux maps un par un, via l'animation du jeu,
        tout en empêchant tout déblocage scénaristique natif de se produire."""

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
        in_minimap = self._player_in_minimap(anim)   # à appeler à chaque tick, avant tout return
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
            # Maintient constamment l'ID de la map en cours de déblocage.
            await bizhawk.write(ctx.bizhawk_ctx, [
                (MAP_UNLOCK_ID_ADDR, bytes([self._pending_game_id]), "Main RAM"),
            ])

            # Le suivi de fin d'animation ne dépend PAS de in_minimap : si le joueur quitte
            # la carte juste après l'animation, le compteur reste figé et in_minimap finit
            # par retomber à False, ce qui ne doit pas retarder l'enregistrement du bit.

            # Signal A : 0xFF n'apparaît que pendant l'animation de déblocage (hors mini-map
            # le compteur reste sur sa valeur haute normale). L'avoir vu prouve donc que
            # le jeu a bien joué l'animation.
            #print(f"DEBUG: _handle_map_unlocks: anim={anim:02X}, timer={timer:02X}, in_minimap={in_minimap}, ff={anim == ANIM_UNLOCKING}")
            if anim == ANIM_UNLOCKING:
                self._saw_unlocking_anim = True

            # Signal B : le timer interne de l'animation (filet de sécurité lent).
            if timer != 0:
                self._unlock_timer_started = True
                self._unlock_zero_streak = 0
            elif self._unlock_timer_started:
                self._unlock_zero_streak += 1

            # Fin RAPIDE : FF vu, compteur revenu à une valeur normale (boucle OU figé sur
            # sa valeur haute, les deux sont != FF) et timer à 0, pendant 2 ticks de suite.
            if self._saw_unlocking_anim and anim != ANIM_UNLOCKING and timer == 0:
                self._unlock_end_streak += 1
            else:
                self._unlock_end_streak = 0

            fast_end = self._unlock_end_streak >= UNLOCK_FAST_END_TICKS
            slow_end = self._unlock_timer_started and self._unlock_zero_streak >= UNLOCK_STABILITY_FRAMES

            if fast_end or slow_end:
                # Terminé : on enregistre le bit et on remet le mode au repos.
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
                    return  # garde échouée : rien n'a été écrit, on reste "en cours" et on réessaie
                self._unlock_in_progress = False
                self._unlock_timer_started = False
                self._unlock_zero_streak = 0
                self._saw_unlocking_anim = False
                self._unlock_end_streak = 0
                return

            # Maintien du mode : jamais 02 quand le joueur est dans la sélection.
            wanted = MODE_IDLE if in_minimap else MODE_REVEAL
            if current_mode != wanted:
                #print(f"DEBUG: _handle_map_unlocks: changing mode from {current_mode:02X} to {wanted:02X}")
                await bizhawk.write(ctx.bizhawk_ctx, [(MAP_UNLOCK_MODE_ADDR, bytes([wanted]), "Main RAM")])
            return

        # Rien en cours : on empêche le jeu de déclencher son propre déblocage.
        if current_mode != MODE_IDLE:
            #print(f"DEBUG: _handle_map_unlocks: forcing mode to IDLE (was {current_mode:02X})")
            await bizhawk.write(ctx.bizhawk_ctx, [(MAP_UNLOCK_MODE_ADDR, bytes([MODE_IDLE]), "Main RAM")])
            #print("Forcing map unlock mode to IDLE to prevent native unlocks.")

        # Le joueur choisit une map : on garde le mode à 01 et on retente au prochain tick.
        if in_minimap:
            #print("Player is in the minimap, waiting for them to leave before applying new unlocks.")
            #print(f"DEBUG: _handle_map_unlocks: player is in minimap")
            return

        # On cherche le prochain item "Access_*" reçu mais pas encore appliqué.
        for network_item in ctx.items_received:

            item_name = ctx.item_names.lookup_in_game(network_item.item)
            game_id = MAP_ITEM_TO_GAME_ID.get(item_name)
            if game_id is None or (bitfield & _map_bit(game_id)):
                continue  # Pas un item de map, ou déjà appliqué.
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

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.server is None or ctx.slot is None:
            return  # not connected to the AP server/slot yet

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

        # ── Bestiaire : un check par monstre dont le statut n'est plus 0x00 ─────
        for monster_id in range(MONSTER_COUNT):
            status = unlocked_monsters[monster_id * MONSTER_ENTRY_SIZE]
            if status == MONSTER_STATUS_LOCKED:
                continue  # pas encore débloqué

            location_ap_id = MONSTER_ID_TO_LOCATION_ID.get(monster_id)
            if location_ap_id is not None and location_ap_id not in ctx.checked_locations:
                new_checks.add(location_ap_id)
            print(f"DEBUG: monster_id={monster_id} status={status:02X} location_ap_id={location_ap_id} new_check={location_ap_id not in ctx.checked_locations}")
            print(f"DEBUG: {MONSTER_ID_TO_LOCATION_ID}")
        if new_checks:
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": list(new_checks)}])

        # ── 3. Item delivery + goal detection ───────────────────────────────────
        
        if len(ctx.items_received) > self.num_items_received:
            item = ctx.items_received[self.num_items_received]
            item_name = ctx.item_names.lookup_in_game(item.item)
            
            # Gestion des items Slime
            if item_name.startswith("Slime_"):
                self.total_slimes += 1
                await bizhawk.write(ctx.bizhawk_ctx, [(TOTAL_NUMBER_OF_SLIME_ADDR, bytes([self.total_slimes]), "Main RAM")])

            # Gestion du filler "100 Gold"
            elif item_name == "100 Gold":
                # Lecture de l'or actuel (4 octets = 32 bits)
                gold_data = (await bizhawk.read(ctx.bizhawk_ctx, [(GOLD_COUNTER_ADDR, 4, "Main RAM")]))[0]
                current_gold = int.from_bytes(gold_data, byteorder="little")
                
                # Calcul et écriture du nouvel or
                new_gold = current_gold + 100
                await bizhawk.write(ctx.bizhawk_ctx, [(GOLD_COUNTER_ADDR, new_gold.to_bytes(4, byteorder="little"), "Main RAM")])
            
            # Enregistrement des items Unlocked
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

        #pseudo-code:
        #new_items_received_list = archipelago.received_list
        #for new_item_received in new_items_received_list:
        #   if new_item_received:
        #       # Key_items Checks
        #
        #      if item_name.beginswith("Slime_"): # Useful Checks
        #          total_slimes += 1
        #      elif item_name == "100 Gold": # Filler Checks
        #           money = bizhawk.read(GOLD_COUNTER_ADRR,2,"Main RAM")
        #           new_money = list(money) + 100
        #           await bizhawk.write(ctx.bizhawk_ctx, [(GOLD_COUNTER_ADDR, bytes(new_money)), "Main RAM"]