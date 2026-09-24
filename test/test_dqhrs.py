# test_dqhrs.py — Unit tests for the DQH-RS world.
#
# Tests run with:
#   AP_TEST_WORLDS=DQH-RS pytest worlds/DQH-RS/test/
#
# WorldTestBase already runs a set of default checks for free:
#   - the world generates without errors
#   - every location is reachable in some order
#   - no location is permanently locked
#   - the completion condition is beatable
#
# Add your own tests below for anything that is specific to this world.
#
# Useful assertion helpers from WorldTestBase:
#   self.assertBeatable(True/False)
#   self.assertAccessDependency([location_names], [[item_names]])
#   self.collect_by_name([item_names])   → put items in state, return state
#   self.multiworld.get_location(name, self.player)
#   self.multiworld.get_entrance(name, self.player)

from test.bases import WorldTestBase


class TestDQHRSWorld(WorldTestBase):
    """Default generation tests inherited from WorldTestBase."""
    game = "DQH-RS"


class TestDQHRSAccessRules(WorldTestBase):
    """Tests that verify specific access dependencies."""
    game = "DQH-RS"

    def test_start_zone_has_checks(self) -> None:
        """La zone de départ doit contenir au moins un check."""
        part1 = self.multiworld.get_region("Forewood_Forest_part1", self.player)
        self.assertGreater(len(part1.locations), 0)

    def test_full_forest_needs_tomb(self) -> None:
        """La forêt complète exige l'accès à la tombe."""
        forest = self.multiworld.get_region("Forewood_Forest", self.player)
        names = [loc.name for loc in forest.locations]
        self.assertAccessDependency(names, [["Access_Tootinschleiman_Tomb"]])

    def test_area1_requires_key_item_1(self) -> None:
        """Area 1 should not be accessible without Key Item 1."""
        # TODO: replace with real location and item names.
        self.assertAccessDependency(
            ["TODO_Area1_Chest_1", "TODO_Area1_Chest_2"],
            [["TODO_Key_Item_1"]],
        )

    def test_boss_reward_requires_key_item_2(self) -> None:
        """The Area 1 boss reward needs Key Item 2 in addition to Key Item 1."""
        # TODO: adjust once real rules are written.
        self.assertAccessDependency(
            ["TODO_Area1_Boss_Reward"],
            [["TODO_Key_Item_2"]],
        )

    def test_game_is_beatable_with_all_items(self) -> None:
        """The game must be completable when all items are collected."""
        self.collect_all_but([])  # collect everything
        self.assertBeatable(True)


class TestDQHRSOptions(WorldTestBase):
    """Tests that verify option-driven behavior."""
    game = "DQH-RS"

    # TODO: add option overrides using the `options` class attribute.
    # Example:
    #   options = {"extra_checks": 0}
    #
    # Then verify that the locations added by extra_checks are absent.
