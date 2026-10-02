"""W5_07 character sheet: official Comfy template api_ideogram_v4_5_image_edit, with the
bbox prompt chain replaced by a fixed text prompt.
image_1 = blank turnaround layout (the canvas Ideogram edits), image_2 = input person.
Usage: python3 week5/build_charsheet.py <path to api_ideogram_v4_5_image_edit.json>
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "workflows", "W5_07_Ideogram45_CharacterSheet.json")

LAYOUT = "W5_charsheet_layout_blank.png"          # week5/assets, upload to Cloud input first
PERSON = "MISSING_W5_07_person_input.png"         # instructor-approved photo of the person

PROMPT = (
    "Image 1 is a blank character turnaround sheet. Image 2 is a photo of a real person. "
    "Fill every grey silhouette in image 1 with that exact person from image 2, as a "
    "photographic studio character sheet.\n"
    "Keep the sheet exactly as it is: the five panels, panel borders, the header labels "
    "\"FACE CLOSE UP\", \"FRONT\", \"BACK\", \"LEFT PROFILE\", \"RIGHT PROFILE\", the height "
    "rulers and the NAME / AGE / HEIGHT / WEIGHT / GENDER fields. Do not add any other text.\n"
    "Panel 1 FACE CLOSE UP: head and shoulders, facing camera, neutral expression.\n"
    "Panel 2 FRONT: full body facing camera, standing straight, arms relaxed at the sides.\n"
    "Panel 3 BACK: full body seen from directly behind.\n"
    "Panel 4 LEFT PROFILE: full body, 90 degree side view facing left.\n"
    "Panel 5 RIGHT PROFILE: full body, 90 degree side view facing right.\n"
    "Same face, hairstyle, skin tone, body proportions, outfit and shoes in every panel, "
    "copied from image 2. Head to feet fully visible, same scale in panels 2 to 5, aligned "
    "to the height rulers. Even soft studio lighting, plain light grey panel background."
)


def main(template_path):
    wf = copy.deepcopy(json.load(open(template_path)))
    drop_types = {"BuildJsonPromptIdeogram", "CreateBoundingBoxes", "PreviewAny"}
    # The template's own notes describe the bbox workflow and its sample asset; drop them too.
    drop_ids = {n["id"] for n in wf["nodes"]
                if n["type"] in drop_types or n["type"] == "MarkdownNote"}
    wf["nodes"] = [n for n in wf["nodes"] if n["id"] not in drop_ids]
    wf["links"] = [l for l in wf["links"] if l[1] not in drop_ids and l[3] not in drop_ids]

    nid = max(n["id"] for n in wf["nodes"])
    lid = max(l[0] for l in wf["links"])
    by_type = {n["type"]: n for n in wf["nodes"]}
    edit = by_type["IdeogramEditApi"]
    layout = by_type["LoadImage"]
    save = by_type["SaveImageAdvanced"]

    def setw(node, idx, key, value):
        node["widgets_values"][idx] = value
        if key in node.get("widgets_values_named", {}):
            node["widgets_values_named"][key] = value

    # image_1: blank layout (already wired in the template)
    setw(layout, 0, "image", LAYOUT)
    layout["title"] = "image_1 - blank character sheet layout (fixed)"

    # image_2: person
    nid += 1
    person = {
        "id": nid, "type": "LoadImage", "pos": [-670, 1420], "size": [390, 520], "flags": {},
        "order": 0, "mode": 0, "inputs": [],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []},
                    {"name": "MASK", "type": "MASK", "links": None}],
        "properties": {"Node name for S&R": "LoadImage"},
        "widgets_values": [PERSON, "image"],
        "title": "STUDENT - image_2: person (full body, front, plain background)",
        "color": "#322", "bgcolor": "#533",
    }
    wf["nodes"].append(person)
    lid += 1
    wf["links"].append([lid, person["id"], 0, edit["id"], 1, "IMAGE"])
    person["outputs"][0]["links"].append(lid)
    edit["inputs"][1]["link"] = lid

    # prompt
    nid += 1
    prompt = {
        "id": nid, "type": "PrimitiveStringMultiline", "pos": [-190, 630], "size": [700, 600],
        "flags": {}, "order": 0, "mode": 0, "inputs": [],
        "outputs": [{"name": "STRING", "type": "STRING", "links": []}],
        "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
        "widgets_values": [PROMPT], "title": "Character sheet prompt (fixed)",
    }
    wf["nodes"].append(prompt)
    lid += 1
    wf["links"].append([lid, prompt["id"], 0, edit["id"], 2, "STRING"])
    prompt["outputs"][0]["links"].append(lid)
    edit["inputs"][2]["link"] = lid

    # layout output no longer feeds the bbox canvas
    for out in layout["outputs"]:
        if out.get("links"):
            out["links"] = [l for l in out["links"]
                            if any(x[0] == l for x in wf["links"])]

    edit["title"] = "Ideogram 4.5 Image Edit (PAID API - run only after approval)"
    setw(edit, 2, "model.size", "source")          # output keeps the layout's size/aspect
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
        "id": nid, "type": "MarkdownNote", "pos": [-1140, 960], "size": [420, 420],
        "flags": {}, "order": 0, "mode": 0, "inputs": [], "outputs": [], "properties": {},
        "widgets_values": [
            "## W5_07 Character sheet\n\n"
            "- **image_1** = blank turnaround layout. It is the canvas Ideogram edits, so the "
            "output keeps its size and panel layout (`size: source`).\n"
            "- **image_2** = the person. Use a full-body, front-facing photo on a plain background.\n"
            "- Students change only image_2.\n\n"
            "Limits: BACK and PROFILE views are invented by the model from one photo. "
            "Small faces, labels and ruler numbers can drift. Check every panel.\n\n"
            "Paid API node: one run per approval."],
        "title": "READ ME", "color": "#222", "bgcolor": "#000",
    })
    wf["last_node_id"] = nid
    wf["last_link_id"] = lid
    wf.setdefault("extra", {})["comfy_mcp"] = {
        "name": "W5_07_Ideogram45_CharacterSheet",
        "description": "Person photo -> 5-panel turnaround character sheet with Ideogram 4.5 Image Edit.",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(wf, open(OUT, "w"), ensure_ascii=False, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
