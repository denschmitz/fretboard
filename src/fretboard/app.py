from pathlib import Path

from fretboard.cad.interface import ExportRequest
from fretboard.cad.step_export import StepExportBackend
from fretboard.domain.models import FretboardSpec
from fretboard.domain.presets import build_spec_from_preset, list_presets, save_user_preset
from fretboard.logging_utils import get_logger
from fretboard.outputs.files import default_step_output_path, resolve_work_folder, write_design_output
from fretboard.outputs.manifest import build_manifest
from fretboard.units import DIMENSION_FIELDS, convert_dimension_dict, from_internal_length, round_display


logger = get_logger(__name__)


def available_presets(user_path: Path | None = None):
    presets = list_presets(user_path=user_path)
    logger.debug("Loaded %s presets", len(presets))
    return presets



def resolve_spec(
    preset: str,
    overrides: dict | None = None,
    *,
    user_path: Path | None = None,
) -> FretboardSpec:
    logger.info("Resolving preset %s", preset)
    spec = build_spec_from_preset(preset, overrides=overrides, user_path=user_path)
    logger.debug("Resolved spec %s in %s", spec.name, spec.units)
    return spec



def editable_fields_from_preset(
    preset: str,
    *,
    user_path: Path | None = None,
) -> dict:
    spec = resolve_spec(preset, user_path=user_path)
    geometry = {
        field: round_display(from_internal_length(getattr(spec.geometry, field), spec.units))
        for field in spec.geometry.__dict__
        if field in DIMENSION_FIELDS
    }
    counts = {
        field: getattr(spec.geometry, field)
        for field in spec.geometry.__dict__
        if field not in DIMENSION_FIELDS
    }
    return {
        "id": spec.id,
        "source": spec.source,
        "name": spec.name,
        "units": spec.units,
        **geometry,
        **counts,
        **spec.metadata.__dict__,
    }



def convert_display_fields(fields: dict, new_units: str) -> dict:
    current_units = fields["units"]
    geometry = {field: fields[field] for field in DIMENSION_FIELDS if field in fields}
    converted = convert_dimension_dict(geometry, current_units, new_units)
    updated = fields.copy()
    updated.update({field: round_display(value) for field, value in converted.items()})
    updated["units"] = new_units
    logger.debug("Converted display fields from %s to %s", current_units, new_units)
    return updated



def rename_spec(spec: FretboardSpec, new_name: str) -> FretboardSpec:
    return FretboardSpec(
        id=spec.id,
        name=new_name,
        units=spec.units,
        geometry=spec.geometry,
        metadata=spec.metadata,
        source=spec.source,
    )



def save_named_user_preset(
    spec: FretboardSpec,
    preset_name: str,
    *,
    user_path: Path | None = None,
    overwrite: bool = False,
):
    renamed_spec = rename_spec(spec, preset_name)
    logger.info("Saving user preset %s", preset_name)
    return save_user_preset(renamed_spec, preset_name, user_path=user_path, overwrite=overwrite)



def build_design_summary(spec: FretboardSpec) -> dict:
    return build_manifest(spec)



def generate_output(
    spec: FretboardSpec,
    *,
    output_path: Path | None = None,
    work_folder: Path | None = None,
) -> Path:
    step_path = output_path or default_step_output_path(spec, work_folder)
    logger.info("Generating STEP output for %s", spec.name)
    backend = StepExportBackend()
    backend.export_step(ExportRequest(spec=spec, output_path=step_path))
    summary = build_design_summary(spec)
    write_design_output(summary, step_path)
    logger.info("Generated STEP output at %s", step_path)
    return step_path



def resolved_work_folder(work_folder: Path | None = None) -> Path:
    resolved = resolve_work_folder(work_folder)
    logger.debug("Resolved work folder to %s", resolved)
    return resolved
