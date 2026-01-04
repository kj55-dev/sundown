"""Time-based scheduling for automatic color temperature adjustment."""

import math
import threading
import time
from datetime import datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun

from sundown.gamma import set_color_temperature, get_temperature_for_time


def _smooth_step(t: float) -> float:
    """Attempt a smooth interpolation (slow start/end) using cosine."""
    # t is 0-1, returns 0-1 with smooth easing
    return (1 - math.cos(t * math.pi)) / 2


class SundownScheduler:
    """Scheduler that automatically adjusts color temperature based on time."""

    def __init__(
        self,
        day_temp: int = 6500,
        night_temp: int = 3400,
        update_interval: float = 30.0,
        location: LocationInfo | None = None,
        transition_minutes: float = 60.0,
    ):
        """Initialize the scheduler.

        Args:
            day_temp: Daytime color temperature in Kelvin
            night_temp: Nighttime color temperature in Kelvin
            update_interval: Seconds between temperature updates
            location: Optional location for sun-based transitions
            transition_minutes: Duration of sunrise/sunset transitions
        """
        self.day_temp = day_temp
        self.night_temp = night_temp
        self.update_interval = update_interval
        self.location = location
        self.transition_minutes = transition_minutes

        self._running = False
        self._thread: threading.Thread | None = None
        self._on_change: Callable[[int], None] | None = None
        self._current_temp: int | None = None
        self._sun_cache: dict | None = None
        self._sun_cache_date: datetime | None = None

    def on_change(self, callback: Callable[[int], None]) -> None:
        """Set a callback to be called when temperature changes."""
        self._on_change = callback

    def _get_sun_times(self) -> dict | None:
        """Get sun times for today, with caching."""
        if self.location is None:
            return None

        today = datetime.now().date()

        # Use cached value if same day
        if self._sun_cache_date == today and self._sun_cache is not None:
            return self._sun_cache

        try:
            tz = ZoneInfo(self.location.timezone) if self.location.timezone else None
            s = sun(self.location.observer, date=today, tzinfo=tz)
            self._sun_cache = s
            self._sun_cache_date = today
            return s
        except Exception:
            return None

    def _datetime_to_hours(self, dt: datetime) -> float:
        """Convert datetime to fractional hours."""
        return dt.hour + dt.minute / 60.0 + dt.second / 3600.0

    def _calculate_temperature(self) -> int:
        """Calculate the current target temperature with smooth transitions."""
        now = datetime.now()
        hour = self._datetime_to_hours(now)
        transition_hours = self.transition_minutes / 60.0

        sun_times = self._get_sun_times()

        if sun_times:
            sunrise = self._datetime_to_hours(sun_times["sunrise"])
            sunset = self._datetime_to_hours(sun_times["sunset"])

            # Morning transition: starts at sunrise, ends transition_hours later
            morning_start = sunrise
            morning_end = sunrise + transition_hours

            # Evening transition: starts transition_hours before sunset, ends at sunset
            evening_start = sunset - transition_hours
            evening_end = sunset

            if morning_end <= hour < evening_start:
                # Full daytime
                return self.day_temp
            elif hour < morning_start or hour >= evening_end:
                # Full nighttime
                return self.night_temp
            elif morning_start <= hour < morning_end:
                # Morning transition (warming up)
                progress = (hour - morning_start) / transition_hours
                smooth_progress = _smooth_step(progress)
                return int(self.night_temp + (self.day_temp - self.night_temp) * smooth_progress)
            else:
                # Evening transition (cooling down)
                progress = (hour - evening_start) / transition_hours
                smooth_progress = _smooth_step(progress)
                return int(self.day_temp + (self.night_temp - self.day_temp) * smooth_progress)
        else:
            # Fallback to fixed schedule if no location
            return get_temperature_for_time(hour, self.day_temp, self.night_temp)

    def _apply_temperature(self, temp: int) -> None:
        """Apply temperature and notify callback if changed."""
        if temp != self._current_temp:
            set_color_temperature(temp)
            self._current_temp = temp
            if self._on_change:
                self._on_change(temp)

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        # Apply immediately on start
        self._apply_temperature(self._calculate_temperature())

        while self._running:
            time.sleep(self.update_interval)
            if self._running:
                self._apply_temperature(self._calculate_temperature())

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.update_interval + 1)
            self._thread = None

    def set_temperature_now(self, kelvin: int) -> None:
        """Manually override the current temperature."""
        self._apply_temperature(kelvin)

    def get_current_temperature(self) -> int | None:
        """Get the currently applied temperature."""
        return self._current_temp

    def __enter__(self) -> "SundownScheduler":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()
