import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import "./Navbar.css";
import logo from "../assets/logo.png";

const Navbar = ({ onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogoutClick = () => {
    localStorage.removeItem("user");
    if (onLogout) onLogout();
    navigate("/");
  };

  const isActive = (path) => location.pathname === path;
  const user = localStorage.getItem("user");

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/" className="logo flex items-center gap-2">
          <img
            src={logo}
            alt="Thai ID OCR Logo"
            className="h-14 w-auto object-contain"
          />
          <span className="font-semibold text-lg">Thai ID OCR</span>
        </Link>
      </div>

      <div className="navbar-center">
        <ul className="menu">
          <li className={`menu-item ${isActive("/upload") ? "active" : ""}`}>
            <Link to="/upload">📩 อัปโหลด</Link>
          </li>
          {/* <li className={`menu-item ${isActive("/edit") ? "active" : ""}`}>
            <Link to="/edit">✏️ Edit</Link>
          </li> */}
          <li className={`menu-item ${isActive("/history") ? "active" : ""}`}>
            <Link to="/history">🧾 ประวัติ</Link>
          </li>
        </ul>
      </div>

      <div className="navbar-right">
        {user && (
          <button onClick={handleLogoutClick} className="logout-button">
            👋 ออกจากระบบ
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
