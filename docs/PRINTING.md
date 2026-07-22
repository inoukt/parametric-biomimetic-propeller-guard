# Hard-TPU Printing Guide

Creator: **Inouk T.** — inoukt1@gmail.com

This guard is intended to print flat without supports. Settings below are conservative starting points, not universal profiles. Follow the filament manufacturer's temperature, drying, and speed limits first.

## Orientation

- Put the motor-plate underside and flat branch bottoms on the build plate.
- Do not rotate the guard vertically.
- Supports should not be required for the generated body.
- Use a release layer when the TPU manufacturer recommends one; flexible materials can bond aggressively to some build surfaces.

## Starting profiles

| Setting | Hard TPU 98A starting point | TPE/TPU 60D starting point |
|---|---:|---:|
| Nozzle | 0.4 or 0.6 mm | 0.4 or 0.6 mm |
| Layer height | 0.20–0.30 mm | 0.20–0.30 mm |
| Nozzle temperature | 220–240 °C | 210–230 °C |
| Bed temperature | 40–70 °C | 30–60 °C |
| Print speed | 20–40 mm/s | 40–80 mm/s if the filament and extruder permit |
| Walls/perimeters | 3–4 | 3–4 |
| Infill | 15–25% | 15–25% |
| Supports | Off | Off |

A 0.6 mm nozzle is a useful speed/strength choice for larger guards. Set `Nozzle Preset = 2` so the geometry respects a 1.8 mm minimum printable feature.

## Slicer checks

1. Confirm the STL units are millimetres.
2. Inspect every motor recess and through hole in layer preview.
3. Confirm the motor plate, all three branch roots, and the outer arc are connected.
4. Check that no slicer thin-wall warning removes fork sections.
5. Prefer continuous walls around the bumper and branches; infill percentage matters less than sound perimeters and layer bonding.
6. Check estimated mass and print time in the slicer for the chosen prop size.

## Fit and durability test

Print the low-height fit configuration from [USAGE.md](USAGE.md) before a full 4–5 inch guard or a new motor layout.

Reject the print if it has:

- loose or oval motor holes;
- incomplete recess shoulders;
- gaps at branch roots or bumper junctions;
- under-extruded forks;
- severe stringing inside the propeller path;
- cracks, whitening, or permanent deformation after moderate hand flexing.

After a hard impact, remove the propeller and inspect both sides. Replace the guard if the wear bead is torn through, layers separate, roots crack, or the arc no longer returns to its original position.

## Safety note

Never rely on the guard as complete blade containment. Keep people clear of the propeller plane, test at low power first, and follow normal LiPo and rotating-propeller safety practices.

## Printing references

- [Prusa flexible-material guidance](https://help.prusa3d.com/article/flexible-materials_2057)
- [Fiberthree TPU 98A technical data sheet](https://www.fiberthree.com/downloads/tdb/filaments/TDS_F3_TPU_98A_English_vers_12_2024.pdf)
- [BASF Ultrafuse TPE 60D technical data sheet](https://www.mholland.com/media/Ultrafuse_TPE_60D_TDS.pdf)
