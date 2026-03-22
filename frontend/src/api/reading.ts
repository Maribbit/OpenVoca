export interface ReadingSentenceResponse {
  sentence: string;
  words: string[];
  tokens: ReadingSentenceToken[];
}

export interface ReadingSentenceToken {
  text: string;
  isWord: boolean;
}

export interface GenerateReadingSentenceRequest {
  targetWords: string[];
  promptTemplate: string;
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
