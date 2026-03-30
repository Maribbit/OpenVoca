<template>
  <router-view />
</template>

<script setup lang="ts">
  import { onMounted } from "vue";

  type UiFontSizeOption = "sm" | "md" | "lg";

  const UI_FONT_SIZE_KEY = "openvoca.ui.fontSize";

  const ROOT_FONT_SIZE_MAP: Record<UiFontSizeOption, string> = {
    sm: "14px",
    md: "16px",
    lg: "18px",
  };

  function loadUiFontSize(): UiFontSizeOption {
    if (typeof window === "undefined") return "md";
    const saved = window.localStorage.getItem(UI_FONT_SIZE_KEY);
    if (saved === "sm" || saved === "md" || saved === "lg") return saved;
    return "md";
  }

  onMounted(() => {
    document.documentElement.style.fontSize =
      ROOT_FONT_SIZE_MAP[loadUiFontSize()];
  });
</script>
