"""
enderscope: control library for the Enderscope 3D-printer-based microscope.

This package preserves the original flat `enderscope` API (``from enderscope
import Stage, Enderlights, ...``) while splitting the implementation into
smaller modules for maintainability.
"""

from .constants import G_CODES, DIRECTION_PREFIXES, ENDER3V3SE
from .serial_utils import SerialUtils
from .serial_device import SerialDevice
from .stage import Stage
from .panel import Panel
from .lights import Enderlights
from .scan_patterns import ScanPatterns
from .discovery import autoconnect

__all__ = [
    "G_CODES",
    "DIRECTION_PREFIXES",
    "ENDER3V3SE",
    "SerialUtils",
    "SerialDevice",
    "Stage",
    "Panel",
    "Enderlights",
    "ScanPatterns",
    "autoconnect",
]
