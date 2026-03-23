import json
import shutil
import uuid
from pathlib import Path

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

    positions = calculate_fret_positions(equal_temperament(), 25.5, 22)
    assert positions[0] == 0.0
    assert positions[1] > 0.0
    assert positions[-1] < 25.5



def test_cli_lists_presets(capsys, monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["fretboard", "list-presets"])
    cli.main()
    out = capsys.readouterr().out
    assert "gibson_les_paul" in out
    assert "Gibson Les Paul" in out



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
                "--scale-length",
                "25.0",
                "--save-preset-name",
                "Workshop LP",
                "--user-presets",
                str(user_path),
            ],
        )

        cli.main()

        out = json.loads(capsys.readouterr().out)
        assert out["saved_preset"] == "Workshop LP"
        payload = json.loads(user_path.read_text())
        assert payload["presets"][0]["name"] == "Workshop LP"
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
                "--num-frets",
                "24",
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
        assert out["summary"]["geometry"]["num_frets"] == 24
        payload = json.loads(user_path.read_text())
        assert payload["presets"][0]["name"] == "Stage LP"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
