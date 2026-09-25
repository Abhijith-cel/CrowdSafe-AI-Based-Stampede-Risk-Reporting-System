"""Helper utility for downloading and verifying pretrained weights for CrowdSafe.

Specifically:
- YOLOv8n (default detection model)
- CSRNet (ShanghaiTech Part-A crowd density model)
"""

import os
import urllib.request
import sys

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

YOLO_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
YOLO_PATH = os.path.join(MODELS_DIR, "yolov8n.pt")

# Common public mirror for CSRNet ShanghaiTech Part-A weights
CSRNET_PATH = os.path.join(MODELS_DIR, "CSRNet_ShanghaiTech_A.pth")


def download_file(url: str, dest_path: str) -> None:
    print(f"Downloading from {url} to {dest_path}...")
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest_path, reporthook)
    print("\nDownload complete.")


def verify_models():
    print("Checking Pretrained Models in:", MODELS_DIR)
    
    if os.path.exists(YOLO_PATH):
        size_mb = os.path.getsize(YOLO_PATH) / (1024 * 1024)
        print(f"[OK] YOLOv8n weights found: {YOLO_PATH} ({size_mb:.2f} MB)")
    else:
        print(f"[MISSING] YOLOv8n weights: {YOLO_PATH}")
        print("  Downloading YOLOv8n...")
        try:
            download_file(YOLO_URL, YOLO_PATH)
        except Exception as e:
            print(f"  Error downloading YOLOv8n: {e}")

    if os.path.exists(CSRNET_PATH):
        size_mb = os.path.getsize(CSRNET_PATH) / (1024 * 1024)
        print(f"[OK] CSRNet weights found: {CSRNET_PATH} ({size_mb:.2f} MB)")
    else:
        print(f"[NOTE] CSRNet weights not found at: {CSRNET_PATH}")
        print("  Please download ShanghaiTech Part-A pretrained CSRNet weights (.pth)")
        print("  and save them to this folder as 'CSRNet_ShanghaiTech_A.pth'.")


if __name__ == "__main__":
    verify_models()
