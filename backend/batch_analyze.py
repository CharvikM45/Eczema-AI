"""
Batch Analyzer — Pre-compute severity for all eczema dataset images.
Saves results to dataset_results.json (without heavy base64 data for the batch file).
"""

import os
import sys
import json
import time
from analyzer import analyze_image

ECZEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "Eczema")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "dataset_results.json")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def batch_analyze():
    if not os.path.isdir(ECZEMA_DIR):
        print(f"Error: Eczema directory not found at {ECZEMA_DIR}")
        sys.exit(1)

    # Get all image files
    files = sorted([
        f for f in os.listdir(ECZEMA_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ])

    print(f"Found {len(files)} images in {ECZEMA_DIR}")
    results = []
    errors = []

    start = time.time()
    for i, filename in enumerate(files):
        filepath = os.path.join(ECZEMA_DIR, filename)
        try:
            result = analyze_image(image_path=filepath)
            # Remove heavy base64 data for batch storage
            result.pop("heatmap_base64", None)
            result.pop("original_base64", None)
            result["filename"] = filename
            results.append(result)

            if (i + 1) % 50 == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                remaining = (len(files) - i - 1) / rate
                print(f"  [{i+1}/{len(files)}] {filename} → {result['severity_score']} ({result['category']}) "
                      f"[{rate:.1f} img/s, ~{remaining:.0f}s remaining]")
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(files)}] {filename} → ERROR: {e}")

    elapsed = time.time() - start

    # Save results
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Batch analysis complete!")
    print(f"  Total images: {len(files)}")
    print(f"  Successful:   {len(results)}")
    print(f"  Errors:       {len(errors)}")
    print(f"  Time:         {elapsed:.1f}s ({len(results)/elapsed:.1f} img/s)")
    print(f"  Output:       {OUTPUT_PATH}")

    if results:
        scores = [r["severity_score"] for r in results]
        categories = {}
        for r in results:
            cat = r["category"]
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n  Score range:  {min(scores):.1f} – {max(scores):.1f}")
        print(f"  Mean score:   {sum(scores)/len(scores):.1f}")
        print(f"  Distribution: {json.dumps(categories, indent=4)}")

    if errors:
        print(f"\n  Errors:")
        for e in errors[:10]:
            print(f"    {e['filename']}: {e['error']}")
        if len(errors) > 10:
            print(f"    ... and {len(errors)-10} more")


if __name__ == "__main__":
    batch_analyze()
