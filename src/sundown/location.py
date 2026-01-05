"""Location utilities for zipcode lookup and timezone detection."""

from dataclasses import dataclass

import pgeocode
from timezonefinder import TimezoneFinder


@dataclass
class Location:
    """A geographic location with coordinates and timezone."""

    latitude: float
    longitude: float
    timezone: str
    name: str = ""


_tf: TimezoneFinder | None = None


def _get_timezone_finder() -> TimezoneFinder:
    """Get or create a TimezoneFinder instance (cached)."""
    global _tf
    if _tf is None:
        _tf = TimezoneFinder()
    return _tf


def get_timezone(latitude: float, longitude: float) -> str | None:
    """Get timezone name for coordinates.

    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees

    Returns:
        Timezone name (e.g., 'America/New_York') or None if not found.
    """
    tf = _get_timezone_finder()
    return tf.timezone_at(lat=latitude, lng=longitude)


def from_zipcode(zipcode: str, country: str = "US") -> Location | None:
    """Look up location from a postal/zip code.

    Args:
        zipcode: Postal code (e.g., '10001' for US, 'SW1A 1AA' for UK)
        country: Two-letter country code (default: 'US')

    Returns:
        Location with coordinates and timezone, or None if not found.
    """
    nomi = pgeocode.Nominatim(country)
    result = nomi.query_postal_code(zipcode)

    if result is None or result.latitude != result.latitude:  # NaN check
        return None

    lat = float(result.latitude)
    lon = float(result.longitude)
    tz = get_timezone(lat, lon)

    name_parts = []
    if hasattr(result, "place_name") and result.place_name:
        name_parts.append(str(result.place_name))
    if hasattr(result, "state_name") and result.state_name:
        name_parts.append(str(result.state_name))

    return Location(
        latitude=lat,
        longitude=lon,
        timezone=tz or "",
        name=", ".join(name_parts) if name_parts else zipcode,
    )


def from_coordinates(latitude: float, longitude: float) -> Location:
    """Create a Location from coordinates with automatic timezone detection.

    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees

    Returns:
        Location with timezone filled in.
    """
    tz = get_timezone(latitude, longitude)
    return Location(
        latitude=latitude,
        longitude=longitude,
        timezone=tz or "",
        name=f"{latitude:.2f}, {longitude:.2f}",
    )
