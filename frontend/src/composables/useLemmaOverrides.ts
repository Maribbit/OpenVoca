import { computed, ref } from "vue";

import type { ReadingSentenceToken } from "../api/reading";

export type LemmaOverrideSource = "dictionary" | "progress";

export interface LemmaOverride {
  oldLemma: string;
  newLemma: string;
  source: LemmaOverrideSource;
}

const VALID_LEMMA_PATTERN = /^[a-z]+(?:[-'][a-z]+)*$/;

export function normalizeLemmaInput(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/\u2019/g, "'");
}

export function isValidLemmaInput(value: string): boolean {
  return VALID_LEMMA_PATTERN.test(normalizeLemmaInput(value));
}

function tokenBaseLemma(token: ReadingSentenceToken): string {
  return normalizeLemmaInput(token.lemma || token.text);
}

export function useLemmaOverrides() {
  const overrides = ref<Map<string, LemmaOverride>>(new Map());

  const list = computed(() => Array.from(overrides.value.values()));

  function resolveLemma(value: string): string {
    let current = normalizeLemmaInput(value);
    const seen = new Set<string>();

    while (overrides.value.has(current) && !seen.has(current)) {
      seen.add(current);
      current = overrides.value.get(current)!.newLemma;
    }

    return current;
  }

  function effectiveLemma(value: ReadingSentenceToken | string): string {
    const base = typeof value === "string" ? value : tokenBaseLemma(value);
    return resolveLemma(base);
  }

  function setOverride(
    oldLemmaValue: string,
    newLemmaValue: string,
    source: LemmaOverrideSource,
  ): boolean {
    const oldLemma = normalizeLemmaInput(oldLemmaValue);
    const newLemma = normalizeLemmaInput(newLemmaValue);

    if (!isValidLemmaInput(oldLemma) || !isValidLemmaInput(newLemma)) {
      return false;
    }

    const next = new Map(overrides.value);
    if (oldLemma === newLemma) {
      next.delete(oldLemma);
    } else {
      next.set(oldLemma, { oldLemma, newLemma, source });
    }
    overrides.value = next;
    return true;
  }

  function clearOverrides(): void {
    overrides.value = new Map();
  }

  function uniqueEffectiveLemmas(values: Array<ReadingSentenceToken | string>) {
    return Array.from(
      new Set(
        values
          .map((value) => effectiveLemma(value))
          .filter((lemma) => isValidLemmaInput(lemma)),
      ),
    );
  }

  return {
    overrides,
    list,
    effectiveLemma,
    setOverride,
    clearOverrides,
    uniqueEffectiveLemmas,
  };
}
