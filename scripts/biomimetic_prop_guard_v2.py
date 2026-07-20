import bpy
import bmesh
import math
import sys

OBJECT_NAME = "halfApexPropGuardModify.001"
MOTOR_CENTER = (0.0, 0.0)
PLATE_RADIUS = 10.0
HOLE_CIRCLE_DIAMETER = 12.0
THROUGH_RADIUS = 1.5
RECESS_RADIUS = 2.25
MOUNT_Z_MIN = -3.0034074783325195
RECESS_TOP_Z = -1.6034074783325195
MOUNT_Z_MAX = 0.2965925931930542
ARC_START = 30.0
ARC_END = 240.0
PROP_PRESETS = (2.0, 2.5, 3.0, 3.5, 4.0, 5.0)
GROUP_NAME = "PG_BiomimeticGuardV2"
MODIFIER_NAME = "PG Biomimetic Guard V2"
NORMAL_MODIFIER_NAME = "PG Weighted Normals"
PARAMETERS = {
    "Propeller Diameter (in)": (2.0, 5.0, 2.0),
    "Guard Height (mm)": (3.3, 101.6, 12.0),
    "Bumper Thickness (mm)": (1.2, 8.0, 2.2),
    "Strength / Weight": (0.0, 1.0, 0.5),
    "Nozzle Diameter (mm)": (0.4, 0.8, 0.4),
    "Safety Clearance Override (mm)": (0.0, 1_000_000.0, 0.0),
    "Under-Prop Rib Height (mm)": (1.2, 12.0, 3.3),
    "Bio Reinforcement": (0.0, 1.0, 0.5),
    "Edge Smoothness": (0.0, 1.0, 0.65),
}
VALIDATION_CASES = (
    (2.0, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (2.5, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (3.0, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (3.5, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (4.0, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (5.0, 12.0, 2.2, 0.5, 0.4, 0.0, 3.3, 0.5, 0.65),
    (2.0, 3.3, 1.2, 0.0, 0.4, 0.0, 3.3, 0.0, 0.0),
    (2.0, 101.6, 8.0, 1.0, 0.8, 0.0, 3.3, 1.0, 1.0),
    (5.0, 3.3, 1.2, 0.0, 0.4, 0.0, 3.3, 0.0, 0.0),
    (5.0, 101.6, 8.0, 1.0, 0.8, 0.0, 3.3, 1.0, 1.0),
    (2.5, 3.3, 1.2, 0.0, 0.8, 0.0, 3.3, 0.0, 1.0),
    (3.5, 12.0, 2.2, 0.5, 0.4, 3.0, 3.3, 0.5, 0.65),
    (4.3, 24.0, 2.0, 0.25, 0.6, 0.0, 3.3, 0.25, 0.75),
)


def get_guard():
    obj = bpy.data.objects.get(OBJECT_NAME)
    assert obj and obj.type == "MESH", f"Missing mesh: {OBJECT_NAME}"
    return obj


def hole_centers():
    radius = HOLE_CIRCLE_DIAMETER / 2.0
    return ((radius, 0.0), (0.0, radius), (-radius, 0.0), (0.0, -radius))


def sizing(
    prop_inches,
    height,
    bumper,
    strength,
    nozzle,
    clearance_override=0.0,
    rib_height=3.3,
    bio_reinforcement=0.5,
    edge_smoothness=0.65,
):
    assert 2.0 <= prop_inches <= 5.0
    assert 3.3 <= height <= 101.6
    assert 0.0 <= strength <= 1.0
    assert 0.4 <= nozzle <= 0.8
    assert clearance_override >= 0.0
    assert 1.2 <= rib_height <= 12.0
    assert 0.0 <= bio_reinforcement <= 1.0
    assert 0.0 <= edge_smoothness <= 1.0
    prop_mm = prop_inches * 25.4
    min_feature = 3.0 * nozzle
    assert 1.2 <= bumper <= 8.0
    bumper = max(bumper, min_feature)
    clearance = clearance_override or max(2.0, 0.04 * prop_mm)
    inner_radius = prop_mm / 2.0 + clearance
    prop_scale = (prop_inches - 2.0) / 3.0
    span_reinforcement = 1.0 + prop_scale * (0.35 + 0.20 * bio_reinforcement)
    primary_width = max(min_feature, bumper * (0.55 + 0.25 * strength) * span_reinforcement)
    fork_width = max(min_feature, primary_width * (0.65 + 0.15 * strength))
    rib_height = min(height, max(rib_height, min_feature))
    return {
        "prop_mm": prop_mm,
        "height": height,
        "bumper": bumper,
        "strength": strength,
        "nozzle": nozzle,
        "min_feature": min_feature,
        "clearance": clearance,
        "inner_radius": inner_radius,
        "bumper_center_radius": inner_radius + bumper / 2.0,
        "outer_diameter": 2.0 * (inner_radius + bumper),
        "primary_width": primary_width,
        "fork_width": fork_width,
        "root_radius": 12.0,
        "rib_height": rib_height,
        "fork_radius": max(16.0, inner_radius * 0.68),
        "fork_angle": math.radians(18.0),
        "bio_reinforcement": bio_reinforcement,
        "span_reinforcement": span_reinforcement,
        "edge_smoothness": edge_smoothness,
    }


def node(nodes, node_type, name, operation=None):
    result = nodes.new(node_type)
    result.name = result.label = name
    if operation:
        result.operation = operation
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
    rib_height = math_node(
        group,
        "Validated Under-Prop Rib Height",
        "MAXIMUM",
        group_in.outputs["Under-Prop Rib Height (mm)"],
        minimum_feature,
    )
    rib_height = math_node(
        group,
        "Clamped Under-Prop Rib Height",
        "MINIMUM",
        rib_height,
        group_in.outputs["Guard Height (mm)"],
    )
    smooth_steps = math_node(
        group,
        "Edge Smoothness Resolution",
        "ADD",
        12.0,
        math_node(
            group,
            "Scaled Edge Smoothness Resolution",
            "MULTIPLY",
            group_in.outputs["Edge Smoothness"],
            12.0,
        ),
    )
    prop_scale = math_node(
        group,
        "Large Prop Span Scale",
        "DIVIDE",
        math_node(group, "Prop Inches Above Minimum", "SUBTRACT", group_in.outputs["Propeller Diameter (in)"], 2.0),
        3.0,
    )
    span_reinforcement = math_node(
        group,
        "Large Prop Span Reinforcement",
        "ADD",
        1.0,
        math_node(
            group,
            "Scaled Large Prop Span Reinforcement",
            "MULTIPLY",
            prop_scale,
            math_node(
                group,
                "Bio Span Reinforcement Amount",
                "ADD",
                0.35,
                math_node(group, "Bio Span Reinforcement Blend", "MULTIPLY", group_in.outputs["Bio Reinforcement"], 0.20),
            ),
        ),
    )
    prop_radius = math_node(group, "Propeller Radius", "DIVIDE", prop_mm, 2.0)
    inner_radius = math_node(
        group, "Inner Opening Radius", "ADD", prop_radius, clearance.outputs["Output"]
    )
    half_bumper = math_node(group, "Half Bumper", "DIVIDE", bumper, 2.0)
    bumper_center_radius = math_node(
        group, "Bumper Center Radius", "ADD", inner_radius, half_bumper
    )
    low_height = math_node(
        group,
        "Low Height Boolean Stabilization",
        "LESS_THAN",
        group_in.outputs["Guard Height (mm)"],
        7.0,
    )
    return {
        "prop_mm": prop_mm,
        "clearance": clearance.outputs["Output"],
        "minimum_feature": minimum_feature,
        "bumper": bumper,
        "inner_radius": inner_radius,
        "bumper_center_radius": bumper_center_radius,
        "height": group_in.outputs["Guard Height (mm)"],
        "rib_height": rib_height,
        "bio_reinforcement": group_in.outputs["Bio Reinforcement"],
        "span_reinforcement": span_reinforcement,
        "smooth_steps": smooth_steps,
        "strength": group_in.outputs["Strength / Weight"],
        "low_height": low_height,
    }


def flat_bottom_profile(group, name, width_socket, height_socket, resolution):
    nodes, links = group.nodes, group.links
    circle = node(nodes, "GeometryNodeCurvePrimitiveCircle", f"{name} Circle")
    circle.mode = "RADIUS"
    _set_or_link(links, circle.inputs["Resolution"], resolution)
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
    trim = node(nodes, "GeometryNodeTrimCurve", "Open Bumper Arc")
    trim.mode = "FACTOR"
    trim.inputs["Start"].default_value = ARC_START / 360.0
    trim.inputs["End"].default_value = ARC_END / 360.0
    relief = math_node(
        group, "Low Height Bumper Relief", "MULTIPLY", values["low_height"], 0.02
    )
    bumper_height = math_node(
        group, "Boolean Relief Bumper Height", "SUBTRACT", values["height"], relief
    )
    profile = flat_bottom_profile(
        group, "Rounded Bumper Profile", values["bumper"], bumper_height, values["smooth_steps"]
    )
    curve_to_mesh = node(nodes, "GeometryNodeCurveToMesh", "Solid Bumper")
    curve_to_mesh.inputs["Fill Caps"].default_value = True
    transform = node(nodes, "GeometryNodeTransform", "Place Bumper")
    cap_radius = math_node(group, "Bumper End Cap Radius", "DIVIDE", values["bumper"], 2.0)
    start_x = math_node(
        group,
        "Bumper Start Cap X",
        "MULTIPLY",
        values["bumper_center_radius"],
        math.cos(math.radians(ARC_START)),
    )
    start_y = math_node(
        group,
        "Bumper Start Cap Y",
        "MULTIPLY",
        values["bumper_center_radius"],
        math.sin(math.radians(ARC_START)),
    )
    end_x = math_node(
        group,
        "Bumper End Cap X",
        "MULTIPLY",
        values["bumper_center_radius"],
        math.cos(math.radians(ARC_END)),
    )
    end_y = math_node(
        group,
        "Bumper End Cap Y",
        "MULTIPLY",
        values["bumper_center_radius"],
        math.sin(math.radians(ARC_END)),
    )
    start_cap = junction_pad(
        group,
        "Rounded Bumper Start Cap",
        start_x,
        start_y,
        values["bumper"],
        bumper_height,
        radius_socket=cap_radius,
    )
    end_cap = junction_pad(
        group,
        "Rounded Bumper End Cap",
        end_x,
        end_y,
        values["bumper"],
        bumper_height,
        radius_socket=cap_radius,
    )
    with_start_cap = union_node(
        group, "Bumper With Rounded Start Cap", curve_to_mesh.outputs["Mesh"], start_cap, solver="MANIFOLD"
    )
    rounded_bumper = union_node(
        group, "Bumper With Rounded End Caps", with_start_cap, end_cap, solver="MANIFOLD"
    )
    links.new(values["bumper_center_radius"], circle.inputs["Radius"])
    links.new(circle.outputs["Curve"], trim.inputs["Curve"])
    links.new(trim.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    links.new(profile, curve_to_mesh.inputs["Profile Curve"])
    links.new(rounded_bumper, transform.inputs["Geometry"])
    z_center = math_node(group, "Bumper Half Height", "DIVIDE", bumper_height, 2.0)
    z_center = math_node(group, "Bumper Print Bed Alignment", "ADD", z_center, MOUNT_Z_MIN)
    links.new(
        combine_xyz(group, "Bumper Position", MOTOR_CENTER[0], MOTOR_CENTER[1], z_center),
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


def continuous_branch(group, name, curve_socket, width_socket, height_socket, resolution):
    nodes, links = group.nodes, group.links
    profile = flat_bottom_profile(group, f"{name} Rounded Profile", width_socket, height_socket, resolution)
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
    pad.inputs["Vertices"].default_value = 48
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
        math_node(
            group,
            "Scaled Primary Width",
            "MULTIPLY",
            math_node(group, "Strength Primary Width", "MULTIPLY", values["bumper"], strength_factor),
            values["span_reinforcement"],
        ),
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
        (9.0, 0.0, 0.0),
        (12.0, 0.0, 0.0),
        combine_xyz(group, "Primary End Handle", primary_end_handle_x, 0.0, 0.0),
        combine_xyz(group, "Primary Fork Point", fork_radius, 0.0, 0.0),
    )
    primary = continuous_branch(
        group, "Primary Arm", primary_curve, primary_width, values["rib_height"], values["smooth_steps"]
    )

    cos_angle = math.cos(math.radians(18.0))
    sin_angle = math.sin(math.radians(18.0))
    end_x = math_node(group, "Fork End X", "MULTIPLY", values["bumper_center_radius"], cos_angle)
    end_y = math_node(group, "Fork End Y", "MULTIPLY", values["bumper_center_radius"], sin_angle)
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
    upper = continuous_branch(
        group, "Upper Fork", upper_curve, fork_width, values["rib_height"], values["smooth_steps"]
    )
    lower = continuous_branch(
        group, "Lower Fork", lower_curve, fork_width, values["rib_height"], values["smooth_steps"]
    )
    local = node(nodes, "GeometryNodeJoinGeometry", "Local Y Arm")
    bio_pad = math_node(
        group,
        "Bio Junction Reinforcement",
        "ADD",
        1.0,
        math_node(group, "Scaled Bio Junction Reinforcement", "MULTIPLY", values["bio_reinforcement"], 0.45),
    )
    root_pad_radius = math_node(group, "Scaled Root Bridge Radius", "MULTIPLY", primary_width, bio_pad)
    root_pad_radius = math_node(group, "Maximum Root Bridge Radius", "MINIMUM", root_pad_radius, 2.8)
    root_pad_radius = math_node(group, "Minimum Root Bridge Radius", "MAXIMUM", root_pad_radius, 0.95)
    root_pad = junction_pad(
        group,
        "Root Junction Pad",
        9.5,
        0.0,
        primary_width,
        values["rib_height"],
        radius_socket=root_pad_radius,
    )
    fork_pad_radius = math_node(group, "Bio Fork Pad Radius", "MULTIPLY", fork_width, bio_pad)
    fork_pad = junction_pad(
        group,
        "Fork Junction Pad",
        fork_radius,
        0.0,
        fork_width,
        values["rib_height"],
        radius_socket=fork_pad_radius,
    )
    bumper_pad_radius = math_node(
        group,
        "Printable Bumper Pad Radius",
        "MINIMUM",
        math_node(group, "Scaled Bumper Pad Radius", "MULTIPLY", fork_width, bio_pad),
        math_node(group, "Half Bumper Pad Limit", "MULTIPLY", values["bumper"], 0.5),
    )
    upper_pad = junction_pad(
        group,
        "Upper Bumper Pad",
        end_x,
        end_y,
        fork_width,
        values["rib_height"],
        radius_socket=bumper_pad_radius,
    )
    lower_pad = junction_pad(
        group,
        "Lower Bumper Pad",
        end_x,
        negative_end_y,
        fork_width,
        values["rib_height"],
        radius_socket=bumper_pad_radius,
    )
    for geometry in (primary, upper, lower, root_pad, fork_pad, upper_pad, lower_pad):
        links.new(geometry, local.inputs["Geometry"])

    points = node(nodes, "GeometryNodeMeshLine", "Three Arm Points")
    points.mode = "OFFSET"
    points.inputs["Count"].default_value = 3
    points.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    points.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    index = node(nodes, "GeometryNodeInputIndex", "Arm Index")
    rotation_z = math_node(
        group,
        "Arm Rotation Step",
        "MULTIPLY",
        index.outputs["Index"],
        math.radians(85.0),
    )
    rotation_z = math_node(
        group, "Arm Rotation", "ADD", rotation_z, math.radians(50.0)
    )
    rotation = combine_xyz(group, "Arm Rotation Vector", 0.0, 0.0, rotation_z)
    instances = node(nodes, "GeometryNodeInstanceOnPoints", "Threefold Arm Instances")
    realize = node(nodes, "GeometryNodeRealizeInstances", "Realize Arm Network")
    place = node(nodes, "GeometryNodeTransform", "Place Arm Network")
    links.new(points.outputs["Mesh"], instances.inputs["Points"])
    links.new(local.outputs["Geometry"], instances.inputs["Instance"])
    links.new(rotation, instances.inputs["Rotation"])
    links.new(instances.outputs["Instances"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], place.inputs["Geometry"])
    z_center = math_node(group, "Arm Half Height", "DIVIDE", values["rib_height"], 2.0)
    z_center = math_node(group, "Arm Top Anchored Below Motor", "SUBTRACT", MOUNT_Z_MAX, z_center)
    links.new(
        combine_xyz(group, "Arm Network Position", MOTOR_CENTER[0], MOTOR_CENTER[1], z_center),
        place.inputs["Translation"],
    )
    return place.outputs["Geometry"]


def union_node(group, name, first, second, solver="EXACT"):
    result = node(group.nodes, "GeometryNodeMeshBoolean", name)
    result.operation = "UNION"
    result.solver = solver
    if "Self Intersection" in result.inputs:
        result.inputs["Self Intersection"].default_value = True
    if "Hole Tolerant" in result.inputs:
        result.inputs["Hole Tolerant"].default_value = True
    group.links.new(first, result.inputs[1])
    group.links.new(second, result.inputs[1])
    return result.outputs["Mesh"]


def motor_plate_nodes(group):
    nodes, links = group.nodes, group.links
    plate = node(nodes, "GeometryNodeMeshCylinder", "V3 Motor Plate")
    plate.inputs["Vertices"].default_value = 128
    plate.inputs["Radius"].default_value = PLATE_RADIUS
    plate.inputs["Depth"].default_value = MOUNT_Z_MAX - MOUNT_Z_MIN
    place_plate = node(nodes, "GeometryNodeTransform", "Place V3 Motor Plate")
    place_plate.inputs["Translation"].default_value = (
        *MOTOR_CENTER,
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
    place_through.inputs["Translation"].default_value = (
        0.0,
        0.0,
        (MOUNT_Z_MIN + MOUNT_Z_MAX) / 2.0,
    )
    links.new(through.outputs["Mesh"], place_through.inputs["Geometry"])

    recess = node(nodes, "GeometryNodeMeshCylinder", "V3 Recess Cutter")
    recess.inputs["Vertices"].default_value = 48
    recess.inputs["Radius"].default_value = RECESS_RADIUS
    recess.inputs["Depth"].default_value = RECESS_TOP_Z - MOUNT_Z_MIN + 0.1
    place_recess = node(nodes, "GeometryNodeTransform", "Place V3 Recess Cutter")
    place_recess.inputs["Translation"].default_value = (
        0.0,
        0.0,
        (MOUNT_Z_MIN + RECESS_TOP_Z) / 2.0 - 0.05,
    )
    links.new(recess.outputs["Mesh"], place_recess.inputs["Geometry"])

    through_instances = node(
        nodes, "GeometryNodeInstanceOnPoints", "Instance V3 Through Cutters"
    )
    through_realized = node(nodes, "GeometryNodeRealizeInstances", "V3 Through Cutters")
    links.new(points.outputs["Points"], through_instances.inputs["Points"])
    links.new(place_through.outputs["Geometry"], through_instances.inputs["Instance"])
    links.new(through_instances.outputs["Instances"], through_realized.inputs["Geometry"])

    recess_instances = node(
        nodes, "GeometryNodeInstanceOnPoints", "Instance V3 Recess Cutters"
    )
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
    values = parameter_nodes(group, group_in)
    bumper = bumper_nodes(group, values)
    arms = arm_nodes(group, values)
    mount = motor_plate_nodes(group)
    body = union_node(group, "Union Mount and Arms", mount, arms)
    final = union_node(group, "Union V3 Body", body, bumper, solver="MANIFOLD")
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
    modifier = install_modifier(obj)
    normal = obj.modifiers.get(NORMAL_MODIFIER_NAME)
    if normal:
        assert normal.type == "WEIGHTED_NORMAL"
    else:
        normal = obj.modifiers.new(NORMAL_MODIFIER_NAME, "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    return modifier


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
        coordinates = tuple(tuple(vertex.co) for vertex in mesh.vertices)
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
            "dimensions": dimensions(coordinates),
            "coordinates": coordinates,
        }
    finally:
        bm.free()
        evaluated.to_mesh_clear()


def node_mesh_report(obj, node_name):
    group = obj.modifiers[MODIFIER_NAME].node_group
    output = group.nodes["Output"].inputs["Geometry"]
    original_socket = output.links[0].from_socket
    try:
        for link in tuple(output.links):
            group.links.remove(link)
        group.links.new(group.nodes[node_name].outputs[0], output)
        bpy.context.view_layer.update()
        return mesh_report(obj)
    finally:
        for link in tuple(output.links):
            group.links.remove(link)
        group.links.new(original_socket, output)
        bpy.context.view_layer.update()


def hole_report(obj):
    vertices = evaluated_vertices(obj)
    reports = []
    for expected_x, expected_y in hole_centers():
        top = [
            co
            for co in vertices
            if abs(co[2] - MOUNT_Z_MAX) < 1e-4
            and 1.2 < math.hypot(co[0] - expected_x, co[1] - expected_y) < 1.8
        ]
        bottom = [
            co
            for co in vertices
            if abs(co[2] - MOUNT_Z_MIN) < 1e-4
            and 2.0 < math.hypot(co[0] - expected_x, co[1] - expected_y) < 2.5
        ]
        shoulder = [
            co
            for co in vertices
            if MOUNT_Z_MIN + 0.2 < co[2] < MOUNT_Z_MAX - 0.2
            and 2.0
            < math.hypot(co[0] - expected_x, co[1] - expected_y)
            < 2.5
        ]
        assert top and bottom and shoulder
        center = (
            sum(co[0] for co in top) / len(top),
            sum(co[1] for co in top) / len(top),
        )
        reports.append(
            {
                "center": center,
                "through_radius": sum(
                    math.hypot(co[0] - center[0], co[1] - center[1]) for co in top
                )
                / len(top),
                "recess_radius": sum(
                    math.hypot(co[0] - expected_x, co[1] - expected_y)
                    for co in bottom
                )
                / len(bottom),
                "recess_top_z": sum(co[2] for co in shoulder) / len(shoulder),
            }
        )
    return tuple(reports)


def self_check():
    centers = hole_centers()
    assert centers == ((6.0, 0.0), (0.0, 6.0), (-6.0, 0.0), (0.0, -6.0))
    assert all(
        math.dist(centers[first], centers[second]) == HOLE_CIRCLE_DIAMETER
        for first, second in ((0, 2), (1, 3))
    )
    obj = get_guard()
    assert tuple(obj.scale) == (1.0, 1.0, 1.0)
    values = sizing(2.0, 12.0, 2.2, 0.5, 0.4)
    assert math.isclose(values["prop_mm"], 50.8)
    assert math.isclose(values["clearance"], 2.032)
    assert math.isclose(values["outer_diameter"], 59.264)
    assert math.isclose(values["min_feature"], 1.2)
    large_values = sizing(5.0, 12.0, 2.2, 0.5, 0.4)
    assert large_values["primary_width"] >= values["primary_width"] * 1.3
    assert large_values["fork_width"] >= values["fork_width"] * 1.25
    modifier = obj.modifiers.get(MODIFIER_NAME)
    assert modifier and modifier.type == "NODES", "Missing V2 modifier"
    normal = obj.modifiers.get(NORMAL_MODIFIER_NAME)
    assert normal and normal.type == "WEIGHTED_NORMAL"
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
    required = {
        "V3 Motor Plate",
        "V3 Through Cutters",
        "V3 Recess Cutters",
        "V3 Mount",
        "Open Bumper Arc",
        "Rounded Bumper Start Cap",
        "Rounded Bumper End Cap",
        "Primary Arm",
        "Upper Fork",
        "Lower Fork",
        "Threefold Arm Instances",
    }
    assert required <= {item.name for item in group.nodes}
    trim = group.nodes["Open Bumper Arc"]
    assert 0.0 < ARC_END - ARC_START <= 210.0
    assert math.isclose(
        trim.inputs["Start"].default_value, ARC_START / 360.0, abs_tol=1e-6
    )
    assert math.isclose(
        trim.inputs["End"].default_value, ARC_END / 360.0, abs_tol=1e-6
    )
    holes = hole_report(obj)
    assert len(holes) == 4
    for measured_hole, expected in zip(holes, hole_centers()):
        assert math.dist(measured_hole["center"], expected) <= 0.02
        assert abs(measured_hole["through_radius"] - THROUGH_RADIUS) <= 0.03
        assert abs(measured_hole["recess_radius"] - RECESS_RADIUS) <= 0.03
        assert abs(measured_hole["recess_top_z"] - RECESS_TOP_Z) <= 0.02
    mount_and_arms = node_mesh_report(obj, "Union Mount and Arms")
    assert mount_and_arms["components"] == 1, mount_and_arms
    assert mount_and_arms["nonmanifold_edges"] == 0, mount_and_arms
    for arm_name in ("Primary Arm", "Upper Fork", "Lower Fork"):
        arm = node_mesh_report(obj, arm_name)
        assert arm["dimensions"][2] <= values["rib_height"] + 0.05, (
            arm_name,
            arm["dimensions"],
        )
    set_parameter(modifier, "Under-Prop Rib Height (mm)", 12.0)
    bpy.context.view_layer.update()
    tall_arms = node_mesh_report(obj, "Place Arm Network")
    assert max(z for _x, _y, z in tall_arms["coordinates"]) <= MOUNT_Z_MAX + 0.05, (
        max(z for _x, _y, z in tall_arms["coordinates"]),
        MOUNT_Z_MAX,
    )
    for name, (_minimum, _maximum, default) in PARAMETERS.items():
        set_parameter(modifier, name, default)
    bpy.context.view_layer.update()
    bumper = node_mesh_report(obj, "Place Bumper")
    bumper_angles = tuple(
        math.degrees(math.atan2(y, x)) % 360.0 for x, y, _z in bumper["coordinates"]
    )
    assert bumper_angles
    cap_angle = math.degrees(math.asin(values["bumper"] / 2.0 / values["bumper_center_radius"]))
    assert min(bumper_angles) >= ARC_START - cap_angle - 1.0, min(bumper_angles)
    assert max(bumper_angles) <= ARC_END + cap_angle + 1.0, max(bumper_angles)
    for name, (_minimum, _maximum, default) in PARAMETERS.items():
        socket = parameter_socket(modifier, name)
        actual = getattr(modifier.properties.inputs, socket.identifier).value
        assert math.isclose(actual, default, rel_tol=1e-6, abs_tol=1e-6), (name, actual)
    bpy.context.view_layer.update()
    evaluated = evaluated_vertices(obj)
    measured = dimensions(evaluated)
    radial_diameter = 2.0 * max(math.hypot(x, y) for x, y, _z in evaluated)
    assert abs(radial_diameter - values["outer_diameter"]) <= 0.05, radial_diameter
    assert abs(measured[2] - 12.0) <= 0.05, measured
    report = mesh_report(obj)
    assert report["components"] == 1, report
    assert report["nonmanifold_edges"] == 0, report
    mass_low = report["volume_mm3"] * 0.00120
    mass_high = report["volume_mm3"] * 0.00125
    assert 0.0 < mass_low < mass_high, (mass_low, mass_high)
    measurements = {
        "PG_V3_Evaluated_Volume_mm3": report["volume_mm3"],
        "PG_V3_Estimated_Mass_g_1.20": mass_low,
        "PG_V3_Estimated_Mass_g_1.25": mass_high,
    }
    defaults = "2 in, 12 mm height, 2.2 mm bumper, balanced, 0.4 mm nozzle"
    if "--verify-only" in sys.argv:
        for key, expected in measurements.items():
            assert key in obj and math.isclose(obj[key], expected, rel_tol=1e-6), key
        assert obj.get("PG_V3_Defaults") == defaults
    else:
        for old_key in (
            "PG_V2_Estimated_Mass_g_1.20",
            "PG_V2_Estimated_Mass_g_1.25",
            "PG_V2_Defaults",
        ):
            obj.pop(old_key, None)
        for key, value in measurements.items():
            obj[key] = value
        obj["PG_V3_Defaults"] = defaults

    try:
        for case in VALIDATION_CASES:
            for name, value in zip(PARAMETERS, case):
                set_parameter(modifier, name, value)
            bpy.context.view_layer.update()
            expected = sizing(*case)
            case_report = mesh_report(obj)
            assert (
                case_report["components"],
                case_report["nonmanifold_edges"],
            ) == (1, 0), (case, case_report["components"], case_report["nonmanifold_edges"])
            radial_diameter = 2.0 * max(
                math.hypot(x, y) for x, y, _z in case_report["coordinates"]
            )
            assert abs(radial_diameter - expected["outer_diameter"]) <= 0.05, (
                case,
                radial_diameter,
            )
            assert abs(case_report["dimensions"][2] - case[1]) <= 0.05, (
                case,
                case_report["dimensions"],
            )
            for measured_hole, expected_center in zip(
                hole_report(obj), hole_centers()
            ):
                assert math.dist(measured_hole["center"], expected_center) <= 0.02, case
                assert abs(measured_hole["through_radius"] - THROUGH_RADIUS) <= 0.03, case
                assert abs(measured_hole["recess_radius"] - RECESS_RADIUS) <= 0.03, case
                assert abs(measured_hole["recess_top_z"] - RECESS_TOP_Z) <= 0.02, case
    finally:
        for name, (_minimum, _maximum, default) in PARAMETERS.items():
            set_parameter(modifier, name, default)
        bpy.context.view_layer.update()


if __name__ == "__main__":
    if "--verify-only" not in sys.argv:
        install()
    if "--self-check" in sys.argv:
        self_check()
