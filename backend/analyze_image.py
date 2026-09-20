import os
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Copy .env.example to .env and paste your key in."
    )

client = genai.Client(api_key=API_KEY)

# NOTE ON MODEL NAMES: Google renames/retires Gemini model IDs frequently.
# gemini-2.0-flash and gemini-2.5-flash have both since been retired for
# new users as of this writing. gemini-3.6-flash is current as of now -
# if this ever 404s again, check https://ai.google.dev/gemini-api/docs/models
# for the current list rather than guessing.
MODEL_NAME = "gemini-3.6-flash"

# Gemini's servers occasionally return a transient error (e.g. temporary
# overload) rather than an actual error in your code. Retry a couple of
# times with a short pause before giving up.
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

ANALYSIS_PROMPT = """You are analyzing a photo of what may be a waste/trash item.

Respond with ONLY a JSON object (no markdown fences, no extra text) with
exactly these fields:

{
  "object_detected": "<short name of the main item, or 'unclear' if you cannot tell>",
  "visible_material": "<one of: plastic, paper, cardboard, glass, metal, organic, e-waste, mixed, unclear>",
  "image_is_clear": <true or false>,
  "multiple_objects_present": <true or false>,
  "other_objects": ["<list any additional distinct items you see, empty list if none>"],
  "raw_confidence_signal": "<one of: high, medium, low>",
  "uncertainty_notes": "<plain-language explanation of anything that makes this hard to judge - blur, bad lighting, ambiguous material, packaging obscuring the item, etc. Empty string if none.>"
}

Important rules:
- Do NOT guess with false confidence. If the image is blurry, dark, too
  zoomed out, or ambiguous, say so honestly in uncertainty_notes and set
  raw_confidence_signal to "low".
- If you see more than one distinct waste item, set multiple_objects_present
  to true and list them in other_objects.
- Only describe what you can actually see. Do not invent details.
"""


def analyze_image(image_path: str) -> dict:
    """Send one image to Gemini and return the parsed structured description."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"No such file: {image_path}")

    img = Image.open(image_path)

    last_error = None
    response = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[ANALYSIS_PROMPT, img],
            )
            break
        except Exception as e:
            last_error = e
            is_last_attempt = attempt == MAX_RETRIES
            if is_last_attempt:
                raise RuntimeError(
                    f"Gemini API call failed after {MAX_RETRIES} attempts: {e}"
                ) from e
            print(
                f"[attempt {attempt}/{MAX_RETRIES}] API call failed ({e}). "
                f"Retrying in {RETRY_DELAY_SECONDS}s..."
            )
            time.sleep(RETRY_DELAY_SECONDS)

    raw_text = response.text.strip()

    # Models sometimes wrap JSON in ```json fences despite instructions -
    # strip those defensively rather than assuming perfect compliance.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Fail loudly and visibly rather than silently returning bad data -
        # this matters for a project that must not fabricate results.
        raise RuntimeError(
            f"Model did not return valid JSON. Raw response was:\n{raw_text}"
        ) from e

    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_image.py <path_to_image>")
        sys.exit(1)

    result = analyze_image(sys.argv[1])
    print(json.dumps(result, indent=2))
