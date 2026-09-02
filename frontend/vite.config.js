import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 開發時把 /api 代理到後端 FastAPI。
// 後端位址預設 http://localhost:8000,可用環境變數 VITE_API_TARGET 覆寫,
// 方便與其他系統並存時改用別的埠(例:http://localhost:8001)。
const API_TARGET = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": API_TARGET,
    },
  },
});
