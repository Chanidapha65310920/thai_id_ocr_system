import os
import re
import cv2
import pytesseract
import numpy as np
from flask import Blueprint, request, jsonify
from database import db
from database.models import OcrResult, CerResult
from pathlib import Path
import Levenshtein as L
from utils.normalizer import normalize_pred

# ===== PATH CONFIG (macOS) =====
pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/local/share/tessdata/"

ocr_bp = Blueprint("ocr_bp", __name__)

# ===== PREPROCESS (Gaussian + Otsu) =====
def preprocess_gaussian_otsu(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

# ===== CER =====
def compute_cer(pred: str, truth: str) -> float:
    pred = re.sub(r"\s+", "", (pred or "").strip())
    truth = re.sub(r"\s+", "", (truth or "").strip())
    if len(truth) == 0:
        return 0.0 if len(pred) == 0 else 1.0
    return round(L.distance(pred, truth) / len(truth), 4)

# ===== OCR ทั้งภาพ + Regex =====
def extract_fields_from_text(text):
    data = {}

    # --- ล้างอักขระแปลก ๆ ---
    text = re.sub(r"[^\u0E00-\u0E7F0-9\s\.\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # =============================
    # 🔹 1. ดึงเลขบัตรประชาชน (รองรับช่องว่าง)
    # =============================
    id_match = re.search(r"(\d\s*){13}", text)
    if id_match:
        d = re.sub(r"\s+", "", id_match.group(0))
        data["id_number"] = d
    else:
        # fallback: หาเลขยาว >= 12
        id_match2 = re.search(r"\d{12,}", text)
        data["id_number"] = id_match2.group(0) if id_match2 else ""

    # =============================
    # 🔹 2. ชื่อ-นามสกุล (OCR เพี้ยน)
    # =============================
    # แก้กรณี OCR เพี้ยน "ไน. สี." = "น.ส."
    text_fixed = re.sub(r"ไน\.?\s*สี\.?", "น.ส.", text)

    name_match = re.search(r"(นาย|นางสาว|นาง|น\.ส\.)\s*([ก-๙]+)\s*([ก-๙]+)", text_fixed)
    if name_match:
        data["prefix"] = name_match.group(1)
        data["first_name"] = name_match.group(2)
        data["last_name"] = name_match.group(3)
    else:
        # fuzzy matching prefix
        cand_prefixes = ["นาย", "นางสาว", "นาง", "น.ส.", "นส", "ไน", "ไน์"]
        prefix_found = ""
        for cand in cand_prefixes:
            if L.ratio(cand, text[:12]) > 0.5:
                prefix_found = "น.ส." if "ส" in cand or "ไ" in cand else cand
                break
        data["prefix"] = prefix_found
        data["first_name"] = ""
        data["last_name"] = ""

    # =============================
    # 🔹 3. วันเกิด (OCR เพี้ยน “ก.ุพ.” → “ก.พ.”)
    # =============================
    text_fixed = re.sub(r"ก\.ุพ\.", "ก.พ.", text_fixed)
    text_fixed = re.sub(r"ก\.ุพ", "ก.พ.", text_fixed)

    dob_match = re.search(
        r"(\d{1,2}\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มค|เมษา|พฤษภา|มิถุนา|กรกฎา|สิงหา|กันยา|ตุลา|พฤศจิกา|ธันวา)\s*\d{2,4})",
        text_fixed
    )
    data["dob"] = dob_match.group(1) if dob_match else ""

    # =============================
    # 🔹 4. ที่อยู่
    # =============================
    addr_match = re.search(r"(ที่อยู่|บ้านเลขที่)\s*[:\-]?\s*(.*)", text_fixed)
    if addr_match:
        data["address"] = addr_match.group(2).strip()
    else:
        # fallback: หาคำว่าหมู่/ตำบล/อำเภอ
        addr_fallback = re.search(r"(หมู่|ตำบล|อำเภอ|จังหวัด)[\u0E00-\u0E7F0-9\s/]*", text_fixed)
        data["address"] = addr_fallback.group(0).strip() if addr_fallback else ""

    # =============================
    # 🔹 5. Normalize ทุกฟิลด์
    # =============================
    for k in data:
        data[k] = normalize_pred(k, data[k])

    return data

# ===== ROUTE: /upload_ocr =====
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

    img = cv2.imread(save_path)
    if img is None:
        return jsonify({"error": "Cannot read image"}), 400

    processed = preprocess_gaussian_otsu(img)

    text = pytesseract.image_to_string(
        processed,
        lang="tha",
        config="--oem 3 --psm 6"
    )

    data = extract_fields_from_text(text)

    return jsonify({
        "message": "OCR (whole-image) processed successfully!",
        "filename": filename,
        "raw_text": text,
        "result": data
    })

@ocr_bp.route("/save_ocr", methods=["POST"])
def save_ocr():
    data = request.get_json()

    required = ["filename", "id_number", "prefix", "first_name", "last_name", "dob", "address"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # ✅ OCR เดิม (ก่อนผู้ใช้แก้)
    ocr_prev = OcrResult.query.filter_by(filename=data["filename"]).order_by(OcrResult.id.desc()).first()

    # ✅ บันทึก OCR หลังผู้ใช้แก้ไข
    ocr_result = OcrResult(
        filename=data["filename"],
        id_number=data["id_number"],
        prefix=data["prefix"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        address=data["address"]
    )

    db.session.add(ocr_result)
    db.session.commit()

    # ✅ คำนวณ CER แยกฟิลด์
    fields = ["id_number", "prefix", "first_name", "last_name", "dob", "address"]
    field_cer = {}
    for f in fields:
        pred = getattr(ocr_prev, f) if ocr_prev else ""  # OCR เดิม
        truth = data.get(f, "")                          # ที่ผู้ใช้แก้
        field_cer[f] = compute_cer(pred or "", truth or "")

    cer_avg = round(sum(field_cer.values()) / len(field_cer), 4)

    # ✅ บันทึก CER summary
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
