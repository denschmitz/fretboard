import json
import re
from pathlib import Path

from fretboard.domain.models import FretboardSpec



def _slugify_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "fretboard"



def default_output_path(spec: FretboardSpec, output_dir: Path | None = None) -> Path:
    directory = output_dir or Path.cwd()
    filename = f"{_slugify_filename(spec.name)}.fretboard.json"
    return directory / filename



def write_design_output(
    summary: dict,
    spec: FretboardSpec,
    *,
    output_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    target_path = output_path or default_output_path(spec, output_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "output_type": "fretboard_design_manifest",
        "spec": summary,
    }
    target_path.write_text(json.dumps(payload, indent=2) + "\n")
    return target_path
