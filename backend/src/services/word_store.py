import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select

LEVEL_MIN = 1
LEVEL_MAX = 6
LEVEL_BASE = 2  # actual interval = LEVEL_BASE ** level


class WordRecord(SQLModel, table=True):
    lemma: str = Field(primary_key=True)
    level: int = Field(default=LEVEL_MIN, ge=LEVEL_MIN)
    cooldown: int = Field(default=0, ge=0)
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_context: str | None = Field(default=None)
    seen_count: int = Field(default=0, ge=0)


def _make_engine():
    """Create a SQLite engine, respecting OPENVOCA_DATA_DIR if set."""
    data_dir = os.environ.get("OPENVOCA_DATA_DIR")
    if data_dir:
        db_path = Path(data_dir) / "openvoca.db"
    else:
        db_path = Path("openvoca.db")
    return create_engine(f"sqlite:///{db_path}")


_engine = _make_engine()
SQLModel.metadata.create_all(_engine)


def get_engine():
    return _engine


def init_db(engine=None) -> None:
    """Create tables if they don't exist."""
    target = engine or _engine
    SQLModel.metadata.create_all(target)


def apply_feedback(
    target_words: list[str],
    marked_words: list[str],
    sentence: str,
    original_targets: list[str] | None = None,
    engine=None,
) -> None:
    """Update level/cooldown based on user feedback.

    Each word is a lemma string.
    - Marked words (user flagged as unknown): decrement level (min LEVEL_MIN).
    - Unmarked target words (user already knows): increment level (max LEVEL_MAX).

    ``original_targets`` are the raw lemmas originally picked by
    ``pick_target_words``.  When the LLM uses a derived form whose spaCy
    lemma differs from the DB lemma (e.g. "analysis" vs "analyze"), the
    tokenizer cannot match it back.  By including the original lemmas we
    guarantee every picked word advances unless the user explicitly marked
    it unknown.
    """
    target = engine or _engine
    now = datetime.now(timezone.utc)

    marked_set = {w.lower() for w in marked_words}
    target_set = {w.lower() for w in target_words}
    unmarked_targets = target_set - marked_set

    with Session(target) as session:
        # Miss: decrement level for marked (unknown) words
        for lemma in marked_set:
            record = session.get(WordRecord, lemma)
            if record is None:
                new_level = LEVEL_MIN
                record = WordRecord(
                    lemma=lemma,
                    level=new_level,
                    cooldown=LEVEL_BASE**new_level,
                    first_seen=now,
                    last_seen=now,
                    last_context=sentence,
                    seen_count=1,
                )
                session.add(record)
            else:
                record.level = max(LEVEL_MIN, record.level - 1)
                record.cooldown = LEVEL_BASE**record.level
                record.last_seen = now
                record.last_context = sentence
                record.seen_count += 1

        # Hit: increment level for unmarked target words
        processed_lemmas: set[str] = set()
        for lemma in unmarked_targets:
            record = session.get(WordRecord, lemma)
            if record is None:
                new_level = LEVEL_MIN + 1
                record = WordRecord(
                    lemma=lemma,
                    level=new_level,
                    cooldown=LEVEL_BASE**new_level,
                    first_seen=now,
                    last_seen=now,
                    last_context=sentence,
                    seen_count=1,
                )
                session.add(record)
            else:
                record.level = min(record.level + 1, LEVEL_MAX)
                record.cooldown = LEVEL_BASE**record.level
                record.last_seen = now
                record.last_context = sentence
                record.seen_count += 1
            processed_lemmas.add(lemma)

        # Safety net: ensure every originally-picked lemma advances
        # even if the tokenizer could not match it back to the sentence.
        if original_targets:
            for orig in original_targets:
                low = orig.lower()
                if low in marked_set or low in processed_lemmas:
                    continue
                record = session.get(WordRecord, low)
                if record is not None:
                    record.level = min(record.level + 1, LEVEL_MAX)
                    record.cooldown = LEVEL_BASE**record.level
                    record.last_seen = now
                    record.last_context = sentence
                    record.seen_count += 1

        session.commit()


def tick_cooldowns(engine=None) -> None:
    """Decrement cooldown by 1 for all words with cooldown > 0."""
    target = engine or _engine
    with Session(target) as session:
        session.exec(
            text("UPDATE wordrecord SET cooldown = cooldown - 1 WHERE cooldown > 0")
        )
        session.commit()


def pick_target_words(limit: int = 3, engine=None) -> list[str]:
    """Return up to `limit` lemmas that are due for review.

    Only words with cooldown == 0 and level < LEVEL_MAX are eligible.
    Sorted by level ASC (least familiar first), then last_seen ASC (oldest first).
    """
    target = engine or _engine
    with Session(target) as session:
        statement = (
            select(WordRecord)
            .where(WordRecord.cooldown == 0, WordRecord.level < LEVEL_MAX)
            .order_by(WordRecord.level, WordRecord.last_seen)
            .limit(limit)
        )
        results = session.exec(statement).all()
        return [r.lemma for r in results]


def list_all_words(engine=None, *, sort: str = "due") -> list[WordRecord]:
    """Return all word records sorted by the given mode.

    Modes:
        - "due": cooldown ASC, level ASC (due for review first)
        - "familiarity": level ASC, cooldown ASC (least familiar first)
        - "recent": last_seen DESC (most recently reviewed first)
    """
    target = engine or _engine
    with Session(target) as session:
        if sort == "recent":
            statement = select(WordRecord).order_by(
                WordRecord.last_seen.desc()  # type: ignore[union-attr]
            )
        elif sort == "familiarity":
            statement = select(WordRecord).order_by(
                WordRecord.level, WordRecord.cooldown
            )
        else:
            statement = select(WordRecord).order_by(
                WordRecord.cooldown, WordRecord.level
            )
        results = session.exec(statement).all()
        return list(results)


def clear_all_words(engine=None) -> int:
    """Delete all word records. Returns count of deleted rows."""
    target = engine or _engine
    with Session(target) as session:
        result = session.exec(text("DELETE FROM wordrecord"))
        session.commit()
        return result.rowcount  # type: ignore[return-value]


def update_word_record(
    lemma: str,
    *,
    level: int | None = None,
    cooldown: int | None = None,
    engine=None,
) -> WordRecord | None:
    """Update level and/or cooldown for a specific word record.

    Level is clamped to [LEVEL_MIN, LEVEL_MAX].
    Cooldown is clamped to [0, LEVEL_BASE ** record.level].
    Returns the updated record, or None if not found.
    """
    target = engine or _engine
    with Session(target) as session:
        record = session.get(WordRecord, lemma)
        if record is None:
            return None

        if level is not None:
            record.level = max(LEVEL_MIN, min(level, LEVEL_MAX))
        if cooldown is not None:
            record.cooldown = max(0, min(cooldown, LEVEL_BASE**record.level))

        session.commit()
        session.refresh(record)
        return record


def delete_word_record(lemma: str, engine=None) -> bool:
    """Delete a specific word record. Returns True if deleted, False if not found."""
    target = engine or _engine
    with Session(target) as session:
        record = session.get(WordRecord, lemma)
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Vocabulary import
# ---------------------------------------------------------------------------

MAX_IMPORT_ROWS = 5_000
_REQUIRED_IMPORT_COLS = {"lemma"}


@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def import_vocabulary(
    rows: list[dict[str, str]],
    *,
    mode: Literal["skip", "overwrite"] = "skip",
    engine=None,
) -> ImportResult:
    """Import vocabulary from parsed CSV rows.

    Required columns: lemma.
    Optional columns: level, cooldown, last_seen, first_seen, last_context,
    seen_count.  The legacy ``pos`` column is accepted but ignored.
    - level defaults to LEVEL_MIN, clamped to [LEVEL_MIN, LEVEL_MAX].
    - cooldown defaults to 0, clamped to [0, LEVEL_BASE ** level].
    - last_seen defaults to now (UTC); parsed as ISO 8601 if provided.
    - first_seen defaults to now; parsed as ISO 8601 if provided.
    - last_context defaults to None.
    - seen_count defaults to 0.
    - lemma is lowercased for normalization.
    - mode="skip" (default): existing records are kept, only new words imported.
    - mode="overwrite": existing records are overwritten with imported values.
    - Invalid rows are skipped and counted in result.skipped.
    """
    result = ImportResult()

    if len(rows) > MAX_IMPORT_ROWS:
        result.errors.append(f"Too many rows: {len(rows)} (max {MAX_IMPORT_ROWS})")
        return result

    target = engine or _engine
    now = datetime.now(timezone.utc)

    with Session(target) as session:
        for i, row in enumerate(rows, start=2):  # row 1 is the CSV header
            if not _REQUIRED_IMPORT_COLS.issubset(row.keys()):
                missing = sorted(_REQUIRED_IMPORT_COLS - set(row.keys()))
                result.skipped += 1
                result.errors.append(f"Row {i}: missing columns: {missing}")
                continue

            lemma = row["lemma"].strip().lower()

            if not lemma:
                result.skipped += 1
                result.errors.append(f"Row {i}: lemma must not be empty")
                continue

            # --- level (optional, default LEVEL_MIN) ---
            raw_level = row.get("level", "").strip()
            if raw_level:
                try:
                    level = int(raw_level)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: level must be an integer")
                    continue
            else:
                level = LEVEL_MIN
            level = max(LEVEL_MIN, min(level, LEVEL_MAX))

            # --- cooldown (optional, default 0) ---
            raw_cooldown = row.get("cooldown", "").strip()
            if raw_cooldown:
                try:
                    cooldown = int(raw_cooldown)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: cooldown must be an integer")
                    continue
            else:
                cooldown = 0
            cooldown = max(0, min(cooldown, LEVEL_BASE**level))

            # --- last_seen (optional, default now) ---
            raw_last_seen = row.get("last_seen", "").strip()
            if raw_last_seen:
                try:
                    last_seen = datetime.fromisoformat(raw_last_seen)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: last_seen must be ISO 8601")
                    continue
            else:
                last_seen = now

            # --- first_seen (optional, default now) ---
            raw_first_seen = row.get("first_seen", "").strip()
            if raw_first_seen:
                try:
                    first_seen = datetime.fromisoformat(raw_first_seen)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: first_seen must be ISO 8601")
                    continue
            else:
                first_seen = now

            # --- last_context (optional, default None) ---
            last_context = row.get("last_context", "").strip() or None

            # --- seen_count (optional, default 0) ---
            raw_seen_count = row.get("seen_count", "").strip()
            if raw_seen_count:
                try:
                    seen_count = int(raw_seen_count)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: seen_count must be an integer")
                    continue
                seen_count = max(0, seen_count)
            else:
                seen_count = 0

            existing = session.get(WordRecord, lemma)

            if existing is not None:
                if mode == "skip":
                    result.skipped += 1
                    continue
                existing.level = level
                existing.cooldown = cooldown
                existing.last_seen = last_seen
                existing.first_seen = first_seen
                existing.last_context = last_context
                existing.seen_count = seen_count
            else:
                session.add(
                    WordRecord(
                        lemma=lemma,
                        level=level,
                        cooldown=cooldown,
                        first_seen=first_seen,
                        last_seen=last_seen,
                        last_context=last_context,
                        seen_count=seen_count,
                    )
                )

            result.imported += 1

        session.commit()

    return result
