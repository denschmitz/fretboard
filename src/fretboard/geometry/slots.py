from dataclasses import dataclass

from fretboard.domain.models import FretboardSpec
from fretboard.geometry.outline import string_paths
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament


@dataclass(frozen=True)
class SlotDefinition:
    fret_number: int
    start_x: float
    start_y: float
    end_x: float
    end_y: float



def fret_slot_centerlines(spec: FretboardSpec) -> list[SlotDefinition]:
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
                start_x=points[0].x,
                start_y=points[0].y,
                end_x=points[-1].x,
                end_y=points[-1].y,
            )
        )

    return slots
