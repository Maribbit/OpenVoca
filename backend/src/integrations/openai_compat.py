import httpx


class OpenAICompatibleClient:
    """LLM client for any OpenAI-compatible chat completions API.

    Works with OpenRouter, Groq, Together.ai, SiliconFlow, DeepSeek,
    and any service that implements POST /v1/chat/completions.

    Uses a persistent ``httpx.AsyncClient`` to reuse TCP connections
    across requests, avoiding repeated DNS lookups and TLS handshakes.
    Call ``aclose()`` when the client is no longer needed.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def generate_completion(self, prompt: str) -> str:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        response = await self._client.post(
            "/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError(
                "OpenAI-compatible response has no choices in the payload."
            )

        content = choices[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "OpenAI-compatible response has empty content in the payload."
            )

        return " ".join(content.split())
