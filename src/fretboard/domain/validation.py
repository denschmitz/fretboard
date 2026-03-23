from fretboard.errors import ValidationError
from fretboard.units import SUPPORTED_UNITS

from .models import FretboardGeometry, FretboardSpec



def validate_geometry(geometry: FretboardGeometry) -> None:
    if geometry.scale_length <= 0:
        raise ValidationError("scale_length must be greater than zero")
    if geometry.num_frets <= 0:
        raise ValidationError("num_frets must be greater than zero")
    if geometry.num_strings < 2:
        raise ValidationError("num_strings must be at least 2")
    if geometry.fingerboard_width_at_nut <= 0:
        raise ValidationError("fingerboard_width_at_nut must be greater than zero")
    if geometry.fingerboard_width_at_12th_fret <= 0:
        raise ValidationError("fingerboard_width_at_12th_fret must be greater than zero")
    if geometry.fingerboard_radius <= 0:
        raise ValidationError("fingerboard_radius must be greater than zero")



def validate_spec(spec: FretboardSpec) -> None:
    if spec.units not in SUPPORTED_UNITS:
        raise ValidationError(f"Unsupported units: {spec.units}")
    validate_geometry(spec.geometry)
