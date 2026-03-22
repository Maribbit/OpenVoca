from collections.abc import Sequence

import httpx
from pydantic import BaseModel


class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma3:4b",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.transport = transport

    async def generate_sentence(
        self,
        words: Sequence[str],
        prompt_template: str,
    ) -> str:
        prompt = self._build_prompt(words, prompt_template)
        payload = OllamaGenerateRequest(model=self.model, prompt=prompt)

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = await client.post(
                "/api/generate",
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()

        result = response.json().get("response")
        if not isinstance(result, str) or not result.strip():
            raise ValueError("Ollama response payload is missing the response field.")

        return " ".join(result.split())

    @staticmethod
    def _build_prompt(words: Sequence[str], prompt_template: str) -> str:
        normalized_words = [word.strip() for word in words if word.strip()]
        if not normalized_words:
            raise ValueError("At least one word is required to generate a sentence.")

        normalized_template = prompt_template.strip()
        if not normalized_template:
            raise ValueError("A prompt template is required to generate a sentence.")

        words_text = ", ".join(normalized_words)
        if "{{target_words}}" in normalized_template:
            return normalized_template.replace("{{target_words}}", words_text)

        return f"{normalized_template}\nTarget words: {words_text}."
