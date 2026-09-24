# rules.py — Access rules for regions and locations.
#
# An "access rule" is a function that receives a CollectionState (everything the
# player currently has) and returns True if the location or entrance is reachable.
#
# Core helpers on CollectionState:
#   state.has("Item Name", player)           → player owns at least one of this item
#   state.has_any({"A", "B"}, player)        → player owns A or B (or both)
#   state.has_all({"A", "B"}, player)        → player owns both A and B
#   state.has_group("group_name", player)    → player owns enough of a group
#   state.count("Item Name", player)         → how many copies the player has
#
# The two main setter functions from worlds.generic.Rules:
#   set_rule(location_or_entrance, rule_fn)  → replaces the rule entirely
#   add_rule(location_or_entrance, rule_fn)  → ANDs a new condition with existing rule
#
# Note: rules run during generation, not at runtime.  They shape what the generator
#       considers logically reachable.  The client enforces nothing here.
#
# TODO: fill in real rules based on your game research.
# TODO: every item that gates a location must be in the item pool (items.py).
# TODO: every option that affects logic must be read from `world.options` here.

from worlds.generic.Rules import set_rule, add_rule

# TYPE_CHECKING guard keeps the import from creating a real circular dependency.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import DQHRSWorld


def set_rules(world: "DQHRSWorld") -> None:
    """Attach all access rules to regions and locations for this player."""
    multiworld = world.multiworld
    player = world.player

    zone_to_item = {
        "Tootinschleimans_Tomb":   "Access_Tootinschleiman_Tomb",
        "Mt_Krakatroda":           "Access_Mt_Krakatroda",
        "Backwoods":               "Access_Backwoods",
        "Callmigh_Bluff":          "Access_Callmigh_Bluff",
        "Flucifers_Necropolis":    "Access_Flucifer_Necropolis",
        "Flying_Clawtress":        "Access_Flying_Clawtress",
    }

    for zone_name, item_name in zone_to_item.items():
        set_rule(
            multiworld.get_entrance(f"Boingburg -> {zone_name}", player),
            lambda state, item=item_name: state.has(item, player),
        )

    # ── Entrance rules ─────────────────────────────────────────────────────────
    # An entrance connects two regions.  Gate it if entering the new region
    # requires an item.
    #
    # Example pattern:
    #   set_rule(
    #       multiworld.get_entrance("Menu -> TODO_Area_1", player),
    #       lambda state: state.has("TODO_Key_Item_1", player),
    #   )
    #
    # TODO: replace the example with real entrances and real items.
    # set_rule(
    #     multiworld.get_entrance("Menu -> TODO_Area_1", player),
    #     lambda state: state.has("TODO_Key_Item_1", player),
    # )

    # set_rule(
    #     multiworld.get_entrance("TODO_Area_1 -> TODO_Area_2", player),
    #     lambda state: (
    #         state.has("TODO_Key_Item_1", player)
    #         and state.has("TODO_Key_Item_2", player)
    #     ),
    # )

    # ── Location rules ─────────────────────────────────────────────────────────
    # Use add_rule when a specific location inside a region has an extra
    # requirement beyond being able to enter the region at all.
    #
    # Example:
    #   add_rule(
    #       multiworld.get_location("TODO_Area1_Boss_Reward", player),
    #       lambda state: state.has("TODO_Key_Item_2", player),
    #   )
    #
    # TODO: add per-location rules for every locked spot in the game.
    # add_rule(
    #     multiworld.get_location("TODO_Area1_Boss_Reward", player),
    #     lambda state: state.has("TODO_Key_Item_2", player),
    # )

    # ── Option-driven rules ────────────────────────────────────────────────────
    # If an option changes what is reachable, apply the rule conditionally here.
    #
    # Example:
    #   if world.options.extra_checks:
    #       add_rule(
    #           multiworld.get_location("TODO_Optional_Location", player),
    #           lambda state: state.has("TODO_Useful_Item_1", player),
    #       )

    # ── Completion condition ────────────────────────────────────────────────────
    # This is the victory condition from the generator's perspective.
    # It must be satisfied for the game to be considered beatable.
    # The actual gameplay completion is reported by the client (client.py).
    # multiworld.completion_condition[player] = lambda state: (
    #     state.has("TODO_Key_Item_1", player)  # TODO: replace with real goal check
    #     and state.has("TODO_Key_Item_2", player)
    # )
