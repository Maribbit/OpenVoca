<template>
  <div class="min-h-zoom-screen bg-paper p-8 text-ink antialiased">
    <div class="mx-auto max-w-5xl">
      <header class="mb-12 flex items-center justify-between">
        <div>
          <h1 class="mb-2 font-serif text-3xl tracking-wide text-ink">
            {{ i18nMessages.vocabulary }}
          </h1>
          <p class="text-sm text-inkLight">
            {{ words.length }} {{ i18nMessages.showingWords }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex items-center gap-2 rounded-full border border-black/8 bg-surface px-5 py-2.5 text-sm font-medium text-ink transition-all hover:border-black/15 hover:shadow-sm"
            @click="handleExport"
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
                d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V3"
              />
            </svg>
            {{ i18nMessages.exportVocabulary }}
          </button>
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
        </div>
      </header>

      <div
        v-if="words.length === 0"
        class="rounded-2xl border border-black/5 bg-surface p-12 text-center"
      >
        <p class="text-inkLight">{{ i18nMessages.emptyVocabulary }}</p>
      </div>

      <div
        v-else
        class="overflow-hidden rounded-2xl border border-black/5 bg-surface shadow-sm"
      >
        <!-- Sort toggle -->
        <div class="flex gap-1 border-b border-black/5 px-6 py-3">
          <button
            type="button"
            class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
            :class="
              sortMode === 'familiarity'
                ? 'bg-black/8 text-ink'
                : 'text-inkLight hover:bg-black/4'
            "
            @click="sortMode = 'familiarity'"
          >
            {{ i18nMessages.sortByFamiliarity }}
          </button>
          <button
            type="button"
            class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
            :class="
              sortMode === 'recent'
                ? 'bg-black/8 text-ink'
                : 'text-inkLight hover:bg-black/4'
            "
            @click="sortMode = 'recent'"
          >
            {{ i18nMessages.sortByRecent }}
          </button>
        </div>

        <table class="w-full border-collapse text-left">
          <thead>
            <tr
              class="border-b border-black/5 bg-surface text-xs uppercase tracking-widest text-inkLight"
            >
              <th class="px-6 py-4 font-medium">
                {{ i18nMessages.statsLemma }}
              </th>
              <th class="px-6 py-4 font-medium">{{ i18nMessages.pos }}</th>
              <th class="px-6 py-4 font-medium">
                {{ i18nMessages.statsInterval }}
              </th>
              <th class="px-6 py-4 font-medium">
                {{ i18nMessages.statsCooldown }}
              </th>
              <th class="w-10 px-2 py-4"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-black/3 text-sm">
            <template v-for="word in words" :key="`${word.lemma}-${word.pos}`">
              <tr
                class="cursor-pointer transition-colors hover:bg-black/2"
                @click="toggleExpand(word)"
              >
                <td class="px-6 py-4">
                  <span class="font-serif text-lg text-ink">{{
                    word.lemma
                  }}</span>
                </td>
                <td class="px-6 py-4">
                  <span
                    class="inline-block rounded-full bg-black/5 px-2.5 py-0.5 font-mono text-xs text-inkLight"
                  >
                    {{ word.pos }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="cursor-pointer rounded p-0.5 text-inkLight/40 transition-colors hover:bg-black/5 hover:text-inkLight disabled:cursor-not-allowed disabled:opacity-30"
                      :disabled="word.interval <= 2"
                      :title="i18nMessages.intervalHalve"
                      @click.stop="changeInterval(word, word.interval / 2)"
                    >
                      <svg
                        class="h-3 w-3"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M5 12h14"
                        />
                      </svg>
                    </button>
                    <span
                      class="min-w-[1.5rem] text-center font-mono text-xs text-ink"
                      >{{ word.interval }}</span
                    >
                    <button
                      type="button"
                      class="cursor-pointer rounded p-0.5 text-inkLight/40 transition-colors hover:bg-black/5 hover:text-inkLight disabled:cursor-not-allowed disabled:opacity-30"
                      :disabled="word.interval >= 64"
                      :title="i18nMessages.intervalDouble"
                      @click.stop="changeInterval(word, word.interval * 2)"
                    >
                      <svg
                        class="h-3 w-3"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M12 5v14m-7-7h14"
                        />
                      </svg>
                    </button>
                    <span class="text-xs text-inkLight/60">
                      {{ intervalLabel(word.interval) }}
                    </span>
                    <div
                      class="h-2 w-2 rounded-full"
                      :class="intervalDotColor(word.interval)"
                    />
                  </div>
                </td>
                <td class="px-6 py-4">
                  <input
                    type="number"
                    :value="word.cooldown"
                    :min="0"
                    :max="word.interval"
                    class="w-14 rounded border border-transparent bg-transparent px-1 py-0.5 text-center font-mono text-xs outline-none transition-colors focus:border-black/15 focus:bg-surface"
                    :class="
                      word.cooldown > 0 ? 'text-inkLight' : 'text-green-500'
                    "
                    @change="onCooldownInput(word, $event)"
                    @click.stop
                  />
                </td>
                <td class="px-2 py-4">
                  <button
                    type="button"
                    class="cursor-pointer rounded p-1 text-inkLight/30 transition-colors hover:bg-red-50 hover:text-red-400"
                    :title="i18nMessages.deleteWord"
                    @click.stop="handleDeleteWord(word)"
                  >
                    <svg
                      class="h-3.5 w-3.5"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M6 18 18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </td>
              </tr>
              <!-- Expanded detail row -->
              <tr v-if="expandedKey === wordKey(word)">
                <td colspan="5" class="bg-black/2 px-6 py-3">
                  <div class="flex flex-col gap-1 text-xs text-inkLight">
                    <div>
                      <span class="font-medium"
                        >{{ i18nMessages.lastSeenLabel }}:</span
                      >
                      {{ formatLastSeen(word.lastSeen) }}
                    </div>
                    <div v-if="word.lastContext">
                      <span class="font-medium"
                        >{{ i18nMessages.lastContextLabel }}:</span
                      >
                      <span class="ml-1 font-serif italic">{{
                        word.lastContext
                      }}</span>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>

        <div
          class="border-t border-black/5 bg-black/2 px-6 py-4 text-sm text-inkLight"
        >
          {{ words.length }} {{ i18nMessages.showingWords }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { onMounted, ref, watch } from "vue";

  import {
    deleteWordRecord,
    exportVocabulary,
    fetchVocabulary,
    updateWordRecord,
    type WordRecordOut,
  } from "../api/reading";
  import { useI18n } from "../composables/useI18n";

  type SortMode = "familiarity" | "recent";

  const { messages: i18nMessages } = useI18n();
  const words = ref<WordRecordOut[]>([]);
  const sortMode = ref<SortMode>("familiarity");
  const expandedKey = ref<string | null>(null);

  function wordKey(word: WordRecordOut): string {
    return `${word.lemma}-${word.pos}`;
  }

  function toggleExpand(word: WordRecordOut): void {
    const key = wordKey(word);
    expandedKey.value = expandedKey.value === key ? null : key;
  }

  function formatLastSeen(iso: string | null | undefined): string {
    if (!iso) return "—";
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}h ago`;
    const diffD = Math.floor(diffH / 24);
    return `${diffD}d ago`;
  }

  async function loadWords(): Promise<void> {
    try {
      const response = await fetchVocabulary(sortMode.value);
      words.value = response.words;
    } catch {
      words.value = [];
    }
  }

  async function handleExport(): Promise<void> {
    await exportVocabulary();
  }

  async function changeInterval(
    word: WordRecordOut,
    newInterval: number,
  ): Promise<void> {
    try {
      const updated = await updateWordRecord(word.lemma, word.pos, {
        interval: Math.round(newInterval),
      });
      word.interval = updated.interval;
      word.cooldown = updated.cooldown;
    } catch {
      /* silently ignore */
    }
  }

  async function changeCooldown(
    word: WordRecordOut,
    newCooldown: number,
  ): Promise<void> {
    try {
      const updated = await updateWordRecord(word.lemma, word.pos, {
        cooldown: newCooldown,
      });
      word.cooldown = updated.cooldown;
    } catch {
      /* silently ignore */
    }
  }

  function onCooldownInput(word: WordRecordOut, event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = parseInt(input.value, 10);
    if (Number.isNaN(value)) {
      input.value = String(word.cooldown);
      return;
    }
    void changeCooldown(word, value);
  }

  async function handleDeleteWord(word: WordRecordOut): Promise<void> {
    try {
      await deleteWordRecord(word.lemma, word.pos);
      words.value = words.value.filter(
        (w) => !(w.lemma === word.lemma && w.pos === word.pos),
      );
    } catch {
      /* silently ignore — record may already be deleted */
    }
  }

  function intervalDotColor(interval: number): string {
    if (interval <= 2) return "bg-orange-400";
    if (interval <= 8) return "bg-yellow-400";
    if (interval <= 32) return "bg-green-400";
    return "bg-green-500";
  }

  function intervalLabel(interval: number): string {
    if (interval <= 2) return i18nMessages.value.familiarityNeedsReview;
    if (interval <= 8) return i18nMessages.value.familiarityLearning;
    if (interval <= 32) return i18nMessages.value.familiarityFamiliar;
    return i18nMessages.value.familiarityMastered;
  }

  watch(sortMode, () => {
    expandedKey.value = null;
    void loadWords();
  });

  onMounted(() => {
    void loadWords();
  });
</script>
