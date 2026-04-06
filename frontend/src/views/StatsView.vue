<template>
  <div class="min-h-screen bg-paper p-8 text-ink antialiased">
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
            @click="handleClear"
          >
            {{ i18nMessages.clearVocabulary }}
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
            </tr>
          </thead>
          <tbody class="divide-y divide-black/3 text-sm">
            <tr
              v-for="word in words"
              :key="`${word.lemma}-${word.pos}`"
              class="transition-colors hover:bg-black/2"
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
                  <div
                    class="h-2 w-2 rounded-full"
                    :class="intervalDotColor(word.interval)"
                  />
                  <span class="font-mono text-xs text-ink">{{
                    word.interval
                  }}</span>
                  <span class="text-xs text-inkLight/60">
                    {{ intervalLabel(word.interval) }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span
                  class="font-mono text-xs"
                  :class="
                    word.cooldown > 0 ? 'text-inkLight' : 'text-green-500'
                  "
                >
                  {{ word.cooldown }}
                </span>
              </td>
            </tr>
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
  import { onMounted, ref } from "vue";

  import {
    clearVocabulary,
    fetchVocabulary,
    type WordRecordOut,
  } from "../api/reading";
  import { useI18n } from "../composables/useI18n";

  const { messages: i18nMessages } = useI18n();
  const words = ref<WordRecordOut[]>([]);

  async function loadWords(): Promise<void> {
    try {
      const response = await fetchVocabulary();
      words.value = response.words;
    } catch {
      words.value = [];
    }
  }

  async function handleClear(): Promise<void> {
    await clearVocabulary();
    words.value = [];
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

  onMounted(() => {
    void loadWords();
  });
</script>
