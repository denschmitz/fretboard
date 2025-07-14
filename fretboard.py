"""Utilities for calculating guitar fret positions and optionally generating
FreeCAD geometry for a fretboard.

The :class:`Fretboard` class stores parameters such as scale length and number
of frets. It can calculate fret positions without requiring FreeCAD. Geometry
functions only work when FreeCAD is installed.
"""
from __future__ import annotations

from typing import Dict, List, Optional

try:
    import FreeCAD  # type: ignore
    import Part  # type: ignore
    import FreeCADGui  # type: ignore
    import Sketcher  # type: ignore
    FREECAD_AVAILABLE = True
except Exception:  # pragma: no cover - FreeCAD is optional
    FREECAD_AVAILABLE = False

# Preset data for several common guitars
GUITAR_PRESETS: Dict[str, Dict[str, float]] = {
    "Gibson Les Paul": {
        "scale_length": 24.75,
        "num_frets": 22,
        "fingerboard_radius": 12.0,
    },
    "Fender Stratocaster": {
        "scale_length": 25.5,
        "num_frets": 22,
        "fingerboard_radius": 9.5,
    },
    "PRS Custom 24": {
        "scale_length": 25.0,
        "num_frets": 24,
        "fingerboard_radius": 10.0,
    },
}


class Fretboard:
    """Representation of a guitar fretboard."""

    def __init__(
        self,
        preset: Optional[str] = None,
        custom_params: Optional[Dict[str, float]] = None,
    ) -> None:
        """Create a new fretboard instance.

        Parameters
        ----------
        preset:
            Name of a preset from :data:`GUITAR_PRESETS` to initialise
            the fretboard. If omitted the ``Gibson Les Paul`` preset is used.
        custom_params:
            Mapping of parameter names to override the preset defaults.
        """
        self.params: Dict[str, float] = GUITAR_PRESETS["Gibson Les Paul"].copy()
        if preset:
            try:
                self.params.update(GUITAR_PRESETS[preset])
            except KeyError as exc:
                raise ValueError(f"Preset '{preset}' not found") from exc
        if custom_params:
            self.params.update(custom_params)
        self._fret_positions: Optional[List[float]] = None

    def __getattr__(self, attr: str) -> float:
        """Access parameters as attributes."""
        if attr in self.params:
            return self.params[attr]
        raise AttributeError(attr)

    @property
    def fret_positions(self) -> List[float]:
        """Fret locations in inches measured from the nut."""
        if self._fret_positions is None:
            self._fret_positions = self.calculate_fret_positions()
        return self._fret_positions

    def calculate_fret_positions(self) -> List[float]:
        """Calculate fret positions using the 12-tone equal temperament rule."""
        positions: List[float] = []
        for i in range(self.num_frets + 1):  # include open string
            distance = self.scale_length * (1 - 2 ** (-i / 12))
            positions.append(distance)
        return positions

    # ------------------------------------------------------------------
    # Geometry helpers (optional)
    # ------------------------------------------------------------------
    def create_geometry(self) -> None:
        """Create a simple FreeCAD model of the fretboard."""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for geometry operations")
        doc = FreeCAD.newDocument()
        self.fretboard = doc.addObject("Part::Box", "Fretboard")
        self.fretboard.Length = self.scale_length
        self.fretboard.Width = 2.0  # arbitrary width
        self.fretboard.Height = 0.25  # arbitrary thickness
        doc.recompute()

    def export_step(self, output_file_path: str) -> None:
        """Export the generated geometry to a STEP file."""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for geometry operations")
        if not hasattr(self, "fretboard"):
            self.create_geometry()
        Part.export([self.fretboard], output_file_path)


if __name__ == "__main__":
    fb = Fretboard()
    for i, pos in enumerate(fb.fret_positions):
        print(f"Fret {i:2d}: {pos:.3f} in")
