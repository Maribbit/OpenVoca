export interface ReadingPreferences {
  promptTemplate: string;
  targetWordCount: number;
}

export const DEFAULT_READING_PREFERENCES: ReadingPreferences = {
  promptTemplate:
    "Write natural English text. Use every target word at least once. Return only the text, no explanations. Target words: {{target_words}}.",
  targetWordCount: 1,
};
