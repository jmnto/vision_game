Place trusted, Ultralytics-compatible YOLO detection `.pt` checkpoints here.

Included: `yolov8n.pt`, official COCO-pretrained Ultralytics YOLOv8 nano weights.
Source: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
Integrity: see `SHA256SUMS` (paths relative to the project root).

Class names: `apple`, `orange`. Optional `<model-stem>.json` maps other names:
`{"ripe_apple":"apple","laranja":"orange"}`.

In the game: Model lab → Refresh model list → Field simulator → Detection model.
The loader detects checkpoint modifications even when the filename is unchanged.
See the main README for compatibility and Ultralytics licensing.
