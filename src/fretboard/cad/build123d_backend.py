from pathlib import Path

from build123d import Align, Box, BuildSketch, Cylinder, Polygon, Pos, Rotation, export_step, extrude

from fretboard.cad.defaults import CadDefaults
from fretboard.cad.interface import CadBackend, ExportRequest
from fretboard.geometry.outline import width_at_distance
from fretboard.logging_utils import get_logger
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament


logger = get_logger(__name__)


def _board_length_mm(request: ExportRequest, defaults: CadDefaults) -> float:
    fret_positions = calculate_fret_positions(
        equal_temperament(), request.spec.geometry.scale_length, request.spec.geometry.num_frets
    )
    return fret_positions[-1] + defaults.end_extension_mm



def _final_width_mm(request: ExportRequest, board_length_mm: float) -> float:
    return width_at_distance(request.spec, board_length_mm)



def _rectangular_blank_width_mm(final_width_mm: float, defaults: CadDefaults, request: ExportRequest) -> float:
    return max(
        request.spec.geometry.fingerboard_width_at_nut,
        final_width_mm,
    ) + (2 * defaults.rectangular_side_margin_mm)



def _build_trim_prism(nut_width_mm: float, final_width_mm: float, board_length_mm: float, thickness_mm: float):
    with BuildSketch() as outline:
        Polygon(
            (-nut_width_mm / 2, 0),
            (nut_width_mm / 2, 0),
            (final_width_mm / 2, board_length_mm),
            (-final_width_mm / 2, board_length_mm),
        )
    return Pos(0, board_length_mm / 2, 0) * extrude(outline.sketch, amount=thickness_mm)



def build_fretboard_part(request: ExportRequest, defaults: CadDefaults | None = None):
    defaults = defaults or CadDefaults()
    board_length_mm = _board_length_mm(request, defaults)
    logger.debug("Building fretboard part for %s", request.spec.name)
    final_width_mm = _final_width_mm(request, board_length_mm)
    blank_width_mm = _rectangular_blank_width_mm(final_width_mm, defaults, request)
    thickness_mm = defaults.fingerboard_thickness_mm
    radius_mm = request.spec.geometry.fingerboard_radius

    blank = Box(
        blank_width_mm,
        board_length_mm,
        thickness_mm,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )

    cylinder = Pos(0, board_length_mm / 2, thickness_mm - radius_mm) * Cylinder(
        radius_mm,
        board_length_mm + defaults.cylinder_length_margin_mm,
        rotation=Rotation(90, 0, 0),
    )
    slotted_blank = blank & cylinder

    inner_radius_mm = radius_mm - defaults.fret_slot_depth_mm
    if inner_radius_mm <= 0:
        logger.error("Invalid slot depth %s for radius %s", defaults.fret_slot_depth_mm, radius_mm)
        raise ValueError("fret_slot_depth_mm must be smaller than the fingerboard radius")

    inner_cylinder = Pos(0, board_length_mm / 2, thickness_mm - radius_mm) * Cylinder(
        inner_radius_mm,
        board_length_mm + defaults.cylinder_length_margin_mm,
        rotation=Rotation(90, 0, 0),
    )
    slot_shell = cylinder - inner_cylinder

    fret_positions = calculate_fret_positions(
        equal_temperament(), request.spec.geometry.scale_length, request.spec.geometry.num_frets
    )
    for fret_number in range(1, request.spec.geometry.num_frets + 1):
        y_position_mm = fret_positions[fret_number]
        slot_band = Pos(0, y_position_mm, 0) * Box(
            blank_width_mm + 2.0,
            defaults.fret_slot_width_mm,
            thickness_mm,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        slot_cutter = slot_shell & slot_band
        slotted_blank = slotted_blank - slot_cutter

    trim_prism = _build_trim_prism(
        request.spec.geometry.fingerboard_width_at_nut,
        final_width_mm,
        board_length_mm,
        thickness_mm,
    )
    logger.debug("Built fretboard part length=%s width=%s thickness=%s", board_length_mm, final_width_mm, thickness_mm)
    return slotted_blank & trim_prism


class Build123dStepBackend(CadBackend):
    name = "build123d"

    def __init__(self, defaults: CadDefaults | None = None) -> None:
        self.defaults = defaults or CadDefaults()

    def export_step(self, request: ExportRequest) -> Path:
        logger.info("Exporting STEP with %s backend to %s", self.name, request.output_path)
        part = build_fretboard_part(request, self.defaults)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        export_step(part, request.output_path)
        logger.info("STEP export complete: %s", request.output_path)
        return request.output_path
