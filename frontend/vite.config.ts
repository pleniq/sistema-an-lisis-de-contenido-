import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El backend del Laboratorio corre en 8010 (el 8000 lo usa otro proyecto local).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8010" } },
});
