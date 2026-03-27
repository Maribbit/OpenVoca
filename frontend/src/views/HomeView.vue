<template>
  <div
    class="relative min-h-screen overflow-hidden bg-paper text-ink transition-colors duration-300"
    :class="uiFontFamily === 'serif' ? 'font-serif' : 'font-sans'"
  >
    <div class="fixed inset-x-0 top-0 z-10 h-px bg-black/6">
      <div class="h-full w-1/3 bg-inkLight/55"></div>
    </div>

    <header
      class="group fixed inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-6 uppercase tracking-[0.45em] text-inkLight/50 md:px-10"
      :class="uiHeaderSizeClass"
    >
      <div class="flex flex-1 justify-start">
        <button
          type="button"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:bg-black/4 hover:text-ink"
          @click="openMenu"
        >
          {{ i18nMessages.menu }}
        </button>
      </div>

      <div
        class="pointer-events-none flex flex-1 items-center justify-center"
      ></div>

      <div class="flex flex-1 items-center justify-end gap-1 md:gap-3">
        <button
          type="button"
          data-testid="reading-settings-trigger"
          class="cursor-pointer rounded-full p-2 transition-all hover:bg-black/4 hover:text-ink opacity-0 group-hover:opacity-100 focus:opacity-100"
          @click="toggleUiPanel"
          :title="i18nMessages.readingDisplaySettings"
        >
          <span class="sr-only">{{ i18nMessages.readingDisplaySettings }}</span>
          <svg
            class="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
            />
          </svg>
        </button>

        <router-link
          to="/stats"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:bg-black/4 hover:text-ink"
        >
          {{ i18nMessages.stats }}
        </router-link>
      </div>
    </header>

    <ReadingSettingsBar
      v-if="isUiPanelOpen"
      :settings="readingUiSettings"
      :messages="i18nMessages"
      @close="closeUiPanel"
      @update:settings="onReadingSettingsChange"
    />

    <main
      class="flex min-h-screen flex-col items-center justify-center gap-14 px-8 py-24"
    >
      <SentenceDisplay
        :tokens="tokens"
        :marked-words="markedWords"
        :is-loading="isLoading"
        :error-message="errorMessage"
        :loading-text="i18nMessages.loadingSentence"
        :typography-class="sentenceTypographyClass"
        @toggle-mark="toggleWordMark"
      />

      <HoldButton
        ref="holdButtonRef"
        :disabled="isLoading || isMenuOpen || isUiPanelOpen"
        :hold-text="i18nMessages.nextSentenceHint"
        :release-text="i18nMessages.releaseHint"
        :header-size-class="uiHeaderSizeClass"
        @advance="goToNextSentence"
      />
    </main>

    <Transition name="fade">
      <p
        v-if="feedbackError"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg"
      >
        {{ feedbackError }}
      </p>
    </Transition>

    <PreferencesModal
      v-if="isMenuOpen"
      :preferences="preferences"
      :default-prompt-template="DEFAULT_READING_PREFERENCES.promptTemplate"
      :locale="locale"
      :font-family="uiFontFamily"
      :font-size="uiFontSize"
      :messages="i18nMessages"
      @close="closeMenu"
      @save="onMenuSave"
      @switch-language="switchLanguage"
      @update:font-family="setUiFontFamily"
      @update:font-size="setUiFontSize"
    />
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref, watch } from "vue";

  import {
    fetchNextReadingSentence,
    submitFeedback,
    type ReadingSentenceToken,
  } from "../api/reading";
  import {
    DEFAULT_READING_PREFERENCES,
    loadReadingPreferences,
    saveReadingPreferences,
    type ReadingPreferences,
  } from "../composables/readingPreferences";
  import { type Locale, useI18n } from "../composables/useI18n";
  import HoldButton from "../components/HoldButton.vue";
  import PreferencesModal from "../components/PreferencesModal.vue";
  import ReadingSettingsBar from "../components/ReadingSettingsBar.vue";
  import type {
    ReadingUiSettings,
    ThemeOption,
  } from "../components/ReadingSettingsBar.vue";
  import SentenceDisplay from "../components/SentenceDisplay.vue";

  type FontSizeOption = "sm" | "md" | "lg";
  type SpacingOption = "tight" | "normal" | "loose";
  type UiFontFamily = "sans" | "serif";
  type UiFontSizeOption = "sm" | "md" | "lg";

  const UI_SETTINGS_STORAGE_KEY = "openvoca.reading.ui.settings";
  const FONT_SIZE_OPTIONS: FontSizeOption[] = ["sm", "md", "lg"];
  const SPACING_OPTIONS: SpacingOption[] = ["tight", "normal", "loose"];
  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  const DEFAULT_READING_UI_SETTINGS: ReadingUiSettings = {
    fontSize: "md",
    spacing: "normal",
    theme: "light",
  };

  const sentence = ref("");
  const tokens = ref<ReadingSentenceToken[]>([]);
  const errorMessage = ref("");
  const feedbackError = ref("");
  const isLoading = ref(true);
  const isMenuOpen = ref(false);
  const isUiPanelOpen = ref(false);
  const markedWords = ref<Set<string>>(new Set());

  const holdButtonRef = ref<InstanceType<typeof HoldButton> | null>(null);

  const preferences = ref<ReadingPreferences>(loadReadingPreferences());
  const readingUiSettings = ref<ReadingUiSettings>(loadReadingUiSettings());
  const uiFontFamily = ref<UiFontFamily>(loadUiFontFamily());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());
  const { locale, messages: i18nMessages, setLocale } = useI18n();

  const sentenceTypographyClass = computed(() => {
    const fontSizeMap: Record<FontSizeOption, string> = {
      sm: "text-[1.55rem] md:text-[2.0rem]",
      md: "text-[1.7rem] md:text-[2.2rem]",
      lg: "text-[1.85rem] md:text-[2.45rem]",
    };

    const spacingMap: Record<SpacingOption, string> = {
      tight: "leading-[1.5] tracking-[0.005em]",
      normal: "leading-[1.62] tracking-[0.012em]",
      loose: "leading-[1.75] tracking-[0.02em]",
    };

    return `${fontSizeMap[readingUiSettings.value.fontSize]} ${spacingMap[readingUiSettings.value.spacing]}`;
  });

  const uiHeaderSizeClass = computed(() => {
    const map: Record<UiFontSizeOption, string> = {
      sm: "text-[11px]",
      md: "text-[13px]",
      lg: "text-[15px]",
    };
    return map[uiFontSize.value];
  });

  // --- Persistence helpers ---

  function loadReadingUiSettings(): ReadingUiSettings {
    if (typeof window === "undefined") return DEFAULT_READING_UI_SETTINGS;
    const savedValue = window.localStorage.getItem(UI_SETTINGS_STORAGE_KEY);
    if (!savedValue) return DEFAULT_READING_UI_SETTINGS;

    try {
      const parsed = JSON.parse(savedValue) as Partial<ReadingUiSettings>;
      return {
        fontSize: FONT_SIZE_OPTIONS.includes(parsed.fontSize as FontSizeOption)
          ? (parsed.fontSize as FontSizeOption)
          : DEFAULT_READING_UI_SETTINGS.fontSize,
        spacing: SPACING_OPTIONS.includes(parsed.spacing as SpacingOption)
          ? (parsed.spacing as SpacingOption)
          : DEFAULT_READING_UI_SETTINGS.spacing,
        theme: THEME_OPTIONS.includes(parsed.theme as ThemeOption)
          ? (parsed.theme as ThemeOption)
          : DEFAULT_READING_UI_SETTINGS.theme,
      };
    } catch {
      return DEFAULT_READING_UI_SETTINGS;
    }
  }

  function saveReadingUiSettings(): void {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      UI_SETTINGS_STORAGE_KEY,
      JSON.stringify(readingUiSettings.value),
    );
  }

  function loadUiFontFamily(): UiFontFamily {
    if (typeof window === "undefined") return "sans";
    const saved = window.localStorage.getItem("openvoca.ui.fontFamily");
    if (saved === "sans" || saved === "serif") return saved;
    return "sans";
  }

  function setUiFontFamily(font: UiFontFamily): void {
    uiFontFamily.value = font;
    if (typeof window !== "undefined") {
      window.localStorage.setItem("openvoca.ui.fontFamily", font);
    }
  }

  function loadUiFontSize(): UiFontSizeOption {
    if (typeof window === "undefined") return "md";
    const saved = window.localStorage.getItem("openvoca.ui.fontSize");
    if (saved === "sm" || saved === "md" || saved === "lg") return saved;
    return "md";
  }

  function setUiFontSize(size: UiFontSizeOption): void {
    uiFontSize.value = size;
    if (typeof window !== "undefined") {
      window.localStorage.setItem("openvoca.ui.fontSize", size);
    }
  }

  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") return;
    window.document.documentElement.setAttribute("data-reading-theme", theme);
  }

  // --- UI panel ---

  function toggleUiPanel(): void {
    isUiPanelOpen.value = !isUiPanelOpen.value;
  }

  function closeUiPanel(): void {
    isUiPanelOpen.value = false;
  }

  function onReadingSettingsChange(next: ReadingUiSettings): void {
    readingUiSettings.value = next;
    applyTheme(next.theme);
  }

  // --- Sentence & feedback ---

  function tokenKey(token: ReadingSentenceToken): string {
    return `${token.text.toLowerCase()}/${token.pos ?? ""}`;
  }

  function toggleWordMark(token: ReadingSentenceToken): void {
    const key = tokenKey(token);
    const next = new Set(markedWords.value);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    markedWords.value = next;
  }

  async function loadSentence(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = "";
    try {
      const response = await fetchNextReadingSentence(preferences.value);
      sentence.value = response.sentence;
      tokens.value = response.tokens;
      markedWords.value = new Set();
    } catch {
      errorMessage.value = i18nMessages.value.ollamaError;
      tokens.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function goToNextSentence(): Promise<void> {
    if (isLoading.value) return;

    if (sentence.value) {
      const targetEntries = tokens.value
        .filter((t) => t.isTarget && t.pos)
        .map((t) => ({ word: t.text.toLowerCase(), pos: t.pos! }));
      const markedEntries = tokens.value
        .filter((t) => t.isWord && t.pos && markedWords.value.has(tokenKey(t)))
        .map((t) => ({ word: t.text.toLowerCase(), pos: t.pos! }));

      submitFeedback({
        targetWords: targetEntries,
        markedWords: markedEntries,
        sentence: sentence.value,
      }).catch(() => {
        feedbackError.value = i18nMessages.value.feedbackError;
        setTimeout(() => {
          feedbackError.value = "";
        }, 4000);
      });
    }

    await loadSentence();
  }

  // --- Menu ---

  function openMenu(): void {
    isUiPanelOpen.value = false;
    isMenuOpen.value = true;
  }

  function closeMenu(): void {
    isMenuOpen.value = false;
  }

  async function onMenuSave(next: {
    promptTemplate: string;
    targetWordCount: number;
  }): Promise<void> {
    preferences.value = next;
    saveReadingPreferences(preferences.value);
    closeMenu();
    await loadSentence();
  }

  function switchLanguage(nextLocale: Locale): void {
    setLocale(nextLocale);
    if (errorMessage.value) {
      errorMessage.value = i18nMessages.value.ollamaError;
    }
  }

  // --- Keyboard ---

  function handleKeydown(event: KeyboardEvent): void {
    if (event.code === "Space" && !isMenuOpen.value && !isUiPanelOpen.value) {
      const target = event.target as HTMLElement;
      if (target.tagName === "TEXTAREA" || target.tagName === "INPUT") return;
      event.preventDefault();
      if (!event.repeat) {
        holdButtonRef.value?.startHold();
      }
    }
  }

  function handleKeyup(event: KeyboardEvent): void {
    if (event.code === "Space") {
      holdButtonRef.value?.releaseHold();
    }
  }

  // --- Lifecycle ---

  onMounted(() => {
    applyTheme(readingUiSettings.value.theme);
    void loadSentence();
    window.addEventListener("keydown", handleKeydown);
    window.addEventListener("keyup", handleKeyup);
  });

  onUnmounted(() => {
    holdButtonRef.value?.abortHold();
    window.removeEventListener("keydown", handleKeydown);
    window.removeEventListener("keyup", handleKeyup);
  });

  watch(
    readingUiSettings,
    () => {
      saveReadingUiSettings();
    },
    { deep: true },
  );
</script>
