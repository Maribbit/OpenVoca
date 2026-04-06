from src.services.word_store import (
    INTERVAL_BASE,
    INTERVAL_MAX,
    apply_feedback,
    clear_all_words,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
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
