"""Lightweight dictionary lookup backed by a pre-built SQLite extract of ECDICT."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "dictionary.db"

_conn: sqlite3.Connection | None = None


@dataclass(frozen=True, slots=True)
class DictionaryEntry:
    word: str
    phonetic: str | None
    definition: str | None
    translation: str
    pos: str | None
    tag: str | None
    exchange: str | None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if not _DB_PATH.exists():
            raise FileNotFoundError(f"Dictionary database not found: {_DB_PATH}")
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def lookup(word: str) -> DictionaryEntry | None:
    """Look up a word (case-insensitive). Returns None if not found."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT word, phonetic, definition, translation, pos, tag, exchange "
        "FROM dictionary WHERE word = ? COLLATE NOCASE",
        (word,),
    ).fetchone()
    if row is None:
        return None
    return DictionaryEntry(
        word=row["word"],
        phonetic=row["phonetic"],
        definition=row["definition"],
        translation=row["translation"],
        pos=row["pos"],
        tag=row["tag"],
        exchange=row["exchange"],
    )


def lookup_custom(word: str, db_path: Path) -> DictionaryEntry | None:
    """Look up a word using a custom database path (for testing)."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT word, phonetic, definition, translation, pos, tag, exchange "
            "FROM dictionary WHERE word = ? COLLATE NOCASE",
            (word,),
        ).fetchone()
        if row is None:
            return None
        return DictionaryEntry(
            word=row["word"],
            phonetic=row["phonetic"],
            definition=row["definition"],
            translation=row["translation"],
            pos=row["pos"],
            tag=row["tag"],
            exchange=row["exchange"],
        )
    finally:
        conn.close()
