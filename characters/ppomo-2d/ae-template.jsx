// Ppomo 2D - After Effects build script
// File > Scripts > Run Script File... and pick this file.
// Builds 5 test comps (one per expression), each with the layered Ppomo as shape layers.
// All parts are parented to "body", so moving/scaling body moves the whole character.

(function () {
  var LAYERS = /*__LAYERS__*/;
  var LINE = /*__LINE__*/;
  var W = 1000, H = 700, DUR = 6, FPS = 30;
  var BG = [0.984, 0.953, 0.918];

  var EXPR = {
    wiggle: [
      "// 1. Wiggle - anxious trembling",
      "// wiggle(times per second, amount in px)",
      "wiggle(14, 4);"
    ].join("\n"),

    squash: [
      "// 2. Squash & stretch - squeeze and release, wobbles then settles",
      "var period = 2.0;  // seconds between squeezes",
      "var freq = 2.5;    // wobbles per second",
      "var decay = 4.0;   // how fast it settles",
      "var amp = 20;      // strength in %",
      "var t = time % period;",
      "var s = amp * Math.sin(t * freq * Math.PI * 2) / Math.exp(t * decay);",
      "[value[0] + s, value[1] - s];"
    ].join("\n"),

    heart: [
      "// 3. Heartbeat - needs 2 Scale keyframes (100% -> 106%), then ping-pongs them",
      "loopOut(\"pingpong\");"
    ].join("\n"),

    bounce: [
      "// 4. Bounce - drops, then bounces smaller and smaller",
      "var period = 3.0;  // loop length (s)",
      "var h = 160;       // drop height (px)",
      "var g = 3200;      // gravity (px/s^2)",
      "var e = 0.5;       // bounciness 0..1",
      "var t = time % period;",
      "var v = Math.sqrt(2 * g * h);",
      "var tFall = v / g;",
      "var y = 0;",
      "if (t < tFall) {",
      "  y = -h + 0.5 * g * t * t;",
      "} else {",
      "  t -= tFall;",
      "  v *= e;",
      "  while (v > 40) {",
      "    var tb = 2 * v / g;",
      "    if (t < tb) { y = -(v * t - 0.5 * g * t * t); break; }",
      "    t -= tb;",
      "    v *= e;",
      "  }",
      "}",
      "[value[0], value[1] + y];"
    ].join("\n"),

    blink: [
      "// 5. Blink - closes the dot eye every few seconds",
      "var interval = 3.0;  // seconds between blinks",
      "var dur = 0.16;      // blink length (s)",
      "var t = time % interval;",
      "var k = (t < dur) ? Math.abs(Math.cos(t / dur * Math.PI)) : 1;",
      "[value[0], value[1] * k];"
    ].join("\n")
  };

  function vecsOf(layer) {
    // re-fetch every time: adding properties can invalidate older references
    return layer.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group");
  }

  function buildPpomo(comp) {
    var map = {};
    for (var i = 0; i < LAYERS.length; i++) {
      var L = LAYERS[i];
      var lay = comp.layers.addShape();          // new layers go on top, so LAYERS is bottom -> top
      lay.name = L.name;
      var grp = lay.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
      grp.name = L.name;

      if (L.kind === "ellipse") {
        var el = vecsOf(lay).addProperty("ADBE Vector Shape - Ellipse");
        el.property("ADBE Vector Ellipse Size").setValue(L.size);
        el.property("ADBE Vector Ellipse Position").setValue(L.c);
      } else {
        var pg = vecsOf(lay).addProperty("ADBE Vector Shape - Group");
        var s = new Shape();
        s.vertices = L.shape.v;
        s.inTangents = L.shape.inT;
        s.outTangents = L.shape.outT;
        s.closed = L.shape.closed;
        pg.property("ADBE Vector Shape").setValue(s);
      }
      if (L.stroke) {                               // added before fill -> drawn on top of fill
        var st = vecsOf(lay).addProperty("ADBE Vector Graphic - Stroke");
        st.property("ADBE Vector Stroke Color").setValue(LINE);
        st.property("ADBE Vector Stroke Width").setValue(L.strokeW);
        st.property("ADBE Vector Stroke Line Cap").setValue(2);   // round
        st.property("ADBE Vector Stroke Line Join").setValue(2);  // round
      }
      if (L.fill) {
        var f = vecsOf(lay).addProperty("ADBE Vector Graphic - Fill");
        f.property("ADBE Vector Fill Color").setValue(L.fill);
        f.property("ADBE Vector Fill Opacity").setValue(L.fillOp);
      }
      // path coordinates are in comp pixels: anchor == position keeps them in place
      var tr = lay.property("ADBE Transform Group");
      tr.property("ADBE Anchor Point").setValue(L.pivot);
      tr.property("ADBE Position").setValue(L.pivot);
      map[L.name] = lay;
    }
    for (var j = 0; j < LAYERS.length; j++) {
      if (LAYERS[j].parent) map[LAYERS[j].name].parent = map[LAYERS[j].parent];
    }
    return map;
  }

  function newComp(name, folder) {
    var comp = app.project.items.addComp(name, W, H, 1, DUR, FPS);
    comp.bgColor = BG;
    comp.parentFolder = folder;
    return comp;
  }

  function prop(layer, matchName) { return layer.property("ADBE Transform Group").property(matchName); }

  app.beginUndoGroup("Build Ppomo 2D tests");
  try {
    var folder = app.project.items.addFolder("Ppomo 2D Tests");
    var m;

    m = buildPpomo(newComp("01_Wiggle", folder));
    prop(m.body, "ADBE Position").expression = EXPR.wiggle;

    m = buildPpomo(newComp("02_SquashStretch", folder));
    prop(m.body, "ADBE Scale").expression = EXPR.squash;

    m = buildPpomo(newComp("03_Heartbeat_loopOut", folder));
    var sc = prop(m.body, "ADBE Scale");
    sc.setValueAtTime(0, [100, 100]);
    sc.setValueAtTime(0.28, [106, 106]);
    try {                                            // easy ease on both keys (optional)
      var ez = new KeyframeEase(0, 75), arr = [];
      for (var d = 0; d < sc.value.length; d++) arr.push(ez);
      sc.setTemporalEaseAtKey(1, arr, arr);
      sc.setTemporalEaseAtKey(2, arr, arr);
    } catch (easeErr) {}
    sc.expression = EXPR.heart;

    m = buildPpomo(newComp("04_Bounce", folder));
    prop(m.body, "ADBE Position").expression = EXPR.bounce;

    m = buildPpomo(newComp("05_Blink", folder));
    prop(m.eye_L, "ADBE Scale").expression = EXPR.blink;
    prop(m.eye_R, "ADBE Scale").expression = EXPR.blink;

    alert("Ppomo 2D: 5 test comps created in the 'Ppomo 2D Tests' folder.");
  } catch (err) {
    alert("Ppomo 2D build failed: " + err.toString() + (err.line ? " (line " + err.line + ")" : ""));
  }
  app.endUndoGroup();
})();
