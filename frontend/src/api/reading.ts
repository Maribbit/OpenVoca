export interface ReadingSentenceResponse {
  sentence: string;
  words: string[];
  tokens: ReadingSentenceToken[];
}

export interface ReadingSentenceToken {
  text: string;
  isWord: boolean;
  isTarget?: boolean;
  pos?: string | null;
  lemma?: string | null;
  trailingSpace?: boolean;
}

export interface GenerateReadingSentenceRequest {
  promptTemplate: string;
  targetWords: string[];
  composerInstructions?: string;
}

export interface WordPosEntry {
  lemma: string;
  pos: string;
}

export interface FeedbackRequest {
  targetWords: WordPosEntry[];
  markedWords: WordPosEntry[];
  sentence: string;
}

export interface WordRecordOut {
  lemma: string;
  pos: string;
  interval: number;
  cooldown: number;
  lastContext?: string | null;
}

export interface VocabularyResponse {
  words: WordRecordOut[];
  total: number;
}

export async function fetchNextReadingSentence(
  request: GenerateReadingSentenceRequest,
): Promise<ReadingSentenceResponse> {
  const response = await fetch("/api/reading-sentence/next", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load reading sentence.");
  }

  return (await response.json()) as ReadingSentenceResponse;
}

export async function submitFeedback(request: FeedbackRequest): Promise<void> {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Failed to submit feedback.");
  }
}

export async function fetchVocabulary(): Promise<VocabularyResponse> {
  const response = await fetch("/api/vocabulary", {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error("Unable to load vocabulary.");
  }

  return (await response.json()) as VocabularyResponse;
}

export async function clearVocabulary(): Promise<void> {
  await fetch("/api/vocabulary", { method: "DELETE" });
}

export async function fetchTargetWords(limit: number): Promise<string[]> {
  const response = await fetch(`/api/target-words?limit=${limit}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error("Unable to load target words.");
  }

  const data = (await response.json()) as { words: string[] };
  return data.words;
}
