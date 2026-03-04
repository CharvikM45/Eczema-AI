"""
Eczema Severity Analyzer — FastAPI Backend
"""

import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from analyzer import analyze_image
from config import SEVERITY_THRESHOLDS, FORMULA_WEIGHTS, UV_CATEGORY_DURATIONS

app = FastAPI(
    title="Eczema Severity Analyzer API",
    description="Analyzes eczema images using computer vision and the EASI-inspired severity formula",
    version="1.0.0",
)

# CORS for frontend — set ALLOWED_ORIGINS env var in production (comma-separated)
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check (helpful for debugging)
@app.get("/")
async def root_health():
    return {"status": "online", "message": "Eczema Severity Analyzer API is running"}

@app.get("/api/health")
@app.get("/api/health/")
async def health_check():
    return {"status": "healthy", "service": "Eczema Severity Analyzer"}

DATASET_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "dataset_results.json")

@app.get("/api/config")
@app.get("/api/config/")
async def get_config():
    return {
        "severity_thresholds": SEVERITY_THRESHOLDS,
        "formula_weights": FORMULA_WEIGHTS,
        "uv_durations": UV_CATEGORY_DURATIONS,
    }


@app.post("/api/analyze")
@app.post("/api/analyze/")
async def analyze_uploaded_image(file: UploadFile = File(...)):
    """Analyze an uploaded eczema image and return severity results."""
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        result = analyze_image(image_bytes=image_bytes)
        result["filename"] = file.filename
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/dataset-results")
async def get_dataset_results():
    """Return pre-computed analysis results for all dataset eczema images."""
    if not os.path.exists(DATASET_RESULTS_PATH):
        raise HTTPException(
            status_code=404,
            detail="Dataset results not found. Run batch_analyze.py first."
        )
    with open(DATASET_RESULTS_PATH, "r") as f:
        results = json.load(f)
    return JSONResponse(content=results)


@app.get("/api/dataset-results/summary")
async def get_dataset_summary():
    """Return a summary of the dataset analysis (without base64 images to save bandwidth)."""
    if not os.path.exists(DATASET_RESULTS_PATH):
        raise HTTPException(status_code=404, detail="Dataset results not found.")
    with open(DATASET_RESULTS_PATH, "r") as f:
        results = json.load(f)

    summary = []
    for r in results:
        summary.append({
            "filename": r["filename"],
            "severity_score": r["severity_score"],
            "category": r["category"],
            "category_color": r["category_color"],
            "uv_recommendation": r["uv_recommendation"],
            "metrics": r["metrics"],
            "explanation": r["explanation"],
        })

    # Statistics
    scores = [r["severity_score"] for r in results]
    categories = {}
    for r in results:
        cat = r["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return JSONResponse(content={
        "total_images": len(results),
        "statistics": {
            "mean_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "category_distribution": categories,
        },
        "results": summary,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
