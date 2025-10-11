import re
import Levenshtein as L

# --- แปลงเลขไทย / ตัวอักษรคล้ายเลข ---
DIGIT_FIX = str.maketrans({
    'l':'1','I':'1','|':'1','O':'0','o':'0','B':'8','S':'5'
})
TH_NUM = str.maketrans('๐๑๒๓๔๕๖๗๘๙','0123456789')

# --- ตรวจสอบบัตรประชาชน ---
def th_id_valid(d13):
    if len(d13)!=13 or not d13.isdigit():
        return False
    s = sum(int(d13[i])*(13-i) for i in range(12))
    return (11 - s % 11) % 10 == int(d13[-1])

# --- แก้กรณีพิมพ์ผิด 1 หลัก ---
def th_id_fix_one_digit(d):
    if len(d)!=13 or not d.isdigit():
        return d
    for i in range(13):
        orig = d[i]
        for k in "0123456789":
            if k==orig: continue
            cand = d[:i]+k+d[i+1:]
            if th_id_valid(cand):
                return cand
    return d

# --- Normalize ---
def fix_digits(s):
    s = s.translate(TH_NUM).translate(DIGIT_FIX)
    return re.sub(r'[^0-9]', '', s)

def normalize_name(text):
    toks = re.findall(r'[ก-๙]{2,}', text)
    return max(toks, key=len) if toks else ""

MONTH_VARIANTS = {
    'มค':'ม.ค.','กพ':'ก.พ.','มีค':'มี.ค.','เมย':'เม.ย.','พค':'พ.ค.',
    'มิย':'มิ.ย.','กค':'ก.ค.','สค':'ส.ค.','กย':'ก.ย.','ตค':'ต.ค.','พย':'พ.ย.','ธค':'ธ.ค.'
}

def normalize_date_th(text):
    s = text.translate(TH_NUM)
    s = re.sub(r'[^0-9ก-๙\. ]',' ', s)
    s = re.sub(r'\s+',' ', s).strip()
    for k,v in MONTH_VARIANTS.items():
        s = re.sub(k, v, s)
    m = re.search(r'(\d{1,2})\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s*(\d{2,4})', s)
    if not m:
        return s.strip()
    dd, mon, yy = m.groups()
    yy = yy if len(yy)==4 else ('25'+yy.zfill(2))
    return f"{int(dd)} {mon} {yy}"

def normalize_address(text):
    s = text.translate(TH_NUM).translate(DIGIT_FIX)
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'[^\w\s\.\-ก-๙/]', ' ', s)
    return s.strip()

CAND_PREFIX = ["นาย","นาง","น.ส."]

def fix_prefix(text):
    p = re.sub(r'\s+', '', text)
    if not p:
        return ""
    if p in ["นาย", "นาง", "น.ส", "น.ส."]:
        return "น.ส." if "ส" in p else p
    best = min(CAND_PREFIX, key=lambda c: L.distance(p, c))
    return best

# --- รวมทั้งหมดไว้ในฟังก์ชันหลัก ---
def normalize_pred(field, text):
    text = (text or "").strip()
    if field == "id_number":
        d = fix_digits(text)
        d = (d + "0000000000000")[:13]
        if not th_id_valid(d):
            d = th_id_fix_one_digit(d)
        return d
    if field == "prefix":
        return fix_prefix(text)
    if field in ("first_name","last_name"):
        return normalize_name(text)
    if field == "dob":
        return normalize_date_th(text)
    if field == "address":
        return normalize_address(text)
    return text
