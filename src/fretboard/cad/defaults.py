from dataclasses import dataclass


@dataclass(frozen=True)
class CadDefaults:
    compatibility_fingerboard_thickness_mm: float = 6.35
    compatibility_fret_slot_depth_mm: float = 1.8
    compatibility_fret_slot_width_mm: float = 0.58
    compatibility_board_end_extension_mm: float = 12.0
    rectangular_side_margin_mm: float = 2.0
    cylinder_length_margin_mm: float = 4.0
    inlay_dot_diameter_mm: float = 6.0
    inlay_depth_mm: float = 5.0
    inlay_octave_pair_offset_ratio: float = 0.18

    @property
    def fingerboard_thickness_mm(self) -> float:
        return self.compatibility_fingerboard_thickness_mm

    @property
    def fret_slot_depth_mm(self) -> float:
        return self.compatibility_fret_slot_depth_mm

    @property
    def fret_slot_width_mm(self) -> float:
        return self.compatibility_fret_slot_width_mm

    @property
    def end_extension_mm(self) -> float:
        return self.compatibility_board_end_extension_mm
