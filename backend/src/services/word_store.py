from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel, create_engine, select


class WordRecord(SQLModel, table=True):
    word: str = Field(primary_key=True)
    familiarity: int = Field(default=0, ge=0, le=4)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


_engine = create_engine("sqlite:///openvoca.db")
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
    engine=None,
) -> None:
    """Update familiarity based on user feedback.

    - Marked words (user flagged as unknown): decrease familiarity (min 0).
    - Unmarked target words (user already knows): increase familiarity (max 4).
    """
    target = engine or _engine
    now = datetime.now(timezone.utc)

    marked_set = {w.lower() for w in marked_words}
    target_set = {w.lower() for w in target_words}
    unmarked_targets = target_set - marked_set

    with Session(target) as session:
        # Decrease familiarity for marked (unknown) words
        for word in marked_set:
            record = session.get(WordRecord, word)
            if record is None:
                record = WordRecord(word=word, familiarity=0, last_seen=now)
                session.add(record)
            else:
                record.familiarity = max(0, record.familiarity - 1)
                record.last_seen = now
            session.add(record)

        # Increase familiarity for unmarked target words
        for word in unmarked_targets:
            record = session.get(WordRecord, word)
            if record is None:
                record = WordRecord(word=word, familiarity=1, last_seen=now)
                session.add(record)
            else:
                record.familiarity = min(4, record.familiarity + 1)
                record.last_seen = now
            session.add(record)

        session.commit()


def pick_target_words(limit: int = 3, engine=None) -> list[str]:
    """Return up to `limit` words with lowest familiarity, most recently seen first as tiebreaker."""
    target = engine or _engine
    with Session(target) as session:
        statement = (
            select(WordRecord)
            .where(WordRecord.familiarity < 4)
            .order_by(WordRecord.familiarity, WordRecord.last_seen.desc())
            .limit(limit)
        )
        results = session.exec(statement).all()
        return [r.word for r in results]


def list_all_words(engine=None) -> list[WordRecord]:
    """Return all word records ordered by familiarity ascending."""
    target = engine or _engine
    with Session(target) as session:
        statement = select(WordRecord).order_by(
            WordRecord.familiarity, WordRecord.last_seen.desc()
        )
        results = session.exec(statement).all()
        return list(results)


def clear_all_words(engine=None) -> int:
    """Delete all word records. Returns count of deleted rows."""
    target = engine or _engine
    with Session(target) as session:
        records = session.exec(select(WordRecord)).all()
        count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        return count
