###Backend API

## What this is

A FastAPI server that wires together everything you've already built and
tested:
- `analyze_image.py` (Phase 5) — image → structured description
- `classify_waste.py` (Phase 6) — description → waste category
- `rag_query.py` (Phase 7) — category → grounded disposal recommendation

into a single `POST /analyze` endpoint that takes an image and returns a
complete result.

This file does not contain new AI logic — it only orchestrates the
modules you already tested individually, and shapes the response into
the fields your project brief specifies (Detected Item, Waste Category,
Confidence, Recommended Action, Explanation, Sustainability Impact,
Source/Reference).

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# paste your real Gemini API key into .env
```

You also need the Phase 7 vector store built here, since `rag_query.py`
reads from a local `chroma_store/` folder next to it:

```bash
python ingest_knowledge_base.py
```

(This is the same ingestion step from Phase 7 — just run it once in this
folder too, since `knowledge_base/` was copied here alongside the code.)

## Run the server

```bash
uvicorn main:app --reload
```

You should see something like:
```
Uvicorn running on http://127.0.0.1:8000
```

## Test it

**Option A — interactive docs (easiest):**
Open `http://127.0.0.1:8000/docs` in your browser. FastAPI auto-generates
a UI where you can upload an image directly and see the response, no
extra tools needed.

**Option B — curl:**
```bash
curl -X POST "http://127.0.0.1:8000/analyze" -F "file=@waste1.jpg"
```

**Option C — health check:**
```
http://127.0.0.1:8000/health
```
Should return `{"status": "ok"}` — useful to confirm the server itself
is running before debugging anything else.

## Response shape

```json
{
  "status": "classified",
  "items": [
    {
      "detected_item": "plastic water bottle",
      "waste_category": "Recyclable/Dry Waste",
      "confidence_note": "",
      "recommended_action": "...",
      "explanation": "...",
      "sustainability_impact": "...",
      "sources": ["plastic_waste_guidelines.txt", "swm_rules_2026.txt"],
      "grounded_in_sources": true
    }
  ],
  "uncertainty_reason": ""
}
```

For a blurry image, `status` will be `"uncertain"`, `items` will be
empty, and `uncertainty_reason` will explain why. For a multi-item
photo, `status` will be `"multi_item"` and `items` will have one entry
per detected object.

## What to test next

Run all the same test photos through this endpoint that you tested on
the individual scripts (plastic bottle, blurry image, multi-item photo,
glass bottle) and confirm the combined API behaves the same way the
individual scripts did. If anything differs, that's a real integration
bug worth catching now, before the frontend is built on top of it.
