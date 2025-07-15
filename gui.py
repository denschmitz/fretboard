import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from fretboard import Fretboard

def load_presets(filepath="presets.json"):
    with open(filepath) as f:
        return json.load(f)

def generate_fretboard(preset_name, params, output_file):
    fretboard = Fretboard.from_preset(preset_name, overrides=params)
    fretboard.summary()
    # Real STEP export is outside the scope of this simple example
    if output_file:
        print(f"Would export STEP to {output_file}")

def launch_gui():
    presets = load_presets()

    root = tk.Tk()
    root.title("Fretboard Generator")

    tk.Label(root, text="Select Preset:").grid(row=0, column=0, sticky="e")
    preset_var = tk.StringVar(value=list(presets.keys())[0])
    preset_menu = ttk.Combobox(root, textvariable=preset_var, values=list(presets.keys()), width=30, state="readonly")
    preset_menu.grid(row=0, column=1)

    tk.Label(root, text="Scale Length:").grid(row=1, column=0, sticky="e")
    scale_entry = tk.Entry(root)
    scale_entry.grid(row=1, column=1)

    tk.Label(root, text="Fret Count:").grid(row=2, column=0, sticky="e")
    frets_entry = tk.Entry(root)
    frets_entry.grid(row=2, column=1)

    def update_fields(*_):
        preset = preset_var.get()
        data = presets.get(preset, {})
        scale_entry.delete(0, tk.END)
        scale_entry.insert(0, str(data.get("scale_length", "")))
        frets_entry.delete(0, tk.END)
        frets_entry.insert(0, str(data.get("num_frets", "")))

    preset_var.trace_add("write", update_fields)
    update_fields()

    def choose_file():
        return filedialog.asksaveasfilename(defaultextension=".step", filetypes=[("STEP Files", "*.step")])

    def on_generate():
        preset = preset_var.get()
        if preset not in presets:
            messagebox.showerror("Error", f"Preset '{preset}' not found.")
            return

        params = {}
        if scale_entry.get():
            try:
                params["scale_length"] = float(scale_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Scale length must be a number.")
                return
        if frets_entry.get():
            try:
                params["num_frets"] = int(frets_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Fret count must be an integer.")
                return

        output_file = choose_file()
        if not output_file:
            return

        try:
            generate_fretboard(preset, params, output_file)
            messagebox.showinfo("Success", "Fretboard generated. Check console for details.")
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed:\n{e}")

    tk.Button(root, text="Generate Fretboard", command=on_generate).grid(row=3, column=0, columnspan=2, pady=10)

    root.mainloop()
