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
          <input
            ref="importFileInput"
            type="file"
            accept=".csv"
            class="hidden"
            @change="onFileSelected"
          />
          <button
            type="button"
            class="flex items-center gap-2 rounded-full border border-black/8 bg-surface px-5 py-2.5 text-sm font-medium text-ink transition-all hover:border-black/15 hover:shadow-sm"
            @click="importFileInput?.click()"
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
                d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2m-4-8-4-4m0 0L8 8m4-4v12"
              />
            </svg>
            {{ i18nMessages.importVocabulary }}
          </button>
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

      <!-- Import result banner -->
      <Transition name="menu-fade">
        <div
          v-if="importStatus"
          class="mb-6 flex items-center justify-between rounded-xl px-5 py-3 text-sm shadow-sm"
          :class="
            importError
              ? 'border border-red-200 bg-red-50 text-red-600'
              : 'border border-green-500/20 bg-green-500/5 text-green-600'
          "
        >
          <div class="flex items-center gap-3">
            <span>{{ importStatus }}</span>
            <button
              v-if="lastImportedFile && importSkippedExisting"
              type="button"
              class="cursor-pointer rounded-full bg-black/5 px-3 py-1 text-xs font-medium text-ink transition-colors hover:bg-black/10"
              @click="reimportOverwrite"
            >
              {{ i18nMessages.importModeOverwrite }}
            </button>
          </div>
          <button
            type="button"
            class="ml-4 cursor-pointer rounded p-1 transition-colors hover:bg-black/5"
            @click="importStatus = ''"
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
        </div>
      </Transition>

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
        <div
          class="flex flex-wrap items-center justify-between gap-1 border-b border-black/5 px-6 py-3"
        >
          <div class="flex gap-1">
            <button
              type="button"
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
              :class="
                sortMode === 'due'
                  ? 'bg-black/8 text-ink'
                  : 'text-inkLight hover:bg-black/4'
              "
              @click="sortMode = 'due'"
            >
              {{ i18nMessages.sortByDue }}
            </button>
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
          <span class="text-xs text-inkLight/60">
            {{ i18nMessages.statsIntervalTip }}
          </span>
        </div>

        <table class="w-full border-collapse text-left">
          <thead>
            <tr
              class="border-b border-black/5 bg-surface text-xs uppercase tracking-widest text-inkLight"
            >
              <th class="px-6 py-4 font-medium">
                {{ i18nMessages.statsLemma }}
              </th>
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
            <template v-for="word in words" :key="word.lemma">
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
                  <input
                    type="number"
                    :value="word.level"
                    :min="1"
                    :max="6"
                    class="w-14 rounded border border-transparent bg-transparent px-1 py-0.5 text-center font-mono text-xs outline-none transition-colors focus:border-black/15 focus:bg-surface"
                    :class="
                      word.level >= 6 ? 'text-emerald-500' : 'text-inkLight'
                    "
                    @change="onLevelInput(word, $event)"
                    @click.stop
                  />
                </td>
                <td class="px-6 py-4">
                  <input
                    type="number"
                    :value="word.cooldown"
                    :min="0"
                    :max="2 ** word.level"
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
              <tr v-if="expandedKey === word.lemma">
                <td colspan="4" class="bg-black/2 px-6 py-3">
                  <div class="flex flex-col gap-1 text-xs text-inkLight">
                    <div>
                      <span class="font-medium"
                        >{{ i18nMessages.lastSeenLabel }}:</span
                      >
                      {{ formatLastSeen(word.lastSeen) }}
                    </div>
                    <div v-if="word.firstSeen">
                      <span class="font-medium"
                        >{{ i18nMessages.firstSeenLabel }}:</span
                      >
                      {{ formatLastSeen(word.firstSeen) }}
                    </div>
                    <div v-if="word.seenCount !== undefined">
                      <span class="font-medium"
                        >{{ i18nMessages.seenCountLabel }}:</span
                      >
                      {{ word.seenCount }}×
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
    importVocabulary,
    updateWordRecord,
    type WordRecordOut,
  } from "../api/reading";
  import { useI18n } from "../composables/useI18n";

  type SortMode = "due" | "familiarity" | "recent";

  const { messages: i18nMessages } = useI18n();
  const words = ref<WordRecordOut[]>([]);
  const sortMode = ref<SortMode>("due");
  const expandedKey = ref<string | null>(null);
  const importFileInput = ref<HTMLInputElement | null>(null);
  const importStatus = ref<string>("");
  const importError = ref(false);
  const lastImportedFile = ref<File | null>(null);
  const importSkippedExisting = ref(false);

  function toggleExpand(word: WordRecordOut): void {
    const key = word.lemma;
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

  async function onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    input.value = "";
    importStatus.value = "";
    importError.value = false;
    importSkippedExisting.value = false;
    lastImportedFile.value = file;
    try {
      const result = await importVocabulary(file, "skip");
      importSkippedExisting.value = result.skipped > 0;
      importStatus.value =
        result.skipped > 0
          ? i18nMessages.value.importedSkipped
              .replace("{0}", String(result.imported))
              .replace("{1}", String(result.skipped))
          : i18nMessages.value.importedWords.replace(
              "{0}",
              String(result.imported),
            );
      importError.value = false;
      await loadWords();
    } catch (err) {
      importError.value = true;
      lastImportedFile.value = null;
      importStatus.value =
        err instanceof Error ? err.message : i18nMessages.value.importFailed;
    }
  }

  async function reimportOverwrite(): Promise<void> {
    const file = lastImportedFile.value;
    if (!file) return;
    importStatus.value = "";
    importError.value = false;
    importSkippedExisting.value = false;
    try {
      const result = await importVocabulary(file, "overwrite");
      lastImportedFile.value = null;
      importStatus.value =
        result.skipped > 0
          ? i18nMessages.value.importedSkipped
              .replace("{0}", String(result.imported))
              .replace("{1}", String(result.skipped))
          : i18nMessages.value.importedWords.replace(
              "{0}",
              String(result.imported),
            );
      importError.value = false;
      await loadWords();
    } catch (err) {
      importError.value = true;
      importStatus.value =
        err instanceof Error ? err.message : i18nMessages.value.importFailed;
    }
  }

  async function changeLevel(
    word: WordRecordOut,
    newLevel: number,
  ): Promise<void> {
    try {
      const updated = await updateWordRecord(word.lemma, {
        level: Math.round(newLevel),
      });
      word.level = updated.level;
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
      const updated = await updateWordRecord(word.lemma, {
        cooldown: newCooldown,
      });
      word.cooldown = updated.cooldown;
    } catch {
      /* silently ignore */
    }
  }

  function onLevelInput(word: WordRecordOut, event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = parseInt(input.value, 10);
    if (Number.isNaN(value)) {
      input.value = String(word.level);
      return;
    }
    void changeLevel(word, value);
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
      await deleteWordRecord(word.lemma);
      words.value = words.value.filter((w) => w.lemma !== word.lemma);
    } catch {
      /* silently ignore — record may already be deleted */
    }
  }

  watch(sortMode, () => {
    expandedKey.value = null;
    void loadWords();
  });

  onMounted(() => {
    void loadWords();
  });
</script>
