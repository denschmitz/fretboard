from pathlib import Path

from fretboard.cad.build123d_backend import Build123dStepBackend
from fretboard.cad.interface import ExportRequest


class StepExportBackend(Build123dStepBackend):
    def export_step(self, request: ExportRequest) -> Path:
        return super().export_step(request)
