import json
import re
from pathlib import Path

from fretboard.errors import PresetError
from fretboard.logging_utils import get_logger
from fretboard.units import DIMENSION_FIELDS, from_internal_length, round_display, to_internal_length

from .models import FretboardGeometry, FretboardMetadata, FretboardSpec, Preset
from .validation import validate_spec


PRESET_FILE_VERSION = 1

logger = get_logger(__name__)


def default_presets_path() -> Path:
    return Path(__file__).resolve().parents[3] / "presets" / "presets.json"



def default_user_presets_path() -> Path:
    return Path(__file__).resolve().parents[3] / "presets" / "user_presets.json"



def slugify_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not slug:
        raise PresetError("Preset name must contain at least one letter or number")
    return slug



def _geometry_to_internal(raw_geometry: dict, units: str) -> dict:
    converted = raw_geometry.copy()
    for field in DIMENSION_FIELDS:
        if field in converted and converted[field] is not None:
            converted[field] = to_internal_length(converted[field], units)
    return converted



def _geometry_to_display(raw_geometry: dict, units: str) -> dict:
    converted = raw_geometry.copy()
    for field in DIMENSION_FIELDS:
        if field in converted and converted[field] is not None:
            converted[field] = round_display(from_internal_length(converted[field], units))
    return converted



def spec_to_record(spec: FretboardSpec, *, preset_id: str | None = None, preset_name: str | None = None) -> dict:
    return {
        "id": preset_id or spec.id or slugify_name(spec.name),
        "name": preset_name or spec.name,
        "units": spec.units,
        "geometry": _geometry_to_display(spec.geometry.__dict__.copy(), spec.units),
        "metadata": spec.metadata.__dict__.copy(),
    }



def _read_payload(path: Path, *, create_if_missing: bool = False) -> dict:
    if not path.exists():
        if not create_if_missing:
            raise PresetError(f"Preset file not found: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": PRESET_FILE_VERSION, "presets": []}
        path.write_text(json.dumps(payload, indent=2) + "\n")
        logger.info("Created preset store at %s", path)
        return payload

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise PresetError(f"Preset file is not valid JSON: {exc}") from exc

    version = payload.get("version")
    if version != PRESET_FILE_VERSION:
        raise PresetError(f"Unsupported preset file version: {version}")

    presets = payload.get("presets")
    if not isinstance(presets, list):
        raise PresetError("Preset file must contain a 'presets' list")

    return payload



def _preset_from_dict(raw: dict, *, source: str) -> Preset:
    try:
        units = raw["units"]
        geometry = FretboardGeometry(**_geometry_to_internal(raw["geometry"], units))
        metadata = FretboardMetadata(**raw.get("metadata", {}))
        preset = Preset(
            id=raw["id"],
            name=raw["name"],
            units=units,
            geometry=geometry,
            metadata=metadata,
            source=source,
        )
    except KeyError as exc:
        raise PresetError(f"Missing preset field: {exc}") from exc
    except TypeError as exc:
        raise PresetError(f"Invalid preset shape: {exc}") from exc

    validate_spec(
        FretboardSpec(
            id=preset.id,
            name=preset.name,
            units=preset.units,
            geometry=preset.geometry,
            metadata=preset.metadata,
            source=preset.source,
        )
    )
    return preset



def _load_presets_from_path(path: Path, *, source: str, create_if_missing: bool = False) -> list[Preset]:
    payload = _read_payload(path, create_if_missing=create_if_missing)
    return [_preset_from_dict(raw, source=source) for raw in payload["presets"]]



def load_presets(
    path: Path | None = None,
    *,
    include_user: bool = True,
    user_path: Path | None = None,
) -> list[Preset]:
    built_in_path = path or default_presets_path()
    built_in = _load_presets_from_path(built_in_path, source="built_in")
    if not include_user:
        logger.debug("Loaded %s built-in presets", len(built_in))
        return built_in

    user_store = user_path or default_user_presets_path()
    user_presets = _load_presets_from_path(
        user_store,
        source="user",
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
    geometry_data = preset.geometry.__dict__.copy()
    metadata_data = preset.metadata.__dict__.copy()
    units = preset.units
    name = preset.name

    incoming = (overrides or {}).copy()
    if incoming.get("units") is not None:
        units = incoming["units"]

    logger.debug("Applying overrides for preset %s: %s", identifier, sorted(key for key, value in incoming.items() if value is not None))

    for key, value in incoming.items():
        if value is None:
            continue
        if key in geometry_data:
            geometry_data[key] = to_internal_length(value, units) if key in DIMENSION_FIELDS else value
        elif key in metadata_data:
            metadata_data[key] = value
        elif key == "units":
            units = value
        elif key == "name":
            name = value
        else:
            raise PresetError(f"Unknown override field: {key}")

    spec = FretboardSpec(
        id=preset.id,
        name=name,
        units=units,
        geometry=FretboardGeometry(**geometry_data),
        metadata=FretboardMetadata(**metadata_data),
        source=preset.source,
    )
    validate_spec(spec)
    return spec



def save_user_preset(
    spec: FretboardSpec,
    preset_name: str,
    *,
    user_path: Path | None = None,
    overwrite: bool = False,
) -> Preset:
    target_path = user_path or default_user_presets_path()
    payload = _read_payload(target_path, create_if_missing=True)
    preset_id = slugify_name(preset_name)
    record = spec_to_record(spec, preset_id=preset_id, preset_name=preset_name)

    existing = payload["presets"]
    existing_index = None
    for index, raw in enumerate(existing):
        if raw.get("id") == preset_id or raw.get("name") == preset_name:
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
    return _preset_from_dict(record, source="user")
