from pathlib import Path

from fretboard.app import (
    available_presets,
    convert_display_fields,
    editable_fields_from_preset,
    generate_output,
    resolve_spec,
    resolved_work_folder,
    save_named_user_preset,
)
from fretboard.logging_utils import configure_logging, get_logger


USER_PRESET_PATH = Path(__file__).resolve().parents[3] / "presets" / "user_presets.json"
FIELD_KEYS = [
    "name",
    "units",
    "scale_length",
    "num_frets",
    "num_strings",
    "fingerboard_width_at_nut",
    "fingerboard_width_at_12th_fret",
    "fingerboard_radius",
    "fingerboard_material",
    "fret_material",
    "nut_material",
    "inlay_material",
    "inlay_style",
    "source",
    "id",
]

logger = get_logger(__name__)


def _state_key(field: str) -> str:
    return f"fb_{field}"



def _load_preset_into_state(st, preset_name: str) -> None:
    fields = editable_fields_from_preset(preset_name, user_path=USER_PRESET_PATH)
    for key in FIELD_KEYS:
        st.session_state[_state_key(key)] = fields.get(key)
    st.session_state["fb_loaded_preset"] = preset_name
    st.session_state["fb_previous_units"] = fields["units"]
    logger.debug("Loaded preset %s into UI state", preset_name)



def _snapshot_fields(st) -> dict:
    return {key: st.session_state.get(_state_key(key)) for key in FIELD_KEYS}



def _build_overrides(st) -> dict:
    return {
        "name": st.session_state.get(_state_key("name")),
        "units": st.session_state.get(_state_key("units")),
        "scale_length": float(st.session_state.get(_state_key("scale_length"))),
        "num_frets": int(st.session_state.get(_state_key("num_frets"))),
        "num_strings": int(st.session_state.get(_state_key("num_strings"))),
        "fingerboard_width_at_nut": float(st.session_state.get(_state_key("fingerboard_width_at_nut"))),
        "fingerboard_width_at_12th_fret": float(st.session_state.get(_state_key("fingerboard_width_at_12th_fret"))),
        "fingerboard_radius": float(st.session_state.get(_state_key("fingerboard_radius"))),
        "fingerboard_material": st.session_state.get(_state_key("fingerboard_material")) or None,
        "fret_material": st.session_state.get(_state_key("fret_material")) or None,
        "nut_material": st.session_state.get(_state_key("nut_material")) or None,
        "inlay_material": st.session_state.get(_state_key("inlay_material")) or None,
        "inlay_style": st.session_state.get(_state_key("inlay_style")) or None,
    }



def main() -> None:
    configure_logging()
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not installed. Install the project with the `ui` extra, for example `python -m pip install -e .[ui]`."
        ) from exc

    st.title("Fretboard Generator")
    st.caption("Preset-driven fretboard generation with editable parameters and user preset save-as.")

    presets = available_presets(user_path=USER_PRESET_PATH)
    preset_names = [preset.name for preset in presets]

    st.subheader("Preset")
    selected_name = st.selectbox("Preset", preset_names, key="fb_selected_preset")

    if st.session_state.get("fb_loaded_preset") != selected_name:
        _load_preset_into_state(st, selected_name)

    st.subheader("Preset Status")
    units = st.selectbox("Units", ["in", "mm"], key=_state_key("units"))
    previous_units = st.session_state.get("fb_previous_units", units)
    if units != previous_units:
        converted = convert_display_fields(_snapshot_fields(st), units)
        for field in ("scale_length", "fingerboard_width_at_nut", "fingerboard_width_at_12th_fret", "fingerboard_radius"):
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
    st.number_input("Fingerboard Radius", key=_state_key("fingerboard_radius"))
    generate_requested = st.button("Generate")

    st.subheader("Metadata")
    st.text_input("Fingerboard Material", key=_state_key("fingerboard_material"))
    st.text_input("Fret Material", key=_state_key("fret_material"))
    st.text_input("Nut Material", key=_state_key("nut_material"))
    st.text_input("Inlay Material", key=_state_key("inlay_material"))
    st.text_input("Inlay Style", key=_state_key("inlay_style"))

    st.subheader("User Preset")
    save_preset_name = st.text_input("Save As User Preset")
    save_requested = st.button("Save User Preset")

    if save_requested:
        if not save_preset_name.strip():
            st.write("Enter a user preset name to save the current parameter set.")
        else:
            save_spec = resolve_spec(selected_name, overrides=_build_overrides(st), user_path=USER_PRESET_PATH)
            save_named_user_preset(save_spec, save_preset_name.strip(), user_path=USER_PRESET_PATH, overwrite=True)
            st.success(f"Saved user preset: {save_preset_name.strip()}")

    if not generate_requested:
        return

    logger.info("UI generation requested for preset %s", selected_name)
    spec = resolve_spec(selected_name, overrides=_build_overrides(st), user_path=USER_PRESET_PATH)
    output_path = generate_output(spec, work_folder=resolved_work_folder())
    st.success(f"Generated output: {output_path}")


main()
