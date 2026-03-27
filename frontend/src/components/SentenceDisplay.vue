<template>
  <article class="w-full max-w-3xl text-center">
    <p
      v-if="isLoading"
      class="sentence-fade font-serif text-inkLight/65"
      :class="typographyClass"
    >
      {{ loadingText }}
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
        <span v-if="needsLeadingSpace(index)" aria-hidden="true">&nbsp;</span>
        <button
          v-if="token.isWord"
          type="button"
          class="cursor-pointer rounded-md px-[0.09em] py-[0.04em] transition-colors focus:outline-none"
          :class="[
            markedWords.has(tokenKey(token))
              ? 'bg-highlight'
              : 'hover:bg-highlight/70',
          ]"
          @click="$emit('toggle-mark', token)"
        >
          <span
            :class="
              token.isTarget
                ? 'border-b border-dotted border-inkLight/65 pb-[0.01em]'
                : ''
            "
          >
            {{ token.text }}
          </span>
        </button>
        <span v-else>{{ token.text }}</span>
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
    typographyClass: string;
  }>();

  defineEmits<{
    "toggle-mark": [token: ReadingSentenceToken];
  }>();

  function tokenKey(token: ReadingSentenceToken): string {
    return `${token.text.toLowerCase()}/${token.pos ?? ""}`;
  }

  function needsLeadingSpace(index: number): boolean {
    if (index === 0) return false;
    const prev = props.tokens[index - 1];
    return prev?.trailingSpace !== false;
  }
</script>
