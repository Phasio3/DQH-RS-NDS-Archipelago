# settings.py — Per-player local settings for DQH-RS.
#
# Declares where the player's own copy of the ROM lives, so the patch-apply
# step (run on the player's machine) knows which file to patch.

from __future__ import annotations
import settings


class DQHRSSettings(settings.Group):
    class RomFile(settings.UserFilePath):
        """Path to your legally-obtained Dragon Quest Heroes: Rocket Slime (USA) ROM file."""
        description = "DQH-RS ROM File"
        copy_to = "DQH-RS (USA).nds"
        md5s = ["fd690dd6ce68037947c7a6ac87440f51"]

    rom_file: RomFile = RomFile(RomFile.copy_to)