# rules.py — Access rules for regions and locations.
#
# An "access rule" is a function that receives a CollectionState (everything the
# player currently has) and returns True if the location or entrance is reachable.
#
# Core helpers on CollectionState:
#   state.has("Item Name", player)           → player owns at least one of this item
#   state.has_all({"A", "B"}, player)        → player owns both A and B
#   state.has_group("group", player, n)      → player owns at least n items of the group
#
# The setter function from worlds.generic.Rules:
#   set_rule(location_or_entrance, rule_fn)  → replaces the rule entirely
#
# Note: rules run during generation, not at runtime.  They shape what the generator
#       considers logically reachable.  The client enforces nothing here.

from worlds.generic.Rules import set_rule

from .options import Goal

# TYPE_CHECKING guard keeps the import from creating a real circular dependency.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import DQHRSWorld


# Zone (region name) -> item that opens the door to it.
ZONE_TO_ITEM: dict[str, str] = {
    "Tootinschleimans_Tomb":   "Access_Tootinschleiman_Tomb",
    "Mt_Krakatroda":           "Access_Mt_Krakatroda",
    "Backwoods":               "Access_Backwoods",
    "Callmigh_Bluff":          "Access_Callmigh_Bluff",
    "Flucifers_Necropolis":    "Access_Flucifer_Necropolis",
    "Flying_Clawtress":        "Access_Flying_Clawtress",
}
ACCESS_ITEMS: list[str] = list(ZONE_TO_ITEM.values())

# Region where the final boss lives: needed to win with the "defeat_final_boss" goal.
FINAL_BOSS_ACCESS_ITEM = "Access_Flying_Clawtress"

TOTAL_SLIMES = 100


def set_rules(world: "DQHRSWorld") -> None:
    """Attach all access rules to regions and locations for this player."""
    multiworld = world.multiworld
    player = world.player

    # ── Entrance rules: one locked door per zone ───────────────────────────────
    for zone_name, item_name in ZONE_TO_ITEM.items():
        set_rule(
            multiworld.get_entrance(f"Boingburg -> {zone_name}", player),
            lambda state, item=item_name: state.has(item, player),
        )

    # ── Goal ───────────────────────────────────────────────────────────────────
    # "Victory" is an EVENT location (no real id) created in __init__.py. The
    # generator considers the game won when the player can "collect" it.
    # Each goal only changes the rule that decides WHEN Victory becomes reachable.
    victory = multiworld.get_location("Victory", player)

    if world.options.goal == Goal.option_defeat_final_boss:
        # Being able to enter the final boss's zone.
        set_rule(victory, lambda state: state.has(FINAL_BOSS_ACCESS_ITEM, player))

    elif world.options.goal == Goal.option_save_all_slimes:
        # Every zone must be enterable (all 100 slimes are spread over them) AND all
        # 100 Slime items must reach the player (the in-game slime counter depends on them).
        set_rule(
            victory,
            lambda state: state.has_all(ACCESS_ITEMS, player)
            and state.has_group("Slimes", player, TOTAL_SLIMES),
        )

    multiworld.completion_condition[player] = lambda state: state.has("Victory", player)