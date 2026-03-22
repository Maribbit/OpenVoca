import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine

import src.main as main_module
from src.main import app
from src.integrations.ollama import OllamaClient
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
)

client = TestClient(app)


def _in_memory_engine():
    """Create a fresh in-memory SQLite engine for test isolation."""
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


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


def test_tokenize_sentence_splits_words_and_punctuation() -> None:
    """The tokenizer should preserve punctuation while marking clickable word tokens."""

    tokens = tokenize_sentence("A harbor lantern flickered in the rain.")

    assert [token.text for token in tokens] == [
        "A",
        "harbor",
        "lantern",
        "flickered",
        "in",
        "the",
        "rain",
        ".",
    ]
    assert [token.is_word for token in tokens] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
    ]


def test_tokenize_sentence_preserves_apostrophes_and_quotes() -> None:
    """The tokenizer should keep common English word forms as single word tokens."""

    tokens = tokenize_sentence('"It\'s" softly-lit.')

    assert [token.text for token in tokens] == [
        '"',
        "It's",
        '"',
        "softly",
        "-",
        "lit",
        ".",
    ]
    assert [token.is_word for token in tokens] == [
        False,
        True,
        False,
        True,
        False,
        True,
        False,
    ]


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
        "tokens": [
            {"text": "A", "isWord": True},
            {"text": "harbor", "isWord": True},
            {"text": "lantern", "isWord": True},
            {"text": "flickered", "isWord": True},
            {"text": "in", "isWord": True},
            {"text": "the", "isWord": True},
            {"text": "rain", "isWord": True},
            {"text": ".", "isWord": False},
        ],
    }


# ---------------------------------------------------------------------------
# Word store / familiarity update tests
# ---------------------------------------------------------------------------


def test_apply_feedback_creates_new_records() -> None:
    """Marked words should be created with familiarity 0, unmarked targets with 1."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=["lantern", "meadow"],
        marked_words=["meadow"],
        sentence="A lantern glowed beside the meadow.",
        engine=engine,
    )

    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["lantern"] == 1  # unmarked target → +1
    assert words["meadow"] == 0  # marked (unknown) → stays at 0


def test_apply_feedback_decreases_familiarity_for_marked_words() -> None:
    """Marking a previously familiar word should decrease its familiarity."""
    engine = _in_memory_engine()

    # First round: word becomes familiar
    apply_feedback(
        target_words=["harbor"],
        marked_words=[],
        sentence="The harbor was calm.",
        engine=engine,
    )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["harbor"] == 1

    # Second round: user marks it as unknown
    apply_feedback(
        target_words=["harbor"],
        marked_words=["harbor"],
        sentence="Ships lined the harbor.",
        engine=engine,
    )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["harbor"] == 0


def test_apply_feedback_caps_familiarity_at_boundaries() -> None:
    """Familiarity should never go below 0 or above 4."""
    engine = _in_memory_engine()

    # Increase to max
    for _ in range(6):
        apply_feedback(
            target_words=["resolve"],
            marked_words=[],
            sentence="They showed resolve.",
            engine=engine,
        )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["resolve"] == 4

    # Decrease past zero
    for _ in range(6):
        apply_feedback(
            target_words=[],
            marked_words=["resolve"],
            sentence="They showed resolve.",
            engine=engine,
        )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["resolve"] == 0


def test_pick_target_words_returns_least_familiar() -> None:
    """pick_target_words should return words with lowest familiarity first."""
    engine = _in_memory_engine()

    apply_feedback(["alpha", "beta", "gamma", "delta"], [], "sentence", engine=engine)
    # All start at familiarity 1. Boost alpha twice more.
    apply_feedback(["alpha"], [], "sentence", engine=engine)
    apply_feedback(["alpha"], [], "sentence", engine=engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "alpha" not in picked  # alpha has familiarity 3, others have 1
    assert len(picked) == 3


def test_clear_all_words_empties_database() -> None:
    """clear_all_words should delete every record."""
    engine = _in_memory_engine()

    apply_feedback(["a", "b", "c"], [], "sentence", engine=engine)
    assert len(list_all_words(engine)) == 3

    deleted = clear_all_words(engine)
    assert deleted == 3
    assert len(list_all_words(engine)) == 0
