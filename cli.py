import argparse
import json
from fretboard import Fretboard

def load_presets(filepath="presets.json"):
    with open(filepath) as f:
        return json.load(f)

def run_cli():
    presets = load_presets()

    parser = argparse.ArgumentParser(description="Guitar Fretboard Generator")
    parser.add_argument("--preset", required=True, help="Guitar preset name (e.g. 'Gibson Les Paul')")
    parser.add_argument("--output", required=True, help="Output STEP file path")
    parser.add_argument("--frets", type=int, help="Override fret count")
    parser.add_argument("--scale", type=float, help="Override scale length")
    parser.add_argument("--dry-run", action="store_true", help="Print params and exit")

    args = parser.parse_args()

    if args.preset not in presets:
        print(f"Preset '{args.preset}' not found.")
        print("Available presets:", ", ".join(presets.keys()))
        return

    overrides = {}
    if args.frets:
        overrides["num_frets"] = args.frets
    if args.scale:
        overrides["scale_length"] = args.scale

    params = presets[args.preset].copy()
    params.update(overrides)

    if args.dry_run:
        from pprint import pprint
        pprint(params)
        return

    fretboard = Fretboard.from_preset(args.preset, overrides=overrides)
    fretboard.summary()
    print("(STEP export not implemented in this simplified example.)")
