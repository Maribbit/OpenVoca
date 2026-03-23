from src.services.tokenizer import SentenceToken, tokenize_sentence


def test_tokenize_plain_sentence() -> None:
    """It should tokenize a simple sentence without markup."""
    tokens = tokenize_sentence("A cat sat.")
    assert tokens == [
        SentenceToken(text="A", is_word=False, is_target=False),
        SentenceToken(text="cat", is_word=True, is_target=False),
        SentenceToken(text="sat", is_word=True, is_target=False),
        SentenceToken(text=".", is_word=False, is_target=False),
    ]


def test_tokenize_with_target_words() -> None:
    """It should parse *word* as a target word and strip the asterisks."""
    tokens = tokenize_sentence("A *lantern* glowed.")

    assert tokens == [
        SentenceToken(text="A", is_word=False, is_target=False),
        SentenceToken(text="lantern", is_word=True, is_target=True),
        SentenceToken(text="glowed", is_word=True, is_target=False),
        SentenceToken(text=".", is_word=False, is_target=False),
    ]


def test_tokenize_mixed_content() -> None:
    """It should handle punctuation next to markup."""
    tokens = tokenize_sentence("*Run*, said the *fox*!")

    assert tokens == [
        SentenceToken(text="Run", is_word=True, is_target=True),
        SentenceToken(text=",", is_word=False, is_target=False),
        SentenceToken(text="said", is_word=True, is_target=False),
        SentenceToken(text="the", is_word=False, is_target=False),
        SentenceToken(text="fox", is_word=True, is_target=True),
        SentenceToken(text="!", is_word=False, is_target=False),
    ]


def test_target_word_bypasses_stopword_filter() -> None:
    """A markdown-marked target must stay clickable even if it is a stop word."""
    tokens = tokenize_sentence("She said *the* softly.")

    assert tokens == [
        SentenceToken(text="She", is_word=False, is_target=False),
        SentenceToken(text="said", is_word=True, is_target=False),
        SentenceToken(text="the", is_word=True, is_target=True),
        SentenceToken(text="softly", is_word=True, is_target=False),
        SentenceToken(text=".", is_word=False, is_target=False),
    ]


def test_tokenize_bold_markdown() -> None:
    """It should robustly handle **bold** markdown which LLMs sometimes output."""
    tokens = tokenize_sentence("A **lantern** glowed.")
    # We want it to treat "lantern" as the target and strip ALL asterisks.

    # 0 = A
    # 1 = lantern
    # 2 = glowed
    # 3 = .
    assert len(tokens) == 4

    lantern_token = tokens[1]
    assert lantern_token.text == "lantern"
    assert lantern_token.is_target is True
    # Ensure no stray asterisk tokens around it
    assert tokens[0].text == "A"
    assert tokens[2].text == "glowed"


def test_validation_ignores_malformed_markup() -> None:
    """Edge cases: empty markup or partial markup should be handled gracefully."""
    # This is a behavior choice: either fail or treat as normal text.
    # Current regex might treat '**' as punctuation if not matched by the target group.
    # We'll treat weird input as best-effort.
    tokenize_sentence("A ** star.")
    # Expectation: * and * are punctuation, 'star' is word.
    # Current regex: [^\w\s] catches *.
    pass
