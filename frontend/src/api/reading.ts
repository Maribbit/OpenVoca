export type ReadingMode = "sentence" | "riddle";

export interface ReadingSentenceResponse {
  sentence: string;
  words: string[];
  tokens: ReadingSentenceToken[];
  mode?: ReadingMode;
  riddle?: ReadingRiddle;
}

export interface ReadingRiddle {
  clue: string;
  question: string;
  answer: string;
  clueTokens: ReadingSentenceToken[];
  questionTokens: ReadingSentenceToken[];
  answerTokens: ReadingSentenceToken[];
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
  prompt: string;
  targetWords: string[];
  mode?: ReadingMode;
}

export interface FeedbackRequest {
  targetWords: string[];
  markedWords: string[];
  sentence: string;
  originalTargets?: string[];
}

export interface WordRecordOut {
  lemma: string;
  level: number;
  cooldown: number;
  firstSeen?: string | null;
  lastSeen?: string | null;
  lastContext?: string | null;
  seenCount?: number;
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

export interface StreamCallbacks {
  onProgress: (wordCount: number) => void;
  onComplete: (response: ReadingSentenceResponse) => void;
  onError: (error: string) => void;
}

export async function fetchNextReadingSentenceStream(
  request: GenerateReadingSentenceRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/reading-sentence/next/stream", {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error("Unable to load reading sentence.");
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop()!;

    for (const part of parts) {
      const lines = part.split("\n");
      let eventType = "";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) eventType = line.slice(7);
        else if (line.startsWith("data: ")) data = line.slice(6);
      }
      if (!eventType || !data) continue;

      if (eventType === "progress") {
        const parsed = JSON.parse(data) as { wordCount: number };
        callbacks.onProgress(parsed.wordCount);
      } else if (eventType === "complete") {
        callbacks.onComplete(JSON.parse(data) as ReadingSentenceResponse);
      } else if (eventType === "error") {
        const parsed = JSON.parse(data) as { detail: string };
        callbacks.onError(parsed.detail);
      }
    }
  }
}

export interface LevelDelta {
  lemma: string;
  old_level: number;
  new_level: number;
  is_new: boolean;
}

export async function submitFeedbackDraft(
  request: FeedbackRequest,
): Promise<LevelDelta[]> {
  const response = await fetch("/api/feedback/draft", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      target_words: request.targetWords,
      marked_words: request.markedWords,
      sentence: request.sentence,
      original_targets: request.originalTargets,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to get feedback draft.");
  }
  return await response.json();
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

export async function fetchVocabulary(
  sort: "due" | "familiarity" | "recent" = "due",
): Promise<VocabularyResponse> {
  const response = await fetch(`/api/vocabulary?sort=${sort}`, {
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

export async function exportVocabulary(): Promise<void> {
  const response = await fetch("/api/vocabulary/export");
  if (!response.ok) throw new Error("Unable to export vocabulary.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "openvoca-vocabulary.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export interface VocabularyImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export async function importVocabulary(
  file: File,
  mode: "skip" | "overwrite" = "skip",
): Promise<VocabularyImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);
  const response = await fetch("/api/vocabulary/import", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const detail =
      ((await response.json()) as { detail?: string }).detail ??
      "Import failed.";
    throw new Error(detail);
  }
  return (await response.json()) as VocabularyImportResult;
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

export interface DictionaryEntry {
  word: string;
  phonetic: string;
  definition: string;
  translation: string;
  pos: string;
  tag: string;
  exchange: string;
}

export async function fetchDefinition(
  word: string,
): Promise<DictionaryEntry | null> {
  const response = await fetch(`/api/dictionary/${encodeURIComponent(word)}`, {
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Dictionary lookup failed.");
  return (await response.json()) as DictionaryEntry;
}

export async function updateWordRecord(
  lemma: string,
  update: { level?: number; cooldown?: number },
): Promise<WordRecordOut> {
  const response = await fetch(`/api/vocabulary/${encodeURIComponent(lemma)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!response.ok) throw new Error("Failed to update word record.");
  return (await response.json()) as WordRecordOut;
}

export async function fetchTtsAudio(
  text: string,
  voice?: string,
): Promise<Blob> {
  const params = new URLSearchParams({ text });
  if (voice) params.set("voice", voice);
  const response = await fetch(`/api/tts?${params.toString()}`);
  if (!response.ok) throw new Error("TTS request failed.");
  return await response.blob();
}

export async function deleteWordRecord(lemma: string): Promise<void> {
  const response = await fetch(`/api/vocabulary/${encodeURIComponent(lemma)}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete word record.");
}

export function tokensToPlainText(tokens: ReadingSentenceToken[]): string {
  return tokens
    .map((t, i) => {
      const space = i > 0 && tokens[i - 1].trailingSpace !== false ? " " : "";
      return space + t.text;
    })
    .join("");
}
