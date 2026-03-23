from fretboard.domain.models import FretboardSpec
from fretboard.geometry.outline import width_at_distance
from fretboard.geometry.slots import fret_slot_centerlines



def build_manifest(spec: FretboardSpec) -> dict:
    return {
        "id": spec.id,
        "name": spec.name,
        "units": spec.units,
        "geometry": {
            "scale_length": spec.geometry.scale_length,
            "num_frets": spec.geometry.num_frets,
            "num_strings": spec.geometry.num_strings,
            "fingerboard_width_at_nut": spec.geometry.fingerboard_width_at_nut,
            "fingerboard_width_at_12th_fret": spec.geometry.fingerboard_width_at_12th_fret,
            "fingerboard_width_at_scale": width_at_distance(spec, spec.geometry.scale_length),
            "fingerboard_radius": spec.geometry.fingerboard_radius,
        },
        "metadata": spec.metadata.__dict__,
        "slot_count": len(fret_slot_centerlines(spec)),
    }
