#!/usr/bin/env python3
"""Build workflows/ksampler_3model_compare_v2.json.

The three per-model system prompts live as editable markdown under
workflows/system_prompts/ and are inlined into the graph's system-prompt nodes,
so the workflow stays a single self-contained .json you can drag into ComfyUI.

Run:  python3 tools/build_3model_compare.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SP = ROOT / "workflows" / "system_prompts"
OUT = ROOT / "workflows" / "ksampler_3model_compare_v2.json"

SYS_SEEDANCE = (SP / "seedance20_rewriter.md").read_text(encoding="utf-8")
SYS_H3 = (SP / "minimax_h3_rewriter.md").read_text(encoding="utf-8")
SYS_FLUX = (SP / "flux3_rewriter.md").read_text(encoding="utf-8")

# The rewriter LLM. Same model for all three so the comparison isolates the
# system prompt, not the writer.
LLM_MODEL = "openai/gpt-5.6-sol"
LLM_EFFORT = "low"

ROUGH_PROMPT = """2003년 한국 장난감 광고 느낌으로.

Image 1의 손바닥만한 전자기기가 주인공. 처음엔 제품이 빙글 돌면서 반짝이고,
그 다음 Image 2처럼 부품이 분해됐다가 다시 합쳐지고, Image 3의 모델이 제품을
들고 웃고, 마지막에 Image 4 로고 카드로 끝.

뽕짝같은 신스 음악 깔아주고, 부품 딸깍거리는 소리 넣어줘. 요즘 스마트폰 느낌 나면 안 됨."""

READ_ME = """# 3-MODEL VIDEO COMPARISON RIG  ·  v2

Same 4 images + **one rough prompt** -> three model-native prompts -> three videos.

## What changed from v1

1. **MiniMax H3 is now the open-weights model**, not the API node.
   `MiniMaxH3ReferenceToVideo` + `UNETLoader` / `CLIPLoader` / 2x `VAELoader`,
   sampled locally and muxed with `CreateVideo`. Weights auto-download on first run.
2. **Seedance is 2.0, not 2.5.** There is no Seedance 2.5 node in ComfyUI yet -
   `ByteDance2ReferenceNode` only offers `Seedance 2.0 / 2.0 Fast / 2.0 Mini`.
   The v1 file had the string `"Seedance 2.5"` in that widget, which is not a
   valid option.
3. **A prompt rewriter sits in front of every model.** You write one rough idea
   (Korean is fine). Three `OpenRouter LLM` nodes rewrite it into each model's
   native prompt dialect, using that model's official prompt guide as a system
   prompt. The four reference images are fed to the rewriters too, so they can
   assign real roles to real pictures instead of guessing.
4. **FLUX 3 keyframe slots are 0-indexed** (`keyframes.image_0`). v1 used
   `image_1..image_4`, which is off by one.

## How to use

1. Load your 4 images into the LoadImage nodes.
2. Write your idea, however roughly, in **ROUGH PROMPT**. It feeds all three
   rewriters.
3. Run. Read the three **Preview as Text** nodes to see what each model was
   actually asked for.
4. To run only one model, Ctrl+B the other two groups. Running all three costs
   three generations plus three LLM calls.

## The prompts are deliberately different

Each model wants a different dialect, and that is the point:

- **Seedance 2.0** - a shooting script. `@Image1 defines X. Do NOT take Y.`
  role bindings, `[00:00-00:03]` time budgets, an explicit closing beat, a
  trailing negative list.
- **MiniMax H3** - a six-section structured brief (`subject_definitions:` ...
  `non_diegetic_music:`), `<Picture N>` / `<Subject N>` labels, `(S1)` speaker
  IDs, `<d>[Korean] ...</d>` dialogue tags. This mirrors MiniMax's own
  H3-Context-IR stage.
- **FLUX 3** - flowing prose. Keyframes land on screen pixel-exact, so the
  prompt describes what *moves* rather than what is visible, with layered,
  causal audio and exclusions written as plain sentences.

## Read this before comparing results

The three models do NOT use your images the same way:

- Seedance 2.0 and MiniMax H3 treat them as **references** - identity, style,
  material - that the model reinterprets.
- FLUX 3 treats them as **keyframes** - those exact pixels appear on screen at
  0s / 3s / 6s / 8s.

So a "fair" comparison is only fair on prompt handling and motion, not on how
faithfully the source images survive. Switch the FLUX 3 `placement` widget to
`spread across the clip` if you want it to place the frames itself.

Resolution is also not identical: the API models run 720p, while the local H3
defaults to 864x480 (0.4 MP) to keep 243 frames tractable. Set the Resolution
Selector to **0.9 MP -> 1280x736** to match 720p, at a real cost in time.
"""

H3_NOTE = """## MiniMax H3 - open weights

The `MiniMaxH3ReferenceToVideo` node is the open-source path. Models
auto-download from [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3)
on first run:

```
ComfyUI/models/
  diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
  text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
  vae/minimax_h3_video_vae_fp16.safetensors
  vae/minimax_h3_audio_vae_fp32.safetensors
```

**Reference tags.** In the prompt, images are `<Picture 1>`..`<Picture 4>` in
connection order - the OSS node's own convention. This is NOT the `Image 1`
syntax the MiniMax *API* node uses. The rewriter system prompt already knows.

**Length.** `length` is frames at 24 fps and must land on the model's `17k + 5`
grid. The Math Expression node does that for you:
`max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17`.
10 s -> 243 frames. Trained range is roughly 124-362 frames.

**Scheduler.** `beta` (or `normal`) beats `simple` on reference-heavy prompts.

**ref_image_size.** `match` scales references down to the generation resolution
and is much faster. `max` keeps a 2048px short edge for stronger identity
fidelity - reference tokens ride through every sampling step, so it can be
several times slower.
"""

nodes = []
links = []
_link = [0]


def link(src_id, src_slot, dst_id, dst_slot, typ):
    _link[0] += 1
    links.append([_link[0], src_id, src_slot, dst_id, dst_slot, typ])
    return _link[0]


def node(nid, ntype, pos, size, *, title=None, inputs=None, outputs=None,
         widgets=None, props=None, color=None, bgcolor=None, order=0):
    n = {
        "id": nid,
        "type": ntype,
        "pos": list(pos),
        "size": list(size),
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": ntype},
    }
    if props:
        n["properties"].update(props)
    if widgets is not None:
        n["widgets_values"] = widgets
    if title:
        n["title"] = title
    if color:
        n["color"] = color
        n["bgcolor"] = bgcolor
    nodes.append(n)
    return n


def out(name, typ, links_=None, slot=0):
    return {"name": name, "type": typ, "links": links_ if links_ is not None else [],
            "slot_index": slot}


def sock(name, typ, label=None, optional=False):
    d = {"name": name, "type": typ, "link": None}
    if label:
        d["label"] = label
    if optional:
        d["shape"] = 7
    return d


def wsock(name, typ):
    return {"name": name, "type": typ, "widget": {"name": name}, "link": None}


def wire(node_obj, socket_name, link_id):
    for s in node_obj["inputs"]:
        if s["name"] == socket_name:
            s["link"] = link_id
            return
    raise KeyError(f"{node_obj['id']} has no input {socket_name}")


# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------
X_SYS, X_LLM, X_PRE, X_GEN, X_SAVE = 620, 1090, 1570, 2000, 2470
Y_SEED, Y_FLUX, Y_H3 = 0, 700, 1400
Y_ENGINE = 1900

RED, RED_BG = "#322", "#533"
NOTE_C, NOTE_BG = "#222", "#000"

# --------------------------------------------------------------------------
# Shared inputs
# --------------------------------------------------------------------------
node(1, "MarkdownNote", (-40, -1120), (560, 1040), title="READ ME",
     widgets=[READ_ME], color=NOTE_C, bgcolor=NOTE_BG, order=0)

n_prompt = node(
    10, "PrimitiveStringMultiline", (-40, -40), (560, 300),
    title="ROUGH PROMPT  -  write it lazily, Korean is fine",
    outputs=[out("STRING", "STRING")], widgets=[ROUGH_PROMPT],
    color=RED, bgcolor=RED_BG, order=1)

IMG_META = [
    (20, "Image 1 - hero", "hero.png", (-40, 300)),
    (21, "Image 2 - exploded", "exploded.png", (250, 300)),
    (22, "Image 3 - model", "model.png", (-40, 640)),
    (23, "Image 4 - logo card", "logo.png", (250, 640)),
]
img_nodes = []
for i, (nid, title, fn, pos) in enumerate(IMG_META):
    img_nodes.append(node(
        nid, "LoadImage", pos, (270, 310), title=title,
        outputs=[out("IMAGE", "IMAGE"), out("MASK", "MASK", None, 1)],
        widgets=[fn, "image"], order=2 + i))

# --------------------------------------------------------------------------
# Rewriter bands
# --------------------------------------------------------------------------
BANDS = [
    ("SEEDANCE 2.0", 60, 61, 62, Y_SEED, SYS_SEEDANCE),
    ("FLUX 3", 70, 71, 72, Y_FLUX, SYS_FLUX),
    ("MINIMAX H3", 80, 81, 82, Y_H3, SYS_H3),
]
rewriters = {}
order = 10
for label, sid, lid, pid, y, sys_text in BANDS:
    n_sys = node(
        sid, "PrimitiveStringMultiline", (X_SYS, y), (430, 560),
        title=f"SYSTEM PROMPT - {label}", outputs=[out("STRING", "STRING")],
        widgets=[sys_text], color=RED, bgcolor=RED_BG, order=order)

    n_llm = node(
        lid, "OpenRouterLLMNode", (X_LLM, y), (440, 560),
        title=f"REWRITER - {label}",
        inputs=[
            sock("model.images.image_1", "IMAGE", "image_1", True),
            sock("model.images.image_2", "IMAGE", "image_2", True),
            sock("model.images.image_3", "IMAGE", "image_3", True),
            sock("model.images.image_4", "IMAGE", "image_4", True),
            sock("model.images.image_5", "IMAGE", "image_5", True),
            wsock("prompt", "STRING"),
            wsock("system_prompt", "STRING"),
        ],
        outputs=[out("STRING", "STRING")],
        # order: prompt, model, model.reasoning_effort, seed, system_prompt.
        # model.search_context_size is conditional on the Perplexity models
        # only, so it is not serialized for this model.
        widgets=["", LLM_MODEL, LLM_EFFORT, 42, ""],
        order=order + 1)

    n_pre = node(
        pid, "PreviewAny", (X_PRE, y), (400, 560),
        title=f"PROMPT SENT TO {label}",
        inputs=[sock("source", "*")], outputs=[out("STRING", "STRING")],
        widgets=[], order=order + 2)

    wire(n_llm, "system_prompt", link(sid, 0, lid, 6, "STRING"))
    wire(n_llm, "prompt", link(10, 0, lid, 5, "STRING"))
    for i, img in enumerate(img_nodes):
        wire(n_llm, f"model.images.image_{i + 1}",
             link(img["id"], 0, lid, i, "IMAGE"))
    wire(n_pre, "source", link(lid, 0, pid, 0, "STRING"))

    rewriters[label] = n_llm
    order += 3

# --------------------------------------------------------------------------
# Seedance 2.0  (partner API)
# --------------------------------------------------------------------------
n_seed = node(
    30, "ByteDance2ReferenceNode", (X_GEN, Y_SEED), (430, 560),
    title="Seedance 2.0 - Reference to Video",
    inputs=[
        sock("model.reference_images.image_1", "IMAGE", "image_1", True),
        sock("model.reference_images.image_2", "IMAGE", "image_2", True),
        sock("model.reference_images.image_3", "IMAGE", "image_3", True),
        sock("model.reference_images.image_4", "IMAGE", "image_4", True),
        sock("model.reference_images.image_5", "IMAGE", "image_5", True),
        sock("model.reference_videos.video_1", "VIDEO", "video_1", True),
        sock("model.reference_audios.audio_1", "AUDIO", "audio_1", True),
        sock("model.reference_assets.asset_1", "STRING", "asset_1", True),
        wsock("model.prompt", "STRING"),
    ],
    outputs=[out("VIDEO", "VIDEO")],
    # model, prompt, resolution, ratio, duration, generate_audio,
    # auto_downscale, auto_upscale, seed, control_after_generate, watermark
    widgets=["Seedance 2.0", "", "720p", "16:9", 10, True, True, False,
             42, "fixed", False],
    color="#432", bgcolor="#653", order=30)

n_seed_save = node(
    31, "SaveVideo", (X_SAVE, Y_SEED), (420, 480), title="SAVE - Seedance 2.0",
    inputs=[sock("video", "VIDEO")], outputs=[out("video", "VIDEO", None)],
    widgets=["video/seedance20_", "auto", "auto"], order=31)

wire(n_seed, "model.prompt", link(61, 0, 30, 8, "STRING"))
for i, img in enumerate(img_nodes):
    wire(n_seed, f"model.reference_images.image_{i + 1}",
         link(img["id"], 0, 30, i, "IMAGE"))
wire(n_seed_save, "video", link(30, 0, 31, 0, "VIDEO"))

# --------------------------------------------------------------------------
# FLUX 3  (partner API)
# --------------------------------------------------------------------------
n_flux = node(
    90, "Flux3ImageToVideoNode", (X_GEN, Y_FLUX), (430, 560),
    title="FLUX 3 - Image to Video",
    inputs=[
        sock("keyframes.image_0", "IMAGE", "image_0"),
        sock("keyframes.image_1", "IMAGE", "image_1", True),
        sock("keyframes.image_2", "IMAGE", "image_2", True),
        sock("keyframes.image_3", "IMAGE", "image_3", True),
        sock("keyframes.image_4", "IMAGE", "image_4", True),
        wsock("prompt", "STRING"),
    ],
    outputs=[out("VIDEO", "VIDEO")],
    # prompt, placement, placement.times, aspect_ratio, duration,
    # resolution, generate_audio, safety_tolerance, seed, control
    widgets=["", "at times", "0, 3, 6, 8", "16:9", "10", "720p", True, 2,
             42, "fixed"],
    color="#432", bgcolor="#653", order=32)

n_flux_save = node(
    91, "SaveVideo", (X_SAVE, Y_FLUX), (420, 480), title="SAVE - FLUX 3",
    inputs=[sock("video", "VIDEO")], outputs=[out("video", "VIDEO", None)],
    widgets=["video/flux3_", "auto", "auto"], order=33)

wire(n_flux, "prompt", link(71, 0, 90, 5, "STRING"))
for i, img in enumerate(img_nodes):
    wire(n_flux, f"keyframes.image_{i}", link(img["id"], 0, 90, i, "IMAGE"))
wire(n_flux_save, "video", link(90, 0, 91, 0, "VIDEO"))

# --------------------------------------------------------------------------
# MiniMax H3  (open weights)
# --------------------------------------------------------------------------
HF = "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main"

n_unet = node(
    40, "UNETLoader", (0, Y_ENGINE), (620, 100),
    outputs=[out("MODEL", "MODEL")],
    widgets=["minimax_h3_ref2va_pruned_int8_convrot.safetensors", "default"],
    props={"models": [{
        "name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        "url": f"{HF}/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        "directory": "diffusion_models"}]}, order=40)

n_clip = node(
    41, "CLIPLoader", (0, Y_ENGINE + 140), (620, 130),
    outputs=[out("CLIP", "CLIP")],
    widgets=["qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "minimax",
             "default"],
    props={"models": [{
        "name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "url": f"{HF}/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "directory": "text_encoders"}]}, order=41)

n_vvae = node(
    42, "VAELoader", (0, Y_ENGINE + 310), (620, 80), title="VAE - video",
    outputs=[out("VAE", "VAE")],
    widgets=["minimax_h3_video_vae_fp16.safetensors"],
    props={"models": [{
        "name": "minimax_h3_video_vae_fp16.safetensors",
        "url": f"{HF}/vae/minimax_h3_video_vae_fp16.safetensors",
        "directory": "vae"}]}, order=42)

n_avae = node(
    43, "VAELoader", (0, Y_ENGINE + 430), (620, 80), title="VAE - audio",
    outputs=[out("VAE", "VAE")],
    widgets=["minimax_h3_audio_vae_fp32.safetensors"],
    props={"models": [{
        "name": "minimax_h3_audio_vae_fp32.safetensors",
        "url": f"{HF}/vae/minimax_h3_audio_vae_fp32.safetensors",
        "directory": "vae"}]}, order=43)

n_res = node(
    44, "ResolutionSelector", (0, Y_ENGINE + 550), (290, 180),
    title="Resolution  (0.4 MP -> 864x480; use 0.9 for 1280x736)",
    outputs=[out("width", "INT"), out("height", "INT", None, 1)],
    widgets=["16:9 (Widescreen)", 0.4, 32],
    color=RED, bgcolor=RED_BG, order=44)
n_res["showAdvanced"] = False

n_dur = node(
    45, "PrimitiveFloat", (0, Y_ENGINE + 760), (290, 80),
    title="Duration (seconds)", outputs=[out("FLOAT", "FLOAT")],
    widgets=[10.0], color=RED, bgcolor=RED_BG, order=45)

n_len = node(
    46, "ComfyMathExpression", (0, Y_ENGINE + 870), (290, 80),
    title="seconds -> frames (17k+5 grid @ 24fps)",
    inputs=[{"name": "values.a", "type": "FLOAT,INT,BOOLEAN", "label": "a",
             "link": None},
            {"name": "values.b", "type": "FLOAT,INT,BOOLEAN", "label": "b",
             "shape": 7, "link": None}],
    outputs=[out("FLOAT", "FLOAT", None, 0), out("INT", "INT", None, 1),
             out("BOOL", "BOOLEAN", None, 2)],
    widgets=["max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17"],
    order=46)

n_h3 = node(
    47, "MiniMaxH3ReferenceToVideo", (680, Y_ENGINE), (430, 620),
    title="MiniMax H3 - Reference to Video (open weights)",
    inputs=[
        sock("clip", "CLIP"),
        sock("vae", "VAE"),
        sock("audio_vae", "VAE"),
        sock("ref_images.ref_image_0", "IMAGE", "ref_image_0", True),
        sock("ref_images.ref_image_1", "IMAGE", "ref_image_1", True),
        sock("ref_images.ref_image_2", "IMAGE", "ref_image_2", True),
        sock("ref_images.ref_image_3", "IMAGE", "ref_image_3", True),
        sock("ref_images.ref_image_4", "IMAGE", "ref_image_4", True),
        sock("ref_videos.ref_video_0", "IMAGE", "ref_video_0", True),
        sock("ref_video_audios.ref_video_audio_0", "AUDIO",
             "ref_video_audio_0", True),
        sock("ref_audios.ref_audio_0", "AUDIO", "ref_audio_0", True),
        wsock("prompt", "STRING"),
        wsock("width", "INT"),
        wsock("height", "INT"),
        wsock("length", "INT"),
    ],
    outputs=[out("positive", "CONDITIONING"), out("LATENT", "LATENT", None, 1)],
    widgets=["", 864, 480, 243, "match"],
    color="#432", bgcolor="#653", order=47)

n_noise = node(
    48, "RandomNoise", (1160, Y_ENGINE), (360, 100),
    outputs=[out("NOISE", "NOISE")], widgets=[42, "fixed"], order=48)

n_sampsel = node(
    50, "KSamplerSelect", (1160, Y_ENGINE + 140), (360, 80),
    outputs=[out("SAMPLER", "SAMPLER")], widgets=["res_multistep"], order=49)

n_sched = node(
    51, "BasicScheduler", (1160, Y_ENGINE + 260), (360, 140),
    inputs=[sock("model", "MODEL")], outputs=[out("SIGMAS", "SIGMAS")],
    widgets=["beta", 20, 1], order=50)

n_guider = node(
    49, "BasicGuider", (1160, Y_ENGINE + 440), (360, 80),
    inputs=[sock("model", "MODEL"), sock("conditioning", "CONDITIONING")],
    outputs=[out("GUIDER", "GUIDER")], widgets=[], order=51)

n_samp = node(
    52, "SamplerCustomAdvanced", (1570, Y_ENGINE), (260, 160),
    inputs=[sock("noise", "NOISE"), sock("guider", "GUIDER"),
            sock("sampler", "SAMPLER"), sock("sigmas", "SIGMAS"),
            sock("latent_image", "LATENT")],
    outputs=[out("output", "LATENT"),
             out("denoised_output", "LATENT", None, 1)],
    widgets=[], order=52)

n_vdec = node(
    53, "VAEDecode", (1880, Y_ENGINE), (250, 70),
    inputs=[sock("samples", "LATENT"), sock("vae", "VAE")],
    outputs=[out("IMAGE", "IMAGE")], widgets=[], order=53)

n_adec = node(
    54, "VAEDecodeAudio", (1880, Y_ENGINE + 120), (250, 70),
    inputs=[sock("samples", "LATENT"), sock("vae", "VAE")],
    outputs=[out("AUDIO", "AUDIO")], widgets=[], order=54)

n_cv = node(
    55, "CreateVideo", (2180, Y_ENGINE), (280, 120),
    inputs=[sock("images", "IMAGE"), sock("audio", "AUDIO", None, True)],
    outputs=[out("VIDEO", "VIDEO")], widgets=[24, 8], order=55)

n_h3_save = node(
    56, "SaveVideo", (2510, Y_ENGINE), (420, 480), title="SAVE - MiniMax H3",
    inputs=[sock("video", "VIDEO")], outputs=[out("video", "VIDEO", None)],
    widgets=["video/minimax_h3_oss_", "auto", "auto"], order=56)

node(57, "MarkdownNote", (0, Y_ENGINE + 990), (620, 620),
     title="Note: MiniMax H3 open weights", widgets=[H3_NOTE],
     color=NOTE_C, bgcolor=NOTE_BG, order=57)

wire(n_h3, "clip", link(41, 0, 47, 0, "CLIP"))
wire(n_h3, "vae", link(42, 0, 47, 1, "VAE"))
wire(n_h3, "audio_vae", link(43, 0, 47, 2, "VAE"))
for i, img in enumerate(img_nodes):
    wire(n_h3, f"ref_images.ref_image_{i}", link(img["id"], 0, 47, 3 + i, "IMAGE"))
wire(n_h3, "prompt", link(81, 0, 47, 11, "STRING"))
wire(n_h3, "width", link(44, 0, 47, 12, "INT"))
wire(n_h3, "height", link(44, 1, 47, 13, "INT"))
wire(n_len, "values.a", link(45, 0, 46, 0, "FLOAT"))
wire(n_h3, "length", link(46, 1, 47, 14, "INT"))

wire(n_sched, "model", link(40, 0, 51, 0, "MODEL"))
wire(n_guider, "model", link(40, 0, 49, 0, "MODEL"))
wire(n_guider, "conditioning", link(47, 0, 49, 1, "CONDITIONING"))

wire(n_samp, "noise", link(48, 0, 52, 0, "NOISE"))
wire(n_samp, "guider", link(49, 0, 52, 1, "GUIDER"))
wire(n_samp, "sampler", link(50, 0, 52, 2, "SAMPLER"))
wire(n_samp, "sigmas", link(51, 0, 52, 3, "SIGMAS"))
wire(n_samp, "latent_image", link(47, 1, 52, 4, "LATENT"))

wire(n_vdec, "samples", link(52, 0, 53, 0, "LATENT"))
wire(n_vdec, "vae", link(42, 0, 53, 1, "VAE"))
wire(n_adec, "samples", link(52, 0, 54, 0, "LATENT"))
wire(n_adec, "vae", link(43, 0, 54, 1, "VAE"))
wire(n_cv, "images", link(53, 0, 55, 0, "IMAGE"))
wire(n_cv, "audio", link(54, 0, 55, 1, "AUDIO"))
wire(n_h3_save, "video", link(55, 0, 56, 0, "VIDEO"))

# --------------------------------------------------------------------------
# Backfill output link lists from the link table
# --------------------------------------------------------------------------
by_id = {n["id"]: n for n in nodes}
for lid, src, sslot, _dst, _dslot, _t in links:
    by_id[src]["outputs"][sslot]["links"].append(lid)
for n in nodes:
    for o in n["outputs"]:
        if o["links"] == []:
            o["links"] = None if n["type"] == "SaveVideo" else []

groups = [
    {"id": 1, "title": "SHARED INPUTS", "bounding": [-60, -80, 600, 1010],
     "color": "#3f789e", "font_size": 24, "flags": {}},
    {"id": 2, "title": "SEEDANCE 2.0  (Ctrl+B to bypass)",
     "bounding": [600, -60, 2310, 640], "color": "#a1309b", "font_size": 24,
     "flags": {}},
    {"id": 3, "title": "FLUX 3  (Ctrl+B to bypass)",
     "bounding": [600, 640, 2310, 640], "color": "#88A", "font_size": 24,
     "flags": {}},
    {"id": 4, "title": "MINIMAX H3 - OPEN WEIGHTS  (Ctrl+B to bypass)",
     "bounding": [600, 1340, 2310, 640], "color": "#3f789e", "font_size": 24,
     "flags": {}},
    {"id": 5, "title": "MINIMAX H3 ENGINE", "bounding": [-40, 1840, 3010, 1800],
     "color": "#3f789e", "font_size": 24, "flags": {}},
]

workflow = {
    "id": "ksampler-3model-compare-v2",
    "revision": 0,
    "last_node_id": max(n["id"] for n in nodes),
    "last_link_id": _link[0],
    "nodes": nodes,
    "links": links,
    "groups": groups,
    "config": {},
    "extra": {"frontendVersion": "1.47.11"},
    "version": 0.4,
}

OUT.write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
               encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}  "
      f"({len(nodes)} nodes, {len(links)} links)")
