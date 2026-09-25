# Pretrained Models Directory

This directory stores pretrained neural network weights used by the CrowdSafe system.

## Required Models

### 1. YOLOv8n (Person Detection & Coarse Crowd Counting)
- File: `yolov8n.pt`
- Description: Ultralytics YOLOv8 nano model trained on COCO dataset (class 0: person).
- Auto-download: Ultralytics automatically downloads this file when first initialized in `crowd_counter.py`, or you can download it directly from:
  `https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt`

### 2. CSRNet (Congested Scene Recognition Network for High-Density Crowds)
- File: `CSRNet_ShanghaiTech_A.pth` or `weights.pth`
- Description: Dilated convolutional neural network designed for dense crowd counting, trained on the ShanghaiTech Part-A dataset.
- Source: Research implementations on GitHub (e.g., `https://github.com/leeyeehoo/CSRNet-pytorch`).
