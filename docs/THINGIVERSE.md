# Thingiverse Publishing Package

Creator: **Inouk T.** — Contact: **inoukt1@gmail.com**

## Suggested title

Parametric Biomimetic TPU Propeller Guard — 2 to 5 Inch, Multiple Motor Mounts

## Ready-to-paste summary

Parametric open-arc quadcopter propeller guard for 2–5 inch props. The Blender Geometry Nodes source supports diameter 9 mm, diameter 12 mm, 16x16 mm, and 16x19 mm motor-hole layouts, with nozzle-aware walls, organic forked reinforcement, adjustable arc coverage, and a thin outer wear bead. Designed to print flat without supports in hard TPU.

## Ready-to-paste description

This is a configurable biomimetic propeller guard created by **Inouk T.** The structure uses three forked load paths and rounded junctions to support an open 180–210° outer protector while reducing material in low-load areas.

The Blender source is the main file: select `halfApexPropGuardModify.001`, open the `PG Biomimetic Guard V2` modifier, choose the propeller and motor layout, then export an evaluated STL.

Supported propeller presets:

- 2 inch
- 2.5 inch
- 3 inch
- 3.5 inch
- 4 inch
- 5 inch

Motor layouts:

- Diameter 9 mm — BETAFPV 1105 example
- Diameter 12 mm — BETAFPV 1505 example
- 16x16 mm
- 16x19 mm

The mount keeps 3.0 mm through holes and 4.5 mm lower recesses. Always compare the selected pattern with the actual motor drawing; motor stator size alone does not guarantee the hole layout.

For hard TPU, start with the balanced defaults. For faster printing, try 180–195° arc coverage, the light bumper profile, lower edge smoothness, and a 0.6 mm nozzle preset. Follow the filament manufacturer's temperatures and speed recommendations.

This is experimental equipment, not certified propeller containment. Check screw length, hand-spin blade clearance with the battery disconnected, test at low power, and replace damaged guards.

Created by **Inouk T.** — **inoukt1@gmail.com**. Please credit the creator and identify modified versions.

## Suggested print settings

- Material: hard TPU 98A or TPE/TPU 60D
- Orientation: flat, motor plate underside on the bed
- Supports: no
- Nozzle: 0.4 or 0.6 mm
- Layer height: 0.20–0.30 mm
- Walls: 3–4
- Infill: 15–25%
- Speed and temperature: use the filament manufacturer's profile; see `docs/PRINTING.md` for starting ranges

## Suggested tags

`drone`, `quadcopter`, `fpv`, `propeller_guard`, `prop_guard`, `tpu`, `parametric`, `geometry_nodes`, `blender`, `biomimetic`, `2_inch`, `3_inch`, `4_inch`, `5_inch`, `betafpv`, `motor_mount`

## Files to upload

- The verified `.blend` source.
- `README.md`.
- `docs/USAGE.md`.
- `docs/PARAMETER_REFERENCE.md`.
- `docs/PRINTING.md`.
- `LICENSE.md`.
- Preview images: top view, underside/motor holes, modifier controls, and one printed prototype.
- Optional convenience STLs exported from the verified source for the prop sizes and motor layouts you physically tested.

Do not label an STL as tested unless its motor fit, propeller clearance, and slice preview were actually checked.

## License selection on Thingiverse

Choose **Creative Commons — Attribution (CC BY 4.0)** for the model/design files. Use this attribution line:

> Parametric Biomimetic Propeller Guard by Inouk T. is licensed under CC BY 4.0. Changes must be identified.

The included Python generator is separately available under the MIT License.

## Suggested initial version notes

- Parametric 2–5 inch open-arc protector.
- Organic reinforced branches with smoother junctions.
- Arc coverage and nozzle presets.
- Outer wear lip and light bumper option.
- Real motor layouts: diameter 9 mm, diameter 12 mm, 16x16 mm, and 16x19 mm.
- Correct BETAFPV 1505 diameter 12 mm preset.
- Preserved through holes and lower recess/chamfer profile.
