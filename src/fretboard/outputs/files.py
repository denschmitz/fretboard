import json
import os
import re
from pathlib import Path

from fretboard.domain.models import FretboardSpec
from fretboard.logging_utils import get_logger


WORK_FOLDER_ENV = "FRETBOARD_WORK_FOLDER"

logger = get_logger(__name__)


def _slugify_filename(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "fretboard"



def resolve_work_folder(work_folder: Path | None = None) -> Path:
    if work_folder is not None:
        resolved = work_folder
    else:
        env_value = os.environ.get(WORK_FOLDER_ENV)
        resolved = Path(env_value) if env_value else Path.cwd()
    resolved.mkdir(parents=True, exist_ok=True)
    logger.debug("Resolved work folder %s", resolved)
    return resolved



def default_step_output_path(spec: FretboardSpec, work_folder: Path | None = None) -> Path:
    directory = resolve_work_folder(work_folder)
    filename = f"{_slugify_filename(spec.name)}.step"
    return directory / filename



def sidecar_manifest_path(step_path: Path) -> Path:
    return step_path.with_suffix(".fretboard.json")



def write_design_output(summary: dict, step_path: Path) -> Path:
    target_path = sidecar_manifest_path(step_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "output_type": "fretboard_design_manifest",
        "step_file": str(step_path),
        "spec": summary,
    }
    target_path.write_text(json.dumps(payload, indent=2) + "\n")
    logger.info("Wrote manifest to %s", target_path)
    return target_path
