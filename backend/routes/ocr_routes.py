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
from flask import send_file
import csv
import io

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

    # --- Clean up unwanted chars ---
    text = re.sub(r"[^\u0E00-\u0E7F0-9\s\.\/\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # =============================
    # 🔹 1. หมายเลขบัตรประชาชน
    # =============================
    id_match = re.search(r"\b[1-8]\s?[0-9]{4}\s?[0-9]{5}\s?[0-9]{2}\s?[0-9]\b", text)
    if id_match:
        data["id_number"] = re.sub(r"\s+", "", id_match.group(0))
    else:
        id_match2 = re.search(r"\d{12,}", text)
        data["id_number"] = id_match2.group(0) if id_match2 else ""

    # =============================
    # 🔹 2. ใช้ NER หาคำนำหน้า / ชื่อ / นามสกุล (พร้อม fallback)
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
    # 🔹 4. ที่อยู่ (ปรับปรุงใหม่ - กลยุทธ์ "นักสืบหาชิ้นส่วน")
    # =============================
    address = ""
    text_for_addr = re.sub(r"\s+", " ", text) 
    
    # --- Step 1: หา Anchor "ที่อยู่" เพื่อกำหนดพื้นที่ค้นหา ---
    address_anchor = "ที่อยู่"
    best_match_ratio = 0.6
    best_match_start_index = -1

    tokens = text_for_addr.split()
    for token in tokens:
        # ใช้ Fuzzy matching หาคำที่คล้าย "ที่อยู่" ที่สุด
        ratio = L.ratio(token, address_anchor)
        if ratio > best_match_ratio:
            best_match_ratio = ratio
            best_match_start_index = text_for_addr.find(token)
            
    # --- Step 2: ถ้าเจอ Anchor, สร้าง "หน้าต่างค้นหา" และเริ่มตามล่าชิ้นส่วน ---
    if best_match_start_index != -1:
        # กำหนดหน้าต่างค้นหาประมาณ 150 ตัวอักษรหลัง Anchor
        search_window = text_for_addr[best_match_start_index : best_match_start_index + 150]
        
        # --- เตรียมข้อมูลในหน้าต่าง: แก้คำผิดที่เจอบ่อย ---
        search_window = search_window.replace("หม่ที", "หมู่ที่").replace("ด.", "ต.").replace("ทบคลอ", "ทับคล้อ")

        # --- ตามล่าหาแต่ละชิ้นส่วนด้วย Regex เฉพาะทาง ---
        house_no_match = re.search(r"\d+[\/\d-]*", search_window)
        moo_match = re.search(r"(?:หมู่ที่|หมู่ที|หมู่|ม\.)\s*\d+", search_window)
        tambon_match = re.search(r"(?:ต\.?|ตำบล|แขวง)\s*[\u0E00-\u0E7F]+", search_window)
        amphoe_match = re.search(r"(?:อ\.|อำเภอ)\s*[\u0E00-\u0E7F]+", search_window)
        province_match = re.search(r"(?:จ\.?|จังหวัด)\s*[\u0E00-\u0E7F]+", search_window)
        
        # --- Step 3: ประกอบร่างชิ้นส่วนที่หาเจอ ---
        address_parts = []
        if house_no_match:
            address_parts.append(house_no_match.group(0))
        if moo_match:
            address_parts.append(moo_match.group(0))
        if tambon_match:
            address_parts.append(tambon_match.group(0))
        if amphoe_match:
            address_parts.append(amphoe_match.group(0))
        if province_match:
            # นำผลลัพธ์ของจังหวัดมาตัดคำว่า "จังหวัด" หรือ "จ." ซ้ำซ้อนออก
            clean_province = province_match.group(0).replace("จังหวัด", "จ.").strip()
            address_parts.append(clean_province)
            
        # รวมทุกชิ้นส่วนและทำความสะอาดครั้งสุดท้าย
        address = " ".join(address_parts)
        address = re.sub(r"\s+", " ", address).strip()

    data["address"] = address

    # =============================
    # 🔹 5. Normalize ทุกฟิลด์
    # =============================
    for k in data:
        data[k] = normalize_pred(k, data[k])

    return data

# ====== /upload_ocr ======
# ====== /upload_ocr ======
@ocr_bp.route("/upload_ocr", methods=["POST"])
def upload_ocr():
    file = request.files.get("file")
    user_id = request.form.get("user_id")  # ✅ ดึง user_id จาก frontend

    # 🔹 แปลง user_id จาก string → int
    try:
        user_id = int(user_id) if user_id else None
    except ValueError:
        user_id = None

    # 🔹 Debug ดูค่าที่ Flask ได้รับ
    print(f"[DEBUG] /upload_ocr: user_id={user_id}, type={type(user_id)}")

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

    # ✅ สร้าง Draft Record (เก็บ OCR ดิบก่อนแก้)
    from database.models import OcrResult
    ocr_draft = OcrResult(
        user_id=user_id,
        filename=filename,
        original_image_path=f"uploads/{filename}",
        processed_image_path=f"uploads/processed_{filename}",
        id_number=data.get("id_number"),
        prefix=data.get("prefix"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        dob=data.get("dob"),
        address=data.get("address"),
        is_draft=bool(True),  # ✅ เก็บสถานะเป็น Draft
    )
    db.session.add(ocr_draft)
    db.session.commit()

    return jsonify({
        "message": "OCR (Gaussian + EasyOCR) processed successfully!",
        "filename": filename,
        "raw_text": text,
        "processed_image_path": os.path.join("uploads", f"processed_{filename}"),
        "result": data
    })


# ====== /save_ocr ======
@ocr_bp.route("/save_ocr", methods=["POST"])
def save_ocr():
    data = request.get_json()

    # ✅ ตรวจสอบข้อมูลที่จำเป็น
    required = ["filename", "id_number", "prefix", "first_name", "last_name", "dob", "address", "user_id"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    filename = data["filename"]
    user_id = data["user_id"]

    # ✅ หา draft (ผล OCR ดิบก่อนแก้) ที่ยังไม่ปิด
    draft = (
        OcrResult.query
        .filter_by(user_id=user_id, filename=filename, is_draft=True)
        .order_by(OcrResult.id.desc())
        .first()
    )

    # ✅ สร้างบันทึกใหม่ (ผลที่ผู้ใช้แก้ไขแล้ว)
    ocr_result = OcrResult(
        user_id=user_id,
        filename=filename,
        original_image_path=f"uploads/{filename}",
        processed_image_path=f"uploads/processed_{filename}",
        id_number=data["id_number"],
        prefix=data["prefix"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        dob=data["dob"],
        address=data["address"],
        is_draft=False,  # ✅ อันนี้คือผลจริง ไม่ใช่ draft
    )
    db.session.add(ocr_result)
    db.session.commit()

    # ✅ คำนวณ CER เทียบกับ draft (baseline)
    fields = ["id_number", "prefix", "first_name", "last_name", "dob", "address"]
    field_cer = {}

    for f in fields:
        pred = getattr(draft, f) if draft else ""   # baseline = draft
        truth = data.get(f, "")
        field_cer[f] = compute_cer(pred or "", truth or "")

    cer_avg = round(sum(field_cer.values()) / len(field_cer), 4)

    # ✅ บันทึกผล CER ลงตาราง cer_results
    cer_summary = CerResult(
        ocr_result_id=ocr_result.id,
        filename=filename,
        cer_id_number=field_cer["id_number"],
        cer_prefix=field_cer["prefix"],
        cer_first_name=field_cer["first_name"],
        cer_last_name=field_cer["last_name"],
        cer_dob=field_cer["dob"],
        cer_address=field_cer["address"],
        cer_avg=cer_avg,
    )
    db.session.add(cer_summary)

    # ✅ ปิดสถานะ draft (ไม่ให้ใช้ซ้ำ)
    # if draft:
    #     draft.is_draft = False

    db.session.commit()

    return jsonify({
        "message": "OCR + CER summary saved successfully!",
        "filename": filename,
        "ocr_result_id": ocr_result.id,
        "cer_avg": cer_avg,
        "fields_cer": field_cer,
        "saved_data": data,
        "processed_image_path": f"uploads/processed_{filename}",
        "original_image_path": f"uploads/{filename}"
    })


# ====== /get_ocr_history ======

@ocr_bp.route("/get_ocr_history/<int:user_id>", methods=["GET"])
def get_ocr_history(user_id):
    """ดึงประวัติผล OCR ของผู้ใช้ — เรียงไฟล์เดียวกันให้อยู่คู่กัน (draft ก่อน ผลจริงทีหลัง)"""
    results = (
        OcrResult.query
        .filter_by(user_id=user_id)
        .order_by(OcrResult.filename.asc(), OcrResult.is_draft.desc(), OcrResult.created_at.asc())
        .all()
    )

    data = []
    for r in results:
        cer = (
            CerResult.query.filter_by(ocr_result_id=r.id)
            .order_by(CerResult.id.desc())
            .first()
        )
        data.append({
            "id": r.id,
            "filename": r.filename,
            "id_number": r.id_number,
            "id_number": r.id_number,
            "prefix": r.prefix,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "dob": r.dob,
            "address": r.address,
            "is_draft": r.is_draft,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "cer_avg": cer.cer_avg if cer else None
        })

    # ✅ จัดเรียงซ้ำใน Python เพื่อความชัวร์
    data.sort(key=lambda x: (x["filename"].lower(), 1 if x["is_draft"] else 2))

    return jsonify({"history": data})


@ocr_bp.route("/export_csv_final/<int:user_id>", methods=["GET"])
def export_csv_final(user_id):
    try:
        # ✅ ดึงเฉพาะข้อมูลหลังแก้ไขแล้ว (is_draft = 'Final')
        results = (
            OcrResult.query
            .filter(OcrResult.user_id == user_id, OcrResult.is_draft == "Final")
            .order_by(OcrResult.created_at.desc())
            .all()
        )

        if not results:
            return jsonify({"error": "ไม่พบข้อมูลที่ผ่านการแก้ไขแล้ว"}), 404

        # ✅ สร้างไฟล์ CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header ภาษาไทย
        writer.writerow(["เลขบัตรประชาชน", "ชื่อ-นามสกุล", "วันเกิด", "ที่อยู่"])

        for r in results:
            full_name = f"{r.prefix or ''}{r.first_name or ''} {r.last_name or ''}".strip()
            writer.writerow([
                r.id_number or "",
                full_name,
                r.dob or "",
                r.address or "",
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"ผลลัพธ์OCR_user_{user_id}.csv"
        )

    except Exception as e:
        print("[ERROR /export_csv_final]", e)
        return jsonify({"error": "ไม่สามารถสร้างไฟล์ CSV ได้"}), 500



@ocr_bp.route("/get_cer_details/<int:ocr_id>", methods=["GET"])
def get_cer_details(ocr_id):
    try:
        cer_result = CerResult.query.filter_by(ocr_result_id=ocr_id).first()
        if not cer_result:
            return jsonify({"error": "ไม่พบข้อมูล CER สำหรับรายการนี้"}), 404

        data = {
    "id_number_cer": cer_result.cer_id_number,
    "prefix_cer": cer_result.cer_prefix,
    "first_name_cer": cer_result.cer_first_name,
    "last_name_cer": cer_result.cer_last_name,
    "dob_cer": cer_result.cer_dob,
    "address_cer": cer_result.cer_address,
    "cer_avg": round(cer_result.cer_avg or 0, 4),
}


        return jsonify(data), 200

    except Exception as e:
        print("[ERROR /get_cer_details]", e)
        return jsonify({"error": "เกิดข้อผิดพลาดภายในเซิร์ฟเวอร์"}), 500
