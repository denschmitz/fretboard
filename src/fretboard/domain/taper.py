from fretboard.cad.defaults import CadDefaults
from fretboard.domain.models import FretboardGeometry
from fretboard.errors import ValidationError
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament


TAPER_TOLERANCE_MM = 1e-6


def board_length_mm(geometry: FretboardGeometry) -> float:
    fret_positions = calculate_fret_positions(equal_temperament(), geometry.scale_length, geometry.num_frets)
    return fret_positions[-1] + CadDefaults().end_extension_mm


def resolve_taper_widths(geometry: FretboardGeometry) -> tuple[float, float]:
    nut_width = geometry.fingerboard_width_at_nut
    twelfth_width = geometry.fingerboard_width_at_12th_fret
    end_width = geometry.fingerboard_width_at_end

    if nut_width <= 0:
        raise ValidationError("fingerboard_width_at_nut must be greater than zero")
    if twelfth_width is not None and twelfth_width <= 0:
        raise ValidationError("fingerboard_width_at_12th_fret must be greater than zero")
    if end_width is not None and end_width <= 0:
        raise ValidationError("fingerboard_width_at_end must be greater than zero")
    if twelfth_width is None and end_width is None:
        raise ValidationError("Either fingerboard_width_at_12th_fret or fingerboard_width_at_end must be provided")

    half_scale = geometry.scale_length / 2
    board_length = board_length_mm(geometry)

    if half_scale <= 0:
        raise ValidationError("scale_length must be greater than zero")
    if board_length <= 0:
        raise ValidationError("Resolved board length must be greater than zero")

    if twelfth_width is None:
        twelfth_width = nut_width + ((end_width - nut_width) * (half_scale / board_length))
    if end_width is None:
        end_width = nut_width + ((twelfth_width - nut_width) * (board_length / half_scale))

    expected_end_width = nut_width + ((twelfth_width - nut_width) * (board_length / half_scale))
    if abs(expected_end_width - end_width) > TAPER_TOLERANCE_MM:
        raise ValidationError(
            "fingerboard_width_at_12th_fret and fingerboard_width_at_end do not define the same linear taper"
        )

    return twelfth_width, end_width
