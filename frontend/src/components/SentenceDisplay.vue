<template>
  <article class="w-full min-w-0 max-w-3xl text-center">
    <p
      v-if="isLoading"
      class="sentence-fade font-serif text-inkLight/65"
      :class="typographyClass"
    >
      {{ loadingText
      }}<span
        v-if="loadingProgress != null"
        class="ml-2 font-sans text-[0.5em] tabular-nums tracking-normal text-inkLight/40"
        data-testid="loading-progress"
        >{{ loadingProgress }}</span
      >
    </p>

    <p
      v-else-if="errorMessage"
      class="sentence-fade font-serif text-inkLight/75"
      :class="typographyClass"
    >
      {{ errorMessage }}
    </p>

    <p
      v-else
      class="sentence-fade font-serif text-ink"
      :class="typographyClass"
    >
      <template
        v-for="(token, index) in tokens"
        :key="`${token.text}-${index}`"
      >
        <template v-if="needsLeadingSpace(index)">{{ " " }}</template>
        <span v-if="token.isWord" class="inline whitespace-nowrap">
          <button
            type="button"
            class="cursor-pointer rounded-md px-[0.09em] py-[0.04em] transition-colors focus:outline-none"
            :class="[
              markedWords.has(tokenKey(token))
                ? 'bg-highlight'
                : 'hover:bg-highlight/70',
            ]"
            @click="$emit('word-click', token)"
          >
            <span
              :class="
                token.isTarget
                  ? 'border-b border-dotted border-inkLight/65 pb-[0.01em]'
                  : ''
              "
            >
              {{ token.text }}
            </span></button
          ><!--
       --><span v-if="hasTrailingPunctuation(index)">{{
            tokens[index + 1].text
          }}</span>
        </span>
        <span v-else-if="!isPunctuationAfterWord(index)">{{ token.text }}</span>
      </template>
    </p>
  </article>
</template>

<script setup lang="ts">
  import type { ReadingSentenceToken } from "../api/reading";

  const props = defineProps<{
    tokens: ReadingSentenceToken[];
    markedWords: Set<string>;
    isLoading: boolean;
    errorMessage: string;
    loadingText: string;
    loadingProgress?: string | null;
    typographyClass: string;
  }>();

  defineEmits<{
    "word-click": [token: ReadingSentenceToken];
  }>();

  function tokenKey(token: ReadingSentenceToken): string {
    return `${token.text.toLowerCase()}/${token.pos ?? ""}`;
  }

  function needsLeadingSpace(index: number): boolean {
    if (index === 0) return false;
    const prev = props.tokens[index - 1];
    // Skip space if this punctuation was already rendered with the previous word
    if (isPunctuationAfterWord(index)) return false;
    return prev?.trailingSpace !== false;
  }

  function hasTrailingPunctuation(index: number): boolean {
    const next = props.tokens[index + 1];
    if (!next || next.isWord) return false;
    return /^[.,;:!?'")\]}\u2014\u2013\u2026]+$/.test(next.text);
  }

  function isPunctuationAfterWord(index: number): boolean {
    if (index === 0) return false;
    const prev = props.tokens[index - 1];
    if (!prev?.isWord) return false;
    const token = props.tokens[index];
    if (token.isWord) return false;
    return /^[.,;:!?'")\]}\u2014\u2013\u2026]+$/.test(token.text);
  }
</script>
