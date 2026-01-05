"""Tests for gamma module."""

from sundown.gamma import get_temperature_for_time, kelvin_to_rgb


class TestKelvinToRgb:
    """Tests for kelvin_to_rgb function."""

    def test_daylight_6500k(self):
        """6500K should be close to neutral white."""
        r, g, b = kelvin_to_rgb(6500)
        assert 0.99 <= r <= 1.0
        assert 0.99 <= g <= 1.0
        assert 0.95 <= b <= 1.0  # Blue is slightly less at 6500K

    def test_warm_2700k(self):
        """2700K should be warm (high red, low blue)."""
        r, g, b = kelvin_to_rgb(2700)
        assert r == 1.0
        assert g < r
        assert b < g

    def test_very_warm_2000k(self):
        """2000K should be very warm/orange."""
        r, g, b = kelvin_to_rgb(2000)
        assert r == 1.0
        assert 0.4 < g < 0.7
        assert b < 0.2

    def test_cool_10000k(self):
        """10000K should be cool (high blue)."""
        r, g, b = kelvin_to_rgb(10000)
        assert b == 1.0
        assert r < 1.0

    def test_returns_tuple_of_floats(self):
        """Should return a tuple of 3 floats."""
        result = kelvin_to_rgb(5000)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    def test_values_in_range(self):
        """All RGB values should be between 0 and 1."""
        for kelvin in [1000, 2000, 4000, 6500, 8000, 10000]:
            r, g, b = kelvin_to_rgb(kelvin)
            assert 0.0 <= r <= 1.0
            assert 0.0 <= g <= 1.0
            assert 0.0 <= b <= 1.0


class TestGetTemperatureForTime:
    """Tests for get_temperature_for_time function."""

    def test_midday_returns_day_temp(self):
        """Midday should return day temperature."""
        temp = get_temperature_for_time(12.0, day_temp=6500, night_temp=3400)
        assert temp == 6500

    def test_midnight_returns_night_temp(self):
        """Midnight should return night temperature."""
        temp = get_temperature_for_time(0.0, day_temp=6500, night_temp=3400)
        assert temp == 3400

    def test_late_night_returns_night_temp(self):
        """Late night (2am) should return night temperature."""
        temp = get_temperature_for_time(2.0, day_temp=6500, night_temp=3400)
        assert temp == 3400

    def test_morning_transition(self):
        """7am should be in morning transition (between night and day)."""
        temp = get_temperature_for_time(7.0, day_temp=6500, night_temp=3400)
        assert 3400 < temp < 6500

    def test_evening_transition(self):
        """7pm should be in evening transition (between day and night)."""
        temp = get_temperature_for_time(19.0, day_temp=6500, night_temp=3400)
        assert 3400 < temp < 6500
