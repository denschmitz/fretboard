# Architecture

The active architecture is centered on a package API that resolves validated preset data into geometric construction data, and later into CAD solids and STEP export.

Current layer order:

1. `fretboard.domain` loads and validates presets.
2. `fretboard.music` computes scale and fret positions.
3. `fretboard.geometry` derives outline, surface, and slot definitions.
4. `fretboard.cad` will own backend-specific solid generation and export.
5. `fretboard.ui` remains optional and must call package APIs instead of embedding geometry logic.
