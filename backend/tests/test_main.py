import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import src.main as main_module
from src.main import app
from src.integrations.ollama import OllamaClient
from src.integrations.provider import LLMProvider
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
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
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


def test_ollama_client_satisfies_llm_provider_protocol() -> None:
    """OllamaClient must be a structural subtype of LLMProvider."""
    assert isinstance(OllamaClient(), LLMProvider)


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
        False,
        True,
        True,
        True,
        False,
        False,
        True,
        False,
    ]
    # All alphabetic tokens should have POS; punctuation should not.
    assert all(t.pos is not None for t in tokens if t.text.isalpha())
    assert all(t.pos is None for t in tokens if not t.text.isalpha())


def test_tokenize_sentence_handles_contractions() -> None:
    """spaCy splits contractions; each part should be tokenized correctly."""

    tokens = tokenize_sentence('"It\'s" softly-lit.')

    texts = [t.text for t in tokens]
    # spaCy splits "It's" into "It" + "'s"
    assert '"' in texts
    assert "It" in texts
    assert "softly" in texts
    assert "lit" in texts

    # "It" is a stopword → not a clickable word
    it_tok = next(t for t in tokens if t.text == "It")
    assert it_tok.is_word is False

    # Content words should be clickable
    softly_tok = next(t for t in tokens if t.text == "softly")
    assert softly_tok.is_word is True
    lit_tok = next(t for t in tokens if t.text == "lit")
    assert lit_tok.is_word is True


@pytest.mark.anyio
async def test_ollama_client_returns_sentence_from_response() -> None:
    """The Ollama client should extract the generated sentence from the API payload."""

    prompt = (
        "Write exactly one natural English sentence. "
        "Keep it calm and literary. Include these words: lantern, meadow, window."
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

    sentence = await ollama_client.generate_completion(prompt)

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
        await ollama_client.generate_completion("Use these words: lantern.")


def test_reading_sentence_endpoint_returns_pos_tags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should return POS-tagged tokens with Markdown target markers."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("harbor", "NOUN"), ("lantern", "NOUN")],
        marked_words=[("harbor", "NOUN"), ("lantern", "NOUN")],
        sentence="A harbor lantern.",
        engine=engine,
    )

    async def fake_generate_completion(prompt: str) -> str:
        assert "harbor" in prompt
        assert "lantern" in prompt
        assert "You MUST mark the target words" in prompt
        return "A *harbor* *lantern* flickered in the rain."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "targetWords": [],
            "promptTemplate": "Write one sentence with {{target_words}}.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sentence"] == "A *harbor* *lantern* flickered in the rain."

    tokens = data["tokens"]
    harbor_tok = next(t for t in tokens if t["text"] == "harbor")
    assert harbor_tok["isWord"] is True
    assert harbor_tok["isTarget"] is True
    assert harbor_tok["pos"] == "NOUN"

    lantern_tok = next(t for t in tokens if t["text"] == "lantern")
    assert lantern_tok["pos"] == "NOUN"

    flickered_tok = next(t for t in tokens if t["text"] == "flickered")
    assert flickered_tok["isWord"] is True
    assert flickered_tok["pos"] == "VERB"

    dot_tok = next(t for t in tokens if t["text"] == ".")
    assert dot_tok["pos"] is None


def test_next_sentence_endpoint_picks_from_vocabulary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should prefer words from the vocabulary database."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("meadow", "NOUN")],
        marked_words=[("meadow", "NOUN")],
        sentence="A meadow bloomed.",
        engine=engine,
    )

    async def fake_generate_completion(prompt: str) -> str:
        assert "meadow" in prompt
        return "The *meadow* was green."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "targetWords": [],
            "promptTemplate": "Write one sentence with {{target_words}}.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "meadow" in data["words"]
    meadow_tok = next(t for t in data["tokens"] if t["text"] == "meadow")
    assert meadow_tok["isTarget"] is True


def test_delete_vocabulary_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/vocabulary should clear all records and return the count."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("alpha", "NOUN"), ("beta", "NOUN")],
        marked_words=[],
        sentence="test",
        engine=engine,
    )
    assert len(list_all_words(engine)) == 2

    response = client.delete("/api/vocabulary")
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    assert len(list_all_words(engine)) == 0


def test_reading_sentence_returns_502_on_ollama_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The API should return 502 when Ollama is unreachable."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("test", "NOUN")],
        marked_words=[("test", "NOUN")],
        sentence="test",
        engine=engine,
    )

    async def failing_generate(prompt: str) -> str:
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        failing_generate,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "targetWords": [],
            "promptTemplate": "Write a sentence with {{target_words}}.",
        },
    )

    assert response.status_code == 502


# ---------------------------------------------------------------------------
# Word store / familiarity update tests
# ---------------------------------------------------------------------------


def test_apply_feedback_creates_new_records() -> None:
    """Marked words should be created with familiarity 0, unmarked targets with 1."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("lantern", "NOUN"), ("meadow", "NOUN")],
        marked_words=[("meadow", "NOUN")],
        sentence="A lantern glowed beside the meadow.",
        engine=engine,
    )

    words = {(r.word, r.pos): r.familiarity for r in list_all_words(engine)}
    assert words[("lantern", "NOUN")] == 1  # unmarked target → +1
    assert words[("meadow", "NOUN")] == 0  # marked (unknown) → stays at 0


def test_apply_feedback_decreases_familiarity_for_marked_words() -> None:
    """Marking a previously familiar word should decrease its familiarity."""
    engine = _in_memory_engine()

    # First round: word becomes familiar
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor was calm.",
        engine=engine,
    )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["harbor"] == 1

    # Second round: user marks it as unknown
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
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
            target_words=[("resolve", "NOUN")],
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
            marked_words=[("resolve", "NOUN")],
            sentence="They showed resolve.",
            engine=engine,
        )
    words = {r.word: r.familiarity for r in list_all_words(engine)}
    assert words["resolve"] == 0


def test_pick_target_words_returns_least_familiar() -> None:
    """pick_target_words should return words with lowest familiarity first."""
    engine = _in_memory_engine()

    apply_feedback(
        [("alpha", "NOUN"), ("beta", "NOUN"), ("gamma", "NOUN"), ("delta", "NOUN")],
        [],
        "sentence",
        engine=engine,
    )
    # All start at familiarity 1. Boost alpha twice more.
    apply_feedback([("alpha", "NOUN")], [], "sentence", engine=engine)
    apply_feedback([("alpha", "NOUN")], [], "sentence", engine=engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "alpha" not in picked  # alpha has familiarity 3, others have 1
    assert len(picked) == 3


def test_clear_all_words_empties_database() -> None:
    """clear_all_words should delete every record."""
    engine = _in_memory_engine()

    apply_feedback(
        [("a", "NOUN"), ("b", "NOUN"), ("c", "NOUN")],
        [],
        "sentence",
        engine=engine,
    )
    assert len(list_all_words(engine)) == 3

    deleted = clear_all_words(engine)
    assert deleted == 3
    assert len(list_all_words(engine)) == 0


# ---------------------------------------------------------------------------
# POS-aware word store tests
# ---------------------------------------------------------------------------


def test_same_word_different_pos_stored_separately() -> None:
    """'leaves' as NOUN and 'leaves' as VERB should be separate records."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("leaves", "NOUN")],
        marked_words=[("leaves", "NOUN")],
        sentence="The leaves are beautiful.",
        engine=engine,
    )
    apply_feedback(
        target_words=[("leaves", "VERB")],
        marked_words=[],
        sentence="She leaves the room.",
        engine=engine,
    )

    records = {(r.word, r.pos): r.familiarity for r in list_all_words(engine)}
    assert records[("leaves", "NOUN")] == 0  # marked unknown
    assert records[("leaves", "VERB")] == 1  # unmarked target
    assert len(records) == 2


def test_feedback_with_pos_via_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/feedback endpoint should accept and store word+POS pairs."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.post(
        "/api/feedback",
        json={
            "targetWords": [
                {"word": "harbor", "pos": "NOUN"},
                {"word": "glowed", "pos": "VERB"},
            ],
            "markedWords": [{"word": "harbor", "pos": "NOUN"}],
            "sentence": "The harbor glowed at dusk.",
        },
    )

    assert response.status_code == 200
    records = {(r.word, r.pos): r.familiarity for r in list_all_words(engine)}
    assert records[("harbor", "NOUN")] == 0
    assert records[("glowed", "VERB")] == 1


def test_vocabulary_includes_pos(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/vocabulary endpoint should include POS in the response."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("lantern", "NOUN")],
        marked_words=[],
        sentence="The lantern glowed.",
        engine=engine,
    )

    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["words"][0] == {"word": "lantern", "pos": "NOUN", "familiarity": 1}
