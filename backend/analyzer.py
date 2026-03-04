"""
Eczema Severity Analyzer — Core Image Analysis Engine
Uses OpenCV to extract measurable features from eczema images
and compute severity via the explicit EASI-inspired formula.
"""

import cv2
import numpy as np
from PIL import Image
import io
import base64
from config import (
    FORMULA_WEIGHTS,
    SEVERITY_THRESHOLDS,
    REDNESS_HSV_LOWER, REDNESS_HSV_UPPER,
    REDNESS_HSV_LOWER2, REDNESS_HSV_UPPER2,
    SKIN_HSV_LOWER, SKIN_HSV_UPPER,
    MIN_LESION_AREA, ANALYSIS_SIZE,
    compute_uv_duration,
)


def load_image(image_path: str = None, image_bytes: bytes = None) -> np.ndarray:
    """Load an image from a file path or bytes."""
    if image_bytes:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif image_path:
        img = cv2.imread(image_path)
    else:
        raise ValueError("Must provide image_path or image_bytes")
    if img is None:
        raise ValueError("Could not load image")
    return img


def preprocess(img: np.ndarray) -> np.ndarray:
    """Resize image for consistent analysis."""
    return cv2.resize(img, ANALYSIS_SIZE, interpolation=cv2.INTER_AREA)


def detect_skin_mask(hsv: np.ndarray) -> np.ndarray:
    """Detect skin regions using HSV color space."""
    mask = cv2.inRange(hsv, np.array(SKIN_HSV_LOWER), np.array(SKIN_HSV_UPPER))
    # Also detect darker skin tones
    mask2 = cv2.inRange(hsv, np.array([0, 10, 40]), np.array([50, 200, 255]))
    combined = cv2.bitwise_or(mask, mask2)
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
    return combined


def detect_affected_regions(img: np.ndarray, hsv: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
    """
    Detect eczema-affected regions using multiple indicators:
    - Redness (inflamed areas)
    - Texture anomalies
    - Color deviation from normal skin
    """
    # 1. Detect reddish/inflamed regions
    red_mask1 = cv2.inRange(hsv, np.array(REDNESS_HSV_LOWER), np.array(REDNESS_HSV_UPPER))
    red_mask2 = cv2.inRange(hsv, np.array(REDNESS_HSV_LOWER2), np.array(REDNESS_HSV_UPPER2))
    redness_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # 2. Detect areas with high saturation (often inflamed/irritated)
    high_sat_mask = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([180, 255, 255]))

    # 3. Detect rough/textured areas via Laplacian edge density
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    lap_abs = np.abs(laplacian).astype(np.uint8)
    _, texture_mask = cv2.threshold(lap_abs, 30, 255, cv2.THRESH_BINARY)

    # 4. Detect abnormal brightness deviation
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]
    skin_pixels = l_channel[skin_mask > 0]
    if len(skin_pixels) > 0:
        mean_l = np.mean(skin_pixels)
        std_l = np.std(skin_pixels)
        deviation_mask = np.zeros_like(l_channel, dtype=np.uint8)
        deviation_mask[np.abs(l_channel.astype(float) - mean_l) > std_l * 1.2] = 255
    else:
        deviation_mask = np.zeros_like(l_channel, dtype=np.uint8)

    # Combine all indicators
    combined = cv2.bitwise_or(redness_mask, texture_mask)
    combined = cv2.bitwise_or(combined, deviation_mask)
    combined = cv2.bitwise_or(combined, high_sat_mask)

    # Only keep affected areas within skin regions
    affected = cv2.bitwise_and(combined, skin_mask)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    affected = cv2.morphologyEx(affected, cv2.MORPH_CLOSE, kernel)
    affected = cv2.morphologyEx(affected, cv2.MORPH_OPEN, kernel)

    return affected


def compute_area_score(affected_mask: np.ndarray, skin_mask: np.ndarray) -> float:
    """Compute percentage of skin that is affected (0–100)."""
    skin_pixels = np.count_nonzero(skin_mask)
    affected_pixels = np.count_nonzero(affected_mask)
    if skin_pixels == 0:
        return 0.0
    percentage = (affected_pixels / skin_pixels) * 100
    return min(percentage, 100.0)


def compute_redness_score(img: np.ndarray, affected_mask: np.ndarray) -> float:
    """Compute redness intensity in affected regions (0–100)."""
    if np.count_nonzero(affected_mask) == 0:
        return 0.0

    # Extract red channel values in affected areas
    b, g, r = cv2.split(img)
    affected_r = r[affected_mask > 0].astype(float)
    affected_g = g[affected_mask > 0].astype(float)
    affected_b = b[affected_mask > 0].astype(float)

    if len(affected_r) == 0:
        return 0.0

    # Redness = how much red dominates over green and blue
    redness_ratio = np.mean(affected_r) / (np.mean(affected_g) + np.mean(affected_b) + 1)
    # Also consider absolute red intensity
    red_intensity = np.mean(affected_r) / 255.0

    # Combine both metrics
    score = (redness_ratio * 50 + red_intensity * 50)
    return min(max(score, 0), 100.0)


def compute_texture_score(img: np.ndarray, affected_mask: np.ndarray) -> float:
    """Compute texture roughness using Laplacian variance (0–100)."""
    if np.count_nonzero(affected_mask) == 0:
        return 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)

    # Get texture values only in affected areas
    affected_lap = laplacian[affected_mask > 0]
    if len(affected_lap) == 0:
        return 0.0

    # Variance of Laplacian indicates texture roughness
    variance = np.var(affected_lap)
    # Normalize: typical range 0–5000, map to 0–100
    score = min(variance / 50.0, 100.0)
    return score


def compute_lesion_density(affected_mask: np.ndarray) -> float:
    """Count distinct lesion regions and compute density (0–100)."""
    contours, _ = cv2.findContours(affected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter small contours
    significant_contours = [c for c in contours if cv2.contourArea(c) >= MIN_LESION_AREA]
    num_lesions = len(significant_contours)

    # Total lesion area
    total_area = sum(cv2.contourArea(c) for c in significant_contours)
    image_area = affected_mask.shape[0] * affected_mask.shape[1]

    # Density combines count and total coverage
    count_score = min(num_lesions / 50.0 * 100, 100)
    area_score = (total_area / image_area) * 100 if image_area > 0 else 0

    score = (count_score * 0.4 + area_score * 0.6)
    return min(score, 100.0)


def compute_swelling_score(img: np.ndarray, affected_mask: np.ndarray, skin_mask: np.ndarray) -> float:
    """Estimate swelling/inflammation via brightness and edge analysis (0–100)."""
    if np.count_nonzero(affected_mask) == 0:
        return 0.0

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(float)
    a_channel = lab[:, :, 1].astype(float)  # red-green axis

    # Compare brightness in affected vs normal skin areas
    normal_mask = cv2.bitwise_and(skin_mask, cv2.bitwise_not(affected_mask))

    affected_l = l_channel[affected_mask > 0]
    normal_l = l_channel[normal_mask > 0]

    if len(normal_l) == 0 or len(affected_l) == 0:
        brightness_diff = 0
    else:
        brightness_diff = abs(np.mean(affected_l) - np.mean(normal_l))

    # Red-green channel difference in affected areas (inflammation indicator)
    affected_a = a_channel[affected_mask > 0]
    a_deviation = np.mean(affected_a) - 128  # LAB a-channel centered at 128

    # Combine metrics
    brightness_score = min(brightness_diff / 40.0 * 100, 100)
    inflammation_score = min(max(a_deviation, 0) / 30.0 * 100, 100)

    score = brightness_score * 0.5 + inflammation_score * 0.5
    return min(score, 100.0)


def generate_heatmap(img: np.ndarray, affected_mask: np.ndarray) -> np.ndarray:
    """Generate a heatmap overlay on the affected regions."""
    # Create colored overlay
    heatmap = np.zeros_like(img)
    heatmap[affected_mask > 0] = [0, 0, 255]  # Red overlay

    # Blend with original
    alpha = 0.4
    overlay = cv2.addWeighted(img, 1 - alpha, heatmap, alpha, 0)

    # Draw contours around affected areas
    contours, _ = cv2.findContours(affected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    significant = [c for c in contours if cv2.contourArea(c) >= MIN_LESION_AREA]
    cv2.drawContours(overlay, significant, -1, (0, 255, 255), 2)

    return overlay


def classify_severity(score: float) -> dict:
    """Classify severity based on score and configurable thresholds."""
    for threshold in SEVERITY_THRESHOLDS:
        if threshold["min"] <= score <= threshold["max"]:
            return {"category": threshold["category"], "color": threshold["color"]}
    return {"category": "Critical", "color": "#e74c3c"}


def generate_explanation(metrics: dict, category: str) -> str:
    """Generate a brief human-readable explanation of the severity assessment."""
    area = metrics["affected_area_pct"]
    redness = metrics["redness_score"]
    texture = metrics["texture_score"]
    lesion = metrics["lesion_density"]
    swelling = metrics["swelling_score"]

    parts = []

    if area > 50:
        parts.append(f"Large affected area ({area:.1f}% of visible skin)")
    elif area > 20:
        parts.append(f"Moderate affected area ({area:.1f}% of visible skin)")
    else:
        parts.append(f"Small affected area ({area:.1f}% of visible skin)")

    if redness > 60:
        parts.append("significant redness/inflammation")
    elif redness > 30:
        parts.append("moderate redness")
    else:
        parts.append("mild redness")

    if texture > 50:
        parts.append("rough/scaly texture")
    elif texture > 25:
        parts.append("moderate texture changes")

    if lesion > 40:
        parts.append("high lesion density")
    elif lesion > 15:
        parts.append("moderate lesion presence")

    if swelling > 40:
        parts.append("notable swelling/inflammation markers")

    explanation = f"Assessment: {category} eczema. "
    explanation += "Detected " + ", ".join(parts) + ". "

    if category == "Critical":
        explanation += "Immediate dermatologist consultation is strongly recommended."
    elif category == "Severe":
        explanation += "Dermatologist consultation is recommended."
    elif category == "Moderate":
        explanation += "Monitor closely and consider medical advice if worsening."
    else:
        explanation += "Continue routine skin care and monitoring."

    return explanation


def analyze_image(image_path: str = None, image_bytes: bytes = None) -> dict:
    """
    Full analysis pipeline for a single image.
    Returns severity score, category, UV duration, metrics, and heatmap.
    """
    # Load and preprocess
    img = load_image(image_path=image_path, image_bytes=image_bytes)
    img = preprocess(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Detect regions
    skin_mask = detect_skin_mask(hsv)
    affected_mask = detect_affected_regions(img, hsv, skin_mask)

    # Compute feature metrics
    area_pct = compute_area_score(affected_mask, skin_mask)
    redness = compute_redness_score(img, affected_mask)
    texture = compute_texture_score(img, affected_mask)
    lesion = compute_lesion_density(affected_mask)
    swelling = compute_swelling_score(img, affected_mask, skin_mask)

    # Apply severity formula
    w = FORMULA_WEIGHTS
    severity_score = (
        area_pct * w["w1_area"] +
        redness * w["w2_redness"] +
        texture * w["w3_texture"] +
        lesion * w["w4_lesion"] +
        swelling * w["w5_swelling"]
    )
    severity_score = round(min(max(severity_score, 0), 100), 2)

    # Classify
    classification = classify_severity(severity_score)
    category = classification["category"]
    color = classification["color"]

    # UV recommendation
    uv = compute_uv_duration(severity_score, category)

    # Metrics dict
    metrics = {
        "affected_area_pct": round(area_pct, 2),
        "redness_score": round(redness, 2),
        "texture_score": round(texture, 2),
        "lesion_density": round(lesion, 2),
        "swelling_score": round(swelling, 2),
    }

    # Explanation
    explanation = generate_explanation(metrics, category)

    # Heatmap
    heatmap_img = generate_heatmap(img, affected_mask)
    _, heatmap_buffer = cv2.imencode('.jpg', heatmap_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    heatmap_b64 = base64.b64encode(heatmap_buffer).decode('utf-8')

    # Original image as base64 for comparison
    _, orig_buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    original_b64 = base64.b64encode(orig_buffer).decode('utf-8')

    return {
        "severity_score": severity_score,
        "category": category,
        "category_color": color,
        "uv_recommendation": uv,
        "metrics": metrics,
        "explanation": explanation,
        "heatmap_base64": heatmap_b64,
        "original_base64": original_b64,
        "formula": f"Score = ({area_pct:.1f}×{w['w1_area']}) + ({redness:.1f}×{w['w2_redness']}) + ({texture:.1f}×{w['w3_texture']}) + ({lesion:.1f}×{w['w4_lesion']}) + ({swelling:.1f}×{w['w5_swelling']}) = {severity_score}",
    }
