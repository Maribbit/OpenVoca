import re
from dataclasses import dataclass

import spacy

from src.services.stopwords import FUNCTION_POS

_nlp = spacy.load("en_core_web_sm")

# Regex to find *word*, **word**, or *hyphen-compound* target markers.
_TARGET_PATTERN = re.compile(r"\*+([A-Za-z]+(?:[-'\'\u2019][A-Za-z]+)*)\*+")


@dataclass(frozen=True)
class SentenceToken:
    text: str
    is_word: bool
    is_target: bool = False
    pos: str | None = None
    lemma: str | None = None
    trailing_space: bool = True


def _merge_hyphenated(tokens: list[SentenceToken]) -> list[SentenceToken]:
    """Merge adjacent ``word - word`` sequences (no whitespace) into one token.

    spaCy splits hyphenated compounds like "lo-fi" into ["lo", "-", "fi"].
    This pass detects such patterns and merges them back into a single token
    so they behave as one clickable unit in the UI.
    """
    if len(tokens) < 3:
        return tokens

    merged: list[SentenceToken] = []
    i = 0
    while i < len(tokens):
        # Look for pattern: alpha(no space) + hyphen(no space) + alpha
        if (
            i + 2 < len(tokens)
            and tokens[i].pos is not None  # alphabetic word
            and tokens[i].trailing_space is False
            and tokens[i + 1].text == "-"
            and tokens[i + 1].trailing_space is False
            and tokens[i + 2].pos is not None  # alphabetic word
        ):
            # Collect the whole chain: word-word-word...
            parts_text = [tokens[i].text]
            first_pos = tokens[i].pos
            j = i + 1
            while (
                j + 1 < len(tokens)
                and tokens[j].text == "-"
                and tokens[j].trailing_space is False
                and tokens[j + 1].pos is not None
            ):
                parts_text.append("-")
                parts_text.append(tokens[j + 1].text)
                j += 2
                # Continue if next is another hyphen with no space
                if j < len(tokens) and tokens[j - 1].trailing_space is False:
                    continue
                break

            combined_text = "".join(parts_text)
            # Use the first sub-token's POS; lemma is the full compound lowercased
            merged.append(
                SentenceToken(
                    text=combined_text,
                    is_word=True,
                    is_target=False,  # target matching happens after merge
                    pos=first_pos,
                    lemma=combined_text.lower(),
                    trailing_space=tokens[j - 1].trailing_space,
                )
            )
            i = j
        else:
            merged.append(tokens[i])
            i += 1

    return merged


def tokenize_sentence(sentence: str) -> list[SentenceToken]:
    """Tokenize a sentence using spaCy, with target-word markup and stopword filtering.

    1. Extract target words from *...* / **...** markers.
    2. Strip all asterisks to produce clean text for spaCy.
    3. Run spaCy to get tokens with POS tags.
    4. Merge hyphenated sub-tokens back into single tokens.
    5. For each token: mark targets, filter stopwords, assign POS.
    """
    if not sentence.strip():
        return []

    # Step 1: collect lowercased target words from markdown markers.
    # Both whole hyphenated forms ("lo-fi") and individual parts ("lo", "fi")
    # are stored so we can match either merged or unmerged tokens.
    target_words: dict[str, int] = {}
    for match in _TARGET_PATTERN.finditer(sentence):
        raw = match.group(1).lower()
        # Store the whole form (e.g. "lo-fi")
        target_words[raw] = target_words.get(raw, 0) + 1
        # Also store individual parts for non-compound targets
        parts = [p for p in re.split(r"[^a-z]+", raw) if p]
        if len(parts) == 1:
            # Simple word — ensure it's in the dict
            target_words[parts[0]] = target_words.get(parts[0], 0) + 1

    # Step 2: strip all asterisks for clean spaCy input.
    clean = sentence.replace("*", "")

    # Step 3: run spaCy.
    doc = _nlp(clean)

    # Step 3.5: build raw token list, then merge hyphenated compounds.
    raw_tokens: list[SentenceToken] = []
    for spacy_token in doc:
        text = spacy_token.text
        is_alpha = spacy_token.is_alpha
        pos = spacy_token.pos_ if is_alpha else None
        lemma = spacy_token.lemma_.lower() if is_alpha else None

        is_word = False
        if is_alpha:
            is_word = pos not in FUNCTION_POS

        raw_tokens.append(
            SentenceToken(
                text=text,
                is_word=is_word,
                is_target=False,
                pos=pos,
                lemma=lemma,
                trailing_space=len(spacy_token.whitespace_) > 0,
            )
        )

    tokens = _merge_hyphenated(raw_tokens)

    # Step 4: mark targets on the (possibly merged) token list.
    remaining_targets = dict(target_words)
    result: list[SentenceToken] = []
    for token in tokens:
        is_target = False
        if token.pos is not None and token.lemma:
            # Match by lemma first (handles inflected forms).
            if token.lemma in remaining_targets and remaining_targets[token.lemma] > 0:
                is_target = True
                remaining_targets[token.lemma] -= 1
            else:
                # Fallback: match by surface text.
                low = token.text.lower()
                if low in remaining_targets and remaining_targets[low] > 0:
                    is_target = True
                    remaining_targets[low] -= 1

        if is_target:
            result.append(
                SentenceToken(
                    text=token.text,
                    is_word=True,
                    is_target=True,
                    pos=token.pos,
                    lemma=token.lemma,
                    trailing_space=token.trailing_space,
                )
            )
        else:
            result.append(token)

    return result
