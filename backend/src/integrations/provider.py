"""Abstract LLM provider interface.

All LLM integrations implement the ``LLMProvider`` protocol so the rest
of the application can depend on a single, stable API surface.
"""

from collections.abc import AsyncGenerator
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

    async def generate_completion_stream(
        self, prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from the model as they are generated.

        Yields individual content deltas.
        """
        ...
