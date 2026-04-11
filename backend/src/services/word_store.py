import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select

INTERVAL_BASE = 2
INTERVAL_MAX = 64


class WordRecord(SQLModel, table=True):
    lemma: str = Field(primary_key=True)
    pos: str = Field(primary_key=True)
    interval: int = Field(default=INTERVAL_BASE, ge=INTERVAL_BASE)
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


def _find_record(session: Session, lemma: str, pos: str) -> WordRecord | None:
    """Find a WordRecord by (lemma, pos), falling back to lemma-only match.

    The LLM may use a word with a different POS than stored in the DB
    (e.g., "run" as NOUN when the DB has it as VERB). Without this fallback,
    feedback would create a duplicate record and the original would never
    have its interval updated — causing words to be stuck in "learning" state.
    """
    record = session.exec(
        select(WordRecord).where(WordRecord.lemma == lemma, WordRecord.pos == pos)
    ).first()
    if record is not None:
        return record
    # Fallback: match by lemma alone, prefer lowest interval (most likely picked)
    return session.exec(
        select(WordRecord)
        .where(WordRecord.lemma == lemma)
        .order_by(WordRecord.interval)
    ).first()


def apply_feedback(
    target_words: list[tuple[str, str]],
    marked_words: list[tuple[str, str]],
    sentence: str,
    engine=None,
) -> None:
    """Update interval/cooldown based on user feedback.

    Each word is a (lemma, pos) tuple.
    - Marked words (user flagged as unknown): halve interval (min INTERVAL_BASE).
    - Unmarked target words (user already knows): double interval (max INTERVAL_MAX).
    """
    target = engine or _engine
    now = datetime.now(timezone.utc)

    marked_set = {(w.lower(), p) for w, p in marked_words}
    target_set = {(w.lower(), p) for w, p in target_words}
    unmarked_targets = target_set - marked_set

    with Session(target) as session:
        # Miss: halve interval for marked (unknown) words
        for lemma, pos in marked_set:
            record = _find_record(session, lemma, pos)
            if record is None:
                record = WordRecord(
                    lemma=lemma,
                    pos=pos,
                    interval=INTERVAL_BASE,
                    cooldown=INTERVAL_BASE,
                    first_seen=now,
                    last_seen=now,
                    last_context=sentence,
                    seen_count=1,
                )
                session.add(record)
            else:
                record.interval = max(INTERVAL_BASE, record.interval // 2)
                record.cooldown = record.interval
                record.last_seen = now
                record.last_context = sentence
                record.seen_count += 1

        # Hit: double interval for unmarked target words
        for lemma, pos in unmarked_targets:
            record = _find_record(session, lemma, pos)
            if record is None:
                record = WordRecord(
                    lemma=lemma,
                    pos=pos,
                    interval=INTERVAL_BASE * 2,
                    cooldown=INTERVAL_BASE * 2,
                    first_seen=now,
                    last_seen=now,
                    last_context=sentence,
                    seen_count=1,
                )
                session.add(record)
            else:
                record.interval = min(record.interval * 2, INTERVAL_MAX)
                record.cooldown = record.interval
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
    """Return up to `limit` unique lemmas that are due for review.

    Only words with cooldown == 0 and interval < INTERVAL_MAX are eligible.
    Sorted by interval ASC (least familiar first), then last_seen ASC (oldest first).
    """
    target = engine or _engine
    with Session(target) as session:
        statement = (
            select(WordRecord)
            .where(WordRecord.cooldown == 0, WordRecord.interval < INTERVAL_MAX)
            .order_by(WordRecord.interval, WordRecord.last_seen)
        )
        results = session.exec(statement).all()
        seen: set[str] = set()
        words: list[str] = []
        for r in results:
            if r.lemma not in seen:
                seen.add(r.lemma)
                words.append(r.lemma)
                if len(words) >= limit:
                    break
        return words


def list_all_words(engine=None, *, sort: str = "due") -> list[WordRecord]:
    """Return all word records sorted by the given mode.

    Modes:
        - "due": cooldown ASC, interval ASC (due for review first)
        - "familiarity": interval ASC, cooldown ASC (least familiar first)
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
                WordRecord.interval, WordRecord.cooldown
            )
        else:
            statement = select(WordRecord).order_by(
                WordRecord.cooldown, WordRecord.interval
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
    pos: str,
    *,
    interval: int | None = None,
    cooldown: int | None = None,
    engine=None,
) -> WordRecord | None:
    """Update interval and/or cooldown for a specific word record.

    Interval is clamped to [INTERVAL_BASE, INTERVAL_MAX].
    Cooldown is clamped to [0, record.interval].
    Returns the updated record, or None if not found.
    """
    target = engine or _engine
    with Session(target) as session:
        record = session.exec(
            select(WordRecord).where(WordRecord.lemma == lemma, WordRecord.pos == pos)
        ).first()
        if record is None:
            return None

        if interval is not None:
            record.interval = max(INTERVAL_BASE, min(interval, INTERVAL_MAX))
        if cooldown is not None:
            record.cooldown = max(0, min(cooldown, record.interval))

        session.commit()
        session.refresh(record)
        return record


def delete_word_record(lemma: str, pos: str, engine=None) -> bool:
    """Delete a specific word record. Returns True if deleted, False if not found."""
    target = engine or _engine
    with Session(target) as session:
        record = session.exec(
            select(WordRecord).where(WordRecord.lemma == lemma, WordRecord.pos == pos)
        ).first()
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Vocabulary import
# ---------------------------------------------------------------------------

MAX_IMPORT_ROWS = 5_000
_REQUIRED_IMPORT_COLS = {"lemma", "pos"}


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

    Required columns: lemma, pos.
    Optional columns: interval, cooldown, last_seen, last_context.
    - interval defaults to INTERVAL_BASE, clamped to [INTERVAL_BASE, INTERVAL_MAX].
    - cooldown defaults to 0, clamped to [0, interval].
    - last_seen defaults to now (UTC); parsed as ISO 8601 if provided.
    - first_seen defaults to now; parsed as ISO 8601 if provided.
    - last_context defaults to None.
    - seen_count defaults to 0.
    - lemma is lowercased; pos is uppercased for normalization.
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
            pos = row["pos"].strip().upper()

            if not lemma or not pos:
                result.skipped += 1
                result.errors.append(f"Row {i}: lemma and pos must not be empty")
                continue

            # --- interval (optional, default INTERVAL_BASE) ---
            raw_interval = row.get("interval", "").strip()
            if raw_interval:
                try:
                    interval = int(raw_interval)
                except ValueError:
                    result.skipped += 1
                    result.errors.append(f"Row {i}: interval must be an integer")
                    continue
            else:
                interval = INTERVAL_BASE
            interval = max(INTERVAL_BASE, min(interval, INTERVAL_MAX))

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
            cooldown = max(0, min(cooldown, interval))

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

            existing = session.exec(
                select(WordRecord).where(
                    WordRecord.lemma == lemma, WordRecord.pos == pos
                )
            ).first()

            if existing is not None:
                if mode == "skip":
                    result.skipped += 1
                    continue
                existing.interval = interval
                existing.cooldown = cooldown
                existing.last_seen = last_seen
                existing.first_seen = first_seen
                existing.last_context = last_context
                existing.seen_count = seen_count
            else:
                session.add(
                    WordRecord(
                        lemma=lemma,
                        pos=pos,
                        interval=interval,
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
