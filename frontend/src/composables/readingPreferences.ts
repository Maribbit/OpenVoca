export interface ReadingPreferences {
  targetWords: string[];
  promptTemplate: string;
}

export const DEFAULT_READING_PREFERENCES: ReadingPreferences = {
  targetWords: ["lantern", "meadow", "window"],
  promptTemplate:
    "Write exactly one natural English sentence. Use every target word once if possible, keep the tone calm and literary, and return only the sentence. Target words: {{target_words}}.",
};

const STORAGE_KEY = "openvoca.reading.preferences";

export function loadReadingPreferences(): ReadingPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_READING_PREFERENCES;
  }

  const savedValue = window.localStorage.getItem(STORAGE_KEY);
  if (!savedValue) {
    return DEFAULT_READING_PREFERENCES;
  }

  try {
    const parsed = JSON.parse(savedValue) as Partial<ReadingPreferences>;
    const targetWords = Array.isArray(parsed.targetWords)
      ? sanitizeTargetWords(parsed.targetWords)
      : DEFAULT_READING_PREFERENCES.targetWords;
    const promptTemplate =
      typeof parsed.promptTemplate === "string" && parsed.promptTemplate.trim()
        ? parsed.promptTemplate.trim()
        : DEFAULT_READING_PREFERENCES.promptTemplate;

    return {
      targetWords,
      promptTemplate,
    };
  } catch {
    return DEFAULT_READING_PREFERENCES;
  }
}

export function saveReadingPreferences(preferences: ReadingPreferences): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}

export function formatTargetWords(words: string[]): string {
  return words.join(", ");
}

export function sanitizeTargetWords(words: string[]): string[] {
  const seen = new Set<string>();

  return words
    .map((word) => word.trim())
    .filter((word) => word.length > 0)
    .filter((word) => {
      const key = word.toLowerCase();
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
}

export function parseTargetWordsInput(input: string): string[] {
  return sanitizeTargetWords(input.split(/[\n,]/));
}
