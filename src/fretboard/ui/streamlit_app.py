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



def _state_key(field: str) -> str:
    return f"fb_{field}"



def _load_preset_into_state(st, preset_name: str) -> None:
    fields = editable_fields_from_preset(preset_name, user_path=USER_PRESET_PATH)
    for key in FIELD_KEYS:
        st.session_state[_state_key(key)] = fields.get(key)
    st.session_state["fb_loaded_preset"] = preset_name
    st.session_state["fb_previous_units"] = fields["units"]



def _snapshot_fields(st) -> dict:
    return {
        key: st.session_state.get(_state_key(key))
        for key in FIELD_KEYS
    }



def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not installed. Install with `pip install -r requirements.txt`."
        ) from exc

    st.title("Fretboard Generator")
    st.caption("Preset-driven fretboard generation with editable parameters and user preset save-as.")

    presets = available_presets(user_path=USER_PRESET_PATH)
    preset_names = [preset.name for preset in presets]
    selected_name = st.selectbox("Preset", preset_names, key="fb_selected_preset")

    if st.session_state.get("fb_loaded_preset") != selected_name:
        _load_preset_into_state(st, selected_name)

    units = st.selectbox("Units", ["in", "mm"], key=_state_key("units"))
    previous_units = st.session_state.get("fb_previous_units", units)
    if units != previous_units:
        converted = convert_display_fields(_snapshot_fields(st), units)
        for field in ("scale_length", "fingerboard_width_at_nut", "fingerboard_width_at_12th_fret", "fingerboard_radius"):
            st.session_state[_state_key(field)] = converted[field]
        st.session_state["fb_previous_units"] = units

    st.write(f"Preset source: {st.session_state.get(_state_key('source'))}")
    st.write(f"Work folder: {resolved_work_folder()}")

    name = st.text_input("Name", key=_state_key("name"))
    scale_length = st.number_input("Scale Length", key=_state_key("scale_length"))
    num_frets = st.number_input("Number of Frets", min_value=1, key=_state_key("num_frets"))
    num_strings = st.number_input("Number of Strings", min_value=2, key=_state_key("num_strings"))
    width_at_nut = st.number_input("Fingerboard Width At Nut", key=_state_key("fingerboard_width_at_nut"))
    width_at_12th_fret = st.number_input("Fingerboard Width At 12th Fret", key=_state_key("fingerboard_width_at_12th_fret"))
    radius = st.number_input("Fingerboard Radius", key=_state_key("fingerboard_radius"))
    fingerboard_material = st.text_input("Fingerboard Material", key=_state_key("fingerboard_material"))
    fret_material = st.text_input("Fret Material", key=_state_key("fret_material"))
    nut_material = st.text_input("Nut Material", key=_state_key("nut_material"))
    inlay_material = st.text_input("Inlay Material", key=_state_key("inlay_material"))
    inlay_style = st.text_input("Inlay Style", key=_state_key("inlay_style"))
    save_preset_name = st.text_input("Save As User Preset")

    if not st.button("Generate"):
        return

    overrides = {
        "name": name,
        "units": st.session_state[_state_key("units")],
        "scale_length": float(scale_length),
        "num_frets": int(num_frets),
        "num_strings": int(num_strings),
        "fingerboard_width_at_nut": float(width_at_nut),
        "fingerboard_width_at_12th_fret": float(width_at_12th_fret),
        "fingerboard_radius": float(radius),
        "fingerboard_material": fingerboard_material or None,
        "fret_material": fret_material or None,
        "nut_material": nut_material or None,
        "inlay_material": inlay_material or None,
        "inlay_style": inlay_style or None,
    }
    spec = resolve_spec(selected_name, overrides=overrides, user_path=USER_PRESET_PATH)

    if save_preset_name.strip():
        save_named_user_preset(spec, save_preset_name.strip(), user_path=USER_PRESET_PATH, overwrite=True)
        st.success(f"Saved user preset: {save_preset_name.strip()}")

    output_path = generate_output(spec, work_folder=resolved_work_folder())
    st.success(f"Generated output: {output_path}")


main()
