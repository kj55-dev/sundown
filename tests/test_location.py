"""Tests for location module."""

from sundown.location import from_coordinates, from_zipcode, get_timezone


class TestFromZipcode:
    """Tests for from_zipcode function."""

    def test_valid_us_zipcode(self):
        """Valid US zipcode should return location."""
        loc = from_zipcode("10001", "US")
        assert loc is not None
        assert loc.name == "New York, New York"
        assert 40.7 < loc.latitude < 40.8
        assert -74.0 < loc.longitude < -73.9
        assert loc.timezone == "America/New_York"

    def test_invalid_zipcode(self):
        """Invalid zipcode should return None."""
        loc = from_zipcode("00000", "US")
        assert loc is None

    def test_uk_postcode(self):
        """UK postcode should work with country code."""
        loc = from_zipcode("SW1A 1AA", "GB")
        assert loc is not None
        assert loc.timezone == "Europe/London"


class TestFromCoordinates:
    """Tests for from_coordinates function."""

    def test_nyc_coordinates(self):
        """NYC coordinates should detect Eastern timezone."""
        loc = from_coordinates(40.7128, -74.0060)
        assert loc.timezone == "America/New_York"

    def test_london_coordinates(self):
        """London coordinates should detect London timezone."""
        loc = from_coordinates(51.5074, -0.1278)
        assert loc.timezone == "Europe/London"

    def test_tokyo_coordinates(self):
        """Tokyo coordinates should detect Tokyo timezone."""
        loc = from_coordinates(35.6762, 139.6503)
        assert loc.timezone == "Asia/Tokyo"


class TestGetTimezone:
    """Tests for get_timezone function."""

    def test_returns_string(self):
        """Should return a timezone string."""
        tz = get_timezone(40.7128, -74.0060)
        assert isinstance(tz, str)
        assert "/" in tz  # Timezone format like "America/New_York"
