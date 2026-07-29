# ComfyUI VFX — Best 12 Workflows

Filenames are the exact Comfy Cloud `template_id`, so you can run any of them directly:

```
run_template(template_id="templates_shane_change_any_objects")
```

…or drag the `.json` into the ComfyUI canvas.

**Node titles, types, IDs and positions are byte-identical to the official templates.** Nothing was renamed or moved.

---

## Two kinds of graph in here

| | What you see on canvas | Can you tune it? |
|---|---|---|
| **Full graph** (3, 7, 12) | Every loader, sampler, LoRA and ControlNet is a real node | Yes — full control |
| **Subgraph wrapper** (the rest) | One packed node between Load and Save | No — models resolve server-side |

That's why the model column below says "server-side" for some: the checkpoints are real, they just aren't exposed as loader nodes on the canvas. Model names for those were read from the template schema.

---

## 1. `api_bria_remove_video_background_transparent`
**Role** — Extract the subject from a video and output it with a real alpha channel.
**Base model** — BRIA (server-side)
**Graph** — `LoadVideo → GetVideoComponents → BriaTransparentVideoBackground → JoinImageWithAlpha → SaveWEBM`
**Why it's here** — Outputs alpha WebM **plus** a mask sequence. The only one in the set that hands off cleanly to Nuke/After Effects.

## 2. `video_bernini_r_video_editing` ⭐
**Role** — Replace the background *and* integrate lighting in a single pass. Filed under "relighting" in the catalog, but its stock prompt is literally a background-replacement instruction: *"Replace the gray studio backdrop with a daytime urban street… Only the environment behind the subject should change."*
**Base model** — Wan 2.2 Bernini-R: `wan2.2_bernini_r_high_noise_fp8_scaled` + `wan2.2_bernini_r_low_noise_fp8_scaled`, `lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16`, `umt5_xxl_fp8_e4m3fn_scaled`, `Wan2_1_VAE_bf16`
**Graph** — `LoadVideo + LoadImage(ref) → Video Slice → Bernini-R Video Edit → SaveVideo`
**Why it's here** — Newest model generation in the set, and it collapses the usual matte → generate → relight chain into one pass, so there's no keying edge to fix afterwards.

## 3. `templates_shane_change_any_objects` ⭐
**Role** — Name an object in text, get it masked and replaced by a prompt or a reference image.
**Base model** — `wan2.1_vace_14B_fp16` + `Wan21_CausVid_14B_T2V_lora_rank32_v2` + `umt5-xxl-enc-bf16` + `Wan2_1_VAE_bf16`, with SAM3 for segmentation
**Graph** — 30 nodes in 9 labelled groups: `INPUT VIDEOS AND SETTINGS → SAM3 LOADERS + SAMPLERS → MASK SETTINGS / COMPOSITE → WAN VACE MODEL LOADERS → WAN SAMPLERS → SAVE VIDEO`
**Why it's here** — The most tunable graph in the set. Mask growth, blur and VACE strength are all real nodes you can adjust.

## 4. `utility_void_video_inpainting`
**Role** — Remove an object **together with its shadows and reflections**. Target it via the `sam3_text_prompt` field.
**Base model** — VOID two-pass: `void_pass1` + `void_pass2`, `t5xxl_fp16`, `cogvideox_vae`, plus a SAM3 checkpoint and an optical-flow model (server-side)
**Graph** — `LoadVideo → Video Inpaint (VOID) → SaveVideo`
**Why it's here** — Most removal tools leave the contact shadow behind. This one models the physical interaction.

## 5. `video_wan21_scail2_character_replacement_int8`
**Role** — Swap the person in a shot for a reference character, keeping the original motion.
**Base model** — `wan2.1_14B_SCAIL_2_int8_convrot` + `wan2.1_SCAIL_2_DPO_lora_bf16` + `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16`, `clip_vision_h`, `sam3.1_multiplex_fp16` (server-side)
**Graph** — Base pass + Extend pass, so shots longer than one clip window chain together (81-frame segments, 5-frame overlap)
**Why it's here** — int8 beats the fp8 build on both quality and speed.

## 6. `api_runway_aleph2_video_edit`
**Role** — Apply a described change while locking original motion and timing.
**Base model** — Runway Aleph2 (partner API)
**Graph** — `LoadVideo (+ optional guidance images) → RunwayAleph2VideoToVideo → SaveVideo`
**Why it's here** — Fallback when #2 drifts on motion. Closed API, no tuning.

## 7. `templates_shane_video_restyle`
**Role** — Restyle a video from a reference image while holding original structure via depth.
**Base model** — `wan2.1_vace_14B_fp16` + `Wan2_1-VACE_module_14B_bf16` + `Wan21_CausVid_14B_T2V_lora_rank32`, with `depth_anything_v2_vitl_fp32` driving the ControlNet
**Graph** — `Load Control Video → Control Video Preprocessing (depth) → Load Reference Image → VACE encode → sampler → Save Video (Mp4)`
**Why it's here** — Depth conditioning is what stops restyling from sliding around between frames.

## 8. `templates_rob_wan_ati_motion_control`
**Role** — Draw motion paths directly on the image and generate video that follows them.
**Base model** — Wan ATI (server-side)
**Graph** — `LoadImage → Animate Path → SaveVideo`
**Why it's here** — Only workflow here with hand-drawn trajectory control — useful for placing an effect along a specific path.

## 9. `utility_video_segment_sam3`
**Role** — Produce mask sequences from a video by text prompt.
**Base model** — SAM3 (server-side)
**Graph** — `LoadVideo → SAM3 segmentation → mask output`
**Why it's here** — Feed it into #3/#4, or use it standalone as a roto replacement.

## 10. `utility_seedvr2_3b_int8_upscale_video`
**Role** — Upscale and restore video without inter-frame flicker.
**Base model** — `seedvr2_3b_int8_convrot` + `seedvr2_ema_vae_fp16` (server-side)
**Graph** — `LoadVideo → SeedVR2 3B Int8 upscale → SaveVideo`
**Why it's here** — One-step diffusion, so it's the best speed/quality trade in the set. Exposes `color_correction_method`, which matters when matching a graded plate.

## 11. `utility_depth_anything3_video_depth_estimation`
**Role** — Generate a depth pass for a video.
**Base model** — Depth Anything v3 (server-side)
**Graph** — `LoadVideo → depth estimation → PreviewImage / CreateVideo → SaveVideo`
**Why it's here** — Drives ControlNet in #7, and works as a depth pass for comp (fog, DOF, atmospheric perspective).

## 12. `basic_mask_operations_and_compositing`
**Role** — Reference graph for mask creation, boolean mask ops, feathering and compositing. **No model required.**
**Base model** — none
**Graph** — 41 nodes in 5 groups: `Example Input`, `Mask Operations`, `Combine Masks`, `Image & Mask Compositing`, `Try It Yourself`
**Why it's here** — Parts bin. Copy nodes out of this when building your own comp graph.

---

## Suggested chains

**Background replacement** — `#2` alone. If you need a real matte for downstream comp, run `#1` first and composite manually.

**Object replacement** — `#9` (mask) → `#3` (replace) → `#4` if a contact shadow survives.

**FX** — `#8` (path) → `#7` (restyle, swapping in an effect LoRA) → `#10` (finish).

## Notes

- **Group boxes**: 12 group rectangles across workflows 3, 5, 6 and 7 were slightly too small for the nodes inside them. The boxes were enlarged. **No node was moved** — verified id/type/title/pos/size identical to source.
- **Don't trust `default` values from `get_template_schema`** — they're shifted by one slot (e.g. `width`=81, `height`=848 on #2). Slot names and types are correct; set values yourself. The ComfyUI UI shows them correctly.
- Workflows 3, 7 and 12 are full local-style graphs; the rest wrap server-side subgraphs.
