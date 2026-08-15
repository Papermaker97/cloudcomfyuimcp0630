#!/usr/bin/env python3
"""Migrate and keep both comparison workflows in sync.

Targets a 2-way head-to-head — Seedance 2.5 (API) vs MiniMax H3 (open
weights) — driven by 6 reference images at 12 seconds.

Applied to every workflow in TARGETS, idempotently:

  * 6 LoadImage nodes wired, in story order, to both generators and to the
    rewriters (OpenRouter images / captioned VLM batch);
  * the FLUX 3 band removed and the MiniMax H3 band pulled up into the gap;
  * durations pinned to 12s (H3: 294 frames = 17*17+5 at 24fps) and H3's
    resolution raised to 0.9 MP / 1280x736 to match Seedance's 720p;
  * workflows/rough_prompt.txt and workflows/system_prompts/*.md re-inlined.

Links are re-indexed by socket NAME after the graph is mutated, so inserting
sockets can never silently repoint an existing link.

Run:  python3 tools/build_workflows.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WF = ROOT / "workflows"
SP = WF / "system_prompts"

TARGETS = [
    WF / "ksampler_3model_compare_v2.json",              # OpenRouter API rewriter
    WF / "ksampler_3model_compare_v3_local_vlm.json",    # local Qwen3-VL rewriter
]

# node ids shared by both files
ROUGH = 10
IMAGES = [20, 21, 22, 23, 24, 25]
SEEDANCE, SEEDANCE_SAVE = 30, 31
H3, RES_SEL, DURATION = 47, 44, 45
SYS_SEEDANCE, PRE_SEEDANCE = 60, 62
SYS_H3, PRE_H3 = 80, 82
FLUX_NODES = {70, 71, 72, 90, 91, 220, 221}      # sys/rewriter/preview/gen/save
H3_BAND = {80, 82, 230, 231} | set(range(40, 58))
CAPTIONS = [200, 201, 202, 203, 206, 207]
BATCH = 204
REWRITERS = {"openrouter": [61, 81], "vlm": [211, 231]}

IMAGE_META = [
    ("ref1_device_hero.png", "Image 1 — device hero"),
    ("ref2_device_exploded.png", "Image 2 — exploded"),
    ("ref3_button_macro.png", "Image 3 — RUN button macro"),
    ("ref4_desk_before.png", "Image 4 — desk / before"),
    ("ref5_magical_girl.png", "Image 5 — magical girl"),
    ("ref6_logo_card.png", "Image 6 — logo card"),
]

DURATION_S = 12
H3_FRAMES = 294          # max(5, 12*24) rounded onto the 17k+5 grid
H3_W, H3_H = 1280, 736
H3_MEGAPIXELS = 0.9

README = """# K-SAMPLER — 2-MODEL COMPARISON RIG

**Seedance 2.5 (API) vs MiniMax H3 (open weights).** Same 6 references, same
12 seconds, same seed.

## How to use

1. Load the 6 images into the LoadImage nodes. **Connection order is the
   reference number** — image 1 is the device hero, image 6 is the logo card.
   Getting this order wrong silently rewrites every role binding.
2. Edit **ROUGH PROMPT**. Prose can be lazy; the reference roles cannot.
   The rewriter can see the pictures but it cannot guess your intent for
   them — which room is the opening location, which background is a VFX
   plate and must be thrown away.
3. Run. Read both **Preview as Text** nodes before spending credits.

## What to check in the previews

- Image 5's background exclusion survived (this one evaporates first).
- Image 4's room is being carried in, not discarded.
- The image-4 / image-5 same-person lock is still there.
- Korean dialogue is still Korean. Translated dialogue breaks lip sync.
- The closing beat is stated.
- MiniMax H3 only: `retention_analysis` marks image 5 `partially_preserved`.
  If it says `fully_preserved`, the sparkle background comes with it.

## Locked comparison conditions

| | Seedance 2.5 | MiniMax H3 |
|---|---|---|
| path | partner API | open weights, local sampling |
| duration | 12s | 294 frames (17x17+5 @ 24fps) |
| resolution | 720p | 1280x736 (0.9 MP) |
| references | 6 | 6 |
| seed | 42 | 42 |

H3's `length` must land on a `17k + 5` grid, so 12s becomes 294 frames —
12.25s, a quarter second longer than Seedance's 12.0. Imperceptible side by
side, but do not cut to a shared beat grid assuming they match.
H3's trained range tops out near 362 frames (15s); Seedance 2.5 would go to
30s. Both are held at 12 for parity and cost.

The two prompts are **deliberately different** — each model gets its own
dialect. That is the second story: same idea, two shooting scripts.
"""

H3_NOTE = """## MiniMax H3 — open weights

Models auto-download from
[Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) on first
run:

```
ComfyUI/models/
  diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
  text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
  vae/minimax_h3_video_vae_fp16.safetensors
  vae/minimax_h3_audio_vae_fp32.safetensors
```

**Reference tags.** In the prompt the images are `<Picture 1>`..`<Picture 6>`
in connection order — the open-weights node's own convention, not the
`Image 1` syntax the MiniMax *API* node uses. The rewriter knows.

**Length.** `length` is frames at 24 fps and must land on the model's
`17k + 5` grid; the Math Expression node handles it. 12 s -> 294 frames,
i.e. 12.25 s of actual output. The trained range tops out near 362 frames
(15 s). Change the Duration node, not the frame count.

**Scheduler.** `beta` (or `normal`) beats `simple` on reference-heavy
prompts.

**ref_image_size.** `match` scales references down to the generation
resolution and is much faster. `max` keeps a 2048px short edge for stronger
identity fidelity, but reference tokens ride through every sampling step.

**This node stack is the story.** One API node on the left, a full loader +
sampler chain on the right — that screenshot is the proof it runs on your
own GPU.
"""


# --------------------------------------------------------------- helpers
class Graph:
    def __init__(self, path):
        self.path = path
        self.w = json.loads(path.read_text(encoding="utf-8"))
        self.by = {n["id"]: n for n in self.w["nodes"]}

    def save(self):
        self.reindex()
        self.w["last_node_id"] = max(n["id"] for n in self.w["nodes"])
        self.w["last_link_id"] = max([l[0] for l in self.w["links"]] or [0])
        self.path.write_text(
            json.dumps(self.w, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")

    def has(self, nid):
        return nid in self.by

    def new_link_id(self):
        return max([l[0] for l in self.w["links"]] or [0]) + 1

    def snapshot_names(self):
        """link id -> (dst node, dst socket name), captured before mutation."""
        names = {}
        for lid, _s, _ss, d, ds, _t in self.w["links"]:
            node = self.by.get(d)
            if node and ds < len(node["inputs"]):
                names[lid] = (d, node["inputs"][ds]["name"])
        self._names = names

    def reindex(self):
        """Recompute every link's dst_slot from socket names, and rebuild the
        output link lists. Safe to call after arbitrary socket insertion."""
        pos = {}
        for n in self.w["nodes"]:
            for i, s in enumerate(n["inputs"]):
                pos[(n["id"], s["name"])] = i
            for o in n["outputs"]:
                o["links"] = []
        kept = []
        for link in self.w["links"]:
            lid, s, ss, d, _ds, t = link
            if s not in self.by or d not in self.by:
                continue
            name = getattr(self, "_names", {}).get(lid)
            sock = name[1] if name and name[0] == d else None
            if sock is None:
                node = self.by[d]
                hit = [x["name"] for x in node["inputs"] if x["link"] == lid]
                if not hit:
                    continue
                sock = hit[0]
            if (d, sock) not in pos:
                continue
            link[4] = pos[(d, sock)]
            kept.append(link)
        self.w["links"] = kept
        for n in self.w["nodes"]:
            for s in n["inputs"]:
                s["link"] = None
        for lid, s, ss, d, ds, _t in kept:
            self.by[d]["inputs"][ds]["link"] = lid
            outs = self.by[s]["outputs"]
            if ss < len(outs):
                outs[ss]["links"].append(lid)
        for n in self.w["nodes"]:
            for o in n["outputs"]:
                if not o["links"] and n["type"] == "SaveVideo":
                    o["links"] = None

    def drop(self, ids):
        ids = {i for i in ids if i in self.by}
        if not ids:
            return
        self.w["nodes"] = [n for n in self.w["nodes"] if n["id"] not in ids]
        self.w["links"] = [l for l in self.w["links"]
                           if l[1] not in ids and l[3] not in ids]
        for i in ids:
            self.by.pop(i)

    def connect(self, src, src_slot, dst, socket, typ):
        node = self.by[dst]
        idx = next(i for i, s in enumerate(node["inputs"]) if s["name"] == socket)
        lid = self.new_link_id()
        self.w["links"].append([lid, src, src_slot, dst, idx, typ])
        node["inputs"][idx]["link"] = lid
        self._names[lid] = (dst, socket)
        return lid

    def ensure_socket(self, nid, name, typ, after, *, label=None, optional=True):
        """Insert an input socket right after `after` if it is missing."""
        node = self.by[nid]
        if any(s["name"] == name for s in node["inputs"]):
            return False
        sock = {"name": name, "type": typ, "link": None}
        if label:
            sock["label"] = label
        if optional:
            sock["shape"] = 7
        idx = next((i for i, s in enumerate(node["inputs"])
                    if s["name"] == after), len(node["inputs"]) - 1)
        node["inputs"].insert(idx + 1, sock)
        return True

    def add_node(self, nid, ntype, pos, size, *, title=None, inputs=None,
                 outputs=None, widgets=None, color=None, bgcolor=None):
        n = {"id": nid, "type": ntype, "pos": list(pos), "size": list(size),
             "flags": {}, "order": 0, "mode": 0, "inputs": inputs or [],
             "outputs": outputs or [],
             "properties": {"Node name for S&R": ntype}}
        if widgets is not None:
            n["widgets_values"] = widgets
        if title:
            n["title"] = title
        if color:
            n["color"], n["bgcolor"] = color, bgcolor
        self.w["nodes"].append(n)
        self.by[nid] = n
        return n


def img_out(g, nid):
    """Slot index of a LoadImage IMAGE output."""
    return next(i for i, o in enumerate(g.by[nid]["outputs"])
                if o["name"] == "IMAGE")


# --------------------------------------------------------------- migration
def migrate(path):
    g = Graph(path)
    g.snapshot_names()
    kind = "vlm" if g.has(211) else "openrouter"

    # ---- 1. remove the FLUX 3 band, pull MiniMax H3 up into the gap ------
    flux_y = g.by[70]["pos"][1] if g.has(70) else None
    if flux_y is not None:
        dy = flux_y - g.by[SYS_H3]["pos"][1]
        for nid in H3_BAND:
            if g.has(nid):
                g.by[nid]["pos"][1] += dy
        for gr in g.w["groups"]:
            if gr["title"].startswith(("MINIMAX H3 -", "MINIMAX H3 E")) or \
                    "ENGINE" in gr["title"]:
                gr["bounding"][1] += dy
        g.w["groups"] = [gr for gr in g.w["groups"]
                         if not gr["title"].startswith("FLUX")]
    g.drop(FLUX_NODES)

    # ---- 2. six reference images ---------------------------------------
    base = g.by[IMAGES[0]]
    step_x = g.by[IMAGES[1]]["pos"][0] - base["pos"][0]
    step_y = g.by[IMAGES[2]]["pos"][1] - base["pos"][1]
    for i, nid in enumerate(IMAGES):
        fn, title = IMAGE_META[i]
        if not g.has(nid):
            g.add_node(nid, "LoadImage",
                       (base["pos"][0] + step_x * (i % 2),
                        base["pos"][1] + step_y * (i // 2)),
                       list(base["size"]),
                       outputs=[{"name": "IMAGE", "type": "IMAGE", "links": []},
                                {"name": "MASK", "type": "MASK", "links": []}],
                       widgets=[fn, "image"])
        g.by[nid]["widgets_values"][0] = fn
        g.by[nid]["title"] = title

    # ---- 3. wire images 5 and 6 into both generators --------------------
    for i, nid in enumerate(IMAGES):
        n = i + 1
        g.ensure_socket(SEEDANCE, f"model.reference_images.image_{n}", "IMAGE",
                        f"model.reference_images.image_{n - 1}"
                        if n > 1 else "model.prompt", label=f"image_{n}")
        g.ensure_socket(H3, f"ref_images.ref_image_{i}", "IMAGE",
                        f"ref_images.ref_image_{i - 1}" if i else "audio_vae",
                        label=f"ref_image_{i}")
    g.ensure_socket(SEEDANCE, "model.reference_images.image_7", "IMAGE",
                    "model.reference_images.image_6", label="image_7")
    g.ensure_socket(H3, "ref_images.ref_image_6", "IMAGE",
                    "ref_images.ref_image_5", label="ref_image_6")

    for i, nid in enumerate(IMAGES):
        slot = img_out(g, nid)
        if g.by[SEEDANCE]["inputs"][
                next(j for j, s in enumerate(g.by[SEEDANCE]["inputs"])
                     if s["name"] == f"model.reference_images.image_{i + 1}")
        ]["link"] is None:
            g.connect(nid, slot, SEEDANCE,
                      f"model.reference_images.image_{i + 1}", "IMAGE")
        if g.by[H3]["inputs"][
                next(j for j, s in enumerate(g.by[H3]["inputs"])
                     if s["name"] == f"ref_images.ref_image_{i}")
        ]["link"] is None:
            g.connect(nid, slot, H3, f"ref_images.ref_image_{i}", "IMAGE")

    # ---- 4. feed the rewriters ------------------------------------------
    if kind == "openrouter":
        for rw in REWRITERS["openrouter"]:
            if not g.has(rw):
                continue
            for n in range(1, 8):
                g.ensure_socket(rw, f"model.images.image_{n}", "IMAGE",
                                f"model.images.image_{n - 1}" if n > 1
                                else "prompt", label=f"image_{n}")
            for i, nid in enumerate(IMAGES):
                sock = f"model.images.image_{i + 1}"
                idx = next(j for j, s in enumerate(g.by[rw]["inputs"])
                           if s["name"] == sock)
                if g.by[rw]["inputs"][idx]["link"] is None:
                    g.connect(nid, img_out(g, nid), rw, sock, "IMAGE")
    else:
        cap_x = min(g.by[i]["pos"][0] for i in IMAGES)
        cap_y = max(g.by[i]["pos"][1] + g.by[i]["size"][1] for i in IMAGES) + 40
        for i, cid in enumerate(CAPTIONS):
            if not g.has(cid):
                g.add_node(cid, "TextOverlay", (cap_x, cap_y + i * 130),
                           (270, 120), title=f"caption REF {i + 1}",
                           inputs=[{"name": "images", "type": "IMAGE",
                                    "link": None}],
                           outputs=[{"name": "IMAGE", "type": "IMAGE",
                                     "links": []}],
                           widgets=[f"REF {i + 1}", 6.0, "#ffffff", "top",
                                    "left", True])
            else:
                g.by[cid]["pos"] = [cap_x, cap_y + i * 130]
            if g.by[cid]["inputs"][0]["link"] is None:
                g.connect(IMAGES[i], img_out(g, IMAGES[i]), cid, "images",
                          "IMAGE")

        g.by[BATCH]["pos"] = [cap_x + 290, cap_y]
        g.by[BATCH]["title"] = "REF 1-6 -> one sequence for the VLM"
        for i in range(7):
            g.ensure_socket(BATCH, f"images.image{i}", "IMAGE",
                            f"images.image{i - 1}" if i else None,
                            label=f"image{i}", optional=i > 0)
        for i, cid in enumerate(CAPTIONS):
            idx = next(j for j, s in enumerate(g.by[BATCH]["inputs"])
                       if s["name"] == f"images.image{i}")
            if g.by[BATCH]["inputs"][idx]["link"] is None:
                g.connect(cid, 0, BATCH, f"images.image{i}", "IMAGE")

    # ---- 5. pin the comparison conditions -------------------------------
    g.by[SEEDANCE]["widgets_values"][4] = DURATION_S
    g.by[SEEDANCE]["title"] = "Seedance 2.5 — Reference to Video"
    g.by[SEEDANCE_SAVE]["widgets_values"][0] = "video/seedance25_"
    g.by[SEEDANCE_SAVE]["title"] = "SAVE — Seedance 2.5"
    g.by[DURATION]["widgets_values"][0] = float(DURATION_S)
    g.by[RES_SEL]["widgets_values"][1] = H3_MEGAPIXELS
    g.by[RES_SEL]["title"] = (
        f"Resolution ({H3_MEGAPIXELS} MP -> {H3_W}x{H3_H}, matches 720p)")
    g.by[H3]["widgets_values"][1:4] = [H3_W, H3_H, H3_FRAMES]

    # ---- 6. re-inline the editable text ---------------------------------
    g.by[ROUGH]["widgets_values"] = [
        (WF / "rough_prompt.txt").read_text(encoding="utf-8")]
    g.by[ROUGH]["title"] = "ROUGH PROMPT — 대충 써도 됨, 역할만 명시"
    g.by[SYS_SEEDANCE]["widgets_values"] = [
        (SP / "seedance25_rewriter.md").read_text(encoding="utf-8")]
    g.by[SYS_SEEDANCE]["title"] = "SYSTEM PROMPT — SEEDANCE 2.5"
    g.by[SYS_H3]["widgets_values"] = [
        (SP / "minimax_h3_rewriter.md").read_text(encoding="utf-8")]
    for nid, t in ((PRE_SEEDANCE, "PROMPT SENT TO SEEDANCE 2.5"),
                   (PRE_H3, "PROMPT SENT TO MINIMAX H3")):
        g.by[nid]["title"] = t
    for gr in g.w["groups"]:
        if gr["title"].startswith("SEEDANCE"):
            gr["title"] = "SEEDANCE 2.5  (Ctrl+B to bypass)"

    # ---- 7. notes, and keep them out of the image column ----------------
    g.by[1]["widgets_values"] = [README]
    if g.has(57):
        g.by[57]["widgets_values"] = [H3_NOTE]
        col = g.by[1]
        bottom = col["pos"][1] + col["size"][1]
        if g.has(205):
            g.by[205]["pos"] = [col["pos"][0], bottom + 60]
            bottom = g.by[205]["pos"][1] + g.by[205]["size"][1]
        g.by[57]["pos"] = [col["pos"][0], bottom + 60]
        g.by[57]["size"] = [560, 620]

    g.save()
    return g


# --------------------------------------------------------------- validation
def validate(path):
    w = json.loads(path.read_text(encoding="utf-8"))
    by = {n["id"]: n for n in w["nodes"]}
    errs = []
    for lid, s, ss, d, ds, _t in w["links"]:
        if s not in by or d not in by:
            errs.append(f"L{lid}: dangling")
            continue
        if ds >= len(by[d]["inputs"]) or by[d]["inputs"][ds]["link"] != lid:
            errs.append(f"L{lid}: dst {d}.{ds} mismatch")
        if ss >= len(by[s]["outputs"]) or lid not in (by[s]["outputs"][ss]["links"] or []):
            errs.append(f"L{lid}: src {s}.{ss} mismatch")
    for n in w["nodes"]:
        for i, s in enumerate(n["inputs"]):
            if s["link"] is None and s.get("shape") != 7 and "widget" not in s:
                errs.append(f"{n['id']} {n['type']}: '{s['name']}' unconnected")
    # the six references must reach both generators in story order
    for gen, tmpl, off in ((SEEDANCE, "model.reference_images.image_%d", 1),
                           (H3, "ref_images.ref_image_%d", 0)):
        for i in range(6):
            sock = tmpl % (i + off)
            hit = [s for s in by[gen]["inputs"] if s["name"] == sock]
            if not hit or hit[0]["link"] is None:
                errs.append(f"{gen}: {sock} not connected")
                continue
            src = [l for l in w["links"] if l[0] == hit[0]["link"]][0][1]
            if src != IMAGES[i]:
                errs.append(f"{gen}: {sock} <- node {src}, expected {IMAGES[i]}")
    return errs


if __name__ == "__main__":
    for p in TARGETS:
        migrate(p)
        errs = validate(p)
        w = json.loads(p.read_text(encoding="utf-8"))
        state = "OK" if not errs else "FAIL\n  " + "\n  ".join(errs)
        print(f"{p.name}: {len(w['nodes'])} nodes / {len(w['links'])} links -> {state}")
