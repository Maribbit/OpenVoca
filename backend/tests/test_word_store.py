import pytest
from src.services.word_store import (
    INTERVAL_BASE,
    INTERVAL_MAX,
    ImportResult,
    MAX_IMPORT_ROWS,
    _make_engine,
    apply_feedback,
    clear_all_words,
    delete_word_record,
    import_vocabulary,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
    update_word_record,
)

from conftest import _in_memory_engine


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
    # Second feedback finds the existing NOUN record by lemma fallback
    # and updates it as a hit (interval doubles: 2 → 4)
    assert records[("leaves", "NOUN")] == INTERVAL_BASE * 2
    assert len(records) == 1


def test_feedback_pos_mismatch_updates_existing_record() -> None:
    """When feedback POS differs from DB POS, the existing record should be updated.

    This prevents the 'stuck in learning' bug where pick_target_words returns a
    lemma, the LLM uses it with a different POS, and the original record is never
    updated because apply_feedback creates a new record instead.
    """
    engine = _in_memory_engine()

    # User marks "run" as unknown — enters DB as (run, VERB)
    apply_feedback(
        target_words=[("run", "VERB")],
        marked_words=[("run", "VERB")],
        sentence="I run every morning.",
        engine=engine,
    )
    records = list_all_words(engine)
    assert len(records) == 1
    assert records[0].lemma == "run"
    assert records[0].pos == "VERB"
    assert records[0].interval == INTERVAL_BASE

    # Tick to make it available
    for _ in range(INTERVAL_BASE):
        tick_cooldowns(engine)

    # LLM uses "run" as NOUN, user doesn't mark it (hit)
    # Feedback comes with pos=NOUN but DB has pos=VERB
    apply_feedback(
        target_words=[("run", "NOUN")],
        marked_words=[],
        sentence="She went for a run.",
        engine=engine,
    )

    records = list_all_words(engine)
    # Should update existing record, NOT create a second one
    assert len(records) == 1
    assert records[0].lemma == "run"
    assert records[0].interval == INTERVAL_BASE * 2  # hit → doubled


def test_feedback_pos_mismatch_miss_updates_existing_record() -> None:
    """When user marks a word with a different POS than in DB, existing record updates."""
    engine = _in_memory_engine()

    # "light" enters as ADJ hit → interval=4
    apply_feedback(
        target_words=[("light", "ADJ")],
        marked_words=[],
        sentence="A light breeze.",
        engine=engine,
    )
    for _ in range(INTERVAL_BASE * 2):
        tick_cooldowns(engine)

    # User marks "light" as NOUN (miss) — should update existing ADJ record
    apply_feedback(
        target_words=[("light", "NOUN")],
        marked_words=[("light", "NOUN")],
        sentence="Turn on the light.",
        engine=engine,
    )

    records = list_all_words(engine)
    assert len(records) == 1
    assert records[0].lemma == "light"
    assert records[0].interval == max(INTERVAL_BASE, (INTERVAL_BASE * 2) // 2)


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


# ---------------------------------------------------------------------------
# Manual word record update (v0.6.7)
# ---------------------------------------------------------------------------


def test_update_word_record_interval() -> None:
    """update_word_record should update interval within bounds."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record(
        "apple", "NOUN", interval=INTERVAL_BASE * 2, engine=engine
    )
    assert record is not None
    assert record.interval == INTERVAL_BASE * 2

    record = update_word_record("apple", "NOUN", interval=INTERVAL_BASE, engine=engine)
    assert record is not None
    assert record.interval == INTERVAL_BASE


def test_update_word_record_interval_clamped() -> None:
    """Interval should be clamped to [INTERVAL_BASE, INTERVAL_MAX]."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )

    record = update_word_record("apple", "NOUN", interval=0, engine=engine)
    assert record is not None
    assert record.interval == INTERVAL_BASE

    record = update_word_record("apple", "NOUN", interval=999, engine=engine)
    assert record is not None
    assert record.interval == INTERVAL_MAX


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
        "apple", "NOUN", cooldown=INTERVAL_BASE * 2, engine=engine
    )
    assert record is not None
    assert record.cooldown == INTERVAL_BASE * 2


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
    assert record.cooldown == INTERVAL_BASE


def test_update_word_record_not_found() -> None:
    """update_word_record should return None for missing records."""
    engine = _in_memory_engine()

    result = update_word_record("nonexistent", "NOUN", interval=4, engine=engine)
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
    result = update_word_record("apple", "NOUN", interval=8, engine=engine)
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
        {"lemma": "harbor", "pos": "NOUN", "interval": "8", "cooldown": "3"},
        {"lemma": "lantern", "pos": "NOUN", "interval": "4", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    assert result.skipped == 0
    records = {(r.lemma, r.pos): r for r in list_all_words(engine)}
    assert records[("harbor", "NOUN")].interval == 8
    assert records[("harbor", "NOUN")].cooldown == 3
    assert records[("lantern", "NOUN")].interval == 4
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

    rows = [{"lemma": "harbor", "pos": "NOUN", "interval": "16", "cooldown": "8"}]
    result = import_vocabulary(rows, mode="overwrite", engine=engine)

    assert result.imported == 1
    assert result.skipped == 0
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].interval == 16
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
    original_interval = list_all_words(engine)[0].interval

    rows = [
        {"lemma": "harbor", "pos": "NOUN", "interval": "32", "cooldown": "16"},
        {"lemma": "lantern", "pos": "NOUN", "interval": "4", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, mode="skip", engine=engine)

    assert result.imported == 1  # only lantern
    assert result.skipped == 1  # harbor skipped
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].interval == original_interval  # preserved
    assert records["lantern"].interval == 4  # new


def test_import_vocabulary_default_mode_is_skip() -> None:
    """The default import mode should be 'skip' (safe default)."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    original_interval = list_all_words(engine)[0].interval

    rows = [{"lemma": "harbor", "pos": "NOUN", "interval": "32", "cooldown": "16"}]
    result = import_vocabulary(rows, engine=engine)  # no mode= → default

    assert result.imported == 0
    assert result.skipped == 1
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].interval == original_interval


def test_import_vocabulary_skips_missing_columns() -> None:
    """Rows missing required columns should be skipped and counted."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "apple", "pos": "NOUN", "interval": "4", "cooldown": "0"},
        {"lemma": "banana", "interval": "4", "cooldown": "0"},  # missing pos
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 1
    assert result.skipped == 1
    assert len(result.errors) == 1


def test_import_vocabulary_skips_empty_lemma_or_pos() -> None:
    """Rows with empty lemma or pos should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "", "pos": "NOUN", "interval": "4", "cooldown": "0"},
        {"lemma": "apple", "pos": "", "interval": "4", "cooldown": "0"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 2


def test_import_vocabulary_skips_non_integer_values() -> None:
    """Rows with non-integer interval or cooldown should be skipped."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "cherry", "pos": "NOUN", "interval": "abc", "cooldown": "0"},
        {"lemma": "mango", "pos": "NOUN", "interval": "4", "cooldown": "xyz"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 0
    assert result.skipped == 2
    assert len(result.errors) == 2


def test_import_vocabulary_clamps_out_of_range_values() -> None:
    """Interval and cooldown outside valid ranges should be clamped, not rejected."""
    engine = _in_memory_engine()

    rows = [
        {"lemma": "alpha", "pos": "NOUN", "interval": "0", "cooldown": "0"},
        {"lemma": "beta", "pos": "NOUN", "interval": "999", "cooldown": "500"},
    ]
    result = import_vocabulary(rows, engine=engine)

    assert result.imported == 2
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["alpha"].interval == INTERVAL_BASE
    assert records["beta"].interval == INTERVAL_MAX
    assert records["beta"].cooldown == INTERVAL_MAX  # clamped to interval


def test_import_vocabulary_normalizes_case() -> None:
    """lemma should be lowercased and pos uppercased on import."""
    engine = _in_memory_engine()

    rows = [{"lemma": "HARBOR", "pos": "noun", "interval": "4", "cooldown": "0"}]
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
        {"lemma": f"word{i}", "pos": "NOUN", "interval": "2", "cooldown": "0"}
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
    assert records["harbor"].interval == INTERVAL_BASE
    assert records["harbor"].cooldown == 0
    assert records["harbor"].last_context is None
    assert records["glow"].interval == INTERVAL_BASE


def test_import_vocabulary_with_last_seen_and_context() -> None:
    """Import should accept and preserve last_seen and last_context."""
    engine = _in_memory_engine()

    rows = [
        {
            "lemma": "harbor",
            "pos": "NOUN",
            "interval": "8",
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
            "interval": "8",
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
            "interval": "16",
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
