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
PARAMETERS = {
    "Propeller Diameter (in)": (2.0, 5.0, 2.0),
    "Guard Height (mm)": (3.0, 101.6, 12.0),
    "Bumper Thickness (mm)": (1.2, 8.0, 3.2),
    "Strength / Weight": (0.0, 1.0, 0.5),
    "Nozzle Diameter (mm)": (0.4, 0.8, 0.4),
    "Safety Clearance Override (mm)": (0.0, 20.0, 0.0),
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
    assert 3.0 <= height <= 101.6
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
    links.new(separate.outputs["Selection"], group_out.inputs["Geometry"])
    return group


def install_modifier(obj):
    modifier = obj.modifiers.get(MODIFIER_NAME)
    if modifier:
        assert modifier.type == "NODES"
    else:
        modifier = obj.modifiers.new(MODIFIER_NAME, "NODES")
    modifier.node_group = build_node_group()
    v1 = obj.modifiers.get("PG Parametric Guard")
    if v1:
        v1.show_viewport = False
        v1.show_render = False
    return modifier


def install():
    obj = get_guard()
    build_source_attributes(obj)
    return install_modifier(obj)


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
    values = sizing(2.0, 12.0, 3.2, 0.5, 0.4)
    assert math.isclose(values["prop_mm"], 50.8)
    assert math.isclose(values["clearance"], 2.032)
    assert math.isclose(values["outer_diameter"], 61.264)
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


if __name__ == "__main__":
    if "--verify-only" not in sys.argv:
        install()
    if "--self-check" in sys.argv:
        self_check()
