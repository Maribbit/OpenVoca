from datetime import datetime, timezone

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select

INTERVAL_BASE = 2
INTERVAL_MAX = 64


class WordRecord(SQLModel, table=True):
    lemma: str = Field(primary_key=True)
    pos: str = Field(primary_key=True)
    interval: int = Field(default=INTERVAL_BASE, ge=INTERVAL_BASE)
    cooldown: int = Field(default=0, ge=0)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_context: str | None = Field(default=None)


_engine = create_engine("sqlite:///openvoca.db")
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
                    last_seen=now,
                    last_context=sentence,
                )
                session.add(record)
            else:
                record.interval = max(INTERVAL_BASE, record.interval // 2)
                record.cooldown = record.interval
                record.last_seen = now
                record.last_context = sentence

        # Hit: double interval for unmarked target words
        for lemma, pos in unmarked_targets:
            record = _find_record(session, lemma, pos)
            if record is None:
                record = WordRecord(
                    lemma=lemma,
                    pos=pos,
                    interval=INTERVAL_BASE * 2,
                    cooldown=INTERVAL_BASE * 2,
                    last_seen=now,
                    last_context=sentence,
                )
                session.add(record)
            else:
                record.interval = min(record.interval * 2, INTERVAL_MAX)
                record.cooldown = record.interval
                record.last_seen = now
                record.last_context = sentence

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


def list_all_words(engine=None) -> list[WordRecord]:
    """Return all word records sorted by review priority.

    Order: cooldown ASC (ready-to-review first), then interval ASC
    (least familiar first).
    """
    target = engine or _engine
    with Session(target) as session:
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
