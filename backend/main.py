import shutil
import tempfile
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from classify_waste import classify_waste
from rag_query import generate_recommendation
from analytics_db import log_result

app = FastAPI(title="AI WasteWise API")

# Allow the frontend (running on a different port during development) to
# call this API. Tighten this to specific origins before any real
# deployment -- "*" is fine for local development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ItemResult(BaseModel):
    detected_item: str
    waste_category: str
    confidence_note: str
    recommended_action: str
    explanation: str
    sustainability_impact: str
    sources: list[str]
    grounded_in_sources: bool


class AnalyzeResponse(BaseModel):
    status: str  # "classified" | "multi_item" | "uncertain"
    items: list[ItemResult]
    uncertainty_reason: str = ""


def _build_item_result(object_name: str, material: str, category: str, confidence_note: str) -> ItemResult:
    """Call Phase 7 (RAG) for one classified item and shape the combined result."""
    rag_result = generate_recommendation(object_name, material, category)

    # If Phase 7 came back with nothing grounded, surface that honestly
    # rather than showing an empty recommendation.
    action = rag_result.get("recommended_action") or "No grounded recommendation available for this item yet."
    explanation = rag_result.get("explanation") or rag_result.get("coverage_note", "")

    return ItemResult(
        detected_item=object_name,
        waste_category=category,
        confidence_note=confidence_note,
        recommended_action=action,
        explanation=explanation,
        sustainability_impact=rag_result.get("sustainability_impact", ""),
        sources=rag_result.get("sources", []),
        grounded_in_sources=rag_result.get("grounded_in_sources", False),
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    """Full pipeline: image upload -> analysis -> classification -> grounded recommendation."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # Save the upload to a temp file, since the Phase 5/6 functions take
    # a file path (they were built and tested that way) -- no need to
    # rewrite them to accept in-memory bytes.
    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        classification = classify_waste(tmp_path)
    finally:
        os.unlink(tmp_path)  # always clean up the temp file, even on error

    # --- Route based on Phase 6's three possible outcomes ---

    if classification["status"] == "uncertain":
        log_result(
            detected_item="",
            waste_category="Uncertain/Needs Verification",
            grounded_in_sources=False,
            is_uncertain=True,
        )
        return AnalyzeResponse(
            status="uncertain",
            items=[],
            uncertainty_reason=classification.get("uncertainty_notes")
            or classification.get("reason", "Image was flagged as unclear."),
        )

    if classification["status"] == "multi_item":
        items = [
            _build_item_result(
                object_name=item["object"],
                material=item["material"],
                category=item["category"],
                confidence_note="",  # per-object confidence isn't tracked individually yet
            )
            for item in classification["items"]
        ]
        for item in items:
            log_result(
                detected_item=item.detected_item,
                waste_category=item.waste_category,
                grounded_in_sources=item.grounded_in_sources,
                is_uncertain=False,
            )
        return AnalyzeResponse(status="multi_item", items=items)

    # status == "classified" (single item)
    item = _build_item_result(
        object_name=classification["object"],
        material=classification["material"],
        category=classification["category"],
        confidence_note=classification.get("confidence_note", ""),
    )
    log_result(
        detected_item=item.detected_item,
        waste_category=item.waste_category,
        grounded_in_sources=item.grounded_in_sources,
        is_uncertain=False,
    )
    return AnalyzeResponse(status="classified", items=[item])


@app.get("/health")
async def health():
    """Simple check that the API is up -- useful for the frontend and for debugging."""
    return {"status": "ok"}
