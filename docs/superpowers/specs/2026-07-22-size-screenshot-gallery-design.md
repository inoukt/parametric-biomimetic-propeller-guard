# Size Screenshot Gallery Design

## Goal

Show every supported propeller preset clearly in GitHub and provide ready-to-upload Thingiverse images.

## Visual design

- Render six 1200x900 PNG images for 2, 2.5, 3, 3.5, 4, and 5 inch propellers.
- Use the same top-perspective camera direction, neutral studio background, light-blue guard color, and 1505 diameter-12-mm motor mount.
- Frame each guard individually so geometry remains readable; display the propeller size in the filename and GitHub gallery caption.
- Keep render helpers out of the saved public Blender scene and restore the 1505/default parameter state after rendering.

## Publishing

Store images under `screenshots/`. Add a compact gallery to `README.md` and list the exact PNG files in `docs/THINGIVERSE.md`.

## Verification

Confirm that all six files exist, are 1200x900 PNGs, contain visible geometry, and correspond to the six supported propeller presets and captions. Visually inspect every output before committing.
