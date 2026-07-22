# Thingiverse Documentation Design

## Goal

Publish the parametric biomimetic propeller guard with enough information to configure, print, verify, modify, and attribute it without reading the generator source.

## Public documentation

- `README.md`: project landing page, feature summary, quick start, author, and document links.
- `docs/USAGE.md`: Blender workflow from selecting the object through STL export.
- `docs/PARAMETER_REFERENCE.md`: exact controls, ranges, defaults, formulas, and motor-hole coordinates.
- `docs/PRINTING.md`: flat TPU printing workflow, conservative starting settings, fit checks, and safety inspection.
- `docs/DEVELOPMENT.md`: generator architecture, installation, verification, and release maintenance.
- `docs/THINGIVERSE.md`: ready-to-paste listing copy, tags, file checklist, attribution, and version notes.
- `CHANGELOG.md`: public release history.
- `LICENSE.md`: CC BY 4.0 for model/design material and MIT for the Python generator.

## Accuracy rules

- Credit `Inouk T.` and publish `inoukt1@gmail.com` as the creator contact.
- Describe the four real mount layouts as diameter 9 mm, diameter 12 mm, 16x16 mm, and 16x19 mm.
- State that a nonzero Motor Example Preset overrides Motor Mount Pattern.
- Keep the existing 3.0 mm through holes and 4.5 mm lower recess explicit; motor fit must be checked from a manufacturer drawing or physical measurement.
- Describe Sacrificial Lip as an outer wear bead, not a separately replaceable part.
- State that Size Check Print currently does not create a separate coupon; the full guard always follows the selected propeller diameter.
- Present temperatures and speeds only as starting points; the filament manufacturer's profile takes priority.
- Do not claim flight certification, guaranteed propeller containment, FEA validation, or universal motor compatibility.

## Licensing

The original model, Blender geometry, images, and documentation use Creative Commons Attribution 4.0 International. The Python generator uses the MIT License. Attribution should name `Inouk T.` and link to the Thingiverse listing when available.

## Verification

Cross-check every documented parameter against `PARAMETERS` and `PARAMETER_DESCRIPTIONS` in `scripts/biomimetic_prop_guard_v2.py`. Check Markdown links and scan public files for placeholders, contradictory dimensions, and unsupported performance claims.
