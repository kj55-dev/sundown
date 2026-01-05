# Sundown

Screen color temperature adjustment for Python. Reduce blue light in the evening for better sleep.

## Installation

```bash
pip install sundown
```

Or with uv:
```bash
uv add sundown
```

## Usage

### Command Line

```bash
# Set color temperature manually
sundown set 3400            # Set to 3400K (warm)
sundown set --preset night  # Use preset (day/night/sunset/candle)
sundown reset               # Reset to 6500K (neutral)

# Run automatic adjustment based on time
sundown run                           # Use fixed schedule
sundown run --zipcode 10001           # Use sun times for location
sundown run --lat 40.7 --lon -74.0    # Use coordinates
sundown run -v                        # Verbose logging

# List displays
sundown displays
```

### Python API

```python
import sundown

# Set temperature directly
sundown.set_color_temperature(3400)  # Warm
sundown.reset_gamma()                 # Back to normal

# Get RGB values for a temperature
r, g, b = sundown.kelvin_to_rgb(2700)

# Location lookup
loc = sundown.from_zipcode("10001")
print(f"{loc.name}: {loc.timezone}")

# Automatic scheduling
scheduler = sundown.SundownScheduler(
    day_temp=6500,
    night_temp=3400,
)
scheduler.start()
```

## Features

- **Windows gamma adjustment** via SetDeviceGammaRamp API
- **Multi-monitor support** - applies to all connected displays
- **Zipcode/postal code lookup** - supports US, UK, DE, and more
- **Automatic timezone detection** from coordinates
- **Smooth transitions** using cosine interpolation
- **Sun-based scheduling** using sunrise/sunset times

## Options

| Option | Description |
|--------|-------------|
| `--day-temp` | Daytime temperature in Kelvin (default: 6500) |
| `--night-temp` | Nighttime temperature in Kelvin (default: 3400) |
| `--zipcode`, `-z` | Postal code for location lookup |
| `--country` | Country code for zipcode (default: US) |
| `--lat`, `--lon` | Latitude/longitude coordinates |
| `--timezone`, `-tz` | Timezone override |
| `--transition` | Transition duration in minutes (default: 60) |
| `--verbose`, `-v` | Enable debug logging |
| `--log-file` | Log to file |

## Requirements

- Python 3.11+
- Windows (for gamma adjustment)

## License

MIT
