# __init__.py — Main World class for DQH-RS.
#
# This is the entry point the Archipelago generator loads.
# It ties together items, locations, options, rules, and client.
#
# Generation flow (called in this order by the generator):
#   1. generate_early()   → optional; compute world properties before region graph
#   2. create_regions()   → build the region graph and add locations
#   3. create_items()     → fill the item pool
#   4. set_rules()        → attach access rules to entrances and locations
#   5. generate_output()  → optional; write a patch file or data bundle
#   6. fill_slot_data()   → return data the client needs after connecting

from worlds.AutoWorld import World, WebWorld
from BaseClasses import Item, ItemClassification, Region, Location, Tutorial

from .items    import ITEM_TABLE, ITEM_NAME_TO_ID, BASE_ID, DQHRSItemData
from .locations import LOCATION_TABLE, LOCATION_NAME_TO_ID, ALL_REGIONS
from .options  import DQHRSOptions, Goal
from .rules    import set_rules as _set_rules
from .settings import DQHRSSettings

# Importing the client module registers DQHRSClient with BizHawk automatically.
from . import client  # noqa: F401

from typing import ClassVar


# ── Web documentation ──────────────────────────────────────────────────────────
class DQHRSWebWorld(WebWorld):
    theme = "ocean"
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="How to install and connect DQH-RS for Archipelago.",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["Phasio"],
        )
    ]


# ── Item class ─────────────────────────────────────────────────────────────────
class DQHRSItem(Item):
    game = "dqh_rs"


# ── Location class ─────────────────────────────────────────────────────────────
class DQHRSLocation(Location):
    game = "dqh_rs"


# ── World class ────────────────────────────────────────────────────────────────
class DQHRSWorld(World):
    """Dragon Quest Heroes: Rocket Slime randomizer world.

    TODO: replace this docstring with a short player-facing description.
    """

    game              = "dqh_rs"
    options_dataclass = DQHRSOptions
    options: DQHRSOptions
    web               = DQHRSWebWorld()
    base_id           = BASE_ID

    item_name_to_id     = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    # A "name group" lets rules (and players' YAML) talk about a set of items at once.
    # Here: state.has_group("Slimes", player, 100) = "I own 100 slimes".
    item_name_groups = {
        "Slimes": {name for name in ITEM_TABLE if name.startswith("Slime_")},
    }

    settings: ClassVar[DQHRSSettings]

    # ── create_regions ─────────────────────────────────────────────────────────
    def create_regions(self) -> None:
        """Build the region graph (regions, locations, entrances)."""
        regions: dict[str, Region] = {}
        for region_name in ALL_REGIONS:
            region = Region(region_name, self.player, self.multiworld)
            regions[region_name] = region
            self.multiworld.regions.append(region)

        # Add locations to their respective regions.
        for location_name, loc_data in LOCATION_TABLE.items():
            region = regions[loc_data.region_name]
            location = DQHRSLocation(
                self.player,
                location_name,
                self.location_name_to_id[location_name],
                region,
            )
            region.locations.append(location)

        # ── Victory event ──────────────────────────────────────────────────────
        # An EVENT is a location with id=None holding a locked item with id=None.
        # It exists only during generation: it lets the generator answer
        # "can the player win?". It is never sent to the player. The real goal
        # is reported by the client (see client.py, _check_goal).
        # The rule that decides when it is reachable lives in rules.py (per goal).
        victory = DQHRSLocation(self.player, "Victory", None, regions["Boingburg"])
        victory.place_locked_item(
            DQHRSItem("Victory", ItemClassification.progression, None, self.player)
        )
        regions["Boingburg"].locations.append(victory)

        # Le point de départ mène au hub
        regions["Menu"].connect(regions["Boingburg"], "Menu -> Boingburg")

        # La première moitié de la forêt : accessible d'entrée de jeu (pas de règle)
        regions["Boingburg"].connect(regions["Forewood_Forest_part1"], "Boingburg -> Forewood_Forest_part1")

        # Les 6 zones verrouillées : une porte chacune, avec le nom EXACT attendu par rules.py
        for zone in (
            "Tootinschleimans_Tomb",
            "Mt_Krakatroda",
            "Backwoods",
            "Callmigh_Bluff",
            "Flucifers_Necropolis",
            "Flying_Clawtress",
        ):
            regions["Boingburg"].connect(regions[zone], f"Boingburg -> {zone}")

        # La forêt complète s'atteint UNIQUEMENT depuis la tombe
        regions["Tootinschleimans_Tomb"].connect(regions["Forewood_Forest"], "Tootinschleimans_Tomb -> Forewood_Forest")

    # ── create_items ───────────────────────────────────────────────────────────
    def create_items(self) -> None:
        """Fill the multiworld item pool: exactly one item per location.

        Priority order (so that nothing important is ever silently dropped):
          1. Access_* and Slime_* items: ALWAYS in the pool.
          2. Filler ("100 Gold"): a share of the remaining slots, set by filler_weight.
          3. "... Unlocked" items: drawn at random to fill what is left.
             The ones that do not fit are given to the player at the start
             (precollected) instead of being lost.
        """
        location_count = len(LOCATION_TABLE)  # the Victory event is not counted (no real id)

        # 1. Mandatory items
        pool: list[DQHRSItem] = [
            self.create_item(name)
            for name in ITEM_TABLE
            if name.startswith(("Access_", "Slime_"))
        ]
        free_slots = location_count - len(pool)
        if free_slots < 0:
            raise Exception(
                f"DQH-RS: {len(pool)} mandatory items but only {location_count} locations."
            )

        # 2. Filler: filler_weight 1..10 -> 10%..100% of the free slots
        filler_count = free_slots * self.options.filler_weight.value // 10
        unlocked_slots = free_slots - filler_count

        # 3. "Unlocked" items: random draw, the overflow starts in the player's inventory
        unlocked_names = [name for name in ITEM_TABLE if name.endswith(" Unlocked")]
        self.random.shuffle(unlocked_names)  # self.random = the seeded RNG of this world
        for name in unlocked_names[:unlocked_slots]:
            pool.append(self.create_item(name))
        for name in unlocked_names[unlocked_slots:]:
            self.multiworld.push_precollected(self.create_item(name))

        # Pad with filler until the pool matches the number of locations
        while len(pool) < location_count:
            pool.append(self.create_item(self.get_filler_item_name()))

        self.multiworld.itempool += pool

    # ── create_item (helper) ───────────────────────────────────────────────────
    def create_item(self, name: str) -> DQHRSItem:
        """Build a single DQHRSItem from its name."""
        data = ITEM_TABLE[name]
        classification = data.classification

        # With the "save all slimes" goal the player needs all 100 Slime items,
        # so they become progression (= the generator must place and guarantee them).
        if name.startswith("Slime_") and self.options.goal == Goal.option_save_all_slimes:
            classification = ItemClassification.progression

        return DQHRSItem(name, classification, self.item_name_to_id[name], self.player)

    # ── get_filler_item_name ───────────────────────────────────────────────────
    def get_filler_item_name(self) -> str:
        return "100 Gold"

    # ── set_rules ──────────────────────────────────────────────────────────────
    def set_rules(self) -> None:
        """Delegate to rules.py."""
        _set_rules(self)

    # ── fill_slot_data ─────────────────────────────────────────────────────────
    def fill_slot_data(self) -> dict:
        """Data sent to the client after it connects (read via ctx.slot_data)."""
        return {
            "goal": self.options.goal.value,
        }