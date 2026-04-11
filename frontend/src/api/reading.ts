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
  prompt: string;
  targetWords: string[];
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
  pos: string,
  update: { interval?: number; cooldown?: number },
): Promise<WordRecordOut> {
  const response = await fetch(
    `/api/vocabulary/${encodeURIComponent(lemma)}/${encodeURIComponent(pos)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    },
  );
  if (!response.ok) throw new Error("Failed to update word record.");
  return (await response.json()) as WordRecordOut;
}

export async function deleteWordRecord(
  lemma: string,
  pos: string,
): Promise<void> {
  const response = await fetch(
    `/api/vocabulary/${encodeURIComponent(lemma)}/${encodeURIComponent(pos)}`,
    { method: "DELETE" },
  );
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
