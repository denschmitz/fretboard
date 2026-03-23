from pathlib import Path

from fretboard.domain.models import FretboardSpec
from fretboard.domain.presets import build_spec_from_preset, list_presets, save_user_preset
from fretboard.outputs.files import write_design_output
from fretboard.outputs.manifest import build_manifest



def available_presets(user_path: Path | None = None):
    return list_presets(user_path=user_path)



def resolve_spec(
    preset: str,
    overrides: dict | None = None,
    *,
    user_path: Path | None = None,
) -> FretboardSpec:
    return build_spec_from_preset(preset, overrides=overrides, user_path=user_path)



def editable_fields_from_preset(
    preset: str,
    *,
    user_path: Path | None = None,
) -> dict:
    spec = resolve_spec(preset, user_path=user_path)
    return {
        "id": spec.id,
        "source": spec.source,
        "name": spec.name,
        "units": spec.units,
        **spec.geometry.__dict__,
        **spec.metadata.__dict__,
    }



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
    return save_user_preset(renamed_spec, preset_name, user_path=user_path, overwrite=overwrite)



def build_design_summary(spec: FretboardSpec) -> dict:
    return build_manifest(spec)



def generate_output(
    spec: FretboardSpec,
    *,
    output_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    summary = build_design_summary(spec)
    return write_design_output(summary, spec, output_path=output_path, output_dir=output_dir)
