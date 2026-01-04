"""Command-line interface for sundown."""

import argparse
import sys
import time

from sundown.gamma import (
    set_color_temperature,
    reset_gamma,
    TEMPERATURE_DAYLIGHT,
    TEMPERATURE_NIGHT,
    TEMPERATURE_SUNSET,
    TEMPERATURE_CANDLE,
)
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

    elif args.command == "run":
        print(f"Running automatic adjustment (day: {args.day_temp}K, night: {args.night_temp}K)")
        print("Press Ctrl+C to stop")

        scheduler = SundownScheduler(
            day_temp=args.day_temp,
            night_temp=args.night_temp,
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
