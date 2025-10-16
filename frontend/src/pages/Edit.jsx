import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import axiosClient from "../api/axiosClient";

export default function Edit() {
  const location = useLocation();
  const navigate = useNavigate();
  const { ocrData } = location.state || {};

  const [form, setForm] = useState(ocrData?.result || {});
  const [msg, setMsg] = useState("");
  const user = JSON.parse(localStorage.getItem("user"));

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    if (!user) {
      setMsg("❌ กรุณาเข้าสู่ระบบก่อนบันทึก");
      return;
    }

    try {
      const res = await axiosClient.post("/save_ocr", {
        user_id: user.id,
        filename: ocrData.filename,
        id_number: form.id_number,
        prefix: form.prefix,
        first_name: form.first_name,
        last_name: form.last_name,
        dob: form.dob,
        address: form.address,
      });

      setMsg(`✅ บันทึกสำเร็จ (CER avg: ${res.data.cer_avg})`);
      setTimeout(() => navigate("/history"), 1200);
    } catch (err) {
      console.error(err);
      setMsg(err.response?.data?.error || "เกิดข้อผิดพลาดในการบันทึก");
    }
  };

  if (!ocrData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-100 to-blue-50">
        <p className="text-red-500 font-medium">❌ ไม่พบข้อมูล OCR</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-30 px-8 bg-gradient-to-br from-indigo-200 via-blue-50 to-pink-100">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-6xl backdrop-blur-lg bg-white/60 border border-white/30 rounded-3xl shadow-2xl p-8">
        
        {/* ===== LEFT: IMAGE PREVIEW ===== */}
<div className="flex flex-col items-center justify-center">
  <h2 className="text-xl font-semibold text-gray-700 mb-4">
    🖼️ ภาพที่ประมวลผลแล้ว
  </h2>
  <div className="w-full h-[380px] flex items-center justify-center bg-gray-100/70 border border-gray-300 rounded-2xl overflow-hidden shadow-inner">
    {ocrData.processed_image_path ? (
      <img
        src={`http://127.0.0.1:5000/${ocrData.processed_image_path}`}
        alt="Processed"
        className="object-contain max-h-[360px]"
      />
    ) : (
      <p className="text-gray-500">ไม่มีภาพแนบจากการประมวลผล</p>
    )}
  </div>
</div>


        {/* ===== RIGHT: FORM ===== */}
        <div>
          <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
            📝 แก้ไขข้อมูล OCR
          </h1>

          <div className="space-y-2">
            {Object.entries(form).map(([key, value]) => (
              <div key={key} className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1 capitalize">
                  {key.replaceAll("_", " ")}
                </label>
                <input
                  name={key}
                  value={value || ""}
                  onChange={handleChange}
                  className="border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-400 outline-none bg-white/80 shadow-sm hover:shadow-md transition-all"
                />
              </div>
            ))}
          </div>

          <button
            onClick={handleSave}
            className="mt-8 w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md hover:scale-[1.02] transition-all"
          >
            💾 บันทึกลงฐานข้อมูล
          </button>

          {msg && (
            <p
              className={`mt-4 text-center font-medium ${
                msg.startsWith("✅") ? "text-green-600" : "text-red-500"
              }`}
            >
              {msg}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
