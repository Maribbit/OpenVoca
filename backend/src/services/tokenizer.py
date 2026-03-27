import re
from dataclasses import dataclass

import spacy

from src.services.stopwords import FUNCTION_POS

_nlp = spacy.load("en_core_web_sm")

# Regex to find *word* or **word** target markers in the raw LLM output.
_TARGET_PATTERN = re.compile(r"\*+([A-Za-z]+(?:['\'\u2019][A-Za-z]+)*)\*+")


@dataclass(frozen=True)
class SentenceToken:
    text: str
    is_word: bool
    is_target: bool = False
    pos: str | None = None


def tokenize_sentence(sentence: str) -> list[SentenceToken]:
    """Tokenize a sentence using spaCy, with target-word markup and stopword filtering.

    1. Extract target words from *...* / **...** markers.
    2. Strip all asterisks to produce clean text for spaCy.
    3. Run spaCy to get tokens with POS tags.
    4. For each spaCy token: mark targets, filter stopwords, assign POS.
    """
    if not sentence.strip():
        return []

    # Step 1: collect lowercased target words from markdown markers.
    target_words: dict[str, int] = {}
    for match in _TARGET_PATTERN.finditer(sentence):
        word = match.group(1).lower()
        target_words[word] = target_words.get(word, 0) + 1

    # Step 2: strip all asterisks for clean spaCy input.
    clean = sentence.replace("*", "")

    # Step 3: run spaCy.
    doc = _nlp(clean)

    # Step 4: build token list from spaCy output.
    remaining_targets = dict(target_words)
    tokens: list[SentenceToken] = []
    for spacy_token in doc:
        text = spacy_token.text
        is_alpha = spacy_token.is_alpha
        pos = spacy_token.pos_ if is_alpha else None

        # Check if this word was marked as a target by the LLM.
        is_target = False
        low = text.lower()
        if is_alpha and low in remaining_targets and remaining_targets[low] > 0:
            is_target = True
            remaining_targets[low] -= 1

        # Determine if the token is a clickable word.
        if is_target:
            is_word = True
        elif is_alpha:
            is_word = pos not in FUNCTION_POS
        else:
            is_word = False

        tokens.append(
            SentenceToken(text=text, is_word=is_word, is_target=is_target, pos=pos)
        )

    return tokens
