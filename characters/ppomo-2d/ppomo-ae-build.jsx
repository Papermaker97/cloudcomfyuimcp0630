// Ppomo 2D - After Effects build script
// File > Scripts > Run Script File... and pick this file.
// Builds 5 test comps (one per expression), each with the layered Ppomo as shape layers.
// All parts are parented to "body", so moving/scaling body moves the whole character.

(function () {
  var LAYERS = [{"name":"shadow","kind":"ellipse","parent":null,"pivot":[530,566],"c":[530,566],"size":[840,40],"shape":null,"fill":[0,0,0],"fillOp":8,"stroke":false,"strokeW":6},{"name":"foot_back","kind":"ellipse","parent":"body","pivot":[912,540],"c":[912,540],"size":[96,54],"shape":null,"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"paw_back","kind":"ellipse","parent":"body","pivot":[142,546],"c":[142,546],"size":[92,48],"shape":null,"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"ear_L","kind":"path","parent":"body","pivot":[240,360],"shape":{"v":[[172,400],[220,300],[302,362]],"inT":[[0,0],[-30,5],[-22,-32]],"outT":[[-7,-55],[30,2],[0,0]],"closed":true},"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"ear_R","kind":"path","parent":"body","pivot":[455,320],"shape":{"v":[[392,345],[448,264],[518,322]],"inT":[[0,0],[-28,-2],[-13,-27]],"outT":[[0,-55],[30,3],[0,0]],"closed":true},"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"body","kind":"path","parent":null,"pivot":[530,560],"shape":{"v":[[175,560],[105,470],[250,345],[520,315],[720,205],[812,232],[880,212],[962,380],[900,550],[760,561]],"inT":[[0,0],[0,50],[-80,0],[-80,10],[-80,0],[-12,-17],[-30,-2],[0,-80],[50,-10],[40,0]],"outT":[[-45,0],[0,-70],[80,0],[80,-10],[60,0],[18,-20],[60,4],[0,90],[-30,8],[0,0]],"closed":true},"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"belly","kind":"path","parent":"body","pivot":[520,540],"shape":{"v":[[162,540],[420,503],[882,520],[760,556],[182,556],[162,540]],"inT":[[0,0],[-90,-15],[-162,-52],[60,0],[178,1],[3,8]],"outT":[[68,-42],[140,-25],[-20,28],[-200,1],[-10,-3],[0,0]],"closed":true},"fill":[1,0.949,0.8471],"fillOp":100,"stroke":false,"strokeW":6},{"name":"butt_line","kind":"path","parent":"body","pivot":[818,274],"shape":{"v":[[812,236],[818,312]],"inT":[[0,0],[6,-27]],"outT":[[10,22],[0,0]],"closed":false},"fill":null,"fillOp":100,"stroke":true,"strokeW":6},{"name":"blush_L","kind":"ellipse","parent":"body","pivot":[190,502],"c":[190,502],"size":[78,46],"shape":null,"fill":[0.949,0.6275,0.651],"fillOp":45,"stroke":false,"strokeW":6},{"name":"blush_R","kind":"ellipse","parent":"body","pivot":[420,502],"c":[420,502],"size":[78,46],"shape":null,"fill":[0.949,0.6275,0.651],"fillOp":45,"stroke":false,"strokeW":6},{"name":"paw_front","kind":"ellipse","parent":"body","pivot":[482,548],"c":[482,548],"size":[112,54],"shape":null,"fill":[0.9686,0.7647,0.7765],"fillOp":100,"stroke":true,"strokeW":6},{"name":"eye_L","kind":"ellipse","parent":"body","pivot":[226,470],"c":[226,470],"size":[28,28],"shape":null,"fill":[0.4314,0.2314,0.1373],"fillOp":100,"stroke":false,"strokeW":6},{"name":"eye_R","kind":"ellipse","parent":"body","pivot":[388,470],"c":[388,470],"size":[28,28],"shape":null,"fill":[0.4314,0.2314,0.1373],"fillOp":100,"stroke":false,"strokeW":6},{"name":"mouth","kind":"path","parent":"body","pivot":[306,482],"shape":{"v":[[290,478],[306,478],[322,478]],"inT":[[0,0],[-4,12],[-4,12]],"outT":[[4,12],[4,12],[0,0]],"closed":false},"fill":null,"fillOp":100,"stroke":true,"strokeW":5}];
  var LINE = [0.5412,0.2941,0.1882];
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
