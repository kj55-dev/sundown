"""Sundown - Screen color temperature adjustment for Python."""

from sundown.gamma import (
    set_color_temperature,
    reset_gamma,
    get_temperature_for_time,
    kelvin_to_rgb,
    TEMPERATURE_DAYLIGHT,
    TEMPERATURE_NIGHT,
    TEMPERATURE_SUNSET,
    TEMPERATURE_CANDLE,
)
from sundown.scheduler import SundownScheduler

__version__ = "0.1.0"
__all__ = [
    "set_color_temperature",
    "reset_gamma",
    "get_temperature_for_time",
    "kelvin_to_rgb",
    "SundownScheduler",
    "TEMPERATURE_DAYLIGHT",
    "TEMPERATURE_NIGHT",
    "TEMPERATURE_SUNSET",
    "TEMPERATURE_CANDLE",
]
