import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from fretboard import Fretboard

def load_presets(filepath="presets.json"):
    with open(filepath) as f:
        return json.load(f)

def generate_fretboard(preset_name, params, output_file):
    fretboard = Fretboard(preset=preset_name, custom_params=params)
    fretboard.create_geometry()
    fretboard.export_step(output_file)

def launch_gui():
    presets = load_presets()

    root = tk.Tk()
    root.title("Fretboard Generator")

    tk.Label(root, text="Select Preset:").grid(row=0, column=0, sticky="e")
    preset_var = tk.StringVar(value=list(presets.keys())[0])
    preset_menu = ttk.Combobox(root, textvariable=preset_var, values=list(presets.keys()), width=30)
    preset_menu.grid(row=0, column=1)

    tk.Label(root, text="Override Scale Length:").grid(row=1, column=0, sticky="e")
    scale_entry = tk.Entry(root)
    scale_entry.grid(row=1, column=1)

    tk.Label(root, text="Override Fret Count:").grid(row=2, column=0, sticky="e")
    frets_entry = tk.Entry(root)
    frets_entry.grid(row=2, column=1)

    def choose_file():
        return filedialog.asksaveasfilename(defaultextension=".step", filetypes=[("STEP Files", "*.step")])

    def on_generate():
        preset = preset_var.get()
        if preset not in presets:
            messagebox.showerror("Error", f"Preset '{preset}' not found.")
            return

        params = presets[preset].copy()
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
            messagebox.showinfo("Success", f"STEP file saved to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed:\n{e}")

    tk.Button(root, text="Generate Fretboard", command=on_generate).grid(row=3, column=0, columnspan=2, pady=10)

    root.mainloop()
