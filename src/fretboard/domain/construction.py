from fretboard.cad.defaults import CadDefaults

from .models import ConstructionParameters, FretboardSpec


def resolve_construction(spec: FretboardSpec) -> ConstructionParameters:
    defaults = CadDefaults()
    construction = spec.construction
    return ConstructionParameters(
        fingerboard_thickness=(
            construction.fingerboard_thickness
            if construction.fingerboard_thickness is not None
            else defaults.compatibility_fingerboard_thickness_mm
        ),
        board_end_extension=(
            construction.board_end_extension
            if construction.board_end_extension is not None
            else defaults.compatibility_board_end_extension_mm
        ),
        edge_fillet=construction.edge_fillet if construction.edge_fillet is not None else 0.0,
    )
