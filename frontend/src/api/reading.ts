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
}

export interface GenerateReadingSentenceRequest {
  promptTemplate: string;
  targetWordCount: number;
}

export interface WordPosEntry {
  word: string;
  pos: string;
}

export interface FeedbackRequest {
  targetWords: WordPosEntry[];
  markedWords: WordPosEntry[];
  sentence: string;
}

export interface WordRecordOut {
  word: string;
  pos: string;
  familiarity: number;
}

export interface VocabularyResponse {
  words: WordRecordOut[];
  total: number;
}

export async function fetchReadingSentence(
  request: GenerateReadingSentenceRequest,
): Promise<ReadingSentenceResponse> {
  const response = await fetch("/api/reading-sentence", {
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
  await fetch("/api/feedback", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
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
