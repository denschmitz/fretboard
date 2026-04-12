from fretboard.domain.models import FretboardSpec
from fretboard.domain.taper import resolve_taper_widths
from fretboard.geometry.construction_geometry import Point, Segment


def width_at_distance(spec: FretboardSpec, distance_from_nut: float) -> float:
    half_scale = spec.geometry.scale_length / 2
    nut_width = spec.geometry.fingerboard_width_at_nut
    twelfth_width, _ = resolve_taper_widths(spec.geometry)
    return nut_width + ((twelfth_width - nut_width) * (distance_from_nut / half_scale))


def nut_line(spec: FretboardSpec) -> Segment:
    return Segment(Point(0.0, 0.0), Point(spec.geometry.fingerboard_width_at_nut, 0.0))


def width_line_at_scale(spec: FretboardSpec) -> Segment:
    width = width_at_distance(spec, spec.geometry.scale_length)
    return Segment(Point(0.0, spec.geometry.scale_length), Point(width, spec.geometry.scale_length))


def string_paths(spec: FretboardSpec) -> list[Segment]:
    nut = spec.geometry.fingerboard_width_at_nut
    end = width_at_distance(spec, spec.geometry.scale_length)
    string_count = spec.geometry.num_strings
    return [
        Segment(
            Point(nut * (index / (string_count - 1)), 0.0),
            Point(end * (index / (string_count - 1)), spec.geometry.scale_length),
        )
        for index in range(string_count)
    ]
