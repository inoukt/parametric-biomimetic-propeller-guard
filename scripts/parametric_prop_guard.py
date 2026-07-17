import bpy
import math
import sys
from collections import defaultdict
from mathutils import Vector

OBJECT_NAME = "halfApexPropGuardModify.001"
CENTER = (2.204754, -2.317232)
FIXED_RADIUS = 10.0
GUARD_RADIUS = 25.0
BASE_DIAMETER = 86.906372
BASE_HEIGHT = 26.400002
BASE_THICKNESS = 4.0
GROUP_NAME = "PG_ParametricGuard"
MODIFIER_NAME = "PG Parametric Guard"
PARAMETERS = {
    "Guard Diameter (mm)": (50.8, 1_000_000.0, BASE_DIAMETER),
    "Guard Height (mm)": (3.0, 101.6, BASE_HEIGHT),
    "Wall Thickness (mm)": (2.0, 8.0, BASE_THICKNESS),
}


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
    ring_center = Vector(
        (
            (min(v.co.x for v in mesh.vertices) + max(v.co.x for v in mesh.vertices)) / 2.0,
            (min(v.co.y for v in mesh.vertices) + max(v.co.y for v in mesh.vertices)) / 2.0,
        )
    )
    fixed = point_attribute(mesh, "PG_FixedMount", "FLOAT")
    guard = point_attribute(mesh, "PG_GuardWeight", "FLOAT")
    inner = point_attribute(mesh, "PG_InnerWeight", "FLOAT")
    direction = point_attribute(mesh, "PG_ThicknessDirection", "FLOAT_VECTOR")
    normal_sums = defaultdict(lambda: Vector((0.0, 0.0, 0.0)))
    outer_vertices = set()

    for face in mesh.polygons:
        radial = Vector((face.center.x - cx, face.center.y - cy))
        ring_radial = Vector((face.center.x, face.center.y)) - ring_center
        dot = face.normal.x * radial.x + face.normal.y * radial.y
        ring_dot = face.normal.x * ring_radial.x + face.normal.y * ring_radial.y
        if ring_radial.length > 20.0 and abs(face.normal.z) < 0.45 and ring_dot > 0.0:
            outer_vertices.update(face.vertices)
        if radial.length > 20.0 and abs(face.normal.z) < 0.45 and dot < 0.0 and ring_dot < 0.0:
            xy_normal = Vector((face.normal.x, face.normal.y, 0.0))
            if xy_normal.length:
                xy_normal.normalize()
                for vertex_index in face.vertices:
                    normal_sums[vertex_index] += xy_normal

    parent = list(range(len(mesh.vertices)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in mesh.edges:
        a, b = edge.vertices
        if (mesh.vertices[a].co - mesh.vertices[b].co).length < 0.1:
            a, b = find(a), find(b)
            if a != b:
                parent[b] = a

    clusters = defaultdict(list)
    for index in range(len(mesh.vertices)):
        clusters[find(index)].append(index)
    for members in clusters.values():
        protected = any(
            index in outer_vertices
            or math.hypot(mesh.vertices[index].co.x - cx, mesh.vertices[index].co.y - cy) <= FIXED_RADIUS
            for index in members
        )
        combined = sum((normal_sums[index] for index in members), Vector((0.0, 0.0, 0.0)))
        if protected or not combined.length:
            combined = Vector((0.0, 0.0, 0.0))
        else:
            combined.normalize()
        for index in members:
            normal_sums[index] = combined.copy()

    for vertex in mesh.vertices:
        radius = math.hypot(vertex.co.x - cx, vertex.co.y - cy)
        fixed.data[vertex.index].value = float(radius <= FIXED_RADIUS)
        guard.data[vertex.index].value = smoothstep(
            (radius - FIXED_RADIUS) / (GUARD_RADIUS - FIXED_RADIUS)
        )
        vector = normal_sums[vertex.index]
        is_inner = bool(vector.length) and vertex.index not in outer_vertices
        inner.data[vertex.index].value = float(is_inner)
        if is_inner:
            vector.normalize()
        direction.data[vertex.index].vector = vector


def _node(nodes, node_type, label, operation=None):
    node = nodes.new(node_type)
    node.label = label
    node.name = label
    if operation:
        node.operation = operation
    return node


def _named_attribute(nodes, name, data_type):
    node = _node(nodes, "GeometryNodeInputNamedAttribute", name)
    node.data_type = data_type
    node.inputs["Name"].default_value = name
    return node


def _guard_z_min(obj):
    weights = obj.data.attributes["PG_GuardWeight"].data
    return min(v.co.z for v in obj.data.vertices if weights[v.index].value >= 0.999)


def build_node_group():
    obj = get_guard()
    group = bpy.data.node_groups.get(GROUP_NAME)
    if group:
        assert group.bl_idname == "GeometryNodeTree", f"Wrong node group type: {GROUP_NAME}"
    else:
        group = bpy.data.node_groups.new(GROUP_NAME, "GeometryNodeTree")
    group.is_modifier = True
    group.nodes.clear()
    group.interface.clear()

    interface = group.interface
    interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for name, (minimum, maximum, default) in PARAMETERS.items():
        socket = interface.new_socket(name=name, in_out="INPUT", socket_type="NodeSocketFloat")
        socket.min_value = minimum
        socket.max_value = maximum
        socket.default_value = default

    nodes, links = group.nodes, group.links
    group_input = _node(nodes, "NodeGroupInput", "Parameters")
    group_output = _node(nodes, "NodeGroupOutput", "Result")
    position = _node(nodes, "GeometryNodeInputPosition", "Baseline Position")
    guard = _named_attribute(nodes, "PG_GuardWeight", "FLOAT")
    inner = _named_attribute(nodes, "PG_InnerWeight", "FLOAT")
    direction = _named_attribute(nodes, "PG_ThicknessDirection", "FLOAT_VECTOR")

    radial = _node(nodes, "ShaderNodeVectorMath", "Position From Mount Center", "SUBTRACT")
    radial.inputs[1].default_value = (*CENTER, 0.0)
    radial_xy = _node(nodes, "ShaderNodeVectorMath", "XY Radius Only", "MULTIPLY")
    radial_xy.inputs[1].default_value = (1.0, 1.0, 0.0)
    diameter_ratio = _node(nodes, "ShaderNodeMath", "Diameter Ratio", "DIVIDE")
    diameter_ratio.inputs[1].default_value = BASE_DIAMETER
    diameter_delta = _node(nodes, "ShaderNodeMath", "Diameter Scale Delta", "SUBTRACT")
    diameter_delta.inputs[1].default_value = 1.0
    diameter_offset = _node(nodes, "ShaderNodeVectorMath", "Diameter Offset", "SCALE")
    diameter_weighted = _node(nodes, "ShaderNodeVectorMath", "Blend Diameter Into Arms", "SCALE")

    separate = _node(nodes, "ShaderNodeSeparateXYZ", "Baseline Z")
    z_from_bottom = _node(nodes, "ShaderNodeMath", "Z From Guard Bottom", "SUBTRACT")
    z_from_bottom.inputs[1].default_value = _guard_z_min(obj)
    height_ratio = _node(nodes, "ShaderNodeMath", "Height Ratio", "DIVIDE")
    height_ratio.inputs[1].default_value = BASE_HEIGHT
    height_delta = _node(nodes, "ShaderNodeMath", "Height Scale Delta", "SUBTRACT")
    height_delta.inputs[1].default_value = 1.0
    height_offset = _node(nodes, "ShaderNodeMath", "Height Offset", "MULTIPLY")
    height_weighted = _node(nodes, "ShaderNodeMath", "Blend Height Into Arms", "MULTIPLY")
    combine_height = _node(nodes, "ShaderNodeCombineXYZ", "Height Offset Vector")

    thickness_delta = _node(nodes, "ShaderNodeMath", "Thickness Delta", "SUBTRACT")
    thickness_delta.inputs[1].default_value = BASE_THICKNESS
    thickness_offset = _node(nodes, "ShaderNodeVectorMath", "Inner Wall Offset", "SCALE")
    thickness_weighted = _node(nodes, "ShaderNodeVectorMath", "Inner Wall Selection", "SCALE")

    add_guard = _node(nodes, "ShaderNodeVectorMath", "Diameter Plus Height", "ADD")
    add_all = _node(nodes, "ShaderNodeVectorMath", "Final Offset", "ADD")
    set_position = _node(nodes, "GeometryNodeSetPosition", "Deform Imported Guard")

    links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
    links.new(set_position.outputs["Geometry"], group_output.inputs["Geometry"])
    links.new(position.outputs["Position"], radial.inputs[0])
    links.new(radial.outputs["Vector"], radial_xy.inputs[0])
    links.new(group_input.outputs["Guard Diameter (mm)"], diameter_ratio.inputs[0])
    links.new(diameter_ratio.outputs[0], diameter_delta.inputs[0])
    links.new(radial_xy.outputs["Vector"], diameter_offset.inputs[0])
    links.new(diameter_delta.outputs[0], diameter_offset.inputs[3])
    links.new(diameter_offset.outputs["Vector"], diameter_weighted.inputs[0])
    links.new(guard.outputs["Attribute"], diameter_weighted.inputs[3])

    links.new(position.outputs["Position"], separate.inputs[0])
    links.new(separate.outputs["Z"], z_from_bottom.inputs[0])
    links.new(group_input.outputs["Guard Height (mm)"], height_ratio.inputs[0])
    links.new(height_ratio.outputs[0], height_delta.inputs[0])
    links.new(z_from_bottom.outputs[0], height_offset.inputs[0])
    links.new(height_delta.outputs[0], height_offset.inputs[1])
    links.new(height_offset.outputs[0], height_weighted.inputs[0])
    links.new(guard.outputs["Attribute"], height_weighted.inputs[1])
    links.new(height_weighted.outputs[0], combine_height.inputs["Z"])

    links.new(group_input.outputs["Wall Thickness (mm)"], thickness_delta.inputs[0])
    links.new(direction.outputs["Attribute"], thickness_offset.inputs[0])
    links.new(thickness_delta.outputs[0], thickness_offset.inputs[3])
    links.new(thickness_offset.outputs["Vector"], thickness_weighted.inputs[0])
    links.new(inner.outputs["Attribute"], thickness_weighted.inputs[3])

    links.new(diameter_weighted.outputs["Vector"], add_guard.inputs[0])
    links.new(combine_height.outputs["Vector"], add_guard.inputs[1])
    links.new(add_guard.outputs["Vector"], add_all.inputs[0])
    links.new(thickness_weighted.outputs["Vector"], add_all.inputs[1])
    links.new(add_all.outputs["Vector"], set_position.inputs["Offset"])
    return group


def install_modifier(obj):
    modifier = obj.modifiers.get(MODIFIER_NAME)
    if modifier:
        assert modifier.type == "NODES", f"Wrong modifier type: {MODIFIER_NAME}"
    else:
        modifier = obj.modifiers.new(MODIFIER_NAME, "NODES")
    modifier.node_group = build_node_group()
    return modifier


def _parameter_socket(modifier, name):
    return next(
        item
        for item in modifier.node_group.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == name
    )


def set_parameter(modifier, name, value):
    socket = _parameter_socket(modifier, name)
    getattr(modifier.properties.inputs, socket.identifier).value = value
    modifier.id_data.update_tag()


def evaluated_vertices(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return tuple(tuple(vertex.co) for vertex in mesh.vertices)
    finally:
        evaluated.to_mesh_clear()


def evaluated_mount_signature(obj, baseline):
    vertices = evaluated_vertices(obj)
    return tuple((index, vertices[index]) for index, _coordinate in baseline)


def _dimensions(vertices, indices=None):
    points = vertices if indices is None else (vertices[index] for index in indices)
    points = tuple(points)
    return tuple(max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(3))


def _component_count(mesh):
    neighbors = [set() for _vertex in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbors[a].add(b)
        neighbors[b].add(a)
    unseen = set(range(len(mesh.vertices)))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            for neighbor in neighbors[stack.pop()]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def _wall_geometry(mesh):
    center = Vector(
        (
            (min(v.co.x for v in mesh.vertices) + max(v.co.x for v in mesh.vertices)) / 2.0,
            (min(v.co.y for v in mesh.vertices) + max(v.co.y for v in mesh.vertices)) / 2.0,
        )
    )
    inner, outer = set(), set()
    for face in mesh.polygons:
        radial = Vector((face.center.x, face.center.y)) - center
        dot = face.normal.x * radial.x + face.normal.y * radial.y
        if radial.length > 20.0 and abs(face.normal.z) < 0.45:
            (inner if dot < 0.0 else outer).update(face.vertices)
    return inner, outer


def _wall_pairs(mesh, inner_indices, outer_indices, directions):
    pairs = []
    for inner_index in inner_indices:
        direction = Vector(directions[inner_index].vector)
        if not direction.length:
            continue
        outward = -Vector((direction.x, direction.y, 0.0))
        point = mesh.vertices[inner_index].co
        best = None
        for outer_index in outer_indices:
            candidate = mesh.vertices[outer_index].co
            if abs(candidate.z - point.z) > 0.06:
                continue
            delta = Vector((candidate.x - point.x, candidate.y - point.y, 0.0))
            distance = delta.dot(outward)
            if not 3.95 <= distance <= 4.05:
                continue
            perpendicular = (delta - outward * distance).length
            if perpendicular <= 0.1 and (best is None or perpendicular < best[0]):
                best = (perpendicular, outer_index)
        if best:
            pairs.append((inner_index, best[1], outward))
    return pairs


def install():
    obj = get_guard()
    before = mount_signature(obj)
    build_attributes(obj)
    modifier = install_modifier(obj)
    assert mount_signature(obj) == before, "Setup changed the imported mount mesh"
    return modifier


def self_check():
    obj = get_guard()
    for name in ("PG_FixedMount", "PG_GuardWeight", "PG_InnerWeight", "PG_ThicknessDirection"):
        attribute = obj.data.attributes.get(name)
        assert attribute and attribute.domain == "POINT", f"Missing point attribute: {name}"

    modifier = obj.modifiers.get(MODIFIER_NAME)
    assert modifier and modifier.type == "NODES", "Missing parametric guard modifier"
    group = modifier.node_group
    assert group and group.name == GROUP_NAME, "Wrong node group"
    floats = {
        item.name: item
        for item in group.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.socket_type == "NodeSocketFloat"
    }
    assert set(floats) == set(PARAMETERS), tuple(floats)
    for name, (minimum, maximum, default) in PARAMETERS.items():
        socket = floats[name]
        assert all(
            math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)
            for actual, expected in zip(
                (socket.min_value, socket.max_value, socket.default_value),
                (minimum, maximum, default),
            )
        )

    baseline_mount = mount_signature(obj)
    baseline_vertices = tuple(tuple(vertex.co) for vertex in obj.data.vertices)
    guard_weights = obj.data.attributes["PG_GuardWeight"].data
    inner_weights = obj.data.attributes["PG_InnerWeight"].data
    directions = obj.data.attributes["PG_ThicknessDirection"].data
    guard_indices = tuple(v.index for v in obj.data.vertices if guard_weights[v.index].value >= 0.999)
    inner_indices = tuple(v.index for v in obj.data.vertices if inner_weights[v.index].value > 0.5)
    _inner_wall, outer_indices = _wall_geometry(obj.data)
    wall_pairs = _wall_pairs(obj.data, inner_indices, outer_indices, directions)
    assert guard_indices and inner_indices
    assert wall_pairs, "No 4 mm inner/outer wall samples found"
    assert _component_count(obj.data) == 1, "Imported mesh is not one connected component"

    cases = (
        (50.8, BASE_HEIGHT, BASE_THICKNESS),
        (BASE_DIAMETER, BASE_HEIGHT, BASE_THICKNESS),
        (120.0, BASE_HEIGHT, BASE_THICKNESS),
        (BASE_DIAMETER, 3.0, BASE_THICKNESS),
        (BASE_DIAMETER, 101.6, BASE_THICKNESS),
        (BASE_DIAMETER, BASE_HEIGHT, 2.0),
        (BASE_DIAMETER, BASE_HEIGHT, 8.0),
        (50.8, 3.0, 2.0),
        (120.0, 101.6, 8.0),
    )
    results = []
    try:
        for diameter, height, thickness in cases:
            set_parameter(modifier, "Guard Diameter (mm)", diameter)
            set_parameter(modifier, "Guard Height (mm)", height)
            set_parameter(modifier, "Wall Thickness (mm)", thickness)
            bpy.context.view_layer.update()
            vertices = evaluated_vertices(obj)
            assert tuple((index, vertices[index]) for index, _co in baseline_mount) == baseline_mount, (
                "Mount changed", diameter, height, thickness
            )
            dimensions = _dimensions(vertices)
            guard_height = _dimensions(vertices, guard_indices)[2]
            if (diameter, height, thickness) == (BASE_DIAMETER, BASE_HEIGHT, BASE_THICKNESS):
                expected = (86.892616, 86.906372, 26.400002)
                assert all(abs(actual - target) <= 0.01 for actual, target in zip(dimensions, expected)), dimensions
            else:
                assert abs(max(dimensions[:2]) - diameter) <= 0.05, (diameter, dimensions)
                assert abs(guard_height - height) <= 0.05, (height, guard_height)
            if diameter == BASE_DIAMETER and height == BASE_HEIGHT:
                delta = thickness - BASE_THICKNESS
                errors = []
                for index in inner_indices:
                    movement = Vector(vertices[index]) - Vector(baseline_vertices[index])
                    direction = Vector(directions[index].vector)
                    errors.append(abs(movement.dot(direction) - delta))
                assert max(errors) <= 0.05, (thickness, max(errors))
                assert all(vertices[index] == baseline_vertices[index] for index in outer_indices), (
                    "Outer contour changed", thickness
                )
                measured = [
                    (Vector(vertices[outer]) - Vector(vertices[inner])).dot(outward)
                    for inner, outer, outward in wall_pairs
                ]
                assert all(abs(value - thickness) <= 0.05 for value in measured), (
                    thickness, min(measured), max(measured)
                )
                for edge in obj.data.edges:
                    a, b = edge.vertices
                    base_edge = (obj.data.vertices[a].co - obj.data.vertices[b].co).length
                    if base_edge < 0.1:
                        movement_a = Vector(vertices[a]) - Vector(baseline_vertices[a])
                        movement_b = Vector(vertices[b]) - Vector(baseline_vertices[b])
                        assert (movement_a - movement_b).length <= 0.05, (
                            "Thickness split near-duplicate vertices", a, b
                        )
            results.append((diameter, height, thickness, dimensions, guard_height))
    finally:
        for name, value in (
            ("Guard Diameter (mm)", BASE_DIAMETER),
            ("Guard Height (mm)", BASE_HEIGHT),
            ("Wall Thickness (mm)", BASE_THICKNESS),
        ):
            set_parameter(modifier, name, value)
        bpy.context.view_layer.update()
    print("PG_SELF_CHECK_OK", results)


if __name__ == "__main__":
    install()
    if "--self-check" in sys.argv:
        self_check()
