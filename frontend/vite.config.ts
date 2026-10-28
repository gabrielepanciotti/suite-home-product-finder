import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev su 3342; le chiamate /api/* sono proxate al backend FastAPI.
// Il target è configurabile via VITE_BACKEND_PROXY_TARGET (usato dal frontend
// containerizzato per puntare al service backend); fallback al backend nativo.
const backendProxyTarget =
  process.env.VITE_BACKEND_PROXY_TARGET || "http://localhost:10008";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3342,
    proxy: {
      "/api": backendProxyTarget,
    },
  },
});
