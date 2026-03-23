INTERNAL_UNITS = "mm"
DEFAULT_UNITS = "mm"
SUPPORTED_UNITS = {"in", "mm"}
INCH_TO_MM = 25.4
DIMENSION_FIELDS = {
    "scale_length",
    "fingerboard_width_at_nut",
    "fingerboard_width_at_12th_fret",
    "fingerboard_radius",
    "fingerboard_width_at_scale",
}



def validate_units(units: str) -> None:
    if units not in SUPPORTED_UNITS:
        raise ValueError(f"Unsupported units: {units}")



def to_internal_length(value: float, units: str) -> float:
    validate_units(units)
    if units == INTERNAL_UNITS:
        return float(value)
    return float(value) * INCH_TO_MM



def from_internal_length(value_mm: float, units: str) -> float:
    validate_units(units)
    if units == INTERNAL_UNITS:
        return float(value_mm)
    return float(value_mm) / INCH_TO_MM



def convert_dimension_dict(data: dict, from_units: str, to_units: str) -> dict:
    validate_units(from_units)
    validate_units(to_units)
    if from_units == to_units:
        return data.copy()

    converted = data.copy()
    for field in DIMENSION_FIELDS:
        if field in converted and converted[field] is not None:
            internal_value = to_internal_length(converted[field], from_units)
            converted[field] = from_internal_length(internal_value, to_units)
    return converted



def round_display(value: float) -> float:
    return round(float(value), 6)
