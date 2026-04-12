import json
import re
from dataclasses import asdict
from pathlib import Path

from fretboard.cad.defaults import CadDefaults
from fretboard.errors import PresetError
from fretboard.logging_utils import get_logger
from fretboard.units import DIMENSION_FIELDS, from_internal_length, round_display, to_internal_length

from .models import (
    ConstructionParameters,
    FitProfile,
    FretboardGeometry,
    FretboardMetadata,
    FretboardSpec,
    Preset,
    SlottingParameters,
    WireProfile,
)
from .slotting import default_fit_profiles, default_wire_profiles
from .taper import resolve_taper_widths
from .validation import validate_profiles, validate_spec


PRESET_FILE_VERSION = 2
LEGACY_PRESET_FILE_VERSION = 1

logger = get_logger(__name__)

GEOMETRY_FIELDS = set(FretboardGeometry.__dataclass_fields__)
CONSTRUCTION_FIELDS = set(ConstructionParameters.__dataclass_fields__)
SLOTTING_FIELDS = set(SlottingParameters.__dataclass_fields__)
METADATA_FIELDS = set(FretboardMetadata.__dataclass_fields__)
PROFILE_LIST_FIELDS = ("wire_profiles", "fit_profiles")


def default_presets_path() -> Path:
    return Path(__file__).resolve().parents[3] / "presets" / "presets.json"


def default_user_presets_path() -> Path:
    return Path(__file__).resolve().parents[3] / "presets" / "user_presets.json"


def slugify_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not slug:
        raise PresetError("Preset name must contain at least one letter or number")
    return slug


def _empty_payload() -> dict:
    return {
        "version": PRESET_FILE_VERSION,
        "presets": [],
        "wire_profiles": [asdict(profile) for profile in default_wire_profiles()],
        "fit_profiles": [asdict(profile) for profile in default_fit_profiles()],
    }


def _compact_dict(data: dict) -> dict:
    return {key: value for key, value in data.items() if value is not None}


def _section_to_internal(raw_section: dict, units: str) -> dict:
    converted = raw_section.copy()
    for field, value in list(converted.items()):
        if field in DIMENSION_FIELDS and value is not None:
            converted[field] = to_internal_length(value, units)
    return converted


def _section_to_display(raw_section: dict, units: str) -> dict:
    converted = raw_section.copy()
    for field, value in list(converted.items()):
        if field in DIMENSION_FIELDS and value is not None:
            converted[field] = round_display(from_internal_length(value, units))
    return converted


def _normalize_geometry(raw_geometry: dict) -> FretboardGeometry:
    geometry = FretboardGeometry(**raw_geometry)
    twelfth_width, end_width = resolve_taper_widths(geometry)
    return FretboardGeometry(
        scale_length=geometry.scale_length,
        num_frets=geometry.num_frets,
        num_strings=geometry.num_strings,
        fingerboard_width_at_nut=geometry.fingerboard_width_at_nut,
        fingerboard_width_at_12th_fret=twelfth_width,
        fingerboard_width_at_end=end_width,
        fingerboard_radius=geometry.fingerboard_radius,
        fingerboard_radius_end=geometry.fingerboard_radius_end,
        fingerboard_thickness_at_nut=geometry.fingerboard_thickness_at_nut,
        fingerboard_thickness_at_end=geometry.fingerboard_thickness_at_end,
    )


def _apply_taper_override_precedence(geometry_data: dict, incoming: dict) -> dict:
    updated = geometry_data.copy()
    has_twelfth_override = incoming.get("fingerboard_width_at_12th_fret") is not None
    has_end_override = incoming.get("fingerboard_width_at_end") is not None
    changed_taper_basis = any(incoming.get(key) is not None for key in ("scale_length", "num_frets"))

    if has_twelfth_override and not has_end_override:
        updated["fingerboard_width_at_end"] = None
    elif has_end_override and not has_twelfth_override:
        updated["fingerboard_width_at_12th_fret"] = None
    elif changed_taper_basis and not has_twelfth_override and not has_end_override:
        updated["fingerboard_width_at_end"] = None

    return updated


def _coerce_wire_profile(raw: dict) -> WireProfile:
    try:
        return WireProfile(**raw)
    except TypeError as exc:
        raise PresetError(f"Invalid wire profile shape: {exc}") from exc


def _coerce_fit_profile(raw: dict) -> FitProfile:
    try:
        return FitProfile(**raw)
    except TypeError as exc:
        raise PresetError(f"Invalid fit profile shape: {exc}") from exc


def _compatibility_construction(units: str) -> dict:
    defaults = CadDefaults()
    return {
        "fingerboard_thickness": round_display(from_internal_length(defaults.compatibility_fingerboard_thickness_mm, units)),
        "board_end_extension": round_display(from_internal_length(defaults.compatibility_board_end_extension_mm, units)),
    }


def _migrate_legacy_preset(raw: dict, *, source: str) -> dict:
    migrated = raw.copy()
    units = migrated.get("units", "mm")
    if "construction" not in migrated:
        construction = {}
        for field in CONSTRUCTION_FIELDS:
            if field in migrated:
                construction[field] = migrated.pop(field)
        if not construction:
            construction = _compatibility_construction(units)
        migrated["construction"] = construction
        logger.warning("Migrated legacy preset %s by adding a construction section", migrated.get("name", migrated.get("id", "<unknown>")))

    if "slotting" not in migrated:
        slotting = {}
        for field in SLOTTING_FIELDS:
            if field in migrated:
                slotting[field] = migrated.pop(field)
        geometry = migrated.get("geometry", {})
        for field in ("slot_width", "slot_depth", "tang_offset", "wire_profile_id", "fit_profile_id"):
            if field in geometry:
                slotting[field] = geometry.pop(field)
        if "tang_width" in migrated or "tang_depth" in migrated:
            raise PresetError(
                "Legacy preset contains tang_width/tang_depth without a deterministic migration rule; define slotting explicitly"
            )
        migrated["slotting"] = slotting
        logger.warning("Migrated legacy preset %s by adding a slotting section", migrated.get("name", migrated.get("id", "<unknown>")))

    if "metadata" not in migrated:
        migrated["metadata"] = {}

    return migrated


def _normalize_payload(payload: dict, *, source: str) -> dict:
    if not isinstance(payload, dict):
        raise PresetError("Preset file must contain a JSON object")

    version = payload.get("version")
    if version not in {PRESET_FILE_VERSION, LEGACY_PRESET_FILE_VERSION}:
        raise PresetError(f"Unsupported preset file version: {version}")

    presets = payload.get("presets")
    if not isinstance(presets, list):
        raise PresetError("Preset file must contain a 'presets' list")

    if version == LEGACY_PRESET_FILE_VERSION:
        logger.warning("Migrating legacy preset store version %s loaded from %s data", version, source)

    normalized = {
        "version": PRESET_FILE_VERSION,
        "presets": [
            _migrate_legacy_preset(raw, source=source) if version == LEGACY_PRESET_FILE_VERSION or "construction" not in raw or "slotting" not in raw else raw
            for raw in presets
        ],
        "wire_profiles": payload.get("wire_profiles") or [asdict(profile) for profile in default_wire_profiles()],
        "fit_profiles": payload.get("fit_profiles") or [asdict(profile) for profile in default_fit_profiles()],
    }
    return normalized


def _read_payload(path: Path, *, create_if_missing: bool = False) -> dict:
    if not path.exists():
        if not create_if_missing:
            raise PresetError(f"Preset file not found: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _empty_payload()
        path.write_text(json.dumps(payload, indent=2) + "\n")
        logger.info("Created preset store at %s", path)
        return payload

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PresetError(f"Preset file is not valid JSON: {exc}") from exc

    return _normalize_payload(payload, source=str(path))


def _preset_from_dict(
    raw: dict,
    *,
    source: str,
    wire_profiles: list[WireProfile],
    fit_profiles: list[FitProfile],
) -> Preset:
    try:
        units = raw["units"]
        geometry = _normalize_geometry(_section_to_internal(raw["geometry"], units))
        construction = ConstructionParameters(**_section_to_internal(raw.get("construction", {}), units))
        slotting = SlottingParameters(**_section_to_internal(raw.get("slotting", {}), units))
        metadata = FretboardMetadata(**raw.get("metadata", {}))
        preset = Preset(
            id=raw["id"],
            name=raw["name"],
            units=units,
            geometry=geometry,
            construction=construction,
            slotting=slotting,
            metadata=metadata,
            source=source,
        )
    except KeyError as exc:
        raise PresetError(f"Missing preset field: {exc}") from exc
    except TypeError as exc:
        raise PresetError(f"Invalid preset shape: {exc}") from exc

    validate_spec(preset_to_spec(preset), wire_profiles=wire_profiles, fit_profiles=fit_profiles)
    return preset


def spec_to_record(spec: FretboardSpec, *, preset_id: str | None = None, preset_name: str | None = None) -> dict:
    geometry = _normalize_geometry(asdict(spec.geometry))
    geometry_data = asdict(geometry)
    geometry_data.pop("fingerboard_width_at_end", None)
    return {
        "id": preset_id or spec.id or slugify_name(spec.name),
        "name": preset_name or spec.name,
        "units": spec.units,
        "geometry": _compact_dict(_section_to_display(geometry_data, spec.units)),
        "construction": _compact_dict(_section_to_display(asdict(spec.construction), spec.units)),
        "slotting": _compact_dict(_section_to_display(asdict(spec.slotting), spec.units)),
        "metadata": _compact_dict(asdict(spec.metadata)),
    }


def preset_to_spec(preset: Preset) -> FretboardSpec:
    return FretboardSpec(
        id=preset.id,
        name=preset.name,
        units=preset.units,
        geometry=preset.geometry,
        construction=preset.construction,
        slotting=preset.slotting,
        metadata=preset.metadata,
        source=preset.source,
    )


def load_profile_store(
    path: Path | None = None,
    *,
    user_path: Path | None = None,
) -> tuple[list[WireProfile], list[FitProfile]]:
    built_in_payload = _read_payload(path or default_presets_path())
    user_payload = _read_payload(user_path or default_user_presets_path(), create_if_missing=True)

    wire_by_id: dict[str, WireProfile] = {}
    fit_by_id: dict[str, FitProfile] = {}
    for raw in [*built_in_payload["wire_profiles"], *user_payload["wire_profiles"]]:
        profile = _coerce_wire_profile(raw)
        wire_by_id[profile.id] = profile
    for raw in [*built_in_payload["fit_profiles"], *user_payload["fit_profiles"]]:
        profile = _coerce_fit_profile(raw)
        fit_by_id[profile.id] = profile

    wire_profiles = list(wire_by_id.values())
    fit_profiles = list(fit_by_id.values())
    validate_profiles(wire_profiles, fit_profiles)
    return wire_profiles, fit_profiles


def _load_presets_from_path(
    path: Path,
    *,
    source: str,
    wire_profiles: list[WireProfile],
    fit_profiles: list[FitProfile],
    create_if_missing: bool = False,
) -> list[Preset]:
    payload = _read_payload(path, create_if_missing=create_if_missing)
    return [
        _preset_from_dict(raw, source=source, wire_profiles=wire_profiles, fit_profiles=fit_profiles)
        for raw in payload["presets"]
    ]


def load_presets(
    path: Path | None = None,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> list[Preset]:
    wire_profiles, fit_profiles = load_profile_store(path, user_path=user_path)
    built_in_path = path or default_presets_path()
    built_in = _load_presets_from_path(
        built_in_path,
        source="built_in",
        wire_profiles=wire_profiles,
        fit_profiles=fit_profiles,
    )
    if not include_user:
        logger.debug("Loaded %s built-in presets", len(built_in))
        return built_in

    user_store = user_path or default_user_presets_path()
    user_presets = _load_presets_from_path(
        user_store,
        source="user",
        wire_profiles=wire_profiles,
        fit_profiles=fit_profiles,
        create_if_missing=True,
    )
    logger.debug("Loaded %s built-in presets and %s user presets", len(built_in), len(user_presets))
    return [*built_in, *user_presets]


def list_presets(
    path: Path | None = None,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> list[Preset]:
    return load_presets(path, include_user=include_user, user_path=user_path)


def get_preset(
    identifier: str,
    path: Path | None = None,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> Preset:
    presets = load_presets(path, include_user=include_user, user_path=user_path)
    for preset in presets:
        if preset.id == identifier or preset.name == identifier:
            return preset
    raise PresetError(f"Unknown preset: {identifier}")


def build_spec_from_preset(
    identifier: str,
    path: Path | None = None,
    overrides: dict | None = None,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> FretboardSpec:
    preset = get_preset(identifier, path, include_user=include_user, user_path=user_path)
    wire_profiles, fit_profiles = load_profile_store(path, user_path=user_path)
    geometry_data = asdict(preset.geometry)
    construction_data = asdict(preset.construction)
    slotting_data = asdict(preset.slotting)
    metadata_data = asdict(preset.metadata)
    units = preset.units
    name = preset.name

    incoming = (overrides or {}).copy()
    if incoming.get("units") is not None:
        units = incoming["units"]

    logger.debug(
        "Applying overrides for preset %s: %s",
        identifier,
        sorted(key for key, value in incoming.items() if value is not None),
    )

    for key, value in incoming.items():
        if value is None:
            continue
        target = None
        if key in GEOMETRY_FIELDS:
            target = geometry_data
        elif key in CONSTRUCTION_FIELDS:
            target = construction_data
        elif key in SLOTTING_FIELDS:
            target = slotting_data
        elif key in METADATA_FIELDS:
            target = metadata_data
        elif key == "units":
            units = value
            continue
        elif key == "name":
            name = value
            continue
        else:
            raise PresetError(f"Unknown override field: {key}")

        target[key] = to_internal_length(value, units) if key in DIMENSION_FIELDS else value

    geometry_data = _apply_taper_override_precedence(geometry_data, incoming)
    spec = FretboardSpec(
        id=preset.id,
        name=name,
        units=units,
        geometry=_normalize_geometry(geometry_data),
        construction=ConstructionParameters(**construction_data),
        slotting=SlottingParameters(**slotting_data),
        metadata=FretboardMetadata(**metadata_data),
        source=preset.source,
    )
    validate_spec(spec, wire_profiles=wire_profiles, fit_profiles=fit_profiles)
    return spec


def export_preset(
    identifier: str,
    path: Path,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> Path:
    preset = get_preset(identifier, include_user=include_user, user_path=user_path)
    record = spec_to_record(preset_to_spec(preset), preset_id=preset.id, preset_name=preset.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")
    logger.info("Exported preset %s to %s", identifier, path)
    return path


def load_single_preset(path: Path, *, user_path: Path | None = None) -> Preset:
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise PresetError(f"Preset file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PresetError(f"Preset file is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise PresetError("Standalone preset file must contain a single preset object")

    if "construction" not in raw or "slotting" not in raw:
        raw = _migrate_legacy_preset(raw, source="standalone")

    wire_profiles, fit_profiles = load_profile_store(user_path=user_path)
    return _preset_from_dict(raw, source="user", wire_profiles=wire_profiles, fit_profiles=fit_profiles)


def save_user_preset(
    spec: FretboardSpec,
    preset_name: str,
    *,
    user_path: Path | None = None,
    overwrite: bool = False,
    preset_id: str | None = None,
) -> Preset:
    target_path = user_path or default_user_presets_path()
    payload = _read_payload(target_path, create_if_missing=True)
    resolved_preset_id = preset_id or slugify_name(preset_name)
    record = spec_to_record(spec, preset_id=resolved_preset_id, preset_name=preset_name)

    existing = payload["presets"]
    existing_index = None
    for index, raw in enumerate(existing):
        if raw.get("id") == resolved_preset_id or raw.get("name") == preset_name:
            existing_index = index
            break

    if existing_index is not None and not overwrite:
        raise PresetError(f"User preset already exists: {preset_name}")

    if existing_index is None:
        existing.append(record)
    else:
        existing[existing_index] = record

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2) + "\n")
    logger.info("Saved user preset %s to %s", preset_name, target_path)
    wire_profiles, fit_profiles = load_profile_store(user_path=target_path)
    return _preset_from_dict(record, source="user", wire_profiles=wire_profiles, fit_profiles=fit_profiles)


def import_user_preset(
    path: Path,
    *,
    user_path: Path | None = None,
    overwrite: bool = False,
) -> Preset:
    preset = load_single_preset(path, user_path=user_path)
    return save_user_preset(
        preset_to_spec(preset),
        preset.name,
        user_path=user_path,
        overwrite=overwrite,
        preset_id=preset.id,
    )
