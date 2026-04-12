from dataclasses import dataclass
from math import atan2, degrees

from fretboard.domain.models import FretboardSpec
from fretboard.domain.presets import load_profile_store
from fretboard.domain.slotting import resolve_slotting
from fretboard.geometry.outline import string_paths
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament


@dataclass(frozen=True)
class SlotDefinition:
    fret_number: int
    position_y: float
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    orientation_degrees: float
    slot_depth: float
    slot_width: float



def fret_slot_centerlines(
    spec: FretboardSpec,
) -> list[SlotDefinition]:
    wire_profiles, fit_profiles = load_profile_store()
    slotting = resolve_slotting(spec, wire_profiles=wire_profiles, fit_profiles=fit_profiles)
    scale = equal_temperament(12)
    positions = calculate_fret_positions(scale, spec.geometry.scale_length, spec.geometry.num_frets)
    strings = string_paths(spec)
    slots: list[SlotDefinition] = []

    for fret_number in range(1, spec.geometry.num_frets + 1):
        points = [
            string.point_at_ratio(positions[fret_number] / spec.geometry.scale_length)
            for string in strings
        ]
        slots.append(
            SlotDefinition(
                fret_number=fret_number,
                position_y=positions[fret_number],
                start_x=points[0].x,
                start_y=points[0].y,
                end_x=points[-1].x,
                end_y=points[-1].y,
                orientation_degrees=degrees(atan2(points[-1].y - points[0].y, points[-1].x - points[0].x)),
                slot_depth=slotting.resolved_slot_depth,
                slot_width=slotting.resolved_slot_width,
            )
        )

    return slots
