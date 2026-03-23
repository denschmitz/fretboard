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



def test_cli_lists_presets(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["fretboard", "list-presets"])
    cli.main()
    out = capsys.readouterr().out
    assert "gibson_les_paul" in out
    assert "preferred_display=in" in out



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



def test_cli_generate_writes_output_to_current_directory_and_can_save_user_preset(
    capsys,
    monkeypatch,
) -> None:
    temp_dir = _make_workspace_temp_dir()
    try:
        user_path = temp_dir / "user_presets.json"
        monkeypatch.chdir(temp_dir)
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
                "--save-preset-name",
                "Stage LP",
                "--user-presets",
                str(user_path),
            ],
        )

        cli.main()

        out = json.loads(capsys.readouterr().out)
        output_path = Path(out["output"])
        assert output_path.parent == temp_dir
        assert output_path.exists()
        assert out["summary"]["name"] == "Stage LP"
        assert out["summary"]["units"] == "mm"
        assert out["summary"]["geometry"]["num_frets"] == 24
        assert out["summary"]["geometry"]["scale_length"] == 635.0
        payload = json.loads(user_path.read_text())
        assert payload["presets"][0]["name"] == "Stage LP"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def test_streamlit_module_executes_main(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakeForm:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_streamlit = types.SimpleNamespace(
        session_state={},
        title=lambda value: calls.append(("title", value)),
        caption=lambda value: calls.append(("caption", value)),
        selectbox=lambda label, options, key=None, index=0: options[index],
        write=lambda value: calls.append(("write", value)),
        text_input=lambda label, key=None: "",
        number_input=lambda label, key=None, min_value=None: 0,
        button=lambda label: False,
        success=lambda value: calls.append(("success", value)),
    )

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
