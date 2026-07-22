# Thingiverse Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a concise Thingiverse-ready documentation and licensing package for the parametric biomimetic propeller guard.

**Architecture:** Keep the root README short and route detailed information to focused Markdown documents. Treat the Python generator as the source of truth for parameter values and use a dual license appropriate to model files and software.

**Tech Stack:** Markdown, Blender Geometry Nodes, Blender Python, Python standard library.

## Global Constraints

- Creator: Inouk T.
- Public contact: inoukt1@gmail.com.
- Model/design license: CC BY 4.0.
- Generator license: MIT.
- No unsupported safety, compatibility, weight, or structural claims.

---

### Task 1: Public documentation package

**Files:**
- Create: `README.md`
- Create: `docs/USAGE.md`
- Create: `docs/PARAMETER_REFERENCE.md`
- Create: `docs/PRINTING.md`
- Create: `docs/DEVELOPMENT.md`
- Create: `docs/THINGIVERSE.md`
- Create: `CHANGELOG.md`
- Create: `LICENSE.md`

**Interfaces:**
- Consumes: `PARAMETERS`, `PARAMETER_DESCRIPTIONS`, geometry constants, and `self_check()` from `scripts/biomimetic_prop_guard_v2.py`.
- Produces: a self-contained public release guide and ready-to-paste Thingiverse listing.

- [ ] Write the eight public Markdown files with one responsibility per file.
- [ ] Include exact mount coordinates, hole diameters, parameter precedence, and honest control limitations.
- [ ] Include conservative hard-TPU starting settings and tell users to follow their filament datasheet.
- [ ] Add author attribution and dual-license notices.

### Task 2: Documentation verification

**Files:**
- Verify: all files from Task 1

**Interfaces:**
- Consumes: the public Markdown package.
- Produces: placeholder-free, internally linked, source-matched documentation.

- [ ] Compare every parameter row with the Python source.
- [ ] Search for `TBD`, `TODO`, broken relative links, outdated 16/19 mm bolt-circle wording, and unsupported claims.
- [ ] Run `python -m py_compile scripts/biomimetic_prop_guard_v2.py` to ensure documentation work did not disturb the generator.
- [ ] Review the final diff and commit only documentation files.
