import json
import shutil
import uuid
from pathlib import Path
import types

from fretboard import cli



def _make_workspace_temp_dir() -> Path:
    base = Path(__file__).resolve().parents[1] / ".test_tmp"
    base.mkdir(exist_ok=True)
    path = base / str(uuid.uuid4())
    path.mkdir()
    return path



def test_equal_temperament_starts_at_zero() -> None:
    from fretboard.music.fret_positions import calculate_fret_positions
    from fretboard.music.scales import equal_temperament

    positions = calculate_fret_positions(equal_temperament(), 25.5 * 25.4, 22)
    assert positions[0] == 0.0
    assert positions[1] > 0.0
    assert positions[-1] < 25.5 * 25.4



def test_cli_lists_preset_names(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["fretboard", "list-presets"])
    cli.main()
    out_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert "Gibson Les Paul" in out_lines
    assert all("	" not in line for line in out_lines)



def test_cli_save_preset_command(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        user_path = temp_dir / "user_presets.json"
        monkeypatch.setattr(
            "sys.argv",
            [
                "fretboard",
                "save-preset",
                "--preset",
                "gibson_les_paul",
                "--units",
                "mm",
                "--scale-length",
                "635.0",
                "--save-preset-name",
                "Workshop LP",
                "--user-presets",
                str(user_path),
            ],
        )

        cli.main()

        out = json.loads(capsys.readouterr().out)
        assert out["saved_preset"] == "Workshop LP"
        assert out["units"] == "mm"
        payload = json.loads(user_path.read_text())
        assert payload["presets"][0]["name"] == "Workshop LP"
        assert payload["presets"][0]["geometry"]["scale_length"] == 635.0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_cli_exports_imports_and_lists_user_presets(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        export_path = temp_dir / "gibson_lp.json"
        user_path = temp_dir / "user_presets.json"

        monkeypatch.setattr(
            "sys.argv",
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
        exported = json.loads(export_path.read_text())
        exported["name"] = "Workshop LP Imported"
        exported["id"] = "workshop_lp_imported"
        exported["geometry"]["scale_length"] = 25.0
        export_path.write_text(json.dumps(exported, indent=2) + "\n")

        monkeypatch.setattr(
            "sys.argv",
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
        out = json.loads(capsys.readouterr().out)
        assert out["imported_preset"] == "Workshop LP Imported"

        monkeypatch.setattr(
            "sys.argv",
            [
                "fretboard",
                "list-presets",
                "--user-presets",
                str(user_path),
            ],
        )
        cli.main()
        out_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert "Workshop LP Imported" in out_lines

        monkeypatch.setattr(
            "sys.argv",
            [
                "fretboard",
                "generate",
                "--preset",
                "Workshop LP Imported",
                "--user-presets",
                str(user_path),
                "--output",
                str(temp_dir / "custom-output.step"),
            ],
        )
        cli.main()
        generated = json.loads(capsys.readouterr().out)
        assert Path(generated["output"]).name == "custom-output.step"
        assert Path(generated["output"]).exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_cli_generate_writes_step_to_explicit_output_path(capsys, monkeypatch) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        output_path = temp_dir / "named-output.step"
        monkeypatch.setattr(
            "sys.argv",
            [
                "fretboard",
                "generate",
                "--preset",
                "gibson_les_paul",
                "--units",
                "mm",
                "--num-frets",
                "24",
                "--scale-length",
                "635.0",
                "--output",
                str(output_path),
            ],
        )

        cli.main()

        out = json.loads(capsys.readouterr().out)
        assert Path(out["output"]) == output_path
        assert output_path.exists()
        assert out["work_folder"] == str(temp_dir)
        assert out["summary"]["name"] == "Gibson Les Paul"
        assert out["summary"]["units"] == "mm"
        assert out["summary"]["geometry"]["num_frets"] == 24
        assert out["summary"]["geometry"]["scale_length"] == 635.0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_streamlit_module_executes_main(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

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
            value = options[index]
            if key is not None:
                self.session_state[key] = value
            return value

        def write(self, value):
            calls.append(("write", value))

        def text_input(self, label, key=None):
            if key is not None:
                self.session_state.setdefault(key, "")
                return self.session_state[key]
            return ""

        def number_input(self, label, key=None, min_value=None):
            if key is not None:
                self.session_state.setdefault(key, 0)
                return self.session_state[key]
            return 0

        def button(self, label):
            return False

        def success(self, value):
            calls.append(("success", value))

    fake_streamlit = FakeStreamlit()

    import sys
    import importlib

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setattr("fretboard.app.available_presets", lambda user_path=None: [types.SimpleNamespace(name="Gibson Les Paul")])
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
    monkeypatch.setattr("fretboard.app.convert_display_fields", lambda fields, new_units: {**fields, "units": new_units})

    import fretboard.ui.streamlit_app

    importlib.reload(fretboard.ui.streamlit_app)

    assert any(name == "title" for name, _ in calls)
