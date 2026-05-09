<template>
  <div
    v-if="update.show && !update.dismissed"
    data-testid="update-banner"
    class="fixed top-0 left-0 right-0 z-50 flex items-center justify-between gap-4 px-4 py-2 text-sm bg-[var(--color-surface)] border-b border-[var(--color-ink)]/10 text-[var(--color-ink)]"
  >
    <span>{{ messages.updateAvailable.replace("{0}", update.version) }}</span>
    <div class="flex items-center gap-3">
      <a
        :href="update.url"
        target="_blank"
        rel="noopener noreferrer"
        class="underline underline-offset-2 opacity-80 hover:opacity-100"
        >{{ messages.updateDownload }}</a
      >
      <button
        class="opacity-60 hover:opacity-100"
        @click="update.dismissed = true"
      >
        {{ messages.updateDismiss }}
      </button>
    </div>
  </div>
  <router-view v-slot="{ Component }">
    <KeepAlive include="HomeView">
      <component :is="Component" />
    </KeepAlive>
  </router-view>
</template>

<script setup lang="ts">
  import { onMounted, reactive } from "vue";

  import { useI18n } from "./composables/useI18n";
  import { useSettings } from "./composables/useSettings";

  const UI_ZOOM_MAP: Record<string, string> = {
    xs: "0.9",
    sm: "1",
    md: "1.25",
    lg: "1.4",
    xl: "1.5",
  };

  const { hydrate, get } = useSettings();
  const { messages } = useI18n();

  const update = reactive({
    show: false,
    dismissed: false,
    version: "",
    url: "",
  });

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
      document.documentElement.setAttribute("data-palette", colorTheme);
    }
    const readingTheme = get("reading", "theme", "light");
    document.documentElement.setAttribute("data-theme", readingTheme);

    // Check for updates after a short delay so the UI is fully settled.
    setTimeout(async () => {
      try {
        const resp = await fetch("/api/update-check");
        if (resp.ok) {
          const data = await resp.json();
          if (data.hasUpdate) {
            update.version = data.latestVersion;
            update.url = data.url;
            update.show = true;
          }
        }
      } catch {
        // Offline or dev environment — silently ignore.
      }
    }, 3000);
  });
</script>
