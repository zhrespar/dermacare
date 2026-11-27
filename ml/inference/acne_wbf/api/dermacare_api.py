
from pathlib import Path
from io import BytesIO
import json
import numpy as np
import torch

from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, UploadFile, File, HTTPException
from ultralytics import YOLO
from ensemble_boxes import weighted_boxes_fusion

CONFIG_PATH = Path(__file__).resolve().parent.parent / "ensemble_configuration.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

DEVICE = 0 if torch.cuda.is_available() else "cpu"

MODEL_1 = YOLO(str((CONFIG_PATH.parent / CONFIG["model_1"]["checkpoint"]).resolve()))
MODEL_2 = YOLO(str((CONFIG_PATH.parent / CONFIG["model_2"]["checkpoint"]).resolve()))

INFER = CONFIG["prediction_settings"]
FUSION = CONFIG["fusion_settings"]

app = FastAPI(
    title="DermaCare AI",
    version="0.1.0",
    description="Research-only acne lesion candidate detection"
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "DermaCare-WBF-V1-V4",
        "device": str(DEVICE),
        "medical_diagnosis": False
    }

def predict_image(image):
    bgr = np.asarray(image.convert("RGB"))[:, :, ::-1].copy()
    h, w = bgr.shape[:2]

    scale = np.array([w, h, w, h], dtype=float)
    all_boxes, all_scores, all_labels = [], [], []

    for model, details in [
        (MODEL_1, CONFIG["model_1"]),
        (MODEL_2, CONFIG["model_2"])
    ]:
        prediction = model.predict(
            source=bgr,
            imgsz=details["imgsz"],
            conf=INFER["conf"],
            iou=INFER["nms_iou"],
            max_det=INFER["max_det_per_model"],
            augment=INFER["augment"],
            device=DEVICE,
            verbose=False
        )[0]

        boxes = prediction.boxes.xyxy.cpu().numpy()
        scores = prediction.boxes.conf.cpu().numpy()

        boxes = np.clip(boxes / scale, 0, 1)

        all_boxes.append(boxes.tolist())
        all_scores.append(scores.tolist())
        all_labels.append([0] * len(scores))

    boxes, scores, labels = weighted_boxes_fusion(
        all_boxes,
        all_scores,
        all_labels,
        weights=FUSION["weights"],
        iou_thr=FUSION["iou_thr"],
        skip_box_thr=FUSION["skip_box_thr"],
        conf_type=FUSION["conf_type"]
    )

    max_count = FUSION["max_fused_detections"]
    display_threshold = 0.10

    detections = []

    for box, score in zip(boxes[:max_count], scores[:max_count]):
        if float(score) < display_threshold:
            continue

        x1, y1, x2, y2 = [float(v) for v in box]

        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            continue

        detections.append({
            "class_id": 0,
            "class_name": "possible_acne_lesion",
            "score": round(float(score), 6),
            "bbox_xyxy_normalized": [
                round(x1, 6), round(y1, 6),
                round(x2, 6), round(y2, 6)
            ]
        })

    return {
        "model": "DermaCare-WBF-V1-V4",
        "status": "research_preview",
        "image_width": w,
        "image_height": h,
        "display_threshold": display_threshold,
        "candidate_count": len(detections),
        "detections": detections,
        "medical_diagnosis": False,
        "clinical_severity_assessed": False,
        "disclaimer": (
            "Research prototype. Possible lesion regions only. "
            "Scores are not calibrated medical probabilities."
        )
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=415, detail="JPEG or PNG required"
        )

    raw = await file.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail="Image too large"
        )

    try:
        with Image.open(BytesIO(raw)) as source:
            if source.width * source.height > 20_000_000:
                raise HTTPException(
                    status_code=413, detail="Image dimensions too large"
                )
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=400, detail="Invalid image"
        )

    return predict_image(image)
