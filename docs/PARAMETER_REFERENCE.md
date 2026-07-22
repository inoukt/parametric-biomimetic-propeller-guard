# Parameter and Motor Reference

Creator: **Inouk T.** — inoukt1@gmail.com

## Geometry controls

| Parameter | Range | Default | Effect |
|---|---:|---:|---|
| Propeller Diameter (in) | 2–5 | 2 | Target propeller diameter. Tested presets: 2, 2.5, 3, 3.5, 4, 5 inches. |
| Guard Height (mm) | 3.3–101.6 | 12 | Total outer protector height. |
| Bumper Thickness (mm) | 1.2–8 | 2.2 | Base radial thickness before nozzle and light-profile limits. |
| Strength / Weight | 0–1 | 0.5 | Raises branch widths and junction reinforcement. |
| Nozzle Diameter (mm) | 0.4–0.8 | 0.4 | Custom nozzle diameter when Nozzle Preset is 0. |
| Safety Clearance Override (mm) | 0–1,000,000 | 0 | `0` uses automatic radial clearance; a positive value replaces it. Use practical values appropriate to the aircraft. |
| Under-Prop Rib Height (mm) | 1.2–12 | 3.3 | Branch height growing downward from the motor-top reference, without raising material under the motor. |
| Bio Reinforcement | 0–1 | 0.5 | Strengthens organic root and fork junctions, especially on long spans. |
| Edge Smoothness | 0–1 | 0.65 | Controls curve/profile resolution and evaluated mesh density. |
| Arc Coverage (deg) | 180–210 | 210 | Protected angular coverage. Branch attachment angles follow the arc ends. |
| Nozzle Preset | 0–3 | 0 | `0` custom, `1` 0.4 mm, `2` 0.6 mm, `3` 0.8 mm. |
| Sacrificial Lip (mm) | 0–1.2 | 0.4 | Adds a thin outer wear bead for scuffs. It is joined to the bumper, not a separately replaceable part. |
| Light Bumper Profile | 0–1 | 0 | Reduces bumper section while retaining the same base protection envelope. |
| Size Check Print | 0–1 | 0 | Compatibility flag. It currently makes no separate coupon and does not change the full guard geometry. |
| Motor Mount Pattern | 0–3 integer | 1 | Manual motor layout, used only when Motor Example Preset is 0. |
| Motor Example Preset | 0–4 integer | 0 | Named/example layout. Any nonzero value overrides Motor Mount Pattern. |

## Motor mount layouts

All coordinates are millimetres from the motor center `(0, 0)`.

| Manual pattern | Example preset | Layout | Hole centers |
|---:|---:|---|---|
| 0 | 1 | Diameter 9 mm / BETAFPV 1105 example | `(±4.5, 0)`, `(0, ±4.5)` |
| 1 | 2 | Diameter 12 mm / BETAFPV 1505 example | `(±6, 0)`, `(0, ±6)` |
| 2 | 3 | 16x16 mm | `(±8, ±8)` |
| 3 | 4 | 16x19 mm | `(±8, ±9.5)` |

The motor-size name alone does not guarantee a mounting pattern. Check the manufacturer's bottom drawing or measure opposite/adjacent hole centers before printing.

Manufacturer examples: [BETAFPV 1105 — M2 on diameter 9 mm](https://betafpv.com/collections/2024-prime-day/products/1105-6000kv-motors-4-pcs) and [BETAFPV 1505 — four M2 holes on diameter 12 mm](https://betafpv.com/collections/brushless-motors/products/1505-4600kv-brushless-motor).

## Hole and recess geometry

- Through-hole diameter: `3.0 mm`.
- Lower recess diameter: `4.5 mm`.
- Motor plate bottom Z: `-3.0034 mm`.
- Recess shoulder Z: `-1.6034 mm`.
- Motor plate top Z: `0.2966 mm`.

The hole and recess diameters remain fixed for every layout to preserve the approved chamfered profile. Confirm that this clearance is suitable for the intended M2 or M3 hardware.

## Derived dimensions

Let `D` be propeller diameter in millimetres, `C` radial clearance, `B` base bumper thickness, and `L` wear-lip width.

- `D = Propeller Diameter (in) × 25.4`
- Automatic clearance: `C = max(2 mm, 0.04 × D)`
- Minimum printable rib/wall: `3 × effective nozzle diameter`
- Approximate maximum outside diameter: `D + 2 × (C + B + L)`

Because the protector is an open arc, its axis-aligned bounding box may be smaller than the derived full radial envelope.
