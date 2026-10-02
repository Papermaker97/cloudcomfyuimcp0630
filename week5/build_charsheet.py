"""W5_07 character sheet: official Comfy template api_ideogram_v4_5_image_edit.

Input is ONE person photo (image_1) plus a text prompt that describes the whole
turnaround-sheet layout. No layout image is needed. The bbox prompt chain of the
template is replaced by a fixed text prompt, and the output size is set to a 16:9
2K preset (from IDEOGRAM_45_EDIT_SIZES in comfy_api_nodes/nodes_ideogram.py) so the
sheet is wide even when the photo is portrait.

Usage: python3 week5/build_charsheet.py <path to api_ideogram_v4_5_image_edit.json>
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "workflows", "W5_07_Ideogram45_CharacterSheet.json")

PERSON = "MISSING_W5_07_person_input.png"   # instructor-approved photo of the person
SIZE = "(2K) 2560x1440 (16:9)"

PROMPT = (
    "Create a photographic character turnaround reference sheet of the exact person in @Image1.\n"
    "Layout: one wide landscape sheet with a dark brown rounded outer border on a warm greige "
    "background. Inside, a light grey sheet divided by thin vertical lines into five equal-height "
    "panels, left to right. Each panel has a small, thin, all-caps sans-serif header at the top: "
    "\"FACE CLOSE UP\", \"FRONT\", \"BACK\", \"LEFT PROFILE\", \"RIGHT PROFILE\".\n"
    "Panel 1 FACE CLOSE UP: a head-and-shoulders photo of the person facing the camera with a "
    "neutral expression, inside a framed box in the upper part of the panel. Below it, five "
    "left-aligned form lines with labels: \"NAME:\", \"AGE:\", \"HEIGHT:\", \"WEIGHT:\", "
    "\"GENDER:\", each followed by an empty underline.\n"
    "Panels 2 to 5: the same person full body, head to feet fully visible, standing straight with "
    "arms relaxed at the sides, all at the same scale and with feet on the same baseline. Panel 2 "
    "FRONT faces the camera. Panel 3 BACK is seen from directly behind. Panel 4 LEFT PROFILE is a "
    "90 degree side view facing left. Panel 5 RIGHT PROFILE is a 90 degree side view facing right. "
    "Each of panels 2 to 5 has a thin vertical height ruler with small tick marks along its right "
    "edge.\n"
    "Keep the person identical to @Image1 in every panel: face, hairstyle, skin tone, body "
    "proportions, outfit, colours and shoes. Even soft studio lighting, plain light grey panel "
    "backgrounds, clean catalogue photography. No other text, logos or watermarks."
)


def main(template_path):
    wf = copy.deepcopy(json.load(open(template_path)))
    # The bbox chain and the template's own notes (which describe the bbox workflow and
    # its sample asset) are not used.
    drop_types = {"BuildJsonPromptIdeogram", "CreateBoundingBoxes", "PreviewAny", "MarkdownNote"}
    drop_ids = {n["id"] for n in wf["nodes"] if n["type"] in drop_types}
    wf["nodes"] = [n for n in wf["nodes"] if n["id"] not in drop_ids]
    wf["links"] = [l for l in wf["links"] if l[1] not in drop_ids and l[3] not in drop_ids]
    live = {l[0] for l in wf["links"]}
    for node in wf["nodes"]:
        for out in node.get("outputs", []):
            if out.get("links"):
                out["links"] = [l for l in out["links"] if l in live]

    nid = max(n["id"] for n in wf["nodes"])
    lid = max(l[0] for l in wf["links"])
    by_type = {n["type"]: n for n in wf["nodes"]}
    edit = by_type["IdeogramEditApi"]
    person = by_type["LoadImage"]          # already wired to image_1 and ImageCompare A
    save = by_type["SaveImageAdvanced"]

    def setw(node, idx, key, value):
        node["widgets_values"][idx] = value
        if key in node.get("widgets_values_named", {}):
            node["widgets_values_named"][key] = value

    setw(person, 0, "image", PERSON)
    person["title"] = "STUDENT - image_1: person photo (only input)"
    person["color"], person["bgcolor"] = "#322", "#533"

    nid += 1
    prompt = {
        "id": nid, "type": "PrimitiveStringMultiline", "pos": [-190, 630], "size": [700, 760],
        "flags": {}, "order": 0, "mode": 0, "inputs": [],
        "outputs": [{"name": "STRING", "type": "STRING", "links": []}],
        "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
        "widgets_values": [PROMPT], "title": "Character sheet prompt (layout described in text)",
    }
    wf["nodes"].append(prompt)
    lid += 1
    wf["links"].append([lid, prompt["id"], 0, edit["id"], 2, "STRING"])
    prompt["outputs"][0]["links"].append(lid)
    edit["inputs"][2]["link"] = lid

    edit["title"] = "Ideogram 4.5 Edit (PAID API - run only after approval)"
    setw(edit, 2, "model.size", SIZE)
    setw(edit, 5, "model.quality", "medium")
    setw(edit, 6, "model.seed", 42)
    edit["widgets_values"][7] = "fixed"
    edit["widgets_values"][8] = "fixed"
    for k in ("control_after_generate", "control_after_generate#1"):
        if k in edit.get("widgets_values_named", {}):
            edit["widgets_values_named"][k] = "fixed"

    setw(save, 0, "filename_prefix", "W5_07_CharacterSheet/result")

    nid += 1
    wf["nodes"].append({
        "id": nid, "type": "MarkdownNote", "pos": [-1140, 630], "size": [420, 460],
        "flags": {}, "order": 0, "mode": 0, "inputs": [], "outputs": [], "properties": {},
        "widgets_values": [
            "## W5_07 Character sheet\n\n"
            "- Only input: **one person photo** (image_1). Full body, front-facing, plain "
            "background works best.\n"
            "- The sheet layout (5 panels, headers, form lines, rulers) comes from the prompt; "
            "no layout image is used.\n"
            "- Output size: 2560x1440 (16:9).\n"
            "- Students change only the photo.\n\n"
            "Limits: BACK and PROFILE views are invented by the model from one photo. Panel "
            "count, header text and ruler marks can come out wrong. Check every panel.\n\n"
            "Paid API node: one run per approval."],
        "title": "READ ME", "color": "#222", "bgcolor": "#000",
    })
    wf["last_node_id"] = nid
    wf["last_link_id"] = lid
    wf.setdefault("extra", {})["comfy_mcp"] = {
        "name": "W5_07_Ideogram45_CharacterSheet",
        "description": "One person photo + prompt -> 5-panel turnaround character sheet (Ideogram 4.5 Edit).",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(wf, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
