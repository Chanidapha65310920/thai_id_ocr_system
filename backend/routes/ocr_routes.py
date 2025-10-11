import os
import json
import cv2
import pytesseract
import numpy as np
from flask import Blueprint, request, jsonify
from database import db
from database.models import OcrResult, CerResult
import Levenshtein as L
import re
from pathlib import Path
from utils.normalizer import normalize_pred

# ===== PATH CONFIG (macOS) =====
pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/local/share/tessdata/"

ocr_bp = Blueprint("ocr_bp", __name__)

# ===== LOAD ROI JSON =====
BASE = Path(__file__).resolve().parents[1]  # backend/
ROI_PATH = BASE / "roi.json"

with open(ROI_PATH, encoding="utf-8") as f:
    ROI_MAP = json.load(f)

# ===== CROP FUNCTION =====
def crop_by_roi(full_img_bgr, base_name, field):
    if base_name not in ROI_MAP or field not in ROI_MAP[base_name]:
        return None

    x1, y1, x2, y2 = ROI_MAP[base_name][field]
    h, w = full_img_bgr.shape[:2]

    # ✅ ปรับพิกัดให้ปลอดภัย
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))

    # ✅ ตรวจขนาดก่อน crop (ถ้าพิกัดผิดจะข้าม)
    if x2 <= x1 or y2 <= y1:
        print(f"[WARN] Invalid ROI for field '{field}': {x1,y1,x2,y2}")
        return None

    roi = full_img_bgr[y1:y2, x1:x2]
    return roi


# ===== PREPROCESS (Gaussian + Otsu) =====
def preprocess_gaussian_otsu(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

# =============== CER ===================
def compute_cer(pred: str, truth: str) -> float:
    """คำนวณ Character Error Rate"""
    pred = re.sub(r"\s+", "", (pred or "").strip())
    truth = re.sub(r"\s+", "", (truth or "").strip())

    if len(truth) == 0:
        return 0.0 if len(pred) == 0 else 1.0

    return round(L.distance(pred, truth) / len(truth), 4)

# ===== MAIN OCR ROUTE =====
@ocr_bp.route("/upload_ocr", methods=["POST"])
def upload_ocr():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    allowed_ext = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        return jsonify({"error": "File type not allowed"}), 400

    # --- Save upload (macOS safe path) ---
    filename = file.filename
    BASE_DIR = Path(__file__).resolve().parents[1]  # → โฟลเดอร์ backend/
    save_dir = BASE_DIR / "uploads"
    save_dir.mkdir(exist_ok=True)
    os.chmod(save_dir, 0o777)
    save_path = str(save_dir / filename)
    file.save(save_path)


    # --- Load & preprocess ---
    img = cv2.imread(save_path)
    if img is None:
        return jsonify({"error": "Cannot read image"}), 400
    processed = preprocess_gaussian_otsu(img)

    # --- ROI selection ---
    if len(ROI_MAP) == 0:
        return jsonify({"error": "ROI data is empty"}), 404

    first_key = next(iter(ROI_MAP))
    roi_fields = ROI_MAP[first_key]

    debug_dir = Path(__file__).resolve().parents[1] / "debug_rois"
    debug_dir.mkdir(exist_ok=True)

    result_data = {}
    for field, coords in roi_fields.items():
        roi = crop_by_roi(processed, first_key, field)
        if roi is None:
            continue

        cv2.imwrite(str(debug_dir / f"{field}.png"), roi)  # ✅ save preview

        if field == "address":
            config = "--oem 3 --psm 6"
        else:
            config = "--oem 3 --psm 7"

        text = pytesseract.image_to_string(roi, lang="tha", config=config)
        result_data[field] = normalize_pred(field, text)


    debug_rois = {}
    # เพิ่มตรงท้าย upload_ocr เพื่อ debug
    if debug_rois:
        for field, roi in debug_rois.items():
            cv2.imwrite(f"debug_{field}.png", roi)
        



    # ✅ ส่งข้อมูลทุกฟิลด์กลับ frontend
    return jsonify({
        "message": "OCR processed successfully!",
        "filename": filename,
        "original_image_path": save_path,
        "processed_image_path": save_path,
        "result": {
            "id_number": result_data.get("id_number", ""),
            "prefix": result_data.get("prefix", ""),
            "first_name": result_data.get("first_name", ""),
            "last_name": result_data.get("last_name", ""),
            "dob": result_data.get("dob", ""),
            "address": result_data.get("address", "")
        }
    })


@ocr_bp.route("/save_ocr", methods=["POST"])
def save_ocr():
    data = request.get_json()

    required = ["filename", "id_number", "prefix", "first_name", "last_name", "dob", "address"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # ✅ ดึง OCR ก่อนหน้า (ใช้เปรียบเทียบ)
    ocr_prev = OcrResult.query.filter_by(filename=data["filename"]).order_by(OcrResult.id.desc()).first()

    # ✅ บันทึก OCR หลังผู้ใช้แก้ไข
    ocr_result = OcrResult(
        filename=data["filename"],
        original_image_path=data.get("original_image_path"),
        processed_image_path=data.get("processed_image_path"),
        id_number=data["id_number"],
        prefix=data["prefix"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        address=data["address"]
    )

    db.session.add(ocr_result)
    db.session.commit()  # ต้อง commit ก่อนเพื่อให้มี ocr_result.id

    # ✅ คำนวณ CER ต่อฟิลด์
    fields = ["id_number", "prefix", "first_name", "last_name", "dob", "address"]
    field_cer = {}
    for f in fields:
        pred = getattr(ocr_prev, f) if ocr_prev else ""
        truth = data.get(f, "")
        field_cer[f] = compute_cer(pred or "", truth or "")

    cer_avg = round(sum(field_cer.values()) / len(field_cer), 4) if field_cer and any(field_cer.values()) else 0.0

    # ✅ บันทึก summary CER แยกใน cer_results
    cer_summary = CerResult(
        ocr_result_id=ocr_result.id,
        filename=data["filename"],
        cer_id_number=field_cer["id_number"],
        cer_prefix=field_cer["prefix"],
        cer_first_name=field_cer["first_name"],
        cer_last_name=field_cer["last_name"],
        cer_dob=field_cer["dob"],
        cer_address=field_cer["address"],
        cer_avg=cer_avg
    )

    db.session.add(cer_summary)
    db.session.commit()

    return jsonify({
        "message": "OCR + CER summary saved successfully!",
        "filename": data["filename"],
        "ocr_result_id": ocr_result.id,
        "cer_avg": cer_avg,
        "fields_cer": field_cer,
        "saved_data": data
    })
