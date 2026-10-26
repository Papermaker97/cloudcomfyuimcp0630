# Renders a pile of sitting Ppomos from ppomo-sit-3d.html: python3 render-pile.py render-pile.json out.html, then screenshot out.html.
# Layout (positions, tilts, colors) and camera live in render-pile.json.
import os, sys, json
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ppomo-sit-3d.html')).read()
layout = json.load(open(sys.argv[1]))
pile = """
// ---------- pile render (scratch) ----------
{
  const PILE = %s;
  const proto = ppomo;
  scene.remove(proto);
  for (const p of PILE) {
    const c = proto.clone(true);
    c.traverse((o) => { if (o.isMesh && o.material === furMat) { o.geometry = o.geometry.clone(); colorizeGeometry(o.geometry, p.color); o.castShadow = true; o.receiveShadow = true; } });
    c.position.set(p.x, p.y, p.z);
    c.rotation.set(p.rx || 0, p.ry || 0, p.rz || 0);
    const s = p.s || 1; c.scale.set(s * (p.sx || 1), s * (p.sy || 1), s);
    scene.add(c);
  }
  Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 0.5, far: 30 });
  sun.position.set(-4, 12, 7);
  sun.shadow.camera.updateProjectionMatrix();
  ground.scale.set(4, 4, 1);
  document.querySelector('header').hidden = true;
  document.querySelector('.controls').hidden = true;
}
""" % json.dumps(layout['ppomos'])
marker = '// ---------- camera & controls ----------'
out = src.replace(marker, pile + marker)
cam = layout['camera']
out = out.replace("const TARGET = new THREE.Vector3(0, 0.98, 0);", "const TARGET = new THREE.Vector3(%s);" % ', '.join(map(str, cam['target'])))
out = out.replace("camera.position.set(4.4, 2.6, 5.2);       // 3/4 front view", "camera.position.set(%s);" % ', '.join(map(str, cam['pos'])))
out = out.replace("controls.minDistance = 4;", "controls.minDistance = 1;").replace("controls.maxDistance = 13;", "controls.maxDistance = 60;")
out = out.replace("controls.autoRotate = !SHEET", "controls.autoRotate = false && !SHEET")
out = out.replace("renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });", "controls.update(); renderer.render(scene, camera);")
out = out.replace("preserveDrawingBuffer: SHEET", "preserveDrawingBuffer: true")
assert "controls.update(); renderer.render(scene, camera);\n" in out
open(sys.argv[2], 'w').write(out)
