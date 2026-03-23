export interface ReadingPreferences {
  promptTemplate: string;
  targetWordCount: number;
}

export const DEFAULT_READING_PREFERENCES: ReadingPreferences = {
  promptTemplate:
    "Write exactly one natural English sentence. Use every target word once if possible, keep the tone calm and literary, and return only the sentence. Target words: {{target_words}}.",
  targetWordCount: 3,
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
    const promptTemplate =
      typeof parsed.promptTemplate === "string" && parsed.promptTemplate.trim()
        ? parsed.promptTemplate.trim()
        : DEFAULT_READING_PREFERENCES.promptTemplate;
    const targetWordCount =
      typeof parsed.targetWordCount === "number" &&
      Number.isInteger(parsed.targetWordCount) &&
      parsed.targetWordCount >= 1 &&
      parsed.targetWordCount <= 5
        ? parsed.targetWordCount
        : DEFAULT_READING_PREFERENCES.targetWordCount;

    return {
      promptTemplate,
      targetWordCount,
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
