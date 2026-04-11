<template>
  <router-view />
</template>

<script setup lang="ts">
  import { onMounted } from "vue";

  import { useSettings } from "./composables/useSettings";

  const UI_ZOOM_MAP: Record<string, string> = {
    xs: "0.9",
    sm: "1",
    md: "1.25",
    lg: "1.4",
    xl: "1.5",
  };

  const { hydrate, get } = useSettings();

  onMounted(async () => {
    await hydrate();
    const size = get("interface", "uiFontSize", "sm");
    const appEl = document.getElementById("app");
    if (appEl) {
      const zoomVal = UI_ZOOM_MAP[size] ?? "1";
      appEl.style.zoom = zoomVal;
      appEl.style.setProperty("--app-zoom", zoomVal);
    }
    const colorTheme = get("interface", "colorTheme", "default");
    if (colorTheme !== "default") {
      document.documentElement.setAttribute("data-color-theme", colorTheme);
    }
  });
</script>
