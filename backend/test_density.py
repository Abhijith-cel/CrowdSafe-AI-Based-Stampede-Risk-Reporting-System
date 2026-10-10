"""Compare density-map crowd counters on one photo. Usage: python test_density.py photo.jpg"""
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit("Usage: python test_density.py photo.jpg")
path = Path(sys.argv[1])
if not path.is_file():
    sys.exit(f"Photo not found: {path}")

from lwcc import LWCC

for name, weights in [("DM-Count", "QNRF"), ("DM-Count", "SHA"), ("CSRNet", "SHA")]:
    try:
        count = LWCC.get_count(str(path), model_name=name, model_weights=weights, resize_img=False)
        print(f"  {name:<9} {weights:<5} ->  about {round(float(count))} people")
    except Exception as exc:
        print(f"  {name:<9} {weights:<5} ->  FAILED: {exc}")
