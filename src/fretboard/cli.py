import argparse
import json
from pathlib import Path

from fretboard.app import (
    available_presets,
    build_design_summary,
    export_named_preset,
    generate_output,
    import_preset_file,
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
    parser.add_argument("--width-at-end", type=float, help="Override fingerboard width at end")
    parser.add_argument(
        "--width-at-12th-fret",
        type=float,
        help="Override fingerboard width at 12th fret",
    )
    parser.add_argument("--radius", type=float, help="Override fingerboard radius")
    parser.add_argument("--fingerboard-thickness", type=float, help="Override fingerboard thickness")
    parser.add_argument("--board-end-extension", type=float, help="Override board end extension")
    parser.add_argument("--edge-fillet", type=float, help="Override edge fillet")
    parser.add_argument("--wire-profile-id", help="Select fretwire profile id")
    parser.add_argument("--fit-profile-id", help="Select fit/process profile id")
    parser.add_argument("--slot-width", type=float, help="Override resolved slot width")
    parser.add_argument("--slot-depth", type=float, help="Override resolved slot depth")
    parser.add_argument("--tang-offset", type=float, help="Override tang offset")



def extract_overrides(args: argparse.Namespace) -> dict:
    return {
        "units": args.units,
        "scale_length": args.scale_length,
        "num_frets": args.num_frets,
        "num_strings": args.num_strings,
        "fingerboard_width_at_nut": args.width_at_nut,
        "fingerboard_width_at_end": args.width_at_end,
        "fingerboard_width_at_12th_fret": args.width_at_12th_fret,
        "fingerboard_radius": args.radius,
        "fingerboard_thickness": args.fingerboard_thickness,
        "board_end_extension": args.board_end_extension,
        "edge_fillet": args.edge_fillet,
        "wire_profile_id": args.wire_profile_id,
        "fit_profile_id": args.fit_profile_id,
        "slot_width": args.slot_width,
        "slot_depth": args.slot_depth,
        "tang_offset": args.tang_offset,
    }



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parametric fretboard generator")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-presets", help="List available presets")
    list_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")

    export_parser = subparsers.add_parser("export-preset", help="Export a preset to a standalone JSON file")
    export_parser.add_argument("--preset", required=True, help="Preset id or display name")
    export_parser.add_argument("--output", type=Path, required=True, help="Path to the exported preset JSON file")
    export_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")

    import_parser = subparsers.add_parser("import-preset", help="Import a standalone preset JSON file")
    import_parser.add_argument("--input", type=Path, required=True, help="Path to the preset JSON file to import")
    import_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")
    import_parser.add_argument("--overwrite", action="store_true", help="Overwrite matching user preset")

    save_parser = subparsers.add_parser("save-preset", help="Save a user preset")
    save_parser.add_argument("--preset", required=True, help="Preset id or display name")
    save_parser.add_argument("--save-preset-name", required=True, help="Name for the saved user preset")
    save_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")
    save_parser.add_argument("--overwrite", action="store_true", help="Overwrite matching user preset")
    add_override_arguments(save_parser)

    generate_parser = subparsers.add_parser("generate", help="Generate output from a preset")
    generate_parser.add_argument("--preset", required=True, help="Preset id or display name")
    generate_parser.add_argument("--user-presets", type=Path, help="Path to user presets JSON")
    generate_parser.add_argument("--output", type=Path, help="Explicit STEP output file path")
    generate_parser.add_argument("--work-folder", type=Path, help="Folder for generated artifacts")
    add_override_arguments(generate_parser)

    return parser



def _print_preset_list(user_path: Path | None) -> None:
    for preset in available_presets(user_path=user_path):
        print(preset.name)



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)
    logger.debug("CLI command: %s", args.command)

    if args.command == "list-presets":
        _print_preset_list(args.user_presets)
        return

    if args.command == "export-preset":
        output_path = export_named_preset(args.preset, args.output, user_path=args.user_presets)
        print(json.dumps({"exported_preset": args.preset, "output": str(output_path)}, indent=2))
        return

    if args.command == "import-preset":
        imported = import_preset_file(args.input, user_path=args.user_presets, overwrite=args.overwrite)
        print(json.dumps({"imported_preset": imported.name, "id": imported.id, "units": imported.units}, indent=2))
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

    work_folder = args.output.parent if args.output is not None else resolved_work_folder(args.work_folder)
    output_path = generate_output(spec, output_path=args.output, work_folder=work_folder)
    print(json.dumps({"output": str(output_path), "work_folder": str(work_folder), "summary": build_design_summary(spec)}, indent=2))


if __name__ == "__main__":
    main()
