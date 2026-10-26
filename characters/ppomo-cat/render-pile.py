# Renders a pile of Ppomos from one of the 3D pages: python3 render-pile.py <layout.json> out.html, then screenshot out.html.
# The layout file names the source page ("source"), the camera, and each Ppomo's position, tilt and color.
# Optional layout keys: "ortho" (half-height of a straight-on orthographic view instead of the perspective camera),
# "background" (color), "sun" (light position), "shadowBox" (half-size of the shadow area), "noGround",
# "pivot" (model point each Ppomo turns and is placed around), "meshStep" (coarser mesh for big piles),
# "light" ({hemi, sun, env, exposure, shadowRadius}).
import os, re, sys, json
layout = json.load(open(sys.argv[1]))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), layout.get('source', 'ppomo-sit-3d.html'))).read()
pile = """
// ---------- pile render (scratch) ----------
{
  const PILE = %s;
  const OPT = %s;
  const proto = ppomo;
  scene.remove(proto);
  if (OPT.meshStep) { bodyMesh.geometry.dispose(); bodyMesh.geometry = meshField(modelSDF, BOUNDS.min, BOUNDS.max, OPT.meshStep); }
  const pivot = OPT.pivot || [0, 0, 0];
  for (const p of PILE) {
    const c = proto.clone(true);
    c.traverse((o) => { if (o.isMesh && o.material === furMat) { o.geometry = o.geometry.clone(); colorizeGeometry(o.geometry, p.color); o.castShadow = true; o.receiveShadow = true; } });
    c.position.set(-pivot[0], -pivot[1], -pivot[2]);
    const g = new THREE.Group();
    g.add(c);
    g.position.set(p.x, p.y, p.z);
    g.rotation.set(p.rx || 0, p.ry || 0, p.rz || 0, 'ZXY');
    const s = p.s || 1; g.scale.set(s * (p.sx || 1), s * (p.sy || 1), s);
    scene.add(g);
  }
  const box = OPT.shadowBox || 8;
  Object.assign(sun.shadow.camera, { left: -box, right: box, top: box, bottom: -box, near: 0.5, far: 60 });
  sun.position.set(...(OPT.sun || [-4, 12, 7]));
  sun.shadow.camera.updateProjectionMatrix();
  ground.scale.set(4, 4, 1);
  if (OPT.noGround) ground.visible = false;
  if (OPT.background) scene.background = new THREE.Color(OPT.background);
  if (OPT.light) {   // { hemi, sun, env, exposure }: stronger key light and less fill = clearer contact shadows
    scene.traverse((o) => { if (o.isHemisphereLight && OPT.light.hemi != null) o.intensity = OPT.light.hemi; });
    if (OPT.light.sun != null) sun.intensity = OPT.light.sun;
    if (OPT.light.env != null) scene.environmentIntensity = OPT.light.env;
    if (OPT.light.exposure != null) renderer.toneMappingExposure = OPT.light.exposure;
    if (OPT.light.shadowRadius != null) sun.shadow.radius = OPT.light.shadowRadius;
  }
  document.querySelector('header').hidden = true;
  document.querySelector('.controls').hidden = true;
}
""" % (json.dumps(layout['ppomos']), json.dumps({k: layout[k] for k in ('meshStep', 'pivot', 'shadowBox', 'sun', 'noGround', 'background', 'light') if k in layout}))
marker = '// ---------- camera & controls ----------'
out = src.replace(marker, pile + marker)
cam = layout['camera']
out = re.sub(r"const TARGET = new THREE\.Vector3\([^)]*\);", "const TARGET = new THREE.Vector3(%s);" % ', '.join(map(str, cam['target'])), out, count=1)
out = re.sub(r"(const controls = new OrbitControls)", "camera.position.set(%s);\n\\1" % ', '.join(map(str, cam['pos'])), out, count=1)
out = out.replace("controls.minDistance = 4;", "controls.minDistance = 1;").replace("controls.maxDistance = 13;", "controls.maxDistance = 60;")
out = out.replace("controls.autoRotate = !SHEET", "controls.autoRotate = false && !SHEET")
out = out.replace("renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });", "controls.update(); renderer.render(scene, camera);")
out = out.replace("preserveDrawingBuffer: SHEET", "preserveDrawingBuffer: true")
assert "controls.update(); renderer.render(scene, camera);\n" in out
if 'ortho' in cam:
    t = cam['target']
    out = out.replace("controls.update(); renderer.render(scene, camera);\n",
        "{ const H = %s, a = stage.clientWidth / stage.clientHeight, oc = new THREE.OrthographicCamera(-H * a, H * a, H, -H, 0.1, 200);"
        " oc.position.set(%s, %s, %s + 60); oc.lookAt(%s, %s, %s); renderer.render(scene, oc); }\n" % (cam['ortho'], t[0], t[1], t[2], t[0], t[1], t[2]))
open(sys.argv[2], 'w').write(out)
