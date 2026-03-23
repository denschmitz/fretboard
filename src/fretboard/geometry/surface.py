from dataclasses import dataclass

from fretboard.domain.models import FretboardSpec


@dataclass(frozen=True)
class CylindricalSurfaceDefinition:
    radius: float



def top_surface(spec: FretboardSpec) -> CylindricalSurfaceDefinition:
    return CylindricalSurfaceDefinition(radius=spec.geometry.fingerboard_radius)
