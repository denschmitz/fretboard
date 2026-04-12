from fretboard.cad.defaults import CadDefaults
from fretboard.errors import ValidationError

from .models import FitProfile, FretboardSpec, ResolvedSlotting, SlottingParameters, WireProfile


COMPATIBILITY_WIRE_PROFILE_ID = "legacy_medium"
COMPATIBILITY_FIT_PROFILE_ID = "legacy_default"


def default_wire_profiles() -> list[WireProfile]:
    return [
        WireProfile(
            id=COMPATIBILITY_WIRE_PROFILE_ID,
            name="Legacy Medium Fretwire",
            tang_width=0.58,
            tang_depth=1.8,
            crown_width=2.4,
            crown_height=1.1,
            notes="Compatibility profile matching the historical slot-width default.",
        )
    ]


def default_fit_profiles() -> list[FitProfile]:
    return [
        FitProfile(
            id=COMPATIBILITY_FIT_PROFILE_ID,
            name="Legacy Default Fit",
            slot_width_delta_from_tang=0.0,
            slot_depth_delta_from_tang=0.0,
            tang_measurement_basis="compatibility",
            slot_cut_method="saw",
            fret_installation_method="press",
            tang_style="straight",
            notes="Compatibility profile matching the historical slot-depth default.",
        )
    ]


def _profile_index(items):
    return {item.id: item for item in items}


def resolve_slotting(
    spec: FretboardSpec,
    *,
    wire_profiles: list[WireProfile] | None = None,
    fit_profiles: list[FitProfile] | None = None,
) -> ResolvedSlotting:
    if wire_profiles is None or fit_profiles is None:
        try:
            from .presets import load_profile_store

            resolved_wire_profiles, resolved_fit_profiles = load_profile_store()
            wire_profiles = wire_profiles or resolved_wire_profiles
            fit_profiles = fit_profiles or resolved_fit_profiles
        except Exception:
            wire_profiles = wire_profiles or default_wire_profiles()
            fit_profiles = fit_profiles or default_fit_profiles()
    wire_by_id = _profile_index(wire_profiles)
    fit_by_id = _profile_index(fit_profiles)
    slotting = spec.slotting

    wire_profile = None
    fit_profile = None
    width_source = "override" if slotting.slot_width is not None else "profile"
    depth_source = "override" if slotting.slot_depth is not None else "profile"
    tang_offset_source = "override" if slotting.tang_offset is not None else "default"

    if slotting.wire_profile_id is not None:
        wire_profile = wire_by_id.get(slotting.wire_profile_id)
        if wire_profile is None:
            raise ValidationError(f"Unknown wire profile: {slotting.wire_profile_id}")

    if slotting.fit_profile_id is not None:
        fit_profile = fit_by_id.get(slotting.fit_profile_id)
        if fit_profile is None:
            raise ValidationError(f"Unknown fit profile: {slotting.fit_profile_id}")

    resolved_slot_width = slotting.slot_width
    resolved_slot_depth = slotting.slot_depth
    resolved_tang_offset = slotting.tang_offset

    if resolved_slot_width is None or resolved_slot_depth is None:
        if wire_profile is not None and fit_profile is not None:
            if resolved_slot_width is None:
                resolved_slot_width = wire_profile.tang_width + fit_profile.slot_width_delta_from_tang
            if resolved_slot_depth is None:
                resolved_slot_depth = wire_profile.tang_depth + fit_profile.slot_depth_delta_from_tang
        else:
            defaults = CadDefaults()
            compatibility_allowed = (
                slotting.wire_profile_id in {None, COMPATIBILITY_WIRE_PROFILE_ID}
                and slotting.fit_profile_id in {None, COMPATIBILITY_FIT_PROFILE_ID}
            )
            if not compatibility_allowed:
                raise ValidationError("Slotting is under-specified; select both wire and fit profiles or provide explicit overrides")
            if resolved_slot_width is None:
                resolved_slot_width = defaults.compatibility_fret_slot_width_mm
                width_source = "compatibility_default"
            if resolved_slot_depth is None:
                resolved_slot_depth = defaults.compatibility_fret_slot_depth_mm
                depth_source = "compatibility_default"
            if slotting.wire_profile_id is None:
                wire_profile = wire_by_id.get(COMPATIBILITY_WIRE_PROFILE_ID)
            if slotting.fit_profile_id is None:
                fit_profile = fit_by_id.get(COMPATIBILITY_FIT_PROFILE_ID)

    if resolved_tang_offset is None:
        resolved_tang_offset = 0.0

    if resolved_slot_width is None or resolved_slot_width <= 0:
        raise ValidationError("Resolved slot_width must be greater than zero")
    if resolved_slot_depth is None or resolved_slot_depth <= 0:
        raise ValidationError("Resolved slot_depth must be greater than zero")
    if resolved_tang_offset < 0:
        raise ValidationError("Resolved tang_offset must be greater than or equal to zero")

    return ResolvedSlotting(
        wire_profile_id=wire_profile.id if wire_profile is not None else slotting.wire_profile_id,
        fit_profile_id=fit_profile.id if fit_profile is not None else slotting.fit_profile_id,
        resolved_slot_width=resolved_slot_width,
        resolved_slot_depth=resolved_slot_depth,
        resolved_tang_offset=resolved_tang_offset,
        slot_width_source=width_source,
        slot_depth_source=depth_source,
        tang_offset_source=tang_offset_source,
        wire_profile=wire_profile,
        fit_profile=fit_profile,
    )


def validate_slotting(
    slotting: SlottingParameters,
    *,
    wire_profiles: list[WireProfile] | None = None,
    fit_profiles: list[FitProfile] | None = None,
) -> None:
    if slotting.slot_width is not None and slotting.slot_width <= 0:
        raise ValidationError("slot_width must be greater than zero")
    if slotting.slot_depth is not None and slotting.slot_depth <= 0:
        raise ValidationError("slot_depth must be greater than zero")
    if slotting.tang_offset is not None and slotting.tang_offset < 0:
        raise ValidationError("tang_offset must be greater than or equal to zero")

    has_partial_profile_selection = (slotting.wire_profile_id is None) != (slotting.fit_profile_id is None)
    has_explicit_override_pair = slotting.slot_width is not None and slotting.slot_depth is not None

    if has_partial_profile_selection and not has_explicit_override_pair:
        raise ValidationError("Slotting requires both wire_profile_id and fit_profile_id unless explicit slot width and slot depth are provided")

    resolve_slotting(
        FretboardSpec(
            id=None,
            name="validation",
            units="mm",
            geometry=spec_stub_geometry(),
            construction=spec_stub_construction(),
            slotting=slotting,
        ),
        wire_profiles=wire_profiles,
        fit_profiles=fit_profiles,
    )


def spec_stub_geometry():
    from .models import FretboardGeometry

    return FretboardGeometry(
        scale_length=1.0,
        num_frets=1,
        num_strings=2,
        fingerboard_width_at_nut=1.0,
        fingerboard_width_at_12th_fret=1.0,
        fingerboard_radius=1.0,
    )


def spec_stub_construction():
    from .models import ConstructionParameters

    return ConstructionParameters()
