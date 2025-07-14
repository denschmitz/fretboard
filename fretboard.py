import sys
import ctypes
import os
import subprocess

freecad_bin_path = r'C:\Program Files\FreeCAD 0.20\bin'
freecad_lib_path = r'C:\Program Files\FreeCAD 0.20\lib'

# Load the required DLLs
ctypes.CDLL(os.path.join(freecad_bin_path, 'FreeCADApp.dll'))
ctypes.CDLL(os.path.join(freecad_bin_path, 'FreeCADBase.dll'))

# Append the FreeCAD lib and bin paths to sys.path
sys.path.append(freecad_lib_path)
sys.path.append(freecad_bin_path)

# Now import FreeCAD and Part
import FreeCAD
import Part
import FreeCADGui

guitar_presets = {
    "Gibson Les Paul": {
        "scale_length": 24.75,
        "num_frets": 22,
        "num_strings": 6,
        "fingerboard_material": "Rosewood",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.695,
        "fingerboard_width_at_12th_fret": 2.260,
        "fingerboard_radius": 12,
        "nut_material": "Graph Tech",
        "inlay_material": "Acrylic",
        "inlay_style": "Trapezoid"
    },
    "Fender Stratocaster": {
        "scale_length": 25.5,
        "num_frets": 22,
        "num_strings": 6,
        "fingerboard_material": "Maple",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.685,
        "fingerboard_width_at_12th_fret": 2.165,
        "fingerboard_radius": 9.5,
        "nut_material": "Synthetic Bone",
        "inlay_material": "Acrylic",
        "inlay_style": "Dot"
    },
    "Fender Telecaster": {
        "scale_length": 25.5,
        "num_frets": 22,
        "num_strings": 6,
        "fingerboard_material": "Maple",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.650,
        "fingerboard_width_at_12th_fret": 2.200,
        "fingerboard_radius": 9.5,
        "nut_material": "Synthetic Bone",
        "inlay_material": "Acrylic",
        "inlay_style": "Dot"
    },
    "PRS Custom 24": {
        "scale_length": 25,
        "num_frets": 24,
        "num_strings": 6,
        "fingerboard_material": "Rosewood",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.650,
        "fingerboard_width_at_12th_fret": 2.245,
        "fingerboard_radius": 10,
        "nut_material": "Graph Tech",
        "inlay_material": "Abalone",
        "inlay_style": "Birds"
    },
    "Ibanez RG": {
        "scale_length": 25.5,
        "num_frets": 24,
        "num_strings": 6,
        "fingerboard_material": "Rosewood",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.692,
        "fingerboard_width_at_12th_fret": 2.283,
        "fingerboard_radius": 16,
        "nut_material": "Graph Tech",
        "inlay_material": "Acrylic",
        "inlay_style": "Dot"
    },
    "Gibson ES-335": {
        "scale_length": 24.75,
        "num_frets": 22,
        "num_strings": 6,
        "fingerboard_material": "Rosewood",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.6875,
        "fingerboard_width_at_12th_fret": 2.240,
        "fingerboard_radius": 12,
        "nut_material": "Bone",
        "inlay_material": "Acrylic",
        "inlay_style": "Dot"
    },
    "Rickenbacker 360": {
        "scale_length": 24.75,
        "num_frets": 24,
        "num_strings": 6,
        "fingerboard_material": "Rosewood",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.63,
        "fingerboard_width_at_12th_fret": 1.93,
        "fingerboard_radius": 10,
        "nut_material": "Bone",
        "inlay_material": "Acrylic",
        "inlay_style": "Triangle"
    },
    "Martin D-28": {
        "scale_length": 25.4,
        "num_frets": 20,
        "num_strings": 6,
        "fingerboard_material": "Ebony",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.750,
        "fingerboard_width_at_12th_fret": 2.125,
        "fingerboard_radius": 16,
        "nut_material": "Bone",
        "inlay_material": "Mother of Pearl",
        "inlay_style": "Dot"
    },
    "Gretsch White Falcon": {
        "scale_length": 25.5,
        "num_frets": 22,
        "num_strings": 6,
        "fingerboard_material": "Ebony",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.6875,
        "fingerboard_width_at_12th_fret": 2.218,
        "fingerboard_radius": 12,
        "nut_material": "Bone",
        "inlay_material": "Mother of Pearl",
        "inlay_style": "Neo-Classic Thumbnail"
    },
    "Taylor 814ce": {
        "scale_length": 25.5,
        "num_frets": 20,
        "num_strings": 6,
        "fingerboard_material": "Ebony",
        "fret_material": "Nickel Silver",
        "fingerboard_width_at_nut": 1.75,
        "fingerboard_width_at_12th_fret": 2.25,
        "fingerboard_radius": 15,
        "nut_material": "Tusq",
        "inlay_material": "Mother of Pearl",
        "inlay_style": "Element"
    }
}

class Fretboard:
    def __init__(self, preset=None, custom_params=None):
        self.params = guitar_presets.get("Gibson Les Paul").copy()

        if preset:
            if preset in guitar_presets:
                self.params.update(guitar_presets[preset])
            else:
                raise ValueError(f"Preset '{preset}' not found in the guitar presets.")

        if custom_params:
            self.params.update(custom_params)
        
        self._fret_positions = None

    """
    def __getattr__(self, attr): # possibly gratuitous access to the object params
    if attr in self.params:
        return self.params[attr]
    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr}'")
    """

    @property
    def fret_positions(self):
        if self._fret_positions is None:
            self._fret_positions = self.calculate_fret_positions()
        return self._fret_positions

    def calculate_fret_positions(self):
        positions = []
        for i in range(self.params['num_frets'] + 1):  # Assuming 24 frets + 1 for the nut (zero-fret)
            distance = self.params['scale_length'] * (1 - 2 ** (-i / 12))
            positions.append(distance)
        return positions

    def create_geometry(self):
        # Create a new FreeCAD document
        doc = FreeCAD.newDocument()

        # Create a sketch for the fretboard profile
        profile_sketch = doc.addObject("Sketcher::SketchObject", "FretboardProfile")

        # Add points and lines for the fretboard profile
        for i in range(len(self.fret_positions) - 1):
            profile_sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(self.fret_positions[i], 0, 0),
                                                        FreeCAD.Vector(self.fret_positions[i + 1], 0, 0)))
            profile_sketch.addConstraint(Sketcher.Constraint("Coincident", i, 1, i + 1, 0))

        # Create a sketch for the neck profile
        profile_points = self.get_neck_profile_points()
        neck_profile = doc.addObject("Sketcher::SketchObject", "NeckProfile")

        # Add neck profile points and constraints
        for i in range(len(profile_points) - 1):
            neck_profile.addGeometry(Part.LineSegment(profile_points[i], profile_points[i + 1]))
            neck_profile.addConstraint(Sketcher.Constraint("Coincident", i, 1, i + 1, 0))

        # Loft the neck profile along the fretboard profile
        loft = doc.addObject("Part::Loft", "Fretboard")
        loft.Sections = [profile_sketch, neck_profile]
        loft.Solid = True
        loft.Ruled = True

        # Compute the shape
        doc.recompute()

        # Create a cylindrical face radius for the fretboard
        cylinder = doc.addObject("Part::Cylinder", "FretboardRadius")
        cylinder.Radius = self.fretboard_radius
        cylinder.Height = self.total_length
        cylinder.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

        # Cut the loft with the cylinder to create the final fretboard shape
        fretboard = doc.addObject("Part::Cut", "FretboardCut")
        fretboard.Base = loft
        fretboard.Tool = cylinder

        # Compute the final shape
        doc.recompute()

        self.fretboard = fretboard
        return fretboard

    def cut_fretwire_channels(self):
        doc = FreeCAD.ActiveDocument

        # Define fretwire dimensions
        fretwire_width = 0.8  # Modify this value as needed
        fretwire_height = 1.5  # Modify this value as needed
        fretwire_depth = self.fretboard_radius * 2

        for i, fret_position in enumerate(self.fret_positions):
            # Create a fretwire sketch
            fretwire_sketch = doc.addObject("Sketcher::SketchObject", f"FretwireProfile{i}")

            # Draw a rectangle for the fretwire profile
            fretwire_sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-fretwire_width / 2, 0, 0), FreeCAD.Vector(fretwire_width / 2, 0, 0)))
            fretwire_sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(fretwire_width / 2, 0, 0), FreeCAD.Vector(fretwire_width / 2, fretwire_height, 0)))
            fretwire_sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(fretwire_width / 2, fretwire_height, 0), FreeCAD.Vector(-fretwire_width / 2, fretwire_height, 0)))
            fretwire_sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(-fretwire_width / 2, fretwire_height, 0), FreeCAD.Vector(-fretwire_width / 2, 0, 0)))

            # Create the fretwire extrusion
            fretwire = doc.addObject("Part::Extrusion", f"FretwireExtrusion{i}")
            fretwire.Base = fretwire_sketch
            fretwire.DirMode = "Normal"
            fretwire.LengthFwd = fretwire_depth
            fretwire.Solid = True

            # Position the fretwire
            fretwire.Placement = FreeCAD.Placement(FreeCAD.Vector(fret_position, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

            # Cut the fretwire from the fretboard
            fretboard_cut = doc.addObject("Part::Cut", f"FretboardCut{i}")
            fretboard_cut.Base = self.fretboard
            fretboard_cut.Tool = fretwire
            self.fretboard = fretboard_cut

            # Update the document
            doc.recompute()

        return self.fretboard

    def export_step(self, output_file_path):
        pass

fb = Fretboard()
print(fb.fret_positions)
fb.create_geometry()

