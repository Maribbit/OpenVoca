<template>
  <div class="min-h-zoom-screen bg-paper p-8 text-ink antialiased">
    <div class="mx-auto max-w-3xl">
      <!-- Header -->
      <header class="mb-12 flex items-center justify-between">
        <div>
          <h1 class="mb-2 font-serif text-3xl tracking-wide text-ink">
            {{ i18nMessages.settings }}
          </h1>
          <p class="text-sm text-inkLight">
            {{ i18nMessages.settingsSubtitle }}
          </p>
        </div>
        <router-link
          to="/"
          class="flex items-center gap-2 rounded-full border border-black/8 bg-surface px-5 py-2.5 text-sm font-medium text-ink transition-all hover:border-black/15 hover:shadow-sm"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          {{ i18nMessages.backToReading }}
        </router-link>
      </header>

      <div class="space-y-10">
        <!-- ===== Interface ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.interfaceSection }}
            </h2>
          </div>
          <div class="p-6">
            <div class="flex flex-wrap gap-6">
              <!-- Language -->
              <div>
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.language }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(locale === 'zh')"
                    @click="switchLanguage('zh')"
                  >
                    中文
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(locale === 'en')"
                    @click="switchLanguage('en')"
                  >
                    English
                  </button>
                </div>
              </div>

              <!-- Theme -->
              <div>
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.theme }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(currentTheme === 'light')"
                    @click="setTheme('light')"
                  >
                    {{ i18nMessages.themeLight }}
                  </button>
                  <button
                    type="button"
                    class="rounded-lg px-3 py-1.5 text-sm transition-all"
                    :class="toggleClass(currentTheme === 'dark')"
                    @click="setTheme('dark')"
                  >
                    {{ i18nMessages.themeDark }}
                  </button>
                </div>
              </div>

              <!-- UI Size -->
              <div>
                <label
                  class="mb-3 flex items-center gap-1.5 text-sm font-medium text-ink"
                >
                  {{ i18nMessages.uiSize }}
                  <button
                    type="button"
                    class="flex h-4 w-4 cursor-pointer items-center justify-center rounded-full border border-black/10 text-[10px] text-inkLight transition-colors hover:bg-black/4 hover:text-ink"
                    @click="showZoomHint = !showZoomHint"
                    :title="i18nMessages.uiSizeHint"
                  >
                    ?
                  </button>
                </label>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    v-for="opt in uiFontSizeOptions"
                    :key="opt.value"
                    type="button"
                    class="flex h-8 items-center justify-center rounded-lg px-2.5 transition-all"
                    :class="toggleClass(uiFontSize === opt.value)"
                    @click="setUiFontSize(opt.value)"
                  >
                    <span class="text-xs font-medium">{{ opt.label }}</span>
                  </button>
                </div>
                <p v-if="showZoomHint" class="mt-2 text-xs text-inkLight">
                  {{ i18nMessages.uiSizeHint }}
                </p>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== LLM Provider ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.llmProvider }}
            </h2>
            <p class="mt-1 text-xs text-inkLight/70">
              {{ i18nMessages.llmProviderHint }}
            </p>
          </div>
          <div class="space-y-5 p-6">
            <!-- Endpoint & Model -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <label
                  class="flex items-center gap-1.5 text-sm font-medium text-ink"
                >
                  {{ i18nMessages.endpoint }}
                  <button
                    type="button"
                    class="flex h-4 w-4 items-center justify-center rounded-full border border-black/10 text-[10px] text-inkLight transition-colors hover:bg-black/4 hover:text-ink cursor-pointer"
                    @click="showEndpointHint = !showEndpointHint"
                    :title="i18nMessages.endpointHint"
                  >
                    ?
                  </button>
                </label>
                <input
                  v-model="providerEndpoint"
                  type="text"
                  placeholder="http://localhost:11434"
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                  @change="saveProvider"
                />
                <p v-if="showEndpointHint" class="text-xs text-inkLight">
                  {{ i18nMessages.endpointHint }}
                </p>
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-sm font-medium text-ink">
                  {{ i18nMessages.model }}
                </label>
                <input
                  v-model="selectedModel"
                  type="text"
                  :placeholder="i18nMessages.modelPlaceholder"
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                  @change="saveProvider"
                />
              </div>
            </div>

            <!-- API Key -->
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-ink">
                {{ i18nMessages.apiKey }}
              </label>
              <div class="flex gap-2">
                <input
                  v-model="providerApiKey"
                  type="password"
                  :placeholder="i18nMessages.apiKeyPlaceholder"
                  class="flex-1 rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                  @change="saveProvider"
                />
                <button
                  type="button"
                  class="whitespace-nowrap rounded-xl border border-black/10 px-4 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
                  :disabled="connectionStatus === 'testing'"
                  @click="handleTestConnection"
                >
                  {{
                    connectionStatus === "testing"
                      ? i18nMessages.testingConnection
                      : i18nMessages.testConnection
                  }}
                </button>
              </div>
              <div class="flex items-center justify-between">
                <p class="text-xs text-inkLight">
                  {{ i18nMessages.apiKeyHint }}
                </p>
                <span
                  v-if="connectionStatus === 'ok'"
                  class="text-xs text-green-600"
                >
                  ✓ {{ connectionMessage }}
                </span>
                <span
                  v-else-if="connectionStatus === 'error'"
                  class="max-w-xs truncate text-xs text-red-500"
                  :title="connectionMessage"
                >
                  ✗ {{ connectionMessage }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== Generation Defaults ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.generationDefaults }}
            </h2>
          </div>
          <div class="space-y-6 p-6">
            <!-- Target word count -->
            <div>
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-ink">
                  {{ i18nMessages.targetWordCount }}
                </span>
                <span
                  class="rounded-full border border-black/8 bg-paper px-3 py-1 font-mono text-xs text-inkLight"
                >
                  {{ draftTargetWordCount }}
                </span>
              </div>
              <input
                v-model="draftTargetWordCount"
                type="range"
                min="1"
                max="5"
                step="1"
                class="w-full accent-ink"
              />
              <div
                class="mt-1 flex justify-between px-1 text-[11px] text-inkLight/70"
              >
                <span>1</span>
                <span>2</span>
                <span>3</span>
                <span>4</span>
                <span>5</span>
              </div>
              <p class="mt-2 text-xs text-inkLight">
                {{ i18nMessages.targetWordCountHint }}
              </p>
            </div>
          </div>
        </section>

        <!-- ===== Dictionary ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.dictionarySection }}
            </h2>
          </div>
          <div class="p-6">
            <div>
              <span class="mb-3 block text-sm font-medium text-ink">
                {{ i18nMessages.dictionaryDisplay }}
              </span>
              <div
                class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
              >
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'zh')"
                  @click="setDictionaryDisplay('zh')"
                >
                  {{ i18nMessages.dictionaryDisplayZh }}
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'en')"
                  @click="setDictionaryDisplay('en')"
                >
                  {{ i18nMessages.dictionaryDisplayEn }}
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-all"
                  :class="toggleClass(dictionaryDisplay === 'both')"
                  @click="setDictionaryDisplay('both')"
                >
                  {{ i18nMessages.dictionaryDisplayBoth }}
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== Data ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div class="border-b border-black/5 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.dataSection }}
            </h2>
          </div>
          <div class="flex items-center justify-between p-6">
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.exportVocabularySettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.exportVocabularySettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-black/10 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="handleExportVocabulary"
            >
              {{ i18nMessages.exportVocabularySettingsButton }}
            </button>
          </div>
          <div
            class="flex items-center justify-between border-t border-black/5 p-6"
          >
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.exportSettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.exportSettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-black/10 px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-black/4 dark:border-white/15 dark:hover:bg-white/8"
              @click="handleExportSettings"
            >
              {{ i18nMessages.exportSettingsButton }}
            </button>
          </div>
        </section>

        <!-- ===== Danger Zone ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-red-200/60 bg-surface shadow-sm"
        >
          <div class="border-b border-red-100 px-6 py-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-red-400"
            >
              {{ i18nMessages.dangerZone }}
            </h2>
          </div>
          <div class="flex items-center justify-between p-6">
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.clearAllVocabulary }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.clearAllVocabularyDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
              @click="confirmClearVocabulary"
            >
              {{ i18nMessages.clearDatabase }}
            </button>
          </div>
          <div
            class="flex items-center justify-between border-t border-red-100 p-6"
          >
            <div>
              <p class="text-sm font-medium text-ink">
                {{ i18nMessages.clearAllSettings }}
              </p>
              <p class="mt-1 text-xs text-inkLight">
                {{ i18nMessages.clearAllSettingsDescription }}
              </p>
            </div>
            <button
              type="button"
              class="whitespace-nowrap rounded-xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
              @click="confirmClearSettings"
            >
              {{ i18nMessages.clearSettingsButton }}
            </button>
          </div>
        </section>
      </div>

      <!-- Bottom padding -->
      <div class="h-16"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { onBeforeUnmount, onMounted, ref, watch } from "vue";

  import { clearVocabulary, exportVocabulary } from "../api/reading";
  import { fetchProvider, setProvider, testProvider } from "../api/settings";
  import { type Locale, useI18n } from "../composables/useI18n";
  import { useSettings } from "../composables/useSettings";

  type ThemeOption = "light" | "dark";
  type UiFontSizeOption = "xs" | "sm" | "md" | "lg" | "xl";

  const DEFAULT_MODEL = "";

  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  const { get, set, clearAll, exportAll } = useSettings();
  const { locale, messages: i18nMessages, setLocale } = useI18n();

  const draftTargetWordCount = ref(
    Number(get("generation", "targetWordCount", "1")),
  );

  const currentTheme = ref<ThemeOption>(loadTheme());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());

  const selectedModel = ref("");
  const providerEndpoint = ref("http://localhost:11434");
  const providerApiKey = ref("");
  const connectionStatus = ref<"idle" | "testing" | "ok" | "error">("idle");
  const connectionMessage = ref("");
  const showEndpointHint = ref(false);
  const showZoomHint = ref(false);

  type DictionaryDisplayOption = "zh" | "en" | "both";
  const DICT_DISPLAY_OPTIONS: DictionaryDisplayOption[] = ["zh", "en", "both"];
  const dictionaryDisplay = ref<DictionaryDisplayOption>(loadDictDisplay());

  const uiFontSizeOptions = [
    { value: "xs" as const, label: "90%" },
    { value: "sm" as const, label: "100%" },
    { value: "md" as const, label: "125%" },
    { value: "lg" as const, label: "140%" },
    { value: "xl" as const, label: "150%" },
  ];

  // --- Persistence helpers ---

  function loadTheme(): ThemeOption {
    const saved = get("reading", "theme", "light");
    return THEME_OPTIONS.includes(saved as ThemeOption)
      ? (saved as ThemeOption)
      : "light";
  }

  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    window.document.documentElement.setAttribute("data-reading-theme", theme);
  }

  function setTheme(theme: ThemeOption): void {
    currentTheme.value = theme;
    applyTheme(theme);
    set("reading", { theme });
  }

  const UI_ZOOM_MAP: Record<UiFontSizeOption, string> = {
    xs: "0.9",
    sm: "1",
    md: "1.25",
    lg: "1.4",
    xl: "1.5",
  };

  function loadUiFontSize(): UiFontSizeOption {
    const saved = get("interface", "uiFontSize", "md");
    const valid: UiFontSizeOption[] = ["xs", "sm", "md", "lg", "xl"];
    if (valid.includes(saved as UiFontSizeOption))
      return saved as UiFontSizeOption;
    return "md";
  }

  function applyZoom(size: UiFontSizeOption): void {
    if (typeof document === "undefined") return;
    const appEl = document.getElementById("app");
    if (appEl) {
      const zoomVal = UI_ZOOM_MAP[size];
      appEl.style.zoom = zoomVal;
      appEl.style.setProperty("--app-zoom", zoomVal);
    }
  }

  function setUiFontSize(size: UiFontSizeOption): void {
    uiFontSize.value = size;
    applyZoom(size);
    set("interface", { uiFontSize: size });
  }

  function switchLanguage(nextLocale: Locale): void {
    setLocale(nextLocale);
    set("interface", { locale: nextLocale });
  }

  function toggleClass(isActive: boolean): string {
    return isActive
      ? "bg-ink text-paper shadow-sm font-medium"
      : "text-inkLight hover:text-ink";
  }

  function loadDictDisplay(): DictionaryDisplayOption {
    const saved = get("dictionary", "display", "both");
    return DICT_DISPLAY_OPTIONS.includes(saved as DictionaryDisplayOption)
      ? (saved as DictionaryDisplayOption)
      : "both";
  }

  function setDictionaryDisplay(mode: DictionaryDisplayOption): void {
    dictionaryDisplay.value = mode;
    set("dictionary", { display: mode });
  }

  async function saveProvider(): Promise<void> {
    await setProvider({
      endpoint: providerEndpoint.value,
      model: selectedModel.value,
      apiKey: providerApiKey.value,
    });
  }

  async function handleTestConnection(): Promise<void> {
    connectionStatus.value = "testing";
    connectionMessage.value = "";
    await saveProvider();
    try {
      const result = await testProvider();
      connectionStatus.value = result.ok ? "ok" : "error";
      connectionMessage.value = result.message;
    } catch {
      connectionStatus.value = "error";
      connectionMessage.value = "Network error";
    }
  }

  async function handleClearVocabulary(): Promise<void> {
    await clearVocabulary();
  }

  function confirmClearVocabulary(): void {
    if (window.confirm(i18nMessages.value.confirmClearVocabulary)) {
      void handleClearVocabulary();
    }
  }

  async function handleClearSettings(): Promise<void> {
    await clearAll();
    window.location.reload();
  }

  function confirmClearSettings(): void {
    if (window.confirm(i18nMessages.value.confirmClearSettings)) {
      void handleClearSettings();
    }
  }

  function handleExportVocabulary(): void {
    void exportVocabulary();
  }

  function handleExportSettings(): void {
    const data = exportAll();
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "openvoca-settings.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  // Auto-save generation preferences when drafts change
  watch(draftTargetWordCount, () => {
    set("generation", {
      targetWordCount: String(draftTargetWordCount.value),
    });
  });

  // Apply current theme on mount
  onMounted(() => {
    applyTheme(currentTheme.value);

    Promise.all([fetchProvider()])
      .then(([provider]) => {
        providerEndpoint.value = provider?.endpoint ?? "http://localhost:11434";
        selectedModel.value = provider?.model ?? DEFAULT_MODEL;
      })
      .catch(() => {
        // keep defaults
      });
  });

  // Save on leave as a safety net
  onBeforeUnmount(() => {
    set("generation", {
      targetWordCount: String(draftTargetWordCount.value),
    });
  });
</script>
