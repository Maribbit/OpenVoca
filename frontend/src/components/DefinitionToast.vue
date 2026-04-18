<template>
  <div
    class="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center"
  >
    <Transition name="def-toast">
      <div v-if="entry || notFoundWord" class="pointer-events-auto" @click.stop>
        <div
          class="flex flex-col gap-2 rounded-xl border border-ink/5 bg-surface px-4 py-2.5 shadow-lg dark:border-white/10"
        >
          <span v-if="entry" class="flex min-w-0 flex-col gap-0.5">
            <span class="flex items-center gap-2">
              <span class="font-sans text-sm font-semibold text-ink">{{
                entry.word
              }}</span>
              <span
                v-if="entry.phonetic"
                class="font-sans text-xs text-inkLight"
                >/{{ entry.phonetic }}/</span
              >
              <span
                v-if="entry.pos"
                class="rounded bg-ink/5 px-1 py-px font-mono text-[10px] leading-none text-inkLight/60 dark:bg-white/10"
                >{{ entry.pos.toUpperCase() }}</span
              >
              <button
                type="button"
                data-testid="speak-word"
                class="ml-auto shrink-0 rounded-full p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :class="{ 'animate-pulse text-ink': wordSpeaking }"
                :title="pronounceLabel"
                @click="speakWord"
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
                    d="M11 5L6 9H2v6h4l5 4V5Z"
                  />
                  <path
                    v-if="!wordSpeaking"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.54 8.46a5 5 0 0 1 0 7.07"
                  />
                </svg>
              </button>
            </span>
            <template v-if="displayMode !== 'en' && entry.translation">
              <span
                v-for="(line, i) in splitLines(entry.translation)"
                :key="'zh-' + i"
                class="font-sans text-sm leading-snug text-inkLight"
                >{{ line }}</span
              >
            </template>
            <template v-if="displayMode !== 'zh' && entry.definition">
              <span
                v-for="(line, i) in splitLines(entry.definition)"
                :key="'en-' + i"
                class="font-sans text-sm leading-snug text-inkLight"
                >{{ line }}</span
              >
            </template>
          </span>
          <span v-else class="flex min-w-0 flex-col gap-0.5">
            <span class="flex items-center gap-2">
              <span class="font-sans text-sm font-semibold text-ink">{{
                notFoundWord
              }}</span>
              <button
                type="button"
                data-testid="speak-word"
                class="ml-auto shrink-0 rounded-full p-0.5 text-inkLight/40 transition-colors hover:text-ink"
                :class="{ 'animate-pulse text-ink': wordSpeaking }"
                :title="pronounceLabel"
                @click="speakWord"
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
                    d="M11 5L6 9H2v6h4l5 4V5Z"
                  />
                  <path
                    v-if="!wordSpeaking"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.54 8.46a5 5 0 0 1 0 7.07"
                  />
                </svg>
              </button>
            </span>
            <span class="font-sans text-sm leading-snug text-inkLight/60">{{
              notFoundText
            }}</span>
          </span>

          <!-- External dictionary links -->
          <div class="flex items-center justify-center gap-2">
            <a
              :href="`https://www.merriam-webster.com/dictionary/${encodeURIComponent(lookupWord)}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >MW</a
            >
            <span class="select-none text-inkLight/20">·</span>
            <a
              :href="`https://dictionary.cambridge.org/dictionary/english/${encodeURIComponent(lookupWord)}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >Cambridge</a
            >
            <span class="select-none text-inkLight/20">·</span>
            <a
              :href="`https://dict.youdao.com/result?word=${encodeURIComponent(lookupWord)}&lang=en`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] text-inkLight/40 transition-colors hover:text-inkLight"
              >Youdao</a
            >
          </div>

          <!-- Know / Don't know toggle -->
          <div class="flex justify-center">
            <div
              class="inline-flex items-center rounded-full border border-ink/5 bg-paper p-0.5 dark:border-white/10 dark:bg-white/5"
            >
              <button
                type="button"
                class="rounded-full px-3.5 py-1 text-xs font-medium transition-all"
                :class="
                  !isMarked
                    ? 'bg-ink text-paper shadow-sm dark:bg-white dark:text-black'
                    : 'text-inkLight hover:text-ink'
                "
                @click="$emit('mark', false)"
              >
                {{ knowText }}
              </button>
              <button
                type="button"
                class="rounded-full px-3.5 py-1 text-xs font-medium transition-all"
                :class="
                  isMarked
                    ? 'bg-highlight text-ink shadow-sm'
                    : 'text-inkLight hover:text-ink'
                "
                @click="$emit('mark', true)"
              >
                {{ dontKnowText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
  import { computed, ref, onBeforeUnmount } from "vue";
  import type { DictionaryEntry } from "../api/reading";

  export type DictionaryDisplayMode = "zh" | "en" | "both";

  const props = defineProps<{
    entry: DictionaryEntry | null;
    notFoundWord: string | null;
    notFoundText: string;
    knowText: string;
    dontKnowText: string;
    isMarked: boolean;
    displayMode: DictionaryDisplayMode;
    pronounceLabel: string;
  }>();

  const lookupWord = computed(
    () => props.entry?.word ?? props.notFoundWord ?? "",
  );

  defineEmits<{
    mark: [marked: boolean];
  }>();

  const MAX_LINES = 4;

  function splitLines(text: string): string[] {
    return text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, MAX_LINES);
  }

  // --- Word pronunciation ---

  const wordSpeaking = ref(false);
  let wordAudio: HTMLAudioElement | null = null;

  function stopWordAudio(): void {
    if (wordAudio) {
      wordAudio.pause();
      wordAudio.src = "";
      wordAudio = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    wordSpeaking.value = false;
  }

  function speakWordBrowser(word: string): void {
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = "en-US";
    utterance.onend = () => {
      wordSpeaking.value = false;
    };
    wordSpeaking.value = true;
    window.speechSynthesis.speak(utterance);
  }

  function speakWord(): void {
    const word = lookupWord.value;
    if (!word) return;
    if (wordSpeaking.value) {
      stopWordAudio();
      return;
    }
    stopWordAudio();
    wordSpeaking.value = true;
    const params = new URLSearchParams({ text: word });
    const audio = new Audio(`/api/tts?${params.toString()}`);
    wordAudio = audio;
    audio.onplaying = () => {
      wordSpeaking.value = true;
    };
    audio.onended = () => {
      wordAudio = null;
      wordSpeaking.value = false;
    };
    audio.onerror = () => {
      wordAudio = null;
      wordSpeaking.value = false;
      if (window.speechSynthesis) {
        speakWordBrowser(word);
      }
    };
    audio.play().catch(() => {
      wordAudio = null;
      wordSpeaking.value = false;
      if (window.speechSynthesis) {
        speakWordBrowser(word);
      }
    });
  }

  onBeforeUnmount(() => {
    stopWordAudio();
  });
</script>

<style scoped>
  .def-toast-enter-active,
  .def-toast-leave-active {
    transition:
      transform 0.3s ease,
      opacity 0.25s ease;
  }
  .def-toast-enter-from,
  .def-toast-leave-to {
    transform: translateY(120%);
    opacity: 0;
  }
</style>
