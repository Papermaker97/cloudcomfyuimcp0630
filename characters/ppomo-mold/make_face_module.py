"""
Ppomo face module, WIRED version for the first cast (Tuesday demo).

The first silicone body was cast with the first core (124 mm), so its face opening is a 40 x 22 mm rounded
tunnel about 15 mm long that opens into the head pocket. This module is a plug for that tunnel:
  * FRONT SHELL: Ppomo's face (eyes, nose, mouth stand out 0.9 mm) on a rounded box that fills the tunnel.
    It is 0.5 mm bigger than the tunnel on every side, so the soft silicone hugs it and seals the body.
    Walls 2.2 mm (front 2.4 mm). A 4.4 mm hole under the mouth lets the 4 sensor wires out (seal with hot glue).
  * BACK CAP: closes the shell from behind. The MPRLS sensor sits against it; the sensor's metal port goes
    through the cap's hole into the air inside the body. Press in, then seal the edge with hot glue.
Inside the body all the hollow space is one air chamber (head pocket, neck, torso pocket), so the port only has
to reach that air. The wires go to the Nano 33 IoT on the breadboard, exactly as before (VIN, GND, SCL, SDA).

  python make_face_module.py  ->  face-module/face-front.stl, face-module/face-cap.stl
Print: face-front standing on its open back (face up); face-cap flat. PLA or PETG, 0.2 mm, no supports.
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
from manifold3d import Manifold
import trimesh
from scipy import ndimage

import make_hollow_mold as hm
import make_mold_v1 as v1
from make_hollow_mold import mm, mv, sk, prism_y

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "face-module")
SEAL = 0.5                 # module is this much bigger than the silicone tunnel on each side
WALL, FRONT = 2.2, 2.4     # side walls, front wall behind the face
Y_BACK = -30.0             # back end of the shell (the face surface is at about y = -54)
CAP_T, LIP_T, CAP_GAP = 1.6, 1.2, 0.2
WIRE_Z, WIRE_R = 9.5, 2.2  # wire hole under the mouth
PORT_Z, PORT_R = sk.WIN_Z, 1.45
SENSOR = (17.8, 16.7)      # MPRLS breakout, x by z

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    body = mm.to_manifold(trimesh.load(mm.BODY_STL))
    A, B = sk.WIN_A + SEAL, sk.WIN_B + SEAL
    outer = prism_y(A, B, -75.0, Y_BACK) ^ body
    inner = prism_y(A - WALL, B - WALL, -75.0, Y_BACK + 5.0) ^ body.translate([0, FRONT, 0])
    shell = outer - inner

    # raised face (eyes, nose, mouth) from the same face data as the earlier models
    sp = hm.skull_plug()
    g = sp["g"]
    bumps = mm.to_manifold(mv.mc(ndimage.gaussian_filter(sp["face"].astype(np.float32), 0.5), sk.h, g["lo"], level=0.4))
    shell = shell + bumps

    wire = Manifold.cylinder(30.0, WIRE_R, WIRE_R, 32).rotate([-90, 0, 0]).translate([0, -70.0, WIRE_Z])
    shell = shell - wire

    # back cap: a plate that fits inside the shell's back opening, with a lip that stops on the shell's end
    plate = prism_y(A - WALL - CAP_GAP, B - WALL - CAP_GAP, Y_BACK - CAP_T, Y_BACK)
    lip = prism_y(A, B, Y_BACK, Y_BACK + LIP_T)
    port = Manifold.cylinder(20.0, PORT_R, PORT_R, 32).rotate([-90, 0, 0]).translate([0, Y_BACK - 10.0, PORT_Z])
    cap = plate + lip - port

    # checks
    zi = B - WALL
    xs = SENSOR[0] / 2 / (A - WALL)
    room_z = 2 * zi * (1 - xs ** sk.WIN_E) ** (1 / sk.WIN_E)
    front_in = -54.1 + FRONT
    print(f"module outside {2 * A:.1f} x {2 * B:.1f} mm (tunnel 40 x 22 mm, {SEAL} mm squeeze each side)")
    print(f"inside {2 * (A - WALL):.1f} x {2 * zi:.1f} mm; the sensor ({SENSOR[0]} x {SENSOR[1]} mm) has {room_z:.1f} mm of height at its corners")
    print(f"room for sensor + wires from the front wall (y={front_in:.1f}) to the cap (y={Y_BACK - CAP_T:.1f}): {Y_BACK - CAP_T - front_in:.1f} mm (sensor needs 3.8)")
    print(f"sensor port (3.7 mm) pokes {3.7 - CAP_T - LIP_T:.1f} mm past the cap into the body's air")
    print("shell one piece:", len(shell.decompose()) == 1, "| cap one piece:", len(cap.decompose()) == 1,
          "| cap fits in shell (overlap mm3):", round((cap ^ shell).volume(), 2))

    # print orientation
    ts = mm.to_trimesh(shell)
    ts.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))   # face up, open back on the bed
    ts.apply_translation(-ts.bounds[0])
    tc = mm.to_trimesh(cap)
    tc.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))    # lip down, flat
    tc.apply_translation(-tc.bounds[0])
    for name, t in (("face-front.stl", ts), ("face-cap.stl", tc)):
        t = v1.save_clean(t, os.path.join(OUT, name))
        print(f"{name}: watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}, {np.round(t.extents, 1)} mm, {t.volume / 1000:.1f} cm3")
    # assembled, for a picture
    trimesh.util.concatenate([mm.to_trimesh(shell), mm.to_trimesh(cap)]).export(os.path.join(OUT, "face-assembled.stl"))
