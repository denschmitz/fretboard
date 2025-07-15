from fretfind import Point, Segment, Scale, calculate_fret_positions
import json
import os

# Load presets at import so other modules can easily reference them
PRESETS_PATH = os.path.join(os.path.dirname(__file__), "presets.json")
try:
    with open(PRESETS_PATH, "r") as f:
        GUITAR_PRESETS = json.load(f)
except FileNotFoundError:
    GUITAR_PRESETS = {}

class Fretboard:
    """Simple representation of a guitar fretboard."""

    @classmethod
    def from_preset(cls, preset_name: str, overrides: dict | None = None):
        """Create a ``Fretboard`` from a named preset in ``GUITAR_PRESETS``.

        Parameters
        ----------
        preset_name : str
            Key in ``GUITAR_PRESETS``.
        overrides : dict | None
            Optional parameter overrides such as ``scale_length`` or ``num_frets``.
        """
        if preset_name not in GUITAR_PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")

        params = GUITAR_PRESETS[preset_name].copy()
        if overrides:
            params.update(overrides)

        # Map JSON keys to constructor arguments
        mapped = {
            "scale_length": params.get("scale_length"),
            "num_frets": params.get("num_frets"),
            "num_strings": params.get("num_strings", 6),
            "nut_width": params.get("fingerboard_width_at_nut"),
            "twelfth_fret_width": params.get("fingerboard_width_at_12th_fret"),
        }
        return cls(**mapped)

    def __init__(self,
                 scale_length: float,
                 num_frets: int,
                 num_strings: int,
                 nut_width: float,
                 twelfth_fret_width: float,
                 scale: Scale = None):
        
        self.scale_length = scale_length
        self.num_frets = num_frets
        self.num_strings = num_strings
        self.nut_width = nut_width
        self.twelfth_fret_width = twelfth_fret_width
        self.scale = scale or self.default_scale()

        self.nut_line = self._create_nut_line()
        self.bridge_line = self._create_bridge_line()
        self.strings = self._create_strings()
        self.frets = self._calculate_frets()

    def default_scale(self):
        scale = Scale()
        scale.from_equal_temperament(12)
        return scale

    def _create_nut_line(self):
        y = 0
        return Segment(
            Point(0, y),
            Point(self.nut_width, y)
        )

    def _create_bridge_line(self):
        y = self.scale_length
        return Segment(
            Point(0, y),
            Point(self.twelfth_fret_width, y)  # Approximates symmetry for now
        )

    def _create_strings(self):
        strings = []
        for i in range(self.num_strings):
            x_nut = self.nut_width * (i / (self.num_strings - 1))
            x_bridge = self.twelfth_fret_width * (i / (self.num_strings - 1))
            string = Segment(
                Point(x_nut, 0),
                Point(x_bridge, self.scale_length)
            )
            strings.append(string)
        return strings

    def _calculate_frets(self):
        """Generate fret segments per fret across all strings."""
        fret_positions = [
            calculate_fret_positions(self.scale, self.scale_length, self.num_frets)
            for _ in range(self.num_strings)
        ]
        frets = []

        for fret_idx in range(self.num_frets + 1):
            fret_points = []
            for string_idx, string in enumerate(self.strings):
                pos = fret_positions[string_idx][fret_idx]
                point = string.point_at_ratio(pos / self.scale_length)
                fret_points.append(point)

            # Join adjacent fret points into fret segments
            fret_segments = [
                Segment(fret_points[i], fret_points[i + 1])
                for i in range(len(fret_points) - 1)
            ]
            frets.append(fret_segments)

        return frets

    def summary(self):
        print("Fretboard geometry:")
        print(f"  Scale length: {self.scale_length}")
        print(f"  Frets: {self.num_frets}")
        print(f"  Strings: {self.num_strings}")
        print(f"  Nut width: {self.nut_width}")
        print(f"  12th fret width: {self.twelfth_fret_width}")
        print("\nNut:", self.nut_line)
        print("Bridge:", self.bridge_line)
        print("\nStrings:")
        for idx, string in enumerate(self.strings):
            print(f"  {idx + 1}: {string}")
        print("\nFirst 5 frets:")
        for i, fret_group in enumerate(self.frets[:5]):
            print(f"Fret {i}:")
            for seg in fret_group:
                print(f"  {seg}")

# Example usage
if __name__ == "__main__":
    fretboard = Fretboard(
        scale_length=25.5,
        num_frets=22,
        num_strings=6,
        nut_width=1.6875,
        twelfth_fret_width=2.218
    )
    fretboard.summary()
