import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/council": "http://127.0.0.1:8080",
      "/ledger":  "http://127.0.0.1:8080",
      "/ticker":  "http://127.0.0.1:8080",
      "/watchlist": "http://127.0.0.1:8080",
      "/integrations": "http://127.0.0.1:8080",
      "/oauth":   "http://127.0.0.1:8080",
      "/config":  "http://127.0.0.1:8080",
      "/health":  "http://127.0.0.1:8080",
      "/static":  "http://127.0.0.1:8080",
    },
  },
  build: {
    outDir: "../src/apex_ledger/web/dist",
    emptyOutDir: true,
  },
});
