from pathlib import Path

from fretboard.cad.interface import CadBackend, ExportRequest
from fretboard.errors import ExportNotImplementedError


class StepExportBackend(CadBackend):
    name = "placeholder"

    def export_step(self, request: ExportRequest) -> Path:
        raise ExportNotImplementedError(
            "STEP export backend is not implemented yet. The project is now structured so "
            "a scripted CAD backend can be added without reworking presets, math, or CLI layers."
        )
