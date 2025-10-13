import axios from "axios";

// ตั้งค่า baseURL ให้ชี้ไปยัง Flask (backend)
const axiosClient = axios.create({
  baseURL: "http://127.0.0.1:5000",  // Flask รันที่พอร์ต 5000
  headers: {
    "Content-Type": "application/json",
  },
});

export default axiosClient;
