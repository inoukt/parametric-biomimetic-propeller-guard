# Open-Arc Motor Mount V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the disconnected imported hub with a procedural 12 mm four-hole motor plate and restore an open, maximum-210-degree protector.

**Architecture:** Modify the existing `PG_BiomimeticGuardV2` Geometry Nodes generator in place. A procedural plate with measured recessed M2 holes replaces the retained source mount; the existing D-profile bumper is trimmed to an arc and the three branch motifs are rotated within that arc. V1 remains recoverable by disabling the V2 modifier.

**Tech Stack:** Blender 5.2 Python API, Geometry Nodes, `bmesh`, Python standard library.

## Global Constraints

- Motor center is local `(0, 0)`.
- Four hole centers are `(±6, 0)` and `(0, ±6)` mm.
- Imported hole profile is 3.0 mm through diameter with a 4.5 mm lower recess from Z `-3.0034075` to `-1.6034075`; top face is Z `0.2965926`.
- Protector coverage is at most 210 degrees, from approximately 30 to 240 degrees in local coordinates.
- Keep all six V2 user parameters and their current ranges/defaults.
- Add no dependency, add-on, handler, interchangeable mount framework, or FEA workflow.
- Only the primary agent mutates the connected Blender scene.

---

### Task 1: Replace the immutable-source contract with measured mount constants

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`

**Interfaces:**
- Produces: `hole_centers() -> tuple[tuple[float, float], ...]`.
- Produces constants consumed by Task 2: `MOTOR_CENTER`, `PLATE_RADIUS`, `HOLE_CIRCLE_DIAMETER`, `THROUGH_RADIUS`, `RECESS_RADIUS`, `RECESS_TOP_Z`, `MOUNT_Z_MIN`, `MOUNT_Z_MAX`.

- [ ] **Step 1: Add a failing physical-model check**

At the start of `self_check()`, add:

```python
assert hole_centers() == ((6.0, 0.0), (0.0, 6.0), (-6.0, 0.0), (0.0, -6.0))
for index, center in enumerate(hole_centers()):
    opposite = hole_centers()[(index + 2) % 4]
    assert math.dist(center, opposite) == 12.0
```

- [ ] **Step 2: Run the check and verify it fails**

Run:

```powershell
& 'D:\Blender 5.2\blender.exe' --background 'C:\Users\inouk\OneDrive\Documents\Untitled.blend' --python 'C:\Users\inouk\OneDrive\Documents\BlenderMCP\scripts\biomimetic_prop_guard_v2.py' -- --verify-only --self-check
```

Expected: nonzero exit with `NameError: name 'hole_centers' is not defined`.

- [ ] **Step 3: Add the measured constants and helper**

Replace the old fixed-source constants with:

```python
MOTOR_CENTER = (0.0, 0.0)
PLATE_RADIUS = 10.0
HOLE_CIRCLE_DIAMETER = 12.0
THROUGH_RADIUS = 1.5
RECESS_RADIUS = 2.25
MOUNT_Z_MIN = -3.0034074783325195
RECESS_TOP_Z = -1.6034074783325195
MOUNT_Z_MAX = 0.2965925931930542
ARC_START = math.radians(30.0)
ARC_END = math.radians(240.0)


def hole_centers():
    radius = HOLE_CIRCLE_DIAMETER / 2.0
    return ((radius, 0.0), (0.0, radius), (-radius, 0.0), (0.0, -radius))
```

Delete `FIXED_RADIUS`, `MOUNT_KEEP_RADIUS`, `mount_signature()`, `replace_attribute()`, and `build_source_attributes()`. Change `install()` to call only `install_modifier(get_guard())`.

- [ ] **Step 4: Run the pure-Python syntax check**

Run:

```powershell
python -m py_compile scripts/biomimetic_prop_guard_v2.py
```

Expected: exit code 0.

- [ ] **Step 5: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "refactor: define measured v3 motor geometry"
```

---

### Task 2: Generate the procedural plate and recessed M2 holes

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`

**Interfaces:**
- Consumes: constants and `hole_centers()` from Task 1.
- Produces: `motor_plate_nodes(group) -> bpy.types.NodeSocketGeometry`.
- Produces: `hole_report(obj) -> tuple[dict[str, object], ...]` for validation.

- [ ] **Step 1: Add failing node and measurement checks**

Replace old fixed-attribute assertions in `self_check()` with:

```python
required = {"V3 Motor Plate", "V3 Through Cutters", "V3 Recess Cutters", "V3 Mount"}
assert required <= {node.name for node in group.nodes}
holes = hole_report(obj)
assert len(holes) == 4
for measured, expected in zip(holes, hole_centers()):
    assert math.dist(measured["center"], expected) <= 0.02
    assert abs(measured["through_radius"] - THROUGH_RADIUS) <= 0.03
    assert abs(measured["recess_radius"] - RECESS_RADIUS) <= 0.03
```

- [ ] **Step 2: Run the live check and verify it fails**

Execute `install()` and `self_check()` in the connected scene.

Expected: failure because `V3 Motor Plate` does not exist.

- [ ] **Step 3: Build one plate and two four-hole cutter sets**

Implement `motor_plate_nodes()` using existing `node()`, `combine_xyz()`, and `union_node()` helpers:

```python
def motor_plate_nodes(group):
    nodes, links = group.nodes, group.links
    plate = node(nodes, "GeometryNodeMeshCylinder", "V3 Motor Plate")
    plate.inputs["Vertices"].default_value = 128
    plate.inputs["Radius"].default_value = PLATE_RADIUS
    plate.inputs["Depth"].default_value = MOUNT_Z_MAX - MOUNT_Z_MIN
    place_plate = node(nodes, "GeometryNodeTransform", "Place V3 Motor Plate")
    place_plate.inputs["Translation"].default_value = (
        0.0,
        0.0,
        (MOUNT_Z_MIN + MOUNT_Z_MAX) / 2.0,
    )
    links.new(plate.outputs["Mesh"], place_plate.inputs["Geometry"])

    points_curve = node(nodes, "GeometryNodeCurvePrimitiveCircle", "V3 Hole Circle")
    points_curve.mode = "RADIUS"
    points_curve.inputs["Resolution"].default_value = 4
    points_curve.inputs["Radius"].default_value = HOLE_CIRCLE_DIAMETER / 2.0
    points = node(nodes, "GeometryNodeCurveToPoints", "V3 Hole Points")
    points.mode = "EVALUATED"
    links.new(points_curve.outputs["Curve"], points.inputs["Curve"])

    through = node(nodes, "GeometryNodeMeshCylinder", "V3 Through Cutter")
    through.inputs["Vertices"].default_value = 48
    through.inputs["Radius"].default_value = THROUGH_RADIUS
    through.inputs["Depth"].default_value = MOUNT_Z_MAX - MOUNT_Z_MIN + 0.2
    place_through = node(nodes, "GeometryNodeTransform", "Place V3 Through Cutter")
    place_through.inputs["Translation"].default_value = (0.0, 0.0, (MOUNT_Z_MIN + MOUNT_Z_MAX) / 2.0)
    links.new(through.outputs["Mesh"], place_through.inputs["Geometry"])

    recess = node(nodes, "GeometryNodeMeshCylinder", "V3 Recess Cutter")
    recess.inputs["Vertices"].default_value = 48
    recess.inputs["Radius"].default_value = RECESS_RADIUS
    recess.inputs["Depth"].default_value = RECESS_TOP_Z - MOUNT_Z_MIN + 0.1
    place_recess = node(nodes, "GeometryNodeTransform", "Place V3 Recess Cutter")
    place_recess.inputs["Translation"].default_value = (0.0, 0.0, (MOUNT_Z_MIN + RECESS_TOP_Z) / 2.0 - 0.05)
    links.new(recess.outputs["Mesh"], place_recess.inputs["Geometry"])

    through_instances = node(nodes, "GeometryNodeInstanceOnPoints", "Instance V3 Through Cutters")
    through_realized = node(nodes, "GeometryNodeRealizeInstances", "V3 Through Cutters")
    links.new(points.outputs["Points"], through_instances.inputs["Points"])
    links.new(place_through.outputs["Geometry"], through_instances.inputs["Instance"])
    links.new(through_instances.outputs["Instances"], through_realized.inputs["Geometry"])

    recess_instances = node(nodes, "GeometryNodeInstanceOnPoints", "Instance V3 Recess Cutters")
    recess_realized = node(nodes, "GeometryNodeRealizeInstances", "V3 Recess Cutters")
    links.new(points.outputs["Points"], recess_instances.inputs["Points"])
    links.new(place_recess.outputs["Geometry"], recess_instances.inputs["Instance"])
    links.new(recess_instances.outputs["Instances"], recess_realized.inputs["Geometry"])

    subtract_through = node(nodes, "GeometryNodeMeshBoolean", "Cut V3 Through Holes")
    subtract_through.operation = "DIFFERENCE"
    subtract_through.solver = "EXACT"
    links.new(place_plate.outputs["Geometry"], subtract_through.inputs[0])
    links.new(through_realized.outputs["Geometry"], subtract_through.inputs[1])

    mount = node(nodes, "GeometryNodeMeshBoolean", "V3 Mount")
    mount.operation = "DIFFERENCE"
    mount.solver = "EXACT"
    links.new(subtract_through.outputs["Mesh"], mount.inputs[0])
    links.new(recess_realized.outputs["Geometry"], mount.inputs[1])
    return mount.outputs["Mesh"]
```

Replace `closed_mount_nodes()` and its call in `build_node_group()` with `motor_plate_nodes(group)`. Remove the `PG_V2_MountKeep` named-attribute and Separate Geometry nodes.

- [ ] **Step 4: Add the smallest evaluated-hole measurement helper**

Implement `hole_report()` by reading evaluated vertices at the known Z rings:

```python
def hole_report(obj):
    vertices = evaluated_vertices(obj)
    reports = []
    for expected_x, expected_y in hole_centers():
        top = [co for co in vertices if abs(co[2] - MOUNT_Z_MAX) < 1e-4 and 1.2 < math.hypot(co[0] - expected_x, co[1] - expected_y) < 1.8]
        bottom = [co for co in vertices if abs(co[2] - MOUNT_Z_MIN) < 1e-4 and 2.0 < math.hypot(co[0] - expected_x, co[1] - expected_y) < 2.5]
        assert top and bottom
        center = (sum(co[0] for co in top) / len(top), sum(co[1] for co in top) / len(top))
        reports.append({
            "center": center,
            "through_radius": sum(math.hypot(co[0] - center[0], co[1] - center[1]) for co in top) / len(top),
            "recess_radius": sum(math.hypot(co[0] - expected_x, co[1] - expected_y) for co in bottom) / len(bottom),
        })
    return tuple(reports)
```

- [ ] **Step 5: Run `self_check()`**

Expected: four centers within 0.02 mm; radii within 0.03 mm; final mesh remains manifold.

- [ ] **Step 6: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: generate 12mm recessed motor mount"
```

---

### Task 3: Trim the bumper and connect every branch to the plate

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`

**Interfaces:**
- Consumes: `motor_plate_nodes(group)` and existing parameter/branch/profile helpers.
- Produces named node `Union Mount and Arms` for isolated connectivity validation.
- Produces: `node_mesh_report(obj, node_name) -> dict[str, object]`.

- [ ] **Step 1: Add failing arc and isolated-connectivity checks**

Add to `self_check()`:

```python
assert "Open Bumper Arc" in group.nodes
mount_arms = node_mesh_report(obj, "Union Mount and Arms")
assert mount_arms["components"] == 1, mount_arms
assert mount_arms["nonmanifold_edges"] == 0, mount_arms
outer_angles = [
    math.degrees(math.atan2(co[1], co[0])) % 360.0
    for co in node_mesh_report(obj, "Place Bumper")["coordinates"]
]
assert outer_angles
assert min(outer_angles) >= 29.0
assert max(outer_angles) <= 241.0
```

- [ ] **Step 2: Run the check and verify the full-circle failure**

Expected: `Open Bumper Arc` is missing.

- [ ] **Step 3: Trim the native circle to the approved arc**

In `bumper_nodes()`, insert a `GeometryNodeTrimCurve` between `Bumper Centerline` and `Solid Bumper`:

```python
trim = node(nodes, "GeometryNodeTrimCurve", "Open Bumper Arc")
trim.mode = "FACTOR"
trim.inputs["Start"].default_value = math.degrees(ARC_START) / 360.0
trim.inputs["End"].default_value = math.degrees(ARC_END) / 360.0
links.new(circle.outputs["Curve"], trim.inputs["Curve"])
links.new(trim.outputs["Curve"], curve_to_mesh.inputs["Curve"])
curve_to_mesh.inputs["Fill Caps"].default_value = True
```

Remove the old direct circle-to-mesh link.

- [ ] **Step 4: Move roots into the plate and distribute branches inside the arc**

In `arm_nodes()`:

```python
primary_curve = bezier_segment(
    group,
    "Primary Arm Curve",
    (9.0, 0.0, 0.0),
    (12.0, 0.0, 0.0),
    combine_xyz(group, "Primary End Handle", primary_end_handle_x, 0.0, 0.0),
    combine_xyz(group, "Primary Fork Point", fork_radius, 0.0, 0.0),
)

rotation_z = math_node(
    group,
    "Arm Rotation Step",
    "MULTIPLY",
    index.outputs["Index"],
    math.radians(85.0),
)
rotation_z = math_node(group, "Arm Rotation", "ADD", rotation_z, math.radians(50.0))
```

Center the rounded root pad at local `(9.5, 0, 0)` and retain its existing bounded radius. These rotations place the three motifs at 50, 135, and 220 degrees; their ±18-degree fork endpoints remain inside the 30–240 degree bumper arc.

In `build_node_group()`, union the procedural plate and arms before the bumper:

```python
mount_arms = union_node(group, "Union Mount and Arms", motor_plate, arms)
final = union_node(group, "Union V3 Body", mount_arms, bumper)
links.new(final, group_out.inputs["Geometry"])
```

- [ ] **Step 5: Add isolated-node reporting by temporarily rewiring the group output**

Implement:

```python
def node_mesh_report(obj, node_name):
    group = obj.modifiers[MODIFIER_NAME].node_group
    output = group.nodes["Output"]
    original = output.inputs["Geometry"].links[0].from_socket
    try:
        for link in tuple(output.inputs["Geometry"].links):
            group.links.remove(link)
        group.links.new(group.nodes[node_name].outputs[0], output.inputs["Geometry"])
        bpy.context.view_layer.update()
        return mesh_report(obj)
    finally:
        for link in tuple(output.inputs["Geometry"].links):
            group.links.remove(link)
        group.links.new(original, output.inputs["Geometry"])
        bpy.context.view_layer.update()
```

Also add the evaluated coordinates to `mesh_report()` so the isolated bumper can be inspected without another rewiring helper:

```python
"coordinates": tuple(tuple(vertex.co) for vertex in mesh.vertices),
```

- [ ] **Step 6: Run `self_check()` and inspect top/underside views**

Expected: open lower-right sector; capped arc ends; all three roots visibly overlap the plate; `Union Mount and Arms` is one manifold component.

- [ ] **Step 7: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: restore connected open-arc protector"
```

---

### Task 4: Validate every parameter boundary and save the scene

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`
- Update artifact: `C:\Users\inouk\OneDrive\Documents\Untitled.blend`

**Interfaces:**
- Consumes: `self_check()`, `mesh_report()`, `hole_report()`, `node_mesh_report()`, `set_parameter()`, and `sizing()`.
- Produces the completed saved Blender scene and final verification evidence.

- [ ] **Step 1: Run the final matrix in the connected scene**

Use:

```python
cases = [
    *((prop, 12.0, 2.2, 0.5, 0.4, 0.0) for prop in PROP_PRESETS),
    (2.0, 3.3, 1.2, 0.0, 0.4, 0.0),
    (2.0, 101.6, 8.0, 1.0, 0.8, 0.0),
    (5.0, 3.3, 1.2, 0.0, 0.4, 0.0),
    (5.0, 101.6, 8.0, 1.0, 0.8, 0.0),
    (2.5, 3.3, 1.2, 0.0, 0.8, 0.0),
    (3.5, 12.0, 2.2, 0.5, 0.4, 3.0),
    (4.3, 24.0, 2.0, 0.25, 0.6, 0.0),
]
```

For each case, assert:

```python
report["components"] == 1
report["nonmanifold_edges"] == 0
node_mesh_report(obj, "Union Mount and Arms")["components"] == 1
abs(2.0 * max(math.hypot(co[0], co[1]) for co in report["coordinates"]) - sizing(*case)["outer_diameter"]) <= 0.06
abs(report["dimensions"][2] - case[1]) <= 0.06
all(math.dist(measured["center"], expected) <= 0.02 for measured, expected in zip(hole_report(obj), hole_centers()))
```

Also assert all isolated `Place Bumper` vertices remain between 29 and 241 degrees. Do not compare the open guard's XY bounding box with the full derived diameter; validate its maximum radial envelope as shown above.

- [ ] **Step 2: Restore balanced defaults and record mass**

Restore the six defaults in `PARAMETERS`, run `self_check()`, and write evaluated volume and estimated TPU mass at densities 1.20 and 1.25 g/cm³ to object custom properties. Report the result; do not add material solely to reach 7 g.

- [ ] **Step 3: Save and headlessly reopen**

In Blender:

```python
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\inouk\OneDrive\Documents\Untitled.blend")
```

Then run:

```powershell
& 'D:\Blender 5.2\blender.exe' --background 'C:\Users\inouk\OneDrive\Documents\Untitled.blend' --python 'C:\Users\inouk\OneDrive\Documents\BlenderMCP\scripts\biomimetic_prop_guard_v2.py' -- --verify-only --self-check
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py docs/superpowers/specs/2026-07-17-open-arc-motor-mount-v3-design.md docs/superpowers/plans/2026-07-17-open-arc-motor-mount-v3.md
git commit -m "test: verify open-arc motor mount v3"
```
