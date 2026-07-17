# Parametric Biomimetic Propeller Guard V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace V1's stretched guard body with a procedural, biomimetic 2–5-inch TPU guard while preserving the imported motor mount and mounting holes exactly.

**Architecture:** A new idempotent Blender Python script creates inspectable mount-selection attributes and one Geometry Nodes modifier on `halfApexPropGuardModify.001`. The node group retains the original hub plus short arm roots, generates a rounded rectangular bumper and three forked Bezier arm networks from physical inputs, and joins them with exact mesh booleans outside the fixed 10 mm mount radius. V1 remains recoverable by disabling the V2 modifier.

**Tech Stack:** Blender 5.2 Python API, Geometry Nodes, Python standard library, `mathutils`; no add-on, handler, or external dependency.

## Global Constraints

- Target object: `halfApexPropGuardModify.001` in `C:\Users\inouk\OneDrive\Documents\Untitled.blend`.
- Preserve every imported vertex within 10 mm of mount center `(2.204754, -2.317232)` bit-for-bit.
- Preserve mounting-hole centers, diameters, fastener clearances, and hub geometry.
- Propeller presets: 2, 2.5, 3, 3.5, 4, and 5 inches.
- Automatic radial clearance: `max(2 mm, 0.04 × propeller diameter)`.
- Derived outer diameter: `propeller diameter + 2 × (clearance + bumper thickness)`.
- Height range: 3–101.6 mm; default 12 mm.
- Bumper thickness: `max(3 × nozzle diameter, 1.2 mm)` through 8 mm; default 3.2 mm.
- Strength / Weight range: 0–1; default 0.5.
- Nozzle diameter range: 0.4–0.8 mm; default 0.4 mm.
- Minimum printable feature: `3 × nozzle diameter`.
- The 2-inch balanced default must estimate 7–8 g at TPU density 1.20–1.25 g/cm³.
- Output must be one connected manifold body that prints flat without supports.
- Preserve V1 and do not create a swappable mount system, add-on, runtime handler, external dependency, decorative Voronoi perforation, or FEA subsystem.

---

## File Structure

- Create `scripts/biomimetic_prop_guard_v2.py`: V2 setup, sizing formulas, Geometry Nodes construction, parameter access, and self-check.
- Modify `C:\Users\inouk\OneDrive\Documents\Untitled.blend`: store V2 attributes, node group, modifier, and defaults.
- Preserve `scripts/parametric_prop_guard.py`: V1 remains unchanged and can be disabled or restored.

### Task 1: Record the immutable mount and physical sizing model

**Files:**
- Create: `scripts/biomimetic_prop_guard_v2.py`
- Test: `scripts/biomimetic_prop_guard_v2.py --self-check`

**Interfaces:**
- Produces: `get_guard() -> bpy.types.Object`
- Produces: `mount_signature(obj) -> tuple[tuple[int, tuple[float, float, float]], ...]`
- Produces: `sizing(prop_inches, height, bumper, strength, nozzle, clearance_override=0.0) -> dict[str, float]`
- Produces point attribute `PG_V2_FixedMount` and face attribute `PG_V2_MountKeep`.

- [ ] **Step 1: Write the failing sizing and attribute self-check**

Create the file with constants and checks:

```python
import bpy
import math
import sys

OBJECT_NAME = "halfApexPropGuardModify.001"
CENTER = (2.204754, -2.317232)
FIXED_RADIUS = 10.0
MOUNT_KEEP_RADIUS = 14.0
PROP_PRESETS = (2.0, 2.5, 3.0, 3.5, 4.0, 5.0)
GROUP_NAME = "PG_BiomimeticGuardV2"
MODIFIER_NAME = "PG Biomimetic Guard V2"


def get_guard():
    obj = bpy.data.objects.get(OBJECT_NAME)
    assert obj and obj.type == "MESH", f"Missing mesh: {OBJECT_NAME}"
    return obj


def mount_signature(obj):
    cx, cy = CENTER
    return tuple(
        (vertex.index, tuple(vertex.co))
        for vertex in obj.data.vertices
        if math.hypot(vertex.co.x - cx, vertex.co.y - cy) <= FIXED_RADIUS
    )


def self_check():
    obj = get_guard()
    assert obj.data.attributes.get("PG_V2_FixedMount")
    assert obj.data.attributes.get("PG_V2_MountKeep")
    values = sizing(2.0, 12.0, 3.2, 0.5, 0.4)
    assert math.isclose(values["prop_mm"], 50.8)
    assert math.isclose(values["clearance"], 2.032)
    assert math.isclose(values["outer_diameter"], 61.264)
    assert math.isclose(values["min_feature"], 1.2)


if __name__ == "__main__" and "--self-check" in sys.argv:
    self_check()
```

- [ ] **Step 2: Run the check in the connected scene and verify it fails**

Run through Blender MCP or:

```powershell
& 'D:\Blender 5.2\blender.exe' --background 'C:\Users\inouk\OneDrive\Documents\Untitled.blend' --python 'scripts\biomimetic_prop_guard_v2.py' -- --self-check
```

Expected: nonzero exit with `Missing attribute` or `NameError: name 'sizing' is not defined`.

- [ ] **Step 3: Implement sizing and source attributes**

Add:

```python
def sizing(prop_inches, height, bumper, strength, nozzle, clearance_override=0.0):
    assert prop_inches in PROP_PRESETS
    assert 3.0 <= height <= 101.6
    assert 0.0 <= strength <= 1.0
    assert 0.4 <= nozzle <= 0.8
    prop_mm = prop_inches * 25.4
    min_feature = 3.0 * nozzle
    assert max(min_feature, 1.2) <= bumper <= 8.0
    clearance = clearance_override or max(2.0, 0.04 * prop_mm)
    inner_radius = prop_mm / 2.0 + clearance
    primary_width = max(min_feature, bumper * (0.55 + 0.25 * strength))
    fork_width = max(min_feature, primary_width * (0.65 + 0.15 * strength))
    return {
        "prop_mm": prop_mm,
        "height": height,
        "bumper": bumper,
        "strength": strength,
        "nozzle": nozzle,
        "min_feature": min_feature,
        "clearance": clearance,
        "inner_radius": inner_radius,
        "outer_diameter": 2.0 * (inner_radius + bumper),
        "primary_width": primary_width,
        "fork_width": fork_width,
        "root_radius": 12.0,
        "fork_radius": max(16.0, inner_radius * 0.68),
        "fork_angle": math.radians(18.0),
    }


def replace_attribute(mesh, name, data_type, domain):
    old = mesh.attributes.get(name)
    if old:
        mesh.attributes.remove(old)
    return mesh.attributes.new(name=name, type=data_type, domain=domain)


def build_source_attributes(obj):
    mesh = obj.data
    cx, cy = CENTER
    fixed = replace_attribute(mesh, "PG_V2_FixedMount", "FLOAT", "POINT")
    keep = replace_attribute(mesh, "PG_V2_MountKeep", "BOOLEAN", "FACE")
    for vertex in mesh.vertices:
        fixed.data[vertex.index].value = float(
            math.hypot(vertex.co.x - cx, vertex.co.y - cy) <= FIXED_RADIUS
        )
    for face in mesh.polygons:
        keep.data[face.index].value = all(
            math.hypot(mesh.vertices[index].co.x - cx, mesh.vertices[index].co.y - cy)
            <= MOUNT_KEEP_RADIUS
            for index in face.vertices
        )
```

Call `build_source_attributes(get_guard())` before `self_check()` in command-line mode.

- [ ] **Step 4: Run the check and verify it passes**

Run the Step 2 command. Expected: exit code 0.

- [ ] **Step 5: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: define biomimetic guard sizing contract"
```

### Task 2: Build the V2 modifier interface and retained mount

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`
- Test: `scripts/biomimetic_prop_guard_v2.py --self-check`

**Interfaces:**
- Consumes: `get_guard()`, `build_source_attributes(obj)`.
- Produces: `build_node_group() -> bpy.types.GeometryNodeTree`
- Produces: `install_modifier(obj) -> bpy.types.Modifier`
- Produces six float inputs named `Propeller Diameter (in)`, `Guard Height (mm)`, `Bumper Thickness (mm)`, `Strength / Weight`, `Nozzle Diameter (mm)`, and `Safety Clearance Override (mm)`.

- [ ] **Step 1: Extend the self-check so it fails without the V2 modifier**

Add:

```python
modifier = obj.modifiers.get(MODIFIER_NAME)
assert modifier and modifier.type == "NODES", "Missing V2 modifier"
group = modifier.node_group
assert group and group.name == GROUP_NAME
inputs = {
    item.name: item
    for item in group.interface.items_tree
    if item.item_type == "SOCKET"
    and item.in_out == "INPUT"
    and item.socket_type == "NodeSocketFloat"
}
assert set(inputs) == {
    "Propeller Diameter (in)",
    "Guard Height (mm)",
    "Bumper Thickness (mm)",
    "Strength / Weight",
    "Nozzle Diameter (mm)",
    "Safety Clearance Override (mm)",
}
```

- [ ] **Step 2: Run the check and verify `Missing V2 modifier`**

Run the Task 1 command. Expected: nonzero exit with `Missing V2 modifier`.

- [ ] **Step 3: Add node-building helpers and the interface**

Add these reusable helpers:

```python
PARAMETERS = {
    "Propeller Diameter (in)": (2.0, 5.0, 2.0),
    "Guard Height (mm)": (3.0, 101.6, 12.0),
    "Bumper Thickness (mm)": (1.2, 8.0, 3.2),
    "Strength / Weight": (0.0, 1.0, 0.5),
    "Nozzle Diameter (mm)": (0.4, 0.8, 0.4),
    "Safety Clearance Override (mm)": (0.0, 20.0, 0.0),
}


def node(nodes, node_type, name, operation=None):
    result = nodes.new(node_type)
    result.name = result.label = name
    if operation:
        result.operation = operation
    return result


def named_attribute(nodes, name, data_type):
    result = node(nodes, "GeometryNodeInputNamedAttribute", name)
    result.data_type = data_type
    result.inputs["Name"].default_value = name
    return result


def build_node_group():
    group = bpy.data.node_groups.get(GROUP_NAME)
    if group:
        assert group.bl_idname == "GeometryNodeTree"
    else:
        group = bpy.data.node_groups.new(GROUP_NAME, "GeometryNodeTree")
    group.is_modifier = True
    group.nodes.clear()
    group.interface.clear()
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for name, (minimum, maximum, default) in PARAMETERS.items():
        socket = group.interface.new_socket(
            name=name, in_out="INPUT", socket_type="NodeSocketFloat"
        )
        socket.min_value, socket.max_value, socket.default_value = minimum, maximum, default
    return group


def install_modifier(obj):
    modifier = obj.modifiers.get(MODIFIER_NAME)
    if modifier:
        assert modifier.type == "NODES"
    else:
        modifier = obj.modifiers.new(MODIFIER_NAME, "NODES")
    modifier.node_group = build_node_group()
    return modifier
```

- [ ] **Step 4: Retain only the mount and short arm roots**

Inside `build_node_group()`, create Group Input/Output, read `PG_V2_MountKeep`, and use `GeometryNodeSeparateGeometry` with domain `FACE`. Link its Selection output to Group Output temporarily:

```python
nodes, links = group.nodes, group.links
group_in = node(nodes, "NodeGroupInput", "Inputs")
group_out = node(nodes, "NodeGroupOutput", "Output")
keep = named_attribute(nodes, "PG_V2_MountKeep", "BOOLEAN")
separate = node(nodes, "GeometryNodeSeparateGeometry", "Keep Fixed Mount")
separate.domain = "FACE"
links.new(group_in.outputs["Geometry"], separate.inputs["Geometry"])
links.new(keep.outputs["Attribute"], separate.inputs["Selection"])
links.new(separate.outputs["Selection"], group_out.inputs["Geometry"])
```

Call `build_source_attributes(obj)` before `install_modifier(obj)`.

- [ ] **Step 5: Run the self-check and verify the interface passes**

Run the Task 1 command. Expected: exit code 0, with only the retained mount visible when V1 is hidden.

- [ ] **Step 6: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: add biomimetic guard modifier interface"
```

### Task 3: Generate the derived outer bumper

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`
- Test: `scripts/biomimetic_prop_guard_v2.py --self-check`

**Interfaces:**
- Consumes: Group Input parameter sockets from Task 2.
- Produces: `parameter_nodes(group, group_in) -> dict[str, bpy.types.NodeSocket]`
- Produces: `bumper_nodes(group, values) -> bpy.types.NodeSocketGeometry`

- [ ] **Step 1: Add a failing evaluated-diameter assertion**

Add parameter assignment and evaluated bounds helpers, then assert the 2-inch default outer diameter is 61.264 mm within 0.05 mm:

```python
def parameter_socket(modifier, name):
    return next(
        item for item in modifier.node_group.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == name
    )


def set_parameter(modifier, name, value):
    socket = parameter_socket(modifier, name)
    getattr(modifier.properties.inputs, socket.identifier).value = value
    modifier.id_data.update_tag()


def evaluated_vertices(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return tuple(tuple(vertex.co) for vertex in mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def dimensions(vertices):
    return tuple(
        max(co[axis] for co in vertices) - min(co[axis] for co in vertices)
        for axis in range(3)
    )


set_parameter(modifier, "Propeller Diameter (in)", 2.0)
set_parameter(modifier, "Guard Height (mm)", 12.0)
set_parameter(modifier, "Bumper Thickness (mm)", 3.2)
bpy.context.view_layer.update()
assert abs(max(dimensions(evaluated_vertices(obj))[:2]) - 61.264) <= 0.05
```

- [ ] **Step 2: Run and verify the diameter assertion fails**

Run the Task 1 command. Expected: nonzero exit because only the retained mount exists.

- [ ] **Step 3: Build exact sizing fields in the node group**

Implement `parameter_nodes()` with `ShaderNodeMath` nodes for these formulas:

```python
prop_mm = prop_inches * 25.4
automatic_clearance = max(2.0, prop_mm * 0.04)
clearance = clearance_override if clearance_override > 0.0 else automatic_clearance
minimum_feature = nozzle * 3.0
validated_bumper = max(bumper, minimum_feature)
inner_radius = prop_mm / 2.0 + clearance
bumper_center_radius = inner_radius + validated_bumper / 2.0
```

Use `ShaderNodeMath` operations `MULTIPLY`, `MAXIMUM`, `DIVIDE`, `ADD`, `GREATER_THAN`, and `MULTIPLY_ADD`; use a `GeometryNodeSwitch` with input type `FLOAT` for the override choice. Return sockets named `prop_mm`, `clearance`, `minimum_feature`, `bumper`, `inner_radius`, `bumper_center_radius`, `height`, and `strength`.

- [ ] **Step 4: Generate the flat-printable bumper**

Implement `bumper_nodes()`:

```python
def bumper_nodes(group, values):
    nodes, links = group.nodes, group.links
    circle = node(nodes, "GeometryNodeCurvePrimitiveCircle", "Bumper Centerline")
    circle.mode = "RADIUS"
    circle.inputs["Resolution"].default_value = 128
    profile = node(nodes, "GeometryNodeCurvePrimitiveQuadrilateral", "Rounded Rectangle Profile")
    profile.mode = "RECTANGLE"
    curve_to_mesh = node(nodes, "GeometryNodeCurveToMesh", "Solid Bumper")
    transform = node(nodes, "GeometryNodeTransform", "Place Bumper")
    links.new(values["bumper_center_radius"], circle.inputs["Radius"])
    links.new(values["bumper"], profile.inputs["Width"])
    links.new(values["height"], profile.inputs["Height"])
    links.new(circle.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    links.new(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
    links.new(curve_to_mesh.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (*CENTER, 0.0)
    return transform.outputs["Geometry"]
```

Join the bumper with the retained mount for this task using `GeometryNodeJoinGeometry`.

- [ ] **Step 5: Run the check and verify derived diameter and height**

Run the Task 1 command. Expected: exit code 0; evaluated diameter 61.264 ±0.05 mm and height 12 ±0.05 mm.

- [ ] **Step 6: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: generate derived TPU bumper"
```

### Task 4: Generate forked biomimetic arms and organic cells

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`
- Test: `scripts/biomimetic_prop_guard_v2.py --self-check`

**Interfaces:**
- Consumes: `values` sockets from `parameter_nodes()` and bumper geometry from `bumper_nodes()`.
- Produces: `arm_nodes(group, values) -> bpy.types.NodeSocketGeometry`.
- Produces three primary arms, six fork branches, and rounded junction pads.

- [ ] **Step 1: Add a failing structural node assertion**

Add:

```python
required = {
    "Primary Arm",
    "Upper Fork",
    "Lower Fork",
    "Threefold Arm Instances",
    "Union V2 Body",
}
assert required <= {node.name for node in group.nodes}, "Missing biomimetic arm network"
```

- [ ] **Step 2: Run and verify `Missing biomimetic arm network`**

Run the Task 1 command. Expected: nonzero exit with that message.

- [ ] **Step 3: Add curve-segment and tapered-profile helpers**

Implement these helpers using supported Blender 5.2 nodes:

```python
def bezier_segment(nodes, links, name, start, start_handle, end, end_handle):
    curve = node(nodes, "GeometryNodeCurvePrimitiveBezierSegment", name)
    for socket, value in (
        ("Start", start),
        ("Start Handle", start_handle),
        ("End", end),
        ("End Handle", end_handle),
    ):
        curve.inputs[socket].default_value = value
    return curve


def tapered_curve_mesh(group, curve_socket, width_socket, height_socket, name):
    nodes, links = group.nodes, group.links
    spline = node(nodes, "GeometryNodeSplineParameter", f"{name} Factor")
    scale = node(nodes, "ShaderNodeMapRange", f"{name} Taper")
    scale.clamp = True
    scale.inputs["From Min"].default_value = 0.0
    scale.inputs["From Max"].default_value = 1.0
    scale.inputs["To Min"].default_value = 1.25
    scale.inputs["To Max"].default_value = 0.85
    radius = node(nodes, "GeometryNodeSetCurveRadius", f"{name} Radius")
    profile = node(nodes, "GeometryNodeCurvePrimitiveQuadrilateral", f"{name} Profile")
    profile.mode = "RECTANGLE"
    mesh = node(nodes, "GeometryNodeCurveToMesh", name)
    links.new(curve_socket, radius.inputs["Curve"])
    links.new(spline.outputs["Factor"], scale.inputs["Value"])
    links.new(scale.outputs["Result"], radius.inputs["Radius"])
    links.new(width_socket, profile.inputs["Width"])
    links.new(height_socket, profile.inputs["Height"])
    links.new(radius.outputs["Curve"], mesh.inputs["Curve"])
    links.new(profile.outputs["Curve"], mesh.inputs["Profile Curve"])
    return mesh.outputs["Mesh"]
```

- [ ] **Step 4: Build one local Y-shaped arm motif**

Use node math for dynamic radii, but keep the approved topology fixed: root radius 12 mm, fork radius `max(16, inner_radius × 0.68)`, and endpoints on the inner bumper radius at ±18°. The local-X motif uses:

```python
primary_start = (12.0, 0.0, 0.0)
primary_start_handle = (14.5, 0.0, 0.0)
primary_end_handle_fraction = 0.82
fork_angle = math.radians(18.0)
```

Construct `Primary Arm`, `Upper Fork`, and `Lower Fork` with Bezier Segment nodes. Use `ShaderNodeMath` `SINE`/`COSINE` and `ShaderNodeCombineXYZ` so fork endpoints follow `inner_radius`. Use `tapered_curve_mesh()` separately for the primary and forks. Compute widths in nodes:

```python
minimum_feature = nozzle * 3.0
primary_width = max(minimum_feature, bumper * (0.55 + 0.25 * strength))
fork_width = max(minimum_feature, primary_width * (0.65 + 0.15 * strength))
```

Join the three local meshes. Their curved spacing forms the organic material-removal cells; do not add random Voronoi cuts.

- [ ] **Step 5: Instance the motif threefold and add rounded junction pads**

Create three coincident points with `GeometryNodeMeshLine`, derive Z rotation as `Index × 2π/3`, instance the local motif with `GeometryNodeInstanceOnPoints`, realize it, and translate by `CENTER`. Name the Instance node `Threefold Arm Instances`.

At each fork and bumper attachment, instance vertical `GeometryNodeMeshCylinder` pads with radius `1.2 × fork_width`, depth equal to height, and 32 vertices. These pads create printable rounded load-spreading junctions.

- [ ] **Step 6: Union outside the fixed region**

Use `GeometryNodeMeshBoolean` nodes with `operation = "UNION"` and `solver = "EXACT"` to combine bumper, realized arm network, junction pads, and retained mount. Name the final node `Union V2 Body`. Keep all procedural intersections outside the fixed 10 mm radius; arm overlap begins at 12 mm and the retained source extends through 14 mm.

- [ ] **Step 7: Run the structural check and visually inspect the default**

Run the Task 1 command. Expected: exit code 0. In the viewport, confirm three tapered primary arms, six curved forks, continuous bumper, open organic cells, rounded junctions, and unchanged hub.

- [ ] **Step 8: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "feat: generate biomimetic forked arm network"
```

### Task 5: Validate presets, manufacturability, weight, and saved scene

**Files:**
- Modify: `scripts/biomimetic_prop_guard_v2.py`
- Modify: `C:\Users\inouk\OneDrive\Documents\Untitled.blend`
- Test: `scripts/biomimetic_prop_guard_v2.py --self-check`

**Interfaces:**
- Consumes: V2 modifier, sizing formulas, and evaluated geometry.
- Produces: `mesh_report(obj) -> dict[str, object]` and a self-check that restores the 2-inch balanced defaults in `finally`.

- [ ] **Step 1: Add failing mount, topology, clearance, and mass assertions**

Add:

```python
baseline_coordinates = {coordinate for _index, coordinate in mount_signature(obj)}
report = mesh_report(obj)
assert baseline_coordinates <= report["coordinates"], "Fixed mount coordinates changed"
assert report["components"] == 1, report["components"]
assert report["manifold"], "V2 output is not manifold"
mass_low = report["volume_mm3"] * 0.00120
mass_high = report["volume_mm3"] * 0.00125
assert 7.0 <= mass_low and mass_high <= 8.0, (mass_low, mass_high)
```

- [ ] **Step 2: Run and verify at least one new assertion fails**

Run the Task 1 command. Expected: `NameError: name 'mesh_report' is not defined`.

- [ ] **Step 3: Implement the complete mesh report**

Use `bmesh` for manifold, component, and volume checks:

```python
import bmesh


def mesh_report(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        unseen = set(bm.verts)
        components = 0
        while unseen:
            components += 1
            stack = [unseen.pop()]
            while stack:
                current = stack.pop()
                for edge in current.link_edges:
                    other = edge.other_vert(current)
                    if other in unseen:
                        unseen.remove(other)
                        stack.append(other)
        dimensions_mm = tuple(
            max(v.co[axis] for v in bm.verts) - min(v.co[axis] for v in bm.verts)
            for axis in range(3)
        )
        return {
            "coordinates": {tuple(v.co) for v in bm.verts},
            "components": components,
            "manifold": all(len(edge.link_faces) == 2 for edge in bm.edges),
            "dimensions": dimensions_mm,
            "volume_mm3": abs(bm.calc_volume(signed=True)),
        }
    finally:
        bm.free()
        evaluated.to_mesh_clear()
```

- [ ] **Step 4: Test every propeller preset and manufacturing boundary**

Use this matrix:

```python
cases = [
    (prop, 12.0, 3.2, 0.5, 0.4, 0.0)
    for prop in PROP_PRESETS
] + [
    (2.0, 3.0, 2.4, 0.0, 0.8, 0.0),
    (2.0, 101.6, 8.0, 1.0, 0.8, 0.0),
    (5.0, 3.0, 2.4, 0.0, 0.8, 0.0),
    (5.0, 101.6, 8.0, 1.0, 0.8, 0.0),
    (3.5, 12.0, 3.2, 0.5, 0.4, 3.0),
]
```

For each case:

1. Set all six modifier values and update the dependency graph.
2. Assert all baseline fixed coordinates are present exactly.
3. Assert `components == 1` and `manifold is True`.
4. Assert measured XY diameter equals `sizing(...)["outer_diameter"]` within 0.1 mm.
5. Assert measured height equals the requested height within 0.1 mm.
6. Assert `primary_width`, `fork_width`, and bumper are each at least `min_feature`.
7. For the 2-inch balanced default, compute mass range as `volume_mm3 × 0.00120` through `volume_mm3 × 0.00125` and assert it overlaps 7–8 g.

Restore defaults in `finally`.

- [ ] **Step 5: Verify visual quality and print orientation**

In the connected Blender scene inspect these cases from top, bottom, and side views:

- 2-inch balanced default;
- 5-inch balanced default;
- 2-inch minimum-height/light case;
- 5-inch maximum-height/strong case.

Confirm no folded faces, disconnected junctions, blade-clearance intrusion, unsupported downward overhangs, or sharp internal corners. Export the 2-inch and 5-inch balanced cases to temporary STL files and inspect them in the user's slicer with 0.4 and 0.8 mm nozzle profiles. Do not retain temporary STL files in the repository.

- [ ] **Step 6: Install, verify, restore defaults, and save**

Execute the script in the connected Blender scene, run `self_check()`, restore the 2-inch balanced defaults, then save:

```python
bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\inouk\OneDrive\Documents\Untitled.blend")
```

Reopen the saved file headlessly and run `self_check()` without rebuilding first. Expected: Blender exits 0 and prints `PG_V2_SELF_CHECK_OK`.

- [ ] **Step 7: Print-test handoff**

Export one arm-to-bumper junction coupon and the complete 2-inch balanced prototype. Record the parameter values and estimated mass in Blender custom properties on the V2 object. Physical coupon acceptance requires no layer separation, no permanent set after repeated hand deflection to half the safety-clearance budget, and no crack initiation at the fork or bumper junction.

- [ ] **Step 8: Commit**

```powershell
git add scripts/biomimetic_prop_guard_v2.py
git commit -m "test: validate biomimetic guard presets"
```

## Upgrade Boundary

Do not add material-specific FEA or interchangeable mounts in V2. After a TPU brand, hardness, perimeter count, print temperature, and physical coupon results are known, a later plan may calibrate the Strength / Weight mapping and flex budget from measured data without changing the fixed-mount interface.
