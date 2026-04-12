from fretboard.cad.defaults import CadDefaults
from fretboard.errors import ValidationError
from fretboard.units import SUPPORTED_UNITS

from .models import ConstructionParameters, FitProfile, FretboardGeometry, FretboardSpec, SlottingParameters, WireProfile
from .slotting import validate_slotting
from .taper import resolve_taper_widths


def validate_geometry(geometry: FretboardGeometry) -> None:
    if geometry.scale_length <= 0:
        raise ValidationError("scale_length must be greater than zero")
    if geometry.num_frets <= 0:
        raise ValidationError("num_frets must be greater than zero")
    if geometry.num_strings < 2:
        raise ValidationError("num_strings must be at least 2")
    if geometry.fingerboard_width_at_nut <= 0:
        raise ValidationError("fingerboard_width_at_nut must be greater than zero")
    if geometry.fingerboard_width_at_12th_fret is not None and geometry.fingerboard_width_at_12th_fret <= 0:
        raise ValidationError("fingerboard_width_at_12th_fret must be greater than zero")
    if geometry.fingerboard_width_at_end is not None and geometry.fingerboard_width_at_end <= 0:
        raise ValidationError("fingerboard_width_at_end must be greater than zero")
    if geometry.fingerboard_radius <= 0:
        raise ValidationError("fingerboard_radius must be greater than zero")
    if geometry.fingerboard_radius_end is not None and geometry.fingerboard_radius_end <= 0:
        raise ValidationError("fingerboard_radius_end must be greater than zero")
    if geometry.fingerboard_thickness_at_nut is not None and geometry.fingerboard_thickness_at_nut <= 0:
        raise ValidationError("fingerboard_thickness_at_nut must be greater than zero")
    if geometry.fingerboard_thickness_at_end is not None and geometry.fingerboard_thickness_at_end <= 0:
        raise ValidationError("fingerboard_thickness_at_end must be greater than zero")
    resolve_taper_widths(geometry)


def validate_construction(construction: ConstructionParameters) -> None:
    defaults = CadDefaults()
    if construction.fingerboard_thickness is not None and construction.fingerboard_thickness <= 0:
        raise ValidationError("fingerboard_thickness must be greater than zero")
    if construction.board_end_extension is not None and construction.board_end_extension < 0:
        raise ValidationError("board_end_extension must be greater than or equal to zero")
    if construction.edge_fillet is not None and construction.edge_fillet < 0:
        raise ValidationError("edge_fillet must be greater than or equal to zero")
    thickness = construction.fingerboard_thickness
    if thickness is not None and thickness > defaults.compatibility_fingerboard_thickness_mm * 10:
        raise ValidationError("fingerboard_thickness is not a plausible fretboard thickness")


def validate_profiles(
    wire_profiles: list[WireProfile] | None = None,
    fit_profiles: list[FitProfile] | None = None,
) -> None:
    for wire in wire_profiles or []:
        if wire.tang_width <= 0:
            raise ValidationError(f"Wire profile {wire.id} tang_width must be greater than zero")
        if wire.tang_depth <= 0:
            raise ValidationError(f"Wire profile {wire.id} tang_depth must be greater than zero")
    for fit in fit_profiles or []:
        if fit.slot_width_delta_from_tang <= -10:
            raise ValidationError(f"Fit profile {fit.id} slot_width_delta_from_tang is not plausible")
        if fit.slot_depth_delta_from_tang <= -10:
            raise ValidationError(f"Fit profile {fit.id} slot_depth_delta_from_tang is not plausible")


def validate_spec(
    spec: FretboardSpec,
    *,
    wire_profiles: list[WireProfile] | None = None,
    fit_profiles: list[FitProfile] | None = None,
) -> None:
    if spec.units not in SUPPORTED_UNITS:
        raise ValidationError(f"Unsupported units: {spec.units}")
    validate_profiles(wire_profiles, fit_profiles)
    validate_geometry(spec.geometry)
    validate_construction(spec.construction)
    validate_slotting(spec.slotting, wire_profiles=wire_profiles, fit_profiles=fit_profiles)
