r"""Run the app's real crowd counter on one photo: no Flask, no database.

Run from backend/ with the venv active:
    python test_counter.py crowd.jpg
    python test_counter.py crowd.jpg CSRNet SHA        (optional: model name, weights)

Prints the people estimate and the risk each location type would give.
"""
import sys
from pathlib import Path

import cv2

from app.routes.report_routes import CONTEXT_PROFILES
from app.services.crowd_counter import CounterUnavailableError, CrowdCounter
from app.services.risk_classifier import RiskClassifier

if len(sys.argv) not in (2, 4):
    sys.exit("Usage: python test_counter.py photo.jpg [model_name weights]")

image = cv2.imread(sys.argv[1])
if image is None:
    sys.exit(f"Could not read an image from {sys.argv[1]}")

counter = CrowdCounter(*sys.argv[2:4]) if len(sys.argv) == 4 else CrowdCounter()
try:
    result = counter.count(image)
except CounterUnavailableError as exc:
    sys.exit(f"AI unavailable: {exc}")

print(f"\nPeople estimated: about {result.count}  (model {result.backend})")
print("Risk if this photo were reported as each location type (assumed areas are placeholders):")
classifier = RiskClassifier()
for tag, p in CONTEXT_PROFILES.items():
    density = round(result.count / p["area"], 2)
    a = classifier.classify(density=density, headcount=result.count, is_bottleneck=p["bottleneck"])
    print(f"  {tag:<12} area {p['area']:>5.0f} m2  density {density:>5}  ->  {a.level.value.title()}")