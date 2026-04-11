<template>
  <div class="w-full max-w-xl mx-auto fade-enter">
    <!-- Composer Card -->
    <div
      class="w-full bg-surface/80 backdrop-blur-md rounded-2xl border border-ink/5 shadow-sm p-5 space-y-6"
    >
      <!-- Target Words -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <span
            class="text-xs font-semibold uppercase tracking-[0.15em] text-inkLight"
            >{{ t.composerTargetWords }}</span
          >
          <button
            type="button"
            class="text-inkLight/40 hover:text-inkLight transition-colors cursor-pointer"
            :title="t.composerRefreshSuggestions"
            @click="loadTargetWords"
          >
            <svg
              class="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
          </button>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="word in suggestedWords"
            :key="'s-' + word"
            type="button"
            :class="[
              'suggestion-chip',
              activeSuggestions.has(word) ? 'active' : 'inactive',
            ]"
            @click="toggleSuggestion(word)"
          >
            {{ word }}
          </button>
          <span
            v-for="(word, idx) in customWords"
            :key="'c-' + idx"
            class="custom-chip"
          >
            {{ word
            }}<span class="remove-btn" @click.stop="removeCustomWord(idx)"
              >×</span
            >
          </span>
          <button
            v-if="!addingWord"
            type="button"
            class="inline-flex items-center justify-center w-7 h-7 rounded-full border border-dashed border-ink/15 text-inkLight hover:border-ink/30 hover:text-ink transition-all cursor-pointer"
            @click="startAddWord"
          >
            <svg
              class="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
          </button>
          <input
            v-if="addingWord"
            ref="addWordInputRef"
            v-model="newWordText"
            type="text"
            :placeholder="t.composerAddWordPlaceholder"
            class="w-24 px-3 py-1.5 rounded-full border border-dashed border-ink/20 text-xs text-ink placeholder:text-inkLight/40 focus:outline-none focus:border-ink/30 transition-colors bg-transparent"
            @keydown.enter="confirmAddWord"
            @keydown.escape="cancelAddWord"
            @blur="cancelAddWord"
          />
        </div>
      </div>

      <!-- Scenario -->
      <div>
        <span
          class="text-xs font-semibold uppercase tracking-[0.15em] text-inkLight block mb-3"
          >{{ t.composerScenario }}</span
        >
        <div class="grid grid-cols-5 gap-2">
          <button
            v-for="s in SCENARIOS"
            :key="s.key"
            :class="['scenario-card', { active: selectedScenario === s.key }]"
            @click="selectScenario(s.key)"
          >
            <span class="scenario-emoji">{{ s.emoji }}</span>
            <span class="scenario-label">{{ scenarioLabel(s.key) }}</span>
          </button>
        </div>
        <!-- Supplement: expand button for presets, always-open for Custom -->
        <div class="mt-3">
          <button
            v-if="
              selectedScenario !== 'none' &&
              !supplementOpen &&
              !customScenario.trim()
            "
            @click="supplementOpen = true"
            class="text-xs text-inkLight/50 hover:text-inkLight transition-colors cursor-pointer"
          >
            + {{ t.composerAddDetails }}
          </button>
          <textarea
            v-else
            rows="2"
            :placeholder="customPlaceholder"
            v-model="customScenario"
            class="w-full px-3.5 py-2.5 bg-paper/80 border border-ink/8 rounded-xl text-sm text-ink placeholder:text-inkLight/50 focus:outline-none focus:ring-2 focus:ring-highlight/80 transition-shadow resize-none leading-relaxed"
          ></textarea>
        </div>
      </div>

      <!-- Difficulty (collapsible) -->
      <div>
        <button
          @click="difficultyOpen = !difficultyOpen"
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-inkLight hover:text-ink transition-colors cursor-pointer w-full"
        >
          <svg
            class="w-3 h-3 transition-transform"
            :class="{ 'rotate-90': difficultyOpen }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
          {{ t.composerDifficulty }}
          <span
            v-if="!difficultyOpen"
            class="ml-auto text-[11px] font-normal normal-case tracking-normal text-inkLight/60"
          >
            {{ currentDifficultyLabel }}
          </span>
        </button>
        <div v-if="difficultyOpen" class="flex gap-2 mt-3">
          <button
            v-for="opt in difficultyOptions"
            :key="opt.value"
            :class="['option-card', { active: difficulty === opt.value }]"
            @click="difficulty = opt.value"
          >
            <span class="opt-label">{{ opt.label }}</span>
            <span class="opt-desc">{{ opt.desc }}</span>
          </button>
        </div>
        <div v-if="difficultyOpen && difficulty === 'custom'" class="mt-2">
          <textarea
            rows="2"
            :placeholder="t.composerCustomDifficultyPlaceholder"
            v-model="customDifficulty"
            class="w-full px-3.5 py-2.5 bg-paper/80 border border-ink/8 rounded-xl text-sm text-ink placeholder:text-inkLight/50 focus:outline-none focus:ring-2 focus:ring-highlight/80 transition-shadow resize-none leading-relaxed"
          ></textarea>
        </div>
      </div>

      <!-- Length (collapsible) -->
      <div>
        <button
          @click="lengthOpen = !lengthOpen"
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-inkLight hover:text-ink transition-colors cursor-pointer w-full"
        >
          <svg
            class="w-3 h-3 transition-transform"
            :class="{ 'rotate-90': lengthOpen }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
          {{ t.composerLength }}
          <span
            v-if="!lengthOpen"
            class="ml-auto text-[11px] font-normal normal-case tracking-normal text-inkLight/60"
          >
            {{ currentLengthLabel }}
          </span>
        </button>
        <div v-if="lengthOpen" class="flex gap-2 mt-3">
          <button
            v-for="opt in lengthOptions"
            :key="opt.value"
            :class="['option-card', { active: length === opt.value }]"
            @click="length = opt.value"
          >
            <span class="opt-label">{{ opt.label }}</span>
          </button>
        </div>
        <div v-if="lengthOpen && length === 'custom'" class="mt-2">
          <textarea
            rows="2"
            :placeholder="t.composerCustomLengthPlaceholder"
            v-model="customLength"
            class="w-full px-3.5 py-2.5 bg-paper/80 border border-ink/8 rounded-xl text-sm text-ink placeholder:text-inkLight/50 focus:outline-none focus:ring-2 focus:ring-highlight/80 transition-shadow resize-none leading-relaxed"
          ></textarea>
        </div>
      </div>

      <!-- Prompt Preview -->
      <div>
        <button
          @click="previewOpen = !previewOpen"
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-inkLight hover:text-ink transition-colors cursor-pointer w-full"
        >
          <svg
            class="w-3 h-3 transition-transform"
            :class="{ 'rotate-90': previewOpen }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
          {{ t.composerPreview }}
        </button>
        <div v-if="previewOpen" class="mt-3">
          <pre
            class="w-full px-3.5 py-2.5 bg-paper/80 border border-ink/6 rounded-xl text-xs text-inkLight/70 font-mono leading-relaxed whitespace-pre-wrap overflow-auto max-h-40"
            >{{ fullPreviewText }}</pre
          >
        </div>
      </div>
    </div>

    <!-- Generate button -->
    <div class="flex flex-col items-center mt-8">
      <button
        @click="emitGenerate"
        class="px-8 py-3 bg-ink text-paper rounded-full text-sm font-medium shadow-sm hover:bg-ink/85 active:scale-95 transition-all cursor-pointer"
      >
        {{ t.composerGenerate }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { nextTick, onMounted, ref, computed, watch } from "vue";

  import { fetchTargetWords } from "../api/reading";
  import { DEFAULT_READING_PREFERENCES } from "../composables/readingPreferences";
  import { useI18n } from "../composables/useI18n";
  import { useSettings } from "../composables/useSettings";

  const emit = defineEmits<{
    generate: [prompt: string, targetWords: string[]];
  }>();

  const { messages: t } = useI18n();
  const { get, set } = useSettings();

  // --- Target Words ---
  const suggestedWords = ref<string[]>([]);
  const activeSuggestions = ref<Set<string>>(new Set());
  const customWords = ref<string[]>([]);
  const addingWord = ref(false);
  const newWordText = ref("");
  const addWordInputRef = ref<HTMLInputElement | null>(null);

  const effectiveTargetWords = computed<string[]>(() => [
    ...suggestedWords.value.filter((w) => activeSuggestions.value.has(w)),
    ...customWords.value,
  ]);

  async function loadTargetWords(): Promise<void> {
    const poolSize = Number(get("generation", "suggestionPoolSize", "3"));
    const autoSelect = Number(get("generation", "targetWordCount", "1"));
    try {
      const words = await fetchTargetWords(poolSize);
      suggestedWords.value = words;
      activeSuggestions.value = new Set(words.slice(0, autoSelect));
    } catch {
      suggestedWords.value = [];
      activeSuggestions.value = new Set();
    }
  }

  function toggleSuggestion(word: string): void {
    const next = new Set(activeSuggestions.value);
    if (next.has(word)) {
      next.delete(word);
    } else {
      next.add(word);
    }
    activeSuggestions.value = next;
  }

  function removeCustomWord(idx: number): void {
    customWords.value.splice(idx, 1);
  }

  function startAddWord(): void {
    addingWord.value = true;
    nextTick(() => addWordInputRef.value?.focus());
  }

  function confirmAddWord(): void {
    const word = newWordText.value.trim().toLowerCase();
    const allWords = [...suggestedWords.value, ...customWords.value];
    if (word && !allWords.includes(word)) {
      customWords.value.push(word);
    }
    newWordText.value = "";
    addingWord.value = false;
  }

  function cancelAddWord(): void {
    newWordText.value = "";
    addingWord.value = false;
  }

  onMounted(() => {
    loadTargetWords();
  });

  const SCENARIO_PROMPTS: Record<string, string> = {
    absurd_headlines:
      "You are a deadpan news broadcaster reporting a story with complete " +
      "professional composure. The story itself is utterly absurd or impossible " +
      "— but you deliver it with the same measured, straight-faced gravity you " +
      "would give any ordinary report. The story can belong to any beat: local " +
      "news, science, culture, sports, weather, economics, or anything else. " +
      "Let the absurdity speak for itself; never wink at the audience.",
    poetry:
      "Write as a poet — use vivid imagery, metaphor, and rhythm. " +
      "Let the language be evocative and musical.",
    fun_facts:
      "Share a surprising, little-known fact in an engaging, " +
      "conversational tone — the kind of thing that makes people say " +
      "'wait, really?' Connect it to everyday life when possible.",
    slice_of_life:
      "Randomly adopt an everyday voice: it could be a diary entry, a casual " +
      "conversation, a letter to a friend, an overheard remark, a text message, " +
      "a monologue, or any other natural, personal form of expression. " +
      "Don't announce which one you chose; just write naturally in that voice.",
  };

  const DIFFICULTY_INSTRUCTIONS: Record<string, string> = {
    easy: "Use simple vocabulary and short sentence structures (CEFR A2\u2013B1 level).",
    normal:
      "Use intermediate vocabulary and natural sentence structures (CEFR B1\u2013B2 level).",
    challenge:
      "Use advanced vocabulary and complex sentence structures (CEFR C1\u2013C2 level).",
  };

  const LENGTH_INSTRUCTIONS: Record<string, string> = {
    brief: "Keep the output very short and concise.",
    sentence: "Use a natural, moderate length.",
    narrative:
      "Write at length with rich descriptive detail and subordinate clauses.",
  };

  // --- Scenarios ---
  const SCENARIOS = [
    { key: "slice_of_life", emoji: "💬" },
    { key: "fun_facts", emoji: "🧠" },
    { key: "absurd_headlines", emoji: "📰" },
    { key: "poetry", emoji: "📜" },
    { key: "none", emoji: "✍️" },
  ] as const;

  const SCENARIO_KEYS = SCENARIOS.map((s) => s.key) as unknown as string[];

  const savedScenario = get("composer", "scenario", "slice_of_life");
  const selectedScenario = ref<string>(
    SCENARIO_KEYS.includes(savedScenario) ? savedScenario : "slice_of_life",
  );

  const savedCustom = get("composer", "customScenario", "");
  const customScenario = ref(savedCustom);
  const supplementOpen = ref(false);

  watch(selectedScenario, (newKey) => {
    if (newKey !== "none" && !customScenario.value.trim()) {
      supplementOpen.value = false;
    }
  });

  function selectScenario(key: string) {
    if (selectedScenario.value === key && key !== "none") {
      selectedScenario.value = "none";
    } else {
      selectedScenario.value = key;
    }
  }

  function scenarioLabel(key: string): string {
    const k = `composerScenario_${key}` as keyof typeof t.value;
    return (t.value[k] as string) ?? key;
  }

  const customPlaceholder = computed(() =>
    selectedScenario.value in SCENARIO_PROMPTS
      ? t.value.composerCustomPlaceholderSupplement
      : t.value.composerCustomPlaceholder,
  );

  // --- Difficulty ---
  const savedDiff = get("composer", "difficulty", "easy");
  const difficulty = ref<"easy" | "normal" | "challenge" | "custom">(
    ["easy", "normal", "challenge", "custom"].includes(savedDiff)
      ? (savedDiff as "easy" | "normal" | "challenge" | "custom")
      : "easy",
  );

  const savedCustomDiff = get("composer", "customDifficulty", "");
  const customDifficulty = ref(savedCustomDiff);

  const difficultyOptions = computed(() => [
    { value: "easy" as const, label: t.value.composerDiffEasy, desc: "A2–B1" },
    {
      value: "normal" as const,
      label: t.value.composerDiffNormal,
      desc: "B1–B2",
    },
    {
      value: "challenge" as const,
      label: t.value.composerDiffChallenge,
      desc: "C1–C2",
    },
    {
      value: "custom" as const,
      label: t.value.composerCustom,
      desc: "✍️",
    },
  ]);

  const difficultyOpen = ref(false);

  const currentDifficultyLabel = computed(() => {
    if (difficulty.value === "custom") {
      const cd = customDifficulty.value.trim();
      return cd || t.value.composerNoLimit;
    }
    const opt = difficultyOptions.value.find(
      (o) => o.value === difficulty.value,
    );
    return opt ? `${opt.label} · ${opt.desc}` : "";
  });

  // --- Length ---
  type LengthKey = "brief" | "sentence" | "narrative" | "custom";
  const LENGTH_KEYS: LengthKey[] = ["brief", "sentence", "narrative", "custom"];

  const savedLength = get("composer", "length", "brief");
  const length = ref<LengthKey>(
    LENGTH_KEYS.includes(savedLength as LengthKey)
      ? (savedLength as LengthKey)
      : "brief",
  );

  const savedCustomLen = get("composer", "customLength", "");
  const customLength = ref(savedCustomLen);

  const lengthOptions = computed(() => [
    {
      value: "brief" as const,
      label: t.value.composerLenBrief,
    },
    {
      value: "sentence" as const,
      label: t.value.composerLenSentence,
    },
    {
      value: "narrative" as const,
      label: t.value.composerLenNarrative,
    },
    {
      value: "custom" as const,
      label: t.value.composerCustom,
    },
  ]);

  const lengthOpen = ref(false);

  const currentLengthLabel = computed(() => {
    if (length.value === "custom") {
      const cl = customLength.value.trim();
      return cl || t.value.composerNoLimit;
    }
    const opt = lengthOptions.value.find((o) => o.value === length.value);
    return opt ? opt.label : "";
  });

  // --- Preview ---
  const previewOpen = ref(false);

  const composerInstructions = computed(() => {
    const parts: string[] = [];

    const custom = customScenario.value.trim();
    if (selectedScenario.value in SCENARIO_PROMPTS) {
      const base = SCENARIO_PROMPTS[selectedScenario.value];
      parts.push(
        custom ? `[Scenario] ${base} ${custom}` : `[Scenario] ${base}`,
      );
    } else if (custom) {
      parts.push(`[Scenario] ${custom}`);
    }

    if (difficulty.value === "custom") {
      const cd = customDifficulty.value.trim();
      if (cd) {
        parts.push(`[Difficulty] ${cd}`);
      }
    } else if (difficulty.value in DIFFICULTY_INSTRUCTIONS) {
      parts.push(`[Difficulty] ${DIFFICULTY_INSTRUCTIONS[difficulty.value]}`);
    }

    if (length.value === "custom") {
      const cl = customLength.value.trim();
      if (cl) {
        parts.push(`[Length] ${cl}`);
      }
    } else if (length.value in LENGTH_INSTRUCTIONS) {
      parts.push(`[Length] ${LENGTH_INSTRUCTIONS[length.value]}`);
    }

    return parts.length ? parts.join("\n") : "";
  });

  // --- Prompt Template (read-only, for preview) ---
  const DEFAULT_PROMPT_TEMPLATE = DEFAULT_READING_PREFERENCES.promptTemplate;

  const promptTemplate = ref(
    get("generation", "promptTemplate", DEFAULT_PROMPT_TEMPLATE),
  );

  /** Build the full prompt from template + target words + composer instructions. */
  function buildPrompt(words: string[]): string {
    const template = promptTemplate.value.trim() || DEFAULT_PROMPT_TEMPLATE;

    const wordsText = words.length ? words.join(", ") : "";
    const resolved = template.includes("{{target_words}}")
      ? template.replace("{{target_words}}", wordsText)
      : template;

    const ci = composerInstructions.value;
    return ci ? resolved + "\n" + ci : resolved;
  }

  const fullPreviewText = computed(() => {
    const words = effectiveTargetWords.value.length
      ? effectiveTargetWords.value
      : ["(no words selected)"];
    return buildPrompt(words);
  });

  // --- Emit ---
  function emitGenerate() {
    set("composer", {
      scenario: selectedScenario.value,
      customScenario: customScenario.value,
      difficulty: difficulty.value,
      customDifficulty: customDifficulty.value,
      length: length.value,
      customLength: customLength.value,
    });

    emit(
      "generate",
      buildPrompt(effectiveTargetWords.value),
      effectiveTargetWords.value,
    );
  }
</script>

<style scoped>
  .suggestion-chip {
    display: inline-flex;
    align-items: center;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    user-select: none;
  }
  .suggestion-chip.active {
    background: var(--color-ink);
    color: var(--color-paper);
  }
  .suggestion-chip.active:hover {
    opacity: 0.8;
  }
  .suggestion-chip.inactive {
    background: transparent;
    border: 1px dashed color-mix(in srgb, var(--color-ink) 20%, transparent);
    color: color-mix(in srgb, var(--color-inkLight) 45%, transparent);
  }
  .suggestion-chip.inactive:hover {
    border-color: color-mix(in srgb, var(--color-ink) 40%, transparent);
    color: var(--color-inkLight);
  }
  .custom-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px 5px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 500;
    background: color-mix(in srgb, var(--color-ink) 8%, transparent);
    color: var(--color-ink);
    border: 1px solid color-mix(in srgb, var(--color-ink) 10%, transparent);
    transition: all 0.15s;
  }
  .custom-chip .remove-btn {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: color-mix(in srgb, var(--color-ink) 10%, transparent);
    font-size: 11px;
    line-height: 1;
    transition: background 0.15s;
    cursor: pointer;
  }
  .custom-chip .remove-btn:hover {
    background: color-mix(in srgb, var(--color-ink) 20%, transparent);
  }

  .scenario-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 10px 4px 8px;
    border-radius: 12px;
    cursor: pointer;
    border: 1px solid color-mix(in srgb, var(--color-ink) 8%, transparent);
    background: var(--color-surface);
    transition: all 0.15s;
    text-align: center;
    color: var(--color-inkLight);
  }
  .scenario-card:hover {
    border-color: color-mix(in srgb, var(--color-ink) 18%, transparent);
    transform: translateY(-1px);
  }
  .scenario-card.active {
    background: var(--color-ink);
    color: var(--color-paper);
    border-color: transparent;
  }
  .scenario-card.active:hover {
    opacity: 0.9;
  }
  .scenario-emoji {
    font-size: 22px;
    line-height: 1;
  }
  .scenario-label {
    font-size: 10px;
    font-weight: 500;
    line-height: 1.2;
  }

  .option-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 8px 0;
    border-radius: 12px;
    cursor: pointer;
    border: 1px solid color-mix(in srgb, var(--color-ink) 8%, transparent);
    background: var(--color-surface);
    transition: all 0.15s;
    text-align: center;
    flex: 1;
  }
  .option-card:hover {
    border-color: color-mix(in srgb, var(--color-ink) 15%, transparent);
  }
  .option-card.active {
    background: var(--color-ink);
    color: var(--color-paper);
    border-color: transparent;
  }
  .opt-label {
    font-size: 13px;
    font-weight: 500;
  }
  .opt-desc {
    font-size: 11px;
    opacity: 0.5;
  }
  .option-card.active .opt-desc {
    opacity: 0.65;
  }
</style>
