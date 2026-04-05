import importlib
import json
import logging
import math
import shutil
import sys
import types
import uuid
from pathlib import Path

import pytest

from fretboard import cli
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
from fretboard.cad import build123d_backend
from fretboard.cad.build123d_backend import _board_length_mm, _build_dot_inlay_profile, _extrude_inlay_profile, build_inlay_cut_parts
from fretboard.cad.defaults import CadDefaults
from fretboard.cad.interface import ExportRequest
from fretboard.domain.presets import PRESET_FILE_VERSION, default_presets_path
from fretboard.errors import PresetError, ValidationError
from fretboard.geometry.inlays import inlay_recesses, marker_center_y, resolved_inlay_style
from fretboard.geometry.outline import width_at_distance
from fretboard.geometry.slots import fret_slot_centerlines
from fretboard.logging_utils import configure_logging, normalize_log_level
from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import Scale, equal_temperament
from fretboard.outputs.files import WORK_FOLDER_ENV, resolve_work_folder, sidecar_manifest_path



def _make_workspace_temp_dir() -> Path:
    base = Path(__file__).resolve().parents[1] / ".test_tmp"
    base.mkdir(exist_ok=True)
    path = base / str(uuid.uuid4())
    path.mkdir()
    return path



def test_fr_001_generate_output_writes_step_file() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        spec = resolve_spec("gibson_les_paul")
        output_path = generate_output(spec, work_folder=temp_dir)
        assert output_path.exists()
        assert output_path.suffix == ".step"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_fr_002_generate_output_writes_manifest_with_resolved_spec() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        spec = resolve_spec("gibson_les_paul")
        output_path = generate_output(spec, work_folder=temp_dir)
        manifest_path = sidecar_manifest_path(output_path)
        payload = json.loads(manifest_path.read_text())

        assert manifest_path.exists()
        assert payload["output_type"] == "fretboard_design_manifest"
        assert payload["spec"]["name"] == "Gibson Les Paul"
        assert payload["spec"]["units"] == "in"
        assert payload["spec"]["internal_units"] == "mm"
        assert payload["spec"]["slot_count"] == spec.geometry.num_frets
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_fr_003_internal_geometry_uses_millimeters() -> None:
    spec = resolve_spec("gibson_les_paul")
    assert math.isclose(spec.geometry.scale_length, 628.65, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(spec.geometry.fingerboard_width_at_nut, 43.053, rel_tol=0, abs_tol=1e-6)



def test_fr_004_invalid_required_inputs_are_rejected() -> None:
    invalid_overrides = [
        {"scale_length": 0},
        {"num_frets": 0},
        {"num_strings": 1},
        {"fingerboard_width_at_nut": 0},
        {"fingerboard_width_at_12th_fret": 0},
        {"fingerboard_radius": 0},
    ]

    for overrides in invalid_overrides:
        with pytest.raises(ValidationError):
            resolve_spec("gibson_les_paul", overrides=overrides)



def test_fr_005_built_in_preset_store_has_required_shape() -> None:
    payload = json.loads(default_presets_path().read_text())
    first = payload["presets"][0]

    assert payload["version"] == PRESET_FILE_VERSION
    assert isinstance(payload["presets"], list)
    assert {"id", "name", "units", "geometry", "metadata"}.issubset(first)



def test_fr_006_preset_lookup_supports_id_and_name() -> None:
    assert resolve_spec("gibson_les_paul").name == "Gibson Les Paul"
    assert resolve_spec("Gibson Les Paul").id == "gibson_les_paul"



def test_fr_007_editable_fields_preload_geometry_units_and_metadata() -> None:
    fields = editable_fields_from_preset("gibson_les_paul")

    assert fields["units"] == "in"
    assert fields["scale_length"] == 24.75
    assert fields["num_frets"] == 22
    assert fields["fingerboard_material"] == "Rosewood"
    assert fields["id"] == "gibson_les_paul"
    assert fields["source"] == "built_in"



def test_fr_008_display_unit_conversion_preserves_modeled_geometry() -> None:
    fields = editable_fields_from_preset("gibson_les_paul")
    converted = convert_display_fields(fields, "mm")
    overrides = {
        "units": converted["units"],
        "scale_length": converted["scale_length"],
        "fingerboard_width_at_nut": converted["fingerboard_width_at_nut"],
        "fingerboard_width_at_12th_fret": converted["fingerboard_width_at_12th_fret"],
        "fingerboard_radius": converted["fingerboard_radius"],
    }
    spec = resolve_spec("gibson_les_paul", overrides=overrides)

    assert converted["units"] == "mm"
    assert math.isclose(spec.geometry.scale_length, 628.65, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(spec.geometry.fingerboard_radius, 304.8, rel_tol=0, abs_tol=1e-6)



def test_fr_009_cli_overrides_use_selected_or_preset_units() -> None:
    spec_with_explicit_mm = resolve_spec(
        "gibson_les_paul",
        overrides={"units": "mm", "scale_length": 635.0},
    )
    spec_with_preset_units = resolve_spec(
        "gibson_les_paul",
        overrides={"scale_length": 25.0},
    )

    assert math.isclose(spec_with_explicit_mm.geometry.scale_length, 635.0, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(spec_with_preset_units.geometry.scale_length, 635.0, rel_tol=0, abs_tol=1e-6)



def test_fr_010_user_presets_are_separate_serialized_in_display_units_and_listed() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        user_path = temp_dir / "user_presets.json"
        spec = resolve_spec("gibson_les_paul", overrides={"units": "mm", "scale_length": 635.0}, user_path=user_path)
        saved = save_named_user_preset(spec, "My Custom LP", user_path=user_path)
        payload = json.loads(user_path.read_text())
        names = [preset.name for preset in available_presets(user_path=user_path)]

        assert saved.source == "user"
        assert payload["presets"][0]["units"] == "mm"
        assert payload["presets"][0]["geometry"]["scale_length"] == 635.0
        assert "My Custom LP" in names
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_fr_011_output_location_resolution_precedence(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        cwd_path = temp_dir / "cwd"
        env_path = temp_dir / "env"
        explicit_work_folder = temp_dir / "explicit"
        explicit_output = temp_dir / "named" / "chosen.step"
        cwd_path.mkdir()
        monkeypatch.chdir(cwd_path)
        monkeypatch.setenv(WORK_FOLDER_ENV, str(env_path))

        assert resolve_work_folder() == env_path
        assert resolve_work_folder(explicit_work_folder) == explicit_work_folder

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "generate",
                "--preset",
                "gibson_les_paul",
                "--work-folder",
                str(explicit_work_folder),
                "--output",
                str(explicit_output),
            ],
        )
        cli.main()
        output = json.loads(capsys.readouterr().out)
        assert Path(output["output"]) == explicit_output
        assert output["work_folder"] == str(explicit_output.parent)

        monkeypatch.delenv(WORK_FOLDER_ENV)
        assert resolve_work_folder() == cwd_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_fr_012_width_at_half_scale_matches_specified_twelfth_fret_width() -> None:
    spec = resolve_spec("gibson_les_paul")
    assert math.isclose(
        width_at_distance(spec, spec.geometry.scale_length / 2),
        spec.geometry.fingerboard_width_at_12th_fret,
        rel_tol=0,
        abs_tol=1e-6,
    )



def test_fr_013_board_length_extends_past_last_fret_by_default_extension() -> None:
    spec = resolve_spec("gibson_les_paul")
    defaults = CadDefaults()
    board_length = _board_length_mm(ExportRequest(spec=spec, output_path=Path("unused.step")), defaults)
    fret_positions = calculate_fret_positions(equal_temperament(), spec.geometry.scale_length, spec.geometry.num_frets)

    assert math.isclose(board_length, fret_positions[-1] + defaults.end_extension_mm, rel_tol=0, abs_tol=1e-6)



def test_fr_014_slot_definitions_include_required_cut_fields() -> None:
    spec = resolve_spec("gibson_les_paul")
    slots = fret_slot_centerlines(spec)
    first = slots[0]

    assert len(slots) == spec.geometry.num_frets
    assert first.position_y > 0
    assert math.isclose(first.start_y, first.end_y, rel_tol=0, abs_tol=1e-6)
    assert first.orientation_degrees == 0.0
    assert first.slot_depth > 0
    assert first.slot_width > 0



def test_fr_015_cli_supports_list_export_import_save_and_generate_without_ui(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        user_path = temp_dir / "user_presets.json"
        export_path = temp_dir / "gibson_les_paul.json"

        monkeypatch.setattr(sys, "argv", ["fretboard", "list-presets"])
        cli.main()
        assert "Gibson Les Paul" in capsys.readouterr().out

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "export-preset",
                "--preset",
                "gibson_les_paul",
                "--output",
                str(export_path),
            ],
        )
        cli.main()
        capsys.readouterr()
        assert export_path.exists()
        exported = json.loads(export_path.read_text())
        exported["name"] = "Stage LP Imported"
        exported["id"] = "stage_lp_imported"
        export_path.write_text(json.dumps(exported, indent=2) + "\n")

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "import-preset",
                "--input",
                str(export_path),
                "--user-presets",
                str(user_path),
            ],
        )
        cli.main()
        assert json.loads(capsys.readouterr().out)["imported_preset"] == "Stage LP Imported"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "save-preset",
                "--preset",
                "gibson_les_paul",
                "--save-preset-name",
                "Stage LP",
                "--user-presets",
                str(user_path),
            ],
        )
        cli.main()
        assert json.loads(capsys.readouterr().out)["saved_preset"] == "Stage LP"

        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "generate",
                "--preset",
                "Stage LP Imported",
                "--user-presets",
                str(user_path),
            ],
        )
        cli.main()
        output = json.loads(capsys.readouterr().out)
        assert Path(output["output"]).parent == temp_dir
        assert Path(output["output"]).exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def _render_streamlit_ui(monkeypatch, *, button_values=None, save_name=""):
    calls: list[tuple[str, object]] = []
    convert_calls: list[tuple[dict, str]] = []
    save_calls: list[tuple[str, str, bool]] = []
    generate_calls: list[str] = []

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}

        def title(self, value):
            calls.append(("title", value))

        def caption(self, value):
            calls.append(("caption", value))

        def subheader(self, value):
            calls.append(("subheader", value))

        def selectbox(self, label, options, key=None, index=0):
            if label == "Preset":
                value = options[index]
            elif label == "Units":
                value = "mm"
            else:
                value = options[index]
            if key is not None:
                self.session_state[key] = value
            calls.append(("selectbox", label))
            return value

        def write(self, value):
            calls.append(("write", value))

        def text_input(self, label, key=None):
            if key is not None:
                default = save_name if label == "Save As User Preset" else ""
                self.session_state.setdefault(key, default)
                value = self.session_state[key]
            else:
                value = save_name if label == "Save As User Preset" else ""
            calls.append(("text_input", label))
            return value

        def number_input(self, label, key=None, min_value=None):
            if key is not None:
                self.session_state.setdefault(key, 0)
                value = self.session_state[key]
            else:
                value = 0
            calls.append(("number_input", label))
            return value

        def button(self, label):
            calls.append(("button", label))
            return (button_values or {}).get(label, False)

        def success(self, value):
            calls.append(("success", value))

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setattr(
        "fretboard.app.available_presets",
        lambda user_path=None: [types.SimpleNamespace(name="Gibson Les Paul")],
    )
    monkeypatch.setattr(
        "fretboard.app.editable_fields_from_preset",
        lambda preset, user_path=None: {
            "source": "built_in",
            "name": "Gibson Les Paul",
            "units": "in",
            "scale_length": 24.75,
            "num_frets": 22,
            "num_strings": 6,
            "fingerboard_width_at_nut": 1.695,
            "fingerboard_width_at_12th_fret": 2.26,
            "fingerboard_radius": 12.0,
            "fingerboard_material": "Rosewood",
            "fret_material": "Nickel Silver",
            "nut_material": "Graph Tech",
            "inlay_material": "Acrylic",
            "inlay_style": "Trapezoid",
            "id": "gibson_les_paul",
        },
    )

    def _convert(fields, new_units):
        convert_calls.append((fields.copy(), new_units))
        return {
            **fields,
            "units": new_units,
            "scale_length": 628.65,
            "fingerboard_width_at_nut": 43.053,
            "fingerboard_width_at_12th_fret": 57.404,
            "fingerboard_radius": 304.8,
        }

    monkeypatch.setattr("fretboard.app.convert_display_fields", _convert)
    monkeypatch.setattr("fretboard.app.resolved_work_folder", lambda work_folder=None: Path("C:/tmp/work"))
    monkeypatch.setattr(
        "fretboard.app.resolve_spec",
        lambda preset, overrides=None, user_path=None: types.SimpleNamespace(name="Gibson Les Paul"),
    )
    monkeypatch.setattr(
        "fretboard.app.generate_output",
        lambda spec, output_path=None, work_folder=None: generate_calls.append(str(work_folder)) or Path("C:/tmp/work/out.step"),
    )

    def _save(spec, preset_name, user_path=None, overwrite=False):
        save_calls.append((spec.name, preset_name, overwrite))
        return types.SimpleNamespace(name=preset_name)

    monkeypatch.setattr("fretboard.app.save_named_user_preset", _save)

    sys.modules.pop("fretboard.ui.streamlit_app", None)
    importlib.import_module("fretboard.ui.streamlit_app")
    return fake_streamlit, calls, convert_calls, save_calls, generate_calls

def test_fr_016_streamlit_ui_separates_preset_context_from_editable_sections(monkeypatch) -> None:
    _, calls, _, _, _ = _render_streamlit_ui(monkeypatch)

    subheaders = [value for kind, value in calls if kind == "subheader"]
    assert subheaders[:3] == ["Preset", "Preset Status", "Work Folder"]
    assert "Core Geometry" in subheaders



def test_fr_017_streamlit_ui_groups_core_geometry_and_metadata_inputs(monkeypatch) -> None:
    _, calls, _, _, _ = _render_streamlit_ui(monkeypatch)

    subheaders = [value for kind, value in calls if kind == "subheader"]
    assert "Core Geometry" in subheaders
    assert "Metadata" in subheaders
    assert "User Preset" in subheaders



def test_fr_018_streamlit_ui_core_geometry_precedes_metadata(monkeypatch) -> None:
    _, calls, _, _, _ = _render_streamlit_ui(monkeypatch)

    sequence = [value for kind, value in calls if kind in {"subheader", "number_input"}]
    assert sequence.index("Core Geometry") < sequence.index("Scale Length")
    assert sequence.index("Fingerboard Radius") < sequence.index("Metadata")



def test_fr_019_streamlit_ui_shows_preset_source_and_work_folder_in_separate_sections(monkeypatch) -> None:
    _, calls, _, _, _ = _render_streamlit_ui(monkeypatch)

    writes = [value for kind, value in calls if kind == "write"]
    assert "Preset source: built_in" in writes
    assert "Preset id: gibson_les_paul" in writes
    assert any(value.startswith("Work folder:") for value in writes)

    subheaders = [value for kind, value in calls if kind == "subheader"]
    assert subheaders.index("Work Folder") < subheaders.index("Core Geometry")



def test_fr_020_streamlit_ui_places_generate_with_core_geometry(monkeypatch) -> None:
    _, calls, _, _, _ = _render_streamlit_ui(monkeypatch)

    sequence = [value for kind, value in calls if kind in {"subheader", "button"}]
    assert sequence.index("Core Geometry") < sequence.index("Generate")
    assert sequence.index("Generate") < sequence.index("Metadata")



def test_fr_021_streamlit_ui_converts_display_state_when_units_change(monkeypatch) -> None:
    fake_streamlit, calls, convert_calls, _, _ = _render_streamlit_ui(monkeypatch)

    assert ("selectbox", "Preset") in calls
    assert ("selectbox", "Units") in calls
    assert fake_streamlit.session_state["fb_scale_length"] == 628.65
    assert convert_calls and convert_calls[0][1] == "mm"



def test_fr_022_streamlit_ui_preloads_editable_fields_into_session_state(monkeypatch) -> None:
    fake_streamlit, _, _, _, _ = _render_streamlit_ui(monkeypatch)

    assert fake_streamlit.session_state["fb_name"] == "Gibson Les Paul"
    assert fake_streamlit.session_state["fb_num_frets"] == 22
    assert fake_streamlit.session_state["fb_fingerboard_material"] == "Rosewood"
    assert fake_streamlit.session_state["fb_inlay_style"] == "Trapezoid"



def test_fr_023_streamlit_ui_saves_user_preset_from_separate_section(monkeypatch) -> None:
    _, calls, _, save_calls, generate_calls = _render_streamlit_ui(
        monkeypatch,
        button_values={"Save User Preset": True},
        save_name="Stage LP",
    )

    sequence = [value for kind, value in calls if kind in {"subheader", "button"}]
    assert sequence.index("Metadata") < sequence.index("User Preset")
    assert sequence.index("User Preset") < sequence.index("Save User Preset")
    assert save_calls == [("Gibson Les Paul", "Stage LP", True)]
    assert generate_calls == []



def test_fr_024_scale_utilities_support_equal_temperament_and_explicit_scales() -> None:
    equal = equal_temperament(12)
    scala = Scale().from_scala_string("""Test scale
3
100.0
3/2
2/1
""")

    equal_positions = calculate_fret_positions(equal, 628.65, 3)
    scala_positions = calculate_fret_positions(scala, 628.65, 3)

    assert equal.errors == []
    assert scala.errors == []
    assert equal_positions[0] == 0.0
    assert scala_positions[0] == 0.0
    assert scala_positions[-1] < 628.65



def test_fr_025_logging_supports_standard_levels_and_cli_configuration(monkeypatch) -> None:
    assert normalize_log_level("DEBUG") == logging.DEBUG
    assert normalize_log_level("INFO") == logging.INFO
    assert normalize_log_level("WARNING") == logging.WARNING
    assert normalize_log_level("ERROR") == logging.ERROR

    monkeypatch.setenv("FRETBOARD_LOG_LEVEL", "WARNING")
    assert configure_logging() == logging.WARNING
    assert logging.getLogger().level == logging.WARNING

    monkeypatch.setattr(cli, "_print_preset_list", lambda user_path: None)
    monkeypatch.setattr(sys, "argv", ["fretboard", "--log-level", "DEBUG", "list-presets"])
    cli.main()
    assert logging.getLogger().level == logging.DEBUG





def test_fr_026_cli_exports_standalone_single_preset_json() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "exported.json"
        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())

        assert payload["id"] == "gibson_les_paul"
        assert payload["name"] == "Gibson Les Paul"
        assert payload["units"] == "in"
        assert "geometry" in payload
        assert "metadata" in payload
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_027_cli_imports_standalone_preset_into_user_store() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "import_me.json"
        user_path = temp_dir / "user_presets.json"
        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())
        payload["name"] = "Imported Workshop LP"
        payload["id"] = "imported_workshop_lp"
        payload["units"] = "mm"
        payload["geometry"]["scale_length"] = 635.0
        export_path.write_text(json.dumps(payload, indent=2) + "\n")

        imported = import_preset_file(export_path, user_path=user_path)
        store = json.loads(user_path.read_text())

        assert imported.name == "Imported Workshop LP"
        assert store["presets"][0]["name"] == "Imported Workshop LP"
        assert store["presets"][0]["units"] == "mm"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_028_imported_presets_are_selectable_by_name() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "import_me.json"
        user_path = temp_dir / "user_presets.json"
        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())
        payload["name"] = "Imported Name Lookup"
        payload["id"] = "imported_name_lookup"
        export_path.write_text(json.dumps(payload, indent=2) + "\n")

        import_preset_file(export_path, user_path=user_path)
        resolved = resolve_spec("Imported Name Lookup", user_path=user_path)

        assert resolved.id == "imported_name_lookup"
        assert resolved.name == "Imported Name Lookup"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_029_cli_lists_all_available_preset_names(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "import_me.json"
        user_path = temp_dir / "user_presets.json"
        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())
        payload["name"] = "Listed Imported LP"
        payload["id"] = "listed_imported_lp"
        export_path.write_text(json.dumps(payload, indent=2) + "\n")
        import_preset_file(export_path, user_path=user_path)

        monkeypatch.setattr(sys, "argv", ["fretboard", "list-presets", "--user-presets", str(user_path)])
        cli.main()
        lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]

        assert "Gibson Les Paul" in lines
        assert "Listed Imported LP" in lines
        assert all("\t" not in line for line in lines)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_030_cli_generate_accepts_explicit_output_file_path(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        output_path = temp_dir / "named" / "custom.step"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "fretboard",
                "generate",
                "--preset",
                "gibson_les_paul",
                "--output",
                str(output_path),
            ],
        )
        cli.main()
        payload = json.loads(capsys.readouterr().out)

        assert Path(payload["output"]) == output_path
        assert output_path.exists()
        assert payload["work_folder"] == str(output_path.parent)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_031_standalone_preset_json_contains_recreation_fields() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "exported.json"
        export_named_preset("gibson_les_paul", export_path)
        payload = json.loads(export_path.read_text())

        assert set(payload) == {"id", "name", "units", "geometry", "metadata"}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_fr_032_imported_preset_json_is_validated() -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        invalid_path = temp_dir / "invalid.json"
        invalid_path.write_text(json.dumps({"name": "Broken"}, indent=2) + "\n")

        with pytest.raises(PresetError):
            import_preset_file(invalid_path, user_path=temp_dir / "user_presets.json")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_fr_033_inlay_recesses_are_generated_at_standard_marker_positions() -> None:
    spec = resolve_spec("gibson_les_paul")
    recesses = inlay_recesses(spec)
    positions = calculate_fret_positions(equal_temperament(), spec.geometry.scale_length, spec.geometry.num_frets)
    expected_marker_frets = [3, 5, 7, 9, 12, 15, 17, 19, 21]

    assert sorted(set(recess.fret_number for recess in recesses)) == expected_marker_frets

    for fret_number in expected_marker_frets:
        expected_y = marker_center_y(positions, fret_number)
        marker_recesses = [recess for recess in recesses if recess.fret_number == fret_number]

        assert marker_recesses
        assert all(math.isclose(recess.center_y, expected_y, rel_tol=0, abs_tol=1e-6) for recess in marker_recesses)


def test_fr_034_non_dot_inlay_styles_fall_back_to_dot_geometry() -> None:
    gibson_spec = resolve_spec("gibson_les_paul")
    prs_spec = resolve_spec("prs_custom_24")

    assert resolved_inlay_style("Dot") == "dot"
    assert resolved_inlay_style("Trapezoid") == "dot"
    assert resolved_inlay_style("Birds") == "dot"
    assert all(recess.style == "dot" for recess in inlay_recesses(gibson_spec))
    assert all(recess.style == "dot" for recess in inlay_recesses(prs_spec))


def test_fr_035_single_dot_markers_share_one_diameter() -> None:
    spec = resolve_spec("fender_stratocaster")
    recesses = [recess for recess in inlay_recesses(spec) if recess.fret_number != 12]

    assert recesses
    assert {recess.diameter for recess in recesses} == {CadDefaults().inlay_dot_diameter_mm}


def test_fr_036_octave_marker_uses_two_matching_dots() -> None:
    spec = resolve_spec("fender_stratocaster")
    octave_recesses = [recess for recess in inlay_recesses(spec) if recess.fret_number == 12]

    assert len(octave_recesses) == 2
    assert math.isclose(octave_recesses[0].diameter, octave_recesses[1].diameter, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(octave_recesses[0].center_y, octave_recesses[1].center_y, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(octave_recesses[0].center_x, -octave_recesses[1].center_x, rel_tol=0, abs_tol=1e-6)


def test_fr_037_inlay_cad_uses_circle_profile_and_subtractive_extrusion() -> None:
    defaults = CadDefaults()
    spec = resolve_spec("fender_stratocaster")
    profile = _build_dot_inlay_profile(defaults.inlay_dot_diameter_mm)
    cut = _extrude_inlay_profile(profile, inlay_recesses(spec)[0], defaults.fingerboard_thickness_mm)
    bbox = cut.bounding_box()

    assert math.isclose(bbox.max.X - bbox.min.X, defaults.inlay_dot_diameter_mm, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(bbox.max.Y - bbox.min.Y, defaults.inlay_dot_diameter_mm, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(bbox.max.Z, defaults.fingerboard_thickness_mm, rel_tol=0, abs_tol=1e-6)


def test_fr_038_inlay_depth_is_five_mm_at_crown_apex() -> None:
    defaults = CadDefaults()
    spec = resolve_spec("fender_stratocaster")
    profile = _build_dot_inlay_profile(defaults.inlay_dot_diameter_mm)
    cut = _extrude_inlay_profile(profile, inlay_recesses(spec)[0], defaults.fingerboard_thickness_mm)
    bbox = cut.bounding_box()

    assert math.isclose(bbox.max.Z - bbox.min.Z, defaults.inlay_depth_mm, rel_tol=0, abs_tol=1e-6)
    assert math.isclose(bbox.min.Z, defaults.fingerboard_thickness_mm - defaults.inlay_depth_mm, rel_tol=0, abs_tol=1e-6)


def test_fr_039_inlay_profile_creation_is_separate_from_extrusion(monkeypatch) -> None:
    request = ExportRequest(spec=resolve_spec("gibson_les_paul"), output_path=Path("unused.step"))
    defaults = CadDefaults()
    calls: list[tuple] = []

    def fake_profile_builder(diameter):
        calls.append(("profile", diameter))
        return f"profile-{diameter}"

    def fake_resolver(style):
        calls.append(("resolve", style))
        return fake_profile_builder

    def fake_extrude(profile, recess, top_surface_z):
        calls.append(("extrude", profile, recess.fret_number, top_surface_z))
        return (profile, recess.fret_number)

    monkeypatch.setattr(build123d_backend, "_resolve_inlay_profile_builder", fake_resolver)
    monkeypatch.setattr(build123d_backend, "_extrude_inlay_profile", fake_extrude)

    cut_parts = build_inlay_cut_parts(request, defaults, top_surface_z=defaults.fingerboard_thickness_mm)

    assert cut_parts
    assert calls[0] == ("resolve", "Trapezoid")
    profile_calls = [call for call in calls if call[0] == "profile"]
    extrude_calls = [call for call in calls if call[0] == "extrude"]
    assert len(profile_calls) == len(extrude_calls) == len(cut_parts)
    assert all(call[1].startswith("profile-") for call in extrude_calls)
