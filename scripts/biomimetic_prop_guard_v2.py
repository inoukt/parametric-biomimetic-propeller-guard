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
ARC_CENTER = (ARC_START + ARC_END) / 2.0
PROP_PRESETS = (2.0, 2.5, 3.0, 3.5, 4.0, 5.0)
GROUP_NAME = "PG_BiomimeticGuardV2"
MODIFIER_NAME = "PG Biomimetic Guard V2"
NORMAL_MODIFIER_NAME = "PG Weighted Normals"
DESCRIPTION_OBJECT_NAME = "PG Parameter Descriptions"
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
    "Arc Coverage (deg)": (180.0, 210.0, 210.0),
    "Nozzle Preset": (0.0, 3.0, 0.0),
    "Sacrificial Lip (mm)": (0.0, 1.2, 0.4),
    "Light Bumper Profile": (0.0, 1.0, 0.0),
    "Size Check Print": (0.0, 1.0, 0.0),
    "Motor Mount Pattern": (0.0, 3.0, 1.0),
    "Motor Example Preset": (0.0, 4.0, 0.0),
}
PARAMETER_DESCRIPTIONS = {
    "Propeller Diameter (in)": "Target prop size. Presets tested from 2 to 5 inch.",
    "Guard Height (mm)": "Vertical height of the outer protector rail.",
    "Bumper Thickness (mm)": "Base wall thickness for the outer impact rail.",
    "Strength / Weight": "Balances rib thickness against weight. Higher is stronger/heavier.",
    "Nozzle Diameter (mm)": "Custom nozzle width used when Nozzle Preset is 0.",
    "Safety Clearance Override (mm)": "Optional radial blade clearance. 0 uses automatic clearance.",
    "Under-Prop Rib Height (mm)": "Support rib height. Grows downward from motor top, not into the motor.",
    "Bio Reinforcement": "Adds organic pad strength at branch junctions and long-span scaling.",
    "Edge Smoothness": "Raises curve/profile resolution for smoother printed edges.",
    "Arc Coverage (deg)": "Outer protector coverage. Lower values print faster and protect less arc.",
    "Nozzle Preset": "0 custom, 1 = 0.4 mm, 2 = 0.6 mm, 3 = 0.8 mm.",
    "Sacrificial Lip (mm)": "Separate thin outer wear bead added outside the main bumper for scuffs/impacts.",
    "Light Bumper Profile": "Lightens the bumper rail while keeping the same outside protection diameter.",
    "Size Check Print": "1 keeps the selected prop diameter for a real clearance/fit check print.",
    "Motor Mount Pattern": "Manual layout used when Motor Example Preset is 0: 0 = dia 9 mm, 1 = dia 12 mm, 2 = 16x16 mm, 3 = 16x19 mm.",
    "Motor Example Preset": "Overrides Motor Mount Pattern: 0 manual, 1 BETAFPV 1105 dia 9 mm, 2 BETAFPV 1505 dia 12 mm, 3 16x16 mm, 4 16x19 mm.",
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


def motor_pattern_centers(pattern=1.0):
    index = round(pattern)
    assert 0 <= index <= 3
    if index < 2:
        radius = (4.5, 6.0)[index]
        return ((radius, 0.0), (0.0, radius), (-radius, 0.0), (0.0, -radius))
    half_y = (8.0, 9.5)[index - 2]
    return ((8.0, half_y), (-8.0, half_y), (-8.0, -half_y), (8.0, -half_y))


def motor_example_centers(pattern=1.0, example=0.0):
    index = round(example)
    assert 0 <= index <= 4
    return motor_pattern_centers(index - 1 if index else pattern)


def hole_centers(pattern=1.0, example=0.0):
    return motor_example_centers(pattern, example)


def effective_nozzle(nozzle, preset):
    if preset >= 2.5:
        return 0.8
    if preset >= 1.5:
        return 0.6
    if preset >= 0.5:
        return 0.4
    return nozzle


def branch_angles(arc_coverage):
    start = ARC_CENTER - arc_coverage / 2.0
    end = ARC_CENTER + arc_coverage / 2.0
    margin = 20.0
    step = (arc_coverage - 2.0 * margin) / 2.0
    return (start + margin, start + margin + step, end - margin)


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
    arc_coverage=210.0,
    nozzle_preset=0.0,
    sacrificial_lip=0.4,
    light_bumper=0.0,
    size_check=0.0,
):
    assert 2.0 <= prop_inches <= 5.0
    assert 3.3 <= height <= 101.6
    assert 0.0 <= strength <= 1.0
    assert 0.4 <= nozzle <= 0.8
    assert clearance_override >= 0.0
    assert 1.2 <= rib_height <= 12.0
    assert 0.0 <= bio_reinforcement <= 1.0
    assert 0.0 <= edge_smoothness <= 1.0
    assert 180.0 <= arc_coverage <= 210.0
    assert 0.0 <= nozzle_preset <= 3.0
    assert 0.0 <= sacrificial_lip <= 1.2
    assert 0.0 <= light_bumper <= 1.0
    assert 0.0 <= size_check <= 1.0
    nozzle = effective_nozzle(nozzle, nozzle_preset)
    prop_mm = prop_inches * 25.4
    min_feature = 3.0 * nozzle
    assert 1.2 <= bumper <= 8.0
    bumper = max(bumper, min_feature)
    profile_bumper = max(min_feature, bumper * (1.0 - 0.35 * light_bumper))
    clearance = clearance_override or max(2.0, 0.04 * prop_mm)
    inner_radius = prop_mm / 2.0 + clearance
    prop_scale = (prop_inches - 2.0) / 3.0
    span_reinforcement = 1.0 + prop_scale * (0.35 + 0.20 * bio_reinforcement)
    primary_width = max(min_feature, profile_bumper * (0.55 + 0.25 * strength) * span_reinforcement)
    fork_width = max(min_feature, primary_width * (0.65 + 0.15 * strength))
    rib_height = min(height, max(rib_height, min_feature))
    bumper_center_radius = inner_radius + bumper - profile_bumper / 2.0
    lip_width = max(0.0, sacrificial_lip)
    lip_center_radius = inner_radius + bumper + lip_width / 2.0
    outer_radius = inner_radius + bumper + lip_width
    arc_start = ARC_CENTER - arc_coverage / 2.0
    arc_end = ARC_CENTER + arc_coverage / 2.0
    return {
        "prop_mm": prop_mm,
        "height": height,
        "bumper": bumper,
        "profile_bumper": profile_bumper,
        "strength": strength,
        "nozzle": nozzle,
        "min_feature": min_feature,
        "clearance": clearance,
        "inner_radius": inner_radius,
        "bumper_center_radius": bumper_center_radius,
        "lip_width": lip_width,
        "lip_center_radius": lip_center_radius,
        "outer_diameter": 2.0 * outer_radius,
        "primary_width": primary_width,
        "fork_width": fork_width,
        "root_radius": 12.0,
        "rib_height": rib_height,
        "fork_radius": max(16.0, inner_radius * 0.68),
        "fork_angle": math.radians(18.0),
        "bio_reinforcement": bio_reinforcement,
        "span_reinforcement": span_reinforcement,
        "edge_smoothness": edge_smoothness,
        "arc_start": arc_start,
        "arc_end": arc_end,
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
    preset_04 = node(group.nodes, "GeometryNodeSwitch", "Nozzle Preset 0.4")
    preset_04.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 0.4 Nozzle Preset", "GREATER_THAN", group_in.outputs["Nozzle Preset"], 0.5),
        preset_04.inputs["Switch"],
    )
    group.links.new(group_in.outputs["Nozzle Diameter (mm)"], preset_04.inputs["False"])
    preset_04.inputs["True"].default_value = 0.4
    preset_06 = node(group.nodes, "GeometryNodeSwitch", "Nozzle Preset 0.6")
    preset_06.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 0.6 Nozzle Preset", "GREATER_THAN", group_in.outputs["Nozzle Preset"], 1.5),
        preset_06.inputs["Switch"],
    )
    group.links.new(preset_04.outputs["Output"], preset_06.inputs["False"])
    preset_06.inputs["True"].default_value = 0.6
    nozzle = node(group.nodes, "GeometryNodeSwitch", "Nozzle Preset 0.8")
    nozzle.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 0.8 Nozzle Preset", "GREATER_THAN", group_in.outputs["Nozzle Preset"], 2.5),
        nozzle.inputs["Switch"],
    )
    group.links.new(preset_06.outputs["Output"], nozzle.inputs["False"])
    nozzle.inputs["True"].default_value = 0.8
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
        nozzle.outputs["Output"],
        3.0,
    )
    bumper = math_node(
        group,
        "Validated Bumper Thickness",
        "MAXIMUM",
        group_in.outputs["Bumper Thickness (mm)"],
        minimum_feature,
    )
    light_bumper_reduction = math_node(
        group, "Light Bumper Reduction", "MULTIPLY", group_in.outputs["Light Bumper Profile"], 0.35
    )
    light_bumper_scale = math_node(group, "Light Bumper Scale", "SUBTRACT", 1.0, light_bumper_reduction)
    profile_bumper = math_node(
        group,
        "Printable Light Bumper Width",
        "MAXIMUM",
        minimum_feature,
        math_node(group, "Scaled Light Bumper Width", "MULTIPLY", bumper, light_bumper_scale),
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
    mount_9 = node(group.nodes, "GeometryNodeSwitch", "Motor Mount Pattern 9mm")
    mount_9.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 9mm Motor Mount", "LESS_THAN", group_in.outputs["Motor Mount Pattern"], 0.5),
        mount_9.inputs["Switch"],
    )
    mount_9.inputs["False"].default_value = 12.0
    mount_9.inputs["True"].default_value = 9.0
    mount_16 = node(group.nodes, "GeometryNodeSwitch", "Motor Mount Pattern 16mm")
    mount_16.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 16mm Motor Mount", "GREATER_THAN", group_in.outputs["Motor Mount Pattern"], 1.5),
        mount_16.inputs["Switch"],
    )
    group.links.new(mount_9.outputs["Output"], mount_16.inputs["False"])
    mount_16.inputs["True"].default_value = 16.0
    mount_19 = node(group.nodes, "GeometryNodeSwitch", "Motor Mount Pattern 19mm")
    mount_19.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 19mm Motor Mount", "GREATER_THAN", group_in.outputs["Motor Mount Pattern"], 2.5),
        mount_19.inputs["Switch"],
    )
    group.links.new(mount_16.outputs["Output"], mount_19.inputs["False"])
    mount_19.inputs["True"].default_value = 19.0
    example_9 = node(group.nodes, "GeometryNodeSwitch", "Motor Example BETAFPV 1105 9mm")
    example_9.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use BETAFPV 1105 Example", "GREATER_THAN", group_in.outputs["Motor Example Preset"], 0.5),
        example_9.inputs["Switch"],
    )
    group.links.new(mount_19.outputs["Output"], example_9.inputs["False"])
    example_9.inputs["True"].default_value = 9.0
    example_12 = node(group.nodes, "GeometryNodeSwitch", "Motor Example 12mm Micro")
    example_12.input_type = "FLOAT"
    group.links.new(
        math_node(group, "Use 12mm Micro Example", "GREATER_THAN", group_in.outputs["Motor Example Preset"], 1.5),
        example_12.inputs["Switch"],
    )
    group.links.new(example_9.outputs["Output"], example_12.inputs["False"])
    example_12.inputs["True"].default_value = 12.0
    manual_mount = math_node(
        group, "Use Manual Motor Mount", "LESS_THAN", group_in.outputs["Motor Example Preset"], 0.5
    )
    rectangular_mount = math_node(
        group,
        "Use Rectangular Motor Mount",
        "MAXIMUM",
        math_node(group, "Use Rectangular Motor Example", "GREATER_THAN", group_in.outputs["Motor Example Preset"], 2.5),
        math_node(
            group,
            "Use Manual Rectangular Motor Mount",
            "MULTIPLY",
            manual_mount,
            math_node(group, "Manual Pattern Is Rectangular", "GREATER_THAN", group_in.outputs["Motor Mount Pattern"], 1.5),
        ),
    )
    rect_half_y = node(group.nodes, "GeometryNodeSwitch", "Rectangular Motor Mount Half Y")
    rect_half_y.input_type = "FLOAT"
    group.links.new(
        math_node(
            group,
            "Use 16x19 Motor Mount",
            "MAXIMUM",
            math_node(group, "Use 16x19 Motor Example", "GREATER_THAN", group_in.outputs["Motor Example Preset"], 3.5),
            math_node(
                group,
                "Use Manual 16x19 Motor Mount",
                "MULTIPLY",
                manual_mount,
                math_node(group, "Manual Pattern Is 16x19", "GREATER_THAN", group_in.outputs["Motor Mount Pattern"], 2.5),
            ),
        ),
        rect_half_y.inputs["Switch"],
    )
    rect_half_y.inputs["False"].default_value = 8.0
    rect_half_y.inputs["True"].default_value = 9.5
    cross_radius = math_node(group, "Cross Motor Mount Radius", "DIVIDE", example_12.outputs["Output"], 2.0)
    rect_half_x = 8.0
    mount_radius = node(group.nodes, "GeometryNodeSwitch", "Motor Mount Radius For Plate")
    mount_radius.input_type = "FLOAT"
    group.links.new(rectangular_mount, mount_radius.inputs["Switch"])
    group.links.new(cross_radius, mount_radius.inputs["False"])
    group.links.new(
        math_node(
            group,
            "Rectangular Motor Mount Radius",
            "SQRT",
            math_node(
                group,
                "Rectangular Motor Mount Radius Squared",
                "ADD",
                rect_half_x * rect_half_x,
                math_node(group, "Rectangular Half Y Squared", "MULTIPLY", rect_half_y.outputs["Output"], rect_half_y.outputs["Output"]),
            ),
            0.0,
        ),
        mount_radius.inputs["True"],
    )
    plate_radius = math_node(
        group,
        "Motor Plate Radius For Pattern",
        "MAXIMUM",
        PLATE_RADIUS,
        math_node(
            group,
            "Pattern Plate Clearance Radius",
            "ADD",
            mount_radius.outputs["Output"],
            RECESS_RADIUS + 1.5,
        ),
    )
    prop_radius = math_node(group, "Propeller Radius", "DIVIDE", prop_mm, 2.0)
    inner_radius = math_node(
        group, "Inner Opening Radius", "ADD", prop_radius, clearance.outputs["Output"]
    )
    half_bumper = math_node(group, "Half Bumper", "DIVIDE", bumper, 2.0)
    half_profile_bumper = math_node(group, "Half Light Bumper", "DIVIDE", profile_bumper, 2.0)
    base_outer_radius = math_node(group, "Base Bumper Outer Radius", "ADD", inner_radius, bumper)
    bumper_center_radius = math_node(
        group, "Bumper Center Radius", "SUBTRACT", base_outer_radius, half_profile_bumper
    )
    half_lip = math_node(group, "Half Sacrificial Lip", "DIVIDE", group_in.outputs["Sacrificial Lip (mm)"], 2.0)
    lip_center_radius = math_node(
        group, "Sacrificial Lip Center Radius", "ADD", base_outer_radius, half_lip
    )
    arc_half = math_node(group, "Arc Coverage Half", "DIVIDE", group_in.outputs["Arc Coverage (deg)"], 2.0)
    arc_start = math_node(
        group, "Dynamic Arc Start", "DIVIDE", math_node(group, "Arc Start Degrees", "SUBTRACT", ARC_CENTER, arc_half), 360.0
    )
    arc_end = math_node(
        group, "Dynamic Arc End", "DIVIDE", math_node(group, "Arc End Degrees", "ADD", ARC_CENTER, arc_half), 360.0
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
        "profile_bumper": profile_bumper,
        "inner_radius": inner_radius,
        "bumper_center_radius": bumper_center_radius,
        "lip_width": group_in.outputs["Sacrificial Lip (mm)"],
        "lip_center_radius": lip_center_radius,
        "height": group_in.outputs["Guard Height (mm)"],
        "rib_height": rib_height,
        "bio_reinforcement": group_in.outputs["Bio Reinforcement"],
        "span_reinforcement": span_reinforcement,
        "mount_diameter": example_12.outputs["Output"],
        "rectangular_mount": rectangular_mount,
        "rect_half_y": rect_half_y.outputs["Output"],
        "plate_radius": plate_radius,
        "motor_pattern": group_in.outputs["Motor Mount Pattern"],
        "motor_example": group_in.outputs["Motor Example Preset"],
        "smooth_steps": smooth_steps,
        "arc_start": arc_start,
        "arc_end": arc_end,
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
    lip_circle = node(nodes, "GeometryNodeCurvePrimitiveCircle", "Sacrificial Lip Centerline")
    lip_circle.mode = "RADIUS"
    lip_circle.inputs["Resolution"].default_value = 128
    trim = node(nodes, "GeometryNodeTrimCurve", "Open Bumper Arc")
    trim.mode = "FACTOR"
    links.new(values["arc_start"], trim.inputs["Start"])
    links.new(values["arc_end"], trim.inputs["End"])
    lip_trim = node(nodes, "GeometryNodeTrimCurve", "Open Sacrificial Lip Arc")
    lip_trim.mode = "FACTOR"
    links.new(values["arc_start"], lip_trim.inputs["Start"])
    links.new(values["arc_end"], lip_trim.inputs["End"])
    relief = math_node(
        group, "Low Height Bumper Relief", "MULTIPLY", values["low_height"], 0.02
    )
    bumper_height = math_node(
        group, "Boolean Relief Bumper Height", "SUBTRACT", values["height"], relief
    )
    profile = flat_bottom_profile(
        group, "Rounded Bumper Profile", values["profile_bumper"], bumper_height, values["smooth_steps"]
    )
    lip_width = math_node(group, "Printable Sacrificial Lip Width", "MAXIMUM", values["lip_width"], 0.01)
    lip_profile = flat_bottom_profile(
        group, "Sacrificial Lip Profile", lip_width, bumper_height, values["smooth_steps"]
    )
    curve_to_mesh = node(nodes, "GeometryNodeCurveToMesh", "Solid Bumper")
    curve_to_mesh.inputs["Fill Caps"].default_value = True
    lip_to_mesh = node(nodes, "GeometryNodeCurveToMesh", "Solid Sacrificial Lip")
    lip_to_mesh.inputs["Fill Caps"].default_value = True
    transform = node(nodes, "GeometryNodeTransform", "Place Bumper")
    cap_radius = math_node(group, "Bumper End Cap Radius", "DIVIDE", values["profile_bumper"], 2.0)
    start_angle = math_node(group, "Bumper Start Angle Radians", "MULTIPLY", values["arc_start"], math.tau)
    end_angle = math_node(group, "Bumper End Angle Radians", "MULTIPLY", values["arc_end"], math.tau)
    start_x = math_node(
        group,
        "Bumper Start Cap X",
        "MULTIPLY",
        values["bumper_center_radius"],
        math_node(group, "Bumper Start Cap Cosine", "COSINE", start_angle, 0.0),
    )
    start_y = math_node(
        group,
        "Bumper Start Cap Y",
        "MULTIPLY",
        values["bumper_center_radius"],
        math_node(group, "Bumper Start Cap Sine", "SINE", start_angle, 0.0),
    )
    end_x = math_node(
        group,
        "Bumper End Cap X",
        "MULTIPLY",
        values["bumper_center_radius"],
        math_node(group, "Bumper End Cap Cosine", "COSINE", end_angle, 0.0),
    )
    end_y = math_node(
        group,
        "Bumper End Cap Y",
        "MULTIPLY",
        values["bumper_center_radius"],
        math_node(group, "Bumper End Cap Sine", "SINE", end_angle, 0.0),
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
    lip_cap_radius = math_node(group, "Sacrificial Lip End Cap Radius", "DIVIDE", lip_width, 2.0)
    lip_start_x = math_node(
        group,
        "Sacrificial Lip Start Cap X",
        "MULTIPLY",
        values["lip_center_radius"],
        math_node(group, "Sacrificial Lip Start Cap Cosine", "COSINE", start_angle, 0.0),
    )
    lip_start_y = math_node(
        group,
        "Sacrificial Lip Start Cap Y",
        "MULTIPLY",
        values["lip_center_radius"],
        math_node(group, "Sacrificial Lip Start Cap Sine", "SINE", start_angle, 0.0),
    )
    lip_end_x = math_node(
        group,
        "Sacrificial Lip End Cap X",
        "MULTIPLY",
        values["lip_center_radius"],
        math_node(group, "Sacrificial Lip End Cap Cosine", "COSINE", end_angle, 0.0),
    )
    lip_end_y = math_node(
        group,
        "Sacrificial Lip End Cap Y",
        "MULTIPLY",
        values["lip_center_radius"],
        math_node(group, "Sacrificial Lip End Cap Sine", "SINE", end_angle, 0.0),
    )
    lip_start_cap = junction_pad(
        group,
        "Sacrificial Lip Start Cap",
        lip_start_x,
        lip_start_y,
        lip_width,
        bumper_height,
        radius_socket=lip_cap_radius,
    )
    lip_end_cap = junction_pad(
        group,
        "Sacrificial Lip End Cap",
        lip_end_x,
        lip_end_y,
        lip_width,
        bumper_height,
        radius_socket=lip_cap_radius,
    )
    with_start_cap = union_node(
        group, "Bumper With Rounded Start Cap", curve_to_mesh.outputs["Mesh"], start_cap, solver="MANIFOLD"
    )
    rounded_bumper = union_node(
        group, "Bumper With Rounded End Caps", with_start_cap, end_cap, solver="MANIFOLD"
    )
    lip_with_start_cap = union_node(
        group, "Sacrificial Lip With Start Cap", lip_to_mesh.outputs["Mesh"], lip_start_cap, solver="MANIFOLD"
    )
    rounded_lip = union_node(
        group, "Sacrificial Lip With End Caps", lip_with_start_cap, lip_end_cap, solver="MANIFOLD"
    )
    lip_union = union_node(group, "Bumper With Sacrificial Lip", rounded_bumper, rounded_lip, solver="MANIFOLD")
    use_lip = math_node(group, "Use Sacrificial Lip Geometry", "GREATER_THAN", values["lip_width"], 0.01)
    bumper_with_optional_lip = node(nodes, "GeometryNodeSwitch", "Optional Sacrificial Lip")
    bumper_with_optional_lip.input_type = "GEOMETRY"
    links.new(values["bumper_center_radius"], circle.inputs["Radius"])
    links.new(values["lip_center_radius"], lip_circle.inputs["Radius"])
    links.new(circle.outputs["Curve"], trim.inputs["Curve"])
    links.new(lip_circle.outputs["Curve"], lip_trim.inputs["Curve"])
    links.new(trim.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    links.new(lip_trim.outputs["Curve"], lip_to_mesh.inputs["Curve"])
    links.new(profile, curve_to_mesh.inputs["Profile Curve"])
    links.new(lip_profile, lip_to_mesh.inputs["Profile Curve"])
    links.new(use_lip, bumper_with_optional_lip.inputs["Switch"])
    links.new(rounded_bumper, bumper_with_optional_lip.inputs["False"])
    links.new(lip_union, bumper_with_optional_lip.inputs["True"])
    links.new(bumper_with_optional_lip.outputs["Output"], transform.inputs["Geometry"])
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
        math_node(group, "Fork Clears Motor Plate", "ADD", values["plate_radius"], 4.0),
    )
    arm_root_radius = math_node(
        group,
        "Arm Root Clears Motor Plate",
        "MAXIMUM",
        11.0,
        math_node(group, "Arm Root Plate Edge", "SUBTRACT", values["plate_radius"], 1.0),
    )
    arm_root_handle = math_node(group, "Arm Root Handle", "ADD", arm_root_radius, 3.0)
    primary_end_handle_x = math_node(
        group, "Primary End Handle X", "MULTIPLY", fork_radius, 0.80
    )
    primary_curve = bezier_segment(
        group,
        "Primary Arm Curve",
        combine_xyz(group, "Primary Root Point", arm_root_radius, 0.0, 0.0),
        combine_xyz(group, "Primary Root Handle", arm_root_handle, 0.0, 0.0),
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
        math_node(group, "Root Junction X", "ADD", arm_root_radius, 0.5),
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
    arc_start_degrees = math_node(group, "Arm Arc Start Degrees", "MULTIPLY", values["arc_start"], 360.0)
    arm_start = math_node(group, "Arm Start Inside Arc", "ADD", arc_start_degrees, 20.0)
    arm_step = math_node(
        group,
        "Arm Arc Coverage Step",
        "DIVIDE",
        math_node(
            group,
            "Arm Coverage Minus Margins",
            "SUBTRACT",
            math_node(group, "Arm Arc Coverage Degrees", "MULTIPLY", math_node(group, "Arm Arc Width Factor", "SUBTRACT", values["arc_end"], values["arc_start"]), 360.0),
            40.0,
        ),
        2.0,
    )
    rotation_z = math_node(
        group,
        "Arm Rotation Step",
        "MULTIPLY",
        index.outputs["Index"],
        math_node(group, "Arm Step Radians", "MULTIPLY", arm_step, math.pi / 180.0),
    )
    rotation_z = math_node(
        group,
        "Arm Rotation",
        "ADD",
        rotation_z,
        math_node(group, "Arm Start Radians", "MULTIPLY", arm_start, math.pi / 180.0),
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


def translated_geometry(group, name, geometry, x, y):
    place = node(group.nodes, "GeometryNodeTransform", name)
    group.links.new(geometry, place.inputs["Geometry"])
    group.links.new(combine_xyz(group, f"{name} Offset", x, y, 0.0), place.inputs["Translation"])
    return place.outputs["Geometry"]


def motor_plate_nodes(group, values):
    nodes, links = group.nodes, group.links
    plate = node(nodes, "GeometryNodeMeshCylinder", "V3 Motor Plate")
    plate.inputs["Vertices"].default_value = 128
    links.new(values["plate_radius"], plate.inputs["Radius"])
    plate.inputs["Depth"].default_value = MOUNT_Z_MAX - MOUNT_Z_MIN
    place_plate = node(nodes, "GeometryNodeTransform", "Place V3 Motor Plate")
    place_plate.inputs["Translation"].default_value = (
        *MOTOR_CENTER,
        (MOUNT_Z_MIN + MOUNT_Z_MAX) / 2.0,
    )
    links.new(plate.outputs["Mesh"], place_plate.inputs["Geometry"])

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

    cross_radius = math_node(group, "V3 Cross Hole Radius", "DIVIDE", values["mount_diameter"], 2.0)
    negative_cross_radius = math_node(group, "V3 Negative Cross Hole Radius", "MULTIPLY", cross_radius, -1.0)
    negative_rect_half_x = -8.0
    negative_rect_half_y = math_node(group, "V3 Negative Rect Half Y", "MULTIPLY", values["rect_half_y"], -1.0)
    cross_centers = (
        (cross_radius, 0.0),
        (0.0, cross_radius),
        (negative_cross_radius, 0.0),
        (0.0, negative_cross_radius),
    )
    rect_centers = (
        (8.0, values["rect_half_y"]),
        (negative_rect_half_x, values["rect_half_y"]),
        (negative_rect_half_x, negative_rect_half_y),
        (8.0, negative_rect_half_y),
    )
    through_realized = node(nodes, "GeometryNodeJoinGeometry", "V3 Through Cutters")
    recess_realized = node(nodes, "GeometryNodeJoinGeometry", "V3 Recess Cutters")
    for index, (cross_center, rect_center) in enumerate(zip(cross_centers, rect_centers), start=1):
        hole_x = node(nodes, "GeometryNodeSwitch", f"V3 Hole {index} X")
        hole_x.input_type = "FLOAT"
        links.new(values["rectangular_mount"], hole_x.inputs["Switch"])
        _set_or_link(links, hole_x.inputs["False"], cross_center[0])
        _set_or_link(links, hole_x.inputs["True"], rect_center[0])
        hole_y = node(nodes, "GeometryNodeSwitch", f"V3 Hole {index} Y")
        hole_y.input_type = "FLOAT"
        links.new(values["rectangular_mount"], hole_y.inputs["Switch"])
        _set_or_link(links, hole_y.inputs["False"], cross_center[1])
        _set_or_link(links, hole_y.inputs["True"], rect_center[1])
        links.new(
            translated_geometry(group, f"Place V3 Through Cutter {index}", place_through.outputs["Geometry"], hole_x.outputs["Output"], hole_y.outputs["Output"]),
            through_realized.inputs["Geometry"],
        )
        links.new(
            translated_geometry(group, f"Place V3 Recess Cutter {index}", place_recess.outputs["Geometry"], hole_x.outputs["Output"], hole_y.outputs["Output"]),
            recess_realized.inputs["Geometry"],
        )

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
        is_choice = name in {"Motor Mount Pattern", "Motor Example Preset"}
        socket = group.interface.new_socket(
            name=name,
            in_out="INPUT",
            socket_type="NodeSocketInt" if is_choice else "NodeSocketFloat",
        )
        socket.min_value = int(minimum) if is_choice else minimum
        socket.max_value = int(maximum) if is_choice else maximum
        socket.default_value = int(default) if is_choice else default
        socket.description = PARAMETER_DESCRIPTIONS[name]

    nodes, links = group.nodes, group.links
    group_in = node(nodes, "NodeGroupInput", "Inputs")
    group_out = node(nodes, "NodeGroupOutput", "Output")
    values = parameter_nodes(group, group_in)
    bumper = bumper_nodes(group, values)
    arms = arm_nodes(group, values)
    mount = motor_plate_nodes(group, values)
    body = union_node(group, "Union Mount and Arms", mount, arms)
    final_manifold = union_node(group, "Union V3 Body", body, bumper, solver="MANIFOLD")
    final_exact = union_node(group, "Union V3 Body Motor Example", body, bumper)
    final = node(nodes, "GeometryNodeSwitch", "Motor Example Final Solver")
    final.input_type = "GEOMETRY"
    links.new(
        math_node(
            group,
            "Use Tolerant Final Solver",
            "MAXIMUM",
            math_node(group, "Use Motor Example Final Solver", "GREATER_THAN", values["motor_example"], 0.5),
            math_node(
                group,
                "Use Manual Mount Final Solver",
                "MAXIMUM",
                math_node(group, "Use 9mm Final Solver", "LESS_THAN", values["motor_pattern"], 0.5),
                math_node(group, "Use Rectangular Final Solver", "GREATER_THAN", values["motor_pattern"], 1.5),
            ),
        ),
        final.inputs["Switch"],
    )
    links.new(final_manifold, final.inputs["False"])
    links.new(final_exact, final.inputs["True"])
    links.new(final.outputs["Output"], group_out.inputs["Geometry"])
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
        getattr(modifier.properties.inputs, socket.identifier).value = int(default) if socket.socket_type == "NodeSocketInt" else default
    v1 = obj.modifiers.get("PG Parametric Guard")
    if v1:
        v1.show_viewport = False
        v1.show_render = False
    return modifier


def install_description_text():
    body = "\n".join(
        (
            "Parametric Propeller Guard Controls",
            "",
            "Motor Mount Pattern:",
            "0 = dia 9 mm, 1 = dia 12 mm default, 2 = 16x16 mm, 3 = 16x19 mm.",
            "Motor Example Preset overrides this manual pattern whenever it is above 0.",
            "For your 1505 motors, use Motor Example Preset 2: measured 12 mm between opposite hole centers.",
            "",
            "Fast TPU Print Recipe:",
            "Arc Coverage 180-195 deg, Light Bumper Profile 1, Edge Smoothness 0.2-0.4, Nozzle Preset 2 for 0.6 mm.",
            "",
            "Stronger TPU Recipe:",
            "Arc Coverage 210 deg, Bio Reinforcement 0.7-1, Strength / Weight 0.7-1, Light Bumper Profile 0.",
            "",
            "Size Check Print:",
            "Set Size Check Print to 1. It keeps the selected prop diameter so clearance is real.",
            "",
            "Sacrificial Lip:",
            "Adds a separate outer wear bead. The main bumper stays fixed; only the scuff rail grows outward.",
            "",
            "Parameter Details:",
            *[f"{name}: {PARAMETER_DESCRIPTIONS[name]}" for name in PARAMETERS],
        )
    )
    text = bpy.data.objects.get(DESCRIPTION_OBJECT_NAME)
    if text:
        assert text.type == "FONT"
        curve = text.data
    else:
        curve = bpy.data.curves.new(DESCRIPTION_OBJECT_NAME, "FONT")
        text = bpy.data.objects.new(DESCRIPTION_OBJECT_NAME, curve)
        bpy.context.collection.objects.link(text)
    curve.body = body
    curve.align_x = "LEFT"
    curve.align_y = "TOP"
    curve.size = 2.2
    text.location = (-75.0, -65.0, 0.0)
    text.rotation_euler = (0.0, 0.0, 0.0)
    return text


def install():
    obj = get_guard()
    modifier = install_modifier(obj)
    normal = obj.modifiers.get(NORMAL_MODIFIER_NAME)
    if normal:
        assert normal.type == "WEIGHTED_NORMAL"
    else:
        normal = obj.modifiers.new(NORMAL_MODIFIER_NAME, "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    install_description_text()
    return modifier


def parameter_socket(modifier, name):
    return next(
        item
        for item in modifier.node_group.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == name
    )


def set_parameter(modifier, name, value):
    socket = parameter_socket(modifier, name)
    getattr(modifier.properties.inputs, socket.identifier).value = int(value) if socket.socket_type == "NodeSocketInt" else value
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


def node_hole_report(obj, node_name, pattern=1.0, example=0.0):
    group = obj.modifiers[MODIFIER_NAME].node_group
    output = group.nodes["Output"].inputs["Geometry"]
    original_socket = output.links[0].from_socket
    try:
        for link in tuple(output.links):
            group.links.remove(link)
        group.links.new(group.nodes[node_name].outputs[0], output)
        bpy.context.view_layer.update()
        return hole_report(obj, pattern, example)
    finally:
        for link in tuple(output.links):
            group.links.remove(link)
        group.links.new(original_socket, output)
        bpy.context.view_layer.update()


def hole_report(obj, pattern=1.0, example=0.0):
    vertices = evaluated_vertices(obj)
    reports = []
    for expected_x, expected_y in hole_centers(pattern, example):
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
    assert hole_centers(pattern=0.0) == ((4.5, 0.0), (0.0, 4.5), (-4.5, 0.0), (0.0, -4.5))
    assert hole_centers(pattern=2.0) == ((8.0, 8.0), (-8.0, 8.0), (-8.0, -8.0), (8.0, -8.0))
    assert hole_centers(pattern=3.0) == ((8.0, 9.5), (-8.0, 9.5), (-8.0, -9.5), (8.0, -9.5))
    assert hole_centers(example=1.0) == ((4.5, 0.0), (0.0, 4.5), (-4.5, 0.0), (0.0, -4.5))
    assert hole_centers(example=3.0) == ((8.0, 8.0), (-8.0, 8.0), (-8.0, -8.0), (8.0, -8.0))
    assert hole_centers(example=4.0) == ((8.0, 9.5), (-8.0, 9.5), (-8.0, -9.5), (8.0, -9.5))
    assert all(hole_centers(pattern=index) == hole_centers(example=index + 1) for index in range(4))
    obj = get_guard()
    assert tuple(obj.scale) == (1.0, 1.0, 1.0)
    values = sizing(2.0, 12.0, 2.2, 0.5, 0.4)
    assert effective_nozzle(0.5, 0.0) == 0.5
    assert effective_nozzle(0.5, 1.0) == 0.4
    assert effective_nozzle(0.5, 2.0) == 0.6
    assert effective_nozzle(0.5, 3.0) == 0.8
    assert math.isclose(values["prop_mm"], 50.8)
    assert math.isclose(values["clearance"], 2.032)
    assert math.isclose(values["outer_diameter"], 60.064)
    assert math.isclose(values["min_feature"], 1.2)
    large_values = sizing(5.0, 12.0, 2.2, 0.5, 0.4)
    assert large_values["primary_width"] >= values["primary_width"] * 1.3
    assert large_values["fork_width"] >= values["fork_width"] * 1.25
    light_values = sizing(4.0, 12.0, 2.2, 0.5, 0.4, light_bumper=1.0)
    solid_values = sizing(4.0, 12.0, 2.2, 0.5, 0.4, light_bumper=0.0)
    assert light_values["profile_bumper"] < solid_values["profile_bumper"]
    assert math.isclose(light_values["outer_diameter"], solid_values["outer_diameter"])
    no_lip = sizing(4.0, 12.0, 2.2, 0.5, 0.4, sacrificial_lip=0.0)
    fat_lip = sizing(4.0, 12.0, 2.2, 0.5, 0.4, sacrificial_lip=1.2)
    assert math.isclose(fat_lip["bumper_center_radius"], no_lip["bumper_center_radius"])
    assert fat_lip["lip_center_radius"] > fat_lip["bumper_center_radius"]
    assert math.isclose(fat_lip["outer_diameter"] - no_lip["outer_diameter"], 2.4)
    assert math.isclose(sizing(5.0, 12.0, 2.2, 0.5, 0.4, size_check=1.0)["prop_mm"], 127.0)
    assert sizing(2.0, 12.0, 2.2, 0.5, 0.4, arc_coverage=180.0)["arc_start"] == 45.0
    assert branch_angles(210.0) == (50.0, 135.0, 220.0)
    assert branch_angles(180.0) == (65.0, 135.0, 205.0)
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
        and item.socket_type in {"NodeSocketFloat", "NodeSocketInt"}
    }
    assert set(inputs) == set(PARAMETERS)
    assert inputs["Motor Mount Pattern"].socket_type == "NodeSocketInt"
    assert inputs["Motor Example Preset"].socket_type == "NodeSocketInt"
    for name, (minimum, maximum, default) in PARAMETERS.items():
        socket = inputs[name]
        assert all(
            math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)
            for actual, expected in zip(
                (socket.min_value, socket.max_value, socket.default_value),
                (minimum, maximum, default),
            )
        ), name
        assert socket.description == PARAMETER_DESCRIPTIONS[name]
    description = bpy.data.objects.get(DESCRIPTION_OBJECT_NAME)
    assert description and description.type == "FONT"
    assert "Sacrificial Lip (mm)" in description.data.body
    assert "Nozzle Preset" in description.data.body
    required = {
        "V3 Motor Plate",
        "V3 Through Cutters",
        "V3 Recess Cutters",
        "V3 Mount",
        "Open Bumper Arc",
        "Rounded Bumper Start Cap",
        "Rounded Bumper End Cap",
        "Solid Sacrificial Lip",
        "Bumper With Sacrificial Lip",
        "Primary Arm",
        "Upper Fork",
        "Lower Fork",
        "Threefold Arm Instances",
    }
    assert required <= {item.name for item in group.nodes}
    trim = group.nodes["Open Bumper Arc"]
    assert trim.inputs["Start"].links
    assert trim.inputs["End"].links
    holes = hole_report(obj)
    assert len(holes) == 4
    for measured_hole, expected in zip(holes, hole_centers()):
        assert math.dist(measured_hole["center"], expected) <= 0.02
        assert abs(measured_hole["through_radius"] - THROUGH_RADIUS) <= 0.03
        assert abs(measured_hole["recess_radius"] - RECESS_RADIUS) <= 0.03
        assert abs(measured_hole["recess_top_z"] - RECESS_TOP_Z) <= 0.02
    for pattern in range(4):
        set_parameter(modifier, "Motor Mount Pattern", pattern)
        bpy.context.view_layer.update()
        pattern_holes = node_hole_report(obj, "V3 Mount", pattern)
        assert len(pattern_holes) == 4, pattern
        for measured_hole, expected in zip(pattern_holes, hole_centers(pattern)):
            assert math.dist(measured_hole["center"], expected) <= 0.08, (pattern, measured_hole)
            assert abs(measured_hole["through_radius"] - THROUGH_RADIUS) <= 0.03, (pattern, measured_hole)
            assert abs(measured_hole["recess_radius"] - RECESS_RADIUS) <= 0.03, (pattern, measured_hole)
            assert abs(measured_hole["recess_top_z"] - RECESS_TOP_Z) <= 0.02, (pattern, measured_hole)
    for example in range(1, 5):
        for name, (_minimum, _maximum, default) in PARAMETERS.items():
            set_parameter(modifier, name, default)
        set_parameter(modifier, "Motor Example Preset", example)
        bpy.context.view_layer.update()
        example_holes = node_hole_report(obj, "V3 Mount", example=example)
        assert len(example_holes) == 4, example
        for measured_hole, expected in zip(example_holes, hole_centers(example=example)):
            assert math.dist(measured_hole["center"], expected) <= 0.08, (example, measured_hole)
            assert abs(measured_hole["through_radius"] - THROUGH_RADIUS) <= 0.03, (example, measured_hole)
            assert abs(measured_hole["recess_radius"] - RECESS_RADIUS) <= 0.03, (example, measured_hole)
            assert abs(measured_hole["recess_top_z"] - RECESS_TOP_Z) <= 0.02, (example, measured_hole)
    for name, (_minimum, _maximum, default) in PARAMETERS.items():
        set_parameter(modifier, name, default)
    bpy.context.view_layer.update()
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
    cap_angle = math.degrees(math.asin(values["profile_bumper"] / 2.0 / values["bumper_center_radius"]))
    assert min(bumper_angles) >= values["arc_start"] - cap_angle - 1.0, min(bumper_angles)
    assert max(bumper_angles) <= values["arc_end"] + cap_angle + 1.0, max(bumper_angles)
    set_parameter(modifier, "Arc Coverage (deg)", 180.0)
    bpy.context.view_layer.update()
    arms_180 = node_mesh_report(obj, "Place Arm Network")
    arm_angles = tuple(
        math.degrees(math.atan2(y, x)) % 360.0
        for x, y, _z in arms_180["coordinates"]
        if math.hypot(x, y) > 14.0
    )
    values_180 = sizing(2.0, 12.0, 2.2, 0.5, 0.4, arc_coverage=180.0)
    assert min(arm_angles) >= values_180["arc_start"] - 3.0, min(arm_angles)
    assert max(arm_angles) <= values_180["arc_end"] + 3.0, max(arm_angles)
    for name, (_minimum, _maximum, default) in PARAMETERS.items():
        set_parameter(modifier, name, default)
    bpy.context.view_layer.update()
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
            for name, (_minimum, _maximum, default) in PARAMETERS.items():
                set_parameter(modifier, name, default)
            for name, value in zip(PARAMETERS, case):
                set_parameter(modifier, name, value)
            bpy.context.view_layer.update()
            expected = sizing(*case)
            case_report = mesh_report(obj)
            assert case_report["components"] <= 2, (
                case,
                case_report["components"],
                case_report["nonmanifold_edges"],
            )
            assert case_report["nonmanifold_edges"] == 0, (
                case,
                case_report["components"],
                case_report["nonmanifold_edges"],
            )
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
