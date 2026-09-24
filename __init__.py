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
#
# The World class must set:
#   game              → the exact string that identifies this world
#   options_dataclass → the Options dataclass from options.py
#   web               → a WebWorld instance with documentation wiring
#   base_id           → the numeric offset shared by all item/location IDs
#   item_name_to_id   → dict of item name → numeric ID
#   location_name_to_id → dict of location name → numeric ID
#
# TODO: fill in all TODO markers.
# TODO: import client.py so BizHawk auto-registers when this world loads.

from worlds.AutoWorld import World, WebWorld
from BaseClasses import Item, ItemClassification, Region, Location, Tutorial

from .items    import ITEM_TABLE, ITEM_NAME_TO_ID, BASE_ID, DQHRSItemData
from .locations import LOCATION_TABLE, LOCATION_NAME_TO_ID, ALL_REGIONS
from .options  import DQHRSOptions
from .rules    import set_rules as _set_rules
from .settings import DQHRSSettings

# Importing the client module registers DQHRSClient with BizHawk automatically.
from . import client  # noqa: F401

from typing import ClassVar
import os


# ── Web documentation ──────────────────────────────────────────────────────────
class DQHRSWebWorld(WebWorld):
    # TODO: write the actual doc files and update these paths.
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
# A thin subclass so AP can identify items as belonging to this world.
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
    web               = DQHRSWebWorld()
    base_id           = BASE_ID

    item_name_to_id     = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    settings: ClassVar[DQHRSSettings]

    # ── generate_early ─────────────────────────────────────────────────────────
    def generate_early(self) -> None:
        """Run before region graph is built.

        Use this if you need to compute derived properties from options before
        create_regions() is called.  Skip it if nothing needs to happen early.

        TODO: remove this method if you have nothing to compute here.
        """
        # Example: pre-compute which locations are active given options.
        # self.active_locations = {
        #     name for name, data in LOCATION_TABLE.items()
        #     if self._location_is_active(name, data)
        # }
        pass

    # ── create_regions ─────────────────────────────────────────────────────────
    def create_regions(self) -> None:
        """Build the region graph.

        A Region is a named section of the game.  Entrances connect regions.
        Locations live inside regions.  Rules (in rules.py) gate entrances
        and locations.

        The region named "Menu" must always exist — it is the starting point.
        """
        # Create one Region object per named area.
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

        # La forêt complète s'atteint UNIQUEMENT depuis la tombe (pas de règle ici : la tombe est déjà verrouillée)
        regions["Tootinschleimans_Tomb"].connect(regions["Forewood_Forest"], "Tootinschleimans_Tomb -> Forewood_Forest")

    # ── create_items ───────────────────────────────────────────────────────────
    def create_items(self) -> None:
        """Fill the multiworld item pool.

        The total item count must equal the total location count.
        If you have more locations than items, add filler.
        If you have more items than locations, remove some items or locations.
        """
        pool: list[DQHRSItem] = []

        for item_name, item_data in ITEM_TABLE.items():
            # TODO: add option-driven exclusions here if some items are optional.
            item = self.create_item(item_name)
            pool.append(item)

        # Pad with filler if the pool is short.
        location_count = len(LOCATION_TABLE)
        while len(pool) < location_count:
            pool.append(self.create_item(self.get_filler_item_name()))

        self.multiworld.itempool += pool

    # ── create_item (helper) ───────────────────────────────────────────────────
    def create_item(self, name: str) -> DQHRSItem:
        """Build a single DQHRSItem from its name."""
        data = ITEM_TABLE[name]
        return DQHRSItem(name, data.classification, self.item_name_to_id[name], self.player)

    # ── get_filler_item_name ───────────────────────────────────────────────────
    def get_filler_item_name(self) -> str:
        """Return the name of the default filler item.

        TODO: replace with the actual filler item name from items.py.
        """
        return "100 Gold"

    # ── set_rules ──────────────────────────────────────────────────────────────
    def set_rules(self) -> None:
        """Delegate to rules.py."""
        _set_rules(self)

    # ── fill_slot_data ─────────────────────────────────────────────────────────
    def fill_slot_data(self) -> dict:
        """Return a dict sent to the client after it connects.

        Only include data the client truly needs at runtime.
        Never put large blobs here — keep it small.

        TODO: add any seed-specific data the client.py needs.
        """
        return {
            "goal": self.options.goal.value,
            # Example: "death_link": bool(self.options.death_link),
        }
