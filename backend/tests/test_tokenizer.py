from src.services.tokenizer import SentenceToken, tokenize_sentence


def test_tokenize_plain_sentence() -> None:
    """It should tokenize a simple sentence with POS tags from spaCy."""
    tokens = tokenize_sentence("A cat sat.")
    assert tokens == [
        SentenceToken(text="A", is_word=False, is_target=False, pos="DET"),
        SentenceToken(text="cat", is_word=True, is_target=False, pos="NOUN"),
        SentenceToken(text="sat", is_word=True, is_target=False, pos="VERB"),
        SentenceToken(text=".", is_word=False, is_target=False, pos=None),
    ]


def test_tokenize_with_target_words() -> None:
    """It should parse *word* as a target word and strip the asterisks."""
    tokens = tokenize_sentence("A *lantern* glowed.")

    lantern = next(t for t in tokens if t.text == "lantern")
    assert lantern.is_word is True
    assert lantern.is_target is True
    assert lantern.pos == "NOUN"

    glowed = next(t for t in tokens if t.text == "glowed")
    assert glowed.is_word is True
    assert glowed.pos == "VERB"


def test_tokenize_mixed_content() -> None:
    """It should handle punctuation next to markup."""
    tokens = tokenize_sentence("They *run*, said the *fox*!")

    run_tok = next(t for t in tokens if t.text == "run")
    assert run_tok.is_target is True
    assert run_tok.pos == "VERB"

    fox_tok = next(t for t in tokens if t.text == "fox")
    assert fox_tok.is_target is True
    assert fox_tok.pos == "NOUN"

    comma = next(t for t in tokens if t.text == ",")
    assert comma.is_word is False

    # "the" should be filtered by stopwords
    the_tok = next(t for t in tokens if t.text == "the")
    assert the_tok.is_word is False


def test_target_word_bypasses_stopword_filter() -> None:
    """A markdown-marked target must stay clickable even if it is a stop word."""
    tokens = tokenize_sentence("She said *the* softly.")

    the_tok = next(t for t in tokens if t.text == "the")
    assert the_tok.is_word is True
    assert the_tok.is_target is True

    # "She" is a stopword
    she_tok = next(t for t in tokens if t.text == "She")
    assert she_tok.is_word is False


def test_tokenize_bold_markdown() -> None:
    """It should robustly handle **bold** markdown which LLMs sometimes output."""
    tokens = tokenize_sentence("A **lantern** glowed.")

    lantern = next(t for t in tokens if t.text == "lantern")
    assert lantern.is_target is True
    assert lantern.pos == "NOUN"

    # No stray asterisk tokens
    texts = [t.text for t in tokens]
    assert "*" not in texts


def test_tokenize_with_pos_for_all_words() -> None:
    """Every is_word=True token should have a non-None POS tag."""
    tokens = tokenize_sentence("The cat sat on a beautiful mat.")
    for t in tokens:
        if t.is_word:
            assert t.pos is not None, f"'{t.text}' should have POS"


def test_tokenize_distinguishes_leaves_by_context() -> None:
    """'leaves' as a noun vs verb should get different POS tags."""
    tokens_noun = tokenize_sentence("The leaves are beautiful.")
    leaves_noun = next(t for t in tokens_noun if t.text == "leaves")
    assert leaves_noun.pos == "NOUN"

    tokens_verb = tokenize_sentence("She leaves the room every morning.")
    leaves_verb = next(t for t in tokens_verb if t.text == "leaves")
    assert leaves_verb.pos == "VERB"


def test_tokenize_empty_sentence() -> None:
    """An empty string should return an empty list."""
    assert tokenize_sentence("") == []
    assert tokenize_sentence("   ") == []


def test_tokenize_contraction() -> None:
    """spaCy splits contractions; each part should be a token."""
    tokens = tokenize_sentence("Don't stop.")
    texts = [t.text for t in tokens]
    # spaCy splits "Don't" into "Do" + "n't"
    assert "Do" in texts
    assert "n't" in texts
