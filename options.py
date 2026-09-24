# options.py — Player-configurable settings for this world.
#
# Options are exposed to the player in their YAML config file and in the
# Archipelago webhost.  They control things like:
#   - which items are in the pool
#   - which locations are active
#   - difficulty modifiers
#   - goal selection
#
# Every option class inherits from a base type in Options.py in the AP core:
#   Toggle           → 0 (off) or 1 (on)
#   DefaultOnToggle  → same as Toggle but defaults to 1
#   Choice           → named enum (option_a, option_b, …)
#   Range            → integer between a min and max
#   NamedRange       → Range with named special values at specific numbers
#
# The class docstring becomes the description shown in the web UI and YAML docs.
# Keep it short and player-facing — no internal notes.
#
# TODO: remove options you do not need.
# TODO: add options that fit the game's design.
# TODO: make sure every option that affects logic is also referenced in rules.py.

from dataclasses import dataclass
from Options import Toggle, DefaultOnToggle, Choice, Range, PerGameCommonOptions


class Goal(Choice):
    """Choose what the player must accomplish to win.

    - defeat_final_boss: the classic goal
    - save_all_slime: find all 100 slimes
    """
    display_name = "Goal"
    option_defeat_final_boss = 0
    option_save_all_slimes = 1
    #option_alternate_goal = n
    default = 0


class IncludeTraps(Toggle):
    """Whether trap items can appear in the item pool.

    Enable for a harder experience.
    """
    display_name = "Include Traps"


class ExtraChecks(DefaultOnToggle):
    """Whether optional side-content locations are added to the pool.

    Disable to shorten the game's check count.
    """
    display_name = "Extra Checks"


class FillerWeight(Range):
    """How many filler items are added per missing progression slot.

    Higher values mean more consumable items in the pool.
    """
    display_name = "Filler Weight"
    range_start = 1
    range_end = 10
    default = 3


# ── Master options dataclass ───────────────────────────────────────────────────
# This is what __init__.py imports as options_dataclass.
# Every field name becomes the YAML key the player writes in their config.
@dataclass
class DQHRSOptions(PerGameCommonOptions):
    goal:          Goal
    include_traps: IncludeTraps
    extra_checks:  ExtraChecks
    filler_weight: FillerWeight
