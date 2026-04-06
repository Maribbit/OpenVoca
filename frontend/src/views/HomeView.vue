<template>
  <div
    class="relative min-h-zoom-screen overflow-hidden bg-paper font-sans text-ink transition-colors duration-300"
  >
    <header
      class="group fixed inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-6 uppercase tracking-[0.45em] text-inkLight/50 md:px-10"
      :class="uiHeaderSizeClass"
    >
      <div class="flex flex-1 items-center justify-start gap-1">
        <router-link
          to="/settings"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:text-ink"
        >
          {{ i18nMessages.menu }}
        </router-link>
        <button
          type="button"
          data-testid="reading-settings-trigger"
          class="cursor-pointer rounded-full p-2 transition-all hover:text-ink opacity-0 group-hover:opacity-100 focus:opacity-100"
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
      </div>

      <div
        class="pointer-events-none flex flex-1 items-center justify-center"
      ></div>

      <div class="flex flex-1 items-center justify-end">
        <router-link
          to="/stats"
          class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:text-ink"
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
      class="flex min-h-zoom-screen flex-col items-center justify-center gap-14 px-8 py-24"
    >
      <template v-if="showComposer">
        <ComposerCard @generate="onComposerGenerate" />
      </template>

      <template v-else>
        <SentenceDisplay
          :tokens="tokens"
          :marked-words="markedWords"
          :is-loading="isLoading"
          :error-message="errorMessage"
          :loading-text="i18nMessages.loadingSentence"
          :typography-class="sentenceTypographyClass"
          @word-click="onWordClick"
        />

        <div v-if="tokens.length > 0" class="flex items-center gap-1">
          <button
            type="button"
            class="cursor-pointer rounded-full p-2 transition-colors hover:bg-black/4"
            :class="
              copyConfirmed
                ? 'text-emerald-500'
                : 'text-inkLight/40 hover:text-inkLight'
            "
            :title="i18nMessages.copySentence"
            @click="copySentence"
          >
            <svg
              v-if="!copyConfirmed"
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9.75a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184"
              />
            </svg>
            <svg
              v-else
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4.5 12.75l6 6 9-13.5"
              />
            </svg>
          </button>
          <button
            type="button"
            class="cursor-pointer rounded-full p-2 transition-colors hover:bg-black/4"
            :class="
              isSpeaking ? 'text-ink' : 'text-inkLight/40 hover:text-inkLight'
            "
            :title="i18nMessages.readAloud"
            @click="readAloud"
          >
            <svg
              v-if="!isSpeaking"
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
              />
            </svg>
            <svg v-else class="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path
                fill-rule="evenodd"
                d="M4.5 7.5a3 3 0 0 1 3-3h9a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-9Z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>

        <HoldButton
          ref="holdButtonRef"
          :disabled="isLoading || isUiPanelOpen"
          :hold-text="i18nMessages.nextSentenceHint"
          :release-text="i18nMessages.releaseHint"
          :header-size-class="uiHeaderSizeClass"
          @advance="goToNextSentence"
        />
      </template>
    </main>

    <DefinitionToast
      :entry="definitionEntry"
      :not-found-word="definitionNotFound"
      :not-found-text="i18nMessages.definitionNotFound"
      :know-text="i18nMessages.definitionKnow"
      :dont-know-text="i18nMessages.definitionDontKnow"
      :is-marked="isCurrentWordMarked"
      :display-mode="dictionaryDisplayMode"
      @mark="onDefinitionMark"
    />

    <Transition name="fade">
      <p
        v-if="feedbackError"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg"
      >
        {{ feedbackError }}
      </p>
    </Transition>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref, watch } from "vue";

  import {
    fetchNextReadingSentence,
    fetchDefinition,
    submitFeedback,
    tokensToPlainText,
    type DictionaryEntry,
    type ReadingSentenceToken,
  } from "../api/reading";
  import { useI18n } from "../composables/useI18n";
  import { useSettings } from "../composables/useSettings";
  import ComposerCard from "../components/ComposerCard.vue";
  import DefinitionToast from "../components/DefinitionToast.vue";
  import type { DictionaryDisplayMode } from "../components/DefinitionToast.vue";
  import HoldButton from "../components/HoldButton.vue";
  import ReadingSettingsBar from "../components/ReadingSettingsBar.vue";
  import type {
    ReadingUiSettings,
    ThemeOption,
  } from "../components/ReadingSettingsBar.vue";
  import SentenceDisplay from "../components/SentenceDisplay.vue";

  type FontSizeOption = "sm" | "md" | "lg";
  type SpacingOption = "tight" | "normal" | "loose";
  type UiFontSizeOption = "xs" | "sm" | "md" | "lg" | "xl";

  const FONT_SIZE_OPTIONS: FontSizeOption[] = ["sm", "md", "lg"];
  const SPACING_OPTIONS: SpacingOption[] = ["tight", "normal", "loose"];
  const THEME_OPTIONS: ThemeOption[] = ["light", "dark"];

  const DEFAULT_READING_UI_SETTINGS: ReadingUiSettings = {
    fontSize: "md",
    spacing: "normal",
    theme: "light",
  };

  const { get, set } = useSettings();

  const sentence = ref("");
  const tokens = ref<ReadingSentenceToken[]>([]);
  const errorMessage = ref("");
  const feedbackError = ref("");
  const isLoading = ref(false);
  const isUiPanelOpen = ref(false);
  const markedWords = ref<Set<string>>(new Set());
  const showComposer = ref(true);
  const copyConfirmed = ref(false);
  const isSpeaking = ref(false);

  const holdButtonRef = ref<InstanceType<typeof HoldButton> | null>(null);

  const definitionEntry = ref<DictionaryEntry | null>(null);
  const definitionWord = ref<string | null>(null);
  const definitionNotFound = ref<string | null>(null);
  const definitionToken = ref<ReadingSentenceToken | null>(null);
  let wordClickedThisFrame = false;

  const isCurrentWordMarked = computed(() => {
    if (!definitionToken.value) return false;
    return markedWords.value.has(tokenKey(definitionToken.value));
  });

  const readingUiSettings = ref<ReadingUiSettings>(loadReadingUiSettings());
  const uiFontSize = ref<UiFontSizeOption>(loadUiFontSize());
  const { messages: i18nMessages } = useI18n();

  const dictionaryDisplayMode = computed<DictionaryDisplayMode>(() => {
    const v = get("dictionary", "display", "both");
    if (v === "zh" || v === "en") return v;
    return "both";
  });

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
      xs: "text-[11px]",
      sm: "text-[12px]",
      md: "text-[13px]",
      lg: "text-[14px]",
      xl: "text-[15px]",
    };
    return map[uiFontSize.value];
  });

  // --- Persistence helpers ---

  function loadReadingUiSettings(): ReadingUiSettings {
    const fs = get("reading", "fontSize", "md");
    const sp = get("reading", "spacing", "normal");
    const th = get("reading", "theme", "light");
    return {
      fontSize: FONT_SIZE_OPTIONS.includes(fs as FontSizeOption)
        ? (fs as FontSizeOption)
        : DEFAULT_READING_UI_SETTINGS.fontSize,
      spacing: SPACING_OPTIONS.includes(sp as SpacingOption)
        ? (sp as SpacingOption)
        : DEFAULT_READING_UI_SETTINGS.spacing,
      theme: THEME_OPTIONS.includes(th as ThemeOption)
        ? (th as ThemeOption)
        : DEFAULT_READING_UI_SETTINGS.theme,
    };
  }

  function saveReadingUiSettings(): void {
    const s = readingUiSettings.value;
    set("reading", {
      fontSize: s.fontSize,
      spacing: s.spacing,
      theme: s.theme,
    });
  }

  function loadUiFontSize(): UiFontSizeOption {
    const saved = get("interface", "uiFontSize", "md");
    const valid: UiFontSizeOption[] = ["xs", "sm", "md", "lg", "xl"];
    if (valid.includes(saved as UiFontSizeOption))
      return saved as UiFontSizeOption;
    return "md";
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

  function copySentence(): void {
    navigator.clipboard.writeText(tokensToPlainText(tokens.value));
    copyConfirmed.value = true;
    setTimeout(() => {
      copyConfirmed.value = false;
    }, 1500);
  }

  function readAloud(): void {
    if (isSpeaking.value) {
      window.speechSynthesis.cancel();
      isSpeaking.value = false;
      return;
    }
    const text = tokensToPlainText(tokens.value);
    if (!text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.onend = () => {
      isSpeaking.value = false;
    };
    isSpeaking.value = true;
    window.speechSynthesis.speak(utterance);
  }

  function onReadingSettingsChange(next: ReadingUiSettings): void {
    readingUiSettings.value = next;
    applyTheme(next.theme);
  }

  // --- Sentence & feedback ---

  function tokenKey(token: ReadingSentenceToken): string {
    return `${token.text.toLowerCase()}/${token.pos ?? ""}`;
  }

  function dismissDefinition(): void {
    definitionEntry.value = null;
    definitionWord.value = null;
    definitionNotFound.value = null;
    definitionToken.value = null;
  }

  async function onWordClick(token: ReadingSentenceToken): Promise<void> {
    wordClickedThisFrame = true;
    const word = (token.lemma ?? token.text).toLowerCase();

    // If the same word is already showing, toggle know/don't-know
    if (
      definitionToken.value &&
      tokenKey(definitionToken.value) === tokenKey(token)
    ) {
      onDefinitionMark(!isCurrentWordMarked.value);
      return;
    }

    // Show definition for clicked word
    definitionWord.value = word;
    definitionToken.value = token;
    definitionNotFound.value = null;
    try {
      const entry = await fetchDefinition(word);
      if (definitionWord.value === word) {
        definitionEntry.value = entry;
        definitionNotFound.value = entry ? null : word;
      }
    } catch {
      if (definitionWord.value === word) {
        definitionEntry.value = null;
        definitionNotFound.value = word;
      }
    }
  }

  function onDefinitionMark(marked: boolean): void {
    if (!definitionToken.value) return;
    const key = tokenKey(definitionToken.value);
    const next = new Set(markedWords.value);
    if (marked) {
      next.add(key);
    } else {
      next.delete(key);
    }
    markedWords.value = next;
  }

  function onDocumentClick(): void {
    if (wordClickedThisFrame) {
      wordClickedThisFrame = false;
      return;
    }
    if (definitionEntry.value || definitionNotFound.value) {
      dismissDefinition();
    }
  }

  async function loadSentence(
    prompt: string,
    targetWords: string[],
  ): Promise<void> {
    isLoading.value = true;
    errorMessage.value = "";
    try {
      const response = await fetchNextReadingSentence({
        prompt,
        targetWords,
      });
      sentence.value = response.sentence;
      tokens.value = response.tokens;
      markedWords.value = new Set();
      dismissDefinition();
    } catch {
      errorMessage.value = i18nMessages.value.connectionError;
      tokens.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function goToNextSentence(): Promise<void> {
    if (isLoading.value) return;

    if (sentence.value) {
      const targetEntries = tokens.value
        .filter((t) => t.isTarget && t.pos && t.lemma)
        .map((t) => ({ lemma: t.lemma!, pos: t.pos! }));
      const markedEntries = tokens.value
        .filter(
          (t) =>
            t.isWord && t.pos && t.lemma && markedWords.value.has(tokenKey(t)),
        )
        .map((t) => ({ lemma: t.lemma!, pos: t.pos! }));

      try {
        await submitFeedback({
          targetWords: targetEntries,
          markedWords: markedEntries,
          sentence: sentence.value,
        });
      } catch {
        feedbackError.value = i18nMessages.value.feedbackError;
        setTimeout(() => {
          feedbackError.value = "";
        }, 4000);
      }
    }

    showComposer.value = true;
    dismissDefinition();
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      isSpeaking.value = false;
    }
  }

  async function onComposerGenerate(
    prompt: string,
    targetWords: string[],
  ): Promise<void> {
    showComposer.value = false;
    await loadSentence(prompt, targetWords);
  }

  // --- Keyboard ---

  function handleKeydown(event: KeyboardEvent): void {
    if (event.code === "Space" && !isUiPanelOpen.value && !showComposer.value) {
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
    window.addEventListener("keydown", handleKeydown);
    window.addEventListener("keyup", handleKeyup);
    document.addEventListener("click", onDocumentClick);
  });

  onUnmounted(() => {
    holdButtonRef.value?.abortHold();
    window.removeEventListener("keydown", handleKeydown);
    window.removeEventListener("keyup", handleKeyup);
    document.removeEventListener("click", onDocumentClick);
  });

  watch(
    readingUiSettings,
    () => {
      saveReadingUiSettings();
    },
    { deep: true },
  );
</script>
