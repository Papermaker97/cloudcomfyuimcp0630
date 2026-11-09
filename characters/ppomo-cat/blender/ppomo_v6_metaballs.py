"""
Ppomo v6 as Blender metaballs.

How to use (Blender 4.x / 5.x):
  1. Open Blender -> Scripting tab -> Open -> this file -> Run Script.
     (Or just open ppomo_v6_metaballs.blend, which is this script's result.)
  2. Every part has a named HANDLE (a sphere-shaped empty): head, torso, rump, belly, cheek_L, ear_L, ...
     Move / scale / rotate a handle and its ball goes with it. The balls themselves are named
     Ppomo.001, Ppomo.002, ... (Blender only melts metaballs together when their names end in a number)
     and are locked, so clicking the body picks a handle instead of a loose ball.
  3. Mirror: only move the *_L handles (and the centre ones). Each *_R handle follows its *_L partner
     through drivers (x is flipped). The *_R handles are locked so you don't grab them by mistake.
  4. Eyes and mouth are parented to the head handle, so they follow it.
  5. When the shape is right: select the body ("Ppomo") -> Object -> Convert -> Mesh to get a normal mesh
     (for sculpting, export, 3D printing, three.js...). Unlock it first: Outliner -> enable the arrow (selectable).

Shape numbers come from the web model (ppomo-v6.html). Units: about 1 = head height.
Blender axes: X = Ppomo's left/right, -Y = where the face points (front view looks at the face), Z = up.

Made for the Ppomo project with help from Claude.
"""
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FAMILY = "Ppomo"           # metaball objects named "Ppomo", "Ppomo.001", "Ppomo.002", ... melt together
THRESHOLD = 0.6            # Blender default
STIFFNESS = 2.0            # Blender default
# with stiffness 2 and threshold 0.6, a ball shows up at 0.575 x its radius. Dividing by this keeps
# the sizes below equal to the *visible* size in the web model.
VISIBLE = math.sqrt(1 - (THRESHOLD / STIFFNESS) ** (1 / 3))

# web model (x, y-up, z-forward) -> Blender (x, -z, y)
def B(x, y, z):
    return Vector((x, -z, y))

# name, centre (web coords), visible radii (x, y-up, z-forward), tilt about the face axis, mirrored?
PARTS = [
    ("head",  (0.00, 0.40,  0.52), (0.65, 0.40, 0.46), 0.0,  False),
    ("torso", (0.00, 0.48, -0.25), (0.72, 0.48, 0.66), 0.0,  False),
    ("rump",  (0.00, 0.55, -0.45), (0.43, 0.43, 0.43), 0.0,  False),
    ("belly", (0.00, 0.18, -0.10), (0.66, 0.20, 0.85), 0.0,  False),
    ("cheek", (0.36, 0.30,  0.78), (0.21, 0.21, 0.21), 0.0,  True),
    ("ear",   (0.31, 0.81,  0.52), (0.15, 0.16, 0.08), 0.28, True),
    ("paw",   (0.50, 0.09,  0.70), (0.11, 0.11, 0.11), 0.0,  True),
    ("foot",  (0.52, 0.09, -0.86), (0.11, 0.11, 0.11), 0.0,  True),
    ("butt",  (0.27, 0.42, -0.76), (0.36, 0.36, 0.36), 0.0,  True),
]
# metaballs add their fields together where they overlap, so overlapping parts swell a little.
# SHRINK pulls every part in a bit so the total matches the web model (found by testing).
SHRINK = 0.90

PINK = (0.89, 0.55, 0.62, 1.0)     # linear-ish values for #F2B6C2
INK = (0.06, 0.03, 0.02, 1.0)


def clear_old():
    col = bpy.data.collections.get("Ppomo")
    if col:
        for ob in list(col.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(col)
    for mb in [m for m in bpy.data.metaballs if m.users == 0]:
        bpy.data.metaballs.remove(mb)


def make_material(name, color, roughness, subsurface=0.0, sheen=0.0, coat=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    mat.diffuse_color = color
    if bsdf:
        for key, val in (("Base Color", color), ("Roughness", roughness), ("Subsurface Weight", subsurface),
                         ("Sheen Weight", sheen), ("Coat Weight", coat)):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = val
    return mat


def ball_object(col, name, material=None):
    """one metaball object with one ball element at its own origin."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.03            # viewport detail (smaller = smoother, slower)
    mb.render_resolution = 0.015
    mb.threshold = THRESHOLD
    el = mb.elements.new()
    el.type = 'BALL'
    el.radius = 1.0 / VISIBLE
    el.stiffness = STIFFNESS
    if material:
        mb.materials.append(material)
    ob = bpy.data.objects.new(name, mb)
    col.objects.link(ob)
    return ob


_count = [0]
def part(col, handle_name, center, radii, tilt):
    """a named handle (empty) with a numbered metaball ball riding on it."""
    h = bpy.data.objects.new(handle_name, None)
    col.objects.link(h)
    h.empty_display_type = 'SPHERE'
    h.empty_display_size = 1.0
    h.location = B(*center)
    rx, ry, rz = radii
    h.scale = (rx * SHRINK, rz * SHRINK, ry * SHRINK)   # web (x, y-up, z-fwd) -> Blender (x, depth, up)
    h.rotation_euler = (0.0, tilt, 0.0)                  # tilt outward, about the front-back axis
    _count[0] += 1
    ball = ball_object(col, f"{FAMILY}.{_count[0]:03d}")
    ball.parent = h                                      # sits exactly on the handle
    ball.hide_select = True
    return h


def add_mirror_drivers(src, dst):
    """dst copies src mirrored across X: x flips; y, z copy; rotation about Y and Z flips; scale copies."""
    def drive(prop, index, path, expr):
        fc = dst.driver_add(prop, index)
        drv = fc.driver
        drv.type = 'SCRIPTED'
        var = drv.variables.new()
        var.name = "v"
        var.type = 'SINGLE_PROP'
        var.targets[0].id = src
        var.targets[0].data_path = path
        drv.expression = expr      # "v" / "-v" are simple expressions: they work without enabling scripts
    for i in range(3):
        drive("location", i, f"location[{i}]", "-v" if i == 0 else "v")
        drive("rotation_euler", i, f"rotation_euler[{i}]", "v" if i == 0 else "-v")
        drive("scale", i, f"scale[{i}]", "v")
    dst.hide_select = True


def front_point(bvh, x, z):
    """first surface hit when looking from the front (from -Y toward +Y) at height z."""
    hit = bvh.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)))
    return hit[0], hit[1]


def build():
    clear_old()
    scene = bpy.context.scene
    col = bpy.data.collections.new("Ppomo")
    scene.collection.children.link(col)
    skin = make_material("Ppomo Silicone", PINK, 0.55, subsurface=0.15, sheen=0.3, coat=0.15)
    ink = make_material("Ppomo Ink", INK, 0.3, coat=0.6)

    # the basis object (exactly "Ppomo") sets resolution / threshold / material for the whole family.
    # Its own ball is a small one inside the head; it must not be tiny, or Blender meshes almost nothing.
    basis = ball_object(col, FAMILY, skin)
    basis.location = B(0, 0.40, 0.52)
    basis.data.elements[0].radius = 0.3
    basis.hide_select = True

    objs = {}
    for name, c, r, tilt, mirrored in PARTS:
        if mirrored:
            left = part(col, f"{name}_L", c, r, -tilt)
            right = part(col, f"{name}_R", (-c[0], c[1], c[2]), r, tilt)
            add_mirror_drivers(left, right)
            objs[name + "_L"], objs[name + "_R"] = left, right
        else:
            objs[name] = part(col, name, c, r, tilt)

    # face: find the front surface of the evaluated body, place eyes and mouth there, parent to the head
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = basis.evaluated_get(dg)
    tmp = ev.to_mesh()                      # metaballs can't be ray-cast directly: use a temporary mesh
    mw = basis.matrix_world                 # the mesh comes out in the basis object's local space
    bvh = BVHTree.FromPolygons([mw @ v.co for v in tmp.vertices], [tuple(p.vertices) for p in tmp.polygons])
    ev.to_mesh_clear()
    head = objs["head"]

    def parent_to_head(ob):
        ob.parent = head
        ob.matrix_parent_inverse = head.matrix_world.inverted()

    for side, label in ((1, "L"), (-1, "R")):
        loc, nrm = front_point(bvh, 0.24 * side, 0.42)
        me = bpy.data.meshes.new(f"eye_{label}")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.04)
        bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(ink)
        eye = bpy.data.objects.new(f"Ppomo eye_{label}", me)
        col.objects.link(eye)
        eye.scale = (1.0, 0.45, 1.1)
        eye.location = loc + Vector((0, 0.01, 0))
        parent_to_head(eye)

    loc, _ = front_point(bvh, 0.0, 0.39)
    cu = bpy.data.curves.new("mouth", 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.006
    cu.bevel_resolution = 3
    for side in (1, -1):                      # two little arcs = a tiny "ω"
        sp = cu.splines.new('POLY')
        pts = [(side * 0.024 + 0.024 * math.cos(a), 0.0, -0.024 * math.sin(a))
               for a in [math.pi * i / 10 for i in range(11)]]
        sp.points.add(len(pts) - 1)
        for p, (x, y, z) in zip(sp.points, pts):
            p.co = (x, y, z, 1.0)
    cu.materials.append(ink)
    mouth = bpy.data.objects.new("Ppomo mouth", cu)
    col.objects.link(mouth)
    mouth.location = loc + Vector((0, -0.004, 0.024))
    parent_to_head(mouth)

    # floor, light and camera so F12 gives a quick look
    if not bpy.data.objects.get("Floor"):
        me = bpy.data.meshes.new("Floor")
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4); bm.to_mesh(me); bm.free()
        floor = bpy.data.objects.new("Floor", me)
        scene.collection.objects.link(floor)
        floor.data.materials.append(make_material("Floor", (0.93, 0.89, 0.86, 1.0), 0.9))
    if not bpy.data.objects.get("Key Light"):
        light = bpy.data.lights.new("Key Light", 'AREA')
        light.energy = 600; light.size = 3
        lo = bpy.data.objects.new("Key Light", light)
        scene.collection.objects.link(lo)
        lo.location = (-2.5, -3.0, 4.0)
        lo.rotation_euler = (math.radians(45), 0, math.radians(-40))
    if not bpy.data.objects.get("Camera"):
        cam = bpy.data.cameras.new("Camera"); cam.lens = 70
        co = bpy.data.objects.new("Camera", cam)
        scene.collection.objects.link(co)
        co.location = (4.2, -5.2, 2.6)
        direction = Vector((0, 0.1, 0.45)) - co.location
        co.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        scene.camera = co
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.95, 0.92, 0.9)
    world.use_nodes = True                   # soft warm background light for renders
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.95, 0.92, 0.9, 1.0)
        bg.inputs["Strength"].default_value = 0.8
    return objs


build()
print("Ppomo built: move the named handles (head, torso, ear_L, ...); *_R handles follow their *_L partner.")
