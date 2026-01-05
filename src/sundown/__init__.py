"""Sundown - Screen color temperature adjustment for Python."""

from sundown.gamma import (
    TEMPERATURE_CANDLE,
    TEMPERATURE_DAYLIGHT,
    TEMPERATURE_NIGHT,
    TEMPERATURE_SUNSET,
    get_active_displays,
    get_temperature_for_time,
    kelvin_to_rgb,
    reset_gamma,
    set_color_temperature,
)
from sundown.location import (
    Location,
    from_coordinates,
    from_zipcode,
    get_timezone,
)
from sundown.scheduler import SundownScheduler

__version__ = "0.1.0"
__all__ = [
    "set_color_temperature",
    "reset_gamma",
    "get_temperature_for_time",
    "get_active_displays",
    "kelvin_to_rgb",
    "SundownScheduler",
    "Location",
    "from_zipcode",
    "from_coordinates",
    "get_timezone",
    "TEMPERATURE_DAYLIGHT",
    "TEMPERATURE_NIGHT",
    "TEMPERATURE_SUNSET",
    "TEMPERATURE_CANDLE",
]
