# Developer Guide

Creator and maintainer: **Inouk T.** — inoukt1@gmail.com

## Source of truth

The generator is `scripts/biomimetic_prop_guard_v2.py`. It rebuilds the Geometry Nodes group `PG_BiomimeticGuardV2` on `halfApexPropGuardModify.001`. The saved Blender artifact is `C:\Users\inouk\OneDrive\Documents\Untitled.blend` in the creator's working environment.

The project uses Blender Python, Geometry Nodes, `bmesh`, and the Python standard library. It has no third-party Python dependency.

## Install or rebuild in Blender

Open Blender's Scripting workspace and run:

```python
import runpy

module = runpy.run_path(
    r"C:\Users\inouk\OneDrive\Documents\BlenderMCP\scripts\biomimetic_prop_guard_v2.py"
)
module["install"]()
```

`install()` rebuilds the node group, resets parameter defaults, installs the weighted-normal modifier, and refreshes the in-scene parameter-description text.

## Main code areas

- `PARAMETERS` and `PARAMETER_DESCRIPTIONS`: public modifier interface.
- `sizing()`: pure-Python reference calculations.
- `parameter_nodes()`: Geometry Nodes equivalent of the sizing rules.
- `bumper_nodes()`: open arc, rounded ends, light profile, and wear bead.
- `arm_nodes()`: three adaptive biomimetic branch networks.
- `motor_pattern_centers()` and `motor_plate_nodes()`: motor-hole layouts and chamfered plate.
- `self_check()`: geometry, hole, manifold, dimension, and limit validation.

Keep the Python reference calculations and Geometry Nodes graph numerically aligned. When a public parameter changes, update `PARAMETERS`, `PARAMETER_DESCRIPTIONS`, the in-scene description, self-check assertions, and [PARAMETER_REFERENCE.md](PARAMETER_REFERENCE.md) together.

## Verification

Syntax check:

```powershell
python -m py_compile scripts\biomimetic_prop_guard_v2.py
```

Full check in Blender:

```python
import runpy

module = runpy.run_path(
    r"C:\Users\inouk\OneDrive\Documents\BlenderMCP\scripts\biomimetic_prop_guard_v2.py"
)
module["self_check"]()
```

The full check is intentionally slow because it evaluates booleans and mesh topology over propeller presets and parameter extremes. A successful run returns without an assertion error.

Before release:

1. Run `install()`.
2. Run `self_check()`.
3. Restore the intended public default motor layout.
4. Save the `.blend` file.
5. Export and inspect representative STL files in a slicer.
6. Print the low-height fit version and at least one full-strength prototype.

## Release compatibility

- Tested generator target: Blender 5.2.
- Model units: millimetres.
- Supported propeller input: 2–5 inches.
- Public motor layouts: diameter 9 mm, diameter 12 mm, 16x16 mm, and 16x19 mm.

Do not advertise a motor only by stator size. Record the actual hole-center drawing and screw diameter.
