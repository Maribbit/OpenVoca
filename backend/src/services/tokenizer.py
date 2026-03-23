import re
from dataclasses import dataclass

from src.services.stopwords import ENGLISH_STOP_WORDS

# Match standard tokens:
# 1. Words (including contractions like "don't"): [A-Za-z]+(?:['’][A-Za-z]+)*
# 2. Numbers: \d+
# 3. Everything else (punctuation): [^\w\s]
# NOTE: The *...* syntax for targets must be handled FIRST.
# We use (\*+[A-Za-z]...\*+) to match both single *word* and double **word** (bold) styles.
TOKEN_PATTERN = re.compile(
    r"(\*+[A-Za-z]+(?:['’][A-Za-z]+)*\*+)|"  # Group 1: Target word wrapped in *...* or **...**
    r"([A-Za-z]+(?:['’][A-Za-z]+)*|\d+|[^\w\s])"  # Group 2: Standard tokens
)


@dataclass(frozen=True)
class SentenceToken:
    text: str
    is_word: bool
    is_target: bool = False


def tokenize_sentence(sentence: str) -> list[SentenceToken]:
    if not sentence.strip():
        return []

    tokens: list[SentenceToken] = []
    for match in TOKEN_PATTERN.finditer(sentence):
        target_group = match.group(1)
        standard_group = match.group(2)

        if target_group:
            # Strip ALL asterisks (one or many)
            text = target_group.strip("*")
            # Target words from the LLM are ALWAYS treated as valid vocab words, even if they match a stopword
            tokens.append(SentenceToken(text=text, is_word=True, is_target=True))
        elif standard_group:
            text = standard_group
            is_word = bool(re.fullmatch(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d+", text))
            if is_word and text == "*":
                # Fallback: if a lone * got matched in Group 2 (because it had no closing asterisk?)
                # We treat it as punctuation.
                is_word = False

            # Stop word filter logic
            if is_word and text.lower() in ENGLISH_STOP_WORDS:
                is_word = False

            tokens.append(SentenceToken(text=text, is_word=is_word, is_target=False))

    return tokens
