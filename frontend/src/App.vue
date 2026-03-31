<template>
  <router-view />
</template>

<script setup lang="ts">
  import { onMounted } from "vue";

  import { useSettings } from "./composables/useSettings";

  const ROOT_FONT_SIZE_MAP: Record<string, string> = {
    sm: "14px",
    md: "16px",
    lg: "18px",
  };

  const { hydrate, get } = useSettings();

  onMounted(async () => {
    await hydrate();
    const size = get("interface", "uiFontSize", "md");
    document.documentElement.style.fontSize =
      ROOT_FONT_SIZE_MAP[size] ?? "16px";
  });
</script>
