import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [cerDetails, setCerDetails] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // 📦 โหลดประวัติ OCR
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      setMsg("❌ กรุณาเข้าสู่ระบบก่อนดูประวัติ");
      setLoading(false);
      return;
    }

    axiosClient
      .get(`/get_ocr_history/${user.id}`)
      .then((res) => {
        setHistory(res.data.history);
        setLoading(false);
      })
      .catch((err) => {
        console.error("❌ Error while fetching history:", err);
        setMsg(err.response?.data?.error || "เกิดข้อผิดพลาดในการโหลดข้อมูล");
        setLoading(false);
      });
  }, []);

  // 📥 Export CSV เฉพาะรายการหลังแก้ไขแล้ว
  const handleExportFinal = () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      alert("❌ กรุณาเข้าสู่ระบบก่อนดาวน์โหลดข้อมูล");
      return;
    }
    window.open(`http://127.0.0.1:5000/export_csv_final/${user.id}`, "_blank");
  };

  // 🔍 แสดงรายละเอียด CER ต่อฟิลด์
  const handleShowCER = async (ocrId) => {
    console.log("🔹 ocrId ที่ส่งไปหา backend:", ocrId);
    try {
      const res = await axiosClient.get(`/get_cer_details/${ocrId}`);
      console.log("✅ CER Data:", res.data);
      setCerDetails(res.data);
      setShowModal(true);
    } catch (err) {
      console.error("❌ Error:", err);
      alert("⚠️ ไม่พบข้อมูล CER สำหรับรายการนี้");
    }
  };

  if (loading)
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-gray-600 text-lg">
        ⏳ กำลังโหลดข้อมูล...
      </div>
    );

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-33 px-8 bg-gradient-to-br from-indigo-200 via-blue-50 to-pink-100">
      <div className="bg-white/80 backdrop-blur-md shadow-xl rounded-2xl p-6 w-full max-w-6xl border border-gray-100">
        <h1 className="text-3xl font-bold mb-4 text-gray-800 text-center">
          📜 ประวัติการบันทึก OCR
        </h1>

        <div className="flex justify-end mb-4">
          <button
            onClick={handleExportFinal}
            className="text-white px-4 py-2 rounded-lg shadow-md transition-all"
            style={{
              backgroundColor: "#16a34a",
            }}
            onMouseEnter={(e) => (e.target.style.backgroundColor = "#15803d")} // hover bg-green-700
            onMouseLeave={(e) => (e.target.style.backgroundColor = "#16a34a")}
          >
            📥 ดาวน์โหลดข้อมูล (CSV)
          </button>
        </div>

        {msg && <p className="text-red-500 mb-4 text-center">{msg}</p>}

        {history.length === 0 ? (
          <p className="text-center text-gray-500 text-lg">
            ยังไม่มีข้อมูลบันทึก
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm text-gray-700 shadow-sm rounded-xl overflow-hidden">
              <thead className="bg-gradient-to-r from-indigo-500 to-blue-500 text-white text-center">
                <tr>
                  <th className="py-3 px-2">#</th>
                  <th className="py-3 px-2">ไฟล์</th>
                  <th className="py-3 px-4">เลขบัตรประชาชน</th>
                  <th className="py-3 px-4">ชื่อ-นามสกุล</th>
                  <th className="py-3 px-2">วันเกิด</th>
                  <th className="py-3 px-2">ที่อยู่</th>
                  <th className="py-3 px-2">สถานะ</th>
                  <th className="py-3 px-2">CER เฉลี่ย</th>
                  <th className="py-3 px-2">CER ต่อฟิลด์</th>
                  <th className="py-3 px-2">วันที่บันทึก</th>
                </tr>
              </thead>

              <tbody>
                {history.map((item, i) => (
                  <tr
                    key={item.id}
                    className={`text-center transition-all ${
                      item.is_draft
                        ? "bg-gray-50 hover:bg-gray-100"
                        : "bg-green-50 hover:bg-green-100"
                    }`}
                  >
                    <td className="py-4 border-b">{i + 1}</td>
                    <td className="py-4 border-b font-medium text-indigo-700">
                      {item.filename}
                    </td>
                    <td className="py-4 border-b">{item.id_number}</td>
                    <td className="py-4 border-b">
                      {item.prefix} {item.first_name} {item.last_name}
                    </td>
                    <td className="py-4 border-b">{item.dob}</td>
                    <td className="py-4 border-b text-left px-4">
                      {item.address}
                    </td>
                    <td
                      className={`py-4 border-b font-semibold ${
                        item.is_draft ? "text-gray-500" : "text-green-600"
                      }`}
                    >
                      {item.is_draft ? "🧾 ก่อนแก้ไข" : "✅ หลังแก้ไข"}
                    </td>

                    {/* ✅ ช่อง CER เฉลี่ย */}
                    <td className="py-4 border-b text-center">
                      {item.cer_avg !== null ? item.cer_avg.toFixed(4) : "-"}
                    </td>

                    {/* ✅ ปุ่มดู CER ต่อฟิลด์ */}
                    <td className="py-4 border-b text-center">
                      {!item.is_draft && (
                        <button
                          onClick={() => handleShowCER(item.id)}
                          className="px-3 py-1 text-xs bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg shadow-sm transition-all"
                        >
                          🔍
                        </button>
                      )}
                    </td>

                    <td className="py-4 border-b">{item.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ✅ Modal Popup แสดง CER รายฟิลด์ */}
      {showModal && cerDetails && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-50">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-2xl p-6 w-[90%] max-w-md relative">
            <h2 className="text-lg font-semibold mb-4 text-gray-800 text-center">
              📊 รายละเอียด CER ต่อฟิลด์
            </h2>

            <table className="w-full text-sm text-gray-700">
              <tbody>
                <tr>
                  <td>เลขบัตรประชาชน:</td>
                  <td className="text-right">{cerDetails.id_number_cer}</td>
                </tr>
                <tr>
                  <td>คำนำหน้า:</td>
                  <td className="text-right">{cerDetails.prefix_cer}</td>
                </tr>
                <tr>
                  <td>ชื่อ:</td>
                  <td className="text-right">{cerDetails.first_name_cer}</td>
                </tr>
                <tr>
                  <td>นามสกุล:</td>
                  <td className="text-right">{cerDetails.last_name_cer}</td>
                </tr>
                <tr>
                  <td>วันเกิด:</td>
                  <td className="text-right">{cerDetails.dob_cer}</td>
                </tr>
                <tr>
                  <td>ที่อยู่:</td>
                  <td className="text-right">{cerDetails.address_cer}</td>
                </tr>
                <tr className="font-semibold border-t">
                  <td>CER เฉลี่ยรวม:</td>
                  <td className="text-right text-indigo-700">
                    {cerDetails.cer_avg}
                  </td>
                </tr>
              </tbody>
            </table>

            <button
              onClick={() => setShowModal(false)}
              className="mt-5 w-full bg-indigo-500 text-white py-2 rounded-xl hover:bg-indigo-600 transition-all"
            >
              ปิด
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
