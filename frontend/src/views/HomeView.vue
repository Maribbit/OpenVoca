<template>
  <div
    class="relative min-h-screen overflow-hidden bg-paper text-ink transition-colors duration-300"
    :class="uiFontFamily === 'serif' ? 'font-serif' : 'font-sans'"
  >
    <div class="fixed inset-x-0 top-0 z-10 h-px bg-black/6">
      <div class="h-full w-1/3 bg-inkLight/55"></div>
    </div>

    <header
      class="group fixed inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-6 text-[11px] uppercase tracking-[0.45em] text-inkLight/50 md:px-10"
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

      <div class="relative flex flex-1 items-center justify-center">
        <div class="relative flex items-center justify-center">
          <span>{{ i18nMessages.reading }}</span>
          <button
            type="button"
            data-testid="reading-settings-trigger"
            class="absolute left-full top-1/2 ml-1 -translate-y-1/2 cursor-pointer rounded-full p-2 opacity-0 transition-all hover:bg-black/4 hover:text-ink group-hover:opacity-100"
            @click="toggleUiPanel"
          >
            <span class="sr-only">{{
              i18nMessages.readingDisplaySettings
            }}</span>
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
        </div>
      </div>

      <div class="flex flex-1 items-center justify-end gap-3">
        <span class="hidden md:inline">gemma3:4b</span>
        <router-link
          to="/stats"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:bg-black/4 hover:text-ink"
        >
          {{ i18nMessages.stats }}
        </router-link>
      </div>
    </header>

    <section
      v-if="isUiPanelOpen"
      data-testid="reading-settings-overlay"
      class="fixed inset-0 z-20 px-4 pt-20"
      @click.self="closeUiPanel"
    >
      <div
        class="menu-fade mx-auto flex w-fit max-w-full flex-col items-stretch gap-2 rounded-[26px] border border-black/8 bg-surface/82 p-2 shadow-[0_20px_50px_rgba(44,44,44,0.12)] backdrop-blur-md md:flex-row md:flex-wrap md:items-center md:justify-center md:gap-3"
      >
        <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
          <span
            class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
          >
            {{ i18nMessages.fontSize }}
          </span>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.fontSize === 'sm')"
            @click="setFontSize('sm')"
          >
            <span class="text-xs font-medium">A-</span>
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.fontSize === 'md')"
            @click="setFontSize('md')"
          >
            <span class="text-sm font-medium">A</span>
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.fontSize === 'lg')"
            @click="setFontSize('lg')"
          >
            <span class="text-base font-medium">A+</span>
          </button>
        </div>

        <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
          <span
            class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
          >
            {{ i18nMessages.spacing }}
          </span>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.spacing === 'tight')"
            @click="setSpacing('tight')"
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
                d="M4 8h16M4 16h16"
              ></path>
            </svg>
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.spacing === 'normal')"
            @click="setSpacing('normal')"
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
                d="M4 6h16M4 12h16M4 18h16"
              ></path>
            </svg>
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.spacing === 'loose')"
            @click="setSpacing('loose')"
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
                d="M4 4h16M4 12h16M4 20h16"
              ></path>
            </svg>
          </button>
        </div>

        <div class="flex items-center gap-1 rounded-xl bg-paper p-1">
          <span
            class="px-2 text-xs font-medium uppercase tracking-wide text-inkLight"
          >
            {{ i18nMessages.theme }}
          </span>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.theme === 'light')"
            @click="setTheme('light')"
            :title="i18nMessages.themeLight"
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
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0z"
              ></path>
            </svg>
          </button>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-all"
            :class="uiOptionButtonClass(readingUiSettings.theme === 'dark')"
            @click="setTheme('dark')"
            :title="i18nMessages.themeDark"
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
                d="M20.354 15.354A9 9 0 0 1 8.646 3.646 9.003 9.003 0 0 0 12 21a9.003 9.003 0 0 0 8.354-5.646z"
              ></path>
            </svg>
          </button>
        </div>
      </div>
    </section>

    <main class="flex min-h-screen items-center justify-center px-8 py-24">
      <article class="w-full max-w-3xl text-center">
        <p
          v-if="isLoading"
          class="sentence-fade font-serif text-inkLight/65"
          :class="sentenceTypographyClass"
        >
          {{ i18nMessages.loadingSentence }}
        </p>

        <p
          v-else-if="errorMessage"
          class="sentence-fade font-serif text-inkLight/75"
          :class="sentenceTypographyClass"
        >
          {{ errorMessage }}
        </p>

        <p
          v-else
          class="sentence-fade font-serif text-ink"
          :class="sentenceTypographyClass"
        >
          <template
            v-for="(token, index) in tokens"
            :key="`${token.text}-${index}`"
          >
            <span v-if="needsLeadingSpace(index)" aria-hidden="true"
              >&nbsp;</span
            >
            <button
              v-if="token.isWord"
              type="button"
              class="cursor-pointer rounded-md px-[0.09em] py-[0.04em] transition-colors focus:outline-none"
              :class="
                markedWords.has(token.text.toLowerCase())
                  ? 'bg-highlight'
                  : 'hover:bg-highlight/70'
              "
              @click="toggleWordMark(token.text)"
            >
              {{ token.text }}
            </button>
            <span v-else>{{ token.text }}</span>
          </template>
        </p>
      </article>

      <!-- Right arrow: long-press to advance -->
      <div
        class="group/btn pointer-events-auto absolute bottom-0 right-0 top-0 hidden w-1/6 cursor-pointer items-center justify-end pr-4 select-none md:flex"
        @mousedown.prevent="startHold"
        @mouseup="releaseHold"
        @mouseleave="abortHold"
        @touchstart.prevent="startHold"
        @touchend="releaseHold"
        @touchcancel="abortHold"
      >
        <svg
          class="h-8 w-8 text-ink opacity-0 transition-opacity group-hover/btn:opacity-30"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </main>

    <!-- Footer: long-press hint + progress bar -->
    <footer
      class="fixed inset-x-0 bottom-0 cursor-pointer select-none px-8 py-8 text-center"
      @mousedown.prevent="startHold"
      @mouseup="releaseHold"
      @mouseleave="abortHold"
      @touchstart.prevent="startHold"
      @touchend="releaseHold"
      @touchcancel="abortHold"
    >
      <div
        class="absolute inset-x-0 bottom-0 h-[3px] rounded-full bg-ink/60 transition-all ease-linear"
        :style="{
          width: holdProgress * 100 + '%',
          transitionDuration: holdProgress > 0 ? '600ms' : '0ms',
        }"
      />
      <p class="text-[11px] uppercase tracking-[0.35em] text-inkLight/55">
        {{ i18nMessages.nextSentenceHint }}
      </p>
    </footer>

    <div
      v-if="isMenuOpen"
      class="fixed inset-0 z-30 flex justify-center bg-black/5 p-4 backdrop-blur-sm sm:p-8"
    >
      <main
        class="menu-fade relative flex w-full max-w-3xl flex-col overflow-hidden rounded-[28px] border border-black/6 bg-surface shadow-[0_30px_80px_rgba(44,44,44,0.12)]"
      >
        <header
          class="flex items-center justify-between border-b border-black/5 px-8 py-6"
        >
          <h1 class="font-serif text-2xl tracking-wide text-ink">
            {{ i18nMessages.preferences }}
          </h1>
          <button
            type="button"
            class="rounded-full p-2 text-inkLight transition-colors hover:bg-black/4 hover:text-ink"
            @click="closeMenu"
          >
            <span class="sr-only">{{ i18nMessages.closeMenu }}</span>
            <svg
              class="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M6 18 18 6M6 6l12 12"
              />
            </svg>
          </button>
        </header>

        <div class="flex-1 space-y-10 overflow-y-auto px-8 py-6">
          <section>
            <h2
              class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.llmConfiguration }}
            </h2>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="rounded-2xl border border-black/5 bg-paper p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-inkLight">
                  {{ i18nMessages.provider }}
                </p>
                <p class="mt-2 text-sm font-medium text-ink">
                  {{ i18nMessages.localModelProvider }}
                </p>
              </div>
              <div class="rounded-2xl border border-black/5 bg-paper p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-inkLight">
                  {{ i18nMessages.model }}
                </p>
                <p class="mt-2 text-sm font-medium text-ink">gemma3:4b</p>
              </div>
            </div>
          </section>

          <section class="grid gap-4 sm:grid-cols-2">
            <div>
              <h2
                class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
              >
                {{ i18nMessages.language }}
              </h2>
              <div
                class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
              >
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                  :class="menuToggleButtonClass(locale === 'zh')"
                  @click="switchLanguage('zh')"
                >
                  中文
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                  :class="menuToggleButtonClass(locale === 'en')"
                  @click="switchLanguage('en')"
                >
                  English
                </button>
              </div>
            </div>

            <div>
              <h2
                class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
              >
                {{ i18nMessages.systemFont }}
              </h2>
              <div
                class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
              >
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                  :class="menuToggleButtonClass(uiFontFamily === 'sans')"
                  @click="setUiFontFamily('sans')"
                >
                  {{ i18nMessages.uiFontSans }}
                </button>
                <button
                  type="button"
                  class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                  :class="menuToggleButtonClass(uiFontFamily === 'serif')"
                  @click="setUiFontFamily('serif')"
                >
                  {{ i18nMessages.uiFontSerif }}
                </button>
              </div>
            </div>
          </section>

          <section>
            <h2
              class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ i18nMessages.learningParameters }}
            </h2>
            <div class="space-y-2">
              <label class="text-sm font-medium text-ink" for="target-words">
                {{ i18nMessages.targetWords }}
              </label>
              <textarea
                id="target-words"
                v-model="draftTargetWords"
                rows="3"
                class="w-full rounded-2xl border border-black/8 bg-paper px-4 py-3 text-sm leading-relaxed text-ink outline-none transition-shadow focus:ring-2 focus:ring-highlight"
              />
              <p class="text-xs text-inkLight">
                {{ i18nMessages.targetWordsHint }}
              </p>
            </div>
          </section>

          <section>
            <div class="mb-4 flex items-center justify-between gap-4">
              <h2
                class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
              >
                {{ i18nMessages.promptEngineering }}
              </h2>
              <button
                type="button"
                class="text-xs text-inkLight transition-colors hover:text-ink"
                @click="resetDraftPrompt"
              >
                {{ i18nMessages.resetToDefault }}
              </button>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-ink" for="prompt-template">
                {{ i18nMessages.generationPrompt }}
              </label>
              <textarea
                id="prompt-template"
                v-model="draftPromptTemplate"
                rows="6"
                class="w-full rounded-2xl border border-black/8 bg-paper px-4 py-3 font-mono text-sm leading-relaxed text-ink outline-none transition-shadow focus:ring-2 focus:ring-highlight"
              />
              <p class="text-xs text-inkLight">
                {{ i18nMessages.targetWordsTokenHintPrefix }}
                <span class="font-mono">{{ targetWordsToken }}</span>
                {{ i18nMessages.targetWordsTokenHintSuffix }}
              </p>
            </div>
          </section>

          <p v-if="menuErrorMessage" class="text-sm text-red-600">
            {{ menuErrorMessage }}
          </p>
        </div>

        <footer
          class="flex justify-end gap-3 border-t border-black/5 bg-black/1.5 px-8 py-4"
        >
          <button
            type="button"
            class="rounded-xl px-5 py-2.5 text-sm font-medium text-inkLight transition-colors hover:text-ink"
            @click="closeMenu"
          >
            {{ i18nMessages.cancel }}
          </button>
          <button
            type="button"
            class="rounded-xl bg-ink px-5 py-2.5 text-sm font-medium text-paper transition-opacity hover:opacity-90"
            @click="saveMenuChanges"
          >
            {{ i18nMessages.saveChanges }}
          </button>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref, watch } from "vue";

  import {
    fetchReadingSentence,
    fetchNextReadingSentence,
    submitFeedback,
    type ReadingSentenceToken,
  } from "../api/reading";
  import {
    DEFAULT_READING_PREFERENCES,
    formatTargetWords,
    loadReadingPreferences,
    parseTargetWordsInput,
    saveReadingPreferences,
    type ReadingPreferences,
  } from "../composables/readingPreferences";
  import { type Locale, useI18n } from "../composables/useI18n";

  type FontSizeOption = "sm" | "md" | "lg";
  type SpacingOption = "tight" | "normal" | "loose";
  type ThemeOption = "light" | "dark";

  interface ReadingUiSettings {
    fontSize: FontSizeOption;
    spacing: SpacingOption;
    theme: ThemeOption;
  }

  const UI_SETTINGS_STORAGE_KEY = "openvoca.reading.ui.settings";
  const FONT_SIZE_OPTIONS: FontSizeOption[] = ["sm", "md", "lg"];
  const SPACING_OPTIONS: SpacingOption[] = ["tight", "normal", "loose"];
  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  type UiFontFamily = "sans" | "serif";

  const DEFAULT_READING_UI_SETTINGS: ReadingUiSettings = {
    fontSize: "md",
    spacing: "normal",
    theme: "light",
  };

  const sentence = ref("");
  const tokens = ref<ReadingSentenceToken[]>([]);
  const errorMessage = ref("");
  const isLoading = ref(true);
  const isMenuOpen = ref(false);
  const isUiPanelOpen = ref(false);
  const menuErrorMessage = ref("");
  const draftTargetWords = ref("");
  const draftPromptTemplate = ref("");
  const targetWordsToken = "{{target_words}}";
  const markedWords = ref<Set<string>>(new Set());
  const currentTargetWords = ref<string[]>([]);
  const holdProgress = ref(0);
  const holdReady = ref(false);
  let holdTimer: ReturnType<typeof setTimeout> | null = null;

  const preferences = ref<ReadingPreferences>(loadReadingPreferences());
  const readingUiSettings = ref<ReadingUiSettings>(loadReadingUiSettings());
  const uiFontFamily = ref<UiFontFamily>(loadUiFontFamily());
  const { locale, messages: i18nMessages, setLocale } = useI18n();

  const sentenceTypographyClass = computed(() => {
    const fontSizeMap: Record<FontSizeOption, string> = {
      sm: "text-[1.9rem] md:text-[2.6rem]",
      md: "text-[2.1rem] md:text-[2.9rem]",
      lg: "text-[2.3rem] md:text-[3.15rem]",
    };

    const spacingMap: Record<SpacingOption, string> = {
      tight: "leading-[1.78] tracking-[0.018em]",
      normal: "leading-[1.92] tracking-[0.025em]",
      loose: "leading-[2.02] tracking-[0.033em]",
    };

    return `${fontSizeMap[readingUiSettings.value.fontSize]} ${spacingMap[readingUiSettings.value.spacing]}`;
  });

  function loadReadingUiSettings(): ReadingUiSettings {
    if (typeof window === "undefined") {
      return DEFAULT_READING_UI_SETTINGS;
    }

    const savedValue = window.localStorage.getItem(UI_SETTINGS_STORAGE_KEY);
    if (!savedValue) {
      return DEFAULT_READING_UI_SETTINGS;
    }

    try {
      const parsed = JSON.parse(savedValue) as Partial<ReadingUiSettings>;
      const fontSize = FONT_SIZE_OPTIONS.includes(
        parsed.fontSize as FontSizeOption,
      )
        ? (parsed.fontSize as FontSizeOption)
        : DEFAULT_READING_UI_SETTINGS.fontSize;
      const spacing = SPACING_OPTIONS.includes(parsed.spacing as SpacingOption)
        ? (parsed.spacing as SpacingOption)
        : DEFAULT_READING_UI_SETTINGS.spacing;
      const theme = THEME_OPTIONS.includes(parsed.theme as ThemeOption)
        ? (parsed.theme as ThemeOption)
        : DEFAULT_READING_UI_SETTINGS.theme;

      return {
        fontSize,
        spacing,
        theme,
      };
    } catch {
      return DEFAULT_READING_UI_SETTINGS;
    }
  }

  function saveReadingUiSettings(): void {
    if (typeof window === "undefined") {
      return;
    }

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

  function setUiFontFamily(font: UiFontFamily) {
    uiFontFamily.value = font;
    if (typeof window !== "undefined") {
      window.localStorage.setItem("openvoca.ui.fontFamily", font);
    }
  }
  function applyTheme(theme: ThemeOption): void {
    if (typeof window === "undefined") {
      return;
    }

    window.document.documentElement.setAttribute("data-reading-theme", theme);
  }

  function toggleUiPanel(): void {
    isUiPanelOpen.value = !isUiPanelOpen.value;
  }

  function closeUiPanel(): void {
    isUiPanelOpen.value = false;
  }

  function setFontSize(nextSize: FontSizeOption): void {
    readingUiSettings.value = {
      ...readingUiSettings.value,
      fontSize: nextSize,
    };
  }

  function setSpacing(nextSpacing: SpacingOption): void {
    readingUiSettings.value = {
      ...readingUiSettings.value,
      spacing: nextSpacing,
    };
  }

  function setTheme(nextTheme: ThemeOption): void {
    readingUiSettings.value = {
      ...readingUiSettings.value,
      theme: nextTheme,
    };
    applyTheme(nextTheme);
  }

  function uiOptionButtonClass(isActive: boolean): string {
    return isActive
      ? "bg-surface text-ink shadow-sm"
      : "text-inkLight hover:bg-surface hover:text-ink";
  }

  function menuToggleButtonClass(isActive: boolean): string {
    return isActive
      ? "bg-ink text-paper shadow-sm"
      : "text-inkLight hover:text-ink";
  }

  async function loadSentence(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      const response = await fetchReadingSentence(preferences.value);
      sentence.value = response.sentence;
      tokens.value = response.tokens;
      currentTargetWords.value = response.words;
      markedWords.value = new Set();
    } catch {
      errorMessage.value = i18nMessages.value.ollamaError;
      tokens.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function toggleWordMark(word: string): void {
    const key = word.toLowerCase();
    const next = new Set(markedWords.value);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    markedWords.value = next;
  }

  async function goToNextSentence(): Promise<void> {
    if (isLoading.value) return;

    // Submit feedback for the current sentence (fire-and-forget)
    if (sentence.value) {
      void submitFeedback({
        targetWords: currentTargetWords.value,
        markedWords: [...markedWords.value],
        sentence: sentence.value,
      });
    }

    isLoading.value = true;
    errorMessage.value = "";

    try {
      const response = await fetchNextReadingSentence(preferences.value);
      sentence.value = response.sentence;
      tokens.value = response.tokens;
      currentTargetWords.value = response.words;
      markedWords.value = new Set();
    } catch {
      errorMessage.value = i18nMessages.value.ollamaError;
      tokens.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function startHold(): void {
    if (isLoading.value || isMenuOpen.value || isUiPanelOpen.value) return;
    abortHold();
    holdProgress.value = 1;
    holdReady.value = false;
    holdTimer = setTimeout(() => {
      holdTimer = null;
      holdReady.value = true;
    }, 600);
  }

  function abortHold(): void {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
    holdProgress.value = 0;
    holdReady.value = false;
  }

  function releaseHold(): void {
    const shouldAdvance = holdReady.value;
    abortHold();
    if (shouldAdvance) {
      void goToNextSentence();
    }
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (event.code === "Space" && !isMenuOpen.value && !isUiPanelOpen.value) {
      const target = event.target as HTMLElement;
      if (target.tagName === "TEXTAREA" || target.tagName === "INPUT") return;
      event.preventDefault();
      if (!event.repeat) {
        startHold();
      }
    }
  }

  function handleKeyup(event: KeyboardEvent): void {
    if (event.code === "Space") {
      releaseHold();
    }
  }

  function needsLeadingSpace(index: number): boolean {
    if (index === 0) {
      return false;
    }

    const currentToken = tokens.value[index];
    const previousToken = tokens.value[index - 1];

    if (!currentToken?.isWord) {
      return false;
    }

    return !new Set(['"', "'", "(", "[", "{", "-"]).has(
      previousToken?.text ?? "",
    );
  }

  function switchLanguage(nextLocale: Locale): void {
    setLocale(nextLocale);
    if (errorMessage.value) {
      errorMessage.value = i18nMessages.value.ollamaError;
    }
  }

  function syncDraftFromPreferences(): void {
    draftTargetWords.value = formatTargetWords(preferences.value.targetWords);
    draftPromptTemplate.value = preferences.value.promptTemplate;
  }

  function openMenu(): void {
    menuErrorMessage.value = "";
    isUiPanelOpen.value = false;
    syncDraftFromPreferences();
    isMenuOpen.value = true;
  }

  function closeMenu(): void {
    menuErrorMessage.value = "";
    isMenuOpen.value = false;
  }

  function resetDraftPrompt(): void {
    draftPromptTemplate.value = DEFAULT_READING_PREFERENCES.promptTemplate;
  }

  async function saveMenuChanges(): Promise<void> {
    const targetWords = parseTargetWordsInput(draftTargetWords.value);
    const promptTemplate = draftPromptTemplate.value.trim();

    if (targetWords.length === 0) {
      menuErrorMessage.value = i18nMessages.value.menuErrorMissingWords;
      return;
    }

    if (!promptTemplate) {
      menuErrorMessage.value = i18nMessages.value.menuErrorMissingPrompt;
      return;
    }

    preferences.value = {
      targetWords,
      promptTemplate,
    };
    saveReadingPreferences(preferences.value);
    closeMenu();
    await loadSentence();
  }

  onMounted(() => {
    syncDraftFromPreferences();
    applyTheme(readingUiSettings.value.theme);
    void loadSentence();
    window.addEventListener("keydown", handleKeydown);
    window.addEventListener("keyup", handleKeyup);
  });

  onUnmounted(() => {
    abortHold();
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
