"""Builds the API-format graph for the Qwen Image 2.1 edit comparison version (product is regenerated)."""
import json, pathlib

KEEP = ("Keep the product itself unchanged: same shape, proportions, colors, materials, logo, printed text and "
        "small details, same position and size in the frame. Photorealistic e-commerce product photo.")
STUDIO = ("Replace only the background with a clean bright professional studio backdrop: seamless white to very light "
          "gray paper sweep, soft diffused even softbox lighting, a soft natural contact shadow under the product. " + KEEP)
LIFESTYLE = ("Replace only the background with a calm lifestyle scene: the product rests on a light natural oak wooden "
             "tabletop, softly blurred cozy minimal interior with neutral beige and warm white tones and a small green "
             "plant, gentle natural window light from the side, shallow depth of field, soft contact shadow. " + KEEP)

def L(n, s=0): return [str(n), s]

g = {
  "1":  {"class_type": "LoadImage", "inputs": {"image": "product.png"}},
  "4":  {"class_type": "PrimitiveBoolean", "inputs": {"value": False}},   # False=밝은 스튜디오 / True=차분한 라이프스타일
  "50": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors", "weight_dtype": "default"}},
  "51": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}},
  "52": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
  "53": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": STUDIO}},
  "54": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": LIFESTYLE}},
  "55": {"class_type": "ComfySwitchNode", "inputs": {"switch": L(4), "on_false": L(53), "on_true": L(54)}},
  "56": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": L(51), "prompt": L(55), "negative_prompt": "",
         "resolution": 1024, "images.image_1": L(1), "vae": L(52)}},
  "57": {"class_type": "QwenImage21Cache", "inputs": {"model": L(50), "device": "auto", "dtype": "default"}},
  "62": {"class_type": "KSampler", "inputs": {"model": L(57), "positive": L(56, 0), "negative": L(56, 1),
         "latent_image": L(56, 2), "seed": 20261001, "steps": 25, "cfg": 1.0, "sampler_name": "euler",
         "scheduler": "simple", "denoise": 1.0}},
  "63": {"class_type": "VAEDecode", "inputs": {"samples": L(62), "vae": L(52)}},
  "71": {"class_type": "SaveImage", "inputs": {"images": L(63), "filename_prefix": "bg_swap_qwen21/result"}},
}
out = pathlib.Path(__file__).with_name("product_bg_swap_qwen21_api.json")
out.write_text(json.dumps(g, ensure_ascii=False, indent=2))
print(json.dumps(g, ensure_ascii=False))
