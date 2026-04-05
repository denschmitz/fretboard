from dataclasses import dataclass

from fretboard.domain.models import FretboardSpec
from fretboard.geometry.outline import width_at_distance
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament


ALPHA_INLAY_STYLE = "dot"
STANDARD_DOT_MARKER_FRETS = (3, 5, 7, 9, 12, 15, 17, 19, 21)
DOUBLE_DOT_FRETS = {12}


@dataclass(frozen=True)
class InlayRecess:
    fret_number: int
    style: str
    center_x: float
    center_y: float
    diameter: float
    depth: float


def resolved_inlay_style(style: str | None) -> str | None:
    if style is None or not style.strip():
        return None
    return ALPHA_INLAY_STYLE


def standard_inlay_marker_frets(num_frets: int) -> list[int]:
    return [fret for fret in STANDARD_DOT_MARKER_FRETS if fret <= num_frets]


def marker_center_y(fret_positions: list[float], fret_number: int) -> float:
    return (fret_positions[fret_number - 1] + fret_positions[fret_number]) / 2


def inlay_recesses(
    spec: FretboardSpec,
    *,
    dot_diameter: float = 6.0,
    cut_depth: float = 5.0,
    octave_pair_offset_ratio: float = 0.18,
) -> list[InlayRecess]:
    style = resolved_inlay_style(spec.metadata.inlay_style)
    if style is None:
        return []

    fret_positions = calculate_fret_positions(equal_temperament(), spec.geometry.scale_length, spec.geometry.num_frets)
    recesses: list[InlayRecess] = []

    for fret_number in standard_inlay_marker_frets(spec.geometry.num_frets):
        center_y = marker_center_y(fret_positions, fret_number)
        if fret_number in DOUBLE_DOT_FRETS:
            offset = width_at_distance(spec, center_y) * octave_pair_offset_ratio
            center_x_positions = (-offset, offset)
        else:
            center_x_positions = (0.0,)

        for center_x in center_x_positions:
            recesses.append(
                InlayRecess(
                    fret_number=fret_number,
                    style=style,
                    center_x=center_x,
                    center_y=center_y,
                    diameter=dot_diameter,
                    depth=cut_depth,
                )
            )

    return recesses
