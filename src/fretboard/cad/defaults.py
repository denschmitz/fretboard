from dataclasses import dataclass


@dataclass(frozen=True)
class CadDefaults:
    fingerboard_thickness_mm: float = 6.35
    fret_slot_depth_mm: float = 1.8
    fret_slot_width_mm: float = 0.58
    end_extension_mm: float = 12.0
    rectangular_side_margin_mm: float = 2.0
    cylinder_length_margin_mm: float = 4.0
