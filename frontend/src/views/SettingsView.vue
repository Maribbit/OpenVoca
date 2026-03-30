<template>
  <div class="min-h-screen bg-paper p-8 text-ink antialiased">
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
            <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
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
                <span class="mb-3 block text-sm font-medium text-ink">
                  {{ i18nMessages.uiSize }}
                </span>
                <div
                  class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
                >
                  <button
                    v-for="opt in uiFontSizeOptions"
                    :key="opt.value"
                    type="button"
                    class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
                    :class="toggleClass(uiFontSize === opt.value)"
                    @click="setUiFontSize(opt.value)"
                  >
                    <span :class="opt.labelClass">{{ opt.label }}</span>
                  </button>
                </div>
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
          </div>
          <div class="space-y-5 p-6">
            <!-- Provider selector -->
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-ink">
                {{ i18nMessages.provider }}
              </label>
              <div
                class="inline-flex self-start rounded-xl border border-black/8 bg-paper p-1"
              >
                <button
                  type="button"
                  class="rounded-lg px-4 py-2 text-sm transition-all"
                  :class="toggleClass(true)"
                >
                  {{ i18nMessages.ollamaLocal }}
                </button>
              </div>
            </div>

            <!-- Model & Endpoint -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div class="flex flex-col gap-2">
                <label class="text-sm font-medium text-ink">
                  {{ i18nMessages.model }}
                </label>
                <input
                  type="text"
                  value="gemma3:4b"
                  disabled
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                />
              </div>
              <div class="flex flex-col gap-2">
                <label class="text-sm font-medium text-ink">
                  {{ i18nMessages.endpoint }}
                </label>
                <input
                  type="text"
                  value="http://localhost:11434"
                  disabled
                  class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 font-mono text-sm text-ink transition-shadow focus:outline-none focus:ring-2 focus:ring-highlight"
                />
              </div>
            </div>

            <!-- API Key (disabled for Ollama) -->
            <div class="flex flex-col gap-2 opacity-40">
              <label class="text-sm font-medium text-ink">
                {{ i18nMessages.apiKey }}
              </label>
              <input
                type="password"
                :placeholder="i18nMessages.apiKeyPlaceholder"
                disabled
                class="rounded-xl border border-black/8 bg-paper px-4 py-2.5 text-sm transition-shadow focus:outline-none"
              />
              <p class="text-xs text-inkLight">
                {{ i18nMessages.apiKeyHint }}
              </p>
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
            <p class="mt-1 text-xs text-inkLight/70">
              {{ i18nMessages.generationDefaultsHint }}
            </p>
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

        <!-- ===== Prompt Template ===== -->
        <section
          class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
        >
          <div
            class="flex items-center justify-between border-b border-black/5 px-6 py-4"
          >
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.promptTemplate }}
            </h2>
            <button
              type="button"
              class="text-xs text-inkLight transition-colors hover:text-ink"
              @click="
                draftPromptTemplate = DEFAULT_READING_PREFERENCES.promptTemplate
              "
            >
              {{ i18nMessages.resetToDefault }}
            </button>
          </div>
          <div class="space-y-3 p-6">
            <textarea
              v-model="draftPromptTemplate"
              rows="6"
              class="w-full resize-none rounded-xl border border-black/8 bg-paper px-4 py-3 font-mono text-sm leading-relaxed text-ink outline-none transition-shadow focus:ring-2 focus:ring-highlight"
            />
            <p class="text-xs text-inkLight">
              {{ i18nMessages.targetWordsTokenHintPrefix }}
              <span
                class="rounded border border-black/8 bg-paper px-1.5 py-0.5 font-mono"
                >{{ targetWordsToken }}</span
              >
              {{ i18nMessages.targetWordsTokenHintSuffix }}
            </p>
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
              @click="handleClearVocabulary"
            >
              {{ i18nMessages.clearDatabase }}
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

  import { clearVocabulary } from "../api/reading";
  import {
    DEFAULT_READING_PREFERENCES,
    loadReadingPreferences,
    saveReadingPreferences,
  } from "../composables/readingPreferences";
  import { type Locale, useI18n } from "../composables/useI18n";

  type ThemeOption = "light" | "dark";
  type UiFontSizeOption = "sm" | "md" | "lg";

  const THEME_STORAGE_KEY = "openvoca.reading.ui.settings";
  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  const { locale, messages: i18nMessages, setLocale } = useI18n();
  const preferences = ref(loadReadingPreferences());
  const draftTargetWordCount = ref(preferences.value.targetWordCount);
  const draftPromptTemplate = ref(preferences.value.promptTemplate);
  const targetWordsToken = "{{target_words}}";

  const currentTheme = ref<ThemeOption>(loadTheme());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());

  const uiFontSizeOptions = [
    { value: "sm" as const, label: "A-", labelClass: "text-xs font-medium" },
    { value: "md" as const, label: "A", labelClass: "text-sm font-medium" },
    { value: "lg" as const, label: "A+", labelClass: "text-base font-medium" },
  ];

  // --- Persistence helpers ---

  function loadTheme(): ThemeOption {
    if (typeof window === "undefined") return "light";
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (!saved) return "light";
    try {
      const parsed = JSON.parse(saved) as { theme?: string };
      if (THEME_OPTIONS.includes(parsed.theme as ThemeOption)) {
        return parsed.theme as ThemeOption;
      }
    } catch {
      // ignore
    }
    return "light";
  }

  function saveTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    let settings = { fontSize: "md", spacing: "normal", theme: "light" };
    if (saved) {
      try {
        settings = { ...settings, ...JSON.parse(saved) };
      } catch {
        // ignore
      }
    }
    settings.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(settings));
  }

  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    window.document.documentElement.setAttribute("data-reading-theme", theme);
  }

  function setTheme(theme: ThemeOption): void {
    currentTheme.value = theme;
    applyTheme(theme);
    saveTheme(theme);
  }

  const ROOT_FONT_SIZE_MAP: Record<UiFontSizeOption, string> = {
    sm: "14px",
    md: "16px",
    lg: "18px",
  };

  function loadUiFontSize(): UiFontSizeOption {
    if (typeof window === "undefined") return "md";
    const saved = window.localStorage.getItem("openvoca.ui.fontSize");
    if (saved === "sm" || saved === "md" || saved === "lg") return saved;
    return "md";
  }

  function applyRootFontSize(size: UiFontSizeOption): void {
    if (typeof document === "undefined") return;
    document.documentElement.style.fontSize = ROOT_FONT_SIZE_MAP[size];
  }

  function setUiFontSize(size: UiFontSizeOption): void {
    uiFontSize.value = size;
    applyRootFontSize(size);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("openvoca.ui.fontSize", size);
    }
  }

  function switchLanguage(nextLocale: Locale): void {
    setLocale(nextLocale);
  }

  function toggleClass(isActive: boolean): string {
    return isActive
      ? "bg-ink text-paper shadow-sm font-medium"
      : "text-inkLight hover:text-ink";
  }

  async function handleClearVocabulary(): Promise<void> {
    await clearVocabulary();
  }

  // Auto-save preferences when drafts change
  watch([draftTargetWordCount, draftPromptTemplate], () => {
    const trimmed = draftPromptTemplate.value.trim();
    if (!trimmed) return;
    saveReadingPreferences({
      promptTemplate: trimmed,
      targetWordCount: Number(draftTargetWordCount.value),
    });
  });

  // Apply current theme on mount
  onMounted(() => {
    applyTheme(currentTheme.value);
  });

  // Save on leave as a safety net
  onBeforeUnmount(() => {
    const trimmed = draftPromptTemplate.value.trim();
    if (!trimmed) return;
    saveReadingPreferences({
      promptTemplate: trimmed,
      targetWordCount: Number(draftTargetWordCount.value),
    });
  });
</script>
