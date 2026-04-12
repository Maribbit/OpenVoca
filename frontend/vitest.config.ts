import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import path from "path";
import { readFileSync } from "fs";

const version = readFileSync(
  path.resolve(__dirname, "../VERSION"),
  "utf-8",
).trim();

export default defineConfig({
  plugins: [vue() as any],
  define: {
    __APP_VERSION__: JSON.stringify(version),
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
