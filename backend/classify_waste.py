"""
Phase 6 -- Waste Classification Logic
=======================================

Purpose:
    Take the structured description from Phase 5 (analyze_image.py) and map
    it to one of the project's defined waste categories.

Why rules instead of asking Gemini to output the category directly:
    - Transparent: every classification decision traces to a fixed,
      inspectable rule -- you can explain exactly why an item was
      classified a certain way in an interview.
    - Testable: the mapping table is a fixed table, not a black box.
    - Keeps "uncertainty" handling explicit and separate from "what
      category is this" -- these are two different judgments and
      conflating them would hide failures.

Design decisions (per project owner's choices):
    - Multiple objects in one photo -> classify EACH object separately
      and return a list, rather than lumping everything into one
      "Mixed Waste" label.
    - A low raw_confidence_signal on an otherwise CLEAR, single-object
      image does NOT route to Uncertain -- it still classifies normally,
      just carries a note about lower confidence. Only actual blurriness/
      unclear images route to Uncertain.

Categories (must match the project's documented category definitions):
    - Organic/Wet Waste
    - Recyclable/Dry Waste   (plastic, paper, cardboard)
    - Glass
    - Metal
    - E-waste
    - Uncertain/Needs Verification
"""

import sys
import json

from analyze_image import analyze_image, client, MODEL_NAME, MAX_RETRIES, RETRY_DELAY_SECONDS
from PIL import Image
import time


# --- Material -> category mapping table -------------------------------
# This is the single source of truth for classification. Keep it here,
# in one place, so it's easy to point to and explain.
MATERIAL_TO_CATEGORY = {
    "plastic": "Recyclable/Dry Waste",
    "paper": "Recyclable/Dry Waste",
    "cardboard": "Recyclable/Dry Waste",
    "glass": "Glass",
    "metal": "Metal",
    "organic": "Organic/Wet Waste",
    "e-waste": "E-waste",
}

UNCERTAIN_CATEGORY = "Uncertain/Needs Verification"


def map_material_to_category(material: str) -> str:
    """Look up a single material string in the mapping table.
    Anything not explicitly listed (including 'mixed' or 'unclear')
    falls through to Uncertain -- we never guess on unknown materials.
    """
    return MATERIAL_TO_CATEGORY.get(material.lower().strip(), UNCERTAIN_CATEGORY)


def get_materials_for_objects(image_path: str, object_names: list[str]) -> list[str]:
    """When multiple objects were detected, ask Gemini specifically for the
    material of EACH named object, so we can classify them individually.
    This is a second, narrower call rather than overloading the Phase 5
    prompt -- keeps each prompt doing one clear job.
    """
    img = Image.open(image_path)
    object_list_str = ", ".join(f'"{name}"' for name in object_names)

    prompt = f"""You previously identified these objects in this image: {object_list_str}

For EACH object listed, state its most likely waste material.
Respond with ONLY a JSON object mapping each object name to one material
from this exact list: plastic, paper, cardboard, glass, metal, organic,
e-waste, mixed, unclear.

Example format:
{{"plastic bottle": "plastic", "banana peel": "organic"}}

If you cannot confidently judge an object's material, use "unclear" for it
rather than guessing.
"""

    last_error = None
    response = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[prompt, img],
            )
            break
        except Exception as e:
            last_error = e
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Gemini API call failed after {MAX_RETRIES} attempts: {e}"
                ) from e
            time.sleep(RETRY_DELAY_SECONDS)

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        materials_by_object = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Model did not return valid JSON for per-object materials. Raw response:\n{raw_text}"
        ) from e

    # Preserve the original object order, defaulting to "unclear" if the
    # model somehow skipped one -- never silently drop an item.
    return [materials_by_object.get(name, "unclear") for name in object_names]


def classify_waste(image_path: str) -> dict:
    """Full Phase 5 + Phase 6 pipeline: analyze the image, then classify it.

    Returns a dict with either:
      - a single classification result, or
      - a multi-item result listing each object's own classification
    depending on what was detected.
    """
    analysis = analyze_image(image_path)

    # Rule 1: an unclear image always routes to Uncertain, regardless of
    # anything else. This is a hard gate, not a soft signal.
    if not analysis["image_is_clear"]:
        return {
            "status": "uncertain",
            "category": UNCERTAIN_CATEGORY,
            "reason": "Image was flagged as unclear.",
            "uncertainty_notes": analysis.get("uncertainty_notes", ""),
            "raw_analysis": analysis,
        }

    # Rule 2: multiple objects -> classify each one separately.
    if analysis["multiple_objects_present"]:
        object_names = [analysis["object_detected"]] + analysis.get("other_objects", [])
        materials = get_materials_for_objects(image_path, object_names)

        items = []
        for name, material in zip(object_names, materials):
            items.append({
                "object": name,
                "material": material,
                "category": map_material_to_category(material),
            })

        return {
            "status": "multi_item",
            "items": items,
            "raw_analysis": analysis,
        }

    # Rule 3: single, clear object -> classify normally.
    # A low raw_confidence_signal does NOT force Uncertain here -- it's
    # carried through as a note only, per project owner's decision.
    category = map_material_to_category(analysis["visible_material"])
    return {
        "status": "classified",
        "object": analysis["object_detected"],
        "material": analysis["visible_material"],
        "category": category,
        "model_confidence_signal": analysis["raw_confidence_signal"],
        "confidence_note": (
            "Gemini reported low confidence on this classification -- "
            "treat the result as provisional."
            if analysis["raw_confidence_signal"] == "low"
            else ""
        ),
        "raw_analysis": analysis,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python classify_waste.py <path_to_image>")
        sys.exit(1)

    result = classify_waste(sys.argv[1])
    print(json.dumps(result, indent=2))
