import pytest

from src.services.prompt_builder import build_sentence_generation_prompt


def test_build_prompt_interpolates_target_words() -> None:
    """The builder should replace {{target_words}} with the comma-separated list."""
    words = ["lantern", "meadow"]
    template = "Write a sentence with: {{target_words}}."
    prompt = build_sentence_generation_prompt(words, template)

    assert "Write a sentence with: lantern, meadow." in prompt


def test_build_prompt_appends_target_words_if_placeholder_missing() -> None:
    """The builder should append target words if the template lacks the placeholder."""
    words = ["lantern", "meadow"]
    template = "Write a sentence."
    prompt = build_sentence_generation_prompt(words, template)

    assert "Write a sentence.\nTarget words: lantern, meadow." in prompt


def test_build_prompt_uses_fallback_when_words_empty() -> None:
    """The builder should use a protective fallback instruction when no words are provided."""
    words: list[str] = []
    template = "Write a sentence: {{target_words}}"
    prompt = build_sentence_generation_prompt(words, template)

    assert "The user did not provide target words" in prompt
    assert "You may generate any natural English sentence" in prompt


def test_build_prompt_requires_template() -> None:
    """The builder should raise ValueError if the template is empty."""
    with pytest.raises(ValueError, match="prompt template is required"):
        build_sentence_generation_prompt(["word"], "")
