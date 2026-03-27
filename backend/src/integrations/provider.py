"""Abstract LLM provider interface.

All LLM integrations (Ollama, OpenAI, Anthropic, etc.) implement the
``LLMProvider`` protocol so the rest of the application can depend on
a single, stable API surface.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal contract every LLM backend must satisfy."""

    async def generate_completion(self, prompt: str) -> str:
        """Send *prompt* to the model and return the generated text.

        Implementations MUST:
        - raise ``httpx.HTTPError`` (or subclass) on transport failures.
        - raise ``ValueError`` when the model response is unparseable.
        - return a single, whitespace-normalised string.
        """
        ...
