from pathlib import Path

from fretboard.app import (
    available_presets,
    editable_fields_from_preset,
    generate_output,
    resolve_spec,
    save_named_user_preset,
)


USER_PRESET_PATH = Path(__file__).resolve().parents[3] / "presets" / "user_presets.json"



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
    selected_name = st.selectbox("Preset", preset_names)

    fields = editable_fields_from_preset(selected_name, user_path=USER_PRESET_PATH)
    st.write(f"Preset source: {fields['source']}")

    with st.form("fretboard_parameters"):
        name = st.text_input("Name", value=fields["name"])
        units = st.selectbox("Units", ["in", "mm"], index=["in", "mm"].index(fields["units"]))
        scale_length = st.number_input("Scale Length", value=float(fields["scale_length"]))
        num_frets = st.number_input("Number of Frets", min_value=1, value=int(fields["num_frets"]))
        num_strings = st.number_input("Number of Strings", min_value=2, value=int(fields["num_strings"]))
        width_at_nut = st.number_input("Fingerboard Width At Nut", value=float(fields["fingerboard_width_at_nut"]))
        width_at_12th_fret = st.number_input(
            "Fingerboard Width At 12th Fret",
            value=float(fields["fingerboard_width_at_12th_fret"]),
        )
        radius = st.number_input("Fingerboard Radius", value=float(fields["fingerboard_radius"]))
        fingerboard_material = st.text_input("Fingerboard Material", value=fields.get("fingerboard_material") or "")
        fret_material = st.text_input("Fret Material", value=fields.get("fret_material") or "")
        nut_material = st.text_input("Nut Material", value=fields.get("nut_material") or "")
        inlay_material = st.text_input("Inlay Material", value=fields.get("inlay_material") or "")
        inlay_style = st.text_input("Inlay Style", value=fields.get("inlay_style") or "")
        save_preset_name = st.text_input("Save As User Preset", value="")
        generate_clicked = st.form_submit_button("Generate")

    if not generate_clicked:
        return

    overrides = {
        "name": name,
        "units": units,
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

    output_path = generate_output(spec, output_dir=Path.cwd())
    st.success(f"Generated output: {output_path}")
