import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [ocrData, setOcrData] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMsg("");
    setOcrData(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setMsg("⚠️ กรุณาเลือกไฟล์ก่อนอัปโหลด");
      return;
    }

    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      setMsg("❌ กรุณาเข้าสู่ระบบก่อนอัปโหลด");
      return;
    }

    setLoading(true);
    setMsg("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", user.id);

    try {
      const res = await axios.post("http://127.0.0.1:5000/upload_ocr", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setOcrData(res.data);
      setMsg("✅ OCR สำเร็จแล้ว! ข้อมูลถูกบันทึกเป็น draft");
    } catch (err) {
      console.error(err);
      setMsg(err.response?.data?.error || "❌ อัปโหลดไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    navigate("/edit", { state: { ocrData } });
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-35 px-8 bg-gradient-to-br from-indigo-200 via-blue-50 to-pink-100">
      <div className="backdrop-blur-lg bg-white/50 border border-white/30 shadow-xl rounded-3xl p-8 w-full max-w-5xl text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">
          📤 อัปโหลดบัตรประชาชน
        </h1>

        <div className="space-y-5">
          <div>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-700 border border-gray-300 rounded-xl cursor-pointer bg-white/60 focus:outline-none focus:ring-2 focus:ring-indigo-400 p-2"
            />
          </div>

          <button
            onClick={handleUpload}
            disabled={loading}
            className={`w-full py-3 rounded-xl font-semibold transition-all shadow-md ${
              loading
                ? "!bg-green-500 !text-white cursor-not-allowed hover:!bg-green-700 hover:scale-[1.02]"
                : "!bg-blue-400 !text-black hover:!bg-blue-600"
            }`}
          >
            {loading ? "⏳ กำลังประมวลผล..." : "📎 ประมวลผล"}
          </button>



          {msg && (
            <p
              className={`text-sm font-medium ${
                msg.startsWith("✅")
                  ? "text-green-600"
                  : msg.startsWith("⚠️")
                  ? "text-yellow-600"
                  : "text-red-500"
              }`}
            >
              {msg}
            </p>
          )}

          {ocrData && (
  <div className="mt-8 flex flex-col md:flex-row gap-8 items-start text-left">
    {/* ✅ ฝั่งซ้าย: รูปที่ประมวลผล */}
    {ocrData.processed_image_path && (
      <div className="flex-1 flex justify-center">
        <img
          src={`http://127.0.0.1:5000/${ocrData.processed_image_path}`}
          alt="Processed ID"
          className="rounded-xl shadow-lg border border-gray-200 max-h-96 object-contain"
        />
      </div>
    )}

    {/* ✅ ฝั่งขวา: ข้อมูล OCR */}
    <div className="flex-1">
      <h2 className="text-lg font-semibold mb-2 text-gray-700">
        ผลลัพธ์ OCR:
      </h2>
      <pre className="bg-gray-100/70 border border-gray-200 p-3 rounded-lg text-sm overflow-x-auto max-h-96 overflow-y-auto">
        {JSON.stringify(ocrData.result, null, 2)}
      </pre>
      <button
        onClick={handleEdit}
        className="mt-4 w-full py-2 rounded-xl bg-green-500 text-white font-semibold hover:bg-green-700 transition-all shadow-md hover:scale-[1.02]"
      >
        ✏️ แก้ไขข้อมูล
      </button>
    </div>
  </div>
)}

        </div>
      </div>
    </div>
  );
}
