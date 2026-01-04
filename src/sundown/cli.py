"""Command-line interface for sundown."""

import argparse
import sys
import time

from astral import LocationInfo

from sundown.gamma import (
    set_color_temperature,
    reset_gamma,
    get_active_displays,
    TEMPERATURE_DAYLIGHT,
    TEMPERATURE_NIGHT,
    TEMPERATURE_SUNSET,
    TEMPERATURE_CANDLE,
)
from sundown.location import from_zipcode, from_coordinates
from sundown.scheduler import SundownScheduler


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="sundown",
        description="Adjust screen color temperature",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set color temperature")
    set_parser.add_argument(
        "temperature",
        type=int,
        nargs="?",
        default=None,
        help="Temperature in Kelvin (1000-10000)",
    )
    set_parser.add_argument(
        "--preset",
        choices=["day", "night", "sunset", "candle"],
        help="Use a preset temperature",
    )

    # Reset command
    subparsers.add_parser("reset", help="Reset to default (6500K)")

    # Displays command
    subparsers.add_parser("displays", help="List active displays")

    # Run command (scheduler)
    run_parser = subparsers.add_parser("run", help="Run automatic adjustment")
    run_parser.add_argument(
        "--day-temp",
        type=int,
        default=6500,
        help="Daytime temperature (default: 6500K)",
    )
    run_parser.add_argument(
        "--night-temp",
        type=int,
        default=3400,
        help="Nighttime temperature (default: 3400K)",
    )
    run_parser.add_argument(
        "--lat",
        type=float,
        help="Latitude for sun-based transitions",
    )
    run_parser.add_argument(
        "--lon",
        type=float,
        help="Longitude for sun-based transitions",
    )
    run_parser.add_argument(
        "--zipcode", "-z",
        type=str,
        help="Postal/zip code for location lookup (e.g., 10001)",
    )
    run_parser.add_argument(
        "--country",
        type=str,
        default="US",
        help="Country code for zipcode lookup (default: US)",
    )
    run_parser.add_argument(
        "--timezone", "-tz",
        type=str,
        help="Timezone override (e.g., America/New_York)",
    )
    run_parser.add_argument(
        "--transition",
        type=float,
        default=60.0,
        help="Transition duration in minutes (default: 60)",
    )

    args = parser.parse_args()

    if args.command == "set":
        if args.preset:
            presets = {
                "day": TEMPERATURE_DAYLIGHT,
                "night": TEMPERATURE_NIGHT,
                "sunset": TEMPERATURE_SUNSET,
                "candle": TEMPERATURE_CANDLE,
            }
            temp = presets[args.preset]
        elif args.temperature:
            temp = args.temperature
        else:
            parser.error("Must specify temperature or --preset")
            return 1

        if set_color_temperature(temp):
            print(f"Set color temperature to {temp}K")
            return 0
        else:
            print("Failed to set color temperature", file=sys.stderr)
            return 1

    elif args.command == "reset":
        if reset_gamma():
            print("Reset to 6500K")
            return 0
        else:
            print("Failed to reset", file=sys.stderr)
            return 1

    elif args.command == "displays":
        displays = get_active_displays()
        if displays:
            print(f"Found {len(displays)} active display(s):")
            for i, d in enumerate(displays, 1):
                print(f"  {i}. {d}")
        else:
            print("No displays found (or not on Windows)")
        return 0

    elif args.command == "run":
        # Build location from zipcode, coordinates, or none
        location = None
        loc_info = None

        if args.zipcode:
            loc_info = from_zipcode(args.zipcode, args.country)
            if loc_info is None:
                print(f"Could not find location for zipcode: {args.zipcode}", file=sys.stderr)
                return 1
            print(f"Location: {loc_info.name}")
        elif args.lat is not None and args.lon is not None:
            loc_info = from_coordinates(args.lat, args.lon)

        if loc_info:
            # Use timezone override if provided, otherwise use detected
            tz = args.timezone or loc_info.timezone
            location = LocationInfo(
                name=loc_info.name,
                region="",
                timezone=tz,
                latitude=loc_info.latitude,
                longitude=loc_info.longitude,
            )
            print(f"Coordinates: {loc_info.latitude:.4f}, {loc_info.longitude:.4f}")
            if tz:
                print(f"Timezone: {tz}")

        displays = get_active_displays()
        print(f"Displays: {len(displays)}")
        print(f"Day: {args.day_temp}K, Night: {args.night_temp}K, Transition: {args.transition}min")
        print("Press Ctrl+C to stop")

        scheduler = SundownScheduler(
            day_temp=args.day_temp,
            night_temp=args.night_temp,
            location=location,
            transition_minutes=args.transition,
        )
        scheduler.on_change(lambda t: print(f"Temperature: {t}K"))

        try:
            with scheduler:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            reset_gamma()

        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
