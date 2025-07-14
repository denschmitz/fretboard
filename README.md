# Fretboard

This repository provides a small Python module for calculating guitar fret
positions.  It optionally integrates with [FreeCAD](https://www.freecad.org)
to generate a simple 3D representation of a fretboard.

## Features

- Predefined presets for a few popular guitar models.
- Calculate fret locations using the 12‑tone equal temperament rule.
- Optional helper methods for exporting a STEP model via FreeCAD.

## Requirements

- Python 3.8 or later
- FreeCAD (optional, required for geometry/export functions)

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python fretboard.py
```

The script prints the fret positions for the default preset.  When FreeCAD is
available you can also create geometry and export it as a STEP file:

```python
from fretboard import Fretboard

fb = Fretboard("PRS Custom 24")
fb.create_geometry()
fb.export_step("fretboard.step")
```

## License

This project is released under the MIT License.
