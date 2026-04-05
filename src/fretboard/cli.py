import argparse
import json
from pathlib import Path

from fretboard.app import (
    available_presets,
    build_design_summary,
    generate_output,
    resolve_spec,
    resolved_work_folder,
    save_named_user_preset,
)
from fretboard.logging_utils import configure_logging, get_logger


logger = get_logger(__name__)


def add_override_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--units", choices=["in", "mm"], help="Display/input units for overrides")
    parser.add_argument("--scale-length", type=float, help="Override scale length")
    parser.add_argument("--num-frets", type=int, help="Override fret count")
    parser.add_argument("--num-strings", type=int, help="Override string count")
    parser.add_argument("--width-at-nut", type=float, help="Override fingerboard width at nut")
    parser.add_argument(
        "--width-at-12th-fret",
        type=float,
        help="Override fingerboard width at 12th fret",
    )
    parser.add_argument("--radius", type=float, help="Override fingerboard radius")
    parser.add_argument("--name", help="Override the resolved fretboard name")



def extract_overrides(args: argparse.Namespace) -> dict:
    return {
        "units": args.units,
        "scale_length": args.scale_length,
        "num_frets": args.num_frets,
        "num_strings": args.num_strings,
        "fingerboard_width_at_nut": args.width_at_nut,
        "fingerboard_width_at_12th_fret": args.width_at_12th_fret,
        "fingerboard_radius": args.radius,
        "name": args.name,
    }



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parametric fretboard generator")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-presets", help="List available presets")
    list_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")

    save_parser = subparsers.add_parser("save-preset", help="Save a user preset")
    save_parser.add_argument("--preset", required=True, help="Preset id or display name")
    save_parser.add_argument("--save-preset-name", required=True, help="Name for the saved user preset")
    save_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")
    save_parser.add_argument("--overwrite", action="store_true", help="Overwrite matching user preset")
    add_override_arguments(save_parser)

    generate_parser = subparsers.add_parser("generate", help="Generate output from a preset")
    generate_parser.add_argument("--preset", required=True, help="Preset id or display name")
    generate_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")
    generate_parser.add_argument("--save-preset-name", help="Save resolved values as a new user preset before generation")
    generate_parser.add_argument("--overwrite", action="store_true", help="Overwrite matching user preset")
    generate_parser.add_argument("--output", type=Path, help="Explicit STEP output file path")
    generate_parser.add_argument("--work-folder", type=Path, help="Folder for generated artifacts")
    generate_parser.add_argument("--dry-run", action="store_true", help="Print resolved design data and skip file generation")
    add_override_arguments(generate_parser)

    return parser



def _print_preset_list(user_path: Path | None) -> None:
    for preset in available_presets(user_path=user_path):
        print(f"{preset.id}\t{preset.name}\t{preset.source}\tpreferred_display={preset.units}")



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)
    logger.debug("CLI command: %s", args.command)

    if args.command == "list-presets":
        _print_preset_list(args.user_presets)
        return

    overrides = extract_overrides(args)
    spec = resolve_spec(args.preset, overrides=overrides, user_path=args.user_presets)

    if args.command == "save-preset":
        saved = save_named_user_preset(
            spec,
            args.save_preset_name,
            user_path=args.user_presets,
            overwrite=args.overwrite,
        )
        print(json.dumps({"saved_preset": saved.name, "id": saved.id, "units": saved.units}, indent=2))
        return

    if args.save_preset_name:
        save_named_user_preset(
            spec,
            args.save_preset_name,
            user_path=args.user_presets,
            overwrite=args.overwrite,
        )
        spec = resolve_spec(args.save_preset_name, user_path=args.user_presets)

    summary = build_design_summary(spec)
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return

    work_folder = resolved_work_folder(args.work_folder)
    output_path = generate_output(spec, output_path=args.output, work_folder=work_folder)
    print(json.dumps({"output": str(output_path), "work_folder": str(work_folder), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
