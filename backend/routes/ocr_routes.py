import os
import re
import cv2
import numpy as np
import easyocr
import torch
from flask import Blueprint, request, jsonify
from database import db
from database.models import OcrResult, CerResult
from pathlib import Path
import Levenshtein as L
from utils.normalizer import normalize_pred
from pythainlp.tag import NER

# ====== Thai NER model ======
thai_ner = NER("thainer")

# ====== ตรวจสอบ GPU (MPS) บน Mac ======
USE_GPU = torch.backends.mps.is_available()
print(f"🔥 EasyOCR is using {'GPU (MPS)' if USE_GPU else 'CPU'}")

# ====== EasyOCR Reader ======
reader = easyocr.Reader(['th'], gpu=USE_GPU)

ocr_bp = Blueprint("ocr_bp", __name__)

# ====== Gaussian Preprocess ======
def preprocess_gaussian(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    return blur

# ====== CER Calculation ======
def compute_cer(pred: str, truth: str) -> float:
    pred = re.sub(r"\s+", "", (pred or "").strip())
    truth = re.sub(r"\s+", "", (truth or "").strip())
    if len(truth) == 0:
        return 0.0 if len(pred) == 0 else 1.0
    return round(L.distance(pred, truth) / len(truth), 4)

# ====== Extract Fields with Regex + NER ======
def extract_fields_from_text(text):
    from pythainlp.tag import NER
    import Levenshtein as L
    import re

    thai_ner = NER("thainer")
    data = {}

    # --- Clean unwanted chars ---
    text = re.sub(r"[^\u0E00-\u0E7F0-9\s\.\/\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # =============================
    # 🔹 1. หมายเลขบัตรประชาชน (13 หลัก)
    # =============================
    id_match = re.search(r"\b[1-8]\s?[0-9]{4}\s?[0-9]{5}\s?[0-9]{2}\s?[0-9]\b", text)
    if id_match:
        d = re.sub(r"\s+", "", id_match.group(0))
        data["id_number"] = d
    else:
        id_match2 = re.search(r"\d{12,}", text)
        data["id_number"] = id_match2.group(0) if id_match2 else ""

    # =============================
    # 🔹 2. ใช้ NER หาคำนำหน้า / ชื่อ / นามสกุล
    # =============================
    prefix, first_name, last_name = "", "", ""
    ner_result = thai_ner.tag(text)

    for token, tag in ner_result:
        if tag == "TITLE":
            prefix = token
        elif tag == "NAME" and not first_name:
            first_name = token
        elif tag == "SURNAME" and not last_name:
            last_name = token

    # --- Fallback ด้วย Regex ---
    if not prefix or not first_name or not last_name:
        name_match = re.search(
            r"(นาย|นางสาว|นาง|น\.ส\.|นส)\s*([ก-๙]{2,})\s*([ก-๙]{2,})", text
        )
        if name_match:
            prefix = prefix or name_match.group(1)
            first_name = first_name or name_match.group(2)
            last_name = last_name or name_match.group(3)

    data["prefix"] = prefix
    data["first_name"] = first_name
    data["last_name"] = last_name

    # =============================
    # 🔹 3. วันเดือนปีเกิด
    # =============================
    text_fixed = re.sub(r"ก\.ุพ\.", "ก.พ.", text)
    text_fixed = re.sub(r"เม\.ย\.", "เม.ย.", text_fixed)

    dob_match = re.search(
        r"(\d{1,2}\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s*\d{2,4})",
        text_fixed
    )
    data["dob"] = dob_match.group(1) if dob_match else ""

    # =============================
    # 🔹 4. ที่อยู่ (Address) — OCR เพี้ยนทนได้
    # =============================
    addr_pattern = re.compile(
        r"([หหมู่|บ้าบานเลขที่|ตำ|ทม|อำเภ|อท|จังหวัด|จ\.][\u0E00-\u0E7F0-9\s/\.]*)"
    )
    addr_match = addr_pattern.search(text_fixed)
    if addr_match:
        data["address"] = addr_match.group(0).strip()
    else:
        # fallback fuzzy match
        lines = text_fixed.split()
        keywords = ["หมู่", "ตำบล", "อำเภอ", "จังหวัด", "ต.", "อ.", "จ."]
        for i, token in enumerate(lines):
            for kw in keywords:
                if L.ratio(token, kw) > 0.7:
                    data["address"] = " ".join(lines[i:i + 10])
                    break
            if "address" in data:
                break

    if "address" not in data:
        data["address"] = ""

    # =============================
    # 🔹 5. Normalize ทุกฟิลด์
    # =============================
    for k in data:
        data[k] = normalize_pred(k, data[k])

    return data


# ====== /upload_ocr ======
@ocr_bp.route("/upload_ocr", methods=["POST"])
def upload_ocr():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        return jsonify({"error": "File type not allowed"}), 400

    BASE_DIR = Path(__file__).resolve().parents[1]
    save_dir = BASE_DIR / "uploads"
    save_dir.mkdir(exist_ok=True)
    os.chmod(save_dir, 0o777)

    filename = file.filename
    save_path = str(save_dir / filename)
    file.save(save_path)

    # --- อ่านภาพ + Preprocess ---
    img = cv2.imread(save_path)
    if img is None:
        return jsonify({"error": "Cannot read image"}), 400

    processed = preprocess_gaussian(img)

    processed_path = str(save_dir / f"processed_{filename}")
    cv2.imwrite(processed_path, processed)

    # --- OCR ---
    result = reader.readtext(processed, detail=0, paragraph=True)
    text = "\n".join(result)

    # --- Extract fields ---
    data = extract_fields_from_text(text)

    return jsonify({
        "message": "OCR (Gaussian + EasyOCR) processed successfully!",
        "filename": filename,
        "raw_text": text,
        "processed_image_path": processed_path,
        "result": data
    })


# ====== /save_ocr ======
@ocr_bp.route("/save_ocr", methods=["POST"])
def save_ocr():
    data = request.get_json()

    required = ["filename", "id_number", "prefix", "first_name", "last_name", "dob", "address"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # OCR ก่อนหน้า
    ocr_prev = OcrResult.query.filter_by(filename=data["filename"]).order_by(OcrResult.id.desc()).first()

    # บันทึกผลใหม่
    ocr_result = OcrResult(
        filename=data["filename"],
        original_image_path=f"uploads/{data['filename']}",
        processed_image_path=f"uploads/processed_{data['filename']}",
        id_number=data["id_number"],
        prefix=data["prefix"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        address=data["address"]
    )
    db.session.add(ocr_result)
    db.session.commit()

    # คำนวณ CER
    fields = ["id_number", "prefix", "first_name", "last_name", "dob", "address"]
    field_cer = {}
    for f in fields:
        pred = getattr(ocr_prev, f) if ocr_prev else ""
        truth = data.get(f, "")
        field_cer[f] = compute_cer(pred or "", truth or "")

    cer_avg = round(sum(field_cer.values()) / len(field_cer), 4)

    # บันทึก CER summary
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
