class FretboardError(Exception):
    """Base exception for project-specific failures."""


class PresetError(FretboardError):
    """Raised when preset data is missing or invalid."""


class ValidationError(FretboardError):
    """Raised when a design specification fails validation."""


class ExportNotImplementedError(FretboardError):
    """Raised when a requested CAD/export backend is not implemented."""
