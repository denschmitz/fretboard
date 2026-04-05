import json
import math
import shutil
import uuid
from pathlib import Path

from fretboard.app import (
    available_presets,
    convert_display_fields,
    editable_fields_from_preset,
    export_named_preset,
    generate_output,
    import_preset_file,
    resolve_spec,
    save_named_user_preset,
)
from fretboard.cad.build123d_backend import build_fretboard_part
from fretboard.cad.defaults import CadDefaults
from fretboard.cad.interface import ExportRequest
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament
from fretboard.outputs.files import sidecar_manifest_path



def _make_workspace_temp_dir() -> Path:
    base = Path(__file__).resolve().parents[1] / ".test_tmp"
    base.mkdir(exist_ok=True)
    path = base / str(uuid.uuid4())
    path.mkdir()
    return path



def test_presets_load() -> None:
    presets = available_presets()
    assert len(presets) >= 5



def test_lookup_by_id_and_name() -> None:
    assert resolve_spec("gibson_les_paul").name == "Gibson Les Paul"
    assert resolve_spec("Gibson Les Paul").id == "gibson_les_paul"



def test_internal_geometry_uses_millimeters() -> None:
    spec = resolve_spec("gibson_les_paul")
    assert math.isclose(spec.geometry.scale_length, 628.65, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(spec.geometry.fingerboard_width_at_nut, 43.053, rel_tol=0, abs_tol=1e-6)



def test_editable_fields_preload_display_values_from_preset_units() -> None:
    fields = editable_fields_from_preset("gibson_les_paul")
    assert fields["source"] == "built_in"
    assert fields["name"] == "Gibson Les Paul"
    assert fields["units"] == "in"
    assert fields["scale_length"] == 24.75
    assert fields["num_frets"] == 22
    assert fields["num_strings"] == 6
    assert fields["fingerboard_width_at_nut"] == 1.695
    assert fields["fingerboard_width_at_12th_fret"] == 2.26
    assert fields["fingerboard_radius"] == 12.0
    assert fields["fingerboard_material"] == "Rosewood"
    assert fields["fret_material"] == "Nickel Silver"
    assert fields["nut_material"] == "Graph Tech"
    assert fields["inlay_material"] == "Acrylic"
    assert fields["inlay_style"] == "Trapezoid"



def test_changing_display_units_converts_numeric_fields() -> None:
    fields = editable_fields_from_preset("gibson_les_paul")
    converted = convert_display_fields(fields, "mm")
    assert converted["units"] == "mm"
    assert math.isclose(converted["scale_length"], 628.65, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(converted["fingerboard_width_at_nut"], 43.053, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(converted["fingerboard_radius"], 304.8, rel_tol=0, abs_tol=1e-6)



def test_resolve_spec_applies_overrides_using_selected_display_units() -> None:
    spec = resolve_spec(
        "gibson_les_paul",
        overrides={
            "units": "mm",
            "name": "Modified Les Paul",
            "scale_length": 635.0,
            "num_frets": 24,
            "fingerboard_radius": 355.6,
        },
    )
    assert spec.name == "Modified Les Paul"
    assert spec.units == "mm"
    assert spec.geometry.scale_length == 635.0
    assert spec.geometry.num_frets == 24
    assert spec.geometry.fingerboard_radius == 355.6



def test_save_named_user_preset_uses_separate_user_file() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        user_path = temp_dir / "user_presets.json"
        spec = resolve_spec(
            "gibson_les_paul",
            overrides={"units": "mm", "scale_length": 635.0},
            user_path=user_path,
        )

        saved = save_named_user_preset(spec, "My Custom LP", user_path=user_path)

        payload = json.loads(user_path.read_text())
        assert saved.source == "user"
        assert payload["presets"][0]["name"] == "My Custom LP"
        assert payload["presets"][0]["units"] == "mm"
        assert payload["presets"][0]["geometry"]["scale_length"] == 635.0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_exported_preset_can_be_edited_imported_and_resolved_by_name() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "exported.json"
        user_path = temp_dir / "user_presets.json"

        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())
        assert payload["name"] == "Gibson Les Paul"
        assert payload["metadata"]["fingerboard_material"] == "Rosewood"

        payload["name"] = "Imported LP"
        payload["id"] = "imported_lp"
        payload["units"] = "mm"
        payload["geometry"]["scale_length"] = 635.0
        export_path.write_text(json.dumps(payload, indent=2) + "\n")

        imported = import_preset_file(export_path, user_path=user_path)
        resolved = resolve_spec("Imported LP", user_path=user_path)

        assert imported.name == "Imported LP"
        assert imported.id == "imported_lp"
        assert resolved.id == "imported_lp"
        assert resolved.units == "mm"
        assert math.isclose(resolved.geometry.scale_length, 635.0, rel_tol=0, abs_tol=1e-6)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_backend_part_extends_past_last_fret() -> None:
    spec = resolve_spec("gibson_les_paul")
    defaults = CadDefaults()
    part = build_fretboard_part(ExportRequest(spec=spec, output_path=Path("unused.step")), defaults)
    fret_positions = calculate_fret_positions(equal_temperament(), spec.geometry.scale_length, spec.geometry.num_frets)
    assert part.bounding_box().max.Y > fret_positions[-1]



def test_generate_output_creates_step_and_manifest_in_work_folder() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        spec = resolve_spec("gibson_les_paul")
        output_path = generate_output(spec, work_folder=temp_dir)
        manifest_path = sidecar_manifest_path(output_path)

        assert output_path.parent == temp_dir
        assert output_path.suffix == ".step"
        assert output_path.exists()
        assert manifest_path.exists()

        payload = json.loads(manifest_path.read_text())
        assert payload["output_type"] == "fretboard_design_manifest"
        assert payload["step_file"] == str(output_path)
        assert payload["spec"]["name"] == "Gibson Les Paul"
        assert payload["spec"]["units"] == "in"
        assert payload["spec"]["internal_units"] == "mm"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
