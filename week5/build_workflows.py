"""Build the Week 5 workflow JSONs (API format, except W5_03 which is save format).

Every node class / input name here was checked against the Comfy Cloud MCP
catalog (get_node) or an official template. Run: python3 week5/build_workflows.py
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "workflows")

# Input files that do not exist yet. Kept as explicit, obviously-missing names so a
# run fails loudly instead of silently using an unrelated asset.
MISSING_SCENE = "MISSING_W5_02_target_scene.png"
MISSING_PERSON_REF = "MISSING_W5_02_person_ref_fullbody.png"
MISSING_EDIT_STILL = "MISSING_W5_03_edit_still.png"
MISSING_CLEANPLATE_CLIP = "MISSING_W5_04_cleanplate_source.mp4"
MISSING_DAY_CLIP = "MISSING_W5_05_day_source.mp4"
MISSING_BFS_LORA = "MISSING_BFS_qwen_image_2.1_body.safetensors"


def n(class_type, title, **inputs):
    return {"class_type": class_type, "inputs": inputs, "_meta": {"title": title}}


# --------------------------------------------------------------------------- W5_01
def wf1_lora_comparison():
    """Z-Image Turbo + one LoRA loader. One condition per run; strength 0 = no LoRA."""
    return {
        "1": n("UNETLoader", "Base model (Z-Image Turbo)",
               unet_name="z_image_turbo_int8_convrot.safetensors", weight_dtype="default"),
        "2": n("CLIPLoader", "Text encoder", clip_name="qwen_3_4b_fp8_mixed.safetensors",
               type="lumina2", device="default"),
        "3": n("VAELoader", "VAE", vae_name="ae.safetensors"),
        "10": n("PrimitiveFloat", "STUDENT 1/2 - LoRA strength (0 = no LoRA)", value=0.0),
        "11": n("LoraLoaderModelOnly", "Trained LoRA (owned candidate - confirm with instructor)",
                model=["1", 0], lora_name="0824_car.safetensors", strength_model=["10", 0]),
        "12": n("ModelSamplingAuraFlow", "ModelSamplingAuraFlow", model=["11", 0], shift=3),
        "20": n("CLIPTextEncode", "Test prompt (fixed for every condition)", clip=["2", 0],
                text=("A silver performance coupe parked on wet asphalt at dusk, three-quarter "
                      "front view, low camera. Clean bodywork with sharp panel lines and "
                      "undistorted badging. Hard rim light along the roofline, cool ambient fill. "
                      "Commercial automotive photography.")),
        "21": n("ConditioningZeroOut", "Negative (zeroed, cfg 1)", conditioning=["20", 0]),
        "22": n("EmptySD3LatentImage", "Size (fixed)", width=1344, height=768, batch_size=1),
        "30": n("KSampler", "KSampler (seed fixed)", model=["12", 0], positive=["20", 0],
                negative=["21", 0], latent_image=["22", 0], seed=42, steps=8, cfg=1,
                sampler_name="res_multistep", scheduler="simple", denoise=1),
        "31": n("VAEDecode", "VAE Decode", samples=["30", 0], vae=["3", 0]),
        "40": n("PrimitiveString", "STUDENT 2/2 - condition label (match strength)",
                value="0824car_str0.00"),
        "41": n("StringConcatenate", "Output name", string_a="W5_01_LoRA/",
                string_b=["40", 0], delimiter=""),
        "42": n("SaveImage", "Save (name = LoRA + strength)", images=["31", 0],
                filename_prefix=["41", 0]),
    }


# --------------------------------------------------------------------------- W5_02
def wf2_bodyswap():
    """Qwen Image 2.1 Image Edit template, flattened, with a BFS LoRA slot.

    image_1 = target scene (edit target, sets canvas), image_2 = person reference.
    The BFS LoRA file and its trigger text are NOT on Comfy Cloud / unverified.
    """
    return {
        "1": n("UNETLoader", "Qwen Image 2.1", unet_name="qwen_image_2.1_int8_convrot.safetensors",
               weight_dtype="default"),
        "2": n("CLIPLoader", "Qwen3-VL 8B", clip_name="qwen3vl_8b_int8_convrot.safetensors",
               type="qwen_image", device="default"),
        "3": n("VAELoader", "Qwen Image 2.1 VAE", vae_name="qwen_image_2.1_vae_bf16.safetensors"),
        "4": n("LoraLoaderModelOnly", "BFS Body Swap LoRA (NOT ON CLOUD - import first)",
               model=["1", 0], lora_name=MISSING_BFS_LORA, strength_model=1.0),
        "5": n("QwenImage21Cache", "Qwen Image 2.1 Cache", model=["4", 0], device="auto",
               dtype="default"),
        "10": n("LoadImage", "STUDENT - image_1: target scene", image=MISSING_SCENE),
        "11": n("LoadImage", "STUDENT - image_2: person reference (full body, plain bg)",
                image=MISSING_PERSON_REF),
        "20": n("TextEncodeQwenImage21", "Edit prompt (BFS trigger text unverified)",
                clip=["2", 0], vae=["3", 0], resolution=0,
                prompt=("Replace the person in <image1> with the person from <image2>. Keep the "
                        "pose, framing, background and lighting of <image1>."),
                negative_prompt="", **{"images.image_1": ["10", 0], "images.image_2": ["11", 0]}),
        "30": n("KSampler", "KSampler", model=["5", 0], positive=["20", 0], negative=["20", 1],
                latent_image=["20", 2], seed=42, steps=25, cfg=1, sampler_name="euler",
                scheduler="simple", denoise=1),
        "31": n("VAEDecode", "VAE Decode", samples=["30", 0], vae=["3", 0]),
        "40": n("SaveImage", "Save result", images=["31", 0],
                filename_prefix="W5_02_BodySwap/result"),
        "41": n("ImageStitch", "Scene | result", image1=["10", 0], image2=["31", 0],
                direction="right", match_image_size=True, spacing_width=16, spacing_color="white"),
        "42": n("ImageStitch", "Scene | result | reference", image1=["41", 0], image2=["11", 0],
                direction="right", match_image_size=True, spacing_width=16, spacing_color="white"),
        "43": n("SaveImage", "Save comparison strip", images=["42", 0],
                filename_prefix="W5_02_BodySwap/compare"),
    }


# --------------------------------------------------------------------------- W5_04 / W5_05
LTX_NEG = "pc game, console game, video game, cartoon, childish, ugly, still, static, slow"
LTX_SIGMAS = "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"


def ltx_iclora_v2v(ic_lora, prompt, source_file, out_dir):
    """LTX-2.3 IC-LoRA video-to-video, following Lightricks' official
    LTX-2.3_ICLoRA_HDR_Distilled.json (dev ckpt + distilled LoRA 0.5 + IC-LoRA 1.0,
    8 manual sigmas, cfg 1), minus the HDR decode node which Cloud does not have.
    Min-test defaults: shorter side 544 px, 97 frames (8k+1), no audio.
    """
    ck = "ltx-2.3-22b-dev.safetensors"
    return {
        "1": n("CheckpointLoaderSimple", "LTX-2.3 22B dev", ckpt_name=ck),
        "2": n("LTXAVTextEncoderLoader", "Gemma 3 text encoder",
               text_encoder="gemma_3_12B_it.safetensors", ckpt_name=ck, device="default"),
        "3": n("LTXICLoRALoaderModelOnly", "Distilled LoRA (8-step)", model=["1", 0],
               lora_name="ltx-2.3-22b-distilled-lora-384-1.1.safetensors", strength_model=0.5),
        "4": n("LTXICLoRALoaderModelOnly", "IC-LoRA (task adapter)", model=["3", 0],
               lora_name=ic_lora, strength_model=1.0),
        "10": n("LoadVideo", "STUDENT - source clip", file=source_file),
        "11": n("Video Slice", "Trim to first 5 s", video=["10", 0], start_time=0.0,
                duration=5.0, strict_duration=False),
        "12": n("GetVideoComponents", "Frames + fps", video=["11", 0]),
        "13": n("ImageFromBatch", "First 97 frames (8k+1)", image=["12", 0], batch_index=0,
                length=97),
        "14": n("ResizeImageMaskNode", "Min-test size (short side 544)", input=["13", 0],
                resize_type="scale shorter dimension", **{"resize_type.shorter_size": 544},
                scale_method="area"),
        "15": n("SimpleMath+", "multiple = downscale x 32", a=["4", 1], value="a*32"),
        "16": n("ResizeImageMaskNode", "Snap to IC-LoRA grid", input=["14", 0],
                resize_type="scale to multiple", **{"resize_type.multiple": ["15", 0]},
                scale_method="lanczos"),
        "17": n("GetImageSize", "Size / frame count", image=["16", 0]),
        "20": n("CLIPTextEncode", "Prompt", clip=["2", 0], text=prompt),
        "21": n("CLIPTextEncode", "Negative", clip=["2", 0], text=LTX_NEG),
        "22": n("LTXVConditioning", "Frame rate from source", positive=["20", 0],
                negative=["21", 0], frame_rate=["12", 2]),
        "23": n("EmptyLTXVLatentVideo", "Empty latent (source size/length)", width=["17", 0],
                height=["17", 1], length=["17", 2], batch_size=1),
        "24": n("LTXAddVideoICLoRAGuide", "Source video as IC-LoRA guide", positive=["22", 0],
                negative=["22", 1], vae=["1", 2], latent=["23", 0], image=["16", 0],
                frame_idx=0, strength=1.0, latent_downscale_factor=["4", 1], crop="disabled",
                use_tiled_encode=False, tile_size=256, tile_overlap=64),
        "30": n("CFGGuider", "CFG 1", model=["4", 0], positive=["24", 0], negative=["24", 1],
                cfg=1.0),
        "31": n("RandomNoise", "Seed", noise_seed=42),
        "32": n("KSamplerSelect", "Sampler", sampler_name="euler_ancestral"),
        "33": n("ManualSigmas", "Distilled 8-step sigmas", sigmas=LTX_SIGMAS),
        "34": n("SamplerCustomAdvanced", "Sample", noise=["31", 0], guider=["30", 0],
                sampler=["32", 0], sigmas=["33", 0], latent_image=["24", 2]),
        "35": n("LTXVCropGuides", "Drop guide frames", positive=["24", 0], negative=["24", 1],
                latent=["34", 0]),
        "36": n("VAEDecodeTiled", "Decode", samples=["35", 2], vae=["1", 2], tile_size=768,
                overlap=64, temporal_size=64, temporal_overlap=8),
        "40": n("CreateVideo", "Result video", images=["36", 0], fps=["12", 2]),
        "41": n("SaveVideo", "Save result", video=["40", 0], filename_prefix=f"{out_dir}/result",
                format="mp4", **{"format.codec": "h264"}),
        "42": n("CreateVideo", "Source (same trim/size/fps)", images=["16", 0], fps=["12", 2]),
        "43": n("SaveVideo", "Save source for A/B", video=["42", 0],
                filename_prefix=f"{out_dir}/source", format="mp4", **{"format.codec": "h264"}),
    }


def wf4_clean_plate():
    return ltx_iclora_v2v(
        "ltx-2.3-22b-ic-lora-clean-plate-1.0.safetensors",
        ("Clean plate of the same shot. The person walking through the frame is removed and the "
         "background behind them is filled in. Camera motion, lighting, and every other object "
         "stay exactly as in the source."),
        MISSING_CLEANPLATE_CLIP, "W5_04_CleanPlate")


def wf5_day_to_night():
    return ltx_iclora_v2v(
        "ltx-2.3-22b-ic-lora-day-to-night-0.9.safetensors",
        ("The same shot at night. Dark sky, practical lights and street lamps switched on, warm "
         "window glow, cool moonlit ambient light. People, layout and camera motion unchanged."),
        MISSING_DAY_CLIP, "W5_05_DayToNight")


# --------------------------------------------------------------------------- W5_03
def wf3_ideogram(template_path):
    """Official api_ideogram_v4_5_precise_image_edit template (save format), renamed outputs
    and an explicit missing input. Bounding-box edit only (the template's own mechanism)."""
    wf = copy.deepcopy(json.load(open(template_path)))

    def setw(node, idx, key, value):
        node["widgets_values"][idx] = value
        if key in node.get("widgets_values_named", {}):
            node["widgets_values_named"][key] = value

    for node in wf["nodes"]:
        if node["type"] == "LoadImage":
            setw(node, 0, "image", MISSING_EDIT_STILL)
            node["title"] = "STUDENT - approved still to edit"
        elif node["type"] == "SaveImageAdvanced":
            setw(node, 0, "filename_prefix", "W5_03_IdeogramPreciseEdit/result")
        elif node["type"] == "CreateBoundingBoxes":
            # The template's box sits on its own sample portrait. Clear it so nothing is
            # edited until a box is drawn on the instructor's still (canvas = still size).
            node["title"] = "STUDENT - set canvas to still size, draw ONE box, describe ONE change"
            setw(node, 2, "editor_state", [])
        elif node["type"] == "IdeogramPreciseEditApi":
            node["title"] = "Ideogram 4.5 Precise Edit (PAID API - 1 run per approval)"
            setw(node, 3, "model.seed", 42)
            setw(node, 4, "control_after_generate", "fixed")
    wf.setdefault("extra", {})["comfy_mcp"] = {
        "name": "W5_03_Ideogram45_PreciseEdit",
        "description": "Week 5 - Ideogram 4.5 Precise Edit, one bbox edit per run.",
    }
    return wf


def main():
    os.makedirs(OUT, exist_ok=True)
    built = {
        "W5_01_LoRA_Application_Comparison.json": wf1_lora_comparison(),
        "W5_02_Qwen21_BFS_BodySwap.json": wf2_bodyswap(),
        "W5_04_LTX_CleanPlate.json": wf4_clean_plate(),
        "W5_05_LTX_DayToNight_or_Relight.json": wf5_day_to_night(),
    }
    tpl = sys.argv[1] if len(sys.argv) > 1 else None
    if tpl:
        built["W5_03_Ideogram45_PreciseEdit.json"] = wf3_ideogram(tpl)
    for name, wf in built.items():
        with open(os.path.join(OUT, name), "w") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)
        print("wrote", name)


if __name__ == "__main__":
    main()
