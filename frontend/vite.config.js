import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 開發時把 /api 代理到後端 FastAPI(預設 8000 埠)
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
