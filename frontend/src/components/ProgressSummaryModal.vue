<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref } from "vue";
  import type { LocaleMessages } from "../composables/useI18n";
  import {
    isValidLemmaInput,
    normalizeLemmaInput,
  } from "../composables/useLemmaOverrides";

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
      | "editLemma"
    >;
  }>();

  const emit = defineEmits<{
    (e: "submit"): void;
    (e: "cancel"): void;
    (e: "lemma-change", oldLemma: string, newLemma: string): void;
  }>();

  const words = computed(() => props.words);
  const editingLemma = ref<string | null>(null);
  const draftLemma = ref("");
  const lemmaEditInvalid = computed(() => !isValidLemmaInput(draftLemma.value));

  function startLemmaEdit(lemma: string): void {
    editingLemma.value = lemma;
    draftLemma.value = lemma;
  }

  function cancelLemmaEdit(): void {
    editingLemma.value = null;
    draftLemma.value = "";
  }

  function commitLemmaEdit(): void {
    if (!editingLemma.value || lemmaEditInvalid.value) return;
    emit(
      "lemma-change",
      editingLemma.value,
      normalizeLemmaInput(draftLemma.value),
    );
    cancelLemmaEdit();
  }

  function handleKeydown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    if (target.tagName === "TEXTAREA" || target.tagName === "INPUT") return;

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
      class="bg-surface border border-ink/8 dark:border-white/10 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col transform scale-100 mx-4"
    >
      <!-- Header -->
      <div
        class="p-6 pb-5 border-b border-ink/5 dark:border-white/5 flex justify-between items-start"
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
                class="w-10 h-10 shrink-0 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 dark:text-emerald-400"
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
                <div class="flex min-w-0 items-center gap-1">
                  <template v-if="editingLemma === item.lemma">
                    <input
                      v-model="draftLemma"
                      data-testid="lemma-edit-input"
                      class="w-28 rounded border border-ink/10 bg-paper px-2 py-0.5 font-sans text-sm text-ink outline-none focus:border-ink/25 dark:border-white/10"
                      :class="{ 'border-red-400': lemmaEditInvalid }"
                      @keydown.enter.prevent="commitLemmaEdit"
                      @keydown.escape.prevent="cancelLemmaEdit"
                    />
                    <button
                      type="button"
                      data-testid="lemma-edit-save"
                      class="rounded p-0.5 text-inkLight transition-colors hover:text-ink disabled:opacity-40"
                      :disabled="lemmaEditInvalid"
                      @click="commitLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m4.5 12.75 6 6 9-13.5"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="rounded p-0.5 text-inkLight/60 transition-colors hover:text-ink"
                      @click="cancelLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M6 18 18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </template>
                  <template v-else>
                    <span
                      class="font-sans font-medium text-ink text-[17px] truncate"
                      >{{ item.lemma }}</span
                    >
                    <button
                      type="button"
                      data-testid="lemma-edit-trigger"
                      class="shrink-0 rounded p-0.5 text-inkLight/35 opacity-0 transition-all hover:text-ink group-hover:opacity-100 focus:opacity-100"
                      :title="messages.editLemma"
                      @click="startLemmaEdit(item.lemma)"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                        />
                      </svg>
                    </button>
                  </template>
                </div>
                <span class="text-xs text-inkLight truncate">{{
                  messages.progressRecognized
                }}</span>
              </div>
            </div>
            <div
              data-testid="level-delta"
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-ink/4 dark:bg-white/8 px-3 py-1.5 rounded-lg border border-ink/8 dark:border-white/10 shrink-0 ml-2"
            >
              <span class="text-inkLight">Lv.{{ item.currentLevel ?? 1 }}</span>
              <svg
                class="w-4 h-4 text-emerald-500 dark:text-emerald-400"
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
              <span class="text-emerald-500 dark:text-emerald-400 font-bold"
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
                class="w-10 h-10 shrink-0 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-500 dark:text-rose-400"
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
                <div class="flex min-w-0 items-center gap-1">
                  <template v-if="editingLemma === item.lemma">
                    <input
                      v-model="draftLemma"
                      data-testid="lemma-edit-input"
                      class="w-28 rounded border border-ink/10 bg-paper px-2 py-0.5 font-sans text-sm text-ink outline-none focus:border-ink/25 dark:border-white/10"
                      :class="{ 'border-red-400': lemmaEditInvalid }"
                      @keydown.enter.prevent="commitLemmaEdit"
                      @keydown.escape.prevent="cancelLemmaEdit"
                    />
                    <button
                      type="button"
                      data-testid="lemma-edit-save"
                      class="rounded p-0.5 text-inkLight transition-colors hover:text-ink disabled:opacity-40"
                      :disabled="lemmaEditInvalid"
                      @click="commitLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m4.5 12.75 6 6 9-13.5"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="rounded p-0.5 text-inkLight/60 transition-colors hover:text-ink"
                      @click="cancelLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M6 18 18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </template>
                  <template v-else>
                    <span
                      class="font-sans font-medium text-ink text-[17px] truncate"
                      >{{ item.lemma }}</span
                    >
                    <button
                      type="button"
                      data-testid="lemma-edit-trigger"
                      class="shrink-0 rounded p-0.5 text-inkLight/35 opacity-0 transition-all hover:text-ink group-hover:opacity-100 focus:opacity-100"
                      :title="messages.editLemma"
                      @click="startLemmaEdit(item.lemma)"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                        />
                      </svg>
                    </button>
                  </template>
                </div>
                <span
                  class="text-xs text-rose-500/80 dark:text-rose-400/80 truncate"
                  >{{ messages.progressUnknown }}</span
                >
              </div>
            </div>
            <div
              data-testid="level-delta"
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-ink/4 dark:bg-white/8 px-3 py-1.5 rounded-lg border border-ink/8 dark:border-white/10 shrink-0 ml-2"
            >
              <span class="text-inkLight">Lv.{{ item.currentLevel ?? 1 }}</span>
              <svg
                class="w-4 h-4 text-rose-500 dark:text-rose-400"
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
              <span class="text-rose-500 dark:text-rose-400 font-bold"
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
                class="w-10 h-10 shrink-0 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 dark:text-blue-400"
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
                <div class="flex min-w-0 items-center gap-1">
                  <template v-if="editingLemma === item.lemma">
                    <input
                      v-model="draftLemma"
                      data-testid="lemma-edit-input"
                      class="w-28 rounded border border-ink/10 bg-paper px-2 py-0.5 font-sans text-sm text-ink outline-none focus:border-ink/25 dark:border-white/10"
                      :class="{ 'border-red-400': lemmaEditInvalid }"
                      @keydown.enter.prevent="commitLemmaEdit"
                      @keydown.escape.prevent="cancelLemmaEdit"
                    />
                    <button
                      type="button"
                      data-testid="lemma-edit-save"
                      class="rounded p-0.5 text-inkLight transition-colors hover:text-ink disabled:opacity-40"
                      :disabled="lemmaEditInvalid"
                      @click="commitLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m4.5 12.75 6 6 9-13.5"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      class="rounded p-0.5 text-inkLight/60 transition-colors hover:text-ink"
                      @click="cancelLemmaEdit"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M6 18 18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </template>
                  <template v-else>
                    <span
                      class="font-sans font-medium text-ink text-[17px] truncate"
                      >{{ item.lemma }}</span
                    >
                    <button
                      type="button"
                      data-testid="lemma-edit-trigger"
                      class="shrink-0 rounded p-0.5 text-inkLight/35 opacity-0 transition-all hover:text-ink group-hover:opacity-100 focus:opacity-100"
                      :title="messages.editLemma"
                      @click="startLemmaEdit(item.lemma)"
                    >
                      <svg
                        class="h-3.5 w-3.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L7.5 19.152 3.75 20.25l1.098-3.75 13.701-13.701Z"
                        />
                      </svg>
                    </button>
                  </template>
                </div>
                <span
                  class="text-xs text-blue-500/80 dark:text-blue-400/80 truncate"
                  >{{ messages.progressNew }}</span
                >
              </div>
            </div>
            <div
              data-testid="level-delta"
              class="flex items-center gap-3 text-sm font-mono tracking-tight bg-ink/4 dark:bg-white/8 px-3 py-1.5 rounded-lg border border-ink/8 dark:border-white/10 shrink-0 ml-2"
            >
              <span
                data-testid="new-word-badge"
                class="text-inkLight px-1 border border-ink/15 dark:border-white/15 rounded text-[11px] font-sans"
                >NEW</span
              >
              <svg
                class="w-4 h-4 text-blue-500 dark:text-blue-400"
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
              <span class="text-blue-500 dark:text-blue-400 font-bold"
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
        class="p-6 pt-5 bg-black/5 dark:bg-black/20 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between border-t border-ink/5 dark:border-white/5"
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
