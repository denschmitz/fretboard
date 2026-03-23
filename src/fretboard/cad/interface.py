from dataclasses import dataclass
from pathlib import Path

from fretboard.domain.models import FretboardSpec


@dataclass(frozen=True)
class ExportRequest:
    spec: FretboardSpec
    output_path: Path


class CadBackend:
    name = "unconfigured"

    def export_step(self, request: ExportRequest) -> Path:
        raise NotImplementedError
