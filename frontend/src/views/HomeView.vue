<template>
  <div class="relative min-h-screen overflow-hidden bg-paper text-ink">
    <div class="fixed inset-x-0 top-0 z-10 h-px bg-black/6">
      <div class="h-full w-1/3 bg-inkLight/55"></div>
    </div>

    <header
      class="fixed inset-x-0 top-0 z-10 flex items-center justify-between px-6 py-6 text-[11px] uppercase tracking-[0.45em] text-inkLight/50 md:px-10"
    >
      <button
        type="button"
        class="cursor-pointer rounded-full px-3 py-2 transition-colors hover:bg-black/4 hover:text-ink"
        @click="openMenu"
      >
        {{ i18nMessages.menu }}
      </button>
      <span>{{ i18nMessages.reading }}</span>
      <span>gemma3:4b</span>
    </header>

    <main class="flex min-h-screen items-center justify-center px-8 py-24">
      <article class="w-full max-w-3xl text-center">
        <p
          v-if="isLoading"
          class="sentence-fade font-serif text-3xl leading-[1.8] tracking-[0.02em] text-inkLight/65 md:text-5xl"
        >
          {{ i18nMessages.loadingSentence }}
        </p>

        <p
          v-else-if="errorMessage"
          class="sentence-fade font-serif text-3xl leading-[1.8] tracking-[0.02em] text-inkLight/75 md:text-5xl"
        >
          {{ errorMessage }}
        </p>

        <p
          v-else
          class="sentence-fade font-serif text-3xl leading-[1.8] tracking-[0.02em] text-ink md:text-5xl"
        >
          {{ sentence }}
        </p>
      </article>
    </main>

    <footer
      class="pointer-events-none fixed inset-x-0 bottom-0 px-8 py-8 text-center text-[11px] uppercase tracking-[0.35em] text-inkLight/55"
    >
      {{ i18nMessages.refreshHint }}
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

          <section>
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
                :class="
                  locale === 'zh'
                    ? 'bg-ink text-white'
                    : 'text-inkLight hover:text-ink'
                "
                @click="switchLanguage('zh')"
              >
                中文
              </button>
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                :class="
                  locale === 'en'
                    ? 'bg-ink text-white'
                    : 'text-inkLight hover:text-ink'
                "
                @click="switchLanguage('en')"
              >
                English
              </button>
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
            class="rounded-xl bg-ink px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-black"
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
  import { onMounted, ref } from "vue";

  import { fetchReadingSentence } from "../api/reading";
  import {
    DEFAULT_READING_PREFERENCES,
    formatTargetWords,
    loadReadingPreferences,
    parseTargetWordsInput,
    saveReadingPreferences,
    type ReadingPreferences,
  } from "../composables/readingPreferences";
  import { type Locale, useI18n } from "../composables/useI18n";

  const sentence = ref("");
  const errorMessage = ref("");
  const isLoading = ref(true);
  const isMenuOpen = ref(false);
  const menuErrorMessage = ref("");
  const draftTargetWords = ref("");
  const draftPromptTemplate = ref("");
  const targetWordsToken = "{{target_words}}";

  const preferences = ref<ReadingPreferences>(loadReadingPreferences());
  const { locale, messages: i18nMessages, setLocale } = useI18n();

  async function loadSentence(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      const response = await fetchReadingSentence(preferences.value);
      sentence.value = response.sentence;
    } catch {
      errorMessage.value = i18nMessages.value.ollamaError;
    } finally {
      isLoading.value = false;
    }
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
    void loadSentence();
  });
</script>
