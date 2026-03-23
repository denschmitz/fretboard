# Design Requirements

## 1. Purpose

This project shall generate a parametric guitar fretboard model and export that model as a valid STEP file suitable for downstream CAD, CAM, and fabrication workflows.

The project is not primarily a visualization tool, a preset browser, or a fret-spacing calculator in isolation. Its purpose is to transform a defined set of fretboard parameters into manufacturable 3D geometry.

The generated model shall represent an actual fretboard blank, not merely a 2D reference drawing. Fret locations shall be computed accurately from the musical scale definition, and the resulting 3D solid shall support typical guitar-building use cases such as review in CAD, fixture design, CNC preparation, and dimensional verification.

## 2. Product Definition

The system shall produce a 3D fretboard body with the following essential characteristics:

- A tapered planform from nut end to body end.
- A radiused playing surface derived from a cylindrical surface or an equivalent mathematically identical construction.
- Fret slot centerlines positioned according to the selected scale and fret count.
- Fret slot cuts applied after the primary fretboard surface and body geometry are established.
- Export of the final geometry to STEP format.

The system may additionally emit secondary outputs such as debug drawings, 2D construction data, SVG, DXF, or intermediate CAD scripts. These are subordinate outputs and shall not replace STEP generation as the primary deliverable.

## 3. Design Philosophy

The project shall be designed from the output backward.

The controlling question for every major implementation decision shall be: does this improve the project’s ability to produce a correct and usable STEP model of a fretboard?

Accordingly:

- Geometry generation shall take precedence over UI concerns.
- CAD kernel compatibility shall take precedence over preserving old code structure.
- Rewriting existing modules is acceptable when required to produce a clearer and more reliable geometry pipeline.
- Presets are convenience input data, not the architectural center of the system.
- Future inlay support shall be treated as an extension of the geometry pipeline, not as an isolated decoration feature.

## 4. Primary Use Case

The primary use case is:

1. A user specifies a fretboard design using either a preset, direct parameter entry, or both.
2. The system computes fret locations and board dimensions from those inputs.
3. The system constructs a 3D fretboard solid using a CAD-capable geometry path.
4. The system cuts fret slots into that solid.
5. The system exports the resulting model to a STEP file.

If the project supports both direct Python geometry generation and generation through an external CAD intermediary such as Fusion 360 or FreeCAD, either approach is acceptable provided the resulting process is deterministic, scriptable, and produces a valid STEP output.

## 5. Required Inputs

The following parameters are required design inputs because they define the minimum viable fretboard:

- `scale_length`
- `num_frets`
- `num_strings`
- `fingerboard_width_at_nut`
- `fingerboard_width_at_12th_fret`
- `fingerboard_radius`

The system shall preserve support for explicit scale definitions, including equal temperament and alternate scales.

The following attributes may be retained as metadata unless and until they drive geometry:

- `fingerboard_material`
- `fret_material`
- `nut_material`
- `inlay_material`
- `inlay_style`

## 6. Preset Requirements

Preset data shall remain simple enough for hand editing.

The authoritative preset store shall be JSON with:

- a top-level file version
- a list of preset objects
- a stable machine-readable `id`
- a human-readable `name`
- explicit `units`
- a `geometry` object for model-driving values
- a `metadata` object for descriptive fields

Preset lookup may support both `id` and display name, but internal logic shall prefer the stable identifier.

The system shall ship with a pick list of known guitar presets.

If the project provides a graphical UI, that UI shall present presets in a dropdown or equivalent single-selection control.

Selecting a preset shall preload all available fretboard parameter fields from the selected preset into the editable parameter form.

After a preset is loaded, the user shall be permitted to change any parameter value before generation.

The user shall also be permitted to save a modified parameter set as a user preset by supplying a new preset name. This save-as behavior may write to the main preset store or to a separate user preset file. The implementation choice shall favor clarity, low risk of accidental overwrite, and ease of hand editing.

If user presets are stored separately, the system shall present them through the same preset selection mechanism as built-in presets.

## 7. Geometric Requirements

### 7.1 Coordinate Intent

The project shall define a consistent geometric coordinate system for all computations and exports. At minimum:

- The nut end shall be the reference end of the board.
- Longitudinal position shall increase from nut toward bridge or board end.
- Width shall be measured across the fretboard.
- Thickness, if modeled, shall be measured normal to the fretboard’s base reference plane.

### 7.2 Planform

The fretboard outline shall be modeled as a tapered body whose width at the nut and width at the 12th fret are controlled by input parameters.

Because width at the 12th fret is a required input, the system shall derive the taper from this known width rather than treating taper as decorative or approximate.

The project shall define how the board extends beyond the last fret and how total board length is determined. This may be an explicit input or a documented default rule, but it shall not remain implicit.

### 7.3 Playing Surface Radius

The fretboard top surface shall be modeled as a radiused surface suitable for actual manufacturing geometry.

For the initial implementation, a cylindrical radius is acceptable and preferred. A construction based on intersecting a cylinder with the tapered board body is valid and aligns with the intended manufacturing geometry.

The radius must exist as real 3D geometry in the exported model.

### 7.4 Fret Locations and Slots

Fret positions shall be computed from the selected scale definition and scale length.

Fret positions shall be represented in a form that can drive actual solid cuts or sketches in the CAD pipeline.

Fret slots shall be cut after the fretboard body and top surface are created.

At minimum, each slot definition shall include:

- slot position
- slot orientation
- slot depth
- slot width or cutter-equivalent width

### 7.5 Inlay Direction

The architecture shall permit future inlay geometry without forcing a redesign of the fretboard pipeline.

A future implementation may support inlays defined either parametrically or by user-supplied SVG artwork. SVG-driven inlays shall be treated as geometry input, validated before CAD operations, and cut or pocketed through the same CAD backend approach used for fret slots.

## 8. Output Requirements

STEP export is the primary required output.

A conforming implementation shall:

- produce a STEP file from the generated fretboard geometry
- do so through a repeatable scripted process
- produce output that can be opened in standard CAD software
- preserve the essential fretboard solid and slot geometry in the exported model

If an external CAD tool is used as an intermediary, the automation path shall remain part of the project, not a manual undocumented side process.

## 9. Implementation Requirements

### 9.1 Acceptable Geometry Paths

The following implementation strategies are acceptable:

- native Python generation using a reliable geometry library that can produce solids and STEP output
- scripted FreeCAD generation and export
- scripted Fusion 360 generation and export
- another scriptable CAD kernel or CAD application with reliable STEP support

The choice of implementation shall be driven by reliability, automation, maintainability, and output correctness rather than by preference for a purely native Python stack.

### 9.2 Architecture

The repository shall be organized so that these concerns are separate:

- preset loading and validation
- musical and geometric calculations
- solid-model construction
- file export
- user interface concerns

The package layout shall reflect this separation. User interfaces shall call into the package API rather than containing geometry logic directly.

### 9.3 User Interface Direction

A desktop GUI is not required for the core product to succeed.

If a UI is provided during early development, Streamlit is the preferred default because it is fast to iterate on while geometry and export behavior are still changing. A future alternative UI is acceptable if it better supports CAD-preview and file-upload workflows.

### 9.4 Graphical Workflow Requirements

If a graphical UI is provided, the basic user workflow shall be:

1. The user selects a preset from a dropdown list.
2. The system loads that preset into editable parameter fields.
3. The user optionally modifies any parameter values.
4. The user may optionally provide a new preset name and save the modified values as a user preset.
5. The user clicks a `Generate` action to create the output.

Generated output shall be written to the active work folder unless the implementation later introduces an explicit output-path control.

The UI shall make it clear whether the current parameter set is a built-in preset, a modified unsaved preset, or a saved user preset.

### 9.5 Command-Line Workflow Requirements

The project shall provide a CLI workflow that covers the same basic behavior as the graphical workflow.

At minimum, the CLI shall support:

- listing available presets
- selecting a preset by stable id or display name
- overriding any supported parameter through flags or an equivalent structured input mechanism
- saving the resolved parameter set as a new user preset
- generating output without requiring a graphical interface

The CLI shall treat preset selection as the starting point for parameter resolution, then apply any user-supplied overrides, then perform generation.

The CLI shall support a save-as operation for user presets. This may be implemented through an explicit `save-preset` style command or through generation flags that name and persist a new preset before or during output generation.

Unless an explicit output path is provided, generated files from the CLI shall be written to the current working directory.

## 10. Validation Requirements

The project shall support verification of the generated model against source parameters.

At minimum, the implementation shall permit validation of:

- overall scale length behavior
- fret positions
- nut width
- 12th-fret width
- top radius
- presence and placement of fret slots
- successful STEP export

Validation may be performed through unit tests, geometric assertions, exported measurements, or CAD-side inspection tooling. The exact mechanism may vary, but the project shall not rely solely on visual confidence.

## 11. Immediate Project Direction

The next design and implementation decisions shall be made in this order:

1. Define the minimal authoritative fretboard parameter set required to build a real solid.
2. Choose the CAD generation path most likely to deliver reliable scripted STEP export.
3. Build a geometry pipeline that creates the tapered board body and radiused top surface.
4. Add fret slot cutting as explicit solid operations.
5. Add inlay pocketing only after the core fretboard body and slot workflow is stable.
6. Export STEP and verify the result in an external CAD viewer.

Any existing code that does not materially support this sequence may be replaced.
