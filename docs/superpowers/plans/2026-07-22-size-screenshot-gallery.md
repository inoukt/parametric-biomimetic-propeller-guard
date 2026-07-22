# Size Screenshot Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render and publish six consistent model screenshots covering every supported propeller size.

**Architecture:** Use the existing Geometry Nodes modifier as the only geometry source. Render temporary camera/text helpers through Blender Workbench, delete helpers, restore defaults, then reference the PNG outputs from Markdown.

**Tech Stack:** Blender 5.2 Python API, Geometry Nodes, PNG, Markdown.

## Global Constraints

- Sizes: 2, 2.5, 3, 3.5, 4, and 5 inches.
- Motor layout: BETAFPV 1505 example, diameter 12 mm.
- Resolution: 1200x900 pixels.
- Do not save temporary render helpers into the public `.blend` file.

---

### Task 1: Render and verify the gallery

**Files:**
- Create: `screenshots/guard-2-inch.png`
- Create: `screenshots/guard-2-5-inch.png`
- Create: `screenshots/guard-3-inch.png`
- Create: `screenshots/guard-3-5-inch.png`
- Create: `screenshots/guard-4-inch.png`
- Create: `screenshots/guard-5-inch.png`
- Modify: `README.md`
- Modify: `docs/THINGIVERSE.md`

**Interfaces:**
- Consumes: `set_parameter()` and the `PG Biomimetic Guard V2` modifier.
- Produces: six captioned 1200x900 PNG gallery images.

- [ ] Render each preset with identical shading and camera direction.
- [ ] Restore `Motor Mount Pattern = 1`, `Motor Example Preset = 0`, and `Propeller Diameter (in) = 2` after rendering.
- [ ] Inspect all six images for framing, visible open arc, connected branches, and correct label.
- [ ] Add the six-image gallery to `README.md` and the upload checklist to `docs/THINGIVERSE.md`.
- [ ] Commit and push the gallery to GitHub `main`.
