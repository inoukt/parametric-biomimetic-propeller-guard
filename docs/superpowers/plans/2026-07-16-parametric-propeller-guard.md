# Parametric Propeller Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add non-destructive diameter, height, and radial wall-thickness controls to the imported propeller guard while preserving the current motor mount exactly.

**Architecture:** A single idempotent Blender Python script records the fixed-mount contract, creates inspectable mesh attributes, builds one Geometry Nodes deformation modifier, and runs the geometry checks. The outer guard deforms from stored baseline coordinates; the fixed hub has zero weight, and the arms blend between the two regions.

**Tech Stack:** Blender 5.2 Python API, Geometry Nodes, Blender mesh attributes, Python standard library only.

## Global Constraints

- Target object: `halfApexPropGuardModify.001` in `C:\Users\inouk\OneDrive\Documents\Untitled.blend`.
- Diameter input: minimum 50.8 mm, default 86.906372 mm, no practical design maximum.
- Height input: 3–101.6 mm, default 26.400002 mm.
- Wall-thickness input: 2–8 mm, default 4.0 mm.
- Coordinates use the imported model's millimetre convention; node inputs are plain floats labelled `(mm)`.
- Vertices within 10 mm of the measured mount center `(2.204754, -2.317232)` must remain bit-for-bit unchanged.
- The current mounting-hole centers, diameters, and hub geometry are immutable.
- No add-on, runtime handler, duplicate controller system, or external dependency.
- The fixed-region attributes remain the interface contract for future swappable motor mounts.

---

## File Structure

- Create `scripts/parametric_prop_guard.py`: idempotent scene setup, Geometry Nodes construction, parameter access, and one runnable self-check.
- Modify `C:\Users\inouk\OneDrive\Documents\Untitled.blend`: store the modifier, node group, mesh attributes, and parameter defaults.

### Task 1: Record the fixed mount and deformation fields

**Files:**
- Create: `scripts/parametric_prop_guard.py`
- Test: `scripts/parametric_prop_guard.py --self-check`

**Interfaces:**
- Produces: `get_guard() -> bpy.types.Object`, `mount_signature(obj) -> tuple`, and `build_attributes(obj) -> None`.
- Produces mesh point-domain attributes: `PG_FixedMount`, `PG_GuardWeight`, `PG_InnerWeight`, and `PG_ThicknessDirection`.

- [ ] **Step 1: Write the initial failing self-check**

Add the constants, object lookup, signature capture, and assertion below. The signature contains every coordinate inside the fixed 10 mm radius, ordered by vertex index.

```python
import bpy
import math
import sys

OBJECT_NAME = "halfApexPropGuardModify.001"
CENTER = (2.204754, -2.317232)
FIXED_RADIUS = 10.0
GUARD_RADIUS = 25.0
BASE_DIAMETER = 86.906372
BASE_HEIGHT = 26.400002
BASE_THICKNESS = 4.0

def get_guard():
    obj = bpy.data.objects.get(OBJECT_NAME)
    assert obj and obj.type == "MESH", f"Missing mesh: {OBJECT_NAME}"
    return obj

def mount_signature(obj):
    cx, cy = CENTER
    return tuple(
        (v.index, tuple(v.co))
        for v in obj.data.vertices
        if math.hypot(v.co.x - cx, v.co.y - cy) <= FIXED_RADIUS
    )

def self_check():
    obj = get_guard()
    for name in ("PG_FixedMount", "PG_GuardWeight", "PG_InnerWeight", "PG_ThicknessDirection"):
        assert obj.data.attributes.get(name), f"Missing attribute: {name}"

if __name__ == "__main__" and "--self-check" in sys.argv:
    self_check()
```

- [ ] **Step 2: Run the check and verify it fails**

Run:

```powershell
& 'D:\Blender 5.2\blender.exe' --background 'C:\Users\inouk\OneDrive\Documents\Untitled.blend' --python 'scripts\parametric_prop_guard.py' -- --self-check
```

Expected: Blender exits nonzero with `Missing attribute: PG_FixedMount`.

- [ ] **Step 3: Implement the four attributes**

Add `build_attributes(obj)`. For each vertex, compute radius from `CENTER`; fixed weight is `1` through 10 mm, guard weight is smoothstep from `0` at 10 mm to `1` at 25 mm. Classify inner-wall faces where radius is over 20 mm, `abs(normal.z) < 0.45`, and the XY face-normal dot radial vector is negative. Average those face normals per vertex to create a normalized XY thickness direction; inner weight is `1` on those vertices and `0` elsewhere.

```python
from collections import defaultdict
from mathutils import Vector

def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)

def point_attribute(mesh, name, data_type):
    old = mesh.attributes.get(name)
    if old:
        mesh.attributes.remove(old)
    return mesh.attributes.new(name=name, type=data_type, domain="POINT")

def build_attributes(obj):
    mesh = obj.data
    cx, cy = CENTER
    fixed = point_attribute(mesh, "PG_FixedMount", "FLOAT")
    guard = point_attribute(mesh, "PG_GuardWeight", "FLOAT")
    inner = point_attribute(mesh, "PG_InnerWeight", "FLOAT")
    direction = point_attribute(mesh, "PG_ThicknessDirection", "FLOAT_VECTOR")
    normal_sums = defaultdict(lambda: Vector((0.0, 0.0, 0.0)))

    for face in mesh.polygons:
        radial = Vector((face.center.x - cx, face.center.y - cy))
        dot = face.normal.x * radial.x + face.normal.y * radial.y
        if radial.length > 20.0 and abs(face.normal.z) < 0.45 and dot < 0.0:
            xy_normal = Vector((face.normal.x, face.normal.y, 0.0))
            if xy_normal.length:
                xy_normal.normalize()
                for vertex_index in face.vertices:
                    normal_sums[vertex_index] += xy_normal

    for vertex in mesh.vertices:
        radius = math.hypot(vertex.co.x - cx, vertex.co.y - cy)
        fixed.data[vertex.index].value = float(radius <= FIXED_RADIUS)
        guard.data[vertex.index].value = smoothstep((radius - FIXED_RADIUS) / (GUARD_RADIUS - FIXED_RADIUS))
        vector = normal_sums[vertex.index]
        is_inner = bool(vector.length)
        inner.data[vertex.index].value = float(is_inner)
        if is_inner:
            vector.normalize()
        direction.data[vertex.index].vector = vector
```

Call `build_attributes(get_guard())` before `self_check()`.

- [ ] **Step 4: Run the check and verify it passes**

Run the Step 2 command again. Expected: exit code `0` and no assertion text.

- [ ] **Step 5: Commit**

```powershell
git add scripts/parametric_prop_guard.py
git commit -m "feat: record prop guard deformation fields"
```

### Task 2: Build the Geometry Nodes parameter modifier

**Files:**
- Modify: `scripts/parametric_prop_guard.py`
- Test: `scripts/parametric_prop_guard.py --self-check`

**Interfaces:**
- Consumes: the four `PG_*` attributes from Task 1.
- Produces: `build_node_group() -> bpy.types.GeometryNodeTree` and `install_modifier(obj) -> bpy.types.Modifier`.
- Produces node group `PG_ParametricGuard` with float inputs `Guard Diameter (mm)`, `Guard Height (mm)`, and `Wall Thickness (mm)`.

- [ ] **Step 1: Extend the self-check so it fails without the modifier**

```python
modifier = obj.modifiers.get("PG Parametric Guard")
assert modifier and modifier.type == "NODES", "Missing parametric guard modifier"
group = modifier.node_group
assert group and group.name == "PG_ParametricGuard", "Wrong node group"
inputs = {item.name for item in group.interface.items_tree if item.item_type == "SOCKET" and item.in_out == "INPUT"}
assert {"Guard Diameter (mm)", "Guard Height (mm)", "Wall Thickness (mm)"} <= inputs
```

- [ ] **Step 2: Run the check and verify it fails**

Run the Task 1 command. Expected: `Missing parametric guard modifier`.

- [ ] **Step 3: Build the minimal deformation graph**

Create one Geometry Nodes group and one Set Position node. Read the three stored attributes with Named Attribute nodes. Wire the offset as the sum of these independent formulas, evaluated from the original Position:

```python
diameter_scale = diameter / BASE_DIAMETER
diameter_offset_xy = ((position_xy - CENTER) * (diameter_scale - 1.0)) * guard_weight
height_offset_z = ((position_z - z_min) * (height / BASE_HEIGHT - 1.0)) * guard_weight
thickness_offset = thickness_direction * (thickness - BASE_THICKNESS) * inner_weight
final_offset = diameter_offset_xy + (0.0, 0.0, height_offset_z) + thickness_offset
```

Use `GeometryNodeInputNamedAttribute`, `GeometryNodeInputPosition`, `ShaderNodeVectorMath`, `ShaderNodeMath`, `ShaderNodeSeparateXYZ`, `ShaderNodeCombineXYZ`, and `GeometryNodeSetPosition`. Set socket ranges when creating the interface:

```python
diameter_socket.min_value = 50.8
diameter_socket.max_value = 1_000_000.0
diameter_socket.default_value = BASE_DIAMETER
height_socket.min_value = 3.0
height_socket.max_value = 101.6
height_socket.default_value = BASE_HEIGHT
thickness_socket.min_value = 2.0
thickness_socket.max_value = 8.0
thickness_socket.default_value = BASE_THICKNESS
```

`install_modifier(obj)` must reuse the existing named modifier and node group so rerunning the script does not duplicate data blocks.

- [ ] **Step 4: Run the check and verify it passes**

Run the Task 1 command. Expected: exit code `0`.

- [ ] **Step 5: Commit**

```powershell
git add scripts/parametric_prop_guard.py
git commit -m "feat: add prop guard geometry controls"
```

### Task 3: Verify immutability, parameter measurements, and saved scene

**Files:**
- Modify: `scripts/parametric_prop_guard.py`
- Modify: `C:\Users\inouk\OneDrive\Documents\Untitled.blend`
- Test: `scripts/parametric_prop_guard.py --self-check`

**Interfaces:**
- Consumes: `mount_signature`, `install_modifier`, and the three node inputs.
- Produces: `set_parameter(modifier, name, value) -> None`, `evaluated_vertices(obj) -> tuple`, and a self-check that restores defaults in `finally`.

- [ ] **Step 1: Add failing fixed-mount and bounds assertions**

For each test case, compare evaluated coordinates for every vertex in the baseline mount signature and assert exact equality. Also assert measured evaluated bounds at the defaults, minimums, and bounded maximums.

```python
cases = (
    (50.8, 3.0, 2.0),
    (BASE_DIAMETER, BASE_HEIGHT, BASE_THICKNESS),
    (120.0, 101.6, 8.0),
)
before = mount_signature(obj)
try:
    for diameter, height, thickness in cases:
        set_parameter(modifier, "Guard Diameter (mm)", diameter)
        set_parameter(modifier, "Guard Height (mm)", height)
        set_parameter(modifier, "Wall Thickness (mm)", thickness)
        bpy.context.view_layer.update()
        after = evaluated_mount_signature(obj)
        assert after == before, (diameter, height, thickness)
finally:
    set_parameter(modifier, "Guard Diameter (mm)", BASE_DIAMETER)
    set_parameter(modifier, "Guard Height (mm)", BASE_HEIGHT)
    set_parameter(modifier, "Wall Thickness (mm)", BASE_THICKNESS)
```

- [ ] **Step 2: Run the check and verify it identifies any wiring or weighting error**

Run the Task 1 command. Expected before the measurement helpers are complete: a missing-name failure for `evaluated_mount_signature` or `set_parameter`.

- [ ] **Step 3: Implement evaluation helpers and measurement tolerances**

Resolve modifier socket identifiers from `group.interface.items_tree`, assign modifier values by identifier, and obtain evaluated mesh coordinates through `obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()`. Release evaluated meshes with `to_mesh_clear()`.

At default values assert dimensions within `0.01 mm` of `(86.892616, 86.906372, 26.400002)`. For non-default values, measure height only across vertices whose stored `PG_GuardWeight` is at least `0.999`; the immutable hub is slightly taller than the requested 3 mm minimum and must not be altered merely to reduce the guard. At each non-default case assert:

```python
assert max(evaluated_dimensions[:2]) >= diameter - 0.05
assert abs(evaluated_guard_height - height) <= 0.05
assert 2.0 <= thickness <= 8.0
```

The thickness-direction attribute and requested value are also inspected in the modifier UI; exact wall-thickness sampling is mesh-resolution limited and receives the same `0.05 mm` tolerance when measured across paired inner/outer wall vertices.

- [ ] **Step 4: Install in the live scene, run verification, and save**

Execute `scripts/parametric_prop_guard.py` in the connected Blender session, run `self_check()`, restore defaults, then save `C:\Users\inouk\OneDrive\Documents\Untitled.blend` with `bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)`.

Expected: all assertions pass; the modifier exposes exactly three inputs; the viewport matches the imported default shape.

- [ ] **Step 5: Commit**

```powershell
git add scripts/parametric_prop_guard.py
git commit -m "test: verify parametric guard and fixed mount"
```

## Upgrade Boundary

The first version deliberately stretches the existing arms at extreme parameter values. When a second motor specification is available, retain `PG_FixedMount` as the interface contract, preserve the current hub as the default mount module, and replace only the node group's deformation internals with a procedural arm/guard generator plus interchangeable mount geometry.
