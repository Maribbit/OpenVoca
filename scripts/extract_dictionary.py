"""Extract a compact dictionary from ECDICT's stardict.db.

Selection criteria (OR):
  - BNC frequency rank <= 30,000
  - COCA frequency rank <= 30,000
  - Has exam tag (cet4, cet6, gre, toefl, ielts, etc.)

All selected words must have a Chinese translation.

Output: backend/data/dictionary.db (~5-10MB)
  Table: dictionary (word, phonetic, definition, translation, pos, tag, exchange)
"""

import os
import sqlite3
import sys

SOURCE = "stardict.db"
OUTPUT = os.path.join("backend", "data", "dictionary.db")

QUERY = """
SELECT word, phonetic, definition, translation, pos, tag, exchange
FROM stardict
WHERE (
    (bnc > 0 AND bnc <= 30000)
    OR (frq > 0 AND frq <= 30000)
    OR (tag IS NOT NULL AND tag != '')
)
AND translation IS NOT NULL AND translation != ''
ORDER BY word COLLATE NOCASE
"""


def main() -> None:
    if not os.path.exists(SOURCE):
        print(f"Error: {SOURCE} not found in current directory.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    # Remove old output if exists
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    src = sqlite3.connect(SOURCE)
    dst = sqlite3.connect(OUTPUT)

    dst.execute("""
        CREATE TABLE dictionary (
            word      TEXT NOT NULL,
            phonetic  TEXT,
            definition TEXT,
            translation TEXT NOT NULL,
            pos       TEXT,
            tag       TEXT,
            exchange  TEXT
        )
    """)

    cur = src.execute(QUERY)
    rows = cur.fetchall()

    dst.executemany(
        "INSERT INTO dictionary VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

    # Create index on word for fast lookup
    dst.execute("CREATE INDEX idx_dictionary_word ON dictionary (word COLLATE NOCASE)")

    dst.commit()

    # Stats
    count = dst.execute("SELECT COUNT(*) FROM dictionary").fetchone()[0]
    dst.close()
    src.close()

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"Extracted {count} words → {OUTPUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
