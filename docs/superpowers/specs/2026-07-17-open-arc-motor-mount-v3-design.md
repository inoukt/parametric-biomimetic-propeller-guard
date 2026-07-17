# Open-Arc Motor Mount V3 Design

## Goal

Correct the biomimetic propeller guard by replacing the disconnected imported hub with a procedural motor plate and restoring an open protector. Keep the existing guard parameters, TPU-oriented structure, and hole chamfering.

## Mount

- Generate a new 3.3 mm-thick motor plate centered at local `(0, 0)`, the measured center of the imported four-hole pattern. The old guard-body center offset is not the motor center.
- Use four M2 through-holes equally spaced at `(±6, 0)` and `(0, ±6)` mm from the mount center. Opposite hole centers are exactly 12 mm apart.
- Reproduce the measured imported hole profile: 3.0 mm through diameter, plus a 4.5 mm lower recess from Z `-3.0034075` to `-1.6034075`; the 3.0 mm section continues to the top face at Z `0.2965926`.
- The plate may change shape, but it must leave adequate material around every chamfer and must union directly with all three primary branches.
- The 12 mm bolt circle is fixed hardware geometry, not another user parameter.

## Protector and branches

- Replace the full circular bumper with an open arc covering no more than 210 degrees.
- Match the imported guard orientation: the protected arc runs approximately from 30 to 240 degrees around the mount center, leaving the opening toward the lower-right side in local coordinates.
- Cap both arc ends with the same rounded, flat-bottom profile used by V2.
- Retain three biomimetic branch networks distributed along the protected arc.
- Start every primary branch inside the procedural plate boundary so each hub-to-branch junction has real volumetric overlap before the final boolean.
- Retain rounded root, fork, and bumper junctions and the existing minimum-feature clamping for 0.4–0.8 mm nozzles.

## Parameters

Keep the V2 controls unchanged:

- Propeller Diameter: continuous 2–5 inches, with 2, 2.5, 3, 3.5, 4, and 5 inch presets.
- Guard Height: 3.3–101.6 mm.
- Bumper Thickness: 1.2–8 mm, clamped to at least three nozzle diameters.
- Strength / Weight: 0–1.
- Nozzle Diameter: 0.4–0.8 mm.
- Safety Clearance Override: zero for automatic clearance, positive for manual clearance.

## Validation

1. The four measured hole centers match the 12 mm bolt circle within 0.02 mm.
2. Through-hole and chamfer diameters match the imported profile within mesh-resolution tolerance.
3. The guard has an open bumper arc of at most 210 degrees; no geometry closes the missing sector.
4. Hub plus branches, evaluated without the bumper, forms one connected manifold component. This prevents the previous false positive where the outer ring connected branches while individual roots remained detached.
5. The complete guard forms one connected manifold component with zero non-manifold edges.
6. Every requested propeller preset and all parameter limits preserve the hole pattern, arc opening, dimensions, and branch connectivity.
7. The balanced 2-inch default remains within the 7–8 g estimated TPU target where practical; connectivity and mount strength take priority if the new plate adds a small amount of mass.

## Scope

Modify the existing V2 generator and saved Blender scene. Do not add an add-on, handler, external dependency, interchangeable mount system, or FEA workflow.
