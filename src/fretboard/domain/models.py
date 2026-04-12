from dataclasses import dataclass, field


@dataclass(frozen=True)
class FretboardGeometry:
    scale_length: float
    num_frets: int
    num_strings: int
    fingerboard_width_at_nut: float
    fingerboard_width_at_12th_fret: float | None = None
    fingerboard_width_at_end: float | None = None
    fingerboard_radius: float = 0.0
    fingerboard_radius_end: float | None = None
    fingerboard_thickness_at_nut: float | None = None
    fingerboard_thickness_at_end: float | None = None


@dataclass(frozen=True)
class ConstructionParameters:
    fingerboard_thickness: float | None = None
    board_end_extension: float | None = None
    edge_fillet: float | None = None


@dataclass(frozen=True)
class SlottingParameters:
    wire_profile_id: str | None = None
    fit_profile_id: str | None = None
    slot_width: float | None = None
    slot_depth: float | None = None
    tang_offset: float | None = None


@dataclass(frozen=True)
class FretboardMetadata:
    fingerboard_material: str | None = None
    fret_material: str | None = None
    nut_material: str | None = None
    inlay_material: str | None = None
    inlay_style: str | None = None
    display_notes: str | None = None
    era: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class WireProfile:
    id: str
    name: str
    tang_width: float
    tang_depth: float
    crown_width: float | None = None
    crown_height: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class FitProfile:
    id: str
    name: str
    slot_width_delta_from_tang: float
    slot_depth_delta_from_tang: float
    tang_measurement_basis: str | None = None
    slot_cut_method: str | None = None
    fret_installation_method: str | None = None
    tang_style: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ResolvedSlotting:
    wire_profile_id: str | None
    fit_profile_id: str | None
    resolved_slot_width: float
    resolved_slot_depth: float
    resolved_tang_offset: float | None
    slot_width_source: str
    slot_depth_source: str
    tang_offset_source: str
    wire_profile: WireProfile | None = None
    fit_profile: FitProfile | None = None


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    units: str
    geometry: FretboardGeometry
    construction: ConstructionParameters = field(default_factory=ConstructionParameters)
    slotting: SlottingParameters = field(default_factory=SlottingParameters)
    metadata: FretboardMetadata = field(default_factory=FretboardMetadata)
    source: str = "built_in"


@dataclass(frozen=True)
class FretboardSpec:
    id: str | None
    name: str
    units: str
    geometry: FretboardGeometry
    construction: ConstructionParameters = field(default_factory=ConstructionParameters)
    slotting: SlottingParameters = field(default_factory=SlottingParameters)
    metadata: FretboardMetadata = field(default_factory=FretboardMetadata)
    source: str = "ad_hoc"
