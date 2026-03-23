# Fretboard

This project is a parametric fretboard generator whose primary deliverable is a scripted STEP export path.

The current codebase preserves:

- hand-editable guitar presets
- fret spacing math
- geometric construction data needed for a solid-model pipeline

The current codebase does not yet provide a finished STEP backend. That work is intentionally isolated behind the CAD layer so it can be implemented without reworking presets, validation, or the application interface.

## Structure

```text
docs/       Design and architecture documents
presets/    Versioned preset data
references/ Legacy/reference assets
src/        Application package
tests/      Behavioral tests
scripts/    Small helper scripts
```

## Presets

Presets live in `presets/presets.json` and are stored as versioned records with:

- `id`
- `name`
- `units`
- `geometry`
- `metadata`

This format is intended to stay simple enough for hand editing while being strict enough to validate.

## UI Direction

The legacy Tkinter GUI has been retired from the active architecture. If a UI is developed, Streamlit is the current default direction because it is easier to iterate on while the CAD pipeline is still changing.

## Reference

The original JavaScript fret calculation reference is kept at `references/fretfind.js`.
