<script setup lang="ts">
  import { computed, onMounted, onUnmounted } from "vue";
  import type { LocaleMessages } from "../composables/useI18n";

  export interface WordProgress {
    lemma: string;
    type: "recognized" | "unknown" | "new";
    currentLevel?: number;
    newLevel: number;
  }

  const props = defineProps<{
    words: Omit<WordProgress, "dummy">[]; // Omit trick to avoid typing issues if any
    isSubmitting?: boolean;
    messages: Pick<
      LocaleMessages,
      | "progressSummaryTitle"
      | "progressSummaryDesc"
      | "progressRecognized"
      | "progressUnknown"
      | "progressNew"
      | "progressBack"
      | "progressSubmit"
      | "progressEmpty"
    >;
  }>();

  const emit = defineEmits<{
    (e: "submit"): void;
    (e: "cancel"): void;
  }>();

  const words = computed(() => props.words);

  function handleKeydown(event: KeyboardEvent) {
    if (event.code === "Space" || event.code === "Enter") {
      // Only intercept if we are open, wait, this component is only rendered when open.
      event.preventDefault();
      emit("submit");
    } else if (event.code === "Escape") {
      event.preventDefault();
      emit("cancel");
    }
  }

  onMounted(() => {
    window.addEventListener("keydown", handleKeydown, { capture: true });
  });

  onUnmounted(() => {
    window.removeEventListener("keydown", handleKeydown, { capture: true });
  });
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-paper/90 backdrop-blur-sm transition-opacity"
    @click.self="emit('cancel')"
  >
    <div
      class="bg-surface border border-gray-700 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col transform scale-100 mx-4"
    >
      <!-- Header -->
      <div
        class="p-6 pb-5 border-b border-white/5 flex justify-between items-start"
      >
        <div>
          <h2 class="text-2xl font-serif text-ink">
            {{ messages.progressSummaryTitle }}
          </h2>
          <p class="text-sm text-inkLight mt-1">
            {{ messages.progressSummaryDesc }}
          </p>
        </div>
      </div>

      <!-- Word List -->
      <div class="p-6 flex flex-col gap-5 max-h-[60vh] overflow-y-auto">
        <template v-for="item in words" :key="item.lemma">
          <!-- Known Word -->
          <div
            v-if="item.type === 'recognized'"
            class="flex items-center justify-between group"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 shrink-0 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              </div>
              <div class="flex flex-col min-w-0">
                <span
                  class="font-sans font-medium text-ink text-[17px] truncate"
                  >{{ item.lemma }}</span
                >
                <span class="text-xs text-inkLight truncate">{{
                  messages.progressRecognized
                }}</span>
              </div>
            </div>
            <div
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-700/50 shrink-0 ml-2"
            >
              <span class="text-inkLight">Lv.{{ item.currentLevel ?? 1 }}</span>
              <svg
                class="w-4 h-4 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                ></path>
              </svg>
              <span class="text-emerald-400 font-bold"
                >Lv.{{ item.newLevel }}</span
              >
            </div>
          </div>

          <!-- Unknown Word -->
          <div
            v-else-if="item.type === 'unknown'"
            class="flex items-center justify-between group"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 shrink-0 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-400"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M6 18L18 6M6 6l12 12"
                  ></path>
                </svg>
              </div>
              <div class="flex flex-col min-w-0">
                <span
                  class="font-sans font-medium text-ink text-[17px] truncate"
                  >{{ item.lemma }}</span
                >
                <span class="text-xs text-rose-400/80 truncate">{{
                  messages.progressUnknown
                }}</span>
              </div>
            </div>
            <div
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-700/50 shrink-0 ml-2"
            >
              <span class="text-inkLight">Lv.{{ item.currentLevel ?? 1 }}</span>
              <svg
                class="w-4 h-4 text-rose-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                ></path>
              </svg>
              <span class="text-rose-400 font-bold"
                >Lv.{{ item.newLevel }}</span
              >
            </div>
          </div>

          <!-- First Time / New Word -->
          <div
            v-else-if="item.type === 'new'"
            class="flex items-center justify-between group"
          >
            <div class="flex items-center gap-4">
              <div
                class="w-10 h-10 shrink-0 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  ></path>
                </svg>
              </div>
              <div class="flex flex-col min-w-0">
                <span
                  class="font-sans font-medium text-ink text-[17px] truncate"
                  >{{ item.lemma }}</span
                >
                <span class="text-xs text-blue-400/80 truncate">{{
                  messages.progressNew
                }}</span>
              </div>
            </div>
            <div
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-700/50 shrink-0 ml-2"
            >
              <span
                class="text-inkLight px-1 border border-gray-600 rounded text-[11px] font-sans"
                >NEW</span
              >
              <svg
                class="w-4 h-4 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                ></path>
              </svg>
              <span class="text-blue-400 font-bold"
                >Lv.{{ item.newLevel }}</span
              >
            </div>
          </div>
        </template>

        <p
          v-if="words.length === 0"
          class="text-inkLight text-sm text-center py-4"
        >
          {{
            messages.progressEmpty || "No vocabulary updates for this sentence."
          }}
        </p>
      </div>

      <!-- Footer Actions -->
      <div
        class="p-6 pt-5 bg-black/5 dark:bg-black/20 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between border-t border-white/5"
      >
        <button
          @click="emit('cancel')"
          :disabled="isSubmitting"
          class="px-5 py-2.5 text-inkLight hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 rounded-xl transition-colors text-sm font-medium order-2 sm:order-1 text-center sm:text-left disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ messages.progressBack }}
        </button>
        <button
          @click="emit('submit')"
          :disabled="isSubmitting"
          class="px-8 py-2.5 bg-ink text-paper font-semibold rounded-xl shadow-lg hover:bg-inkLight transition-all flex justify-center items-center gap-2 order-1 sm:order-2 disabled:opacity-75 disabled:cursor-not-allowed"
        >
          <svg
            v-if="isSubmitting"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-paper"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {{ messages.progressSubmit }}
          <kbd
            v-if="!isSubmitting"
            class="ml-1 rounded border border-paper/30 bg-inkLight/20 px-1.5 py-0.5 font-mono text-[10px] text-paper"
            >Enter</kbd
          >
        </button>
      </div>
    </div>
  </div>
</template>
