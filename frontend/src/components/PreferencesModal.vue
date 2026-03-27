<template>
  <div
    class="fixed inset-0 z-30 flex justify-center bg-black/5 p-4 backdrop-blur-sm sm:p-8"
  >
    <main
      class="menu-fade relative flex w-full max-w-3xl flex-col overflow-hidden rounded-[28px] border border-black/6 bg-surface shadow-[0_30px_80px_rgba(44,44,44,0.12)]"
    >
      <header
        class="flex items-center justify-between border-b border-black/5 px-8 py-6"
      >
        <h1 class="font-serif text-2xl tracking-wide text-ink">
          {{ messages.preferences }}
        </h1>
        <button
          type="button"
          class="rounded-full p-2 text-inkLight transition-colors hover:bg-black/4 hover:text-ink"
          @click="$emit('close')"
        >
          <span class="sr-only">{{ messages.closeMenu }}</span>
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
        <!-- LLM Configuration -->
        <section>
          <h2
            class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
          >
            {{ messages.llmConfiguration }}
          </h2>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl border border-black/5 bg-paper p-4">
              <p class="text-xs uppercase tracking-[0.2em] text-inkLight">
                {{ messages.provider }}
              </p>
              <p class="mt-2 text-sm font-medium text-ink">
                {{ messages.localModelProvider }}
              </p>
            </div>
            <div class="rounded-2xl border border-black/5 bg-paper p-4">
              <p class="text-xs uppercase tracking-[0.2em] text-inkLight">
                {{ messages.model }}
              </p>
              <p class="mt-2 text-sm font-medium text-ink">gemma3:4b</p>
            </div>
          </div>
        </section>

        <!-- Language / Font / UI Size -->
        <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <h2
              class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ messages.language }}
            </h2>
            <div
              class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
            >
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                :class="toggleClass(locale === 'zh')"
                @click="$emit('switch-language', 'zh')"
              >
                中文
              </button>
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                :class="toggleClass(locale === 'en')"
                @click="$emit('switch-language', 'en')"
              >
                English
              </button>
            </div>
          </div>

          <div>
            <h2
              class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ messages.systemFont }}
            </h2>
            <div
              class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
            >
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                :class="toggleClass(fontFamily === 'sans')"
                @click="$emit('update:fontFamily', 'sans')"
              >
                {{ messages.uiFontSans }}
              </button>
              <button
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm transition-colors"
                :class="toggleClass(fontFamily === 'serif')"
                @click="$emit('update:fontFamily', 'serif')"
              >
                {{ messages.uiFontSerif }}
              </button>
            </div>
          </div>

          <div>
            <h2
              class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ messages.uiSize }}
            </h2>
            <div
              class="inline-flex rounded-xl border border-black/8 bg-paper p-1"
            >
              <button
                v-for="opt in uiFontSizeOptions"
                :key="opt.value"
                type="button"
                class="flex h-8 w-8 items-center justify-center rounded-lg transition-colors"
                :class="toggleClass(fontSize === opt.value)"
                @click="$emit('update:fontSize', opt.value)"
              >
                <span :class="opt.labelClass">{{ opt.label }}</span>
              </button>
            </div>
          </div>
        </section>

        <!-- Learning Parameters -->
        <section>
          <h2
            class="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
          >
            {{ messages.learningParameters }}
          </h2>
          <div class="space-y-2">
            <label
              class="flex items-center justify-between gap-4 text-sm font-medium text-ink"
              for="target-word-count"
            >
              <span>{{ messages.targetWordCount }}</span>
              <span
                class="rounded-full border border-black/8 bg-paper px-3 py-1 font-mono text-xs text-inkLight"
              >
                {{ draftTargetWordCount }}
              </span>
            </label>
            <input
              id="target-word-count"
              v-model="draftTargetWordCount"
              type="range"
              min="1"
              max="5"
              step="1"
              class="w-full accent-ink"
            />
            <div class="flex justify-between px-1 text-[11px] text-inkLight/70">
              <span>1</span>
              <span>2</span>
              <span>3</span>
              <span>4</span>
              <span>5</span>
            </div>
            <p class="text-xs text-inkLight">
              {{ messages.targetWordCountHint }}
            </p>
          </div>
        </section>

        <!-- Prompt Engineering -->
        <section>
          <div class="mb-4 flex items-center justify-between gap-4">
            <h2
              class="text-xs font-semibold uppercase tracking-[0.2em] text-inkLight"
            >
              {{ messages.promptEngineering }}
            </h2>
            <button
              type="button"
              class="text-xs text-inkLight transition-colors hover:text-ink"
              @click="draftPromptTemplate = defaultPromptTemplate"
            >
              {{ messages.resetToDefault }}
            </button>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-ink" for="prompt-template">
              {{ messages.generationPrompt }}
            </label>
            <textarea
              id="prompt-template"
              v-model="draftPromptTemplate"
              rows="6"
              class="w-full rounded-2xl border border-black/8 bg-paper px-4 py-3 font-mono text-sm leading-relaxed text-ink outline-none transition-shadow focus:ring-2 focus:ring-highlight"
            />
            <p class="text-xs text-inkLight">
              {{ messages.targetWordsTokenHintPrefix }}
              <span class="font-mono">{{ targetWordsToken }}</span>
              {{ messages.targetWordsTokenHintSuffix }}
            </p>
          </div>
        </section>

        <p v-if="errorMessage" class="text-sm text-red-600">
          {{ errorMessage }}
        </p>
      </div>

      <footer
        class="flex justify-end gap-3 border-t border-black/5 bg-black/1.5 px-8 py-4"
      >
        <button
          type="button"
          class="rounded-xl px-5 py-2.5 text-sm font-medium text-inkLight transition-colors hover:text-ink"
          @click="$emit('close')"
        >
          {{ messages.cancel }}
        </button>
        <button
          type="button"
          class="rounded-xl bg-ink px-5 py-2.5 text-sm font-medium text-paper transition-opacity hover:opacity-90"
          @click="handleSave"
        >
          {{ messages.saveChanges }}
        </button>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from "vue";
  import type { Locale } from "../composables/useI18n";

  type UiFontFamily = "sans" | "serif";
  type UiFontSizeOption = "sm" | "md" | "lg";

  interface PreferencesSnapshot {
    promptTemplate: string;
    targetWordCount: number;
  }

  const props = defineProps<{
    preferences: PreferencesSnapshot;
    defaultPromptTemplate: string;
    locale: Locale;
    fontFamily: UiFontFamily;
    fontSize: UiFontSizeOption;
    messages: {
      preferences: string;
      closeMenu: string;
      llmConfiguration: string;
      provider: string;
      localModelProvider: string;
      model: string;
      language: string;
      systemFont: string;
      uiFontSans: string;
      uiFontSerif: string;
      uiSize: string;
      learningParameters: string;
      targetWordCount: string;
      targetWordCountHint: string;
      promptEngineering: string;
      resetToDefault: string;
      generationPrompt: string;
      targetWordsTokenHintPrefix: string;
      targetWordsTokenHintSuffix: string;
      menuErrorMissingPrompt: string;
      cancel: string;
      saveChanges: string;
    };
  }>();

  const emit = defineEmits<{
    close: [];
    save: [prefs: PreferencesSnapshot];
    "switch-language": [locale: Locale];
    "update:fontFamily": [family: UiFontFamily];
    "update:fontSize": [size: UiFontSizeOption];
  }>();

  const draftTargetWordCount = ref(props.preferences.targetWordCount);
  const draftPromptTemplate = ref(props.preferences.promptTemplate);
  const errorMessage = ref("");
  const targetWordsToken = "{{target_words}}";

  watch(
    () => props.preferences,
    (next) => {
      draftTargetWordCount.value = next.targetWordCount;
      draftPromptTemplate.value = next.promptTemplate;
      errorMessage.value = "";
    },
  );

  const uiFontSizeOptions = [
    { value: "sm" as const, label: "A-", labelClass: "text-xs font-medium" },
    { value: "md" as const, label: "A", labelClass: "text-sm font-medium" },
    { value: "lg" as const, label: "A+", labelClass: "text-base font-medium" },
  ];

  function toggleClass(isActive: boolean): string {
    return isActive
      ? "bg-ink text-paper shadow-sm"
      : "text-inkLight hover:text-ink";
  }

  function handleSave(): void {
    const trimmed = draftPromptTemplate.value.trim();
    if (!trimmed) {
      errorMessage.value = props.messages.menuErrorMissingPrompt;
      return;
    }
    emit("save", {
      promptTemplate: trimmed,
      targetWordCount: draftTargetWordCount.value,
    });
  }
</script>
