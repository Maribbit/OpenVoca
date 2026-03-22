import re
from dataclasses import dataclass

TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d+|[^\w\s]")


@dataclass(frozen=True)
class SentenceToken:
    text: str
    is_word: bool


def tokenize_sentence(sentence: str) -> list[SentenceToken]:
    if not sentence.strip():
        return []

    tokens: list[SentenceToken] = []
    for match in TOKEN_PATTERN.finditer(sentence):
        text = match.group(0)
        tokens.append(
            SentenceToken(
                text=text,
                is_word=bool(re.fullmatch(r"[A-Za-z]+(?:['’][A-Za-z]+)*|\d+", text)),
            )
        )

    return tokens
