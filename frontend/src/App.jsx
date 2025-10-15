import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Upload from "./pages/Upload";
import Edit from "./pages/Edit";
import History from "./pages/History";
import Navbar from "./components/Navbar";

export default function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogout = () => {
    const confirmLogout = window.confirm("คุณแน่ใจหรือไม่ว่าจะออกจากระบบ?");
    if (!confirmLogout) return; // ❌ ถ้ากดยกเลิก ก็หยุดตรงนี้

    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <Router>
      <Navbar onLogout={handleLogout} />

      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login setUser={setUser} />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/edit" element={<Edit />} />
        <Route path="/history" element={<History />} />
        <Route
          path="/"
          element={
            <div className="min-h-screen flex flex-col items-center justify-start pt-20 px-8 to-white">
              <div className="text-center max-w-4xl">
                <h1 className="text-5xl font-bold mb-4 text-blue-600 drop-shadow-sm">
                  🎯 Thai ID OCR System
                </h1>
                <p className="text-gray-600 text-lg mb-10">
                  ระบบสกัดข้อมูลบัตรประชาชนไทยอัตโนมัติด้วย OCR + Image
                  Processing
                </p>

                {user ? (
                  <div className="bg-white shadow-lg rounded-2xl p-8 border border-gray-100">
                    <h2 className="text-xl mb-4">
                      👋 ยินดีต้อนรับ, <b>{user.username}</b>
                    </h2>
                    <p className="text-gray-600 mb-6">
                      เลือกเมนูด้านบนเพื่อเริ่มใช้งานระบบ
                      หรืออัปโหลดรูปภาพของคุณได้ทันที
                    </p>
                    <Link
                      to="/upload"
                      className="bg-blue-400 hover:bg-blue-600 text-white px-6 py-3 rounded-xl shadow-md transition"
                    >
                      📄 ไปที่หน้าอัปโหลด
                    </Link>
                  </div>
                ) : (
                  <div className="bg-white shadow-md rounded-2xl p-10 border border-gray-100">
                    <p className="text-lg mb-6">
                      กรุณาเข้าสู่ระบบเพื่อใช้งานระบบ OCR
                    </p>
                    <div className="flex justify-center gap-6">
                      <Link
                        to="/login"
                        className="bg-blue-500 text-white px-6 py-3 rounded-xl hover:bg-blue-600 shadow transition"
                      >
                        🔑 Login
                      </Link>
                      <Link
                        to="/register"
                        className="bg-green-500 text-white px-6 py-3 rounded-xl hover:bg-green-600 shadow transition"
                      >
                        📝 Register
                      </Link>
                    </div>
                  </div>
                )}
              </div>

              {/* ✅ เพิ่ม Section ด้านล่าง */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full mb-6 mt-10">
                {/* 1. เทคโนโลยีที่ใช้ */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">
                    ⚙️ เทคโนโลยีที่ใช้
                  </h3>
                  <p className="text-gray-600 text-sm">
                    EasyOCR, Gaussian Preprocess, Python, Flask, React, MySQL
                  </p>
                </div>

                {/* 2. ฟีเจอร์ระบบ */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">📋 ฟีเจอร์ระบบ</h3>
                  <p className="text-gray-600 text-sm">
                    สกัดเฉพาะข้อมูล ชื่อ-สกุล ที่อยู่ วันเกิด เลข 13 หลัก อัตโนมัติ
                  </p>
                </div>

                {/* 3. ความแม่นยำสูง */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">
                    📌 ความแม่นยำสูง
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Image Processing ช่วยลด Noise และปรับภาพก่อน OCR
                  </p>
                </div>

                {/* 4. Export ข้อมูล */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">
                    📤 Export ข้อมูลได้จริง
                  </h3>
                  <p className="text-gray-600 text-sm">
                    ดาวน์โหลดผลลัพธ์เป็น CSV เพื่อใช้งานต่อหรือเก็บบันทึก
                  </p>
                </div>

                {/* 5. ความปลอดภัยของข้อมูล */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">
                    🔒 ความปลอดภัยของข้อมูล
                  </h3>
                  <p className="text-gray-600 text-sm">
                    จัดเก็บข้อมูลเฉพาะผู้ใช้ ปลอดภัยและไม่เผยแพร่ภายนอก
                  </p>
                </div>

                {/* 6. รองรับไฟล์ jpg / png */}
                <div className="p-6 bg-white rounded-2xl shadow hover:shadow-lg transition">
                  <h3 className="font-semibold text-lg mb-2">
                    🖼️ รองรับไฟล์ภาพ
                  </h3>
                  <p className="text-gray-600 text-sm">
                    อัปโหลดได้ทั้งไฟล์ .jpg และ .png
                  </p>
                </div>
              </div>
            </div>
          }
        />
      </Routes>
    </Router>
  );
}
