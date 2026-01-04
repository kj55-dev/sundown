"""Time-based scheduling for automatic color temperature adjustment."""

import threading
import time
from datetime import datetime
from typing import Callable

from astral import LocationInfo
from astral.sun import sun

from sundown.gamma import set_color_temperature, get_temperature_for_time


class SundownScheduler:
    """Scheduler that automatically adjusts color temperature based on time."""

    def __init__(
        self,
        day_temp: int = 6500,
        night_temp: int = 3400,
        update_interval: float = 60.0,
        location: LocationInfo | None = None,
    ):
        """Initialize the scheduler.

        Args:
            day_temp: Daytime color temperature in Kelvin
            night_temp: Nighttime color temperature in Kelvin
            update_interval: Seconds between temperature updates
            location: Optional location for sun-based transitions
        """
        self.day_temp = day_temp
        self.night_temp = night_temp
        self.update_interval = update_interval
        self.location = location

        self._running = False
        self._thread: threading.Thread | None = None
        self._on_change: Callable[[int], None] | None = None
        self._current_temp: int | None = None

    def on_change(self, callback: Callable[[int], None]) -> None:
        """Set a callback to be called when temperature changes."""
        self._on_change = callback

    def _get_sun_times(self) -> tuple[float, float] | None:
        """Get sunrise and sunset hours for today."""
        if self.location is None:
            return None

        try:
            s = sun(self.location.observer, date=datetime.now().date())
            sunrise = s["sunrise"].hour + s["sunrise"].minute / 60.0
            sunset = s["sunset"].hour + s["sunset"].minute / 60.0
            return (sunrise, sunset)
        except Exception:
            return None

    def _calculate_temperature(self) -> int:
        """Calculate the current target temperature."""
        now = datetime.now()
        hour = now.hour + now.minute / 60.0

        sun_times = self._get_sun_times()
        if sun_times:
            sunrise, sunset = sun_times
            # Use sun times for transitions
            if sunrise + 1 <= hour < sunset - 1:
                return self.day_temp
            elif hour < sunrise or hour >= sunset:
                return self.night_temp
            elif sunrise <= hour < sunrise + 1:
                progress = hour - sunrise
                return int(self.night_temp + (self.day_temp - self.night_temp) * progress)
            else:
                progress = hour - (sunset - 1)
                return int(self.day_temp + (self.night_temp - self.day_temp) * progress)
        else:
            return get_temperature_for_time(hour, self.day_temp, self.night_temp)

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            temp = self._calculate_temperature()

            if temp != self._current_temp:
                set_color_temperature(temp)
                self._current_temp = temp
                if self._on_change:
                    self._on_change(temp)

            time.sleep(self.update_interval)

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

    def __enter__(self) -> "SundownScheduler":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()
