# Usage Guide

Creator: **Inouk T.** — inoukt1@gmail.com

## Configure the guard

1. Open the project in Blender.
2. Select `halfApexPropGuardModify.001` in the Outliner.
3. Open Properties > Modifiers > `PG Biomimetic Guard V2`.
4. Set `Propeller Diameter (in)` first.
5. Select a motor layout:
   - Set `Motor Example Preset` to a named/example layout; or
   - Set `Motor Example Preset` to `0`, then choose `Motor Mount Pattern` manually.
6. Set the nozzle preset or custom nozzle diameter.
7. Adjust arc coverage, strength, reinforcement, and bumper options.
8. Inspect the motor plate, branch roots, arc ends, and blade gap before export.

`Motor Example Preset` overrides `Motor Mount Pattern` whenever the preset is above `0`.

## Recommended starting configurations

### Balanced hard-TPU guard

- Strength / Weight: `0.5`
- Bio Reinforcement: `0.5`
- Edge Smoothness: `0.65`
- Arc Coverage: `210°`
- Light Bumper Profile: `0`
- Sacrificial Lip: `0.4 mm`

### Faster print

- Arc Coverage: `180–195°`
- Light Bumper Profile: `1`
- Edge Smoothness: `0.2–0.4`
- Sacrificial Lip: `0–0.4 mm`
- Nozzle Preset: `2` for a 0.6 mm nozzle

### Stronger long-span guard

For 4–5 inch propellers, start with:

- Strength / Weight: `0.7–1.0`
- Bio Reinforcement: `0.7–1.0`
- Arc Coverage: `210°`
- Light Bumper Profile: `0`

## Quick physical fit print

The `Size Check Print` control currently does not create a separate coupon; the complete guard always follows the selected propeller diameter. For a faster low-height fit print, use:

- Guard Height: `3.3 mm`
- Under-Prop Rib Height: `3.3 mm`
- Arc Coverage: `180°`
- Strength / Weight: `0`
- Bio Reinforcement: `0`
- Light Bumper Profile: `1`
- Sacrificial Lip: `0`

This checks the motor holes and radial propeller clearance with less material, but it is not a flight-strength configuration.

## Export an STL

1. Keep the object scale at `(1, 1, 1)`.
2. Select only the guard object.
3. Use File > Export > STL.
4. Enable selection-only export and apply modifiers when those options are available.
5. Export in millimetres and confirm the dimensions in the slicer before printing.

Duplicate the guard object before creating several size variants in one Blender file. Rename each copy with its prop size and motor layout.

## Before powering the quad

1. Confirm the motor drawing matches the selected hole centers.
2. Confirm screws do not touch the windings.
3. Seat every screw fully in the recess without crushing the TPU.
4. With the battery disconnected, install and hand-spin the propeller through several rotations.
5. Flex the outer arc inward and verify it cannot reach the blade during normal deflection.
