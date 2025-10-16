import { useState } from "react";
import axiosClient from "../api/axiosClient";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      setMsg("❌ รหัสผ่านไม่ตรงกัน");
      return;
    }

    try {
      const res = await axiosClient.post("/register", {
        username: form.username,
        email: form.email,
        password: form.password,
      });
      setMsg("✅ สมัครสมาชิกสำเร็จ! กำลังเปลี่ยนหน้า...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setMsg(err.response?.data?.error || "❌ เกิดข้อผิดพลาด");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-35 px-8 bg-gradient-to-br from-indigo-200 via-blue-50 to-pink-100">
      <div className="bg-white shadow-xl rounded-2xl p-8 w-full max-w-md border border-gray-100">
        <h2 className="text-3xl font-bold text-center text-indigo-700 mb-6">
          สร้างบัญชีผู้ใช้งาน
        </h2>

        {msg && (
          <p className={`text-center mb-4 ${msg.startsWith("✅") ? "text-green-600" : "text-red-500"}`}>
            {msg}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1 font-medium text-gray-600">ชื่อ-นามสกุลผู้ใช้งาน</label>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-400 outline-none"
              placeholder="เช่น ชนิดาภา สร้อยพูล"
              required
            />
          </div>

          <div>
            <label className="block mb-1 font-medium text-gray-600">อีเมล (สำหรับเข้าสู่ระบบ)</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-400 outline-none"
              placeholder="example@email.com"
              required
            />
          </div>

          <div>
            <label className="block mb-1 font-medium text-gray-600">รหัสผ่าน</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-400 outline-none"
              required
            />
          </div>

          <div>
            <label className="block mb-1 font-medium text-gray-600">ยืนยันรหัสผ่านอีกครั้ง</label>
            <input
              type="password"
              name="confirmPassword"
              value={form.confirmPassword}
              onChange={handleChange}
              className="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-400 outline-none"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg font-semibold transition"
          >
            สมัครสมาชิก
          </button>

          <p className="text-center text-sm text-gray-500 mt-2">
            มีบัญชีอยู่แล้วใช่ไหม?{" "}
            <a href="/login" className="login-link">
              คลิกเพื่อเข้าสู่ระบบ
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
