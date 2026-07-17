# Parametric Biomimetic Propeller Guard V2 Design

## Goal

Replace the deformation-based V1 guard body with a fully procedural, biomimetic structure that improves impact strength, reduces weight, and remains printable in TPU. Preserve the existing motor-mount hub and mounting holes numerically unchanged.

The balanced design target is 25–30% less material than an equivalently sized solid-shell V1 reference. For the 2-inch-prop default, V2 should weigh approximately 7–8 g using TPU with density between 1.20 and 1.25 g/cm³. Larger propeller sizes retain the percentage-reduction target rather than the same absolute mass.

## Structural Concept

V2 uses topology-guided organic load paths rather than decorative random holes:

- One continuous, rounded outer bumper absorbs direct impacts.
- Three constant-profile primary arms grow from the fixed motor hub and divide into lighter fork veins.
- Each primary arm forks near the bumper like tree roots or leaf veins, spreading loads across multiple ring attachment points.
- The material hierarchy usually tapers discretely from wider primary veins into narrower fork veins; the printable-minimum clamp may make them equal at large nozzle settings. Individual D-profile branches keep constant height and width so the height parameter remains exact and print-bed contact stays flat.
- Large organic cells remove material from low-stress areas.
- Hub, fork, and bumper junctions use generous continuous fillets without sharp internal corners.
- The result is one connected, manifold body that prints flat without supports.

The imported V1 mesh remains available as reference geometry but is not stretched to create V2. Diameter and height changes regenerate the procedural arms, cells, and bumper.

`PG_V2_MountKeep` is an inspectable audit mask showing every retained source face. The printable mount is produced by an exact 14 mm radial intersection of the unchanged closed source mesh; using the separated face mask itself would introduce an open boundary. Validation checks that every protected coordinate within 10 mm survives the final union exactly.

## Fixed Mount Contract

Retain the existing `PG_FixedMount` contract. Every motor-hub and mounting-hole vertex inside the fixed region remains bit-for-bit unchanged.

V2 may replace geometry only outside the stable guard-to-mount interface. It must not move or reshape:

- mounting-hole centers;
- mounting-hole diameters;
- fastener clearances;
- hub geometry; or
- fixed-region vertex coordinates.

Swappable motor mounts remain deferred until a second motor specification exists.

## Parametric Controls

Expose these controls through one clearly named Geometry Nodes modifier:

- **Propeller Diameter (in):** continuous 2–5-inch input with quick presets for 2, 2.5, 3, 3.5, 4, and 5 inches. Internally the presets are 50.8, 63.5, 76.2, 88.9, 101.6, and 127 mm. Default: 2 inches.
- **Guard Height (mm):** 3.3–101.6 mm. The 3.3 mm lower bound is the unchanged mounting hub's physical height. Default: 12 mm.
- **Bumper Thickness (mm):** changes the radial thickness of the continuous outer impact ring. Input range: 1.2–8 mm; evaluated thickness is clamped to at least `3 × Nozzle Diameter`. Default: 2.2 mm with a 0.4 mm nozzle; selecting a 0.8 mm nozzle automatically clamps it to 2.4 mm.
- **Strength / Weight:** normalized 0–1, where 0 is lightest and 1 is strongest. It changes rib width, branch thickness, fork reinforcement, fillet size, and organic-cell openness together. Default: 0.5.
- **Nozzle Diameter (mm):** 0.4–0.8 mm. It sets manufacturing minimums but does not otherwise redesign the mount. Default: 0.4 mm.
- **Safety Clearance Override (mm):** 0 uses the automatic clearance rule; a positive value replaces it. Default: 0.

Automatic radial propeller clearance is `max(2 mm, 0.04 × Propeller Diameter)`. Derived outer guard diameter is:

`Propeller Diameter + 2 × (Safety Clearance + Bumper Thickness)`

Changing propeller size regenerates the entire bumper, arm branching, rib layout, and organic cells. Guard diameter is a derived output rather than an independent input, preventing combinations that cannot contain the selected propeller safely.

Minimum rib and wall thickness is `3 × Nozzle Diameter`. This produces a 1.2 mm minimum with a 0.4 mm nozzle and a 2.4 mm minimum with a 0.8 mm nozzle.

The Strength / Weight control is deliberately material-agnostic. Use the balanced default for typical 95A TPU. Harder 98A or 60D TPU may use a lighter setting after physical validation.

## Impact Behaviour

V2 is designed for controlled inward flex:

- The outer bumper bends locally during an impact.
- Curved forked arms distribute load into multiple paths and spring back more reliably than straight spokes.
- Junctions thicken automatically while middle rib spans remain lighter.
- The structure must retain a positive propeller safety gap at the allowed flex limit.

The design flex budget is half of the radial safety clearance. The undeformed guard provides the full calculated clearance; the physical prototype must retain at least half that clearance during normal controlled flex and must not take a permanent set.

The geometry generator does not claim an exact flex prediction before a TPU brand, hardness, print orientation, perimeter count, and infill strategy are selected. Propeller clearance is therefore a geometric validation constraint plus a physical-test requirement.

## Printing Requirements

- Material range: TPU 95A through hard TPU 98A/60D.
- Nozzle range: 0.4–0.8 mm.
- Flat print orientation.
- No supports for the main body.
- Continuous rounded transitions at every load-bearing junction.
- One connected manifold solid suitable for slicing.

## Validation

V2 must pass all of the following before replacing V1:

1. Mount hub, hole centers, hole diameters, and fixed-region coordinates are identical to the baseline.
2. Minimum, default, maximum bounded, and representative combined parameter settings produce a connected manifold mesh without overlaps or folded faces.
3. Every generated rib and wall is at least `3 × Nozzle Diameter`.
4. The inner opening clears the selected propeller by the automatic or overridden safety clearance, and the derived outer bumper diameter and height match their formulas within mesh-resolution tolerance.
5. The balanced setting uses 25–30% less material than an equivalently sized solid-shell V1 reference. The 2-inch default has an estimated TPU mass of 7–8 g.
6. At the design flex budget of half the radial safety clearance, at least half the original clearance remains.
7. Minimum, default, and maximum cases are inspected in Blender and in a slicer.
8. One arm-to-bumper junction coupon is printed first and tested for bending, repeated impact, layer separation, and spring-back.
9. A complete prototype is printed only after the coupon passes.

Finite-element analysis is deferred until the exact TPU and print settings are known. The initial engineering evidence is geometric validation, material-volume measurement, slicer inspection, and physical coupon testing.

## Scope Boundary

V2 includes the procedural bumper, forked primary arms, organic material-removal cells, 2–5-inch propeller presets, parameter controls, manufacturability constraints, and validation tools.

V2 does not include a swappable motor-mount system, decorative random Voronoi perforation, an add-on, a runtime handler, an external dependency, or material-specific FEA.
