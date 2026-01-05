"""Core gamma/color temperature adjustment functions."""

import ctypes
import math
import sys
from ctypes import wintypes

# Color temperature presets (Kelvin)
TEMPERATURE_DAYLIGHT = 6500  # Neutral/default
TEMPERATURE_SUNSET = 4500
TEMPERATURE_CANDLE = 2700
TEMPERATURE_NIGHT = 3400


class DISPLAY_DEVICE(ctypes.Structure):
    """Windows DISPLAY_DEVICE structure for enumerating monitors."""

    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


# Display device state flags
DISPLAY_DEVICE_ACTIVE = 0x00000001
DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001


def get_active_displays() -> list[str]:
    """Get a list of active display device names.

    Returns:
        List of device names (e.g., ['\\\\.\\DISPLAY1', '\\\\.\\DISPLAY2'])
    """
    if sys.platform != "win32":
        return []

    user32 = ctypes.windll.user32
    displays = []

    i = 0
    while True:
        device = DISPLAY_DEVICE()
        device.cb = ctypes.sizeof(DISPLAY_DEVICE)

        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(device), 0):
            break

        if device.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
            displays.append(device.DeviceName)

        i += 1

    return displays


def kelvin_to_rgb(kelvin: int) -> tuple[float, float, float]:
    """Convert color temperature in Kelvin to RGB multipliers (0.0-1.0).

    Based on Tanner Helland's algorithm.
    """
    temp = kelvin / 100.0

    # Red
    if temp <= 66:
        red = 1.0
    else:
        red = temp - 60
        red = 329.698727446 * (red**-0.1332047592)
        red = max(0, min(255, red)) / 255.0

    # Green
    if temp <= 66:
        green = 99.4708025861 * math.log(temp) - 161.1195681661 if temp > 1 else 0
    else:
        green = temp - 60
        green = 288.1221695283 * (green**-0.0755148492)
    green = max(0, min(255, green)) / 255.0

    # Blue
    if temp >= 66:
        blue = 1.0
    elif temp <= 19:
        blue = 0.0
    else:
        blue = temp - 10
        blue = 138.5177312231 * math.log(blue) - 305.0447927307
        blue = max(0, min(255, blue)) / 255.0

    return (red, green, blue)


def _create_gamma_ramp(red: float, green: float, blue: float) -> list[list[int]]:
    """Create a gamma ramp array for the given RGB multipliers."""
    ramp = [[0] * 256 for _ in range(3)]
    multipliers = [red, green, blue]

    for i in range(256):
        for channel in range(3):
            value = int(i * 256 * multipliers[channel])
            ramp[channel][i] = min(65535, max(0, value))

    return ramp


def _apply_gamma_to_dc(hdc, ramp_array) -> bool:
    """Apply gamma ramp to a device context."""
    gdi32 = ctypes.windll.gdi32
    result = gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp_array))
    return bool(result)


def set_color_temperature(kelvin: int) -> bool:
    """Set the screen color temperature in Kelvin on all monitors.

    Args:
        kelvin: Color temperature (1000-10000K typical range)
                6500K = neutral daylight
                3400K = warm evening
                2700K = candlelight

    Returns:
        True if successful on all monitors, False otherwise.
    """
    if sys.platform != "win32":
        raise NotImplementedError(f"Platform {sys.platform} not yet supported")

    red, green, blue = kelvin_to_rgb(kelvin)
    ramp = _create_gamma_ramp(red, green, blue)

    # Create ctypes array
    ramp_array = (wintypes.WORD * 256 * 3)()
    for channel in range(3):
        for i in range(256):
            ramp_array[channel][i] = ramp[channel][i]

    gdi32 = ctypes.windll.gdi32
    user32 = ctypes.windll.user32

    # Get all active displays
    displays = get_active_displays()

    if not displays:
        # Fallback to primary display
        hdc = user32.GetDC(None)
        if not hdc:
            return False
        try:
            return _apply_gamma_to_dc(hdc, ramp_array)
        finally:
            user32.ReleaseDC(None, hdc)

    # Apply to each display
    all_success = True
    for display_name in displays:
        hdc = gdi32.CreateDCW("DISPLAY", display_name, None, None)
        if hdc:
            try:
                if not _apply_gamma_to_dc(hdc, ramp_array):
                    all_success = False
            finally:
                gdi32.DeleteDC(hdc)
        else:
            all_success = False

    return all_success


def reset_gamma() -> bool:
    """Reset gamma to default (6500K neutral)."""
    return set_color_temperature(TEMPERATURE_DAYLIGHT)


def get_temperature_for_time(hour: float, day_temp: int = 6500, night_temp: int = 3400) -> int:
    """Calculate appropriate color temperature for a given hour.

    Args:
        hour: Hour of day (0-24, can be fractional)
        day_temp: Daytime temperature in Kelvin
        night_temp: Nighttime temperature in Kelvin

    Returns:
        Interpolated color temperature in Kelvin.
    """
    # Transition periods (hours)
    morning_start = 6.0
    morning_end = 8.0
    evening_start = 18.0
    evening_end = 20.0

    if morning_end <= hour < evening_start:
        # Daytime
        return day_temp
    elif hour < morning_start or hour >= evening_end:
        # Nighttime
        return night_temp
    elif morning_start <= hour < morning_end:
        # Morning transition
        progress = (hour - morning_start) / (morning_end - morning_start)
        return int(night_temp + (day_temp - night_temp) * progress)
    else:
        # Evening transition
        progress = (hour - evening_start) / (evening_end - evening_start)
        return int(day_temp + (night_temp - day_temp) * progress)
