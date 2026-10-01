"""Builds the API-format graph for the product-preserving background swap workflow."""
import json, pathlib

STUDIO = ("clean bright professional studio product photography backdrop, seamless white to very light gray "
          "paper sweep, soft diffused even lighting from large softboxes, the object stands on the smooth floor "
          "of the sweep with a soft subtle contact shadow, minimal, no props, no text, no logo, photorealistic, high detail")
LIFESTYLE = ("calm lifestyle product photo, the object rests on a light natural oak wooden tabletop, softly blurred "
             "cozy minimal interior in the background with neutral beige and warm white tones and a small green plant, "
             "gentle natural window light from the side, shallow depth of field, soft contact shadow, no text, no logo, photorealistic")

def L(n, s=0): return [str(n), s]

g = {
  # ---- 사용자 입력 / 설정 ----
  "1":  {"class_type": "LoadImage", "inputs": {"image": "product.png"}},
  "2":  {"class_type": "LoadImageMask", "inputs": {"image": "product.png", "channel": "red"}},
  "3":  {"class_type": "PrimitiveBoolean", "inputs": {"value": False}},   # use_manual_mask
  "4":  {"class_type": "PrimitiveBoolean", "inputs": {"value": False}},   # False=밝은 스튜디오 / True=차분한 라이프스타일
  "5":  {"class_type": "PrimitiveFloat", "inputs": {"value": 0.6}},       # product size ratio
  "6":  {"class_type": "PrimitiveFloat", "inputs": {"value": 0.5}},       # position x (0..1)
  "7":  {"class_type": "PrimitiveFloat", "inputs": {"value": 0.62}},      # position y (0..1)
  "8":  {"class_type": "PrimitiveInt", "inputs": {"value": 0}},           # mask expand px
  "9":  {"class_type": "PrimitiveFloat", "inputs": {"value": 1.0}},       # mask edge blur
  "10": {"class_type": "PrimitiveInt", "inputs": {"value": 1024}},        # canvas W (fixed)
  "11": {"class_type": "PrimitiveInt", "inputs": {"value": 1024}},        # canvas H (fixed)
  # ---- 1. 제품 분리 ----
  "20": {"class_type": "BiRefNetRMBG", "inputs": {"image": L(1), "model": "BiRefNet-HR-matting", "mask_blur": 0,
         "mask_offset": 0, "invert_output": False, "refine_foreground": False, "background": "Alpha",
         "background_color": "#222222"}},
  "21": {"class_type": "ComfySwitchNode", "inputs": {"switch": L(3), "on_false": L(20, 1), "on_true": L(2)}},
  "22": {"class_type": "GrowMaskWithBlur", "inputs": {"mask": L(21), "expand": L(8), "incremental_expandrate": 0.0,
         "tapered_corners": True, "flip_input": False, "blur_radius": L(9), "lerp_alpha": 1.0, "decay_factor": 1.0,
         "fill_holes": True}},
  "23": {"class_type": "InvertMask", "inputs": {"mask": L(22)}},
  "24": {"class_type": "JoinImageWithAlpha", "inputs": {"image": L(1), "alpha": L(23)}},
  "25": {"class_type": "MaskToImage", "inputs": {"mask": L(22)}},
  "26": {"class_type": "SaveImage", "inputs": {"images": L(24), "filename_prefix": "bg_swap/product_cutout"}},
  "27": {"class_type": "SaveImage", "inputs": {"images": L(25), "filename_prefix": "bg_swap/product_mask"}},
  # ---- 2. 배치 (크기/위치) ----
  "30": {"class_type": "MaskBoundingBox+", "inputs": {"mask": L(22), "padding": 0, "blur": 0, "image_optional": L(1)}},
  "31": {"class_type": "SimpleMath+", "inputs": {"a": L(10), "b": L(5), "value": "a*b"}},
  "32": {"class_type": "SimpleMath+", "inputs": {"a": L(11), "b": L(5), "value": "a*b"}},
  "33": {"class_type": "SimpleMath+", "inputs": {"a": L(31, 1), "b": L(30, 4), "value": "a/b"}},
  "34": {"class_type": "SimpleMath+", "inputs": {"a": L(32, 1), "b": L(30, 5), "value": "a/b"}},
  "35": {"class_type": "SimpleMath+", "inputs": {"a": L(33, 1), "b": L(34, 1), "value": "min(a,b)"}},
  "36": {"class_type": "ImageScaleBy", "inputs": {"image": L(30, 1), "upscale_method": "lanczos", "scale_by": L(35, 1)}},
  "37": {"class_type": "MaskToImage", "inputs": {"mask": L(30)}},
  "38": {"class_type": "ImageScaleBy", "inputs": {"image": L(37), "upscale_method": "bilinear", "scale_by": L(35, 1)}},
  "39": {"class_type": "ImageToMask", "inputs": {"image": L(38), "channel": "red"}},
  "40": {"class_type": "GetImageSize", "inputs": {"image": L(36)}},
  "41": {"class_type": "SimpleMath+", "inputs": {"a": L(10), "b": L(40, 0), "value": "a-b"}},
  "42": {"class_type": "SimpleMath+", "inputs": {"a": L(41), "b": L(6), "value": "max(0, a*b)"}},
  "43": {"class_type": "SimpleMath+", "inputs": {"a": L(11), "b": L(40, 1), "value": "a-b"}},
  "44": {"class_type": "SimpleMath+", "inputs": {"a": L(43), "b": L(7), "value": "max(0, a*b)"}},
  "45": {"class_type": "EmptyImage", "inputs": {"width": L(10), "height": L(11), "batch_size": 1, "color": 8421504}},
  "46": {"class_type": "ImageCompositeMasked", "inputs": {"destination": L(45), "source": L(36), "x": L(42), "y": L(44),
         "resize_source": False, "mask": L(39)}},
  "47": {"class_type": "SolidMask", "inputs": {"value": 0.0, "width": L(10), "height": L(11)}},
  "48": {"class_type": "MaskComposite", "inputs": {"destination": L(47), "source": L(39), "x": L(42), "y": L(44),
         "operation": "add"}},
  # ---- 3. 배경 생성 (제품 영역 제외 인페인트) ----
  "50": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux.1-fill-dev-OneReward-transformer_fp8.safetensors",
         "weight_dtype": "default"}},
  "51": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp16.safetensors",
         "type": "flux", "device": "default"}},
  "52": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
  "53": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": STUDIO}},
  "54": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": LIFESTYLE}},
  "55": {"class_type": "ComfySwitchNode", "inputs": {"switch": L(4), "on_false": L(53), "on_true": L(54)}},
  "56": {"class_type": "CLIPTextEncode", "inputs": {"text": L(55), "clip": L(51)}},
  "57": {"class_type": "FluxGuidance", "inputs": {"guidance": 30.0, "conditioning": L(56)}},
  "58": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": L(56)}},
  "59": {"class_type": "ThresholdMask", "inputs": {"mask": L(48), "value": 0.5}},
  "60": {"class_type": "InvertMask", "inputs": {"mask": L(59)}},
  "61": {"class_type": "InpaintModelConditioning", "inputs": {"positive": L(57), "negative": L(58), "vae": L(52),
         "pixels": L(46), "mask": L(60), "noise_mask": True}},
  "62": {"class_type": "KSampler", "inputs": {"model": L(50), "positive": L(61, 0), "negative": L(61, 1),
         "latent_image": L(61, 2), "seed": 20261001, "steps": 24, "cfg": 1.0, "sampler_name": "euler",
         "scheduler": "normal", "denoise": 1.0}},
  "63": {"class_type": "VAEDecode", "inputs": {"samples": L(62), "vae": L(52)}},
  "64": {"class_type": "PreviewImage", "inputs": {"images": L(63)}},
  # ---- 4. 원본 제품 재합성 + 저장 ----
  "70": {"class_type": "ImageCompositeMasked", "inputs": {"destination": L(63), "source": L(46), "x": 0, "y": 0,
         "resize_source": False, "mask": L(48)}},
  "71": {"class_type": "SaveImage", "inputs": {"images": L(70), "filename_prefix": "bg_swap/result"}},
}
out = pathlib.Path(__file__).with_name("product_bg_swap_api.json")
out.write_text(json.dumps(g, ensure_ascii=False, indent=2))
print(out, len(g))
