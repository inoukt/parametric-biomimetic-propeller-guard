# Parametric Propeller Guard Design

## Goal

Add non-destructive controls to the newly imported propeller guard for outer diameter, guard height, and radial wall thickness while keeping the motor-mount hub and mounting holes numerically unchanged.

## Selected Approach

Use one named Geometry Nodes modifier on `halfApexPropGuardModify.001`. This handles the requested ranges better than bounded shape keys and keeps the imported mesh recoverable by disabling the modifier.

## Parameters

- **Guard Diameter (mm):** minimum 50.8 mm; no practical design maximum. It scales the outer guard in XY around the mounting center.
- **Guard Height (mm):** 3–101.6 mm. The guard's bottom reference stays fixed and its top moves in Z.
- **Wall Thickness (mm):** 2–8 mm. The outer contour stays fixed and the inner wall moves.

Defaults will match the imported geometry as measured from the mesh.

## Fixed and Adjustable Regions

- A named fixed-mount vertex group gives the mounting hub and every mounting-hole vertex zero deformation.
- A named guard vertex group gives the outer ring full deformation.
- The connecting arms receive a smooth transition between those regions so diameter and height changes do not introduce a hard seam.
- Thickness deformation applies only to the guard's inner wall; it does not alter the hub, holes, or outer diameter.

The fixed-mount vertex group is the upgrade contract: future procedural redesigns must continue to leave those vertices unchanged.

## Future Swappable Motor Mounts

The current motor mount remains unchanged in this version. A future upgrade may separate it into a replaceable mount module for different quadcopter motor sizes.

- Treat the boundary between the arms and fixed hub as the stable guard-to-mount interface.
- Keep guard parameters independent from mount dimensions.
- Future mount modules may vary hole pattern, hub diameter, and fastener clearance while sharing that interface.
- Preserve the current mount as the default module and reference geometry.
- Do not build the module system until a second motor specification is available; its dimensions will define the real interface requirements.

## Blender Structure

- Preserve the imported mesh as the modifier input.
- Add one clearly named Geometry Nodes group with the three exposed inputs.
- Use named vertex groups rather than hidden coordinate thresholds wherever practical, so the deformation regions can be inspected and refined later.
- Do not add an add-on, Python runtime handler, duplicate controller system, or external dependency.

## Limits and Validation

Very large diameter or height values stretch the existing connecting arms; they do not redesign arm topology. That is acceptable for this first version and is the explicit upgrade point for a future fully procedural guard. Swappable motor mounts are also deferred until another motor specification provides concrete dimensions.

Validation will check:

1. Mounting-hole centers, diameters, and fixed-region vertex coordinates are identical before and after parameter changes.
2. Inputs respect the stated minimum and maximum values.
3. Outer diameter, height, and wall thickness match several test settings within mesh-resolution tolerance.
4. The mesh remains connected and visually free of obvious folds at minimum, default, and maximum bounded settings.
