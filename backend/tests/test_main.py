import httpx
import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app
from src.integrations.ollama import OllamaClient

client = TestClient(app)


def test_read_root():
    """
    Test the fundamental health check endpoint of the FastAPI application.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "OpenVoca backend is running!",
    }


@pytest.mark.anyio
async def test_ollama_client_returns_sentence_from_response() -> None:
    """The Ollama client should extract the generated sentence from the API payload."""

    prompt_template = (
        "Write exactly one natural English sentence. "
        "Keep it calm and literary. Include these words: {{target_words}}."
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://localhost:11434/api/generate")
        assert request.method == "POST"
        payload = request.read().decode("utf-8")
        assert '"model":"gemma3:4b"' in payload
        assert '"stream":false' in payload
        assert "Keep it calm and literary" in payload
        assert "lantern" in payload
        assert "meadow" in payload
        assert "window" in payload
        return httpx.Response(
            status_code=200,
            json={"response": "A lantern glowed by the window beside the meadow."},
        )

    transport = httpx.MockTransport(handler)
    ollama_client = OllamaClient(
        base_url="http://localhost:11434",
        model="gemma3:4b",
        transport=transport,
    )

    sentence = await ollama_client.generate_sentence(
        ["lantern", "meadow", "window"],
        prompt_template,
    )

    assert sentence == "A lantern glowed by the window beside the meadow."


@pytest.mark.anyio
async def test_ollama_client_rejects_missing_response_field() -> None:
    """The client should fail fast when Ollama returns an invalid payload."""

    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code=200, json={"done": True}),
    )
    ollama_client = OllamaClient(
        base_url="http://localhost:11434",
        model="gemma3:4b",
        transport=transport,
    )

    with pytest.raises(ValueError, match="response"):
        await ollama_client.generate_sentence(
            ["lantern", "meadow", "window"],
            "Use these words: {{target_words}}.",
        )


def test_reading_sentence_endpoint_uses_frontend_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The API should forward prompt and target words from the frontend to Ollama."""

    async def fake_generate_sentence(
        words: list[str],
        prompt_template: str,
    ) -> str:
        assert words == ["harbor", "lantern"]
        assert prompt_template == "Write one sentence with {{target_words}}."
        return "A harbor lantern flickered in the rain."

    monkeypatch.setattr(
        main_module.ollama_client,
        "generate_sentence",
        fake_generate_sentence,
    )

    response = client.post(
        "/api/reading-sentence",
        json={
            "targetWords": ["harbor", "lantern"],
            "promptTemplate": "Write one sentence with {{target_words}}.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "sentence": "A harbor lantern flickered in the rain.",
        "words": ["harbor", "lantern"],
    }
