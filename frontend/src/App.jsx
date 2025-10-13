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
          <div className="mt-24 p-24 flex flex-col items-center justify-start min-h-screen w-full max-w-8xl mx-auto">
            <h1 className="text-4xl font-bold mb-6">🎯 Thai ID OCR System</h1>
            {user ? (
              <p className="text-lg">
                ยินดีต้อนรับ, <b>{user.username}</b>!
              </p>
            ) : (
              <div className="text-center">
                <p className="text-lg mb-6">
                  กรุณาเข้าสู่ระบบเพื่อใช้งานระบบ OCR
                </p>
                <div className="flex justify-center gap-4">
                  <Link
                    to="/login"
                    className="bg-blue-300 text-white px-6 py-3 rounded hover:bg-blue-500 transition"
                  >
                    🔑 Login
                  </Link>
                  <Link
                    to="/register"
                    className="bg-green-300 text-white px-6 py-3 rounded hover:bg-green-500 transition"
                  >
                    📝 Register
                  </Link>
                </div>
              </div>
            )}
          </div>
        }
      />
    </Routes>
  </Router>
);
}
