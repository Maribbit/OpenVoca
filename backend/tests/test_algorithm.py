"""SRS algorithm tests: level progression, cooldown queue, POS matching,
target word picking, and the original_targets safety net."""

from src.services.word_store import (
    LEVEL_BASE,
    LEVEL_MAX,
    LEVEL_MIN,
    apply_feedback,
    list_all_words,
    pick_target_words,
    tick_cooldowns,
)

from conftest import _in_memory_engine


# ---------------------------------------------------------------------------
# Level progression
# ---------------------------------------------------------------------------


def test_apply_feedback_decreases_interval_for_marked_words() -> None:
    """Marking a previously known word should decrement its level."""
    engine = _in_memory_engine()

    # First round: word becomes known (hit -> level = LEVEL_MIN+1)
    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor was calm.",
        engine=engine,
    )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].level == LEVEL_MIN + 1

    # Tick cooldowns to make it available, then mark as unknown
    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[("harbor", "NOUN")],
        sentence="Ships lined the harbor.",
        engine=engine,
    )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["harbor"].level == LEVEL_MIN


def test_apply_feedback_caps_interval_at_boundaries() -> None:
    """Level should never go below LEVEL_MIN or above LEVEL_MAX."""
    engine = _in_memory_engine()

    # Increase to max: keep hitting
    apply_feedback(
        target_words=[("resolve", "NOUN")],
        marked_words=[],
        sentence="They showed resolve.",
        engine=engine,
    )
    # Now level = LEVEL_MIN+1 = 2
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
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)

    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].level == LEVEL_MAX

    # Decrease past minimum
    for _ in range(10):
        apply_feedback(
            target_words=[],
            marked_words=[("resolve", "NOUN")],
            sentence="They showed resolve.",
            engine=engine,
        )
    words = {r.lemma: r for r in list_all_words(engine)}
    assert words["resolve"].level == LEVEL_MIN


def test_graduated_word_relapse_on_mark() -> None:
    """Marking a graduated word (level=MAX) should bring it back into review."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple.",
        engine=engine,
    )
    for _ in range(20):
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)
        apply_feedback(
            target_words=[("apple", "NOUN")],
            marked_words=[],
            sentence="An apple.",
            engine=engine,
        )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX

    # Mark as unknown -> level decremented, back in review pool
    apply_feedback(
        target_words=[],
        marked_words=[("apple", "NOUN")],
        sentence="An apple fell.",
        engine=engine,
    )
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX - 1
    assert records["apple"].cooldown == LEVEL_BASE ** (LEVEL_MAX - 1)


# ---------------------------------------------------------------------------
# POS-aware matching
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

    records = {(r.lemma, r.pos): r.level for r in list_all_words(engine)}
    # Second feedback finds the existing NOUN record by lemma fallback
    # and updates it as a hit (level increments: 1 -> 2)
    assert records[("leaves", "NOUN")] == LEVEL_MIN + 1
    assert len(records) == 1


def test_feedback_pos_mismatch_updates_existing_record() -> None:
    """When feedback POS differs from DB POS, the existing record should be updated.

    This prevents the 'stuck in learning' bug where pick_target_words returns a
    lemma, the LLM uses it with a different POS, and the original record is never
    updated because apply_feedback creates a new record instead.
    """
    engine = _in_memory_engine()

    # User marks "run" as unknown -- enters DB as (run, VERB)
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
    assert records[0].level == LEVEL_MIN

    # Tick to make it available
    for _ in range(LEVEL_BASE**LEVEL_MIN):
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
    assert records[0].level == LEVEL_MIN + 1  # hit -> incremented


def test_feedback_pos_mismatch_miss_updates_existing_record() -> None:
    """When user marks a word with a different POS than in DB, existing record updates."""
    engine = _in_memory_engine()

    # "light" enters as ADJ hit -> level=2
    apply_feedback(
        target_words=[("light", "ADJ")],
        marked_words=[],
        sentence="A light breeze.",
        engine=engine,
    )
    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    # User marks "light" as NOUN (miss) -- should update existing ADJ record
    apply_feedback(
        target_words=[("light", "NOUN")],
        marked_words=[("light", "NOUN")],
        sentence="Turn on the light.",
        engine=engine,
    )

    records = list_all_words(engine)
    assert len(records) == 1
    assert records[0].lemma == "light"
    assert records[0].level == LEVEL_MIN


# ---------------------------------------------------------------------------
# Cooldown queue
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
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN

    tick_cooldowns(engine)
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN - 1


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
    for _ in range(LEVEL_BASE**LEVEL_MIN + 5):
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
    picked = pick_target_words(limit=3, engine=engine)
    assert picked == []


def test_graduated_words_not_picked() -> None:
    """Words with level >= LEVEL_MAX should not be picked."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple.",
        engine=engine,
    )
    for _ in range(20):
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)
        apply_feedback(
            target_words=[("apple", "NOUN")],
            marked_words=[],
            sentence="An apple.",
            engine=engine,
        )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MAX

    for _ in range(LEVEL_BASE**LEVEL_MAX):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" not in picked


def test_pick_target_words_returns_lowest_interval() -> None:
    """pick_target_words should return words with lowest level first."""
    engine = _in_memory_engine()

    # Create 4 words all as miss (level=LEVEL_MIN, cooldown=LEVEL_BASE**LEVEL_MIN)
    apply_feedback(
        [("alpha", "NOUN"), ("beta", "NOUN"), ("gamma", "NOUN"), ("delta", "NOUN")],
        [("alpha", "NOUN"), ("beta", "NOUN"), ("gamma", "NOUN"), ("delta", "NOUN")],
        "sentence",
        engine=engine,
    )
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    # Now hit alpha 3 times to increase its level
    for _ in range(3):
        apply_feedback([("alpha", "NOUN")], [], "sentence", engine=engine)
        for _ in range(LEVEL_BASE**LEVEL_MAX):
            tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "alpha" not in picked  # alpha has high level
    assert len(picked) == 3


# ---------------------------------------------------------------------------
# Full round simulation
# ---------------------------------------------------------------------------


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

    for r in list_all_words(engine):
        assert r.level == LEVEL_MIN
        assert r.cooldown == LEVEL_BASE**LEVEL_MIN

    # Round 1: tick LEVEL_BASE**LEVEL_MIN times to make all available
    for _ in range(LEVEL_BASE**LEVEL_MIN):
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
    assert records["apple"].level == LEVEL_MIN  # miss: stays at MIN
    assert records["apple"].cooldown == LEVEL_BASE**LEVEL_MIN
    assert records["harbor"].level == LEVEL_MIN + 1  # hit: incremented
    assert records["harbor"].cooldown == LEVEL_BASE ** (LEVEL_MIN + 1)
    assert records["lantern"].level == LEVEL_MIN + 1  # hit: incremented

    # Round 2: tick LEVEL_BASE**LEVEL_MIN times -- apple becomes available,
    # harbor/lantern still cooling
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    picked = pick_target_words(limit=3, engine=engine)
    assert "apple" in picked
    assert "harbor" not in picked  # cooldown still > 0
    assert "lantern" not in picked


# ---------------------------------------------------------------------------
# original_targets safety net (prevents infinite loop from lemma mismatch)
# ---------------------------------------------------------------------------


def test_original_targets_advances_unmatched_word() -> None:
    """original_targets should advance a word even when the tokenizer didn't match it."""
    engine = _in_memory_engine()

    # "analyze" enters DB as a miss
    apply_feedback(
        target_words=[("analyze", "VERB")],
        marked_words=[("analyze", "VERB")],
        sentence="Analyze the data.",
        engine=engine,
    )
    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["analyze"].level == LEVEL_MIN

    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    # LLM used "*analysis*" instead of "*analyze*" -- tokenizer matched
    # "analysis" (different lemma).  The feedback target_words only has
    # ("analysis", "NOUN"), missing the original "analyze".
    # Passing original_targets ensures "analyze" still advances.
    apply_feedback(
        target_words=[("analysis", "NOUN")],
        marked_words=[],
        sentence="The analysis was thorough.",
        original_targets=["analyze"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["analyze"].level == LEVEL_MIN + 1  # advanced via safety net


def test_original_targets_skipped_when_already_processed() -> None:
    """original_targets should not double-increment a word already in target_words."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[("apple", "NOUN")],
        sentence="An apple.",
        engine=engine,
    )
    for _ in range(LEVEL_BASE**LEVEL_MIN):
        tick_cooldowns(engine)

    # "apple" appears in both target_words and original_targets
    apply_feedback(
        target_words=[("apple", "NOUN")],
        marked_words=[],
        sentence="An apple fell.",
        original_targets=["apple"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["apple"].level == LEVEL_MIN + 1  # incremented only once


def test_original_targets_skipped_when_marked_unknown() -> None:
    """original_targets should not advance a word the user marked as unknown."""
    engine = _in_memory_engine()

    apply_feedback(
        target_words=[("harbor", "NOUN")],
        marked_words=[],
        sentence="The harbor.",
        engine=engine,
    )
    for _ in range(LEVEL_BASE ** (LEVEL_MIN + 1)):
        tick_cooldowns(engine)

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN + 1

    # User explicitly marks "harbor" unknown; original_targets should NOT override
    apply_feedback(
        target_words=[],
        marked_words=[("harbor", "NOUN")],
        sentence="The harbor glowed.",
        original_targets=["harbor"],
        engine=engine,
    )

    records = {r.lemma: r for r in list_all_words(engine)}
    assert records["harbor"].level == LEVEL_MIN  # decremented by miss, not advanced
