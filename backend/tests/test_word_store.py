import pytest
from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MAX,
    LEVEL_MIN,
    ImportResult,
    MAX_IMPORT_ROWS,
    _make_engine,
    apply_feedback,
    clear_all_words,
    delete_word_record,
    import_vocabulary,
    list_all_words,
    tick_cooldowns,
    update_word_record,
)

from conftest import _in_memory_engine


# ---------------------------------------------------------------------------
# Word store / familiarity update tests
# ---------------------------------------------------------------------------


def test_apply_feedback_creates_new_records() -> None:
    """Marked words should be created with level=LEVEL_MIN, unmarked targets with LEVEL_MIN+1."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("lantern", "NOUN"), ("meadow", "NOUN")],
        marked_words=[("meadow", "NOUN")],
        sentence="A lantern glowed beside the meadow.",
        engine=engine,
    )

    words = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert words[("lantern", "NOUN")].level == LEVEL_MIN + 1  # hit → MIN+1
    assert words[("meadow", "NOUN")].level == LEVEL_MIN  # miss → MIN


def test_apply_feedback_sets_first_seen_once() -> None:
    """first_seen should be set on creation and not modified on updates."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    original_first_seen = list_all_words(engine)[0].first_seen

    # Tick and apply again — first_seen must stay the same
    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="Ships lined the harbor.",
        engine=engine,
    )

    words = list_all_words(engine)
    assert words[0].first_seen == original_first_seen


def test_apply_feedback_increments_seen_count() -> None:
    """seen_count should increment each time a word is a target word."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    assert list_all_words(engine)[0].seen_count == 1

    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="Ships lined the harbor.",
        engine=engine,
    )
    assert list_all_words(engine)[0].seen_count == 2


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
    assert records["flutter"].level == LEVEL_MIN
    assert records["flutter"].cooldown == LEVEL_BASE**LEVEL_MIN


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
# Manual word record update (v0.6.7)
# ---------------------------------------------------------------------------


def test_update_word_record_interval() -> None:
    """update_word_record should update level within bounds."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record("apple", "NOUN", level=LEVEL_MIN + 1, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN + 1

    record = update_word_record("apple", "NOUN", level=LEVEL_MIN, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN


def test_update_word_record_interval_clamped() -> None:
    """Level should be clamped to [LEVEL_MIN, LEVEL_MAX]."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record("apple", "NOUN", level=0, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MIN

    record = update_word_record("apple", "NOUN", level=999, engine=engine)
    assert record is not None
    assert record.level == LEVEL_MAX


def test_update_word_record_cooldown() -> None:
    """update_word_record should update cooldown within [0, interval]."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record("apple", "NOUN", cooldown=0, engine=engine)
    assert record is not None
    assert record.cooldown == 0

    record = update_word_record(
        "apple", "NOUN", cooldown=LEVEL_BASE ** (LEVEL_MIN + 1), engine=engine
    )
    assert record is not None
    assert record.cooldown == LEVEL_BASE ** (LEVEL_MIN + 1)


def test_update_word_record_cooldown_clamped() -> None:
    """Cooldown should be clamped to [0, interval]."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record("apple", "NOUN", cooldown=-5, engine=engine)
    assert record is not None
    assert record.cooldown == 0

    record = update_word_record("apple", "NOUN", cooldown=999, engine=engine)
    assert record is not None
    assert record.cooldown == LEVEL_BASE**LEVEL_MIN


def test_update_word_record_not_found() -> None:
    """update_word_record should return None for missing records."""
    engine = _in_memory_engine()

    result = update_word_record("nonexistent", "NOUN", level=2, engine=engine)
    assert result is None


# ---------------------------------------------------------------------------
# Delete single word record
# ---------------------------------------------------------------------------


def test_delete_word_record() -> None:
    """delete_word_record should remove a specific word."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN"), ("banana", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple and a banana.",
        engine=engine,
    )
    assert len(list_all_words(engine)) == 2

    deleted = delete_word_record("apple", "NOUN", engine=engine)
    assert deleted is True
    remaining = list_all_words(engine)
    assert len(remaining) == 1
    assert remaining[0].lemma == "banana"


def test_delete_word_record_not_found() -> None:
    """delete_word_record should return False for missing records."""
    engine = _in_memory_engine()

    deleted = delete_word_record("nonexistent", "NOUN", engine=engine)
    assert deleted is False


def test_delete_stale_record() -> None:
    """Deleting an already-deleted record (stale tab) should return False."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    # Tab A deletes the record
    assert delete_word_record("apple", "NOUN", engine=engine) is True
    # Tab B tries to delete the same record — stale
    assert delete_word_record("apple", "NOUN", engine=engine) is False


def test_update_stale_record() -> None:
    """Updating a record that was deleted in another tab should return None."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    # Tab A deletes the record
    delete_word_record("apple", "NOUN", engine=engine)
    # Tab B tries to update — stale
    result = update_word_record("apple", "NOUN", level=3, engine=engine)
    assert result is None


# --- OPENVOCA_DATA_DIR engine path ---


def test_make_engine_default_path() -> None:
    """_make_engine() without env var uses a relative openvoca.db path."""
    engine = _make_engine()
    assert "openvoca.db" in str(engine.url)


def test_make_engine_respects_data_dir(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_make_engine() uses OPENVOCA_DATA_DIR when set."""
    monkeypatch.setenv("OPENVOCA_DATA_DIR", str(tmp_path))
    engine = _make_engine()
    assert str(tmp_path / "openvoca.db") in str(engine.url)


# ---------------------------------------------------------------------------
# Vocabulary import (v0.7.3)
# ---------------------------------------------------------------------------


def test_import_vocabulary_creates_new_records() -> None:
    """import_vocabulary should insert records that don't exist yet."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "harbor", "pos": "NOUN", "level": "3", "cooldown": "3"},
        {"lemma": "lantern", "pos": "NOUN", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    assert result.skipped == 0
    records = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert records[("harbor", "NOUN")].level == 3
    assert records[("harbor", "NOUN")].cooldown == 3
    assert records[("lantern", "NOUN")].level == 2
    assert records[("lantern", "NOUN")].cooldown == 0


def test_import_vocabulary_overwrite_existing_records() -> None:
    """import_vocabulary(mode='overwrite') should overwrite existing records."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    # harbor now has interval=BASE*2, cooldown=BASE*2

    rows = [{"lemma": "harbor", "pos": "NOUN", "level": "4", "cooldown": "8"}]
    result = import_vocabulary(rows, mode="overwrite", engine=engine)

    assert result.imported == 1
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == 4
    assert records["harbor"].cooldown == 8


def test_import_vocabulary_skip_preserves_existing_records() -> None:
    """import_vocabulary(mode='skip') should keep existing records untouched."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    original_level = list_all_words(engine)[0].level

    rows = [
        {"lemma": "harbor", "pos": "NOUN", "level": "5", "cooldown": "16"},
        {"lemma": "lantern", "pos": "NOUN", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, mode="skip", engine=engine)

    assert result.imported == 1  # only lantern
    assert result.skipped == 1  # harbor skipped
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level  # preserved
    assert records["lantern"].level == 2  # new


def test_import_vocabulary_default_mode_is_skip() -> None:
    """The default import mode should be 'skip' (safe default)."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    original_level = list_all_words(engine)[0].level

    rows = [{"lemma": "harbor", "pos": "NOUN", "level": "5", "cooldown": "16"}]
    result = import_vocabulary(rows, engine=engine)  # no mode= → default

    assert result.imported == 0
    assert result.skipped == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == original_level


def test_import_vocabulary_skips_missing_columns() -> None:
    """Rows missing required columns should be skipped and counted."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "apple", "pos": "NOUN", "level": "2", "cooldown": "0"},
        {"lemma": "banana", "level": "2", "cooldown": "0"},  # missing pos
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    assert result.skipped == 1
    assert len(result.errors) == 1


def test_import_vocabulary_skips_empty_lemma_or_pos() -> None:
    """Rows with empty lemma or pos should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "", "pos": "NOUN", "level": "2", "cooldown": "0"},
        {"lemma": "apple", "pos": "", "level": "2", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 2


def test_import_vocabulary_skips_non_integer_values() -> None:
    """Rows with non-integer interval or cooldown should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "cherry", "pos": "NOUN", "level": "abc", "cooldown": "0"},
        {"lemma": "mango", "pos": "NOUN", "level": "2", "cooldown": "xyz"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 2
    assert len(result.errors) == 2


def test_import_vocabulary_clamps_out_of_range_values() -> None:
    """Interval and cooldown outside valid ranges should be clamped, not rejected."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "alpha", "pos": "NOUN", "level": "0", "cooldown": "0"},
        {"lemma": "beta", "pos": "NOUN", "level": "999", "cooldown": "500"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["alpha"].level == LEVEL_MIN
    assert records["beta"].level == LEVEL_MAX
    assert records["beta"].cooldown == LEVEL_BASE**LEVEL_MAX  # clamped to interval


def test_import_vocabulary_normalizes_case() -> None:
    """lemma should be lowercased and pos uppercased on import."""
    engine = _in_memory_engine()

    rows = [{"lemma": "HARBOR", "pos": "noun", "level": "2", "cooldown": "0"}]
    import_vocabulary(rows, engine=engine)

    records = list_all_words(engine)
    assert records[0].lemma == "harbor"
    assert records[0].pos == "NOUN"


def test_import_vocabulary_empty_rows() -> None:
    """Empty row list should return imported=0 with no errors."""
    engine = _in_memory_engine()
    result = import_vocabulary([], engine=engine)

    assert result.imported == 0
    assert result.skipped == 0
    assert result.errors == []


def test_import_vocabulary_too_many_rows() -> None:
    """Row count exceeding MAX_IMPORT_ROWS should fail without inserting anything."""
    engine = _in_memory_engine()

    overflow = [
        {"lemma": f"word{i}", "pos": "NOUN", "level": "1", "cooldown": "0"}
        for i in range(MAX_IMPORT_ROWS + 1)
    ]
    result = import_vocabulary(overflow, engine=engine)

    assert result.imported == 0
    assert len(result.errors) == 1
    assert len(list_all_words(engine)) == 0


def test_import_result_is_dataclass() -> None:
    """ImportResult should have default zero values."""
    r = ImportResult()
    assert r.imported == 0
    assert r.skipped == 0
    assert r.errors == []


def test_import_vocabulary_minimal_columns() -> None:
    """Rows with only lemma and pos should import with default values."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "harbor", "pos": "NOUN"},
        {"lemma": "glow", "pos": "VERB"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN
    assert records["harbor"].cooldown == 0
    assert records["harbor"].last_context is None
    assert records["glow"].level == LEVEL_MIN


def test_import_vocabulary_with_last_seen_and_context() -> None:
    """Import should accept and preserve last_seen and last_context."""
    engine = _in_memory_engine()

    rows = [
        {
            "lemma": "harbor",
            "pos": "NOUN",
            "level": "3",
            "cooldown": "3",
            "last_seen": "2026-01-15T10:30:00+00:00",
            "last_context": "The harbor was calm.",
        },
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    records = list_all_words(engine)
    assert records[0].last_seen.year == 2026
    assert records[0].last_seen.month == 1
    assert records[0].last_context == "The harbor was calm."


def test_import_vocabulary_bad_last_seen_skips_row() -> None:
    """Invalid last_seen format should cause the row to be skipped."""
    engine = _in_memory_engine()

    rows = [
        {
            "lemma": "harbor",
            "pos": "NOUN",
            "level": "3",
            "cooldown": "3",
            "last_seen": "not-a-date",
        },
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 1
    assert "ISO 8601" in result.errors[0]


def test_import_vocabulary_overwrite_preserves_csv_context() -> None:
    """Overwrite mode should replace last_seen and last_context from CSV."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )

    rows = [
        {
            "lemma": "harbor",
            "pos": "NOUN",
            "level": "4",
            "cooldown": "8",
            "last_seen": "2025-06-01T00:00:00+00:00",
            "last_context": "A quiet harbor.",
        },
    ]
    result = import_vocabulary(rows, mode="overwrite", engine=engine)

    assert result.imported == 1
    records = list_all_words(engine)
    assert records[0].last_context == "A quiet harbor."
    assert records[0].last_seen.year == 2025
