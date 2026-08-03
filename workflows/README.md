# Workflows

ComfyUI workflows built against Comfy Cloud, in editor **save format** — drag
the `.json` onto the ComfyUI canvas (local or Cloud) to load it.

## `minimax_h3_flf2v.json` — MiniMax H3: First/Last Frame to Video

FLF2V on the **open-weights** MiniMax H3 checkpoint. You give it a first frame
and a last frame, it generates the motion in between — with native stereo audio
in the same forward pass.

This is deliberately *not* the `api_minimax_h3_flf2v` partner-node template.
That one calls MiniMax's hosted API and bills per generation; this one loads
`Comfy-Org/MiniMax-H3` weights and runs the sampler locally (or on Cloud GPU).

### Why the OSS route works for FLF2V

Comfy shipped three open MiniMax H3 templates on 2026-08-02 — `t2v`, `i2v`,
`r2v` — but no `flf2v`. It turns out none was needed: the released checkpoint is
`minimax_h3_fl2va_pruned_int8_convrot.safetensors`, where **`fl2va` = first/last
frame → video + audio**, and the `MiniMaxH3ImageToVideo` node already exposes
both `first_frame` and `last_frame` as optional inputs. Connecting the second
one is the whole difference between i2v and flf2v.

The same node covers all three modes on one checkpoint:

| first_frame | last_frame | mode |
|---|---|---|
| — | — | t2v |
| connected | — | i2v |
| connected | connected | **flf2v** |

### Graph

```
Load First Frame ─┐
Load Last Frame ──┤
UNETLoader   (fl2va)      ├→ MiniMaxH3ImageToVideo ─┬→ BasicGuider ─┐
CLIPLoader   (Qwen3-VL 32B)                         │               ├→ SamplerCustomAdvanced
VAELoader    (video vae) ─┘                         └───── LATENT ──┘        │
                                                                             ├→ VAEDecode ──────┐
VAELoader    (audio vae) ────────────────────────────────────────────────────┴→ VAEDecodeAudio ─┴→ CreateVideo → SaveVideo
```

Sampling is the same recipe as the official H3 templates: `SamplerCustomAdvanced`
+ `BasicGuider` (no CFG — the model is distilled), `res_multistep` / `simple`,
20 steps.

### Models

All four are already resident on Comfy Cloud. For a local install, pull them
from [`Comfy-Org/MiniMax-H3`](https://huggingface.co/Comfy-Org/MiniMax-H3):

| file | folder |
|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `models/diffusion_models/` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` |
| `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` |

`MiniMaxH3ImageToVideo` is a new core node — update ComfyUI first or it loads
as a red missing node.

### Using it

1. Load your two keyframes into **Load First Frame** / **Load Last Frame**.
2. Write the prompt as a timeline, referring to the keyframes as `<Picture 1>`
   (first) and `<Picture 2>` (last). Describe the audio in the same block —
   H3 generates it jointly, so a prompt with no audio direction still produces
   sound, just unsupervised.
3. Set the canvas and duration, then run.

Two constraints worth knowing:

- **Both frames are center-cropped to `width` × `height`.** Give them the same
  aspect ratio as the Resolution Selector, or your endpoints won't match the
  images you loaded. The optional *Scale to Total Pixels → Get Image Size*
  group in the bottom-left is there if you'd rather have the video follow the
  first frame's aspect — drag its outputs onto `width`/`height`.
- **`length` must sit on H3's block grid, `17k + 5` frames at 24fps.** The Math
  Expression node handles this: type seconds into *Float (duration)* and it
  snaps up to the next legal value (5s → 124 frames).

Native canvas is a 768px short edge, capped at 768×1344. `16:9 @ 0.98 MP` =
1344×768 is the sweet spot; larger costs time without buying detail.
