from dataclasses import dataclass, field


@dataclass(frozen=True)
class FretboardGeometry:
    scale_length: float
    num_frets: int
    num_strings: int
    fingerboard_width_at_nut: float
    fingerboard_width_at_12th_fret: float
    fingerboard_radius: float


@dataclass(frozen=True)
class FretboardMetadata:
    fingerboard_material: str | None = None
    fret_material: str | None = None
    nut_material: str | None = None
    inlay_material: str | None = None
    inlay_style: str | None = None


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    units: str
    geometry: FretboardGeometry
    metadata: FretboardMetadata = field(default_factory=FretboardMetadata)
    source: str = "built_in"


@dataclass(frozen=True)
class FretboardSpec:
    id: str | None
    name: str
    units: str
    geometry: FretboardGeometry
    metadata: FretboardMetadata = field(default_factory=FretboardMetadata)
    source: str = "ad_hoc"
