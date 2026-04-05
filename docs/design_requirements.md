# Design Requirements

This document defines the currently supported, testable requirements for the project. Every requirement in this document is intended to be verifiable by automated tests.

## Product Requirements

- `FR-001` The system shall generate a fretboard solid and export it to a STEP file through a scripted process.
- `FR-002` The system shall write a sidecar JSON manifest next to each generated STEP file. The manifest shall include the resolved spec name, display units, internal units, and slot count.
- `FR-003` All in-memory geometric values shall use millimeters regardless of the preset display units.
- `FR-004` The minimum geometric inputs shall be validated: `scale_length`, `num_frets`, `num_strings`, `fingerboard_width_at_nut`, `fingerboard_width_at_12th_fret`, and `fingerboard_radius` must all be valid for generation.
- `FR-005` The authoritative built-in preset store shall be JSON with a top-level `version` field, a top-level `presets` list, and per-preset `id`, `name`, `units`, `geometry`, and `metadata` fields.
- `FR-006` Presets shall be selectable by either stable `id` or display `name`.
- `FR-007` Loading a preset for editing shall preload all current geometry fields, display units, and metadata into editable fields.
- `FR-008` Changing display units shall convert the displayed length fields while preserving the same modeled geometry.
- `FR-009` CLI dimensional overrides shall be interpreted in the units selected for that invocation. If override units are omitted, the preset's preferred display units shall be used.
- `FR-010` User presets shall be stored in a separate JSON file, shall preserve the selected display units when serialized, and shall appear in the same preset listing flow as built-in presets.
- `FR-011` Output location resolution shall prefer an explicit `--output` file path, then an explicit `--work-folder` path, then `FRETBOARD_WORK_FOLDER`, then the current working directory.
- `FR-012` The fretboard taper shall be derived from the nut width and the 12th-fret width, and the width at half scale length shall equal the specified 12th-fret width.
- `FR-013` The default board-length rule shall extend the board beyond the last fret by the configured CAD default end extension.
- `FR-014` Slot definitions shall include slot position, slot orientation, slot depth, and slot width for every fret.
- `FR-015` The CLI shall support listing presets, exporting a preset, importing a preset, saving a user preset, and generating output without requiring the graphical UI.
- `FR-016` If the Streamlit UI is provided, it shall separate preset selection and preset status from editable input controls using distinct visual sections.
- `FR-017` The UI shall group editable inputs into at least two sections: core geometry inputs and secondary metadata inputs.
- `FR-018` The core geometry section shall expose the minimum design-driving inputs without requiring the user to scan through metadata fields first.
- `FR-019` The UI shall present preset source and resolved work-folder information in a section that is visually separate from the editable form fields.
- `FR-020` The primary generation action in the UI shall remain visually associated with the core geometry inputs rather than being placed after all secondary metadata fields.
- `FR-021` If the UI exposes a units selector, changing that selector shall convert displayed numeric length fields rather than only changing labels.
- `FR-022` Selecting a preset in the UI shall preload all editable fields into the appropriate sections of the form.
- `FR-023` The UI shall allow the user to save the current parameter set as a user preset without mixing that action into the primary geometry-editing section.
- `FR-024` Musical scale utilities shall support equal-temperament scales and alternate explicit scale definitions for fret-position calculations.
- `FR-025` The application shall provide a centralized logging configuration that supports the standard Python `DEBUG`, `INFO`, `WARNING`, and `ERROR` levels through configuration inputs.
- `FR-026` The CLI shall export any built-in or user preset to a standalone JSON file representing a single guitar preset that can be edited outside the application.
- `FR-027` The CLI shall import a standalone preset JSON file into the user preset store, preserving its display units and making it available in subsequent preset listings and generation flows.
- `FR-028` Presets imported into the user preset store shall be selectable by name in subsequent CLI runs using the same lookup flow as built-in presets.
- `FR-029` The CLI preset listing command shall print all available preset names to the console, including both built-in and user presets.
- `FR-030` The CLI generate command shall accept an explicit output file path and filename for the generated STEP file. When provided, that path shall take precedence over work-folder-based output location.
- `FR-031` The system shall define a standalone JSON format for an individual preset export/import file, including the fields required to recreate a preset in the user preset store.
- `FR-032` Imported preset JSON files shall be validated for required preset fields and rejected with a clear error if invalid.

## Advisory Notes

These statements guide design decisions but are not treated as requirements for test coverage:

- Geometry and export correctness take priority over UI polish.
- Presets are convenience inputs rather than the architectural center of the system.
- Future inlay support remains a valid extension point, but it is not part of the current required scope.
- Manual CAD inspection is still useful for qualitative review, but it does not replace automated verification.
