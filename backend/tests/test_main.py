import httpx
import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app
from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MIN,
    apply_feedback,
    list_all_words,
    tick_cooldowns,
)

from conftest import _in_memory_engine

client = TestClient(app)


def test_health_endpoint():
    """Health check endpoint returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "OpenVoca backend is running!",
    }


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
    for _ in range(LEVEL_BASE**LEVEL_MIN):
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
    records = {(r.lemma, r.pos): r.level for r in list_all_words(engine)}
    assert records[("harbor", "NOUN")] == LEVEL_MIN  # miss
    assert records[("glow", "VERB")] == LEVEL_MIN + 1  # hit


def test_vocabulary_includes_pos(monkeypatch: pytest.MonkeyPatch) -> None:
    """The /api/vocabulary endpoint should include POS and level in the response."""
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
    assert word_data["level"] == LEVEL_MIN + 1  # hit → MIN+1
    assert word_data["cooldown"] == LEVEL_BASE ** (LEVEL_MIN + 1)


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
    for _ in range(LEVEL_BASE**LEVEL_MIN - 1):
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
    for _ in range(LEVEL_BASE**LEVEL_MIN - 1):
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
    assert (
        lines[0]
        == "lemma,pos,level,cooldown,first_seen,last_seen,last_context,seen_count"
    )
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
    assert lines == [
        "lemma,pos,level,cooldown,first_seen,last_seen,last_context,seen_count"
    ]


def test_patch_vocabulary_word(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH /api/vocabulary/{lemma}/{pos} should update level and cooldown."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("alpha", "NOUN")],
        marked_words=[("alpha", "NOUN")],
        sentence="test",
        engine=engine,
    )

    response = client.patch(
        "/api/vocabulary/alpha/NOUN",
        json={"level": 3, "cooldown": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == 3
    assert data["cooldown"] == 0


def test_patch_vocabulary_word_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH should return 404 for unknown words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.patch(
        "/api/vocabulary/missing/NOUN",
        json={"level": 2},
    )
    assert response.status_code == 404


def test_delete_vocabulary_word(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/vocabulary/{lemma}/{pos} should delete a single word."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("alpha", "NOUN"), ("beta", "NOUN")],
        marked_words=[("alpha", "NOUN")],
        sentence="test",
        engine=engine,
    )
    assert len(list_all_words(engine)) == 2

    response = client.delete("/api/vocabulary/alpha/NOUN")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}
    assert len(list_all_words(engine)) == 1


def test_delete_vocabulary_word_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE should return 404 for unknown words."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.delete("/api/vocabulary/missing/NOUN")
    assert response.status_code == 404


def test_delete_then_patch_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    """PATCH after DELETE on same word (stale tab) should return 404."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("alpha", "NOUN")],
        marked_words=[("alpha", "NOUN")],
        sentence="test",
        engine=engine,
    )

    # Tab A deletes
    response = client.delete("/api/vocabulary/alpha/NOUN")
    assert response.status_code == 200

    # Tab B tries to patch (stale)
    response = client.patch(
        "/api/vocabulary/alpha/NOUN",
        json={"level": 3},
    )
    assert response.status_code == 404


def test_vocabulary_sort_due(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=due returns words by cooldown ASC, level ASC."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("alpha", "NOUN"), ("beta", "NOUN")],
        marked_words=[("alpha", "NOUN")],
        sentence="Alpha and beta.",
        engine=engine,
    )
    # alpha: marked (miss) → level=1, cooldown=2
    # beta: unmarked target (hit) → level=2, cooldown=4

    response = client.get("/api/vocabulary?sort=due")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    # alpha (cooldown=2) comes before beta (cooldown=4)
    assert lemmas == ["alpha", "beta"]


def test_vocabulary_sort_familiarity(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=familiarity returns words by level ASC, cooldown ASC."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("easy", "ADJ"), ("hard", "ADJ")],
        marked_words=[("hard", "ADJ")],
        sentence="Easy and hard.",
        engine=engine,
    )
    # hard: marked (miss) → level=1, cooldown=2
    # easy: unmarked target (hit) → level=2, cooldown=4

    response = client.get("/api/vocabulary?sort=familiarity")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    # hard (level=1) comes before easy (level=2) — least familiar first
    assert lemmas == ["hard", "easy"]


def test_vocabulary_sort_recent(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=recent returns words by last_seen DESC."""
    import time

    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("first", "NOUN")],
        marked_words=[],
        sentence="First sentence.",
        engine=engine,
    )
    time.sleep(0.05)
    apply_feedback(
        target_words=[("second", "NOUN")],
        marked_words=[],
        sentence="Second sentence.",
        engine=engine,
    )

    response = client.get("/api/vocabulary?sort=recent")
    assert response.status_code == 200
    lemmas = [w["lemma"] for w in response.json()["words"]]
    assert lemmas == ["second", "first"]


def test_vocabulary_sort_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary?sort=invalid returns 422."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    response = client.get("/api/vocabulary?sort=invalid")
    assert response.status_code == 422


def test_vocabulary_includes_last_seen(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/vocabulary response includes lastSeen field."""
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
    word_data = response.json()["words"][0]
    assert "lastSeen" in word_data
    assert word_data["lastSeen"] is not None


# ---------------------------------------------------------------------------
# Vocabulary import endpoint (v0.7.3)
# ---------------------------------------------------------------------------


def test_import_vocabulary_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/vocabulary/import should accept a CSV and return import summary."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,pos,level,cooldown\nharbor,NOUN,3,3\nlantern,NOUN,2,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 3
    assert records["lantern"].level == 2


def test_import_vocabulary_endpoint_upserts_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing a word that already exists should overwrite it."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )

    csv_content = "lemma,pos,level,cooldown\nharbor,NOUN,5,16\n"
    response = client.post(
        "/api/vocabulary/import",
        data={"mode": "overwrite"},
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 5
    assert records["harbor"].cooldown == 16


def test_import_vocabulary_endpoint_skips_invalid_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid CSV rows should be skipped and reported."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,pos,level,cooldown\ngood,NOUN,2,0\nbad,NOUN,notanint,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1


def test_import_vocabulary_endpoint_file_too_large(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Files larger than 1 MB should be rejected with 413."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    large_content = b"lemma,pos,level,cooldown\n" + b"x," * 600_000
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("big.csv", large_content, "text/csv")},
    )

    assert response.status_code == 413


def test_import_vocabulary_endpoint_non_utf8(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-UTF-8 encoded files should be rejected with 422."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    bad_bytes = b"\xff\xfe" + "harbor,NOUN,4,0\n".encode("utf-16-le")
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("bad.csv", bad_bytes, "text/csv")},
    )

    assert response.status_code == 422


def test_export_import_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exported CSV should be importable without any data loss.

    This catches column drift between export (main.py) and import
    (word_store.py _REQUIRED_IMPORT_COLS). If any column is renamed,
    added, or removed in either direction, this test will fail.
    """
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    # Seed 3 words with varying states
    apply_feedback(
        target_words=[("harbor", "NOUN"), ("lantern", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="The harbor lantern.",
        engine=engine,
    )
    apply_feedback(
        target_words=[("glow", "VERB")],
        marked_words=[],
        sentence="It glows.",
        engine=engine,
    )
    original = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert len(original) == 3

    # Export
    export_resp = client.get("/api/vocabulary/export")
    assert export_resp.status_code == 200
    csv_bytes = export_resp.content

    # Clear the DB
    from src.services.word_store import clear_all_words

    clear_all_words(engine)
    assert list_all_words(engine) == []

    # Re-import the same CSV
    import_resp = client.post(
        "/api/vocabulary/import",
        files={"file": ("roundtrip.csv", csv_bytes, "text/csv")},
    )
    assert import_resp.status_code == 200
    data = import_resp.json()
    assert data["imported"] == 3
    assert data["skipped"] == 0
    assert data["errors"] == []

    # Verify data integrity
    restored = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert len(restored) == 3
    for key, orig in original.items():
        assert key in restored, f"Missing record after roundtrip: {key}"
        rest = restored[key]
        assert rest.level == orig.level, f"{key} level mismatch"
        assert rest.cooldown == orig.cooldown, f"{key} cooldown mismatch"
        assert rest.last_context == orig.last_context, f"{key} last_context mismatch"
        assert rest.seen_count == orig.seen_count, f"{key} seen_count mismatch"
        assert rest.last_seen.isoformat() == orig.last_seen.isoformat(), (
            f"{key} last_seen mismatch"
        )
        assert rest.first_seen.isoformat() == orig.first_seen.isoformat(), (
            f"{key} first_seen mismatch"
        )


def test_import_vocabulary_endpoint_skip_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default (skip) mode should preserve existing records and only add new ones."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    original_level = list_all_words(engine)[0].level

    csv_content = "lemma,pos,level,cooldown\nharbor,NOUN,5,16\nlantern,NOUN,2,0\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1  # only lantern
    assert data["skipped"] == 1  # harbor skipped
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level  # preserved
    assert records["lantern"].level == 2  # new


def test_import_vocabulary_endpoint_minimal_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A CSV with only lemma and pos columns should import successfully."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "lemma,pos\nharbor,NOUN\nglow,VERB\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


def test_import_vocabulary_endpoint_bom_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A CSV with a UTF-8 BOM (from Excel) should be imported correctly."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    csv_content = "\ufefflemma,pos,level,cooldown\nharbor,NOUN,3,3\n"
    response = client.post(
        "/api/vocabulary/import",
        files={"file": ("vocab.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["skipped"] == 0


# ---------------------------------------------------------------------------
# Update check
# ---------------------------------------------------------------------------


def test_update_check_endpoint_returns_expected_shape() -> None:
    """GET /api/update-check always returns the required fields."""
    response = client.get("/api/update-check")
    assert response.status_code == 200
    data = response.json()
    assert "checked" in data
    assert "hasUpdate" in data
    assert "currentVersion" in data
    assert "latestVersion" in data
    assert "url" in data
    assert isinstance(data["checked"], bool)
    assert isinstance(data["hasUpdate"], bool)


def test_version_gt_comparisons() -> None:
    """_version_gt returns correct ordering for semantic versions."""
    from src.main import _version_gt

    assert _version_gt("0.9.1", "0.9.0") is True
    assert _version_gt("1.0.0", "0.9.9") is True
    assert _version_gt("0.9.0", "0.9.0") is False
    assert _version_gt("0.9.0", "0.9.1") is False
    assert _version_gt("0.10.0", "0.9.0") is True


# ---------------------------------------------------------------------------
# Streaming endpoint
# ---------------------------------------------------------------------------


def test_stream_endpoint_returns_sse_progress_and_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/reading-sentence/next/stream should emit progress + complete SSE events."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_stream(prompt: str):
        yield "A "
        yield "*harbor* "
        yield "gleamed."

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion_stream",
        fake_stream,
    )

    with client.stream(
        "POST",
        "/api/reading-sentence/next/stream",
        json={
            "prompt": "Write a sentence with harbor.",
            "targetWords": ["harbor"],
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = response.read().decode()

    import json as _json

    events = []
    for block in body.strip().split("\n\n"):
        lines = block.strip().split("\n")
        event_type = ""
        data = ""
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = line[6:]
        if event_type and data:
            events.append((event_type, _json.loads(data)))

    progress_events = [e for e in events if e[0] == "progress"]
    assert len(progress_events) >= 1
    assert progress_events[-1][1]["wordCount"] >= 2

    complete_events = [e for e in events if e[0] == "complete"]
    assert len(complete_events) == 1
    result = complete_events[0][1]
    assert result["sentence"] == "A *harbor* gleamed."
    assert "tokens" in result
    assert result["words"] == ["harbor"]


def test_stream_endpoint_returns_error_on_llm_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Streaming endpoint should emit an error event when the LLM raises."""
    engine = _in_memory_engine()
    monkeypatch.setattr("src.services.word_store._engine", engine)

    async def fake_stream(prompt: str):
        raise ValueError("Model unavailable")
        yield  # noqa: RET503 — make it a generator

    monkeypatch.setattr(
        main_module.llm,
        "generate_completion_stream",
        fake_stream,
    )

    with client.stream(
        "POST",
        "/api/reading-sentence/next/stream",
        json={
            "prompt": "Write a sentence.",
            "targetWords": ["word"],
        },
    ) as response:
        body = response.read().decode()

    assert "event: error" in body
    assert "Model unavailable" in body


def test_tts_endpoint_returns_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/tts should return streamed MP3 audio from Edge TTS."""
    import types

    fake_chunks = [
        {"type": "audio", "data": b"\xff\xfb\x90\x00"},
        {"type": "WordBoundary", "text": "Hello", "offset": 0.0, "duration": 0.5},
        {"type": "audio", "data": b"\xff\xfb\x90\x01"},
    ]

    class FakeCommunicate:
        def __init__(self, text: str, voice: str = "") -> None:
            self.text = text
            self.voice = voice

        async def stream(self):
            for chunk in fake_chunks:
                yield chunk

    fake_edge_tts = types.ModuleType("edge_tts")
    fake_edge_tts.Communicate = FakeCommunicate  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "edge_tts", fake_edge_tts)

    response = client.get("/api/tts", params={"text": "Hello world"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"\xff\xfb\x90\x00\xff\xfb\x90\x01"


def test_tts_endpoint_rejects_empty_text() -> None:
    """GET /api/tts should reject empty text."""
    response = client.get("/api/tts", params={"text": ""})
    assert response.status_code == 422


def test_tts_voices_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/tts/voices should return filtered voice list."""
    import types

    fake_voices = [
        {
            "ShortName": "en-US-EmmaNeural",
            "Gender": "Female",
            "Locale": "en-US",
            "FriendlyName": "Emma",
        },
        {
            "ShortName": "zh-CN-XiaoxiaoNeural",
            "Gender": "Female",
            "Locale": "zh-CN",
            "FriendlyName": "Xiaoxiao",
        },
    ]

    async def fake_list_voices():
        return fake_voices

    fake_edge_tts = types.ModuleType("edge_tts")
    fake_edge_tts.list_voices = fake_list_voices  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "edge_tts", fake_edge_tts)

    response = client.get("/api/tts/voices", params={"locale": "en"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "en-US-EmmaNeural"
    assert data[0]["gender"] == "Female"


def test_tts_endpoint_graceful_on_edge_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/tts should return empty audio when Edge TTS is unavailable."""
    import types

    class FakeCommunicateError:
        def __init__(self, text: str, voice: str = "") -> None:
            pass

        async def stream(self):
            raise ConnectionError("Edge TTS unreachable")
            yield  # noqa: RET503 — make it a generator

    fake_edge_tts = types.ModuleType("edge_tts")
    fake_edge_tts.Communicate = FakeCommunicateError  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "edge_tts", fake_edge_tts)

    response = client.get("/api/tts", params={"text": "Hello"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b""
