from pathlib import Path

from fretboard.app import (
    available_presets,
    available_slotting_profiles,
    convert_display_fields,
    editable_fields_from_preset,
    generate_output,
    resolve_spec,
    resolved_work_folder,
    save_named_user_preset,
)
from fretboard.domain.slotting import resolve_slotting
from fretboard.errors import ValidationError
from fretboard.logging_utils import configure_logging, get_logger
from fretboard.units import from_internal_length, round_display


USER_PRESET_PATH = Path(__file__).resolve().parents[3] / "presets" / "user_presets.json"
FIELD_KEYS = [
    "name",
    "units",
    "scale_length",
    "num_frets",
    "num_strings",
    "fingerboard_width_at_nut",
    "fingerboard_width_at_12th_fret",
    "fingerboard_width_at_end",
    "fingerboard_radius",
    "fingerboard_thickness",
    "board_end_extension",
    "edge_fillet",
    "wire_profile_id",
    "fit_profile_id",
    "slot_width",
    "slot_depth",
    "tang_offset",
    "fingerboard_material",
    "fret_material",
    "nut_material",
    "inlay_material",
    "inlay_style",
    "display_notes",
    "era",
    "label",
    "source",
    "id",
]

logger = get_logger(__name__)


def _state_key(field: str) -> str:
    return f"fb_{field}"


def _show_error(st, message: str) -> None:
    if hasattr(st, "error"):
        st.error(message)
    else:
        st.write(message)


def _optional_float(value):
    return None if value in ("", None) else float(value)


def _optional_text(value):
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _load_preset_into_state(st, preset_name: str) -> None:
    fields = editable_fields_from_preset(preset_name, user_path=USER_PRESET_PATH)
    for key in FIELD_KEYS:
        st.session_state[_state_key(key)] = fields.get(key)
    st.session_state["fb_loaded_preset"] = preset_name
    st.session_state["fb_previous_units"] = fields["units"]
    st.session_state["fb_manual_slotting_override"] = any(
        fields.get(field) is not None for field in ("slot_width", "slot_depth", "tang_offset")
    )
    logger.debug("Loaded preset %s into UI state", preset_name)


def _snapshot_fields(st) -> dict:
    return {key: st.session_state.get(_state_key(key)) for key in FIELD_KEYS}


def _build_overrides(st) -> dict:
    overrides = {
        "name": st.session_state.get(_state_key("name")),
        "units": st.session_state.get(_state_key("units")),
        "scale_length": float(st.session_state.get(_state_key("scale_length"))),
        "num_frets": int(st.session_state.get(_state_key("num_frets"))),
        "num_strings": int(st.session_state.get(_state_key("num_strings"))),
        "fingerboard_width_at_nut": float(st.session_state.get(_state_key("fingerboard_width_at_nut"))),
        "fingerboard_width_at_12th_fret": _optional_float(st.session_state.get(_state_key("fingerboard_width_at_12th_fret"))),
        "fingerboard_width_at_end": _optional_float(st.session_state.get(_state_key("fingerboard_width_at_end"))),
        "fingerboard_radius": float(st.session_state.get(_state_key("fingerboard_radius"))),
        "fingerboard_thickness": _optional_float(st.session_state.get(_state_key("fingerboard_thickness"))),
        "board_end_extension": _optional_float(st.session_state.get(_state_key("board_end_extension"))),
        "edge_fillet": _optional_float(st.session_state.get(_state_key("edge_fillet"))),
        "wire_profile_id": _optional_text(st.session_state.get(_state_key("wire_profile_id"))),
        "fit_profile_id": _optional_text(st.session_state.get(_state_key("fit_profile_id"))),
        "fingerboard_material": _optional_text(st.session_state.get(_state_key("fingerboard_material"))),
        "fret_material": _optional_text(st.session_state.get(_state_key("fret_material"))),
        "nut_material": _optional_text(st.session_state.get(_state_key("nut_material"))),
        "inlay_material": _optional_text(st.session_state.get(_state_key("inlay_material"))),
        "inlay_style": _optional_text(st.session_state.get(_state_key("inlay_style"))),
        "display_notes": _optional_text(st.session_state.get(_state_key("display_notes"))),
        "era": _optional_text(st.session_state.get(_state_key("era"))),
        "label": _optional_text(st.session_state.get(_state_key("label"))),
    }
    if st.session_state.get("fb_manual_slotting_override"):
        overrides["slot_width"] = _optional_float(st.session_state.get(_state_key("slot_width")))
        overrides["slot_depth"] = _optional_float(st.session_state.get(_state_key("slot_depth")))
        overrides["tang_offset"] = _optional_float(st.session_state.get(_state_key("tang_offset")))
    else:
        overrides["slot_width"] = None
        overrides["slot_depth"] = None
        overrides["tang_offset"] = None
    return overrides


def main() -> None:
    configure_logging()
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not installed. Install the project with the `ui` extra, for example `python -m pip install -e .[ui]`."
        ) from exc

    st.title("Fretboard Generator")
    st.caption("Preset-driven fretboard generation with geometry, construction, slotting, and metadata controls.")

    presets = available_presets(user_path=USER_PRESET_PATH)
    preset_names = [preset.name for preset in presets]
    profile_store = available_slotting_profiles(user_path=USER_PRESET_PATH)
    wire_profile_ids = [profile.id for profile in profile_store["wire_profiles"]]
    fit_profile_ids = [profile.id for profile in profile_store["fit_profiles"]]

    st.subheader("Preset")
    selected_name = st.selectbox("Preset", preset_names, key="fb_selected_preset")

    if st.session_state.get("fb_loaded_preset") != selected_name:
        _load_preset_into_state(st, selected_name)

    st.subheader("Preset Status")
    units = st.selectbox("Units", ["in", "mm"], key=_state_key("units"))
    previous_units = st.session_state.get("fb_previous_units", units)
    if units != previous_units:
        converted = convert_display_fields(_snapshot_fields(st), units)
        for field in FIELD_KEYS:
            if field in converted:
                st.session_state[_state_key(field)] = converted[field]
        st.session_state["fb_previous_units"] = units
        logger.info("Converted UI display units from %s to %s", previous_units, units)

    st.write(f"Preset source: {st.session_state.get(_state_key('source'))}")
    st.write(f"Preset id: {st.session_state.get(_state_key('id'))}")

    st.subheader("Work Folder")
    st.write(f"Work folder: {resolved_work_folder()}")

    st.subheader("Core Geometry")
    st.text_input("Name", key=_state_key("name"))
    st.number_input("Scale Length", key=_state_key("scale_length"))
    st.number_input("Number of Frets", min_value=1, key=_state_key("num_frets"))
    st.number_input("Number of Strings", min_value=2, key=_state_key("num_strings"))
    st.number_input("Fingerboard Width At Nut", key=_state_key("fingerboard_width_at_nut"))
    st.number_input("Fingerboard Width At 12th Fret", key=_state_key("fingerboard_width_at_12th_fret"))
    st.number_input("Fingerboard Width At End", key=_state_key("fingerboard_width_at_end"))
    st.number_input("Fingerboard Radius", key=_state_key("fingerboard_radius"))
    generate_requested = st.button("Generate")

    st.subheader("Construction")
    st.number_input("Fingerboard Thickness", key=_state_key("fingerboard_thickness"))
    st.number_input("Board End Extension", key=_state_key("board_end_extension"))
    st.number_input("Edge Fillet", min_value=0.0, key=_state_key("edge_fillet"))

    st.subheader("Slotting")
    wire_index = wire_profile_ids.index(st.session_state.get(_state_key("wire_profile_id"))) if st.session_state.get(_state_key("wire_profile_id")) in wire_profile_ids else 0
    fit_index = fit_profile_ids.index(st.session_state.get(_state_key("fit_profile_id"))) if st.session_state.get(_state_key("fit_profile_id")) in fit_profile_ids else 0
    st.selectbox("Wire Profile", wire_profile_ids, index=wire_index, key=_state_key("wire_profile_id"))
    st.selectbox("Fit Profile", fit_profile_ids, index=fit_index, key=_state_key("fit_profile_id"))
    if hasattr(st, "checkbox"):
        st.checkbox("Enable Manual Slot Overrides", key="fb_manual_slotting_override")
    else:
        st.session_state.setdefault("fb_manual_slotting_override", False)
    if st.session_state.get("fb_manual_slotting_override"):
        st.number_input("Slot Width Override", key=_state_key("slot_width"))
        st.number_input("Slot Depth Override", key=_state_key("slot_depth"))
        st.number_input("Tang Offset Override", min_value=0.0, key=_state_key("tang_offset"))

    validation_error = None
    preview_spec = None
    try:
        preview_spec = resolve_spec(selected_name, overrides=_build_overrides(st), user_path=USER_PRESET_PATH)
        resolved_slotting = resolve_slotting(
            preview_spec,
            wire_profiles=profile_store["wire_profiles"],
            fit_profiles=profile_store["fit_profiles"],
        )
        st.write(
            f"Resolved slot width: {round_display(from_internal_length(resolved_slotting.resolved_slot_width, units))} {units}"
        )
        st.write(
            f"Resolved slot depth: {round_display(from_internal_length(resolved_slotting.resolved_slot_depth, units))} {units}"
        )
    except ValidationError as exc:
        validation_error = str(exc)
        _show_error(st, f"Slotting validation: {validation_error}")

    st.subheader("Metadata")
    st.text_input("Fingerboard Material", key=_state_key("fingerboard_material"))
    st.text_input("Fret Material", key=_state_key("fret_material"))
    st.text_input("Nut Material", key=_state_key("nut_material"))
    st.text_input("Inlay Material", key=_state_key("inlay_material"))
    st.text_input("Inlay Style", key=_state_key("inlay_style"))
    st.text_input("Display Notes", key=_state_key("display_notes"))
    st.text_input("Era", key=_state_key("era"))
    st.text_input("Label", key=_state_key("label"))

    st.subheader("User Preset")
    save_preset_name = st.text_input("Save As User Preset")
    save_requested = st.button("Save User Preset")

    if save_requested:
        if not save_preset_name.strip():
            st.write("Enter a user preset name to save the current parameter set.")
        elif validation_error is not None:
            _show_error(st, validation_error)
        else:
            save_spec = resolve_spec(selected_name, overrides=_build_overrides(st), user_path=USER_PRESET_PATH)
            save_named_user_preset(save_spec, save_preset_name.strip(), user_path=USER_PRESET_PATH, overwrite=True)
            st.success(f"Saved user preset: {save_preset_name.strip()}")

    if not generate_requested:
        return

    if validation_error is not None:
        _show_error(st, validation_error)
        return

    logger.info("UI generation requested for preset %s", selected_name)
    spec = preview_spec or resolve_spec(selected_name, overrides=_build_overrides(st), user_path=USER_PRESET_PATH)
    output_path = generate_output(spec, work_folder=resolved_work_folder())
    st.success(f"Generated output: {output_path}")


main()
