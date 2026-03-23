from fretboard.domain.models import FretboardSpec
from fretboard.geometry.outline import width_at_distance
from fretboard.geometry.slots import fret_slot_centerlines
from fretboard.units import from_internal_length, round_display



def build_manifest(spec: FretboardSpec) -> dict:
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
            "fingerboard_width_at_12th_fret": round_display(from_internal_length(spec.geometry.fingerboard_width_at_12th_fret, spec.units)),
            "fingerboard_width_at_scale": round_display(from_internal_length(width_at_distance(spec, spec.geometry.scale_length), spec.units)),
            "fingerboard_radius": round_display(from_internal_length(spec.geometry.fingerboard_radius, spec.units)),
        },
        "geometry_mm": {
            "scale_length": round_display(spec.geometry.scale_length),
            "fingerboard_width_at_nut": round_display(spec.geometry.fingerboard_width_at_nut),
            "fingerboard_width_at_12th_fret": round_display(spec.geometry.fingerboard_width_at_12th_fret),
            "fingerboard_width_at_scale": round_display(width_at_distance(spec, spec.geometry.scale_length)),
            "fingerboard_radius": round_display(spec.geometry.fingerboard_radius),
        },
        "metadata": spec.metadata.__dict__,
        "slot_count": len(fret_slot_centerlines(spec)),
    }
