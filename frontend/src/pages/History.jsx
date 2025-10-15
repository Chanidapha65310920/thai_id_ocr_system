import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

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


  const handleExportFinal = () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) {
      alert("❌ กรุณาเข้าสู่ระบบก่อนดาวน์โหลดข้อมูล");
      return;
    }
    // เปิดลิงก์ไปยัง backend เพื่อดาวน์โหลด CSV
    window.open(`http://127.0.0.1:5000/export_csv_final/${user.id}`, "_blank");
  };

  if (loading)
    return (
      <div className="flex justify-center items-center min-h-screen text-gray-600 text-lg">
        ⏳ กำลังโหลดข้อมูล...
      </div>
    );

  return (
    <div className="mt-5 p-6 flex flex-col items-center justify-start min-h-screen w-full max-w-8xl mx-auto">

      <div className="bg-white/80 backdrop-blur-md shadow-xl rounded-2xl p-4 w-full max-w-6xl border border-gray-100">
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
          <p className="text-center text-gray-500 text-lg">ยังไม่มีข้อมูลบันทึก</p>
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
                    <td className="py-6 border-b">{i + 1}</td>
                    <td className="py-6 border-b font-medium text-indigo-700">
                      {item.filename}
                    </td>
                    <td className="py-6 border-b">{item.id_number}</td>
                    <td className="py-6 border-b">
                      {item.prefix} {item.first_name} {item.last_name}
                    </td>
                    <td className="py-6 border-b">{item.dob}</td>
                    <td className="py-6 border-b text-left px-4">{item.address}</td>
                    <td
                      className={`py-6 border-b font-semibold ${
                        item.is_draft ? "text-gray-500" : "text-green-600"
                      }`}
                    >
                      {item.is_draft ? "🧾 ก่อนแก้ไข" : "✅ หลังแก้ไข"}
                    </td>
                    <td className="py-6 border-b text-center">
                      {item.cer_avg !== null ? item.cer_avg.toFixed(4) : "-"}
                    </td>
                    <td className="py-6 border-b">{item.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
