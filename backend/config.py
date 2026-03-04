"""
Eczema Severity Analyzer — Configuration
All thresholds, weights, and UV durations are editable here.
"""

# ─── Severity Formula Weights ───────────────────────────────────────
# Severity Score = (A × w1) + (R × w2) + (T × w3) + (L × w4) + (S × w5)
# Each component is normalized to 0–100 before weighting.
FORMULA_WEIGHTS = {
    "w1_area": 0.25,       # Affected area percentage weight
    "w2_redness": 0.30,    # Redness intensity weight
    "w3_texture": 0.20,    # Texture roughness weight
    "w4_lesion": 0.15,     # Lesion density weight
    "w5_swelling": 0.10,   # Swelling/inflammation weight
}

# ─── Severity Classification Thresholds ─────────────────────────────
SEVERITY_THRESHOLDS = [
    {"min": 0, "max": 20, "category": "Mild", "color": "#27ae60"},
    {"min": 21, "max": 40, "category": "Moderate", "color": "#f39c12"},
    {"min": 41, "max": 70, "category": "Severe", "color": "#e67e22"},
    {"min": 71, "max": 100, "category": "Critical", "color": "#e74c3c"},
]

# ─── UV Patch Recommendation ────────────────────────────────────────
UV_BASE_TIME_MINUTES = 10  # Base time for UV patch duration

UV_CATEGORY_DURATIONS = {
    "Mild": 10,
    "Moderate": 20,
    "Severe": 35,
    "Critical": 45,
}

# Dynamic formula: UV Duration = BaseTime × (Severity Score / 25)
def compute_uv_duration(severity_score: float, category: str) -> dict:
    dynamic_minutes = UV_BASE_TIME_MINUTES * (severity_score / 25.0)
    category_minutes = UV_CATEGORY_DURATIONS.get(category, 20)
    # Use the average of both methods
    recommended_minutes = round((dynamic_minutes + category_minutes) / 2, 1)
    return {
        "recommended_minutes": recommended_minutes,
        "dynamic_minutes": round(dynamic_minutes, 1),
        "category_minutes": category_minutes,
        "warning": "⚠️ Doctor consultation strongly recommended." if category == "Critical" else None,
    }

# ─── Image Analysis Parameters ──────────────────────────────────────
# HSV ranges for detecting reddish/inflamed skin regions
REDNESS_HSV_LOWER = (0, 40, 60)
REDNESS_HSV_UPPER = (20, 255, 255)
REDNESS_HSV_LOWER2 = (160, 40, 60)
REDNESS_HSV_UPPER2 = (180, 255, 255)

# Skin detection HSV range (broad range to detect skin tones)
SKIN_HSV_LOWER = (0, 20, 50)
SKIN_HSV_UPPER = (50, 255, 255)

# Minimum contour area to count as a lesion (in pixels)
MIN_LESION_AREA = 50

# Image resize dimension for consistent analysis
ANALYSIS_SIZE = (512, 512)
