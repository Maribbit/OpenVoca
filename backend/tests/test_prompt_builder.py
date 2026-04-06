import pytest

from src.services.prompt_builder import (
    build_sentence_generation_prompt,
)


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


def test_build_prompt_includes_composer_instructions() -> None:
    """Composer instructions string should be appended to the final prompt."""
    words = ["hello"]
    template = "Write a sentence: {{target_words}}"
    instructions = "[Scenario] You are a pirate.\n[Difficulty] Use simple vocabulary."
    prompt = build_sentence_generation_prompt(words, template, instructions)

    assert "[Scenario] You are a pirate." in prompt
    assert "[Difficulty] Use simple vocabulary." in prompt


def test_build_prompt_without_composer_instructions() -> None:
    """When no composer instructions, prompt should still work fine."""
    words = ["hello"]
    template = "Write a sentence: {{target_words}}"
    prompt = build_sentence_generation_prompt(words, template)

    assert "hello" in prompt
    assert "[Scenario]" not in prompt


class TestBuildPromptWithComposer:
    def test_composer_instructions_appended(self) -> None:
        """Composer instructions should appear in the final prompt."""
        prompt = build_sentence_generation_prompt(
            ["harbor"],
            "Write a sentence: {{target_words}}",
            composer_instructions="Topic: science. Use a formal tone.",
        )
        assert "harbor" in prompt
        assert "Topic: science. Use a formal tone." in prompt

    def test_empty_composer_instructions_no_change(self) -> None:
        """Empty composer instructions should not add anything extra."""
        base = build_sentence_generation_prompt(
            ["harbor"], "Write a sentence: {{target_words}}"
        )
        with_empty = build_sentence_generation_prompt(
            ["harbor"], "Write a sentence: {{target_words}}", composer_instructions=""
        )
        assert base == with_empty

    def test_composer_instructions_before_marking(self) -> None:
        """Composer instructions should appear before the IMPORTANT marking rule."""
        prompt = build_sentence_generation_prompt(
            ["harbor"],
            "Write a sentence: {{target_words}}",
            composer_instructions="Use past tense.",
        )
        marking_pos = prompt.index("IMPORTANT")
        composer_pos = prompt.index("Use past tense.")
        assert composer_pos < marking_pos
