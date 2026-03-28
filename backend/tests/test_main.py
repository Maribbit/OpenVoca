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
    INTERVAL_BASE,
    INTERVAL_MAX,
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
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
    # Tick cooldowns so words become available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

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
    # Tick cooldowns so word becomes available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

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
    # Tick cooldowns so word becomes available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

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
    """Marked words should be created with interval=BASE, unmarked targets with BASE*2."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("lantern", "NOUN"), ("meadow", "NOUN")],
        marked_words=[("meadow", "NOUN")],
        sentence="A lantern glowed beside the meadow.",
        engine=engine,
    )

    words = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert words[("lantern", "NOUN")].interval == INTERVAL_BASE * 2  # hit → BASE*2
    assert words[("meadow", "NOUN")].interval == INTERVAL_BASE  # miss → BASE


def test_apply_feedback_decreases_interval_for_marked_words() -> None:
    """Marking a previously known word should halve its interval."""
    engine = _in_memory_engine()

    # First round: word becomes known (hit → interval = BASE*2)
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor was calm.",
        engine=engine,
    )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].interval == INTERVAL_BASE * 2

    # Tick cooldowns to make it available, then mark as unknown
    for _ in range(INTERVAL_BASE * 2):
        tick_cooldowns(engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="Ships lined the harbor.",
        engine=engine,
    )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].interval == max(INTERVAL_BASE, (INTERVAL_BASE * 2) // 2)


def test_apply_feedback_caps_interval_at_boundaries() -> None:
    """Interval should never go below INTERVAL_BASE or above INTERVAL_MAX."""
    engine = _in_memory_engine()

    # Increase to max: need log2(INTERVAL_MAX / (BASE*2)) + 1 hits
    # Start at BASE*2=4, then 8, 16, 32, 64 = 4 more hits
    apply_feedback(
        target_words=[("resolve", "NOUN")],
        marked_words=[],
        sentence="They showed resolve.",
        engine=engine,
    )
    # Now interval = BASE*2 = 4
    for _ in range(10):
        tick_cooldowns(engine)
    # Keep hitting until we reach max
    for _ in range(10):
        apply_feedback(
            target_words=[("resolve", "NOUN")],
            marked_words=[],
            sentence="They showed resolve.",
            engine=engine,
        )
        for _ in range(INTERVAL_MAX):
            tick_cooldowns(engine)

    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].interval == INTERVAL_MAX

    # Decrease past minimum
    for _ in range(10):
        apply_feedback(
            target_words=[],
            marked_words=[("resolve", "NOUN")],
            sentence="They showed resolve.",
            engine=engine,
        )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].interval == INTERVAL_BASE


def test_pick_target_words_returns_lowest_interval() -> None:
    """pick_target_words should return words with lowest interval first."""
    engine = _in_memory_engine()

    # Create 4 words all as miss (interval=BASE, cooldown=BASE)
    apply_feedback(
        [("alpha", "NOUN"), ("beta", "NOUN"), ("gamma", "NOUN"), ("delta", "NOUN")],
        [("alpha", "NOUN"), ("beta", "NOUN"), ("gamma", "NOUN"), ("delta", "NOUN")],
        "sentence",
        engine=engine,
    )
    # Tick cooldowns so they become available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

    # Now hit alpha 3 times to increase its interval
    for _ in range(3):
        apply_feedback([("alpha", "NOUN")], [], "sentence", engine=engine)
        for _ in range(INTERVAL_MAX):
            tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "alpha" not in picked  # alpha has high interval
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

    records = {(r.lemma, r.pos): r.interval for r in list_all_words(engine)}
    assert records[("leaves", "NOUN")] == INTERVAL_BASE  # marked (miss)
    assert records[("leaves", "VERB")] == INTERVAL_BASE * 2  # unmarked (hit)
    assert len(records) == 2


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


# ---------------------------------------------------------------------------
# Cooldown queue algorithm tests (v0.5.0)
# ---------------------------------------------------------------------------


def test_tick_cooldowns_decrements() -> None:
    """tick_cooldowns should decrement cooldown by 1 for all words with cooldown > 0."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )
    # apple: interval=BASE, cooldown=BASE
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == INTERVAL_BASE

    tick_cooldowns(engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == INTERVAL_BASE - 1


def test_tick_cooldowns_does_not_go_below_zero() -> None:
    """tick_cooldowns should not decrement cooldown below 0."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )
    # Tick more times than cooldown value
    for _ in range(INTERVAL_BASE + 5):
        tick_cooldowns(engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == 0


def test_cooldown_words_not_picked() -> None:
    """Words with cooldown > 0 should not be picked."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )
    # apple has cooldown=BASE, should not be picked
    picked = pick_target_words(limit=3, engine=engine)
    assert picked == []


def test_graduated_words_not_picked() -> None:
    """Words with interval >= INTERVAL_MAX should not be picked."""
    engine = _in_memory_engine()

    # Manually create a graduated word by repeated hits
    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple.",
        engine=engine,
    )
    # Keep hitting until graduated
    for _ in range(20):
        for _ in range(INTERVAL_MAX):
            tick_cooldowns(engine)
        apply_feedback(
            target_words=[("apple", "NOUN")],
            marked_words=[],
            sentence="An apple.",
            engine=engine,
        )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].interval == INTERVAL_MAX

    for _ in range(INTERVAL_MAX):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" not in picked


def test_graduated_word_relapse_on_mark() -> None:
    """Marking a graduated word (interval=MAX) should bring it back into review."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple.",
        engine=engine,
    )
    for _ in range(20):
        for _ in range(INTERVAL_MAX):
            tick_cooldowns(engine)
        apply_feedback(
            target_words=[("apple", "NOUN")],
            marked_words=[],
            sentence="An apple.",
            engine=engine,
        )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].interval == INTERVAL_MAX

    # Mark as unknown → interval halved, back in review pool
    apply_feedback(
        target_words=[],
        marked_words=[("apple", "NOUN")],
        sentence="An apple fell.",
        engine=engine,
    )
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].interval == INTERVAL_MAX // 2
    assert records["apple"].cooldown == INTERVAL_MAX // 2


def test_non_target_word_marked_creates_record() -> None:
    """Marking a non-target word should create it with miss rules."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[],
        marked_words=[("flutter", "VERB")],
        sentence="The flag fluttered.",
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert "flutter" in records
    assert records["flutter"].interval == INTERVAL_BASE
    assert records["flutter"].cooldown == INTERVAL_BASE


def test_last_context_stored() -> None:
    """apply_feedback should store the sentence as last_context."""
    engine = _in_memory_engine()

    sentence = "The harbor was calm."
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence=sentence,
        engine=engine,
    )
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].last_context == sentence


def test_full_round_simulation() -> None:
    """Simulate a complete 3-round scenario from Algorithm.md."""
    engine = _in_memory_engine()

    # Setup: create 3 words as unknown
    apply_feedback(
        target_words=[("apple", "NOUN"), ("harbor", "NOUN"), ("lantern", "NOUN")],
        marked_words=[("apple", "NOUN"), ("harbor", "NOUN"), ("lantern", "NOUN")],
        sentence="initial",
        engine=engine,
    )

    # All at interval=BASE, cooldown=BASE
    for r in list_all_words(engine):
        assert r.interval == INTERVAL_BASE
        assert r.cooldown == INTERVAL_BASE

    # Round 1: tick BASE times to make all available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert len(picked) == 3

    # User marks apple, knows harbor and lantern
    apply_feedback(
        target_words=[("apple", "NOUN"), ("harbor", "NOUN"), ("lantern", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="Apple harbor lantern.",
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].interval == INTERVAL_BASE  # miss: stays at BASE
    assert records["apple"].cooldown == INTERVAL_BASE
    assert records["harbor"].interval == INTERVAL_BASE * 2  # hit: doubled
    assert records["harbor"].cooldown == INTERVAL_BASE * 2
    assert records["lantern"].interval == INTERVAL_BASE * 2  # hit: doubled

    # Round 2: tick BASE times — apple becomes available, harbor/lantern still cooling
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" in picked
    assert "harbor" not in picked  # cooldown still > 0
    assert "lantern" not in picked


def test_next_endpoint_ticks_cooldowns(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /next endpoint should call tick_cooldowns before picking words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    # Create a word with cooldown=1 (one tick away from being available)
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
        # The endpoint should have ticked, making harbor available
        assert "harbor" in prompt
        return "The *harbor* was calm."

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
    assert "harbor" in response.json()["words"]
