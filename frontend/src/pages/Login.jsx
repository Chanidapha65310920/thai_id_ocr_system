import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axiosClient from "../api/axiosClient";

export default function Login({ setUser }) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    try {
      const res = await axiosClient.post("/login", form);

      // ✅ เก็บ user ไว้ใน localStorage เพื่อใช้ต่อ (เช่น upload, history)
      localStorage.setItem("user", JSON.stringify(res.data.user));

      // ✅ อัปเดต state หลัก (App.jsx)
      if (setUser) setUser(res.data.user);

      // ✅ แสดงข้อความแล้วไปหน้า upload
      setMsg("Login successful!");
      setTimeout(() => navigate("/upload"), 800);
    } catch (err) {
      setMsg(err.response?.data?.error || "Login failed!");
    }
  };

  return (
    <div className="flex flex-col items-center justify-start min-h-screen pt-10 pb-10 px-6">
    <div className="backdrop-blur-lg bg-white/50 border border-white/30 shadow-xl rounded-3xl p-8 w-full max-w-2xl text-center">
      <h1 className="text-2xl font-bold mb-4">Login</h1>

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          name="email"
          type="email"
          placeholder="Email"
          onChange={handleChange}
          value={form.email}
          className="border p-2 w-full rounded"
          required
        />
        <input
          name="password"
          type="password"
          placeholder="Password"
          onChange={handleChange}
          value={form.password}
          className="border p-2 w-full rounded"
          required
        />
        <button className="bg-green-600 text-white p-2 w-full rounded hover:bg-green-700">
          Login
        </button>
      </form>

      {msg && (
        <p
          className={`mt-3 ${
            msg.includes("success") ? "text-green-600" : "text-red-500"
          }`}
        >
          {msg}
        </p>
      )}
    </div>
    </div>
  );
}
