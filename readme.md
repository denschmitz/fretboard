# Fretboard

Fretboard is a parametric guitar fretboard generator focused on producing a scripted STEP export for manufacturing and CAD workflows.

The current project generates a real STEP model, writes output artifacts to a work folder, supports built-in and user presets, and exposes both a CLI workflow and a Streamlit UI.

## Current Capabilities

- Versioned JSON presets with built-in and user-defined entries
- Internal geometric calculations in millimeters with user-facing inch or millimeter display units
- Preset-driven parameter editing with save-as user preset support
- Scripted STEP generation through a `build123d` backend
- Sidecar JSON manifest written alongside each generated STEP file
- Streamlit UI for preset selection, parameter editing, unit switching, and generation
- CLI commands for listing presets, saving user presets, and generating output

## Project Structure

```text
docs/       Design and architecture documents
presets/    Built-in and user preset data
references/ Historical reference assets
src/        Application package
tests/      Behavioral and backend tests
scripts/    Small helper scripts
artifacts/  Generated output when using the default local launch setup
```

## Presets

Presets live in [presets.json](C:/Data/dev/fretboard/presets/presets.json). User presets are stored separately in `presets/user_presets.json` when saved through the app.

Each preset record contains:

- `id`
- `name`
- `units`
- `geometry`
- `metadata`

Preset `units` are treated as preferred display units. Internally, all geometry is converted to millimeters.

## Output

The generator writes:

- a `.step` file for the fretboard solid
- a `.fretboard.json` sidecar manifest with the resolved parameters and summary data

By default, output is written to the active work folder.

The work folder can be controlled by:

- CLI option: `--work-folder`
- environment variable: `FRETBOARD_WORK_FOLDER`
- current working directory when neither is provided

## CLI Usage

List presets:

```powershell
python -m fretboard.cli list-presets
```

Save a modified preset as a user preset:

```powershell
python -m fretboard.cli save-preset --preset gibson_les_paul --units mm --scale-length 635 --save-preset-name "Workshop LP"
```

Generate a STEP file into a work folder:

```powershell
python -m fretboard.cli generate --preset gibson_les_paul --work-folder artifacts
```

Generate with overrides:

```powershell
python -m fretboard.cli generate --preset gibson_les_paul --units mm --num-frets 24 --scale-length 635 --work-folder artifacts
```

## Streamlit UI

The current UI is implemented in [streamlit_app.py](C:/Data/dev/fretboard/src/fretboard/ui/streamlit_app.py).

The UI supports:

- selecting a preset from a dropdown
- preloading all editable parameters from the selected preset
- switching display units between inches and millimeters with numeric conversion
- editing any current geometry or metadata field
- saving the current values as a user preset
- generating a STEP file into the resolved work folder

## CAD Backend

The current STEP backend uses `build123d`.

The baseline modeling sequence is:

1. create an oversize rectangular blank
2. form the cylindrical fretboard crown on that blank
3. cut fret slots on the pre-trim body
4. trim the slotted blank to the final tapered outline
5. export the result to STEP

This matches the current design direction documented in [design_requirements.md](C:/Data/dev/fretboard/docs/design_requirements.md).

## Attribution

This project was originally informed by `fretfind.js` for fret-position calculation ideas and reference behavior. The current codebase, architecture, preset model, UI workflow, unit-handling system, and CAD generation pipeline are independently structured and substantially reworked.

The historical reference file is kept at [fretfind.js](C:/Data/dev/fretboard/references/fretfind.js).

## Development

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -p no:cacheprovider
```

VS Code launch configurations are provided for:

- CLI generation
- Streamlit UI
- test execution
