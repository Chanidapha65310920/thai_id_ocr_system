import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import "./Navbar.css";

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
        <Link to="/" className="logo">
          <i className="icon-feather"></i>
          <span>Thai ID OCR</span>
        </Link>
      </div>

      <div className="navbar-center">
        <ul className="menu">
          <li className={`menu-item ${isActive("/upload") ? "active" : ""}`}>
            <Link to="/upload">📩 Upload</Link>
          </li>
          {/* <li className={`menu-item ${isActive("/edit") ? "active" : ""}`}>
            <Link to="/edit">✏️ Edit</Link>
          </li> */}
          <li className={`menu-item ${isActive("/history") ? "active" : ""}`}>
            <Link to="/history">🧾 History</Link>
          </li>
        </ul>
      </div>

      <div className="navbar-right">
        {user && (
          <button onClick={handleLogoutClick} className="logout-button">
            👋 Logout
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
