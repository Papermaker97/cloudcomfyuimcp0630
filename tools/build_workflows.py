#!/usr/bin/env python3
"""Keep the two comparison workflows in sync with workflows/system_prompts/*.md.

workflows/ksampler_3model_compare_v2.json is the hand-edited base (it carries
whatever the ComfyUI frontend last serialized, including Seedance 2.5). This
script:

  1. re-inlines the three system-prompt markdown files into that base and
     pins the shared duration settings, editing it in place;
  2. derives workflows/ksampler_3model_compare_v3_local_vlm.json from it by
     swapping the three OpenRouter API rewriters for local Qwen3-VL.

Both steps are idempotent. Run:  python3 tools/build_workflows.py
"""

import copy
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SP = ROOT / "workflows" / "system_prompts"
BASE = ROOT / "workflows" / "ksampler_3model_compare_v2.json"
LOCAL = ROOT / "workflows" / "ksampler_3model_compare_v3_local_vlm.json"

# band label -> (system-prompt node, rewriter node, preview node,
#                video node, video node's prompt input name)
BANDS = {
    "SEEDANCE": (60, 61, 62, 30, "model.prompt", "seedance20_rewriter.md"),
    "FLUX 3": (70, 71, 72, 90, "prompt", "flux3_rewriter.md"),
    "MINIMAX H3": (80, 81, 82, 47, "prompt", "minimax_h3_rewriter.md"),
}
IMAGE_NODES = [20, 21, 22, 23]

# Local rewriter settings. keep_model_loaded is False on purpose: the pack
# holds the weights per node instance, so three nodes with it on would mean
# three copies of the model resident at once.
VLM_MODEL = "Qwen3-VL-8B-Instruct"
VLM_MAX_TOKENS = 4096
VLM_TEMPERATURE = 0.3
# 1.2 (the node default) actively fights the H3 brief, which is supposed to
# repeat its labels and field names.
VLM_REPETITION_PENALTY = 1.05

DELIMITER = (
    "\n\n---\n\n"
    "# THE USER'S ROUGH REQUEST\n\n"
    "Rewrite what follows into the format specified above. "
    "Output only the finished prompt.\n\n"
)

LOCAL_NOTE = """## Local rewriter — Qwen3-VL

The three `QwenVL (Advanced)` nodes replace the OpenRouter API rewriters.
Nothing in this column calls an external API.

**Why the batch goes into `video`, not `image`.** The pack's `image` input runs
`tensor_to_pil`, which takes `tensor[0]` — feed it a 4-image batch and three
images are silently dropped. The `video` input iterates the batch, so all four
frames reach the model. `frame_count` only subsamples when the batch is larger
than it, so 16 leaves 4 frames untouched.

**Why the captions.** Qwen sees the four references as video frames, so it needs
something to bind "the second one" to. `Draw Text Overlay` burns `REF 1`..`REF 4`
into the copies the VLM sees; the video models still receive the untouched
originals. All three system prompts are told the caption is a pipeline label to
ignore. Ctrl+B the CAPTION + BATCH group to switch it off — a bypassed
TextOverlay passes the image straight through.

**Why the prompts are concatenated.** This node has no system-prompt field; its
conversation is a single user turn. `Concatenate Text` joins the system prompt
and your rough idea into `custom_prompt`, which overrides `preset_prompt`
whenever it is non-empty.

**keep_model_loaded is off.** The pack stores weights on the node instance, so
leaving it on keeps three copies of the model resident. Off means three
load/unload cycles per run — slower, but it fits.

**Model choice.** `Qwen3-VL-8B-Instruct` is ~12 GB in FP16 (only FP16 is
offered; bitsandbytes quantization is not available here). The MiniMax H3
six-section brief is the hardest format of the three and 8B drops sections
under pressure — move all three nodes to `Qwen3-VL-32B-Instruct` if you see
that, or down to `Qwen3-VL-4B-Instruct` if you are short on VRAM. Weights
download to `models/LLM/Qwen-VL` on first run.

**Batch sizing.** `Batch Images` resizes every image to the first one's
dimensions with a center crop. That only affects what the VLM looks at — the
video models get the originals at their native size.
"""


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p, w):
    p.write_text(json.dumps(w, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def index(w):
    return {n["id"]: n for n in w["nodes"]}


def out_slot(node, name):
    for i, o in enumerate(node["outputs"]):
        if o["name"] == name:
            return i
    raise KeyError(f"node {node['id']} has no output {name}")


# ---------------------------------------------------------------- step 1
def refresh_base():
    w = load(BASE)
    by = index(w)

    for label, (sid, _lid, _pid, _vid, _pin, md) in BANDS.items():
        by[sid]["widgets_values"] = [(SP / md).read_text(encoding="utf-8")]

    # The frontend resets duration to the node default when the model widget
    # changes, so pin the three durations back to the 10s comparison.
    by[30]["widgets_values"][4] = 10          # Seedance model.duration
    by[90]["widgets_values"][4] = "10"        # FLUX 3 duration (a COMBO)
    by[45]["widgets_values"][0] = 10.0        # H3 duration in seconds

    dump(BASE, w)
    return w


# ---------------------------------------------------------------- step 2
def make_local(base):
    w = copy.deepcopy(base)
    by = index(w)
    links = w["links"]
    next_link = [w["last_link_id"]]

    def link(src, sslot, dst, dslot, typ):
        next_link[0] += 1
        links.append([next_link[0], src, sslot, dst, dslot, typ])
        return next_link[0]

    def add(nid, ntype, pos, size, *, title=None, inputs=None, outputs=None,
            widgets=None, color=None, bgcolor=None):
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
        w["nodes"].append(n)
        by[nid] = n
        return n

    def sock(name, typ, *, label=None, optional=False, widget=False):
        d = {"name": name, "type": typ, "link": None}
        if label:
            d["label"] = label
        if optional:
            d["shape"] = 7
        if widget:
            d["widget"] = {"name": name}
        return d

    def wire(node, name, lid):
        for s in node["inputs"]:
            if s["name"] == name:
                s["link"] = lid
                return
        raise KeyError(f"{node['id']} has no input {name}")

    old_rewriters = {b[1] for b in BANDS.values()}

    # The base file is hand-arranged, so work from its real coordinates: keep
    # each band's internal layout and just push the lower bands down to make
    # room for the taller local rewriter (concat + VLM stacked).
    band_members = {
        "SEEDANCE": {60, 61, 30, 31, 62},
        "FLUX 3": {70, 71, 90, 91, 72},
        "MINIMAX H3": {80, 81, 82} | set(range(40, 58)),
    }
    band_shift = {"SEEDANCE": 0, "FLUX 3": 420, "MINIMAX H3": 840}
    band_group = {"SEEDANCE": "SEEDANCE", "FLUX 3": "FLUX 3",
                  "MINIMAX H3": "MINIMAX H3 -"}

    slots = {label: list(by[b[1]]["pos"]) for label, b in BANDS.items()}
    for label, members in band_members.items():
        dy = band_shift[label]
        slots[label][1] += dy
        if not dy:
            continue
        for nid in members:
            by[nid]["pos"][1] += dy
        for g in w["groups"]:
            if g["title"].startswith(band_group[label]) or (
                    label == "MINIMAX H3" and "ENGINE" in g["title"]):
                g["bounding"][1] += dy

    # Drop the OpenRouter nodes and every link touching them.
    w["nodes"] = [n for n in w["nodes"] if n["id"] not in old_rewriters]
    links[:] = [l for l in links
                if l[1] not in old_rewriters and l[3] not in old_rewriters]
    for nid in old_rewriters:
        by.pop(nid, None)
    for n in w["nodes"]:
        for s in n["inputs"]:
            if s["link"] is not None and not any(l[0] == s["link"]
                                                 for l in links):
                s["link"] = None
        for o in n["outputs"]:
            if o["links"]:
                o["links"] = [i for i in o["links"]
                              if any(l[0] == i for l in links)]

    # --- shared: caption each reference, then batch the four together ------
    img_bottom = max(by[i]["pos"][1] + by[i]["size"][1] for i in IMAGE_NODES)
    cap_x = min(by[i]["pos"][0] for i in IMAGE_NODES)
    cap_y = img_bottom + 40

    cap_ids = []
    for i, img_id in enumerate(IMAGE_NODES):
        cid = 200 + i
        cap_ids.append(cid)
        n = add(cid, "TextOverlay", (cap_x, cap_y + i * 130), (270, 120),
                title=f"caption REF {i + 1}",
                inputs=[sock("images", "IMAGE")],
                outputs=[{"name": "IMAGE", "type": "IMAGE", "links": [],
                          "slot_index": 0}],
                widgets=[f"REF {i + 1}", 6.0, "#ffffff", "top", "left", True])
        lid = link(img_id, out_slot(by[img_id], "IMAGE"), cid, 0, "IMAGE")
        wire(n, "images", lid)
        by[img_id]["outputs"][out_slot(by[img_id], "IMAGE")]["links"].append(lid)

    batch = add(204, "BatchImagesNode", (cap_x + 290, cap_y), (270, 190),
                title="REF 1-4 -> one sequence for the VLM",
                inputs=[sock(f"images.image{i}", "IMAGE", label=f"image{i}",
                             optional=i > 0) for i in range(5)],
                outputs=[{"name": "IMAGE", "type": "IMAGE", "links": [],
                          "slot_index": 0}])
    for i, cid in enumerate(cap_ids):
        lid = link(cid, 0, 204, i, "IMAGE")
        wire(batch, f"images.image{i}", lid)
        by[cid]["outputs"][0]["links"].append(lid)

    readme = by[1]
    add(205, "MarkdownNote",
        (readme["pos"][0], readme["pos"][1] + readme["size"][1] + 60),
        (560, 700), title="Note: local Qwen3-VL rewriter",
        widgets=[LOCAL_NOTE], color="#222", bgcolor="#000")

    # --- per band: concatenate the prompts, then run Qwen3-VL -------------
    for k, (label, (sid, _lid, pid, vid, pin, _md)) in enumerate(BANDS.items()):
        X_CAT, y = slots[label]
        cat_id, vlm_id = 210 + k * 10, 211 + k * 10

        cat = add(cat_id, "StringConcatenate", (X_CAT, y), (440, 150),
                  title=f"SYSTEM + ROUGH - {label}",
                  inputs=[sock("string_a", "STRING", widget=True),
                          sock("string_b", "STRING", widget=True)],
                  outputs=[{"name": "STRING", "type": "STRING", "links": [],
                            "slot_index": 0}],
                  widgets=["", "", DELIMITER])

        vlm = add(vlm_id, "AILab_QwenVL_Advanced", (X_CAT, y + 180), (440, 560),
                  title=f"LOCAL REWRITER - {label}",
                  inputs=[sock("custom_prompt", "STRING", widget=True),
                          sock("image", "IMAGE", optional=True),
                          sock("video", "IMAGE", optional=True)],
                  outputs=[{"name": "STRING", "type": "STRING", "links": [],
                            "slot_index": 0}],
                  widgets=[VLM_MODEL, "None (FP16)", "auto", False, "auto",
                           "🖼️ Detailed Description", "", VLM_MAX_TOKENS,
                           VLM_TEMPERATURE, 0.9, 1, VLM_REPETITION_PENALTY,
                           16, False, 1, "fixed"],
                  color="#432", bgcolor="#653")

        lid = link(sid, 0, cat_id, 0, "STRING")
        wire(cat, "string_a", lid)
        by[sid]["outputs"][0]["links"].append(lid)

        lid = link(10, 0, cat_id, 1, "STRING")
        wire(cat, "string_b", lid)
        by[10]["outputs"][0]["links"].append(lid)

        lid = link(cat_id, 0, vlm_id, 0, "STRING")
        wire(vlm, "custom_prompt", lid)
        cat["outputs"][0]["links"].append(lid)

        lid = link(204, 0, vlm_id, 2, "IMAGE")
        wire(vlm, "video", lid)
        batch["outputs"][0]["links"].append(lid)

        prev = by[pid]
        prev["pos"] = [X_CAT, y + 770]
        lid = link(vlm_id, 0, pid, 0, "STRING")
        wire(prev, "source", lid)
        vlm["outputs"][0]["links"].append(lid)

        gen = by[vid]
        slot = next(i for i, s in enumerate(gen["inputs"]) if s["name"] == pin)
        lid = link(vlm_id, 0, vid, slot, "STRING")
        wire(gen, pin, lid)
        vlm["outputs"][0]["links"].append(lid)

    # Grow each band's group box to cover the now-taller rewriter column, and
    # the shared-inputs box to cover the caption/batch cluster.
    for g in w["groups"]:
        if g["title"].startswith(("SEEDANCE", "FLUX", "MINIMAX H3 -")):
            g["bounding"][3] = 1050
        if g["title"] == "SHARED INPUTS":
            bottom = max(by[c]["pos"][1] + by[c]["size"][1] for c in cap_ids)
            g["bounding"][3] = bottom + 40 - g["bounding"][1]

    w["id"] = "ksampler-3model-compare-v3-local-vlm"
    w["last_node_id"] = max(n["id"] for n in w["nodes"])
    w["last_link_id"] = next_link[0]
    dump(LOCAL, w)
    return w


def validate(path):
    w = load(path)
    by = index(w)
    errs = []
    for lid, s, ss, d, ds, t in w["links"]:
        if s not in by or d not in by:
            errs.append(f"L{lid}: dangling endpoint")
            continue
        if ds >= len(by[d]["inputs"]) or by[d]["inputs"][ds]["link"] != lid:
            errs.append(f"L{lid}: dst {d}.{ds} mismatch")
        if ss >= len(by[s]["outputs"]) or lid not in (by[s]["outputs"][ss]["links"] or []):
            errs.append(f"L{lid}: src {s}.{ss} mismatch")
    for n in w["nodes"]:
        for i, s in enumerate(n["inputs"]):
            if s["link"] is None and s.get("shape") != 7 and "widget" not in s:
                errs.append(f"{n['id']} {n['type']}: '{s['name']}' unconnected")
            if s["link"] is not None:
                hit = [l for l in w["links"] if l[0] == s["link"]]
                if not hit or hit[0][3] != n["id"] or hit[0][4] != i:
                    errs.append(f"{n['id']} input {i} '{s['name']}' bad link")
    return errs


if __name__ == "__main__":
    base = refresh_base()
    make_local(base)
    for p in (BASE, LOCAL):
        errs = validate(p)
        w = load(p)
        status = "OK" if not errs else "FAIL\n  " + "\n  ".join(errs)
        print(f"{p.name}: {len(w['nodes'])} nodes / {len(w['links'])} links -> {status}")
