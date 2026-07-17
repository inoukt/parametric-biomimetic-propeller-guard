import bpy
import bmesh
import math
import sys

OBJECT_NAME = "halfApexPropGuardModify.001"
CENTER = (2.204754, -2.317232)
FIXED_RADIUS = 10.0
MOUNT_KEEP_RADIUS = 14.0
MOUNT_Z_MIN = -3.0034074783325195
MOUNT_Z_MAX = 0.2965925931930542
PROP_PRESETS = (2.0, 2.5, 3.0, 3.5, 4.0, 5.0)
GROUP_NAME = "PG_BiomimeticGuardV2"
MODIFIER_NAME = "PG Biomimetic Guard V2"
PARAMETERS = {
    "Propeller Diameter (in)": (2.0, 5.0, 2.0),
    "Guard Height (mm)": (3.3, 101.6, 12.0),
    "Bumper Thickness (mm)": (1.2, 8.0, 2.2),
    "Strength / Weight": (0.0, 1.0, 0.5),
    "Nozzle Diameter (mm)": (0.4, 0.8, 0.4),
    "Safety Clearance Override (mm)": (0.0, 1_000_000.0, 0.0),
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


def sizing(prop_inches, height, bumper, strength, nozzle, clearance_override=0.0):
    assert 2.0 <= prop_inches <= 5.0
    assert 3.3 <= height <= 101.6
    assert 0.0 <= strength <= 1.0
    assert 0.4 <= nozzle <= 0.8
    assert clearance_override >= 0.0
    prop_mm = prop_inches * 25.4
    min_feature = 3.0 * nozzle
    assert 1.2 <= bumper <= 8.0
    bumper = max(bumper, min_feature)
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
    assert obj.mode == "OBJECT", "Switch the guard to Object Mode"
    assert tuple(obj.scale) == (1.0, 1.0, 1.0), "Apply object scale before V2 setup"
    mesh = obj.data
    cx, cy = CENTER
    fixed = replace_attribute(mesh, "PG_FixedMount", "FLOAT", "POINT")
    keep = replace_attribute(mesh, "PG_V2_MountKeep", "BOOLEAN", "FACE")
    for vertex in mesh.vertices:
        fixed.data[vertex.index].value = float(
            math.hypot(vertex.co.x - cx, vertex.co.y - cy) <= FIXED_RADIUS
        )
    for face in mesh.polygons:
        radii = tuple(
            math.hypot(mesh.vertices[index].co.x - cx, mesh.vertices[index].co.y - cy)
            for index in face.vertices
        )
        keep.data[face.index].value = any(radius <= FIXED_RADIUS for radius in radii) or all(
            radius <= MOUNT_KEEP_RADIUS for radius in radii
        )


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


def _set_or_link(links, socket, value):
    if hasattr(value, "is_output"):
        links.new(value, socket)
    else:
        socket.default_value = value


def math_node(group, name, operation, left, right):
    result = node(group.nodes, "ShaderNodeMath", name, operation)
    _set_or_link(group.links, result.inputs[0], left)
    _set_or_link(group.links, result.inputs[1], right)
    return result.outputs[0]


def parameter_nodes(group, group_in):
    prop_mm = math_node(
        group, "Propeller Millimetres", "MULTIPLY", group_in.outputs["Propeller Diameter (in)"], 25.4
    )
    auto_clearance = math_node(
        group, "Scaled Clearance", "MULTIPLY", prop_mm, 0.04
    )
    auto_clearance = math_node(group, "Minimum Clearance", "MAXIMUM", auto_clearance, 2.0)
    use_override = math_node(
        group,
        "Use Clearance Override",
        "GREATER_THAN",
        group_in.outputs["Safety Clearance Override (mm)"],
        0.0,
    )
    clearance = node(group.nodes, "GeometryNodeSwitch", "Clearance")
    clearance.input_type = "FLOAT"
    group.links.new(use_override, clearance.inputs["Switch"])
    group.links.new(auto_clearance, clearance.inputs["False"])
    group.links.new(
        group_in.outputs["Safety Clearance Override (mm)"], clearance.inputs["True"]
    )
    minimum_feature = math_node(
        group,
        "Minimum Printable Feature",
        "MULTIPLY",
        group_in.outputs["Nozzle Diameter (mm)"],
        3.0,
    )
    bumper = math_node(
        group,
        "Validated Bumper Thickness",
        "MAXIMUM",
        group_in.outputs["Bumper Thickness (mm)"],
        minimum_feature,
    )
    prop_radius = math_node(group, "Propeller Radius", "DIVIDE", prop_mm, 2.0)
    inner_radius = math_node(
        group, "Inner Opening Radius", "ADD", prop_radius, clearance.outputs["Output"]
    )
    half_bumper = math_node(group, "Half Bumper", "DIVIDE", bumper, 2.0)
    bumper_center_radius = math_node(
        group, "Bumper Center Radius", "ADD", inner_radius, half_bumper
    )
    return {
        "prop_mm": prop_mm,
        "clearance": clearance.outputs["Output"],
        "minimum_feature": minimum_feature,
        "bumper": bumper,
        "inner_radius": inner_radius,
        "bumper_center_radius": bumper_center_radius,
        "height": group_in.outputs["Guard Height (mm)"],
        "strength": group_in.outputs["Strength / Weight"],
    }


def flat_bottom_profile(group, name, width_socket, height_socket, resolution):
    nodes, links = group.nodes, group.links
    circle = node(nodes, "GeometryNodeCurvePrimitiveCircle", f"{name} Circle")
    circle.mode = "RADIUS"
    circle.inputs["Resolution"].default_value = resolution
    circle.inputs["Radius"].default_value = 1.0
    position = node(nodes, "GeometryNodeInputPosition", f"{name} Position")
    separate = node(nodes, "ShaderNodeSeparateXYZ", f"{name} Separate Position")
    links.new(position.outputs["Position"], separate.inputs["Vector"])
    clamped_y = math_node(group, f"{name} Flat Bottom", "MAXIMUM", separate.outputs["Y"], -0.7)
    remapped_y = math_node(group, f"{name} Shift Bottom", "ADD", clamped_y, 0.7)
    remapped_y = math_node(group, f"{name} Normalize Height", "DIVIDE", remapped_y, 1.7)
    remapped_y = math_node(group, f"{name} Scale Height", "MULTIPLY", remapped_y, 2.0)
    remapped_y = math_node(group, f"{name} Center Height", "SUBTRACT", remapped_y, 1.0)
    offset_y = math_node(group, f"{name} Bottom Offset", "SUBTRACT", remapped_y, separate.outputs["Y"])
    set_position = node(nodes, "GeometryNodeSetPosition", f"{name} D Profile")
    links.new(circle.outputs["Curve"], set_position.inputs["Geometry"])
    links.new(combine_xyz(group, f"{name} Offset", 0.0, offset_y, 0.0), set_position.inputs["Offset"])
    shape = node(nodes, "GeometryNodeTransform", f"{name} Shape")
    half_width = math_node(group, f"{name} Half Width", "DIVIDE", width_socket, 2.0)
    half_height = math_node(group, f"{name} Half Height", "DIVIDE", height_socket, 2.0)
    links.new(set_position.outputs["Geometry"], shape.inputs["Geometry"])
    links.new(combine_xyz(group, f"{name} Scale", half_width, half_height, 1.0), shape.inputs["Scale"])
    return shape.outputs["Geometry"]


def bumper_nodes(group, values):
    nodes, links = group.nodes, group.links
    circle = node(nodes, "GeometryNodeCurvePrimitiveCircle", "Bumper Centerline")
    circle.mode = "RADIUS"
    circle.inputs["Resolution"].default_value = 128
    profile = flat_bottom_profile(
        group, "Rounded Bumper Profile", values["bumper"], values["height"], 24
    )
    curve_to_mesh = node(nodes, "GeometryNodeCurveToMesh", "Solid Bumper")
    transform = node(nodes, "GeometryNodeTransform", "Place Bumper")
    links.new(values["bumper_center_radius"], circle.inputs["Radius"])
    links.new(circle.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    links.new(profile, curve_to_mesh.inputs["Profile Curve"])
    links.new(curve_to_mesh.outputs["Mesh"], transform.inputs["Geometry"])
    z_center = math_node(group, "Bumper Half Height", "DIVIDE", values["height"], 2.0)
    z_center = math_node(group, "Bumper Print Bed Alignment", "ADD", z_center, MOUNT_Z_MIN)
    links.new(
        combine_xyz(group, "Bumper Position", CENTER[0], CENTER[1], z_center),
        transform.inputs["Translation"],
    )
    return transform.outputs["Geometry"]


def combine_xyz(group, name, x=0.0, y=0.0, z=0.0):
    result = node(group.nodes, "ShaderNodeCombineXYZ", name)
    _set_or_link(group.links, result.inputs["X"], x)
    _set_or_link(group.links, result.inputs["Y"], y)
    _set_or_link(group.links, result.inputs["Z"], z)
    return result.outputs["Vector"]


def bezier_segment(group, name, start, start_handle, end_handle, end):
    result = node(group.nodes, "GeometryNodeCurvePrimitiveBezierSegment", name)
    result.mode = "POSITION"
    result.inputs["Resolution"].default_value = 12
    for socket, value in (
        ("Start", start),
        ("Start Handle", start_handle),
        ("End Handle", end_handle),
        ("End", end),
    ):
        _set_or_link(group.links, result.inputs[socket], value)
    return result.outputs["Curve"]


def continuous_branch(group, name, curve_socket, width_socket, height_socket):
    nodes, links = group.nodes, group.links
    profile = flat_bottom_profile(group, f"{name} Rounded Profile", width_socket, height_socket, 16)
    mesh = node(nodes, "GeometryNodeCurveToMesh", name)
    mesh.inputs["Fill Caps"].default_value = True
    links.new(curve_socket, mesh.inputs["Curve"])
    links.new(profile, mesh.inputs["Profile Curve"])
    return mesh.outputs["Mesh"]


def junction_pad(
    group, name, x, y, width_socket, height_socket, radius_factor=1.2, radius_socket=None
):
    nodes, links = group.nodes, group.links
    pad = node(nodes, "GeometryNodeMeshCylinder", name)
    pad.inputs["Vertices"].default_value = 32
    pad.inputs["Side Segments"].default_value = 1
    pad.inputs["Fill Segments"].default_value = 1
    if radius_socket is None:
        radius_socket = math_node(
            group, f"{name} Radius", "MULTIPLY", width_socket, radius_factor
        )
    links.new(radius_socket, pad.inputs["Radius"])
    links.new(height_socket, pad.inputs["Depth"])
    place = node(nodes, "GeometryNodeTransform", f"Place {name}")
    links.new(pad.outputs["Mesh"], place.inputs["Geometry"])
    links.new(combine_xyz(group, f"{name} Position", x, y, 0.0), place.inputs["Translation"])
    return place.outputs["Geometry"]


def arm_nodes(group, values):
    nodes, links = group.nodes, group.links
    strength_factor = math_node(group, "Primary Strength Factor", "MULTIPLY", values["strength"], 0.25)
    strength_factor = math_node(group, "Primary Width Factor", "ADD", strength_factor, 0.55)
    primary_width = math_node(
        group,
        "Primary Width",
        "MAXIMUM",
        values["minimum_feature"],
        math_node(group, "Scaled Primary Width", "MULTIPLY", values["bumper"], strength_factor),
    )
    fork_factor = math_node(group, "Fork Strength Factor", "MULTIPLY", values["strength"], 0.15)
    fork_factor = math_node(group, "Fork Width Factor", "ADD", fork_factor, 0.65)
    fork_width = math_node(
        group,
        "Fork Width",
        "MAXIMUM",
        values["minimum_feature"],
        math_node(group, "Scaled Fork Width", "MULTIPLY", primary_width, fork_factor),
    )
    fork_radius = math_node(
        group,
        "Fork Radius",
        "MAXIMUM",
        math_node(group, "Scaled Fork Radius", "MULTIPLY", values["inner_radius"], 0.68),
        16.0,
    )
    primary_end_handle_x = math_node(
        group, "Primary End Handle X", "MULTIPLY", fork_radius, 0.80
    )
    primary_curve = bezier_segment(
        group,
        "Primary Arm Curve",
        (12.0, 0.0, 0.0),
        (13.0, 0.0, 0.0),
        combine_xyz(group, "Primary End Handle", primary_end_handle_x, 0.0, 0.0),
        combine_xyz(group, "Primary Fork Point", fork_radius, 0.0, 0.0),
    )
    primary = continuous_branch(group, "Primary Arm", primary_curve, primary_width, values["height"])

    cos_angle = math.cos(math.radians(18.0))
    sin_angle = math.sin(math.radians(18.0))
    end_x = math_node(group, "Fork End X", "MULTIPLY", values["inner_radius"], cos_angle)
    end_y = math_node(group, "Fork End Y", "MULTIPLY", values["inner_radius"], sin_angle)
    delta_x = math_node(group, "Fork Delta X", "SUBTRACT", end_x, fork_radius)
    handle1_x = math_node(
        group,
        "Fork Start Handle X",
        "ADD",
        fork_radius,
        math_node(group, "Quarter Fork X", "MULTIPLY", delta_x, 0.25),
    )
    handle2_x = math_node(
        group,
        "Fork End Handle X",
        "ADD",
        fork_radius,
        math_node(group, "Three Quarter Fork X", "MULTIPLY", delta_x, 0.75),
    )
    handle1_y = math_node(group, "Quarter Fork Y", "MULTIPLY", end_y, 0.25)
    handle2_y = math_node(group, "Three Quarter Fork Y", "MULTIPLY", end_y, 0.85)
    negative_end_y = math_node(group, "Negative Fork End Y", "MULTIPLY", end_y, -1.0)
    negative_handle1_y = math_node(group, "Negative Quarter Fork Y", "MULTIPLY", handle1_y, -1.0)
    negative_handle2_y = math_node(group, "Negative Three Quarter Fork Y", "MULTIPLY", handle2_y, -1.0)
    start = combine_xyz(group, "Fork Start", fork_radius, 0.0, 0.0)
    upper_curve = bezier_segment(
        group,
        "Upper Fork Curve",
        start,
        combine_xyz(group, "Upper Fork Start Handle", handle1_x, handle1_y, 0.0),
        combine_xyz(group, "Upper Fork End Handle", handle2_x, handle2_y, 0.0),
        combine_xyz(group, "Upper Fork End", end_x, end_y, 0.0),
    )
    lower_curve = bezier_segment(
        group,
        "Lower Fork Curve",
        start,
        combine_xyz(group, "Lower Fork Start Handle", handle1_x, negative_handle1_y, 0.0),
        combine_xyz(group, "Lower Fork End Handle", handle2_x, negative_handle2_y, 0.0),
        combine_xyz(group, "Lower Fork End", end_x, negative_end_y, 0.0),
    )
    upper = continuous_branch(group, "Upper Fork", upper_curve, fork_width, values["height"])
    lower = continuous_branch(group, "Lower Fork", lower_curve, fork_width, values["height"])
    local = node(nodes, "GeometryNodeJoinGeometry", "Local Y Arm")
    root_pad_radius = math_node(group, "Scaled Root Bridge Radius", "MULTIPLY", primary_width, 0.65)
    root_pad_radius = math_node(group, "Maximum Root Bridge Radius", "MINIMUM", root_pad_radius, 2.0)
    root_pad_radius = math_node(group, "Minimum Root Bridge Radius", "MAXIMUM", root_pad_radius, 0.95)
    root_pad_x = math_node(group, "Root Bridge Center", "ADD", root_pad_radius, 10.2)
    root_pad = junction_pad(
        group,
        "Root Junction Pad",
        root_pad_x,
        0.0,
        primary_width,
        values["height"],
        radius_socket=root_pad_radius,
    )
    fork_pad = junction_pad(group, "Fork Junction Pad", fork_radius, 0.0, fork_width, values["height"])
    upper_pad = junction_pad(group, "Upper Bumper Pad", end_x, end_y, fork_width, values["height"])
    lower_pad = junction_pad(group, "Lower Bumper Pad", end_x, negative_end_y, fork_width, values["height"])
    for geometry in (primary, upper, lower, root_pad, fork_pad, upper_pad, lower_pad):
        links.new(geometry, local.inputs["Geometry"])

    points = node(nodes, "GeometryNodeMeshLine", "Three Arm Points")
    points.mode = "OFFSET"
    points.inputs["Count"].default_value = 3
    points.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    points.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    index = node(nodes, "GeometryNodeInputIndex", "Arm Index")
    rotation_z = math_node(group, "Arm Rotation", "MULTIPLY", index.outputs["Index"], 2.0 * math.pi / 3.0)
    rotation = combine_xyz(group, "Arm Rotation Vector", 0.0, 0.0, rotation_z)
    instances = node(nodes, "GeometryNodeInstanceOnPoints", "Threefold Arm Instances")
    realize = node(nodes, "GeometryNodeRealizeInstances", "Realize Arm Network")
    place = node(nodes, "GeometryNodeTransform", "Place Arm Network")
    links.new(points.outputs["Mesh"], instances.inputs["Points"])
    links.new(local.outputs["Geometry"], instances.inputs["Instance"])
    links.new(rotation, instances.inputs["Rotation"])
    links.new(instances.outputs["Instances"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], place.inputs["Geometry"])
    z_center = math_node(group, "Arm Half Height", "DIVIDE", values["height"], 2.0)
    z_center = math_node(group, "Arm Print Bed Alignment", "ADD", z_center, MOUNT_Z_MIN)
    links.new(
        combine_xyz(group, "Arm Network Position", CENTER[0], CENTER[1], z_center),
        place.inputs["Translation"],
    )
    return place.outputs["Geometry"]


def union_node(group, name, first, second):
    result = node(group.nodes, "GeometryNodeMeshBoolean", name)
    result.operation = "UNION"
    result.solver = "EXACT"
    result.inputs["Self Intersection"].default_value = True
    result.inputs["Hole Tolerant"].default_value = True
    group.links.new(first, result.inputs[1])
    group.links.new(second, result.inputs[1])
    return result.outputs["Mesh"]


def closed_mount_nodes(group, source_geometry):
    nodes, links = group.nodes, group.links
    cutter = node(nodes, "GeometryNodeMeshCylinder", "Mount Interface Cutter")
    cutter.inputs["Vertices"].default_value = 128
    cutter.inputs["Side Segments"].default_value = 1
    cutter.inputs["Fill Segments"].default_value = 1
    cutter.inputs["Radius"].default_value = MOUNT_KEEP_RADIUS
    cutter.inputs["Depth"].default_value = 200.0
    place = node(nodes, "GeometryNodeTransform", "Place Mount Cutter")
    place.inputs["Translation"].default_value = (*CENTER, 0.0)
    links.new(cutter.outputs["Mesh"], place.inputs["Geometry"])
    clipped = node(nodes, "GeometryNodeMeshBoolean", "Clip Closed Mount")
    clipped.operation = "INTERSECT"
    clipped.solver = "EXACT"
    clipped.inputs["Self Intersection"].default_value = True
    clipped.inputs["Hole Tolerant"].default_value = True
    links.new(source_geometry, clipped.inputs[1])
    links.new(place.outputs["Geometry"], clipped.inputs[1])
    return clipped.outputs["Mesh"]


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
        socket.min_value = minimum
        socket.max_value = maximum
        socket.default_value = default

    nodes, links = group.nodes, group.links
    group_in = node(nodes, "NodeGroupInput", "Inputs")
    group_out = node(nodes, "NodeGroupOutput", "Output")
    keep = named_attribute(nodes, "PG_V2_MountKeep", "BOOLEAN")
    separate = node(nodes, "GeometryNodeSeparateGeometry", "Keep Fixed Mount")
    separate.domain = "FACE"
    links.new(group_in.outputs["Geometry"], separate.inputs["Geometry"])
    links.new(keep.outputs["Attribute"], separate.inputs["Selection"])
    values = parameter_nodes(group, group_in)
    bumper = bumper_nodes(group, values)
    arms = arm_nodes(group, values)
    body = union_node(group, "Union Bumper and Arms", bumper, arms)
    # The face selection is an inspectable audit mask. Feeding its open boundary
    # to a boolean would destroy manifoldness, so the closed mount is clipped
    # directly from the unchanged source mesh using the same 14 mm boundary.
    closed_mount = closed_mount_nodes(group, group_in.outputs["Geometry"])
    final = union_node(group, "Union V2 Body", body, closed_mount)
    links.new(final, group_out.inputs["Geometry"])
    return group


def install_modifier(obj):
    modifier = obj.modifiers.get(MODIFIER_NAME)
    if modifier:
        assert modifier.type == "NODES"
    else:
        modifier = obj.modifiers.new(MODIFIER_NAME, "NODES")
    modifier.node_group = build_node_group()
    for name, (_minimum, _maximum, default) in PARAMETERS.items():
        socket = next(
            item
            for item in modifier.node_group.interface.items_tree
            if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == name
        )
        getattr(modifier.properties.inputs, socket.identifier).value = default
    v1 = obj.modifiers.get("PG Parametric Guard")
    if v1:
        v1.show_viewport = False
        v1.show_render = False
    return modifier


def install():
    obj = get_guard()
    build_source_attributes(obj)
    return install_modifier(obj)


def parameter_socket(modifier, name):
    return next(
        item
        for item in modifier.node_group.interface.items_tree
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


def mesh_report(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        seen = set()
        components = 0
        for vertex in bm.verts:
            if vertex.index in seen:
                continue
            components += 1
            seen.add(vertex.index)
            stack = [vertex]
            while stack:
                current = stack.pop()
                for edge in current.link_edges:
                    neighbour = edge.other_vert(current)
                    if neighbour.index not in seen:
                        seen.add(neighbour.index)
                        stack.append(neighbour)
        volume = bm.calc_volume(signed=False)
        return {
            "vertices": len(bm.verts),
            "faces": len(bm.faces),
            "components": components,
            "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "volume_mm3": volume,
            "dimensions": dimensions(tuple(tuple(vertex.co) for vertex in mesh.vertices)),
        }
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def self_check():
    obj = get_guard()
    assert tuple(obj.scale) == (1.0, 1.0, 1.0)
    fixed = obj.data.attributes.get("PG_FixedMount")
    keep = obj.data.attributes.get("PG_V2_MountKeep")
    assert fixed and fixed.data_type == "FLOAT" and fixed.domain == "POINT"
    assert keep and keep.data_type == "BOOLEAN" and keep.domain == "FACE"
    cx, cy = CENTER
    fixed_indices = {
        vertex.index
        for vertex in obj.data.vertices
        if math.hypot(vertex.co.x - cx, vertex.co.y - cy) <= FIXED_RADIUS
    }
    retained_indices = {
        index
        for face in obj.data.polygons
        if keep.data[face.index].value
        for index in face.vertices
    }
    assert fixed_indices <= retained_indices, "MountKeep drops fixed vertices"
    assert all(
        fixed.data[index].value == float(index in fixed_indices)
        for index in range(len(obj.data.vertices))
    )
    values = sizing(2.0, 12.0, 2.2, 0.5, 0.4)
    assert math.isclose(values["prop_mm"], 50.8)
    assert math.isclose(values["clearance"], 2.032)
    assert math.isclose(values["outer_diameter"], 59.264)
    assert math.isclose(values["min_feature"], 1.2)
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
    assert set(inputs) == set(PARAMETERS)
    for name, (minimum, maximum, default) in PARAMETERS.items():
        socket = inputs[name]
        assert all(
            math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)
            for actual, expected in zip(
                (socket.min_value, socket.max_value, socket.default_value),
                (minimum, maximum, default),
            )
        ), name
    assert {"PG_V2_MountKeep", "Keep Fixed Mount", "Union V2 Body"} <= {
        item.name for item in group.nodes
    }
    assert {
        "Primary Arm",
        "Upper Fork",
        "Lower Fork",
        "Threefold Arm Instances",
        "Union V2 Body",
    } <= {item.name for item in group.nodes}, "Missing biomimetic arm network"
    for name, value in (
        ("Propeller Diameter (in)", 2.0),
        ("Guard Height (mm)", 12.0),
        ("Bumper Thickness (mm)", 2.2),
        ("Strength / Weight", 0.5),
        ("Nozzle Diameter (mm)", 0.4),
        ("Safety Clearance Override (mm)", 0.0),
    ):
        set_parameter(modifier, name, value)
    bpy.context.view_layer.update()
    evaluated = evaluated_vertices(obj)
    measured = dimensions(evaluated)
    assert abs(max(measured[:2]) - 59.264) <= 0.05, measured
    assert abs(measured[2] - 12.0) <= 0.05, measured
    evaluated_coordinates = set(evaluated)
    assert {coordinate for _index, coordinate in mount_signature(obj)} <= evaluated_coordinates
    report = mesh_report(obj)
    assert report["components"] == 1, report
    assert report["nonmanifold_edges"] == 0, report
    mass_low = report["volume_mm3"] * 0.00120
    mass_high = report["volume_mm3"] * 0.00125
    assert 7.0 <= mass_low and mass_high <= 8.0, (mass_low, mass_high)
    obj["PG_V2_Estimated_Mass_g_1.20"] = mass_low
    obj["PG_V2_Estimated_Mass_g_1.25"] = mass_high
    obj["PG_V2_Defaults"] = "2 in, 12 mm height, 2.2 mm bumper, balanced, 0.4 mm nozzle"


if __name__ == "__main__":
    if "--verify-only" not in sys.argv:
        install()
    if "--self-check" in sys.argv:
        self_check()
