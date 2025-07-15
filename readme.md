# Fretboard Generator

This project is a **parametric guitar fretboard generator** written in Python. It calculates fret positions based on musical scales and outputs geometry for use in CAD systems like **FreeCAD** or for further export as **STEP**, **SVG**, or **DXF**.

---

## 📐 Features

- Support for multiple guitar models (via `presets.json`)
- Presets are loaded automatically at startup
- Accurate fret placement based on scale length and tuning
- Parametric control over fret count, string count, nut/bridge widths
- CLI and GUI interfaces
- Designed for CAD export (STEP, SVG, DXF planned)
- Easily extendable for multi-scale/fanned frets

---

## 🗂️ Project Structure

fretboard-generator/
├── guitartool.py # Entrypoint: dispatches CLI or GUI
├── cli.py # Command-line interface
├── gui.py # Basic Tkinter GUI
├── fretboard.py # Main geometry engine (fretboard builder)
├── fretfind.py # Fret position calculator (adapted from JS)
├── presets.json # Guitar model presets
├── README.md # This file
└── fretfind.js # [Reference] Original JavaScript algorithm


---

## 🚀 Usage

### Command Line

```bash
python guitartool.py --preset "Ibanez RG" --output ibanez.step

Options:

    --preset — Name of a model in presets.json

    --output — Filepath for STEP file

    --frets — Override number of frets

    --scale — Override scale length

    --dry-run — Print settings but do not generate file

GUI

python guitartool.py --gui

Allows selecting preset, modifying scale or frets, and saving output via a dialog.

Reference Code: fretfind.js

This project was originally inspired by Aaron C. Spike’s FretFind2D JavaScript code and fretfind.js is included in this repository for reference only. The Python implementation closely follows the mathematical logic of the original, while being structured for CAD and manufacturing use cases.

If you’re studying how fret positions are calculated or looking to validate the math, fretfind.js is a good source of truth.

## 🔧 Customizing Presets

To add or modify guitar models:

    Open presets.json

    Add new entries using the same structure:
    
{
  "Custom Model": {
    "scale_length": 25.0,
    "num_frets": 22,
    "num_strings": 6,
    "nut_material": "Bone",
    ...
  }
}
New fields added in code will fall back to Python defaults if missing from the preset.

``Fretboard`` loads ``presets.json`` on start, so any changes to this file are immediately available to both the CLI and GUI tools.
