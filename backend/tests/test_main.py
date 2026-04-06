import httpx
import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app
from src.services.tokenizer import tokenize_sentence
from src.services.word_store import (
    INTERVAL_BASE,
    apply_feedback,
    list_all_words,
    tick_cooldowns,
)

from conftest import _in_memory_engine

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


def test_reading_sentence_endpoint_returns_pos_tags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should return POS-tagged tokens with Markdown target markers."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

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
            "prompt": "Write one sentence with harbor, lantern.",
            "targetWords": ["harbor", "lantern"],
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


def test_target_words_endpoint_picks_from_vocabulary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/target-words should tick cooldowns and pick words from the vocabulary."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("meadow", "NOUN")],
        marked_words=[("meadow", "NOUN")],
        sentence="A meadow bloomed.",
        engine=engine,
    )
    # Tick cooldowns so word becomes available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

    response = client.get("/api/target-words?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert "meadow" in data["words"]


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
    """The API should return 502 when the LLM is unreachable."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

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
            "prompt": "Write a sentence with test.",
            "targetWords": ["test"],
        },
    )

    assert response.status_code == 502


def test_feedback_with_pos_via_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/feedback endpoint should accept and store lemma+POS pairs."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.post(
        "/api/feedback",
        json={
            "targetWords": [
                {"lemma": "harbor", "pos": "NOUN"},
                {"lemma": "glow", "pos": "VERB"},
            ],
            "markedWords": [{"lemma": "harbor", "pos": "NOUN"}],
            "sentence": "The harbor glowed at dusk.",
        },
    )

    assert response.status_code == 200
    records = {(r.lemma, r.pos): r.interval for r in list_all_words(engine)}
    assert records[("harbor", "NOUN")] == INTERVAL_BASE  # miss
    assert records[("glow", "VERB")] == INTERVAL_BASE * 2  # hit


def test_vocabulary_includes_pos(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/vocabulary endpoint should include POS and interval in the response."""
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
    word_data = data["words"][0]
    assert word_data["lemma"] == "lantern"
    assert word_data["pos"] == "NOUN"
    assert word_data["interval"] == INTERVAL_BASE * 2  # hit → BASE*2
    assert word_data["cooldown"] == INTERVAL_BASE * 2


def test_next_endpoint_ticks_cooldowns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/reading-sentence/next should tick cooldowns each generation cycle."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    # Create a word with cooldown=2
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="The harbor.",
        engine=engine,
    )
    # Tick to cooldown=1
    for _ in range(INTERVAL_BASE - 1):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1

    async def fake_generate_completion(prompt: str) -> str:
        return "The *harbor* was calm."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    # After /next, the tick should have decremented cooldown to 0
    client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write one sentence with harbor.",
            "targetWords": ["harbor"],
        },
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 0


def test_target_words_endpoint_does_not_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/target-words should NOT tick cooldowns (to avoid burning on refresh)."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="The harbor.",
        engine=engine,
    )
    # Tick to cooldown=1
    for _ in range(INTERVAL_BASE - 1):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1

    # Multiple calls to /api/target-words should NOT change cooldown
    client.get("/api/target-words?limit=3")
    client.get("/api/target-words?limit=3")

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].cooldown == 1


# ---------------------------------------------------------------------------
# Composer hints API tests
# ---------------------------------------------------------------------------


def test_next_endpoint_accepts_full_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should accept a fully assembled prompt from the frontend."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    captured_prompts: list[str] = []

    async def fake_generate_completion(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "The sunset was calm."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write a sentence: sunset.\n[Scenario] You are a deadpan news anchor.\n[Difficulty] Use simple vocabulary.\n[Length] The sentence MUST be approximately 40 words long.",
            "targetWords": ["sunset"],
        },
    )

    assert response.status_code == 200
    prompt = captured_prompts[0]
    assert "news anchor" in prompt.lower()
    assert "40" in prompt
    assert "sunset" in prompt


def test_next_endpoint_works_with_minimal_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The /next endpoint should work with just a prompt and target words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_generate_completion(prompt: str) -> str:
        return "Hello world."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion",
        fake_generate_completion,
    )

    response = client.post(
        "/api/reading-sentence/next",
        json={
            "prompt": "Write a sentence with hello.",
            "targetWords": ["hello"],
        },
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Vocabulary CSV export (v0.6.3)
# ---------------------------------------------------------------------------


def test_export_vocabulary_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary/export should return a CSV with the correct headers and data."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("lantern", "NOUN"), ("glow", "VERB")],
        marked_words=[("lantern", "NOUN")],
        sentence="The lantern glowed.",
        engine=engine,
    )

    response = client.get("/api/vocabulary/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "openvoca-vocabulary.csv" in response.headers["content-disposition"]

    lines = response.text.strip().splitlines()
    assert lines[0] == "lemma,pos,interval,cooldown"
    assert len(lines) == 3  # header + 2 words

    rows = {line.split(",")[0]: line.split(",") for line in lines[1:]}
    assert rows["lantern"][1] == "NOUN"
    assert rows["glow"][1] == "VERB"


def test_export_vocabulary_csv_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary/export should return a CSV with only headers when vocabulary is empty."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.get("/api/vocabulary/export")
    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines == ["lemma,pos,interval,cooldown"]
