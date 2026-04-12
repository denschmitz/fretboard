from fretboard.domain.models import FretboardSpec
from fretboard.domain.construction import resolve_construction
from fretboard.domain.presets import load_profile_store
from fretboard.domain.slotting import resolve_slotting
from fretboard.domain.taper import resolve_taper_widths
from fretboard.geometry.outline import width_at_distance
from fretboard.geometry.slots import fret_slot_centerlines
from fretboard.units import from_internal_length, round_display


def build_manifest(spec: FretboardSpec) -> dict:
    twelfth_width, end_width = resolve_taper_widths(spec.geometry)
    construction = resolve_construction(spec)
    wire_profiles, fit_profiles = load_profile_store()
    slotting = resolve_slotting(spec, wire_profiles=wire_profiles, fit_profiles=fit_profiles)
    return {
        "id": spec.id,
        "name": spec.name,
        "units": spec.units,
        "internal_units": "mm",
        "geometry": {
            "scale_length": round_display(from_internal_length(spec.geometry.scale_length, spec.units)),
            "num_frets": spec.geometry.num_frets,
            "num_strings": spec.geometry.num_strings,
            "fingerboard_width_at_nut": round_display(from_internal_length(spec.geometry.fingerboard_width_at_nut, spec.units)),
            "fingerboard_width_at_12th_fret": round_display(from_internal_length(twelfth_width, spec.units)),
            "fingerboard_width_at_end": round_display(from_internal_length(end_width, spec.units)),
            "fingerboard_width_at_scale": round_display(from_internal_length(width_at_distance(spec, spec.geometry.scale_length), spec.units)),
            "fingerboard_radius": round_display(from_internal_length(spec.geometry.fingerboard_radius, spec.units)),
        },
        "construction": {
            "fingerboard_thickness": round_display(from_internal_length(construction.fingerboard_thickness, spec.units)),
            "board_end_extension": round_display(from_internal_length(construction.board_end_extension, spec.units)),
            "edge_fillet": round_display(from_internal_length(construction.edge_fillet, spec.units)),
        },
        "construction_mm": {
            "fingerboard_thickness": round_display(construction.fingerboard_thickness),
            "board_end_extension": round_display(construction.board_end_extension),
            "edge_fillet": round_display(construction.edge_fillet),
        },
        "slotting": {
            "wire_profile_id": slotting.wire_profile_id,
            "fit_profile_id": slotting.fit_profile_id,
            "slot_width_source": slotting.slot_width_source,
            "slot_depth_source": slotting.slot_depth_source,
            "tang_offset_source": slotting.tang_offset_source,
            "resolved_slot_width": round_display(from_internal_length(slotting.resolved_slot_width, spec.units)),
            "resolved_slot_depth": round_display(from_internal_length(slotting.resolved_slot_depth, spec.units)),
            "resolved_tang_offset": round_display(from_internal_length(slotting.resolved_tang_offset, spec.units)),
        },
        "slotting_mm": {
            "resolved_slot_width": round_display(slotting.resolved_slot_width),
            "resolved_slot_depth": round_display(slotting.resolved_slot_depth),
            "resolved_tang_offset": round_display(slotting.resolved_tang_offset),
        },
        "geometry_mm": {
            "scale_length": round_display(spec.geometry.scale_length),
            "fingerboard_width_at_nut": round_display(spec.geometry.fingerboard_width_at_nut),
            "fingerboard_width_at_12th_fret": round_display(twelfth_width),
            "fingerboard_width_at_end": round_display(end_width),
            "fingerboard_width_at_scale": round_display(width_at_distance(spec, spec.geometry.scale_length)),
            "fingerboard_radius": round_display(spec.geometry.fingerboard_radius),
        },
        "metadata": spec.metadata.__dict__,
        "slot_count": len(fret_slot_centerlines(spec)),
    }
